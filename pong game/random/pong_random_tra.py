import pygame
from paddle import Paddle
from ball import Ball
from region import Region
import config
import time
import numpy as np
import scipy.optimize as opt
from random import randint

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE  = (51, 146, 255)

class Pong():
    def __init__(self, Size):
        pygame.init()
        self.size = Size 
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("Pong - Hybrid Mode Control")

        self.lastRawData = ""
        self.carryOn = True 
        self.score = 0

        self.paddleHeight = round(self.size[1] / 3)
        self.paddle = Paddle(WHITE, round(self.size[0] * 0.015), self.paddleHeight, self.size)
        self.paddle.rect.x = round(self.size[0] * 0.002)
        self.paddle.rect.y = round(self.size[1] / 2)

        ball_size = round(self.size[1] * 0.03663793103)
        self.ball = Ball(WHITE, ball_size, ball_size)
        self.ball.reset(round(self.size[0] / 2), round(self.size[1] / 2))

        self.region_list = []
        r_width = self.size[0] // 2
        r_height = self.size[1] // 3
        for i in range(6):
            reg = Region(BLUE, r_width, r_height)
            reg.rect.x = (i % 2) * r_width
            reg.rect.y = (i // 2) * r_height 
            self.region_list.append(reg)

        self.all_sprites_list = pygame.sprite.Group()
        for reg in self.region_list:
            self.all_sprites_list.add(reg)
        self.all_sprites_list.add(self.paddle)
        self.all_sprites_list.add(self.ball)

    def extractPosition(self, rawData):
        try:
            temp = rawData.split(',')
            currents = [float(temp[0]), float(temp[1]), float(temp[2])]
            def mapCurrent(c, maxC, minC):
                return max(0.0, min(1.0, (c - minC) / (maxC - minC)))
            # 閾値はゲルの状態に合わせて適宜 3, -10 を調整
            curTop = mapCurrent(currents[0], 5, -11.7)
            curMid = mapCurrent(currents[1], 2.9, -10.7)
            curBot = mapCurrent(currents[2], 4.0, -11.4)

            def func(x, a, b, c):
                return a * np.power(x, 2) + b * x + c

            xdata = np.array([self.size[1]/6, 3*self.size[1]/6, 5*self.size[1]/6])
            ydata = np.array([curTop, curMid, curBot])
            popt, _ = opt.curve_fit(func, xdata, ydata)
            dispX = np.linspace(0, self.size[1], self.size[1])
            dispY = func(dispX, *popt)
            pos = np.argmax(dispY) - (self.paddleHeight / 2)
            self.paddle.setPos(int(pos))
        except: pass

    def gameLoop(self):
        clock = pygame.time.Clock()
        hitFlag = False

        while self.carryOn:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.carryOn = False 

            if config.SenseQ != "":
                if self.lastRawData != config.SenseQ:
                    self.extractPosition(config.SenseQ)
                    self.lastRawData = config.SenseQ

            self.all_sprites_list.update()
            config.BallQ = f"{self.ball.rect.x},{self.ball.rect.y},{self.score}"

            # 壁衝突
            if self.ball.rect.x >= self.size[0] - 40:
                self.ball.velocity[0] = -abs(self.ball.velocity[0])
            if self.ball.rect.x <= 0: 
                self.score = 0
                self.ball.reset(round(self.size[0] / 2), round(self.size[1] / 2))
            if self.ball.rect.y > self.size[1] - 40:
                self.ball.velocity[1] = -abs(self.ball.velocity[1])
            if self.ball.rect.y < 0:
                self.ball.velocity[1] = abs(self.ball.velocity[1])

            # パドル衝突
            if pygame.sprite.collide_mask(self.ball, self.paddle) and not hitFlag:
                self.ball.bounce()
                self.score += 1
                hitFlag = True
            elif not pygame.sprite.collide_mask(self.ball, self.paddle):
                hitFlag = False

            # --- リージョン判定と刺激パターンの共有 ---
            current_stim = [0] * 6
            for i, reg in enumerate(self.region_list):
                if pygame.sprite.collide_rect(self.ball, reg):
                    reg.activate()
                    current_stim[i] = 1 
                else:
                    reg.deactivate()
            
            # メインプログラム(sensor_bridge)が参照する信号を更新
            config.RelayQ = ",".join(map(str, current_stim))

            self.screen.fill(BLACK)
            self.all_sprites_list.draw(self.screen) 
            font = pygame.font.Font(None, 74)
            text = font.render(str(self.score), 1, WHITE)
            self.screen.blit(text, (self.size[0] // 2, 10))
            
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
