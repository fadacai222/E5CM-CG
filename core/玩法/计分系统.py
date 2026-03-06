import math
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class 判定回报:
    类型: str  # "tap" / "hold_head" / "hold_tick"
    轨道序号: int
    判定: str  # "perfect" / "cool" / "good" / "miss"
    时间差毫秒: float  # 正=提前按，负=延后按
    加分: int
    连击增量: int  # tap/hold_head:1; hold_tick:4; miss:0


class 计分系统:
    def __init__(self, 总分: int):
        self.总分 = int(max(0, 总分))
        self.当前分 = 0
        self.当前连击 = 0
        self.最大连击 = 0
        self.最近判定: str = ""
        self.最近时间差毫秒: float = 0.0

    def 重置(self, 总分: Optional[int] = None):
        if 总分 is not None:
            self.总分 = int(max(0, 总分))
        self.当前分 = 0
        self.当前连击 = 0
        self.最大连击 = 0
        self.最近判定 = ""
        self.最近时间差毫秒 = 0.0

    def 批量结算(self, 回报列表: List[判定回报]):
        for 回报 in 回报列表:
            self.结算一次(回报)

    def 结算一次(self, 回报: 判定回报):
        self.最近判定 = str(回报.判定)
        self.最近时间差毫秒 = float(回报.时间差毫秒)

        # Miss：清零连击（按你规则）
        if 回报.判定 == "miss":
            self.当前连击 = 0
        else:
            self.当前连击 += int(max(0, 回报.连击增量))
            if self.当前连击 > self.最大连击:
                self.最大连击 = self.当前连击

        self.当前分 += int(max(0, 回报.加分))

    def 取百分比字符串(self) -> str:
        if self.总分 <= 0:
            return "0.00%"

        比例 = float(self.当前分) / float(self.总分)

        # ✅ 按你要求：先把 0.nnnn 截断到 4 位（不四舍五入）
        比例_截断4 = math.floor(比例 * 10000.0) / 10000.0

        百分比 = 比例_截断4 * 100.0
        if 百分比 < 0:
            百分比 = 0.0
        return f"{百分比:.2f}%"
