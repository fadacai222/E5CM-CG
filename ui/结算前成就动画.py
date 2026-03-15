import json
import math
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pygame

from core.常量与路径 import 取项目根目录 as _公共取项目根目录
from ui.准备动画 import 计算透明控件组倒放参数
from ui.圆环频谱叠加 import 圆环频谱控件, 圆环频谱样式


def _取项目根目录() -> str:
    return _公共取项目根目录()


def _clamp01(v: float) -> float:
    if v <= 0.0:
        return 0.0
    if v >= 1.0:
        return 1.0
    return float(v)


def _lerp(a: float, b: float, t: float) -> float:
    x = _clamp01(t)
    return float(a) + (float(b) - float(a)) * x


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


def _平滑缩放(图: pygame.Surface, 目标尺寸: Tuple[int, int]) -> Optional[pygame.Surface]:
    if not isinstance(图, pygame.Surface):
        return None
    宽 = int(max(1, int(目标尺寸[0])))
    高 = int(max(1, int(目标尺寸[1])))
    try:
        return pygame.transform.smoothscale(图, (宽, 高)).convert_alpha()
    except Exception:
        try:
            return pygame.transform.scale(图, (宽, 高)).convert_alpha()
        except Exception:
            return None


def _旋转缩放(图: pygame.Surface, 角度: float, 缩放: float) -> Optional[pygame.Surface]:
    if not isinstance(图, pygame.Surface):
        return None
    try:
        return pygame.transform.rotozoom(图, float(角度), float(max(0.001, 缩放))).convert_alpha()
    except Exception:
        return None


def _取白色alpha蒙版(图: pygame.Surface) -> Optional[pygame.Surface]:
    if not isinstance(图, pygame.Surface):
        return None
    try:
        蒙版 = pygame.mask.from_surface(图)
        return 蒙版.to_surface(
            setcolor=(255, 255, 255, 255),
            unsetcolor=(255, 255, 255, 0),
        ).convert_alpha()
    except Exception:
        return None


def _调亮颜色(颜色: Tuple[int, int, int], 比例: float) -> Tuple[int, int, int]:
    比例 = float(max(0.0, min(1.0, 比例)))
    return (
        int(round(_lerp(颜色[0], 255.0, 比例))),
        int(round(_lerp(颜色[1], 255.0, 比例))),
        int(round(_lerp(颜色[2], 255.0, 比例))),
    )


def _调暗颜色(颜色: Tuple[int, int, int], 比例: float) -> Tuple[int, int, int]:
    比例 = float(max(0.0, min(1.0, 比例)))
    return (
        int(round(颜色[0] * (1.0 - 比例))),
        int(round(颜色[1] * (1.0 - 比例))),
        int(round(颜色[2] * (1.0 - 比例))),
    )


@dataclass(frozen=True)
class 成就动画主题:
    id: str
    资源目录名: str
    频谱主色: Optional[Tuple[int, int, int]] = None


@dataclass
class 成就动画资源:
    arrow: pygame.Surface
    bar: pygame.Surface
    board: pygame.Surface
    label: pygame.Surface
    ring_light: pygame.Surface
    wind: pygame.Surface
    频谱主色: Tuple[int, int, int]


@dataclass
class 控件组片段:
    图: pygame.Surface
    矩形: pygame.Rect
    组名: str


主题定义表: Dict[str, 成就动画主题] = {
    "full_perfect": 成就动画主题(
        id="full_perfect",
        资源目录名="full_perfect",
        频谱主色=(233, 146, 32),
    ),
    "full_combo": 成就动画主题(
        id="full_combo",
        资源目录名="full_combo",
        频谱主色=None,
    ),
}


def 默认结算前成就动画设置() -> Dict[str, float]:
    return {
        "阶段1底板入场秒": 9.0 / 60.0,
        "阶段2主体入场秒": 6.0 / 60.0,
        "阶段3标签入场秒": 8.0 / 60.0,
        "阶段4停留秒": 5.0,
        "阶段5整体收尾秒": 10.0 / 60.0,
        "阶段6HUD回收秒": 10.0 / 60.0,
        "底板组入场起始X偏移": -420.0,
        "底板组入场起始Y偏移": 80.0,
        "底板组旋转角度": 20.0,
        "底板组缩放倍率": 1.0,
        "底板组箭头速度": 820.0,
        "底板组箭头透明度": 255.0,
        "底板组箭头内部缩放": 0.74,
        "board组缩放倍率": 1.0,
        "board组入场起始透明度": 0.0,
        "board旋转速度": 32.0,
        "假频谱缩放倍率": 1.0,
        "所有控件等比缩放": 1.0,
        "label旋转角度": 0.0,
    }


def 读取结算前成就动画设置(设置路径: str) -> Dict[str, float]:
    默认 = 默认结算前成就动画设置()
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


def 保存结算前成就动画设置(设置路径: str, 设置: Dict[str, float]):
    os.makedirs(os.path.dirname(os.path.abspath(设置路径)), exist_ok=True)
    数据 = 默认结算前成就动画设置()
    for 键 in list(数据.keys()):
        try:
            数据[键] = float(设置.get(键, 数据[键]))
        except Exception:
            pass
    with open(设置路径, "w", encoding="utf-8") as f:
        json.dump(数据, f, ensure_ascii=False, indent=2)


def 计算结算前成就动画时间轴(设置: Dict[str, float]) -> Dict[str, float]:
    阶段1秒 = float(max(0.03, 设置.get("阶段1底板入场秒", 9.0 / 60.0)))
    阶段2秒 = float(max(0.03, 设置.get("阶段2主体入场秒", 6.0 / 60.0)))
    阶段3秒 = float(max(0.03, 设置.get("阶段3标签入场秒", 8.0 / 60.0)))
    阶段4秒 = float(max(0.05, 设置.get("阶段4停留秒", 5.0)))
    阶段5秒 = float(max(0.03, 设置.get("阶段5整体收尾秒", 10.0 / 60.0)))
    阶段6秒 = float(max(0.03, 设置.get("阶段6HUD回收秒", 10.0 / 60.0)))

    阶段1结束 = 阶段1秒
    阶段2结束 = 阶段1结束 + 阶段2秒
    阶段3结束 = 阶段2结束 + 阶段3秒
    阶段4结束 = 阶段3结束 + 阶段4秒
    阶段5结束 = 阶段4结束 + 阶段5秒
    阶段6结束 = 阶段5结束 + 阶段6秒
    return {
        "阶段1开始": 0.0,
        "阶段1结束": 阶段1结束,
        "阶段2开始": 阶段1结束,
        "阶段2结束": 阶段2结束,
        "阶段3开始": 阶段2结束,
        "阶段3结束": 阶段3结束,
        "阶段4开始": 阶段3结束,
        "阶段4结束": 阶段4结束,
        "阶段5开始": 阶段4结束,
        "阶段5结束": 阶段5结束,
        "阶段6开始": 阶段5结束,
        "阶段6结束": 阶段6结束,
        "总时长": 阶段6结束,
    }


class 结算前成就动画控制器:
    _帧率 = 60.0

    def __init__(self, 项目根: Optional[str] = None):
        self._项目根 = str(项目根 or _取项目根目录())
        self._设置路径 = os.path.join(self._项目根, "json", "结算前成就动画_设置.json")
        self._设置: Dict[str, float] = 读取结算前成就动画设置(self._设置路径)
        self._主题资源缓存: Dict[str, Optional[成就动画资源]] = {}
        self._当前主题id: str = ""
        self._当前主题资源: Optional[成就动画资源] = None
        self._开始系统秒: float = 0.0
        self._当前经过秒: float = 0.0
        self._激活: bool = False
        self._已完成: bool = False
        self._频谱控件: Optional[圆环频谱控件] = None
        self._频谱相位1 = [i * 0.73 + 0.15 for i in range(50)]
        self._频谱相位2 = [i * 1.17 + 0.37 for i in range(50)]
        self._频谱相位3 = [i * 0.41 + 0.93 for i in range(50)]
        self._频谱闸门相位 = [i * 0.57 + 0.22 for i in range(50)]
        self._顶部HUD片段: Optional[控件组片段] = None
        self._判定区片段列表: List[控件组片段] = []
        self._收尾缓存尺寸: Tuple[int, int] = (0, 0)

    def 取设置(self) -> Dict[str, float]:
        return dict(self._设置 or {})

    def 应用设置(self, 设置: Dict[str, float]):
        默认 = 默认结算前成就动画设置()
        新设置 = dict(self._设置 or {})
        for 键, 默认值 in 默认.items():
            try:
                新设置[键] = float((设置 or {}).get(键, 新设置.get(键, 默认值)))
            except Exception:
                新设置[键] = float(新设置.get(键, 默认值))
        self._设置 = 新设置
        总时长 = float(self.取总时长())
        if self._当前经过秒 > 总时长:
            self._当前经过秒 = 总时长
            self._已完成 = True
        if bool(self._激活):
            self._开始系统秒 = float(time.perf_counter() - self._当前经过秒)

    def 取总时长(self) -> float:
        return float(计算结算前成就动画时间轴(self._设置).get("总时长", 0.0))

    def 取经过秒(self) -> float:
        return float(self._当前经过秒)

    def 是否激活(self) -> bool:
        return bool(self._激活)

    def 是否完成(self) -> bool:
        return bool(self._激活 and self._已完成)

    def 取当前主题id(self) -> str:
        return str(self._当前主题id or "")

    def 取当前阶段名(self) -> str:
        if not bool(self._激活):
            return "未激活"
        经过秒 = float(self._当前经过秒)
        时间轴 = 计算结算前成就动画时间轴(self._设置)
        if 经过秒 < float(时间轴.get("阶段1结束", 0.0)):
            return "阶段1 底板入场"
        if 经过秒 < float(时间轴.get("阶段2结束", 0.0)):
            return "阶段2 Board 入场"
        if 经过秒 < float(时间轴.get("阶段3结束", 0.0)):
            return "阶段3 Label 入场"
        if 经过秒 < float(时间轴.get("阶段4结束", 0.0)):
            return "阶段4 停留播放"
        if 经过秒 < float(时间轴.get("阶段5结束", 0.0)):
            return "阶段5 整体收尾"
        return "阶段6 HUD / 判定区回收"

    def 启动(self, 主题id: str, 开始系统秒: Optional[float] = None) -> bool:
        self._设置 = 读取结算前成就动画设置(self._设置路径)
        资源 = self._取主题资源(主题id)
        if 资源 is None:
            self.停止()
            return False
        self._当前主题id = str(主题id or "")
        self._当前主题资源 = 资源
        self._开始系统秒 = float(开始系统秒 if 开始系统秒 is not None else time.perf_counter())
        self._当前经过秒 = 0.0
        self._激活 = True
        self._已完成 = False
        self._顶部HUD片段 = None
        self._判定区片段列表 = []
        self._收尾缓存尺寸 = (0, 0)
        self._创建频谱控件(资源)
        return True

    def 停止(self):
        self._当前主题id = ""
        self._当前主题资源 = None
        self._开始系统秒 = 0.0
        self._当前经过秒 = 0.0
        self._激活 = False
        self._已完成 = False
        self._频谱控件 = None
        self._顶部HUD片段 = None
        self._判定区片段列表 = []
        self._收尾缓存尺寸 = (0, 0)

    def 更新(self, 当前系统秒: Optional[float] = None):
        if not bool(self._激活):
            return
        当前 = float(当前系统秒 if 当前系统秒 is not None else time.perf_counter())
        self._当前经过秒 = max(0.0, 当前 - float(self._开始系统秒 or 0.0))
        if self._当前经过秒 >= self.取总时长():
            self._当前经过秒 = float(self.取总时长())
            self._已完成 = True

    def 设置经过秒(self, 经过秒: float):
        if not bool(self._激活):
            return
        总时长 = float(self.取总时长())
        self._当前经过秒 = max(0.0, min(float(经过秒), 总时长))
        self._开始系统秒 = float(time.perf_counter() - self._当前经过秒)
        self._已完成 = bool(self._当前经过秒 >= 总时长)

    def 需要隐藏顶部HUD(self) -> bool:
        return bool(self._激活 and self._当前经过秒 >= self._取阶段6开始秒())

    def 需要隐藏判定区(self) -> bool:
        return bool(self._激活 and self._当前经过秒 >= self._取阶段6开始秒())

    def 绘制(
        self,
        屏幕: pygame.Surface,
        当前系统秒: Optional[float] = None,
        左渲染器: Optional[Any] = None,
        左输入: Optional[Any] = None,
        右渲染器: Optional[Any] = None,
        右输入: Optional[Any] = None,
    ) -> bool:
        if not bool(self._激活) or not isinstance(屏幕, pygame.Surface):
            return False

        if 当前系统秒 is not None:
            self.更新(float(当前系统秒))

        资源 = self._当前主题资源
        if 资源 is None:
            return False

        self._绘制全局遮罩(屏幕)
        if self._当前经过秒 >= self._取阶段6开始秒():
            self._确保收尾片段(屏幕, 左渲染器, 左输入, 右渲染器, 右输入)
            self._绘制阶段6(屏幕)
            return True

        叠加层 = self._绘制成就层(屏幕.get_size(), 资源)
        if not isinstance(叠加层, pygame.Surface):
            return False
        屏幕.blit(叠加层, (0, 0))
        self._绘制爆闪(屏幕)
        return True

    def _取阶段6开始秒(self) -> float:
        return float(计算结算前成就动画时间轴(self._设置).get("阶段6开始", 0.0))

    def _取主题资源(self, 主题id: str) -> Optional[成就动画资源]:
        主题id = str(主题id or "").strip()
        if not 主题id:
            return None
        if 主题id in self._主题资源缓存:
            return self._主题资源缓存[主题id]

        主题 = 主题定义表.get(主题id)
        if 主题 is None:
            self._主题资源缓存[主题id] = None
            return None

        目录 = os.path.join(
            self._项目根,
            "UI-img",
            "游戏界面",
            str(主题.资源目录名 or ""),
        )
        if not os.path.isdir(目录):
            self._主题资源缓存[主题id] = None
            return None

        def _读图(文件名: str) -> Optional[pygame.Surface]:
            路径 = os.path.join(目录, 文件名)
            try:
                if os.path.isfile(路径):
                    return pygame.image.load(路径).convert_alpha()
            except Exception:
                return None
            return None

        arrow = _读图("arrow.png")
        bar = _读图("bar.png")
        board = _读图("board.png")
        label = _读图("label.png")
        ring_light = _读图("ring_light.png")
        wind = _读图("wind.png")
        if not all(
            isinstance(图, pygame.Surface)
            for 图 in (arrow, bar, board, label, ring_light, wind)
        ):
            self._主题资源缓存[主题id] = None
            return None

        频谱主色 = tuple(
            int(v)
            for v in (
                主题.频谱主色
                or self._估算主色(board)
                or self._估算主色(label)
                or (233, 146, 32)
            )[:3]
        )

        资源 = 成就动画资源(
            arrow=arrow,
            bar=bar,
            board=board,
            label=label,
            ring_light=ring_light,
            wind=wind,
            频谱主色=频谱主色,
        )
        self._主题资源缓存[主题id] = 资源
        return 资源

    def _估算主色(self, 图: Optional[pygame.Surface]) -> Optional[Tuple[int, int, int]]:
        if not isinstance(图, pygame.Surface):
            return None
        宽, 高 = 图.get_size()
        if 宽 <= 0 or 高 <= 0:
            return None
        步长x = max(1, int(宽 // 48))
        步长y = max(1, int(高 // 48))
        总r = 0
        总g = 0
        总b = 0
        数量 = 0
        try:
            for x in range(0, 宽, 步长x):
                for y in range(0, 高, 步长y):
                    c = 图.get_at((x, y))
                    if int(getattr(c, "a", 255)) < 24:
                        continue
                    总r += int(c.r)
                    总g += int(c.g)
                    总b += int(c.b)
                    数量 += 1
        except Exception:
            return None
        if 数量 <= 0:
            return None
        return (
            int(round(总r / 数量)),
            int(round(总g / 数量)),
            int(round(总b / 数量)),
        )

    def _创建频谱控件(self, 资源: 成就动画资源):
        主色 = tuple(int(v) for v in tuple(资源.频谱主色 or (233, 146, 32))[:3])
        调色板 = (
            _调暗颜色(主色, 0.24),
            主色,
            _调亮颜色(主色, 0.22),
            _调亮颜色(主色, 0.40),
        )
        样式 = 圆环频谱样式(
            条数=50,
            内半径=32,
            外延最大长度=54,
            圆环线宽=2,
            上升平滑=0.84,
            回落衰减=0.72,
            条宽=3,
            条间隔步长=1,
            条抗锯齿=True,
            旋转速度=0.0,
            启用底部强化=False,
            圆环颜色1=_调亮颜色(主色, 0.22),
            圆环颜色2=_调暗颜色(主色, 0.18),
            调色板=调色板,
        )
        self._频谱控件 = 圆环频谱控件(样式)

    def _生成假频谱(self, 当前秒: float, 条数: int) -> List[float]:
        结果: List[float] = []
        t = float(当前秒)
        for i in range(int(max(1, 条数))):
            波1 = 0.5 + 0.5 * math.sin(t * 6.3 + self._频谱相位1[i % len(self._频谱相位1)])
            波2 = 0.5 + 0.5 * math.sin(t * 10.7 + self._频谱相位2[i % len(self._频谱相位2)])
            波3 = 0.5 + 0.5 * math.sin(t * 3.8 + self._频谱相位3[i % len(self._频谱相位3)])
            闸门 = 0.25 + 0.75 * pow(
                0.5 + 0.5 * math.sin(t * 4.9 - i * 0.53 + self._频谱闸门相位[i % len(self._频谱闸门相位)]),
                2.1,
            )
            值 = ((波1 * 0.18) + (波2 * 0.57) + (波3 * 0.25)) * 闸门
            值 = 0.06 + min(1.0, pow(max(0.0, 值), 1.45) * 1.10)
            结果.append(float(max(0.0, min(1.0, 值))))
        return 结果

    def _生成方形贴边半径数组(self, 半宽: float, 条数: int) -> List[float]:
        结果: List[float] = []
        半宽 = float(max(8.0, 半宽))
        for i in range(int(max(8, 条数))):
            角度 = math.tau * (float(i) / float(max(1, 条数)))
            dx = abs(math.cos(角度))
            dy = abs(math.sin(角度))
            除数 = max(0.0001, dx, dy)
            结果.append(float(半宽 / 除数))
        return 结果

    def _绘制成就层(
        self,
        屏幕尺寸: Tuple[int, int],
        资源: 成就动画资源,
    ) -> Optional[pygame.Surface]:
        屏宽, 屏高 = int(max(1, 屏幕尺寸[0])), int(max(1, 屏幕尺寸[1]))
        图层 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA).convert_alpha()
        布局 = self._计算布局(屏幕尺寸, 资源)
        self._绘制阶段1_底板(图层, 资源, 布局)
        self._绘制阶段2_3_主体(图层, 资源, 布局)

        时间轴 = 计算结算前成就动画时间轴(self._设置)
        阶段5开始 = float(时间轴.get("阶段5开始", 0.0))
        if self._当前经过秒 < 阶段5开始:
            return 图层

        收尾t = _clamp01(
            (self._当前经过秒 - float(阶段5开始))
            / max(0.001, float(时间轴.get("阶段5结束", 阶段5开始) - 阶段5开始))
        )
        return self._应用整体收尾(图层, 收尾t)

    def _计算布局(
        self,
        屏幕尺寸: Tuple[int, int],
        资源: 成就动画资源,
    ) -> Dict[str, Any]:
        屏宽, 屏高 = int(max(1, 屏幕尺寸[0])), int(max(1, 屏幕尺寸[1]))
        最终中心 = (int(round(屏宽 * 0.5)), int(round(屏高 * 0.56)))
        全局缩放 = float(max(0.30, min(2.40, float(self._设置.get("所有控件等比缩放", 1.0) or 1.0))))
        底板组缩放倍率 = float(max(0.30, min(2.40, float(self._设置.get("底板组缩放倍率", 1.0) or 1.0))))
        board组缩放倍率 = float(max(0.30, min(2.40, float(self._设置.get("board组缩放倍率", 1.0) or 1.0))))
        bar基准宽 = float(min(资源.bar.get_width() * 0.82, max(720.0, 屏宽 * 0.86)))
        board基准宽 = float(min(资源.board.get_width() * 0.86, max(188.0, min(屏宽, 屏高) * 0.38)))
        label基准宽 = float(min(资源.label.get_width() * 0.90, max(420.0, bar基准宽 * 底板组缩放倍率 * 0.68)))
        bar目标宽 = int(bar基准宽 * 底板组缩放倍率 * 全局缩放)
        board目标宽 = int(board基准宽 * board组缩放倍率 * 全局缩放)
        label目标宽 = int(label基准宽 * 全局缩放)
        return {
            "中心": 最终中心,
            "bar目标宽": int(max(400, bar目标宽)),
            "board目标宽": int(max(140, board目标宽)),
            "label目标宽": int(max(240, label目标宽)),
            "底板偏移x": float(self._设置.get("底板组入场起始X偏移", -420.0) or -420.0),
            "底板偏移y": float(self._设置.get("底板组入场起始Y偏移", 80.0) or 80.0),
            "底板角度": float(self._设置.get("底板组旋转角度", 20.0) or 20.0),
        }

    def _绘制阶段1_底板(
        self,
        屏幕: pygame.Surface,
        资源: 成就动画资源,
        布局: Dict[str, Any],
    ):
        if not isinstance(屏幕, pygame.Surface):
            return
        时间轴 = 计算结算前成就动画时间轴(self._设置)
        阶段1开始 = float(时间轴.get("阶段1开始", 0.0))
        阶段1结束 = float(时间轴.get("阶段1结束", 0.0))
        进度 = _clamp01(
            (self._当前经过秒 - 阶段1开始) / max(0.001, 阶段1结束 - 阶段1开始)
        )
        入场t = _back_out(进度)
        最终中心x, 最终中心y = tuple(布局["中心"])
        中心x = int(round(最终中心x + _lerp(float(布局["底板偏移x"]), 0.0, 入场t)))
        中心y = int(round(最终中心y + _lerp(float(布局["底板偏移y"]), 0.0, 入场t)))

        bar目标宽 = int(布局["bar目标宽"])
        bar缩放 = float(bar目标宽) / float(max(1, 资源.bar.get_width()))
        bar目标高 = int(max(8, round(float(资源.bar.get_height()) * bar缩放)))
        箭头内部缩放 = float(max(0.10, min(2.50, float(self._设置.get("底板组箭头内部缩放", 0.74) or 0.74))))
        arrow目标高 = int(max(8, round(float(bar目标高) * 箭头内部缩放)))
        arrow缩放 = float(arrow目标高) / float(max(1, 资源.arrow.get_height()))
        arrow目标宽 = int(max(8, round(float(资源.arrow.get_width()) * arrow缩放)))
        bar图 = _平滑缩放(资源.bar, (bar目标宽, bar目标高))
        arrow图 = _平滑缩放(资源.arrow, (arrow目标宽, arrow目标高))
        if not isinstance(bar图, pygame.Surface) or not isinstance(arrow图, pygame.Surface):
            return

        组合 = pygame.Surface(bar图.get_size(), pygame.SRCALPHA).convert_alpha()
        蒙版 = _取白色alpha蒙版(bar图)
        arrow层 = pygame.Surface(bar图.get_size(), pygame.SRCALPHA).convert_alpha()
        arrow层.fill((0, 0, 0, 0))
        速度 = float(max(40.0, float(self._设置.get("底板组箭头速度", 820.0) or 820.0)))
        箭头透明度 = int(
            max(0, min(255, round(float(self._设置.get("底板组箭头透明度", 255.0) or 255.0))))
        )
        偏移x = float(self._当前经过秒 * 速度) % float(max(1, arrow图.get_width()))
        y = int(round((bar图.get_height() - arrow图.get_height()) * 0.5))
        起始x = int(round(-偏移x)) - int(arrow图.get_width())
        while 起始x < int(bar图.get_width() + arrow图.get_width()):
            arrow层.blit(arrow图, (起始x, y))
            起始x += int(arrow图.get_width())
        if isinstance(蒙版, pygame.Surface):
            arrow层.blit(蒙版, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        arrow层.set_alpha(箭头透明度)
        组合.blit(bar图, (0, 0))
        组合.blit(arrow层, (0, 0))

        斜切 = pygame.Surface(组合.get_size(), pygame.SRCALPHA).convert_alpha()
        宽, 高 = 组合.get_size()
        角度 = float(布局.get("底板角度", 20.0) or 20.0)
        偏移 = int(
            max(
                0,
                min(
                    宽 - 2,
                    round(float(高) * math.tan(math.radians(abs(角度)))),
                ),
            )
        )
        if 角度 >= 0.0:
            多边形点 = [
                (0, 0),
                (宽 - 偏移, 0),
                (宽, 高),
                (0, 高),
            ]
        else:
            多边形点 = [
                (0, 0),
                (宽, 0),
                (宽 - 偏移, 高),
                (0, 高),
            ]
        pygame.draw.polygon(斜切, (255, 255, 255, 255), 多边形点)
        组合.blit(斜切, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        旋转后 = _旋转缩放(组合, float(布局["底板角度"]), 1.0)
        if not isinstance(旋转后, pygame.Surface):
            return
        rect = 旋转后.get_rect(center=(中心x, 中心y))
        屏幕.blit(旋转后, rect.topleft)

    def _绘制阶段2_3_主体(
        self,
        屏幕: pygame.Surface,
        资源: 成就动画资源,
        布局: Dict[str, Any],
    ):
        时间轴 = 计算结算前成就动画时间轴(self._设置)
        阶段2起点 = float(时间轴.get("阶段2开始", 0.0))
        阶段2结束 = float(时间轴.get("阶段2结束", 阶段2起点))
        阶段2t = _clamp01(
            (self._当前经过秒 - float(阶段2起点)) / max(0.001, 阶段2结束 - 阶段2起点)
        )
        if 阶段2t <= 0.0:
            return

        中心 = tuple(int(v) for v in tuple(布局["中心"])[:2])
        board目标宽 = int(布局["board目标宽"])
        board本体缩放 = float(board目标宽) / float(max(1, 资源.board.get_width()))
        ring目标宽 = int(round(board目标宽 * (资源.ring_light.get_width() / max(1.0, float(资源.board.get_width())))))
        wind目标宽 = int(round(board目标宽 * 1.08))
        假频谱缩放 = float(max(0.20, min(8.00, float(self._设置.get("假频谱缩放倍率", 1.0) or 1.0))))
        频谱内半径 = int(max(18, round(board目标宽 * 0.18 * 假频谱缩放)))
        频谱外延 = int(max(20, round(board目标宽 * 0.11 * 假频谱缩放)))
        频谱外径 = int((频谱内半径 + 频谱外延) * 2 + max(12, round(board目标宽 * 0.04)))
        group尺寸 = int(max(board目标宽, ring目标宽, wind目标宽, 频谱外径) + 96)
        group图层 = pygame.Surface((group尺寸, group尺寸), pygame.SRCALPHA).convert_alpha()
        group中心 = (group尺寸 // 2, group尺寸 // 2)

        频谱控件 = self._频谱控件
        if 频谱控件 is not None:
            主色 = tuple(int(v) for v in tuple(资源.频谱主色 or (233, 146, 32))[:3])
            频谱控件.样式.条数 = 50
            频谱控件.样式.条宽 = int(max(2, round(board目标宽 * 0.0105)))
            频谱控件.样式.圆环线宽 = int(max(1, round(board目标宽 * 0.010)))
            频谱控件.样式.内半径 = int(频谱内半径)
            频谱控件.样式.外延最大长度 = int(频谱外延)
            频谱控件.样式.圆环颜色1 = _调亮颜色(主色, 0.20)
            频谱控件.样式.圆环颜色2 = _调暗颜色(主色, 0.18)
            频谱控件.设置贴边半径数组(None)
            频谱控件.更新(self._生成假频谱(float(self._当前经过秒), 50))
            圆环频谱控件.按绘制数据绘制(
                group图层,
                频谱控件.取绘制数据(group中心, float(self._当前经过秒)),
            )

        board图 = _旋转缩放(
            资源.board,
            float(self._当前经过秒) * float(self._设置.get("board旋转速度", 32.0) or 32.0),
            board本体缩放,
        )
        if isinstance(board图, pygame.Surface):
            boardrect = board图.get_rect(center=group中心)
            group图层.blit(board图, boardrect.topleft)

        ring图 = _旋转缩放(
            资源.ring_light,
            float(self._当前经过秒) * 28.0,
            float(ring目标宽) / float(max(1, 资源.ring_light.get_width())),
        )
        if isinstance(ring图, pygame.Surface):
            ring图.set_alpha(196)
            ringrect = ring图.get_rect(center=group中心)
            group图层.blit(ring图, ringrect.topleft)

        wind图 = _旋转缩放(
            资源.wind,
            -float(self._当前经过秒) * 96.0,
            float(wind目标宽) / float(max(1, 资源.wind.get_width())),
        )
        if isinstance(wind图, pygame.Surface):
            wind图.set_alpha(int(round(_lerp(82.0, 156.0, 0.5 + 0.5 * math.sin(self._当前经过秒 * 6.2)))))
            windrect = wind图.get_rect(center=group中心)
            group图层.blit(wind图, windrect.topleft)

        group缩放 = _lerp(1.28, 1.0, _back_out(阶段2t))
        board组入场起始透明度 = float(
            max(0.0, min(255.0, float(self._设置.get("board组入场起始透明度", 0.0) or 0.0)))
        )
        group透明度 = int(round(_lerp(board组入场起始透明度, 255.0, _ease_in_out(阶段2t))))
        group目标边 = int(max(4, round(float(group尺寸) * group缩放)))
        group输出 = _平滑缩放(group图层, (group目标边, group目标边))
        if isinstance(group输出, pygame.Surface):
            group输出.set_alpha(group透明度)
            grouprect = group输出.get_rect(center=中心)
            屏幕.blit(group输出, grouprect.topleft)

        阶段3起点 = float(时间轴.get("阶段3开始", 阶段2结束))
        阶段3结束 = float(时间轴.get("阶段3结束", 阶段3起点))
        阶段3t = _clamp01(
            (self._当前经过秒 - float(阶段3起点)) / max(0.001, 阶段3结束 - 阶段3起点)
        )
        if 阶段3t <= 0.0:
            return
        阶段5起点 = float(时间轴.get("阶段5开始", 阶段3结束))
        阶段5结束 = float(时间轴.get("阶段5结束", 阶段5起点))
        收尾label放大t = _clamp01(
            (self._当前经过秒 - 阶段5起点) / max(0.001, 阶段5结束 - 阶段5起点)
        )
        label退场缩放 = _lerp(1.0, 1.20, _ease_in_out(收尾label放大t))
        label终宽 = float(布局["label目标宽"])
        label终高 = float(资源.label.get_height()) * (label终宽 / float(max(1, 资源.label.get_width())))
        label宽 = int(max(64, round(label终宽 * _lerp(0.60, 1.10, _ease_out_cubic(阶段3t)) * label退场缩放)))
        label高 = int(max(8, round(label终高 * label退场缩放)))
        label图 = _旋转缩放(
            _平滑缩放(资源.label, (label宽, label高)),
            float(self._设置.get("label旋转角度", 0.0) or 0.0),
            1.0,
        )
        if not isinstance(label图, pygame.Surface):
            return
        label图.set_alpha(int(round(_lerp(178.0, 255.0, _ease_in_out(阶段3t)))))
        labelrect = label图.get_rect(center=中心)
        屏幕.blit(label图, labelrect.topleft)

    def _应用整体收尾(self, 图层: pygame.Surface, 收尾t: float) -> Optional[pygame.Surface]:
        结果 = 图层
        if 收尾t > 0.0:
            缩小比 = int(max(1, round(1.0 + 收尾t * 5.0)))
            小宽 = int(max(1, round(结果.get_width() / 缩小比)))
            小高 = int(max(1, round(结果.get_height() / 缩小比)))
            try:
                缩小图 = pygame.transform.smoothscale(结果, (小宽, 小高))
                结果 = pygame.transform.smoothscale(缩小图, 结果.get_size()).convert_alpha()
            except Exception:
                结果 = 结果.copy().convert_alpha()
        else:
            结果 = 结果.copy().convert_alpha()

        承载 = pygame.Surface(图层.get_size(), pygame.SRCALPHA).convert_alpha()
        结果.set_alpha(int(round(255.0 * (1.0 - _ease_in_out(收尾t)))))
        承载.blit(结果, (0, 0))
        return 承载

    def _绘制爆闪(self, 屏幕: pygame.Surface):
        时间轴 = 计算结算前成就动画时间轴(self._设置)
        阶段2起点 = float(时间轴.get("阶段2开始", 0.0))
        if self._当前经过秒 < 阶段2起点:
            return
        局部秒 = float(self._当前经过秒 - 阶段2起点)
        阶段2秒 = float(max(0.001, 时间轴.get("阶段2结束", 阶段2起点) - 阶段2起点))
        if 局部秒 > 阶段2秒:
            return
        帧序列 = [0.20, 0.30, 0.50, 0.45, 0.30, 0.05, 0.0]
        位置 = float(_clamp01(局部秒 / 阶段2秒) * float(len(帧序列) - 1))
        左 = int(max(0, min(len(帧序列) - 2, int(math.floor(位置)))))
        右 = int(min(len(帧序列) - 1, 左 + 1))
        t = float(位置 - math.floor(位置))
        透明度 = int(round(_lerp(float(帧序列[左]), float(帧序列[右]), t) * 255.0))
        if 透明度 <= 0:
            return
        闪层 = pygame.Surface(屏幕.get_size(), pygame.SRCALPHA).convert_alpha()
        闪层.fill((255, 255, 255, int(max(0, min(255, 透明度)))))
        屏幕.blit(闪层, (0, 0))

    def _绘制全局遮罩(self, 屏幕: pygame.Surface):
        if not isinstance(屏幕, pygame.Surface):
            return
        遮罩 = pygame.Surface(屏幕.get_size(), pygame.SRCALPHA).convert_alpha()
        遮罩.fill((0, 0, 0, 136))
        屏幕.blit(遮罩, (0, 0))

    def _确保收尾片段(
        self,
        屏幕: pygame.Surface,
        左渲染器: Optional[Any],
        左输入: Optional[Any],
        右渲染器: Optional[Any],
        右输入: Optional[Any],
    ):
        当前尺寸 = tuple(int(v) for v in 屏幕.get_size())
        if 当前尺寸 != tuple(self._收尾缓存尺寸):
            self._顶部HUD片段 = None
            self._判定区片段列表 = []
            self._收尾缓存尺寸 = 当前尺寸
        if self._顶部HUD片段 is None and 左渲染器 is not None and 左输入 is not None:
            self._顶部HUD片段 = self._抓取控件组片段(
                左渲染器,
                "取准备动画顶部HUD图层",
                屏幕,
                左输入,
                "顶部HUD",
            )
        if not self._判定区片段列表:
            if 左渲染器 is not None and 左输入 is not None:
                左片段 = self._抓取控件组片段(
                    左渲染器,
                    "取准备动画判定区图层",
                    屏幕,
                    左输入,
                    "左判定区",
                )
                if 左片段 is not None:
                    self._判定区片段列表.append(左片段)
            if 右渲染器 is not None and 右输入 is not None:
                右片段 = self._抓取控件组片段(
                    右渲染器,
                    "取准备动画判定区图层",
                    屏幕,
                    右输入,
                    "右判定区",
                )
                if 右片段 is not None:
                    self._判定区片段列表.append(右片段)

    def _抓取控件组片段(
        self,
        渲染器: Any,
        方法名: str,
        屏幕: pygame.Surface,
        输入: Any,
        组名: str,
    ) -> Optional[控件组片段]:
        方法 = getattr(渲染器, 方法名, None)
        if not callable(方法):
            return None
        try:
            图层, 矩形 = 方法(屏幕, 输入)
        except Exception:
            return None
        if (not isinstance(图层, pygame.Surface)) or (not isinstance(矩形, pygame.Rect)):
            return None
        if 矩形.w <= 0 or 矩形.h <= 0:
            return None
        try:
            局部图 = 图层.subsurface(矩形).copy().convert_alpha()
        except Exception:
            return None
        return 控件组片段(图=局部图, 矩形=矩形.copy(), 组名=str(组名 or ""))

    def _绘制阶段6(self, 屏幕: pygame.Surface):
        收尾开始 = self._取阶段6开始秒()
        时间轴 = 计算结算前成就动画时间轴(self._设置)
        收尾t = _clamp01(
            (self._当前经过秒 - float(收尾开始))
            / max(0.001, float(时间轴.get("阶段6结束", 收尾开始) - 收尾开始))
        )
        顶部参数 = 计算透明控件组倒放参数(
            进度=收尾t,
            起始偏移y=0.0,
            结束偏移y=-96.0,
            起始alpha=255.0,
            结束alpha=0.0,
            位移缓动=_ease_in_out,
            alpha缓动=_ease_in_out,
        )
        if self._顶部HUD片段 is not None:
            self._绘制片段变换(
                屏幕,
                self._顶部HUD片段,
                缩放=_lerp(1.0, 0.96, _ease_in_out(收尾t)),
                alpha=int(顶部参数.get("alpha", 255)),
                偏移x=int(顶部参数.get("偏移x", 0)),
                偏移y=int(顶部参数.get("偏移y", 0)),
            )

        判定alpha = int(round(255.0 * (1.0 - _ease_in_out(收尾t))))
        判定缩放 = _lerp(1.0, 0.82, _ease_in_out(收尾t))
        判定偏移y = int(round(_lerp(0.0, 36.0, _ease_in_out(收尾t))))
        for 片段 in list(self._判定区片段列表 or []):
            self._绘制片段变换(
                屏幕,
                片段,
                缩放=判定缩放,
                alpha=判定alpha,
                偏移x=0,
                偏移y=判定偏移y,
            )

    def _绘制片段变换(
        self,
        屏幕: pygame.Surface,
        片段: 控件组片段,
        缩放: float = 1.0,
        alpha: int = 255,
        偏移x: int = 0,
        偏移y: int = 0,
    ):
        if not isinstance(屏幕, pygame.Surface) or not isinstance(片段, 控件组片段):
            return
        if int(alpha) <= 0:
            return
        图 = 片段.图
        if not isinstance(图, pygame.Surface):
            return
        目标图 = 图
        if abs(float(缩放) - 1.0) > 0.001:
            目标宽 = int(max(1, round(float(图.get_width()) * float(缩放))))
            目标高 = int(max(1, round(float(图.get_height()) * float(缩放))))
            缩放图 = _平滑缩放(图, (目标宽, 目标高))
            if isinstance(缩放图, pygame.Surface):
                目标图 = 缩放图
        目标图 = 目标图.copy().convert_alpha()
        目标图.set_alpha(int(max(0, min(255, int(alpha)))))
        rect = 目标图.get_rect(
            center=(
                int(片段.矩形.centerx + int(偏移x)),
                int(片段.矩形.centery + int(偏移y)),
            )
        )
        屏幕.blit(目标图, rect.topleft)
