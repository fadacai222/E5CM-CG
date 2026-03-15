import json
import os
from typing import Any, Dict, Optional, Tuple

import pygame

try:
    from pygame._sdl2 import video as _sdl2_video
except Exception:
    _sdl2_video = None


class 全屏透明叠加层:
    """
    复用型全屏叠加层：
    - CPU 侧统一绘制到带 alpha 的 Surface
    - 软件后端直接 blit
    - GPU 后端复用一张 SDL2 Texture 做透明叠加
    """

    def __init__(self):
        self._画布: Optional[pygame.Surface] = None
        self._纹理 = None
        self._纹理渲染器id: int = 0
        self._尺寸: Tuple[int, int] = (0, 0)
        self._有内容: bool = False

    def _规范尺寸(self, 尺寸: Tuple[int, int]) -> Tuple[int, int]:
        try:
            宽 = int(max(1, int(尺寸[0])))
        except Exception:
            宽 = 1
        try:
            高 = int(max(1, int(尺寸[1])))
        except Exception:
            高 = 1
        return 宽, 高

    def _确保画布(self, 尺寸: Tuple[int, int]) -> Optional[pygame.Surface]:
        目标尺寸 = self._规范尺寸(尺寸)
        if isinstance(self._画布, pygame.Surface) and self._尺寸 == 目标尺寸:
            return self._画布
        try:
            self._画布 = pygame.Surface(目标尺寸, pygame.SRCALPHA, 32).convert_alpha()
        except Exception:
            try:
                self._画布 = pygame.Surface(目标尺寸, pygame.SRCALPHA, 32)
            except Exception:
                self._画布 = None
        self._尺寸 = tuple(目标尺寸)
        self._纹理 = None
        return self._画布

    def 开始绘制(
        self,
        尺寸: Tuple[int, int],
        清屏颜色: Tuple[int, int, int, int] = (0, 0, 0, 0),
    ) -> Optional[pygame.Surface]:
        画布 = self._确保画布(尺寸)
        if not isinstance(画布, pygame.Surface):
            self._有内容 = False
            return None
        try:
            画布.fill(清屏颜色)
        except Exception:
            try:
                画布.fill((0, 0, 0, 0))
            except Exception:
                pass
        self._有内容 = True
        return 画布

    def 清空(self, 清除画布: bool = False):
        self._有内容 = False
        if bool(清除画布) and isinstance(self._画布, pygame.Surface):
            try:
                self._画布.fill((0, 0, 0, 0))
            except Exception:
                pass

    def 重置(self):
        self._画布 = None
        self._纹理 = None
        self._纹理渲染器id = 0
        self._尺寸 = (0, 0)
        self._有内容 = False

    def 有内容(self) -> bool:
        return bool(self._有内容) and isinstance(self._画布, pygame.Surface)

    def _同步GPU纹理(self, 渲染器):
        if _sdl2_video is None or 渲染器 is None or not self.有内容():
            return None
        画布 = self._画布
        if not isinstance(画布, pygame.Surface):
            return None
        当前渲染器id = int(id(渲染器))
        if 当前渲染器id != int(self._纹理渲染器id):
            self._纹理 = None
            self._纹理渲染器id = 当前渲染器id
        if self._纹理 is None:
            try:
                self._纹理 = _sdl2_video.Texture.from_surface(渲染器, 画布)
            except Exception:
                self._纹理 = None
                return None
        else:
            try:
                self._纹理.update(画布)
            except Exception:
                try:
                    self._纹理 = _sdl2_video.Texture.from_surface(渲染器, 画布)
                except Exception:
                    self._纹理 = None
                    return None
        try:
            self._纹理.blend_mode = 1
        except Exception:
            pass
        return self._纹理

    def 绘制到显示后端(self, 显示后端) -> bool:
        if not self.有内容():
            return False
        画布 = self._画布
        if not isinstance(画布, pygame.Surface) or 显示后端 is None:
            return False

        if not bool(getattr(显示后端, "是否GPU", False)):
            try:
                屏幕 = 显示后端.取绘制屏幕()
            except Exception:
                屏幕 = None
            if not isinstance(屏幕, pygame.Surface):
                return False
            try:
                屏幕.blit(画布, (0, 0))
                return True
            except Exception:
                return False

        取渲染器 = getattr(显示后端, "取GPU渲染器", None)
        if not callable(取渲染器):
            return False
        try:
            渲染器 = 取渲染器()
        except Exception:
            渲染器 = None
        if 渲染器 is None:
            return False

        纹理 = self._同步GPU纹理(渲染器)
        if 纹理 is None:
            return False
        try:
            纹理.draw(dstrect=(0, 0, int(画布.get_width()), int(画布.get_height())))
            return True
        except Exception:
            try:
                渲染器.blit(纹理)
                return True
            except Exception:
                return False


def 默认准备动画设置() -> Dict[str, float]:
    return {
        "黑屏退场周期": 0.09,
        "背景展示周期": 0.30,
        "背景蒙版展示周期": 0.08,
        "判定区显示周期": 0.20,
        "血条组入场周期": 0.55,
        "场景引导入场周期": 0.18,
        "背景板入场周期": 0.25,
        "背景板高度比例": 1.00,
        "背景板装饰运动速度": 220.0,
        "背景板装饰高度比例": 0.40,
        "提示1缩放幅度": 0.50,
        "提示1缩放周期": 0.65,
        "提示1高度比例": 0.54,
        "提示2缩放幅度": 0.45,
        "提示2缩放周期": 1.10,
        "提示2高度比例": 0.50,
        "场景引导出场周期": 0.20,
        "场景引导暗度": 0.50,
        "背景蒙版透明度": 224.0,
        "专用背景蒙版透明度": 72.0,
        "提示间隔周期": 0.03,
    }


def 读取准备动画设置(设置路径: str) -> Dict[str, float]:
    默认 = 默认准备动画设置()
    if (not 设置路径) or (not os.path.isfile(设置路径)):
        return dict(默认)
    数据: Dict[str, Any] = {}
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(设置路径, "r", encoding=编码) as f:
                obj = json.load(f)
            if isinstance(obj, dict):
                数据 = obj
                break
        except Exception:
            continue
    结果 = dict(默认)
    for 键, 默认值 in 默认.items():
        try:
            结果[键] = float(数据.get(键, 默认值))
        except Exception:
            结果[键] = float(默认值)
    return 结果


def 保存准备动画设置(设置路径: str, 设置: Dict[str, float]):
    os.makedirs(os.path.dirname(os.path.abspath(设置路径)), exist_ok=True)
    数据 = 默认准备动画设置()
    for 键 in list(数据.keys()):
        try:
            数据[键] = float(设置.get(键, 数据[键]))
        except Exception:
            pass
    with open(设置路径, "w", encoding="utf-8") as f:
        json.dump(数据, f, ensure_ascii=False, indent=2)


def _clamp01(v: float) -> float:
    if v <= 0.0:
        return 0.0
    if v >= 1.0:
        return 1.0
    return float(v)


def _ease_out_cubic(v: float) -> float:
    x = 1.0 - _clamp01(v)
    return 1.0 - x * x * x


def _ease_in_out(v: float) -> float:
    x = _clamp01(v)
    return x * x * (3.0 - 2.0 * x)


def _back_out(v: float) -> float:
    x = _clamp01(v)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * pow(x - 1.0, 3) + c1 * pow(x - 1.0, 2)


def _lerp(a: float, b: float, t: float) -> float:
    x = _clamp01(t)
    return float(a) + (float(b) - float(a)) * x


def 计算准备动画时间轴(设置: Dict[str, float]) -> Dict[str, float]:
    黑屏退场周期 = float(max(0.05, 设置.get("黑屏退场周期", 0.09)))
    背景展示周期 = float(max(0.05, 设置.get("背景展示周期", 0.30)))
    背景蒙版展示周期 = float(max(0.05, 设置.get("背景蒙版展示周期", 0.08)))
    判定区显示周期 = float(max(0.05, 设置.get("判定区显示周期", 0.20)))
    血条组入场周期 = float(max(0.05, 设置.get("血条组入场周期", 0.38)))
    场景引导入场周期 = float(max(0.05, 设置.get("场景引导入场周期", 0.18)))
    背景板入场周期 = float(max(0.05, 设置.get("背景板入场周期", 0.25)))
    提示1缩放周期 = float(max(0.05, 设置.get("提示1缩放周期", 0.65)))
    提示2缩放周期 = float(max(0.05, 设置.get("提示2缩放周期", 1.10)))
    场景引导出场周期 = float(max(0.05, 设置.get("场景引导出场周期", 0.20)))
    提示间隔周期 = float(max(0.0, 设置.get("提示间隔周期", 0.03)))

    t0 = 0.0
    黑屏结束 = t0 + 黑屏退场周期
    背景结束 = 黑屏结束 + 背景展示周期
    蒙版结束 = 背景结束 + 背景蒙版展示周期
    判定区结束 = 蒙版结束 + 判定区显示周期
    血条组结束 = 判定区结束 + 血条组入场周期

    引导入场开始 = 血条组结束
    引导入场结束 = 引导入场开始 + 场景引导入场周期
    背景板入场结束 = 引导入场开始 + 背景板入场周期
    提示1开始 = max(引导入场结束, 背景板入场结束)
    提示1结束 = 提示1开始 + 提示1缩放周期
    提示2开始 = 提示1结束 + 提示间隔周期
    提示2结束 = 提示2开始 + 提示2缩放周期
    引导出场开始 = 提示2结束
    引导出场结束 = 引导出场开始 + 场景引导出场周期

    return {
        "黑屏开始": t0,
        "黑屏结束": 黑屏结束,
        "背景开始": 黑屏结束,
        "背景结束": 背景结束,
        "蒙版开始": 背景结束,
        "蒙版结束": 蒙版结束,
        "判定区开始": 蒙版结束,
        "判定区结束": 判定区结束,
        "血条组开始": 判定区结束,
        "血条组结束": 血条组结束,
        "引导开始": 引导入场开始,
        "引导入场结束": 引导入场结束,
        "背景板入场结束": 背景板入场结束,
        "提示1开始": 提示1开始,
        "提示1结束": 提示1结束,
        "提示2开始": 提示2开始,
        "提示2结束": 提示2结束,
        "引导出场开始": 引导出场开始,
        "引导出场结束": 引导出场结束,
        "总时长": 引导出场结束,
    }


def 计算准备动画总时长(设置: Dict[str, float]) -> float:
    return float(计算准备动画时间轴(设置).get("总时长", 0.0))


def 加载准备动画图片(项目根: str) -> Dict[int, pygame.Surface]:
    结果: Dict[int, pygame.Surface] = {}
    目录 = os.path.join(str(项目根 or ""), "UI-img", "游戏界面", "准备就绪")
    for 序号 in range(1, 7):
        路径 = os.path.join(目录, f"{序号}.png")
        try:
            if os.path.isfile(路径):
                结果[序号] = pygame.image.load(路径).convert_alpha()
        except Exception:
            continue
    return 结果


def _取覆盖层缓存图(
    运行缓存: Dict[str, Any], 尺寸: Tuple[int, int], alpha: int
) -> Optional[pygame.Surface]:
    a = int(max(0, min(255, int(alpha))))
    if a <= 0:
        return None
    w, h = int(max(1, 尺寸[0])), int(max(1, 尺寸[1]))
    key = (w, h, a)
    缓存表 = 运行缓存.setdefault("_覆盖层缓存", {})
    图 = 缓存表.get(key)
    if isinstance(图, pygame.Surface):
        return 图
    try:
        图 = pygame.Surface((w, h), pygame.SRCALPHA)
        图.fill((0, 0, 0, a))
        if len(缓存表) > 64:
            缓存表.clear()
        缓存表[key] = 图
        return 图
    except Exception:
        return None


def _取缩放缓存图(
    运行缓存: Dict[str, Any],
    缓存名: str,
    源图: pygame.Surface,
    目标宽: int,
    目标高: int,
    平滑: bool = True,
) -> Optional[pygame.Surface]:
    w = int(max(1, 目标宽))
    h = int(max(1, 目标高))
    key = (str(缓存名), int(id(源图)), w, h, bool(平滑))
    缓存表 = 运行缓存.setdefault("_缩放缓存", {})
    已有 = 缓存表.get(key)
    if isinstance(已有, pygame.Surface):
        return 已有
    try:
        if bool(平滑):
            图 = pygame.transform.smoothscale(源图, (w, h)).convert_alpha()
        else:
            图 = pygame.transform.scale(源图, (w, h)).convert_alpha()
        if len(缓存表) > 256:
            缓存表.clear()
        缓存表[key] = 图
        return 图
    except Exception:
        return None


def 计算透明控件组正放参数(
    进度: float,
    起始偏移x: float = 0.0,
    起始偏移y: float = 0.0,
    结束偏移x: float = 0.0,
    结束偏移y: float = 0.0,
    起始alpha: float = 0.0,
    结束alpha: float = 255.0,
    位移缓动=None,
    alpha缓动=None,
) -> Dict[str, int]:
    t = _clamp01(进度)
    位移t = 位移缓动(t) if callable(位移缓动) else _ease_in_out(t)
    透明t = alpha缓动(t) if callable(alpha缓动) else _ease_in_out(t)
    return {
        "偏移x": int(round(_lerp(起始偏移x, 结束偏移x, 位移t))),
        "偏移y": int(round(_lerp(起始偏移y, 结束偏移y, 位移t))),
        "alpha": int(round(_lerp(起始alpha, 结束alpha, 透明t))),
    }


def 计算透明控件组倒放参数(
    进度: float,
    起始偏移x: float = 0.0,
    起始偏移y: float = 0.0,
    结束偏移x: float = 0.0,
    结束偏移y: float = 0.0,
    起始alpha: float = 0.0,
    结束alpha: float = 255.0,
    位移缓动=None,
    alpha缓动=None,
) -> Dict[str, int]:
    return 计算透明控件组正放参数(
        进度=进度,
        起始偏移x=结束偏移x,
        起始偏移y=结束偏移y,
        结束偏移x=起始偏移x,
        结束偏移y=起始偏移y,
        起始alpha=结束alpha,
        结束alpha=起始alpha,
        位移缓动=位移缓动,
        alpha缓动=alpha缓动,
    )


def 绘制透明控件组回放(
    屏幕: pygame.Surface,
    图层: Optional[pygame.Surface],
    回放参数: Dict[str, int],
    原点: Tuple[int, int] = (0, 0),
) -> bool:
    if 屏幕 is None or (not isinstance(图层, pygame.Surface)):
        return False
    alpha = int(max(0, min(255, int((回放参数 or {}).get("alpha", 255)))))
    if alpha <= 0:
        return False
    偏移x = int((回放参数 or {}).get("偏移x", 0))
    偏移y = int((回放参数 or {}).get("偏移y", 0))
    目标点 = (int(原点[0]) + 偏移x, int(原点[1]) + 偏移y)
    try:
        if alpha >= 255:
            屏幕.blit(图层, 目标点)
            return True
        临时图 = 图层.copy().convert_alpha()
        临时图.set_alpha(alpha)
        屏幕.blit(临时图, 目标点)
        return True
    except Exception:
        return False


def 计算准备动画区域(
    屏幕尺寸: Tuple[int, int],
    轨道起x: int,
    轨道总宽: int,
    判定线y: int,
    箭头基准宽: int,
    血条区域: pygame.Rect,
) -> Dict[str, pygame.Rect]:
    屏宽, 屏高 = int(max(1, 屏幕尺寸[0])), int(max(1, 屏幕尺寸[1]))
    判定高 = int(max(88, 箭头基准宽 * 1.35))
    判定区rect = pygame.Rect(
        int(轨道起x - 50),
        int(判定线y - 判定高 * 0.55),
        int(轨道总宽 + 100),
        int(判定高),
    )
    顶栏高 = int(max(血条区域.bottom + 26, 160))
    顶栏区域 = pygame.Rect(0, 0, 屏宽, min(屏高, 顶栏高))
    return {"判定区": 判定区rect, "顶部HUD": 顶栏区域}


def 绘制准备就绪动画(
    屏幕: pygame.Surface,
    基础场景图: Optional[pygame.Surface],
    背景无蒙版图: Optional[pygame.Surface],
    准备图片: Dict[int, pygame.Surface],
    设置: Dict[str, float],
    经过秒: float,
    判定区矩形: pygame.Rect,
    顶部HUD矩形: pygame.Rect,
    顶部HUD图层: Optional[pygame.Surface] = None,
    判定区图层: Optional[pygame.Surface] = None,
    运行缓存: Optional[Dict[str, Any]] = None,
    仅前景: bool = False,
) -> None:
    if 屏幕 is None:
        return
    缓存 = 运行缓存 if isinstance(运行缓存, dict) else {}
    时间轴 = 计算准备动画时间轴(设置)
    总时长 = float(时间轴.get("总时长", 0.0))
    if 经过秒 < 0.0 or 经过秒 > 总时长:
        return

    屏宽, 屏高 = 屏幕.get_size()
    引导开始 = float(时间轴["引导开始"])
    引导入场结束 = float(时间轴["引导入场结束"])
    引导出场开始 = float(时间轴["引导出场开始"])
    引导出场结束 = float(时间轴["引导出场结束"])
    引导入场t = _clamp01((经过秒 - 引导开始) / max(0.001, 引导入场结束 - 引导开始))
    引导出场t = _clamp01(
        (经过秒 - 引导出场开始) / max(0.001, 引导出场结束 - 引导出场开始)
    )
    if not bool(仅前景):
        屏幕.fill((0, 0, 0))

        背景开始 = float(时间轴["背景开始"])
        背景结束 = float(时间轴["背景结束"])
        背景t = _clamp01((经过秒 - 背景开始) / max(0.001, 背景结束 - 背景开始))
        if 背景无蒙版图 is not None:
            try:
                屏幕.blit(背景无蒙版图, (0, 0))
            except Exception:
                pass
            背景遮黑alpha = int(round(255.0 * (1.0 - _ease_in_out(背景t))))
            覆盖 = _取覆盖层缓存图(缓存, (屏宽, 屏高), 背景遮黑alpha)
            if 覆盖 is not None:
                屏幕.blit(覆盖, (0, 0))

        蒙版开始 = float(时间轴["蒙版开始"])
        蒙版结束 = float(时间轴["蒙版结束"])
        蒙版t = _clamp01((经过秒 - 蒙版开始) / max(0.001, 蒙版结束 - 蒙版开始))
        蒙版目标alpha = int(max(0.0, min(255.0, 设置.get("背景蒙版透明度", 224.0))))
        if 蒙版t > 0.0:
            蒙版 = _取覆盖层缓存图(
                缓存, (屏宽, 屏高), int(蒙版目标alpha * _ease_in_out(蒙版t))
            )
            if 蒙版 is not None:
                屏幕.blit(蒙版, (0, 0))

        判定区开始 = float(时间轴["判定区开始"])
        判定区结束 = float(时间轴["判定区结束"])
        判定区t = _clamp01((经过秒 - 判定区开始) / max(0.001, 判定区结束 - 判定区开始))
        if 判定区t > 0.0 and 判定区矩形.w > 0 and 判定区矩形.h > 0:
            判定alpha = int(255 * _ease_in_out(判定区t))
            判定缩放 = 1.18 - 0.18 * _ease_out_cubic(判定区t)
            if isinstance(判定区图层, pygame.Surface):
                try:
                    局部键 = (
                        "_判定区局部源",
                        int(id(判定区图层)),
                        int(判定区矩形.x),
                        int(判定区矩形.y),
                        int(判定区矩形.w),
                        int(判定区矩形.h),
                    )
                    源图 = 缓存.get(局部键)
                    if not isinstance(源图, pygame.Surface):
                        源图 = 判定区图层.subsurface(判定区矩形).copy().convert_alpha()
                        缓存.clear() if len(缓存) > 512 else None
                        缓存[局部键] = 源图
                    目标宽 = int(max(2, round(float(源图.get_width()) * 判定缩放)))
                    目标高 = int(max(2, round(float(源图.get_height()) * 判定缩放)))
                    量化缩放 = int(max(1, min(2000, round(判定缩放 * 1000.0))))
                    图2 = _取缩放缓存图(
                        缓存,
                        缓存名=f"判定区缩放_{量化缩放}",
                        源图=源图,
                        目标宽=目标宽,
                        目标高=目标高,
                        平滑=True,
                    )
                    if isinstance(图2, pygame.Surface):
                        图2.set_alpha(判定alpha)
                        rr = 图2.get_rect(center=(判定区矩形.centerx, 判定区矩形.centery))
                        屏幕.blit(图2, rr.topleft)
                except Exception:
                    pass
            elif 基础场景图 is not None:
                try:
                    图 = 基础场景图.subsurface(判定区矩形).copy()
                    图.set_alpha(判定alpha)
                    屏幕.blit(图, 判定区矩形.topleft)
                except Exception:
                    pass

        血条组开始 = float(时间轴["血条组开始"])
        血条组结束 = float(时间轴["血条组结束"])
        血条组t = _clamp01((经过秒 - 血条组开始) / max(0.001, 血条组结束 - 血条组开始))
        if (
            血条组t > 0.0
            and 顶部HUD矩形.w > 0
            and 顶部HUD矩形.h > 0
            and isinstance(顶部HUD图层, pygame.Surface)
        ):
            血条回放参数 = 计算透明控件组正放参数(
                进度=血条组t,
                起始偏移y=-float(顶部HUD矩形.h + 36),
                结束偏移y=0.0,
                起始alpha=0.0,
                结束alpha=255.0,
                位移缓动=_ease_out_cubic,
                alpha缓动=_ease_in_out,
            )
            绘制透明控件组回放(屏幕, 顶部HUD图层, 血条回放参数)

        引导暗度 = float(max(0.0, min(1.0, 设置.get("场景引导暗度", 0.50))))
        当前暗化 = _ease_in_out(引导入场t) * (1.0 - _ease_in_out(引导出场t)) * 引导暗度
        if 当前暗化 > 0.0:
            暗层 = _取覆盖层缓存图(缓存, (屏宽, 屏高), int(255 * 当前暗化))
            if 暗层 is not None:
                屏幕.blit(暗层, (0, 0))

    专用蒙版目标alpha = int(
        max(0.0, min(255.0, float(设置.get("专用背景蒙版透明度", 72.0))))
    )
    if 专用蒙版目标alpha > 0:
        专用蒙版强度 = _ease_in_out(引导入场t) * (1.0 - _ease_in_out(引导出场t))
        专用蒙版alpha = int(round(float(专用蒙版目标alpha) * float(专用蒙版强度)))
        if 专用蒙版alpha > 0:
            专用蒙版 = _取覆盖层缓存图(缓存, (屏宽, 屏高), 专用蒙版alpha)
            if 专用蒙版 is not None:
                屏幕.blit(专用蒙版, (0, 0))

    背板1 = 准备图片.get(1)
    背板2 = 准备图片.get(2)
    ready前景 = 准备图片.get(3)
    ready背层 = 准备图片.get(4)
    start前景 = 准备图片.get(5)
    start背层 = 准备图片.get(6)
    板rect = None
    文字区域 = None
    箭头区域 = None
    if 背板1 is not None:
        背景板高度比例 = float(
            max(0.35, min(2.20, float(设置.get("背景板高度比例", 1.00))))
        )
        基础板高 = float(背板1.get_height()) * (
            float(屏宽) / float(max(1, 背板1.get_width()))
        )
        板高 = int(max(1, round(基础板高 * 背景板高度比例)))
        板y = int(屏高 * 0.5 - 板高 * 0.5)
        背景板入场结束 = float(时间轴["背景板入场结束"])
        板入场t = _clamp01(
            (经过秒 - 引导开始) / max(0.001, 背景板入场结束 - 引导开始)
        )
        板退场t = _clamp01(
            (经过秒 - 引导出场开始) / max(0.001, 引导出场结束 - 引导出场开始)
        )
        板横向拉伸 = 1.0 + 0.035 * _ease_in_out(板退场t)
        板宽 = int(max(2, round(float(屏宽) * 板横向拉伸)))
        板入场x = int((-板宽) + (板宽 * _ease_out_cubic(板入场t)))
        板右退偏移 = int((屏宽 + int(板宽 * 0.08)) * _ease_in_out(板退场t))
        板x = int(板入场x + 板右退偏移 - (板宽 - 屏宽) * 0.5)
        板alpha = 255
        if 板退场t > 0.82:
            板alpha = int(
                max(0, min(255, round(255.0 * (1.0 - ((板退场t - 0.82) / 0.18)))))
            )
        if 板alpha > 0 and 板入场t > 0.0:
            try:
                底板图 = _取缩放缓存图(
                    缓存,
                    缓存名=f"准备底板1_{板宽}_{板高}",
                    源图=背板1,
                    目标宽=板宽,
                    目标高=板高,
                    平滑=True,
                )
                if 底板图 is not None:
                    底板图.set_alpha(int(板alpha))
                    屏幕.blit(底板图, (板x, 板y))
                板rect = pygame.Rect(板x, 板y, 板宽, 板高)
            except Exception:
                板rect = None

        if 板rect is not None:
            文本边距x = int(max(52, round(板rect.h * 0.34)))
            文字区域 = pygame.Rect(
                int(板rect.x + 文本边距x),
                int(板rect.y),
                int(max(2, 板rect.w - 文本边距x * 2)),
                int(板rect.h),
            )
            背景板装饰高度比例 = float(
                max(0.10, min(1.20, float(设置.get("背景板装饰高度比例", 0.40))))
            )
            箭头高度 = int(max(8, round(板rect.h * 背景板装饰高度比例)))
            箭头边距x = int(max(24, round(板rect.h * 0.20)))
            箭头区域 = pygame.Rect(
                int(板rect.x + 箭头边距x),
                int(板rect.centery - 箭头高度 * 0.5),
                int(max(2, 板rect.w - 箭头边距x * 2)),
                int(箭头高度),
            )
            if 背板2 is not None:
                _绘制条幅内箭头(
                    屏幕,
                    背板2,
                    箭头区域,
                    板alpha=int(板alpha),
                    当前秒=float(经过秒),
                    起始秒=float(引导开始),
                    速度=float(max(40.0, 设置.get("背景板装饰运动速度", 220.0))),
                    运行缓存=缓存,
                    缓存名前缀="准备条箭头",
                )

    if 文字区域 is None or 板rect is None:
        return

    提示1开始 = float(时间轴["提示1开始"])
    提示1结束 = float(时间轴["提示1结束"])
    提示2开始 = float(时间轴["提示2开始"])
    提示2结束 = float(时间轴["提示2结束"])

    提示1周期 = max(0.08, float(提示1结束 - 提示1开始))
    提示2展示结束 = max(float(提示2开始), float(引导出场开始))
    提示2周期 = max(0.08, float(提示2展示结束 - 提示2开始))
    提示1拉伸幅度 = float(
        max(0.04, min(0.18, float(设置.get("提示1缩放幅度", 0.50)) * 0.20))
    )
    提示2拉伸幅度 = float(
        max(0.04, min(0.16, float(设置.get("提示2缩放幅度", 0.45)) * 0.16))
    )
    提示1高度比例 = float(
        max(0.20, min(0.95, float(设置.get("提示1高度比例", 0.54))))
    )
    提示2高度比例 = float(
        max(0.20, min(0.95, float(设置.get("提示2高度比例", 0.50))))
    )

    if 提示1开始 <= 经过秒 < 提示2开始:
        提示1t = _clamp01((经过秒 - 提示1开始) / 提示1周期)
        提示1揭示占比 = 0.78
        if 提示1t < 提示1揭示占比:
            揭示t = _clamp01(提示1t / max(0.001, 提示1揭示占比))
            _绘制提示文字组合(
                屏幕,
                前景图=ready前景,
                背层图=ready背层,
                区域=文字区域,
                运行缓存=缓存,
                缓存名前缀="准备提示1",
                高度比例=提示1高度比例,
                基础缩放=_lerp(0.96, 1.00, _ease_out_cubic(揭示t)),
                横向拉伸=_lerp(0.92, 1.0 + 提示1拉伸幅度, _ease_in_out(揭示t)),
                可见比例=_ease_in_out(揭示t),
                前景alpha=255,
                背层alpha=int(_lerp(110, 215, _ease_in_out(揭示t))),
                最大宽比例=0.84,
            )
        else:
            收缩t = _clamp01(
                (提示1t - 提示1揭示占比) / max(0.001, 1.0 - 提示1揭示占比)
            )
            _绘制提示文字组合(
                屏幕,
                前景图=ready前景,
                背层图=ready背层,
                区域=文字区域,
                运行缓存=缓存,
                缓存名前缀="准备提示1",
                高度比例=提示1高度比例,
                基础缩放=_lerp(1.00, 0.62, _ease_in_out(收缩t)),
                横向拉伸=_lerp(
                    1.0 + 提示1拉伸幅度, 0.80, _ease_in_out(收缩t)
                ),
                可见比例=1.0,
                前景alpha=int(_lerp(255, 0, _ease_in_out(收缩t))),
                背层alpha=int(_lerp(215, 0, _ease_in_out(收缩t))),
                最大宽比例=0.84,
            )

    if 提示2开始 <= 经过秒:
        if 经过秒 < 引导出场开始:
            提示2t = _clamp01((经过秒 - 提示2开始) / 提示2周期)
            提示2入场占比 = 0.32
            if 提示2t < 提示2入场占比:
                入场t = _clamp01(提示2t / max(0.001, 提示2入场占比))
                _绘制提示文字组合(
                    屏幕,
                    前景图=start前景,
                    背层图=start背层,
                    区域=文字区域,
                    运行缓存=缓存,
                    缓存名前缀="准备提示2",
                    高度比例=提示2高度比例,
                    基础缩放=_lerp(0.84, 1.00, _back_out(入场t)),
                    横向拉伸=1.0,
                    可见比例=1.0,
                    前景alpha=int(_lerp(60, 255, _ease_in_out(入场t))),
                    背层alpha=int(_lerp(36, 220, _ease_in_out(入场t))),
                    最大宽比例=0.78,
                )
            else:
                停留t = _clamp01(
                    (提示2t - 提示2入场占比) / max(0.001, 1.0 - 提示2入场占比)
                )
                _绘制提示文字组合(
                    屏幕,
                    前景图=start前景,
                    背层图=start背层,
                    区域=文字区域,
                    运行缓存=缓存,
                    缓存名前缀="准备提示2",
                    高度比例=提示2高度比例,
                    基础缩放=1.0,
                    横向拉伸=_lerp(
                        1.0,
                        1.03 + 提示2拉伸幅度 * 0.25,
                        _ease_in_out(max(0.0, (停留t - 0.20) / 0.80)),
                    ),
                    可见比例=1.0,
                    前景alpha=255,
                    背层alpha=220,
                    最大宽比例=0.78,
                )
        else:
            _绘制提示文字组合(
                屏幕,
                前景图=start前景,
                背层图=start背层,
                区域=文字区域,
                运行缓存=缓存,
                缓存名前缀="准备提示2",
                高度比例=提示2高度比例,
                基础缩放=1.0,
                横向拉伸=_lerp(
                    1.03 + 提示2拉伸幅度 * 0.25,
                    1.10 + 提示2拉伸幅度 * 0.35,
                    _ease_in_out(板退场t),
                ),
                可见比例=1.0,
                前景alpha=255 if 板退场t < 0.86 else int(_lerp(255, 0, (板退场t - 0.86) / 0.14)),
                背层alpha=220 if 板退场t < 0.82 else int(_lerp(220, 0, (板退场t - 0.82) / 0.18)),
                最大宽比例=0.78,
                偏移x=int(_lerp(0.0, float(文字区域.w) * 0.44, _ease_in_out(板退场t))),
            )


def _绘制裁切贴图(
    屏幕: pygame.Surface,
    图: Optional[pygame.Surface],
    目标矩形: pygame.Rect,
    可见比例: float = 1.0,
) -> None:
    if 图 is None or 目标矩形.w <= 0 or 目标矩形.h <= 0:
        return
    比例 = _clamp01(可见比例)
    if 比例 <= 0.0:
        return
    if 比例 >= 0.999:
        屏幕.blit(图, 目标矩形.topleft)
        return
    可见宽 = int(max(1, round(float(目标矩形.w) * 比例)))
    src = pygame.Rect(0, 0, int(min(图.get_width(), 可见宽)), int(图.get_height()))
    if src.w <= 0 or src.h <= 0:
        return
    try:
        屏幕.blit(图, 目标矩形.topleft, area=src)
    except Exception:
        pass


def _绘制条幅内箭头(
    屏幕: pygame.Surface,
    源图: pygame.Surface,
    区域: pygame.Rect,
    板alpha: int,
    当前秒: float,
    起始秒: float,
    速度: float,
    运行缓存: Optional[Dict[str, Any]] = None,
    缓存名前缀: str = "",
) -> None:
    if 区域.w <= 0 or 区域.h <= 0:
        return
    缓存 = 运行缓存 if isinstance(运行缓存, dict) else {}
    目标高 = int(max(2, 区域.h))
    目标宽 = int(max(2, 源图.get_width() * (目标高 / max(1, 源图.get_height()))))
    单张 = _取缩放缓存图(
        缓存,
        缓存名=f"{缓存名前缀}_{目标宽}_{目标高}",
        源图=源图,
        目标宽=目标宽,
        目标高=目标高,
        平滑=True,
    )
    if 单张 is None:
        return
    单张.set_alpha(int(max(0, min(255, 板alpha))))
    偏移 = int(max(0.0, 当前秒 - 起始秒) * max(10.0, 速度))
    偏移 %= max(1, 单张.get_width())
    起绘x = int(区域.x - 单张.get_width() + 偏移)
    起绘y = int(区域.centery - 单张.get_height() * 0.5)
    原裁切 = 屏幕.get_clip()
    try:
        屏幕.set_clip(区域)
        while 起绘x < 区域.right:
            屏幕.blit(单张, (起绘x, 起绘y))
            起绘x += 单张.get_width()
    finally:
        屏幕.set_clip(原裁切)


def _绘制提示文字组合(
    屏幕: pygame.Surface,
    前景图: Optional[pygame.Surface],
    背层图: Optional[pygame.Surface],
    区域: pygame.Rect,
    运行缓存: Optional[Dict[str, Any]] = None,
    缓存名前缀: str = "",
    高度比例: float = 0.54,
    基础缩放: float = 1.0,
    横向拉伸: float = 1.0,
    可见比例: float = 1.0,
    前景alpha: int = 255,
    背层alpha: int = 255,
    最大宽比例: float = 0.84,
    偏移x: int = 0,
    偏移y: int = 0,
) -> None:
    if 前景图 is None and 背层图 is None:
        return
    if 区域.w <= 0 or 区域.h <= 0:
        return
    缓存 = 运行缓存 if isinstance(运行缓存, dict) else {}

    目标高 = int(max(2, round(float(区域.h) * max(0.1, 高度比例) * max(0.2, 基础缩放))))
    目标高 = int(min(区域.h, max(2, 目标高)))
    图列表 = [图 for 图 in (前景图, 背层图) if isinstance(图, pygame.Surface)]
    if not 图列表:
        return

    def _原始宽(图: pygame.Surface) -> int:
        return int(max(2, round(图.get_width() * (目标高 / max(1, 图.get_height())))))

    最大原宽 = max(_原始宽(图) for 图 in 图列表)
    允许宽 = int(max(2, round(float(区域.w) * max(0.1, 最大宽比例))))
    适配缩放 = min(1.0, float(允许宽) / float(max(1, int(round(最大原宽 * max(0.2, 横向拉伸))))))
    最终高 = int(max(2, round(float(目标高) * 适配缩放)))
    if 最终高 <= 1:
        return

    def _画单层(图: Optional[pygame.Surface], alpha: int, 后缀: str):
        if 图 is None:
            return
        a = int(max(0, min(255, alpha)))
        if a <= 0:
            return
        原宽 = int(max(2, round(图.get_width() * (最终高 / max(1, 图.get_height())))))
        最终宽 = int(max(2, round(float(原宽) * max(0.2, 横向拉伸))))
        图2 = _取缩放缓存图(
            缓存,
            缓存名=f"{缓存名前缀}_{后缀}_{最终宽}_{最终高}",
            源图=图,
            目标宽=最终宽,
            目标高=最终高,
            平滑=True,
        )
        if 图2 is None:
            return
        图2.set_alpha(a)
        rr = 图2.get_rect(
            center=(
                int(区域.centerx + 偏移x),
                int(区域.centery + 偏移y),
            )
        )
        _绘制裁切贴图(屏幕, 图2, rr, 可见比例=可见比例)

    _画单层(背层图, 背层alpha, "bg")
    _画单层(前景图, 前景alpha, "fg")
