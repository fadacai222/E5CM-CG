import json
import math
import os
import time
from typing import Dict, List, Optional, Tuple

import pygame

from core.歌曲记录 import 更新歌曲最高分
from core.工具 import 绘制底部联网与信用
from scenes.场景基类 import 场景基类


def _获取字体(字号: int, 是否粗体: bool = False) -> pygame.font.Font:
    try:
        from core.工具 import 获取字体  # type: ignore

        return 获取字体(int(字号), 是否粗体=bool(是否粗体))
    except Exception:
        pygame.font.init()
        try:
            return pygame.font.SysFont(
                "Microsoft YaHei", int(字号), bold=bool(是否粗体)
            )
        except Exception:
            return pygame.font.Font(None, int(字号))


def _夹取(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


def _缓出三次方(t: float) -> float:
    x = 1.0 - _夹取(t, 0.0, 1.0)
    return 1.0 - x * x * x


def _回弹(t: float) -> float:
    x = _夹取(t, 0.0, 1.0)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * pow(x - 1.0, 3) + c1 * pow(x - 1.0, 2)


def _安全载图(路径: str, 透明: bool = True) -> Optional[pygame.Surface]:
    try:
        if 路径 and os.path.isfile(路径):
            图 = pygame.image.load(路径)
            return 图.convert_alpha() if 透明 else 图.convert()
    except Exception:
        pass
    return None


class 场景_结算(场景基类):
    名称 = "结算"

    def __init__(self, 上下文: dict):
        super().__init__(上下文)
        self._载荷: Dict[str, object] = {}
        self._进入系统秒 = 0.0
        self._数值动画秒 = 2.5
        self._评级砸入秒 = 0.2
        self._顶部砸入秒 = 0.3

        self._背景图: Optional[pygame.Surface] = None
        self._背景视频播放器 = None
        self._背景视频路径: str = ""
        self._面板图: Optional[pygame.Surface] = None
        self._封面图: Optional[pygame.Surface] = None
        self._评级图: Optional[pygame.Surface] = None
        self._全连图: Optional[pygame.Surface] = None
        self._新纪录图: Optional[pygame.Surface] = None
        self._等级窗背景图: Optional[pygame.Surface] = None
        self._等级窗底图: Optional[pygame.Surface] = None
        self._花式经验框图: Optional[pygame.Surface] = None
        self._花式经验值图: Optional[pygame.Surface] = None
        self._竞速经验框图: Optional[pygame.Surface] = None
        self._竞速经验值图: Optional[pygame.Surface] = None
        self._经验数字图集: Dict[str, pygame.Surface] = {}
        self._升级图集: Dict[str, pygame.Surface] = {}
        self._段位图: Optional[pygame.Surface] = None
        self._联网原图: Optional[pygame.Surface] = None
        self._缩放缓存: Dict[Tuple[int, int, int], pygame.Surface] = {}

        self._标题字体 = _获取字体(54, True)
        self._歌名字体 = _获取字体(26, False)
        self._星星字体 = _获取字体(24, False)
        self._数值字体 = _获取字体(42, False)
        self._总分标签字体 = _获取字体(20, False)
        self._总分数字字体 = _获取字体(44, False)
        self._占位字体 = _获取字体(22, False)
        self._等级小窗字体 = _获取字体(22, False)
        self._等级小窗小字体 = _获取字体(18, False)

        self._结算音效: Optional[pygame.mixer.Sound] = None
        self._结算音效时长秒 = 0.0
        self._结算音效播放系统秒 = 0.0
        self._结算音效通道 = None
        self._已切结算BGM = False
        self._奖励数据: Dict[str, object] = {}
        self._歌曲记录结果: Dict[str, object] = {}
        self._奖励窗出现秒 = (
            self._数值动画秒 + self._评级砸入秒 + self._顶部砸入秒 + 0.25
        )

    def 进入(self, 载荷=None):
        self._载荷 = dict(载荷) if isinstance(载荷, dict) else {}
        self._进入系统秒 = time.perf_counter()
        self._已切结算BGM = False
        self._缩放缓存.clear()
        self._奖励数据 = {}
        self._歌曲记录结果 = {}
        self._加载资源()
        self._更新个人资料()
        self._播放结算音效()

    def 退出(self):
        try:
            if self._结算音效通道 is not None:
                self._结算音效通道.stop()
        except Exception:
            pass
        try:
            if self._背景视频播放器 is not None and hasattr(
                self._背景视频播放器, "关闭"
            ):
                self._背景视频播放器.关闭()
        except Exception:
            pass
        self._背景视频播放器 = None

    def 更新(self):
        经过秒 = max(0.0, float(time.perf_counter() - float(self._进入系统秒 or 0.0)))

        if (not self._已切结算BGM) and (经过秒 >= float(self._结算音效时长秒 or 0.0)):
            self._播放结算背景音乐()
        return None

    def 处理事件(self, 事件):
        if 事件.type == pygame.KEYDOWN:
            if 事件.key == pygame.K_ESCAPE:
                return self._返回选歌()
        return None

    def 绘制(self):
        屏幕: pygame.Surface = self.上下文["屏幕"]
        屏宽, 屏高 = 屏幕.get_size()
        经过秒 = max(0.0, float(time.perf_counter() - float(self._进入系统秒 or 0.0)))

        屏幕.fill((0, 0, 0))
        self._绘制结算背景(屏幕)

        常驻暗层 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
        常驻暗层.fill((0, 0, 0, 120))
        屏幕.blit(常驻暗层, (0, 0))

        入场t = _夹取(经过秒 / 0.45, 0.0, 1.0)
        黑幕alpha = int((1.0 - _缓出三次方(入场t)) * 255.0)

        面板尺寸 = int(max(360, min(int(屏高 * 0.82), int(屏宽 * 0.48), 700)))
        面板矩形 = pygame.Rect(
            max(28, int(屏宽 * 0.06)),
            max(20, (屏高 - 面板尺寸) // 2),
            面板尺寸,
            面板尺寸,
        )
        self._绘制结算面板(屏幕, 面板矩形, 经过秒)
        self._绘制奖励小窗(屏幕, 面板矩形, 经过秒)
        self._绘制底部币值(屏幕)

        if 黑幕alpha > 0:
            黑幕 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
            黑幕.fill((0, 0, 0, 黑幕alpha))
            屏幕.blit(黑幕, (0, 0))

    def _绘制结算面板(self, 屏幕: pygame.Surface, 面板矩形: pygame.Rect, 经过秒: float):
        if self._面板图 is not None:
            面板图 = self._缩放图(self._面板图, 面板矩形.size)
            if 面板图 is not None:
                if 经过秒 < 0.25:
                    try:
                        面板图 = 面板图.copy()
                        面板图.set_alpha(int(255 * _缓出三次方(经过秒 / 0.25)))
                    except Exception:
                        pass
                屏幕.blit(面板图, 面板矩形.topleft)
        else:
            pygame.draw.rect(
                屏幕, (30, 45, 90), 面板矩形, border_radius=max(12, 面板矩形.w // 24)
            )

        def px(x: float) -> int:
            return 面板矩形.left + int(面板矩形.w * (float(x) / 512.0))

        def py(y: float) -> int:
            return 面板矩形.top + int(面板矩形.h * (float(y) / 512.0))

        封面框 = pygame.Rect(px(58), py(138), px(184) - px(58), py(272) - py(138))
        self._绘制封面区域(屏幕, 封面框)

        星级 = int(self._载荷.get("星级", 0) or 0)
        星星文本 = ("★" * max(0, 星级)) if 星级 > 0 else ""
        if 星星文本:
            星图 = self._星星字体.render(星星文本, True, (242, 223, 60))
            屏幕.blit(星图, (px(48), py(304)))

        歌名 = str(self._载荷.get("曲目名", "Unknown") or "Unknown")
        self._绘制裁切文本(
            屏幕,
            文本=歌名,
            字体=self._歌名字体,
            颜色=(255, 255, 255),
            区域=pygame.Rect(px(46), py(332), px(214) - px(46), py(370) - py(332)),
        )

        数值t = _缓出三次方(_夹取(经过秒 / float(self._数值动画秒), 0.0, 1.0))
        perfect值 = int(round(int(self._载荷.get("perfect数", 0) or 0) * 数值t))
        cool值 = int(round(int(self._载荷.get("cool数", 0) or 0) * 数值t))
        good值 = int(round(int(self._载荷.get("good数", 0) or 0) * 数值t))
        miss值 = int(round(int(self._载荷.get("miss数", 0) or 0) * 数值t))
        combo值 = int(round(int(self._载荷.get("本局最大combo", 0) or 0) * 数值t))
        分数字 = int(round(int(self._载荷.get("本局最高分", 0) or 0) * 数值t))

        百分比目标 = float(self._载荷.get("百分比数值", 0.0) or 0.0)
        百分比值 = 百分比目标 * 数值t

        行右x = px(442)
        self._绘制右侧数值(屏幕, 行右x, py(147), str(miss值), (166, 19, 27))
        self._绘制右侧数值(屏幕, 行右x, py(194), str(good值), (49, 74, 25))
        self._绘制右侧数值(屏幕, 行右x, py(241), str(cool值), (12, 9, 69))
        self._绘制右侧数值(屏幕, 行右x, py(289), str(perfect值), (113, 19, 61))
        self._绘制右侧数值(屏幕, 行右x, py(336), str(combo值), (56, 33, 113))
        self._绘制右侧数值(屏幕, 行右x, py(390), f"{百分比值:05.2f}%", (223, 193, 61))

        总分标签 = self._总分标签字体.render("", True, (245, 245, 255))
        屏幕.blit(总分标签, 总分标签.get_rect(center=(px(176), py(450))))
        self._绘制纯色文本(
            屏幕,
            str(int(分数字)),
            self._总分数字字体,
            (255, 255, 255),
            (px(340), py(452)),
        )

        self._绘制评级动画(屏幕, 面板矩形, 经过秒)
        self._绘制顶部状态动画(屏幕, 面板矩形, 经过秒)
        self._绘制新纪录提示(屏幕, 面板矩形, 经过秒)

    def _绘制封面区域(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        pygame.draw.rect(屏幕, (20, 20, 20), 区域)
        if self._封面图 is not None:
            图 = self._缩放cover图(self._封面图, 区域.size)
            if 图 is not None:
                rr = 图.get_rect(center=区域.center)
                屏幕.blit(图, rr.topleft)
                return
        占位 = self._占位字体.render("NO IMAGE", True, (230, 230, 230))
        屏幕.blit(占位, 占位.get_rect(center=区域.center))

    def _绘制右侧数值(
        self,
        屏幕: pygame.Surface,
        右x: int,
        中心y: int,
        文本: str,
        颜色: Tuple[int, int, int],
    ):
        self._绘制纯色文本(
            屏幕, 文本, self._数值字体, 颜色, (int(右x), int(中心y)), 右对齐=True
        )

    def _绘制纯色文本(
        self,
        屏幕: pygame.Surface,
        文本: str,
        字体: pygame.font.Font,
        颜色: Tuple[int, int, int],
        中心: Tuple[int, int],
        右对齐: bool = False,
    ):
        if not 文本:
            return
        try:
            图 = 字体.render(str(文本), True, 颜色).convert_alpha()
        except Exception:
            return
        if 右对齐:
            x = int(中心[0] - 图.get_width())
            y = int(中心[1] - 图.get_height() // 2)
        else:
            x = int(中心[0] - 图.get_width() // 2)
            y = int(中心[1] - 图.get_height() // 2)
        屏幕.blit(图, (x, y))

    def _绘制评级动画(self, 屏幕: pygame.Surface, 面板矩形: pygame.Rect, 经过秒: float):
        if self._评级图 is None:
            return
        开始秒 = self._数值动画秒
        进度 = _夹取((经过秒 - 开始秒) / float(self._评级砸入秒), 0.0, 1.0)
        if 进度 <= 0.0:
            return

        目标宽 = int(面板矩形.w * 0.25)
        比例 = float(self._评级图.get_height()) / float(
            max(1, self._评级图.get_width())
        )
        目标高 = int(目标宽 * 比例)

        动画缩放 = 1.0 + (1.30 - 1.0) * (1.0 - _回弹(进度))
        动画宽 = max(2, int(目标宽 * 动画缩放))
        动画高 = max(2, int(目标高 * 动画缩放))
        图 = self._缩放图(self._评级图, (动画宽, 动画高))
        if 图 is None:
            return

        alpha = int(255 * _缓出三次方(进度))
        try:
            图 = 图.copy()
            图.set_alpha(alpha)
        except Exception:
            pass

        目标中心 = (
            面板矩形.left + int(面板矩形.w * (100.0 / 512.0)),
            面板矩形.top + int(面板矩形.h * (425.0 / 512.0)),
        )
        起始中心x = -动画宽 // 2
        当前中心x = int(起始中心x + (目标中心[0] - 起始中心x) * _回弹(进度))
        当前中心y = int(目标中心[1])
        rr = 图.get_rect(center=(当前中心x, 当前中心y))
        屏幕.blit(图, rr.topleft)

    def _绘制顶部状态动画(
        self, 屏幕: pygame.Surface, 面板矩形: pygame.Rect, 经过秒: float
    ):
        if self._全连图 is None:
            return
        if not bool(self._载荷.get("是否全连", False)):
            return
        开始秒 = self._数值动画秒 + self._评级砸入秒
        进度 = _夹取((经过秒 - 开始秒) / float(self._顶部砸入秒), 0.0, 1.0)
        if 进度 <= 0.0:
            return

        目标宽 = int(面板矩形.w * 0.72)
        比例 = float(self._全连图.get_height()) / float(
            max(1, self._全连图.get_width())
        )
        目标高 = int(目标宽 * 比例)
        缩放 = 1.0 + (1.30 - 1.0) * (1.0 - _回弹(进度))
        动画宽 = max(2, int(目标宽 * 缩放))
        动画高 = max(2, int(目标高 * 缩放))
        图 = self._缩放图(self._全连图, (动画宽, 动画高))
        if 图 is None:
            return
        try:
            图 = 图.copy()
            图.set_alpha(int(255 * _缓出三次方(进度)))
        except Exception:
            pass

        目标中心 = (面板矩形.centerx, 面板矩形.top + int(面板矩形.h * 0.10))
        起始中心y = 面板矩形.top - 动画高
        当前中心y = int(起始中心y + (目标中心[1] - 起始中心y) * _回弹(进度))
        rr = 图.get_rect(center=(目标中心[0], 当前中心y))
        屏幕.blit(图, rr.topleft)

    def _绘制新纪录提示(
        self, 屏幕: pygame.Surface, 面板矩形: pygame.Rect, 经过秒: float
    ):
        if self._新纪录图 is None:
            return
        if not bool((self._歌曲记录结果 or {}).get("是否新纪录", False)):
            return
        开始秒 = self._数值动画秒 + 0.15
        t = _夹取((经过秒 - 开始秒) / 0.28, 0.0, 1.0)
        if t <= 0.0:
            return
        目标宽 = int(max(120, 面板矩形.w * 0.42))
        比例 = float(self._新纪录图.get_height()) / float(
            max(1, self._新纪录图.get_width())
        )
        目标高 = int(max(40, 目标宽 * 比例))
        缩放 = 0.86 + 0.14 * _回弹(t)
        图 = self._缩放图(self._新纪录图, (int(目标宽 * 缩放), int(目标高 * 缩放)))
        if 图 is None:
            return
        try:
            图 = 图.copy()
            图.set_alpha(int(255 * _缓出三次方(t)))
        except Exception:
            pass
        rr = 图.get_rect(
            center=(
                面板矩形.right - int(面板矩形.w * 0.04),
                面板矩形.top + int(面板矩形.h * 0.11),
            )
        )
        屏幕.blit(图, rr.topleft)

    def _绘制奖励小窗(self, 屏幕: pygame.Surface, 面板矩形: pygame.Rect, 经过秒: float):
        if 经过秒 < float(self._奖励窗出现秒):
            return
        if self._等级窗背景图 is None:
            return

        t = _夹取((经过秒 - float(self._奖励窗出现秒)) / 0.32, 0.0, 1.0)
        屏宽, 屏高 = 屏幕.get_size()
        目标宽 = int(min(max(380, 屏宽 * 0.36), 620))
        目标高 = int(max(190, 目标宽 * 0.50))
        目标x = int(min(屏宽 - 24 - 目标宽, 面板矩形.right + 24))
        目标y = int(面板矩形.centery - 目标高 // 2)
        当前x = int(屏宽 + 12 - (屏宽 + 12 - 目标x) * _回弹(t))

        背景图 = self._缩放图(self._等级窗背景图, (目标宽, 目标高))
        if 背景图 is None:
            return
        try:
            背景图 = 背景图.copy()
            背景图.set_alpha(int(255 * _缓出三次方(t)))
        except Exception:
            pass
        屏幕.blit(背景图, (当前x, 目标y))
        if self._等级窗底图 is not None:
            底图 = self._缩放图(self._等级窗底图, (目标宽, 目标高))
            if 底图 is not None:
                try:
                    底图 = 底图.copy()
                    底图.set_alpha(int(235 * _缓出三次方(t)))
                except Exception:
                    pass
                屏幕.blit(底图, (当前x, 目标y))

        self._绘制经验奖励数字(屏幕, pygame.Rect(当前x, 目标y, 目标宽, 目标高))
        self._绘制经验进度区(屏幕, pygame.Rect(当前x, 目标y, 目标宽, 目标高))
        self._绘制段位区(屏幕, pygame.Rect(当前x, 目标y, 目标宽, 目标高))
        self._绘制升级动画(屏幕, pygame.Rect(当前x, 目标y, 目标宽, 目标高), 经过秒)

    def _绘制经验奖励数字(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        奖励经验 = int((self._奖励数据 or {}).get("经验增加值", 10) or 10)
        文本 = f"+{奖励经验}"
        图列表: List[pygame.Surface] = []
        for ch in 文本:
            图 = self._经验数字图集.get(ch)
            if 图 is not None:
                图列表.append(图)
        if not 图列表:
            self._绘制纯色文本(
                屏幕,
                文本,
                self._数值字体,
                (220, 220, 90),
                (区域.x + int(区域.w * 0.26), 区域.y + int(区域.h * 0.18)),
            )
            return
        目标高 = int(max(30, 区域.h * 0.28))
        x = int(区域.x + 区域.w * 0.09)
        y = int(区域.y + 区域.h * 0.06)
        for 图源 in 图列表:
            比例 = float(目标高) / float(max(1, 图源.get_height()))
            目标宽 = int(max(10, 图源.get_width() * 比例))
            图 = self._缩放图(图源, (目标宽, 目标高))
            if 图 is None:
                continue
            屏幕.blit(图, (x, y))
            x += 图.get_width() - int(目标高 * 0.10)

    def _绘制经验进度区(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        奖励 = self._奖励数据 or {}
        组列表 = [
            ("花式", self._花式经验框图, self._花式经验值图, 0.46),
            ("竞速", self._竞速经验框图, self._竞速经验值图, 0.62),
        ]
        for 模式名, 框图源, 值图源, y比例 in 组列表:
            数据 = (
                奖励.get(模式名, {}) if isinstance(奖励.get(模式名, {}), dict) else {}
            )
            等级 = int(数据.get("等级", 1) or 1)
            经验 = float(max(0.0, min(1.0, float(数据.get("经验", 0.0) or 0.0))))
            行y = int(区域.y + 区域.h * y比例)
            条rect = pygame.Rect(
                int(区域.x + 区域.w * 0.18),
                int(行y - 区域.h * 0.035),
                int(区域.w * 0.58),
                int(max(10, 区域.h * 0.08)),
            )
            self._绘制结算贴图经验条(
                屏幕=屏幕,
                条rect=条rect,
                经验值=经验,
                框图源=框图源,
                值图源=值图源,
            )
            模式图 = self._等级小窗小字体.render(模式名, True, (240, 240, 245))
            屏幕.blit(
                模式图,
                (
                    int(区域.x + 区域.w * 0.05),
                    int(条rect.centery - 模式图.get_height() // 2),
                ),
            )
            lv图 = self._等级小窗字体.render(f"Lv : {等级}", True, (245, 245, 245))
            屏幕.blit(
                lv图, (条rect.right + 8, int(条rect.centery - lv图.get_height() // 2))
            )

    def _绘制结算贴图经验条(
        self,
        屏幕: pygame.Surface,
        条rect: pygame.Rect,
        经验值: float,
        框图源: Optional[pygame.Surface],
        值图源: Optional[pygame.Surface],
    ):
        try:
            经验值 = float(经验值)
        except Exception:
            经验值 = 0.0
        经验值 = max(0.0, min(1.0, float(经验值)))
        圆角 = max(2, int(条rect.h // 2))

        def _圆角遮罩(w: int, h: int, r: int) -> pygame.Surface:
            罩 = pygame.Surface((max(1, int(w)), max(1, int(h))), pygame.SRCALPHA)
            罩.fill((0, 0, 0, 0))
            pygame.draw.rect(
                罩,
                (255, 255, 255, 255),
                pygame.Rect(0, 0, int(w), int(h)),
                border_radius=max(0, int(r)),
            )
            return 罩

        pygame.draw.rect(
            屏幕, (20, 32, 60), 条rect, border_radius=max(4, 条rect.h // 2)
        )

        if 值图源 is not None:
            值图 = self._缩放图(值图源, (条rect.w, 条rect.h))
            if 值图 is not None:
                填充宽 = int(max(0, min(条rect.w, round(条rect.w * 经验值))))
                if 填充宽 > 0:
                    值层 = pygame.Surface((条rect.w, 条rect.h), pygame.SRCALPHA)
                    值层.fill((0, 0, 0, 0))
                    值层.blit(
                        值图,
                        (0, 0),
                        area=pygame.Rect(0, 0, 填充宽, 条rect.h),
                    )
                    值层.blit(
                        _圆角遮罩(条rect.w, 条rect.h, 圆角),
                        (0, 0),
                        special_flags=pygame.BLEND_RGBA_MULT,
                    )
                    屏幕.blit(值层, 条rect.topleft)

        if 框图源 is not None:
            框图 = self._缩放图(框图源, (条rect.w, 条rect.h))
            if 框图 is not None:
                框层 = pygame.Surface((条rect.w, 条rect.h), pygame.SRCALPHA)
                框层.fill((0, 0, 0, 0))
                框层.blit(框图, (0, 0))
                框层.blit(
                    _圆角遮罩(条rect.w, 条rect.h, 圆角),
                    (0, 0),
                    special_flags=pygame.BLEND_RGBA_MULT,
                )
                屏幕.blit(框层, 条rect.topleft)

    def _绘制段位区(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        if self._段位图 is not None:
            图 = self._缩放图(self._段位图, (int(区域.h * 0.28), int(区域.h * 0.28)))
            if 图 is not None:
                rr = 图.get_rect(
                    center=(int(区域.x + 区域.w * 0.18), int(区域.y + 区域.h * 0.82))
                )
                屏幕.blit(图, rr.topleft)
        文本 = self._等级小窗字体.render("当前段位", True, (240, 240, 245))
        屏幕.blit(文本, (int(区域.x + 区域.w * 0.29), int(区域.y + 区域.h * 0.75)))

    def _绘制升级动画(self, 屏幕: pygame.Surface, 区域: pygame.Rect, 经过秒: float):
        奖励 = self._奖励数据 or {}
        if not bool(奖励.get("是否升级", False)):
            return
        开始秒 = float(self._奖励窗出现秒) + 0.15
        t = _夹取((经过秒 - 开始秒) / 0.9, 0.0, 1.0)
        if t <= 0.0:
            return
        中心 = (int(区域.centerx), int(区域.y + 区域.h * 0.24))
        for 键, dx, dy in (
            ("左上", -1.0, -1.0),
            ("右上", 1.0, -1.0),
            ("左下", -1.0, 1.0),
            ("右下", 1.0, 1.0),
        ):
            图源 = self._升级图集.get(键)
            if 图源 is None:
                continue
            距离 = int(区域.h * 0.18 * _缓出三次方(t))
            尺寸 = int(max(32, 区域.h * (0.18 + 0.10 * (1.0 - t))))
            图 = self._缩放图(图源, (尺寸, 尺寸))
            if 图 is None:
                continue
            try:
                图 = 图.copy()
                图.set_alpha(int(255 * (1.0 - t * 0.45)))
            except Exception:
                pass
            rr = 图.get_rect(
                center=(中心[0] + int(dx * 距离), 中心[1] + int(dy * 距离))
            )
            屏幕.blit(图, rr.topleft)
        升级图 = self._升级图集.get("升级")
        if 升级图 is not None:
            宽 = int(max(120, 区域.w * (0.22 + 0.06 * (1.0 - t))))
            高 = int(max(48, 升级图.get_height() * (宽 / max(1, 升级图.get_width()))))
            图 = self._缩放图(升级图, (宽, 高))
            if 图 is not None:
                try:
                    图 = 图.copy()
                    图.set_alpha(int(255 * _缓出三次方(t)))
                except Exception:
                    pass
                rr = 图.get_rect(center=中心)
                屏幕.blit(图, rr.topleft)

    def _绘制裁切文本(
        self,
        屏幕: pygame.Surface,
        文本: str,
        字体: pygame.font.Font,
        颜色: Tuple[int, int, int],
        区域: pygame.Rect,
    ):
        if not 文本:
            return
        图 = 字体.render(str(文本), True, 颜色).convert_alpha()
        if 图.get_width() <= 区域.w:
            rr = 图.get_rect(center=区域.center)
            屏幕.blit(图, rr.topleft)
            return
        裁切 = pygame.Surface((区域.w, 区域.h), pygame.SRCALPHA)
        裁切.blit(图, (0, max(0, (区域.h - 图.get_height()) // 2)))
        屏幕.blit(裁切, 区域.topleft)

    def _绘制发光文本(
        self,
        屏幕: pygame.Surface,
        文本: str,
        字体: pygame.font.Font,
        颜色: Tuple[int, int, int],
        发光色: Tuple[int, int, int],
        中心: Tuple[int, int],
        发光半径: int = 2,
        右对齐: bool = False,
    ):
        if not 文本:
            return
        主图 = 字体.render(str(文本), True, 颜色).convert_alpha()
        发光图 = 字体.render(str(文本), True, 发光色).convert_alpha()
        if 右对齐:
            基准x = int(中心[0] - 主图.get_width())
            基准y = int(中心[1] - 主图.get_height() // 2)
        else:
            基准x = int(中心[0] - 主图.get_width() // 2)
            基准y = int(中心[1] - 主图.get_height() // 2)
        for dx in range(-发光半径, 发光半径 + 1):
            for dy in range(-发光半径, 发光半径 + 1):
                if dx == 0 and dy == 0:
                    continue
                屏幕.blit(发光图, (基准x + dx, 基准y + dy))
        屏幕.blit(主图, (基准x, 基准y))

    def _缩放图(
        self, 图: Optional[pygame.Surface], 尺寸: Tuple[int, int]
    ) -> Optional[pygame.Surface]:
        if 图 is None:
            return None
        目标w = max(2, int(尺寸[0]))
        目标h = max(2, int(尺寸[1]))
        key = (id(图), 目标w, 目标h)
        if key in self._缩放缓存:
            return self._缩放缓存[key]
        try:
            out = pygame.transform.smoothscale(图, (目标w, 目标h)).convert_alpha()
            self._缩放缓存[key] = out
            return out
        except Exception:
            return None

    def _缩放cover图(
        self, 图: Optional[pygame.Surface], 尺寸: Tuple[int, int]
    ) -> Optional[pygame.Surface]:
        if 图 is None:
            return None
        目标w = max(2, int(尺寸[0]))
        目标h = max(2, int(尺寸[1]))
        try:
            ow, oh = 图.get_size()
            比例 = max(
                float(目标w) / float(max(1, ow)), float(目标h) / float(max(1, oh))
            )
            nw = max(2, int(ow * 比例))
            nh = max(2, int(oh * 比例))
            key = (id(图), nw, nh)
            if key not in self._缩放缓存:
                self._缩放缓存[key] = pygame.transform.smoothscale(
                    图, (nw, nh)
                ).convert_alpha()
            return self._缩放缓存[key]
        except Exception:
            return None

    def _绘制cover背景(self, 屏幕: pygame.Surface, 图: Optional[pygame.Surface]):
        if 图 is None:
            return
        try:
            屏宽, 屏高 = 屏幕.get_size()
            ow, oh = 图.get_size()
            比例 = max(float(屏宽) / float(max(1, ow)), float(屏高) / float(max(1, oh)))
            nw = max(2, int(ow * 比例))
            nh = max(2, int(oh * 比例))
            key = (id(图), nw, nh)
            if key not in self._缩放缓存:
                self._缩放缓存[key] = pygame.transform.smoothscale(
                    图, (nw, nh)
                ).convert()
            背景 = self._缩放缓存[key]
            rr = 背景.get_rect(center=(屏宽 // 2, 屏高 // 2))
            屏幕.blit(背景, rr.topleft)
        except Exception:
            pass

    def _绘制结算背景(self, 屏幕: pygame.Surface):
        try:
            if self._背景视频播放器 is not None and hasattr(
                self._背景视频播放器, "读取帧"
            ):
                帧 = self._背景视频播放器.读取帧()
                if isinstance(帧, pygame.Surface):
                    self._绘制cover背景(屏幕, 帧)
                    return
        except Exception:
            pass
        self._绘制cover背景(屏幕, self._背景图)

    def _加载背景视频(self, 视频来源: str):
        视频来源 = str(视频来源 or "").strip()
        self._背景视频路径 = ""
        try:
            if self._背景视频播放器 is not None and hasattr(
                self._背景视频播放器, "关闭"
            ):
                self._背景视频播放器.关闭()
        except Exception:
            pass
        self._背景视频播放器 = None

        if not 视频来源:
            return

        try:
            if os.path.isdir(视频来源):
                from core.视频 import 全局视频顺序循环播放器

                播放器 = 全局视频顺序循环播放器(视频来源)
                播放器.打开(是否重置进度=False)
                self._背景视频播放器 = 播放器
                self._背景视频路径 = str(视频来源)
                return

            if not os.path.isfile(视频来源):
                return

            from core.视频 import 全局视频循环播放器

            播放器 = 全局视频循环播放器(视频来源)
            播放器.打开(是否重置进度=False)
            self._背景视频播放器 = 播放器
            self._背景视频路径 = str(视频来源)
        except Exception:
            self._背景视频播放器 = None
            self._背景视频路径 = ""

    def _加载资源(self):
        根目录 = str((self.上下文.get("资源", {}) or {}).get("根", "") or os.getcwd())

        背景视频路径 = str(self._载荷.get("背景视频路径", "") or "")
        self._加载背景视频(背景视频路径)

        背景路径 = str(self._载荷.get("背景图片路径", "") or "")
        if (not 背景路径) or (not os.path.isfile(背景路径)):
            背景路径 = os.path.join(根目录, "冷资源", "backimages", "选歌界面.png")
        self._背景图 = _安全载图(背景路径, 透明=False)

        self._面板图 = _安全载图(
            os.path.join(根目录, "UI-img", "游戏界面", "结算", "结算背景通用.png")
        )
        self._封面图 = _安全载图(str(self._载荷.get("封面路径", "") or ""))

        评级 = str(self._载荷.get("评级", "F") or "F").strip().lower()
        self._评级图 = _安全载图(
            os.path.join(根目录, "UI-img", "游戏界面", "结算", "评价", f"{评级}.png")
        )
        self._全连图 = _安全载图(
            os.path.join(根目录, "UI-img", "游戏界面", "结算", "评价", "全连.png")
        )
        self._新纪录图 = _安全载图(
            os.path.join(根目录, "UI-img", "游戏界面", "结算", "新纪录.png")
        )

        小窗目录 = os.path.join(根目录, "UI-img", "游戏界面", "结算", "结算等级小窗")
        self._等级窗背景图 = _安全载图(os.path.join(小窗目录, "背景.png"))
        self._等级窗底图 = _安全载图(os.path.join(小窗目录, "UI_I516.png"))
        经验条目录 = os.path.join(根目录, "UI-img", "经验条")
        self._花式经验框图 = _安全载图(os.path.join(经验条目录, "花式经验-框.png"))
        self._花式经验值图 = _安全载图(os.path.join(经验条目录, "花式经验-值.png"))
        self._竞速经验框图 = _安全载图(os.path.join(经验条目录, "竞速经验-框.png"))
        self._竞速经验值图 = _安全载图(os.path.join(经验条目录, "竞速经验-值.png"))
        self._经验数字图集 = {}
        数字目录 = os.path.join(小窗目录, "经验数字")
        for 名称 in ["+", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            图 = _安全载图(os.path.join(数字目录, f"{名称}.png"))
            if 图 is not None:
                self._经验数字图集[名称] = 图
        self._升级图集 = {}
        升级目录 = os.path.join(小窗目录, "升级动画素材")
        for 名称 in ["升级", "左上", "右上", "左下", "右下"]:
            图 = _安全载图(os.path.join(升级目录, f"{名称}.png"))
            if 图 is not None:
                self._升级图集[名称] = 图
        联网图路径 = str(
            (self.上下文.get("资源", {}) or {}).get("投币_联网图标", "") or ""
        )
        self._联网原图 = _安全载图(联网图路径, 透明=True)

    def _绘制底部币值(self, 屏幕: pygame.Surface):
        try:
            字体_credit = (self.上下文.get("字体", {}) or {}).get("投币_credit字")
        except Exception:
            字体_credit = None
        if not isinstance(字体_credit, pygame.font.Font):
            return
        try:
            状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
            投币数 = int((状态 or {}).get("投币数", 0) or 0)
        except Exception:
            投币数 = 0
        try:
            绘制底部联网与信用(
                屏幕=屏幕,
                联网原图=getattr(self, "_联网原图", None),
                字体_credit=字体_credit,
                credit数值=str(max(0, 投币数)),
                文本=f"CREDIT：{max(0, 投币数)}/3",
            )
        except Exception:
            pass

    def _播放结算音效(self):
        self._结算音效时长秒 = 0.0
        self._结算音效播放系统秒 = time.perf_counter()
        try:
            if not pygame.mixer.get_init():
                return
        except Exception:
            return

        根目录 = str((self.上下文.get("资源", {}) or {}).get("根", "") or os.getcwd())
        音效路径 = os.path.join(根目录, "冷资源", "backsound", "结算音效.mp3")
        try:
            if os.path.isfile(音效路径):
                self._结算音效 = pygame.mixer.Sound(音效路径)
                self._结算音效时长秒 = float(self._结算音效.get_length() or 0.0)
                self._结算音效通道 = self._结算音效.play()
        except Exception:
            self._结算音效 = None
            self._结算音效通道 = None
            self._结算音效时长秒 = 0.0

    def _播放结算背景音乐(self):
        if self._已切结算BGM:
            return
        self._已切结算BGM = True
        try:
            状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
        except Exception:
            状态 = {}
        if isinstance(状态, dict) and bool(状态.get("非游戏菜单背景音乐关闭", False)):
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception:
                pass
            return
        根目录 = str((self.上下文.get("资源", {}) or {}).get("根", "") or os.getcwd())
        音乐路径 = os.path.join(根目录, "冷资源", "backsound", "back_music_ui.mp3")
        try:
            if pygame.mixer.get_init() and os.path.isfile(音乐路径):
                pygame.mixer.music.stop()
                pygame.mixer.music.load(音乐路径)
                pygame.mixer.music.play(-1)
        except Exception:
            pass

    def _返回选歌(self):
        状态 = (
            self.上下文.get("状态", {})
            if isinstance(self.上下文.get("状态", {}), dict)
            else {}
        )
        try:
            状态["选歌_类型"] = str(self._载荷.get("类型", "竞速") or "竞速")
            状态["选歌_模式"] = str(self._载荷.get("模式", "竞速") or "竞速")
            状态["选歌_恢复原始索引"] = int(self._载荷.get("选歌原始索引", -1) or -1)
            状态["选歌_恢复详情页"] = False
        except Exception:
            pass
        return {"切换到": "选歌", "禁用黑屏过渡": True}

    def _个人资料路径(self) -> str:
        根目录 = str((self.上下文.get("资源", {}) or {}).get("根", "") or os.getcwd())
        return os.path.join(根目录, "UI-img", "个人中心-个人资料", "个人资料.json")

    def _读取个人资料(self) -> dict:
        路径 = self._个人资料路径()
        if not os.path.isfile(路径):
            return {}
        try:
            return json.loads(open(路径, "r", encoding="utf-8").read())
        except Exception:
            return {}

    def _写入个人资料(self, 数据: dict):
        路径 = self._个人资料路径()
        try:
            os.makedirs(os.path.dirname(路径), exist_ok=True)
            临时 = 路径 + ".tmp"
            with open(临时, "w", encoding="utf-8") as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            os.replace(临时, 路径)
        except Exception:
            pass

    def _段位路径(self, 等级: int) -> str:
        段位 = max(1, min(7, (max(1, min(70, int(等级))) - 1) // 10 + 1))
        return f"UI-img/个人中心-个人资料/等级/{段位}.png"

    def _更新个人资料(self):
        数据 = self._读取个人资料()
        if not 数据:
            数据 = {
                "昵称": "玩家",
                "头像文件": "",
                "统计": {},
                "进度": {
                    "花式": {"等级": 1, "经验": 0.0, "累计歌曲": 0, "累计首数": 0},
                    "竞速": {"等级": 1, "经验": 0.0, "累计歌曲": 0, "累计首数": 0},
                    "最大等级": 70,
                    "段位": self._段位路径(1),
                },
            }

        统计 = 数据.get("统计", {}) if isinstance(数据.get("统计", {}), dict) else {}
        进度 = 数据.get("进度", {}) if isinstance(数据.get("进度", {}), dict) else {}

        曲目名 = str(self._载荷.get("曲目名", "") or "")
        sm路径 = str(self._载荷.get("sm路径", "") or "")
        本局分数 = int(self._载荷.get("本局最高分", 0) or 0)
        本局最大combo = int(self._载荷.get("本局最大combo", 0) or 0)
        歌曲时长秒 = float(self._载荷.get("歌曲时长秒", 0.0) or 0.0)
        是否评价S = bool(self._载荷.get("是否评价S", False))
        模式键 = str(self._载荷.get("类型", "竞速") or "竞速")
        模式键 = (
            "花式"
            if ("花" in 模式键)
            else ("竞速" if ("竞" in 模式键 or not 模式键) else 模式键)
        )
        奖励经验值 = 10

        统计["游玩时长分钟"] = int(统计.get("游玩时长分钟", 0) or 0) + int(
            max(0, math.ceil(歌曲时长秒 / 60.0))
        )
        if 是否评价S:
            统计["累计评价S数"] = int(统计.get("累计评价S数", 0) or 0) + 1
        if 本局最大combo > int(统计.get("最大Combo", 0) or 0):
            统计["最大Combo"] = int(本局最大combo)
            统计["最大Combo曲目"] = 曲目名
        if 本局分数 > int(统计.get("最高分", 0) or 0):
            统计["最高分"] = int(本局分数)
            统计["最高分曲目"] = 曲目名

        花式进度 = dict(进度.get("花式", {}) or {})
        竞速进度 = dict(进度.get("竞速", {}) or {})
        for 模式进度 in (花式进度, 竞速进度):
            模式进度.setdefault("等级", 1)
            模式进度.setdefault("经验", 0.0)
            模式进度.setdefault("累计歌曲", 0)
            模式进度.setdefault("累计首数", 0)

        原模式进度 = dict(花式进度 if 模式键 == "花式" else 竞速进度)
        模式进度 = dict(原模式进度)
        模式进度["累计首数"] = int(模式进度.get("累计首数", 0) or 0) + 1
        模式进度["累计歌曲"] = int(模式进度.get("累计歌曲", 0) or 0) + 1
        当前经验 = float(模式进度.get("经验", 0.0) or 0.0) + 0.10
        当前等级 = int(模式进度.get("等级", 1) or 1)
        while 当前经验 >= 1.0 and 当前等级 < 70:
            当前经验 -= 1.0
            当前等级 += 1
        模式进度["等级"] = int(max(1, min(70, 当前等级)))
        模式进度["经验"] = float(max(0.0, min(1.0, 当前经验)))
        进度[模式键] = 模式进度
        if 模式键 == "花式":
            花式进度 = dict(模式进度)
        else:
            竞速进度 = dict(模式进度)
        进度["花式"] = dict(花式进度)
        进度["竞速"] = dict(竞速进度)

        最高等级 = max(
            int((进度.get("花式", {}) or {}).get("等级", 1) or 1),
            int((进度.get("竞速", {}) or {}).get("等级", 1) or 1),
        )
        进度["最大等级"] = int(max(int(进度.get("最大等级", 1) or 1), 最高等级))
        进度["段位"] = self._段位路径(最高等级)
        数据["统计"] = 统计
        数据["进度"] = 进度
        self._写入个人资料(数据)

        根目录 = str((self.上下文.get("资源", {}) or {}).get("根", "") or os.getcwd())
        self._歌曲记录结果 = 更新歌曲最高分(根目录, sm路径, 曲目名, 本局分数)

        段位相对路径 = str((进度.get("段位", "") or self._段位路径(最高等级))).replace(
            "\\", "/"
        )
        段位绝对路径 = os.path.join(根目录, 段位相对路径.replace("/", os.sep))
        self._段位图 = _安全载图(段位绝对路径)

        self._奖励数据 = {
            "经验增加值": int(奖励经验值),
            "是否升级": bool(
                int(模式进度.get("等级", 1) or 1) > int(原模式进度.get("等级", 1) or 1)
            ),
            "升级模式": 模式键,
            "花式": {
                "等级": int((花式进度 or {}).get("等级", 1) or 1),
                "经验": float((花式进度 or {}).get("经验", 0.0) or 0.0),
            },
            "竞速": {
                "等级": int((竞速进度 or {}).get("等级", 1) or 1),
                "经验": float((竞速进度 or {}).get("经验", 0.0) or 0.0),
            },
            "段位路径": 段位相对路径,
        }
