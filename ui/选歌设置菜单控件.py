import re
from typing import Dict, List, Optional

import pygame


def 设置菜单行键列表() -> List[str]:
    """
    选歌设置菜单左侧可调行（保留旧布局顺序，兼容旧 json 偏移）。
    """
    return ["调速", "变速", "变速类型", "隐藏", "轨迹", "方向", "大小"]


def 设置菜单默认调速选项() -> List[str]:
    # 固定档位：3.0 ~ 7.0（步进 0.5）
    return ["3.0", "3.5", "4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0"]


def 设置菜单行显示名(行键: str) -> str:
    键 = str(行键 or "")
    if 键 == "变速":
        return "背景"
    if 键 == "变速类型":
        return "谱面"
    return 键


def 设置菜单行值(
    行键: str,
    设置参数: Optional[Dict[str, str]] = None,
) -> str:
    参数 = dict(设置参数 or {})
    键 = str(行键 or "")
    if 键 == "变速":
        return str(参数.get("背景模式", "图片") or "图片")
    if 键 == "变速类型":
        return str(参数.get("谱面", "正常") or "正常")
    if 键 == "隐藏":
        return str(参数.get("隐藏", "关闭") or "关闭")
    if 键 == "轨迹":
        return str(参数.get("轨迹", "正常") or "正常")
    if 键 == "方向":
        return str(参数.get("方向", "关闭") or "关闭")
    if 键 == "大小":
        return str(参数.get("大小", "正常") or "正常")
    if 键 == "调速":
        return str(参数.get("调速", "X4.0") or "X4.0")
    return ""


def 设置参数文本提取值(参数文本: str, 键名: str) -> str:
    try:
        文本 = str(参数文本 or "")
        m = re.search(rf"{re.escape(str(键名))}\s*=\s*([^\s]+)", 文本)
        if not m:
            return ""
        return str(m.group(1)).strip()
    except Exception:
        return ""


def 构建设置参数文本(
    设置参数: Optional[Dict[str, object]] = None,
    背景文件名: str = "",
    箭头文件名: str = "",
) -> str:
    参数 = dict(设置参数 or {})
    参数片段: List[str] = []
    顺序键 = ["调速", "背景模式", "谱面", "隐藏", "轨迹", "方向", "大小"]
    if ("背景模式" not in 参数) and ("变速" in 参数):
        参数["背景模式"] = 参数.get("变速")

    try:
        for 键 in 顺序键:
            if 键 in 参数:
                参数片段.append(f"{键}={参数.get(键)}")
        for 键, 值 in 参数.items():
            if 键 in 顺序键:
                continue
            参数片段.append(f"{键}={值}")
    except Exception:
        参数片段 = []

    if 背景文件名:
        参数片段.append(f"背景={背景文件名}")
    if 箭头文件名:
        参数片段.append(f"箭头={箭头文件名}")
    return "设置参数：" + ("  ".join(参数片段) if 参数片段 else "默认")


def 取非透明裁切矩形(图: pygame.Surface) -> pygame.Rect:
    """
    返回图像 alpha>0 的最小包围盒；若无 alpha 或找不到，则返回整图。
    """
    try:
        w, h = 图.get_size()
    except Exception:
        return pygame.Rect(0, 0, 1, 1)
    if w <= 0 or h <= 0:
        return pygame.Rect(0, 0, 1, 1)

    try:
        mask = pygame.mask.from_surface(图, threshold=1)
        bbox = mask.get_bounding_rects()
        if bbox:
            # 合并所有 rect，避免多块分离导致裁切不全
            out = bbox[0].copy()
            for r in bbox[1:]:
                out = out.union(r)
            if out.w > 0 and out.h > 0:
                return out
    except Exception:
        pass
    return pygame.Rect(0, 0, int(w), int(h))


def 绘制_cover裁切预览(
    目标面: pygame.Surface,
    原图: Optional[pygame.Surface],
    目标区域: pygame.Rect,
) -> bool:
    """
    在目标区域内按 cover 方式绘制并裁切，保证超出部分不外溢。
    """
    if 原图 is None or (not isinstance(目标区域, pygame.Rect)):
        return False
    if 目标区域.w <= 0 or 目标区域.h <= 0:
        return False

    try:
        裁切源 = 取非透明裁切矩形(原图)
        ow, oh = int(裁切源.w), int(裁切源.h)
    except Exception:
        return False
    if ow <= 0 or oh <= 0:
        return False

    比例 = max(float(目标区域.w) / float(ow), float(目标区域.h) / float(oh))
    nw = max(1, int(round(float(ow) * 比例)))
    nh = max(1, int(round(float(oh) * 比例)))

    try:
        源图 = 原图.subsurface(裁切源).copy().convert_alpha()
        图 = pygame.transform.smoothscale(源图, (nw, nh)).convert_alpha()
    except Exception:
        try:
            源图 = 原图.subsurface(裁切源).copy().convert_alpha()
            图 = pygame.transform.scale(源图, (nw, nh)).convert_alpha()
        except Exception:
            return False

    src_x = max(0, (nw - 目标区域.w) // 2)
    src_y = max(0, (nh - 目标区域.h) // 2)
    src = pygame.Rect(src_x, src_y, int(目标区域.w), int(目标区域.h))
    src = src.clip(pygame.Rect(0, 0, nw, nh))

    try:
        目标面.blit(图, 目标区域.topleft, area=src)
        return True
    except Exception:
        return False
