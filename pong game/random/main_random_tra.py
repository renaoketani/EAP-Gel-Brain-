import threading
import time
import config
import csv
import sys
import random
from datetime import datetime
from pong_random_tra import Pong 
from plotter_random_tra import serialPlot 

def main():
    # --- 実験時間の設定 (秒) ---
    INTERVAL_NORMAL = 1200 
    INTERVAL_RANDOM = 600 
    # --------------------------

    s = serialPlot() 
    s.readSerialStart() 
    pong = Pong((1000, 1000))

    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"combined_data_hybrid_{now_str}.csv"

    try:
        f = open(filename, mode='w', newline='')
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "cBlack", "cBrown", "cRed", "RawTime", "BallX", "BallY", "RallyCount", "Mode"])
    except IOError as e:
        print(f"File error: {e}"); sys.exit(1)

    def sensor_bridge():
        # --- 初期化の徹底 ---
        current_mode = "Normal"
        start_time = time.time()
        print(f"\n===== 実験開始: 最初は {INTERVAL_NORMAL}秒間 【NORMAL】 モードです =====")
        
        last_random_time = 0
        random_pattern = "0,0,0,0,0,0"

        while pong.carryOn:
            now = time.time()
            elapsed = now - start_time
            
            # --- モード切り替えロジック ---
            if current_mode == "Normal":
                if elapsed >= INTERVAL_NORMAL:
                    current_mode = "Random"
                    start_time = now # タイマーをリセット
                    print(f">>> {INTERVAL_NORMAL}s 経過: 【RANDOM】 モードに切り替えました")
            else: # Randomモードの場合
                if elapsed >= INTERVAL_RANDOM:
                    current_mode = "Normal"
                    start_time = now # タイマーをリセット
                    print(f">>> {INTERVAL_RANDOM}s 経過: 【NORMAL】 モードに切り替えました")

            # 1. データの同期保存
            current_raw_str = s.getCurrents_RPI() 
            ball_pos_str = config.BallQ
            if current_raw_str and ball_pos_str:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                try:
                    writer.writerow([timestamp] + current_raw_str.split(',') + ball_pos_str.split(',') + [current_mode])
                    f.flush()
                except: pass
                config.SenseQ = current_raw_str 

            # 2. 刺激パターンの決定
            if current_mode == "Normal":
                # pong_random_tra.py がセットしたボール連動刺激を使用
                stim_to_send = config.RelayQ
            else:
                # Randomモード: 1秒ごとに更新
                if now - last_random_time > 1.0:
                    bits = [0] * 6
                    bits[random.randint(0, 5)] = 1
                    random_pattern = ",".join(map(str, bits))
                    last_random_time = now
                stim_to_send = random_pattern
                # 画面(青い四角)もランダムに合わせて点灯させる
                config.RelayQ = stim_to_send

            # 3. GPIO出力の実行
            if stim_to_send:
                s.DriveElectrod_RPI(stim_to_send)
                
            time.sleep(0.01)

    # センサー制御スレッドの開始
    bridge_thread = threading.Thread(target=sensor_bridge, daemon=True)
    bridge_thread.start()

    try:
        pong.gameLoop()
    except KeyboardInterrupt:
        pass
    finally:
        pong.carryOn = False
        f.close()
        s.close()
        print(f"実験終了。データ保存先: {filename}")

if __name__ == '__main__':
    main()
