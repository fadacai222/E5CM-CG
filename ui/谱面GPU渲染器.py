import bisect
import math
from typing import Any, Dict, List, Optional, Tuple

import pygame

try:
    from pygame._sdl2 import video as _sdl2_video
except Exception:
    _sdl2_video = None


def _取浮点(值: Any, 默认值: float = 0.0) -> float:
    try:
        return float(值)
    except Exception:
        return float(默认值)


def _取整数(值: Any, 默认值: int = 0) -> int:
    try:
        return int(值)
    except Exception:
        return int(默认值)


class 谱面GPU管线渲染器:
    def __init__(self):
        self._左帧: Optional[Dict[str, Any]] = None
        self._右帧: Optional[Dict[str, Any]] = None
        self._事件缓存表: Dict[int, Dict[str, Any]] = {}
        self._纹理缓存表: Dict[Tuple[int, int, int, int], Any] = {}
        self._灰度图缓存表: Dict[Tuple[int, int, int], pygame.Surface] = {}
        self._最近绘制统计: str = ""
        self._最近渲染器id: int = 0
        self._彩色轨道颜色: List[Tuple[int, int, int]] = [
            (44, 214, 255),
            (45, 232, 118),
            (255, 152, 48),
            (255, 92, 181),
            (255, 227, 72),
        ]
        self._灰度轨道颜色: List[Tuple[int, int, int]] = [
            (170, 170, 170),
            (182, 182, 182),
            (196, 196, 196),
            (162, 162, 162),
            (205, 205, 205),
        ]

    def 清空(self):
        self._左帧 = None
        self._右帧 = None
        self._最近绘制统计 = ""

    def 提交帧(
        self,
        左输入,
        右输入=None,
        左渲染器=None,
        右渲染器=None,
        屏幕: Optional[pygame.Surface] = None,
    ):
        self._左帧 = self._构建帧输入(左输入, 左渲染器, 屏幕)
        self._右帧 = self._构建帧输入(右输入, 右渲染器, 屏幕)

    def 取最近绘制统计(self) -> str:
        return str(self._最近绘制统计 or "")

    def 绘制(self, 显示后端):
        if 显示后端 is None:
            return
        取渲染器 = getattr(显示后端, "取GPU渲染器", None)
        if not callable(取渲染器):
            return
        渲染器 = 取渲染器()
        if 渲染器 is None:
            return

        self._同步纹理缓存归属(渲染器)

        notes数 = 0
        判定区数 = 0
        特效数 = 0
        计数动画数 = 0
        for 帧输入 in (self._左帧, self._右帧):
            单侧notes, 单侧判定区, 单侧特效, 单侧计数动画 = self._绘制单侧(渲染器, 帧输入)
            notes数 += int(单侧notes)
            判定区数 += int(单侧判定区)
            特效数 += int(单侧特效)
            计数动画数 += int(单侧计数动画)

        self._最近绘制统计 = (
            f"GPU notes={int(notes数)} receptor={int(判定区数)} fx={int(特效数)} judge={int(计数动画数)}"
        )

    def _同步纹理缓存归属(self, 渲染器):
        当前渲染器id = int(id(渲染器))
        if 当前渲染器id == int(getattr(self, "_最近渲染器id", 0) or 0):
            return
        self._最近渲染器id = 当前渲染器id
        if not self._纹理缓存表:
            return
        删除键 = [键 for 键 in self._纹理缓存表 if int(键[0]) != 当前渲染器id]
        for 键 in 删除键:
            self._纹理缓存表.pop(键, None)

    def _构建帧输入(
        self,
        输入,
        软件渲染器=None,
        屏幕: Optional[pygame.Surface] = None,
    ) -> Optional[Dict[str, Any]]:
        if 输入 is None:
            return None
        try:
            轨道中心列表 = [
                int(v) for v in list(getattr(输入, "轨道中心列表", []) or [])[:5]
            ]
        except Exception:
            轨道中心列表 = []
        if len(轨道中心列表) < 5:
            return None

        原事件列表 = getattr(输入, "事件列表", []) or []
        事件列表 = 原事件列表 if isinstance(原事件列表, list) else list(原事件列表)

        判定区列表: List[Dict[str, Any]] = []
        击中特效列表: List[Dict[str, Any]] = []
        计数动画图层: Optional[pygame.Surface] = None
        计数动画矩形: Optional[pygame.Rect] = None
        游戏区参数: Dict[str, float] = {}
        布局锚点: Optional[Dict[str, Any]] = None
        if 屏幕 is not None and 软件渲染器 is not None:
            取判定区数据 = getattr(软件渲染器, "取GPU判定区数据", None)
            if callable(取判定区数据):
                try:
                    判定区列表 = list(取判定区数据(屏幕, 输入) or [])
                except Exception:
                    判定区列表 = []
            取击中特效数据 = getattr(软件渲染器, "取GPU击中特效数据", None)
            if callable(取击中特效数据):
                try:
                    击中特效列表 = list(取击中特效数据(屏幕, 输入) or [])
                except Exception:
                    击中特效列表 = []
            取游戏区参数 = getattr(软件渲染器, "_取游戏区参数", None)
            if callable(取游戏区参数):
                try:
                    游戏区参数 = dict(取游戏区参数() or {})
                except Exception:
                    游戏区参数 = {}
            取判定区实际锚点 = getattr(软件渲染器, "_取判定区实际锚点", None)
            if callable(取判定区实际锚点):
                try:
                    结果 = 取判定区实际锚点(屏幕, 输入)
                    if isinstance(结果, dict):
                        布局锚点 = dict(结果)
                except Exception:
                    布局锚点 = None
            if bool(getattr(输入, "GPU接管计数动画绘制", False)):
                取计数动画图层 = getattr(软件渲染器, "取GPU计数动画图层", None)
                if callable(取计数动画图层):
                    try:
                        图层结果 = 取计数动画图层(屏幕, 输入)
                        if (
                            isinstance(图层结果, tuple)
                            and len(图层结果) == 2
                        ):
                            候选图层, 候选矩形 = 图层结果
                            if isinstance(候选图层, pygame.Surface):
                                计数动画图层 = 候选图层
                            if isinstance(候选矩形, pygame.Rect):
                                计数动画矩形 = 候选矩形.copy()
                    except Exception:
                        计数动画图层 = None
                        计数动画矩形 = None

        游戏缩放 = float(游戏区参数.get("缩放", 1.0) or 1.0)
        y偏移 = float(游戏区参数.get("y偏移", 0.0) or 0.0)
        hold宽度系数 = float(游戏区参数.get("hold宽度系数", 0.96) or 0.96)
        判定线y列表: List[int] = []
        y判定 = int(float(getattr(输入, "判定线y", 0) or 0) + y偏移)
        if isinstance(布局锚点, dict):
            try:
                轨道中心列表 = [
                    int(v)
                    for v in list(布局锚点.get("轨道中心列表", 轨道中心列表) or 轨道中心列表)[:5]
                ]
            except Exception:
                pass
            try:
                判定线y列表 = [
                    int(v) for v in list(布局锚点.get("判定线y列表", []) or [])[:5]
                ]
            except Exception:
                判定线y列表 = []
            try:
                y判定 = int(布局锚点.get("判定线y", y判定) or y判定)
            except Exception:
                pass
        while len(判定线y列表) < 5:
            判定线y列表.append(int(y判定))

        y底 = int(float(getattr(输入, "底部y", 0) or 0) + y偏移)
        有效速度 = max(
            60.0, float(_取浮点(getattr(输入, "滚动速度px每秒", 0.0), 60.0)) * 游戏缩放
        )
        箭头宽_tap = int(
            max(18, int(float(_取整数(getattr(输入, "箭头目标宽", 32), 32)) * 游戏缩放))
        )
        箭头宽_hold = int(max(16, int(float(箭头宽_tap) * hold宽度系数)))
        上边界 = -int(max(40, 箭头宽_tap * 2))
        下边界 = int(y底 + max(40, 箭头宽_tap * 2))
        半隐y阈值 = (
            int(屏幕.get_height() * 0.5)
            if isinstance(屏幕, pygame.Surface)
            else int(max(0, y判定 - (y判定 * 0.45)))
        )
        可视秒 = float(max(1, (y底 - y判定))) / float(max(60.0, float(有效速度)))

        return {
            "当前谱面秒": _取浮点(getattr(输入, "当前谱面秒", 0.0), 0.0),
            "轨道中心列表": 轨道中心列表,
            "判定线y": int(y判定),
            "判定线y列表": 判定线y列表[:5],
            "底部y": int(y底),
            "滚动速度px每秒": float(有效速度),
            "箭头目标宽": int(箭头宽_tap),
            "hold目标宽": int(箭头宽_hold),
            "上边界": int(上边界),
            "下边界": int(下边界),
            "半隐y阈值": int(半隐y阈值),
            "提前秒": float(可视秒 + 1.0),
            "事件列表": 事件列表,
            "隐藏模式": str(getattr(输入, "隐藏模式", "关闭") or "关闭"),
            "轨迹模式": str(getattr(输入, "轨迹模式", "正常") or "正常"),
            "Note层灰度": bool(getattr(输入, "Note层灰度", False)),
            "判定区列表": 判定区列表,
            "击中特效列表": 击中特效列表,
            "计数动画图层": 计数动画图层,
            "计数动画矩形": 计数动画矩形,
            "软件渲染器": 软件渲染器,
        }

    def _取事件缓存(self, 事件列表: List[Any]) -> Dict[str, Any]:
        if not isinstance(事件列表, list):
            事件列表 = list(事件列表 or [])
        首事件 = 事件列表[0] if 事件列表 else None
        末事件 = 事件列表[-1] if 事件列表 else None
        签名 = (
            id(事件列表),
            int(len(事件列表)),
            _取浮点(getattr(首事件, "开始秒", 0.0), 0.0),
            _取浮点(getattr(末事件, "开始秒", 0.0), 0.0),
            _取浮点(getattr(末事件, "结束秒", 0.0), 0.0),
        )
        缓存键 = int(id(事件列表))
        已有缓存 = self._事件缓存表.get(缓存键)
        if isinstance(已有缓存, dict) and 已有缓存.get("签名") == 签名:
            return 已有缓存

        开始秒列表: List[float] = []
        前缀最大结束秒: List[float] = []
        当前最大结束秒 = -1e12
        for 事件 in 事件列表:
            开始秒 = _取浮点(getattr(事件, "开始秒", 0.0), 0.0)
            结束秒 = _取浮点(getattr(事件, "结束秒", 开始秒), 开始秒)
            if 结束秒 < 开始秒:
                结束秒 = 开始秒
            开始秒列表.append(开始秒)
            当前最大结束秒 = max(当前最大结束秒, 结束秒)
            前缀最大结束秒.append(当前最大结束秒)

        新缓存 = {
            "签名": 签名,
            "事件列表": 事件列表,
            "开始秒列表": 开始秒列表,
            "前缀最大结束秒": 前缀最大结束秒,
        }
        self._事件缓存表[缓存键] = 新缓存
        if len(self._事件缓存表) > 8:
            for 旧键 in list(self._事件缓存表.keys())[:-8]:
                self._事件缓存表.pop(旧键, None)
        return 新缓存

    def _绘制单侧(self, 渲染器, 帧输入: Optional[Dict[str, Any]]) -> Tuple[int, int, int, int]:
        if not isinstance(帧输入, dict):
            return 0, 0, 0, 0
        轨道中心列表 = list(帧输入.get("轨道中心列表", []) or [])[:5]
        if len(轨道中心列表) < 5:
            return 0, 0, 0, 0
        notes数 = self._绘制音符组(渲染器, 帧输入)
        判定区数 = self._绘制判定区组(渲染器, 帧输入)
        特效数 = self._绘制击中特效组(渲染器, 帧输入)
        计数动画数 = self._绘制计数动画图层(渲染器, 帧输入)
        return int(notes数), int(判定区数), int(特效数), int(计数动画数)

    def _绘制计数动画图层(self, 渲染器, 帧输入: Dict[str, Any]) -> int:
        图层 = 帧输入.get("计数动画图层")
        矩形 = 帧输入.get("计数动画矩形")
        if not isinstance(图层, pygame.Surface) or not isinstance(矩形, pygame.Rect):
            return 0
        if 矩形.w <= 0 or 矩形.h <= 0:
            return 0
        纹理 = self._建临时纹理(渲染器, 图层)
        if 纹理 is None:
            return 0
        return int(
            bool(
                self._绘制纹理矩形(
                    纹理,
                    图层,
                    pygame.Rect(int(矩形.x), int(矩形.y), int(矩形.w), int(矩形.h)),
                    None,
                    alpha=255,
                    blend_mode=1,
                )
            )
        )

    def _取皮肤帧(self, 软件渲染器, 分包名: str, 名称: str) -> Optional[pygame.Surface]:
        if 软件渲染器 is None:
            return None
        皮肤包 = getattr(软件渲染器, "_皮肤包", None)
        图集 = getattr(皮肤包, str(分包名), None) if 皮肤包 is not None else None
        取图 = getattr(图集, "取", None)
        if not callable(取图):
            return None
        try:
            return 取图(str(名称))
        except Exception:
            return None

    def _取缩放图(
        self,
        软件渲染器,
        缓存键: str,
        原图: Optional[pygame.Surface],
        目标宽: int,
    ) -> Optional[pygame.Surface]:
        if 原图 is None:
            return None
        目标宽 = int(max(2, 目标宽))
        取图 = getattr(软件渲染器, "_取缩放图", None)
        if callable(取图):
            try:
                return 取图(str(缓存键), 原图, int(目标宽))
            except Exception:
                pass
        try:
            比例 = float(目标宽) / float(max(1, 原图.get_width()))
            目标高 = int(max(2, round(float(原图.get_height()) * 比例)))
            return pygame.transform.smoothscale(原图, (int(目标宽), int(目标高))).convert_alpha()
        except Exception:
            return 原图

    def _取灰度图(self, 图: pygame.Surface) -> pygame.Surface:
        键 = (int(id(图)), int(图.get_width()), int(图.get_height()))
        旧图 = self._灰度图缓存表.get(键)
        if isinstance(旧图, pygame.Surface):
            return 旧图
        try:
            新图 = pygame.transform.grayscale(图).convert_alpha()
        except Exception:
            新图 = 图
        self._灰度图缓存表[键] = 新图
        if len(self._灰度图缓存表) > 512:
            for 旧键 in list(self._灰度图缓存表.keys())[:-256]:
                self._灰度图缓存表.pop(旧键, None)
        return 新图

    def _取纹理(self, 渲染器, 图: pygame.Surface):
        if _sdl2_video is None or 图 is None:
            return None
        键 = (int(id(渲染器)), int(id(图)), int(图.get_width()), int(图.get_height()))
        旧纹理 = self._纹理缓存表.get(键)
        if 旧纹理 is not None:
            return 旧纹理
        try:
            新纹理 = _sdl2_video.Texture.from_surface(渲染器, 图)
        except Exception:
            return None
        self._纹理缓存表[键] = 新纹理
        if len(self._纹理缓存表) > 1024:
            for 旧键 in list(self._纹理缓存表.keys())[:-512]:
                self._纹理缓存表.pop(旧键, None)
        return 新纹理

    def _建临时纹理(self, 渲染器, 图: pygame.Surface):
        if _sdl2_video is None or 图 is None:
            return None
        try:
            return _sdl2_video.Texture.from_surface(渲染器, 图)
        except Exception:
            return None

    def _取贴图条目(
        self,
        渲染器,
        软件渲染器,
        缓存键: str,
        原图: Optional[pygame.Surface],
        目标宽: int,
        使用灰度: bool,
    ) -> Tuple[Optional[Any], Optional[pygame.Surface]]:
        图 = self._取缩放图(软件渲染器, 缓存键, 原图, 目标宽)
        if 图 is None:
            return None, None
        if bool(使用灰度):
            图 = self._取灰度图(图)
        return self._取纹理(渲染器, 图), 图

    @staticmethod
    def _设置纹理透明与颜色(
        纹理,
        alpha: int = 255,
        blend_mode: Optional[int] = 1,
    ):
        if 纹理 is None:
            return
        try:
            纹理.alpha = int(max(0, min(255, alpha)))
        except Exception:
            pass
        if blend_mode is not None:
            try:
                纹理.blend_mode = int(blend_mode)
            except Exception:
                pass
        try:
            纹理.color = (255, 255, 255)
        except Exception:
            pass

    def _绘制纹理中心(
        self,
        纹理,
        图: pygame.Surface,
        x中心: int,
        y中心: int,
        flip_x: bool = False,
        angle: float = 0.0,
        alpha: int = 255,
        blend_mode: Optional[int] = 1,
    ) -> bool:
        if 纹理 is None or 图 is None:
            return False
        self._设置纹理透明与颜色(纹理, alpha=alpha, blend_mode=blend_mode)
        try:
            纹理.draw(
                dstrect=(
                    int(x中心 - 图.get_width() // 2),
                    int(y中心 - 图.get_height() // 2),
                    int(图.get_width()),
                    int(图.get_height()),
                ),
                angle=float(angle),
                origin=(float(图.get_width()) * 0.5, float(图.get_height()) * 0.5),
                flip_x=bool(flip_x),
            )
            return True
        except Exception:
            return False

    def _绘制纹理矩形(
        self,
        纹理,
        图: pygame.Surface,
        目标矩形: pygame.Rect,
        源矩形: Optional[pygame.Rect] = None,
        flip_x: bool = False,
        alpha: int = 255,
        blend_mode: Optional[int] = 1,
    ) -> bool:
        if 纹理 is None or 图 is None or not isinstance(目标矩形, pygame.Rect):
            return False
        self._设置纹理透明与颜色(纹理, alpha=alpha, blend_mode=blend_mode)
        try:
            if isinstance(源矩形, pygame.Rect):
                纹理.draw(
                    srcrect=(
                        int(源矩形.x),
                        int(源矩形.y),
                        int(源矩形.w),
                        int(源矩形.h),
                    ),
                    dstrect=(
                        int(目标矩形.x),
                        int(目标矩形.y),
                        int(目标矩形.w),
                        int(目标矩形.h),
                    ),
                    flip_x=bool(flip_x),
                )
            else:
                纹理.draw(
                    dstrect=(
                        int(目标矩形.x),
                        int(目标矩形.y),
                        int(目标矩形.w),
                        int(目标矩形.h),
                    ),
                    flip_x=bool(flip_x),
                )
            return True
        except Exception:
            return False

    def _绘制音符组(self, 渲染器, 帧输入: Dict[str, Any]) -> int:
        软件渲染器 = 帧输入.get("软件渲染器")
        事件缓存 = self._取事件缓存(帧输入.get("事件列表", []) or [])
        事件列表 = 事件缓存.get("事件列表", []) or []
        if not 事件列表:
            return 0

        当前秒 = _取浮点(帧输入.get("当前谱面秒", 0.0), 0.0)
        判定线y = _取整数(帧输入.get("判定线y", 0), 0)
        轨道中心列表 = list(帧输入.get("轨道中心列表", []) or [])[:5]
        判定线y列表 = list(帧输入.get("判定线y列表", []) or [])[:5]
        while len(判定线y列表) < len(轨道中心列表):
            判定线y列表.append(int(判定线y))
        底部y = _取整数(帧输入.get("底部y", 0), 0)
        速度 = max(60.0, _取浮点(帧输入.get("滚动速度px每秒", 60.0), 60.0))
        箭头宽_tap = max(18, _取整数(帧输入.get("箭头目标宽", 32), 32))
        箭头宽_hold = max(16, _取整数(帧输入.get("hold目标宽", 箭头宽_tap), 箭头宽_tap))
        隐藏模式 = str(帧输入.get("隐藏模式", "关闭") or "关闭")
        轨迹模式 = str(帧输入.get("轨迹模式", "正常") or "正常")
        使用灰度 = bool(帧输入.get("Note层灰度", False))
        if "全隐" in 隐藏模式:
            return 0

        半隐模式 = bool("半隐" in 隐藏模式)
        半隐y阈值 = _取整数(帧输入.get("半隐y阈值", 0), 0)
        提前秒 = max(0.5, _取浮点(帧输入.get("提前秒", 1.0), 1.0))
        上边界 = _取整数(帧输入.get("上边界", -max(40, 箭头宽_tap * 2)), -max(40, 箭头宽_tap * 2))
        下边界 = _取整数(帧输入.get("下边界", 底部y + max(40, 箭头宽_tap * 2)), 底部y + max(40, 箭头宽_tap * 2))
        渲染秒 = self._取渲染秒(软件渲染器, float(当前秒))
        self._同步命中可视状态(
            软件渲染器=软件渲染器,
            事件列表=事件列表,
            当前秒=float(当前秒),
            渲染秒=float(渲染秒),
            判定线y列表=判定线y列表,
            速度=float(速度),
            提前秒=float(提前秒),
            上边界=int(上边界),
            下边界=int(下边界),
            半隐模式=bool(半隐模式),
            半隐y阈值=int(半隐y阈值),
        )
        消失后秒 = max(0.8, float(max(0, 判定线y) + 箭头宽_tap * 2) / float(max(1.0, 速度)) + 0.18)
        起始阈值秒 = 当前秒 - float(消失后秒)
        开始秒列表 = list(事件缓存.get("开始秒列表", []) or [])
        前缀最大结束秒 = list(事件缓存.get("前缀最大结束秒", []) or [])
        起始索引 = bisect.bisect_left(前缀最大结束秒, 起始阈值秒)
        if 起始索引 < 0:
            起始索引 = 0

        绘制数 = 0
        for 索引 in range(int(起始索引), len(事件列表)):
            if 索引 >= len(开始秒列表):
                break
            开始秒 = _取浮点(开始秒列表[索引], 0.0)
            if 开始秒 > 当前秒 + 提前秒:
                break

            事件 = 事件列表[索引]
            轨道 = _取整数(getattr(事件, "轨道序号", -1), -1)
            if 轨道 < 0 or 轨道 >= len(轨道中心列表):
                continue
            结束秒 = _取浮点(getattr(事件, "结束秒", 开始秒), 开始秒)
            if 结束秒 < 开始秒:
                结束秒 = 开始秒

            x中心 = int(轨道中心列表[轨道])
            当前轨判定y = _取整数(判定线y列表[轨道], 判定线y)
            y开始 = int(round(float(当前轨判定y) + (开始秒 - 渲染秒) * 速度))
            y结束 = int(round(float(当前轨判定y) + (结束秒 - 渲染秒) * 速度))
            类型 = str(getattr(事件, "类型", "tap") or "tap")

            if str(类型) == "hold":
                是否命中hold = self._是否命中长按(
                    软件渲染器, int(轨道), float(开始秒), float(结束秒), float(当前秒)
                )
                if bool(是否命中hold) and float(当前秒) >= float(结束秒):
                    continue
                绘制数 += self._绘制长按(
                    渲染器,
                    软件渲染器,
                    int(轨道),
                    int(x中心),
                    int(y开始),
                    int(y结束),
                    int(箭头宽_hold),
                    int(当前轨判定y),
                    int(上边界),
                    int(下边界),
                    bool(半隐模式),
                    int(半隐y阈值),
                    使用灰度,
                    bool(是否命中hold),
                    float(当前秒),
                    float(结束秒),
                )
                continue

            if y开始 < int(上边界) or y开始 > int(下边界):
                continue
            if 半隐模式 and y开始 > 半隐y阈值:
                continue
            if self._tap已命中(
                软件渲染器, int(轨道), float(开始秒), int(y开始), int(当前轨判定y), float(当前秒)
            ):
                continue

            x绘制 = float(x中心)
            旋转角度 = 0.0
            if "摇摆" in 轨迹模式:
                主振幅 = max(16.0, float(箭头宽_tap) * 0.52)
                主相位 = float(渲染秒) * (math.pi * 2.0) * 2.05 + float(开始秒) * 0.55 + float(轨道) * 0.72
                次相位 = float(主相位) * 0.52 + float(轨道) * 0.35
                x绘制 = float(x中心) + math.sin(主相位) * 主振幅 + math.sin(次相位) * (主振幅 * 0.22)
            elif "旋转" in 轨迹模式:
                旋转角度 = float(
                    (渲染秒 * 360.0 * 1.25 + float(开始秒) * 140.0 + float(轨道) * 35.0)
                    % 360.0
                )

            if self._绘制点按(
                渲染器,
                软件渲染器,
                int(轨道),
                int(round(x绘制)),
                int(y开始),
                int(箭头宽_tap),
                使用灰度,
                float(旋转角度),
            ):
                绘制数 += 1
        return 绘制数

    def _取渲染秒(self, 软件渲染器, 当前秒: float) -> float:
        if 软件渲染器 is None:
            return float(当前秒)
        取渲染平滑谱面秒 = getattr(软件渲染器, "_取渲染平滑谱面秒", None)
        if callable(取渲染平滑谱面秒):
            try:
                return float(取渲染平滑谱面秒(float(当前秒)))
            except Exception:
                return float(当前秒)
        return float(当前秒)

    def _同步命中可视状态(
        self,
        软件渲染器,
        事件列表: List[Any],
        当前秒: float,
        渲染秒: float,
        判定线y列表: List[int],
        速度: float,
        提前秒: float,
        上边界: int,
        下边界: int,
        半隐模式: bool,
        半隐y阈值: int,
    ):
        if 软件渲染器 is None:
            return
        确保命中映射缓存 = getattr(软件渲染器, "_确保命中映射缓存", None)
        if callable(确保命中映射缓存):
            try:
                确保命中映射缓存()
            except Exception:
                return
        try:
            当前毫秒 = int(round(float(当前秒) * 1000.0))
        except Exception:
            当前毫秒 = 0

        try:
            按下数组 = pygame.key.get_pressed()
        except Exception:
            按下数组 = None
        轨道到按键列表 = (
            dict(getattr(软件渲染器, "_按键反馈轨道到按键列表", {}) or {})
            if isinstance(getattr(软件渲染器, "_按键反馈轨道到按键列表", None), dict)
            else {}
        )
        if not 轨道到按键列表:
            轨道到按键列表 = {
                0: [pygame.K_1, pygame.K_KP1],
                1: [pygame.K_7, pygame.K_KP7],
                2: [pygame.K_5, pygame.K_KP5],
                3: [pygame.K_9, pygame.K_KP9],
                4: [pygame.K_3, pygame.K_KP3],
            }

        def _轨道是否按下(轨道: int) -> bool:
            if 按下数组 is None:
                return False
            for 键 in 轨道到按键列表.get(int(轨道), []):
                try:
                    if 按下数组[键]:
                        return True
                except Exception:
                    continue
            return False

        命中窗毫秒 = int(round(float(getattr(软件渲染器, "_命中匹配窗秒", 0.12) or 0.12) * 1000.0))
        命中窗毫秒 = max(40, min(260, int(命中窗毫秒)))
        已命中tap过期表毫秒 = getattr(软件渲染器, "_已命中tap过期表毫秒", [])
        待命中队列毫秒 = getattr(软件渲染器, "_待命中队列毫秒", [])
        命中hold开始谱面秒 = getattr(软件渲染器, "_命中hold开始谱面秒", [])
        命中hold结束谱面秒 = getattr(软件渲染器, "_命中hold结束谱面秒", [])
        击中特效开始谱面秒 = getattr(软件渲染器, "_击中特效开始谱面秒", [])
        击中特效循环到谱面秒 = getattr(软件渲染器, "_击中特效循环到谱面秒", [])
        if not isinstance(已命中tap过期表毫秒, list) or not isinstance(待命中队列毫秒, list):
            return
        if (
            not isinstance(命中hold开始谱面秒, list)
            or not isinstance(命中hold结束谱面秒, list)
            or not isinstance(击中特效开始谱面秒, list)
            or not isinstance(击中特效循环到谱面秒, list)
        ):
            return

        for 轨 in range(min(5, len(已命中tap过期表毫秒))):
            表 = 已命中tap过期表毫秒[轨]
            if isinstance(表, dict) and 表:
                for 键 in list(表.keys()):
                    try:
                        if 当前毫秒 > int(表.get(键, -1)):
                            del 表[键]
                    except Exception:
                        try:
                            del 表[键]
                        except Exception:
                            pass
            if 轨 < len(待命中队列毫秒):
                队列 = 待命中队列毫秒[轨]
                if isinstance(队列, list) and 队列:
                    丢弃阈值 = int(当前毫秒 - 2000)
                    while 队列 and int(队列[0]) < 丢弃阈值:
                        队列.pop(0)

        取事件渲染缓存 = getattr(软件渲染器, "_取事件渲染缓存", None)
        if callable(取事件渲染缓存):
            try:
                缓存 = dict(取事件渲染缓存(事件列表) or {})
                缓存事件列表 = list(缓存.get("事件", []) or [])
            except Exception:
                缓存事件列表 = []
        else:
            缓存事件列表 = []
            for 事件 in list(事件列表 or []):
                try:
                    st = float(getattr(事件, "开始秒"))
                    ed = float(getattr(事件, "结束秒"))
                    轨道 = int(getattr(事件, "轨道序号"))
                    类型 = str(getattr(事件, "类型"))
                except Exception:
                    continue
                缓存事件列表.append((st, ed, 轨道, 类型, int(round(st * 1000.0))))
            缓存事件列表.sort(key=lambda 项: (float(项[0]), int(项[2]), float(项[1])))

        活跃hold轨道: set[int] = set()
        try:
            软件渲染器._hold当前按下中 = [False] * 5
        except Exception:
            pass

        for 条目 in 缓存事件列表:
            try:
                st, ed, 轨道, 类型, st毫秒 = 条目
            except Exception:
                continue
            if float(st) > float(当前秒) + float(提前秒):
                break
            if float(st) < float(当前秒) - 2.5 and float(ed) < float(当前秒) - 2.5:
                continue
            轨道 = int(轨道)
            if 轨道 < 0 or 轨道 >= len(判定线y列表):
                continue
            当前轨判定y = int(判定线y列表[轨道])
            y开始 = float(当前轨判定y) + (float(st) - float(渲染秒)) * float(速度)

            if abs(float(ed) - float(st)) < 1e-6 or str(类型) == "tap":
                if y开始 < float(上边界) or y开始 > float(下边界):
                    continue
                if 轨道 >= len(已命中tap过期表毫秒):
                    continue
                已命中表 = 已命中tap过期表毫秒[轨道]
                if not isinstance(已命中表, dict):
                    continue
                命中匹配 = False
                try:
                    过期 = int(已命中表.get(int(st毫秒), -1))
                    if 过期 > 0 and 当前毫秒 <= 过期:
                        命中匹配 = True
                except Exception:
                    命中匹配 = False
                if (not 命中匹配) and 轨道 < len(待命中队列毫秒):
                    队列 = 待命中队列毫秒[轨道]
                    if isinstance(队列, list):
                        左界 = int(int(st毫秒) - int(命中窗毫秒))
                        while 队列 and int(队列[0]) < 左界:
                            队列.pop(0)
                        if 队列:
                            hit_ms = int(队列[0])
                            if abs(int(hit_ms) - int(st毫秒)) <= int(命中窗毫秒):
                                队列.pop(0)
                                命中匹配 = True
                                已命中表[int(st毫秒)] = int(
                                    max(int(st毫秒) + 1000, int(当前毫秒) + 650)
                                )
                continue

            y结束 = float(当前轨判定y) + (float(ed) - float(渲染秒)) * float(速度)
            seg_top = float(min(y开始, y结束))
            seg_bot = float(max(y开始, y结束))
            if seg_bot < float(上边界) or seg_top > float(下边界):
                continue

            是否命中hold = False
            if 轨道 < len(命中hold开始谱面秒) and 轨道 < len(命中hold结束谱面秒):
                命中开始 = float(命中hold开始谱面秒[轨道])
                命中结束 = float(命中hold结束谱面秒[轨道])
                if 命中结束 > -1.0 and (float(当前秒) <= 命中结束 + 1.2):
                    if abs(float(st) - 命中开始) <= max(
                        0.08,
                        float(getattr(软件渲染器, "_命中匹配窗秒", 0.12) or 0.12) * 2.0,
                    ):
                        是否命中hold = True
            if (not 是否命中hold) and 轨道 < len(待命中队列毫秒):
                队列 = 待命中队列毫秒[轨道]
                if isinstance(队列, list):
                    左界 = int(int(st毫秒) - int(命中窗毫秒))
                    while 队列 and int(队列[0]) < 左界:
                        队列.pop(0)
                    if 队列:
                        hit_ms = int(队列[0])
                        if abs(int(hit_ms) - int(st毫秒)) <= int(命中窗毫秒):
                            队列.pop(0)
                            if 轨道 < len(命中hold开始谱面秒):
                                命中hold开始谱面秒[轨道] = float(st)
                            if 轨道 < len(命中hold结束谱面秒):
                                命中hold结束谱面秒[轨道] = float(ed)
                            if 轨道 < len(击中特效开始谱面秒):
                                击中特效开始谱面秒[轨道] = float(st)
                            if 轨道 < len(击中特效循环到谱面秒):
                                击中特效循环到谱面秒[轨道] = float(ed)
                            是否命中hold = True
            if bool(是否命中hold) and (float(st) <= float(当前秒) <= float(ed)):
                活跃hold轨道.add(int(轨道))
                try:
                    软件渲染器._hold当前按下中[int(轨道)] = bool(_轨道是否按下(int(轨道)))
                    软件渲染器._hold松手系统秒[int(轨道)] = None
                except Exception:
                    pass

        for i in range(5):
            if i not in 活跃hold轨道:
                try:
                    软件渲染器._hold松手系统秒[i] = None
                    软件渲染器._hold当前按下中[i] = False
                except Exception:
                    pass
            try:
                if (
                    i < len(命中hold结束谱面秒)
                    and float(命中hold结束谱面秒[i]) > -1.0
                    and float(当前秒) > float(命中hold结束谱面秒[i]) + 2.0
                ):
                    if i < len(命中hold开始谱面秒):
                        命中hold开始谱面秒[i] = -999.0
                    if i < len(命中hold结束谱面秒):
                        命中hold结束谱面秒[i] = -999.0
                    if i < len(击中特效循环到谱面秒) and float(击中特效循环到谱面秒[i]) > -1.0:
                        击中特效循环到谱面秒[i] = -999.0
            except Exception:
                continue

    def _绘制判定区组(self, 渲染器, 帧输入: Dict[str, Any]) -> int:
        判定区列表 = list(帧输入.get("判定区列表", []) or [])
        使用灰度 = bool(帧输入.get("Note层灰度", False))
        软件渲染器 = 帧输入.get("软件渲染器")
        if not 判定区列表:
            return 0
        self._绘制判定区双手(渲染器, 软件渲染器, 判定区列表, 使用灰度)
        绘制数 = 0
        for 项 in 判定区列表:
            if not isinstance(项, dict):
                continue
            轨道 = _取整数(项.get("轨道", -1), -1)
            if 轨道 < 0:
                continue
            if self._绘制判定区贴图项(渲染器, 软件渲染器, 项, int(轨道), 使用灰度):
                绘制数 += 1
            else:
                self._绘制几何判定区项(渲染器, 项, int(轨道), 使用灰度)
                绘制数 += 1
        return 绘制数

    def _绘制击中特效组(self, 渲染器, 帧输入: Dict[str, Any]) -> int:
        特效列表 = list(帧输入.get("击中特效列表", []) or [])
        使用灰度 = bool(帧输入.get("Note层灰度", False))
        软件渲染器 = 帧输入.get("软件渲染器")
        当前谱面秒 = _取浮点(帧输入.get("当前谱面秒", 0.0), 0.0)
        绘制数 = 0
        for 项 in 特效列表:
            if not isinstance(项, dict):
                continue
            矩形 = 项.get("rect")
            if not isinstance(矩形, pygame.Rect):
                continue
            轨道 = _取整数(项.get("轨道", -1), -1)
            if self._绘制击中特效贴图项(
                渲染器, 软件渲染器, 项, int(轨道), float(当前谱面秒), 使用灰度
            ):
                绘制数 += 1
            else:
                self._绘制几何特效项(渲染器, 项, int(轨道), 使用灰度)
                绘制数 += 1
        return 绘制数

    def _tap已命中(
        self,
        软件渲染器,
        轨道: int,
        开始秒: float,
        y开始: int,
        判定线y: int,
        当前秒: float,
    ) -> bool:
        if 软件渲染器 is None:
            return False
        try:
            表列表 = list(getattr(软件渲染器, "_已命中tap过期表毫秒", []) or [])
            if not (0 <= int(轨道) < len(表列表)):
                return False
            已命中表 = 表列表[int(轨道)]
            if not isinstance(已命中表, dict):
                return False
            开始毫秒 = int(round(float(开始秒) * 1000.0))
            当前毫秒 = int(round(float(当前秒) * 1000.0))
            过期毫秒 = int(已命中表.get(int(开始毫秒), -1))
            return bool(过期毫秒 > 0 and 当前毫秒 <= 过期毫秒 and int(y开始) < int(判定线y))
        except Exception:
            return False

    def _是否命中长按(
        self,
        软件渲染器,
        轨道: int,
        开始秒: float,
        结束秒: float,
        当前秒: float,
    ) -> bool:
        if 软件渲染器 is None:
            return False
        try:
            命中开始列表 = list(getattr(软件渲染器, "_命中hold开始谱面秒", []) or [])
            命中结束列表 = list(getattr(软件渲染器, "_命中hold结束谱面秒", []) or [])
            轨 = int(轨道)
            if 轨 < 0 or 轨 >= len(命中开始列表) or 轨 >= len(命中结束列表):
                return False
            命中开始 = float(命中开始列表[轨])
            命中结束 = float(命中结束列表[轨])
            命中窗 = float(getattr(软件渲染器, "_命中匹配窗秒", 0.12) or 0.12)
            if 命中结束 <= -1.0 or float(当前秒) > 命中结束 + 1.2:
                return False
            return bool(abs(float(开始秒) - 命中开始) <= max(0.08, 命中窗 * 2.0))
        except Exception:
            return False

    def _绘制点按(
        self,
        渲染器,
        软件渲染器,
        轨道: int,
        x中心: int,
        y: int,
        箭头宽: int,
        使用灰度: bool,
        旋转角度: float = 0.0,
    ) -> bool:
        方位 = self._轨道到arrow方位码(int(轨道))
        文件名 = f"arrow_body_{方位}.png"
        原图 = self._取皮肤帧(软件渲染器, "arrow", 文件名)
        纹理, 图 = self._取贴图条目(
            渲染器,
            软件渲染器,
            f"arrow:{文件名}:{int(箭头宽)}",
            原图,
            int(箭头宽),
            bool(使用灰度),
        )
        if 纹理 is None or 图 is None:
            self._绘制几何点按(
                渲染器,
                int(轨道),
                int(x中心),
                int(y),
                int(箭头宽),
                bool(使用灰度),
                float(旋转角度),
            )
            return False
        return bool(
            self._绘制纹理中心(
                纹理,
                图,
                int(x中心),
                int(y),
                angle=float(旋转角度),
            )
        )

    def _绘制长按(
        self,
        渲染器,
        软件渲染器,
        轨道: int,
        x中心: int,
        y开始: int,
        y结束: int,
        箭头宽: int,
        判定线y: int,
        上边界: int,
        下边界: int,
        半隐模式: bool,
        半隐y阈值: int,
        使用灰度: bool,
        是否命中hold: bool,
        当前谱面秒: float,
        结束谱面秒: float,
    ) -> int:
        方位 = self._轨道到arrow方位码(int(轨道))
        头纹理, 头图 = self._取贴图条目(
            渲染器,
            软件渲染器,
            f"arrow:arrow_body_{方位}.png:{int(箭头宽)}",
            self._取皮肤帧(软件渲染器, "arrow", f"arrow_body_{方位}.png"),
            int(箭头宽),
            bool(使用灰度),
        )
        罩纹理, 罩图 = self._取贴图条目(
            渲染器,
            软件渲染器,
            f"arrow:arrow_mask_{方位}.png:{int(箭头宽)}",
            self._取皮肤帧(软件渲染器, "arrow", f"arrow_mask_{方位}.png"),
            int(箭头宽),
            bool(使用灰度),
        )
        身纹理, 身图 = self._取贴图条目(
            渲染器,
            软件渲染器,
            f"arrow:arrow_repeat_{方位}.png:{int(箭头宽)}",
            self._取皮肤帧(软件渲染器, "arrow", f"arrow_repeat_{方位}.png"),
            int(箭头宽),
            bool(使用灰度),
        )
        尾纹理, 尾图 = self._取贴图条目(
            渲染器,
            软件渲染器,
            f"arrow:arrow_tail_{方位}.png:{int(箭头宽)}",
            self._取皮肤帧(软件渲染器, "arrow", f"arrow_tail_{方位}.png"),
            int(箭头宽),
            bool(使用灰度),
        )
        if all(x is None for x in (头纹理, 罩纹理, 身纹理, 尾纹理)):
            return int(
                self._绘制几何长按(
                    渲染器,
                    int(轨道),
                    int(x中心),
                    int(y开始),
                    int(y结束),
                    int(箭头宽),
                    int(判定线y),
                    int(max(下边界, 判定线y + 箭头宽)),
                    bool(半隐模式),
                    int(半隐y阈值),
                    bool(使用灰度),
                    bool(是否命中hold),
                )
            )

        if bool(半隐模式) and min(int(y开始), int(y结束)) > int(半隐y阈值):
            return 0

        def _取部件度量(缓存键: str, 图: Optional[pygame.Surface]) -> Optional[Dict[str, float]]:
            if 图 is None:
                return None
            顶像素, 底像素 = self._取中心带不透明y边界(软件渲染器, str(缓存键), 图)
            图高 = int(max(1, 图.get_height()))
            return {
                "top_px": float(int(max(0, min(图高 - 1, 顶像素)))),
                "bottom_px": float(int(max(0, min(图高 - 1, 底像素)))),
                "top_rel": float(-图高 * 0.5 + int(max(0, min(图高 - 1, 顶像素)))),
                "bottom_rel": float(-图高 * 0.5 + int(max(0, min(图高 - 1, 底像素)))),
            }

        def _绘制拉伸片段(
            纹理,
            图: Optional[pygame.Surface],
            目标顶y: float,
            高度px: float,
            源顶px: float,
            源高px: float,
        ) -> bool:
            if 纹理 is None or 图 is None or float(高度px) <= 0.0 or float(源高px) <= 0.0:
                return False
            片段顶 = float(目标顶y)
            片段底 = float(目标顶y) + float(高度px)
            if 片段底 <= float(上边界) or 片段顶 >= float(下边界):
                return False
            可见顶 = float(max(float(片段顶), float(上边界)))
            可见底 = float(min(float(片段底), float(下边界)))
            if 可见底 <= 可见顶:
                return False
            目标矩形 = pygame.Rect(
                int(x中心 - 图.get_width() // 2),
                int(round(可见顶)),
                int(图.get_width()),
                int(max(1, round(float(可见底 - 可见顶)))),
            )
            源矩形 = pygame.Rect(
                0,
                int(max(0, min(int(图.get_height()) - 1, round(float(源顶px))))),
                int(图.get_width()),
                int(max(1, min(int(图.get_height()), round(float(源高px))))),
            )
            return bool(self._绘制纹理矩形(纹理, 图, 目标矩形, 源矩形))

        头度量 = _取部件度量(f"gpu:hold:body:{方位}:{int(箭头宽)}", 头图)
        脖子度量 = _取部件度量(f"gpu:hold:mask:{方位}:{int(箭头宽)}", 罩图)
        身体度量 = _取部件度量(f"gpu:hold:repeat:{方位}:{int(箭头宽)}", 身图)
        尾巴度量 = _取部件度量(f"gpu:hold:tail:{方位}:{int(箭头宽)}", 尾图)

        头中心y = float(y开始)
        尾巴中心y = float(y结束)
        目标判定y = float(int(判定线y))

        if bool(是否命中hold):
            if float(当前谱面秒) >= float(结束谱面秒):
                return 0
            if 头中心y < 目标判定y:
                头中心y = float(目标判定y)

        箭头脖子重叠偏移量 = 0.0
        if 头度量 is not None and 脖子度量 is not None:
            箭头脖子重叠偏移量 = float(
                max(0.0, float(头度量["bottom_rel"]) - float(脖子度量["top_rel"]))
            )
        拼接偏移量 = 0.0

        脖子中心y = float(头中心y)
        if 头度量 is not None and 脖子度量 is not None:
            头下边缘y = float(头中心y) + float(头度量["bottom_rel"])
            脖子中心y = float(
                头下边缘y
                - float(脖子度量["top_rel"])
                - float(箭头脖子重叠偏移量)
            )

        if 脖子度量 is not None:
            脖子下拼接y = float(脖子中心y) + float(脖子度量["bottom_rel"])
        elif 头度量 is not None:
            脖子下拼接y = float(头中心y) + float(头度量["bottom_rel"])
        else:
            脖子下拼接y = float(头中心y)

        if 尾巴度量 is not None:
            尾巴上拼接y = float(尾巴中心y) + float(尾巴度量["top_rel"])
        else:
            尾巴上拼接y = float(尾巴中心y)

        最小尾巴上拼接y = float(脖子下拼接y) + float(拼接偏移量)
        if (not bool(是否命中hold)) and 尾巴上拼接y < 最小尾巴上拼接y:
            if 尾巴度量 is not None:
                尾巴中心y = float(最小尾巴上拼接y) - float(尾巴度量["top_rel"])
                尾巴上拼接y = float(最小尾巴上拼接y)
            else:
                尾巴上拼接y = float(最小尾巴上拼接y)
                尾巴中心y = float(尾巴上拼接y)

        身体起始拼接y = float(脖子下拼接y) + float(拼接偏移量)
        身体结束拼接y = float(尾巴上拼接y) - float(拼接偏移量)

        已绘制 = False
        if (
            身纹理 is not None
            and 身图 is not None
            and 身体度量 is not None
            and 身体结束拼接y > 身体起始拼接y
        ):
            身体顶部像素 = float(身体度量["top_px"])
            身体底部像素 = float(身体度量["bottom_px"])
            身体中心像素 = float(
                round((float(身体顶部像素) + float(身体底部像素)) * 0.5)
            )
            已绘制 = bool(
                _绘制拉伸片段(
                    身纹理,
                    身图,
                    目标顶y=float(身体起始拼接y),
                    高度px=float(身体结束拼接y - 身体起始拼接y),
                    源顶px=float(身体中心像素),
                    源高px=1.0,
                )
                or 已绘制
            )
        elif all(x is None for x in (头纹理, 罩纹理, 身纹理, 尾纹理)):
            已绘制 = bool(
                self._绘制几何长按(
                    渲染器,
                    int(轨道),
                    int(x中心),
                    int(y开始),
                    int(y结束),
                    int(箭头宽),
                    int(判定线y),
                    int(max(下边界, 判定线y + 箭头宽)),
                    bool(半隐模式),
                    int(半隐y阈值),
                    bool(使用灰度),
                    bool(是否命中hold),
                )
            )

        if 尾纹理 is not None and 尾图 is not None and 上边界 <= int(round(尾巴中心y)) <= 下边界:
            已绘制 = bool(
                self._绘制纹理中心(尾纹理, 尾图, int(x中心), int(round(尾巴中心y))) or 已绘制
            )
        if (
            罩纹理 is not None
            and 罩图 is not None
            and 上边界 <= int(round(脖子中心y)) <= 下边界
        ):
            已绘制 = bool(
                self._绘制纹理中心(罩纹理, 罩图, int(x中心), int(round(脖子中心y))) or 已绘制
            )
        if (
            头纹理 is not None
            and 头图 is not None
            and 上边界 <= int(round(头中心y)) <= 下边界
        ):
            已绘制 = bool(
                self._绘制纹理中心(头纹理, 头图, int(x中心), int(round(头中心y))) or 已绘制
            )
        return 1 if 已绘制 else 0

    def _绘制软件长按图层(
        self,
        渲染器,
        软件渲染器,
        轨道: int,
        x中心: int,
        y开始: int,
        y结束: int,
        箭头宽: int,
        判定线y: int,
        上边界: int,
        下边界: int,
        头图: Optional[pygame.Surface],
        罩图: Optional[pygame.Surface],
        身图: Optional[pygame.Surface],
        尾图: Optional[pygame.Surface],
        是否命中hold: bool,
        当前谱面秒: float,
        结束谱面秒: float,
    ) -> Optional[int]:
        if 软件渲染器 is None:
            return None
        画hold = getattr(软件渲染器, "_画hold", None)
        图集 = getattr(getattr(软件渲染器, "_皮肤包", None), "arrow", None)
        if not callable(画hold) or 图集 is None:
            return None

        候选图列表 = [图 for 图 in (头图, 罩图, 身图, 尾图) if isinstance(图, pygame.Surface)]
        if not 候选图列表:
            return None

        try:
            最大宽 = max(int(图.get_width()) for 图 in 候选图列表)
            最大高 = max(int(图.get_height()) for 图 in 候选图列表)
        except Exception:
            最大宽 = int(max(16, 箭头宽))
            最大高 = int(max(16, 箭头宽))

        半宽 = int(max(最大宽 // 2 + 8, 箭头宽))
        上余量 = int(max(最大高 + 8, 箭头宽 * 2))
        下余量 = int(max(最大高 + 8, 箭头宽 * 2))
        局部左 = int(x中心 - 半宽)
        局部上 = int(min(y开始, y结束, 判定线y) - 上余量)
        局部下 = int(max(y开始, y结束, 判定线y) + 下余量)
        局部上 = int(max(上边界 - 上余量, 局部上))
        局部下 = int(min(下边界 + 下余量, 局部下))
        if 局部下 <= 局部上:
            return 0

        局部宽 = int(max(2, 半宽 * 2))
        局部高 = int(max(2, 局部下 - 局部上))
        try:
            图层 = pygame.Surface((局部宽, 局部高), pygame.SRCALPHA)
            图层.fill((0, 0, 0, 0))
            画hold(
                图层,
                图集,
                int(轨道),
                int(x中心 - 局部左),
                float(y开始 - 局部上),
                float(y结束 - 局部上),
                当前谱面秒=float(当前谱面秒),
                结束谱面秒=float(结束谱面秒),
                箭头宽=int(箭头宽),
                判定线y=int(判定线y - 局部上),
                是否命中hold=bool(是否命中hold),
                上边界=int(上边界 - 局部上),
                下边界=int(下边界 - 局部上),
                是否绘制头=True,
            )
            if 图层.get_bounding_rect().w <= 0 or 图层.get_bounding_rect().h <= 0:
                return 0
            纹理 = self._建临时纹理(渲染器, 图层)
            if 纹理 is None:
                return 0
            已绘制 = self._绘制纹理矩形(
                纹理,
                图层,
                pygame.Rect(int(局部左), int(局部上), int(局部宽), int(局部高)),
                None,
                alpha=255,
                blend_mode=1,
            )
            return 1 if bool(已绘制) else 0
        except Exception:
            return None

    def _绘制判定区双手(
        self,
        渲染器,
        软件渲染器,
        判定区列表: List[Dict[str, Any]],
        使用灰度: bool,
    ):
        if len(判定区列表) < 5:
            return
        按轨道 = {
            _取整数(项.get("轨道", -1), -1): 项
            for 项 in 判定区列表
            if isinstance(项, dict)
        }
        if 0 not in 按轨道 or 4 not in 按轨道:
            return
        左项 = 按轨道[0]
        右项 = 按轨道[4]
        轨1 = 按轨道.get(1, 左项)
        左x = _取整数(左项.get("x", 0), 0)
        右x = _取整数(右项.get("x", 0), 0)
        参考x = _取整数(轨1.get("x", 左x), 左x)
        间距 = int(max(8, abs(int(参考x) - int(左x))))
        左手x = int(左x - 间距)
        右手x = int(右x + 间距)
        左手y = _取整数(左项.get("y", 0), 0)
        右手y = _取整数(右项.get("y", 左手y), 左手y)
        receptor宽 = int(
            max(
                16,
                _取整数(左项.get("基础宽", 左项.get("w", 0)), 0),
                _取整数(右项.get("基础宽", 右项.get("w", 0)), 0),
            )
        )
        for 文件名, x中心, y中心 in (
            ("key_ll.png", 左手x, 左手y),
            ("key_rr.png", 右手x, 右手y),
        ):
            原图 = self._取皮肤帧(软件渲染器, "key", 文件名)
            纹理, 图 = self._取贴图条目(
                渲染器,
                软件渲染器,
                f"key:{文件名}:{int(receptor宽)}",
                原图,
                int(receptor宽),
                bool(使用灰度),
            )
            if 纹理 is not None and 图 is not None:
                self._绘制纹理中心(纹理, 图, int(x中心), int(y中心))

    def _绘制判定区贴图项(
        self,
        渲染器,
        软件渲染器,
        项: Dict[str, Any],
        轨道: int,
        使用灰度: bool,
    ) -> bool:
        方位 = self._轨道到key方位码(int(轨道))
        文件名 = f"key_{方位}.png"
        目标宽 = int(
            max(
                8,
                _取整数(项.get("w", 0), 0),
                _取整数(项.get("基础宽", 0), 0),
            )
        )
        纹理, 图 = self._取贴图条目(
            渲染器,
            软件渲染器,
            f"key:{文件名}:{int(目标宽)}",
            self._取皮肤帧(软件渲染器, "key", 文件名),
            int(目标宽),
            bool(使用灰度),
        )
        if 纹理 is None or 图 is None:
            return False
        return bool(
            self._绘制纹理中心(
                纹理,
                图,
                _取整数(项.get("x", 0), 0),
                _取整数(项.get("y", 0), 0),
            )
        )

    def _绘制击中特效贴图项(
        self,
        渲染器,
        软件渲染器,
        项: Dict[str, Any],
        轨道: int,
        当前谱面秒: float,
        使用灰度: bool,
    ) -> bool:
        矩形 = 项.get("rect")
        if not isinstance(矩形, pygame.Rect):
            return False
        帧信息 = self._取击中特效帧信息(软件渲染器, int(轨道), float(当前谱面秒))
        if 帧信息 is None:
            return False
        文件名, 需要翻转, 循环播放 = 帧信息
        目标宽 = int(max(24, 矩形.w))
        纹理, 图 = self._取贴图条目(
            渲染器,
            软件渲染器,
            f"fx:{文件名}:{int(目标宽)}",
            self._取皮肤帧(软件渲染器, "key_effect", 文件名),
            int(目标宽),
            bool(使用灰度),
        )
        if 纹理 is None or 图 is None:
            return False
        alpha = int(max(48, min(255, round(float(_取浮点(项.get("强度", 1.0), 1.0)) * 255.0))))
        已绘制 = bool(
            self._绘制纹理中心(
                纹理,
                图,
                int(矩形.centerx),
                int(矩形.centery),
                flip_x=bool(需要翻转),
                alpha=alpha,
                blend_mode=2,
            )
        )
        if bool(循环播放):
            已绘制 = bool(
                self._绘制纹理中心(
                    纹理,
                    图,
                    int(矩形.centerx),
                    int(矩形.centery),
                    flip_x=bool(需要翻转),
                    alpha=alpha,
                    blend_mode=2,
                )
                or 已绘制
            )
        return 已绘制

    def _取击中特效帧信息(
        self,
        软件渲染器,
        轨道: int,
        当前谱面秒: float,
    ) -> Optional[Tuple[str, bool, bool]]:
        if 软件渲染器 is None or int(轨道) < 0 or int(轨道) >= 5:
            return None
        try:
            轨 = int(轨道)
            帧数 = 18
            fps = float(getattr(软件渲染器, "_击中特效帧率", 60.0) or 60.0)
            循环到列表 = list(getattr(软件渲染器, "_击中特效循环到谱面秒", []) or [])
            开始列表 = list(getattr(软件渲染器, "_击中特效开始谱面秒", []) or [])
            进行列表 = list(getattr(软件渲染器, "_击中特效进行秒", []) or [])
            循环到 = float(循环到列表[轨])
            进行秒 = float(进行列表[轨])
            if 循环到 <= 0.0 and 进行秒 < 0.0:
                return None
            循环播放 = False
            if 循环到 > 0.0:
                if float(当前谱面秒) > 循环到 + 0.02:
                    return None
                if 进行秒 < 0.0:
                    进行秒 = 0.0
                帧号 = int(max(0, min(帧数 - 1, int(进行秒 * fps))))
                循环播放 = True
            else:
                帧号 = int(max(0, min(帧数 - 1, int(进行秒 * fps))))
            前缀, 需要翻转 = self._轨道到击中序列(int(轨))
            return (f"{前缀}_{帧号:04d}.png", bool(需要翻转), bool(循环播放))
        except Exception:
            return None

    def _取中心带不透明y边界(
        self,
        软件渲染器,
        缓存键: str,
        图: pygame.Surface,
    ) -> Tuple[int, int]:
        if 图 is None:
            return 0, 0
        取边界 = getattr(软件渲染器, "_取中心带不透明y边界", None)
        if callable(取边界):
            try:
                return tuple(int(v) for v in 取边界(str(缓存键), 图))
            except Exception:
                pass
        宽 = int(max(1, 图.get_width()))
        高 = int(max(1, 图.get_height()))
        try:
            alpha = pygame.surfarray.array_alpha(图)
        except Exception:
            return 0, max(0, 高 - 1)
        起列 = int(max(0, min(宽 - 1, int(宽 * 0.48))))
        止列 = int(max(起列 + 1, min(宽, int(宽 * 0.52))))
        顶列表: List[int] = []
        底列表: List[int] = []
        for x in range(起列, 止列):
            命中行 = [y for y in range(高) if int(alpha[x, y]) > 10]
            if 命中行:
                顶列表.append(int(命中行[0]))
                底列表.append(int(命中行[-1]))
        if not 顶列表 or not 底列表:
            return 0, max(0, 高 - 1)
        return int(min(顶列表)), int(max(底列表))

    def _绘制几何点按(
        self,
        渲染器,
        轨道: int,
        x中心: int,
        y: int,
        箭头宽: int,
        使用灰度: bool,
        旋转角度: float = 0.0,
    ):
        del 旋转角度
        颜色 = self._取轨道颜色(int(轨道), bool(使用灰度))
        尺寸 = int(max(10, 箭头宽))
        矩形 = pygame.Rect(
            int(x中心 - 尺寸 // 2),
            int(y - 尺寸 // 2),
            int(尺寸),
            int(尺寸),
        )
        try:
            渲染器.draw_color = (int(颜色[0]), int(颜色[1]), int(颜色[2]), 230)
            渲染器.fill_rect(矩形)
        except Exception:
            pass

    def _绘制几何长按(
        self,
        渲染器,
        轨道: int,
        x中心: int,
        y开始: int,
        y结束: int,
        箭头宽: int,
        判定线y: int,
        底部y: int,
        半隐模式: bool,
        半隐y阈值: int,
        使用灰度: bool,
        是否命中hold: bool,
    ) -> int:
        颜色 = self._取轨道颜色(int(轨道), bool(使用灰度))
        if bool(是否命中hold) and int(y开始) < int(判定线y):
            y开始 = int(判定线y)
        y1 = int(min(int(y开始), int(y结束)))
        y2 = int(max(int(y开始), int(y结束)))
        if bool(半隐模式):
            y2 = int(min(int(y2), int(半隐y阈值)))
        if y2 < -箭头宽 or y1 > int(底部y + 箭头宽):
            return 0
        宽 = int(max(8, round(float(箭头宽) * 0.4)))
        身体 = pygame.Rect(
            int(x中心 - 宽 // 2),
            int(max(-箭头宽, y1)),
            int(宽),
            int(max(1, min(int(底部y + 箭头宽), y2) - max(-箭头宽, y1))),
        )
        try:
            渲染器.draw_color = (int(颜色[0]), int(颜色[1]), int(颜色[2]), 190)
            if 身体.h > 0:
                渲染器.fill_rect(身体)
            头 = pygame.Rect(
                int(x中心 - 箭头宽 // 2),
                int(y开始 - 箭头宽 // 2),
                int(箭头宽),
                int(箭头宽),
            )
            尾 = pygame.Rect(
                int(x中心 - max(8, 箭头宽 // 3)),
                int(y结束 - max(8, 箭头宽 // 3)),
                int(max(16, 箭头宽 // 1.5)),
                int(max(16, 箭头宽 // 1.5)),
            )
            渲染器.fill_rect(尾)
            渲染器.fill_rect(头)
            return 1
        except Exception:
            return 0

    def _绘制几何判定区项(
        self,
        渲染器,
        项: Dict[str, Any],
        轨道: int,
        使用灰度: bool,
    ):
        颜色 = self._取轨道颜色(int(轨道), bool(使用灰度))
        矩形 = pygame.Rect(
            int(_取整数(项.get("x", 0), 0) - _取整数(项.get("w", 0), 0) // 2),
            int(_取整数(项.get("y", 0), 0) - _取整数(项.get("h", 0), 0) // 2),
            int(max(4, _取整数(项.get("w", 0), 0))),
            int(max(4, _取整数(项.get("h", 0), 0))),
        )
        try:
            渲染器.draw_color = (int(颜色[0]), int(颜色[1]), int(颜色[2]), 210)
            渲染器.fill_rect(矩形)
        except Exception:
            pass

    def _绘制几何特效项(
        self,
        渲染器,
        项: Dict[str, Any],
        轨道: int,
        使用灰度: bool,
    ):
        矩形 = 项.get("rect")
        if not isinstance(矩形, pygame.Rect):
            return
        颜色 = self._取轨道颜色(int(轨道), bool(使用灰度))
        alpha = int(
            max(36, min(220, round(float(_取浮点(项.get("强度", 1.0), 1.0)) * 180.0)))
        )
        try:
            渲染器.draw_color = (int(颜色[0]), int(颜色[1]), int(颜色[2]), alpha)
            渲染器.fill_rect(矩形)
        except Exception:
            pass

    @staticmethod
    def _轨道到key方位码(轨道序号: int) -> str:
        return {0: "bl", 1: "tl", 2: "cc", 3: "tr", 4: "br"}.get(int(轨道序号), "cc")

    @staticmethod
    def _轨道到arrow方位码(轨道序号: int) -> str:
        return {0: "lb", 1: "lt", 2: "cc", 3: "rt", 4: "rb"}.get(int(轨道序号), "cc")

    @staticmethod
    def _轨道到击中序列(轨道: int) -> Tuple[str, bool]:
        if int(轨道) == 0:
            return ("image_084", False)
        if int(轨道) == 1:
            return ("image_085", False)
        if int(轨道) == 2:
            return ("image_086", False)
        if int(轨道) == 3:
            return ("image_085", True)
        if int(轨道) == 4:
            return ("image_084", True)
        return ("image_086", False)

    def _取轨道颜色(self, 轨道: int, 使用灰度: bool) -> Tuple[int, int, int]:
        轨 = int(max(0, min(4, int(轨道))))
        颜色表 = self._灰度轨道颜色 if bool(使用灰度) else self._彩色轨道颜色
        try:
            return tuple(int(v) for v in 颜色表[轨])
        except Exception:
            return (220, 220, 220)
