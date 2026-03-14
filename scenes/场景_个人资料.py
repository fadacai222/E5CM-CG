import os
import time
import json
from typing import Optional, Tuple, List, Dict

import pygame

from core.常量与路径 import (
    取项目根目录 as _公共取项目根目录,
    取运行根目录 as _公共取运行根目录,
)
from core.等级经验 import (
    构建默认模式进度,
    处理经验入账,
    经验数据版本,
    规范化模式进度,
    计算经验显示比例,
)
from core.软件版本 import 读取当前版本展示文本
from core.踏板控制 import 踏板动作_确认
from ui.按钮特效 import 公用按钮点击特效, 公用按钮音效
from ui.场景过渡 import 公用放大过渡器


class 场景_个人资料:
    名称 = "个人资料"
    _设计宽 = 2048
    _设计高 = 1152
    _事件_延迟切场景 = pygame.USEREVENT + 25
    # _bbox_上面板 = (130, 170, 1918, 430)
    # _bbox_下面板 = (300, 520, 1710, 1030)
    # _bbox_离开按钮 = (1740, 835, 1965, 1080)

    def _取程序根目录(self) -> str:
        return _公共取运行根目录()

    def _取资源根目录(self) -> str:
        资源 = self.上下文.get("资源", {}) or {}
        return _公共取项目根目录(资源)

    def _取数据根目录(self) -> str:
        return self._取程序根目录()

    def _取全局缩放(self) -> float:
        屏幕 = self.上下文["屏幕"]
        宽, 高 = 屏幕.get_size()
        return min(
            float(宽) / max(1.0, float(self._设计宽)),
            float(高) / max(1.0, float(self._设计高)),
        )

    def _设计值(self, 值: float, 最小值: int = 1) -> int:
        try:
            结果 = int(round(float(值) * self._取全局缩放()))
        except Exception:
            结果 = int(最小值)
        return max(int(最小值), 结果)

    def _设计字号(self, 字号: int, 最小字号: int = 8) -> int:
        return max(int(最小字号), self._设计值(字号, 最小字号))

    def _设计矩形(self, x: int, y: int, w: int, h: int) -> pygame.Rect:
        屏幕 = self.上下文["屏幕"]
        屏幕宽, 屏幕高 = 屏幕.get_size()

        缩放 = self._取全局缩放()
        内容宽 = float(self._设计宽) * 缩放
        内容高 = float(self._设计高) * 缩放
        偏移x = (float(屏幕宽) - 内容宽) * 0.5
        偏移y = (float(屏幕高) - 内容高) * 0.5

        屏幕x = int(round(偏移x + float(x) * 缩放))
        屏幕y = int(round(偏移y + float(y) * 缩放))
        屏幕w = max(1, int(round(float(w) * 缩放)))
        屏幕h = max(1, int(round(float(h) * 缩放)))
        return pygame.Rect(屏幕x, 屏幕y, 屏幕w, 屏幕h)

    def _布局矩形(self, 名称: str) -> pygame.Rect:
        配置 = getattr(self, "_布局方案", {}).get(名称)
        if not isinstance(配置, (list, tuple)) or len(配置) != 4:
            return pygame.Rect(0, 0, 1, 1)
        return self._设计矩形(
            int(配置[0]),
            int(配置[1]),
            int(配置[2]),
            int(配置[3]),
        )

    def __init__(self, 上下文: dict):
        self.上下文 = 上下文
        资源 = 上下文.get("资源", {}) or {}

        self._背景视频 = 上下文.get("背景视频")

        self._资源根 = self._取资源根目录()
        self._运行根 = self._取数据根目录()
        self._游戏版本文本 = 读取当前版本展示文本(根目录=self._运行根)

        self._联网原图 = self._安全加载图片(资源.get("投币_联网图标", ""), 透明=True)

        self._top栏原图 = self._安全加载图片(
            os.path.join(self._资源根, "UI-img", "top栏", "top栏背景.png"),
            透明=True,
        )

        self._top标题原图 = None
        标题候选 = [
            os.path.join(self._资源根, "UI-img", "top栏", "个人中心top标题.png"),
            os.path.join(self._资源根, "UI-img", "top栏", "个人中心.png"),
            os.path.join(self._资源根, "UI-img", "top栏", "个人中心top标题.jpg"),
        ]
        for 路径 in 标题候选:
            图 = self._安全加载图片(路径, 透明=True)
            if 图 is not None:
                self._top标题原图 = 图
                break

        self._个人资料目录路径 = os.path.join(
            self._资源根, "UI-img", "个人中心-个人资料"
        )
        self._个人资料数据目录路径 = os.path.join(self._运行根, "json", "个人资料")
        self._个人资料json路径 = os.path.join(self._运行根, "json", "个人资料.json")

        self._默认头像路径 = os.path.join(self._个人资料目录路径, "默认头像.png")
        if not os.path.isfile(self._默认头像路径):
            self._默认头像路径 = os.path.join(self._个人资料目录路径, "默认头像.jpg")
        self._默认头像原图 = self._安全加载图片(self._默认头像路径, 透明=False)

        self._当前头像原图 = None
        self._等级原图 = None

        self._软件信息装饰原图 = self._安全加载图片(
            os.path.join(self._个人资料目录路径, "软件信息.png"),
            透明=True,
        )
        self._上面板背景原图 = self._安全加载图片(
            os.path.join(self._个人资料目录路径, "上背景.png"),
            透明=True,
        )
        self._下面板背景原图 = self._安全加载图片(
            os.path.join(self._个人资料目录路径, "下背景.png"),
            透明=True,
        )
        self._头像弹窗背景原图 = self._安全加载图片(
            os.path.join(self._个人资料目录路径, "头像二次弹窗.png"),
            透明=True,
        )

        经验条目录 = os.path.join(self._资源根, "UI-img", "经验条")
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
            os.path.join(self._个人资料目录路径, "离开.png"),
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
        self._主界面静态缓存: Optional[pygame.Surface] = None
        self._主界面静态缓存尺寸 = (0, 0)
        self._头像预览缓存键 = None
        self._头像预览缓存图: Optional[pygame.Surface] = None

        self._rect_top栏 = pygame.Rect(0, 0, 1, 1)
        self._rect_top标题 = pygame.Rect(0, 0, 1, 1)
        self._top栏图 = None
        self._top标题图 = None

        self._rect_上面板 = pygame.Rect(0, 0, 1, 1)
        self._rect_下面板 = pygame.Rect(0, 0, 1, 1)
        self._rect_离开按钮 = pygame.Rect(0, 0, 1, 1)
        self._rect_头像控件 = pygame.Rect(0, 0, 1, 1)
        self._rect_昵称锚点 = pygame.Rect(0, 0, 1, 1)
        self._rect_等级标识 = pygame.Rect(0, 0, 1, 1)
        self._rect_统计区 = pygame.Rect(0, 0, 1, 1)
        self._rect_介绍区 = pygame.Rect(0, 0, 1, 1)
        self._rect_花式条 = pygame.Rect(0, 0, 1, 1)
        self._rect_竞速条 = pygame.Rect(0, 0, 1, 1)
        self._rect_软件按钮 = pygame.Rect(0, 0, 1, 1)
        self._rect_软件信息 = pygame.Rect(0, 0, 1, 1)
        self._rect_软件说明 = pygame.Rect(0, 0, 1, 1)

        # self._头像图 = None
        # self._等级图 = None
        # self._软件信息装饰图 = None
        # self._rect_软件信息装饰 = pygame.Rect(0, 0, 1, 1)
        self._离开按钮图 = None

        self._rect_昵称_渲染 = pygame.Rect(0, 0, 1, 1)

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

        self._布局覆盖_加载并应用()

        self._个人资料数据 = self._个人资料_读取并修复(是否回写=True)
        self._个人资料_刷新头像原图()
        self._个人资料_刷新段位图标()

        self._入场开始 = 0.0
        self._入场时长 = 0.22

    def _布局覆盖_加载并应用(self):
        下移 = 26

        def _下移矩形(x: int, y: int, w: int, h: int) -> list[int]:
            return [int(x), int(y + 下移), int(w), int(h)]

        self._布局方案 = {
            "上面板": _下移矩形(222, 161, 1488, 305),
            "下面板": _下移矩形(214, 517, 1498, 380),
            "离开按钮": _下移矩形(1751, 776, 119, 136),
            "软件按钮": _下移矩形(266, 480, 139, 86),
            "头像控件": _下移矩形(281, 175, 152, 152),
            "昵称锚点": _下移矩形(280, 336, 149, 40),
            # 原来是 [235, 358, 226, 96]
            # 这里按中心轻微缩小，避免视觉上压昵称
            "等级标识": _下移矩形(244, 362, 208, 88),
            "统计区": _下移矩形(479, 190, 767, 166),
            "介绍区": _下移矩形(1322, 194, 362, 142),
            "花式条": _下移矩形(633, 361, 969, 35),
            "竞速条": _下移矩形(632, 411, 969, 35),
            "软件信息": _下移矩形(292, 593, 1383, 274),
            "软件说明": _下移矩形(286, 865, 1340, 44),
        }

        self._字号方案 = {
            "昵称字号": 25,
            "统计字号": 22,
            "介绍字号": 16,
            "下方左字号": 19,
            "下方右字号": 15,
            "进度标签字号": 24,
            "进度LV字号": 25,
        }

        self._间距方案 = {
            "全局字距": 2,
            "统计行距": 38,
            "下方左行距": 8,
            "下方右行距": 4,
            "进度标签间距": 8,
            "进度LV间距": 10,
        }

        self._粗体方案 = {
            "昵称粗体": False,
            "统计粗体": False,
            "介绍粗体": False,
            "下方左粗体": False,
            "下方右粗体": True,
            "进度标签粗体": False,
            "进度LV粗体": False,
        }

        self._失效主界面静态缓存()
        self._缓存尺寸 = (0, 0)

    def _确保缓存(self):
        from ui.top栏 import 生成top栏

        屏幕 = self.上下文["屏幕"]
        宽度, 高度 = 屏幕.get_size()

        if (宽度, 高度) == self._缓存尺寸:
            return

        self._缓存尺寸 = (宽度, 高度)
        self._失效主界面静态缓存()
        self._失效头像预览缓存()

        try:
            if hasattr(self, "_缩放缓存"):
                self._缩放缓存 = {}
        except Exception:
            pass

        暗层 = pygame.Surface((宽度, 高度), pygame.SRCALPHA)
        暗层.fill((0, 0, 0, 128))
        self._遮罩图 = 暗层

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

        self._rect_上面板 = self._布局矩形("上面板")
        self._rect_下面板 = self._布局矩形("下面板")
        self._rect_离开按钮 = self._布局矩形("离开按钮")
        self._rect_软件按钮 = self._布局矩形("软件按钮")
        self._rect_头像控件 = self._布局矩形("头像控件")
        self._rect_昵称锚点 = self._布局矩形("昵称锚点")
        self._rect_等级标识 = self._布局矩形("等级标识")
        self._rect_统计区 = self._布局矩形("统计区")
        self._rect_介绍区 = self._布局矩形("介绍区")
        self._rect_花式条 = self._布局矩形("花式条")
        self._rect_竞速条 = self._布局矩形("竞速条")
        self._rect_软件信息 = self._布局矩形("软件信息")
        self._rect_软件说明 = self._布局矩形("软件说明")

        if self._离开按钮原图 is not None:
            self._离开按钮图 = self._contain缩放(
                self._离开按钮原图,
                self._rect_离开按钮.w,
                self._rect_离开按钮.h,
                透明=True,
            )
        else:
            self._离开按钮图 = None

    def _绘制_上面板(self, 屏幕: pygame.Surface, 缩放: float, 透明: int):
        from core.工具 import 获取字体

        原面板 = self._rect_上面板.copy()
        面板 = 原面板.copy()

        if abs(缩放 - 1.0) > 0.001:
            面板.w = max(1, int(round(面板.w * 缩放)))
            面板.h = max(1, int(round(面板.h * 缩放)))
            面板.center = 原面板.center

        def _随面板缩放(原矩形: pygame.Rect) -> pygame.Rect:
            if abs(缩放 - 1.0) <= 0.001:
                return 原矩形.copy()

            新矩形 = pygame.Rect(
                0,
                0,
                max(1, int(round(原矩形.w * 缩放))),
                max(1, int(round(原矩形.h * 缩放))),
            )
            偏移x = 原矩形.centerx - 原面板.centerx
            偏移y = 原矩形.centery - 原面板.centery
            新矩形.center = (
                int(round(面板.centerx + 偏移x * 缩放)),
                int(round(面板.centery + 偏移y * 缩放)),
            )
            return 新矩形

        if isinstance(self._上面板背景原图, pygame.Surface):
            背景图 = self._取缩放缓存图(
                "个人资料_上背景",
                self._上面板背景原图,
                面板.w,
                面板.h,
            )
            if isinstance(背景图, pygame.Surface):
                背景图 = 背景图.copy()
                背景图.set_alpha(max(0, min(255, int(透明))))
                屏幕.blit(背景图, 面板.topleft)
        else:
            self._绘制圆角面板(
                屏幕, 面板, 背景alpha=175, 线宽=2, 圆角=self._设计值(36, 12)
            )

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

        花式经验 = float(max(0.0, 花式经验))
        竞速经验 = float(max(0.0, 竞速经验))
        花式经验比例 = float(计算经验显示比例(花式等级, 花式经验))
        竞速经验比例 = float(计算经验显示比例(竞速等级, 竞速经验))

        头像rect = _随面板缩放(self._rect_头像控件)
        昵称锚点 = _随面板缩放(self._rect_昵称锚点)
        等级rect = _随面板缩放(self._rect_等级标识)
        统计区 = _随面板缩放(self._rect_统计区)
        介绍区 = _随面板缩放(self._rect_介绍区)
        花式条 = _随面板缩放(self._rect_花式条)
        竞速条 = _随面板缩放(self._rect_竞速条)

        头像图 = self._取圆角头像图(min(头像rect.w, 头像rect.h))
        if 头像图 is not None:
            if 头像图.get_size() != (头像rect.w, 头像rect.h):
                头像图 = self._取缩放缓存图("头像控件", 头像图, 头像rect.w, 头像rect.h)
            if 头像图 is not None:
                头像图 = 头像图.copy()
                头像图.set_alpha(透明)
                屏幕.blit(头像图, 头像rect.topleft)

        昵称字 = 获取字体(
            self._设计字号(self._字号方案["昵称字号"], 12),
            是否粗体=bool(self._粗体方案["昵称粗体"]),
        )
        统计字 = 获取字体(
            self._设计字号(self._字号方案["统计字号"], 10),
            是否粗体=bool(self._粗体方案["统计粗体"]),
        )
        介绍字 = 获取字体(
            self._设计字号(self._字号方案["介绍字号"], 9),
            是否粗体=bool(self._粗体方案["介绍粗体"]),
        )
        标签字 = 获取字体(
            self._设计字号(self._字号方案["进度标签字号"], 10),
            是否粗体=bool(self._粗体方案["进度标签粗体"]),
        )
        等级字 = 获取字体(
            self._设计字号(self._字号方案["进度LV字号"], 10),
            是否粗体=bool(self._粗体方案["进度LV粗体"]),
        )

        全局字距 = self._设计值(self._间距方案["全局字距"], 0)
        统计行距 = self._设计值(self._间距方案["统计行距"], 2)
        标签间距 = self._设计值(self._间距方案["进度标签间距"], 2)
        等级间距 = self._设计值(self._间距方案["进度LV间距"], 2)
        介绍行距 = max(0, self._设计值(3, 0))

        昵称中心x = 昵称锚点.centerx if 昵称锚点.w > 2 else 头像rect.centerx
        昵称顶部y = 昵称锚点.y

        昵称渲染rect = self._绘制文本(
            屏幕,
            昵称,
            昵称字,
            标题白,
            (昵称中心x, 昵称顶部y),
            "midtop",
            字距=全局字距,
        )
        self._rect_昵称_渲染 = 昵称渲染rect.copy()

        if self._等级原图 is not None:
            等级图 = self._取缩放缓存图(
                "等级标识", self._等级原图, 等级rect.w, 等级rect.h
            )
            if 等级图 is not None:
                等级图 = 等级图.copy()
                等级图.set_alpha(透明)
                屏幕.blit(等级图, 等级rect.topleft)

        当前y = 统计区.y + self._设计值(6, 1)
        行定义 = [
            ("游玩时长（分钟）：", str(游玩时长分钟), None),
            ("累计评价S数：", str(累计评价S数), None),
            (
                "最大Combo/曲目：",
                str(最大Combo),
                最大Combo曲目 if 最大Combo曲目 else None,
            ),
            ("最高分/曲目名：", str(最高分), 最高分曲目 if 最高分曲目 else None),
        ]

        最大标题宽 = 0
        for 标题, _, _ in 行定义:
            try:
                最大标题宽 = max(
                    最大标题宽,
                    int(
                        self._渲染字距文本面(标题, 统计字, 标题白, 全局字距).get_width()
                    ),
                )
            except Exception:
                pass

        值列x = min(
            统计区.right - self._设计值(180, 80),
            统计区.x + 最大标题宽 + self._设计值(24, 8),
        )

        for 标题, 数值, 曲目 in 行定义:
            self._绘制文本(
                屏幕,
                标题,
                统计字,
                标题白,
                (统计区.x, 当前y),
                "topleft",
                字距=全局字距,
            )
            数值rect = self._绘制文本(
                屏幕,
                数值,
                统计字,
                数值黄,
                (值列x, 当前y),
                "topleft",
                字距=全局字距,
            )
            if 曲目:
                self._绘制文本(
                    屏幕,
                    f"({曲目})",
                    统计字,
                    曲目紫,
                    (数值rect.right + self._设计值(6, 2), 当前y),
                    "topleft",
                    字距=全局字距,
                )
            当前y += 统计行距

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
            行距=介绍行距,
            字距=全局字距,
        )

        花式标签面 = self._渲染字距文本面("花式经验值：", 标签字, 标题白, 全局字距)
        花式标签面.set_alpha(透明)
        花式标签rect = 花式标签面.get_rect(
            midright=(花式条.left - 标签间距, 花式条.centery)
        )
        屏幕.blit(花式标签面, 花式标签rect.topleft)

        花式等级面 = self._渲染字距文本面(
            f"Lv. {max(1, 花式等级)}", 等级字, 标题白, 全局字距
        )
        花式等级面.set_alpha(透明)
        花式等级rect = 花式等级面.get_rect(
            midleft=(花式条.right + 等级间距, 花式条.centery)
        )
        屏幕.blit(花式等级面, 花式等级rect.topleft)

        self._绘制贴图进度条(
            屏幕,
            花式条,
            进度=float(花式经验比例),
            框原图=self._花式经验框原图,
            值原图=self._花式经验值原图,
            缓存前缀="个人资料_花式经验条",
            透明=透明,
        )

        竞速标签面 = self._渲染字距文本面("竞速经验值：", 标签字, 标题白, 全局字距)
        竞速标签面.set_alpha(透明)
        竞速标签rect = 竞速标签面.get_rect(
            midright=(竞速条.left - 标签间距, 竞速条.centery)
        )
        屏幕.blit(竞速标签面, 竞速标签rect.topleft)

        竞速等级面 = self._渲染字距文本面(
            f"Lv. {max(1, 竞速等级)}", 等级字, 标题白, 全局字距
        )
        竞速等级面.set_alpha(透明)
        竞速等级rect = 竞速等级面.get_rect(
            midleft=(竞速条.right + 等级间距, 竞速条.centery)
        )
        屏幕.blit(竞速等级面, 竞速等级rect.topleft)

        self._绘制贴图进度条(
            屏幕,
            竞速条,
            进度=float(竞速经验比例),
            框原图=self._竞速经验框原图,
            值原图=self._竞速经验值原图,
            缓存前缀="个人资料_竞速经验条",
            透明=透明,
        )

    def _绘制_下面板(self, 屏幕: pygame.Surface, 缩放: float, 透明: int):
        from core.工具 import 获取字体

        原面板 = self._rect_下面板.copy()
        面板 = 原面板.copy()

        if abs(缩放 - 1.0) > 0.001:
            面板.w = max(1, int(round(面板.w * 缩放)))
            面板.h = max(1, int(round(面板.h * 缩放)))
            面板.center = 原面板.center

        def _随面板缩放(原矩形: pygame.Rect) -> pygame.Rect:
            if abs(缩放 - 1.0) <= 0.001:
                return 原矩形.copy()

            新矩形 = pygame.Rect(
                0,
                0,
                max(1, int(round(原矩形.w * 缩放))),
                max(1, int(round(原矩形.h * 缩放))),
            )
            偏移x = 原矩形.centerx - 原面板.centerx
            偏移y = 原矩形.centery - 原面板.centery
            新矩形.center = (
                int(round(面板.centerx + 偏移x * 缩放)),
                int(round(面板.centery + 偏移y * 缩放)),
            )
            return 新矩形

        if isinstance(self._下面板背景原图, pygame.Surface):
            背景图 = self._取缩放缓存图(
                "个人资料_下背景",
                self._下面板背景原图,
                面板.w,
                面板.h,
            )
            if isinstance(背景图, pygame.Surface):
                背景图 = 背景图.copy()
                背景图.set_alpha(max(0, min(255, int(透明))))
                屏幕.blit(背景图, 面板.topleft)
        else:
            self._绘制圆角面板(
                屏幕, 面板, 背景alpha=185, 线宽=2, 圆角=self._设计值(36, 12)
            )

        软件按钮rect = _随面板缩放(self._rect_软件按钮)
        软件信息区 = _随面板缩放(self._rect_软件信息)
        软件说明区 = _随面板缩放(self._rect_软件说明)

        if self._软件信息装饰原图 is not None:
            软件按钮图 = self._取缩放缓存图(
                "软件按钮",
                self._软件信息装饰原图,
                软件按钮rect.w,
                软件按钮rect.h,
            )
            if 软件按钮图 is not None:
                软件按钮图 = 软件按钮图.copy()
                软件按钮图.set_alpha(透明)
                屏幕.blit(软件按钮图, 软件按钮rect.topleft)

        左字 = 获取字体(
            self._设计字号(self._字号方案["下方左字号"], 10),
            是否粗体=bool(self._粗体方案["下方左粗体"]),
        )
        右字 = 获取字体(
            self._设计字号(self._字号方案["下方右字号"], 9),
            是否粗体=bool(self._粗体方案["下方右粗体"]),
        )

        下方左行距 = self._设计值(self._间距方案["下方左行距"], 0)
        下方右行距 = self._设计值(self._间距方案["下方右行距"], 0)
        全局字距 = self._设计值(self._间距方案["全局字距"], 0)

        黄色 = (255, 220, 80)
        白色 = (235, 235, 235)
        浅灰 = (190, 190, 190)

        def _绘制富文本段落(
            起始x: int,
            起始y: int,
            区域: pygame.Rect,
            字体: pygame.font.Font,
            行距: int,
            字距: int,
            行片段列表,
        ):
            if not hasattr(self, "_富文本单字缓存"):
                self._富文本单字缓存 = {}

            def _取字面(单字: str, 颜色):
                缓存键 = (id(字体), 单字, 颜色[0], 颜色[1], 颜色[2])
                已有 = self._富文本单字缓存.get(缓存键)
                if isinstance(已有, pygame.Surface):
                    return 已有
                try:
                    字面 = 字体.render(单字, True, 颜色)
                except Exception:
                    字面 = None
                if isinstance(字面, pygame.Surface):
                    self._富文本单字缓存[缓存键] = 字面
                return 字面

            行高 = max(1, int(字体.get_height()))
            当前y = int(起始y)

            def _落笔一行(字符列表):
                nonlocal 当前y
                if 当前y > 区域.bottom - 2:
                    return
                当前x = int(起始x)
                for 索引, (单字, 颜色) in enumerate(字符列表):
                    字面 = _取字面(单字, 颜色)
                    if isinstance(字面, pygame.Surface):
                        绘制字面 = 字面
                        if 透明 < 255:
                            绘制字面 = 字面.copy()
                            绘制字面.set_alpha(透明)
                        屏幕.blit(绘制字面, (当前x, 当前y))
                        当前x += int(字面.get_width())
                    else:
                        try:
                            当前x += int(字体.size(单字)[0])
                        except Exception:
                            pass
                    if 索引 != len(字符列表) - 1:
                        当前x += int(字距)
                当前y += 行高 + int(行距)

            for 一行片段 in 行片段列表:
                if not 一行片段:
                    当前y += 行高 + int(行距)
                    if 当前y > 区域.bottom - 2:
                        break
                    continue

                字符流 = []
                for 文本, 颜色 in 一行片段:
                    for 单字 in str(文本 or ""):
                        字符流.append((单字, 颜色))

                当前行 = []
                当前宽 = 0

                for 单字, 颜色 in 字符流:
                    try:
                        单字宽 = int(字体.size(单字)[0])
                    except Exception:
                        单字宽 = 0

                    追加宽 = (字距 if 当前行 else 0) + 单字宽
                    if 当前行 and (当前宽 + 追加宽 > 区域.w):
                        _落笔一行(当前行)
                        当前行 = [(单字, 颜色)]
                        当前宽 = 单字宽
                    else:
                        当前行.append((单字, 颜色))
                        当前宽 += 追加宽

                    if 当前y > 区域.bottom - 2:
                        break

                if 当前y > 区域.bottom - 2:
                    break

                if 当前行:
                    _落笔一行(当前行)

                if 当前y > 区域.bottom - 2:
                    break

        主信息片段 = [
            [
                ("游戏版本：", 黄色),
                (f"{self._游戏版本文本}         ", 白色),
                ("开发团队：", 黄色),
                (
                    "程序工程师/策划/游戏制作人：良    UE/UI设计/策划：Emma_H（林曦）",
                    白色,
                ),
            ],
            [("特别鸣谢（排名不分先后）：", 黄色)],
            [("    Cyan（音效提供）|  飞翔e舞模拟器（曲谱资源提供）", 白色)],
            [("LifeErrOr（美术提供）|  小鱼（美术提供）", 白色)],
            [("“e舞时刻”官方粉丝1群参与讨论的群友（反馈提供）", 白色)],
            [],
            [("玩家交流QQ群：1084318862", 白色)],
        ]

        if 软件信息区.w > 8 and 软件信息区.h > 8:
            _绘制富文本段落(
                起始x=软件信息区.x,
                起始y=软件信息区.y,
                区域=软件信息区,
                字体=左字,
                行距=下方左行距,
                字距=全局字距,
                行片段列表=主信息片段,
            )

        说明文本 = (
            "本游戏设计初衷是为了让更多e舞玩家能在各地玩到e舞成名，"
            "本项目纯爱发电，没有任何盈利性质，如您发现有人倒卖本软件，请及时联系我们。"
        )

        if 软件说明区.w > 20 and 软件说明区.h > 16:
            self._绘制自动换行(
                屏幕,
                说明文本,
                右字,
                浅灰,
                软件说明区,
                行距=下方右行距,
                字距=全局字距,
            )

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

    def _失效主界面静态缓存(self):
        self._主界面静态缓存 = None
        self._主界面静态缓存尺寸 = (0, 0)

    def _失效头像预览缓存(self):
        self._头像预览缓存键 = None
        self._头像预览缓存图 = None

    def _取主界面静态缓存(self) -> Optional[pygame.Surface]:
        from core.工具 import 获取字体

        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()
        if isinstance(
            self._主界面静态缓存, pygame.Surface
        ) and self._主界面静态缓存尺寸 == (w, h):
            return self._主界面静态缓存

        缓存面 = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()

        if self._遮罩图 is not None:
            缓存面.blit(self._遮罩图, (0, 0))

        if self._top栏图 is not None:
            缓存面.blit(self._top栏图, self._rect_top栏.topleft)
        if self._top标题图 is not None:
            缓存面.blit(self._top标题图, self._rect_top标题.topleft)
        else:
            标题字 = 获取字体(42, 是否粗体=True)
            self._绘制文本(
                缓存面,
                "个人中心",
                标题字,
                (255, 255, 255),
                (w // 2, self._rect_top栏.centery),
                "center",
            )

        self._绘制_上面板(缓存面, 1.0, 255)
        self._绘制_下面板(缓存面, 1.0, 255)
        self._绘制_离开按钮(缓存面, 255)

        self._主界面静态缓存 = 缓存面
        self._主界面静态缓存尺寸 = (w, h)
        return 缓存面

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

    def _映射到屏幕_rect(self, bbox) -> pygame.Rect:
        left, top, right, bottom = bbox
        return self._设计rect到屏幕rect((left, top, (right - left), (bottom - top)))

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
            值图 = self._取缩放缓存图(f"{缓存前缀}_值", 值原图, 区域.w, 区域.h)
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
            框图 = self._取缩放缓存图(f"{缓存前缀}_框", 框原图, 区域.w, 区域.h)
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

        def _加入候选(路径值: str):
            标准路径 = self._个人资料_规范化头像路径(路径值)
            if 标准路径 and (标准路径 not in 结果):
                结果.append(标准路径)

        _加入候选("UI-img/个人中心-个人资料/默认头像.png")

        try:
            资源目录 = str(getattr(self, "_个人资料目录路径", "") or "")
            if os.path.isdir(资源目录):
                for 文件名 in sorted(os.listdir(资源目录)):
                    小写 = 文件名.lower()
                    if not (
                        小写.endswith(".png")
                        or 小写.endswith(".jpg")
                        or 小写.endswith(".jpeg")
                        or 小写.endswith(".bmp")
                        or 小写.endswith(".webp")
                    ):
                        continue
                    _加入候选(f"UI-img/个人中心-个人资料/{文件名}")
        except Exception:
            pass

        try:
            数据目录 = str(getattr(self, "_个人资料数据目录路径", "") or "")
            if os.path.isdir(数据目录):
                for 文件名 in sorted(os.listdir(数据目录)):
                    小写 = 文件名.lower()
                    if not (
                        小写.endswith(".png")
                        or 小写.endswith(".jpg")
                        or 小写.endswith(".jpeg")
                        or 小写.endswith(".bmp")
                        or 小写.endswith(".webp")
                    ):
                        continue
                    _加入候选(f"json/个人资料/{文件名}")
        except Exception:
            pass

        try:
            当前头像 = str((self._个人资料数据 or {}).get("头像文件", "") or "").strip()
            if 当前头像:
                _加入候选(当前头像)
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
        self._失效头像预览缓存()

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
        self._失效头像预览缓存()
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
            os.makedirs(self._个人资料数据目录路径, exist_ok=True)
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
        目标路径 = os.path.join(self._个人资料数据目录路径, 新文件名)
        try:
            pygame.image.save(图, 目标路径)
        except Exception:
            return False

        try:
            当前头像值 = str((self._个人资料数据 or {}).get("头像文件", "") or "")
            当前头像值 = 当前头像值.replace("\\", "/")
            旧文件名 = os.path.basename(当前头像值)
            if 当前头像值.startswith("json/个人资料/") and 旧文件名 != 新文件名:
                旧路径 = os.path.join(self._个人资料数据目录路径, 旧文件名)
                if os.path.isfile(旧路径):
                    os.remove(旧路径)
        except Exception:
            pass

        self._应用头像路径(f"json/个人资料/{新文件名}")
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
        self._失效主界面静态缓存()
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
        try:
            缓存键 = (
                os.path.abspath(路径),
                max(1, int(边长)),
                int(os.path.getmtime(路径)),
                int(os.path.getsize(路径)),
            )
        except Exception:
            缓存键 = (os.path.abspath(路径), max(1, int(边长)))
        if 缓存键 == self._头像预览缓存键 and isinstance(
            self._头像预览缓存图, pygame.Surface
        ):
            return self._头像预览缓存图
        原图 = self._安全加载图片(路径, 透明=True)
        if 原图 is None:
            return None
        try:
            原图 = 原图.convert_alpha()
        except Exception:
            pass
        方图 = self._cover缩放(原图, int(边长), int(边长))
        预览图 = self._contain缩放(方图, int(边长), int(边长), 透明=True)
        self._头像预览缓存键 = 缓存键
        self._头像预览缓存图 = 预览图
        return 预览图

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
                pygame.draw.rect(屏幕, (42, 73, 128), r, border_radius=max(8, r.h // 3))
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
                        self._头像候选索引 = (self._头像候选索引 - 1) % len(
                            self._头像候选路径列表
                        )
                    return True
                if 事件.key in (pygame.K_RIGHT, pygame.K_d):
                    self._头像待导入源路径 = ""
                    if self._头像候选路径列表:
                        self._头像候选索引 = (self._头像候选索引 + 1) % len(
                            self._头像候选路径列表
                        )
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
                if isinstance(区域rect, pygame.Rect) and (
                    not 区域rect.collidepoint(pos)
                ):
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
                            self._头像候选索引 = (self._头像候选索引 + 1) % len(
                                self._头像候选路径列表
                            )
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
                if isinstance(区域rect, pygame.Rect) and (
                    not 区域rect.collidepoint(pos)
                ):
                    self._关闭二次弹窗()
                    return True
                if self._弹窗按钮.get(
                    "昵称_输入框", pygame.Rect(0, 0, 0, 0)
                ).collidepoint(pos):
                    self._弹窗昵称输入激活 = True
                    try:
                        pygame.key.start_text_input()
                        pygame.key.set_text_input_rect(self._弹窗输入框)
                    except Exception:
                        pass
                    return True
                if self._弹窗按钮.get(
                    "昵称_确定", pygame.Rect(0, 0, 0, 0)
                ).collidepoint(pos):
                    self._应用昵称(self._弹窗昵称文本)
                    self._关闭二次弹窗()
                    return True
                if self._弹窗按钮.get(
                    "昵称_返回", pygame.Rect(0, 0, 0, 0)
                ).collidepoint(pos):
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

    def 退出(self):
        pygame.time.set_timer(self._事件_延迟切场景, 0)
        self._关闭二次弹窗()

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

    def 绘制(self):
        from core.工具 import 绘制底部联网与信用, 获取字体

        屏幕 = self.上下文["屏幕"]
        self._确保缓存()
        w, h = 屏幕.get_size()

        屏幕.fill((0, 0, 0))
        背景面 = self._背景视频.读取覆盖帧(w, h) if self._背景视频 else None
        if 背景面 is not None:
            屏幕.blit(背景面, (0, 0))

        t = (time.time() - float(self._入场开始)) / max(0.001, float(self._入场时长))
        t = self._缓出(t)
        面板缩放 = 0.99 + 0.01 * t
        面板透明 = max(0, min(255, int(255 * t)))

        使用静态缓存 = bool(
            (not bool(self.上下文.get("布局调试_开启", False))) and t >= 0.999
        )
        if 使用静态缓存:
            静态层 = self._取主界面静态缓存()
            if 静态层 is not None:
                屏幕.blit(静态层, (0, 0))
        else:
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

            self._绘制_上面板(屏幕, 面板缩放, 面板透明)
            self._绘制_下面板(屏幕, 面板缩放, 面板透明)
            self._绘制_离开按钮(屏幕, 面板透明)

        字体_credit = self.上下文["字体"].get("投币_credit字")
        信用 = "0"
        try:
            状态 = self.上下文.get("状态", {})
            信用 = str(int(状态.get("投币数", 0) or 0))
        except Exception:
            信用 = "0"

        所需信用 = int(self.上下文.get("状态", {}).get("每局所需信用", 3) or 3)
        绘制底部联网与信用(
            屏幕=屏幕,
            联网原图=self._联网原图,
            字体_credit=字体_credit,
            credit数值=f"{信用}/{所需信用}",
            总信用需求=所需信用,
        )

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

    def 处理全局踏板(self, 动作: str):
        if 动作 != 踏板动作_确认:
            return None
        if self._弹窗类型 or self._全屏放大过渡.是否进行中():
            return None
        self._触发离开()
        return None

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
                "经验版本": int(经验数据版本),
                "段位": "UI-img/个人中心-个人资料/等级/1.png",
                "花式": 构建默认模式进度(),
                "竞速": 构建默认模式进度(),
            },
        }

    def _个人资料_规范化头像路径(self, 值) -> str:
        文本 = str(值 or "").strip().replace("\\", "/")
        if not 文本:
            return "UI-img/个人中心-个人资料/默认头像.png"
        if os.path.isabs(文本):
            return 文本
        if 文本.startswith("UI-img/") or 文本.startswith("json/"):
            return 文本

        文件名 = os.path.basename(文本)
        if 文件名.lower().startswith("头像_"):
            return f"json/个人资料/{文件名}"

        return f"UI-img/个人中心-个人资料/{文件名}"

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
        运行根 = str(getattr(self, "_运行根", _公共取运行根目录()) or _公共取运行根目录())
        资源根 = str(getattr(self, "_资源根", _公共取项目根目录()) or _公共取项目根目录())

        if 文本.startswith(f"json{os.sep}"):
            return os.path.join(运行根, 文本)
        if 文本.startswith(f"UI-img{os.sep}"):
            return os.path.join(资源根, 文本)

        文件名 = os.path.basename(文本)
        if 文件名.lower().startswith("头像_"):
            return os.path.join(运行根, "json", "个人资料", 文件名)
        return os.path.join(资源根, "UI-img", "个人中心-个人资料", 文件名)

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
        经验版本 = int(进度.get("经验版本", 0) or 0)
        进度["花式"] = 规范化模式进度(
            进度.get("花式", {}),
            最大等级=int(进度["最大等级"]),
            经验版本=经验版本,
        )
        进度["竞速"] = 规范化模式进度(
            进度.get("竞速", {}),
            最大等级=int(进度["最大等级"]),
            经验版本=经验版本,
        )
        进度["经验版本"] = int(经验数据版本)

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
            os.makedirs(
                os.path.dirname(os.path.abspath(self._个人资料json路径)),
                exist_ok=True,
            )
        except Exception:
            pass

        try:
            os.makedirs(
                str(getattr(self, "_个人资料数据目录路径", "") or ""),
                exist_ok=True,
            )
        except Exception:
            pass

        try:
            准备写入 = dict(数据 or {})
            准备写入["头像文件"] = self._个人资料_规范化头像路径(
                准备写入.get("头像文件", "UI-img/个人中心-个人资料/默认头像.png")
            )

            进度 = 准备写入.get("进度", {})
            if isinstance(进度, dict):
                try:
                    花式等级 = int((进度.get("花式", {}) or {}).get("等级", 1) or 1)
                except Exception:
                    花式等级 = 1
                try:
                    竞速等级 = int((进度.get("竞速", {}) or {}).get("等级", 1) or 1)
                except Exception:
                    竞速等级 = 1
                默认段位 = self._个人资料_计算段位(max(花式等级, 竞速等级))
                进度["段位"] = self._个人资料_规范化段位路径(
                    进度.get("段位", ""),
                    默认段位,
                )
                准备写入["进度"] = 进度

            临时路径 = self._个人资料json路径 + ".tmp"
            with open(临时路径, "w", encoding="utf-8") as 文件:
                json.dump(准备写入, 文件, ensure_ascii=False, indent=2)
            os.replace(临时路径, self._个人资料json路径)
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
        self._失效主界面静态缓存()
        self._失效头像预览缓存()

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
        self._失效主界面静态缓存()

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
                if 窗 is not None and bool(
                    getattr(窗, "winfo_exists", lambda: False)()
                ):
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
        经验增加值: int = 0,
    ):
        """
        给其他场景使用的个人资料更新入口。
        统计项会按单首歌累加，但等级经验必须由调用方显式传入 `经验增加值`，
        这里不再保留旧的“每首歌固定 +0.1 / 满 1.0 升级”逻辑。
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
        经验版本 = int(进度.get("经验版本", 0) or 0)

        模式键 = (
            "花式"
            if ("花" in str(模式))
            else ("竞速" if ("竞" in str(模式)) else "花式")
        )
        模式进度 = 规范化模式进度(
            进度.get(模式键, 构建默认模式进度()),
            最大等级=最大等级,
            经验版本=经验版本,
        )
        进度["经验版本"] = int(经验数据版本)

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

        入账结果 = 处理经验入账(
            模式进度,
            增加经验值=max(0, int(经验增加值 or 0)),
        )
        模式进度 = 规范化模式进度(
            入账结果.get("模式进度", 模式进度),
            最大等级=最大等级,
            经验版本=经验数据版本,
        )
        进度[模式键] = 模式进度

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

    def 进入(self):
        资源 = self.上下文.get("资源", {})
        状态 = self.上下文.get("状态", {})

        根目录 = _公共取项目根目录(资源)
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
        self._失效主界面静态缓存()
        self._失效头像预览缓存()

        # 布局改为纯硬编码，但仍保留统一初始化入口
        self._布局覆盖_加载并应用()

        # 进入时重新读一次个人资料（别的场景可能写过）
        self._个人资料数据 = self._个人资料_读取并修复(是否回写=False)
        self._个人资料_刷新头像原图()
        self._个人资料_刷新段位图标()

        self._确保缓存()
