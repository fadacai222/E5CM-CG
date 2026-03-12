from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass
class 判定参数:
    # 正：提前按；负：延后按（单位ms）
    perfect_提前毫秒: int = 100
    perfect_延后毫秒: int = -100

    cool_提前毫秒: int = 150
    cool_延后毫秒: int = -150

    good_提前毫秒: int = 200
    good_延后毫秒: int = -200

    搜索半径秒: float = 0.20

    长按每拍连击: int = 4
    长按松手宽限毫秒: int = 360


@dataclass
class 判定音符:
    轨道序号: int
    类型: str  # "tap" / "hold"
    开始秒: float
    结束秒: float
    tick秒列表: List[float]  # hold用：每个整拍的判定时刻（秒）


@dataclass
class 判定回报:
    类型: str  # "tap" / "hold_head" / "hold_tick"
    轨道序号: int
    判定: str  # "perfect" / "cool" / "good" / "miss"
    时间差毫秒: float  # 正=提前按，负=延后按
    加分: int
    连击增量: int  # tap/hold_head=1; hold_tick=4; miss=0


class 判定系统:
    def __init__(
        self,
        参数: Optional[判定参数] = None,
        输入补偿秒: float = 0.0,
        自动模式: bool = False,
    ):
        self.参数 = 参数 or 判定参数()
        self.输入补偿秒 = float(输入补偿秒)
        self.自动模式 = bool(自动模式)

        self._音符列表: List[判定音符] = []
        self._音符已判定头: List[bool] = []
        self._音符已结束: List[bool] = []

        # 每轨道：按开始秒排序后的索引列表 + 游标（避免每帧全扫）
        self._轨道到索引: Dict[int, List[int]] = {}
        self._轨道游标: Dict[int, int] = {}

        # 长按状态：每个hold音符有自己的tick游标
        self._长按tick游标: Dict[int, int] = {}  # 音符索引 -> tick_idx
        self._活跃长按索引: List[int] = []  # 已判定头且未结束的hold音符索引
        self._长按判定缓存: Dict[int, str] = {}  # 音符索引 -> hold_head 判定
        self._长按最近按住秒: Dict[int, float] = {}  # 音符索引 -> 最近一次确认按住时间

    def 加载谱面(self, 音符列表: List[判定音符]):
        self._音符列表 = list(音符列表 or [])
        self._音符已判定头 = [False] * len(self._音符列表)
        self._音符已结束 = [False] * len(self._音符列表)

        self._轨道到索引 = {}
        for i, 音符 in enumerate(self._音符列表):
            self._轨道到索引.setdefault(int(音符.轨道序号), []).append(i)

        for 轨道, 索引列表 in self._轨道到索引.items():
            索引列表.sort(key=lambda idx: float(self._音符列表[idx].开始秒))
        self._轨道游标 = {int(k): 0 for k in self._轨道到索引.keys()}

        self._长按tick游标 = {}
        self._活跃长按索引 = []
        self._长按判定缓存 = {}
        self._长按最近按住秒 = {}

    # ---------- 对外：按下 ----------
    def 处理按下(self, 轨道序号: int, 当前谱面秒: float) -> List[判定回报]:
        if self.自动模式:
            return []

        轨道序号 = int(轨道序号)
        当前谱面秒 = float(当前谱面秒) + float(self.输入补偿秒)

        候选索引 = self._找候选音符索引(轨道序号, 当前谱面秒)
        if 候选索引 is None:
            return []

        音符 = self._音符列表[候选索引]
        时间差毫秒 = (float(音符.开始秒) - float(当前谱面秒)) * 1000.0  # ✅ 正=提前按

        判定 = self._计算判定(时间差毫秒)
        加分 = self._判定到分数(判定)

        if 音符.类型 == "tap":
            self._音符已判定头[候选索引] = True
            self._音符已结束[候选索引] = True
            return [
                判定回报(
                    类型="tap",
                    轨道序号=轨道序号,
                    判定=判定,
                    时间差毫秒=float(时间差毫秒),
                    加分=int(加分),
                    连击增量=0 if 判定 == "miss" else 1,
                )
            ]

        # hold：先判头
        self._音符已判定头[候选索引] = True

        回报列表 = [
            判定回报(
                类型="hold_head",
                轨道序号=轨道序号,
                判定=判定,
                时间差毫秒=float(时间差毫秒),
                加分=int(加分),
                连击增量=0 if 判定 == "miss" else 1,
            )
        ]

        # 头是miss：按你“超过即miss”，直接终止该hold（否则会产生大量tick误解）
        if 判定 == "miss":
            self._音符已结束[候选索引] = True
            return 回报列表

        # 头命中：进入活跃长按，tick从0开始
        if 候选索引 not in self._长按tick游标:
            self._长按tick游标[候选索引] = 0
        if 候选索引 not in self._活跃长按索引:
            self._活跃长按索引.append(候选索引)
        self._长按判定缓存[候选索引] = str(判定 or "perfect")
        self._长按最近按住秒[候选索引] = float(当前谱面秒)

        return 回报列表

    # ---------- 每帧更新：miss判定 + hold tick ----------
    def 更新(
        self, 当前谱面秒: float, 轨道是否按下: Callable[[int], bool]
    ) -> List[判定回报]:
        当前谱面秒 = float(当前谱面秒) + float(self.输入补偿秒)

        if self.自动模式:
            return self._自动更新(当前谱面秒)

        回报列表: List[判定回报] = []

        # 1) 自动miss：超过 -25ms 还没判头 -> miss（按你规则，窗口非常窄）
        for 轨道, 索引列表 in self._轨道到索引.items():
            游标 = int(self._轨道游标.get(int(轨道), 0))
            while 游标 < len(索引列表):
                idx = int(索引列表[游标])
                if self._音符已结束[idx]:
                    游标 += 1
                    continue

                音符 = self._音符列表[idx]
                if self._音符已判定头[idx]:
                    break

                时间差毫秒 = (float(音符.开始秒) - float(当前谱面秒)) * 1000.0
                if 时间差毫秒 < float(self.参数.good_延后毫秒):  # 例如 < -25ms
                    # miss
                    self._音符已判定头[idx] = True
                    self._音符已结束[idx] = True
                    回报列表.append(
                        判定回报(
                            类型="tap" if 音符.类型 == "tap" else "hold_head",
                            轨道序号=int(音符.轨道序号),
                            判定="miss",
                            时间差毫秒=float(时间差毫秒),
                            加分=0,
                            连击增量=0,
                        )
                    )
                    游标 += 1
                    continue

                # 还没到“必miss时间”
                break

            self._轨道游标[int(轨道)] = int(游标)

        # 2) hold tick：tick时刻 <= 当前秒 就结算一次（按住=perfect，否则miss）
        新活跃: List[int] = []
        松手宽限秒 = max(
            0.0, float(getattr(self.参数, "长按松手宽限毫秒", 0) or 0) / 1000.0
        )
        for idx in self._活跃长按索引:
            if self._音符已结束[idx]:
                continue

            音符 = self._音符列表[idx]
            if 音符.类型 != "hold":
                self._音符已结束[idx] = True
                continue

            tick游标 = int(self._长按tick游标.get(idx, 0))
            tick列表 = 音符.tick秒列表 or []
            最近按住秒 = self._长按最近按住秒.get(idx, None)

            if bool(轨道是否按下(int(音符.轨道序号))):
                最近按住秒 = float(当前谱面秒)
                self._长按最近按住秒[idx] = float(最近按住秒)

            while tick游标 < len(tick列表) and float(tick列表[tick游标]) <= float(
                当前谱面秒
            ):
                tick秒 = float(tick列表[tick游标])
                是否视为按住 = 最近按住秒 is not None and (
                    tick秒 - float(最近按住秒)
                ) <= 松手宽限秒
                if 是否视为按住:
                    tick判定 = str(self._长按判定缓存.get(idx, "perfect") or "perfect")
                    回报列表.append(
                        判定回报(
                            类型="hold_tick",
                            轨道序号=int(音符.轨道序号),
                            判定=tick判定,
                            时间差毫秒=0.0,
                            加分=int(self._判定到分数(tick判定)),
                            连击增量=int(self.参数.长按每拍连击),
                        )
                    )
                else:
                    回报列表.append(
                        判定回报(
                            类型="hold_tick",
                            轨道序号=int(音符.轨道序号),
                            判定="miss",
                            时间差毫秒=0.0,
                            加分=0,
                            连击增量=0,
                        )
                    )
                tick游标 += 1

            self._长按tick游标[idx] = int(tick游标)

            # tick都算完，并且超过结束秒一定时间，认为结束
            if (
                tick游标 >= len(tick列表)
                and float(当前谱面秒) > float(音符.结束秒) + 0.05
            ):
                self._音符已结束[idx] = True
                self._长按判定缓存.pop(idx, None)
                self._长按最近按住秒.pop(idx, None)
            else:
                新活跃.append(idx)

        self._活跃长按索引 = 新活跃

        return 回报列表

    # ---------- 内部：自动模式（用于你调UI） ----------
    def _自动更新(self, 当前谱面秒: float) -> List[判定回报]:
        回报列表: List[判定回报] = []

        # 自动判头：到点就perfect
        for 轨道, 索引列表 in self._轨道到索引.items():
            游标 = int(self._轨道游标.get(int(轨道), 0))
            while 游标 < len(索引列表):
                idx = int(索引列表[游标])
                if self._音符已结束[idx]:
                    游标 += 1
                    continue

                音符 = self._音符列表[idx]
                if self._音符已判定头[idx]:
                    break

                if float(音符.开始秒) <= float(当前谱面秒):
                    self._音符已判定头[idx] = True

                    if 音符.类型 == "tap":
                        self._音符已结束[idx] = True
                        回报列表.append(
                            判定回报("tap", int(音符.轨道序号), "perfect", 0.0, 5000, 1)
                        )
                    else:
                        # hold head
                        回报列表.append(
                            判定回报(
                                "hold_head", int(音符.轨道序号), "perfect", 0.0, 5000, 1
                            )
                        )
                        # 入活跃tick
                        if idx not in self._长按tick游标:
                            self._长按tick游标[idx] = 0
                        if idx not in self._活跃长按索引:
                            self._活跃长按索引.append(idx)
                        self._长按判定缓存[idx] = "perfect"
                        self._长按最近按住秒[idx] = float(当前谱面秒)

                    游标 += 1
                    continue

                break

            self._轨道游标[int(轨道)] = int(游标)

        # 自动tick：一律perfect
        新活跃: List[int] = []
        for idx in self._活跃长按索引:
            if self._音符已结束[idx]:
                continue

            音符 = self._音符列表[idx]
            tick游标 = int(self._长按tick游标.get(idx, 0))
            tick列表 = 音符.tick秒列表 or []

            while tick游标 < len(tick列表) and float(tick列表[tick游标]) <= float(
                当前谱面秒
            ):
                回报列表.append(
                    判定回报(
                        "hold_tick",
                        int(音符.轨道序号),
                        "perfect",
                        0.0,
                        5000,
                        int(self.参数.长按每拍连击),
                    )
                )
                tick游标 += 1

            self._长按tick游标[idx] = int(tick游标)

            if (
                tick游标 >= len(tick列表)
                and float(当前谱面秒) > float(音符.结束秒) + 0.05
            ):
                self._音符已结束[idx] = True
                self._长按判定缓存.pop(idx, None)
                self._长按最近按住秒.pop(idx, None)
            else:
                新活跃.append(idx)

        self._活跃长按索引 = 新活跃
        return 回报列表

    # ---------- 内部：找候选 ----------
    def _找候选音符索引(self, 轨道序号: int, 当前谱面秒: float) -> Optional[int]:
        索引列表 = self._轨道到索引.get(int(轨道序号), [])
        if not 索引列表:
            return None

        搜索半径 = float(self.参数.搜索半径秒)
        游标 = int(self._轨道游标.get(int(轨道序号), 0))

        # 从游标往后找开始秒在范围内的note
        候选: List[int] = []
        i = 游标
        while i < len(索引列表):
            idx = int(索引列表[i])
            if self._音符已结束[idx]:
                i += 1
                continue
            if self._音符已判定头[idx]:
                i += 1
                continue

            音符 = self._音符列表[idx]
            dt = float(音符.开始秒) - float(当前谱面秒)
            if dt < -搜索半径:
                # 已经太晚：理论上应该在更新里miss掉，但这里也顺手跳过
                i += 1
                continue
            if dt > 搜索半径:
                break
            候选.append(idx)
            i += 1

        if not 候选:
            return None

        # 选“绝对时间差最小”的
        最佳 = min(
            候选,
            key=lambda idx: abs(float(self._音符列表[idx].开始秒) - float(当前谱面秒)),
        )
        return int(最佳)

    # ---------- 内部：判定 ----------
    def _计算判定(self, 时间差毫秒: float) -> str:
        t = float(时间差毫秒)

        # Perfect
        if float(self.参数.perfect_延后毫秒) <= t <= float(self.参数.perfect_提前毫秒):
            return "perfect"

        # Cool
        if float(self.参数.cool_延后毫秒) <= t <= float(self.参数.cool_提前毫秒):
            return "cool"

        # Good
        if float(self.参数.good_延后毫秒) <= t <= float(self.参数.good_提前毫秒):
            return "good"

        return "miss"

    @staticmethod
    def _判定到分数(判定: str) -> int:
        if 判定 == "perfect":
            return 5000
        if 判定 == "cool":
            return 4000
        if 判定 == "good":
            return 3000
        return 0
