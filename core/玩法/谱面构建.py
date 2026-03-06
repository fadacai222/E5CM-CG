import math
from dataclasses import dataclass
from typing import Callable, List, Tuple

from core.玩法.判定系统 import 判定音符


@dataclass
class 输入音符事件:
    轨道序号: int
    开始秒: float
    结束秒: float
    开始beat: float
    结束beat: float
    类型: str  # "tap" / "hold"


def 构建判定谱面(
    事件列表: List[输入音符事件],
    beat转秒: Callable[[float], float],
) -> Tuple[List[判定音符], int]:
    判定音符列表: List[判定音符] = []
    最大分计数 = 0

    for e in 事件列表 or []:
        轨道 = int(e.轨道序号)
        st = float(e.开始秒)
        ed = float(e.结束秒)
        sb = float(e.开始beat)
        eb = float(e.结束beat)

        if e.类型 == "tap":
            判定音符列表.append(
                判定音符(轨道序号=轨道, 类型="tap", 开始秒=st, 结束秒=st, tick秒列表=[])
            )
            最大分计数 += 1
            continue

        # hold：tick按“整拍(beat整数)”生成
        # ✅ 头部也是一次判定（计入总分）
        tick秒列表: List[float] = []

        # tick从“下一个整数拍”开始（避免头部和tick重叠）
        起始tick拍 = int(math.ceil(sb + 1e-9))
        结束tick拍 = int(math.floor(eb + 1e-9))

        for b in range(起始tick拍, 结束tick拍 + 1):
            try:
                t = float(beat转秒(float(b)))
                if st <= t <= ed + 1e-6:
                    tick秒列表.append(t)
            except Exception:
                continue

        判定音符列表.append(
            判定音符(
                轨道序号=轨道, 类型="hold", 开始秒=st, 结束秒=ed, tick秒列表=tick秒列表
            )
        )

        # 最大分：头 + 每个tick都按5000算（✅ 这里是我做的“可验证假设”，你如果想改别的权重很容易）
        最大分计数 += 1 + len(tick秒列表)

    # 总分=最大分计数*5000
    总分 = int(max(0, 最大分计数 * 5000))
    判定音符列表.sort(key=lambda x: float(x.开始秒))
    return 判定音符列表, 总分
