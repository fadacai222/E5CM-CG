import os
import time
import json
from typing import Optional, Tuple, List, Dict

import pygame

from ui.按钮特效 import 公用按钮点击特效, 公用按钮音效
from ui.场景过渡 import 公用放大过渡器


class 场景_个人资料:
    名称 = "个人资料"

    _设计宽 = 2048
    _设计高 = 1152

    _事件_延迟切场景 = pygame.USEREVENT + 25

    _bbox_上面板 = (130, 170, 1918, 430)
    _bbox_下面板 = (300, 520, 1710, 1030)
    _bbox_离开按钮 = (1740, 835, 1965, 1080)

    def __init__(self, 上下文: dict):
        self.上下文 = 上下文
        资源 = 上下文.get("资源", {})

        self._背景视频 = 上下文.get("背景视频")

        self._遮罩原图 = self._安全加载图片(资源.get("投币_遮罩", ""), 透明=True)
        self._联网原图 = self._安全加载图片(资源.get("投币_联网图标", ""), 透明=True)

        根 = str(资源.get("根", "") or os.getcwd())
        self._资源根 = 根

        self._top栏原图 = self._安全加载图片(
            os.path.join(根, "UI-img", "top栏", "top栏背景.png"), 透明=True
        )

        self._top标题原图 = None
        标题候选 = [
            os.path.join(根, "UI-img", "top栏", "个人中心top标题.png"),
            os.path.join(根, "UI-img", "top栏", "个人中心.png"),
            os.path.join(根, "UI-img", "top栏", "个人中心top标题.jpg"),
        ]
        for 路径 in 标题候选:
            图 = self._安全加载图片(路径, 透明=True)
            if 图 is not None:
                self._top标题原图 = 图
                break

        # ---------- 个人资料目录 / JSON ----------
        self._个人资料目录路径 = os.path.join(根, "UI-img", "个人中心-个人资料")
        self._个人资料json路径 = os.path.join(self._个人资料目录路径, "个人资料.json")

        # ✅ 个人资料页布局覆盖（你挪到这里了）
        self._布局覆盖json路径 = os.path.join(根, "json", "个人资料场景_布局.json")

        # 默认头像（永远保留：没有自定义头像时用它）
        self._默认头像路径 = os.path.join(self._个人资料目录路径, "默认头像.png")
        if not os.path.isfile(self._默认头像路径):
            self._默认头像路径 = os.path.join(self._个人资料目录路径, "默认头像.jpg")
        self._默认头像原图 = self._安全加载图片(self._默认头像路径, 透明=False)

        # 当前头像（会根据 json 的 头像文件 切换）
        self._当前头像原图 = None

        # 段位图标（1.png-7.png）—根据 json 的段位/等级动态加载
        self._等级原图 = None

        self._软件信息装饰原图 = self._安全加载图片(
            os.path.join(根, "UI-img", "个人中心-个人资料", "软件信息.png"),
            透明=True,
        )
        self._上面板背景原图 = self._安全加载图片(
            os.path.join(根, "UI-img", "个人中心-个人资料", "上背景.png"),
            透明=True,
        )
        self._下面板背景原图 = self._安全加载图片(
            os.path.join(根, "UI-img", "个人中心-个人资料", "下背景.png"),
            透明=True,
        )
        self._头像弹窗背景原图 = self._安全加载图片(
            os.path.join(根, "UI-img", "个人中心-个人资料", "头像二次弹窗.png"),
            透明=True,
        )

        经验条目录 = os.path.join(根, "UI-img", "经验条")
        self._花式经验框原图 = self._安全加载图片(
            os.path.join(经验条目录, "花式经验-框.png"),
            透明=True,
        )
        self._花式经验值原图 = self._安全加载图片(
            os.path.join(经验条目录, "花式经验-值.png"),
            透明=True,
        )
        self._竞速经验框原图 = self._安全加载图片(
            os.path.join(经验条目录, "竞速经验-框.png"),
            透明=True,
        )
        self._竞速经验值原图 = self._安全加载图片(
            os.path.join(经验条目录, "竞速经验-值.png"),
            透明=True,
        )
        self._离开按钮原图 = self._安全加载图片(
            os.path.join(根, "UI-img", "个人中心-个人资料", "离开.png"),
            透明=True,
        )


        self.按钮音效 = 公用按钮音效(资源.get("按钮音效", ""))
        self._按钮点击特效 = 公用按钮点击特效()
        self._全屏放大过渡 = 公用放大过渡器(总时长毫秒=320)

        self._按钮特效_截图: Optional[pygame.Surface] = None
        self._按钮特效_rect = pygame.Rect(0, 0, 1, 1)

        self._正在放大切场景 = False
        self._延迟目标场景: Optional[str] = None

        self._缓存尺寸 = (0, 0)
        self._遮罩图 = None

        self._rect_top栏 = pygame.Rect(0, 0, 1, 1)
        self._rect_top标题 = pygame.Rect(0, 0, 1, 1)
        self._top栏图 = None
        self._top标题图 = None

        self._rect_上面板 = pygame.Rect(0, 0, 1, 1)
        self._rect_下面板 = pygame.Rect(0, 0, 1, 1)
        self._rect_离开按钮 = pygame.Rect(0, 0, 1, 1)

        self._头像图 = None
        self._等级图 = None
        self._软件信息装饰图 = None
        self._rect_软件信息装饰 = pygame.Rect(0, 0, 1, 1)
        self._离开按钮图 = None

        # 点击区域（渲染后更新）
        self._rect_昵称_渲染 = pygame.Rect(0, 0, 1, 1)

        # 二次弹窗状态（头像/改名）
        self._弹窗类型 = ""
        self._弹窗按钮: Dict[str, pygame.Rect] = {}
        self._弹窗输入框 = pygame.Rect(0, 0, 1, 1)
        self._弹窗昵称输入激活 = False
        self._弹窗昵称文本 = ""
        self._弹窗昵称预编辑 = ""
        self._头像候选路径列表: List[str] = []
        self._头像候选索引 = 0
        self._头像待导入源路径 = ""
        self._弹窗提示文本 = ""

        # ✅ 进入就默认加载一次布局覆盖（优先新路径；必要时从 _debug 迁移/抽取）
        self._布局覆盖_加载并应用(是否允许迁移=True)

        # 个人资料数据（json）
        self._个人资料数据 = self._个人资料_读取并修复(是否回写=True)
        self._个人资料_刷新头像原图()
        self._个人资料_刷新段位图标()

        self._入场开始 = 0.0
        self._入场时长 = 0.22

    # ---------------- 工具 ----------------

    def _安全加载图片(self, 路径: str, 透明: bool):
        try:
            if (not 路径) or (not os.path.isfile(路径)):
                return None
            图 = pygame.image.load(路径)
            return 图.convert_alpha() if 透明 else 图.convert()
        except Exception:
            return None

    def _cover缩放(
        self, 图片: pygame.Surface, 目标宽: int, 目标高: int
    ) -> pygame.Surface:
        ow, oh = 图片.get_size()
        比例 = max(目标宽 / max(1, ow), 目标高 / max(1, oh))
        nw, nh = max(1, int(ow * 比例)), max(1, int(oh * 比例))
        缩放 = pygame.transform.smoothscale(图片, (nw, nh))
        x = (nw - 目标宽) // 2
        y = (nh - 目标高) // 2
        out = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
        out.blit(缩放, (0, 0), area=pygame.Rect(x, y, 目标宽, 目标高))
        return out

    def _contain缩放(
        self, 图片: pygame.Surface, 目标宽: int, 目标高: int, 透明: bool = True
    ) -> pygame.Surface:
        ow, oh = 图片.get_size()
        比例 = min(目标宽 / max(1, ow), 目标高 / max(1, oh))
        nw, nh = max(1, int(ow * 比例)), max(1, int(oh * 比例))
        缩放 = pygame.transform.smoothscale(图片, (nw, nh))
        画布 = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
        画布.fill((0, 0, 0, 0))
        x = (目标宽 - nw) // 2
        y = (目标高 - nh) // 2
        画布.blit(缩放, (x, y))
        return 画布.convert_alpha() if 透明 else 画布.convert()

    def _缓出(self, t: float) -> float:
        if t < 0.0:
            t = 0.0
        if t > 1.0:
            t = 1.0
        return 1.0 - (1.0 - t) * (1.0 - t)

    def _取设计映射参数(self) -> Tuple[float, float, float]:
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()
        scale = min(
            float(w) / max(1.0, float(self._设计宽)),
            float(h) / max(1.0, float(self._设计高)),
        )
        content_w = float(self._设计宽) * scale
        content_h = float(self._设计高) * scale
        ox = (float(w) - content_w) * 0.5
        oy = (float(h) - content_h) * 0.5
        return float(scale), float(ox), float(oy)

    def _设计rect到屏幕rect(self, 设计rect) -> pygame.Rect:
        x, y, w, h = 设计rect
        scale, ox, oy = self._取设计映射参数()
        sx = int(round(ox + float(x) * scale))
        sy = int(round(oy + float(y) * scale))
        sw = int(round(float(w) * scale))
        sh = int(round(float(h) * scale))
        return pygame.Rect(sx, sy, max(1, sw), max(1, sh))

    def _覆盖值转设计rect(self, 覆盖值) -> pygame.Rect:
        x = int(覆盖值[0])
        y = int(覆盖值[1])
        w = int(覆盖值[2])
        h = int(覆盖值[3])

        坐标模式 = str(getattr(self, "_布局覆盖_坐标模式", "设计") or "设计").strip().lower()
        if 坐标模式 in ("screen", "屏幕"):
            参考宽 = max(1, int(getattr(self, "_布局覆盖_参考宽", 1920) or 1920))
            参考高 = max(1, int(getattr(self, "_布局覆盖_参考高", 1080) or 1080))
            sx = float(self._设计宽) / float(参考宽)
            sy = float(self._设计高) / float(参考高)
            x = int(round(float(x) * sx))
            y = int(round(float(y) * sy))
            w = int(round(float(w) * sx))
            h = int(round(float(h) * sy))

        return pygame.Rect(x, y, w, h)

    def _取覆盖屏幕rect(
        self, 名称: str, 默认: pygame.Rect, 最小边: int = 20
    ) -> pygame.Rect:
        try:
            覆盖 = getattr(self, "_调试_覆盖", {}) or {}
        except Exception:
            覆盖 = {}
        v = 覆盖.get(名称)
        if isinstance(v, list) and len(v) == 4:
            try:
                设计rect = self._覆盖值转设计rect(v)
                屏幕rect = self._设计rect到屏幕rect(
                    (设计rect.x, 设计rect.y, 设计rect.w, 设计rect.h)
                )
                屏幕rect.w = max(int(最小边), int(屏幕rect.w))
                屏幕rect.h = max(int(最小边), int(屏幕rect.h))
                return 屏幕rect
            except Exception:
                pass
        return 默认.copy()

    def _映射到屏幕_rect(self, bbox) -> pygame.Rect:
        l, t, r, b = bbox
        return self._设计rect到屏幕rect((l, t, (r - l), (b - t)))

    def _稿1920rect到屏幕rect(
        self, x: int, y: int, w: int, h: int
    ) -> pygame.Rect:
        sx = float(self._设计宽) / 1920.0
        sy = float(self._设计高) / 1080.0
        设计rect = (
            int(round(float(x) * sx)),
            int(round(float(y) * sy)),
            int(round(float(w) * sx)),
            int(round(float(h) * sy)),
        )
        return self._设计rect到屏幕rect(设计rect)

    def _绘制圆角面板(
        self,
        屏幕: pygame.Surface,
        矩形: pygame.Rect,
        背景alpha: int,
        线宽: int = 2,
        圆角: Optional[int] = None,
    ):
        if 圆角 is None:
            圆角 = 28  # ✅ 默认加大
        圆角 = max(8, int(圆角))
        线宽 = max(1, int(线宽))

        面 = pygame.Surface((矩形.w, 矩形.h), pygame.SRCALPHA)
        面.fill((0, 0, 0, 0))

        pygame.draw.rect(
            面,
            (0, 0, 0, max(0, min(255, int(背景alpha)))),
            pygame.Rect(0, 0, 矩形.w, 矩形.h),
            border_radius=圆角,
        )
        pygame.draw.rect(
            面,
            (150, 150, 150),
            pygame.Rect(0, 0, 矩形.w, 矩形.h),
            width=线宽,
            border_radius=圆角,
        )
        屏幕.blit(面, 矩形.topleft)

    def _取缩放缓存图(
        self, 缓存键: str, 原图: Optional[pygame.Surface], 宽: int, 高: int
    ) -> Optional[pygame.Surface]:
        if 原图 is None:
            return None
        宽 = max(1, int(宽))
        高 = max(1, int(高))

        if not hasattr(self, "_缩放缓存"):
            self._缩放缓存 = {}

        键 = (str(缓存键), 宽, 高)
        已有 = self._缩放缓存.get(键)
        if isinstance(已有, pygame.Surface):
            return 已有

        try:
            图 = pygame.transform.smoothscale(原图, (宽, 高)).convert_alpha()
        except Exception:
            try:
                图 = pygame.transform.scale(原图, (宽, 高)).convert_alpha()
            except Exception:
                return None

        self._缩放缓存[键] = 图
        return 图

    def _取圆角头像图(self, 边: int) -> Optional[pygame.Surface]:
        边 = max(48, int(边))

        原图源 = (
            self._当前头像原图
            if isinstance(self._当前头像原图, pygame.Surface)
            else self._默认头像原图
        )
        if 原图源 is None:
            return None

        if not hasattr(self, "_缩放缓存"):
            self._缩放缓存 = {}

        # ✅ 头像变化后会清缓存，所以这里仍用同一个 key
        键 = ("圆角头像", 边, 边)
        已有 = self._缩放缓存.get(键)
        if isinstance(已有, pygame.Surface):
            return 已有

        try:
            原 = 原图源.convert_alpha()
        except Exception:
            try:
                原 = 原图源.convert()
            except Exception:
                原 = 原图源

        方图 = self._cover缩放(原, 边, 边)
        self._缩放缓存[键] = 方图
        return 方图

    def _渲染字距文本面(
        self,
        文本: str,
        字体: pygame.font.Font,
        颜色: Tuple[int, int, int],
        字距: int,
    ) -> pygame.Surface:
        """
        按字符渲染，模拟 tracking（每个字之间的间距）。
        注意：比 Font.render 慢，但页面文字量不大可接受。
        """
        文本 = str(文本 or "")
        文本 = 文本.replace("\n", " ")

        try:
            字距 = int(字距)
        except Exception:
            字距 = 0
        字距 = max(0, min(80, 字距))

        if not 文本:
            return pygame.Surface((1, 1), pygame.SRCALPHA)

        # 简单缓存：避免每帧重复拼字（字体对象 id + 文本 + 颜色 + 字距）
        if not hasattr(self, "_字距文本缓存"):
            self._字距文本缓存 = {}
        缓存键 = (id(字体), 文本, 颜色[0], 颜色[1], 颜色[2], 字距)
        已有 = self._字距文本缓存.get(缓存键)
        if isinstance(已有, pygame.Surface):
            return 已有

        # 计算尺寸
        总宽 = 0
        最大高 = 0
        字宽列表 = []
        for ch in 文本:
            try:
                w, h = 字体.size(ch)
            except Exception:
                w, h = (0, 0)
            字宽列表.append(max(0, int(w)))
            最大高 = max(最大高, int(h))

        for i, w in enumerate(字宽列表):
            总宽 += w
            if i != len(字宽列表) - 1:
                总宽 += 字距

        总宽 = max(1, int(总宽))
        最大高 = max(1, int(最大高))

        面 = pygame.Surface((总宽, 最大高), pygame.SRCALPHA)
        面.fill((0, 0, 0, 0))

        x = 0
        for i, ch in enumerate(文本):
            try:
                字面 = 字体.render(ch, True, 颜色)
            except Exception:
                字面 = None
            if 字面 is not None:
                面.blit(字面, (x, 0))
                x += 字面.get_width()
            else:
                x += 字宽列表[i]
            if i != len(文本) - 1:
                x += 字距

        self._字距文本缓存[缓存键] = 面
        return 面

    def _绘制文本(
        self,
        屏幕: pygame.Surface,
        文本: str,
        字体: pygame.font.Font,
        颜色: Tuple[int, int, int],
        位置,
        对齐: str,
        字距: Optional[int] = None,
    ):
        样式 = getattr(self, "_调试_样式", None)
        if 字距 is None:
            # 默认走全局字距
            try:
                if isinstance(样式, dict):
                    字距 = int(样式.get("全局字距", 1))
                else:
                    字距 = 1
            except Exception:
                字距 = 1

        字距 = max(0, min(80, int(字距)))

        if 字距 <= 0:
            文面 = 字体.render(str(文本), True, 颜色)
        else:
            文面 = self._渲染字距文本面(str(文本), 字体, 颜色, 字距)

        r = 文面.get_rect()
        setattr(r, 对齐, 位置)
        屏幕.blit(文面, r.topleft)
        return r

    def _绘制自动换行(
        self,
        屏幕: pygame.Surface,
        文本: str,
        字体: pygame.font.Font,
        颜色: Tuple[int, int, int],
        区域: pygame.Rect,
        行距: int = 4,
        字距: Optional[int] = None,
    ):
        文本 = str(文本 or "")
        if not 文本:
            return

        样式 = getattr(self, "_调试_样式", None)
        if 字距 is None:
            try:
                if isinstance(样式, dict):
                    字距 = int(样式.get("全局字距", 1))
                else:
                    字距 = 1
            except Exception:
                字距 = 1
        字距 = max(0, min(80, int(字距)))

        # 逐字构建换行（支持字距的宽度累加）
        行列表: List[str] = []
        当前行 = ""
        当前宽 = 0

        for ch in 文本:
            if ch == "\n":
                行列表.append(当前行)
                当前行 = ""
                当前宽 = 0
                continue

            try:
                字宽, _字高 = 字体.size(ch)
            except Exception:
                字宽 = 0
            字宽 = max(0, int(字宽))

            新宽 = 当前宽 + (字距 if 当前行 else 0) + 字宽
            if (当前行 == "") or (新宽 <= 区域.w):
                当前行 += ch
                当前宽 = 新宽
            else:
                行列表.append(当前行)
                当前行 = ch
                当前宽 = 字宽

        if 当前行:
            行列表.append(当前行)

        y = int(区域.y)
        行距 = int(行距)

        for 行 in 行列表:
            if y > 区域.bottom - 2:
                break

            if 字距 <= 0:
                文面 = 字体.render(行, True, 颜色)
            else:
                文面 = self._渲染字距文本面(行, 字体, 颜色, 字距)

            屏幕.blit(文面, (区域.x, y))
            y += int(文面.get_height()) + 行距

    def _绘制进度条(
        self,
        屏幕: pygame.Surface,
        区域: pygame.Rect,
        进度: float,
        边框色: Tuple[int, int, int],
    ):
        try:
            进度 = float(进度)
        except Exception:
            进度 = 0.0
        进度 = 0.0 if 进度 < 0.0 else (1.0 if 进度 > 1.0 else 进度)

        圆角 = max(10, int(区域.h * 0.45))

        # ✅ 边框更细（原来 0.18 太粗）
        线宽 = max(1, int(区域.h * 0.10))

        底面 = pygame.Surface((区域.w, 区域.h), pygame.SRCALPHA)
        底面.fill((0, 0, 0, 0))
        pygame.draw.rect(
            底面, (0, 0, 0, 120), pygame.Rect(0, 0, 区域.w, 区域.h), border_radius=圆角
        )
        pygame.draw.rect(
            底面,
            边框色,
            pygame.Rect(0, 0, 区域.w, 区域.h),
            width=线宽,
            border_radius=圆角,
        )

        内 = pygame.Rect(
            线宽, 线宽, max(1, 区域.w - 线宽 * 2), max(1, 区域.h - 线宽 * 2)
        )
        内.w = max(1, int(内.w * 进度))
        pygame.draw.rect(
            底面,
            (边框色[0], 边框色[1], 边框色[2], 110),
            内,
            border_radius=max(8, 圆角 - 4),
        )
        屏幕.blit(底面, 区域.topleft)

    def _绘制贴图进度条(
        self,
        屏幕: pygame.Surface,
        区域: pygame.Rect,
        进度: float,
        框原图: Optional[pygame.Surface],
        值原图: Optional[pygame.Surface],
        缓存前缀: str,
        透明: int = 255,
    ):
        try:
            进度 = float(进度)
        except Exception:
            进度 = 0.0
        进度 = 0.0 if 进度 < 0.0 else (1.0 if 进度 > 1.0 else 进度)
        圆角 = max(2, int(区域.h // 2))

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

        绘制了贴图 = False
        if isinstance(值原图, pygame.Surface):
            值图 = self._取缩放缓存图(
                f"{缓存前缀}_值", 值原图, 区域.w, 区域.h
            )
            if isinstance(值图, pygame.Surface):
                填充宽 = int(max(0, min(区域.w, round(float(区域.w) * float(进度)))))
                if 填充宽 > 0:
                    值层 = pygame.Surface((区域.w, 区域.h), pygame.SRCALPHA)
                    值层.fill((0, 0, 0, 0))
                    if 透明 < 255:
                        值图 = 值图.copy()
                        值图.set_alpha(max(0, min(255, int(透明))))
                    值层.blit(
                        值图,
                        (0, 0),
                        area=pygame.Rect(0, 0, int(填充宽), int(区域.h)),
                    )
                    值层.blit(
                        _圆角遮罩(区域.w, 区域.h, 圆角),
                        (0, 0),
                        special_flags=pygame.BLEND_RGBA_MULT,
                    )
                    屏幕.blit(值层, 区域.topleft)
                    绘制了贴图 = True

        if isinstance(框原图, pygame.Surface):
            框图 = self._取缩放缓存图(
                f"{缓存前缀}_框", 框原图, 区域.w, 区域.h
            )
            if isinstance(框图, pygame.Surface):
                if 透明 < 255:
                    框图 = 框图.copy()
                    框图.set_alpha(max(0, min(255, int(透明))))
                框层 = pygame.Surface((区域.w, 区域.h), pygame.SRCALPHA)
                框层.fill((0, 0, 0, 0))
                框层.blit(框图, (0, 0))
                框层.blit(
                    _圆角遮罩(区域.w, 区域.h, 圆角),
                    (0, 0),
                    special_flags=pygame.BLEND_RGBA_MULT,
                )
                屏幕.blit(框层, 区域.topleft)
                绘制了贴图 = True

        if not 绘制了贴图:
            self._绘制进度条(屏幕, 区域, 进度=进度, 边框色=(220, 220, 220))

    def _扫描头像候选路径(self) -> List[str]:
        结果: List[str] = []
        默认 = self._个人资料_规范化头像路径(
            "UI-img/个人中心-个人资料/默认头像.png"
        )
        if 默认 not in 结果:
            结果.append(默认)

        try:
            for fn in sorted(os.listdir(self._个人资料目录路径)):
                小写 = fn.lower()
                if not (
                    小写.endswith(".png")
                    or 小写.endswith(".jpg")
                    or 小写.endswith(".jpeg")
                    or 小写.endswith(".bmp")
                    or 小写.endswith(".webp")
                ):
                    continue
                相对 = self._个人资料_规范化头像路径(
                    f"UI-img/个人中心-个人资料/{fn}"
                )
                if 相对 not in 结果:
                    结果.append(相对)
        except Exception:
            pass
        return 结果

    def _打开头像二次弹窗(self):
        try:
            pygame.key.stop_text_input()
        except Exception:
            pass
        self._弹窗类型 = "头像"
        self._弹窗提示文本 = ""
        self._弹窗按钮 = {}
        self._头像待导入源路径 = ""
        self._头像候选路径列表 = self._扫描头像候选路径()
        当前路径 = self._个人资料_规范化头像路径(
            (self._个人资料数据 or {}).get(
                "头像文件", "UI-img/个人中心-个人资料/默认头像.png"
            )
        )
        try:
            self._头像候选索引 = self._头像候选路径列表.index(当前路径)
        except Exception:
            self._头像候选索引 = 0

    def _打开昵称二次弹窗(self):
        self._弹窗类型 = "昵称"
        self._弹窗提示文本 = ""
        self._弹窗按钮 = {}
        self._弹窗昵称输入激活 = True
        self._弹窗昵称文本 = str(
            (self._个人资料数据 or {}).get("昵称", "玩家昵称") or "玩家昵称"
        )
        self._弹窗昵称预编辑 = ""
        try:
            pygame.key.start_text_input()
        except Exception:
            pass

    def _关闭二次弹窗(self):
        self._弹窗类型 = ""
        self._弹窗按钮 = {}
        self._弹窗提示文本 = ""
        self._弹窗昵称输入激活 = False
        self._弹窗昵称预编辑 = ""
        self._头像待导入源路径 = ""
        try:
            pygame.key.stop_text_input()
        except Exception:
            pass

    def _应用头像路径(self, 新路径: str):
        数据 = (
            self._个人资料数据
            if isinstance(getattr(self, "_个人资料数据", None), dict)
            else self._个人资料_默认数据()
        )
        标准路径 = self._个人资料_规范化头像路径(新路径)
        数据["头像文件"] = 标准路径
        self._个人资料数据 = self._个人资料_读取并修复(是否回写=False)
        self._个人资料数据["头像文件"] = 标准路径
        self._个人资料_保存(self._个人资料数据)
        self._个人资料_刷新头像原图()
        self._确保缓存()

    def _导入外部头像并应用(self, 源路径: str) -> bool:
        路径 = str(源路径 or "").strip()
        if (not 路径) or (not os.path.isfile(路径)):
            return False

        try:
            os.makedirs(self._个人资料目录路径, exist_ok=True)
        except Exception:
            pass

        try:
            图 = pygame.image.load(路径)
            try:
                图 = 图.convert_alpha()
            except Exception:
                图 = 图.convert()
        except Exception:
            return False

        新文件名 = f"头像_{int(time.time())}.png"
        目标路径 = os.path.join(self._个人资料目录路径, 新文件名)
        try:
            pygame.image.save(图, 目标路径)
        except Exception:
            return False

        # 删除旧头像文件（仅删除个人资料目录下的历史头像文件）
        try:
            当前头像值 = str((self._个人资料数据 or {}).get("头像文件", "") or "")
            旧文件名 = os.path.basename(当前头像值)
            if 旧文件名.lower().startswith("头像_") and 旧文件名 != 新文件名:
                旧路径 = os.path.join(self._个人资料目录路径, 旧文件名)
                if os.path.isfile(旧路径):
                    os.remove(旧路径)
        except Exception:
            pass

        self._应用头像路径(f"UI-img/个人中心-个人资料/{新文件名}")
        return True

    def _应用昵称(self, 新昵称: str):
        文本 = str(新昵称 or "").strip()
        if not 文本:
            return
        if len(文本) > 16:
            文本 = 文本[:16]
        数据 = (
            self._个人资料数据
            if isinstance(getattr(self, "_个人资料数据", None), dict)
            else self._个人资料_默认数据()
        )
        数据["昵称"] = 文本
        self._个人资料数据 = self._个人资料_读取并修复(是否回写=False)
        self._个人资料数据["昵称"] = 文本
        self._个人资料_保存(self._个人资料数据)
        try:
            self._缓存尺寸 = (0, 0)
        except Exception:
            pass

    def _弹窗_取头像预览图(self, 边长: int) -> Optional[pygame.Surface]:
        路径 = ""
        if self._头像待导入源路径 and os.path.isfile(self._头像待导入源路径):
            路径 = str(self._头像待导入源路径)
        else:
            if not self._头像候选路径列表:
                return None
            idx = max(0, min(len(self._头像候选路径列表) - 1, int(self._头像候选索引)))
            路径 = self._个人资料_取资源绝对路径(self._头像候选路径列表[idx])
        原图 = self._安全加载图片(路径, 透明=True)
        if 原图 is None:
            return None
        try:
            原图 = 原图.convert_alpha()
        except Exception:
            pass
        方图 = self._cover缩放(原图, int(边长), int(边长))
        return self._contain缩放(方图, int(边长), int(边长), 透明=True)

    def _绘制二次弹窗(self, 屏幕: pygame.Surface):
        if not self._弹窗类型:
            return

        w, h = 屏幕.get_size()
        暗层 = pygame.Surface((w, h), pygame.SRCALPHA)
        暗层.fill((0, 0, 0, 160))
        屏幕.blit(暗层, (0, 0))
        self._弹窗按钮 = {}

        if self._弹窗类型 == "头像":
            from core.工具 import 获取字体

            基准rect = self._设计rect到屏幕rect((0, 0, 608, 301))
            主rect = pygame.Rect(
                0,
                0,
                int(max(300, min(w - 20, 基准rect.w))),
                int(max(160, min(h - 20, 基准rect.h))),
            )
            主rect.center = (w // 2, h // 2)
            比例x = float(主rect.w) / 608.0
            比例y = float(主rect.h) / 301.0

            def _弹窗内rect(rx: float, ry: float, rw: float, rh: float) -> pygame.Rect:
                return pygame.Rect(
                    int(round(float(主rect.x) + float(rx) * 比例x)),
                    int(round(float(主rect.y) + float(ry) * 比例y)),
                    max(8, int(round(float(rw) * 比例x))),
                    max(8, int(round(float(rh) * 比例y))),
                )

            if isinstance(self._头像弹窗背景原图, pygame.Surface):
                背景图 = self._取缩放缓存图(
                    "头像二次弹窗背景",
                    self._头像弹窗背景原图,
                    主rect.w,
                    主rect.h,
                )
                if isinstance(背景图, pygame.Surface):
                    屏幕.blit(背景图, 主rect.topleft)
            else:
                pygame.draw.rect(
                    屏幕, (18, 34, 72), 主rect, border_radius=max(14, 主rect.w // 34)
                )
                pygame.draw.rect(
                    屏幕,
                    (160, 186, 232),
                    主rect,
                    width=max(2, 主rect.w // 240),
                    border_radius=max(14, 主rect.w // 34),
                )

            预览rect = _弹窗内rect(254, 89, 100, 100)
            预览图 = self._弹窗_取头像预览图(max(24, min(预览rect.w, 预览rect.h)))
            if isinstance(预览图, pygame.Surface):
                if 预览图.get_size() != (预览rect.w, 预览rect.h):
                    预览图 = self._取缩放缓存图(
                        "头像弹窗预览", 预览图, 预览rect.w, 预览rect.h
                    )
                if isinstance(预览图, pygame.Surface):
                    屏幕.blit(预览图, 预览rect.topleft)

            打开目录 = _弹窗内rect(91, 218, 118, 40)
            返回 = _弹窗内rect(253, 218, 117, 40)
            确定 = _弹窗内rect(402, 214, 116, 42)

            说明字 = 获取字体(max(12, int(主rect.h * 0.060)), 是否粗体=False)
            if self._弹窗提示文本:
                提示 = 说明字.render(self._弹窗提示文本, True, (255, 230, 120))
                屏幕.blit(
                    提示,
                    提示.get_rect(
                        center=(主rect.centerx, 主rect.bottom - int(主rect.h * 0.08))
                    ),
                )

            self._弹窗按钮 = {
                "头像_预览": 预览rect,
                "头像_打开目录": 打开目录,
                "头像_确定": 确定,
                "头像_返回": 返回,
                "头像_区域": 主rect,
            }
            return

        if self._弹窗类型 == "昵称":
            主rect = self._设计rect到屏幕rect((710, 355, 500, 250))
            pygame.draw.rect(
                屏幕, (18, 34, 72), 主rect, border_radius=max(14, 主rect.w // 28)
            )
            pygame.draw.rect(
                屏幕,
                (160, 186, 232),
                主rect,
                width=max(2, 主rect.w // 220),
                border_radius=max(14, 主rect.w // 28),
            )

            from core.工具 import 获取字体

            标题字 = 获取字体(max(18, int(主rect.h * 0.13)), 是否粗体=True)
            按钮字 = 获取字体(max(13, int(主rect.h * 0.10)), 是否粗体=False)
            输入字 = 获取字体(max(14, int(主rect.h * 0.12)), 是否粗体=False)

            标题 = 标题字.render("修改昵称", True, (245, 245, 250))
            屏幕.blit(
                标题,
                标题.get_rect(
                    midtop=(主rect.centerx, 主rect.y + max(12, int(主rect.h * 0.10)))
                ),
            )

            输入框 = pygame.Rect(
                主rect.x + int(主rect.w * 0.10),
                主rect.y + int(主rect.h * 0.36),
                int(主rect.w * 0.80),
                int(主rect.h * 0.22),
            )
            self._弹窗输入框 = 输入框
            try:
                pygame.key.set_text_input_rect(输入框)
            except Exception:
                pass
            pygame.draw.rect(
                屏幕,
                (12, 22, 45),
                输入框,
                border_radius=max(8, 输入框.h // 4),
            )
            pygame.draw.rect(
                屏幕,
                (120, 175, 240) if self._弹窗昵称输入激活 else (90, 120, 170),
                输入框,
                width=2,
                border_radius=max(8, 输入框.h // 4),
            )

            光标闪烁 = bool(self._弹窗昵称输入激活 and int(time.time() * 2) % 2 == 0)
            主文本 = str(self._弹窗昵称文本 or "")
            预编辑 = str(self._弹窗昵称预编辑 or "")
            基础x = int(输入框.x + 10)
            基础y = int(输入框.centery)

            主图 = 输入字.render(主文本, True, (240, 240, 250))
            屏幕.blit(主图, (基础x, int(基础y - 主图.get_height() // 2)))

            预编辑x = int(基础x + 主图.get_width())
            if 预编辑:
                预图 = 输入字.render(预编辑, True, (142, 196, 255))
                屏幕.blit(预图, (预编辑x, int(基础y - 预图.get_height() // 2)))
                预编辑x += int(预图.get_width())

            if 光标闪烁:
                光标图 = 输入字.render("|", True, (240, 240, 250))
                屏幕.blit(光标图, (预编辑x, int(基础y - 光标图.get_height() // 2)))

            确定 = pygame.Rect(
                主rect.x + int(主rect.w * 0.58),
                主rect.bottom - int(主rect.h * 0.22),
                int(主rect.w * 0.16),
                int(主rect.h * 0.13),
            )
            返回 = pygame.Rect(
                主rect.x + int(主rect.w * 0.77),
                主rect.bottom - int(主rect.h * 0.22),
                int(主rect.w * 0.16),
                int(主rect.h * 0.13),
            )
            for r, t in ((确定, "确定"), (返回, "返回")):
                pygame.draw.rect(
                    屏幕, (42, 73, 128), r, border_radius=max(8, r.h // 3)
                )
                pygame.draw.rect(
                    屏幕, (160, 194, 246), r, width=2, border_radius=max(8, r.h // 3)
                )
                文 = 按钮字.render(t, True, (245, 245, 250))
                屏幕.blit(文, 文.get_rect(center=r.center))

            self._弹窗按钮 = {
                "昵称_输入框": 输入框,
                "昵称_确定": 确定,
                "昵称_返回": 返回,
                "昵称_区域": 主rect,
            }

    def _处理二次弹窗事件(self, 事件) -> bool:
        if not self._弹窗类型:
            return False

        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
            self._关闭二次弹窗()
            return True

        if self._弹窗类型 == "头像":
            if 事件.type == pygame.KEYDOWN:
                if 事件.key in (pygame.K_LEFT, pygame.K_a):
                    self._头像待导入源路径 = ""
                    if self._头像候选路径列表:
                        self._头像候选索引 = (
                            self._头像候选索引 - 1
                        ) % len(self._头像候选路径列表)
                    return True
                if 事件.key in (pygame.K_RIGHT, pygame.K_d):
                    self._头像待导入源路径 = ""
                    if self._头像候选路径列表:
                        self._头像候选索引 = (
                            self._头像候选索引 + 1
                        ) % len(self._头像候选路径列表)
                    return True
                if 事件.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self._头像待导入源路径:
                        if self._导入外部头像并应用(self._头像待导入源路径):
                            self._关闭二次弹窗()
                        else:
                            self._弹窗提示文本 = "导入失败，请更换图片"
                    elif self._头像候选路径列表:
                        idx = max(
                            0,
                            min(
                                len(self._头像候选路径列表) - 1,
                                int(self._头像候选索引),
                            ),
                        )
                        self._应用头像路径(self._头像候选路径列表[idx])
                        self._关闭二次弹窗()
                    return True

            if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
                pos = 事件.pos
                区域rect = self._弹窗按钮.get("头像_区域")
                if isinstance(区域rect, pygame.Rect) and (not 区域rect.collidepoint(pos)):
                    self._关闭二次弹窗()
                    return True
                for 键, rect in self._弹窗按钮.items():
                    if not isinstance(rect, pygame.Rect):
                        continue
                    if not rect.collidepoint(pos):
                        continue
                    if 键 == "头像_预览":
                        self._头像待导入源路径 = ""
                        if self._头像候选路径列表:
                            self._头像候选索引 = (
                                self._头像候选索引 + 1
                            ) % len(self._头像候选路径列表)
                    elif 键 == "头像_打开目录":
                        选中路径 = self._弹窗_选择图片文件()
                        if 选中路径 and os.path.isfile(选中路径):
                            self._头像待导入源路径 = str(选中路径)
                            self._弹窗提示文本 = "已选择图片，点确定应用"
                    elif 键 == "头像_确定":
                        if self._头像待导入源路径:
                            if self._导入外部头像并应用(self._头像待导入源路径):
                                self._关闭二次弹窗()
                            else:
                                self._弹窗提示文本 = "导入失败，请更换图片"
                        elif self._头像候选路径列表:
                            idx = max(
                                0,
                                min(
                                    len(self._头像候选路径列表) - 1,
                                    int(self._头像候选索引),
                                ),
                            )
                            self._应用头像路径(self._头像候选路径列表[idx])
                            self._关闭二次弹窗()
                    elif 键 == "头像_返回":
                        self._关闭二次弹窗()
                    return True
                return True
            return True

        if self._弹窗类型 == "昵称":
            if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
                pos = 事件.pos
                区域rect = self._弹窗按钮.get("昵称_区域")
                if isinstance(区域rect, pygame.Rect) and (not 区域rect.collidepoint(pos)):
                    self._关闭二次弹窗()
                    return True
                if self._弹窗按钮.get("昵称_输入框", pygame.Rect(0, 0, 0, 0)).collidepoint(
                    pos
                ):
                    self._弹窗昵称输入激活 = True
                    try:
                        pygame.key.start_text_input()
                        pygame.key.set_text_input_rect(self._弹窗输入框)
                    except Exception:
                        pass
                    return True
                if self._弹窗按钮.get("昵称_确定", pygame.Rect(0, 0, 0, 0)).collidepoint(
                    pos
                ):
                    self._应用昵称(self._弹窗昵称文本)
                    self._关闭二次弹窗()
                    return True
                if self._弹窗按钮.get("昵称_返回", pygame.Rect(0, 0, 0, 0)).collidepoint(
                    pos
                ):
                    self._关闭二次弹窗()
                    return True
                return True

            if 事件.type == pygame.TEXTINPUT and self._弹窗昵称输入激活:
                txt = str(getattr(事件, "text", "") or "")
                if txt:
                    新文本 = (self._弹窗昵称文本 or "") + txt
                    self._弹窗昵称文本 = 新文本[:16]
                self._弹窗昵称预编辑 = ""
                return True

            if 事件.type == pygame.TEXTEDITING and self._弹窗昵称输入激活:
                self._弹窗昵称预编辑 = str(getattr(事件, "text", "") or "")
                return True

            if 事件.type == pygame.KEYDOWN:
                if 事件.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._应用昵称(self._弹窗昵称文本)
                    self._关闭二次弹窗()
                    return True
                if 事件.key == pygame.K_BACKSPACE:
                    self._弹窗昵称文本 = str(self._弹窗昵称文本 or "")[:-1]
                    self._弹窗昵称预编辑 = ""
                    return True
                return True
            return True

        return True

    # ---------------- 缓存/布局 ----------------
    def _确保缓存(self):
        from ui.top栏 import 生成top栏

        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()

        # ✅ 允许调试时强制重算：调试器会把 _缓存尺寸 置(0,0)
        if (w, h) == self._缓存尺寸:
            return
        self._缓存尺寸 = (w, h)

        # ✅ 缩放缓存：屏幕尺寸变化时清一次，避免爆内存
        try:
            if hasattr(self, "_缩放缓存"):
                self._缩放缓存 = {}
        except Exception:
            pass

        # 遮罩
        if self._遮罩原图 is not None:
            self._遮罩图 = self._cover缩放(self._遮罩原图, w, h)
        else:
            暗层 = pygame.Surface((w, h), pygame.SRCALPHA)
            暗层.fill((0, 0, 0, 128))
            self._遮罩图 = 暗层

        # top栏
        self._rect_top栏, self._top栏图, self._rect_top标题, self._top标题图 = (
            生成top栏(
                屏幕=屏幕,
                top背景原图=self._top栏原图,
                标题原图=self._top标题原图,
                设计宽=self._设计宽,
                设计高=self._设计高,
                top设计高=150,
                top背景宽占比=1,
                top背景高占比=1,
                标题最大宽占比=0.5,
                标题最大高占比=0.5,
                标题整体缩放=1,
                标题上移比例=0.1,
            )
        )

        # ---------- 三大框（必须可控） ----------
        self._rect_上面板 = self._取覆盖屏幕rect(
            "上面板", self._映射到屏幕_rect(self._bbox_上面板)
        )
        self._rect_下面板 = self._取覆盖屏幕rect(
            "下面板", self._映射到屏幕_rect(self._bbox_下面板)
        )
        self._rect_离开按钮 = self._取覆盖屏幕rect(
            "离开按钮", self._映射到屏幕_rect(self._bbox_离开按钮)
        )

        # ---------- 下方“软件按钮”(可控/可缩放) ----------
        默认软件按钮 = pygame.Rect(
            self._rect_下面板.left + max(18, int(self._rect_下面板.w * 0.02)),
            self._rect_下面板.top - max(28, int(self._rect_下面板.h * 0.10)),
            max(160, int(self._rect_下面板.w * 0.18)),
            max(70, int(self._rect_下面板.h * 0.18)),
        )
        self._rect_软件按钮 = self._取覆盖屏幕rect("软件按钮", 默认软件按钮)

        # ---------- 上面板内部：全部变成可编辑 rect（解决“控件太少”） ----------
        面板 = self._rect_上面板
        内边距 = max(10, int(面板.w * 0.015))
        可用 = pygame.Rect(
            面板.x + 内边距, 面板.y + 内边距, 面板.w - 内边距 * 2, 面板.h - 内边距 * 2
        )

        左宽 = max(200, int(可用.w * 0.10))  # ✅ 左侧占 10%
        左区 = pygame.Rect(可用.x, 可用.y, 左宽, 可用.h)
        右区 = pygame.Rect(
            左区.right + max(8, int(可用.w * 0.01)),
            可用.y,
            可用.w - 左区.w - max(8, int(可用.w * 0.01)),
            可用.h,
        )

        # 头像控件 rect（默认在左区上方）
        头像边 = max(64, min(int(左区.w * 0.92), int(左区.h * 0.56)))
        默认头像 = pygame.Rect(0, 0, 头像边, 头像边)
        默认头像.midtop = (左区.centerx, 左区.y + max(2, int(左区.h * 0.02)))
        self._rect_头像控件 = self._取覆盖屏幕rect("头像控件", 默认头像)

        # 昵称锚点（作为文本起点）
        默认昵称 = pygame.Rect(
            self._rect_头像控件.left,
            self._rect_头像控件.bottom + max(4, int(面板.h * 0.02)),
            max(80, self._rect_头像控件.w),
            24,
        )
        self._rect_昵称锚点 = self._取覆盖屏幕rect("昵称锚点", 默认昵称)

        # 等级标识 rect（强制在上面板内，避免被挤出去）
        默认等级 = pygame.Rect(
            self._rect_昵称锚点.left,
            self._rect_昵称锚点.bottom + 6,
            max(120, int(左区.w * 0.95)),
            max(24, int(面板.h * 0.16)),
        )
        默认等级.clamp_ip(面板)  # ✅ 不允许跑出面板
        self._rect_等级标识 = self._取覆盖屏幕rect("等级标识", 默认等级)

        上区 = pygame.Rect(右区.x, 右区.y, 右区.w, int(右区.h * 0.62))
        下区 = pygame.Rect(
            右区.x,
            上区.bottom + max(6, int(右区.h * 0.03)),
            右区.w,
            右区.h - (上区.h + max(6, int(右区.h * 0.03))),
        )

        默认统计 = pygame.Rect(上区.x, 上区.y, int(上区.w * 0.62), 上区.h)
        默认介绍 = pygame.Rect(
            默认统计.right + max(8, int(上区.w * 0.02)),
            上区.y,
            上区.w - 默认统计.w - max(8, int(上区.w * 0.02)),
            上区.h,
        )

        self._rect_统计区 = self._取覆盖屏幕rect("统计区", 默认统计)
        self._rect_介绍区 = self._取覆盖屏幕rect("介绍区", 默认介绍)

        条高 = max(12, int(下区.h * 0.32))
        默认花式条 = pygame.Rect(
            下区.x + int(下区.w * 0.18),
            下区.y + max(2, int(下区.h * 0.08)),
            int(下区.w * 0.66),
            条高,
        )
        默认竞速条 = pygame.Rect(
            默认花式条.x,
            默认花式条.bottom + max(6, int(下区.h * 0.18)),
            默认花式条.w,
            条高,
        )

        self._rect_花式条 = self._取覆盖屏幕rect("花式条", 默认花式条)
        self._rect_竞速条 = self._取覆盖屏幕rect("竞速条", 默认竞速条)

        # ---------- 下面板左右两列（可控） ----------
        面板2 = self._rect_下面板
        内边距2 = max(12, int(面板2.w * 0.02))
        文框 = pygame.Rect(
            面板2.x + 内边距2,
            面板2.y + 内边距2,
            面板2.w - 内边距2 * 2,
            面板2.h - 内边距2 * 2,
        )
        列间距 = max(10, int(文框.w * 0.02))
        默认软件信息 = pygame.Rect(文框.x, 文框.y, int(文框.w * 0.62), 文框.h)
        默认软件说明 = pygame.Rect(
            默认软件信息.right + 列间距,
            文框.y,
            文框.w - 默认软件信息.w - 列间距,
            文框.h,
        )

        self._rect_软件信息 = self._取覆盖屏幕rect("软件信息", 默认软件信息)
        self._rect_软件说明 = self._取覆盖屏幕rect("软件说明", 默认软件说明)

        # ---------- 资源缩放缓存（离开/软件按钮/等级） ----------
        if self._离开按钮原图 is not None:
            self._离开按钮图 = self._contain缩放(
                self._离开按钮原图,
                self._rect_离开按钮.w,
                self._rect_离开按钮.h,
                透明=True,
            )
        else:
            self._离开按钮图 = None

        # ✅ 输出给调试器：控件必须“够多”，否则你点不动/调不了
        self._调试_rect表 = {
            "上面板": self._rect_上面板.copy(),
            "下面板": self._rect_下面板.copy(),
            "离开按钮": self._rect_离开按钮.copy(),
            "软件按钮": self._rect_软件按钮.copy(),
            "头像控件": self._rect_头像控件.copy(),
            "昵称锚点": self._rect_昵称锚点.copy(),
            "等级标识": self._rect_等级标识.copy(),
            "统计区": self._rect_统计区.copy(),
            "介绍区": self._rect_介绍区.copy(),
            "花式条": self._rect_花式条.copy(),
            "竞速条": self._rect_竞速条.copy(),
            "软件信息": self._rect_软件信息.copy(),
            "软件说明": self._rect_软件说明.copy(),
        }

    # ---------------- 生命周期 ----------------
    def 进入(self):
        资源 = self.上下文.get("资源", {})
        状态 = self.上下文.get("状态", {})

        根目录 = str(资源.get("根", "") or os.getcwd())
        排行榜BGM路径 = os.path.join(根目录, "冷资源", "backsound", "排行榜.mp3")

        已经在播排行榜 = False
        try:
            已经在播排行榜 = bool(状态.get("bgm_排行榜_已播放", False))
        except Exception:
            已经在播排行榜 = False

        if (not 已经在播排行榜) and os.path.isfile(排行榜BGM路径):
            try:
                self.上下文["音乐"].播放循环(排行榜BGM路径)
                状态["bgm_排行榜_已播放"] = True
            except Exception:
                pass

        self._入场开始 = time.time()

        self._正在放大切场景 = False
        self._延迟目标场景 = None
        pygame.time.set_timer(self._事件_延迟切场景, 0)

        self._按钮特效_截图 = None
        self._按钮特效_rect = pygame.Rect(0, 0, 1, 1)

        # ✅ 每次进入都默认加载（方便你手动改 json 后立刻生效）
        self._布局覆盖_加载并应用(是否允许迁移=False)

        # ✅ 进入时重新读一次个人资料（可能别的场景更新了 json）
        self._个人资料数据 = self._个人资料_读取并修复(是否回写=False)
        self._个人资料_刷新头像原图()
        self._个人资料_刷新段位图标()

        self._确保缓存()

    def 退出(self):
        pygame.time.set_timer(self._事件_延迟切场景, 0)
        self._关闭二次弹窗()

    def _布局覆盖_加载并应用(self, 是否允许迁移: bool = True):

        # 默认先清空，避免读坏导致残留旧覆盖
        self._调试_覆盖 = {}
        self._调试_样式 = {}
        self._布局覆盖_坐标模式 = "design"
        self._布局覆盖_参考宽 = int(self._设计宽)
        self._布局覆盖_参考高 = int(self._设计高)

        新路径 = str(getattr(self, "_布局覆盖json路径", "") or "")
        if not 新路径:
            return

        try:
            os.makedirs(os.path.dirname(新路径), exist_ok=True)
        except Exception:
            pass

        def _读json(路径: str):
            if (not 路径) or (not os.path.isfile(路径)):
                return None
            try:
                with open(路径, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None

        def _写json(路径: str, 数据: dict):
            try:
                os.makedirs(os.path.dirname(路径), exist_ok=True)
            except Exception:
                pass
            try:
                tmp = 路径 + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(数据, f, ensure_ascii=False, indent=2)
                os.replace(tmp, 路径)
                return True
            except Exception:
                return False

        数据 = _读json(新路径)

        # 迁移：新文件不存在/读不到时，从旧总文件抽取
        if (not isinstance(数据, dict)) and bool(是否允许迁移):
            旧单页路径 = os.path.join(self._个人资料目录路径, "layout_overrides.json")
            旧单页数据 = _读json(旧单页路径)
            if isinstance(旧单页数据, dict):
                _写json(新路径, dict(旧单页数据))
                数据 = _读json(新路径)

        if (not isinstance(数据, dict)) and bool(是否允许迁移):
            旧路径 = os.path.join(
                str(self._资源根 or os.getcwd()), "_debug", "layout_overrides.json"
            )
            旧总 = _读json(旧路径)
            if isinstance(旧总, dict):
                # 旧总文件可能直接就是 {"覆盖","样式"}（单场景）
                if ("覆盖" in 旧总) or ("样式" in 旧总):
                    候选 = 旧总
                else:
                    # 旧总文件是多场景：优先用 key=个人资料 或 类名
                    场景键列表 = []
                    try:
                        场景键列表.append(str(getattr(self, "名称", "") or ""))
                    except Exception:
                        pass
                    场景键列表.extend(["个人资料", self.__class__.__name__])

                    候选 = None
                    for 键 in 场景键列表:
                        if 键 and isinstance(旧总.get(键), dict):
                            候选 = 旧总.get(键)
                            break

                if isinstance(候选, dict) and (("覆盖" in 候选) or ("样式" in 候选)):
                    # 写入新位置（单页文件）
                    _写json(
                        新路径,
                        {
                            "覆盖": 候选.get("覆盖", {}) or {},
                            "样式": 候选.get("样式", {}) or {},
                        },
                    )
                    数据 = _读json(新路径)

        if not isinstance(数据, dict):
            # 新文件仍不存在：创建一个空的，保证路径固定
            _写json(新路径, {"覆盖": {}, "样式": {}})
            数据 = _读json(新路径)

        if not isinstance(数据, dict):
            return

        # 兼容旧格式：若顶层是多场景 dict
        if (("覆盖" not in 数据) and ("样式" not in 数据)) and isinstance(
            数据.get("个人资料"), dict
        ):
            数据 = 数据.get("个人资料")

        覆盖 = {}
        样式 = {}
        坐标模式 = "auto"
        参考宽 = 1920
        参考高 = 1080
        try:
            if isinstance(数据.get("覆盖"), dict):
                覆盖 = dict(数据.get("覆盖"))
            if isinstance(数据.get("样式"), dict):
                样式 = dict(数据.get("样式"))
            坐标模式 = str(数据.get("坐标模式", "auto") or "auto").strip().lower()
            try:
                参考宽 = int(数据.get("参考宽", 1920) or 1920)
            except Exception:
                参考宽 = 1920
            try:
                参考高 = int(数据.get("参考高", 1080) or 1080)
            except Exception:
                参考高 = 1080
        except Exception:
            覆盖 = {}
            样式 = {}
            坐标模式 = "auto"
            参考宽 = 1920
            参考高 = 1080

        # 最基本防御：覆盖必须是 {控件名: [x,y,w,h]}
        过滤后覆盖 = {}
        for k, v in (覆盖 or {}).items():
            if not k:
                continue
            if isinstance(v, list) and len(v) == 4:
                try:
                    过滤后覆盖[str(k)] = [int(v[0]), int(v[1]), int(v[2]), int(v[3])]
                except Exception:
                    continue

        self._调试_覆盖 = 过滤后覆盖
        self._调试_样式 = 样式 if isinstance(样式, dict) else {}
        参考宽 = max(1, int(参考宽))
        参考高 = max(1, int(参考高))
        if 坐标模式 in ("设计", "design"):
            self._布局覆盖_坐标模式 = "design"
            self._布局覆盖_参考宽 = int(self._设计宽)
            self._布局覆盖_参考高 = int(self._设计高)
        elif 坐标模式 in ("屏幕", "screen"):
            self._布局覆盖_坐标模式 = "screen"
            self._布局覆盖_参考宽 = int(参考宽)
            self._布局覆盖_参考高 = int(参考高)
        else:
            # 兼容历史文件：旧数据常是 1920x1080 的屏幕像素坐标。
            最大右 = 0
            最大下 = 0
            for _, rv in self._调试_覆盖.items():
                try:
                    最大右 = max(最大右, int(rv[0]) + int(rv[2]))
                    最大下 = max(最大下, int(rv[1]) + int(rv[3]))
                except Exception:
                    continue
            if 最大右 <= 1930 and 最大下 <= 1090:
                self._布局覆盖_坐标模式 = "screen"
                self._布局覆盖_参考宽 = 1920
                self._布局覆盖_参考高 = 1080
            else:
                self._布局覆盖_坐标模式 = "design"
                self._布局覆盖_参考宽 = int(self._设计宽)
                self._布局覆盖_参考高 = int(self._设计高)

        # 强制下一帧重算布局
        try:
            self._缓存尺寸 = (0, 0)
        except Exception:
            pass

    # ---------------- 切场景（放大过渡） ----------------
    def _开始放大切场景(
        self, 起始图: Optional[pygame.Surface], 起始rect: pygame.Rect, 目标场景名: str
    ):
        if self._正在放大切场景:
            return

        if 起始图 is None:
            self._延迟目标场景 = 目标场景名
            self._正在放大切场景 = False
            pygame.time.set_timer(self._事件_延迟切场景, 1)
            return

        self._正在放大切场景 = True
        self._延迟目标场景 = 目标场景名

        try:
            self._全屏放大过渡.开始(起始图, 起始rect)
        except Exception:
            pygame.time.set_timer(self._事件_延迟切场景, 1)
            return

        pygame.time.set_timer(self._事件_延迟切场景, 320, loops=1)

    # ---------------- 绘制 ----------------
    def 绘制(self):
        from core.工具 import 绘制底部联网与信用, 获取字体

        屏幕 = self.上下文["屏幕"]
        self._确保缓存()
        w, h = 屏幕.get_size()

        屏幕.fill((0, 0, 0))
        帧 = self._背景视频.读取帧() if self._背景视频 else None
        if 帧 is not None:
            背景面 = self._cover缩放(帧, w, h)
            屏幕.blit(背景面, (0, 0))

        if self._遮罩图 is not None:
            屏幕.blit(self._遮罩图, (0, 0))

        if self._top栏图 is not None:
            屏幕.blit(self._top栏图, self._rect_top栏.topleft)
        if self._top标题图 is not None:
            屏幕.blit(self._top标题图, self._rect_top标题.topleft)
        else:
            标题字 = 获取字体(42, 是否粗体=True)  # ✅ 小一点
            self._绘制文本(
                屏幕,
                "个人中心",
                标题字,
                (255, 255, 255),
                (w // 2, self._rect_top栏.centery),
                "center",
            )

        字体_credit = self.上下文["字体"].get("投币_credit字")
        信用 = "0"
        try:
            状态 = self.上下文.get("状态", {})
            信用 = str(int(状态.get("投币数", 0) or 0))
        except Exception:
            信用 = "0"

        绘制底部联网与信用(
            屏幕=屏幕,
            联网原图=self._联网原图,
            字体_credit=字体_credit,
            credit数值=信用,
        )

        t = (time.time() - float(self._入场开始)) / max(0.001, float(self._入场时长))
        t = self._缓出(t)
        面板缩放 = 0.99 + 0.01 * t
        面板透明 = max(0, min(255, int(255 * t)))

        self._绘制_上面板(屏幕, 面板缩放, 面板透明)
        self._绘制_下面板(屏幕, 面板缩放, 面板透明)
        self._绘制_离开按钮(屏幕, 面板透明)
        self._绘制二次弹窗(屏幕)

        # ✅ 如果你的 公用按钮点击特效 有绘制函数，就给它机会画；没有也不会崩
        try:
            if self._按钮特效_截图 is not None:
                if hasattr(self._按钮点击特效, "是否动画中") and hasattr(
                    self._按钮点击特效, "绘制按钮"
                ):
                    if self._按钮点击特效.是否动画中():
                        self._按钮点击特效.绘制按钮(
                            屏幕, self._按钮特效_截图, self._按钮特效_rect
                        )
        except Exception:
            pass

        if self._全屏放大过渡.是否进行中():
            self._全屏放大过渡.更新并绘制(屏幕)

    def _绘制_上面板(self, 屏幕: pygame.Surface, 缩放: float, 透明: int):
        from core.工具 import 获取字体

        if bool(self.上下文.get("布局调试_开启", False)):
            缩放 = 1.0
            透明 = 255

        面板 = self._rect_上面板.copy()
        if abs(缩放 - 1.0) > 0.001:
            面板.w = max(1, int(面板.w * 缩放))
            面板.h = max(1, int(面板.h * 缩放))
            面板.center = self._rect_上面板.center

        if isinstance(self._上面板背景原图, pygame.Surface):
            背景图 = self._取缩放缓存图(
                "个人资料_上背景",
                self._上面板背景原图,
                面板.w,
                面板.h,
            )
            if isinstance(背景图, pygame.Surface):
                try:
                    背景图 = 背景图.copy()
                    背景图.set_alpha(max(0, min(255, int(透明))))
                except Exception:
                    pass
                屏幕.blit(背景图, 面板.topleft)
        else:
            圆角 = 36
            self._绘制圆角面板(屏幕, 面板, 背景alpha=175, 线宽=2, 圆角=圆角)

        样式 = getattr(self, "_调试_样式", None)

        紧凑系数 = 0.78
        if isinstance(样式, dict):
            v = 样式.get("紧凑系数")
            if isinstance(v, (int, float)):
                紧凑系数 = float(v)
        紧凑系数 = 0.55 if 紧凑系数 < 0.55 else (1.10 if 紧凑系数 > 1.10 else 紧凑系数)

        def _取字号(键: str, 默认: int, 下限: int, 上限: int) -> int:
            vv = None
            if isinstance(样式, dict):
                vv = 样式.get(键)
            if isinstance(vv, int):
                return max(下限, min(上限, int(vv)))
            return max(下限, min(上限, int(默认)))

        def _取粗体(键: str, 默认: bool) -> bool:
            vv = None
            if isinstance(样式, dict):
                vv = 样式.get(键)
            if isinstance(vv, bool):
                return bool(vv)
            return bool(默认)

        def _取间距(键: str, 默认: int, 下限: int = 0, 上限: int = 200) -> int:
            vv = None
            if isinstance(样式, dict):
                vv = 样式.get(键)
            if isinstance(vv, int):
                return max(下限, min(上限, int(vv)))
            return max(下限, min(上限, int(默认)))

        def _取行距(键: str, 默认: int, 下限: int = 0, 上限: int = 120) -> int:
            vv = None
            if isinstance(样式, dict):
                vv = 样式.get(键)
            if isinstance(vv, int):
                return max(下限, min(上限, int(vv)))
            return max(下限, min(上限, int(默认)))

        标题白 = (255, 255, 255)
        数值黄 = (255, 220, 80)
        曲目紫 = (190, 140, 255)
        小灰 = (160, 160, 160)

        数据 = (
            self._个人资料数据
            if isinstance(getattr(self, "_个人资料数据", None), dict)
            else {}
        )
        昵称 = str(数据.get("昵称", "玩家昵称") or "玩家昵称")

        统计 = 数据.get("统计", {}) if isinstance(数据.get("统计", {}), dict) else {}
        游玩时长分钟 = int(统计.get("游玩时长分钟", 0) or 0)
        累计评价S数 = int(统计.get("累计评价S数", 0) or 0)
        最大Combo = int(统计.get("最大Combo", 0) or 0)
        最大Combo曲目 = str(统计.get("最大Combo曲目", "") or "")
        最高分 = int(统计.get("最高分", 0) or 0)
        最高分曲目 = str(统计.get("最高分曲目", "") or "")

        进度 = 数据.get("进度", {}) if isinstance(数据.get("进度", {}), dict) else {}
        花式 = 进度.get("花式", {}) if isinstance(进度.get("花式", {}), dict) else {}
        竞速 = 进度.get("竞速", {}) if isinstance(进度.get("竞速", {}), dict) else {}

        花式等级 = int(花式.get("等级", 1) or 1)
        花式经验 = float(花式.get("经验", 0.0) or 0.0)
        竞速等级 = int(竞速.get("等级", 1) or 1)
        竞速经验 = float(竞速.get("经验", 0.0) or 0.0)

        花式经验 = 0.0 if 花式经验 < 0.0 else (1.0 if 花式经验 > 1.0 else 花式经验)
        竞速经验 = 0.0 if 竞速经验 < 0.0 else (1.0 if 竞速经验 > 1.0 else 竞速经验)

        # ================= 左侧：头像/昵称/段位 =================
        头像rect = getattr(self, "_rect_头像控件", pygame.Rect(0, 0, 1, 1))
        头像图 = self._取圆角头像图(min(头像rect.w, 头像rect.h))
        if 头像图 is not None:
            if 头像rect.w != 头像rect.h:
                头像图 = self._取缩放缓存图("头像控件", 头像图, 头像rect.w, 头像rect.h)
            if 头像图 is not None:
                头像图.set_alpha(透明)
                屏幕.blit(头像图, 头像rect.topleft)

        昵称锚点 = getattr(self, "_rect_昵称锚点", pygame.Rect(0, 0, 1, 1))
        昵称字号 = _取字号(
            "昵称字号", 默认=max(14, int(面板.h * 0.10 * 紧凑系数)), 下限=10, 上限=48
        )
        昵称字 = 获取字体(昵称字号, 是否粗体=False)

        昵称中心x = int(头像rect.centerx)
        昵称顶部y = int(昵称锚点.y - max(8, int(面板.h * 0.02)))

        # ✅ 渲染 rect 记下来：用于点击编辑昵称
        昵称渲染rect = self._绘制文本(
            屏幕, 昵称, 昵称字, 标题白, (昵称中心x, 昵称顶部y), "midtop"
        )
        try:
            self._rect_昵称_渲染 = 昵称渲染rect.copy()
        except Exception:
            self._rect_昵称_渲染 = pygame.Rect(
                昵称锚点.x, 昵称锚点.y, max(60, 昵称锚点.w), max(20, 昵称锚点.h)
            )

        等级rect = getattr(self, "_rect_等级标识", pygame.Rect(0, 0, 1, 1))
        if self._等级原图 is not None:
            try:
                原 = self._等级原图.convert_alpha()
            except Exception:
                原 = self._等级原图
            等级图 = self._取缩放缓存图("等级标识", 原, 等级rect.w, 等级rect.h)
            if 等级图 is not None:
                等级图.set_alpha(透明)
                屏幕.blit(等级图, 等级rect.topleft)

        # ================= 右侧：统计/介绍 =================
        统计区 = getattr(self, "_rect_统计区", pygame.Rect(0, 0, 1, 1))
        介绍区 = getattr(self, "_rect_介绍区", pygame.Rect(0, 0, 1, 1))

        统计字号 = _取字号(
            "统计字号", 默认=max(11, int(面板.h * 0.055 * 紧凑系数)), 下限=9, 上限=28
        )
        统计粗体 = _取粗体("统计粗体", False)
        统计字 = 获取字体(统计字号, 是否粗体=统计粗体)

        默认统计行距 = max(2, int(统计字.get_height() * 1.00))
        统计行距 = _取行距("统计行距", 默认=默认统计行距, 下限=0, 上限=120)

        y = 统计区.y + max(1, int(统计区.h * 0.07 * 紧凑系数))
        行定义 = [
            ("游玩时长（分钟）：", str(游玩时长分钟), None),
            ("累计评价S数：", str(累计评价S数), None),
            ("最大Combo/曲目：", str(最大Combo), 最大Combo曲目 if 最大Combo曲目 else None),
            ("最高分/曲目名：", str(最高分), 最高分曲目 if 最高分曲目 else None),
        ]
        最大标题宽 = 0
        for 标题, _, _ in 行定义:
            try:
                最大标题宽 = max(最大标题宽, int(统计字.size(标题)[0]))
            except Exception:
                pass
        值列x = min(
            统计区.right - int(max(120, 统计区.w * 0.28)),
            统计区.x + 最大标题宽 + int(max(14, 统计区.w * 0.03)),
        )

        def _画一行(标题: str, 数值: str, 曲目: Optional[str] = None):
            nonlocal y
            self._绘制文本(屏幕, 标题, 统计字, 标题白, (统计区.x, y), "topleft")
            数值r = self._绘制文本(屏幕, 数值, 统计字, 数值黄, (值列x, y), "topleft")
            if 曲目:
                self._绘制文本(
                    屏幕, f"({曲目})", 统计字, 曲目紫, (数值r.right + 6, y), "topleft"
                )
            y += int(统计行距)

        for 标题, 数值, 曲目 in 行定义:
            _画一行(标题, 数值, 曲目)

        介绍字号 = _取字号(
            "介绍字号", 默认=max(9, int(面板.h * 0.045 * 紧凑系数)), 下限=8, 上限=20
        )
        介绍粗体 = _取粗体("介绍粗体", False)
        介绍字 = 获取字体(介绍字号, 是否粗体=介绍粗体)

        默认介绍行距 = max(0, int(介绍字.get_height() * 0.18))
        介绍行距 = _取行距("介绍行距", 默认=默认介绍行距, 下限=0, 上限=120)

        介绍文本 = (
            "e舞成名重构版（测试）为非盈利性的游戏；\n"
            "本游戏软件为交流、学习、测试使用，如有侵权，请率先联系我们。\n"
            "如果你有意参与我们的开发项目；\n"
            "请进人QQ群：1084318862\n"
            "进群后联系Emma_H。"
        )
        self._绘制自动换行(
            屏幕,
            介绍文本,
            介绍字,
            小灰,
            pygame.Rect(介绍区.x, 介绍区.y, 介绍区.w, 介绍区.h),
            行距=int(介绍行距),
        )

        # ================= 进度条（从 json 读取） =================
        花式条原 = getattr(self, "_rect_花式条", pygame.Rect(0, 0, 1, 1))
        竞速条原 = getattr(self, "_rect_竞速条", pygame.Rect(0, 0, 1, 1))

        # 经验条字号默认跟统计区一致，保证视觉统一
        进度标签字号 = _取字号(
            "进度标签字号",
            默认=int(统计字号),
            下限=10,
            上限=64,
        )
        进度LV字号 = _取字号(
            "进度LV字号",
            默认=int(统计字号),
            下限=10,
            上限=64,
        )

        进度标签粗体 = _取粗体("进度标签粗体", False)
        进度LV粗体 = _取粗体("进度LV粗体", False)

        标签字 = 获取字体(进度标签字号, 是否粗体=进度标签粗体)
        Lv字 = 获取字体(进度LV字号, 是否粗体=进度LV粗体)

        标签间距 = _取间距("进度标签间距", 默认=max(6, int(进度标签字号 * 0.30)))
        LV间距 = _取间距("进度LV间距", 默认=max(10, int(进度LV字号 * 0.36)))

        标签最大宽 = 0
        try:
            标签最大宽 = max(
                int(标签字.size("花式经验值：")[0]),
                int(标签字.size("竞速经验值：")[0]),
            )
        except Exception:
            标签最大宽 = max(120, int(统计区.w * 0.18))
        try:
            LV预留宽 = int(Lv字.size("Lv. 70")[0])
        except Exception:
            LV预留宽 = max(70, int(统计区.w * 0.10))

        # 与上面信息组左边对齐
        条左x = int(统计区.x + 标签最大宽 + 标签间距)
        条右极限 = int(
            面板.right
            - max(16, int(面板.w * 0.02))
            - LV间距
            - LV预留宽
        )
        可用条宽 = int(max(140, 条右极限 - 条左x))
        # 空间紧张时主动缩短
        原宽上限 = int(max(140, min(int(花式条原.w), int(竞速条原.w))))
        最终条宽 = int(max(140, min(原宽上限, 可用条宽)))

        花式条 = pygame.Rect(
            条左x,
            int(花式条原.y),
            int(最终条宽),
            int(max(10, 花式条原.h)),
        )
        竞速条 = pygame.Rect(
            条左x,
            int(竞速条原.y),
            int(最终条宽),
            int(max(10, 竞速条原.h)),
        )

        花式标签面 = 标签字.render("花式经验值：", True, 标题白)
        花式标签rect_默认 = 花式标签面.get_rect(midleft=(统计区.x, 花式条.centery))
        花式标签rect = self._取覆盖屏幕rect(
            "花式标签", 花式标签rect_默认, 最小边=10
        )
        花式标签面.set_alpha(透明)
        屏幕.blit(花式标签面, 花式标签rect.topleft)

        花式LV面 = Lv字.render(f"Lv. {max(1, 花式等级)}", True, 标题白)
        花式LVrect_默认 = 花式LV面.get_rect(
            midleft=(花式条.right + LV间距, 花式条.centery)
        )
        花式LVrect = self._取覆盖屏幕rect("花式LV", 花式LVrect_默认, 最小边=10)
        花式LV面.set_alpha(透明)
        屏幕.blit(花式LV面, 花式LVrect.topleft)

        self._绘制贴图进度条(
            屏幕,
            花式条,
            进度=float(花式经验),
            框原图=self._花式经验框原图,
            值原图=self._花式经验值原图,
            缓存前缀="个人资料_花式经验条",
            透明=透明,
        )

        竞速标签面 = 标签字.render("竞速经验值：", True, 标题白)
        竞速标签rect_默认 = 竞速标签面.get_rect(midleft=(统计区.x, 竞速条.centery))
        竞速标签rect = self._取覆盖屏幕rect(
            "竞速标签", 竞速标签rect_默认, 最小边=10
        )
        竞速标签面.set_alpha(透明)
        屏幕.blit(竞速标签面, 竞速标签rect.topleft)

        竞速LV面 = Lv字.render(f"Lv. {max(1, 竞速等级)}", True, 标题白)
        竞速LVrect_默认 = 竞速LV面.get_rect(
            midleft=(竞速条.right + LV间距, 竞速条.centery)
        )
        竞速LVrect = self._取覆盖屏幕rect("竞速LV", 竞速LVrect_默认, 最小边=10)
        竞速LV面.set_alpha(透明)
        屏幕.blit(竞速LV面, 竞速LVrect.topleft)

        self._绘制贴图进度条(
            屏幕,
            竞速条,
            进度=float(竞速经验),
            框原图=self._竞速经验框原图,
            值原图=self._竞速经验值原图,
            缓存前缀="个人资料_竞速经验条",
            透明=透明,
        )

        if not isinstance(getattr(self, "_调试_rect表", None), dict):
            self._调试_rect表 = {}
        self._调试_rect表.update(
            {
                "花式标签": 花式标签rect.copy(),
                "花式LV": 花式LVrect.copy(),
                "竞速标签": 竞速标签rect.copy(),
                "竞速LV": 竞速LVrect.copy(),
                "昵称渲染": self._rect_昵称_渲染.copy(),
            }
        )

    def _绘制_下面板(self, 屏幕: pygame.Surface, 缩放: float, 透明: int):
        from core.工具 import 获取字体

        if bool(self.上下文.get("布局调试_开启", False)):
            缩放 = 1.0
            透明 = 255

        面板 = self._rect_下面板.copy()
        if abs(缩放 - 1.0) > 0.001:
            面板.w = max(1, int(面板.w * 缩放))
            面板.h = max(1, int(面板.h * 缩放))
            面板.center = self._rect_下面板.center

        if isinstance(self._下面板背景原图, pygame.Surface):
            背景图 = self._取缩放缓存图(
                "个人资料_下背景",
                self._下面板背景原图,
                面板.w,
                面板.h,
            )
            if isinstance(背景图, pygame.Surface):
                try:
                    背景图 = 背景图.copy()
                    背景图.set_alpha(max(0, min(255, int(透明))))
                except Exception:
                    pass
                屏幕.blit(背景图, 面板.topleft)
        else:
            圆角 = 36
            self._绘制圆角面板(屏幕, 面板, 背景alpha=185, 线宽=2, 圆角=圆角)

        样式 = getattr(self, "_调试_样式", None)

        def _取字号(键: str, 默认: int, 下限: int, 上限: int) -> int:
            vv = None
            if isinstance(样式, dict):
                vv = 样式.get(键)
            if isinstance(vv, int):
                return max(下限, min(上限, int(vv)))
            return max(下限, min(上限, int(默认)))

        def _取粗体(键: str, 默认: bool) -> bool:
            vv = None
            if isinstance(样式, dict):
                vv = 样式.get(键)
            if isinstance(vv, bool):
                return bool(vv)
            return bool(默认)

        def _取行距(键: str, 默认: int, 下限: int = 0, 上限: int = 160) -> int:
            vv = None
            if isinstance(样式, dict):
                vv = 样式.get(键)
            if isinstance(vv, int):
                return max(下限, min(上限, int(vv)))
            return max(下限, min(上限, int(默认)))

        def _取全局字距(默认: int = 1) -> int:
            vv = None
            if isinstance(样式, dict):
                vv = 样式.get("全局字距", 默认)
            try:
                vv = int(vv)
            except Exception:
                vv = 默认
            return 0 if vv < 0 else (40 if vv > 40 else vv)

        # 软件按钮（可缩放、可拖）
        软件按钮rect = getattr(self, "_rect_软件按钮", None)
        if isinstance(软件按钮rect, pygame.Rect) and self._软件信息装饰原图 is not None:
            try:
                原 = self._软件信息装饰原图.convert_alpha()
            except Exception:
                原 = self._软件信息装饰原图
            图 = self._取缩放缓存图("软件按钮", 原, 软件按钮rect.w, 软件按钮rect.h)
            if 图 is not None:
                图.set_alpha(透明)
                屏幕.blit(图, 软件按钮rect.topleft)

        # ✅ 单列：全部内容绘制到“软件信息”区域
        文区 = getattr(self, "_rect_软件信息", pygame.Rect(0, 0, 1, 1))

        左字号 = _取字号(
            "下方左字号", 默认=max(12, int(面板.h * 0.052)), 下限=9, 上限=30
        )
        左粗体 = _取粗体("下方左粗体", True)
        左字 = 获取字体(左字号, 是否粗体=左粗体)

        默认左行距 = max(0, int(左字.get_height() * 0.45))
        下方左行距 = _取行距("下方左行距", 默认=默认左行距, 下限=0, 上限=160)

        全局字距 = _取全局字距(默认=1)

        黄色 = (255, 220, 80)
        白色 = (235, 235, 235)

        # ✅ 富文本逐字绘制（同一行可不同颜色 + 自动换行 + 字距）
        def _绘制富文本段落(
            起始x: int,
            起始y: int,
            区域: pygame.Rect,
            字体: pygame.font.Font,
            行距: int,
            字距: int,
            行片段列表,
        ):
            # 缓存单字渲染：减少每帧开销
            if not hasattr(self, "_富文本单字缓存"):
                self._富文本单字缓存 = {}

            def _取字面(字: str, 颜色):
                键 = (id(字体), 字, 颜色[0], 颜色[1], 颜色[2])
                已有 = self._富文本单字缓存.get(键)
                if isinstance(已有, pygame.Surface):
                    return 已有
                try:
                    面 = 字体.render(字, True, 颜色)
                except Exception:
                    面 = None
                if isinstance(面, pygame.Surface):
                    self._富文本单字缓存[键] = 面
                    return 面
                return None

            行高 = max(1, int(字体.get_height()))
            x0 = int(起始x)
            y = int(起始y)

            for 片段们 in 行片段列表:
                # 空行（用于你写的 \n\n\n 这种效果）
                if not 片段们:
                    y += 行高 + int(行距)
                    if y > 区域.bottom - 2:
                        break
                    continue

                # 展开为字符流（char, color）
                字符流 = []
                for 文本, 颜色 in 片段们:
                    文本 = str(文本 or "")
                    for ch in 文本:
                        字符流.append((ch, 颜色))

                当前行 = []
                当前宽 = 0

                def _落笔一行(要画的行):
                    nonlocal y
                    if y > 区域.bottom - 2:
                        return
                    xx = x0
                    for i, (ch, col) in enumerate(要画的行):
                        字面 = _取字面(ch, col)
                        if isinstance(字面, pygame.Surface):
                            字面2 = 字面
                            if 透明 < 255:
                                字面2 = 字面.copy()
                                字面2.set_alpha(透明)
                            屏幕.blit(字面2, (xx, y))
                            xx += int(字面.get_width())
                        else:
                            try:
                                xx += int(字体.size(ch)[0])
                            except Exception:
                                pass
                        if i != len(要画的行) - 1:
                            xx += int(字距)
                    y += 行高 + int(行距)

                for ch, col in 字符流:
                    if ch == "\n":
                        _落笔一行(当前行)
                        当前行 = []
                        当前宽 = 0
                        continue

                    try:
                        字宽 = int(字体.size(ch)[0])
                    except Exception:
                        字宽 = 0
                    追加宽 = (字距 if 当前行 else 0) + 字宽
                    if 当前行 and (当前宽 + 追加宽 > 区域.w):
                        _落笔一行(当前行)
                        当前行 = [(ch, col)]
                        当前宽 = 字宽
                    else:
                        当前行.append((ch, col))
                        当前宽 += 追加宽

                    if y > 区域.bottom - 2:
                        break

                if y > 区域.bottom - 2:
                    break
                if 当前行:
                    _落笔一行(当前行)

                if y > 区域.bottom - 2:
                    break

            return y

        # ✅ 你的新布局 + 三段标题黄色
        行片段列表 = [
            [
                ("游戏版本：", 黄色),
                ("e舞成名重构版v1.0.0         ", 白色),
                ("开发团队：", 黄色),
                (
                    "程序工程师/策划/游戏制作人：良    UE/UI设计/策划：Emma_H（林曦）",
                    白色,
                ),
            ],
            [
                ("特别鸣谢（排名不分先后）：", 黄色),
            ],
            [
                ("    Cyan（音效提供）|  飞翔e舞模拟器（曲谱资源提供）", 白色),
            ],
            [
                ("LifeErrOr（美术提供）|  小鱼（美术提供）", 白色),
            ],
            [
                ("“e舞时刻”官方粉丝1群参与讨论的群友（反馈提供）", 白色),
            ],
            [],  # 空行
            [
                ("玩家交流QQ群：1084318862", 白色),
            ],
            [
                (
                    "本游戏设计初衷是为了让更多e舞玩家能在各地玩到e舞成名，本项目纯爱发电，没有任何盈利性质，如您发现有人倒卖本软件，请及时联系我们。",
                    白色,
                ),
            ],
        ]

        _绘制富文本段落(
            起始x=文区.x,
            起始y=文区.y,
            区域=文区,
            字体=左字,
            行距=int(下方左行距),
            字距=int(全局字距),
            行片段列表=行片段列表,
        )

    def _绘制_离开按钮(self, 屏幕: pygame.Surface, 透明: int):
        r = self._rect_离开按钮
        if self._离开按钮图 is not None:
            图 = self._离开按钮图.copy()
            图.set_alpha(透明)
            屏幕.blit(图, r.topleft)
        else:
            面 = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            面.fill((0, 0, 0, 0))
            pygame.draw.rect(
                面, (30, 60, 120, 200), pygame.Rect(0, 0, r.w, r.h), border_radius=18
            )
            pygame.draw.rect(
                面,
                (220, 220, 220),
                pygame.Rect(0, 0, r.w, r.h),
                width=3,
                border_radius=18,
            )
            面.set_alpha(透明)
            屏幕.blit(面, r.topleft)

    # ---------------- 事件 ----------------
    def 处理事件(self, 事件):
        if 事件.type == pygame.VIDEORESIZE:
            return None

        if self._弹窗类型:
            if self._处理二次弹窗事件(事件):
                return None

        if 事件.type == self._事件_延迟切场景:
            pygame.time.set_timer(self._事件_延迟切场景, 0)
            self._正在放大切场景 = False
            if self._延迟目标场景:
                目标 = self._延迟目标场景
                self._延迟目标场景 = None
                return {"切换到": 目标, "禁用黑屏过渡": True}
            return None

        if self._全屏放大过渡.是否进行中():
            return None

        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
            self._触发离开()
            return None

        if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            # 1) 离开按钮优先（不改你原逻辑）
            if self._rect_离开按钮.collidepoint(事件.pos):
                self._触发离开()
                return None

            # 2) 点击头像：上传替换
            try:
                if getattr(
                    self, "_rect_头像控件", pygame.Rect(0, 0, 0, 0)
                ).collidepoint(事件.pos):
                    self._点击_更换头像()
                    return None
            except Exception:
                pass

            # 3) 点击昵称：编辑昵称
            try:
                目标rect = getattr(self, "_rect_昵称_渲染", None)
                if not isinstance(目标rect, pygame.Rect):
                    目标rect = getattr(self, "_rect_昵称锚点", pygame.Rect(0, 0, 0, 0))
                # 点击容忍区：放大一点，避免字太小点不到
                目标rect2 = (
                    目标rect.inflate(16, 12)
                    if isinstance(目标rect, pygame.Rect)
                    else pygame.Rect(0, 0, 0, 0)
                )
                if 目标rect2.collidepoint(事件.pos):
                    self._点击_编辑昵称()
                    return None
            except Exception:
                pass

        return None

    def _触发离开(self):
        屏幕 = self.上下文["屏幕"]
        try:
            self.按钮音效.播放()
        except Exception:
            pass

        try:
            if hasattr(self._按钮点击特效, "触发"):
                self._按钮点击特效.触发()
        except Exception:
            pass

        try:
            屏幕矩形 = 屏幕.get_rect()
            r = self._rect_离开按钮.clip(屏幕矩形)
            if r.w <= 0 or r.h <= 0:
                r = pygame.Rect(0, 0, 2, 2)
            self._按钮特效_截图 = 屏幕.subsurface(r).copy()
            self._按钮特效_rect = r
        except Exception:
            self._按钮特效_截图 = None
            self._按钮特效_rect = self._rect_离开按钮.copy()
            r = self._rect_离开按钮.copy()

        self._开始放大切场景(self._按钮特效_截图, r, "大模式")

    def _个人资料_默认数据(self) -> dict:
        return {
            "昵称": "玩家昵称",
            "头像文件": "UI-img/个人中心-个人资料/默认头像.png",
            "统计": {
                "游玩时长分钟": 0,
                "累计评价S数": 0,
                "最大Combo": 0,
                "最大Combo曲目": "",
                "最高分": 0,
                "最高分曲目": "",
            },
            "进度": {
                "最大等级": 70,
                "段位": "UI-img/个人中心-个人资料/等级/1.png",
                "花式": {"等级": 1, "经验": 0.0, "累计歌曲": 0, "累计首数": 0},
                "竞速": {"等级": 1, "经验": 0.0, "累计歌曲": 0, "累计首数": 0},
            },
        }

    def _个人资料_规范化头像路径(self, 值) -> str:
        文本 = str(值 or "").strip().replace("\\", "/")
        if not 文本:
            return "UI-img/个人中心-个人资料/默认头像.png"
        if os.path.isabs(文本):
            return 文本
        if 文本.startswith("UI-img/"):
            return 文本
        return f"UI-img/个人中心-个人资料/{os.path.basename(文本)}"

    def _个人资料_段位路径(self, 段位: int) -> str:
        段位 = max(1, min(7, int(段位)))
        return f"UI-img/个人中心-个人资料/等级/{段位}.png"

    def _个人资料_规范化段位路径(self, 值, 默认段位: int) -> str:
        if isinstance(值, (int, float)):
            return self._个人资料_段位路径(int(值))
        文本 = str(值 or "").strip().replace("\\", "/")
        if not 文本:
            return self._个人资料_段位路径(默认段位)
        if os.path.isabs(文本):
            return 文本
        if 文本.startswith("UI-img/"):
            return 文本
        return self._个人资料_段位路径(默认段位)

    def _个人资料_取资源绝对路径(self, 相对或绝对路径: str) -> str:
        文本 = str(相对或绝对路径 or "").strip()
        if not 文本:
            return ""
        if os.path.isabs(文本):
            return 文本
        文本 = 文本.replace("/", os.sep).replace("\\", os.sep)
        return os.path.join(str(self._资源根 or os.getcwd()), 文本)

    def _个人资料_计算段位(self, 等级: int) -> int:
        try:
            等级 = int(等级)
        except Exception:
            等级 = 1
        等级 = max(1, min(70, 等级))
        段位 = (等级 - 1) // 10 + 1  # 1-10->1, 11-20->2 ... 61-70->7
        段位 = max(1, min(7, int(段位)))
        return 段位

    def _个人资料_读取并修复(self, 是否回写: bool = True) -> dict:
        # 确保目录存在
        try:
            os.makedirs(self._个人资料目录路径, exist_ok=True)
        except Exception:
            pass

        数据 = None
        if os.path.isfile(self._个人资料json路径):
            try:
                with open(self._个人资料json路径, "r", encoding="utf-8") as f:
                    数据 = json.load(f)
            except Exception:
                数据 = None

        if not isinstance(数据, dict):
            数据 = self._个人资料_默认数据()

        # 修复结构
        默认 = self._个人资料_默认数据()

        def _取字典(源, 键, 默认值):
            v = None
            try:
                v = 源.get(键)
            except Exception:
                v = None
            return v if isinstance(v, dict) else 默认值

        数据["昵称"] = str(数据.get("昵称", 默认["昵称"]) or 默认["昵称"])
        数据["头像文件"] = self._个人资料_规范化头像路径(
            数据.get("头像文件", 默认["头像文件"]) or 默认["头像文件"]
        )

        数据["统计"] = _取字典(数据, "统计", 默认["统计"])
        数据["进度"] = _取字典(数据, "进度", 默认["进度"])

        统计 = 数据["统计"]
        统计["游玩时长分钟"] = int(统计.get("游玩时长分钟", 0) or 0)
        统计["累计评价S数"] = int(统计.get("累计评价S数", 0) or 0)
        统计["最大Combo"] = int(统计.get("最大Combo", 0) or 0)
        统计["最大Combo曲目"] = str(统计.get("最大Combo曲目", "") or "")
        统计["最高分"] = int(统计.get("最高分", 0) or 0)
        统计["最高分曲目"] = str(统计.get("最高分曲目", "") or "")

        进度 = 数据["进度"]
        进度["最大等级"] = int(进度.get("最大等级", 70) or 70)
        进度["最大等级"] = max(1, min(70, int(进度["最大等级"])))

        def _修复模式(模式键: str):
            m = 进度.get(模式键)
            if not isinstance(m, dict):
                m = {"等级": 1, "经验": 0.0, "累计歌曲": 0, "累计首数": 0}
                进度[模式键] = m

            m["累计歌曲"] = int(m.get("累计歌曲", 0) or 0)
            m["累计歌曲"] = max(0, m["累计歌曲"])
            m["累计首数"] = int(m.get("累计首数", 0) or 0)
            m["累计首数"] = max(0, m["累计首数"])

            m["等级"] = int(m.get("等级", 1) or 1)
            m["等级"] = max(1, min(int(进度["最大等级"]), m["等级"]))

            try:
                m["经验"] = float(m.get("经验", 0.0) or 0.0)
            except Exception:
                m["经验"] = 0.0
            m["经验"] = (
                0.0 if m["经验"] < 0.0 else (1.0 if m["经验"] > 1.0 else m["经验"])
            )

        _修复模式("花式")
        _修复模式("竞速")

        # 段位从“最高等级”推导，确保一致
        最高等级 = max(int(进度["花式"]["等级"]), int(进度["竞速"]["等级"]))
        段位值 = 进度.get("段位", self._个人资料_计算段位(最高等级))
        进度["段位"] = self._个人资料_规范化段位路径(
            段位值, self._个人资料_计算段位(最高等级)
        )

        if 是否回写:
            self._个人资料_保存(数据)

        return 数据

    def _个人资料_保存(self, 数据: dict) -> bool:
        try:
            os.makedirs(self._个人资料目录路径, exist_ok=True)
        except Exception:
            pass

        try:
            tmp = self._个人资料json路径 + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self._个人资料json路径)
            return True
        except Exception:
            return False

    def _个人资料_刷新头像原图(self):
        数据 = (
            self._个人资料数据
            if isinstance(getattr(self, "_个人资料数据", None), dict)
            else {}
        )
        文件名 = self._个人资料_规范化头像路径(
            数据.get("头像文件", "UI-img/个人中心-个人资料/默认头像.png")
        )
        候选路径 = self._个人资料_取资源绝对路径(文件名)

        头像图 = None
        if os.path.isfile(候选路径):
            try:
                图 = pygame.image.load(候选路径)
                try:
                    头像图 = 图.convert_alpha()
                except Exception:
                    头像图 = 图.convert()
            except Exception:
                头像图 = None

        if 头像图 is None:
            头像图 = self._默认头像原图

        self._当前头像原图 = 头像图

        # 头像变化要清头像相关缓存，否则一直显示旧图
        try:
            if hasattr(self, "_缩放缓存"):
                self._缩放缓存 = {}
        except Exception:
            pass

        try:
            self._缓存尺寸 = (0, 0)
        except Exception:
            pass

    def _个人资料_刷新段位图标(self):
        数据 = (
            self._个人资料数据
            if isinstance(getattr(self, "_个人资料数据", None), dict)
            else {}
        )
        进度 = 数据.get("进度", {}) if isinstance(数据.get("进度", {}), dict) else {}
        最高等级 = max(
            int(进度.get("花式", {}).get("等级", 1) or 1),
            int(进度.get("竞速", {}).get("等级", 1) or 1),
        )
        路径 = self._个人资料_取资源绝对路径(
            self._个人资料_规范化段位路径(
                进度.get("段位", ""), self._个人资料_计算段位(最高等级)
            )
        )
        图 = None
        if os.path.isfile(路径):
            try:
                图 = pygame.image.load(路径).convert_alpha()
            except Exception:
                图 = None

        self._等级原图 = 图

        try:
            if hasattr(self, "_缩放缓存"):
                # 只清“等级标识”相关缓存即可（简单起见清一波）
                self._缩放缓存 = {}
        except Exception:
            pass

    def _弹窗_选择图片文件(self) -> Optional[str]:
        try:
            import tkinter as tk
            from tkinter import filedialog
        except Exception:
            return None

        根 = None
        try:
            根 = tk.Tk()
            根.withdraw()
            根.attributes("-topmost", True)
            初始目录 = ""
            try:
                初始目录 = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.isdir(初始目录):
                    初始目录 = os.path.expanduser("~")
            except Exception:
                初始目录 = ""
            路径 = filedialog.askopenfilename(
                title="选择头像图片",
                initialdir=初始目录 if 初始目录 else None,
                filetypes=[
                    ("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"),
                    ("PNG", "*.png"),
                    ("JPG", "*.jpg;*.jpeg"),
                    ("所有文件", "*.*"),
                ],
            )
            return str(路径) if 路径 else None
        except Exception:
            return None
        finally:
            try:
                if 根 is not None:
                    根.destroy()
            except Exception:
                pass

    def _弹窗_输入昵称(self, 当前昵称: str) -> Optional[str]:
        try:
            import tkinter as tk
        except Exception:
            return None

        根 = None
        窗 = None
        结果 = {"值": None}
        try:
            根 = tk.Tk()
            根.withdraw()
            根.attributes("-topmost", True)

            窗 = tk.Toplevel(根)
            窗.title("修改昵称")
            窗.resizable(False, False)
            窗.attributes("-topmost", True)
            窗.configure(bg="#000000")
            try:
                窗.attributes("-alpha", 0.92)
            except Exception:
                pass

            背景图 = None
            try:
                背景图路径 = os.path.join(
                    self._个人资料目录路径,
                    "二次弹窗背景.png",
                )
                if os.path.isfile(背景图路径):
                    背景图 = tk.PhotoImage(file=背景图路径)
            except Exception:
                背景图 = None

            if 背景图 is not None:
                宽 = int(max(320, int(背景图.width())))
                高 = int(max(180, int(背景图.height())))
            else:
                宽, 高 = 440, 210
            屏宽 = int(窗.winfo_screenwidth())
            屏高 = int(窗.winfo_screenheight())
            x = max(0, int((屏宽 - 宽) // 2))
            y = max(0, int((屏高 - 高) // 2))
            窗.geometry(f"{宽}x{高}+{x}+{y}")

            if 背景图 is not None:
                try:
                    背景标签 = tk.Label(窗, image=背景图, bd=0, highlightthickness=0)
                    背景标签.place(x=0, y=0, relwidth=1, relheight=1)
                    窗._昵称弹窗背景图 = 背景图  # 防GC
                except Exception:
                    pass
                内层 = tk.Frame(窗, bg="#000000", bd=0, highlightthickness=0)
                内层.place(
                    x=int(宽 * 0.08),
                    y=int(高 * 0.16),
                    width=int(宽 * 0.84),
                    height=int(高 * 0.70),
                )
            else:
                外框 = tk.Frame(
                    窗,
                    bg="#b0b0b0",
                    bd=0,
                    highlightthickness=1,
                    highlightbackground="#c0c0c0",
                )
                外框.pack(fill="both", expand=True, padx=1, pady=1)
                内层 = tk.Frame(外框, bg="#000000", bd=0)
                内层.pack(fill="both", expand=True)

            标题 = tk.Label(
                内层,
                text="修改昵称",
                bg="#000000",
                fg="#f0f0f0",
                font=("Microsoft YaHei", 14, "bold"),
            )
            标题.pack(pady=(18, 8))

            文本变量 = tk.StringVar(value=str(当前昵称 or ""))
            输入框 = tk.Entry(
                内层,
                textvariable=文本变量,
                bg="#0c0c0c",
                fg="#f2f2f2",
                insertbackground="#f2f2f2",
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground="#9a9a9a",
                highlightcolor="#c0c0c0",
                font=("Microsoft YaHei", 15),
            )
            输入框.pack(fill="x", padx=38, ipady=8)

            按钮行 = tk.Frame(内层, bg="#000000")
            按钮行.pack(fill="x", padx=38, pady=(18, 0))

            def _确定(*_):
                文本 = str(文本变量.get() or "").strip()
                if len(文本) > 16:
                    文本 = 文本[:16]
                结果["值"] = 文本 if 文本 else None
                try:
                    窗.destroy()
                except Exception:
                    pass

            def _取消(*_):
                结果["值"] = None
                try:
                    窗.destroy()
                except Exception:
                    pass

            确定按钮 = tk.Button(
                按钮行,
                text="确定",
                command=_确定,
                bg="#111111",
                fg="#f0f0f0",
                activebackground="#2a2a2a",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground="#9a9a9a",
                padx=18,
                pady=6,
                font=("Microsoft YaHei", 11),
            )
            返回按钮 = tk.Button(
                按钮行,
                text="返回",
                command=_取消,
                bg="#111111",
                fg="#f0f0f0",
                activebackground="#2a2a2a",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground="#9a9a9a",
                padx=18,
                pady=6,
                font=("Microsoft YaHei", 11),
            )
            返回按钮.pack(side="right")
            确定按钮.pack(side="right", padx=(0, 10))

            窗.bind("<Return>", _确定)
            窗.bind("<Escape>", _取消)

            输入框.focus_set()
            try:
                输入框.select_range(0, "end")
            except Exception:
                pass
            窗.grab_set()
            窗.wait_window()
            return 结果.get("值")
        except Exception:
            return None
        finally:
            try:
                if 窗 is not None and bool(getattr(窗, "winfo_exists", lambda: False)()):
                    窗.destroy()
            except Exception:
                pass
            try:
                if 根 is not None:
                    根.destroy()
            except Exception:
                pass

    def _点击_更换头像(self):
        try:
            self.按钮音效.播放()
        except Exception:
            pass
        self._打开头像二次弹窗()

    def _点击_编辑昵称(self):
        try:
            self.按钮音效.播放()
        except Exception:
            pass
        数据 = (
            self._个人资料数据
            if isinstance(getattr(self, "_个人资料数据", None), dict)
            else self._个人资料_默认数据()
        )
        当前昵称 = str(数据.get("昵称", "玩家昵称") or "玩家昵称")
        新昵称 = self._弹窗_输入昵称(当前昵称)
        if not 新昵称:
            return
        self._应用昵称(新昵称)

    def 记录游玩一首(
        self,
        模式: str,
        本局游玩分钟: int = 0,
        是否评价S: bool = False,
        本局最大combo: int = 0,
        本局最高分: int = 0,
        曲目名: str = "",
    ):
        """
        ✅ 给你留的“外部调用入口”：你在别的场景（游戏结束/结算）调用它就能自动升级/统计
        - 玩一首歌：经验 +0.1
        - 经验满 1.0：等级 +1（最高70）
        - 每 10 级：段位 +1（1~7），段位图标=UI-img\\个人中心-个人资料\\等级\\1.png~7.png
        """
        数据 = (
            self._个人资料数据
            if isinstance(getattr(self, "_个人资料数据", None), dict)
            else self._个人资料_默认数据()
        )
        数据 = self._个人资料_读取并修复(是否回写=False)  # 用磁盘最新

        统计 = 数据.get("统计", {})
        进度 = 数据.get("进度", {})
        最大等级 = int(进度.get("最大等级", 70) or 70)
        最大等级 = max(1, min(70, 最大等级))

        模式键 = (
            "花式"
            if ("花" in str(模式))
            else ("竞速" if ("竞" in str(模式)) else "花式")
        )
        模式进度 = 进度.get(模式键, {})
        if not isinstance(模式进度, dict):
            模式进度 = {"等级": 1, "经验": 0.0, "累计歌曲": 0, "累计首数": 0}
            进度[模式键] = 模式进度

        # ---- 统计 ----
        try:
            统计["游玩时长分钟"] = int(统计.get("游玩时长分钟", 0) or 0) + int(
                max(0, 本局游玩分钟)
            )
        except Exception:
            统计["游玩时长分钟"] = int(统计.get("游玩时长分钟", 0) or 0)

        if bool(是否评价S):
            try:
                统计["累计评价S数"] = int(统计.get("累计评价S数", 0) or 0) + 1
            except Exception:
                统计["累计评价S数"] = int(统计.get("累计评价S数", 0) or 0)

        try:
            本局最大combo = int(本局最大combo or 0)
        except Exception:
            本局最大combo = 0
        if 本局最大combo > int(统计.get("最大Combo", 0) or 0):
            统计["最大Combo"] = int(本局最大combo)
            统计["最大Combo曲目"] = str(曲目名 or "")

        try:
            本局最高分 = int(本局最高分 or 0)
        except Exception:
            本局最高分 = 0
        if 本局最高分 > int(统计.get("最高分", 0) or 0):
            统计["最高分"] = int(本局最高分)
            统计["最高分曲目"] = str(曲目名 or "")

        # ---- 升级规则 ----
        try:
            模式进度["累计歌曲"] = int(模式进度.get("累计歌曲", 0) or 0) + 1
        except Exception:
            模式进度["累计歌曲"] = int(模式进度.get("累计歌曲", 0) or 0)

        try:
            模式进度["累计首数"] = int(模式进度.get("累计首数", 0) or 0) + 1
        except Exception:
            模式进度["累计首数"] = int(模式进度.get("累计首数", 0) or 0)

        当前等级 = int(模式进度.get("等级", 1) or 1)
        当前经验 = float(模式进度.get("经验", 0.0) or 0.0)

        if 当前等级 >= 最大等级:
            当前等级 = 最大等级
            当前经验 = 1.0
        else:
            当前经验 += 0.10
            while 当前经验 >= 1.0 and 当前等级 < 最大等级:
                当前经验 -= 1.0
                当前等级 += 1
            if 当前等级 >= 最大等级:
                当前等级 = 最大等级
                当前经验 = 1.0

        模式进度["等级"] = int(当前等级)
        模式进度["经验"] = float(
            0.0 if 当前经验 < 0.0 else (1.0 if 当前经验 > 1.0 else 当前经验)
        )

        # 段位：由“花式/竞速”最高等级决定
        最高等级 = max(
            int(进度.get("花式", {}).get("等级", 1) or 1),
            int(进度.get("竞速", {}).get("等级", 1) or 1),
        )
        进度["段位"] = self._个人资料_段位路径(self._个人资料_计算段位(最高等级))

        数据["统计"] = 统计
        数据["进度"] = 进度

        self._个人资料_保存(数据)
        self._个人资料数据 = 数据

        # 刷新资源（头像不用动，段位可能变）
        self._个人资料_刷新段位图标()
