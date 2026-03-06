import pygame
from core.工具 import 绘制文本, contain缩放, 画圆角面, 安全加载图片


def 绘制对称蓝渐变按钮底(
    屏幕: pygame.Surface, r: pygame.Rect, 是否按下: bool, 是否悬停: bool
):
    亮度偏移 = 0
    if 是否悬停:
        亮度偏移 = 18
    if 是否按下:
        亮度偏移 = -18

    左色 = (30, 120, 255)
    中色 = (80, 185, 255)
    右色 = (30, 120, 255)

    def 调色(c):
        return (
            max(0, min(255, c[0] + 亮度偏移)),
            max(0, min(255, c[1] + 亮度偏移)),
            max(0, min(255, c[2] + 亮度偏移)),
        )

    左色 = 调色(左色)
    中色 = 调色(中色)
    右色 = 调色(右色)

    渐变面 = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    for x in range(r.w):
        t = x / max(1, r.w - 1)
        if t < 0.5:
            tt = t / 0.5
            c = (
                int(左色[0] + (中色[0] - 左色[0]) * tt),
                int(左色[1] + (中色[1] - 左色[1]) * tt),
                int(左色[2] + (中色[2] - 左色[2]) * tt),
                245,
            )
        else:
            tt = (t - 0.5) / 0.5
            c = (
                int(中色[0] + (右色[0] - 中色[0]) * tt),
                int(中色[1] + (右色[1] - 中色[1]) * tt),
                int(中色[2] + (右色[2] - 中色[2]) * tt),
                245,
            )
        pygame.draw.line(渐变面, c, (x, 0), (x, r.h))

    遮罩 = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    pygame.draw.rect(
        遮罩, (255, 255, 255, 255), pygame.Rect(0, 0, r.w, r.h), border_radius=22
    )
    渐变面.blit(遮罩, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    阴影 = pygame.Rect(r.x + 6, r.y + 8, r.w, r.h)
    pygame.draw.rect(屏幕, (0, 0, 0), 阴影, border_radius=22)

    屏幕.blit(渐变面, r.topleft)
    pygame.draw.rect(屏幕, (255, 255, 255), r, width=6, border_radius=22)


class 渐变按钮:
    def __init__(self, 文本: str):
        self.文本 = 文本
        self.矩形 = pygame.Rect(0, 0, 100, 60)
        self.悬停 = False
        self.按下 = False

    def 设置矩形(self, r: pygame.Rect):
        self.矩形 = r

    def 处理事件(self, 事件) -> bool:
        if 事件.type == pygame.MOUSEMOTION:
            self.悬停 = self.矩形.collidepoint(事件.pos)
        elif 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            if self.矩形.collidepoint(事件.pos):
                self.按下 = True
        elif 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            命中 = self.矩形.collidepoint(事件.pos)
            触发 = self.按下 and 命中
            self.按下 = False
            return 触发
        return False

    def 绘制(self, 屏幕: pygame.Surface, 字体: pygame.font.Font):
        r = self.矩形
        绘制对称蓝渐变按钮底(屏幕, r, self.按下, self.悬停)
        绘制文本(屏幕, self.文本, 字体, (255, 255, 255), r.center, "center")


class 图片按钮:
    def __init__(self, 名称: str, 图片路径: str):
        self.名称 = 名称
        self.图片路径 = 图片路径
        self.矩形 = pygame.Rect(0, 0, 160, 160)
        self.悬停 = False
        self.按下 = False
        self.图片 = None

    def 重新加载图片(self):
        self.图片 = 安全加载图片(self.图片路径, 透明=True)

    def 设置矩形(self, r: pygame.Rect):
        self.矩形 = r

    def 处理事件(self, 事件) -> bool:
        if 事件.type == pygame.MOUSEMOTION:
            self.悬停 = self.矩形.collidepoint(事件.pos)
        elif 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            if self.矩形.collidepoint(事件.pos):
                self.按下 = True
        elif 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            命中 = self.矩形.collidepoint(事件.pos)
            触发 = self.按下 and 命中
            self.按下 = False
            return 触发
        return False

    def 绘制(self, 屏幕: pygame.Surface, 字体: pygame.font.Font):
        r = self.矩形

        缩放系数 = 1.0
        if self.悬停:
            缩放系数 = 1.03
        if self.按下:
            缩放系数 = 0.98

        阴影 = pygame.Rect(r.x + 6, r.y + 10, r.w, r.h)
        pygame.draw.rect(屏幕, (0, 0, 0), 阴影, border_radius=18)

        if self.图片:
            if 缩放系数 != 1.0:
                nw = int(r.w * 缩放系数)
                nh = int(r.h * 缩放系数)
                画布 = contain缩放(self.图片, nw, nh)
                x = r.centerx - nw // 2
                y = r.centery - nh // 2
                屏幕.blit(画布, (x, y))
            else:
                画布 = contain缩放(self.图片, r.w, r.h)
                屏幕.blit(画布, r.topleft)
        else:
            底 = (40, 120, 220) if not self.悬停 else (55, 140, 245)
            if self.按下:
                底 = (28, 95, 180)
            面 = 画圆角面(r.w, r.h, 底, 圆角=18, alpha=245)
            屏幕.blit(面, r.topleft)
            pygame.draw.rect(屏幕, (255, 255, 255), r, width=4, border_radius=18)
            绘制文本(屏幕, self.名称, 字体, (255, 255, 255), r.center, "center")
