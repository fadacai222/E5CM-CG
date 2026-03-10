import math
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pygame


def _取项目根目录() -> str:
    try:
        已缓存路径 = getattr(_取项目根目录, "_缓存路径", "")
        if isinstance(已缓存路径, str) and 已缓存路径 and os.path.isdir(已缓存路径):
            return 已缓存路径
    except Exception:
        pass

    try:
        import sys
    except Exception:
        sys = None

    def _规范路径(路径: str) -> str:
        try:
            return os.path.abspath(str(路径 or "").strip())
        except Exception:
            return ""

    def _目录评分(目录: str) -> int:
        try:
            if (not 目录) or (not os.path.isdir(目录)):
                return -1

            分数 = 0

            if os.path.isdir(os.path.join(目录, "UI-img")):
                分数 += 4
            if os.path.isdir(os.path.join(目录, "json")):
                分数 += 3
            if os.path.isdir(os.path.join(目录, "冷资源")):
                分数 += 2
            if os.path.isdir(os.path.join(目录, "core")):
                分数 += 1
            if os.path.isdir(os.path.join(目录, "ui")):
                分数 += 1

            return 分数
        except Exception:
            return -1

    候选起点列表 = []

    try:
        if sys and getattr(sys, "frozen", False):
            临时资源目录 = _规范路径(getattr(sys, "_MEIPASS", ""))
            if 临时资源目录:
                候选起点列表.append(临时资源目录)

            可执行目录 = _规范路径(os.path.dirname(os.path.abspath(sys.executable)))
            if 可执行目录:
                候选起点列表.append(可执行目录)
    except Exception:
        pass

    try:
        脚本目录 = _规范路径(os.path.dirname(os.path.abspath(__file__)))
        if 脚本目录:
            候选起点列表.append(脚本目录)
    except Exception:
        pass

    try:
        工作目录 = _规范路径(os.getcwd())
        if 工作目录:
            候选起点列表.append(工作目录)
    except Exception:
        pass

    去重后候选 = []
    已见路径 = set()
    for 路径 in 候选起点列表:
        规范后 = _规范路径(路径)
        if (not 规范后) or (规范后 in 已见路径):
            continue
        已见路径.add(规范后)
        去重后候选.append(规范后)

    最佳目录 = ""
    最佳分数 = -1
    已检查目录 = set()

    for 起点 in 去重后候选:
        当前目录 = 起点
        for _ in range(12):
            当前目录 = _规范路径(当前目录)
            if (not 当前目录) or (当前目录 in 已检查目录):
                break

            已检查目录.add(当前目录)
            当前分数 = _目录评分(当前目录)

            if 当前分数 > 最佳分数:
                最佳分数 = 当前分数
                最佳目录 = 当前目录

            if 当前分数 >= 7:
                setattr(_取项目根目录, "_缓存路径", 当前目录)
                return 当前目录

            上级目录 = os.path.dirname(当前目录)
            if 上级目录 == 当前目录:
                break
            当前目录 = 上级目录

    if 最佳目录:
        setattr(_取项目根目录, "_缓存路径", 最佳目录)
        return 最佳目录

    for 路径 in 去重后候选:
        if 路径 and os.path.isdir(路径):
            setattr(_取项目根目录, "_缓存路径", 路径)
            return 路径

    try:
        回退目录 = _规范路径(os.getcwd())
    except Exception:
        回退目录 = "."

    setattr(_取项目根目录, "_缓存路径", 回退目录)
    return 回退目录


@dataclass
class 圆环频谱样式:
    条数: int = 200

    # 下面三个会根据“目标矩形”动态重算
    内半径: int = 32
    外延最大长度: int = 136
    圆环线宽: int = 2

    # 下探到低频段，重低音会明显带动外圈跳动。
    频率下限: float = 55.0
    频率上限: float = 9500.0

    上升平滑: float = 0.78
    回落衰减: float = 0.84

    条宽: int = 2
    条间隔步长: int = 1  # 1=无间隔，2=隔一条绘制
    条抗锯齿: bool = True
    旋转速度: float = 0.0  # 弧度/秒（默认不转，观感更接近原版）

    # 叠加层外观（尽量不遮挡）
    圆环颜色1: Tuple[int, int, int] = (0, 246, 255)
    圆环颜色2: Tuple[int, int, int] = (212, 36, 255)


class 圆环频谱控件:
    def __init__(self, 样式: 圆环频谱样式):
        self.样式 = 样式
        self._上一幅度 = np.zeros(self.样式.条数, dtype=np.float32)
        self._贴边半径数组: Optional[np.ndarray] = None
        self._形状旋转偏移弧度: float = 0.0

    def 设置贴边半径数组(self, 半径数组: Optional[np.ndarray]):
        if 半径数组 is None:
            self._贴边半径数组 = None
            return
        半径数组 = np.asarray(半径数组, dtype=np.float32)
        if 半径数组.size != int(self.样式.条数):
            self._贴边半径数组 = None
            return
        self._贴边半径数组 = np.clip(半径数组, 1.0, 100000.0)

    def 设置形状旋转偏移(self, 弧度: float):
        try:
            self._形状旋转偏移弧度 = float(弧度)
        except Exception:
            self._形状旋转偏移弧度 = 0.0

    def 更新(self, 新幅度: np.ndarray):
        if 新幅度 is None:
            return
        新幅度 = np.asarray(新幅度, dtype=np.float32)
        if 新幅度.size <= 0:
            return
        if 新幅度.size != int(self.样式.条数):
            self.样式.条数 = int(新幅度.size)
        if self._上一幅度.size != 新幅度.size:
            self._上一幅度 = np.zeros(int(新幅度.size), dtype=np.float32)

        上升平滑 = float(self.样式.上升平滑)
        回落衰减 = float(self.样式.回落衰减)

        上升掩码 = 新幅度 >= self._上一幅度
        平滑后 = self._上一幅度.copy()
        平滑后[上升掩码] = (1.0 - 上升平滑) * self._上一幅度[
            上升掩码
        ] + 上升平滑 * 新幅度[上升掩码]
        平滑后[~上升掩码] = self._上一幅度[~上升掩码] * 回落衰减

        self._上一幅度 = np.clip(平滑后, 0.0, 1.0)

    def 取绘制数据(
        self, 中心: Tuple[int, int], 当前时间秒: float
    ) -> Dict[str, object]:
        cx, cy = int(中心[0]), int(中心[1])
        基础相位 = 当前时间秒 * float(self.样式.旋转速度)

        条数 = int(max(8, int(self.样式.条数)))
        if self._上一幅度.size != 条数:
            if self._上一幅度.size <= 0:
                self._上一幅度 = np.zeros(条数, dtype=np.float32)
            else:
                src = np.linspace(
                    0.0,
                    float(max(0, self._上一幅度.size - 1)),
                    int(self._上一幅度.size),
                    dtype=np.float32,
                )
                dst = np.linspace(
                    0.0, float(max(0, self._上一幅度.size - 1)), 条数, dtype=np.float32
                )
                self._上一幅度 = np.interp(
                    dst, src, self._上一幅度.astype(np.float32)
                ).astype(np.float32)

        内半径 = float(self.样式.内半径)
        最大长度 = float(self.样式.外延最大长度)
        贴边半径数组 = self._贴边半径数组
        轮廓1 = []
        轮廓2 = []
        线条列表 = []
        间隔步长 = int(max(1, min(8, int(getattr(self.样式, "条间隔步长", 1) or 1))))
        形状偏移索引 = (
            (float(self._形状旋转偏移弧度) % math.tau) / math.tau * float(条数)
            if 贴边半径数组 is not None
            else 0.0
        )

        for i in range(条数):
            if 间隔步长 > 1 and (i % 间隔步长) != 0:
                continue
            角度 = (i / 条数) * math.tau + 基础相位
            幅度 = float(self._上一幅度[i])
            if 贴边半径数组 is not None:
                起始半径 = self._按浮点索引取值(贴边半径数组, float(i) - 形状偏移索引)
                起始半径 = max(8.0, float(起始半径) - max(1.5, float(self.样式.条宽)))
            else:
                起始半径 = 内半径

            cos值 = math.cos(角度)
            sin值 = math.sin(角度)
            底部权重 = float(max(0.0, min(1.0, (sin值 + 1.0) * 0.5)))
            底部权重 = float(0.12 + 0.88 * (底部权重**1.75))
            毛刺系数 = float(0.86 + 0.30 * abs(math.sin(float(i) * 2.173)))
            长度 = (幅度**0.62) * 最大长度 * 底部权重 * 毛刺系数

            x1 = cx + cos值 * 起始半径
            y1 = cy + sin值 * 起始半径
            x2 = cx + cos值 * (起始半径 + 长度)
            y2 = cy + sin值 * (起始半径 + 长度)

            颜色 = self._按角度取颜色(角度, 幅度)
            if 贴边半径数组 is not None:
                轮廓1.append((x1, y1))
                轮廓2.append(
                    (
                        cx + cos值 * max(4.0, 起始半径 - 2.0),
                        cy + sin值 * max(4.0, 起始半径 - 2.0),
                    )
                )
            线条列表.append(
                {
                    "起点": (float(x1), float(y1)),
                    "终点": (float(x2), float(y2)),
                    "颜色": tuple(int(v) for v in 颜色[:3]),
                    "宽度": int(max(1, int(self.样式.条宽))),
                    "抗锯齿": bool(self.样式.条抗锯齿),
                }
            )

        数据: Dict[str, object] = {
            "线条": 线条列表,
            "轮廓": [],
            "圆": [],
        }
        if 贴边半径数组 is not None and len(轮廓1) >= 3:
            数据["轮廓"] = [
                {
                    "点列": [(float(x), float(y)) for x, y in 轮廓1],
                    "颜色": tuple(int(v) for v in self.样式.圆环颜色1[:3]),
                    "闭合": True,
                    "抗锯齿": True,
                },
                {
                    "点列": [(float(x), float(y)) for x, y in 轮廓2],
                    "颜色": tuple(int(v) for v in self.样式.圆环颜色2[:3]),
                    "闭合": True,
                    "抗锯齿": True,
                },
            ]
        else:
            数据["圆"] = [
                {
                    "中心": (int(cx), int(cy)),
                    "半径": int(self.样式.内半径),
                    "宽度": int(max(1, int(self.样式.圆环线宽))),
                    "颜色": tuple(int(v) for v in self.样式.圆环颜色1[:3]),
                },
                {
                    "中心": (int(cx), int(cy)),
                    "半径": int(self.样式.内半径 + 6),
                    "宽度": 1,
                    "颜色": tuple(int(v) for v in self.样式.圆环颜色2[:3]),
                },
            ]
        return 数据

    @staticmethod
    def 按绘制数据绘制(屏幕: pygame.Surface, 数据: Dict[str, object]):
        if 屏幕 is None or not isinstance(数据, dict):
            return
        for 线条 in list(数据.get("线条", []) or []):
            if not isinstance(线条, dict):
                continue
            起点 = tuple(线条.get("起点", (0.0, 0.0)) or (0.0, 0.0))
            终点 = tuple(线条.get("终点", (0.0, 0.0)) or (0.0, 0.0))
            颜色 = tuple(int(v) for v in tuple(线条.get("颜色", (255, 255, 255)) or (255, 255, 255))[:3])
            宽度 = int(max(1, int(线条.get("宽度", 1) or 1)))
            抗锯齿 = bool(线条.get("抗锯齿", True))
            x1, y1 = float(起点[0]), float(起点[1])
            x2, y2 = float(终点[0]), float(终点[1])
            if 抗锯齿:
                pygame.draw.aaline(屏幕, 颜色, (x1, y1), (x2, y2), 1)
                if 宽度 > 1:
                    for k in range(1, 宽度):
                        pygame.draw.aaline(
                            屏幕,
                            颜色,
                            (x1 + k * 0.4, y1 + k * 0.4),
                            (x2 + k * 0.4, y2 + k * 0.4),
                            1,
                        )
            else:
                pygame.draw.line(屏幕, 颜色, (x1, y1), (x2, y2), 宽度)

        for 轮廓 in list(数据.get("轮廓", []) or []):
            if not isinstance(轮廓, dict):
                continue
            点列 = list(轮廓.get("点列", []) or [])
            if len(点列) < 2:
                continue
            颜色 = tuple(int(v) for v in tuple(轮廓.get("颜色", (255, 255, 255)) or (255, 255, 255))[:3])
            闭合 = bool(轮廓.get("闭合", True))
            抗锯齿 = bool(轮廓.get("抗锯齿", True))
            try:
                if 抗锯齿:
                    pygame.draw.aalines(屏幕, 颜色, 闭合, 点列, 1)
                else:
                    pygame.draw.lines(屏幕, 颜色, 闭合, 点列, 1)
            except Exception:
                pass

        for 圆 in list(数据.get("圆", []) or []):
            if not isinstance(圆, dict):
                continue
            中心 = tuple(int(v) for v in tuple(圆.get("中心", (0, 0)) or (0, 0))[:2])
            半径 = int(max(1, int(圆.get("半径", 1) or 1)))
            宽度 = int(max(1, int(圆.get("宽度", 1) or 1)))
            颜色 = tuple(int(v) for v in tuple(圆.get("颜色", (255, 255, 255)) or (255, 255, 255))[:3])
            pygame.draw.circle(屏幕, 颜色, 中心, 半径, 宽度)

    def 绘制(self, 屏幕: pygame.Surface, 中心: Tuple[int, int], 当前时间秒: float):
        self.按绘制数据绘制(屏幕, self.取绘制数据(中心, 当前时间秒))

    def _按浮点索引取值(self, 数组: np.ndarray, 索引: float) -> float:
        if 数组.size <= 0:
            return 0.0
        基 = float(索引) % float(数组.size)
        左 = int(math.floor(基)) % int(数组.size)
        右 = (左 + 1) % int(数组.size)
        t = float(基 - math.floor(基))
        return float(数组[左] * (1.0 - t) + 数组[右] * t)

    def _按角度取颜色(self, 角度: float, 幅度: float) -> Tuple[int, int, int]:
        t = float((角度 % math.tau) / math.tau)
        幅度 = float(np.clip(幅度, 0.0, 1.0))

        调色板 = (
            (0, 255, 245),  # 霓虹青
            (56, 118, 255),  # 电蓝
            (224, 32, 255),  # 霓虹紫
            (255, 58, 188),  # 赛博粉
        )
        seg = t * float(len(调色板))
        i0 = int(seg) % len(调色板)
        i1 = (i0 + 1) % len(调色板)
        k = float(seg - math.floor(seg))
        r, g, b = self._混色(调色板[i0], 调色板[i1], k)

        亮度倍率 = 0.58 + 0.78 * 幅度
        r = int(min(255, max(0, round(float(r) * 亮度倍率))))
        g = int(min(255, max(0, round(float(g) * 亮度倍率))))
        b = int(min(255, max(0, round(float(b) * 亮度倍率))))

        白提 = int(round(86.0 * (幅度**1.7)))
        return (min(255, r + 白提), min(255, g + 白提), min(255, b + 白提))

    def _混色(
        self, c0: Tuple[int, int, int], c1: Tuple[int, int, int], t: float
    ) -> Tuple[int, int, int]:
        t = float(np.clip(t, 0.0, 1.0))
        r = int(round(float(c0[0]) * (1.0 - t) + float(c1[0]) * t))
        g = int(round(float(c0[1]) * (1.0 - t) + float(c1[1]) * t))
        b = int(round(float(c0[2]) * (1.0 - t) + float(c1[2]) * t))
        return (r, g, b)

    def _hsv转rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        h = float(h) % 1.0
        s = float(np.clip(s, 0.0, 1.0))
        v = float(np.clip(v, 0.0, 1.0))

        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - f * s)
        t = v * (1.0 - (1.0 - f) * s)
        i = i % 6

        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q

        return (int(r * 255), int(g * 255), int(b * 255))


class 音频频谱提取器:
    def __init__(self, 样式: 圆环频谱样式):
        self.样式 = 样式
        self._样本: Optional[np.ndarray] = None
        self._采样率: int = 44100
        self._总样本数: int = 0

        # 更短窗口提升瞬态跟随，鼓点响应更紧。
        self._窗口长度 = 1024
        self._窗函数 = np.hanning(self._窗口长度).astype(np.float32)
        self._log频率索引: Optional[np.ndarray] = None
        self._目标频率hz: Optional[np.ndarray] = None
        self._频段权重: Optional[np.ndarray] = None
        self._低频掩码: Optional[np.ndarray] = None
        self._低频原始索引: Optional[np.ndarray] = None
        self._低频原始能量基线: float = 0.0
        self._上次低频原始能量: float = 0.0
        self._低频原始涨落基线: float = 0.0
        self._上次低频向量: Optional[np.ndarray] = None
        self._低频频谱流基线: float = 0.0
        self._低频能量基线: float = 0.0
        self._上次低频能量: float = 0.0
        self._低频涨落基线: float = 0.0
        self._鼓点脉冲包络: float = 0.0
        self._动态标尺: float = 1.0
        self._变化落差系数: float = 1.0

    def 设置变化落差(self, 值: float):
        try:
            self._变化落差系数 = float(max(0.0, min(2.0, float(值))))
        except Exception:
            self._变化落差系数 = 1.0

    def 设置条数(self, 条数: int):
        try:
            新条数 = int(max(24, min(720, int(条数))))
        except Exception:
            return
        if int(self.样式.条数) == int(新条数):
            return
        self.样式.条数 = int(新条数)
        if self._样本 is not None and self._总样本数 > 0:
            self._预计算_log频率映射()

    def 载入音频路径(self, 音频路径: str):
        初始化信息 = pygame.mixer.get_init()
        if not 初始化信息:
            raise RuntimeError("pygame.mixer 未初始化")

        if not 音频路径 or (not os.path.isfile(音频路径)):
            raise FileNotFoundError(f"音频不存在：{音频路径}")

        sound = pygame.mixer.Sound(os.path.abspath(音频路径))
        self._采样率 = int(初始化信息[0])

        数组 = pygame.sndarray.array(sound)
        数组 = np.asarray(数组)

        if 数组.ndim == 2:
            单声道 = 数组.astype(np.float32).mean(axis=1)
        else:
            单声道 = 数组.astype(np.float32)

        if 数组.dtype == np.int16:
            单声道 /= 32768.0
        elif 数组.dtype == np.int32:
            单声道 /= 2147483648.0
        else:
            单声道 = np.clip(单声道, -1.0, 1.0)

        # 防爆内存：极端大音频时做轻微抽样（不会影响“装饰效果”）
        try:
            总样本 = int(单声道.shape[0])
            目标上限 = int(self._采样率 * 60 * 8)  # 8分钟@44100
            if 总样本 > 目标上限:
                步长 = int(max(1, 总样本 // 目标上限))
                单声道 = 单声道[::步长].copy()
                self._采样率 = int(max(8000, self._采样率 // 步长))
        except Exception:
            pass

        self._样本 = 单声道
        self._总样本数 = int(单声道.shape[0])
        self._预计算_log频率映射()

    def _预计算_log频率映射(self):
        条数 = int(self.样式.条数)
        采样率 = int(self._采样率)

        频点数 = self._窗口长度 // 2 + 1
        频率轴 = np.linspace(0.0, 采样率 / 2.0, 频点数, dtype=np.float32)

        下限 = float(self.样式.频率下限)
        上限 = float(self.样式.频率上限)
        上限 = min(上限, 采样率 / 2.0 - 1.0)
        下限 = max(下限, 1.0)

        目标频率 = np.logspace(math.log10(下限), math.log10(上限), 条数).astype(
            np.float32
        )
        self._目标频率hz = 目标频率.copy()

        映射索引 = np.zeros(条数, dtype=np.int32)
        for i in range(条数):
            映射索引[i] = int(np.argmin(np.abs(频率轴 - 目标频率[i])))

        self._log频率索引 = 映射索引
        # 低频和中低频加权，强化节奏感；高频轻抑制，避免“全段同跳”。
        低频增强 = 1.0 + 1.35 * np.exp(-(((目标频率 - 120.0) / 145.0) ** 2))
        中频增强 = 1.0 + 0.42 * np.exp(-(((目标频率 - 820.0) / 920.0) ** 2))
        高频抑制 = 0.92 - 0.08 * np.clip((目标频率 - 4200.0) / 3800.0, 0.0, 1.0)
        self._频段权重 = (低频增强 * 中频增强 * 高频抑制).astype(np.float32)
        self._低频掩码 = np.asarray(目标频率 <= 280.0, dtype=bool)
        self._低频原始索引 = np.where((频率轴 >= 42.0) & (频率轴 <= 260.0))[0]
        if (self._低频原始索引 is None) or (int(self._低频原始索引.size) <= 0):
            self._低频原始索引 = np.arange(1, min(12, int(频率轴.size)), dtype=np.int32)
        self._低频原始能量基线 = 0.0
        self._上次低频原始能量 = 0.0
        self._低频原始涨落基线 = 0.0
        self._上次低频向量 = None
        self._低频频谱流基线 = 0.0
        self._低频能量基线 = 0.0
        self._上次低频能量 = 0.0
        self._低频涨落基线 = 0.0
        self._鼓点脉冲包络 = 0.0
        self._动态标尺 = 1.0

    def 取当前幅度(self, 当前播放秒: float) -> np.ndarray:
        if self._样本 is None or self._log频率索引 is None:
            return np.zeros(self.样式.条数, dtype=np.float32)

        中心样本 = int(当前播放秒 * self._采样率)
        半窗 = int(self._窗口长度 // 2)
        起 = max(0, 中心样本 - 半窗)
        终 = 起 + self._窗口长度
        if 终 > self._总样本数:
            终 = self._总样本数
            起 = max(0, 终 - self._窗口长度)

        片段 = self._样本[起:终]
        if 片段.shape[0] < self._窗口长度:
            补 = np.zeros(self._窗口长度, dtype=np.float32)
            补[: 片段.shape[0]] = 片段
            片段 = 补

        片段 = 片段.astype(np.float32) * self._窗函数
        频谱 = np.fft.rfft(片段)
        幅度 = np.abs(频谱).astype(np.float32)

        低频原始索引 = self._低频原始索引
        if isinstance(低频原始索引, np.ndarray) and int(低频原始索引.size) > 0:
            低频原始向量 = 幅度[低频原始索引].astype(np.float32)
        else:
            低频原始向量 = 幅度[: min(12, max(1, int(幅度.size)))].astype(np.float32)
        低频原始能量 = (
            float(np.mean(低频原始向量)) if int(低频原始向量.size) > 0 else 0.0
        )
        self._低频原始能量基线 = float(
            self._低频原始能量基线 * 0.90 + 低频原始能量 * 0.10
        )
        低频原始涨落 = max(0.0, float(低频原始能量 - float(self._上次低频原始能量)))
        self._上次低频原始能量 = float(低频原始能量)
        self._低频原始涨落基线 = float(
            self._低频原始涨落基线 * 0.90 + 低频原始涨落 * 0.10
        )

        低频流向量 = np.log1p(低频原始向量 * 16.0).astype(np.float32)
        低频频谱流 = 0.0
        if isinstance(self._上次低频向量, np.ndarray) and int(
            self._上次低频向量.size
        ) == int(低频流向量.size):
            低频频谱流 = float(
                np.mean(np.maximum(0.0, 低频流向量 - self._上次低频向量))
            )
        self._上次低频向量 = 低频流向量
        self._低频频谱流基线 = float(self._低频频谱流基线 * 0.90 + 低频频谱流 * 0.10)

        低频原始基线 = float(max(1e-6, self._低频原始能量基线))
        低频涨落基线_原始 = float(max(1e-6, self._低频原始涨落基线))
        低频频谱流基线 = float(max(1e-6, self._低频频谱流基线))

        原始低频脉冲 = max(
            0.0,
            (低频原始能量 - 低频原始基线 * 0.96) / (低频原始基线 * 1.20),
        )
        原始涨落脉冲 = max(
            0.0,
            (低频原始涨落 - 低频涨落基线_原始 * 0.90) / (低频涨落基线_原始 * 1.35),
        )
        频谱流脉冲 = max(
            0.0,
            (低频频谱流 - 低频频谱流基线 * 0.88) / (低频频谱流基线 * 1.25),
        )

        条幅度 = 幅度[self._log频率索引]
        条幅度 = np.log1p(条幅度 * 35.0)

        if self._频段权重 is not None and self._频段权重.size == 条幅度.size:
            条幅度 = 条幅度 * self._频段权重

        低频掩码 = self._低频掩码
        if (
            isinstance(低频掩码, np.ndarray)
            and 低频掩码.size == 条幅度.size
            and bool(np.any(低频掩码))
        ):
            try:
                低频能量 = float(np.mean(条幅度[低频掩码]))
            except Exception:
                低频能量 = float(np.mean(条幅度))
        else:
            低频能量 = float(np.mean(条幅度))

        self._低频能量基线 = float(self._低频能量基线 * 0.84 + 低频能量 * 0.16)
        低频脉冲 = max(0.0, float(低频能量 - self._低频能量基线))
        低频涨落 = max(0.0, float(低频能量 - float(self._上次低频能量)))
        self._上次低频能量 = float(低频能量)
        self._低频涨落基线 = float(self._低频涨落基线 * 0.88 + 低频涨落 * 0.12)
        涨落基线 = float(max(1e-6, self._低频涨落基线))
        条低频脉冲 = float(max(0.0, (低频涨落 - 涨落基线 * 0.82) / (涨落基线 * 2.9)))
        鼓点瞬态 = float(
            条低频脉冲 * 0.72
            + 原始涨落脉冲 * 1.05
            + 频谱流脉冲 * 1.36
            + 原始低频脉冲 * 0.45
        )
        self._鼓点脉冲包络 = float(max(鼓点瞬态, self._鼓点脉冲包络 * 0.74))
        鼓点脉冲 = float(min(1.75, max(0.0, self._鼓点脉冲包络)))

        if (
            self._目标频率hz is not None
            and self._目标频率hz.size == 条幅度.size
            and 低频脉冲 > 1e-6
        ):
            低频分布 = np.exp(-(((self._目标频率hz - 145.0) / 220.0) ** 2)).astype(
                np.float32
            )
            条幅度 = 条幅度 + (低频脉冲 * 2.8) * 低频分布
        if (
            self._目标频率hz is not None
            and self._目标频率hz.size == 条幅度.size
            and 鼓点脉冲 > 1e-6
        ):
            低中频分布 = (
                np.exp(-(((self._目标频率hz - 130.0) / 230.0) ** 2))
                + 0.45 * np.exp(-(((self._目标频率hz - 900.0) / 1200.0) ** 2))
            ).astype(np.float32)
            条幅度 = 条幅度 + (鼓点脉冲 * 1.85) * 低中频分布 + float(鼓点脉冲) * 0.16

        条幅度 = 条幅度 * float(1.0 + min(0.42, max(0.0, 鼓点脉冲) * 0.35))

        变化落差 = float(max(0.0, min(2.0, getattr(self, "_变化落差系数", 1.0))))
        try:
            局部平均 = self._环形平滑(条幅度)
            尖刺 = np.maximum(0.0, 条幅度 - 局部平均).astype(np.float32)
            条幅度 = (条幅度 + 尖刺 * (0.58 * 变化落差)).astype(np.float32)
            if int(条幅度.size) > 4:
                抬底 = float(np.quantile(条幅度, 0.18)) * float(0.18 + 0.26 * 变化落差)
                条幅度 = np.maximum(0.0, 条幅度 - 抬底).astype(np.float32)
        except Exception:
            pass

        条幅度 = self._拉平首尾落差(条幅度, 强度=0.86)

        标尺目标 = float(np.quantile(条幅度, 0.92)) if 条幅度.size > 0 else 1.0
        标尺目标 = max(1e-6, 标尺目标)
        self._动态标尺 = float(self._动态标尺 * 0.982 + 标尺目标 * 0.018)
        标尺 = float(max(1e-6, self._动态标尺))
        条幅度 = np.clip(条幅度 / 标尺, 0.0, 1.0)
        指数 = float(max(0.82, min(2.10, 0.92 + 0.56 * 变化落差)))
        条幅度 = np.power(条幅度, 指数).astype(np.float32)
        条幅度 = self._环形平滑(条幅度)
        条幅度 = self._拉平首尾落差(条幅度, 强度=0.55)
        条幅度 = np.clip(条幅度, 0.0, 1.0).astype(np.float32)
        if int(条幅度.size) >= 4:
            接缝均值 = float(
                (
                    float(条幅度[0])
                    + float(条幅度[1])
                    + float(条幅度[-1])
                    + float(条幅度[-2])
                )
                * 0.25
            )
            条幅度[0] = 接缝均值
            条幅度[-1] = 接缝均值

        return 条幅度

    def _环形平滑(self, arr: np.ndarray) -> np.ndarray:
        try:
            if arr is None or arr.size < 8:
                return arr
            扩展 = np.concatenate([arr[-2:], arr, arr[:2]]).astype(np.float32)
            核 = np.asarray([1.0, 2.0, 3.0, 2.0, 1.0], dtype=np.float32)
            核 /= float(np.sum(核))
            out = np.convolve(扩展, 核, mode="valid").astype(np.float32)
            return out
        except Exception:
            return arr

    def _平滑首尾接缝(self, arr: np.ndarray) -> np.ndarray:
        try:
            if arr is None:
                return arr
            n = int(arr.size)
            if n < 16:
                return arr
            w = int(max(8, min(24, n // 10)))
            out = arr.copy().astype(np.float32)
            原 = arr.astype(np.float32)
            for i in range(w):
                head = int(i)
                tail = int(n - 1 - i)
                mix = float((原[head] + 原[tail]) * 0.5)
                alpha = float(1.0 - (float(i) / float(max(1, w))))
                out[head] = float(原[head] * (1.0 - alpha) + mix * alpha)
                out[tail] = float(原[tail] * (1.0 - alpha) + mix * alpha)
            return out
        except Exception:
            return arr

    def _镜像映射环形(self, arr: np.ndarray) -> np.ndarray:
        try:
            if arr is None:
                return arr
            n = int(arr.size)
            if n < 8:
                return arr
            half = int(max(4, n // 2))
            src_x = np.linspace(0.0, float(n - 1), n, dtype=np.float32)
            dst_x = np.linspace(0.0, float(n - 1), half, dtype=np.float32)
            half_arr = np.interp(dst_x, src_x, arr.astype(np.float32)).astype(
                np.float32
            )
            if (n % 2) == 0:
                out = np.concatenate([half_arr, half_arr[::-1]]).astype(np.float32)
            else:
                out = np.concatenate([half_arr, half_arr[-2::-1]]).astype(np.float32)
                if out.size > n:
                    out = out[:n]
                elif out.size < n:
                    out = np.pad(out, (0, n - out.size), mode="edge").astype(np.float32)
            if out.size >= 2:
                接缝均值 = float((out[0] + out[-1]) * 0.5)
                out[0] = 接缝均值
                out[-1] = 接缝均值
            return out.astype(np.float32)
        except Exception:
            return arr

    def _拉平首尾落差(self, arr: np.ndarray, 强度: float = 0.8) -> np.ndarray:
        try:
            if arr is None:
                return arr
            n = int(arr.size)
            if n < 8:
                return arr
            out = arr.astype(np.float32).copy()
            差值 = float(out[-1] - out[0])
            if abs(差值) < 1e-6:
                return out
            t = np.linspace(0.0, 1.0, n, dtype=np.float32)
            out = out - (t * 差值 * float(max(0.0, min(1.0, 强度))))
            return out.astype(np.float32)
        except Exception:
            return arr


class 圆环频谱舞台装饰:
    """
    ✅ 用于“Stage背景(board.png)边缘一圈”的圆环频谱装饰
    - 绑定音频路径（开局加载样本做 FFT）
    - 每帧按 当前播放秒 取幅度并画到目标矩形中心
    """

    def __init__(self, 样式: Optional[圆环频谱样式] = None):
        self.样式 = 样式 or 圆环频谱样式()
        self.控件 = 圆环频谱控件(self.样式)
        self.提取器 = 音频频谱提取器(self.样式)
        self._调试外延最大长度覆盖: Optional[int] = None
        self._调试旋转启用覆盖: Optional[bool] = None
        self._调试变化落差覆盖: Optional[float] = None
        self._调试线条数量覆盖: Optional[int] = None
        self._调试线条粗细覆盖: Optional[int] = None
        self._调试线条间隔覆盖: Optional[int] = None
        self._项目根 = _取项目根目录()
        self._形状文件路径: str = ""
        self._形状旋转偏移弧度: float = 0.0
        self._形状图缓存: Dict[str, Optional[pygame.Surface]] = {}
        self._贴边半径缓存: Dict[Tuple[str, int, int, int], np.ndarray] = {}

        self.是否启用: bool = True

        self._已加载路径: str = ""
        self._已载入样本: bool = False

        self._上次目标尺寸: Tuple[int, int] = (-1, -1)

        # FFT 降频：避免 60fps 每帧 FFT 过热
        self._上次计算系统秒: float = 0.0
        self._上次计算播放秒: float = -999.0
        self._上次幅度: Optional[np.ndarray] = None
        self._最小计算间隔秒: float = 1.0 / 60.0  # 约60fps更新频谱

    def 绑定音频(self, 音频路径: str):
        音频路径 = str(音频路径 or "").strip()
        if not 音频路径:
            self._已载入样本 = False
            self._已加载路径 = ""
            return

        绝对路径 = os.path.abspath(音频路径)
        if 绝对路径 == self._已加载路径 and self._已载入样本:
            return

        self._已加载路径 = 绝对路径
        self._已载入样本 = False
        self._上次幅度 = None

        # 这里会依赖 SDL_mixer 对 mp3/ogg/wav 的支持；失败就抛异常给上层处理
        self.提取器.载入音频路径(绝对路径)
        self._已载入样本 = True

    def 更新并绘制(
        self,
        屏幕: pygame.Surface,
        目标矩形: pygame.Rect,
        当前播放秒: float,
    ):
        if not self.是否启用:
            return
        if 屏幕 is None or 目标矩形 is None:
            return

        当前播放秒 = float(max(0.0, 当前播放秒))
        self._按矩形重算样式(目标矩形)

        当前系统秒 = time.perf_counter()

        # 降频：不必每帧 FFT
        if (当前系统秒 - float(self._上次计算系统秒)) < float(self._最小计算间隔秒):
            幅度 = self._上次幅度
        else:
            if self._已载入样本:
                幅度 = self.提取器.取当前幅度(当前播放秒)
            else:
                幅度 = self._生成假频谱(当前播放秒)

            self._上次计算系统秒 = float(当前系统秒)
            self._上次计算播放秒 = float(当前播放秒)
            self._上次幅度 = 幅度

        if 幅度 is None:
            幅度 = self._生成假频谱(当前播放秒)

        self.控件.更新(幅度)
        self.控件.设置形状旋转偏移(self._形状旋转偏移弧度)

        cx = int(目标矩形.centerx)
        cy = int(目标矩形.centery)
        self.控件.绘制(屏幕, (cx, cy), 当前播放秒)

    def 更新并取绘制数据(
        self,
        目标矩形: pygame.Rect,
        当前播放秒: float,
    ) -> Optional[Dict[str, object]]:
        if not self.是否启用 or 目标矩形 is None:
            return None

        当前播放秒 = float(max(0.0, 当前播放秒))
        self._按矩形重算样式(目标矩形)

        当前系统秒 = time.perf_counter()
        if (当前系统秒 - float(self._上次计算系统秒)) < float(self._最小计算间隔秒):
            幅度 = self._上次幅度
        else:
            if self._已载入样本:
                幅度 = self.提取器.取当前幅度(当前播放秒)
            else:
                幅度 = self._生成假频谱(当前播放秒)
            self._上次计算系统秒 = float(当前系统秒)
            self._上次计算播放秒 = float(当前播放秒)
            self._上次幅度 = 幅度

        if 幅度 is None:
            幅度 = self._生成假频谱(当前播放秒)

        self.控件.更新(幅度)
        self.控件.设置形状旋转偏移(self._形状旋转偏移弧度)
        return self.控件.取绘制数据(
            (int(目标矩形.centerx), int(目标矩形.centery)),
            当前播放秒,
        )

    def _按矩形重算样式(self, 目标矩形: pygame.Rect):
        目标尺寸 = (int(max(1, 目标矩形.w)), int(max(1, 目标矩形.h)))
        if 目标尺寸 == self._上次目标尺寸:
            return
        self._上次目标尺寸 = 目标尺寸

        边 = int(max(1, min(目标尺寸[0], 目标尺寸[1])))

        半径 = float(边) * 0.5

        if self._调试外延最大长度覆盖 is not None:
            外延 = int(max(6, int(self._调试外延最大长度覆盖)))
        else:
            # 默认稍更夸张，视觉更有冲击感。
            外延 = int(max(12, min(28, int(半径 * 0.22))))

        # ✅ 贴边但别溢出：留 6px 内边距
        内边距 = int(max(4, min(10, int(半径 * 0.06))))
        内半径 = int(max(10, int(半径 - 外延 - 内边距)))

        self.样式.外延最大长度 = int(max(6, 外延))
        self.样式.内半径 = int(max(8, 内半径))
        self.样式.圆环线宽 = int(max(1, min(3, int(边 * 0.01))))
        默认条宽 = int(max(1, min(3, int(边 * 0.01))))
        if self._调试线条粗细覆盖 is not None:
            默认条宽 = int(max(1, min(12, int(self._调试线条粗细覆盖))))
        self.样式.条宽 = int(默认条宽)

        if self._调试线条间隔覆盖 is not None:
            self.样式.条间隔步长 = int(max(1, min(8, int(self._调试线条间隔覆盖))))
        else:
            self.样式.条间隔步长 = 1

        if self._调试线条数量覆盖 is not None:
            self.样式.条数 = int(max(24, min(720, int(self._调试线条数量覆盖))))

        if self._调试旋转启用覆盖 is False:
            self.样式.旋转速度 = 0.0
        elif self._调试旋转启用覆盖 is True and abs(float(self.样式.旋转速度)) < 1e-6:
            self.样式.旋转速度 = 0.24

        self.提取器.设置条数(int(self.样式.条数))
        if self._调试变化落差覆盖 is not None:
            self.提取器.设置变化落差(float(self._调试变化落差覆盖))

        self.控件.设置贴边半径数组(self._取贴边半径数组(目标尺寸))

    def 设置调试外延最大长度(self, 外延: Optional[int]):
        if 外延 is None:
            self._调试外延最大长度覆盖 = None
        else:
            self._调试外延最大长度覆盖 = int(max(6, int(外延)))
        self._上次目标尺寸 = (-1, -1)

    def 设置调试旋转启用(self, 启用: Optional[bool]):
        self._调试旋转启用覆盖 = None if 启用 is None else bool(启用)
        self._上次目标尺寸 = (-1, -1)

    def 设置调试变化落差(self, 落差: Optional[float]):
        if 落差 is None:
            self._调试变化落差覆盖 = None
        else:
            self._调试变化落差覆盖 = float(max(0.0, min(2.0, float(落差))))
        self._上次目标尺寸 = (-1, -1)

    def 设置调试线条参数(
        self,
        条数: Optional[int] = None,
        粗细: Optional[int] = None,
        间隔: Optional[int] = None,
    ):
        if 条数 is not None:
            self._调试线条数量覆盖 = int(max(24, min(720, int(条数))))
        if 粗细 is not None:
            self._调试线条粗细覆盖 = int(max(1, min(12, int(粗细))))
        if 间隔 is not None:
            self._调试线条间隔覆盖 = int(max(1, min(8, int(间隔))))
        self._上次目标尺寸 = (-1, -1)

    def 设置调试频谱参数(
        self,
        启用旋转: Optional[bool] = None,
        变化落差: Optional[float] = None,
        线条数量: Optional[int] = None,
        线条粗细: Optional[int] = None,
        线条间隔: Optional[int] = None,
    ):
        self.设置调试旋转启用(启用旋转)
        self.设置调试变化落差(变化落差)
        self.设置调试线条参数(线条数量, 线条粗细, 线条间隔)

    def 设置贴边形状文件(self, 路径: str):
        新路径 = str(路径 or "").strip()
        if 新路径 and (not os.path.isabs(新路径)):
            新路径 = os.path.abspath(os.path.join(self._项目根, 新路径))
        if 新路径 == self._形状文件路径:
            return
        self._形状文件路径 = 新路径
        self._上次目标尺寸 = (-1, -1)
        if not self._形状文件路径:
            self.控件.设置贴边半径数组(None)

    def 设置贴边形状旋转角度(self, 角度弧度: float):
        try:
            self._形状旋转偏移弧度 = float(角度弧度)
        except Exception:
            self._形状旋转偏移弧度 = 0.0

    def _取贴边半径数组(self, 目标尺寸: Tuple[int, int]) -> Optional[np.ndarray]:
        if not self._形状文件路径:
            return None
        宽, 高 = int(max(1, 目标尺寸[0])), int(max(1, 目标尺寸[1]))
        缓存键 = (self._形状文件路径, 宽, 高, int(self.样式.条数))
        if 缓存键 in self._贴边半径缓存:
            return self._贴边半径缓存[缓存键]

        图 = self._取形状图(self._形状文件路径)
        if 图 is None:
            return None

        try:
            if int(图.get_width()) != 宽 or int(图.get_height()) != 高:
                图 = pygame.transform.smoothscale(图, (宽, 高)).convert_alpha()
            alpha图 = pygame.surfarray.array_alpha(图)
        except Exception:
            return None

        中心x = (float(宽) - 1.0) * 0.5
        中心y = (float(高) - 1.0) * 0.5
        最大半径 = int(max(8, math.ceil(math.hypot(float(宽), float(高)))))
        条数 = int(self.样式.条数)
        半径数组 = np.zeros(条数, dtype=np.float32)
        阈值 = 72

        for i in range(条数):
            角度 = (float(i) / float(max(1, 条数))) * math.tau
            cos值 = math.cos(角度)
            sin值 = math.sin(角度)
            最后半径 = 0.0
            for 半径 in range(最大半径 + 1):
                x = int(round(中心x + cos值 * float(半径)))
                y = int(round(中心y + sin值 * float(半径)))
                if x < 0 or x >= 宽 or y < 0 or y >= 高:
                    break
                if int(alpha图[x, y]) >= 阈值:
                    最后半径 = float(半径)
            半径数组[i] = float(max(6.0, 最后半径))

        if 半径数组.size >= 5:
            卷积核 = np.asarray([1.0, 2.0, 1.0], dtype=np.float32)
            卷积核 /= float(np.sum(卷积核))
            扩展 = np.concatenate([半径数组[-1:], 半径数组, 半径数组[:1]])
            半径数组 = np.convolve(扩展, 卷积核, mode="valid").astype(np.float32)

        self._贴边半径缓存[缓存键] = 半径数组
        return 半径数组

    def _取形状图(self, 路径: str) -> Optional[pygame.Surface]:
        绝对路径 = str(路径 or "").strip()
        if not 绝对路径:
            return None
        if 绝对路径 in self._形状图缓存:
            return self._形状图缓存[绝对路径]
        if not os.path.isfile(绝对路径):
            self._形状图缓存[绝对路径] = None
            return None
        try:
            图 = pygame.image.load(绝对路径).convert_alpha()
        except Exception:
            图 = None
        self._形状图缓存[绝对路径] = 图
        return 图

    def _生成假频谱(self, t: float) -> np.ndarray:
        条数 = int(self.样式.条数)
        x = np.linspace(0.0, math.tau * 2.0, 条数, dtype=np.float32)
        基 = 0.10 + 0.12 * (np.sin(x + t * 2.4) * 0.5 + 0.5)
        细 = 0.06 * (np.sin(x * 3.0 + t * 5.0) * 0.5 + 0.5)
        幅 = np.clip(基 + 细, 0.0, 1.0)
        return 幅.astype(np.float32)
