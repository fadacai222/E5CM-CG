import os
from typing import Dict, Optional, Tuple

import pygame

from core.常量与路径 import 取项目根目录 as _公共取项目根目录
from core.对局状态 import 初始化对局流程, 取累计S数, 消耗信用, 设置对局流程
from ui.settlement_layout_shared import safe_load_image


提示图名称列表 = ("下一把", "继续挑战", "是否续币", "游戏结束", "赠送一把")


def 取资源根目录(上下文: dict | None = None) -> str:
    资源 = {}
    if isinstance(上下文, dict):
        资源 = 上下文.get("资源", {}) or {}
    return _公共取项目根目录(资源 if isinstance(资源, dict) else {})


def 加载结算提示资源(
    根目录: str,
) -> Tuple[
    Dict[str, pygame.Surface],
    Dict[str, pygame.Surface],
    Optional[pygame.Surface],
    Optional[pygame.Surface],
]:
    提示图集: Dict[str, pygame.Surface] = {}
    倒计时图集: Dict[str, pygame.Surface] = {}

    提示目录 = os.path.join(根目录, "UI-img", "游戏界面", "结算", "提示")
    for 名称 in 提示图名称列表:
        图 = safe_load_image(os.path.join(提示目录, f"{名称}.png"))
        if 图 is not None:
            提示图集[名称] = 图

    数字目录 = os.path.join(提示目录, "数字-倒计时")
    for idx in range(10):
        图 = safe_load_image(os.path.join(数字目录, f"{idx}.png"))
        if 图 is not None:
            倒计时图集[str(idx)] = 图

    是按钮图 = safe_load_image(os.path.join(提示目录, "是.png"))
    否按钮图 = safe_load_image(os.path.join(提示目录, "否.png"))
    return 提示图集, 倒计时图集, 是按钮图, 否按钮图


def 解析结算流程上下文(载荷: dict | None, 状态: dict | None) -> dict:
    载荷 = 载荷 if isinstance(载荷, dict) else {}
    状态 = 状态 if isinstance(状态, dict) else {}

    try:
        当前关卡 = int(载荷.get("当前关卡", 载荷.get("局数", 1)) or 1)
    except Exception:
        当前关卡 = 1
    当前关卡 = max(1, 当前关卡)

    评级 = str(载荷.get("评级", "") or "").strip().upper()
    是否失败 = bool(载荷.get("失败", False)) or 评级 == "F"

    try:
        结算后S数 = int(载荷.get("结算后S数", 载荷.get("累计S数", 取累计S数(状态))) or 0)
    except Exception:
        结算后S数 = 0
    结算后S数 = max(0, min(3, 结算后S数))

    return {
        "当前关卡": 当前关卡,
        "是否失败": 是否失败,
        "结算后S数": 结算后S数,
        "三把S赠送": bool(载荷.get("三把S赠送", False)),
    }


def 构建继续动作(
    返回选歌动作: dict | None,
    *,
    下一关卡: int,
    重开新局: bool,
    累计S数: int,
    每局所需信用: int,
    需要消耗信用: bool = False,
) -> dict:
    动作 = {
        **(dict(返回选歌动作) if isinstance(返回选歌动作, dict) else {}),
        "下一关卡": int(下一关卡),
        "重开新局": bool(重开新局),
        "累计S数": 0 if 重开新局 else int(累计S数),
        "赠送第四把": False,
    }
    if 需要消耗信用:
        动作["消耗信用"] = int(每局所需信用)
    return 动作


def 推进对局流程(
    状态: dict | None,
    *,
    下一关卡: int,
    累计S数: int,
    赠送第四把: bool,
    消耗数量: int = 0,
    重开新局: bool = False,
):
    if not isinstance(状态, dict):
        return

    if 重开新局:
        初始化对局流程(状态)
        设置对局流程(状态, 当前把数=1, 累计S数=0, 赠送第四把=False)

    if 消耗数量 > 0:
        消耗信用(状态, int(消耗数量))

    设置对局流程(
        状态,
        当前把数=int(下一关卡),
        累计S数=int(累计S数),
        赠送第四把=bool(赠送第四把),
    )


def 构建返回选歌动作(载荷: dict | None, 状态: dict | None) -> dict:
    选歌上下文 = _解析选歌上下文(载荷, 状态, None)
    return {
        "类型": "选歌",
        "选歌类型": 选歌上下文["选歌类型"],
        "选歌模式": 选歌上下文["选歌模式"],
        "大模式": 选歌上下文["选歌类型"],
        "子模式": 选歌上下文["选歌模式"],
        "songs子文件夹": 选歌上下文["选歌类型"],
        "选歌原始索引": int(选歌上下文["选歌原始索引"]),
        "选歌恢复详情页": bool(选歌上下文["选歌恢复详情页"]),
    }


def 执行返回选歌(状态: dict | None, 载荷: dict | None, 动作: dict | None = None) -> dict:
    if isinstance(状态, dict):
        try:
            选歌上下文 = _解析选歌上下文(载荷, 状态, 动作)
            状态["选歌_类型"] = 选歌上下文["选歌类型"]
            状态["选歌_模式"] = 选歌上下文["选歌模式"]
            状态["大模式"] = 选歌上下文["选歌类型"]
            状态["子模式"] = 选歌上下文["选歌模式"]
            状态["songs子文件夹"] = 选歌上下文["选歌类型"]
            状态["选歌_恢复原始索引"] = int(选歌上下文["选歌原始索引"])
            状态["选歌_恢复详情页"] = bool(选歌上下文["选歌恢复详情页"])
        except Exception:
            pass
    return {"切换到": "选歌", "禁用黑屏过渡": True}


def _解析选歌上下文(载荷: dict | None, 状态: dict | None, 动作: dict | None) -> dict:
    载荷 = 载荷 if isinstance(载荷, dict) else {}
    状态 = 状态 if isinstance(状态, dict) else {}
    动作 = 动作 if isinstance(动作, dict) else {}
    加载页载荷 = 状态.get("加载页_载荷", {})
    if not isinstance(加载页载荷, dict):
        加载页载荷 = {}

    选歌类型 = _取首个非空文本(
        动作.get("选歌类型", ""),
        动作.get("大模式", ""),
        载荷.get("选歌类型", ""),
        载荷.get("类型", ""),
        载荷.get("大模式", ""),
        状态.get("选歌_类型", ""),
        状态.get("大模式", ""),
        状态.get("songs子文件夹", ""),
        加载页载荷.get("选歌类型", ""),
        加载页载荷.get("类型", ""),
        加载页载荷.get("大模式", ""),
        "竞速",
    )

    选歌模式 = _取首个非空文本(
        动作.get("选歌模式", ""),
        动作.get("子模式", ""),
        载荷.get("选歌模式", ""),
        载荷.get("模式", ""),
        载荷.get("子模式", ""),
        状态.get("选歌_模式", ""),
        状态.get("子模式", ""),
        加载页载荷.get("选歌模式", ""),
        加载页载荷.get("模式", ""),
        加载页载荷.get("子模式", ""),
        "竞速",
    )

    恢复原始索引 = _取首个整数(
        -1,
        动作.get("选歌原始索引", None),
        载荷.get("选歌原始索引", None),
        载荷.get("原始索引", None),
        状态.get("选歌_恢复原始索引", None),
        状态.get("选歌原始索引", None),
        加载页载荷.get("选歌原始索引", None),
    )

    恢复详情页 = _取首个布尔值(
        False,
        动作.get("选歌恢复详情页", None),
        载荷.get("选歌恢复详情页", None),
        状态.get("选歌_恢复详情页", None),
        加载页载荷.get("选歌恢复详情页", None),
    )

    return {
        "选歌类型": 选歌类型,
        "选歌模式": 选歌模式,
        "选歌原始索引": int(恢复原始索引),
        "选歌恢复详情页": bool(恢复详情页),
    }


def _取首个非空文本(*候选值) -> str:
    for 候选值项 in 候选值:
        try:
            文本 = str(候选值项 or "").strip()
        except Exception:
            文本 = ""
        if 文本:
            return 文本
    return ""


def _取首个整数(默认值: int, *候选值) -> int:
    for 候选值项 in 候选值:
        try:
            if 候选值项 is None or str(候选值项).strip() == "":
                continue
            return int(候选值项)
        except Exception:
            continue
    return int(默认值)


def _取首个布尔值(默认值: bool, *候选值) -> bool:
    for 候选值项 in 候选值:
        if isinstance(候选值项, bool):
            return 候选值项
        try:
            文本 = str(候选值项 or "").strip().lower()
        except Exception:
            文本 = ""
        if not 文本:
            continue
        if 文本 in ("1", "true", "yes", "y", "on"):
            return True
        if 文本 in ("0", "false", "no", "n", "off"):
            return False
    return bool(默认值)
