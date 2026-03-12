import json
import math
import os
import time
from typing import Dict, List, Optional, Tuple

import pygame

from core.常量与路径 import 取运行根目录 as _公共取运行根目录
from core.对局状态 import (
    取信用数,
    取每局所需信用,
    重置游戏流程状态,
)
from core.踏板控制 import 踏板动作_左, 踏板动作_右, 踏板动作_确认
from core.歌曲记录 import 更新歌曲最高分
from core.工具 import 绘制底部联网与信用
from scenes.场景基类 import 场景基类
from ui.settlement_layout_shared import (
    SettlementLayoutStore,
    fit_size,
    get_font,
    parse_color,
    render_text_surface,
)
from ui.settlement_scene_shared import (
    加载结算提示资源,
    执行返回选歌 as _执行共享返回选歌,
    构建继续动作,
    构建返回选歌动作 as _构建共享返回选歌动作,
    推进对局流程,
    取资源根目录 as _取资源根目录,
    解析结算流程上下文,
)


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


def _线性插值(a: float, b: float, t: float) -> float:
    return float(a) + (float(b) - float(a)) * _夹取(t, 0.0, 1.0)


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
        self._流程1时长秒 = 3.0
        self._流程2时长秒 = 3.0
        self._经验窗入场秒 = 0.55
        self._背景图: Optional[pygame.Surface] = None
        self._面板图: Optional[pygame.Surface] = None
        self._封面图: Optional[pygame.Surface] = None
        self._评级图: Optional[pygame.Surface] = None
        self._全连图: Optional[pygame.Surface] = None
        self._失败图: Optional[pygame.Surface] = None
        self._新纪录图: Optional[pygame.Surface] = None
        self._等级窗背景图: Optional[pygame.Surface] = None
        self._等级窗底图: Optional[pygame.Surface] = None
        self._花式经验框图: Optional[pygame.Surface] = None
        self._花式经验值图: Optional[pygame.Surface] = None
        self._竞速经验框图: Optional[pygame.Surface] = None
        self._竞速经验值图: Optional[pygame.Surface] = None
        self._经验数字图集: Dict[str, pygame.Surface] = {}
        self._升级图集: Dict[str, pygame.Surface] = {}
        self._提示图集: Dict[str, pygame.Surface] = {}
        self._倒计时图集: Dict[str, pygame.Surface] = {}
        self._是按钮图: Optional[pygame.Surface] = None
        self._否按钮图: Optional[pygame.Surface] = None
        self._段位图: Optional[pygame.Surface] = None
        self._联网原图: Optional[pygame.Surface] = None
        self._缩放缓存: Dict[Tuple[int, int, int], pygame.Surface] = {}
        self._流程1缓存尺寸: Tuple[int, int] = (0, 0)
        self._流程1最终图: Optional[pygame.Surface] = None
        self._流程1虚化图: Optional[pygame.Surface] = None
        self._玩家序号 = 1

        self._流程3提示入场秒 = 1.0
        self._流程3阶段持续秒 = 3.0
        self._流程3内容退场秒 = 1.0

        self._流程3提示键 = ""
        self._流程3阶段类型 = ""
        self._流程3阶段开始秒 = 0.0

        self._流程3退出开始秒 = 0.0

        self._流程3是否显示倒计时 = False
        self._流程3继续动作: Optional[dict] = None
        self._流程3默认否动作: Optional[dict] = None
        self._流程3按钮选中 = "是"
        self._流程3退出动作: Optional[dict] = None
        self._流程3当前关卡 = 1
        self._流程3每局所需信用 = 3
        self._流程3是否失败 = False
        self._流程3结算后S数 = 0
        self._流程3三把S赠送 = False
        self._流程3是按钮rect = pygame.Rect(0, 0, 1, 1)
        self._流程3否按钮rect = pygame.Rect(0, 0, 1, 1)
        self._布局存储: Optional[SettlementLayoutStore] = None
        self._运行时布局缓存: Dict[str, Dict[str, object]] = {}
        self._运行时布局缓存键: Optional[Tuple[int, int, int, Optional[float], str]] = (
            None
        )

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

    def 进入(self, 载荷=None):
        self._载荷 = dict(载荷) if isinstance(载荷, dict) else {}
        self._进入系统秒 = time.perf_counter()
        self._已切结算BGM = False
        self._缩放缓存.clear()
        self._奖励数据 = {}
        self._歌曲记录结果 = {}
        self._流程1缓存尺寸 = (0, 0)
        self._流程1最终图 = None
        self._流程1虚化图 = None
        self._运行时布局缓存 = {}
        self._运行时布局缓存键 = None
        self._加载资源()
        self._更新个人资料()
        self._配置流程状态()
        self._播放结算音效()

    def _配置流程3初始流程(self):
        if self._流程3三把S赠送:
            self._准备流程3进入下一把(
                下一关卡=4,
                提示键="赠送一把",
                提示秒数=3.0,
                累计S数=3,
                赠送第四把=True,
            )
            return
        if self._流程3当前关卡 in (1, 2):
            if not self._流程3是否失败:
                self._准备流程3进入下一把(
                    下一关卡=self._流程3当前关卡 + 1,
                    提示键="下一把",
                    提示秒数=3.0,
                    累计S数=self._流程3结算后S数,
                    赠送第四把=False,
                )
            else:
                self._进入流程3是否继续分支(
                    下一关卡=self._流程3当前关卡 + 1,
                    重开新局=False,
                )
            return
        self._进入流程3是否继续分支(下一关卡=1, 重开新局=True)

    def _进入流程3是否继续分支(self, *, 下一关卡: int, 重开新局: bool):
        if 取信用数(self.上下文.get("状态", {})) >= int(self._流程3每局所需信用):
            self._进入流程3继续挑战提示(
                下一关卡=下一关卡,
                重开新局=bool(重开新局),
            )
            return
        self._流程3阶段类型 = "续币等待"
        self._流程3提示键 = "是否续币"
        self._流程3阶段开始秒 = time.perf_counter()
        self._流程3阶段持续秒 = 10.0
        self._流程3是否显示倒计时 = True
        self._流程3继续动作 = 构建继续动作(
            self._构建返回选歌动作(),
            下一关卡=下一关卡,
            重开新局=重开新局,
            累计S数=self._流程3结算后S数,
            每局所需信用=self._流程3每局所需信用,
        )
        self._流程3默认否动作 = {"类型": "投币"}

    def _进入流程3继续挑战提示(self, *, 下一关卡: int, 重开新局: bool):
        self._流程3阶段类型 = "继续挑战"
        self._流程3提示键 = "继续挑战"
        self._流程3阶段开始秒 = time.perf_counter()
        self._流程3阶段持续秒 = 10.0
        self._流程3是否显示倒计时 = True
        self._流程3按钮选中 = "是"
        self._流程3继续动作 = 构建继续动作(
            self._构建返回选歌动作(),
            下一关卡=下一关卡,
            重开新局=重开新局,
            累计S数=self._流程3结算后S数,
            每局所需信用=self._流程3每局所需信用,
            需要消耗信用=True,
        )
        self._流程3默认否动作 = {"类型": "投币"}

    def _进入流程3自动提示(
        self,
        *,
        提示键: str,
        持续秒: float,
        动作: dict,
        显示倒计时: bool = False,
    ):
        self._流程3阶段类型 = "自动提示"
        self._流程3提示键 = str(提示键 or "")
        self._流程3阶段开始秒 = time.perf_counter()
        self._流程3阶段持续秒 = float(max(0.1, 持续秒))
        self._流程3继续动作 = dict(动作 or {})
        self._流程3是否显示倒计时 = bool(显示倒计时)

    def _准备流程3进入下一把(
        self,
        *,
        下一关卡: int,
        提示键: str,
        提示秒数: float,
        累计S数: int,
        赠送第四把: bool,
        消耗数量: int = 0,
        重开新局: bool = False,
    ):
        推进对局流程(
            self.上下文.get("状态", {}),
            下一关卡=下一关卡,
            累计S数=累计S数,
            赠送第四把=赠送第四把,
            消耗数量=消耗数量,
            重开新局=重开新局,
        )
        self._进入流程3自动提示(
            提示键=提示键,
            持续秒=提示秒数,
            动作=self._构建返回选歌动作(),
            显示倒计时=False,
        )

    def _处理流程3续币成功(self):
        动作 = dict(self._流程3继续动作 or {})
        下一关卡 = int(动作.get("下一关卡", 1) or 1)
        重开新局 = bool(动作.get("重开新局", False))
        累计S数 = int(动作.get("累计S数", 0) or 0)
        self._准备流程3进入下一把(
            下一关卡=下一关卡,
            提示键="下一把",
            提示秒数=3.0,
            累计S数=累计S数,
            赠送第四把=False,
            消耗数量=int(self._流程3每局所需信用),
            重开新局=重开新局,
        )

    def _执行流程3是分支(self):
        动作 = dict(self._流程3继续动作 or {})
        下一关卡 = int(动作.get("下一关卡", 1) or 1)
        重开新局 = bool(动作.get("重开新局", False))
        累计S数 = int(动作.get("累计S数", 0) or 0)
        推进对局流程(
            self.上下文.get("状态", {}),
            下一关卡=下一关卡,
            累计S数=累计S数,
            赠送第四把=False,
            消耗数量=int(动作.get("消耗信用", 0) or 0),
            重开新局=重开新局,
        )
        self._开始流程3退出(self._构建返回选歌动作())

    def _执行流程3否分支(self):
        self._开始流程3退出(dict(self._流程3默认否动作 or {"类型": "投币"}))

    def _开始流程3退出(self, 动作: dict):
        if self._流程3退出动作 is not None:
            return
        self._流程3退出动作 = dict(动作 or {})
        self._流程3退出开始秒 = time.perf_counter()

    def _构建流程3退出结果(self, 动作: dict):
        类型 = str((动作 or {}).get("类型", "") or "")
        if 类型 == "投币":
            重置游戏流程状态(self.上下文.get("状态", {}))
            return {"切换到": "投币", "禁用黑屏过渡": True}
        if 类型 == "选歌":
            return self._返回选歌(动作)
        return None

    def _布局文件路径(self) -> str:
        根目录 = _取资源根目录(self.上下文)
        return os.path.join(根目录, "json", "结算场景布局.json")

    def _刷新布局存储(self) -> SettlementLayoutStore:
        布局路径 = self._布局文件路径()
        if self._布局存储 is None or self._布局存储.layout_path != os.path.abspath(
            布局路径
        ):
            self._布局存储 = SettlementLayoutStore(布局路径)
        else:
            self._布局存储.reload_if_changed()
        return self._布局存储

    def _取运行时布局(self, 屏幕尺寸: Tuple[int, int]) -> Dict[str, Dict[str, object]]:
        存储 = self._刷新布局存储()
        键 = (
            int(屏幕尺寸[0]),
            int(屏幕尺寸[1]),
            int(self._玩家序号),
            getattr(存储, "_mtime", None),
            str(self._流程3提示键 or ""),
        )
        if 键 != self._运行时布局缓存键:
            self._运行时布局缓存 = 存储.runtime_layers(
                屏幕尺寸, player_index=self._玩家序号
            )
            self._运行时布局缓存键 = 键
        return self._运行时布局缓存

    def _取布局层(self, 屏幕尺寸: Tuple[int, int], 图层id: str) -> Dict[str, object]:
        图层 = self._取运行时布局(屏幕尺寸).get(str(图层id), {})
        return 图层 if isinstance(图层, dict) else {}

    def _取布局矩形(
        self,
        屏幕尺寸: Tuple[int, int],
        图层id: str,
        默认值: Optional[pygame.Rect] = None,
    ) -> pygame.Rect:
        图层 = self._取布局层(屏幕尺寸, 图层id)
        rect = (
            图层.get("rect", [0, 0, 0, 0]) if isinstance(图层, dict) else [0, 0, 0, 0]
        )
        if isinstance(rect, (list, tuple)) and len(rect) == 4:
            return pygame.Rect(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        return (
            默认值.copy()
            if isinstance(默认值, pygame.Rect)
            else pygame.Rect(0, 0, 0, 0)
        )

    def _取布局局部矩形(
        self, 屏幕尺寸: Tuple[int, int], 图层id: str, 基准图层id: str
    ) -> pygame.Rect:
        rect = self._取布局矩形(屏幕尺寸, 图层id)
        基准 = self._取布局矩形(屏幕尺寸, 基准图层id)
        return pygame.Rect(rect.x - 基准.x, rect.y - 基准.y, rect.w, rect.h)

    def _取图层内容缩放(self, 图层: Dict[str, object]) -> Tuple[float, float]:
        raw = 图层.get("content_scale", [1.0, 1.0])
        if isinstance(raw, (list, tuple)) and len(raw) == 2:
            try:
                return max(0.05, float(raw[0])), max(0.05, float(raw[1]))
            except Exception:
                return (1.0, 1.0)
        return (1.0, 1.0)

    def _取图层内容偏移(self, 图层: Dict[str, object]) -> Tuple[float, float]:
        raw = 图层.get("content_offset", [0.0, 0.0])
        if isinstance(raw, (list, tuple)) and len(raw) == 2:
            try:
                return float(raw[0]), float(raw[1])
            except Exception:
                return (0.0, 0.0)
        return (0.0, 0.0)

    def _拟合图层内容矩形(
        self, 图层: Dict[str, object], 基础矩形: pygame.Rect, surface: pygame.Surface
    ) -> pygame.Rect:
        fit_mode = str(图层.get("fit", "contain") or "contain")
        scale_x, scale_y = self._取图层内容缩放(图层)
        size = fit_size(surface.get_size(), 基础矩形.size, fit_mode)
        width = max(1, int(round(size[0] * scale_x)))
        height = max(1, int(round(size[1] * scale_y)))
        style = (
            图层.get("text_style", {})
            if isinstance(图层.get("text_style"), dict)
            else {}
        )
        align = str(style.get("align", "center") or "center")
        offset_x, offset_y = self._取图层内容偏移(图层)
        rect = pygame.Rect(0, 0, width, height)
        if align == "left":
            rect.midleft = (基础矩形.left, 基础矩形.centery)
        elif align == "right":
            rect.midright = (基础矩形.right, 基础矩形.centery)
        else:
            rect.center = 基础矩形.center
        rect.x += int(round(offset_x))
        rect.y += int(round(offset_y))
        return rect

    def _绘制布局文本(
        self,
        屏幕: pygame.Surface,
        图层id: str,
        文本: str,
        区域: Optional[pygame.Rect] = None,
        默认字号: int = 24,
        默认颜色: Tuple[int, int, int] = (255, 255, 255),
        默认描边颜色: Tuple[int, int, int] = (0, 0, 0),
        默认描边粗细: int = 0,
        默认字间距: int = 0,
        默认粗体: bool = False,
        默认对齐: str = "center",
    ):
        基础矩形 = 区域 or self._取布局矩形(屏幕.get_size(), 图层id)
        if 基础矩形.w <= 0 or 基础矩形.h <= 0 or not 文本:
            return
        图层 = self._取布局层(屏幕.get_size(), 图层id)
        self._绘制指定图层文本(
            屏幕,
            图层,
            基础矩形,
            文本,
            默认字号=默认字号,
            默认颜色=默认颜色,
            默认描边颜色=默认描边颜色,
            默认描边粗细=默认描边粗细,
            默认字间距=默认字间距,
            默认粗体=默认粗体,
            默认对齐=默认对齐,
        )

    def _绘制指定图层文本(
        self,
        屏幕: pygame.Surface,
        图层: Dict[str, object],
        基础矩形: pygame.Rect,
        文本: str,
        默认字号: int = 24,
        默认颜色: Tuple[int, int, int] = (255, 255, 255),
        默认描边颜色: Tuple[int, int, int] = (0, 0, 0),
        默认描边粗细: int = 0,
        默认字间距: int = 0,
        默认粗体: bool = False,
        默认对齐: str = "center",
    ):
        if 基础矩形.w <= 0 or 基础矩形.h <= 0 or not 文本:
            return
        style = (
            图层.get("text_style", {})
            if isinstance(图层.get("text_style"), dict)
            else {}
        )
        if not style:
            style = {"align": 默认对齐}
        文字图 = render_text_surface(
            str(文本 or ""),
            int(style.get("font_size", 默认字号) or 默认字号),
            parse_color(style.get("color", list(默认颜色)), 默认颜色),
            bool(style.get("bold", 默认粗体)),
            parse_color(style.get("stroke_color", list(默认描边颜色)), 默认描边颜色),
            int(style.get("stroke_width", 默认描边粗细) or 默认描边粗细),
            int(style.get("letter_spacing", 默认字间距) or 默认字间距),
        )
        内容矩形 = self._拟合图层内容矩形(图层, 基础矩形, 文字图)
        待绘图 = 文字图
        if 内容矩形.size != 文字图.get_size():
            待绘图 = pygame.transform.smoothscale(文字图, 内容矩形.size).convert_alpha()
        屏幕.blit(待绘图, 内容矩形.topleft)

    def _绘制布局滚动文本(
        self,
        屏幕: pygame.Surface,
        图层id: str,
        文本: str,
        滚动秒: float,
        默认字号: int = 24,
        默认颜色: Tuple[int, int, int] = (255, 255, 255),
        默认粗体: bool = False,
    ):
        区域 = self._取布局矩形(屏幕.get_size(), 图层id)
        if 区域.w <= 0 or 区域.h <= 0 or not 文本:
            return
        图层 = self._取布局层(屏幕.get_size(), 图层id)
        style = (
            图层.get("text_style", {})
            if isinstance(图层.get("text_style"), dict)
            else {}
        )
        字体 = get_font(
            int(style.get("font_size", 默认字号) or 默认字号),
            bool(style.get("bold", 默认粗体)),
        )
        self._绘制滚动文本(
            屏幕,
            文本=str(文本 or ""),
            字体=字体,
            颜色=parse_color(style.get("color", list(默认颜色)), 默认颜色),
            区域=区域,
            滚动秒=float(滚动秒),
        )

    def _取流程阶段(self, 经过秒: float) -> Tuple[int, float]:
        流程1终点 = float(self._流程1时长秒)
        流程2终点 = 流程1终点 + float(self._流程2时长秒)
        if 经过秒 < 流程1终点:
            return 1, float(max(0.0, 经过秒))
        if 经过秒 < 流程2终点:
            return 2, float(max(0.0, 经过秒 - 流程1终点))
        return 3, float(max(0.0, 经过秒 - 流程2终点))

    def _取结算面板矩形(self, 屏宽: int, 屏高: int) -> pygame.Rect:
        return self._取布局矩形((屏宽, 屏高), "panel")

    def _取奖励窗矩形(self, 面板矩形: pygame.Rect, 屏宽: int, 屏高: int) -> pygame.Rect:
        return self._取布局矩形((屏宽, 屏高), "reward_bg")

    def _渲染流程1层图(self, 尺寸: Tuple[int, int], 经过秒: float) -> pygame.Surface:
        屏宽, 屏高 = int(尺寸[0]), int(尺寸[1])
        图层 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
        面板矩形 = self._取结算面板矩形(屏宽, 屏高)
        self._绘制结算面板(图层, 面板矩形, float(经过秒))
        return 图层

    def _模糊图层(self, 图层: pygame.Surface) -> pygame.Surface:
        w, h = 图层.get_size()
        小图 = pygame.transform.smoothscale(
            图层, (max(1, int(w * 0.22)), max(1, int(h * 0.22)))
        ).convert_alpha()
        return pygame.transform.smoothscale(小图, (w, h)).convert_alpha()

    def _确保流程1缓存(self, 尺寸: Tuple[int, int]):
        目标尺寸 = (int(尺寸[0]), int(尺寸[1]))
        if (
            self._流程1最终图 is not None
            and self._流程1虚化图 is not None
            and self._流程1缓存尺寸 == 目标尺寸
        ):
            return
        最终图 = self._渲染流程1层图(目标尺寸, float(self._流程1时长秒))
        self._流程1最终图 = 最终图
        self._流程1虚化图 = self._模糊图层(最终图)
        self._流程1缓存尺寸 = 目标尺寸

    def _绘制流程1层(
        self,
        屏幕: pygame.Surface,
        经过秒: float,
        是否虚化: bool = False,
        总透明度: float = 1.0,
    ):
        屏宽, 屏高 = 屏幕.get_size()
        if 是否虚化:
            self._确保流程1缓存((屏宽, 屏高))
            图层 = self._流程1虚化图
        else:
            图层 = self._渲染流程1层图((屏宽, 屏高), float(经过秒))
        if 图层 is None:
            return
        待绘图 = 图层
        if (总透明度 < 0.999) or 是否虚化:
            try:
                待绘图 = 图层.copy()
                if 是否虚化:
                    暗化层 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
                    暗化层.fill((0, 0, 0, int(128 * max(0.0, min(1.0, 总透明度)))))
                    待绘图.blit(暗化层, (0, 0))
                if 总透明度 < 0.999:
                    待绘图.set_alpha(int(255 * max(0.0, min(1.0, 总透明度))))
            except Exception:
                待绘图 = 图层
        屏幕.blit(待绘图, (0, 0))

    def _绘制封面区域(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        pygame.draw.rect(屏幕, (20, 20, 20), 区域)
        图层 = self._取布局层(屏幕.get_size(), "cover")
        if self._封面图 is not None:
            内容rect = self._拟合图层内容矩形(图层, 区域, self._封面图)
            图 = self._缩放图(self._封面图, 内容rect.size)
            if 图 is not None:
                屏幕.blit(图, 内容rect.topleft)
                return
        占位 = self._占位字体.render("NO IMAGE", True, (230, 230, 230))
        屏幕.blit(占位, 占位.get_rect(center=区域.center))

    def _绘制右侧数值(
        self,
        屏幕: pygame.Surface,
        右x: int,
        中心y: int,
        文本: str,
        描边颜色: Tuple[int, int, int],
    ):
        self._绘制描边文本(
            屏幕=屏幕,
            文本=文本,
            字体=self._数值字体,
            颜色=(255, 255, 255),
            描边颜色=描边颜色,
            中心=(int(右x), int(中心y)),
            描边粗细=1,
            对齐="right",
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

        if bool(self._载荷.get("三把S赠送", False)):
            self._绘制三S评级动画(屏幕, 面板矩形, 进度)
            return

        屏幕尺寸 = 屏幕.get_size()
        目标rect = self._取布局矩形(屏幕尺寸, "grade_main")
        目标宽 = int(max(2, 目标rect.w))
        目标高 = int(max(2, 目标rect.h))

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

        目标中心 = 目标rect.center
        起始中心x = -动画宽 // 2
        当前中心x = int(起始中心x + (目标中心[0] - 起始中心x) * _回弹(进度))
        当前中心y = int(目标中心[1])
        rr = 图.get_rect(center=(当前中心x, 当前中心y))
        屏幕.blit(图, rr.topleft)

    def _绘制三S评级动画(
        self, 屏幕: pygame.Surface, 面板矩形: pygame.Rect, 进度: float
    ):
        if self._评级图 is None:
            return

        屏幕尺寸 = 屏幕.get_size()
        主rect = self._取布局矩形(屏幕尺寸, "grade_main")
        左rect = self._取布局矩形(屏幕尺寸, "grade_left")
        右rect = self._取布局矩形(屏幕尺寸, "grade_right")
        目标中心 = 主rect.center
        主宽 = int(max(2, 主rect.w))
        主高 = int(max(2, 主rect.h))
        动画缩放 = 1.0 + (1.30 - 1.0) * (1.0 - _回弹(进度))
        主宽 = max(2, int(主宽 * 动画缩放))
        主高 = max(2, int(主高 * 动画缩放))
        副宽 = max(2, int(左rect.w * 动画缩放))
        副高 = max(2, int(左rect.h * 动画缩放))
        alpha = int(255 * _缓出三次方(进度))

        def _画单个(图宽: int, 图高: int, 目标x: int, 目标y: int):
            图 = self._缩放图(self._评级图, (图宽, 图高))
            if 图 is None:
                return
            try:
                图 = 图.copy()
                图.set_alpha(alpha)
            except Exception:
                pass
            起始x = -图宽 // 2
            当前x = int(起始x + (目标x - 起始x) * _回弹(进度))
            rr = 图.get_rect(center=(当前x, 目标y))
            屏幕.blit(图, rr.topleft)

        _画单个(副宽, 副高, 左rect.centerx, 左rect.centery)
        _画单个(主宽, 主高, 目标中心[0], 目标中心[1])
        _画单个(
            max(2, int(右rect.w * 动画缩放)),
            max(2, int(右rect.h * 动画缩放)),
            右rect.centerx,
            右rect.centery,
        )

    def _绘制顶部状态动画(
        self, 屏幕: pygame.Surface, 面板矩形: pygame.Rect, 经过秒: float
    ):
        顶部图 = self._获取顶部状态图()
        if 顶部图 is None:
            return
        开始秒 = self._数值动画秒 + self._评级砸入秒
        进度 = _夹取((经过秒 - 开始秒) / float(self._顶部砸入秒), 0.0, 1.0)
        if 进度 <= 0.0:
            return

        目标rect = self._取布局矩形(屏幕.get_size(), "top_badge")
        目标宽 = int(max(2, 目标rect.w))
        目标高 = int(max(2, 目标rect.h))
        缩放 = 1.0 + (1.30 - 1.0) * (1.0 - _回弹(进度))
        动画宽 = max(2, int(目标宽 * 缩放))
        动画高 = max(2, int(目标高 * 缩放))
        图 = self._缩放图(顶部图, (动画宽, 动画高))
        if 图 is None:
            return
        try:
            图 = 图.copy()
            图.set_alpha(int(255 * _缓出三次方(进度)))
        except Exception:
            pass

        目标中心 = 目标rect.center
        起始中心y = 目标rect.top - 动画高
        当前中心y = int(起始中心y + (目标中心[1] - 起始中心y) * _回弹(进度))
        rr = 图.get_rect(center=(目标中心[0], 当前中心y))
        屏幕.blit(图, rr.topleft)

    def _获取顶部状态图(self) -> Optional[pygame.Surface]:
        评级 = str(self._载荷.get("评级", "") or "").strip().upper()
        if bool(self._载荷.get("失败", False)) or 评级 == "F":
            return self._失败图
        if bool(self._载荷.get("是否全连", False)) or bool(
            self._载荷.get("全连", False)
        ):
            return self._全连图
        return None

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
        目标rect = self._取布局矩形(屏幕.get_size(), "new_record")
        目标宽 = int(max(2, 目标rect.w))
        目标高 = int(max(2, 目标rect.h))
        缩放 = 0.86 + 0.14 * _回弹(t)
        图 = self._缩放图(self._新纪录图, (int(目标宽 * 缩放), int(目标高 * 缩放)))
        if 图 is None:
            return
        try:
            图 = 图.copy()
            图.set_alpha(int(255 * _缓出三次方(t)))
        except Exception:
            pass
        rr = 图.get_rect(center=目标rect.center)
        屏幕.blit(图, rr.topleft)

    def _绘制经验奖励数字(
        self,
        屏幕: pygame.Surface,
        区域: pygame.Rect,
        实际屏幕尺寸: Tuple[int, int],
    ):
        奖励经验 = int((self._奖励数据 or {}).get("经验增加值", 0) or 0)
        文本 = f"+{奖励经验}"
        图列表: List[pygame.Surface] = []
        for ch in 文本:
            图 = self._经验数字图集.get(ch)
            if 图 is not None:
                图列表.append(图)
        数字图层 = self._取布局层(实际屏幕尺寸, "reward_digits")
        数字rect = self._取布局局部矩形(实际屏幕尺寸, "reward_digits", "reward_bg")
        if 数字rect.w <= 0 or 数字rect.h <= 0:
            return
        if not 图列表:
            回退图 = render_text_surface(文本, 36, (245, 230, 92), True, (50, 40, 0), 1)
            内容rect = self._拟合图层内容矩形(数字图层, 数字rect, 回退图)
            屏幕.blit(
                pygame.transform.smoothscale(回退图, 内容rect.size).convert_alpha(),
                内容rect.topleft,
            )
            return

        目标高 = max(28, max(int(图.get_height()) for 图 in 图列表))
        总宽 = 0
        缩放图列: List[pygame.Surface] = []

        数字间距 = 8

        for 图源 in 图列表:
            比例 = float(目标高) / float(max(1, 图源.get_height()))
            目标宽 = int(max(10, 图源.get_width() * 比例))
            图 = self._缩放图(图源, (目标宽, 目标高))
            if 图 is None:
                continue
            缩放图列.append(图)
            总宽 += 图.get_width()

        总宽 += max(0, len(缩放图列) - 1) * 数字间距
        数字图 = pygame.Surface((max(1, 总宽), max(1, 目标高)), pygame.SRCALPHA)

        x = 0
        for 图 in 缩放图列:
            数字图.blit(图, (x, 0))
            x += 图.get_width() + 数字间距

        内容rect = self._拟合图层内容矩形(数字图层, 数字rect, 数字图)
        待绘图 = (
            数字图
            if 内容rect.size == 数字图.get_size()
            else pygame.transform.smoothscale(数字图, 内容rect.size).convert_alpha()
        )
        屏幕.blit(待绘图, 内容rect.topleft)

    def _绘制经验进度区(
        self,
        屏幕: pygame.Surface,
        区域: pygame.Rect,
        经过秒: float,
        实际屏幕尺寸: Tuple[int, int],
    ):
        奖励 = self._奖励数据 or {}
        组列表 = [
            (
                "花式",
                "花式经验：",
                "style_label",
                "style_fill",
                "style_frame",
                "style_lv",
                self._花式经验框图,
                self._花式经验值图,
            ),
            (
                "竞速",
                "竞速经验：",
                "speed_label",
                "speed_fill",
                "speed_frame",
                "speed_lv",
                self._竞速经验框图,
                self._竞速经验值图,
            ),
        ]
        for 模式名, 标签文本, 标签id, 填充id, 框id, 等级id, 框图源, 值图源 in 组列表:
            数据 = (
                奖励.get(模式名, {}) if isinstance(奖励.get(模式名, {}), dict) else {}
            )
            动画状态 = self._计算经验动画状态(模式名, 经过秒)
            等级 = int(动画状态.get("等级", 数据.get("等级", 1)) or 1)
            经验 = float(
                max(
                    0.0,
                    min(
                        1.0,
                        float(动画状态.get("经验", 数据.get("经验", 0.0)) or 0.0),
                    ),
                )
            )
            填充rect = self._取布局局部矩形(实际屏幕尺寸, 填充id, "reward_bg")
            框rect = self._取布局局部矩形(实际屏幕尺寸, 框id, "reward_bg")
            self._绘制结算贴图经验条(
                屏幕=屏幕,
                填充rect=填充rect,
                框rect=框rect,
                经验值=经验,
                框图源=框图源,
                值图源=值图源,
            )
            标签图层 = self._取布局层(实际屏幕尺寸, 标签id)
            标签rect = self._取布局局部矩形(实际屏幕尺寸, 标签id, "reward_bg")
            self._绘制指定图层文本(
                屏幕,
                标签图层,
                标签rect,
                标签文本,
                默认字号=18,
                默认颜色=(240, 240, 245),
                默认对齐="left",
            )
            等级图层 = self._取布局层(实际屏幕尺寸, 等级id)
            等级rect = self._取布局局部矩形(实际屏幕尺寸, 等级id, "reward_bg")
            self._绘制指定图层文本(
                屏幕,
                等级图层,
                等级rect,
                f"Lv : {等级}",
                默认字号=22,
                默认颜色=(245, 245, 245),
                默认对齐="left",
            )

    def _绘制段位区(
        self,
        屏幕: pygame.Surface,
        区域: pygame.Rect,
        实际屏幕尺寸: Tuple[int, int],
    ):
        图标图层 = self._取布局层(实际屏幕尺寸, "rank_icon")
        图标rect = self._取布局局部矩形(实际屏幕尺寸, "rank_icon", "reward_bg")
        if self._段位图 is not None and 图标rect.w > 0 and 图标rect.h > 0:
            内容rect = self._拟合图层内容矩形(图标图层, 图标rect, self._段位图)
            图 = self._缩放图(self._段位图, 内容rect.size)
            if 图 is not None:
                屏幕.blit(图, 内容rect.topleft)

    def _计算经验动画状态(self, 模式名: str, 经过秒: float) -> Dict[str, object]:
        奖励 = self._奖励数据 or {}
        数据 = 奖励.get(模式名, {}) if isinstance(奖励.get(模式名, {}), dict) else {}
        原等级 = int(数据.get("原等级", 数据.get("等级", 1)) or 1)
        原经验 = float(数据.get("原经验", 数据.get("经验", 0.0)) or 0.0)
        新等级 = int(数据.get("等级", 原等级) or 原等级)
        新经验 = float(数据.get("经验", 原经验) or 原经验)
        总增长 = max(0.0, (新等级 - 原等级) + (新经验 - 原经验))
        动画开始秒 = float(self._经验窗入场秒) + 0.20
        动画时长 = max(0.30, float(self._流程2时长秒) - 动画开始秒 - 0.35)
        进度 = _夹取((经过秒 - 动画开始秒) / 动画时长, 0.0, 1.0)
        已增长 = float(总增长) * float(进度)

        当前等级 = int(原等级)
        当前经验 = float(原经验 + 已增长)
        升级节点: List[float] = []
        if 总增长 > 1e-6:
            剩余 = float(总增长)
            临时经验 = float(原经验)
            临时等级 = int(原等级)
            已消费 = 0.0
            while 剩余 > 1e-6 and 临时等级 < 70:
                需要值 = max(0.0, 1.0 - 临时经验)
                if 剩余 + 1e-6 < 需要值 or 需要值 <= 1e-6:
                    break
                已消费 += 需要值
                升级节点.append(float(已消费 / max(1e-6, 总增长)))
                剩余 -= 需要值
                临时经验 = 0.0
                临时等级 += 1
            while 当前经验 >= 1.0 and 当前等级 < 70:
                当前经验 -= 1.0
                当前等级 += 1
        if 进度 >= 0.999:
            当前等级 = int(新等级)
            当前经验 = float(新经验)

        升级动画t = None
        if 升级节点 and 进度 >= 升级节点[0]:
            起点 = float(升级节点[0])
            升级动画t = _夹取((进度 - 起点) / max(0.01, 1.0 - 起点), 0.0, 1.0)

        return {
            "等级": int(max(1, 当前等级)),
            "经验": float(max(0.0, min(1.0, 当前经验))),
            "进度": float(进度),
            "升级动画t": 升级动画t,
            "升级次数": int(max(0, 新等级 - 原等级)),
        }

    def _流程3计算按钮布局(self, 屏宽: int, 屏高: int):
        def _取按钮尺寸(原图: Optional[pygame.Surface]) -> Tuple[int, int]:
            默认比例 = 2.2
            图片比例 = 默认比例
            if 原图 is not None:
                try:
                    原宽, 原高 = 原图.get_size()
                    if 原宽 > 0 and 原高 > 0:
                        图片比例 = float(原宽) / float(原高)
                except Exception:
                    图片比例 = 默认比例

            目标高 = max(72, min(120, int(屏高 * 0.10)))
            目标宽 = int(round(float(目标高) * float(图片比例)))

            最大宽 = max(140, int(屏宽 * 0.18))
            最小宽 = 120

            if 目标宽 > 最大宽:
                目标宽 = 最大宽
                目标高 = max(52, int(round(float(目标宽) / max(0.1, float(图片比例)))))

            if 目标宽 < 最小宽:
                目标宽 = 最小宽
                目标高 = max(52, int(round(float(目标宽) / max(0.1, float(图片比例)))))

            return max(1, int(目标宽)), max(1, int(目标高))

        是宽, 是高 = _取按钮尺寸(self._是按钮图)
        否宽, 否高 = _取按钮尺寸(self._否按钮图)

        间距 = max(24, int(max(是宽, 否宽) * 0.20))
        中心y = int(屏高 * 0.60)

        总宽 = int(是宽 + 否宽 + 间距)
        起始x = int(屏宽 // 2 - 总宽 // 2)

        self._流程3是按钮rect = pygame.Rect(起始x, 0, 是宽, 是高)
        self._流程3否按钮rect = pygame.Rect(起始x + 是宽 + 间距, 0, 否宽, 否高)

        self._流程3是按钮rect.centery = 中心y
        self._流程3否按钮rect.centery = 中心y

    def _绘制流程3选择按钮(self, 屏幕: pygame.Surface, 透明度系数: float):
        屏宽, 屏高 = 屏幕.get_size()
        self._流程3计算按钮布局(屏宽, 屏高)
        self._绘制流程3按钮(
            屏幕,
            self._是按钮图,
            self._流程3是按钮rect,
            self._流程3按钮选中 == "是",
            透明度系数,
        )
        self._绘制流程3按钮(
            屏幕,
            self._否按钮图,
            self._流程3否按钮rect,
            self._流程3按钮选中 == "否",
            透明度系数,
        )

    def _绘制流程3按钮(
        self,
        屏幕: pygame.Surface,
        原图: Optional[pygame.Surface],
        基准rect: pygame.Rect,
        是否选中: bool,
        透明度系数: float,
    ):
        放大系数 = 1.08 if 是否选中 else 1.0

        外框宽 = max(1, int(round(float(基准rect.w) * 放大系数)))
        外框高 = max(1, int(round(float(基准rect.h) * 放大系数)))
        外框rect = pygame.Rect(0, 0, 外框宽, 外框高)
        外框rect.center = 基准rect.center

        图片宽, 图片高 = self._按比例适配图片尺寸(原图, 外框rect.size)
        图片rect = pygame.Rect(0, 0, 图片宽, 图片高)
        图片rect.center = 外框rect.center

        if 原图 is None:
            pygame.draw.rect(
                屏幕,
                (245, 245, 245, int(210 * max(0.0, min(1.0, 透明度系数)))),
                外框rect,
                border_radius=max(12, 外框rect.h // 4),
                width=2,
            )
            return

        图 = self._缩放图(原图, 图片rect.size)
        if 图 is None:
            return

        try:
            图 = 图.copy()
            图.set_alpha(int(255 * max(0.0, min(1.0, 透明度系数))))
        except Exception:
            pass

        屏幕.blit(图, 图片rect.topleft)

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

    def _绘制滚动文本(
        self,
        屏幕: pygame.Surface,
        文本: str,
        字体: pygame.font.Font,
        颜色: Tuple[int, int, int],
        区域: pygame.Rect,
        滚动秒: float,
        速度: float = 72.0,
        停留秒: float = 0.6,
    ):
        if not 文本:
            return
        try:
            图 = 字体.render(str(文本), True, 颜色).convert_alpha()
        except Exception:
            return
        if 图.get_width() <= 区域.w:
            rr = 图.get_rect(center=区域.center)
            屏幕.blit(图, rr.topleft)
            return

        最大偏移 = max(0, 图.get_width() - 区域.w)
        if 最大偏移 <= 0:
            rr = 图.get_rect(center=区域.center)
            屏幕.blit(图, rr.topleft)
            return

        滚动时长 = float(最大偏移) / max(1.0, float(速度))
        周期 = float(停留秒) * 2.0 + 滚动时长
        局部秒 = float(滚动秒) % max(0.01, 周期)
        if 局部秒 <= float(停留秒):
            偏移 = 0.0
        elif 局部秒 <= float(停留秒) + 滚动时长:
            偏移 = (局部秒 - float(停留秒)) * float(速度)
        else:
            偏移 = float(最大偏移)

        裁切 = pygame.Surface((区域.w, 区域.h), pygame.SRCALPHA)
        裁切.blit(
            图,
            (-int(round(偏移)), max(0, (区域.h - 图.get_height()) // 2)),
        )
        屏幕.blit(裁切, 区域.topleft)

    def _绘制描边文本(
        self,
        屏幕: pygame.Surface,
        文本: str,
        字体: pygame.font.Font,
        颜色: Tuple[int, int, int],
        描边颜色: Tuple[int, int, int],
        中心: Tuple[int, int],
        描边粗细: int = 1,
        对齐: str = "center",
    ):
        if not 文本:
            return
        try:
            主图 = 字体.render(str(文本), True, 颜色).convert_alpha()
            描边图 = 字体.render(str(文本), True, 描边颜色).convert_alpha()
        except Exception:
            return

        对齐 = str(对齐 or "center").lower()
        if 对齐 == "right":
            基准x = int(中心[0] - 主图.get_width())
        elif 对齐 == "left":
            基准x = int(中心[0])
        else:
            基准x = int(中心[0] - 主图.get_width() // 2)
        基准y = int(中心[1] - 主图.get_height() // 2)

        半径 = max(0, int(描边粗细))
        for dx in range(-半径, 半径 + 1):
            for dy in range(-半径, 半径 + 1):
                if dx == 0 and dy == 0:
                    continue
                屏幕.blit(描边图, (基准x + dx, 基准y + dy))
        屏幕.blit(主图, (基准x, 基准y))

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
            所需信用 = int((状态 or {}).get("每局所需信用", 3) or 3)
        except Exception:
            投币数 = 0
            所需信用 = 3
        try:
            绘制底部联网与信用(
                屏幕=屏幕,
                联网原图=getattr(self, "_联网原图", None),
                字体_credit=字体_credit,
                credit数值=f"{max(0, 投币数)}/{int(max(1, 所需信用))}",
                总信用需求=int(max(1, 所需信用)),
                文本=f"CREDIT：{max(0, 投币数)}/{int(max(1, 所需信用))}",
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

        根目录 = _取资源根目录(self.上下文)
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
        根目录 = _取资源根目录(self.上下文)
        音乐路径 = os.path.join(根目录, "冷资源", "backsound", "back_music_ui.mp3")
        try:
            if pygame.mixer.get_init() and os.path.isfile(音乐路径):
                pygame.mixer.music.stop()
                pygame.mixer.music.load(音乐路径)
                pygame.mixer.music.play(-1)
        except Exception:
            pass

    def _播放游戏结束音效(self):
        try:
            if not pygame.mixer.get_init():
                return
        except Exception:
            return
        根目录 = _取资源根目录(self.上下文)
        音效路径 = os.path.join(根目录, "冷资源", "backsound", "gameover.mp3")
        try:
            if os.path.isfile(音效路径):
                pygame.mixer.music.stop()
                pygame.mixer.music.load(音效路径)
                pygame.mixer.music.play()
        except Exception:
            pass

    def _个人资料路径(self) -> str:
        候选路径列表 = [os.path.join(_公共取运行根目录(), "json", "个人资料.json")]

        for 候选路径 in 候选路径列表:
            try:
                if 候选路径 and os.path.isfile(候选路径):
                    return 候选路径
            except Exception:
                continue

        return 候选路径列表[0]

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
        评级 = str(self._载荷.get("评级", "F") or "F").strip().upper()
        是否失败 = bool(self._载荷.get("失败", False)) or 评级 == "F"
        奖励经验值 = 0 if 是否失败 else 10

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
        当前经验 = float(模式进度.get("经验", 0.0) or 0.0) + (float(奖励经验值) / 100.0)
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

        根目录 = _取资源根目录(self.上下文)
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
                "原等级": int(
                    (原模式进度 if 模式键 == "花式" else (花式进度 or {})).get(
                        "等级", 1
                    )
                    or 1
                ),
                "原经验": float(
                    (原模式进度 if 模式键 == "花式" else (花式进度 or {})).get(
                        "经验", 0.0
                    )
                    or 0.0
                ),
                "等级": int((花式进度 or {}).get("等级", 1) or 1),
                "经验": float((花式进度 or {}).get("经验", 0.0) or 0.0),
            },
            "竞速": {
                "原等级": int(
                    (原模式进度 if 模式键 == "竞速" else (竞速进度 or {})).get(
                        "等级", 1
                    )
                    or 1
                ),
                "原经验": float(
                    (原模式进度 if 模式键 == "竞速" else (竞速进度 or {})).get(
                        "经验", 0.0
                    )
                    or 0.0
                ),
                "等级": int((竞速进度 or {}).get("等级", 1) or 1),
                "经验": float((竞速进度 or {}).get("经验", 0.0) or 0.0),
            },
            "段位路径": 段位相对路径,
        }

    def _流程3是否允许交互(self, 当前系统秒: Optional[float] = None) -> bool:
        if self._流程3退出动作 is not None:
            return False
        if self._流程3阶段类型 != "继续挑战":
            return False
        return self._流程3是否已完成入场(当前系统秒)

    def 处理事件(self, 事件):
        经过秒 = max(0.0, float(time.perf_counter() - float(self._进入系统秒 or 0.0)))
        流程阶段, _ = self._取流程阶段(经过秒)
        当前系统秒 = time.perf_counter()

        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
            if 流程阶段 == 3:
                if self._流程3是否允许交互(当前系统秒):
                    self._执行流程3否分支()
                return None
            return self._返回选歌()

        if 流程阶段 != 3 or (not self._流程3是否允许交互(当前系统秒)):
            return None

        if 事件.type == pygame.MOUSEMOTION:
            if self._流程3是按钮rect.collidepoint(事件.pos):
                self._流程3按钮选中 = "是"
            elif self._流程3否按钮rect.collidepoint(事件.pos):
                self._流程3按钮选中 = "否"
            return None

        if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            if self._流程3是按钮rect.collidepoint(事件.pos):
                self._执行流程3是分支()
            elif self._流程3否按钮rect.collidepoint(事件.pos):
                self._执行流程3否分支()
            return None

        if 事件.type == pygame.KEYDOWN:
            if 事件.key in (pygame.K_LEFT, pygame.K_KP1, pygame.K_a):
                self._流程3按钮选中 = "是"
            elif 事件.key in (pygame.K_RIGHT, pygame.K_KP3, pygame.K_d):
                self._流程3按钮选中 = "否"
            elif 事件.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_KP5):
                if self._流程3按钮选中 == "是":
                    self._执行流程3是分支()
                else:
                    self._执行流程3否分支()
            elif 事件.key == pygame.K_y:
                self._执行流程3是分支()
            elif 事件.key == pygame.K_n:
                self._执行流程3否分支()

        return None

    def 处理全局踏板(self, 动作: str):
        经过秒 = max(0.0, float(time.perf_counter() - float(self._进入系统秒 or 0.0)))
        流程阶段, _ = self._取流程阶段(经过秒)
        当前系统秒 = time.perf_counter()

        if 流程阶段 != 3 or (not self._流程3是否允许交互(当前系统秒)):
            return None

        if 动作 == 踏板动作_左:
            self._流程3按钮选中 = "是"
            return None
        if 动作 == 踏板动作_右:
            self._流程3按钮选中 = "否"
            return None
        if 动作 == 踏板动作_确认:
            if self._流程3按钮选中 == "是":
                self._执行流程3是分支()
            else:
                self._执行流程3否分支()
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

        场景入场t = _夹取(经过秒 / 0.45, 0.0, 1.0)
        场景黑幕alpha = int((1.0 - _缓出三次方(场景入场t)) * 255.0)

        面板矩形 = self._取结算面板矩形(屏宽, 屏高)
        流程阶段, 阶段秒 = self._取流程阶段(经过秒)

        if 流程阶段 == 1:
            self._绘制流程1层(屏幕, 经过秒, 是否虚化=False, 总透明度=1.0)

        elif 流程阶段 == 2:
            self._绘制流程1层(屏幕, self._流程1时长秒, 是否虚化=True, 总透明度=1.0)
            self._绘制奖励小窗(屏幕, 面板矩形, 阶段秒, 总透明度=1.0)

        else:
            流程3入场t = _夹取(
                阶段秒 / max(0.01, float(self._流程3提示入场秒)),
                0.0,
                1.0,
            )
            流程3入场透明 = _缓出三次方(流程3入场t)

            if self._流程3退出动作 is None and 流程3入场透明 < 0.999:
                旧界面透明 = 1.0 - 流程3入场透明
                if 旧界面透明 > 0.0:
                    self._绘制流程1层(
                        屏幕,
                        self._流程1时长秒,
                        是否虚化=True,
                        总透明度=旧界面透明,
                    )
                    self._绘制奖励小窗(
                        屏幕,
                        面板矩形,
                        self._流程2时长秒,
                        总透明度=旧界面透明,
                        固定最终=True,
                    )

            流程3黑幕透明 = 1.0 if self._流程3退出动作 is not None else 流程3入场透明
            if 流程3黑幕透明 > 0.0:
                流程3黑幕 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
                流程3黑幕.fill((0, 0, 0, int(255 * _夹取(流程3黑幕透明, 0.0, 1.0))))
                屏幕.blit(流程3黑幕, (0, 0))

            提示透明 = self._取流程3界面透明度(阶段秒)
            if 提示透明 > 0.0:
                self._绘制流程3提示(屏幕, 阶段秒, 提示透明)
                if self._流程3阶段类型 == "继续挑战":
                    self._绘制流程3选择按钮(屏幕, 提示透明)
                if self._流程3是否显示倒计时:
                    self._绘制流程3倒计时(屏幕, 提示透明)

        self._绘制底部币值(屏幕)

        if 场景黑幕alpha > 0:
            黑幕 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
            黑幕.fill((0, 0, 0, 场景黑幕alpha))
            屏幕.blit(黑幕, (0, 0))

    def _取流程3界面透明度(self, 阶段秒: float) -> float:
        if self._流程3退出动作 is not None:
            退出t = _夹取(
                (time.perf_counter() - float(self._流程3退出开始秒 or 0.0))
                / max(0.01, float(self._流程3内容退场秒 or 0.0)),
                0.0,
                1.0,
            )
            return _夹取(1.0 - _缓出三次方(退出t), 0.0, 1.0)

        入场t = _夹取(
            阶段秒 / max(0.01, float(self._流程3提示入场秒)),
            0.0,
            1.0,
        )
        return _夹取(_缓出三次方(入场t), 0.0, 1.0)

    def _配置流程状态(self):
        try:
            玩家序号 = int(self._载荷.get("玩家序号", 1) or 1)
        except Exception:
            玩家序号 = 1
        self._玩家序号 = 2 if 玩家序号 == 2 else 1
        self._运行时布局缓存 = {}
        self._运行时布局缓存键 = None
        流程上下文 = 解析结算流程上下文(self._载荷, self.上下文.get("状态", {}))
        self._流程3当前关卡 = int(流程上下文["当前关卡"])
        self._流程3是否失败 = bool(流程上下文["是否失败"])
        self._流程3结算后S数 = int(流程上下文["结算后S数"])
        self._流程3三把S赠送 = bool(流程上下文["三把S赠送"])
        self._流程3每局所需信用 = int(取每局所需信用(self.上下文.get("状态", {})) or 3)
        self._流程3阶段类型 = ""
        self._流程3提示键 = ""
        self._流程3阶段开始秒 = 0.0
        self._流程3计时已启动 = False
        self._流程3阶段持续秒 = 0.0
        self._流程3是否显示倒计时 = False
        self._流程3继续动作 = None
        self._流程3默认否动作 = None
        self._流程3按钮选中 = "是"
        self._流程3退出动作 = None
        self._流程3退出开始秒 = 0.0
        self._配置流程3初始流程()

    def _确保流程3计时起点(self, 当前系统秒: Optional[float] = None):
        if bool(getattr(self, "_流程3计时已启动", False)):
            return

        if 当前系统秒 is None:
            当前系统秒 = time.perf_counter()

        经过秒 = max(0.0, float(当前系统秒 - float(self._进入系统秒 or 0.0)))
        流程阶段, _ = self._取流程阶段(经过秒)
        if 流程阶段 < 3:
            return

        self._流程3阶段开始秒 = float(当前系统秒)
        self._流程3计时已启动 = True

    def _取流程3已持续秒(self, 当前系统秒: Optional[float] = None) -> float:
        if 当前系统秒 is None:
            当前系统秒 = time.perf_counter()

        self._确保流程3计时起点(当前系统秒)

        if not bool(getattr(self, "_流程3计时已启动", False)):
            return 0.0

        return max(0.0, float(当前系统秒) - self._取流程3可见起始秒())

    def _流程3是否已完成入场(self, 当前系统秒: Optional[float] = None) -> bool:
        if 当前系统秒 is None:
            当前系统秒 = time.perf_counter()

        self._确保流程3计时起点(当前系统秒)

        if not bool(getattr(self, "_流程3计时已启动", False)):
            return False

        return float(当前系统秒) >= self._取流程3可见起始秒()

    def _取流程3可见起始秒(self) -> float:
        self._确保流程3计时起点()
        if not bool(getattr(self, "_流程3计时已启动", False)):
            return float("inf")
        return float(self._流程3阶段开始秒 or 0.0) + float(
            max(0.0, float(self._流程3提示入场秒 or 0.0))
        )

    def _按比例适配图片尺寸(
        self, 原图: Optional[pygame.Surface], 目标尺寸: Tuple[int, int]
    ) -> Tuple[int, int]:
        目标宽 = max(1, int(目标尺寸[0]))
        目标高 = max(1, int(目标尺寸[1]))
        if 原图 is None:
            return 目标宽, 目标高
        try:
            原宽, 原高 = 原图.get_size()
            if 原宽 <= 0 or 原高 <= 0:
                return 目标宽, 目标高
            缩放比例 = min(
                float(目标宽) / float(max(1, 原宽)),
                float(目标高) / float(max(1, 原高)),
            )
            适配宽 = max(1, int(round(float(原宽) * 缩放比例)))
            适配高 = max(1, int(round(float(原高) * 缩放比例)))
            return 适配宽, 适配高
        except Exception:
            return 目标宽, 目标高

    def 更新(self):
        经过秒 = max(0.0, float(time.perf_counter() - float(self._进入系统秒 or 0.0)))

        if (not self._已切结算BGM) and (经过秒 >= float(self._结算音效时长秒 or 0.0)):
            self._播放结算背景音乐()

        流程阶段, _ = self._取流程阶段(经过秒)
        if 流程阶段 < 3:
            return None

        当前系统秒 = time.perf_counter()
        可见已持续秒 = self._取流程3已持续秒(当前系统秒)

        if self._流程3退出动作 is not None:
            if (当前系统秒 - float(self._流程3退出开始秒 or 当前系统秒)) >= float(
                max(0.01, float(self._流程3内容退场秒 or 0.0))
            ):
                return self._构建流程3退出结果(self._流程3退出动作)
            return None

        self._尝试播放流程3倒计时音效(当前系统秒)

        if self._流程3阶段类型 == "自动提示":
            if self._流程3是否已完成入场(当前系统秒) and (
                可见已持续秒 >= float(self._流程3阶段持续秒 or 0.0)
            ):
                self._开始流程3退出(dict(self._流程3继续动作 or {}))
            return None

        if self._流程3阶段类型 == "续币等待":
            当前信用 = 取信用数(self.上下文.get("状态", {}))
            if 当前信用 >= int(self._流程3每局所需信用):
                self._处理流程3续币成功()
                return None

            if self._流程3是否已完成入场(当前系统秒) and (
                可见已持续秒 >= float(self._流程3阶段持续秒 or 0.0)
            ):
                self._播放游戏结束音效()
                self._进入流程3自动提示(
                    提示键="游戏结束",
                    持续秒=3.0,
                    动作={"类型": "投币"},
                    显示倒计时=False,
                )
            return None

        if self._流程3阶段类型 == "继续挑战":
            if self._流程3是否已完成入场(当前系统秒) and (
                可见已持续秒 >= float(self._流程3阶段持续秒 or 0.0)
            ):
                self._执行流程3否分支()
        return None

    def _绘制流程3提示(
        self, 屏幕: pygame.Surface, 阶段秒: float, 透明度系数: float = 1.0
    ):
        图 = self._提示图集.get(str(self._流程3提示键 or ""))
        if 图 is None:
            return

        t = _夹取(
            阶段秒 / max(0.01, float(self._流程3提示入场秒)),
            0.0,
            1.0,
        )

        提示rect = self._取布局矩形(屏幕.get_size(), "flow3_prompt")
        放大倍率, 上移像素 = self._取流程3提示显示参数(
            str(self._流程3提示键 or ""),
            int(屏幕.get_height()),
        )

        容器宽 = int(max(2, round(float(提示rect.w) * float(放大倍率))))
        容器高 = int(max(2, round(float(提示rect.h) * float(放大倍率))))

        基准宽, 基准高 = self._按比例适配图片尺寸(图, (容器宽, 容器高))

        动画缩放 = _线性插值(1.12, 1.0, t)
        动画宽 = int(max(2, round(float(基准宽) * 动画缩放)))
        动画高 = int(max(2, round(float(基准高) * 动画缩放)))

        动画图 = self._缩放图(图, (动画宽, 动画高))
        if 动画图 is None:
            return

        try:
            动画图 = 动画图.copy()
            动画图.set_alpha(int(255 * _缓出三次方(t) * _夹取(透明度系数, 0.0, 1.0)))
        except Exception:
            pass

        rr = 动画图.get_rect(
            center=(提示rect.centerx, int(提示rect.centery - 上移像素))
        )
        屏幕.blit(动画图, rr.topleft)

    def _绘制流程3倒计时(self, 屏幕: pygame.Surface, 透明度系数: float):
        if not self._流程3是否显示倒计时:
            return

        剩余秒 = self._取流程3剩余秒()

        文本 = str(剩余秒)
        图列表 = [self._倒计时图集.get(ch) for ch in 文本 if self._倒计时图集.get(ch)]
        if not 图列表:
            return

        间距 = 4
        总宽 = sum(图.get_width() for 图 in 图列表) + max(0, len(图列表) - 1) * 间距
        最大高 = max(图.get_height() for 图 in 图列表)
        画布 = pygame.Surface((max(1, 总宽), max(1, 最大高)), pygame.SRCALPHA)

        x = 0
        for 图 in 图列表:
            try:
                单图 = 图.copy()
                单图.set_alpha(int(255 * 透明度系数))
            except Exception:
                单图 = 图
            画布.blit(单图, (x, 0))
            x += 图.get_width() + 间距

        rr = 画布.get_rect(
            center=(屏幕.get_width() // 2, int(屏幕.get_height() * 0.80))
        )
        屏幕.blit(画布, rr.topleft)

    def _取流程3提示显示参数(self, 提示键: str, 屏幕高: int) -> Tuple[float, int]:
        默认上移 = max(36, int(屏幕高 * 0.06))
        默认倍率 = 1.5

        配置表 = {
            "继续挑战": (
                2.05,
                max(58, int(屏幕高 * 0.085)),
            ),
            "是否续币": (
                2.18,
                max(62, int(屏幕高 * 0.090)),
            ),
        }

        return 配置表.get(str(提示键 or "").strip(), (默认倍率, 默认上移))

    def _取流程3剩余秒(self, 当前系统秒: Optional[float] = None) -> int:
        if 当前系统秒 is None:
            当前系统秒 = time.perf_counter()

        已持续秒 = self._取流程3已持续秒(当前系统秒)
        return max(
            0,
            int(math.ceil(float(self._流程3阶段持续秒 or 0.0) - float(已持续秒))),
        )

    def _尝试加载流程3倒计时音效(self) -> Optional[pygame.mixer.Sound]:
        已有音效 = getattr(self, "_流程3倒计时音效", None)
        if 已有音效 is not None:
            return 已有音效

        if bool(getattr(self, "_流程3倒计时音效已尝试加载", False)):
            return None

        try:
            if not pygame.mixer.get_init():
                return None
        except Exception:
            return None

        self._流程3倒计时音效已尝试加载 = True

        根目录 = _取资源根目录(self.上下文)
        音效路径 = os.path.join(根目录, "冷资源", "Buttonsound", "倒计时音效.mp3")

        try:
            if os.path.isfile(音效路径):
                self._流程3倒计时音效 = pygame.mixer.Sound(音效路径)
                return self._流程3倒计时音效
        except Exception:
            pass

        self._流程3倒计时音效 = None
        return None

    def _尝试播放流程3倒计时音效(self, 当前系统秒: Optional[float] = None):
        if 当前系统秒 is None:
            当前系统秒 = time.perf_counter()

        if not self._流程3是否显示倒计时:
            self._流程3倒计时阶段签名 = None
            self._流程3倒计时上次剩余秒 = None
            return

        if self._流程3退出动作 is not None:
            return

        if not self._流程3是否已完成入场(当前系统秒):
            return

        当前阶段签名 = (
            str(self._流程3阶段类型 or ""),
            str(self._流程3提示键 or ""),
            float(self._流程3阶段开始秒 or 0.0),
            float(self._流程3阶段持续秒 or 0.0),
            bool(self._流程3是否显示倒计时),
        )

        if getattr(self, "_流程3倒计时阶段签名", None) != 当前阶段签名:
            self._流程3倒计时阶段签名 = 当前阶段签名
            self._流程3倒计时上次剩余秒 = None

        当前剩余秒 = self._取流程3剩余秒(当前系统秒)
        上次剩余秒 = getattr(self, "_流程3倒计时上次剩余秒", None)

        if 上次剩余秒 == 当前剩余秒:
            return

        self._流程3倒计时上次剩余秒 = 当前剩余秒

        倒计时音效 = self._尝试加载流程3倒计时音效()
        if 倒计时音效 is None:
            return

        try:
            if not pygame.mixer.get_init():
                return
        except Exception:
            return

        try:
            倒计时音效.play()
        except Exception:
            pass

    def _绘制结算贴图经验条(
        self,
        屏幕: pygame.Surface,
        填充rect: pygame.Rect,
        框rect: pygame.Rect,
        经验值: float,
        框图源: Optional[pygame.Surface],
        值图源: Optional[pygame.Surface],
    ):
        try:
            经验值 = float(经验值)
        except Exception:
            经验值 = 0.0
        经验值 = max(0.0, min(1.0, float(经验值)))

        基础rect = 框rect if 框rect.w > 0 and 框rect.h > 0 else 填充rect
        if 基础rect.w <= 0 or 基础rect.h <= 0:
            return

        圆角 = max(2, int(基础rect.h // 2))

        def _圆角遮罩(宽: int, 高: int, 半径: int) -> pygame.Surface:
            遮罩 = pygame.Surface((max(1, int(宽)), max(1, int(高))), pygame.SRCALPHA)
            遮罩.fill((0, 0, 0, 0))
            pygame.draw.rect(
                遮罩,
                (255, 255, 255, 255),
                pygame.Rect(0, 0, int(宽), int(高)),
                border_radius=max(0, int(半径)),
            )
            return 遮罩

        pygame.draw.rect(
            屏幕,
            (20, 32, 60),
            基础rect,
            border_radius=max(4, 基础rect.h // 2),
        )

        if 框rect.w > 0 and 框rect.h > 0:
            实际填充rect = pygame.Rect(框rect.x, 框rect.y, 框rect.w, 框rect.h)
        else:
            实际填充rect = pygame.Rect(填充rect.x, 填充rect.y, 填充rect.w, 填充rect.h)

        if 值图源 is not None and 实际填充rect.w > 0 and 实际填充rect.h > 0:
            值图 = self._缩放图(值图源, (实际填充rect.w, 实际填充rect.h))
            if 值图 is not None:
                填充宽 = int(
                    max(
                        0,
                        min(
                            实际填充rect.w,
                            round(float(实际填充rect.w) * float(经验值)),
                        ),
                    )
                )
                if 填充宽 > 0:
                    值层 = pygame.Surface(
                        (实际填充rect.w, 实际填充rect.h), pygame.SRCALPHA
                    )
                    值层.fill((0, 0, 0, 0))
                    值层.blit(
                        值图,
                        (0, 0),
                        area=pygame.Rect(0, 0, 填充宽, 实际填充rect.h),
                    )
                    值层.blit(
                        _圆角遮罩(实际填充rect.w, 实际填充rect.h, 圆角),
                        (0, 0),
                        special_flags=pygame.BLEND_RGBA_MULT,
                    )
                    屏幕.blit(值层, 实际填充rect.topleft)

        if 框图源 is not None and 框rect.w > 0 and 框rect.h > 0:
            框图 = self._缩放图(框图源, (框rect.w, 框rect.h))
            if 框图 is not None:
                框层 = pygame.Surface((框rect.w, 框rect.h), pygame.SRCALPHA)
                框层.fill((0, 0, 0, 0))
                框层.blit(框图, (0, 0))
                框层.blit(
                    _圆角遮罩(框rect.w, 框rect.h, 圆角),
                    (0, 0),
                    special_flags=pygame.BLEND_RGBA_MULT,
                )
                屏幕.blit(框层, 框rect.topleft)

    def _绘制奖励小窗(
        self,
        屏幕: pygame.Surface,
        面板矩形: pygame.Rect,
        经过秒: float,
        总透明度: float = 1.0,
        固定最终: bool = False,
    ):
        if self._等级窗背景图 is None and self._等级窗底图 is None:
            return

        实际屏幕尺寸 = 屏幕.get_size()
        目标rect = self._取奖励窗矩形(面板矩形, *实际屏幕尺寸)
        入场t = (
            1.0
            if 固定最终
            else _夹取(经过秒 / max(0.01, float(self._经验窗入场秒)), 0.0, 1.0)
        )
        if 入场t <= 0.0 or 总透明度 <= 0.0:
            return

        if 入场t < 0.55:
            比例 = _线性插值(1.28, 0.90, 入场t / 0.55)
        else:
            比例 = _线性插值(0.90, 1.00, (入场t - 0.55) / 0.45)
        if 固定最终:
            比例 = 1.0

        画布 = pygame.Surface(目标rect.size, pygame.SRCALPHA)
        小窗图层 = self._取布局层(实际屏幕尺寸, "reward_bg")
        小窗基础矩形 = pygame.Rect(0, 0, 目标rect.w, 目标rect.h)

        if self._等级窗背景图 is not None:
            背景图rect = self._拟合图层内容矩形(
                小窗图层, 小窗基础矩形, self._等级窗背景图
            )
            背景图 = self._缩放图(self._等级窗背景图, 背景图rect.size)
            if 背景图 is not None:
                画布.blit(背景图, 背景图rect.topleft)

        if self._等级窗底图 is not None:
            底图rect = self._拟合图层内容矩形(小窗图层, 小窗基础矩形, self._等级窗底图)
            底图 = self._缩放图(self._等级窗底图, 底图rect.size)
            if 底图 is not None:
                try:
                    底图 = 底图.copy()
                    底图.set_alpha(235)
                except Exception:
                    pass
                画布.blit(底图, 底图rect.topleft)

        小窗区域 = pygame.Rect(0, 0, 目标rect.w, 目标rect.h)
        self._绘制经验奖励数字(画布, 小窗区域, 实际屏幕尺寸)
        self._绘制经验进度区(
            画布,
            小窗区域,
            经过秒 if not 固定最终 else float(self._流程2时长秒),
            实际屏幕尺寸,
        )
        self._绘制段位区(画布, 小窗区域, 实际屏幕尺寸)

        动画宽 = max(2, int(round(目标rect.w * 比例)))
        动画高 = max(2, int(round(目标rect.h * 比例)))
        动画图 = pygame.transform.smoothscale(画布, (动画宽, 动画高)).convert_alpha()

        try:
            动画图 = 动画图.copy()
            动画图.set_alpha(
                int(255 * _缓出三次方(入场t) * max(0.0, min(1.0, 总透明度)))
            )
        except Exception:
            pass

        rr = 动画图.get_rect(center=目标rect.center)
        屏幕.blit(动画图, rr.topleft)

        self._绘制升级动画(
            屏幕,
            rr,
            经过秒 if not 固定最终 else float(self._流程2时长秒),
            实际屏幕尺寸,
        )

    def _奖励窗局部矩形转屏幕矩形(
        self,
        奖励窗屏幕rect: pygame.Rect,
        奖励窗局部rect: pygame.Rect,
        实际屏幕尺寸: Tuple[int, int],
    ) -> pygame.Rect:
        奖励窗原始rect = self._取奖励窗矩形(
            pygame.Rect(0, 0, 实际屏幕尺寸[0], 实际屏幕尺寸[1]),
            *实际屏幕尺寸,
        )
        原始宽 = max(1, int(奖励窗原始rect.w))
        原始高 = max(1, int(奖励窗原始rect.h))

        缩放x = float(奖励窗屏幕rect.w) / float(原始宽)
        缩放y = float(奖励窗屏幕rect.h) / float(原始高)

        return pygame.Rect(
            int(round(float(奖励窗屏幕rect.x) + float(奖励窗局部rect.x) * 缩放x)),
            int(round(float(奖励窗屏幕rect.y) + float(奖励窗局部rect.y) * 缩放y)),
            max(1, int(round(float(奖励窗局部rect.w) * 缩放x))),
            max(1, int(round(float(奖励窗局部rect.h) * 缩放y))),
        )

    def _绘制结算面板(self, 屏幕: pygame.Surface, 面板矩形: pygame.Rect, 经过秒: float):
        屏幕尺寸 = 屏幕.get_size()
        面板矩形 = self._取布局矩形(屏幕尺寸, "panel", 面板矩形)
        面板图层 = self._取布局层(屏幕尺寸, "panel")
        if self._面板图 is not None:
            面板内容矩形 = self._拟合图层内容矩形(面板图层, 面板矩形, self._面板图)
            面板图 = self._缩放图(self._面板图, 面板内容矩形.size)
            if 面板图 is not None:
                if 经过秒 < 0.25:
                    try:
                        面板图 = 面板图.copy()
                        面板图.set_alpha(int(255 * _缓出三次方(经过秒 / 0.25)))
                    except Exception:
                        pass
                屏幕.blit(面板图, 面板内容矩形.topleft)
        else:
            pygame.draw.rect(
                屏幕, (30, 45, 90), 面板矩形, border_radius=max(12, 面板矩形.w // 24)
            )

        封面框 = self._取布局矩形(屏幕尺寸, "cover")
        self._绘制封面区域(屏幕, 封面框)

        星级 = int(self._载荷.get("星级", 0) or 0)
        self._绘制星级图片(屏幕, 星级, 屏幕尺寸)

        歌名 = str(self._载荷.get("曲目名", "Unknown") or "Unknown")
        self._绘制布局滚动文本(
            屏幕,
            "song_title",
            歌名,
            float(经过秒),
            默认字号=26,
            默认颜色=(255, 255, 255),
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

        self._绘制布局文本(
            屏幕,
            "miss",
            str(miss值),
            默认字号=42,
            默认描边颜色=(166, 19, 27),
            默认描边粗细=1,
            默认对齐="right",
        )
        self._绘制布局文本(
            屏幕,
            "good",
            str(good值),
            默认字号=42,
            默认描边颜色=(49, 74, 25),
            默认描边粗细=1,
            默认对齐="right",
        )
        self._绘制布局文本(
            屏幕,
            "cool",
            str(cool值),
            默认字号=42,
            默认描边颜色=(12, 9, 69),
            默认描边粗细=1,
            默认对齐="right",
        )
        self._绘制布局文本(
            屏幕,
            "perfect",
            str(perfect值),
            默认字号=42,
            默认描边颜色=(113, 19, 61),
            默认描边粗细=1,
            默认对齐="right",
        )
        self._绘制布局文本(
            屏幕,
            "combo",
            str(combo值),
            默认字号=42,
            默认描边颜色=(56, 33, 113),
            默认描边粗细=1,
            默认对齐="right",
        )
        self._绘制布局文本(
            屏幕,
            "accuracy",
            f"{百分比值:05.2f}%",
            默认字号=42,
            默认描边颜色=(223, 193, 61),
            默认描边粗细=1,
            默认对齐="right",
        )
        self._绘制布局文本(
            屏幕,
            "score",
            str(int(分数字)),
            默认字号=44,
            默认颜色=(255, 255, 255),
            默认对齐="center",
        )

        self._绘制评级动画(屏幕, 面板矩形, 经过秒)
        self._绘制顶部状态动画(屏幕, 面板矩形, 经过秒)
        self._绘制新纪录提示(屏幕, 面板矩形, 经过秒)

    def _绘制星级图片(
        self,
        屏幕: pygame.Surface,
        星级: int,
        屏幕尺寸: Tuple[int, int],
    ):
        星级 = int(max(0, 星级))
        if 星级 <= 0:
            return

        星星图 = getattr(self, "_星星图", None)
        星星区域 = self._取布局矩形(屏幕尺寸, "stars")
        if 星星区域.w <= 0 or 星星区域.h <= 0:
            return

        if 星星图 is None:
            星星文本 = "★" * 星级
            self._绘制布局文本(
                屏幕,
                "stars",
                星星文本,
                区域=星星区域,
                默认字号=24,
                默认颜色=(242, 223, 60),
                默认对齐="center",
            )
            return

        try:
            原宽, 原高 = 星星图.get_size()
        except Exception:
            return
        if 原宽 <= 0 or 原高 <= 0:
            return

        def _绘制单排(单排星数: int, 行区域: pygame.Rect):
            if 单排星数 <= 0 or 行区域.w <= 0 or 行区域.h <= 0:
                return

            单星高 = max(8, int(行区域.h * 0.90))
            单星宽 = max(
                8,
                int(round(float(原宽) * float(单星高) / float(max(1, 原高)))),
            )
            星间距 = max(2, int(单星宽 * 0.08))
            总宽 = 单星宽 * 单排星数 + 星间距 * max(0, 单排星数 - 1)

            if 总宽 > 行区域.w:
                单星宽 = max(
                    6,
                    int((行区域.w - max(0, 单排星数 - 1) * 星间距) / max(1, 单排星数)),
                )
                单星高 = max(
                    6,
                    int(round(float(单星宽) * float(原高) / float(max(1, 原宽)))),
                )
                总宽 = 单星宽 * 单排星数 + 星间距 * max(0, 单排星数 - 1)

            if 总宽 > 行区域.w and 单排星数 > 1:
                星间距 = max(0, int((行区域.w - 单星宽 * 单排星数) / (单排星数 - 1)))
                总宽 = 单星宽 * 单排星数 + 星间距 * max(0, 单排星数 - 1)

            单星图 = self._缩放图(星星图, (单星宽, 单星高))
            if 单星图 is None:
                return

            起始x = int(round(行区域.centerx - 总宽 / 2))
            起始y = int(round(行区域.centery - 单星高 / 2))

            for 索引 in range(单排星数):
                x = int(起始x + 索引 * (单星宽 + 星间距))
                屏幕.blit(单星图, (x, 起始y))

        if 星级 > 10:
            上排星数 = 星级 - 10
            下排星数 = 10

            总高度 = max(16, 星星区域.h * 2)
            上移量 = max(16, int(星星区域.h * 0.95))
            双排行域 = pygame.Rect(
                星星区域.x,
                星星区域.y - 上移量,
                星星区域.w,
                总高度,
            )

            行间距 = max(2, int(星星区域.h * 0.10))
            单行高 = max(8, int((双排行域.h - 行间距) / 2))

            上排区域 = pygame.Rect(
                双排行域.x,
                双排行域.y,
                双排行域.w,
                单行高,
            )
            下排区域 = pygame.Rect(
                双排行域.x,
                双排行域.y + 单行高 + 行间距,
                双排行域.w,
                单行高,
            )

            _绘制单排(上排星数, 上排区域)
            _绘制单排(下排星数, 下排区域)
            return

        _绘制单排(星级, 星星区域)

    def _绘制升级动画(
        self,
        屏幕: pygame.Surface,
        奖励窗屏幕rect: pygame.Rect,
        经过秒: float,
        实际屏幕尺寸: Tuple[int, int],
    ):
        奖励数据 = self._奖励数据 or {}
        升级模式 = str(奖励数据.get("升级模式", "") or "")
        if not 升级模式:
            return

        动画状态 = self._计算经验动画状态(升级模式, 经过秒)
        动画t = 动画状态.get("升级动画t")
        if 动画t is None:
            return

        t = float(max(0.0, min(1.0, float(动画t))))

        升级配置 = {
            "小窗": {
                "x": 338,
                "y": 293,
                "w": 656,
                "h": 340,
            },
            "主图": {
                "资源键": "升级",
                "基准中心x": 0.52,
                "基准中心y": 0.105,
                "基准宽": 358.0,
                "基准高": 218.0,
                "开始": 0.0,
                "结束": 1.0,
                "初始缩放": 0.78,
                "峰值缩放": 1.38,
                "回落缩放": 1.0,
                "峰值分界": 0.18,
                "回落分界": 0.32,
                "alpha倍率": 1.0,
            },
            "左上": {
                "资源键": "左上",
                "中心x": 0.33,
                "中心y": -0.05,
                "尺寸": 134.0,
                "开始": 0.22,
                "结束": 0.42,
                "起始缩放": 0.5,
                "结束缩放": 0.92,
                "alpha起": 0,
                "alpha止": 190,
            },
            "右上": {
                "资源键": "右上",
                "中心x": 0.66,
                "中心y": -0.025,
                "尺寸": 168.0,
                "开始": 0.10,
                "结束": 0.28,
                "起始缩放": 0.5,
                "结束缩放": 0.92,
                "alpha起": 0,
                "alpha止": 190,
            },
            "左下": {
                "资源键": "左下",
                "中心x": 0.32,
                "中心y": 0.34,
                "尺寸": 130.0,
                "开始": 0.22,
                "结束": 0.42,
                "起始缩放": 0.5,
                "结束缩放": 0.92,
                "alpha起": 0,
                "alpha止": 190,
            },
            "右下": {
                "资源键": "右下",
                "中心x": 0.655,
                "中心y": 0.35,
                "尺寸": 152.0,
                "开始": 0.38,
                "结束": 0.58,
                "起始缩放": 0.5,
                "结束缩放": 0.92,
                "alpha起": 0,
                "alpha止": 190,
            },
        }

        小窗基准 = 升级配置["小窗"]
        基准宽 = max(1.0, float(小窗基准["w"]))
        基准高 = max(1.0, float(小窗基准["h"]))

        缩放x = float(奖励窗屏幕rect.w) / 基准宽
        缩放y = float(奖励窗屏幕rect.h) / 基准高
        平均缩放 = (缩放x + 缩放y) * 0.5

        def _取屏幕中心(相对x: float, 相对y: float) -> Tuple[int, int]:
            中心x = int(
                round(float(奖励窗屏幕rect.x) + float(奖励窗屏幕rect.w) * float(相对x))
            )
            中心y = int(
                round(float(奖励窗屏幕rect.y) + float(奖励窗屏幕rect.h) * float(相对y))
            )
            return 中心x, 中心y

        def _画单图(
            图像键: str,
            中心x: int,
            中心y: int,
            宽: int,
            高: int,
            透明度: int,
        ):
            图源 = self._升级图集.get(图像键)
            if 图源 is None:
                return
            图 = self._缩放图(图源, (max(2, 宽), max(2, 高)))
            if 图 is None:
                return
            try:
                图 = 图.copy()
                图.set_alpha(max(0, min(255, int(透明度))))
            except Exception:
                pass
            目标rect = 图.get_rect(center=(int(中心x), int(中心y)))
            屏幕.blit(图, 目标rect.topleft)

        角标结果列表 = []
        角标顺序 = ["左上", "右上", "左下", "右下"]
        for 角名 in 角标顺序:
            角参数 = 升级配置[角名]
            开始 = float(角参数["开始"])
            结束 = float(角参数["结束"])
            if t < 开始:
                continue

            if t <= 结束:
                局部t = (t - 开始) / max(0.0001, 结束 - 开始)
                当前缩放 = _线性插值(
                    float(角参数["起始缩放"]),
                    float(角参数["结束缩放"]),
                    局部t,
                )
                当前透明度 = int(
                    _线性插值(
                        float(角参数["alpha起"]),
                        float(角参数["alpha止"]),
                        局部t,
                    )
                )
            else:
                当前缩放 = float(角参数["结束缩放"])
                当前透明度 = int(float(角参数["alpha止"]))

            基础尺寸 = float(角参数["尺寸"])
            当前尺寸 = int(max(2, 基础尺寸 * 平均缩放 * 当前缩放))
            中心x, 中心y = _取屏幕中心(
                float(角参数["中心x"]),
                float(角参数["中心y"]),
            )

            角标结果列表.append(
                (
                    str(角参数["资源键"]),
                    中心x,
                    中心y,
                    当前尺寸,
                    当前尺寸,
                    当前透明度,
                )
            )

        主图结果 = None
        主图参数 = 升级配置["主图"]
        if t >= float(主图参数["开始"]):
            if t <= float(主图参数["结束"]):
                主图局部t = (t - float(主图参数["开始"])) / max(
                    0.0001, float(主图参数["结束"]) - float(主图参数["开始"])
                )
            else:
                主图局部t = 1.0

            if 主图局部t < float(主图参数["峰值分界"]):
                子进度 = 主图局部t / max(0.0001, float(主图参数["峰值分界"]))
                主图缩放 = _线性插值(
                    float(主图参数["初始缩放"]),
                    float(主图参数["峰值缩放"]),
                    子进度,
                )
            elif 主图局部t < float(主图参数["回落分界"]):
                子进度 = (主图局部t - float(主图参数["峰值分界"])) / max(
                    0.0001,
                    float(主图参数["回落分界"]) - float(主图参数["峰值分界"]),
                )
                主图缩放 = _线性插值(
                    float(主图参数["峰值缩放"]),
                    float(主图参数["回落缩放"]),
                    子进度,
                )
            else:
                主图缩放 = float(主图参数["回落缩放"])

            主图宽 = int(max(2, float(主图参数["基准宽"]) * 平均缩放 * 主图缩放))
            主图高 = int(max(2, float(主图参数["基准高"]) * 平均缩放 * 主图缩放))
            主图中心x, 主图中心y = _取屏幕中心(
                float(主图参数["基准中心x"]),
                float(主图参数["基准中心y"]),
            )
            主图透明度 = int(
                255
                * _缓出三次方(min(1.0, 主图局部t * 1.8))
                * float(主图参数["alpha倍率"])
            )
            主图结果 = (
                str(主图参数["资源键"]),
                主图中心x,
                主图中心y,
                主图宽,
                主图高,
                主图透明度,
            )

        for 图像键, 中心x, 中心y, 宽, 高, 透明度 in 角标结果列表:
            _画单图(图像键, 中心x, 中心y, 宽, 高, 透明度)

        if 主图结果 is not None:
            图像键, 中心x, 中心y, 宽, 高, 透明度 = 主图结果
            _画单图(图像键, 中心x, 中心y, 宽, 高, 透明度)

    def _构建返回选歌动作(self) -> dict:
        return _构建共享返回选歌动作(self._载荷, self.上下文.get("状态", {}))

    def _返回选歌(self, 动作: Optional[dict] = None):
        return _执行共享返回选歌(
            self.上下文.get("状态", {}),
            self._载荷,
            动作,
        )

    def 退出(self):
        try:
            if self._结算音效通道 is not None:
                self._结算音效通道.stop()
        except Exception:
            pass

        self._背景视频播放器 = None
        self._背景视频路径 = ""

    def _加载资源(self):
        根目录 = _取资源根目录(self.上下文)

        背景路径 = os.path.join(根目录, "冷资源", "backimages", "选歌界面.png")
        self._背景图 = _安全载图(背景路径, 透明=False)

        self._面板图 = _安全载图(
            os.path.join(根目录, "UI-img", "游戏界面", "结算", "结算背景通用.png")
        )
        self._封面图 = _安全载图(str(self._载荷.get("封面路径", "") or ""))

        self._星星图 = _安全载图(
            os.path.join(根目录, "UI-img", "选歌界面资源", "小星星", "小星星.png")
        )

        评级 = str(self._载荷.get("评级", "F") or "F").strip().lower()
        self._评级图 = _安全载图(
            os.path.join(根目录, "UI-img", "游戏界面", "结算", "评价", f"{评级}.png")
        )
        self._全连图 = _安全载图(
            os.path.join(根目录, "UI-img", "游戏界面", "结算", "评价", "全连.png")
        )
        self._失败图 = _安全载图(
            os.path.join(根目录, "UI-img", "游戏界面", "结算", "评价", "失败.png")
        )
        self._新纪录图 = _安全载图(
            os.path.join(根目录, "UI-img", "游戏界面", "结算", "新纪录.png")
        )

        (
            self._提示图集,
            self._倒计时图集,
            self._是按钮图,
            self._否按钮图,
        ) = 加载结算提示资源(根目录)

        小窗目录 = os.path.join(根目录, "UI-img", "游戏界面", "结算", "结算等级小窗")
        self._等级窗背景图 = _安全载图(os.path.join(小窗目录, "背景.png"))
        self._等级窗底图 = _安全载图(os.path.join(小窗目录, "UI_I516.png"))
        if self._等级窗背景图 is None and self._等级窗底图 is not None:
            self._等级窗背景图 = self._等级窗底图
            self._等级窗底图 = None

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

    def _绘制结算背景(self, 屏幕: pygame.Surface):
        if self._背景图 is not None:
            self._绘制cover背景(屏幕, self._背景图)
            return
        屏幕.fill((0, 0, 0))
