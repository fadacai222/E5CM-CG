import math
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pygame
from core.常量与路径 import 取项目根目录 as _公共取项目根目录


def _取项目根目录() -> str:
    return _公共取项目根目录()


def _安全读json(路径: str) -> dict:
    if (not 路径) or (not os.path.isfile(路径)):
        return {}
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码) as f:
                obj = json.load(f)
            return obj if isinstance(obj, dict) else {}
        except Exception:
            continue
    try:
        with open(路径, "r", encoding="utf-8", errors="ignore") as f:
            obj = json.load(f)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _安全写json(路径: str, 数据: dict):
    os.makedirs(os.path.dirname(os.path.abspath(路径)), exist_ok=True)
    with open(路径, "w", encoding="utf-8") as f:
        json.dump(数据, f, ensure_ascii=False, indent=2)


def _取数(值: Any, 默认: float = 0.0) -> float:
    try:
        return float(值)
    except Exception:
        return float(默认)


def _解析颜色(
    值: Any, 默认: Tuple[int, int, int] = (255, 255, 255)
) -> Tuple[int, int, int]:
    if isinstance(值, (list, tuple)) and len(值) >= 3:
        try:
            return (int(值[0]), int(值[1]), int(值[2]))
        except Exception:
            return 默认
    return 默认


def _格式化文本(模板: str, 上下文: Dict[str, Any]) -> str:
    模板 = str(模板 or "")
    # 简单 {键} 替换
    out = 模板
    for k, v in (上下文 or {}).items():
        占位 = "{" + str(k) + "}"
        if 占位 in out:
            out = out.replace(占位, str(v))
    return out


def _比较(左: Any, op: str, 右: Any) -> bool:
    op = str(op or "==").strip()
    try:
        if op == "==":
            return 左 == 右
        if op == "!=":
            return 左 != 右
        # 数值比较
        a = float(左)
        b = float(右)
        if op == ">":
            return a > b
        if op == ">=":
            return a >= b
        if op == "<":
            return a < b
        if op == "<=":
            return a <= b
        return False
    except Exception:
        return False


def _条件成立(条件: Any, 上下文: Dict[str, Any]) -> bool:
    # ✅ 调试器强制显示：无视所有可见条件（让你能拖到任何控件）
    try:
        if isinstance(上下文, dict) and bool(上下文.get("_调试强制显示", False)):
            return True
    except Exception:
        pass

    if not 条件:
        return True
    if isinstance(条件, dict):
        键 = 条件.get("键")
        op = 条件.get("op", "==")
        值 = 条件.get("值")
        左 = 上下文.get(str(键), None)
        return _比较(左, op, 值)
    if isinstance(条件, list):
        for 子 in 条件:
            if not _条件成立(子, 上下文):
                return False
        return True
    return True


def _解析动态值(值: Any, 上下文: Dict[str, Any]) -> Any:
    """
    支持：
    - 直接值
    - {"键": "...", "映射": {...}, "默认": "..."}：
        1) 若上下文里有该键，优先取上下文值
        2) 若映射命中，用映射值
        3) 若映射不命中但上下文值存在：直接返回上下文值（✅ 关键修复：允许“映射为空”）
        4) 否则返回默认
    """
    if isinstance(值, dict) and ("键" in 值) and ("映射" in 值):
        键名 = str(值.get("键") or "")
        映射表 = 值.get("映射") or {}
        默认值 = 值.get("默认")

        上下文值 = 上下文.get(键名, None)
        if 上下文值 is None:
            return 默认值

        # 允许 int/float 转字符串键
        try:
            上下文键 = (
                str(int(上下文值))
                if isinstance(上下文值, (int, float))
                else str(上下文值)
            )
        except Exception:
            上下文键 = str(上下文值)

        if isinstance(映射表, dict) and 上下文键 in 映射表:
            return 映射表.get(上下文键)

        # ✅ 关键：映射表为空/未命中时，直接用上下文值（否则永远默认）
        return 上下文值

    return 值

@dataclass
class 调试状态:
    显示全部边框: bool = False
    选中控件id: str = ""


class 谱面渲染器布局管理器:
    """
    - 布局：<根>/json/谱面渲染器_布局.json
    - 负责：加载/热重载/绘制/命中/修改/保存
    - ✅ 修复点：
        1) 命中/渲染必须使用同一上下文（调试器会传）
        2) 组控件自动计算“子树包围盒”，可点空白选中组拖动
        3) 父组缩放会影响子控件“坐标偏移 + 尺寸”（整组缩放才正确）
        4) 字体优先加载 /字体/方正黑体简体.TTF，避免中文方块
        5) _解析动态值 支持“映射为空时直接取上下文值”，修复计数判定永远 perfect
        6) 新增 类型=精灵数字串（x + 0-9 精灵）
        7) 图片支持：水平翻转键、混合(add)
        8) 绘制支持：仅绘制某个根组（避免 HUD 被重复画两遍）
    """

    def __init__(self, 布局json路径: str):
        self.布局json路径 = os.path.abspath(str(布局json路径))
        self.项目根 = _取项目根目录()

        self._布局数据: Dict[str, Any] = {}
        self._控件列表: List[Dict[str, Any]] = []
        self._控件索引: Dict[str, Dict[str, Any]] = {}
        self._子列表索引: Dict[str, List[str]] = {}
        self._上次mtime: float = -1.0

        self._文件图缓存: Dict[str, Tuple[float, Optional[pygame.Surface]]] = {}
        self._外部图集缓存: Dict[
            str, Tuple[float, float, Optional[Dict[str, pygame.Surface]]]
        ] = {}
        self._圆罩缓存: Dict[Tuple[int, int], pygame.Surface] = {}
        self._羽化罩缓存: Dict[Tuple[int, int, int], pygame.Surface] = {}
        self._字体缓存: Dict[Tuple[str, int, bool], pygame.font.Font] = {}
        self._文本图缓存: Dict[
            Tuple[str, str, int, bool, Tuple[int, int, int]], pygame.Surface
        ] = {}
        self._缩放图缓存: Dict[Tuple[str, int, int], pygame.Surface] = {}
        self._暴走血条缓存: Dict[Tuple[Any, ...], Any] = {}
        self._皮肤帧处理缓存: Dict[Tuple[str, str], Optional[pygame.Surface]] = {}
        self._渲染清单缓存: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = {}
        self._布局依赖键: set[str] = set()

        self._默认字体路径 = os.path.join(
            self.项目根, "冷资源", "字体", "方正黑体简体.TTF"
        )

        self._载入(强制=True)

    def _按边距取内容矩形(
        self,
        外矩形: pygame.Rect,
        控件定义: Dict[str, Any],
        项: Dict[str, Any],
    ) -> pygame.Rect:
        """
        ✅ 通用“边距”(padding) 支持：所有控件都可写
        {
          "边距": {"l":6,"t":6,"r":6,"b":6}
        }

        说明：
        - 边距数值按“布局单位”定义
        - 转屏幕像素时：乘 (全局缩放 * 总缩放)
        - 命中/边框仍以外矩形为准（更好选中）
        """
        边距def = 控件定义.get("边距")
        if not isinstance(边距def, dict):
            return 外矩形

        try:
            全局缩放 = float(项.get("全局缩放", 1.0))
        except Exception:
            全局缩放 = 1.0
        try:
            总缩放 = float(项.get("总缩放", 1.0))
        except Exception:
            总缩放 = 1.0

        缩放系数 = float(max(0.01, 全局缩放 * 总缩放))

        def _取边(键名: str) -> int:
            try:
                v = float(边距def.get(键名, 0.0))
            except Exception:
                v = 0.0
            return int(round(v * 缩放系数))

        左 = max(0, _取边("l"))
        上 = max(0, _取边("t"))
        右 = max(0, _取边("r"))
        下 = max(0, _取边("b"))

        新宽 = int(max(2, 外矩形.w - 左 - 右))
        新高 = int(max(2, 外矩形.h - 上 - 下))
        return pygame.Rect(int(外矩形.x + 左), int(外矩形.y + 上), int(新宽), int(新高))

    # ------------------- 公共 -------------------

    def 是否存在控件(self, 控件id: str) -> bool:
        return str(控件id) in self._控件索引

    def _取游戏区参数_可写(self) -> Dict[str, float]:
        if not isinstance(getattr(self, "_布局数据", None), dict):
            self._布局数据 = {}

        参数 = self._布局数据.get("游戏区参数", None)
        if not isinstance(参数, dict):
            参数 = {}
            self._布局数据["游戏区参数"] = 参数

        默认 = {
            "y偏移": -12.0,
            "缩放": 1.0,
            "hold宽度系数": 0.96,
            "判定区宽度系数": 1.0,
            "击中特效宽度系数": 2.6,
            "击中特效偏移x": 0.0,
            "击中特效偏移y": 0.0,
        }
        for k, v in 默认.items():
            if k not in 参数:
                参数[k] = v

        # 统一转 float
        for k in list(参数.keys()):
            try:
                参数[k] = float(参数[k])
            except Exception:
                参数[k] = float(默认.get(k, 0.0))
        return 参数

    def 取全局缩放(self, 屏幕尺寸: Tuple[int, int]) -> float:
        return float(self._取全局缩放(屏幕尺寸))

    # ------------------- I/O -------------------

    def _重建子树索引(self):
        self._子列表索引 = {}
        for 控件定义 in self._控件列表:
            控件id = str(控件定义.get("id") or "")
            父id = str(控件定义.get("父") or "")
            if 父id:
                if 父id not in self._子列表索引:
                    self._子列表索引[父id] = []
                self._子列表索引[父id].append(控件id)

    def _载入(self, 强制: bool = False):
        try:
            修改时间 = (
                float(os.path.getmtime(self.布局json路径))
                if os.path.isfile(self.布局json路径)
                else -1.0
            )
        except Exception:
            修改时间 = -1.0

        if (not 强制) and (修改时间 == self._上次mtime) and self._布局数据:
            return

        self._上次mtime = 修改时间
        数据 = _安全读json(self.布局json路径)
        self._应用布局数据(数据)

    def _应用布局数据(self, 数据: Any):
        self._布局数据 = 数据 if isinstance(数据, dict) else {}
        控件原始 = self._布局数据.get("控件", [])

        if not isinstance(控件原始, list):
            控件原始 = []

        # ✅ 兼容：控件数组里嵌套 list（你现在就是这种）
        扁平控件列表: List[Dict[str, Any]] = []

        def _展开(节点: Any):
            if isinstance(节点, dict):
                if 节点.get("id"):
                    扁平控件列表.append(节点)
                return
            if isinstance(节点, list):
                for 子 in 节点:
                    _展开(子)

        for 条目 in 控件原始:
            _展开(条目)

        self._控件列表 = [
            c for c in 扁平控件列表 if isinstance(c, dict) and c.get("id")
        ]
        self._控件索引 = {str(c["id"]): c for c in self._控件列表}
        self._重建子树索引()
        self._重建布局依赖键()
        self._清空运行时缓存()

    def _清空运行时缓存(self):
        self._渲染清单缓存.clear()
        self._缩放图缓存.clear()
        self._暴走血条缓存.clear()
        self._皮肤帧处理缓存.clear()

    def _重建布局依赖键(self):
        依赖键: set[str] = {"_调试强制显示", "_调试隐藏控件ids"}

        def _收集条件键(条件: Any):
            if isinstance(条件, dict):
                键名 = str(条件.get("键") or "").strip()
                if 键名:
                    依赖键.add(键名)
                for v in 条件.values():
                    _收集条件键(v)
                return
            if isinstance(条件, list):
                for 项 in 条件:
                    _收集条件键(项)

        def _收集动态键(值: Any):
            if isinstance(值, dict):
                键名 = str(值.get("键") or "").strip()
                if 键名:
                    依赖键.add(键名)
                for v in 值.values():
                    _收集动态键(v)
                return
            if isinstance(值, list):
                for 项 in 值:
                    _收集动态键(项)

        for 控件 in self._控件列表:
            if not isinstance(控件, dict):
                continue
            _收集动态键(控件.get("x"))
            _收集动态键(控件.get("y"))
            _收集动态键(控件.get("w"))
            _收集动态键(控件.get("h"))
            _收集条件键(控件.get("可见条件"))

            for 键名 in ("缩放键", "透明键", "水平翻转键"):
                值 = str(控件.get(键名) or "").strip()
                if 值:
                    依赖键.add(值)

        self._布局依赖键 = 依赖键

    def 保存(self):
        self._布局数据["控件"] = self._控件列表
        _安全写json(self.布局json路径, self._布局数据)

    def 热重载(self):
        self._载入(强制=False)

    def 导出快照(self) -> Dict[str, Any]:
        try:
            return json.loads(json.dumps(self._布局数据, ensure_ascii=False))
        except Exception:
            return _安全读json(self.布局json路径)

    def 导入快照(self, 快照: Any):
        if not isinstance(快照, dict):
            return
        try:
            数据 = json.loads(json.dumps(快照, ensure_ascii=False))
        except Exception:
            数据 = dict(快照)
        self._应用布局数据(数据)

    @staticmethod
    def _值转缓存签名(值: Any) -> Any:
        if isinstance(值, (str, int, float, bool)) or 值 is None:
            return 值
        if isinstance(值, (list, tuple)):
            return tuple(谱面渲染器布局管理器._值转缓存签名(v) for v in 值[:32])
        if isinstance(值, dict):
            项列表 = []
            for k in sorted(list(值.keys()))[:32]:
                项列表.append((str(k), 谱面渲染器布局管理器._值转缓存签名(值.get(k))))
            return tuple(项列表)
        if isinstance(值, pygame.Rect):
            return ("rect", int(值.x), int(值.y), int(值.w), int(值.h))
        if isinstance(值, pygame.Surface):
            return ("surface", int(值.get_width()), int(值.get_height()), id(值))
        return str(type(值).__name__)

    def _取渲染清单缓存键(
        self,
        屏幕尺寸: Tuple[int, int],
        上下文: Dict[str, Any],
        仅绘制根id: Optional[str],
        仅绘制控件ids: Optional[List[str]],
    ) -> Tuple[Any, ...]:
        依赖项 = []
        for 键名 in sorted(self._布局依赖键):
            if not isinstance(上下文, dict) or 键名 not in 上下文:
                依赖项.append((键名, None))
                continue
            依赖项.append((键名, self._值转缓存签名(上下文.get(键名))))

        return (
            int(屏幕尺寸[0]),
            int(屏幕尺寸[1]),
            str(仅绘制根id or ""),
            tuple(sorted(str(v) for v in (仅绘制控件ids or []) if str(v or ""))),
            tuple(依赖项),
            float(self._上次mtime),
            int(len(self._控件列表)),
        )

    @staticmethod
    def _复制渲染表(渲染表: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        结果: List[Dict[str, Any]] = []
        for 项 in 渲染表:
            if not isinstance(项, dict):
                continue
            新项 = dict(项)
            矩形 = 新项.get("rect")
            if isinstance(矩形, pygame.Rect):
                新项["rect"] = 矩形.copy()
            结果.append(新项)
        return 结果

    def 取调试图层列表(self) -> List[Dict[str, Any]]:
        def _取深度(控件id: str) -> int:
            深度 = 0
            当前 = self._控件索引.get(str(控件id))
            已见 = set()
            while isinstance(当前, dict):
                父id = str(当前.get("父") or "")
                if not 父id or 父id in 已见:
                    break
                已见.add(父id)
                if 父id not in self._控件索引:
                    break
                深度 += 1
                当前 = self._控件索引.get(父id)
            return int(深度)

        结果: List[Dict[str, Any]] = []
        for 顺序, 控件 in enumerate(self._控件列表):
            if not isinstance(控件, dict):
                continue
            控件id = str(控件.get("id") or "")
            if not 控件id:
                continue
            结果.append(
                {
                    "id": 控件id,
                    "父": str(控件.get("父") or ""),
                    "类型": str(控件.get("类型") or ""),
                    "z": int(_取数(控件.get("z"), 0)),
                    "depth": int(_取深度(控件id)),
                    "顺序": int(顺序),
                }
            )
        结果.sort(key=lambda 项: (-int(项.get("z", 0)), int(项.get("顺序", 0))))
        return 结果

    # ------------------- 选择/修改 -------------------

    def 命中控件(
        self,
        屏幕点: Tuple[int, int],
        屏幕尺寸: Tuple[int, int],
        上下文: Dict[str, Any],
        仅绘制根id: Optional[str] = None,
        仅绘制控件ids: Optional[List[str]] = None,
    ) -> str:
        self.热重载()
        渲染表 = self._构建渲染清单(
            屏幕尺寸,
            上下文,
            仅绘制根id=仅绘制根id,
            仅绘制控件ids=仅绘制控件ids,
        )
        点x, 点y = int(屏幕点[0]), int(屏幕点[1])

        # z 大的优先
        渲染表.sort(key=lambda 项: int(项.get("z", 0)))
        for 项 in reversed(渲染表):
            矩形: pygame.Rect = 项["rect"]
            if 矩形.collidepoint(点x, 点y):
                return str(项["id"])
        return ""

    def 移动控件(
        self, 控件id: str, dx_屏幕: float, dy_屏幕: float, 屏幕尺寸: Tuple[int, int]
    ):
        控件id = str(控件id or "")
        控件 = self._控件索引.get(控件id)
        if not 控件:
            return

        比例 = float(self._取全局缩放(屏幕尺寸))
        if 比例 <= 0:
            比例 = 1.0
        dx = float(dx_屏幕) / 比例
        dy = float(dy_屏幕) / 比例

        # ✅ 调试控制：拖动改游戏区参数（不挪动控件本身位置，像“拖动调值”）
        if 控件id == "调试_游戏区y偏移":
            参数 = self._取游戏区参数_可写()
            参数["y偏移"] = float(
                max(-240.0, min(240.0, float(参数.get("y偏移", 0.0)) + dy))
            )
            self._清空运行时缓存()
            return

        if 控件id == "调试_击中特效偏移":
            参数 = self._取游戏区参数_可写()
            参数["击中特效偏移x"] = float(
                max(-400.0, min(400.0, float(参数.get("击中特效偏移x", 0.0)) + dx))
            )
            参数["击中特效偏移y"] = float(
                max(-240.0, min(240.0, float(参数.get("击中特效偏移y", 0.0)) + dy))
            )
            self._清空运行时缓存()
            return

        # ✅ 计数动画组：X 锚点锁定判定区中心，只允许改 Y
        if 控件id == "计数动画组":
            if not isinstance(控件.get("x"), dict):
                控件["x"] = {"键": "计数组中心x_布局"}
            控件["y"] = _取数(控件.get("y"), 0.0) + dy
            self._清空运行时缓存()
            return

        if 控件id == "判定区组":
            控件["x"] = _取数(控件.get("x"), 0.0) + dx
            控件["y"] = _取数(控件.get("y"), 0.0) + dy

            特效组 = self._控件索引.get("特效层组")
            if isinstance(特效组, dict):
                特效组["x"] = _取数(特效组.get("x"), 0.0) + dx
                特效组["y"] = _取数(特效组.get("y"), 0.0) + dy

            计数组 = self._控件索引.get("计数动画组")
            if isinstance(计数组, dict):
                计数组["y"] = _取数(计数组.get("y"), 0.0) + dy

            self._清空运行时缓存()
            return

        # 默认：正常拖动控件
        控件["x"] = _取数(控件.get("x"), 0.0) + dx
        控件["y"] = _取数(控件.get("y"), 0.0) + dy
        self._清空运行时缓存()

    def 缩放控件(
        self, 控件id: str, dw_屏幕: float, dh_屏幕: float, 屏幕尺寸: Tuple[int, int]
    ):
        控件id = str(控件id or "")
        控件 = self._控件索引.get(控件id)
        if not 控件:
            return

        # ✅ 调试控制：滚轮改游戏区参数（你调试器滚轮一次一般是 +10/-10）
        合力 = float(dw_屏幕 + dh_屏幕)
        方向 = 1.0 if 合力 > 0 else (-1.0 if 合力 < 0 else 0.0)
        if 方向 != 0.0:
            if 控件id == "调试_游戏区缩放":
                参数 = self._取游戏区参数_可写()
                当前 = float(参数.get("缩放", 1.0))
                新 = 当前 * (1.03 if 方向 > 0 else 0.97)
                参数["缩放"] = float(max(0.3, min(3.0, 新)))
                self._清空运行时缓存()
                return

            if 控件id == "调试_hold宽度":
                参数 = self._取游戏区参数_可写()
                当前 = float(参数.get("hold宽度系数", 0.96))
                新 = 当前 + (0.01 if 方向 > 0 else -0.01)
                参数["hold宽度系数"] = float(max(0.6, min(1.2, 新)))
                self._清空运行时缓存()
                return

            if 控件id == "调试_判定区宽度":
                参数 = self._取游戏区参数_可写()
                当前 = float(参数.get("判定区宽度系数", 1.0))
                新 = 当前 + (0.02 if 方向 > 0 else -0.02)
                参数["判定区宽度系数"] = float(max(0.6, min(2.0, 新)))
                self._清空运行时缓存()
                return

            if 控件id == "调试_击中特效宽度":
                参数 = self._取游戏区参数_可写()
                当前 = float(参数.get("击中特效宽度系数", 2.6))
                新 = 当前 + (0.05 if 方向 > 0 else -0.05)
                参数["击中特效宽度系数"] = float(max(0.8, min(6.0, 新)))
                self._清空运行时缓存()
                return

        # 默认：正常缩放控件大小
        比例 = float(self._取全局缩放(屏幕尺寸))
        if 比例 <= 0:
            比例 = 1.0
        dw = float(dw_屏幕) / 比例
        dh = float(dh_屏幕) / 比例
        控件["w"] = max(2.0, _取数(控件.get("w"), 10.0) + dw)
        控件["h"] = max(2.0, _取数(控件.get("h"), 10.0) + dh)
        self._清空运行时缓存()

    def 改字号(self, 控件id: str, d字号: int):
        控件 = self._控件索引.get(str(控件id))
        if not 控件:
            return
        if str(控件.get("类型")) != "文本":
            return
        旧 = int(_取数(控件.get("字号"), 24))
        新 = int(max(6, min(200, 旧 + int(d字号))))
        控件["字号"] = 新
        self._清空运行时缓存()

    def 改字间距(self, 控件id: str, d字距: int):
        控件 = self._控件索引.get(str(控件id))
        if not 控件:
            return
        if str(控件.get("类型")) != "文本":
            return
        旧 = int(_取数(控件.get("字间距"), 0))
        新 = int(max(-32, min(64, 旧 + int(d字距))))
        控件["字间距"] = int(新)
        self._清空运行时缓存()

    def 改层级(self, 控件id: str, dz: int):
        控件 = self._控件索引.get(str(控件id))
        if not 控件:
            return
        旧 = int(_取数(控件.get("z"), 0))
        控件["z"] = int(max(-9999, min(9999, 旧 + int(dz))))
        self._清空运行时缓存()

    def 缩放全局(self, d比例: float):
        当前 = float(_取数(self._布局数据.get("全局缩放"), 1.0))
        新 = float(max(0.2, min(6.0, 当前 * float(d比例))))
        self._布局数据["全局缩放"] = 新
        self._清空运行时缓存()

    # ------------------- 绘制 -------------------

    def 绘制(
        self,
        屏幕: pygame.Surface,
        上下文: Dict[str, Any],
        皮肤包: Any,
        调试: Optional[Any] = None,
        仅绘制根id: Optional[str] = None,
        仅绘制控件ids: Optional[List[str]] = None,
    ):
        self.热重载()
        if 调试 is None:
            调试 = 调试状态()

        屏幕尺寸 = 屏幕.get_size()
        渲染表 = self._构建渲染清单(
            屏幕尺寸,
            上下文,
            仅绘制根id=仅绘制根id,
            仅绘制控件ids=仅绘制控件ids,
        )

        # 画（按 z 从小到大）
        渲染表.sort(key=lambda 项: int(项.get("z", 0)))
        for 项 in 渲染表:
            self._绘制单控件(屏幕, 项, 上下文, 皮肤包)

        # 边框（默认不画）
        if bool(getattr(调试, "显示全部边框", False)):
            for 项 in 渲染表:
                矩形: pygame.Rect = 项["rect"]
                pygame.draw.rect(屏幕, (0, 120, 255), 矩形, width=2)
                self._绘制调试标注(屏幕, 项, (0, 120, 255))

        # 选中黄框（即使全局边框关闭也要画）
        选中id = str(getattr(调试, "选中控件id", "") or "")
        if 选中id:
            for 项 in 渲染表:
                if str(项["id"]) == 选中id:
                    矩形: pygame.Rect = 项["rect"]
                    pygame.draw.rect(屏幕, (255, 220, 0), 矩形, width=2)
                    self._绘制调试标注(屏幕, 项, (255, 220, 0))
                    break

    # ------------------- 内部：布局计算 -------------------

    def _绘制调试标注(
        self,
        屏幕: pygame.Surface,
        项: Dict[str, Any],
        边框颜色: Tuple[int, int, int],
    ):
        try:
            矩形: pygame.Rect = 项["rect"]
            控件定义 = 项["def"]
            控件id = str(项.get("id") or 控件定义.get("id") or "")
            控件类型 = str(控件定义.get("类型") or "")
        except Exception:
            return

        if (not 控件id) and (not 控件类型):
            return

        标注文本 = str(控件id or "?")
        if 控件类型:
            标注文本 += f" [{控件类型}]"

        try:
            文图 = self._取文本图("调试标注", 标注文本, 12, True, (255, 255, 255), 255)
        except Exception:
            文图 = None
        if 文图 is None:
            return

        标签宽 = int(max(8, 文图.get_width() + 8))
        标签高 = int(max(8, 文图.get_height() + 4))
        标签x = int(max(0, 矩形.x))
        标签y = int(max(0, 矩形.y - 标签高 - 2))
        if 标签y < 0:
            标签y = int(max(0, 矩形.y + 2))

        try:
            底图 = pygame.Surface((标签宽, 标签高), pygame.SRCALPHA)
            底图.fill((0, 0, 0, 170))
            屏幕.blit(底图, (标签x, 标签y))
            pygame.draw.rect(
                屏幕,
                边框颜色,
                pygame.Rect(标签x, 标签y, 标签宽, 标签高),
                width=1,
                border_radius=4,
            )
            屏幕.blit(文图, (标签x + 4, 标签y + 2))
        except Exception:
            return

    def _取全局缩放(self, 屏幕尺寸: Tuple[int, int]) -> float:
        基准宽 = int(_取数(self._布局数据.get("基准宽"), 1280))
        基准高 = int(_取数(self._布局数据.get("基准高"), 720))
        屏宽, 屏高 = int(屏幕尺寸[0]), int(屏幕尺寸[1])

        if 基准宽 <= 0 or 基准高 <= 0:
            return float(_取数(self._布局数据.get("全局缩放"), 1.0))

        比例 = min(float(屏宽) / float(基准宽), float(屏高) / float(基准高))
        return float(比例) * float(_取数(self._布局数据.get("全局缩放"), 1.0))

    def _收集子树id(self, 根id: str) -> List[str]:
        根id = str(根id or "")
        if not 根id:
            return []
        if 根id not in self._控件索引:
            return []
        结果: List[str] = []
        栈: List[str] = [根id]
        while 栈:
            当前 = 栈.pop()
            结果.append(当前)
            子列表 = self._子列表索引.get(当前, [])
            for 子 in 子列表:
                栈.append(子)
        return 结果

    def _取表达式数(self, 值def: Any, 上下文: Dict[str, Any], 默认: float) -> float:
        if isinstance(值def, (int, float)):
            return float(值def)

        if isinstance(值def, dict) and ("键" in 值def):
            键名 = str(值def.get("键") or "")
            默认值 = 值def.get("默认", 默认)
            原值 = 上下文.get(键名, 默认值)

            if "索引" in 值def:
                try:
                    索引 = int(值def.get("索引"))
                    if isinstance(原值, (list, tuple)) and 0 <= 索引 < len(原值):
                        原值 = 原值[索引]
                    else:
                        原值 = 默认值
                except Exception:
                    原值 = 默认值

            try:
                数 = float(原值)
            except Exception:
                数 = float(默认值)

            乘 = self._取表达式数(值def.get("乘", 1.0), 上下文, 1.0)
            偏移 = self._取表达式数(值def.get("偏移", 0.0), 上下文, 0.0)
            return float(数) * float(乘) + float(偏移)

        try:
            return float(值def)
        except Exception:
            return float(默认)

    def _条件成立_可调试强制(self, 条件: Any, 上下文: Dict[str, Any]) -> bool:
        # ✅ 调试强制显示：上下文里塞 _调试强制显示=true 就无视所有可见条件
        if bool(上下文.get("_调试强制显示", False)):
            return True
        return _条件成立(条件, 上下文)

    def _构建渲染清单(
        self,
        屏幕尺寸: Tuple[int, int],
        上下文: Dict[str, Any],
        仅绘制根id: Optional[str] = None,
        仅绘制控件ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        缓存键 = self._取渲染清单缓存键(屏幕尺寸, 上下文, 仅绘制根id, 仅绘制控件ids)
        if 缓存键 in self._渲染清单缓存:
            return self._复制渲染表(self._渲染清单缓存[缓存键])

        全局缩放 = float(self._取全局缩放(屏幕尺寸))
        隐藏集合: set = set()
        try:
            原值 = (
                上下文.get("_调试隐藏控件ids", []) if isinstance(上下文, dict) else []
            )
            if isinstance(原值, (list, tuple, set)):
                隐藏集合 = {str(v) for v in 原值 if str(v or "")}
        except Exception:
            隐藏集合 = set()

        允许集合: Optional[set] = None
        if 仅绘制根id:
            子树 = self._收集子树id(str(仅绘制根id))
            允许集合 = set(子树)
        if 仅绘制控件ids:
            指定集合: set[str] = set()
            for v in 仅绘制控件ids:
                控件id = str(v or "")
                if not 控件id:
                    continue
                指定集合.add(控件id)
                当前 = self._控件索引.get(控件id)
                已见: set[str] = set()
                while isinstance(当前, dict):
                    父id = str(当前.get("父") or "")
                    if (not 父id) or (父id in 已见):
                        break
                    已见.add(父id)
                    指定集合.add(父id)
                    当前 = self._控件索引.get(父id)
            允许集合 = 指定集合 if 允许集合 is None else (允许集合 & 指定集合)

        # 节点状态缓存
        状态表: Dict[str, Dict[str, Any]] = {}

        def _取父子原点(父状态: Dict[str, Any]) -> Tuple[float, float]:
            # 组锚点=center：子坐标系原点在组中心；否则在组左上
            if bool(父状态.get("子原点在中心", False)):
                return (float(父状态["中心x"]), float(父状态["中心y"]))
            矩形: pygame.Rect = 父状态["rect"]
            return (float(矩形.x), float(矩形.y))

        def _构建节点(
            控件id: str,
            父状态: Optional[Dict[str, Any]],
            父总缩放: float,
            父总透明: float,
        ):
            控件id = str(控件id)
            if 控件id in 状态表:
                return

            控件 = self._控件索引.get(控件id)
            if not 控件:
                return

            if 控件id in 隐藏集合:
                return

            if 允许集合 is not None and 控件id not in 允许集合:
                return

            if not self._条件成立_可调试强制(控件.get("可见条件"), 上下文):
                return

            # 父子坐标原点
            if 父状态 is None:
                父原点x, 父原点y = (0.0, 0.0)
                父对子坐标缩放 = 1.0
            else:
                父原点x, 父原点y = _取父子原点(父状态)
                父对子坐标缩放 = float(父状态.get("总缩放", 1.0))

            # 位置：只吃“父缩放”，不吃“自己缩放”
            本地x = self._取表达式数(控件.get("x"), 上下文, 0.0) * 全局缩放
            本地y = self._取表达式数(控件.get("y"), 上下文, 0.0) * 全局缩放
            锚点点x = float(父原点x) + float(本地x) * float(父对子坐标缩放)
            锚点点y = float(父原点y) + float(本地y) * float(父对子坐标缩放)

            # 自己缩放/透明（会影响自己尺寸 & 子坐标系）
            自己缩放键 = str(控件.get("缩放键") or "")
            自己透明键 = str(控件.get("透明键") or "")

            自己缩放 = 1.0
            if 自己缩放键:
                try:
                    自己缩放 = float(上下文.get(自己缩放键, 1.0))
                except Exception:
                    自己缩放 = 1.0

            自己透明 = 1.0
            if 自己透明键:
                try:
                    自己透明 = float(上下文.get(自己透明键, 1.0))
                except Exception:
                    自己透明 = 1.0

            总缩放 = float(父总缩放) * float(max(0.01, 自己缩放))
            总透明 = float(父总透明) * float(max(0.0, min(1.0, 自己透明)))

            本地w = self._取表达式数(控件.get("w"), 上下文, 10.0) * 全局缩放
            本地h = self._取表达式数(控件.get("h"), 上下文, 10.0) * 全局缩放

            宽 = int(max(2, float(本地w) * 总缩放))
            高 = int(max(2, float(本地h) * 总缩放))

            锚点 = str(控件.get("锚点") or "").lower()
            左上x = int(锚点点x - 宽 // 2) if 锚点 == "center" else int(锚点点x)
            左上y = int(锚点点y - 高 // 2) if 锚点 == "center" else int(锚点点y)

            矩形 = pygame.Rect(左上x, 左上y, 宽, 高)

            类型 = str(控件.get("类型") or "")
            是组 = 类型 == "组"

            # 先记一个占位状态（组包围盒后面再修正）
            状态 = {
                "id": 控件id,
                "def": 控件,
                "rect": 矩形,
                "z": int(_取数(控件.get("z"), 0)),
                "总缩放": 总缩放,
                "总透明": 总透明,
                "全局缩放": 全局缩放,
                "是否组": 是组,
                "中心x": float(锚点点x),
                "中心y": float(锚点点y),
                "子原点在中心": (是组 and (锚点 == "center")),
            }
            状态表[控件id] = 状态

            # 递归子控件
            子列表 = self._子列表索引.get(控件id, [])
            for 子id in 子列表:
                _构建节点(str(子id), 状态, 总缩放, 总透明)

            # ✅ 组包围盒：用子树叶子 union（可点空白选中组）
            if 是组:
                子矩形们: List[pygame.Rect] = []
                for 子id in 子列表:
                    子状态 = 状态表.get(str(子id))
                    if 子状态:
                        子矩形们.append(子状态["rect"])

                if 子矩形们:
                    包围 = 子矩形们[0].copy()
                    for r in 子矩形们[1:]:
                        包围.union_ip(r)
                    状态["rect"] = 包围

        # 构建：从所有“无父/父不存在”的控件作为根
        根列表: List[str] = []
        for 控件定义 in self._控件列表:
            控件id = str(控件定义.get("id") or "")
            父id = str(控件定义.get("父") or "")
            if not 父id or (父id not in self._控件索引):
                根列表.append(控件id)

        for 根id in 根列表:
            _构建节点(str(根id), None, 1.0, 1.0)

        结果 = list(状态表.values())
        self._渲染清单缓存[缓存键] = self._复制渲染表(结果)
        return self._复制渲染表(结果)

    # ------------------- 内部：资源 -------------------

    def _取文件图(self, 相对路径: str) -> Optional[pygame.Surface]:
        相对路径 = str(相对路径 or "").replace("\\", "/")
        if not 相对路径:
            return None
        绝对路径 = os.path.abspath(os.path.join(self.项目根, 相对路径))

        try:
            修改时间 = (
                float(os.path.getmtime(绝对路径)) if os.path.isfile(绝对路径) else -1.0
            )
        except Exception:
            修改时间 = -1.0

        旧 = self._文件图缓存.get(绝对路径)
        if 旧 and 旧[0] == 修改时间 and 旧[1] is not None:
            return 旧[1]

        if not os.path.isfile(绝对路径):
            self._文件图缓存[绝对路径] = (修改时间, None)
            return None

        try:
            图 = pygame.image.load(绝对路径).convert_alpha()
            self._文件图缓存[绝对路径] = (修改时间, 图)
            return 图
        except Exception:
            self._文件图缓存[绝对路径] = (修改时间, None)
            return None

    @staticmethod
    def _构建外部图集帧表(
        图集图: pygame.Surface, json数据: dict
    ) -> Dict[str, pygame.Surface]:
        帧表: Dict[str, pygame.Surface] = {}
        try:
            图集图 = 图集图.convert_alpha()
        except Exception:
            pass

        frames = json数据.get("frames", None)
        if isinstance(frames, dict):
            可迭代 = []
            for 文件名, fr in frames.items():
                if isinstance(fr, dict):
                    fr2 = dict(fr)
                    fr2["filename"] = 文件名
                    可迭代.append(fr2)
            frames = 可迭代

        if not isinstance(frames, list):
            return 帧表

        for fr in frames:
            try:
                文件名 = str(fr.get("filename", "") or "")
                frame = fr.get("frame", {}) or {}
                x = int(frame.get("x", 0))
                y = int(frame.get("y", 0))
                w = int(frame.get("w", 0))
                h = int(frame.get("h", 0))
                rotated = bool(fr.get("rotated", False))
                trimmed = bool(fr.get("trimmed", False))
                if (not 文件名) or w <= 0 or h <= 0:
                    continue

                子图 = 图集图.subsurface(pygame.Rect(x, y, w, h)).copy()
                if rotated:
                    子图 = pygame.transform.rotate(子图, 90)

                if trimmed:
                    src = fr.get("sourceSize", {}) or {}
                    ssw = int(src.get("w", w))
                    ssh = int(src.get("h", h))
                    sss = fr.get("spriteSourceSize", {}) or {}
                    ox = int(sss.get("x", 0))
                    oy = int(sss.get("y", 0))
                    还原 = pygame.Surface((max(1, ssw), max(1, ssh)), pygame.SRCALPHA)
                    还原.fill((0, 0, 0, 0))
                    还原.blit(子图, (ox, oy))
                    子图 = 还原

                帧表[文件名] = 子图
            except Exception:
                continue

        return 帧表

    def _取外部图集帧(self, 图集目录: str, 帧名: str) -> Optional[pygame.Surface]:
        图集目录 = str(图集目录 or "").replace("\\", "/").strip()
        帧名 = str(帧名 or "").strip()
        if (not 图集目录) or (not 帧名):
            return None

        if os.path.isabs(图集目录):
            绝对目录 = os.path.abspath(图集目录)
        else:
            绝对目录 = os.path.abspath(os.path.join(self.项目根, 图集目录))

        json路径 = os.path.join(绝对目录, "skin.json")
        png路径 = os.path.join(绝对目录, "skin.png")

        try:
            json_mtime = (
                float(os.path.getmtime(json路径)) if os.path.isfile(json路径) else -1.0
            )
        except Exception:
            json_mtime = -1.0
        try:
            png_mtime = (
                float(os.path.getmtime(png路径)) if os.path.isfile(png路径) else -1.0
            )
        except Exception:
            png_mtime = -1.0

        旧 = self._外部图集缓存.get(绝对目录)
        if (
            旧 is not None
            and float(旧[0]) == float(json_mtime)
            and float(旧[1]) == float(png_mtime)
        ):
            帧表 = 旧[2]
            return 帧表.get(帧名) if isinstance(帧表, dict) else None

        if (not os.path.isfile(json路径)) or (not os.path.isfile(png路径)):
            self._外部图集缓存[绝对目录] = (json_mtime, png_mtime, None)
            return None

        try:
            json数据 = _安全读json(json路径)
            图集图 = pygame.image.load(png路径)
            帧表 = self._构建外部图集帧表(图集图, json数据)
            self._外部图集缓存[绝对目录] = (json_mtime, png_mtime, 帧表)
            return 帧表.get(帧名)
        except Exception:
            self._外部图集缓存[绝对目录] = (json_mtime, png_mtime, None)
            return None

    def _取皮肤帧(
        self, 皮肤包: Any, 分包名: str, 帧名: str
    ) -> Optional[pygame.Surface]:
        分包名 = str(分包名 or "").strip()
        帧名 = str(帧名 or "").strip()
        if (not 分包名) or (not 帧名):
            return None
        try:
            图集 = getattr(皮肤包, 分包名, None)
            if 图集 is None:
                return None
            取函数 = getattr(图集, "取", None)
            if not callable(取函数):
                return None
            原图 = 取函数(帧名)
            if not isinstance(原图, pygame.Surface):
                return None
            if 分包名 != "key_effect":
                return 原图

            缓存键 = (str(分包名), str(帧名))
            if 缓存键 in self._皮肤帧处理缓存:
                return self._皮肤帧处理缓存[缓存键]

            try:
                图 = 原图.copy().convert_alpha()
                w = int(图.get_width())
                h = int(图.get_height())
                if w > 0 and h > 0:
                    for y in range(h):
                        for x in range(w):
                            r, g, b, a = 图.get_at((x, y))
                            if a <= 0:
                                continue
                            if max(int(r), int(g), int(b)) <= 8:
                                图.set_at((x, y), (0, 0, 0, 0))
                self._皮肤帧处理缓存[缓存键] = 图
                return 图
            except Exception:
                self._皮肤帧处理缓存[缓存键] = 原图
                return 原图
        except Exception:
            return None

    def _取字体(self, 字号: int, 粗体: bool) -> pygame.font.Font:
        pygame.font.init()

        字号 = int(max(6, min(180, int(字号))))
        粗体 = bool(粗体)

        # ✅ 优先项目内字体：/字体/方正黑体简体.TTF
        字体路径 = os.path.join(self.项目根, "冷资源", "字体", "方正黑体简体.TTF")
        路径键 = 字体路径 if os.path.isfile(字体路径) else "sys"

        key = (路径键, int(字号), bool(粗体))
        if key in self._字体缓存:
            return self._字体缓存[key]

        字体对象 = None
        if os.path.isfile(字体路径):
            try:
                字体对象 = pygame.font.Font(字体路径, int(字号))
                try:
                    字体对象.set_bold(bool(粗体))
                except Exception:
                    pass
            except Exception:
                字体对象 = None

        if 字体对象 is None:
            try:
                字体对象 = pygame.font.Font(None, int(字号))
                try:
                    字体对象.set_bold(bool(粗体))
                except Exception:
                    pass
            except Exception:
                字体对象 = pygame.font.Font(None, int(字号))

        self._字体缓存[key] = 字体对象
        return 字体对象

    def _取文本图(
        self,
        缓存种类: str,
        文本: str,
        字号: int,
        粗体: bool,
        颜色: Tuple[int, int, int],
        透明度255: int = 255,
        字间距: int = 0,
    ) -> Optional[pygame.Surface]:
        文本 = str(文本 or "")
        if not 文本:
            return None

        try:
            字间距 = int(字间距)
        except Exception:
            字间距 = 0
        字间距 = int(max(-64, min(96, 字间距)))

        颜色键 = (int(颜色[0]), int(颜色[1]), int(颜色[2]))
        缓存键 = (str(缓存种类), 文本, int(字号), bool(粗体), 颜色键, int(字间距))
        基础图 = self._文本图缓存.get(缓存键)
        if 基础图 is None:
            try:
                字体 = self._取字体(int(字号), bool(粗体))
                if int(字间距) == 0:
                    基础图 = 字体.render(文本, True, 颜色键).convert_alpha()
                else:
                    字形列表: List[pygame.Surface] = []
                    for ch in 文本:
                        try:
                            字形列表.append(
                                字体.render(ch, True, 颜色键).convert_alpha()
                            )
                        except Exception:
                            continue
                    if not 字形列表:
                        return None
                    max_h = int(max(1, max(int(g.get_height()) for g in 字形列表)))
                    x = 0
                    min_x = 0
                    max_x = 0
                    x位置: List[int] = []
                    for i, g in enumerate(字形列表):
                        x位置.append(int(x))
                        min_x = min(min_x, int(x))
                        max_x = max(max_x, int(x + int(g.get_width())))
                        if i != len(字形列表) - 1:
                            x += int(g.get_width()) + int(字间距)
                    总宽 = int(max(1, max_x - min_x))
                    基础图 = pygame.Surface((总宽, max_h), pygame.SRCALPHA)
                    基础图.fill((0, 0, 0, 0))
                    偏移x = int(-min_x)
                    for i, g in enumerate(字形列表):
                        y = int((max_h - int(g.get_height())) // 2)
                        基础图.blit(g, (int(x位置[i] + 偏移x), y))
            except Exception:
                return None
            if len(self._文本图缓存) >= 1024:
                self._文本图缓存.clear()
            self._文本图缓存[缓存键] = 基础图

        if int(透明度255) >= 255:
            return 基础图

        try:
            图 = 基础图.copy()
            图.set_alpha(int(max(0, min(255, 透明度255))))
            return 图
        except Exception:
            return 基础图

    def _取缩放图(
        self,
        缓存键: str,
        原图: pygame.Surface,
        目标宽: int,
        目标高: int,
    ) -> pygame.Surface:
        目标宽 = int(max(2, 目标宽))
        目标高 = int(max(2, 目标高))
        key = (str(缓存键), int(目标宽), int(目标高))
        if key in self._缩放图缓存:
            return self._缩放图缓存[key]

        图2 = pygame.transform.smoothscale(原图, (目标宽, 目标高)).convert_alpha()
        if len(self._缩放图缓存) >= 2048:
            self._缩放图缓存.clear()
        self._缩放图缓存[key] = 图2
        return 图2

    @staticmethod
    def _平滑步进(t: float) -> float:
        t = float(max(0.0, min(1.0, t)))
        return t * t * (3.0 - 2.0 * t)

    def _绘制血条头波浪(
        self,
        屏幕: pygame.Surface,
        目标矩形: pygame.Rect,
        控件定义: Dict[str, Any],
        上下文: Dict[str, Any],
    ):
        值键 = str(控件定义.get("值键") or "血量最终显示").strip()
        时间键 = str(控件定义.get("时间键") or "当前谱面秒").strip()
        玩家键 = str(控件定义.get("玩家键") or "玩家序号").strip()
        if 目标矩形.w <= 2 or 目标矩形.h <= 2:
            return

        try:
            值 = float(上下文.get(值键, 0.0) or 0.0)
        except Exception:
            值 = 0.0
        值 = float(max(0.0, min(1.0, 值)))
        if 值 <= 0.001:
            return

        try:
            当前秒 = float(上下文.get(时间键, 0.0) or 0.0)
        except Exception:
            当前秒 = 0.0
        try:
            玩家序号 = int(上下文.get(玩家键, 1) or 1)
        except Exception:
            玩家序号 = 1

        def _转rgba(
            值: Any, 默认: Tuple[int, int, int, int]
        ) -> Tuple[int, int, int, int]:
            if isinstance(值, (list, tuple)) and len(值) >= 4:
                try:
                    return (int(值[0]), int(值[1]), int(值[2]), int(值[3]))
                except Exception:
                    return 默认
            if isinstance(值, (list, tuple)) and len(值) >= 3:
                try:
                    return (int(值[0]), int(值[1]), int(值[2]), 默认[3])
                except Exception:
                    return 默认
            return 默认

        主色 = _转rgba(控件定义.get("颜色"), (179, 143, 179, 255))
        次色 = _转rgba(控件定义.get("次颜色"), (220, 158, 226, 180))
        高光色 = _转rgba(控件定义.get("高光颜色"), (255, 234, 255, 210))

        try:
            头宽系数 = float(控件定义.get("头宽系数", 0.82) or 0.82)
        except Exception:
            头宽系数 = 0.82
        try:
            速度 = float(控件定义.get("速度", 1.28) or 1.28)
        except Exception:
            速度 = 1.28
        try:
            幅度系数 = float(控件定义.get("幅度系数", 0.15) or 0.15)
        except Exception:
            幅度系数 = 0.15

        头区域 = pygame.Rect(目标矩形)
        try:
            基准w = int(max(2, _取数(上下文.get("血条填充区域w"), 目标矩形.w)))
            填充宽 = int(max(0, min(基准w, round(float(基准w) * 值))))
            缺失宽 = int(max(0, 基准w - 填充宽))
            if 玩家序号 == 2:
                头区域.x = int(目标矩形.x + 缺失宽)
            else:
                头区域.x = int(目标矩形.x - 缺失宽)
        except Exception:
            pass
        if 头区域.w <= 2 or 头区域.h <= 2:
            return

        临时层 = pygame.Surface((头区域.w, 头区域.h), pygame.SRCALPHA)
        振幅 = float(max(3.0, 头区域.w * max(0.14, min(0.34, 幅度系数 * 1.6))))
        前片厚度 = float(
            max(
                10.0,
                min(
                    float(头区域.w) * 0.54, float(头区域.w) * max(0.32, 头宽系数 * 0.46)
                ),
            )
        )
        呼吸相位 = float(当前秒) * max(0.1, 速度) * 0.85

        def _生成前缘曲线(前片厚度偏移: float = 0.0) -> List[Tuple[int, int]]:
            点列: List[Tuple[int, int]] = []
            for y in range(头区域.h + 1):
                t = float(y) / float(max(1, 头区域.h))
                s = float(t * 2.0 - 1.0)
                s形 = float((1.18 * s) - (0.92 * (s**3)))
                不规则 = float(
                    math.sin((t + 呼吸相位 * 0.08) * math.pi + 0.42) * 振幅 * 0.18
                    + math.sin((t * math.pi * 0.5) + 呼吸相位 * 0.33 + 0.9)
                    * 振幅
                    * 0.09
                )
                顶底收口 = 1.0 - 0.10 * math.cos(t * math.pi * 2.0)
                位移 = float((s形 * 振幅 + 不规则) * 顶底收口)
                if 玩家序号 == 2:
                    x曲线 = float(头区域.w) * 0.52 - 前片厚度 - 前片厚度偏移 + 位移
                else:
                    x曲线 = float(头区域.w) * 0.48 + 前片厚度偏移 + 位移
                x曲线 = float(max(1.0, min(float(头区域.w - 2), x曲线)))
                点列.append((int(round(x曲线)), int(y)))
            return 点列

        前缘曲线 = _生成前缘曲线(0.0)
        阴影曲线 = _生成前缘曲线(max(4.0, 前片厚度 * 0.14))

        try:
            if 玩家序号 == 2:
                主多边形 = [(0, 0), (0, 头区域.h)] + list(reversed(前缘曲线))
                阴影多边形 = [(0, 0), (0, 头区域.h)] + list(reversed(阴影曲线))
            else:
                主多边形 = list(前缘曲线) + [(头区域.w, 头区域.h), (头区域.w, 0)]
                阴影多边形 = list(阴影曲线) + [(头区域.w, 头区域.h), (头区域.w, 0)]
            if len(阴影多边形) >= 3:
                pygame.draw.polygon(临时层, 次色, 阴影多边形)
            if len(主多边形) >= 3:
                pygame.draw.polygon(临时层, 主色, 主多边形)
            if len(前缘曲线) >= 2:
                pygame.draw.lines(临时层, 高光色, False, 前缘曲线, width=2)
        except Exception:
            return

        屏幕.blit(临时层, 头区域.topleft)

    def _绘制暴走血条(
        self,
        屏幕: pygame.Surface,
        目标矩形: pygame.Rect,
        控件定义: Dict[str, Any],
        上下文: Dict[str, Any],
        皮肤包: Any,
    ):
        if 目标矩形.w <= 1 or 目标矩形.h <= 1:
            return

        启用键 = str(控件定义.get("启用键") or "血条暴走").strip()
        try:
            if 启用键 and (not bool(上下文.get(启用键, False))):
                return
        except Exception:
            return

        值键 = str(控件定义.get("值键") or "血量最终显示").strip()
        try:
            值 = float(上下文.get(值键, 0.0) or 0.0)
        except Exception:
            值 = 0.0
        if 值 < 0.999:
            return

        图源def = 控件定义.get("图源")
        原图 = self._解析图源(图源def, 上下文, 皮肤包)
        if 原图 is None:
            return

        try:
            时间键 = str(控件定义.get("时间键") or "当前谱面秒").strip()
        except Exception:
            时间键 = "当前谱面秒"
        try:
            当前秒 = float(上下文.get(时间键, 0.0) or 0.0)
        except Exception:
            当前秒 = 0.0
        try:
            速度 = float(_取数(控件定义.get("速度"), 150.0))
        except Exception:
            速度 = 150.0
        try:
            速度 = float(_取数(上下文.get("调试_暴走血条速度", 速度), 速度))
        except Exception:
            pass
        try:
            不透明度 = float(_取数(控件定义.get("不透明度"), 1.0))
        except Exception:
            不透明度 = 1.0
        不透明度 = float(max(0.0, min(1.0, 不透明度)))

        try:
            羽化像素 = int(_取数(控件定义.get("边缘羽化"), 8))
        except Exception:
            羽化像素 = 8
        try:
            羽化像素 = int(_取数(上下文.get("调试_暴走血条羽化", 羽化像素), 羽化像素))
        except Exception:
            pass
        羽化像素 = int(max(0, min(128, 羽化像素)))
        try:
            玩家序号 = int(上下文.get("玩家序号", 1) or 1)
        except Exception:
            玩家序号 = 1
        向右 = bool(玩家序号 != 2)

        try:
            拖影像素 = int(_取数(控件定义.get("拖影像素"), max(8, 羽化像素 * 2)))
        except Exception:
            拖影像素 = max(8, 羽化像素 * 2)
        拖影像素 = int(max(0, min(96, 拖影像素)))

        try:
            比例 = float(目标矩形.h) / float(max(1, 原图.get_height()))
            目标宽 = int(max(2, round(float(原图.get_width()) * 比例)))
            条纹图 = self._取缩放图(
                f"暴走血条:{玩家序号}",
                原图,
                目标宽,
                int(目标矩形.h),
            )
        except Exception:
            return

        条纹宽 = int(max(1, 条纹图.get_width()))
        if 条纹宽 <= 0:
            return

        缓存键 = (
            "暴走血条带",
            int(id(原图)),
            int(目标矩形.w),
            int(目标矩形.h),
            int(玩家序号),
            int(max(0, min(255, round(255.0 * 不透明度)))),
            int(拖影像素),
        )
        已缓存 = self._暴走血条缓存.get(缓存键)
        if isinstance(已缓存, tuple) and len(已缓存) == 2:
            重复条带, 条带步长 = 已缓存
        else:
            模糊条纹宽 = int(条纹宽 + max(0, 拖影像素))
            模糊条纹 = pygame.Surface((模糊条纹宽, int(目标矩形.h)), pygame.SRCALPHA)
            采样列表 = (
                ((1.00, 0.00), (0.56, 0.36), (0.26, 0.68), (0.12, 1.00))
                if 向右
                else ((1.00, 1.00), (0.56, 0.64), (0.26, 0.32), (0.12, 0.00))
            )
            for 透明倍率, 偏移比例 in 采样列表:
                try:
                    样本 = 条纹图.copy()
                    样本.set_alpha(
                        int(max(0, min(255, round(255.0 * float(透明倍率)))))
                    )
                except Exception:
                    样本 = 条纹图
                偏移x = int(round(float(拖影像素) * float(偏移比例)))
                模糊条纹.blit(样本, (int(偏移x), 0))

            if 羽化像素 > 0:
                try:
                    羽化罩 = self._取边缘羽化遮罩(
                        int(模糊条纹.get_width()),
                        int(模糊条纹.get_height()),
                        羽化像素,
                    )
                    模糊条纹.blit(羽化罩, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                except Exception:
                    pass

            if 不透明度 < 0.999:
                try:
                    模糊条纹.set_alpha(
                        int(max(0, min(255, round(255.0 * 不透明度))))
                    )
                except Exception:
                    pass

            条带步长 = int(max(1, 条纹宽))
            条带宽 = int(max(目标矩形.w + 条带步长 * 2, 模糊条纹.get_width() * 3))
            重复条带 = pygame.Surface((条带宽, int(目标矩形.h)), pygame.SRCALPHA)
            x = 0
            while x < 条带宽:
                重复条带.blit(模糊条纹, (int(x), 0))
                x += int(条带步长)
            if len(self._暴走血条缓存) >= 128:
                self._暴走血条缓存.clear()
            self._暴走血条缓存[缓存键] = (重复条带, 条带步长)

        偏移 = int((max(0.0, float(当前秒)) * float(速度)) % float(max(1, 条带步长)))
        采样x = int(max(0, (条带步长 - 偏移) if 向右 else 偏移))
        采样x = int(min(采样x, max(0, 重复条带.get_width() - 目标矩形.w)))
        屏幕.blit(
            重复条带,
            目标矩形.topleft,
            area=pygame.Rect(int(采样x), 0, int(目标矩形.w), int(目标矩形.h)),
        )

    def _绘制程序化血条(
        self,
        屏幕: pygame.Surface,
        内矩形: pygame.Rect,
        填充宽: int,
        控件定义: Dict[str, Any],
        上下文: Dict[str, Any],
        最终透明: float,
        皮肤包: Any,
    ) -> bool:
        if 内矩形.w <= 1 or 内矩形.h <= 1 or 填充宽 <= 0:
            return False

        程序化 = 控件定义.get("程序化") or {}
        动态位移 = 控件定义.get("动态位移") or {}

        try:
            时间键 = str(
                (程序化.get("时间键") or 动态位移.get("时间键") or "当前谱面秒")
            ).strip()
        except Exception:
            时间键 = "当前谱面秒"
        try:
            当前秒 = float(上下文.get(时间键, 0.0) or 0.0)
        except Exception:
            当前秒 = 0.0

        try:
            玩家序号 = int(_取数(上下文.get("玩家序号", 1), 1))
        except Exception:
            玩家序号 = 1
        try:
            当前血量值 = float(_取数(上下文.get("血量最终显示", 0.0), 0.0))
        except Exception:
            当前血量值 = 0.0

        def _取rgba(
            值: Any, 默认: Tuple[int, int, int, int]
        ) -> Tuple[int, int, int, int]:
            if isinstance(值, (list, tuple)) and len(值) >= 4:
                try:
                    return (int(值[0]), int(值[1]), int(值[2]), int(值[3]))
                except Exception:
                    return 默认
            if isinstance(值, (list, tuple)) and len(值) >= 3:
                try:
                    return (int(值[0]), int(值[1]), int(值[2]), 默认[3])
                except Exception:
                    return 默认
            return 默认

        if 玩家序号 == 2:
            主色 = _取rgba(程序化.get("颜色_p2"), (230, 83, 229, 178))
        else:
            主色 = _取rgba(程序化.get("颜色"), (230, 83, 229, 178))
        try:
            调试颜色 = 上下文.get("调试_血条颜色", None)
            if isinstance(调试颜色, (list, tuple)) and len(调试颜色) >= 3:
                主色 = _取rgba(调试颜色, 主色)
        except Exception:
            pass
        try:
            亮度 = float(_取数(上下文.get("调试_血条亮度"), 1.0))
        except Exception:
            亮度 = 1.0
        try:
            不透明度 = float(
                _取数(上下文.get("调试_血条不透明度"), float(主色[3]) / 255.0)
            )
        except Exception:
            不透明度 = float(主色[3]) / 255.0
        主色 = (
            int(max(0, min(255, round(float(主色[0]) * max(0.0, 亮度))))),
            int(max(0, min(255, round(float(主色[1]) * max(0.0, 亮度))))),
            int(max(0, min(255, round(float(主色[2]) * max(0.0, 亮度))))),
            int(max(0, min(255, round(max(0.0, min(1.0, 不透明度)) * 255.0)))),
        )

        try:
            x振幅 = float(_取数(动态位移.get("x振幅"), 5.0))
        except Exception:
            x振幅 = 5.0
        try:
            位移速度 = float(_取数(动态位移.get("速度"), 0.9))
        except Exception:
            位移速度 = 0.9
        try:
            x振幅 = float(_取数(上下文.get("调试_血条晃荡幅度"), x振幅))
        except Exception:
            pass
        try:
            位移速度 = float(_取数(上下文.get("调试_血条晃荡速度"), 位移速度))
        except Exception:
            pass

        if float(当前血量值) >= 0.999:
            x振幅 = 0.0

        动态偏移x = (
            int(
                round(
                    math.sin(float(当前秒) * float(位移速度) * math.tau) * float(x振幅)
                )
            )
            if abs(x振幅) > 0.01 and abs(位移速度) > 0.01
            else 0
        )

        图层 = pygame.Surface((内矩形.w, 内矩形.h), pygame.SRCALPHA)
        左边 = int(round(float(动态偏移x)))
        条形rect = pygame.Rect(左边, 0, int(填充宽), int(内矩形.h))
        可视rect = 条形rect.clip(pygame.Rect(0, 0, 内矩形.w, 内矩形.h))
        if 可视rect.w <= 0 or 可视rect.h <= 0:
            return False

        try:
            pygame.draw.rect(
                图层,
                主色,
                可视rect,
                border_radius=max(0, min(10, int(内矩形.h * 0.18))),
            )
        except Exception:
            return False

        覆盖def = 控件定义.get("贴图覆盖") or 控件定义.get("填充")
        覆盖图 = self._解析图源(覆盖def, 上下文, 皮肤包)
        if 覆盖图 is not None:
            try:
                扩展宽 = int(max(内矩形.w, 内矩形.w + abs(int(round(x振幅))) * 2))
                覆盖缩放图 = self._取缩放图(
                    f"程序化血条覆盖:{id(覆盖图)}",
                    覆盖图,
                    扩展宽,
                    int(内矩形.h),
                )
                覆盖层 = pygame.Surface((内矩形.w, 内矩形.h), pygame.SRCALPHA)
                起贴x = int(-abs(int(round(x振幅))) + 动态偏移x)
                覆盖层.blit(覆盖缩放图, (int(起贴x), 0))
                遮罩层 = pygame.Surface((内矩形.w, 内矩形.h), pygame.SRCALPHA)
                pygame.draw.rect(
                    遮罩层,
                    (255, 255, 255, 255),
                    可视rect,
                    border_radius=max(0, min(10, int(内矩形.h * 0.18))),
                )
                覆盖层.blit(遮罩层, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                图层.blit(覆盖层, (0, 0))
            except Exception:
                pass

        if 当前血量值 >= 0.999 and 可视rect.w > 2 and 可视rect.h > 2:
            try:
                发光层 = pygame.Surface((内矩形.w + 16, 内矩形.h + 16), pygame.SRCALPHA)
                发光rect = pygame.Rect(
                    int(可视rect.x + 8),
                    int(可视rect.y + 8),
                    int(可视rect.w),
                    int(可视rect.h),
                )
                for 膨胀, alpha in ((12, 22), (8, 34), (4, 48)):
                    pygame.draw.rect(
                        发光层,
                        (主色[0], 主色[1], 主色[2], alpha),
                        发光rect.inflate(膨胀, 膨胀),
                        border_radius=max(0, min(18, int(内矩形.h * 0.28) + 膨胀 // 2)),
                    )
                图层.blit(发光层, (-8, -8))
            except Exception:
                pass

        if 最终透明 < 0.999:
            try:
                图层.set_alpha(int(255 * 最终透明))
            except Exception:
                pass
        屏幕.blit(图层, 内矩形.topleft)
        return True

    def _取圆形遮罩(self, 宽: int, 高: int) -> pygame.Surface:
        键 = (int(宽), int(高))
        if 键 in self._圆罩缓存:
            return self._圆罩缓存[键]
        遮罩 = pygame.Surface((max(2, 宽), max(2, 高)), pygame.SRCALPHA)
        遮罩.fill((0, 0, 0, 0))
        pygame.draw.circle(
            遮罩, (255, 255, 255, 255), (宽 // 2, 高 // 2), min(宽, 高) // 2
        )
        self._圆罩缓存[键] = 遮罩
        return 遮罩

    def _取边缘羽化遮罩(self, 宽: int, 高: int, 羽化像素: int) -> pygame.Surface:
        w = int(max(2, 宽))
        h = int(max(2, 高))
        f = int(max(0, 羽化像素))
        if f <= 0:
            罩 = pygame.Surface((w, h), pygame.SRCALPHA)
            罩.fill((255, 255, 255, 255))
            return 罩
        f = int(min(f, max(1, w // 2), max(1, h // 2)))
        键 = (w, h, f)
        if 键 in self._羽化罩缓存:
            return self._羽化罩缓存[键]

        罩 = pygame.Surface((w, h), pygame.SRCALPHA)
        罩.fill((255, 255, 255, 255))
        try:
            for i in range(f):
                a = int(max(0, min(255, round(255.0 * float(i + 1) / float(f + 1)))))
                c = (a, a, a, a)
                pygame.draw.line(罩, c, (i, 0), (i, h - 1))
                pygame.draw.line(罩, c, (w - 1 - i, 0), (w - 1 - i, h - 1))
                pygame.draw.line(罩, c, (0, i), (w - 1, i))
                pygame.draw.line(罩, c, (0, h - 1 - i), (w - 1, h - 1 - i))
        except Exception:
            pass
        self._羽化罩缓存[键] = 罩
        return 罩

    def _绘制单控件(
        self,
        屏幕: pygame.Surface,
        项: Dict[str, Any],
        上下文: Dict[str, Any],
        皮肤包: Any,
    ):
        控件定义 = 项["def"]
        外矩形: pygame.Rect = 项["rect"]
        类型 = str(控件定义.get("类型") or "")

        if 类型 == "组":
            return

        # ---------- 项级总透明（上游可能已经预计算） ----------
        try:
            总透明 = float(项.get("总透明", 1.0))
        except Exception:
            总透明 = 1.0
        总透明 = float(max(0.0, min(1.0, 总透明)))

        # ---------- 父级缩放键/透明键叠加（你最开始漏掉的） ----------
        额外缩放 = 1.0
        额外透明 = 1.0
        父id = str(控件定义.get("父") or "")
        while 父id:
            父def = self._控件索引.get(父id)
            if not 父def:
                break

            缩放键 = str(父def.get("缩放键") or "")
            透明键 = str(父def.get("透明键") or "")

            if 缩放键:
                try:
                    额外缩放 *= float(上下文.get(缩放键, 1.0))
                except Exception:
                    pass

            if 透明键:
                try:
                    额外透明 *= float(上下文.get(透明键, 1.0))
                except Exception:
                    pass

            父id = str(父def.get("父") or "")

        最终透明 = float(max(0.0, min(1.0, 总透明 * 额外透明)))
        if 最终透明 <= 0.001:
            return

        # ---------- 内容矩形（支持边距） ----------
        内容矩形 = self._按边距取内容矩形(外矩形, 控件定义, 项)

        # ---------- 额外缩放：围绕中心缩放矩形 ----------
        def _按中心缩放矩形(矩形: pygame.Rect, 缩放: float) -> pygame.Rect:
            try:
                缩放 = float(缩放)
            except Exception:
                缩放 = 1.0
            if abs(缩放 - 1.0) < 1e-6:
                return pygame.Rect(矩形)

            新宽 = int(max(1, round(float(矩形.w) * 缩放)))
            新高 = int(max(1, round(float(矩形.h) * 缩放)))
            cx, cy = int(矩形.centerx), int(矩形.centery)
            return pygame.Rect(cx - 新宽 // 2, cy - 新高 // 2, 新宽, 新高)

        目标矩形 = _按中心缩放矩形(内容矩形, 额外缩放)

        # =========================
        # ✅ 矩形（轨道背景）
        # =========================
        if 类型 == "矩形":
            颜色def = 控件定义.get("颜色", [255, 255, 255, 80])
            圆角 = int(_取数(控件定义.get("圆角"), 0))

            r, g, b, a = 255, 255, 255, 255
            if isinstance(颜色def, (list, tuple)) and len(颜色def) >= 3:
                try:
                    r = int(颜色def[0])
                    g = int(颜色def[1])
                    b = int(颜色def[2])
                except Exception:
                    r, g, b = 255, 255, 255
                if len(颜色def) >= 4:
                    try:
                        a = int(颜色def[3])
                    except Exception:
                        a = 255

            最终a = int(max(0, min(255, int(float(a) * 最终透明))))
            if 目标矩形.w <= 1 or 目标矩形.h <= 1 or 最终a <= 0:
                return

            try:
                临时层 = pygame.Surface((目标矩形.w, 目标矩形.h), pygame.SRCALPHA)
                临时层.fill((0, 0, 0, 0))
                pygame.draw.rect(
                    临时层,
                    (r, g, b, 最终a),
                    pygame.Rect(0, 0, 目标矩形.w, 目标矩形.h),
                    border_radius=max(0, 圆角),
                )
                屏幕.blit(临时层, (目标矩形.x, 目标矩形.y))
            except Exception:
                pass
            return

        # =========================
        # ✅ 圆环频谱
        # =========================
        if 类型 == "圆环频谱":
            启用键 = str(控件定义.get("启用键") or "圆环频谱_启用")
            try:
                if 启用键 and (not bool(上下文.get(启用键, True))):
                    return
            except Exception:
                pass

            时间键 = str(控件定义.get("时间键") or "当前谱面秒")
            try:
                当前播放秒 = float(上下文.get(时间键, 0.0) or 0.0)
            except Exception:
                try:
                    当前播放秒 = float(上下文.get("调试_时间秒", 0.0) or 0.0)
                except Exception:
                    当前播放秒 = 0.0
            当前播放秒 = float(max(0.0, 当前播放秒))

            频谱对象 = 上下文.get("圆环频谱对象", None)
            if 频谱对象 is None or (not hasattr(频谱对象, "更新并绘制")):
                try:
                    if not hasattr(self, "_圆环频谱_调试对象"):
                        from ui.圆环频谱叠加 import 圆环频谱舞台装饰

                        self._圆环频谱_调试对象 = 圆环频谱舞台装饰()
                    频谱对象 = getattr(self, "_圆环频谱_调试对象", None)
                except Exception:
                    频谱对象 = None

            if 频谱对象 is None or (not hasattr(频谱对象, "更新并绘制")):
                return

            try:
                启用旋转 = bool(上下文.get("调试_圆环频谱_启用旋转", True))
                变化落差 = float(_取数(上下文.get("调试_圆环频谱_变化落差"), 1.0))
                线条数量 = int(_取数(上下文.get("调试_圆环频谱_线条数量"), 200))
                线条粗细 = int(_取数(上下文.get("调试_圆环频谱_线条粗细"), 2))
                线条间隔 = int(_取数(上下文.get("调试_圆环频谱_线条间隔"), 1))
                if hasattr(频谱对象, "设置调试频谱参数"):
                    getattr(频谱对象, "设置调试频谱参数")(
                        启用旋转=bool(启用旋转),
                        变化落差=float(变化落差),
                        线条数量=int(线条数量),
                        线条粗细=int(线条粗细),
                        线条间隔=int(线条间隔),
                    )

                形状文件 = str(控件定义.get("形状文件") or "").strip()
                if hasattr(频谱对象, "设置贴边形状文件"):
                    getattr(频谱对象, "设置贴边形状文件")(形状文件)

                形状旋转时间键 = str(
                    控件定义.get("形状旋转时间键") or 时间键 or "当前谱面秒"
                ).strip()
                try:
                    形状时间秒 = float(
                        上下文.get(形状旋转时间键, 当前播放秒) or 当前播放秒
                    )
                except Exception:
                    形状时间秒 = float(当前播放秒)
                try:
                    形状旋转速度 = float(_取数(控件定义.get("形状旋转速度"), 0.0))
                except Exception:
                    形状旋转速度 = 0.0
                形状旋转速度键 = str(控件定义.get("形状旋转速度键") or "").strip()
                if 形状旋转速度键:
                    try:
                        形状旋转速度 = float(
                            _取数(上下文.get(形状旋转速度键), 形状旋转速度)
                        )
                    except Exception:
                        pass
                else:
                    try:
                        if "调试_圆环频谱_背景板旋转速度" in 上下文:
                            形状旋转速度 = float(
                                _取数(
                                    上下文.get("调试_圆环频谱_背景板旋转速度"),
                                    形状旋转速度,
                                )
                            )
                    except Exception:
                        pass
                if hasattr(频谱对象, "设置贴边形状旋转角度"):
                    getattr(频谱对象, "设置贴边形状旋转角度")(
                        math.radians(float(形状时间秒) * float(形状旋转速度))
                    )

                getattr(频谱对象, "更新并绘制")(
                    屏幕=屏幕,
                    目标矩形=目标矩形,
                    当前播放秒=float(当前播放秒),
                )
            except Exception:
                pass
            return

        # =========================
        # ✅ 序列帧（用于特效层/调试循环）
        # =========================
        if 类型 == "序列帧":
            if bool(上下文.get("性能模式", False)) and bool(
                控件定义.get("性能模式隐藏", False)
            ):
                return

            分包 = str(控件定义.get("分包") or "key_effect").strip()
            图集目录 = str(控件定义.get("图集目录") or "").strip()
            前缀 = str(控件定义.get("前缀") or "").strip()
            帧数 = int(_取数(控件定义.get("帧数"), 18))
            帧率 = float(_取数(控件定义.get("fps"), 60.0))
            帧率键 = str(控件定义.get("fps键") or "").strip()
            循环 = bool(控件定义.get("循环", True))
            混合 = str(控件定义.get("混合") or "add").lower()
            播放周期秒 = float(_取数(控件定义.get("播放周期秒"), 0.0))
            等比 = str(控件定义.get("等比") or "stretch").lower()

            if 帧率键:
                try:
                    帧率 = float(_取数(上下文.get(帧率键), 帧率))
                except Exception:
                    pass

            是否翻转 = bool(控件定义.get("水平翻转", False))
            翻转键 = str(控件定义.get("水平翻转键") or "").strip()
            if 翻转键:
                try:
                    是否翻转 = bool(上下文.get(翻转键, 是否翻转))
                except Exception:
                    pass

            时间键 = str(控件定义.get("时间键") or "调试_时间秒").strip()
            try:
                时间秒 = float(上下文.get(时间键, 0.0) or 0.0)
            except Exception:
                try:
                    时间秒 = float(pygame.time.get_ticks()) / 1000.0
                except Exception:
                    时间秒 = 0.0

            if (not 前缀) or 帧数 <= 0 or 帧率 <= 0:
                return

            if 播放周期秒 > 0.0:
                周期内秒 = float(时间秒) % float(max(0.001, 播放周期秒))
                if 循环:
                    时间秒 = 周期内秒
                else:
                    动画时长秒 = float(帧数) / float(max(1.0, 帧率))
                    if 周期内秒 > 动画时长秒:
                        return
                    时间秒 = 周期内秒

            帧号 = (
                int((时间秒 * 帧率) % float(帧数))
                if 循环
                else int(min(帧数 - 1, max(0, int(时间秒 * 帧率))))
            )

            文件名 = f"{前缀}_{帧号:04d}.png"
            if 图集目录:
                原图 = self._取外部图集帧(图集目录, 文件名)
            else:
                原图 = self._取皮肤帧(皮肤包, 分包, 文件名)
            if 原图 is None:
                return

            try:
                if 是否翻转:
                    原图 = pygame.transform.flip(原图, True, False)
            except Exception:
                pass

            目标w = int(max(2, 目标矩形.w))
            目标h = int(max(2, 目标矩形.h))
            try:
                原宽 = int(max(1, 原图.get_width()))
                原高 = int(max(1, 原图.get_height()))
                if 等比 == "contain":
                    比例 = min(float(目标w) / float(原宽), float(目标h) / float(原高))
                    新宽 = int(max(2, round(float(原宽) * 比例)))
                    新高 = int(max(2, round(float(原高) * 比例)))
                    图2 = self._取缩放图(
                        f"序列帧:{图集目录 or 分包}:{文件名}:contain",
                        原图,
                        新宽,
                        新高,
                    )
                    绘制x = int(目标矩形.centerx - 图2.get_width() // 2)
                    绘制y = int(目标矩形.centery - 图2.get_height() // 2)
                else:
                    图2 = self._取缩放图(
                        f"序列帧:{图集目录 or 分包}:{文件名}:stretch",
                        原图,
                        目标w,
                        目标h,
                    )
                    绘制x = int(目标矩形.x)
                    绘制y = int(目标矩形.y)
                if 最终透明 < 0.999:
                    图2 = 图2.copy()
                    图2.set_alpha(int(255 * 最终透明))
            except Exception:
                return

            if 混合 == "add":
                屏幕.blit(图2, (绘制x, 绘制y), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                屏幕.blit(图2, (绘制x, 绘制y))
            return

        # =========================
        # ✅ 精灵数字串（x + 数字）
        # =========================
        if 类型 == "精灵数字串":
            分包 = str(控件定义.get("分包") or "number").strip()
            值键 = str(控件定义.get("值键") or "").strip()
            前缀帧 = str(控件定义.get("前缀帧") or "").strip()
            数字帧格式 = str(控件定义.get("数字帧格式") or "").strip()
            对齐 = str(控件定义.get("对齐") or "left").lower()
            间距 = float(_取数(控件定义.get("间距"), 0.0))

            if (not 值键) or (not 数字帧格式):
                return

            try:
                数值 = int(上下文.get(值键, 0) or 0)
            except Exception:
                数值 = 0
            数值 = int(max(0, 数值))

            帧名列表: List[str] = []
            if 前缀帧:
                帧名列表.append(前缀帧)
            for 字符 in str(数值):
                if 字符.isdigit():
                    帧名列表.append(数字帧格式.replace("{d}", 字符))

            原图列表: List[pygame.Surface] = []
            for 帧名 in 帧名列表:
                图 = self._取皮肤帧(皮肤包, 分包, str(帧名))
                if 图 is None:
                    原图列表 = []
                    break
                原图列表.append(图)

            if not 原图列表:
                # 缺帧兜底：字体画
                try:
                    文本 = f"x{数值}"
                    字号 = int(max(10, min(120, int(目标矩形.h * 0.85))))
                    文图 = self._取文本图(
                        "精灵数字串兜底",
                        文本,
                        字号,
                        True,
                        (255, 255, 255),
                        int(255 * 最终透明),
                    )
                    if 文图 is None:
                        return

                    if 对齐 == "right":
                        x = 目标矩形.right - 文图.get_width()
                    elif 对齐 == "center":
                        x = 目标矩形.centerx - 文图.get_width() // 2
                    else:
                        x = 目标矩形.x
                    y = 目标矩形.centery - 文图.get_height() // 2
                    屏幕.blit(文图, (int(x), int(y)))
                except Exception:
                    pass
                return

            目标高 = int(max(2, 目标矩形.h))
            实际间距 = int(max(0, int(round(间距 * max(0.1, 额外缩放)))))

            缩放后列表: List[pygame.Surface] = []
            总宽 = 0
            for 索引, 原图 in enumerate(原图列表):
                原宽, 原高 = int(原图.get_width()), int(原图.get_height())
                if 原宽 <= 0 or 原高 <= 0:
                    continue
                新宽 = int(max(2, int(float(原宽) * (float(目标高) / float(原高)))))
                图2 = self._取缩放图(
                    f"精灵数字串:{分包}:{帧名列表[min(索引, len(帧名列表) - 1)]}",
                    原图,
                    新宽,
                    目标高,
                )
                if 最终透明 < 0.999:
                    图2 = 图2.copy()
                    图2.set_alpha(int(255 * 最终透明))
                缩放后列表.append(图2)
                总宽 += 图2.get_width()

            if not 缩放后列表:
                return

            总宽 += 实际间距 * (len(缩放后列表) - 1)
            if 对齐 == "right":
                起x = 目标矩形.right - 总宽
            elif 对齐 == "center":
                起x = 目标矩形.centerx - (总宽 // 2)
            else:
                起x = 目标矩形.x

            y = 目标矩形.centery - (目标高 // 2)
            当前x = int(起x)
            for 图2 in 缩放后列表:
                屏幕.blit(图2, (int(当前x), int(y)))
                当前x += int(图2.get_width() + 实际间距)
            return

        # =========================
        # ✅ 图片（混合add + 水平翻转键 + 圆形遮罩）
        # =========================
        if 类型 == "图片":
            原图 = self._解析图源(控件定义.get("图源"), 上下文, 皮肤包)
            if 原图 is None:
                return

            等比 = str(控件定义.get("等比") or "stretch").lower()
            遮罩 = str(控件定义.get("遮罩") or "").lower()
            混合 = str(控件定义.get("混合") or "").lower()
            旋转度数 = float(_取数(控件定义.get("旋转"), 0.0))
            旋转速度 = float(_取数(控件定义.get("旋转速度"), 0.0))
            旋转速度键 = str(控件定义.get("旋转速度键") or "").strip()
            旋转时间键 = str(控件定义.get("旋转时间键") or "当前谱面秒").strip()
            if bool(上下文.get("性能模式", False)) and bool(
                控件定义.get("性能模式禁用旋转", False)
            ):
                旋转度数 = 0.0
                旋转速度 = 0.0
            if 旋转速度键:
                try:
                    旋转速度 = float(_取数(上下文.get(旋转速度键), 旋转速度))
                except Exception:
                    pass

            是否翻转 = bool(控件定义.get("水平翻转", False))
            翻转键 = str(控件定义.get("水平翻转键") or "").strip()
            if 翻转键:
                try:
                    是否翻转 = bool(上下文.get(翻转键, 是否翻转))
                except Exception:
                    pass

            图源 = 原图
            try:
                if 是否翻转:
                    图源 = pygame.transform.flip(图源, True, False)
            except Exception:
                图源 = 原图

            目标w = int(max(2, 目标矩形.w))
            目标h = int(max(2, 目标矩形.h))

            if 等比 == "contain":
                原宽, 原高 = int(图源.get_width()), int(图源.get_height())
                if 原宽 <= 0 or 原高 <= 0:
                    return
                比例 = min(float(目标w) / float(原宽), float(目标h) / float(原高))
                新宽 = int(max(2, 原宽 * 比例))
                新高 = int(max(2, 原高 * 比例))
                图2 = self._取缩放图(f"图片:contain:{id(图源)}", 图源, 新宽, 新高)
                x = 目标矩形.centerx - 新宽 // 2
                y = 目标矩形.centery - 新高 // 2
            else:
                图2 = self._取缩放图(f"图片:stretch:{id(图源)}", 图源, 目标w, 目标h)
                x = 目标矩形.x
                y = 目标矩形.y

            if 遮罩 == "circle":
                罩 = self._取圆形遮罩(图2.get_width(), 图2.get_height())
                图2.blit(罩, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            if 最终透明 < 0.999:
                try:
                    图2 = 图2.copy()
                    图2.set_alpha(int(255 * 最终透明))
                except Exception:
                    pass

            if abs(float(旋转速度)) > 0.001:
                try:
                    当前时间 = float(上下文.get(旋转时间键, 0.0) or 0.0)
                except Exception:
                    try:
                        当前时间 = float(pygame.time.get_ticks()) / 1000.0
                    except Exception:
                        当前时间 = 0.0
                旋转度数 += float(旋转速度) * float(当前时间)

            if abs(float(旋转度数)) > 0.001:
                try:
                    图2 = pygame.transform.rotozoom(
                        图2, -float(旋转度数), 1.0
                    ).convert_alpha()
                    x = int(
                        round(float(目标矩形.centerx) - float(图2.get_width()) * 0.5)
                    )
                    y = int(
                        round(float(目标矩形.centery) - float(图2.get_height()) * 0.5)
                    )
                except Exception:
                    pass

            if 混合 == "add":
                屏幕.blit(图2, (int(x), int(y)), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                屏幕.blit(图2, (int(x), int(y)))
            return

        # =========================
        # ✅ 文本
        # =========================
        if 类型 == "文本":
            文本模板 = str(控件定义.get("文本") or "")
            文本 = _格式化文本(文本模板, 上下文)

            字号 = int(_取数(控件定义.get("字号"), 24))
            粗体 = bool(控件定义.get("粗体", False))
            颜色 = _解析颜色(控件定义.get("颜色"), (255, 255, 255))
            对齐 = str(控件定义.get("对齐") or "left").lower()
            短文本居中 = bool(控件定义.get("短文本居中", False))
            滚动 = 控件定义.get("滚动") or {}
            字间距 = int(_取数(控件定义.get("字间距"), 0))

            文本缩放 = 1.0
            try:
                if 内容矩形.h > 0:
                    文本缩放 = float(目标矩形.h) / float(max(1, 内容矩形.h))
            except Exception:
                文本缩放 = 1.0
            实际字号 = int(max(6, round(float(字号) * float(max(0.1, 文本缩放)))))

            文图 = self._取文本图(
                "文本主层",
                文本,
                实际字号,
                粗体,
                颜色,
                int(255 * 最终透明),
                int(字间距),
            )
            if 文图 is None:
                return

            发光图 = None
            发光 = 控件定义.get("发光")
            发光色 = (255, 0, 255)
            发光半径 = 0
            if isinstance(发光, dict):
                发光色 = _解析颜色(发光.get("颜色"), (255, 0, 255))
                发光半径 = int(_取数(发光.get("半径"), 2))
                if 发光半径 > 0:
                    发光图 = self._取文本图(
                        "文本发光",
                        文本,
                        实际字号,
                        粗体,
                        发光色,
                        int(255 * 最终透明),
                        int(字间距),
                    )

            描边图 = None
            描边 = 控件定义.get("描边")
            描边色 = (255, 105, 210)
            描边半径 = 0
            if isinstance(描边, dict):
                描边色 = _解析颜色(描边.get("颜色"), (255, 105, 210))
                描边半径 = int(_取数(描边.get("半径"), 1))
                if 描边半径 > 0:
                    描边图 = self._取文本图(
                        "文本描边",
                        文本,
                        实际字号,
                        粗体,
                        描边色,
                        int(255 * 最终透明),
                        int(字间距),
                    )

            if 对齐 == "right":
                x = 目标矩形.right - 文图.get_width()
            elif 对齐 == "center":
                x = 目标矩形.centerx - 文图.get_width() // 2
            else:
                x = 目标矩形.x
            if 短文本居中 and 文图.get_width() <= 目标矩形.w:
                x = 目标矩形.centerx - 文图.get_width() // 2
            y = 目标矩形.y

            启用滚动 = bool(isinstance(滚动, dict) and 滚动.get("启用", False))
            if bool(上下文.get("性能模式", False)) and bool(
                控件定义.get("性能模式禁用滚动", False)
            ):
                启用滚动 = False
            if 启用滚动 and 文图.get_width() > 目标矩形.w:
                try:
                    时间键 = str(滚动.get("时间键") or "调试_时间秒").strip()
                    try:
                        当前秒 = float(上下文.get(时间键, 0.0) or 0.0)
                    except Exception:
                        当前秒 = float(pygame.time.get_ticks()) / 1000.0

                    速度 = float(_取数(滚动.get("速度"), 80.0))
                    间隔 = int(max(12, _取数(滚动.get("间隔"), 48.0)))
                    循环宽 = int(max(1, 文图.get_width() + 间隔))
                    偏移 = int((当前秒 * max(1.0, 速度)) % 循环宽)

                    条带 = pygame.Surface(
                        (max(2, 目标矩形.w), max(2, 目标矩形.h)), pygame.SRCALPHA
                    )
                    文本y = int(
                        max(0, (条带.get_height() - int(文图.get_height())) // 2)
                    )

                    def _画一份(底图: pygame.Surface, 左x: int):
                        if 描边图 is not None and 描边半径 > 0:
                            for dx in range(-描边半径, 描边半径 + 1):
                                for dy in range(-描边半径, 描边半径 + 1):
                                    if dx == 0 and dy == 0:
                                        continue
                                    条带.blit(
                                        描边图,
                                        (int(左x + dx), int(文本y + dy)),
                                    )
                        if 发光图 is not None and 发光半径 > 0:
                            for dx in range(-发光半径, 发光半径 + 1):
                                for dy in range(-发光半径, 发光半径 + 1):
                                    if dx == 0 and dy == 0:
                                        continue
                                    条带.blit(
                                        底图,
                                        (int(左x + dx), int(文本y + dy)),
                                    )
                        条带.blit(文图, (int(左x), int(文本y)))

                    _画一份(发光图 if 发光图 is not None else 文图, -偏移)
                    _画一份(发光图 if 发光图 is not None else 文图, -偏移 + 循环宽)
                    屏幕.blit(条带, (int(目标矩形.x), int(目标矩形.y)))
                except Exception:
                    屏幕.blit(文图, (int(x), int(y)))
                return

            if 描边图 is not None and 描边半径 > 0:
                try:
                    for dx in range(-描边半径, 描边半径 + 1):
                        for dy in range(-描边半径, 描边半径 + 1):
                            if dx == 0 and dy == 0:
                                continue
                            屏幕.blit(描边图, (int(x + dx), int(y + dy)))
                except Exception:
                    pass

            if 发光图 is not None and 发光半径 > 0:
                try:
                    for dx in range(-发光半径, 发光半径 + 1):
                        for dy in range(-发光半径, 发光半径 + 1):
                            if dx == 0 and dy == 0:
                                continue
                            屏幕.blit(发光图, (int(x + dx), int(y + dy)))
                except Exception:
                    pass

            屏幕.blit(文图, (int(x), int(y)))
            return

        # =========================
        # ✅ 血条头波浪
        # =========================
        if 类型 == "血条头波浪":
            try:
                self._绘制血条头波浪(屏幕, 目标矩形, 控件定义, 上下文)
            except Exception:
                pass
            return

        # =========================
        # ✅ 暴走血条
        # =========================
        if 类型 == "暴走血条":
            try:
                self._绘制暴走血条(屏幕, 目标矩形, 控件定义, 上下文, 皮肤包)
            except Exception:
                pass
            return

        # =========================
        # ✅ 进度条（血条）
        # =========================
        if 类型 == "进度条":
            值键 = str(控件定义.get("值键") or "")
            try:
                值 = float(上下文.get(值键, 0.0))
            except Exception:
                值 = 0.0
            值 = float(max(0.0, min(1.0, 值)))

            内边距 = 控件定义.get("内边距") or {}
            try:
                全局缩放 = float(项.get("全局缩放", 1.0))
            except Exception:
                全局缩放 = 1.0
            try:
                总缩放 = float(项.get("总缩放", 1.0))
            except Exception:
                总缩放 = 1.0
            边距缩放 = float(max(0.01, 全局缩放 * 总缩放))
            l = int(round(_取数(内边距.get("l"), 0) * 边距缩放))
            t = int(round(_取数(内边距.get("t"), 0) * 边距缩放))
            r = int(round(_取数(内边距.get("r"), 0) * 边距缩放))
            b = int(round(_取数(内边距.get("b"), 0) * 边距缩放))

            内矩形 = pygame.Rect(
                int(目标矩形.x + l),
                int(目标矩形.y + t),
                int(max(2, 目标矩形.w - l - r)),
                int(max(2, 目标矩形.h - t - b)),
            )

            填充宽 = int(max(0, min(内矩形.w, int(float(内矩形.w) * 值))))
            if 填充宽 <= 0:
                return

            if str(控件定义.get("绘制模式") or "").strip() == "程序化血条":
                try:
                    if self._绘制程序化血条(
                        屏幕, 内矩形, 填充宽, 控件定义, 上下文, 最终透明, 皮肤包
                    ):
                        return
                except Exception:
                    pass

            填充def = 控件定义.get("填充")
            填充图 = self._解析图源(填充def, 上下文, 皮肤包)

            动态位移 = 控件定义.get("动态位移") or {}
            try:
                时间键 = str(动态位移.get("时间键") or "当前谱面秒").strip()
            except Exception:
                时间键 = "当前谱面秒"
            try:
                当前秒 = float(上下文.get(时间键, 0.0) or 0.0)
            except Exception:
                当前秒 = 0.0
            try:
                x振幅 = float(_取数(动态位移.get("x振幅"), 0.0))
            except Exception:
                x振幅 = 0.0
            try:
                速度 = float(_取数(动态位移.get("速度"), 0.0))
            except Exception:
                速度 = 0.0
            try:
                当前血量值 = float(_取数(上下文.get("血量最终显示", 值), 值))
            except Exception:
                当前血量值 = float(值)
            if float(当前血量值) >= 0.999:
                x振幅 = 0.0
            动态偏移x = (
                int(
                    round(
                        math.sin(float(当前秒) * float(速度) * math.tau) * float(x振幅)
                    )
                )
                if abs(x振幅) > 0.01 and abs(速度) > 0.01
                else 0
            )

            if 填充图 is not None:
                try:
                    扩展宽 = int(max(内矩形.w, 内矩形.w + abs(int(x振幅)) * 2))
                    图2 = self._取缩放图(
                        f"进度条填充:{id(填充图)}",
                        填充图,
                        扩展宽,
                        内矩形.h,
                    )
                    if 最终透明 < 0.999:
                        图2 = 图2.copy()
                        图2.set_alpha(int(255 * 最终透明))
                    临时层 = pygame.Surface((填充宽, 内矩形.h), pygame.SRCALPHA)
                    起贴x = int(-abs(int(x振幅)) + 动态偏移x)
                    临时层.blit(图2, (int(起贴x), 0))
                    屏幕.blit(
                        临时层,
                        内矩形.topleft,
                    )
                    return
                except Exception:
                    pass

            渐变 = 控件定义.get("渐变兜底") or {}
            if bool(渐变.get("启用", True)):
                try:
                    玩家序号 = int(_取数(上下文.get("玩家序号", 1), 1))
                except Exception:
                    玩家序号 = 1

                if 玩家序号 == 2:
                    颜色1 = _解析颜色(渐变.get("颜色1_p2"), (60, 180, 255))
                    颜色2 = _解析颜色(渐变.get("颜色2_p2"), (200, 255, 255))
                else:
                    颜色1 = _解析颜色(渐变.get("颜色1"), (255, 60, 220))
                    颜色2 = _解析颜色(渐变.get("颜色2"), (255, 200, 255))

                try:
                    渐变图 = pygame.Surface((内矩形.w, 内矩形.h), pygame.SRCALPHA)
                    for x in range(内矩形.w):
                        t2 = 0.0 if 内矩形.w <= 1 else float(x) / float(内矩形.w - 1)
                        rr = int(颜色1[0] + (颜色2[0] - 颜色1[0]) * t2)
                        gg = int(颜色1[1] + (颜色2[1] - 颜色1[1]) * t2)
                        bb = int(颜色1[2] + (颜色2[2] - 颜色1[2]) * t2)
                        aa = int(235 * 最终透明)
                        pygame.draw.line(
                            渐变图, (rr, gg, bb, aa), (x, 0), (x, 内矩形.h)
                        )

                    pygame.draw.rect(
                        渐变图,
                        (255, 255, 255, int(60 * 最终透明)),
                        pygame.Rect(0, 0, 内矩形.w, int(max(1, 内矩形.h * 0.18))),
                    )

                    屏幕.blit(
                        渐变图, 内矩形.topleft, area=pygame.Rect(0, 0, 填充宽, 内矩形.h)
                    )
                except Exception:
                    pass
            return

        return

    def _解析图源(
        self, 图源def: Any, 上下文: Dict[str, Any], 皮肤包: Any
    ) -> Optional[pygame.Surface]:
        if not isinstance(图源def, dict):
            return None
        类型 = str(图源def.get("类型") or "").strip()

        if 类型 == "绑定":
            键 = str(图源def.get("键") or "").strip()
            值 = 上下文.get(键, None)
            return 值 if isinstance(值, pygame.Surface) else None

        if 类型 == "文件":
            路径 = str(图源def.get("路径") or "").strip()
            return self._取文件图(路径)

        if 类型 == "皮肤帧":
            分包 = str(图源def.get("分包") or "").strip()
            名 = _解析动态值(图源def.get("名"), 上下文)
            名 = str(名 or "").strip()
            return self._取皮肤帧(皮肤包, 分包, 名)

        return None
