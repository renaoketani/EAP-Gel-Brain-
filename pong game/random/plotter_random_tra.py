from threading import Thread
import time
import config 
from os.path import exists
from datetime import date
import os

import board 
import busio 
import adafruit_ina219 
import RPi.GPIO as GPIO 

class serialPlot:
    def __init__(self, *args):
        self.isRun = True
        self.thread = None
        
        # 保存用ディレクトリ作成
        if not os.path.exists("Data"): os.makedirs("Data")
        
        # 1. GPIOの初期化
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # ピン定義
        self.PINS = [21, 15, 18, 20, 8, 24]
        for pin in self.PINS:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        
        # 2. I2Cと3つのセンサーを初期化 (ここが重要！)
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            # tra_plotter.py と同じアドレス設定
            self.ina_black = self._init_sensor(0x40, "Black")
            self.ina_brown = self._init_sensor(0x41, "Brown")
            self.ina_red   = self._init_sensor(0x44, "Red")
        except Exception as e:
            print(f"I2C Init Error: {e}")

        # 保存先ファイル作成
        filePathCount = 0
        while (exists(f"Data/senseData_{date.today()}_{filePathCount}.txt")): 
            filePathCount += 1
        self.filePath = f"Data/senseData_{date.today()}_{filePathCount}.txt"
        
        print("GPIO and 3 Sensors initialized.")

    def _init_sensor(self, address, name):
        """センサー初期化用ヘルパー"""
        try:
            s = adafruit_ina219.INA219(self.i2c, address)
            print(f"INA219 {name} connected at {hex(address)}.")
            return s
        except:
            print(f"INA219 {name} not found at {hex(address)}.")
            return None

    def readSerialStart(self):
        self.thread = Thread(target=self.backgroundThread)
        self.thread.start()

    def getCurrents_RPI(self):
        """3つのセンサーから電流を取得して返す"""
        cBlack, cBrown, cRed = 0.0, 0.0, 0.0
        try:
            if self.ina_black: cBlack = self.ina_black.current
            if self.ina_brown: cBrown = self.ina_brown.current
            if self.ina_red:   cRed   = self.ina_red.current
        except: pass
        # pong_random_tra.py の extractPosition が期待する形式
        return f"{cBlack:.1f},{cBrown:.1f},{cRed:.1f},{time.time()*1000:.0f}"

    def DriveElectrod_RPI(self, inputs_str):
        try:
            if isinstance(inputs_str, str):
                outputs = [int(x.strip()) for x in inputs_str.split(',')]
            else:
                outputs = inputs_str

            for i in range(min(len(outputs), len(self.PINS))):
                GPIO.output(self.PINS[i], GPIO.HIGH if outputs[i] != 0 else GPIO.LOW)
        except: pass

    def backgroundThread(self):
        while self.isRun:
            if config.RelayQ:
                self.DriveElectrod_RPI(config.RelayQ)
            
            # ログ保存
            current_data = self.getCurrents_RPI()
            try:
                with open(self.filePath, "a") as f:
                    f.write(f"{config.RelayQ}:{current_data}\n")
            except: pass
            
            time.sleep(0.1)

    def close(self):
        self.isRun = False
        if self.thread: 
            self.thread.join()
        GPIO.cleanup()
        print("GPIO Cleaned up.")
