import os
import pygame


class 音乐管理:
    def __init__(self):
        self.可用 = True
        try:
            pygame.mixer.init()
        except Exception:
            self.可用 = False
        self.当前路径 = None

    def 播放循环(self, 路径: str):
        if not self.可用:
            return
        if not 路径 or not os.path.isfile(路径):
            return
        if self.当前路径 == 路径 and pygame.mixer.music.get_busy():
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        try:
            pygame.mixer.music.load(路径)
            pygame.mixer.music.play(-1)
            self.当前路径 = 路径
        except Exception:
            pass

    def 停止(self):
        if not self.可用:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.当前路径 = None
