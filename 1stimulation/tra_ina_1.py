import RPi.GPIO as GPIO
import time
import board
import busio
from adafruit_ina219 import INA219
from collections import deque
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import sys
import threading  # 並列処理用

# --- 設定項目 ---
# GPIOピン設定
BLUE_POS = 18
BLUE_NEG = 1


ACTIVE_INTERVAL = 10    # ONの間隔（秒）
INACTIVE_INTERVAL = 5     # 最初の待機時間（秒）
TOTAL_DURATION = 36000        # 全体の実行時間（秒）

ACTIVE_STATE  = GPIO.HIGH
INACTIVE_STATE = GPIO.LOW

# INA219設定
INA219_ADDRESSES = [0x40, 0x41, 0x44]
MAX_DATA_POINTS = 200
SAMPLE_INTERVAL = 0.1
LOG_FILENAME = 'multi_current_log.csv'

# --- グローバル変数（スレッド停止用） ---
stop_event = threading.Event()

# --- リレー制御用関数（別スレッドで実行） ---
def relay_control_task():
    print(">>> リレー制御スレッド開始")
    
    # GPIO初期化
    pins = [BLUE_POS, BLUE_NEG]
    # 重複を除去してセットアップ
    unique_pins = list(set(pins))
    
    GPIO.setup(unique_pins, GPIO.OUT, initial=INACTIVE_STATE)

    
    
    start_time = time.time()
    loop_counter = 0

    try:
        while not stop_event.is_set():
            elapsed = time.time() - start_time
            if elapsed >= TOTAL_DURATION:
                print("[Relay] 設定時間が経過しました。制御を終了します。")
                stop_event.set() # メインスレッドにも終了を通知
                break

            loop_counter += 1
            # --- BLUE OFF---
            print(f"[Relay Loop {loop_counter}] BLUE OFF ({INACTIVE_INTERVAL}s)")
            GPIO.output(BLUE_POS, INACTIVE_STATE)
            GPIO.output(BLUE_NEG, INACTIVE_STATE)
            time.sleep(INACTIVE_INTERVAL)

            # --- BLUE ON ---
            print(f"[Relay Loop {loop_counter}] BLUE ON ({ACTIVE_INTERVAL}s)")
            GPIO.output(BLUE_POS, ACTIVE_STATE)
            GPIO.output(BLUE_NEG, INACTIVE_STATE)
            
            # 指定時間待機（1秒ごとに停止フラグをチェックして即時終了できるようにする）
            for _ in range(ACTIVE_INTERVAL):
                if stop_event.is_set(): return
                time.sleep(1)
            
    finally:
        # スレッド終了時に全OFF
        GPIO.output(unique_pins, INACTIVE_STATE)
        print(">>> リレー制御スレッド終了")

# --- メイン処理 ---
def main():
    # 1. GPIO初期設定
    GPIO.setmode(GPIO.BCM)
    # 詳細はスレッド内で行うが、モード設定は必須

    # 2. センサー初期化
    i2c_bus = None
    sensors = []
    try:
        i2c_bus = busio.I2C(board.SCL, board.SDA)
        for addr in INA219_ADDRESSES:
            try:
                sensor = INA219(i2c_bus, addr)
                sensors.append(sensor)
                print(f'Sensor initialized at {hex(addr)}')
            except Exception as e:
                print(f'Warning: Failed at {hex(addr)}: {e}')
        
        if not sensors:
            print('Error: No sensors found.')
            sys.exit(1)
    except Exception as e:
        print(f'I2C Init Failed: {e}')
        sys.exit(1)

    # 3. ログファイル準備
    try:
        log_file = open(LOG_FILENAME, 'w')
        header = 'time,' + ','.join([f'current_mA_{hex(s.i2c_device.device_address)}' for s in sensors]) + '\n'
        log_file.write(header)
    except IOError as e:
        print(f"File error: {e}")
        sys.exit(1)

    # 4. グラフ準備
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 8))
    lines = []
    colors = ['blue', 'red', 'green', 'orange']
    
    # データ保存用
    all_time_data = [deque(maxlen=MAX_DATA_POINTS) for _ in sensors]
    all_current_data = [deque(maxlen=MAX_DATA_POINTS) for _ in sensors]

    for i, sensor in enumerate(sensors):
        addr = hex(sensor.i2c_device.device_address)
        line, = ax.plot([], [], color=colors[i % len(colors)], label=f'Sensor ({addr})')
        lines.append(line)

    ax.set_title('Real-time Current Readings')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Current (mA)')
    ax.legend()
    ax.grid(True)

    # 5. リレー制御スレッドの開始
    relay_thread = threading.Thread(target=relay_control_task)
    relay_thread.start()

    print('Measurement started. Press Ctrl+C to stop.')
    start_time = time.time()

    try:
        while not stop_event.is_set():
            now = time.time()
            elapsed_time = now - start_time
            
            current_readings = []
            print_str = f"T={elapsed_time:.1f}s"

            for i, sensor in enumerate(sensors):
                try:
                    mA = sensor.current
                except:
                    mA = 0.0 # 読み取りエラー時は0など
                
                current_readings.append(mA)
                all_time_data[i].append(elapsed_time)
                all_current_data[i].append(mA)
                lines[i].set_data(all_time_data[i], all_current_data[i])
                print_str += f", {hex(sensor.i2c_device.device_address)}: {mA:.1f}mA"

            # ログ書き込み
            log_line = f"{elapsed_time:.4f}," + ','.join([f"{c:.4f}" for c in current_readings]) + "\n"
            log_file.write(log_line)
            
            # グラフ更新（軸調整含む）
            ax.relim()
            ax.autoscale_view()
            # plt.pauseは内部でGUIイベントループを回すため必須
            plt.pause(SAMPLE_INTERVAL) 
            
            print(print_str)

            # もしリレー制御スレッドが終わっていたら（時間経過など）、ループを抜ける
            if not relay_thread.is_alive():
                stop_event.set()

    except KeyboardInterrupt:
        print("\nStop requested by user.")
        stop_event.set() # スレッドを停止させる

    finally:
        # 終了処理
        if not log_file.closed:
            log_file.close()
        
        # リレースレッドが終わるのを待つ
        relay_thread.join(timeout=2.0)
        
        GPIO.cleanup()
        print("Cleaned up GPIO and closed files.")
        plt.ioff()
        plt.show()

if __name__ == '__main__':
    main()
