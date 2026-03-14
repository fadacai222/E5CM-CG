from __future__ import annotations

from typing import Dict, List


最高等级 = 70
经验数据版本 = 2
正式局歌曲数 = 3
正式局连续S倍率计数上限 = 2
正式局经验缓存键 = "对局_正式局经验缓存"


def _安全取字典(值) -> dict:
    return 值 if isinstance(值, dict) else {}


def _夹取(数值: float, 最小值: float, 最大值: float) -> float:
    return max(float(最小值), min(float(最大值), float(数值)))


def _经验值四舍五入(经验值: int | float) -> int:
    try:
        数值 = float(经验值 or 0.0)
    except Exception:
        数值 = 0.0
    return int(max(0.0, 数值) + 0.5)


def 取升下一级所需经验(当前等级: int) -> int:
    try:
        当前等级 = int(当前等级)
    except Exception:
        当前等级 = 1
    当前等级 = max(0, min(最高等级, 当前等级))
    if 当前等级 >= 最高等级:
        return 0
    分段表 = (
        (12, 5),
        (24, 10),
        (36, 20),
        (48, 45),
        (58, 80),
        (65, 130),
        (最高等级, 200),
    )
    for 上限等级, 所需经验 in 分段表:
        if 当前等级 <= 上限等级:
            return int(所需经验)
    return 50


def 计算经验显示比例(当前等级: int, 当前经验: float) -> float:
    所需经验 = int(取升下一级所需经验(当前等级))
    if 所需经验 <= 0:
        return 1.0
    try:
        当前经验 = float(当前经验)
    except Exception:
        当前经验 = 0.0
    return float(_夹取(当前经验 / float(max(1, 所需经验)), 0.0, 1.0))


def 构建默认模式进度() -> dict:
    return {"等级": 1, "经验": 0.0, "累计歌曲": 0, "累计首数": 0}


def 规范化模式进度(模式进度, *, 最大等级: int = 最高等级, 经验版本: int | None = None) -> dict:
    模式进度 = dict(_安全取字典(模式进度))
    最大等级 = max(1, min(最高等级, int(最大等级 or 最高等级)))

    模式进度["累计歌曲"] = max(0, int(模式进度.get("累计歌曲", 0) or 0))
    模式进度["累计首数"] = max(0, int(模式进度.get("累计首数", 0) or 0))

    当前等级 = int(模式进度.get("等级", 1) or 1)
    当前等级 = max(1, min(最大等级, 当前等级))

    try:
        当前经验 = float(模式进度.get("经验", 0.0) or 0.0)
    except Exception:
        当前经验 = 0.0

    if 当前等级 >= 最高等级 or 当前等级 >= 最大等级:
        当前经验 = 0.0
    else:
        当前等级所需经验 = float(max(1, 取升下一级所需经验(当前等级)))
        if int(经验版本 or 0) < int(经验数据版本) and 当前经验 <= 1.0 + 1e-6:
            当前经验 *= 当前等级所需经验
        当前经验 = _夹取(当前经验, 0.0, 当前等级所需经验)

    模式进度["等级"] = int(当前等级)
    模式进度["经验"] = float(当前经验)
    return 模式进度


def 计算单首歌基础经验(评级: str) -> int:
    评级 = str(评级 or "").strip().upper()
    if 评级 == "S":
        return 15
    if 评级 == "A":
        return 7
    if 评级 in {"B", "C", "D", "E"}:
        return 5
    return 0


def 判断是否ALL_PERFECT(*, cool数: int, good数: int, miss数: int) -> bool:
    return int(cool数 or 0) <= 0 and int(good数 or 0) <= 0 and int(miss数 or 0) <= 0


def 计算正式局内单首歌连续S倍率(当前连续S数: int, 当前评级: str) -> tuple[int, int]:
    当前评级 = str(当前评级 or "").strip().upper()
    if 当前评级 != "S":
        return 1, 0
    新连续S数 = max(1, min(正式局连续S倍率计数上限, int(当前连续S数 or 0) + 1))
    倍率表 = {1: 1, 2: 2}
    return int(倍率表.get(新连续S数, 1)), int(新连续S数)


def 计算单首歌奖励倍率(*, 是否全连: bool, 是否ALL_PERFECT: bool) -> float:
    if bool(是否ALL_PERFECT):
        return 2.0
    if bool(是否全连):
        return 1.5
    return 1.0


def 计算单首歌最终经验(基础经验: int, 连续S倍率: int | float, 单首歌奖励倍率: int | float) -> int:
    基础经验值 = max(0.0, float(基础经验 or 0))
    连续S加成 = max(1.0, float(连续S倍率 or 1.0))
    单首歌加成 = max(1.0, float(单首歌奖励倍率 or 1.0))
    return _经验值四舍五入(基础经验值 * 连续S加成 * 单首歌加成)


def 计算正式局单首歌结果(
    *,
    评级: str,
    cool数: int,
    good数: int,
    miss数: int,
    当前连续S数: int,
) -> dict:
    基础经验 = int(计算单首歌基础经验(评级))
    连续S倍率, 新连续S数 = 计算正式局内单首歌连续S倍率(当前连续S数, 评级)
    是否全连 = int(miss数 or 0) <= 0
    是否全P = 判断是否ALL_PERFECT(cool数=int(cool数 or 0), good数=int(good数 or 0), miss数=int(miss数 or 0))
    奖励倍率 = 计算单首歌奖励倍率(是否全连=是否全连, 是否ALL_PERFECT=是否全P)
    最终经验 = 计算单首歌最终经验(基础经验, 连续S倍率, 奖励倍率)
    return {
        "评级": str(评级 or "").strip().upper(),
        "基础经验": int(基础经验),
        "连续S倍率": int(连续S倍率),
        "连续S计数": int(新连续S数),
        "奖励倍率": float(奖励倍率),
        "最终经验": int(最终经验),
        "是否全连": bool(是否全连),
        "是否ALL_PERFECT": bool(是否全P),
    }


def 计算赠送歌经验(*, 评级: str) -> dict:
    基础经验 = int(计算单首歌基础经验(评级))
    return {
        "评级": str(评级 or "").strip().upper(),
        "基础经验": int(基础经验),
        "连续S倍率": 1,
        "连续S计数": 0,
        "奖励倍率": 1.0,
        "最终经验": int(基础经验),
        "是否全连": False,
        "是否ALL_PERFECT": False,
    }


def 清空正式局经验缓存(状态):
    if isinstance(状态, dict):
        状态.pop(正式局经验缓存键, None)


def 取正式局经验缓存(状态, *, 模式键: str | None = None, 当前关卡: int | None = None) -> dict:
    if not isinstance(状态, dict):
        return {"模式": str(模式键 or ""), "歌曲": [], "连续S数": 0}

    if 当前关卡 is not None and int(当前关卡 or 0) <= 1:
        清空正式局经验缓存(状态)

    缓存 = _安全取字典(状态.get(正式局经验缓存键))
    if not 缓存:
        缓存 = {"模式": str(模式键 or ""), "歌曲": [], "连续S数": 0}

    if 模式键 and str(缓存.get("模式", "") or "") != str(模式键):
        缓存 = {"模式": str(模式键 or ""), "歌曲": [], "连续S数": 0}

    歌曲列表 = 缓存.get("歌曲", [])
    if not isinstance(歌曲列表, list):
        歌曲列表 = []

    缓存["模式"] = str(模式键 if 模式键 is not None else 缓存.get("模式", "") or "")
    缓存["歌曲"] = [dict(_安全取字典(歌曲)) for 歌曲 in 歌曲列表[:正式局歌曲数]]
    缓存["连续S数"] = max(0, min(正式局歌曲数, int(缓存.get("连续S数", 0) or 0)))
    状态[正式局经验缓存键] = 缓存
    return 缓存


def 缓存正式局前两首歌经验与状态(
    状态,
    *,
    模式键: str,
    当前关卡: int,
    单首歌结果: dict,
) -> dict:
    缓存 = 取正式局经验缓存(状态, 模式键=模式键, 当前关卡=当前关卡)
    歌曲列表 = [dict(_安全取字典(歌曲)) for 歌曲 in list(缓存.get("歌曲", []))]
    当前关卡 = max(1, min(正式局歌曲数, int(当前关卡 or 1)))
    if 当前关卡 <= 1:
        歌曲列表 = []
    elif len(歌曲列表) >= 当前关卡:
        歌曲列表 = 歌曲列表[: 当前关卡 - 1]
    歌曲列表.append(dict(_安全取字典(单首歌结果)))
    缓存["模式"] = str(模式键 or "")
    缓存["歌曲"] = 歌曲列表[:正式局歌曲数]
    缓存["连续S数"] = max(0, min(正式局歌曲数, int(单首歌结果.get("连续S计数", 0) or 0)))
    if isinstance(状态, dict):
        状态[正式局经验缓存键] = 缓存
    return 缓存


def 处理经验入账(模式进度, *, 增加经验值: int | float) -> dict:
    原模式进度 = 规范化模式进度(模式进度, 经验版本=经验数据版本)
    原等级 = int(原模式进度.get("等级", 1) or 1)
    原经验 = float(原模式进度.get("经验", 0.0) or 0.0)
    try:
        剩余经验 = float(增加经验值 or 0.0)
    except Exception:
        剩余经验 = 0.0
    剩余经验 = max(0.0, 剩余经验)

    当前等级 = int(原等级)
    当前经验 = float(原经验)
    已应用经验 = 0.0
    进度片段: List[Dict[str, object]] = []

    while 剩余经验 > 1e-6 and 当前等级 < 最高等级:
        当前级所需经验 = float(max(1, 取升下一级所需经验(当前等级)))
        当前剩余需求 = max(0.0, 当前级所需经验 - float(当前经验))
        if 当前剩余需求 <= 1e-6:
            当前等级 += 1
            当前经验 = 0.0
            continue

        本段增长 = min(float(剩余经验), float(当前剩余需求))
        段结束经验 = float(当前经验 + 本段增长)
        是否升级 = bool(段结束经验 >= 当前级所需经验 - 1e-6 and 当前等级 < 最高等级)
        升级后等级 = int(当前等级 + 1) if 是否升级 else int(当前等级)
        进度片段.append(
            {
                "等级": int(当前等级),
                "等级所需经验": float(当前级所需经验),
                "起始经验": float(当前经验),
                "结束经验": 0.0 if 是否升级 else float(段结束经验),
                "增长": float(本段增长),
                "是否升级": bool(是否升级),
                "升级后等级": int(升级后等级),
            }
        )
        已应用经验 += float(本段增长)
        剩余经验 -= float(本段增长)

        if 是否升级:
            当前等级 = int(升级后等级)
            当前经验 = 0.0
        else:
            当前经验 = float(段结束经验)

    if 当前等级 >= 最高等级:
        当前等级 = 最高等级
        当前经验 = 0.0

    新模式进度 = dict(原模式进度)
    新模式进度["等级"] = int(当前等级)
    新模式进度["经验"] = float(当前经验)

    return {
        "原等级": int(原等级),
        "原经验": float(原经验),
        "等级": int(当前等级),
        "经验": float(当前经验),
        "申请增加经验": float(max(0.0, float(增加经验值 or 0.0))),
        "实际增加经验": float(max(0.0, 已应用经验)),
        "剩余未使用经验": float(max(0.0, 剩余经验)),
        "升级次数": int(max(0, 当前等级 - 原等级)),
        "是否升级": bool(当前等级 > 原等级),
        "是否满级": bool(当前等级 >= 最高等级),
        "进度片段": 进度片段,
        "模式进度": 新模式进度,
    }


def 第3首歌结束后统一结算正式局经验(
    状态,
    *,
    模式键: str,
    模式进度,
    当前关卡: int,
    当前单首歌结果: dict,
) -> dict:
    缓存 = 缓存正式局前两首歌经验与状态(
        状态,
        模式键=模式键,
        当前关卡=当前关卡,
        单首歌结果=当前单首歌结果,
    )
    正式局歌曲 = [dict(_安全取字典(歌曲)) for 歌曲 in list(缓存.get("歌曲", []))[:正式局歌曲数]]
    总经验 = int(sum(int(歌曲.get("最终经验", 0) or 0) for 歌曲 in 正式局歌曲))
    入账结果 = 处理经验入账(模式进度, 增加经验值=总经验)
    清空正式局经验缓存(状态)
    return {
        "结算类型": "正式局结算",
        "经验增加值": int(round(float(入账结果.get("实际增加经验", 0.0) or 0.0))),
        "正式局总经验": int(总经验),
        "正式局歌曲": 正式局歌曲,
        "经验结算": 入账结果,
        "模式进度": dict(入账结果.get("模式进度", 模式进度) or 模式进度),
        "显示奖励窗": True,
        "显示升级动画": bool(int(入账结果.get("升级次数", 0) or 0) > 0),
    }


def 处理赠送歌静默经验入账逻辑(
    状态,
    模式进度,
    *,
    评级: str,
) -> dict:
    清空正式局经验缓存(状态)
    单首歌结果 = 计算赠送歌经验(评级=评级)
    入账结果 = 处理经验入账(模式进度, 增加经验值=int(单首歌结果.get("最终经验", 0) or 0))
    return {
        "结算类型": "赠送歌静默入账",
        "经验增加值": int(round(float(入账结果.get("实际增加经验", 0.0) or 0.0))),
        "单首歌结果": 单首歌结果,
        "经验结算": 入账结果,
        "模式进度": dict(入账结果.get("模式进度", 模式进度) or 模式进度),
        "显示奖励窗": False,
        "显示升级动画": False,
    }


def 处理歌曲经验结算(
    状态,
    *,
    模式键: str,
    模式进度,
    当前关卡: int,
    评级: str,
    cool数: int,
    good数: int,
    miss数: int,
) -> dict:
    当前关卡 = max(1, int(当前关卡 or 1))
    模式进度 = 规范化模式进度(模式进度, 经验版本=经验数据版本)

    if 当前关卡 > 正式局歌曲数:
        return 处理赠送歌静默经验入账逻辑(状态, 模式进度, 评级=评级)

    缓存 = 取正式局经验缓存(状态, 模式键=模式键, 当前关卡=当前关卡)
    当前连续S数 = int(缓存.get("连续S数", 0) or 0)
    单首歌结果 = 计算正式局单首歌结果(
        评级=评级,
        cool数=int(cool数 or 0),
        good数=int(good数 or 0),
        miss数=int(miss数 or 0),
        当前连续S数=int(当前连续S数),
    )

    if 当前关卡 < 正式局歌曲数:
        新缓存 = 缓存正式局前两首歌经验与状态(
            状态,
            模式键=模式键,
            当前关卡=当前关卡,
            单首歌结果=单首歌结果,
        )
        return {
            "结算类型": "正式局缓存",
            "经验增加值": 0,
            "缓存经验值": int(单首歌结果.get("最终经验", 0) or 0),
            "单首歌结果": 单首歌结果,
            "正式局歌曲": [dict(_安全取字典(歌曲)) for 歌曲 in list(新缓存.get("歌曲", []))],
            "模式进度": dict(模式进度),
            "经验结算": None,
            "显示奖励窗": False,
            "显示升级动画": False,
        }

    结果 = 第3首歌结束后统一结算正式局经验(
        状态,
        模式键=模式键,
        模式进度=模式进度,
        当前关卡=当前关卡,
        当前单首歌结果=单首歌结果,
    )
    结果["单首歌结果"] = 单首歌结果
    return 结果
