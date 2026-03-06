import io
import json
import math
import os
import re
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pygame


def _取数(值: Any, 默认值: float = 0.0) -> float:
    try:
        if 值 is None:
            return float(默认值)
        return float(值)
    except Exception:
        return float(默认值)


@dataclass
class 渲染输入:
    当前谱面秒: float
    总时长秒: float

    轨道中心列表: List[int]  # 5轨：0..4
    判定线y: int
    底部y: int
    滚动速度px每秒: float

    箭头目标宽: int
    事件列表: List[Any]  # 只要求：轨道序号/开始秒/结束秒/类型

    显示_判定: str
    显示_连击: int
    显示_分数: int
    显示_百分比: str

    血条区域: pygame.Rect
    血量显示: float

    # 头像（从个人资料.json 读取）
    头像图: Optional[pygame.Surface]
    总血量HP: int = 0
    可见血量HP: int = 0
    Note层灰度: bool = False
    血条暴走: bool = False

    # ✅ 玩家信息
    玩家序号: int = 1
    玩家昵称: str = ""
    段位图: Optional[pygame.Surface] = None
    当前关卡: int = 1
    歌曲名: str = ""
    星级: int = 0

    # ✅ 新增：血条待机演示（不传也默认启用：45%~55%来回跳）
    血条待机演示: bool = True

    显示手装饰: bool = False
    错误提示: str = ""

    轨迹模式: str = "正常"
    隐藏模式: str = "关闭"
    大小倍率: float = 1.0

    # ✅ 新增：圆环频谱对象（场景里创建并绑定音频，布局里只负责“画”）
    圆环频谱对象: Optional[Any] = None


class _贴图集:
    def __init__(self, 帧表: Dict[str, pygame.Surface]):
        self.帧表 = 帧表

    def 取(self, 名: str) -> Optional[pygame.Surface]:
        return self.帧表.get(str(名), None)


class _皮肤包:
    """
    支持：目录 or zip
    结构：
      arrow/skin.json + skin.png
      blood_bar/skin.json + skin.png
      judge/skin.json + skin.png
      key/skin.json + skin.png
      key_effect/skin.json + skin.png
      number/skin.json + skin.png
    """

    def __init__(self):
        self.根路径: str = ""
        self.源类型: str = ""  # dir/zip
        self.压缩包路径: str = ""
        self.压缩包前缀: str = ""

        self.arrow: Optional[_贴图集] = None
        self.blood_bar: Optional[_贴图集] = None
        self.judge: Optional[_贴图集] = None
        self.key: Optional[_贴图集] = None
        self.key_effect: Optional[_贴图集] = None
        self.number: Optional[_贴图集] = None

        self.缺失分包: List[str] = []
        self.加载告警: List[str] = []

    def 加载(self, 皮肤根路径: str):
        self.根路径 = os.path.abspath(str(皮肤根路径 or "").strip())
        if not self.根路径:
            raise RuntimeError("皮肤根路径为空")

        self.arrow = None
        self.blood_bar = None
        self.judge = None
        self.key = None
        self.key_effect = None
        self.number = None
        self.缺失分包 = []
        self.加载告警 = []

        源类型, 真实路径, 前缀 = self._解析皮肤源(self.根路径)
        self.源类型 = 源类型
        self.压缩包路径 = 真实路径 if 源类型 == "zip" else ""
        self.压缩包前缀 = 前缀 if 源类型 == "zip" else ""

        if self.源类型 == "dir":
            self.arrow = self._尝试读贴图集_目录(self.根路径, "arrow")
            self.key = self._尝试读贴图集_目录(self.根路径, "key")
            self.key_effect = self._尝试读贴图集_目录(self.根路径, "key_effect")
            self.blood_bar = self._尝试读固定贴图集("blood_bar") or self._尝试读贴图集_目录(
                self.根路径, "blood_bar"
            )
            self.judge = self._尝试读固定贴图集("judge") or self._尝试读贴图集_目录(
                self.根路径, "judge"
            )
            self.number = self._尝试读固定贴图集("number") or self._尝试读贴图集_目录(
                self.根路径, "number"
            )
            return

        with zipfile.ZipFile(self.压缩包路径, "r") as 压缩包:
            self.arrow = self._尝试读贴图集_zip(压缩包, self.压缩包前缀, "arrow")
            self.key = self._尝试读贴图集_zip(压缩包, self.压缩包前缀, "key")
            self.key_effect = self._尝试读贴图集_zip(
                压缩包, self.压缩包前缀, "key_effect"
            )
            self.blood_bar = self._尝试读固定贴图集("blood_bar") or self._尝试读贴图集_zip(
                压缩包, self.压缩包前缀, "blood_bar"
            )
            self.judge = self._尝试读固定贴图集("judge") or self._尝试读贴图集_zip(
                压缩包, self.压缩包前缀, "judge"
            )
            self.number = self._尝试读固定贴图集("number") or self._尝试读贴图集_zip(
                压缩包, self.压缩包前缀, "number"
            )

    @staticmethod
    def _解析皮肤源(皮肤根路径: str) -> Tuple[str, str, str]:
        皮肤根路径 = os.path.abspath(皮肤根路径)

        目录json = os.path.join(皮肤根路径, "arrow", "skin.json")
        if os.path.isfile(目录json):
            return ("dir", 皮肤根路径, "")

        if os.path.isfile(皮肤根路径) and str(皮肤根路径).lower().endswith(".zip"):
            压缩包路径 = 皮肤根路径
            前缀 = _皮肤包._推断zip前缀(压缩包路径)
            return ("zip", 压缩包路径, 前缀)

        压缩包候选 = 皮肤根路径.rstrip(r"\/") + ".zip"
        if os.path.isfile(压缩包候选):
            前缀 = _皮肤包._推断zip前缀(压缩包候选)
            return ("zip", 压缩包候选, 前缀)

        raise FileNotFoundError(
            f"找不到皮肤：目录缺少 arrow/skin.json 且不存在 zip：{皮肤根路径}"
        )

    @staticmethod
    def _推断zip前缀(压缩包路径: str) -> str:
        with zipfile.ZipFile(压缩包路径, "r") as 压缩包:
            for 名 in 压缩包.namelist():
                if 名.endswith("arrow/skin.json"):
                    return 名[: -len("arrow/skin.json")]
        return ""

    @staticmethod
    def _安全读json(二进制数据: bytes) -> dict:
        try:
            return json.loads(二进制数据.decode("utf-8"))
        except Exception:
            return json.loads(二进制数据.decode("utf-8", errors="ignore"))

    @staticmethod
    def _安全转alpha(图: pygame.Surface) -> pygame.Surface:
        try:
            return 图.convert_alpha()
        except Exception:
            return 图

    @staticmethod
    def _转bool值(值: Any) -> bool:
        if isinstance(值, bool):
            return 值
        if isinstance(值, (int, float)):
            return bool(值)
        if isinstance(值, str):
            return str(值).strip().lower() in ("1", "true", "yes", "y", "on")
        return False

    @staticmethod
    def _取帧矩形(fr: dict) -> Tuple[int, int, int, int]:
        frame = fr.get("frame", {}) or {}
        if isinstance(frame, list) and len(frame) >= 4:
            try:
                return int(frame[0]), int(frame[1]), int(frame[2]), int(frame[3])
            except Exception:
                return 0, 0, 0, 0
        return (
            int(frame.get("x", 0)),
            int(frame.get("y", 0)),
            int(frame.get("w", 0)),
            int(frame.get("h", 0)),
        )

    @staticmethod
    def _取尺寸节点(节点: Any, 默认w: int, 默认h: int) -> Tuple[int, int]:
        if isinstance(节点, dict):
            return int(节点.get("w", 默认w)), int(节点.get("h", 默认h))
        if isinstance(节点, list) and len(节点) >= 2:
            return int(节点[0]), int(节点[1])
        return int(默认w), int(默认h)

    @staticmethod
    def _取偏移节点(节点: Any) -> Tuple[int, int]:
        if isinstance(节点, dict):
            return int(节点.get("x", 0)), int(节点.get("y", 0))
        if isinstance(节点, list) and len(节点) >= 2:
            return int(节点[0]), int(节点[1])
        return 0, 0

    def _构建帧表(
        self, 图集图: pygame.Surface, json数据: dict
    ) -> Dict[str, pygame.Surface]:
        帧表: Dict[str, pygame.Surface] = {}
        图集图 = self._安全转alpha(图集图)

        frames = json数据.get("frames", None)

        # 兼容 frames=list / frames=dict
        if isinstance(frames, dict):
            可迭代 = []
            for 文件名, fr in frames.items():
                if isinstance(fr, dict):
                    fr2 = dict(fr)
                    fr2["filename"] = 文件名
                    可迭代.append(fr2)
            frames = 可迭代

        if not isinstance(frames, list):
            raise RuntimeError("skin.json frames 不是 list/dict")

        for fr in frames:
            try:
                文件名 = str(fr.get("filename", "") or "")
                x, y, w, h = self._取帧矩形(fr)
                rotated = self._转bool值(fr.get("rotated", False))
                trimmed = self._转bool值(fr.get("trimmed", False))

                if (not 文件名) or w <= 0 or h <= 0:
                    continue

                子 = 图集图.subsurface(pygame.Rect(x, y, w, h)).copy()

                if rotated:
                    子 = pygame.transform.rotate(子, 90)

                if trimmed:
                    ssw, ssh = self._取尺寸节点(fr.get("sourceSize", {}) or {}, w, h)
                    ox, oy = self._取偏移节点(fr.get("spriteSourceSize", {}) or {})
                    还原 = pygame.Surface((max(1, ssw), max(1, ssh)), pygame.SRCALPHA)
                    还原.fill((0, 0, 0, 0))
                    还原.blit(子, (ox, oy))
                    子 = 还原

                帧表[文件名] = 子
            except Exception:
                continue

        return 帧表

    def _尝试读贴图集_路径(self, 目录路径: str, 标识: str) -> Optional[_贴图集]:
        json路径 = os.path.join(目录路径, "skin.json")
        png路径 = os.path.join(目录路径, "skin.png")
        if not os.path.isfile(json路径) or not os.path.isfile(png路径):
            self.缺失分包.append(标识)
            return None

        try:
            with open(json路径, "rb") as f:
                json数据 = self._安全读json(f.read())
            图集图 = pygame.image.load(png路径)
            帧表 = self._构建帧表(图集图, json数据)
            return _贴图集(帧表=帧表)
        except Exception as 异常:
            self.加载告警.append(f"{标识}加载失败：{type(异常).__name__} {异常}")
            return None

    def _尝试读贴图集_目录(self, 根: str, 子夹: str) -> Optional[_贴图集]:
        return self._尝试读贴图集_路径(os.path.join(根, 子夹), 子夹)

    def _查找固定贴图集目录(self, 子夹: str) -> str:
        相对子路径 = os.path.join("UI-img", "游戏界面", "血条", 子夹)
        起点 = str(self.根路径 or "").strip()
        if not 起点:
            return ""

        当前 = os.path.abspath(起点 if os.path.isdir(起点) else os.path.dirname(起点))
        for _ in range(10):
            候选 = os.path.join(当前, 相对子路径)
            if os.path.isfile(os.path.join(候选, "skin.json")) and os.path.isfile(
                os.path.join(候选, "skin.png")
            ):
                return 候选
            上级 = os.path.dirname(当前)
            if 上级 == 当前:
                break
            当前 = 上级
        return ""

    def _尝试读固定贴图集(self, 子夹: str) -> Optional[_贴图集]:
        目录路径 = self._查找固定贴图集目录(子夹)
        if not 目录路径:
            return None
        return self._尝试读贴图集_路径(目录路径, f"固定:{子夹}")

    def _尝试读贴图集_zip(
        self, 压缩包: zipfile.ZipFile, 前缀: str, 子夹: str
    ) -> Optional[_贴图集]:
        json名 = f"{前缀}{子夹}/skin.json"
        png名 = f"{前缀}{子夹}/skin.png"

        名单 = set(压缩包.namelist())
        if json名 not in 名单 or png名 not in 名单:
            self.缺失分包.append(子夹)
            return None

        try:
            json数据 = self._安全读json(压缩包.read(json名))
            png数据 = 压缩包.read(png名)
            图集图 = pygame.image.load(io.BytesIO(png数据))
            帧表 = self._构建帧表(图集图, json数据)
            return _贴图集(帧表=帧表)
        except Exception as 异常:
            self.加载告警.append(f"{子夹}加载失败：{type(异常).__name__} {异常}")
            return None


class 谱面渲染器:

    def __init__(self):
        self._皮肤包 = _皮肤包()
        self._当前皮肤路径: str = ""
        self._兜底击中特效方案: str = "击中特效1"
        self._兜底击中特效图集缓存: Dict[str, Optional[_贴图集]] = {}
        self._兜底击中特效帧名缓存: Dict[str, List[str]] = {}
        self._击中特效可见宽系数缓存: Dict[str, float] = {}

        self._按下反馈剩余秒: List[float] = [0.0] * 5
        self._按下反馈总时长秒: float = 0.12
        self._按键反馈轨道到按键列表: Dict[int, List[int]] = {
            0: [pygame.K_1, pygame.K_KP1],
            1: [pygame.K_7, pygame.K_KP7],
            2: [pygame.K_5, pygame.K_KP5],
            3: [pygame.K_9, pygame.K_KP9],
            4: [pygame.K_3, pygame.K_KP3],
        }

        # 击中特效
        self._击中特效进行秒: List[float] = [-1.0] * 5
        self._击中特效帧率: float = 60.0
        self._击中特效最大秒: float = 0.35

        # ✅ 用谱面秒驱动：便于 hold 循环
        self._击中特效开始谱面秒: List[float] = [-999.0] * 5
        self._击中特效循环到谱面秒: List[float] = [-999.0] * 5  # >0 表示循环到该结束秒

        # ✅ 最近一次渲染时的谱面秒
        self._最近渲染谱面秒: float = 0.0

        # ✅ 最近一次击中（按轨道记录谱面秒）
        self._最近击中谱面秒: List[float] = [-999.0] * 5
        self._命中匹配窗秒: float = 0.12
        self._击中后消失距离系数: float = 0.35
        self._击中后消失最小像素: int = 24

        # ✅ hold 命中状态
        self._命中hold开始谱面秒: List[float] = [-999.0] * 5
        self._命中hold结束谱面秒: List[float] = [-999.0] * 5
        self._hold当前按下中: List[bool] = [False] * 5

        # ✅ hold：松手后 1 秒隐藏“头”
        self._hold松手系统秒: List[Optional[float]] = [None] * 5
        self._hold松手隐藏延迟秒: float = 1.0

        # ✅ 计数动画组（Perfect/Cool/Good/Miss + Combo + xNN）
        self._计数动画剩余秒: float = 0.0
        self._计数动画总秒: float = 0.30
        self._计数动画判定: str = ""
        self._计数动画combo: int = 0
        self._计数动画队列: List[Tuple[str, int]] = []
        self._计数动画距上次触发秒: float = 999.0
        self._计数动画队列断流秒: float = 0.10
        self._计数动画停留总秒: float = 0.30
        self._计数动画停留剩余秒: float = 0.0
        self._计数动画打断最短秒: float = 0.033

        self._分数动画剩余秒: float = 0.0
        self._分数动画总秒: float = 0.18
        self._上次显示分数: Optional[int] = None

        self._缩放缓存: Dict[Tuple[str, int, int], pygame.Surface] = {}
        self._中心带边界缓存: Dict[Tuple[str, int, int], Tuple[int, int]] = {}

        # ✅ 固定资源缓存（board.png / 段位等独立文件）
        self._固定图缓存: Dict[str, Tuple[str, float, Optional[pygame.Surface]]] = {}
        self._顶部HUD静态层缓存: Optional[pygame.Surface] = None
        self._顶部HUD静态层签名: Optional[Tuple[Any, ...]] = None
        self._顶部HUD半静态层缓存: Optional[pygame.Surface] = None
        self._顶部HUD半静态层签名: Optional[Tuple[Any, ...]] = None
        self._notes静态层缓存: Optional[pygame.Surface] = None
        self._notes静态层签名: Optional[Tuple[Any, ...]] = None
        self._判定区层缓存: Optional[pygame.Surface] = None
        self._判定区层签名: Optional[Tuple[Any, ...]] = None
        self._头像灰度缓存key: Optional[Tuple[int, int, int]] = None
        self._头像灰度缓存图: Optional[pygame.Surface] = None

    def _取游戏区参数(self) -> Dict[str, float]:
        def _取浮点(值: Any, 默认: float) -> float:
            try:
                return float(值)
            except Exception:
                return float(默认)

        默认参数 = {
            "y偏移": -12.0,
            "缩放": 1.0,
            "hold宽度系数": 0.96,
            "判定区宽度系数": 1.0,
            "击中特效宽度系数": 3.0,
            "击中特效偏移x": 0.0,
            "击中特效偏移y": 0.0,
            "击中特效走布局层": 1.0,
        }

        # ✅ 1) 优先：从布局管理器内存里读（调试拖动立刻生效，不依赖保存/mtime）
        布局 = self._确保布局管理器()
        if 布局 is not None:
            try:
                布局数据 = getattr(布局, "_布局数据", None)
                if isinstance(布局数据, dict):
                    游戏区参数 = 布局数据.get("游戏区参数", None)
                    if not isinstance(游戏区参数, dict):
                        游戏区参数 = {}
                        布局数据["游戏区参数"] = 游戏区参数

                    # 补默认键
                    for k, v in 默认参数.items():
                        if k not in 游戏区参数:
                            游戏区参数[k] = v

                    参数 = {
                        k: _取浮点(游戏区参数.get(k), 默认参数[k]) for k in 默认参数
                    }

                    # 合法范围约束
                    参数["缩放"] = float(max(0.3, min(3.0, 参数["缩放"])))
                    参数["hold宽度系数"] = float(
                        max(0.6, min(1.2, 参数["hold宽度系数"]))
                    )
                    参数["判定区宽度系数"] = float(
                        max(0.6, min(2.0, 参数["判定区宽度系数"]))
                    )
                    参数["击中特效宽度系数"] = float(
                        max(0.8, min(6.0, 参数["击中特效宽度系数"]))
                    )
                    参数["击中特效走布局层"] = (
                        1.0 if float(参数.get("击中特效走布局层", 1.0)) >= 0.5 else 0.0
                    )
                    return 参数
            except Exception:
                pass

        # ✅ 2) 兜底：读 json 文件（沿用你原来的 mtime 缓存）
        if not hasattr(self, "_游戏区参数_缓存"):
            self._游戏区参数_缓存 = {}
            self._游戏区参数_mtime = -1.0

        try:
            项目根 = os.path.abspath(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
            )
        except Exception:
            项目根 = os.path.abspath(os.getcwd())

        布局路径 = os.path.join(项目根, "json", "谱面渲染器_布局.json")
        try:
            mtime = (
                float(os.path.getmtime(布局路径)) if os.path.isfile(布局路径) else -1.0
            )
        except Exception:
            mtime = -1.0

        if mtime == float(getattr(self, "_游戏区参数_mtime", -2.0)) and isinstance(
            getattr(self, "_游戏区参数_缓存", None), dict
        ):
            return dict(self._游戏区参数_缓存)

        参数 = dict(默认参数)

        try:
            if os.path.isfile(布局路径):
                with open(布局路径, "r", encoding="utf-8") as f:
                    数据 = json.load(f)
                if isinstance(数据, dict):
                    游戏区参数 = 数据.get("游戏区参数", {}) or {}
                    if isinstance(游戏区参数, dict):
                        for k in list(参数.keys()):
                            if k in 游戏区参数:
                                参数[k] = _取浮点(游戏区参数.get(k), 参数[k])
        except Exception:
            pass

        参数["缩放"] = float(max(0.3, min(3.0, 参数["缩放"])))
        参数["hold宽度系数"] = float(max(0.6, min(1.2, 参数["hold宽度系数"])))
        参数["判定区宽度系数"] = float(max(0.6, min(2.0, 参数["判定区宽度系数"])))
        参数["击中特效宽度系数"] = float(max(0.8, min(6.0, 参数["击中特效宽度系数"])))
        参数["击中特效走布局层"] = (
            1.0 if float(参数.get("击中特效走布局层", 1.0)) >= 0.5 else 0.0
        )

        self._游戏区参数_缓存 = dict(参数)
        self._游戏区参数_mtime = float(mtime)
        return dict(参数)

    def _确保命中映射缓存(self):
        # 你原来的（保留，避免别处引用炸）
        if not hasattr(self, "_待选择命中谱面秒"):
            self._待选择命中谱面秒 = [-999.0] * 5
        if not hasattr(self, "_命中tap目标谱面秒"):
            self._命中tap目标谱面秒 = [-999.0] * 5
        if not hasattr(self, "_命中tap目标过期谱面秒"):
            self._命中tap目标过期谱面秒 = [-999.0] * 5

        # ✅ 新增：每轨“命中时间队列”（毫秒整数，避免 float 误差）
        if not hasattr(self, "_待命中队列毫秒") or (
            not isinstance(getattr(self, "_待命中队列毫秒"), list)
        ):
            self._待命中队列毫秒 = [[] for _ in range(5)]
        if len(self._待命中队列毫秒) != 5:
            self._待命中队列毫秒 = [[] for _ in range(5)]

        # ✅ 新增：已命中 tap 表（key=st_ms, value=过期ms）
        if not hasattr(self, "_已命中tap过期表毫秒") or (
            not isinstance(getattr(self, "_已命中tap过期表毫秒"), list)
        ):
            self._已命中tap过期表毫秒 = [{} for _ in range(5)]
        if len(self._已命中tap过期表毫秒) != 5:
            self._已命中tap过期表毫秒 = [{} for _ in range(5)]

    def 设置皮肤(self, 皮肤根路径: str):
        皮肤根路径 = str(皮肤根路径 or "").strip()
        if not 皮肤根路径:
            raise RuntimeError("皮肤根路径为空")

        if os.path.abspath(皮肤根路径) == os.path.abspath(self._当前皮肤路径 or ""):
            return

        self._皮肤包.加载(皮肤根路径)
        self._当前皮肤路径 = 皮肤根路径
        self._缩放缓存.clear()
        self._击中特效可见宽系数缓存.clear()
        self._顶部HUD静态层缓存 = None
        self._顶部HUD静态层签名 = None
        self._顶部HUD半静态层缓存 = None
        self._顶部HUD半静态层签名 = None
        self._notes静态层缓存 = None
        self._notes静态层签名 = None
        self._判定区层缓存 = None
        self._判定区层签名 = None

    @staticmethod
    def _规范兜底击中特效方案(方案: str) -> str:
        文本 = str(方案 or "").strip()
        if ("2" in 文本) or ("特效2" in 文本):
            return "击中特效2"
        return "击中特效1"

    @staticmethod
    def _解析帧文件序列与序号(文件名: str) -> Tuple[str, int]:
        基名 = os.path.basename(str(文件名 or ""))
        小写 = 基名.lower()
        if not (
            小写.endswith(".png")
            or 小写.endswith(".jpg")
            or 小写.endswith(".jpeg")
            or 小写.endswith(".webp")
        ):
            return os.path.splitext(基名)[0], 0

        m = re.match(
            r"^(?P<序列>.+?)(?:_|-)(?P<序号>\d{1,6})\.(png|jpg|jpeg|webp)$",
            基名,
            re.IGNORECASE,
        )
        if m:
            序列名 = str(m.group("序列")).rstrip(" _-")
            return (序列名 if 序列名 else os.path.splitext(基名)[0]), int(m.group("序号"))

        m2 = re.match(
            r"^(?P<序列>.*?)(?P<序号>\d{1,6})\.(png|jpg|jpeg|webp)$",
            基名,
            re.IGNORECASE,
        )
        if m2:
            序列名 = str(m2.group("序列")).rstrip(" _-")
            if 序列名.strip():
                return 序列名, int(m2.group("序号"))

        return os.path.splitext(基名)[0], 0

    def _排序并筛选兜底帧名(self, 帧名列表: List[str]) -> List[str]:
        if not 帧名列表:
            return []
        分组: Dict[str, List[Tuple[int, str]]] = {}
        for 名 in 帧名列表:
            try:
                序列, 序号 = self._解析帧文件序列与序号(str(名 or ""))
                分组.setdefault(str(序列), []).append((int(序号), str(名)))
            except Exception:
                continue
        if not 分组:
            return []
        主序列 = max(分组.keys(), key=lambda k: len(分组.get(k, [])))
        列表 = list(分组.get(主序列, []))
        列表.sort(key=lambda it: (int(it[0]), str(it[1])))
        return [str(名) for _, 名 in 列表]

    def _构建击中特效序列映射(
        self, 帧名列表: List[str]
    ) -> Dict[str, List[str]]:
        映射: Dict[str, List[Tuple[int, str]]] = {}
        for 名 in 帧名列表:
            try:
                序列, 序号 = self._解析帧文件序列与序号(str(名 or ""))
                if not 序列:
                    continue
                映射.setdefault(str(序列), []).append((int(序号), str(名)))
            except Exception:
                continue

        输出: Dict[str, List[str]] = {}
        for 序列名, 序列帧 in 映射.items():
            try:
                序列帧.sort(key=lambda it: (int(it[0]), str(it[1])))
                输出[str(序列名)] = [str(名) for _, 名 in 序列帧]
            except Exception:
                continue
        return 输出

    @staticmethod
    def _从序列映射选序列(
        序列映射: Dict[str, List[str]], 候选列表: List[str]
    ) -> str:
        for 候选 in 候选列表:
            序列帧 = 序列映射.get(str(候选), [])
            if 序列帧:
                return str(候选)
        if not 序列映射:
            return ""
        # 最后兜底：取帧数最多的序列，避免 key_effect 命名不一致时完全不显示。
        return max(序列映射.keys(), key=lambda k: len(序列映射.get(k, [])))

    def _估算击中特效可见宽系数(
        self, 图集: Optional[_贴图集], 序列名: str, 帧名列表: List[str]
    ) -> float:
        if 图集 is None or (not 序列名) or (not 帧名列表):
            return 1.0

        缓存键 = str(序列名)
        已缓存 = self._击中特效可见宽系数缓存.get(缓存键, None)
        if 已缓存 is not None:
            return float(已缓存)

        样本索引: List[int] = [0, len(帧名列表) // 3, (len(帧名列表) * 2) // 3, len(帧名列表) - 1]
        样本索引 = sorted(set([int(max(0, min(len(帧名列表) - 1, i))) for i in 样本索引]))

        可见宽样本: List[int] = []
        原图宽 = 0
        for idx in 样本索引:
            try:
                名 = str(帧名列表[idx])
                图 = 图集.取(名)
                if 图 is None:
                    continue
                原图宽 = max(int(原图宽), int(图.get_width()))

                可见宽 = 0
                try:
                    # 不能只看 alpha：很多素材黑底也带 alpha，需结合亮度阈值提取真正发光主体。
                    import numpy as _np

                    rgb = pygame.surfarray.array3d(图)
                    a = pygame.surfarray.array_alpha(图)
                    亮度 = rgb[:, :, 0].astype(_np.int32) + rgb[:, :, 1].astype(_np.int32) + rgb[:, :, 2].astype(_np.int32)
                    亮度阈值 = int(max(140, int(_np.max(亮度) * 0.52)))
                    掩码 = (a >= 20) & (亮度 >= 亮度阈值)
                    列命中 = _np.any(掩码, axis=1)
                    命中索引 = _np.flatnonzero(列命中)
                    if 命中索引.size > 0:
                        可见宽 = int(命中索引[-1] - 命中索引[0] + 1)
                except Exception:
                    可见宽 = 0

                if 可见宽 > 0:
                    可见宽样本.append(int(可见宽))
            except Exception:
                continue

        系数 = 1.0
        if 原图宽 > 0 and 可见宽样本:
            # 用样本中的最大可见宽，避免末帧淡出把尺寸误判得过大或过小。
            最大可见宽 = int(max(可见宽样本))
            if 最大可见宽 > 0:
                系数 = float(原图宽) / float(最大可见宽)
        elif 原图宽 > 0:
            # 样本都淡出时回退 1.0，避免异常放大。
            系数 = 1.0
        系数 = float(max(1.0, min(5.0, 系数)))
        self._击中特效可见宽系数缓存[缓存键] = float(系数)
        return float(系数)

    def 设置兜底击中特效方案(self, 方案: str):
        self._兜底击中特效方案 = self._规范兜底击中特效方案(方案)

    def _查找通用击中特效目录(self, 方案: str) -> str:
        方案目录名 = self._规范兜底击中特效方案(方案)
        相对子路径 = os.path.join("UI-img", "游戏界面", "通用特效", 方案目录名)

        起点列表: List[str] = []
        for 值 in (
            str(self._当前皮肤路径 or "").strip(),
            str(getattr(self._皮肤包, "根路径", "") or "").strip(),
            os.path.dirname(os.path.abspath(__file__)),
            os.getcwd(),
        ):
            if not 值:
                continue
            起点列表.append(值)

        for 起点 in 起点列表:
            try:
                当前 = os.path.abspath(起点 if os.path.isdir(起点) else os.path.dirname(起点))
            except Exception:
                continue
            for _ in range(12):
                候选 = os.path.join(当前, 相对子路径)
                if os.path.isfile(os.path.join(候选, "skin.json")) and os.path.isfile(
                    os.path.join(候选, "skin.png")
                ):
                    return 候选
                上级 = os.path.dirname(当前)
                if 上级 == 当前:
                    break
                当前 = 上级
        return ""

    def _取兜底击中特效图集(self) -> Optional[_贴图集]:
        方案 = self._规范兜底击中特效方案(getattr(self, "_兜底击中特效方案", ""))
        if 方案 in self._兜底击中特效图集缓存:
            return self._兜底击中特效图集缓存.get(方案, None)

        目录 = self._查找通用击中特效目录(方案)
        if not 目录:
            self._兜底击中特效图集缓存[方案] = None
            self._兜底击中特效帧名缓存[方案] = []
            return None

        读取器 = _皮肤包()
        图集 = 读取器._尝试读贴图集_路径(目录, f"通用击中特效:{方案}")
        self._兜底击中特效图集缓存[方案] = 图集
        if 图集 is not None:
            try:
                全部帧名 = [str(k) for k in list(getattr(图集, "帧表", {}).keys())]
                self._兜底击中特效帧名缓存[方案] = self._排序并筛选兜底帧名(全部帧名)
            except Exception:
                self._兜底击中特效帧名缓存[方案] = []
        else:
            self._兜底击中特效帧名缓存[方案] = []
        return 图集

    def _取兜底击中特效帧名列表(self) -> List[str]:
        方案 = self._规范兜底击中特效方案(getattr(self, "_兜底击中特效方案", ""))
        if 方案 not in self._兜底击中特效帧名缓存:
            self._取兜底击中特效图集()
        return list(self._兜底击中特效帧名缓存.get(方案, []))

    def 取加载诊断(self) -> str:
        诊断 = []
        if self._皮肤包.加载告警:
            诊断.append("加载告警：" + " | ".join(self._皮肤包.加载告警))
        return " ; ".join(诊断)

    def 触发按下反馈(self, 轨道序号: int):
        轨道序号 = int(轨道序号)
        if 0 <= 轨道序号 < 5:
            self._按下反馈剩余秒[轨道序号] = float(self._按下反馈总时长秒)

    def 设置按键反馈映射(self, 轨道到按键列表: Optional[Dict[int, List[int]]]):
        默认映射: Dict[int, List[int]] = {
            0: [pygame.K_1, pygame.K_KP1],
            1: [pygame.K_7, pygame.K_KP7],
            2: [pygame.K_5, pygame.K_KP5],
            3: [pygame.K_9, pygame.K_KP9],
            4: [pygame.K_3, pygame.K_KP3],
        }
        结果: Dict[int, List[int]] = {}
        if isinstance(轨道到按键列表, dict):
            for 轨道 in range(5):
                原值 = 轨道到按键列表.get(int(轨道), [])
                if isinstance(原值, (list, tuple)):
                    键表 = []
                    for k in 原值:
                        try:
                            键表.append(int(k))
                        except Exception:
                            continue
                    结果[int(轨道)] = 键表
                else:
                    结果[int(轨道)] = []
        for 轨道 in range(5):
            if not 结果.get(int(轨道)):
                结果[int(轨道)] = list(默认映射.get(int(轨道), []))
        self._按键反馈轨道到按键列表 = 结果

    def 触发判定提示(self, 判定: str):
        判定 = str(判定 or "").strip().lower()
        if not 判定:
            return
        self._判定提示 = 判定
        self._判定提示剩余秒 = 0.45

    def 触发击中特效(
        self, 轨道序号: int, 判定: str, 发生谱面秒: Optional[float] = None
    ):
        判定 = str(判定 or "").strip().lower()

        轨道序号 = int(轨道序号)
        if not (0 <= 轨道序号 < 5):
            return
        if 判定 == "miss":
            return

        if 发生谱面秒 is None:
            发生谱面秒 = float(self._最近渲染谱面秒)

        # ✅ 命中队列：不再用“单槽位覆盖”
        self._确保命中映射缓存()
        try:
            命中毫秒 = int(round(float(发生谱面秒) * 1000.0))
        except Exception:
            命中毫秒 = int(round(float(self._最近渲染谱面秒) * 1000.0))

        队列 = self._待命中队列毫秒[轨道序号]
        队列.append(int(命中毫秒))

        # ✅ 防止无限增长（极端情况下）
        if len(队列) > 12:
            del 队列[: len(队列) - 12]

        # （可选保留）如果你别处还在用 _待选择命中谱面秒，也让它继续同步最后一次
        try:
            self._待选择命中谱面秒[轨道序号] = float(发生谱面秒)
        except Exception:
            self._待选择命中谱面秒[轨道序号] = float(self._最近渲染谱面秒)

        # 原逻辑：击中特效播放
        self._击中特效开始谱面秒[轨道序号] = float(发生谱面秒)
        self._击中特效循环到谱面秒[轨道序号] = -999.0
        self._击中特效进行秒[轨道序号] = 0.0

    def 触发combo轻闪(self, combo: int):
        # 懒初始化：不依赖 __init__
        if not hasattr(self, "_combo轻闪剩余秒"):
            self._combo轻闪剩余秒 = 0.0
            self._combo轻闪总秒 = 0.12
            self._combo轻闪combo = 0

        try:
            self._combo轻闪combo = int(max(0, combo))
        except Exception:
            self._combo轻闪combo = 0

        self._combo轻闪剩余秒 = float(getattr(self, "_combo轻闪总秒", 0.12) or 0.12)

    def 触发计数动画(self, 判定: str, combo: int):
        判定 = str(判定 or "").strip().lower()
        if not 判定:
            return

        try:
            combo = int(max(0, combo))
        except Exception:
            combo = 0

        self._计数动画距上次触发秒 = 0.0
        self._计数动画停留剩余秒 = 0.0

        if float(getattr(self, "_计数动画剩余秒", 0.0) or 0.0) > 0.0:
            self._计数动画队列.append((判定, int(combo)))
            if len(self._计数动画队列) > 64:
                del self._计数动画队列[: len(self._计数动画队列) - 64]
            return

        self._开始计数动画(判定, int(combo))

    def _开始计数动画(self, 判定: str, combo: int):
        判定 = str(判定 or "").strip().lower()
        if not 判定:
            return

        self._计数动画总秒 = 0.20
        self._计数动画判定 = 判定
        self._计数动画combo = int(max(0, combo))
        self._计数动画剩余秒 = float(self._计数动画总秒)

        try:
            self.触发combo轻闪(self._计数动画combo)
        except Exception:
            pass

    def 触发分数缩放动画(self):
        self._分数动画剩余秒 = float(
            max(0.06, getattr(self, "_分数动画总秒", 0.18) or 0.18)
        )

    def _取分数缩放(self) -> float:
        剩余 = float(getattr(self, "_分数动画剩余秒", 0.0) or 0.0)
        总时长 = float(getattr(self, "_分数动画总秒", 0.18) or 0.18)
        if 剩余 <= 0.0 or 总时长 <= 0.0:
            return 1.0

        进度 = 1.0 - float(max(0.0, min(总时长, 剩余)) / max(0.001, 总时长))
        return float(1.0 + math.sin(math.pi * 进度) * 0.14)

    def _更新按键反馈缩放(self, 时间差秒: float):
        最小缩放 = 0.50
        时间差秒 = float(max(0.0, min(0.2, 时间差秒)))

        if (not hasattr(self, "_按键反馈缩放")) or (
            not isinstance(getattr(self, "_按键反馈缩放"), list)
        ):
            self._按键反馈缩放 = [1.0] * 5
        if len(self._按键反馈缩放) != 5:
            self._按键反馈缩放 = [1.0] * 5

        try:
            按下数组 = pygame.key.get_pressed()
        except Exception:
            按下数组 = None

        轨道到按键列表 = (
            dict(getattr(self, "_按键反馈轨道到按键列表", {}) or {})
            if isinstance(getattr(self, "_按键反馈轨道到按键列表", None), dict)
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

        按下速度 = 26.0
        松开速度 = 18.0

        for i in range(5):
            目标缩放 = 1.0

            try:
                剩余 = float(self._按下反馈剩余秒[i])
            except Exception:
                剩余 = 0.0

            if 剩余 > 0.0:
                p = 1.0 - (剩余 / float(max(0.001, self._按下反馈总时长秒)))
                p = float(max(0.0, min(1.0, p)))
                tap缩放 = 1.0 - 0.50 * math.sin(p * math.pi)
                tap缩放 = float(max(最小缩放, min(1.0, tap缩放)))
                目标缩放 = tap缩放

            if _轨道是否按下(i):
                目标缩放 = 最小缩放

            当前缩放 = float(self._按键反馈缩放[i])
            速度 = 按下速度 if 目标缩放 < 当前缩放 else 松开速度
            系数 = float(min(1.0, 时间差秒 * 速度))
            新缩放 = 当前缩放 + (目标缩放 - 当前缩放) * 系数
            self._按键反馈缩放[i] = float(max(最小缩放, min(1.0, 新缩放)))

    def _取头像图_按血量状态(self, 输入: 渲染输入) -> Optional[pygame.Surface]:
        原图 = getattr(输入, "头像图", None)
        if not isinstance(原图, pygame.Surface):
            return 原图
        if not bool(getattr(输入, "Note层灰度", False)):
            return 原图

        try:
            缓存key = (id(原图), int(原图.get_width()), int(原图.get_height()))
        except Exception:
            缓存key = (id(原图), 0, 0)

        if self._头像灰度缓存key != 缓存key or self._头像灰度缓存图 is None:
            try:
                self._头像灰度缓存图 = pygame.transform.grayscale(原图).convert_alpha()
            except Exception:
                self._头像灰度缓存图 = 原图
            self._头像灰度缓存key = 缓存key

        return self._头像灰度缓存图

    def 更新(self, 时间差秒: float):
        时间差秒 = float(max(0.0, min(0.2, 时间差秒)))
        self._计数动画距上次触发秒 = float(
            max(0.0, float(getattr(self, "_计数动画距上次触发秒", 999.0)) + 时间差秒)
        )

        for i in range(5):
            self._按下反馈剩余秒[i] = max(
                0.0, float(self._按下反馈剩余秒[i]) - 时间差秒
            )
        self._更新按键反馈缩放(时间差秒)

        周期秒 = float(18.0 / max(1.0, float(self._击中特效帧率)))
        for i in range(5):
            if self._击中特效进行秒[i] < 0.0:
                continue

            if float(self._击中特效循环到谱面秒[i]) > 0.0:
                self._击中特效进行秒[i] = (
                    float(self._击中特效进行秒[i]) + 时间差秒
                ) % max(0.001, 周期秒)
                continue

            self._击中特效进行秒[i] = float(self._击中特效进行秒[i]) + 时间差秒
            if self._击中特效进行秒[i] > float(self._击中特效最大秒):
                self._击中特效进行秒[i] = -1.0
                self._击中特效开始谱面秒[i] = -999.0
                self._击中特效循环到谱面秒[i] = -999.0

        已切换计数动画 = False
        if self._计数动画剩余秒 > 0.0:
            已显示秒 = float(
                max(0.0, float(self._计数动画总秒) - float(self._计数动画剩余秒))
            )
            if (
                self._计数动画队列
                and float(self._计数动画距上次触发秒)
                <= float(getattr(self, "_计数动画队列断流秒", 0.10) or 0.10)
                and 已显示秒
                >= float(getattr(self, "_计数动画打断最短秒", 0.05) or 0.05)
            ):
                下一个判定, 下一个combo = self._计数动画队列.pop(0)
                self._开始计数动画(str(下一个判定), int(下一个combo))
                已切换计数动画 = True

            if not 已切换计数动画:
                self._计数动画剩余秒 = max(
                    0.0, float(self._计数动画剩余秒) - 时间差秒
                )
                if self._计数动画剩余秒 <= 0.0:
                    if self._计数动画队列:
                        if float(self._计数动画距上次触发秒) <= float(
                            getattr(self, "_计数动画队列断流秒", 0.10) or 0.10
                        ):
                            下一个判定, 下一个combo = self._计数动画队列.pop(0)
                            self._开始计数动画(str(下一个判定), int(下一个combo))
                        else:
                            self._计数动画队列.clear()
                            self._计数动画停留剩余秒 = float(
                                getattr(self, "_计数动画停留总秒", 0.30) or 0.30
                            )
                    else:
                        self._计数动画停留剩余秒 = float(
                            getattr(self, "_计数动画停留总秒", 0.30) or 0.30
                        )
        elif self._计数动画停留剩余秒 > 0.0:
            self._计数动画停留剩余秒 = max(
                0.0, float(self._计数动画停留剩余秒) - 时间差秒
            )
        elif self._计数动画队列:
            if float(self._计数动画距上次触发秒) <= float(
                getattr(self, "_计数动画队列断流秒", 0.10) or 0.10
            ):
                下一个判定, 下一个combo = self._计数动画队列.pop(0)
                self._开始计数动画(str(下一个判定), int(下一个combo))
            else:
                self._计数动画队列.clear()

        if self._分数动画剩余秒 > 0.0:
            self._分数动画剩余秒 = max(
                0.0, float(self._分数动画剩余秒) - 时间差秒
            )

        # ✅ combo 轻闪倒计时
        if hasattr(self, "_combo轻闪剩余秒"):
            try:
                self._combo轻闪剩余秒 = max(
                    0.0, float(getattr(self, "_combo轻闪剩余秒", 0.0)) - 时间差秒
                )
            except Exception:
                self._combo轻闪剩余秒 = 0.0

    def 渲染(
        self,
        屏幕: pygame.Surface,
        输入: 渲染输入,
        字体: pygame.font.Font,
        小字体: pygame.font.Font,
    ):
        try:
            self._最近渲染谱面秒 = float(输入.当前谱面秒)
        except Exception:
            self._最近渲染谱面秒 = 0.0

        # 1) 顶部HUD
        self._绘制血条(屏幕, 输入, 字体, 小字体)

        if bool(getattr(输入, "Note层灰度", False)):
            notes层 = pygame.Surface(屏幕.get_size(), pygame.SRCALPHA)
            # 低血量时只灰化主 notes 层；击中特效序列帧保持彩色单独补绘。
            self._绘制notes层(notes层, 输入, 绘制击中特效=False)
            屏幕.blit(pygame.transform.grayscale(notes层), (0, 0))
            self._绘制击中特效(屏幕, 输入)
        else:
            self._绘制notes层(屏幕, 输入)

        诊断 = self.取加载诊断()
        if 诊断:
            文 = 小字体.render(诊断, True, (255, 180, 120))
            屏幕.blit(文, (18, int(输入.血条区域.bottom + 8)))

        if 输入.错误提示:
            文2 = 小字体.render(str(输入.错误提示), True, (255, 120, 120))
            屏幕.blit(文2, (18, int(输入.血条区域.bottom + 28)))

    def _绘制notes层(
        self, 屏幕: pygame.Surface, 输入: 渲染输入, 绘制击中特效: bool = True
    ):
        布局 = self._确保布局管理器()
        布局版本 = float(
            getattr(布局, "_上次mtime", -1.0) if 布局 is not None else -1.0
        )
        notes静态签名 = (
            tuple(int(v) for v in 屏幕.get_size()),
            tuple(int(v) for v in list(getattr(输入, "轨道中心列表", []) or [])[:5]),
            int(getattr(输入, "判定线y", 0) or 0),
            int(getattr(输入, "底部y", 0) or 0),
            int(getattr(输入, "箭头目标宽", 0) or 0),
            float(self._取游戏区参数().get("y偏移", 0.0)),
            float(self._取游戏区参数().get("缩放", 1.0)),
            布局版本,
        )
        if (
            self._notes静态层缓存 is None
            or self._notes静态层签名 != notes静态签名
            or self._notes静态层缓存.get_size() != 屏幕.get_size()
        ):
            self._notes静态层缓存 = pygame.Surface(屏幕.get_size(), pygame.SRCALPHA)
            self._notes静态层缓存.fill((0, 0, 0, 0))
            self._绘制轨道背景(self._notes静态层缓存, 输入)
            self._notes静态层签名 = notes静态签名
        屏幕.blit(self._notes静态层缓存, (0, 0))

        # 2) arrows（音符还是你原来的渲染逻辑）
        self._绘制音符(屏幕, 输入)

        # 3) 判定区（独立缓存：按反馈缩放/几何变化失效）
        判定区签名 = (
            tuple(int(v) for v in 屏幕.get_size()),
            tuple(int(v) for v in list(getattr(输入, "轨道中心列表", []) or [])[:5]),
            int(getattr(输入, "判定线y", 0) or 0),
            int(getattr(输入, "箭头目标宽", 0) or 0),
            tuple(round(float(v), 4) for v in list(getattr(self, "_按键反馈缩放", []) or [])[:5]),
            float(self._取游戏区参数().get("判定区宽度系数", 1.0)),
            float(self._取游戏区参数().get("y偏移", 0.0)),
            float(self._取游戏区参数().get("缩放", 1.0)),
            布局版本,
        )
        if (
            self._判定区层缓存 is None
            or self._判定区层签名 != 判定区签名
            or self._判定区层缓存.get_size() != 屏幕.get_size()
        ):
            self._判定区层缓存 = pygame.Surface(屏幕.get_size(), pygame.SRCALPHA)
            self._判定区层缓存.fill((0, 0, 0, 0))
            self._绘制判定区(self._判定区层缓存, 输入)
            self._判定区层签名 = 判定区签名
        屏幕.blit(self._判定区层缓存, (0, 0))

        # 4) 特效层（走 JSON；若 JSON 缺控件会兜底旧逻辑）
        if bool(绘制击中特效):
            self._绘制击中特效(屏幕, 输入)

        # 5) 计数动画组（仍走 JSON）
        self._绘制计数动画组(屏幕, 输入)

    def _构建notes装饰上下文(
        self, 屏幕: pygame.Surface, 输入: 渲染输入
    ) -> Dict[str, Any]:
        布局 = self._确保布局管理器()
        if 布局 is None:
            return {}

        try:
            比例 = float(布局.取全局缩放(屏幕.get_size()))
        except Exception:
            比例 = 1.0
        if 比例 <= 0:
            比例 = 1.0

        参数 = self._取游戏区参数()
        游戏缩放 = float(参数.get("缩放", 1.0))
        y偏移 = float(参数.get("y偏移", 0.0))
        判定区宽度系数 = float(参数.get("判定区宽度系数", 1.08))

        特效宽度系数 = float(参数.get("击中特效宽度系数", 2.6))
        特效偏移x = float(参数.get("击中特效偏移x", 0.0))
        特效偏移y = float(参数.get("击中特效偏移y", 0.0))

        轨道中心列表_布局 = []
        for x in 输入.轨道中心列表 or []:
            try:
                轨道中心列表_布局.append(float(x) / 比例)
            except Exception:
                轨道中心列表_布局.append(0.0)

        判定线y_游戏_布局 = (float(getattr(输入, "判定线y", 0)) + y偏移) / 比例
        底部y_游戏_布局 = (float(getattr(输入, "底部y", 0)) + y偏移) / 比例

        音符区高度_布局 = float(max(10.0, 底部y_游戏_布局 - 判定线y_游戏_布局))
        音符区中心y_布局 = float(判定线y_游戏_布局 + 音符区高度_布局 * 0.5)

        轨道中心间距_布局 = 0.0
        if len(轨道中心列表_布局) >= 2:
            轨道中心间距_布局 = float(轨道中心列表_布局[1] - 轨道中心列表_布局[0])

        判定区_receptor宽_布局 = (
            float(getattr(输入, "箭头目标宽", 0)) * 判定区宽度系数 * 游戏缩放
        ) / 比例
        判定区_receptor宽_布局 = float(max(12.0, 判定区_receptor宽_布局))

        左手x_布局 = 0.0
        右手x_布局 = 0.0
        if len(轨道中心列表_布局) >= 5:
            间距 = float(
                轨道中心间距_布局
                if 轨道中心间距_布局 != 0.0
                else 判定区_receptor宽_布局
            )
            左手x_布局 = float(轨道中心列表_布局[0] - 间距)
            右手x_布局 = float(轨道中心列表_布局[4] + 间距)

        判定线y_特效_布局 = (
            float(getattr(输入, "判定线y", 0)) + y偏移 + 特效偏移y
        ) / 比例
        特效目标宽_布局 = (
            float(getattr(输入, "箭头目标宽", 0)) * 特效宽度系数 * 游戏缩放 * 1.25
        ) / 比例
        特效目标宽_布局 = float(max(40.0, 特效目标宽_布局))
        击中特效偏移x_布局 = float(特效偏移x) / 比例

        # 判定区缩放（从你现有的回弹数组读）
        判定区缩放表 = []
        try:
            if hasattr(self, "_按键反馈缩放") and isinstance(
                getattr(self, "_按键反馈缩放"), list
            ):
                判定区缩放表 = list(getattr(self, "_按键反馈缩放"))
        except Exception:
            判定区缩放表 = []
        while len(判定区缩放表) < 5:
            判定区缩放表.append(1.0)

        上下文: Dict[str, Any] = {
            "轨道中心列表_布局": 轨道中心列表_布局,
            "判定线y_游戏_布局": float(判定线y_游戏_布局),
            "底部y_游戏_布局": float(底部y_游戏_布局),
            "音符区高度_布局": float(音符区高度_布局),
            "音符区中心y_布局": float(音符区中心y_布局),
            "轨道中心间距_布局": float(轨道中心间距_布局),
            "判定区_receptor宽_布局": float(判定区_receptor宽_布局),
            "左手x_布局": float(左手x_布局),
            "右手x_布局": float(右手x_布局),
            "判定线y_特效_布局": float(判定线y_特效_布局),
            "特效目标宽_布局": float(特效目标宽_布局),
            "击中特效偏移x_布局": float(击中特效偏移x_布局),
            "判定区_缩放_0": float(判定区缩放表[0]),
            "判定区_缩放_1": float(判定区缩放表[1]),
            "判定区_缩放_2": float(判定区缩放表[2]),
            "判定区_缩放_3": float(判定区缩放表[3]),
            "判定区_缩放_4": float(判定区缩放表[4]),
        }

        return 上下文

    def _绘制轨道背景(self, 屏幕: pygame.Surface, 输入: 渲染输入):
        try:
            from ui.调试_谱面渲染器_渲染控件 import 调试状态
        except Exception:
            return

        布局 = self._确保布局管理器()
        if 布局 is None:
            return

        # JSON 里没有就直接跳过
        try:
            if not 布局.是否存在控件("轨道背景组"):
                return
        except Exception:
            return

        上下文 = self._构建notes装饰上下文(屏幕, 输入)
        if not 上下文:
            return

        调试 = 调试状态(显示全部边框=False, 选中控件id="")
        try:
            布局.绘制(屏幕, 上下文, self._皮肤包, 调试=调试, 仅绘制根id="轨道背景组")
        except Exception:
            pass

    def _取判定区实际锚点(
        self, 屏幕: pygame.Surface, 输入: 渲染输入
    ) -> Optional[Dict[str, Any]]:
        布局 = self._确保布局管理器()
        if 布局 is None:
            return None

        try:
            if not 布局.是否存在控件("判定区组"):
                return None
        except Exception:
            return None

        上下文 = self._构建notes装饰上下文(屏幕, 输入)
        if not 上下文:
            return None

        try:
            构建清单 = getattr(布局, "_构建渲染清单", None)
            if not callable(构建清单):
                return None
            项列表 = 构建清单(屏幕.get_size(), 上下文, 仅绘制根id="判定区组")
        except Exception:
            return None

        if not isinstance(项列表, list):
            return None

        轨道中心列表: List[int] = []
        判定线y列表: List[int] = []
        宽度列表: List[int] = []
        状态表: Dict[str, Dict[str, Any]] = {}
        for 项 in 项列表:
            if isinstance(项, dict):
                状态表[str(项.get("id") or "")] = 项

        for 轨道 in range(5):
            项 = 状态表.get(f"判定区_{轨道}")
            if not isinstance(项, dict):
                return None
            矩形 = 项.get("rect")
            if not isinstance(矩形, pygame.Rect):
                return None
            轨道中心列表.append(int(矩形.centerx))
            判定线y列表.append(int(矩形.centery))
            宽度列表.append(int(max(8, 矩形.w)))

        判定线y = int(
            判定线y列表[2]
            if len(判定线y列表) >= 3
            else sum(判定线y列表) / float(max(1, len(判定线y列表)))
        )
        return {
            "轨道中心列表": 轨道中心列表,
            "判定线y列表": 判定线y列表,
            "判定线y": 判定线y,
            "判定区宽度列表": 宽度列表,
        }

    def _求布局清单并集矩形(
        self, 项列表: List[Dict[str, Any]]
    ) -> Optional[pygame.Rect]:
        矩形们: List[pygame.Rect] = []
        for 项 in 项列表:
            if not isinstance(项, dict):
                continue
            矩形 = 项.get("rect")
            if isinstance(矩形, pygame.Rect):
                矩形们.append(矩形.copy())
        if not 矩形们:
            return None
        out = 矩形们[0].copy()
        for rr in 矩形们[1:]:
            out.union_ip(rr)
        return out

    def 取准备动画判定区矩形(
        self, 屏幕: pygame.Surface, 输入: 渲染输入
    ) -> Optional[pygame.Rect]:
        布局 = self._确保布局管理器()
        if 布局 is None:
            return None

        try:
            if not 布局.是否存在控件("判定区组"):
                return None
        except Exception:
            return None

        上下文 = self._构建notes装饰上下文(屏幕, 输入)
        if not 上下文:
            return None

        try:
            构建清单 = getattr(布局, "_构建渲染清单", None)
            if not callable(构建清单):
                return None
            项列表 = 构建清单(屏幕.get_size(), 上下文, 仅绘制根id="判定区组")
        except Exception:
            return None
        if not isinstance(项列表, list):
            return None
        return self._求布局清单并集矩形(项列表)

    def 取准备动画判定区图层(
        self, 屏幕: pygame.Surface, 输入: 渲染输入
    ) -> Tuple[Optional[pygame.Surface], Optional[pygame.Rect]]:
        """
        给“准备就绪动画”用：
        - 返回仅包含“判定区组”的透明图层（不含背景）
        - 同时返回判定区组并集矩形，便于做缩放中心
        """
        布局 = self._确保布局管理器()
        if 布局 is None:
            return None, None

        try:
            if not 布局.是否存在控件("判定区组"):
                return None, None
        except Exception:
            return None, None

        上下文 = self._构建notes装饰上下文(屏幕, 输入)
        if not 上下文:
            return None, None

        try:
            构建清单 = getattr(布局, "_构建渲染清单", None)
            if not callable(构建清单):
                return None, None
            项列表 = 构建清单(屏幕.get_size(), 上下文, 仅绘制根id="判定区组")
            判定区矩形 = (
                self._求布局清单并集矩形(项列表) if isinstance(项列表, list) else None
            )
        except Exception:
            return None, None

        try:
            from ui.调试_谱面渲染器_渲染控件 import 调试状态
        except Exception:
            return None, 判定区矩形

        try:
            图层 = pygame.Surface(屏幕.get_size(), pygame.SRCALPHA)
            图层.fill((0, 0, 0, 0))
            调试 = 调试状态(显示全部边框=False, 选中控件id="")
            布局.绘制(图层, 上下文, self._皮肤包, 调试=调试, 仅绘制根id="判定区组")
            return 图层, 判定区矩形
        except Exception:
            return None, 判定区矩形

    def _取固定资源图(self, 路径: str) -> Optional[pygame.Surface]:
        路径 = str(路径 or "").strip()
        if not 路径:
            return None
        try:
            绝对 = os.path.abspath(路径)
        except Exception:
            绝对 = 路径

        try:
            mtime = float(os.path.getmtime(绝对)) if os.path.isfile(绝对) else -1.0
        except Exception:
            mtime = -1.0

        旧 = self._固定图缓存.get(绝对)
        if 旧 is not None:
            旧路径, 旧mtime, 旧图 = 旧
            if (旧路径 == 绝对) and (旧mtime == mtime) and (旧图 is not None):
                return 旧图

        if not os.path.isfile(绝对):
            self._固定图缓存[绝对] = (绝对, mtime, None)
            return None

        try:
            图 = pygame.image.load(绝对).convert_alpha()
            self._固定图缓存[绝对] = (绝对, mtime, 图)
            return 图
        except Exception:
            self._固定图缓存[绝对] = (绝对, mtime, None)
            return None

    def _绘制发光文本(
        self,
        屏幕: pygame.Surface,
        文本: str,
        字体: pygame.font.Font,
        位置: Tuple[int, int],
        主色: Tuple[int, int, int],
        发光色: Tuple[int, int, int],
        发光半径: int = 2,
        是否粗体: bool = True,
    ):
        x, y = int(位置[0]), int(位置[1])
        文本 = str(文本 or "")

        try:
            原粗体 = bool(字体.get_bold())
            字体.set_bold(bool(是否粗体))
        except Exception:
            原粗体 = False

        try:
            发光层 = 字体.render(文本, True, 发光色).convert_alpha()
            主层 = 字体.render(文本, True, 主色).convert_alpha()

            r = int(max(1, 发光半径))
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if dx == 0 and dy == 0:
                        continue
                    屏幕.blit(发光层, (x + dx, y + dy))

            屏幕.blit(主层, (x, y))
        except Exception:
            pass
        finally:
            try:
                字体.set_bold(bool(原粗体))
            except Exception:
                pass

    @staticmethod
    def _轨道到key方位码(轨道序号: int) -> str:
        # key：03包是 bl/tl/cc/tr/br
        return {0: "bl", 1: "tl", 2: "cc", 3: "tr", 4: "br"}.get(int(轨道序号), "cc")

    @staticmethod
    def _轨道到arrow方位码(轨道序号: int) -> str:
        # arrow：03包是 lb/lt/cc/rt/rb（注意不是 bl/tl/tr/br）
        return {0: "lb", 1: "lt", 2: "cc", 3: "rt", 4: "rb"}.get(int(轨道序号), "cc")

    def _取缩放图(
        self, 分组键: str, 原图: pygame.Surface, 目标宽: int
    ) -> pygame.Surface:
        目标宽 = int(max(2, 目标宽))
        比例 = float(目标宽) / float(max(1, 原图.get_width()))
        目标高 = int(max(2, int(原图.get_height() * 比例)))

        缓存键 = (str(分组键), int(目标宽), int(目标高))
        if 缓存键 in self._缩放缓存:
            return self._缩放缓存[缓存键]
        图2 = pygame.transform.smoothscale(原图, (目标宽, 目标高))
        if len(self._缩放缓存) >= 2048:
            self._缩放缓存.clear()
        self._缩放缓存[缓存键] = 图2
        return 图2

    def _取按高缩放图(
        self, 分组键: str, 原图: pygame.Surface, 目标高: int
    ) -> pygame.Surface:
        目标高 = int(max(2, 目标高))
        比例 = float(目标高) / float(max(1, 原图.get_height()))
        目标宽 = int(max(2, int(原图.get_width() * 比例)))
        return self._取缩放图(f"{分组键}_按高", 原图, 目标宽)

    @staticmethod
    def _上下文签名值(值: Any) -> Any:
        if isinstance(值, (str, int, float, bool)) or 值 is None:
            return 值
        if isinstance(值, (list, tuple)):
            return tuple(谱面渲染器._上下文签名值(v) for v in 值[:16])
        if isinstance(值, pygame.Rect):
            return (int(值.x), int(值.y), int(值.w), int(值.h))
        if isinstance(值, pygame.Surface):
            return (int(值.get_width()), int(值.get_height()), id(值))
        return str(type(值).__name__)

    def _绘制布局缓存层(
        self,
        缓存属性名: str,
        签名属性名: str,
        签名: Tuple[Any, ...],
        屏幕: pygame.Surface,
        布局: Any,
        上下文: Dict[str, Any],
        控件id列表: List[str],
    ):
        缓存图 = getattr(self, 缓存属性名, None)
        旧签名 = getattr(self, 签名属性名, None)
        if (
            缓存图 is None
            or 旧签名 != 签名
            or 缓存图.get_size() != 屏幕.get_size()
        ):
            缓存图 = pygame.Surface(屏幕.get_size(), pygame.SRCALPHA)
            try:
                from ui.调试_谱面渲染器_渲染控件 import 调试状态

                调试 = 调试状态(显示全部边框=False, 选中控件id="")
            except Exception:
                调试 = None
            try:
                布局.绘制(
                    缓存图,
                    上下文,
                    self._皮肤包,
                    调试=调试,
                    仅绘制控件ids=控件id列表,
                )
            except Exception:
                return
            setattr(self, 缓存属性名, 缓存图)
            setattr(self, 签名属性名, 签名)

        屏幕.blit(缓存图, (0, 0))

    def 预热性能缓存(
        self,
        屏幕尺寸: Tuple[int, int],
        箭头目标宽: int,
        判定区宽: int,
        特效宽: int,
    ):
        try:
            箭头目标宽 = int(max(16, 箭头目标宽))
            判定区宽 = int(max(16, 判定区宽))
            特效宽 = int(max(24, 特效宽))
        except Exception:
            return

        arrow图集 = getattr(self._皮肤包, "arrow", None)
        if arrow图集 is not None and hasattr(arrow图集, "取"):
            for 方位 in ("lb", "lt", "cc", "rt", "rb"):
                for 前缀 in ("arrow_body_", "arrow_mask_", "arrow_repeat_", "arrow_tail_"):
                    名 = f"{前缀}{方位}.png"
                    图 = arrow图集.取(名)
                    if 图 is not None:
                        self._取缩放图(f"arrow:{名}:{箭头目标宽}", 图, 箭头目标宽)

        key图集 = getattr(self._皮肤包, "key", None)
        if key图集 is not None and hasattr(key图集, "取"):
            for 名 in (
                "key_ll.png",
                "key_rr.png",
                "key_bl.png",
                "key_tl.png",
                "key_cc.png",
                "key_tr.png",
                "key_br.png",
            ):
                图 = key图集.取(名)
                if 图 is not None:
                    self._取缩放图(f"key:{名}:{判定区宽}", 图, 判定区宽)

        特效图集 = getattr(self._皮肤包, "key_effect", None)
        if 特效图集 is not None and hasattr(特效图集, "取"):
            for 轨道 in range(5):
                名 = f"effect_bg_{轨道}"
                图 = 特效图集.取(名)
                if 图 is not None:
                    self._取缩放图(f"effect:{名}:{特效宽}", 图, 特效宽)

    def _取布局控件矩形(
        self,
        布局: Any,
        屏幕: pygame.Surface,
        上下文: Dict[str, Any],
        根id: str,
        控件id: str,
    ) -> Optional[pygame.Rect]:
        try:
            构建清单 = getattr(布局, "_构建渲染清单", None)
            if not callable(构建清单):
                return None
            项列表 = 构建清单(屏幕.get_size(), 上下文, 仅绘制根id=str(根id))
        except Exception:
            return None

        if not isinstance(项列表, list):
            return None

        for 项 in 项列表:
            if not isinstance(项, dict):
                continue
            if str(项.get("id") or "") != str(控件id):
                continue
            矩形 = 项.get("rect")
            if isinstance(矩形, pygame.Rect):
                return 矩形.copy()
        return None

    def _绘制循环滚动条纹(
        self,
        屏幕: pygame.Surface,
        目标区域: pygame.Rect,
        图: pygame.Surface,
        时间秒: float,
        速度px每秒: float,
        向右: bool,
        缓存键: str = "血条暴走条纹",
    ):
        if 目标区域.w <= 1 or 目标区域.h <= 1:
            return

        条纹图 = self._取按高缩放图(str(缓存键), 图, int(目标区域.h))
        宽 = int(max(1, 条纹图.get_width()))

        临时层 = pygame.Surface((目标区域.w, 目标区域.h), pygame.SRCALPHA)
        偏移 = int((max(0.0, float(时间秒)) * float(速度px每秒)) % float(宽))
        起x = int(-宽 + 偏移) if 向右 else int(-偏移)
        x = 起x
        while x < 目标区域.w:
            临时层.blit(条纹图, (int(x), 0))
            x += 宽
        屏幕.blit(临时层, 目标区域.topleft)

    def _绘制满血暴走血条(
        self,
        屏幕: pygame.Surface,
        输入: 渲染输入,
        布局: Any,
        上下文: Dict[str, Any],
    ):
        if not bool(getattr(输入, "血条暴走", False)):
            return
        try:
            if float(上下文.get("血量最终显示", 0.0) or 0.0) < 0.999:
                return
        except Exception:
            return

        图集 = getattr(self._皮肤包, "blood_bar", None)
        if 图集 is None or not hasattr(图集, "取"):
            return

        try:
            基准x = int(上下文.get("血条填充区域x", 0) or 0)
            基准y = int(上下文.get("血条填充区域y", 0) or 0)
            基准w = int(上下文.get("血条填充区域w", 0) or 0)
            基准h = int(上下文.get("血条填充区域h", 0) or 0)
        except Exception:
            基准x = 基准y = 基准w = 基准h = 0

        if 基准w <= 1 or 基准h <= 1:
            暴走区域 = self._取布局控件矩形(
                布局, 屏幕, 上下文, "顶部HUD", "血条值"
            )
            if not isinstance(暴走区域, pygame.Rect):
                return
        else:
            暴走区域 = pygame.Rect(基准x, 基准y, 基准w, 基准h)

        if 暴走区域.w <= 1 or 暴走区域.h <= 1:
            return

        动画名 = (
            "full_s_r.png"
            if int(getattr(输入, "玩家序号", 1) or 1) == 2
            else "full_s_l.png"
        )
        条纹图 = 图集.取(动画名)

        if 条纹图 is not None:
            self._绘制循环滚动条纹(
                屏幕,
                暴走区域,
                条纹图,
                float(getattr(输入, "当前谱面秒", 0.0) or 0.0),
                150.0,
                向右=bool(int(getattr(输入, "玩家序号", 1) or 1) != 2),
                缓存键=f"血条暴走条纹_{动画名}",
            )

    def _取中心带不透明y边界(
        self, 缓存键: str, 图: pygame.Surface
    ) -> Tuple[int, int]:
        宽 = int(max(1, 图.get_width()))
        高 = int(max(1, 图.get_height()))
        key = (str(缓存键), 宽, 高)
        if key in self._中心带边界缓存:
            return self._中心带边界缓存[key]

        try:
            alpha = pygame.surfarray.array_alpha(图)
        except Exception:
            结果 = (0, max(0, 高 - 1))
            self._中心带边界缓存[key] = 结果
            return 结果

        起列 = int(max(0, min(宽 - 1, int(宽 * 0.48))))
        止列 = int(max(起列 + 1, min(宽, int(宽 * 0.52))))
        顶列表: List[int] = []
        底列表: List[int] = []
        for x in range(起列, 止列):
            命中行 = [y for y in range(高) if int(alpha[x, y]) > 10]
            if 命中行:
                顶列表.append(int(命中行[0]))
                底列表.append(int(命中行[-1]))

        if (not 顶列表) or (not 底列表):
            结果 = (0, max(0, 高 - 1))
        else:
            结果 = (int(sum(顶列表) / len(顶列表)), int(sum(底列表) / len(底列表)))
        self._中心带边界缓存[key] = 结果
        return 结果

    # ---------------- blood_bar ----------------

    def _确保布局管理器(self):
        布局 = getattr(self, "_布局管理器_谱面渲染器", None)
        if 布局 is not None:
            return 布局

        try:
            from ui.调试_谱面渲染器_渲染控件 import 谱面渲染器布局管理器
        except Exception:
            self._布局管理器_谱面渲染器 = None
            return None

        项目根 = ""
        try:
            项目根 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            项目根 = os.getcwd()
        布局路径 = os.path.join(项目根, "json", "谱面渲染器_布局.json")
        try:
            self._布局管理器_谱面渲染器 = 谱面渲染器布局管理器(布局路径)
        except Exception:
            self._布局管理器_谱面渲染器 = None
        return getattr(self, "_布局管理器_谱面渲染器", None)

    def _绘制血条(
        self,
        屏幕: pygame.Surface,
        输入: 渲染输入,
        字体: pygame.font.Font,
        小字体: pygame.font.Font,
    ):
        try:
            from ui.调试_谱面渲染器_渲染控件 import 调试状态
        except Exception:
            return

        布局 = self._确保布局管理器()
        if 布局 is None:
            return

        # 倒计时
        try:
            剩余秒 = float(max(0.0, float(输入.总时长秒) - float(输入.当前谱面秒)))
            分 = int(剩余秒 // 60)
            秒 = int(剩余秒 - 分 * 60)
            倒计时 = f"{分:02d}:{秒:02d}"
        except Exception:
            倒计时 = "00:00"

        # 血量最终显示（待机演示）
        try:
            相位 = float(pygame.time.get_ticks()) / 1000.0
        except Exception:
            相位 = 0.0
        if bool(getattr(输入, "血条待机演示", True)):
            血量最终显示 = 0.50 + 0.05 * math.sin(相位 * 2.0 * math.pi * 1.2)
        else:
            血量最终显示 = float(getattr(输入, "血量显示", 0.0) or 0.0)
        血量最终显示 = float(max(0.0, min(1.0, 血量最终显示)))

        当前分数 = int(getattr(输入, "显示_分数", 0) or 0)
        if self._上次显示分数 is None:
            self._上次显示分数 = int(当前分数)
        elif int(当前分数) != int(self._上次显示分数):
            self._上次显示分数 = int(当前分数)
            self.触发分数缩放动画()

        歌曲名 = str(getattr(输入, "歌曲名", "") or "").strip()
        try:
            星级 = int(getattr(输入, "星级", 0) or 0)
        except Exception:
            星级 = 0
        星级文本 = f"{max(0, 星级)}★" if 星级 > 0 else ""

        # ✅ 布局坐标系 key
        比例 = float(布局.取全局缩放(屏幕.get_size()))
        if 比例 <= 0:
            比例 = 1.0
        轨道中心列表_布局 = [float(x) / 比例 for x in (输入.轨道中心列表 or [])]
        判定线y_布局 = float(getattr(输入, "判定线y", 0)) / 比例
        箭头目标宽_布局 = float(getattr(输入, "箭头目标宽", 0)) / 比例
        轨道中心间距_布局 = 0.0
        try:
            if len(轨道中心列表_布局) >= 2:
                轨道中心间距_布局 = float(轨道中心列表_布局[1] - 轨道中心列表_布局[0])
        except Exception:
            轨道中心间距_布局 = 0.0

        游戏区参数 = self._取游戏区参数()
        调试显示游戏区控制 = bool(getattr(输入, "调试_显示游戏区控制", False))

        圆环频谱对象 = getattr(输入, "圆环频谱对象", None)
        圆环频谱启用 = bool(圆环频谱对象 is not None)

        上下文 = {
            "玩家序号": int(getattr(输入, "玩家序号", 1) or 1),
            "玩家昵称": str(getattr(输入, "玩家昵称", "") or ""),
            "当前关卡": int(getattr(输入, "当前关卡", 1) or 1),
            "头像图": self._取头像图_按血量状态(输入),
            "段位图": getattr(输入, "段位图", None),
            "显示_分数": int(当前分数),
            "分数_缩放": float(self._取分数缩放()),
            "倒计时": 倒计时,
            "血量最终显示": 血量最终显示,
            "总血量HP": int(getattr(输入, "总血量HP", 0) or 0),
            "可见血量HP": int(getattr(输入, "可见血量HP", 0) or 0),
            "血条暴走": bool(getattr(输入, "血条暴走", False)),
            "歌曲名": 歌曲名,
            "歌曲星级文本": 星级文本,
            # 计数默认关闭（计数单独在 _绘制计数动画组 里画）
            "计数_启用": False,
            "计数_缩放": 1.0,
            "计数_透明": 1.0,
            "计数_combo": 0,
            "计数_判定帧": "",
            # ✅ 给 JSON 动态定位用
            "轨道中心列表_布局": 轨道中心列表_布局,
            "判定线y_布局": 判定线y_布局,
            "箭头目标宽_布局": 箭头目标宽_布局,
            "轨道中心间距_布局": 轨道中心间距_布局,
            # ✅ 调试控制
            "_调试显示游戏区控制": bool(调试显示游戏区控制),
            "游戏区_y偏移": float(游戏区参数.get("y偏移", -12.0)),
            "游戏区_缩放": float(游戏区参数.get("缩放", 1.0)),
            "游戏区_hold宽度系数": float(游戏区参数.get("hold宽度系数", 0.96)),
            "游戏区_判定区宽度系数": float(游戏区参数.get("判定区宽度系数", 1.08)),
            "游戏区_击中特效宽度系数": float(游戏区参数.get("击中特效宽度系数", 2.6)),
            "游戏区_击中特效偏移x": float(游戏区参数.get("击中特效偏移x", 0.0)),
            "游戏区_击中特效偏移y": float(游戏区参数.get("击中特效偏移y", 0.0)),
            # ✅ 给“圆环频谱”控件用（布局里画，不在场景里画）
            "当前谱面秒": float(getattr(输入, "当前谱面秒", 0.0) or 0.0),
            "调试_时间秒": float(getattr(输入, "当前谱面秒", 0.0) or 0.0),
            "圆环频谱对象": 圆环频谱对象,
            "圆环频谱_启用": bool(圆环频谱启用),
        }

        try:
            调试血条颜色 = getattr(输入, "调试_血条颜色", None)
            if isinstance(调试血条颜色, (list, tuple)) and len(调试血条颜色) >= 3:
                上下文["调试_血条颜色"] = list(调试血条颜色)
        except Exception:
            pass
        try:
            上下文["调试_血条亮度"] = float(
                getattr(输入, "调试_血条亮度", 1.0) or 1.0
            )
        except Exception:
            pass
        try:
            上下文["调试_血条不透明度"] = float(
                getattr(输入, "调试_血条不透明度", 1.0) or 1.0
            )
        except Exception:
            pass
        try:
            上下文["调试_血条晃荡速度"] = float(
                getattr(输入, "调试_血条晃荡速度", 0.0) or 0.0
            )
        except Exception:
            pass
        try:
            上下文["调试_血条晃荡幅度"] = float(
                getattr(输入, "调试_血条晃荡幅度", 0.0) or 0.0
            )
        except Exception:
            pass
        try:
            上下文["调试_暴走血条速度"] = float(
                getattr(输入, "调试_暴走血条速度", 0.0) or 0.0
            )
        except Exception:
            pass
        try:
            上下文["调试_暴走血条不透明度"] = float(
                getattr(输入, "调试_暴走血条不透明度", 1.0) or 1.0
            )
        except Exception:
            pass
        try:
            上下文["调试_暴走血条羽化"] = float(
                getattr(输入, "调试_暴走血条羽化", 8.0) or 8.0
            )
        except Exception:
            pass
        try:
            上下文["调试_头像框特效速度"] = float(
                getattr(输入, "调试_头像框特效速度", 30.0) or 30.0
            )
        except Exception:
            pass
        try:
            上下文["调试_圆环频谱_启用旋转"] = bool(
                getattr(输入, "调试_圆环频谱_启用旋转", True)
            )
        except Exception:
            pass
        try:
            上下文["调试_圆环频谱_背景板旋转速度"] = float(
                getattr(输入, "调试_圆环频谱_背景板旋转速度", 20.0) or 20.0
            )
        except Exception:
            pass
        try:
            上下文["调试_圆环频谱_变化落差"] = float(
                getattr(输入, "调试_圆环频谱_变化落差", 1.0) or 1.0
            )
        except Exception:
            pass
        try:
            上下文["调试_圆环频谱_线条数量"] = int(
                getattr(输入, "调试_圆环频谱_线条数量", 200) or 200
            )
        except Exception:
            pass
        try:
            上下文["调试_圆环频谱_线条粗细"] = int(
                getattr(输入, "调试_圆环频谱_线条粗细", 2) or 2
            )
        except Exception:
            pass
        try:
            上下文["调试_圆环频谱_线条间隔"] = int(
                getattr(输入, "调试_圆环频谱_线条间隔", 1) or 1
            )
        except Exception:
            pass
        try:
            上下文["性能模式"] = bool(getattr(输入, "性能模式", False))
        except Exception:
            pass

        try:
            血条值矩形 = self._取布局控件矩形(布局, 屏幕, 上下文, "顶部HUD", "血条值")
            血条值定义 = getattr(布局, "_控件索引", {}).get("血条值", {})
            内边距 = (
                血条值定义.get("内边距", {})
                if isinstance(血条值定义, dict)
                else {}
            )
            if isinstance(血条值矩形, pygame.Rect):
                try:
                    边距缩放 = float(max(0.01, 比例))
                except Exception:
                    边距缩放 = 1.0
                l = int(round(_取数((内边距 or {}).get("l"), 0) * 边距缩放))
                t = int(round(_取数((内边距 or {}).get("t"), 0) * 边距缩放))
                r = int(round(_取数((内边距 or {}).get("r"), 0) * 边距缩放))
                b = int(round(_取数((内边距 or {}).get("b"), 0) * 边距缩放))
                内矩形 = pygame.Rect(
                    int(血条值矩形.x + l),
                    int(血条值矩形.y + t),
                    int(max(2, 血条值矩形.w - l - r)),
                    int(max(2, 血条值矩形.h - t - b)),
                )
                上下文["血条填充区域x"] = int(内矩形.x)
                上下文["血条填充区域y"] = int(内矩形.y)
                上下文["血条填充区域w"] = int(内矩形.w)
                上下文["血条填充区域h"] = int(内矩形.h)
        except Exception:
            pass

        调试 = 调试状态(显示全部边框=False, 选中控件id="")
        try:
            布局.绘制(屏幕, 上下文, self._皮肤包, 调试=调试, 仅绘制根id="顶部HUD")
        except Exception:
            return

        if 调试显示游戏区控制:
            try:
                布局.绘制(
                    屏幕, 上下文, self._皮肤包, 调试=调试, 仅绘制根id="调试控制组"
                )
            except Exception:
                pass

    def _绘制计数动画组(self, 屏幕: pygame.Surface, 输入: 渲染输入):
        调试常显 = bool(getattr(输入, "调试_计数常显", False))

        主计数活跃 = bool(调试常显) or (self._计数动画剩余秒 > 0.0) or (
            float(getattr(self, "_计数动画停留剩余秒", 0.0) or 0.0) > 0.0
        )
        if not 主计数活跃:
            return

        try:
            from ui.调试_谱面渲染器_渲染控件 import 调试状态
        except Exception:
            return

        布局 = self._确保布局管理器()
        if 布局 is None:
            return
        try:
            计数组定义 = getattr(布局, "_控件索引", {}).get("计数动画组", None)
            if isinstance(计数组定义, dict):
                x定义 = 计数组定义.get("x", None)
                if (not isinstance(x定义, dict)) or (str(x定义.get("键") or "") != "计数组中心x_布局"):
                    计数组定义["x"] = {"键": "计数组中心x_布局"}
        except Exception:
            pass

        # =========================
        # ✅ 关键参数（你就盯这几个调）
        # =========================
        def _平滑分段插值(
            p: float, 关键帧: List[Tuple[float, float]]
        ) -> float:
            p = float(max(0.0, min(1.0, p)))
            if not 关键帧:
                return 1.0
            if p <= float(关键帧[0][0]):
                return float(关键帧[0][1])

            for i in range(1, len(关键帧)):
                前t, 前v = 关键帧[i - 1]
                后t, 后v = 关键帧[i]
                if p <= float(后t):
                    段长 = float(max(1e-6, float(后t) - float(前t)))
                    tp = float(p - float(前t)) / 段长
                    # 用 smoothstep 让关键帧之间的缩放过渡更圆滑，避免折线感太重。
                    tp = tp * tp * (3.0 - 2.0 * tp)
                    return float(前v) + (float(后v) - float(前v)) * tp

            return float(关键帧[-1][1])

        # 原版观察近似：
        # 0f: 150% 最虚
        # 1f: 130%
        # 2f: 85% 且仍偏虚
        # 3f: 95% 最亮最实
        # 4f: 保持
        # 5f: 100%
        # 6f: 消失
        缩放关键帧 = [
            (0.00, 1.50),
            (0.17, 1.30),
            (0.34, 0.85),
            (0.50, 0.95),
            (0.67, 0.95),
            (0.84, 1.00),
            (1.00, 1.00),
        ]
        透明关键帧 = [
            (0.00, 0.34),
            (0.17, 0.54),
            (0.34, 0.80),
            (0.50, 1.00),
            (0.84, 1.00),
            (1.00, 1.00),
        ]

        # =========================
        # 计算（主计数 / 轻闪）
        # =========================
        if 调试常显:
            判定 = str(getattr(输入, "调试_计数判定", "perfect") or "perfect").lower()
            combo值 = int(getattr(输入, "调试_计数combo", 23) or 23)
            缩放 = 1.0
            透明 = 1.0
        else:
            if 主计数活跃:
                判定 = str(self._计数动画判定 or "").lower() or "perfect"
                combo值 = int(max(0, int(self._计数动画combo)))

                if float(self._计数动画剩余秒) > 0.0:
                    总 = float(
                        self._计数动画总秒
                        if getattr(self, "_计数动画总秒", 0.0) > 0
                        else 0.20
                    )
                    剩余 = float(self._计数动画剩余秒)
                    经过 = float(max(0.0, 总 - 剩余))
                    进度 = float(max(0.0, min(1.0, 经过 / max(0.001, 总))))

                    缩放 = float(_平滑分段插值(进度, 缩放关键帧))
                    透明 = float(_平滑分段插值(进度, 透明关键帧))
                    缩放 = float(max(0.80, min(1.60, 缩放)))
                    透明 = float(max(0.0, min(1.0, 透明)))
                else:
                    缩放 = 1.0
                    透明 = 1.0

            else:
                return

        判定帧 = {
            "perfect": "text_pf1_perfect.png",
            "cool": "text_pf1_cool.png",
            "good": "text_pf1_good.png",
            "miss": "text_pf1_miss.png",
        }.get(判定, "")

        try:
            比例 = float(布局.取全局缩放(屏幕.get_size()))
        except Exception:
            比例 = 1.0
        if 比例 <= 0:
            比例 = 1.0
        try:
            轨道中心列表 = [int(v) for v in list(getattr(输入, "轨道中心列表", []) or [])[:5]]
        except Exception:
            轨道中心列表 = []
        if len(轨道中心列表) >= 3:
            计数组中心x_布局 = float(轨道中心列表[2]) / float(比例)
        else:
            计数组中心x_布局 = float(屏幕.get_width()) * 0.5 / float(比例)
        try:
            大小倍率 = float(getattr(输入, "大小倍率", 1.0) or 1.0)
        except Exception:
            大小倍率 = 1.0
        大小倍率 = float(max(0.5, min(2.0, 大小倍率)))

        上下文 = {
            "计数_启用": True,
            "计数_缩放": float(缩放 * 大小倍率),
            "计数_透明": float(透明),
            "计数_combo": int(max(0, combo值)),
            "计数_判定帧": str(判定帧),
            "计数组中心x_布局": float(计数组中心x_布局),
        }

        调试 = 调试状态(显示全部边框=False, 选中控件id="")
        try:
            布局.绘制(屏幕, 上下文, self._皮肤包, 调试=调试, 仅绘制根id="计数动画组")
        except Exception:
            return

    # # ---------------- key ----------------
    # def _绘制判定区(self, 屏幕: pygame.Surface, 输入: 渲染输入):
    #     图集 = self._皮肤包.key
    #     if 图集 is None:
    #         return
    #     if len(输入.轨道中心列表) < 5:
    #         return

    #     参数 = self._取游戏区参数()
    #     游戏缩放 = float(参数.get("缩放", 1.0))
    #     y偏移 = float(参数.get("y偏移", 1.0))
    #     判定区宽度系数 = float(参数.get("判定区宽度系数", 1.08))

    #     y判定 = int(float(输入.判定线y) + y偏移)
    #     receptor宽 = int(
    #         max(24, int(float(输入.箭头目标宽) * 判定区宽度系数 * 游戏缩放))
    #     )

    #     间距 = (
    #         int(输入.轨道中心列表[1] - 输入.轨道中心列表[0])
    #         if len(输入.轨道中心列表) >= 2
    #         else int(receptor宽 * 0.9)
    #     )
    #     左手x = int(输入.轨道中心列表[0] - 间距)
    #     右手x = int(输入.轨道中心列表[4] + 间距)

    #     左手图 = 图集.取("key_ll.png")
    #     右手图 = 图集.取("key_rr.png")
    #     if 左手图 is not None:
    #         图2 = self._取缩放图("key:ll", 左手图, receptor宽)
    #         屏幕.blit(
    #             图2, (左手x - 图2.get_width() // 2, y判定 - 图2.get_height() // 2)
    #         )
    #     if 右手图 is not None:
    #         图2 = self._取缩放图("key:rr", 右手图, receptor宽)
    #         屏幕.blit(
    #             图2, (右手x - 图2.get_width() // 2, y判定 - 图2.get_height() // 2)
    #         )

    #     # =========================
    #     # ✅ 按键反馈：带动画的缩到 50%，长按保持 50%
    #     #   - 使用 dt 平滑逼近 target，实现按下/松开都有过渡
    #     # =========================
    #     最小缩放 = 0.50

    #     # 懒初始化：不改 __init__ 也能跑
    #     if (not hasattr(self, "_按键反馈缩放")) or (
    #         not isinstance(getattr(self, "_按键反馈缩放"), list)
    #     ):
    #         self._按键反馈缩放 = [1.0] * 5
    #     if len(self._按键反馈缩放) != 5:
    #         self._按键反馈缩放 = [1.0] * 5

    #     if not hasattr(self, "_按键反馈上次秒"):
    #         try:
    #             self._按键反馈上次秒 = float(pygame.time.get_ticks()) / 1000.0
    #         except Exception:
    #             self._按键反馈上次秒 = 0.0

    #     try:
    #         当前秒 = float(pygame.time.get_ticks()) / 1000.0
    #     except Exception:
    #         当前秒 = float(getattr(self, "_按键反馈上次秒", 0.0) or 0.0)

    #     dt = float(当前秒 - float(getattr(self, "_按键反馈上次秒", 0.0) or 0.0))
    #     if dt < 0.0:
    #         dt = 0.0
    #     if dt > 0.05:
    #         dt = 0.05
    #     self._按键反馈上次秒 = float(当前秒)

    #     # 实时按键状态
    #     try:
    #         按下数组 = pygame.key.get_pressed()
    #     except Exception:
    #         按下数组 = None

    #     轨道到按键列表 = {
    #         0: [pygame.K_1, pygame.K_KP1],
    #         1: [pygame.K_7, pygame.K_KP7],
    #         2: [pygame.K_5, pygame.K_KP5],
    #         3: [pygame.K_9, pygame.K_KP9],
    #         4: [pygame.K_3, pygame.K_KP3],
    #     }

    #     def _轨道是否按下(轨道: int) -> bool:
    #         if 按下数组 is None:
    #             return False
    #         for k in 轨道到按键列表.get(int(轨道), []):
    #             try:
    #                 if 按下数组[k]:
    #                     return True
    #             except Exception:
    #                 continue
    #         return False

    #     # 动画速度：按下更快、松开稍慢（更像回弹）
    #     按下速度 = 26.0
    #     松开速度 = 18.0

    #     for i in range(5):
    #         方位 = self._轨道到key方位码(i)
    #         名 = f"key_{方位}.png"
    #         图 = 图集.取(名)
    #         if 图 is None:
    #             continue

    #         # ---------- 目标缩放 ----------
    #         目标缩放 = 1.0

    #         # tap 动画（原本 0.06，现在改成缩到 50%）
    #         剩余 = float(self._按下反馈剩余秒[i])
    #         if 剩余 > 0.0:
    #             p = 1.0 - (剩余 / float(self._按下反馈总时长秒))
    #             p = float(max(0.0, min(1.0, p)))
    #             # sin(pi*p)：0->1->0，对应：1->0.5->1
    #             tap缩放 = 1.0 - 0.50 * math.sin(p * math.pi)
    #             tap缩放 = float(max(最小缩放, min(1.0, tap缩放)))
    #             目标缩放 = tap缩放

    #         # 长按：目标直接锁定 0.5（但靠平滑逼近，所以不会硬跳）
    #         if _轨道是否按下(i):
    #             目标缩放 = 最小缩放

    #         # ---------- 平滑逼近（有动画） ----------
    #         当前缩放 = float(self._按键反馈缩放[i])

    #         if 目标缩放 < 当前缩放:
    #             速度 = 按下速度
    #         else:
    #             速度 = 松开速度

    #         系数 = float(min(1.0, dt * 速度))
    #         新缩放 = 当前缩放 + (目标缩放 - 当前缩放) * 系数
    #         新缩放 = float(max(最小缩放, min(1.0, 新缩放)))
    #         self._按键反馈缩放[i] = 新缩放

    #         目标宽 = int(max(8, int(receptor宽 * 新缩放)))
    #         图2 = self._取缩放图(f"key:{名}:{目标宽}", 图, 目标宽)
    #         x = int(输入.轨道中心列表[i] - 图2.get_width() // 2)
    #         y = int(y判定 - 图2.get_height() // 2)
    #         屏幕.blit(图2, (x, y))

    def _绘制判定区(self, 屏幕: pygame.Surface, 输入: 渲染输入):
        图集 = self._皮肤包.key
        if 图集 is None or len(输入.轨道中心列表) < 5:
            return

        try:
            from ui.调试_谱面渲染器_渲染控件 import 调试状态
        except Exception:
            调试状态 = None

        # ========== 1) 判定区缩放状态在 更新() 中逐帧更新，这里只负责绘制 ==========
        if (not hasattr(self, "_按键反馈缩放")) or (
            not isinstance(getattr(self, "_按键反馈缩放"), list)
        ):
            self._按键反馈缩放 = [1.0] * 5
        if len(self._按键反馈缩放) != 5:
            self._按键反馈缩放 = [1.0] * 5

        # ========== 2) 走 JSON 绘制判定区组 ==========
        布局 = self._确保布局管理器()
        if 布局 is not None:
            try:
                if 布局.是否存在控件("判定区组"):
                    上下文 = self._构建notes装饰上下文(屏幕, 输入)
                    if 上下文:
                        调试 = (
                            调试状态(显示全部边框=False, 选中控件id="")
                            if 调试状态
                            else None
                        )
                        布局.绘制(
                            屏幕, 上下文, self._皮肤包, 调试=调试, 仅绘制根id="判定区组"
                        )
                        return
            except Exception:
                pass

        # ========== 3) 兜底：JSON 不存在时，回到旧绘制 ==========
        参数 = self._取游戏区参数()
        游戏缩放 = float(参数.get("缩放", 1.0))
        y偏移 = float(参数.get("y偏移", -12.0))
        判定区宽度系数 = float(参数.get("判定区宽度系数", 1.08))

        y判定 = int(float(输入.判定线y) + y偏移)
        receptor宽 = int(
            max(24, int(float(输入.箭头目标宽) * 判定区宽度系数 * 游戏缩放))
        )

        间距 = int(输入.轨道中心列表[1] - 输入.轨道中心列表[0])
        左手x = int(输入.轨道中心列表[0] - 间距)
        右手x = int(输入.轨道中心列表[4] + 间距)

        左手图 = 图集.取("key_ll.png")
        右手图 = 图集.取("key_rr.png")
        if 左手图 is not None:
            图2 = self._取缩放图("key:ll", 左手图, receptor宽)
            屏幕.blit(
                图2, (左手x - 图2.get_width() // 2, y判定 - 图2.get_height() // 2)
            )
        if 右手图 is not None:
            图2 = self._取缩放图("key:rr", 右手图, receptor宽)
            屏幕.blit(
                图2, (右手x - 图2.get_width() // 2, y判定 - 图2.get_height() // 2)
            )

        for i in range(5):
            方位 = self._轨道到key方位码(i)
            名 = f"key_{方位}.png"
            图 = 图集.取(名)
            if 图 is None:
                continue
            缩放值 = float(self._按键反馈缩放[i])
            目标宽 = int(max(8, int(receptor宽 * 缩放值)))
            图2 = self._取缩放图(f"key:{名}:{目标宽}", 图, 目标宽)
            x = int(输入.轨道中心列表[i] - 图2.get_width() // 2)
            y = int(y判定 - 图2.get_height() // 2)
            屏幕.blit(图2, (x, y))

    def _绘制音符(self, 屏幕: pygame.Surface, 输入: 渲染输入):
        图集 = self._皮肤包.arrow
        if 图集 is None:
            for i in range(5):
                self._hold当前按下中[i] = False
                self._hold松手系统秒[i] = None
            return

        参数 = self._取游戏区参数()
        游戏缩放 = float(参数.get("缩放", 1.0))
        y偏移 = float(参数.get("y偏移", 0.0))
        hold宽度系数 = float(参数.get("hold宽度系数", 0.96))
        布局锚点 = self._取判定区实际锚点(屏幕, 输入)

        当前秒 = float(输入.当前谱面秒)
        轨迹模式 = str(getattr(输入, "轨迹模式", "正常") or "正常")
        隐藏模式 = str(getattr(输入, "隐藏模式", "关闭") or "关闭")
        全隐模式 = bool("全隐" in 隐藏模式)
        半隐模式 = (not 全隐模式) and bool("半隐" in 隐藏模式)
        半隐y阈值 = int(屏幕.get_height() * 0.5)
        try:
            当前毫秒 = int(round(当前秒 * 1000.0))
        except Exception:
            当前毫秒 = 0

        轨道中心列表 = list(getattr(输入, "轨道中心列表", []) or [])
        判定线y列表: List[int] = []
        if isinstance(布局锚点, dict):
            try:
                轨道中心列表 = list(布局锚点.get("轨道中心列表", 轨道中心列表) or 轨道中心列表)
            except Exception:
                pass
            try:
                判定线y列表 = [int(v) for v in list(布局锚点.get("判定线y列表", []) or [])[:5]]
            except Exception:
                判定线y列表 = []
            try:
                y判定 = int(布局锚点.get("判定线y", 0) or 0)
            except Exception:
                y判定 = int(float(输入.判定线y) + y偏移)
        else:
            y判定 = int(float(输入.判定线y) + y偏移)
        y底 = int(float(输入.底部y) + y偏移)

        有效速度 = float(输入.滚动速度px每秒) * 游戏缩放
        箭头宽_tap = int(max(18, int(float(输入.箭头目标宽) * 游戏缩放)))
        箭头宽_hold = int(max(16, int(float(箭头宽_tap) * hold宽度系数)))

        while len(轨道中心列表) < 5:
            轨道中心列表.append(0)
        while len(判定线y列表) < 5:
            判定线y列表.append(int(y判定))

        # ✅ 上边界在屏幕外：允许未击中跑出屏幕
        上边界 = -int(max(40, 箭头宽_tap * 2))
        下边界 = int(y底 + max(40, 箭头宽_tap * 2))

        可视秒 = float(max(1, (y底 - y判定))) / float(max(60.0, float(有效速度)))
        提前秒 = 可视秒 + 1.0

        try:
            按下数组 = pygame.key.get_pressed()
        except Exception:
            按下数组 = None

        轨道到按键列表 = (
            dict(getattr(self, "_按键反馈轨道到按键列表", {}) or {})
            if isinstance(getattr(self, "_按键反馈轨道到按键列表", None), dict)
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
            for k in 轨道到按键列表.get(int(轨道), []):
                try:
                    if 按下数组[k]:
                        return True
                except Exception:
                    continue
            return False

        # ✅ 新：队列+已命中表
        self._确保命中映射缓存()
        命中窗毫秒 = int(round(float(self._命中匹配窗秒) * 1000.0))
        if 命中窗毫秒 < 40:
            命中窗毫秒 = 40
        if 命中窗毫秒 > 260:
            命中窗毫秒 = 260

        # ✅ 清理已命中tap过期表 + 清理过老的命中队列
        for 轨 in range(5):
            表 = self._已命中tap过期表毫秒[轨]
            if isinstance(表, dict) and 表:
                for k in list(表.keys()):
                    try:
                        if 当前毫秒 > int(表.get(k, -1)):
                            del 表[k]
                    except Exception:
                        try:
                            del 表[k]
                        except Exception:
                            pass

            队列 = self._待命中队列毫秒[轨]
            if isinstance(队列, list) and 队列:
                # 超过 2 秒的输入基本不可能再匹配任何 note，直接丢掉
                丢弃阈值 = int(当前毫秒 - 2000)
                while 队列 and int(队列[0]) < 丢弃阈值:
                    队列.pop(0)

        活跃hold轨道: set[int] = set()
        for i in range(5):
            self._hold当前按下中[i] = False

        for 事件 in 输入.事件列表 or []:
            try:
                st = float(getattr(事件, "开始秒"))
                ed = float(getattr(事件, "结束秒"))
                轨道 = int(getattr(事件, "轨道序号"))
                类型 = str(getattr(事件, "类型"))
            except Exception:
                continue

            if st < 当前秒 - 2.5 and ed < 当前秒 - 2.5:
                continue
            if st > 当前秒 + 提前秒:
                break
            if not (0 <= 轨道 < 5):
                continue

            x中心 = int(轨道中心列表[轨道])
            当前轨判定y = int(判定线y列表[轨道])

            dy开始 = (st - 当前秒) * float(有效速度)
            y开始 = float(当前轨判定y) + float(dy开始)

            st毫秒 = int(round(st * 1000.0))

            # ---------- tap ----------
            if abs(ed - st) < 1e-6 or 类型 == "tap":
                if y开始 < float(上边界) or y开始 > float(下边界):
                    continue

                # ✅ 命中判定：先看“已命中表”，不靠单槽位覆盖
                已命中表 = self._已命中tap过期表毫秒[轨道]
                命中匹配 = False
                try:
                    过期 = int(已命中表.get(st毫秒, -1))
                    if 过期 > 0 and 当前毫秒 <= 过期:
                        命中匹配 = True
                except Exception:
                    命中匹配 = False

                # ✅ 没命中则尝试从“命中队列”消费一次
                if not 命中匹配:
                    队列 = self._待命中队列毫秒[轨道]

                    # 丢掉早于本 note 窗口左边界的输入（不可能匹配本 note 或后续 note）
                    左界 = int(st毫秒 - 命中窗毫秒)
                    while 队列 and int(队列[0]) < 左界:
                        队列.pop(0)

                    if 队列:
                        hit_ms = int(队列[0])
                        if abs(hit_ms - st毫秒) <= 命中窗毫秒:
                            # ✅ 消费这次命中
                            队列.pop(0)
                            命中匹配 = True

                            # ✅ 记录这个 note 已命中：保证它穿过判定线后立刻消失
                            # 过期给足 600ms~1000ms，防止穿越判定线前表就过期
                            过期候选1 = int(st毫秒 + 1000)
                            过期候选2 = int(当前毫秒 + 650)
                            已命中表[int(st毫秒)] = int(max(过期候选1, 过期候选2))

                # ✅ 命中的 tap：穿过当前轨判定线就隐藏
                if 命中匹配 and (y开始 < float(当前轨判定y)):
                    continue

                if 全隐模式:
                    continue
                if 半隐模式 and (y开始 > float(半隐y阈值)):
                    continue

                x绘制 = float(x中心)
                旋转角度 = 0.0
                if "摇摆" in 轨迹模式:
                    # 节奏摆动：基于时间连续变化，避免“抖动感”；位移允许超出轨道宽度。
                    主振幅 = max(16.0, float(箭头宽_tap) * 0.52)
                    主相位 = (
                        float(当前秒) * (math.pi * 2.0) * 2.05
                        + float(st) * 0.55
                        + float(轨道) * 0.72
                    )
                    次相位 = float(主相位) * 0.52 + float(轨道) * 0.35
                    x绘制 = float(x中心) + math.sin(主相位) * 主振幅 + math.sin(次相位) * (
                        主振幅 * 0.22
                    )
                elif "旋转" in 轨迹模式:
                    旋转角度 = float(
                        (当前秒 * 360.0 * 1.25 + float(st) * 140.0 + float(轨道) * 35.0)
                        % 360.0
                    )

                self._画tap(
                    屏幕,
                    图集,
                    轨道,
                    int(round(x绘制)),
                    y开始,
                    int(箭头宽_tap),
                    旋转角度=旋转角度,
                )
                continue

            # ---------- hold ----------
            dy结束 = (ed - 当前秒) * float(有效速度)
            y结束 = float(当前轨判定y) + float(dy结束)

            seg_top = float(min(y开始, y结束))
            seg_bot = float(max(y开始, y结束))
            if seg_bot < float(上边界) or seg_top > float(下边界):
                continue

            是否命中hold = False
            命中开始 = float(self._命中hold开始谱面秒[轨道])
            命中结束 = float(self._命中hold结束谱面秒[轨道])

            if 命中结束 > -1.0 and (当前秒 <= 命中结束 + 1.2):
                if abs(st - 命中开始) <= max(0.08, float(self._命中匹配窗秒) * 2.0):
                    是否命中hold = True

            # ✅ hold 也用队列消费（解决 tap/hold 交错时被覆盖的问题）
            if not 是否命中hold:
                队列 = self._待命中队列毫秒[轨道]
                左界 = int(st毫秒 - 命中窗毫秒)
                while 队列 and int(队列[0]) < 左界:
                    队列.pop(0)

                if 队列:
                    hit_ms = int(队列[0])
                    if abs(hit_ms - st毫秒) <= 命中窗毫秒:
                        # 只要结束秒明显晚于开始秒，就按 hold 消费。
                        # 短 hold 也必须能命中，不能再被 0.15s 门槛吞掉。
                        if float(ed - st) > 1e-6:
                            队列.pop(0)
                            self._命中hold开始谱面秒[轨道] = float(st)
                            self._命中hold结束谱面秒[轨道] = float(ed)
                            self._击中特效开始谱面秒[轨道] = float(st)
                            self._击中特效循环到谱面秒[轨道] = float(ed)
                            是否命中hold = True

            是否绘制头 = True
            if 是否命中hold and (float(st) <= 当前秒 <= float(ed)):
                活跃hold轨道.add(int(轨道))
                是否按下 = _轨道是否按下(int(轨道))
                self._hold当前按下中[int(轨道)] = bool(是否按下)
                self._hold松手系统秒[int(轨道)] = None

            if 全隐模式:
                continue

            绘制下边界 = int(下边界)
            if 半隐模式:
                绘制下边界 = int(min(int(绘制下边界), int(半隐y阈值)))
                if min(float(y开始), float(y结束)) > float(半隐y阈值):
                    continue

            self._画hold(
                屏幕,
                图集,
                轨道,
                x中心,
                y开始,
                y结束,
                int(箭头宽_hold),
                判定线y=int(当前轨判定y),
                是否命中hold=bool(是否命中hold),
                上边界=int(上边界),
                下边界=int(绘制下边界),
                是否绘制头=bool(是否绘制头),
            )

        for i in range(5):
            if i not in 活跃hold轨道:
                self._hold松手系统秒[i] = None
                self._hold当前按下中[i] = False

        for i in range(5):
            if (
                float(self._命中hold结束谱面秒[i]) > -1.0
                and 当前秒 > float(self._命中hold结束谱面秒[i]) + 2.0
            ):
                self._命中hold开始谱面秒[i] = -999.0
                self._命中hold结束谱面秒[i] = -999.0
                if float(self._击中特效循环到谱面秒[i]) > -1.0:
                    self._击中特效循环到谱面秒[i] = -999.0

    def _画tap(
        self,
        屏幕: pygame.Surface,
        图集: _贴图集,
        轨道: int,
        x中心: int,
        y: float,
        箭头宽: int,
        旋转角度: float = 0.0,
    ):
        方位 = self._轨道到arrow方位码(轨道)
        名 = f"arrow_body_{方位}.png"
        图 = 图集.取(名)
        if 图 is None:
            return
        图2 = self._取缩放图(f"arrow:{名}:{箭头宽}", 图, 箭头宽)
        if abs(float(旋转角度)) > 0.01:
            try:
                图3 = pygame.transform.rotate(图2, -float(旋转角度)).convert_alpha()
                屏幕.blit(
                    图3,
                    (
                        int(x中心 - 图3.get_width() // 2),
                        int(y - 图3.get_height() // 2),
                    ),
                )
                return
            except Exception:
                pass
        屏幕.blit(
            图2, (int(x中心 - 图2.get_width() // 2), int(y - 图2.get_height() // 2))
        )

    def _画hold(
        self,
        屏幕: pygame.Surface,
        图集: _贴图集,
        轨道: int,
        x中心: int,
        y开始: float,
        y结束: float,
        箭头宽: int,
        判定线y: int,
        是否命中hold: bool,
        上边界: int,
        下边界: int,
        是否绘制头: bool,
    ):
        方位 = self._轨道到arrow方位码(轨道)

        头名 = f"arrow_body_{方位}.png"
        罩名 = f"arrow_mask_{方位}.png"
        身名 = f"arrow_repeat_{方位}.png"
        尾名 = f"arrow_tail_{方位}.png"

        头图 = 图集.取(头名)
        罩图 = 图集.取(罩名)
        身图 = 图集.取(身名)
        尾图 = 图集.取(尾名)

        头2 = (
            self._取缩放图(f"arrow:{头名}:{箭头宽}", 头图, 箭头宽)
            if 头图 is not None
            else None
        )
        罩2 = (
            self._取缩放图(f"arrow:{罩名}:{箭头宽}", 罩图, 箭头宽)
            if 罩图 is not None
            else None
        )
        身2 = (
            self._取缩放图(f"arrow:{身名}:{箭头宽}", 身图, 箭头宽)
            if 身图 is not None
            else None
        )
        尾2 = (
            self._取缩放图(f"arrow:{尾名}:{箭头宽}", 尾图, 箭头宽)
            if 尾图 is not None
            else None
        )

        # ==========
        # ✅ 命中 hold 的头必须和判定区中心重叠，否则会出现“头还没盖到判定区就消失”的错位感
        # ==========
        目标判定y = float(int(判定线y))

        # ==========
        # ✅ 命中 hold：头钉在“目标判定y”，尾巴穿过“目标判定y”就结束
        # ==========
        原y头 = float(y开始)
        原y尾 = float(y结束)
        mask下边缘y: Optional[float] = None
        tail可见顶边y: Optional[float] = None

        if bool(是否命中hold):
            # 头如果已经到判定线上方（更小的y），就钉住到目标y
            if 原y头 < 目标判定y:
                y开始 = float(目标判定y)
            if 罩2 is not None:
                _罩顶, 罩底 = self._取中心带不透明y边界(f"geom:{罩名}", 罩2)
                mask下边缘y = float(y开始 - 罩2.get_height() * 0.5 + 罩底)
            if 尾2 is not None:
                尾顶, _尾底 = self._取中心带不透明y边界(f"geom:{尾名}", 尾2)
                tail可见顶边y = float(y结束 - 尾2.get_height() * 0.5 + 尾顶)

            # 把消失阈值从“tail 走完”提前到“tail 开始进入 mask 下边缘”。
            if (
                mask下边缘y is not None
                and tail可见顶边y is not None
                and float(tail可见顶边y) <= float(mask下边缘y)
            ):
                return
            if mask下边缘y is None and 原y尾 < float(目标判定y):
                return

        y1 = float(min(y开始, y结束))
        y2 = float(max(y开始, y结束))

        # ==========
        # ✅ 屏幕裁剪（加缓冲减少边缘闪）
        # ==========
        缓冲 = 6
        绘制y1 = float(max(float(上边界 - 缓冲), y1))
        绘制y2 = float(min(float(下边界 + 缓冲), y2))
        if bool(是否命中hold) and (mask下边缘y is not None):
            绘制y1 = float(max(float(绘制y1), float(mask下边缘y)))

        if 绘制y2 <= 绘制y1:
            # 只有单点可画：先画尾，再画头
            if 尾2 is not None:
                if float(上边界) <= y2 <= float(下边界):
                    屏幕.blit(
                        尾2,
                        (
                            int(x中心 - 尾2.get_width() // 2),
                            int(y2 - 尾2.get_height() // 2),
                        ),
                    )

            if 是否绘制头 and 罩2 is not None:
                y罩 = float(y开始)
                if float(上边界) <= y罩 <= float(下边界):
                    屏幕.blit(
                        罩2,
                        (
                            int(x中心 - 罩2.get_width() // 2),
                            int(y罩 - 罩2.get_height() // 2),
                        ),
                    )

            if 是否绘制头 and 头2 is not None:
                y头 = float(y开始)
                if float(上边界) <= y头 <= float(下边界):
                    屏幕.blit(
                        头2,
                        (
                            int(x中心 - 头2.get_width() // 2),
                            int(y头 - 头2.get_height() // 2),
                        ),
                    )
            return

        # ==========
        # body 平铺
        # ==========
        if 身2 is not None:
            单高 = int(max(6, 身2.get_height()))
            cy = int(math.floor(绘制y1))
            终点 = int(math.ceil(绘制y2))
            while cy < 终点:
                屏幕.blit(身2, (int(x中心 - 身2.get_width() // 2), int(cy)))
                cy += 单高

        # ==========
        # tail
        # ==========
        if 尾2 is not None:
            if float(上边界) <= y2 <= float(下边界):
                屏幕.blit(
                    尾2,
                    (
                        int(x中心 - 尾2.get_width() // 2),
                        int(y2 - 尾2.get_height() // 2),
                    ),
                )

        # ==========
        # arrow_mask：按每个方向自己的遮罩形状吃掉 hold-body 顶端
        # 原版不是统一水平裁切，5 个方向的视觉消失位置各不相同
        # ==========
        if 是否绘制头 and 罩2 is not None:
            y罩 = float(y开始)
            if float(上边界) <= y罩 <= float(下边界):
                屏幕.blit(
                    罩2,
                    (
                        int(x中心 - 罩2.get_width() // 2),
                        int(y罩 - 罩2.get_height() // 2),
                    ),
                )

        # ==========
        # head（命中 hold 时已被钉到目标y，不会飞天）
        # ==========
        if 是否绘制头 and 头2 is not None:
            y头 = float(y开始)
            if float(上边界) <= y头 <= float(下边界):
                屏幕.blit(
                    头2,
                    (
                        int(x中心 - 头2.get_width() // 2),
                        int(y头 - 头2.get_height() // 2),
                    ),
                )

    # def _绘制击中特效(self, 屏幕: pygame.Surface, 输入: 渲染输入):
    #     图集 = self._皮肤包.key_effect
    #     if 图集 is None:
    #         return

    #     if bool(getattr(输入, "调试_循环击中特效", False)):
    #         当前 = float(getattr(输入, "当前谱面秒", 0.0) or 0.0)
    #         for i in range(5):
    #             self._击中特效开始谱面秒[i] = 当前
    #             self._击中特效循环到谱面秒[i] = 当前 + 99999.0
    #             if self._击中特效进行秒[i] < 0.0:
    #                 self._击中特效进行秒[i] = 0.0

    #     参数 = self._取游戏区参数()
    #     游戏缩放 = float(参数.get("缩放", 1.1))
    #     y偏移 = float(参数.get("y偏移", 0.0))
    #     偏移x = float(参数.get("击中特效偏移x", 0.0))
    #     偏移y = float(参数.get("击中特效偏移y", 0.0))
    #     宽度系数 = float(参数.get("击中特效宽度系数", 2.6))

    #     当前谱面秒 = float(输入.当前谱面秒)
    #     y判定 = int(float(输入.判定线y) + y偏移 + 偏移y)

    #     # ✅ 特效更大：整体再乘 1.25
    #     目标宽 = int(max(90, int(float(输入.箭头目标宽) * 宽度系数 * 游戏缩放 * 1.25)))

    #     帧数 = 18
    #     fps = float(self._击中特效帧率)

    #     for i in range(5):
    #         循环到 = float(self._击中特效循环到谱面秒[i])

    #         if 循环到 > 0.0:
    #             if 当前谱面秒 > 循环到 + 0.02:
    #                 self._击中特效循环到谱面秒[i] = -999.0
    #                 self._击中特效进行秒[i] = -1.0
    #                 self._击中特效开始谱面秒[i] = -999.0
    #                 continue

    #             起点 = float(self._击中特效开始谱面秒[i])
    #             if 起点 < -100.0:
    #                 起点 = 当前谱面秒
    #             进行秒 = max(0.0, 当前谱面秒 - 起点)

    #             # ✅ hold 循环：速度 *2
    #             帧号 = int((进行秒 * (fps * 2.0)) % float(帧数))
    #             是否循环态 = True
    #         else:
    #             进行秒 = float(self._击中特效进行秒[i])
    #             if 进行秒 < 0.0:
    #                 continue
    #             帧号 = int(max(0, min(帧数 - 1, int(进行秒 * fps))))
    #             是否循环态 = False

    #         序列前缀, 需要水平翻转 = self._轨道到击中序列(i)
    #         文件名 = f"{序列前缀}_{帧号:04d}.png"

    #         原图 = 图集.取(文件名)
    #         if 原图 is None:
    #             continue

    #         if 需要水平翻转:
    #             缓存键 = f"eff:{文件名}:fx1:{目标宽}"
    #             原图2 = pygame.transform.flip(原图, True, False)
    #         else:
    #             缓存键 = f"eff:{文件名}:fx0:{目标宽}"
    #             原图2 = 原图

    #         图2 = self._取缩放图(缓存键, 原图2, 目标宽)

    #         x = int(float(输入.轨道中心列表[i]) - 图2.get_width() // 2 + 偏移x)
    #         y = int(y判定 - 图2.get_height() // 2)

    #         # ✅ 更亮：循环态叠两次（ADD），普通态叠一次
    #         if 是否循环态:
    #             屏幕.blit(图2, (x, y), special_flags=pygame.BLEND_RGBA_ADD)
    #             屏幕.blit(图2, (x, y), special_flags=pygame.BLEND_RGBA_ADD)
    #         else:
    #             屏幕.blit(图2, (x, y), special_flags=pygame.BLEND_RGBA_ADD)

    def _绘制击中特效(self, 屏幕: pygame.Surface, 输入: 渲染输入):
        图集 = self._皮肤包.key_effect
        if 图集 is None:
            return

        if bool(getattr(输入, "调试_循环击中特效", False)):
            当前 = float(getattr(输入, "当前谱面秒", 0.0) or 0.0)
            for i in range(5):
                self._击中特效开始谱面秒[i] = 当前
                self._击中特效循环到谱面秒[i] = 当前 + 99999.0
                if self._击中特效进行秒[i] < 0.0:
                    self._击中特效进行秒[i] = 0.0

        参数 = self._取游戏区参数()
        游戏缩放 = float(参数.get("缩放", 1.1))
        y偏移 = float(参数.get("y偏移", 0.0))
        偏移x = float(参数.get("击中特效偏移x", 0.0))
        偏移y = float(参数.get("击中特效偏移y", 0.0))
        宽度系数 = float(参数.get("击中特效宽度系数", 2.6))

        当前谱面秒 = float(输入.当前谱面秒)
        y判定 = int(float(输入.判定线y) + y偏移 + 偏移y)
        目标宽 = int(
            max(90, int(float(输入.箭头目标宽) * 宽度系数 * 游戏缩放 * 1.25))
        )

        帧数 = 18
        fps = float(self._击中特效帧率)
        特效帧名列表: List[str] = [""] * 5
        特效翻转列表: List[bool] = [False] * 5

        for i in range(5):
            循环到 = float(self._击中特效循环到谱面秒[i])

            if 循环到 > 0.0:
                if 当前谱面秒 > 循环到 + 0.02:
                    self._击中特效循环到谱面秒[i] = -999.0
                    self._击中特效进行秒[i] = -1.0
                    self._击中特效开始谱面秒[i] = -999.0
                    continue

                起点 = float(self._击中特效开始谱面秒[i])
                if 起点 < -100.0:
                    起点 = 当前谱面秒
                进行秒 = max(0.0, 当前谱面秒 - 起点)
                帧号 = int((进行秒 * (fps * 2.0)) % float(帧数))
            else:
                进行秒 = float(self._击中特效进行秒[i])
                if 进行秒 < 0.0:
                    continue
                帧号 = int(max(0, min(帧数 - 1, int(进行秒 * fps))))

            序列前缀, 需要水平翻转 = self._轨道到击中序列(i)
            特效帧名列表[i] = f"{序列前缀}_{帧号:04d}.png"
            特效翻转列表[i] = bool(需要水平翻转)

        特效布局矩形表: Dict[int, pygame.Rect] = {}
        try:
            布局 = self._确保布局管理器()
            if 布局 is not None and bool(布局.是否存在控件("特效层组")):
                上下文 = self._构建notes装饰上下文(屏幕, 输入)
                if isinstance(上下文, dict):
                    for i in range(5):
                        上下文[f"特效帧_{i}"] = str(特效帧名列表[i] or "")
                        上下文[f"特效翻转_{i}"] = bool(特效翻转列表[i])
                    构建清单 = getattr(布局, "_构建渲染清单", None)
                    if callable(构建清单):
                        项列表 = 构建清单(
                            屏幕.get_size(), 上下文, 仅绘制根id="特效层组"
                        )
                        if isinstance(项列表, list):
                            for 项 in 项列表:
                                if not isinstance(项, dict):
                                    continue
                                项id = str(项.get("id") or "")
                                if not 项id.startswith("击中特效_"):
                                    continue
                                try:
                                    轨道 = int(项id.rsplit("_", 1)[1])
                                except Exception:
                                    continue
                                矩形 = 项.get("rect")
                                if isinstance(矩形, pygame.Rect):
                                    特效布局矩形表[int(轨道)] = 矩形.copy()
        except Exception:
            特效布局矩形表 = {}

        for i in range(5):
            文件名 = str(特效帧名列表[i] or "")
            if not 文件名:
                continue

            原图 = 图集.取(文件名)
            if 原图 is None:
                continue

            当前目标宽 = int(max(48, 目标宽))
            布局矩形 = 特效布局矩形表.get(int(i))
            if isinstance(布局矩形, pygame.Rect):
                当前目标宽 = int(max(48, 布局矩形.w))

            if 特效翻转列表[i]:
                缓存键 = f"eff:{文件名}:fx1:{当前目标宽}"
                原图2 = pygame.transform.flip(原图, True, False)
            else:
                缓存键 = f"eff:{文件名}:fx0:{当前目标宽}"
                原图2 = 原图

            图2 = self._取缩放图(缓存键, 原图2, 当前目标宽)

            if isinstance(布局矩形, pygame.Rect):
                x = int(布局矩形.centerx - 图2.get_width() // 2)
                y = int(布局矩形.centery - 图2.get_height() // 2)
            else:
                x = int(float(输入.轨道中心列表[i]) - 图2.get_width() // 2 + 偏移x)
                y = int(y判定 - 图2.get_height() // 2)

            if float(self._击中特效循环到谱面秒[i]) > 0.0:
                屏幕.blit(图2, (x, y), special_flags=pygame.BLEND_RGBA_ADD)
                屏幕.blit(图2, (x, y), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                屏幕.blit(图2, (x, y), special_flags=pygame.BLEND_RGBA_ADD)

    @staticmethod
    def _轨道到击中序列(轨道: int) -> Tuple[str, bool]:
        """
        你的最新定义：
        - 083：左手装饰序列，忽略不用
        - 084：左下
        - 085：左上
        - 086：中间
        右上/右下：由 085/084 水平翻转得到（但你的素材本体偏“朝右”，所以这里让左侧翻转）
        """
        轨道 = int(轨道)

        # 左侧（素材本体更朝右，因此左侧需要镜像）
        if 轨道 == 0:  # 左下
            return ("image_084", False)
        if 轨道 == 1:  # 左上
            return ("image_085", False)

        # 中间不翻
        if 轨道 == 2:
            return ("image_086", False)

        # 右侧不翻
        if 轨道 == 3:  # 右上
            return ("image_085", True)
        if 轨道 == 4:  # 右下
            return ("image_084", True)

        return ("image_086", False)

    # ---------------- judge ----------------
    def _绘制判定提示(self, 屏幕: pygame.Surface, 输入: 渲染输入):
        图集 = self._皮肤包.judge
        if 图集 is None:
            return
        if self._判定提示剩余秒 <= 0.0:
            return

        判定 = str(self._判定提示 or "").lower()
        名 = {
            "perfect": "text_pf1_perfect.png",
            "cool": "text_pf1_cool.png",
            "good": "text_pf1_good.png",
            "miss": "text_pf1_miss.png",
        }.get(判定, "")
        if not 名:
            return

        图 = 图集.取(名)
        if 图 is None:
            return

        轨道中心 = 输入.轨道中心列表
        x中心 = (
            int((轨道中心[0] + 轨道中心[4]) // 2)
            if len(轨道中心) >= 5
            else (屏幕.get_width() // 2)
        )
        y中心 = int(输入.判定线y - int(输入.箭头目标宽 * 2.3))

        p = float(max(0.0, min(1.0, self._判定提示剩余秒 / 0.45)))
        缩放 = 1.0 + 0.18 * (1.0 - p)

        目标高 = int(max(24, min(140, 输入.箭头目标宽 * 1.05)))
        目标宽 = int(图.get_width() * (目标高 / max(1, 图.get_height())))
        目标宽 = int(目标宽 * 缩放)
        目标高 = int(目标高 * 缩放)

        图2 = self._取缩放图("判定提示", 图, 目标宽)

        alpha = int(255 * p)
        try:
            图2 = 图2.convert_alpha()
            图2.set_alpha(alpha)
        except Exception:
            pass

        屏幕.blit(图2, (x中心 - 图2.get_width() // 2, y中心 - 图2.get_height() // 2))

    # ---------------- combo / number ----------------
    def _绘制combo(self, 屏幕: pygame.Surface, 输入: 渲染输入):
        judge图集 = self._皮肤包.judge
        number图集 = self._皮肤包.number
        if judge图集 is None or number图集 is None:
            return

        combo = int(max(0, 输入.显示_连击))
        if combo < 2:
            return

        combo图 = judge图集.取("text_pf1_combo.png")
        if combo图 is None:
            return

        数字字符串 = str(combo)
        数字图列表: List[pygame.Surface] = []
        for ch in 数字字符串:
            名 = f"text_pf1_{ch}.png"
            图 = number图集.取(名)
            if 图 is not None:
                数字图列表.append(图)

        if not 数字图列表:
            return

        轨道中心 = 输入.轨道中心列表
        x中心 = (
            int((轨道中心[0] + 轨道中心[4]) // 2)
            if len(轨道中心) >= 5
            else (屏幕.get_width() // 2)
        )
        y基 = int(输入.判定线y - int(输入.箭头目标宽 * 1.55))

        combo高 = int(max(18, min(90, 输入.箭头目标宽 * 0.62)))
        combo宽 = int(combo图.get_width() * (combo高 / max(1, combo图.get_height())))
        combo2 = self._取缩放图("combo字", combo图, combo宽)

        数字高 = int(combo高 * 1.05)
        数字缩放后: List[pygame.Surface] = []
        总宽 = 0
        for idx, 原图 in enumerate(数字图列表):
            目标宽 = int(原图.get_width() * (数字高 / max(1, 原图.get_height())))
            图2 = self._取缩放图(f"combo数字:{数字字符串}:{idx}", 原图, 目标宽)
            数字缩放后.append(图2)
            总宽 += 图2.get_width()

        数字y = int(y基 - 数字高 // 2)
        combo_y = int(数字y + 数字高 + 2)

        x起 = int(x中心 - 总宽 // 2)
        cx = x起
        for 图2 in 数字缩放后:
            屏幕.blit(图2, (cx, 数字y))
            cx += 图2.get_width()

        屏幕.blit(combo2, (x中心 - combo2.get_width() // 2, combo_y))

    @staticmethod
    def _格式化倒计时(秒: float) -> str:
        秒 = float(max(0.0, 秒))
        m = int(秒 // 60)
        s = int(秒 - m * 60)
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def _规范判定显示(判定: str) -> str:
        p = str(判定 or "").strip().lower()
        if p == "perfect":
            return "Perfect"
        if p == "cool":
            return "Cool"
        if p == "good":
            return "Good"
        if p == "miss":
            return "Miss"
        return p.capitalize() if p else "-"
