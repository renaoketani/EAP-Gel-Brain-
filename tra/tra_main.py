import sys
import threading
from pong import Pong 
from tra_plotter import serialPlot 
import time
import config
import csv  
import os
from datetime import datetime  

def main():
    # フォルダの安全確保
    os.makedirs("Data", exist_ok=True)

    # 接続設定
    s = serialPlot('NOT_USED', 115200, 1000, 4)
    s.readSerialStart()
    
    # ゲームの初期化 (1000, 1000)
    pong = Pong((1000, 1000))
    
    # ログファイル名生成
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"combined_data_{now_str}.csv"

    try:
        f = open(filename, mode='w', newline='')
        writer = csv.writer(f)
        # ★修正：ヘッダーに RallyCount を追加
        writer.writerow(["Timestamp", "cBlack", "cBrown", "cRed", "RawTime", "BallX", "BallY", "RallyCount","PaddleY"])
    except IOError as e:
        print(f"File error: {e}"); sys.exit(1)

    def sensor_bridge():
        print("センサー・ボール位置・ラリー同期保存開始...")

        while pong.carryOn:
            # 電流値を取得 (tra_plotterからは "cBlack,cBrown,cRed,RawTime" が返る)
            current_raw_str = s.getCurrents_RPI() 
            
            # ボール位置とスコアを取得 (pong.pyから "BallX,BallY,RallyCount" が届く)
            ball_pos_str = config.BallQ
            
            if current_raw_str and ball_pos_str:
                current_list = current_raw_str.split(',')
                ball_data = ball_pos_str.split(',')
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                try:
                    # current_list は [cBlack, cBrown, cRed, RawTime]
                    # ball_data は [BallX, BallY, RallyCount]
                    # これらを結合して一行にする
                    writer.writerow([timestamp] + current_list + ball_data)
                    f.flush() 
                except:
                    pass
                
                # パドル移動のためにconfigへ共有
                config.SenseQ = current_raw_str 
            
            # 刺激命令があれば実行
            if config.RelayQ != "":
                s.setRelays_RPI(config.RelayQ)
            
            time.sleep(0.01)

    # センサー監視スレッド
    bridge_thread = threading.Thread(target=sensor_bridge, daemon=True)
    bridge_thread.start()

    try:
        # Pygameのメインループ
        pong.gameLoop()
    except KeyboardInterrupt:
        pass
    finally:
        f.close()
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    main()