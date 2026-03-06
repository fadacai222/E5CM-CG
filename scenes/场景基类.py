from dataclasses import dataclass
from typing import Optional


@dataclass
class 场景切换请求:
    目标场景名: str
    动作: str = "PUSH"  # PUSH / POP / REPLACE
    载荷: Optional[dict] = None


class 场景基类:
    名称 = "BASE"

    def __init__(self, 上下文: dict):
        self.上下文 = 上下文

    def 进入(self, 载荷: Optional[dict] = None):
        pass

    def 退出(self):
        pass

    def 更新(self):
        return None

    def 绘制(self):
        pass

    def 处理事件(self, 事件):
        return None
