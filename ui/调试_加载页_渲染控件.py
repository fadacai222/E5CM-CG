import os
import sys
import json
from typing import Any, Dict, List, Optional, Tuple

import pygame


_项目根目录_缓存: str | None = None


def 取项目根目录() -> str:
    global _项目根目录_缓存
    if _项目根目录_缓存:
        return _项目根目录_缓存

    try:
        if getattr(sys, "frozen", False):
            起点 = os.path.dirname(os.path.abspath(sys.executable))
        else:
            起点 = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        起点 = os.getcwd()

    当前 = os.path.abspath(起点)
    for _ in range(10):
        if (
            os.path.isdir(os.path.join(当前, "core"))
            and os.path.isdir(os.path.join(当前, "ui"))
            and os.path.isdir(os.path.join(当前, "songs"))
        ):
            _项目根目录_缓存 = 当前
            return 当前
        上级 = os.path.dirname(当前)
        if 上级 == 当前:
            break
        当前 = 上级

    _项目根目录_缓存 = os.path.abspath(起点)
    return _项目根目录_缓存


def _安全读json(路径: str) -> Dict[str, Any]:
    try:
        if (not 路径) or (not os.path.isfile(路径)):
            return {}
        with open(路径, "r", encoding="utf-8") as f:
            数据 = json.load(f)
        return dict(数据) if isinstance(数据, dict) else {}
    except Exception:
        return {}


def _安全写json(路径: str, 数据: Dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(路径), exist_ok=True)
        with open(路径, "w", encoding="utf-8") as f:
            json.dump(数据, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _四元(值: Any) -> Tuple[int, int, int, int]:
    if isinstance(值, (list, tuple)) and len(值) == 4:
        return (int(值[0]), int(值[1]), int(值[2]), int(值[3]))
    if isinstance(值, (list, tuple)) and len(值) == 2:
        v0, v1 = int(值[0]), int(值[1])
        return (v0, v1, v0, v1)
    if isinstance(值, (int, float)):
        v = int(值)
        return (v, v, v, v)
    return (0, 0, 0, 0)


def _颜色(值: Any, 默认: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    if isinstance(值, (list, tuple)) and len(值) in (3, 4):
        r = int(值[0])
        g = int(值[1])
        b = int(值[2])
        a = int(值[3]) if len(值) == 4 else 255
        return (
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)),
            max(0, min(255, a)),
        )
    return 默认


def _取布尔(值: Any, 默认: bool = False) -> bool:
    if isinstance(值, bool):
        return bool(值)
    if isinstance(值, (int, float)):
        return bool(int(值))
    if isinstance(值, str):
        return 值.strip().lower() in ("1", "true", "yes", "y", "on")
    return 默认


def _取文本(值: Any) -> str:
    try:
        return str(值 if 值 is not None else "")
    except Exception:
        return ""


def _按路径取值(数据: Dict[str, Any], 路径: str) -> Any:
    """
    路径形如：$.载荷.封面路径
    """
    if not isinstance(路径, str):
        return None
    路径 = 路径.strip()
    if not 路径.startswith("$."):
        return None
    节点: Any = 数据
    for 段 in 路径[2:].split("."):
        if not 段:
            continue
        if isinstance(节点, dict):
            节点 = 节点.get(段, None)
        else:
            return None
    return 节点


def _格式化文本(模板: str, 数据: Dict[str, Any]) -> str:
    """
    仅支持 {键} 形式，占位符从 数据 的顶层取。
    若需要深层，建议你在调用方先“拍平”。
    """
    try:
        return 模板.format(**数据)
    except Exception:
        return 模板


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


def _自动换行(字体: pygame.font.Font, 文本: str, 最大宽: int) -> List[str]:
    文本 = _取文本(文本).replace("\r", "")
    最大宽 = max(1, int(最大宽))

    行列表: List[str] = []
    当前行 = ""

    for ch in 文本:
        if ch == "\n":
            行列表.append(当前行)
            当前行 = ""
            continue

        测试 = 当前行 + ch
        try:
            if 字体.size(测试)[0] <= 最大宽:
                当前行 = 测试
            else:
                if 当前行:
                    行列表.append(当前行)
                当前行 = ch
        except Exception:
            当前行 = 测试

    if 当前行:
        行列表.append(当前行)
    return 行列表


def _contain缩放(图片: pygame.Surface, 目标宽: int, 目标高: int) -> pygame.Surface:
    ow, oh = 图片.get_size()
    ow = max(1, int(ow))
    oh = max(1, int(oh))
    目标宽 = max(1, int(目标宽))
    目标高 = max(1, int(目标高))

    比例 = min(目标宽 / ow, 目标高 / oh)
    nw = max(1, int(ow * 比例))
    nh = max(1, int(oh * 比例))
    缩放 = pygame.transform.smoothscale(图片, (nw, nh)).convert_alpha()

    画布 = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
    画布.fill((0, 0, 0, 0))
    x = (目标宽 - nw) // 2
    y = (目标高 - nh) // 2
    画布.blit(缩放, (x, y))
    return 画布


def _cover缩放(图片: pygame.Surface, 目标宽: int, 目标高: int) -> pygame.Surface:
    ow, oh = 图片.get_size()
    ow = max(1, int(ow))
    oh = max(1, int(oh))
    目标宽 = max(1, int(目标宽))
    目标高 = max(1, int(目标高))

    比例 = max(目标宽 / ow, 目标高 / oh)
    nw = max(1, int(ow * 比例))
    nh = max(1, int(oh * 比例))
    缩放 = pygame.transform.smoothscale(图片, (nw, nh)).convert_alpha()

    画布 = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
    画布.fill((0, 0, 0, 0))
    x = (目标宽 - nw) // 2
    y = (目标高 - nh) // 2
    画布.blit(缩放, (x, y))
    return 画布


class 加载页布局渲染器:
    def __init__(self, 布局路径: str, 项目根目录: Optional[str] = None):
        self.布局路径 = str(布局路径 or "")
        self.项目根目录 = str(项目根目录 or "") or 取项目根目录()

        self._布局数据: Dict[str, Any] = {}
        self.设计宽 = 2048
        self.设计高 = 1152

        self._图片缓存: Dict[Tuple[str, bool], Optional[pygame.Surface]] = {}
        self._图片缩放缓存: Dict[
            Tuple[str, int, int, str], Optional[pygame.Surface]
        ] = {}
        self._字体缓存: Dict[Tuple[int, bool], pygame.font.Font] = {}

        self.重载布局()

    def 重载布局(self):
        数据 = _安全读json(self.布局路径)
        if not 数据:
            # 不强行生成默认，交给调试器或调用方
            self._布局数据 = {"版本": 1, "设计宽": 2048, "设计高": 1152, "控件": []}
        else:
            self._布局数据 = 数据

        try:
            self.设计宽 = int(self._布局数据.get("设计宽", 2048) or 2048)
            self.设计高 = int(self._布局数据.get("设计高", 1152) or 1152)
        except Exception:
            self.设计宽, self.设计高 = 2048, 1152

        self.设计宽 = max(1, self.设计宽)
        self.设计高 = max(1, self.设计高)

        # 缩放缓存清掉（布局改了，rect 可能变）
        self._图片缩放缓存.clear()

    def 保存布局(self):
        if not self.布局路径:
            return
        _安全写json(self.布局路径, self._布局数据)

    def 取布局原始数据(self) -> Dict[str, Any]:
        return self._布局数据

    def _设计到屏幕参数(self, 屏幕宽: int, 屏幕高: int) -> Tuple[float, float, float]:
        屏幕宽 = max(1, int(屏幕宽))
        屏幕高 = max(1, int(屏幕高))
        scale = min(屏幕宽 / self.设计宽, 屏幕高 / self.设计高)
        content_w = self.设计宽 * scale
        content_h = self.设计高 * scale
        ox = (屏幕宽 - content_w) / 2.0
        oy = (屏幕高 - content_h) / 2.0
        return (scale, ox, oy)

    def 屏幕到设计点(
        self, 屏幕点: Tuple[int, int], 屏幕宽: int, 屏幕高: int
    ) -> Tuple[float, float]:
        x, y = float(屏幕点[0]), float(屏幕点[1])
        scale, ox, oy = self._设计到屏幕参数(屏幕宽, 屏幕高)
        dx = (x - ox) / max(1e-6, scale)
        dy = (y - oy) / max(1e-6, scale)
        return (dx, dy)

    def 设计rect到屏幕rect(
        self, 设计rect: List[float], 屏幕宽: int, 屏幕高: int
    ) -> pygame.Rect:
        x, y, w, h = 设计rect
        scale, ox, oy = self._设计到屏幕参数(屏幕宽, 屏幕高)
        sx = int(round(ox + x * scale))
        sy = int(round(oy + y * scale))
        sw = int(round(w * scale))
        sh = int(round(h * scale))
        return pygame.Rect(sx, sy, max(1, sw), max(1, sh))

    def _加载图片(self, 源: str, 透明: bool = True) -> Optional[pygame.Surface]:
        if not 源:
            return None

        # 支持相对路径（相对项目根目录）
        源 = str(源)
        if not os.path.isabs(源):
            源 = os.path.join(self.项目根目录, 源)

        键 = (源, bool(透明))
        if 键 in self._图片缓存:
            return self._图片缓存[键]

        try:
            if not os.path.isfile(源):
                self._图片缓存[键] = None
                return None
            图 = pygame.image.load(源)
            图 = 图.convert_alpha() if 透明 else 图.convert()
            self._图片缓存[键] = 图
            return 图
        except Exception:
            self._图片缓存[键] = None
            return None

    def _取字体(self, 字号: int, 加粗: bool) -> pygame.font.Font:
        字号 = max(6, int(字号))
        键 = (字号, bool(加粗))
        if 键 in self._字体缓存:
            return self._字体缓存[键]
        字体 = _获取字体(字号, 是否粗体=bool(加粗))
        self._字体缓存[键] = 字体
        return 字体

    def _绘制面板(
        self,
        屏幕: pygame.Surface,
        rect: pygame.Rect,
        颜色: Tuple[int, int, int, int],
        圆角: int,
    ):
        # ✅ 默认不画边框（你的要求）
        r, g, b, a = 颜色
        a = max(0, min(255, int(a)))

        if a <= 0:
            return

        面 = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        面.fill((0, 0, 0, 0))
        pygame.draw.rect(
            面,
            (r, g, b, a),
            pygame.Rect(0, 0, rect.w, rect.h),
            border_radius=max(0, int(圆角)),
        )
        屏幕.blit(面, rect.topleft)

    def _绘制线(
        self,
        屏幕: pygame.Surface,
        rect: pygame.Rect,
        颜色: Tuple[int, int, int, int],
        厚度: int,
    ):
        r, g, b, a = 颜色
        a = max(0, min(255, int(a)))
        if a <= 0:
            return
        厚度 = max(1, int(厚度))

        # 线用水平/垂直两种：根据 rect 长宽决定
        if rect.w >= rect.h:
            y = rect.centery
            x1 = rect.x
            x2 = rect.right
            pygame.draw.line(屏幕, (r, g, b, a), (x1, y), (x2, y), width=厚度)
        else:
            x = rect.centerx
            y1 = rect.y
            y2 = rect.bottom
            pygame.draw.line(屏幕, (r, g, b, a), (x, y1), (x, y2), width=厚度)

    def _绘制图片(
        self, 屏幕: pygame.Surface, rect: pygame.Rect, 图片: pygame.Surface, 适配: str
    ):
        适配 = (适配 or "contain").strip().lower()
        if rect.w <= 0 or rect.h <= 0:
            return

        if 适配 == "stretch":
            try:
                图 = pygame.transform.smoothscale(
                    图片, (rect.w, rect.h)
                ).convert_alpha()
                屏幕.blit(图, rect.topleft)
            except Exception:
                pass
            return

        缓存键 = ("<img>", rect.w, rect.h, 适配)
        # 注意：这里不能用固定键，否则不同图会互相污染；改用图片 id
        缓存键 = (f"id:{id(图片)}", rect.w, rect.h, 适配)
        if 缓存键 in self._图片缩放缓存 and self._图片缩放缓存[缓存键] is not None:
            屏幕.blit(self._图片缩放缓存[缓存键], rect.topleft)
            return

        try:
            if 适配 == "cover":
                图 = _cover缩放(图片, rect.w, rect.h)
            else:
                图 = _contain缩放(图片, rect.w, rect.h)
            self._图片缩放缓存[缓存键] = 图
            屏幕.blit(图, rect.topleft)
        except Exception:
            self._图片缩放缓存[缓存键] = None

    def _绘制文本(
        self,
        屏幕: pygame.Surface,
        rect: pygame.Rect,
        文本: str,
        字号: int,
        加粗: bool,
        颜色: Tuple[int, int, int, int],
        对齐: str,
        垂直: str,
        自动换行: bool,
        最大行数: int,
        行距: int,
    ):
        字号 = max(6, int(字号))
        字体 = self._取字体(字号, bool(加粗))
        r, g, b, a = 颜色
        a = max(0, min(255, int(a)))
        if a <= 0:
            return

        对齐 = (对齐 or "left").strip().lower()
        垂直 = (垂直 or "top").strip().lower()
        最大行数 = max(1, int(最大行数)) if 最大行数 else 999
        行距 = int(行距)

        if 自动换行:
            行列表 = _自动换行(字体, 文本, rect.w)
        else:
            行列表 = _取文本(文本).split("\n")

        行列表 = 行列表[:最大行数]

        渲染列表: List[pygame.Surface] = []
        总高 = 0
        for 行 in 行列表:
            try:
                面 = 字体.render(行, True, (r, g, b))
                if a < 255:
                    面.set_alpha(a)
                渲染列表.append(面)
                总高 += 面.get_height()
            except Exception:
                pass

        if not 渲染列表:
            return

        总高 += max(0, (len(渲染列表) - 1) * 行距)

        if 垂直 in ("middle", "center"):
            y = rect.y + (rect.h - 总高) // 2
        elif 垂直 == "bottom":
            y = rect.bottom - 总高
        else:
            y = rect.y

        for 面 in 渲染列表:
            if 对齐 == "center":
                x = rect.x + (rect.w - 面.get_width()) // 2
            elif 对齐 == "right":
                x = rect.right - 面.get_width()
            else:
                x = rect.x
            屏幕.blit(面, (x, y))
            y += 面.get_height() + 行距

    def _绘制星星行(
        self,
        屏幕: pygame.Surface,
        rect: pygame.Rect,
        星图: pygame.Surface,
        星数: int,
        单星高度: int,
        每行最大: int,
        间距: int,
        行距: int,
        透明度: int,
    ):
        星数 = max(0, int(星数))
        if 星数 <= 0:
            return

        单星高度 = max(6, int(单星高度))
        每行最大 = max(1, int(每行最大))
        间距 = max(0, int(间距))
        行距 = max(0, int(行距))
        透明度 = max(0, min(255, int(透明度)))

        try:
            比例 = 单星高度 / max(1, 星图.get_height())
            单星宽度 = max(1, int(round(星图.get_width() * 比例)))
            星 = pygame.transform.smoothscale(
                星图, (单星宽度, 单星高度)
            ).convert_alpha()
            if 透明度 < 255:
                星.set_alpha(透明度)
        except Exception:
            return

        # 分行：优先两行/多行都可以
        行列表: List[int] = []
        剩余 = 星数
        while 剩余 > 0:
            本行 = min(每行最大, 剩余)
            行列表.append(本行)
            剩余 -= 本行

        总高 = len(行列表) * 单星高度 + max(0, (len(行列表) - 1) * 行距)
        起始y = rect.y + (rect.h - 总高) // 2

        y = 起始y
        for 数量 in 行列表:
            总宽 = 数量 * 单星宽度 + max(0, 数量 - 1) * 间距
            x = rect.centerx - 总宽 // 2
            for i in range(数量):
                屏幕.blit(星, (x + i * (单星宽度 + 间距), y))
            y += 单星高度 + 行距

    def 计算控件命中列表(self, 屏幕: pygame.Surface) -> List[Dict[str, Any]]:
        """
        给调试器用：返回每个控件的屏幕 rect + 指向原始控件 dict（可改）
        """
        w, h = 屏幕.get_size()
        控件列表 = self._布局数据.get("控件", [])
        if not isinstance(控件列表, list):
            return []

        输出: List[Dict[str, Any]] = []
        for i, 控件 in enumerate(控件列表):
            if not isinstance(控件, dict):
                continue
            控件id = _取文本(控件.get("id", f"控件{i}"))
            rect值 = 控件.get("rect", None)
            if not (isinstance(rect值, (list, tuple)) and len(rect值) == 4):
                continue
            try:
                dx = float(rect值[0])
                dy = float(rect值[1])
                dw = float(rect值[2])
                dh = float(rect值[3])
            except Exception:
                continue

            屏幕rect = self.设计rect到屏幕rect([dx, dy, dw, dh], w, h)
            输出.append(
                {
                    "id": 控件id,
                    "索引": i,
                    "屏幕rect": 屏幕rect,
                    "设计rect": [dx, dy, dw, dh],
                    "控件": 控件,
                }
            )
        return 输出

    def 命中控件(
        self, 屏幕: pygame.Surface, 鼠标位置: Tuple[int, int]
    ) -> Optional[Dict[str, Any]]:
        列表 = self.计算控件命中列表(屏幕)
        x, y = int(鼠标位置[0]), int(鼠标位置[1])

        # 后画的优先命中（更符合直觉）
        for 信息 in reversed(列表):
            rr: pygame.Rect = 信息["屏幕rect"]
            if rr.collidepoint(x, y):
                return 信息
        return None

    def 绘制(
        self,
        屏幕: pygame.Surface,
        数据: Dict[str, Any],
        显示全部边框: bool = False,
        选中id: Optional[str] = None,
    ):
        w, h = 屏幕.get_size()
        控件列表 = self._布局数据.get("控件", [])
        if not isinstance(控件列表, list):
            return

        # ✅ 调试边框颜色
        蓝 = (80, 140, 255)
        黄 = (255, 220, 60)

        for i, 控件 in enumerate(控件列表):
            if not isinstance(控件, dict):
                continue

            类型 = _取文本(控件.get("类型", "")).strip()
            控件id = _取文本(控件.get("id", f"控件{i}"))

            rect值 = 控件.get("rect", None)
            if not (isinstance(rect值, (list, tuple)) and len(rect值) == 4):
                continue

            try:
                dx = float(rect值[0])
                dy = float(rect值[1])
                dw = float(rect值[2])
                dh = float(rect值[3])
            except Exception:
                continue

            外边距 = _四元(控件.get("外边距", 0))
            内边距 = _四元(控件.get("内边距", 0))

            设计rect = [dx, dy, dw, dh]
            屏幕rect = self.设计rect到屏幕rect(设计rect, w, h)

            # 外/内边距映射：用屏幕像素（按 scale）
            scale, _, _ = self._设计到屏幕参数(w, h)
            外_l, 外_t, 外_r, 外_b = [int(round(v * scale)) for v in 外边距]
            内_l, 内_t, 内_r, 内_b = [int(round(v * scale)) for v in 内边距]

            内容rect = pygame.Rect(
                屏幕rect.x + 内_l,
                屏幕rect.y + 内_t,
                max(1, 屏幕rect.w - 内_l - 内_r),
                max(1, 屏幕rect.h - 内_t - 内_b),
            )

            if 类型 == "面板":
                颜色 = _颜色(控件.get("颜色", [0, 0, 0, 160]), (0, 0, 0, 160))
                圆角 = int(控件.get("圆角", 0) or 0)
                self._绘制面板(屏幕, 屏幕rect, 颜色, 圆角)

            elif 类型 == "线":
                颜色 = _颜色(
                    控件.get("颜色", [160, 160, 160, 255]), (160, 160, 160, 255)
                )
                厚度 = int(控件.get("厚度", max(1, 屏幕rect.h)) or max(1, 屏幕rect.h))
                self._绘制线(屏幕, 屏幕rect, 颜色, 厚度)

            elif 类型 == "图":
                透明 = _取布尔(控件.get("透明", True), True)
                适配 = _取文本(控件.get("适配", "contain"))
                源 = 控件.get("源", "")
                if isinstance(源, str) and 源.strip().startswith("$."):
                    源值 = _按路径取值(数据, 源.strip())
                    源 = _取文本(源值)
                else:
                    源 = _取文本(源)

                图 = self._加载图片(源, 透明=透明)
                if 图 is not None:
                    self._绘制图片(屏幕, 内容rect, 图, 适配)

            elif 类型 == "文本":
                模板 = _取文本(控件.get("内容", ""))
                模板 = _格式化文本(模板, 数据)

                字号 = int(控件.get("字号", 24) or 24)
                加粗 = _取布尔(控件.get("加粗", False), False)
                颜色 = _颜色(
                    控件.get("颜色", [255, 255, 255, 255]), (255, 255, 255, 255)
                )
                对齐 = _取文本(控件.get("对齐", "left"))
                垂直 = _取文本(控件.get("垂直", "top"))
                换行 = _取布尔(控件.get("换行", True), True)
                行数 = int(控件.get("行数", 999) or 999)
                行距 = int(控件.get("行距", 4) or 4)

                self._绘制文本(
                    屏幕,
                    内容rect,
                    模板,
                    字号=字号,
                    加粗=加粗,
                    颜色=颜色,
                    对齐=对齐,
                    垂直=垂直,
                    自动换行=换行,
                    最大行数=行数,
                    行距=行距,
                )

            elif 类型 == "星星行":
                源 = _取文本(控件.get("星图", ""))
                透明 = _取布尔(控件.get("透明", True), True)
                星数键 = _取文本(控件.get("星数键", "星级"))
                try:
                    星数 = int(数据.get(星数键, 0) or 0)
                except Exception:
                    星数 = 0

                星图 = self._加载图片(源, 透明=透明)
                if 星图 is not None:
                    单星高度 = int(
                        控件.get("单星高度", int(内容rect.h * 0.55))
                        or int(内容rect.h * 0.55)
                    )
                    每行最大 = int(控件.get("每行最大", 12) or 12)
                    间距 = int(控件.get("间距", 6) or 6)
                    行距 = int(控件.get("行距", 10) or 10)
                    透明度 = int(控件.get("透明度", 255) or 255)
                    self._绘制星星行(
                        屏幕,
                        内容rect,
                        星图,
                        星数=星数,
                        单星高度=单星高度,
                        每行最大=每行最大,
                        间距=间距,
                        行距=行距,
                        透明度=透明度,
                    )

            # ✅ 调试边框（默认全删，只有调试叠加）
            if 显示全部边框 or (选中id and 控件id == 选中id):
                颜色 = 黄 if (选中id and 控件id == 选中id) else 蓝

                # 内容框（更有用）
                pygame.draw.rect(屏幕, 颜色, 内容rect, width=2)

                # 画外边距框（同色细线）
                if any(v != 0 for v in 外边距):
                    外框 = pygame.Rect(
                        屏幕rect.x - 外_l,
                        屏幕rect.y - 外_t,
                        屏幕rect.w + 外_l + 外_r,
                        屏幕rect.h + 外_t + 外_b,
                    )
                    pygame.draw.rect(屏幕, 颜色, 外框, width=1)
