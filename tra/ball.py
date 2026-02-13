import pygame
import math
from random import randint, uniform, choice

BLACK = (0, 0, 0)
 
class Ball(pygame.sprite.Sprite):
    def __init__(self, color, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        pygame.draw.rect(self.image, color, [0, 0, width, height])
        self.rect = self.image.get_rect()
        
        # ボールの速さを固定
        self.base_speed = 20.0
        self.velocity = [0, 0]
        
    def reset(self, posX, posY):
        # 初期発射：右方向へ飛ばす
        # 角度は 30度(π/6) 〜 60度(π/3) の間に限定
        angle = uniform(math.pi / 6, math.pi / 3)
        
        # 上(マイナス)に行くか下(プラス)に行くかランダム
        direction_y = choice([-1, 1])
        
        self.velocity = [
            self.base_speed * math.cos(angle),              # 右方向（プラス）
            self.base_speed * math.sin(angle) * direction_y # 上下ランダム
        ]
        
        self.rect.x = posX
        self.rect.y = posY
        
    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
          
    def bounce(self):
        # 跳ね返り：パドル（左）に当たったので、右へ飛ばす
        
        # 角度をランダムに再設定（30度〜60度）
        angle = uniform(math.pi / 6, math.pi / 3)
        
        # 上に行くか下に行くかランダム
        direction_y = choice([-1, 1])
        
        # 左にあるパドルに当たったので、X速度は必ずプラス（右向き）にする
        self.velocity[0] = self.base_speed * math.cos(angle)
        self.velocity[1] = self.base_speed * math.sin(angle) * direction_y
            
    def getPos(self):
        return str(self.rect.x) + ',' + str(self.rect.y)
