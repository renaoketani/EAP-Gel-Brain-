# pong.py (リセット機能・正規化ロジック完全統合版)

import pygame
from paddle import Paddle
from ball import Ball
from region import Region
import config
from os.path import exists
from datetime import date
import time
import numpy as np
import scipy.optimize as opt
from random import randint
import os

BLACK  = (0  ,0  ,0  )
WHITE  = (255,255,255)
BLUE   = (51 ,146,255)
ORANGE = (232,176,7  )

class Pong():
    def __init__(self, Size):
        pygame.init()
        self.lastRawData = ""
        self.size = Size 
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("Pong")
        pygame.display.update()

        # ファイルパスの設定
        filePathCount = 0
        while (exists(r"Data/pongData_"+str(date.today())+"_"+str(filePathCount)+".txt")): 
            filePathCount += 1
        self.filePath = r"Data/pongData_"+str(date.today())+"_"+str(filePathCount)+".txt"
        self.epoch_time = float(time.time())

        self.ballFilePath = r"Data/ballPos_"+str(date.today())+"_"+str(filePathCount)+".txt"
        self.lastBallPosTime = -0.5
        
        self.carryOn = True 

        # パドルとボールのサイズ設定
        self.paddleHeight = round(self.size[1]/3)
        self.paddle = Paddle(WHITE, round(self.size[0]*0.015), self.paddleHeight, self.size) 
        self.paddle.rect.x = round(self.size[0]*0.002) 
        self.paddle.rect.y = round(self.size[1]/2) 

        self.ball = Ball(WHITE,round(self.size[1]*0.03663793103),round(self.size[1]*0.03663793103)) 
        self.ball.reset(round(self.size[0]/2),round(self.size[1]/2)) 

        # 領域（Region）の設定
        self.ballRegions = [Region] * 6
        for i in range(6):
            self.ballRegions[i] = Region(BLUE,(self.size[0])/2,self.size[1]/3)
            self.ballRegions[i].rect.x = i%2*((self.size[0])/2)
            self.ballRegions[i].rect.y = i%3*self.size[1]/3

        self.all_sprites_list = pygame.sprite.Group()
        for i in range(6):
            self.all_sprites_list.add(self.ballRegions[i])
        self.all_sprites_list.add(self.paddle)
        self.all_sprites_list.add(self.ball)

        self.score = 0

    def getScore(self):
        return self.score

    def clearScore(self):
        self.score = 0

    def close(self):
        self.carryOn = False 

    def extractPosition(self, rawData):
        """正規化ロジック (scipy.optimizeを使用)"""
        try:
            temp = rawData.split(',')
            currents = [float(temp[0]), float(temp[1]), float(temp[2])]
            
            # 正規化用パラメータ (環境に合わせて調整)
            origTop, origMid, origBot = 0, 0, 0 
            topupRangeC = 6.7
            midupRangeC = 4.9
            botupRangeC = 7.6
            toplowRangeC = 3.7#マイナスの値は正の値で入力
            midlowRangeC = 3.1
            botlowRangeC = 4.4 
    
            curTop = self.mapCurrent(currents[0], origTop + topupRangeC, origTop - toplowRangeC)
            curMid = self.mapCurrent(currents[1], origMid + midupRangeC, origMid - midlowRangeC)
            curBot = self.mapCurrent(currents[2], origBot + botupRangeC, origBot - botlowRangeC)

            # 二次関数フィッティング
            def func(x, a, b, c):
                return a * np.power(x, 2) + b * x + c

            xdata = np.array([int(self.size[1]/6), int((3*self.size[1])/6), int((5*self.size[1])/6)])
            ydata = np.array([curTop, curMid, curBot])

            optimizedParameters, pcov = opt.curve_fit(func, xdata, ydata)
            dispX = np.linspace(0, self.size[1], self.size[1])
            dispY = func(dispX, *optimizedParameters)
            
            # 最大値の場所をパドル位置にする
            pos = np.argmax(dispY) - (self.paddleHeight / 2)
            self.paddle.setPos(int(pos))
            
        except:
            pass

    def mapCurrent(self, current, maxC, minC):
        temp = ((current - minC) / (maxC - minC))
        return max(0.0, min(1.0, temp))

    def directCovert(self, stim):
        return -1 if stim != 0 else 0

    def gameLoop(self):
        clock = pygame.time.Clock()
        tempRegion = [False] * 6
        hitFlag = False
        scoreFlag = False # スコアが増えた/リセットされた時のログ用フラグ
        resetFlag = False # ボールを中央に戻す用フラグ

        while self.carryOn:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.carryOn = False 
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_x: 
                        self.carryOn=False

            # センサー入力によるパドル移動
            if not config.SenseQ == "":
                rawData = config.SenseQ
                if not self.lastRawData == rawData:
                    self.extractPosition(rawData)
                    self.lastRawData = rawData

            self.all_sprites_list.update()
            config.BallQ = f"{self.ball.rect.x},{self.ball.rect.y},{self.score}"

            # ボール位置の記録
            if ((float(time.time())-self.epoch_time)-self.lastBallPosTime) >= 0.5 :
                with open(self.ballFilePath, "a") as file:
                    file.write(str(round(float(time.time())-self.epoch_time,2))+','+self.ball.getPos()+"\n")
                self.lastBallPosTime = float(time.time())-self.epoch_time

            # --- 壁およびパドルの衝突判定ロジック ---
            
            # 1. 右壁: 跳ね返るのみ
            if self.ball.rect.x >= self.size[0] - 40:
                self.ball.velocity[0] = -abs(self.ball.velocity[0])
            
            # 2. 左壁 (ミス): スコアを0にし、ボールをリセットする
            if self.ball.rect.x <= 0: 
                self.clearScore()  # スコアリセット
                scoreFlag = True
                resetFlag = True   # ボールを中央へ
            
            # 3. 下壁: 跳ね返るのみ
            if self.ball.rect.y > self.size[1] - 40:
                self.ball.velocity[1] = -abs(self.ball.velocity[1])
            
            # 4. 上壁: 跳ね返るのみ
            if self.ball.rect.y < 0:
                self.ball.velocity[1] = abs(self.ball.velocity[1])

            # 5. パドル衝突: カウントアップ (+1)
            if pygame.sprite.collide_mask(self.ball, self.paddle) and not hitFlag:
                hitFlag = True
                self.ball.bounce() # 跳ね返り処理
                self.score += 1    # 加点
                scoreFlag = True
            elif not pygame.sprite.collide_mask(self.ball, self.paddle) and hitFlag:
                hitFlag = False

            # リージョン（刺激領域）の衝突判定
            RegionStim = [False] * 6
            for i in range(6):
                if pygame.sprite.collide_mask(self.ball, self.ballRegions[i]):
                    self.ballRegions[i].activate()
                    RegionStim[i] = True
                else :
                    self.ballRegions[i].deactivate()
                    RegionStim[i] = False

            # スコア変動やミスが発生した時のファイル保存処理
            if scoreFlag:
                hitSpot = "miss" if resetFlag else "paddle"
                # 当たった場所の特定
                if RegionStim[0]: hitSpot += "_top"
                if RegionStim[4]: hitSpot += "_mid"
                if RegionStim[2]: hitSpot += "_bot"

                with open(self.filePath, "a") as file:
                    file.write(f"{hitSpot},{self.score},{round(float(time.time())-self.epoch_time,2)}\n")

                if resetFlag:
                    self.ball.reset(round(self.size[0]/2),round(self.size[1]/2))
                    resetFlag = False
                scoreFlag = False

            # 刺激信号の更新
            if not RegionStim == tempRegion:
                RegionStimString = ",".join([str(self.directCovert(int(s))) for s in RegionStim])
                config.RelayQ = RegionStimString
                tempRegion = RegionStim[:]

            # 画面描画
            self.screen.fill(BLACK)
            self.all_sprites_list.draw(self.screen) 
            font = pygame.font.Font(None, 74)
            text = font.render(str(self.score), 1, WHITE)
            self.screen.blit(text, (self.size[0]*0.5, 10))
            pygame.display.flip()
            clock.tick(60)

        pygame.display.quit()
        pygame.quit()
