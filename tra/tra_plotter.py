import time
import board 
import busio 
import adafruit_ina219 
import RPi.GPIO as GPIO 
import config 
from threading import Thread
from datetime import date
from os.path import exists

# --- ピン定義 (1電極1ピンのシンプル構成) ---
BLUE_PIN   = 8 
PURPLE_PIN = 15
YELLOW_PIN = 21
GREEN_PIN  = 24
GREY_PIN   = 18
WHITE_PIN  = 20

ALL_ELECTRODE_PINS = [
    BLUE_PIN, PURPLE_PIN, YELLOW_PIN, 
    GREEN_PIN, GREY_PIN, WHITE_PIN
]

# ボールの位置（Region 0〜5）に対応するピンマップ
PONG_MAP_RPI = [
 
    YELLOW_PIN,  # Region 1
    PURPLE_PIN,  # Region 2
    GREY_PIN,    # Region 3
    WHITE_PIN,   # Region 4
    BLUE_PIN,    # Region 5
    GREEN_PIN,   # Region 6
]

class serialPlot:
    def __init__(self, *args):
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.rawData = ""
        
        # 1. GPIOの初期化
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.ACTIVE_STATE   = GPIO.HIGH
        self.INACTIVE_STATE = GPIO.LOW

        for pin in ALL_ELECTRODE_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, self.INACTIVE_STATE)

        # 2. I2C/センサーの初期化
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.ina_black = self._init_sensor(0x40, "Black")
            self.ina_brown = self._init_sensor(0x41, "Brown")
            self.ina_red   = self._init_sensor(0x44, "Red")
        except Exception as e:
            print(f"I2C Init Error: {e}")

        # 3. 保存先ファイル作成
        filePathCount = 0
        while (exists(f"Data/senseData_{date.today()}_{filePathCount}.txt")): 
            filePathCount += 1
        self.filePath = f"Data/senseData_{date.today()}_{filePathCount}.txt"

        print("GPIO and Sensors initialized (1-pin per electrode mode).")
        self.isReceiving = True

    def _init_sensor(self, address, name):
        try:
            s = adafruit_ina219.INA219(self.i2c, address)
            print(f"INA219 {name} connected at {hex(address)}.")
            return s
        except:
            print(f"INA219 {name} not found at {hex(address)}.")
            return None

    def readSerialStart(self):
        if self.thread is None:
            self.isRun = True
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            print("Background thread started.")

    def DriveElectrod_RPI(self, inputs):
        """
        1電極1ピン制御: 値が 0 以外ならピンを HIGH にする
        """
        try:
            if isinstance(inputs, str):
                outputs = [int(x.strip()) for x in inputs.split(',')]
            else:
                outputs = inputs

            for i in range(min(len(outputs), len(PONG_MAP_RPI))):
                val = outputs[i]
                target_pin = PONG_MAP_RPI[i]
                
                if val != 0:
                    GPIO.output(target_pin, self.ACTIVE_STATE)
                else:
                    GPIO.output(target_pin, self.INACTIVE_STATE)
        except Exception:
            pass

    def setRelays_RPI(self, relay_str):
        self.DriveElectrod_RPI(relay_str)

    def getCurrents_RPI(self):
        cBlack, cBrown, cRed = 0.0, 0.0, 0.0
        try:
            if self.ina_black: cBlack = self.ina_black.current
            if self.ina_brown: cBrown = self.ina_brown.current
            if self.ina_red:   cRed   = self.ina_red.current
        except: pass
        return f"{cBlack:.1f},{cBrown:.1f},{cRed:.1f},{time.time()*1000:.0f}"

    def backgroundThread(self):
        while self.isRun:
            self.rawData = self.getCurrents_RPI()
            if config.RelayQ:
                self.DriveElectrod_RPI(config.RelayQ)
            try:
                with open(self.filePath, "a") as f:
                    f.write(f"{config.RelayQ}:{self.rawData}\n")
            except: pass
            time.sleep(0.1)

    def RestStim_RPI(self):
        for pin in ALL_ELECTRODE_PINS:
            GPIO.output(pin, self.INACTIVE_STATE)
        print("All electrode pins set to LOW.")

    def close(self):
        self.isRun = False
        if self.thread: 
            self.thread.join()
        self.RestStim_RPI()
        GPIO.cleanup()
        print("GPIO Cleaned up.")
