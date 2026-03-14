from __future__ import annotations

from core.等级经验 import 清空正式局经验缓存


def _安全取状态字典(状态) -> dict:
    return 状态 if isinstance(状态, dict) else {}


def 取当前关卡(状态, 默认值: int = 1) -> int:
    状态 = _安全取状态字典(状态)
    try:
        数值 = int(状态.get("对局_当前把数", 默认值) or 默认值)
    except Exception:
        数值 = int(默认值)
    return max(1, 数值)


def 取累计S数(状态) -> int:
    状态 = _安全取状态字典(状态)
    try:
        数值 = int(状态.get("对局_S次数", 0) or 0)
    except Exception:
        数值 = 0
    return max(0, min(3, 数值))


def 是否赠送第四把(状态) -> bool:
    状态 = _安全取状态字典(状态)
    return bool(状态.get("对局_赠送第四把", False))


def 设置信用数(状态, 数值: int) -> int:
    状态 = _安全取状态字典(状态)
    新值 = max(0, int(数值))
    状态["投币数"] = int(新值)
    状态["credit"] = str(int(新值))
    return int(新值)


def 取每局所需信用(状态, 默认值: int = 3) -> int:
    状态 = _安全取状态字典(状态)
    try:
        数值 = int(状态.get("每局所需信用", 默认值) or 默认值)
    except Exception:
        数值 = int(默认值)
    return max(1, 数值)


def 取信用数(状态) -> int:
    状态 = _安全取状态字典(状态)
    try:
        return max(0, int(状态.get("投币数", 0) or 0))
    except Exception:
        return 0


def 消耗信用(状态, 数量: int = 1) -> int:
    当前值 = 取信用数(状态)
    return 设置信用数(状态, 当前值 - max(0, int(数量)))


def 初始化对局流程(状态):
    状态 = _安全取状态字典(状态)
    状态["对局_当前把数"] = 1
    状态["对局_S次数"] = 0
    状态["对局_赠送第四把"] = False
    清空正式局经验缓存(状态)


def 设置对局流程(
    状态,
    *,
    当前把数: int | None = None,
    累计S数: int | None = None,
    赠送第四把: bool | None = None,
):
    状态 = _安全取状态字典(状态)
    if 当前把数 is not None:
        状态["对局_当前把数"] = max(1, int(当前把数))
    if 累计S数 is not None:
        状态["对局_S次数"] = max(0, min(3, int(累计S数)))
    if 赠送第四把 is not None:
        状态["对局_赠送第四把"] = bool(赠送第四把)


def 重置游戏流程状态(状态):
    状态 = _安全取状态字典(状态)
    初始化对局流程(状态)
    for 键 in (
        "大模式",
        "子模式",
        "选歌_类型",
        "选歌_模式",
        "选歌_BGM",
        "选歌_恢复原始索引",
        "选歌_恢复详情页",
        "加载页_载荷",
    ):
        状态.pop(键, None)
