import json
import os
from typing import Any, Dict, Optional, Tuple

import pygame


def 默认准备动画设置() -> Dict[str, float]:
    return {
        "黑屏退场周期": 0.40,
        "背景展示周期": 0.50,
        "背景蒙版展示周期": 0.40,
        "判定区显示周期": 0.40,
        "血条组入场周期": 0.55,
        "场景引导入场周期": 0.45,
        "背景板入场周期": 0.55,
        "背景板装饰运动速度": 120.0,
        "提示1缩放幅度": 0.30,
        "提示1缩放周期": 0.30,
        "提示2缩放幅度": 0.30,
        "提示2缩放周期": 0.30,
        "场景引导出场周期": 0.35,
        "场景引导暗度": 0.50,
        "背景蒙版透明度": 224.0,
        "提示间隔周期": 0.06,
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


def 计算准备动画时间轴(设置: Dict[str, float]) -> Dict[str, float]:
    黑屏退场周期 = float(max(0.05, 设置.get("黑屏退场周期", 0.40)))
    背景展示周期 = float(max(0.05, 设置.get("背景展示周期", 0.50)))
    背景蒙版展示周期 = float(max(0.05, 设置.get("背景蒙版展示周期", 0.40)))
    判定区显示周期 = float(max(0.05, 设置.get("判定区显示周期", 0.40)))
    血条组入场周期 = float(max(0.05, 设置.get("血条组入场周期", 0.55)))
    场景引导入场周期 = float(max(0.05, 设置.get("场景引导入场周期", 0.45)))
    背景板入场周期 = float(max(0.05, 设置.get("背景板入场周期", 0.55)))
    提示1缩放周期 = float(max(0.05, 设置.get("提示1缩放周期", 0.30)))
    提示2缩放周期 = float(max(0.05, 设置.get("提示2缩放周期", 0.30)))
    场景引导出场周期 = float(max(0.05, 设置.get("场景引导出场周期", 0.35)))
    提示间隔周期 = float(max(0.0, 设置.get("提示间隔周期", 0.06)))

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
    判定区图层: Optional[pygame.Surface] = None,
    运行缓存: Optional[Dict[str, Any]] = None,
) -> None:
    if 屏幕 is None:
        return
    缓存 = 运行缓存 if isinstance(运行缓存, dict) else {}
    时间轴 = 计算准备动画时间轴(设置)
    总时长 = float(时间轴.get("总时长", 0.0))
    if 经过秒 < 0.0 or 经过秒 > 总时长:
        return

    屏宽, 屏高 = 屏幕.get_size()
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

    if 基础场景图 is not None:
        血条组开始 = float(时间轴["血条组开始"])
        血条组结束 = float(时间轴["血条组结束"])
        血条组t = _clamp01((经过秒 - 血条组开始) / max(0.001, 血条组结束 - 血条组开始))
        if 血条组t > 0.0 and 顶部HUD矩形.w > 0 and 顶部HUD矩形.h > 0:
            try:
                顶部键 = (
                    "_顶部HUD源",
                    int(id(基础场景图)),
                    int(顶部HUD矩形.x),
                    int(顶部HUD矩形.y),
                    int(顶部HUD矩形.w),
                    int(顶部HUD矩形.h),
                )
                图 = 缓存.get(顶部键)
                if not isinstance(图, pygame.Surface):
                    图 = 基础场景图.subsurface(顶部HUD矩形).copy()
                    if len(缓存) > 512:
                        缓存.clear()
                    缓存[顶部键] = 图
                图.set_alpha(int(255 * _ease_in_out(血条组t)))
                偏移y = int(
                    (1.0 - _ease_out_cubic(血条组t)) * -float(顶部HUD矩形.h + 36)
                )
                屏幕.blit(图, (顶部HUD矩形.x, 顶部HUD矩形.y + 偏移y))
            except Exception:
                pass

    引导开始 = float(时间轴["引导开始"])
    引导入场结束 = float(时间轴["引导入场结束"])
    引导出场开始 = float(时间轴["引导出场开始"])
    引导出场结束 = float(时间轴["引导出场结束"])
    引导暗度 = float(max(0.0, min(1.0, 设置.get("场景引导暗度", 0.50))))

    引导入场t = _clamp01((经过秒 - 引导开始) / max(0.001, 引导入场结束 - 引导开始))
    引导出场t = _clamp01(
        (经过秒 - 引导出场开始) / max(0.001, 引导出场结束 - 引导出场开始)
    )
    当前暗化 = _ease_in_out(引导入场t) * (1.0 - _ease_in_out(引导出场t)) * 引导暗度
    if 当前暗化 > 0.0:
        暗层 = _取覆盖层缓存图(缓存, (屏宽, 屏高), int(255 * 当前暗化))
        if 暗层 is not None:
            屏幕.blit(暗层, (0, 0))

    背板1 = 准备图片.get(1)
    背板2 = 准备图片.get(2)
    板rect = None
    if 背板1 is not None:
        板高 = int(max(1, 背板1.get_height() * (屏宽 / max(1, 背板1.get_width()))))
        板y = int(屏高 * 0.5 - 板高 * 0.5)
        背景板入场结束 = float(时间轴["背景板入场结束"])
        板t = _clamp01((经过秒 - 引导开始) / max(0.001, 背景板入场结束 - 引导开始))
        板淡出t = _clamp01(
            (经过秒 - 引导出场开始) / max(0.001, 引导出场结束 - 引导出场开始)
        )
        入场x = int((-屏宽) + (屏宽 * _ease_out_cubic(板t)))
        退场偏移x = int(屏宽 * _ease_in_out(板淡出t))
        板x = int(入场x + 退场偏移x)
        板alpha = int(255 * (1.0 - _ease_in_out(板淡出t)))
        if 板alpha > 0 and 板t > 0.0:
            try:
                底板图 = _取缩放缓存图(
                    缓存,
                    缓存名=f"准备底板1_{屏宽}_{板高}",
                    源图=背板1,
                    目标宽=屏宽,
                    目标高=板高,
                    平滑=True,
                )
                if 底板图 is not None:
                    底板图.set_alpha(板alpha)
                    屏幕.blit(底板图, (板x, 板y))
                板rect = pygame.Rect(板x, 板y, 屏宽, 板高)
            except Exception:
                板rect = None
            if 板rect is not None and 背板2 is not None:
                try:
                    叠图高 = int(max(1, 板rect.h * 0.72))
                    叠图宽 = int(
                        max(
                            1, 背板2.get_width() * (叠图高 / max(1, 背板2.get_height()))
                        )
                    )
                    单张 = _取缩放缓存图(
                        缓存,
                        缓存名=f"准备底板2_{叠图宽}_{叠图高}",
                        源图=背板2,
                        目标宽=叠图宽,
                        目标高=叠图高,
                        平滑=True,
                    )
                    if 单张 is None:
                        raise RuntimeError("准备底板2缩放失败")
                    单张.set_alpha(板alpha)
                    速度 = float(max(10.0, 设置.get("背景板装饰运动速度", 120.0)))
                    偏移 = int((经过秒 - 引导开始) * 速度) % max(1, 单张.get_width())
                    起绘x = 板rect.x - 单张.get_width() + 偏移
                    叠图y = int(板rect.y + (板rect.h - 叠图高) * 0.5)
                    while 起绘x < 板rect.right:
                        屏幕.blit(单张, (起绘x, 叠图y))
                        起绘x += 单张.get_width()
                except Exception:
                    pass

    if 板rect is not None:
        _绘制提示图(
            屏幕,
            准备图片,
            底图序号=3,
            叠图序号=4,
            开始秒=float(时间轴["提示1开始"]),
            时长=float(max(0.05, 设置.get("提示1缩放周期", 0.30))),
            缩放幅度=float(max(0.01, 设置.get("提示1缩放幅度", 0.30))),
            从大到小=True,
            当前秒=float(经过秒),
            背板矩形=板rect,
            运行缓存=缓存,
            缓存名前缀="提示1",
        )
        _绘制提示图(
            屏幕,
            准备图片,
            底图序号=5,
            叠图序号=6,
            开始秒=float(时间轴["提示2开始"]),
            时长=float(max(0.05, 设置.get("提示2缩放周期", 0.30))),
            缩放幅度=float(max(0.01, 设置.get("提示2缩放幅度", 0.30))),
            从大到小=False,
            当前秒=float(经过秒),
            背板矩形=板rect,
            运行缓存=缓存,
            缓存名前缀="提示2",
        )


def _绘制提示图(
    屏幕: pygame.Surface,
    准备图片: Dict[int, pygame.Surface],
    底图序号: int,
    叠图序号: int,
    开始秒: float,
    时长: float,
    缩放幅度: float,
    从大到小: bool,
    当前秒: float,
    背板矩形: pygame.Rect,
    运行缓存: Optional[Dict[str, Any]] = None,
    缓存名前缀: str = "",
) -> None:
    缓存 = 运行缓存 if isinstance(运行缓存, dict) else {}
    底图 = 准备图片.get(底图序号)
    叠图 = 准备图片.get(叠图序号)
    if 底图 is None:
        return
    t = _clamp01((当前秒 - 开始秒) / max(0.001, 时长))
    if t <= 0.0 or t >= 1.0:
        return

    结束缩放 = 1.0
    if 从大到小:
        起始缩放 = 1.0 + float(缩放幅度)
    else:
        起始缩放 = max(0.1, 1.0 - float(缩放幅度))
    缩放 = 起始缩放 + (结束缩放 - 起始缩放) * _ease_in_out(t)
    alpha = int(255 * (1.0 - _ease_in_out(t)))

    def _画(图: pygame.Surface):
        目标宽 = int(max(2, 图.get_width() * 缩放))
        目标高 = int(max(2, 图.get_height() * 缩放))
        量化 = int(max(1, min(2000, round(缩放 * 1000.0))))
        图2 = _取缩放缓存图(
            缓存,
            缓存名=f"{缓存名前缀}_{底图序号}_{叠图序号}_{int(id(图))}_{量化}",
            源图=图,
            目标宽=目标宽,
            目标高=目标高,
            平滑=True,
        )
        if 图2 is None:
            return
        图2.set_alpha(alpha)
        rr = 图2.get_rect(center=(背板矩形.centerx, 背板矩形.centery))
        屏幕.blit(图2, rr.topleft)

    try:
        _画(底图)
        if 叠图 is not None:
            _画(叠图)
    except Exception:
        return
