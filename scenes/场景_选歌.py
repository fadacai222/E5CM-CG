import os
import sys
import json


def 确保项目根目录在模块路径里():
    当前文件 = os.path.abspath(__file__)
    场景目录 = os.path.dirname(当前文件)
    项目根目录 = os.path.abspath(os.path.join(场景目录, ".."))
    if 项目根目录 not in sys.path:
        sys.path.insert(0, 项目根目录)


确保项目根目录在模块路径里()
import re
import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Callable
from core.歌曲记录 import 读取歌曲记录索引, 取歌曲记录键
from core.对局状态 import 取当前关卡, 取累计S数, 是否赠送第四把
from core.踏板控制 import 踏板动作_左, 踏板动作_右, 踏板动作_确认
from ui.top栏 import 生成top栏
from ui.选歌设置菜单控件 import (
    构建设置参数文本,
    设置参数文本提取值,
    设置菜单默认调速选项,
    设置菜单行显示名,
    设置菜单行键列表,
    设置菜单行值,
    绘制_cover裁切预览,
)
import pygame
from scenes.场景基类 import 场景基类


_项目根目录_缓存: str | None = None
_运行根目录_缓存: str | None = None
_songs根目录_缓存: str | None = None


def _取项目根目录() -> str:
    global _项目根目录_缓存
    if _项目根目录_缓存:
        return _项目根目录_缓存

    候选起点列表: List[str] = []

    try:
        if getattr(sys, "frozen", False):
            临时资源目录 = str(getattr(sys, "_MEIPASS", "") or "").strip()
            if 临时资源目录:
                候选起点列表.append(os.path.abspath(临时资源目录))
            候选起点列表.append(os.path.dirname(os.path.abspath(sys.executable)))
    except Exception:
        pass

    try:
        候选起点列表.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass

    try:
        候选起点列表.append(os.getcwd())
    except Exception:
        pass

    已检查: Set[str] = set()
    for 起点 in 候选起点列表:
        当前 = os.path.abspath(str(起点 or ""))
        if (not 当前) or (当前 in 已检查):
            continue
        已检查.add(当前)

        for _ in range(10):
            if os.path.isdir(os.path.join(当前, "UI-img")) and os.path.isdir(
                os.path.join(当前, "json")
            ):
                _项目根目录_缓存 = 当前
                return 当前
            上级 = os.path.dirname(当前)
            if 上级 == 当前:
                break
            当前 = 上级

    for 起点 in 候选起点列表:
        if 起点:
            _项目根目录_缓存 = os.path.abspath(起点)
            return _项目根目录_缓存

    _项目根目录_缓存 = os.getcwd()
    return _项目根目录_缓存


def _取运行根目录() -> str:
    global _运行根目录_缓存
    if _运行根目录_缓存:
        return _运行根目录_缓存

    候选起点列表: List[str] = []

    try:
        if getattr(sys, "frozen", False):
            候选起点列表.append(os.path.dirname(os.path.abspath(sys.executable)))
    except Exception:
        pass

    try:
        候选起点列表.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass

    try:
        候选起点列表.append(os.getcwd())
    except Exception:
        pass

    已检查: Set[str] = set()
    for 起点 in 候选起点列表:
        当前 = os.path.abspath(str(起点 or ""))
        if (not 当前) or (当前 in 已检查):
            continue
        已检查.add(当前)

        for _ in range(10):
            if os.path.isdir(os.path.join(当前, "songs")) or os.path.isfile(
                os.path.join(当前, "main.py")
            ):
                _运行根目录_缓存 = 当前
                return 当前
            上级 = os.path.dirname(当前)
            if 上级 == 当前:
                break
            当前 = 上级

    try:
        if getattr(sys, "frozen", False):
            _运行根目录_缓存 = os.path.dirname(os.path.abspath(sys.executable))
            return _运行根目录_缓存
    except Exception:
        pass

    _运行根目录_缓存 = os.path.abspath(
        os.path.dirname(os.path.abspath(__file__))
        if "__file__" in globals()
        else os.getcwd()
    )
    return _运行根目录_缓存


def _取songs根目录(资源: Optional[dict] = None, 状态: Optional[dict] = None) -> str:
    global _songs根目录_缓存

    def _规范路径(路径值) -> str:
        try:
            文本 = str(路径值 or "").strip()
        except Exception:
            文本 = ""
        if not 文本:
            return ""
        try:
            return os.path.abspath(文本)
        except Exception:
            return ""

    def _加入候选(候选路径列表: List[str], 路径值):
        路径 = _规范路径(路径值)
        if 路径:
            候选路径列表.append(路径)

    def _向上搜索songs(起点路径: str, 最大层数: int = 8) -> str:
        当前路径 = _规范路径(起点路径)
        if not 当前路径:
            return ""

        if os.path.isfile(当前路径):
            当前路径 = os.path.dirname(当前路径)

        for _ in range(max(1, int(最大层数))):
            songs路径 = os.path.join(当前路径, "songs")
            try:
                if os.path.isdir(songs路径):
                    return os.path.abspath(songs路径)
            except Exception:
                pass

            上级路径 = os.path.dirname(当前路径)
            if 上级路径 == 当前路径:
                break
            当前路径 = 上级路径

        return ""

    if _songs根目录_缓存:
        try:
            if os.path.isdir(_songs根目录_缓存):
                return os.path.abspath(_songs根目录_缓存)
        except Exception:
            pass
        _songs根目录_缓存 = None

    候选路径列表: List[str] = []

    if isinstance(状态, dict):
        _加入候选(候选路径列表, 状态.get("songs根目录", ""))
        _加入候选(候选路径列表, 状态.get("外置songs根目录", ""))

    if isinstance(资源, dict):
        _加入候选(候选路径列表, 资源.get("songs根目录", ""))
        _加入候选(候选路径列表, 资源.get("外置songs根目录", ""))

        资源根目录 = _规范路径(资源.get("根", ""))
        if 资源根目录:
            _加入候选(候选路径列表, os.path.join(资源根目录, "songs"))

    try:
        if getattr(sys, "frozen", False):
            exe目录 = os.path.dirname(os.path.abspath(sys.executable))
            _加入候选(候选路径列表, os.path.join(exe目录, "songs"))
            _加入候选(候选路径列表, _向上搜索songs(exe目录, 最大层数=8))
    except Exception:
        pass

    try:
        启动目录 = os.path.dirname(os.path.abspath(sys.argv[0]))
        _加入候选(候选路径列表, os.path.join(启动目录, "songs"))
        _加入候选(候选路径列表, _向上搜索songs(启动目录, 最大层数=8))
    except Exception:
        pass

    try:
        运行根目录 = _取运行根目录()
        _加入候选(候选路径列表, os.path.join(运行根目录, "songs"))
        _加入候选(候选路径列表, _向上搜索songs(运行根目录, 最大层数=8))
    except Exception:
        pass

    try:
        项目根目录 = _取项目根目录()
        _加入候选(候选路径列表, os.path.join(项目根目录, "songs"))
        _加入候选(候选路径列表, _向上搜索songs(项目根目录, 最大层数=8))
    except Exception:
        pass

    try:
        当前工作目录 = os.getcwd()
        _加入候选(候选路径列表, os.path.join(当前工作目录, "songs"))
        _加入候选(候选路径列表, _向上搜索songs(当前工作目录, 最大层数=8))
    except Exception:
        pass

    已检查集合: Set[str] = set()
    for 候选路径 in 候选路径列表:
        标准路径 = _规范路径(候选路径)
        if (not 标准路径) or (标准路径 in 已检查集合):
            continue
        已检查集合.add(标准路径)

        try:
            if os.path.isdir(标准路径):
                _songs根目录_缓存 = 标准路径
                return 标准路径
        except Exception:
            continue

    默认根目录 = ""
    try:
        if getattr(sys, "frozen", False):
            默认根目录 = os.path.dirname(os.path.abspath(sys.executable))
    except Exception:
        默认根目录 = ""

    if not 默认根目录:
        try:
            默认根目录 = _取运行根目录()
        except Exception:
            默认根目录 = os.getcwd()

    默认路径 = os.path.abspath(os.path.join(默认根目录, "songs"))
    _songs根目录_缓存 = 默认路径
    return 默认路径


def _归一化目录名(名称: str) -> str:
    return re.sub(r"[\s_\-]+", "", str(名称 or "")).strip().lower()


def _列出一级子目录(目录路径: str) -> List[str]:
    结果: List[str] = []
    if not os.path.isdir(目录路径):
        return 结果

    try:
        for 名称 in os.listdir(目录路径):
            完整路径 = os.path.join(目录路径, 名称)
            if os.path.isdir(完整路径):
                结果.append(str(名称))
    except Exception:
        return []

    结果.sort()
    return 结果


def _在现有名称中匹配(现有名称列表: List[str], 候选名称: str) -> str:
    if not 现有名称列表:
        return ""

    目标 = str(候选名称 or "").strip()
    if not 目标:
        return ""

    if 目标 in 现有名称列表:
        return 目标

    目标归一 = _归一化目录名(目标)
    for 现有名称 in 现有名称列表:
        if _归一化目录名(现有名称) == 目标归一:
            return 现有名称

    return ""


def _匹配子目录名(父目录: str, 候选名称列表: List[str]) -> str:
    子目录列表 = _列出一级子目录(父目录)
    if not 子目录列表:
        return ""

    for 候选名称 in 候选名称列表:
        匹配结果 = _在现有名称中匹配(子目录列表, str(候选名称 or ""))
        if 匹配结果:
            return 匹配结果

    return ""


def _解析选歌入口参数(状态: dict, songs根目录: str) -> Tuple[str, str]:
    if not isinstance(状态, dict):
        状态 = {}

    加载页载荷 = 状态.get("加载页_载荷", {})
    if not isinstance(加载页载荷, dict):
        加载页载荷 = {}

    def _转文本(值) -> str:
        try:
            return str(值 or "").strip()
        except Exception:
            return ""

    def _取首个非空(*候选值) -> str:
        for 候选值 in 候选值:
            文本 = _转文本(候选值)
            if 文本:
                return 文本
        return ""

    def _生成别名列表(名称: str) -> List[str]:
        原始名称 = _转文本(名称)
        if not 原始名称:
            return []

        归一名称 = _归一化目录名(原始名称)
        别名列表: List[str] = [原始名称]

        if ("竞" in 原始名称) or ("speed" in 归一名称):
            别名列表.extend(["竞速", "speed", "Speed"])
        if ("花" in 原始名称) or ("fancy" in 归一名称):
            别名列表.extend(["花式", "fancy", "Fancy"])
        if ("派对" in 原始名称) or ("party" in 归一名称):
            别名列表.extend(["派对", "party", "Party"])
        if ("表演" in 原始名称) or ("show" in 归一名称):
            别名列表.extend(["表演", "show", "Show"])
        if ("学习" in 原始名称) or ("easy" in 归一名称) or ("learn" in 归一名称):
            别名列表.extend(["学习", "easy", "learn", "Easy", "Learn"])
        if ("疯狂" in 原始名称) or ("crazy" in 归一名称):
            别名列表.extend(["疯狂", "crazy", "Crazy"])
        if ("混音" in 原始名称) or ("mix" in 归一名称) or ("remix" in 归一名称):
            别名列表.extend(["混音", "mix", "remix", "Mix", "Remix"])
        if ("情侣" in 原始名称) or ("lover" in 归一名称):
            别名列表.extend(["情侣", "lover", "Lover"])
        if ("双踏板" in 原始名称) or ("club" in 归一名称):
            别名列表.extend(["双踏板", "club", "Club"])

        去重后列表: List[str] = []
        已出现集合: Set[str] = set()
        for 别名 in 别名列表:
            归一键 = _归一化目录名(别名)
            if (not 归一键) or (归一键 in 已出现集合):
                continue
            已出现集合.add(归一键)
            去重后列表.append(str(别名))
        return 去重后列表

    def _尝试修复songs根目录(原始songs根目录: str) -> str:
        候选路径列表: List[str] = []

        def _加入(路径值):
            try:
                路径文本 = str(路径值 or "").strip()
            except Exception:
                路径文本 = ""
            if not 路径文本:
                return
            try:
                候选路径列表.append(os.path.abspath(路径文本))
            except Exception:
                pass

        _加入(原始songs根目录)
        _加入(状态.get("songs根目录", ""))
        _加入(os.path.join(_取运行根目录(), "songs"))
        _加入(os.path.join(_取项目根目录(), "songs"))

        try:
            if getattr(sys, "frozen", False):
                _加入(
                    os.path.join(
                        os.path.dirname(os.path.abspath(sys.executable)), "songs"
                    )
                )
        except Exception:
            pass

        已检查集合: Set[str] = set()
        for 候选路径 in 候选路径列表:
            if (not 候选路径) or (候选路径 in 已检查集合):
                continue
            已检查集合.add(候选路径)
            try:
                if os.path.isdir(候选路径):
                    return 候选路径
            except Exception:
                continue

        return _转文本(原始songs根目录)

    def _匹配目录名_支持别名(
        父目录: str, 候选名称列表: List[str]
    ) -> Tuple[str, List[str]]:
        子目录列表 = _列出一级子目录(父目录)
        if not 子目录列表:
            return "", []

        for 候选名称 in 候选名称列表:
            for 别名 in _生成别名列表(候选名称):
                匹配结果 = _在现有名称中匹配(子目录列表, 别名)
                if 匹配结果:
                    return 匹配结果, 子目录列表

        return "", 子目录列表

    songs根目录 = _尝试修复songs根目录(songs根目录)

    类型候选列表 = [
        状态.get("选歌_类型", ""),
        状态.get("大模式", ""),
        状态.get("songs子文件夹", ""),
        状态.get("选歌类型", ""),
        加载页载荷.get("选歌类型", ""),
        加载页载荷.get("类型", ""),
        加载页载荷.get("大模式", ""),
    ]

    模式候选列表 = [
        状态.get("选歌_模式", ""),
        状态.get("子模式", ""),
        状态.get("选歌模式", ""),
        加载页载荷.get("选歌模式", ""),
        加载页载荷.get("模式", ""),
        加载页载荷.get("子模式", ""),
    ]

    原始类型候选 = _取首个非空(*类型候选列表)
    原始模式候选 = _取首个非空(*模式候选列表)

    类型名, 所有类型列表 = _匹配目录名_支持别名(
        songs根目录, [str(x or "") for x in 类型候选列表]
    )
    if not 类型名 and len(所有类型列表) == 1:
        类型名 = 所有类型列表[0]
    elif not 类型名 and 所有类型列表:
        类型名 = 所有类型列表[0]

    模式父目录 = os.path.join(songs根目录, 类型名) if 类型名 else ""
    模式名, 所有模式列表 = _匹配目录名_支持别名(
        模式父目录, [str(x or "") for x in 模式候选列表]
    )
    if not 模式名 and len(所有模式列表) == 1:
        模式名 = 所有模式列表[0]
    elif not 模式名 and 所有模式列表:
        模式名 = 所有模式列表[0]

    最终类型名 = str(类型名 or 原始类型候选 or "")
    最终模式名 = str(模式名 or 原始模式候选 or "")

    if 最终类型名:
        状态["选歌_类型"] = 最终类型名
        if not _转文本(状态.get("大模式", "")):
            状态["大模式"] = 最终类型名
        if not _转文本(状态.get("songs子文件夹", "")):
            状态["songs子文件夹"] = 最终类型名
        if 类型名:
            状态["大模式"] = 类型名
            状态["songs子文件夹"] = 类型名
    else:
        状态.pop("选歌_类型", None)

    if 最终模式名:
        状态["选歌_模式"] = 最终模式名
        if not _转文本(状态.get("子模式", "")):
            状态["子模式"] = 最终模式名
        if 模式名:
            状态["子模式"] = 模式名
    else:
        状态.pop("选歌_模式", None)

    return 最终类型名, 最终模式名


class 场景_选歌(场景基类):
    名称 = "选歌"

    def __init__(self, 上下文: dict):
        super().__init__(上下文)
        self._选歌实例: 选歌游戏 | None = None

    def 调试_获取可编辑样式(self) -> dict:
        return {}

    def 调试_设置样式(self, 键: str, 值):
        return

    def 调试_获取可编辑控件(self) -> dict:
        return {}

    def 调试_设置控件rect(self, 控件名: str, 新rect: pygame.Rect):
        return

    def 调试_导出布局(self) -> dict:
        return {}

    def 调试_导入布局(self, 数据: dict):
        return

    def 进入(self, 载荷=None):
        资源 = self.上下文.get("资源", {})
        状态 = self.上下文.get("状态", {})
        if not isinstance(状态, dict):
            状态 = {}
            self.上下文["状态"] = 状态

        进入载荷 = dict(载荷) if isinstance(载荷, dict) else {}

        def _转文本(值) -> str:
            try:
                return str(值 or "").strip()
            except Exception:
                return ""

        def _写入状态(键名: str, 值):
            if 键名 == "加载页_载荷":
                if isinstance(值, dict):
                    状态[键名] = dict(值)
                return

            if 键名 in ("选歌原始索引", "选歌_恢复原始索引"):
                try:
                    状态[键名] = int(值)
                except Exception:
                    pass
                return

            if 键名 in ("选歌恢复详情页", "选歌_恢复详情页"):
                状态[键名] = bool(值)
                return

            文本 = _转文本(值)
            if 文本:
                状态[键名] = 文本

        if 进入载荷:
            _写入状态("songs根目录", 进入载荷.get("songs根目录", ""))
            _写入状态("外置songs根目录", 进入载荷.get("外置songs根目录", ""))
            _写入状态("选歌_BGM", 进入载荷.get("选歌_BGM", ""))
            _写入状态("加载页_载荷", 进入载荷.get("加载页_载荷", {}))
            _写入状态("选歌_恢复原始索引", 进入载荷.get("选歌原始索引", None))
            _写入状态("选歌_恢复详情页", 进入载荷.get("选歌恢复详情页", False))

            载荷选歌类型 = _转文本(进入载荷.get("选歌类型", ""))
            载荷选歌模式 = _转文本(进入载荷.get("选歌模式", ""))
            载荷类型 = _转文本(进入载荷.get("类型", ""))
            载荷模式 = _转文本(进入载荷.get("模式", ""))
            载荷大模式 = _转文本(进入载荷.get("大模式", ""))
            载荷子模式 = _转文本(进入载荷.get("子模式", ""))
            载荷songs子文件夹 = _转文本(进入载荷.get("songs子文件夹", ""))

            最终类型 = 载荷选歌类型 or 载荷大模式 or 载荷类型 or 载荷songs子文件夹
            最终模式 = 载荷选歌模式 or 载荷子模式 or 载荷模式

            if 最终类型:
                状态["选歌_类型"] = 最终类型
                状态["大模式"] = 最终类型
                状态["songs子文件夹"] = 最终类型

            if 最终模式:
                状态["选歌_模式"] = 最终模式
                状态["子模式"] = 最终模式

        资源根目录 = _取项目根目录()
        songs根目录 = _取songs根目录(资源, 状态)
        玩家数 = int(状态.get("玩家数", 1) or 1)

        类型名, 模式名 = _解析选歌入口参数(状态, songs根目录)

        def _取第一个存在的文件(*候选路径: str) -> str:
            for 路径 in 候选路径:
                try:
                    路径 = str(路径 or "")
                    if 路径 and os.path.isfile(路径):
                        return 路径
                except Exception:
                    continue
            return ""

        try:
            状态["songs根目录"] = songs根目录
        except Exception:
            pass

        try:
            self.上下文["音乐"].停止()
        except Exception:
            pass

        背景音乐路径 = str(状态.get("选歌_BGM", "") or "")
        if not os.path.isfile(背景音乐路径):
            背景音乐路径 = ""

        模式小写 = 模式名.strip().lower()

        学习路径 = _取第一个存在的文件(
            str(资源.get("音乐_easy", "") or ""),
            os.path.join(资源根目录, "冷资源", "backsound", "easy.mp3"),
        )
        情侣路径 = _取第一个存在的文件(
            str(资源.get("音乐_lover", "") or ""),
            os.path.join(资源根目录, "冷资源", "backsound", "lover.mp3"),
        )

        if (("学习" in 模式名) or ("easy" in 模式小写)) and 学习路径:
            背景音乐路径 = 学习路径
        elif (("情侣" in 模式名) or ("lover" in 模式小写)) and 情侣路径:
            背景音乐路径 = 情侣路径

        if not 背景音乐路径:
            表演路径 = _取第一个存在的文件(
                str(资源.get("音乐_show", "") or ""),
                os.path.join(资源根目录, "冷资源", "backsound", "show.mp3"),
            )
            疯狂路径 = _取第一个存在的文件(
                str(资源.get("音乐_devil", "") or ""),
                os.path.join(资源根目录, "冷资源", "backsound", "devil.mp3"),
            )
            混音路径 = _取第一个存在的文件(
                str(资源.get("音乐_remix", "") or ""),
                os.path.join(资源根目录, "冷资源", "backsound", "remix.mp3"),
            )
            club路径 = _取第一个存在的文件(
                str(资源.get("音乐_club", "") or ""),
                os.path.join(资源根目录, "冷资源", "backsound", "club.mp3"),
            )

            if "表演" in 模式名 and 表演路径:
                背景音乐路径 = 表演路径
            elif "疯狂" in 模式名 and 疯狂路径:
                背景音乐路径 = 疯狂路径
            elif "混音" in 模式名 and 混音路径:
                背景音乐路径 = 混音路径
            elif (("club" in 模式小写) or ("双踏板" in 模式名)) and club路径:
                背景音乐路径 = club路径

        if not 背景音乐路径:
            背景音乐路径 = _取第一个存在的文件(
                str(资源.get("音乐_UI", "") or ""),
                str(资源.get("back_music_ui", "") or ""),
                str(资源.get("投币_BGM", "") or ""),
            )

        logo路径 = _取第一个存在的文件(
            os.path.join(资源根目录, "res", "logo", "base.png"),
            os.path.join(_取运行根目录(), "res", "logo", "base.png"),
        )

        self._选歌实例 = 选歌游戏(
            songs根目录=songs根目录,
            背景音乐路径=背景音乐路径,
            logo路径=logo路径,
            指定类型名=类型名,
            指定模式名=模式名,
            玩家数=玩家数,
            是否继承已有窗口=True,
        )
        try:
            self._选歌实例.上下文 = self.上下文
        except Exception:
            pass

        try:
            setattr(self._选歌实例, "_全局点击特效", None)
        except Exception:
            pass

        try:
            if hasattr(self._选歌实例, "绑定外部屏幕"):
                self._选歌实例.绑定外部屏幕(self.上下文["屏幕"])
        except Exception:
            pass

        try:
            恢复原始索引 = 状态.pop("选歌_恢复原始索引", None)
        except Exception:
            恢复原始索引 = None
        try:
            恢复详情页 = bool(状态.pop("选歌_恢复详情页", False))
        except Exception:
            恢复详情页 = False

        if 恢复原始索引 is not None and self._选歌实例 is not None:
            try:
                原始列表 = self._选歌实例.当前原始歌曲列表()
            except Exception:
                原始列表 = []
            if 原始列表:
                try:
                    if int(恢复原始索引) < 0:
                        raise ValueError("restore index disabled")
                    恢复原始索引 = int(
                        max(0, min(int(恢复原始索引), len(原始列表) - 1))
                    )
                    self._选歌实例.当前选择原始索引 = 恢复原始索引
                    if 恢复详情页 and hasattr(self._选歌实例, "进入详情_原始索引"):
                        self._选歌实例.进入详情_原始索引(int(恢复原始索引))
                    else:
                        列表, 映射 = self._选歌实例.当前歌曲列表与映射()
                        if 映射:
                            try:
                                视图索引 = 映射.index(int(恢复原始索引))
                            except Exception:
                                视图索引 = 0
                            self._选歌实例.当前页 = max(
                                0, int(视图索引 // max(1, int(self._选歌实例.每页数量)))
                            )
                        self._选歌实例.是否详情页 = False
                        self._选歌实例.当前页卡片 = self._选歌实例.生成指定页卡片(
                            int(self._选歌实例.当前页)
                        )
                        self._选歌实例.安排预加载(基准页=int(self._选歌实例.当前页))
                except Exception:
                    pass

    def 退出(self):
        # ✅ 停止选歌里的 pygame.mixer.music，避免回到其它场景仍在播
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

        self._选歌实例 = None

    # ---- 帧更新 ----
    def 更新(self):
        if self._选歌实例 is None:
            return {"切换到": "子模式", "禁用黑屏过渡": True}

        # 同步屏幕（main.py resize 后会换 surface）
        try:
            if hasattr(self._选歌实例, "绑定外部屏幕"):
                self._选歌实例.绑定外部屏幕(self.上下文["屏幕"])
        except Exception:
            pass

        退出状态 = None
        try:
            if hasattr(self._选歌实例, "帧更新"):
                退出状态 = self._选歌实例.帧更新()
        except Exception:
            退出状态 = None

        if 退出状态:
            return self._根据退出状态切场景(str(退出状态))

        return None

    def 绘制(self):
        if self._选歌实例 is None:
            return
        try:
            if hasattr(self._选歌实例, "帧绘制"):
                self._选歌实例.帧绘制()
        except Exception:
            # 防御：别让选歌绘制崩全局
            pass

    def 处理全局踏板(self, 动作: str):
        if self._选歌实例 is None:
            return None

        退出状态 = None
        try:
            if hasattr(self._选歌实例, "处理全局踏板"):
                退出状态 = self._选歌实例.处理全局踏板(动作)
        except Exception:
            退出状态 = None

        if 退出状态:
            return self._根据退出状态切场景(str(退出状态))
        return None

    def 处理事件(self, 事件):
        if self._选歌实例 is None:
            return None

        退出状态 = None
        try:
            if hasattr(self._选歌实例, "处理事件_外部"):
                退出状态 = self._选歌实例.处理事件_外部(事件)
        except Exception:
            退出状态 = None

        if 退出状态:
            return self._根据退出状态切场景(str(退出状态))
        return None

    def _根据退出状态切场景(self, 退出状态: str):
        状态 = self.上下文.get("状态", {})
        if not isinstance(状态, dict):
            状态 = {}
            self.上下文["状态"] = 状态

        载荷 = {}
        if 退出状态 == "GO_LOADING":
            try:
                if self._选歌实例 is not None and hasattr(
                    self._选歌实例, "_加载页_载荷"
                ):
                    临时载荷 = getattr(self._选歌实例, "_加载页_载荷", None)
                    if isinstance(临时载荷, dict):
                        载荷 = dict(临时载荷)
            except Exception:
                载荷 = {}

            try:
                状态["加载页_载荷"] = dict(载荷)
            except Exception:
                pass

            try:
                载荷类型 = str(载荷.get("类型", "") or "").strip()
            except Exception:
                载荷类型 = ""
            try:
                载荷模式 = str(载荷.get("模式", "") or "").strip()
            except Exception:
                载荷模式 = ""

            if 载荷类型:
                状态["选歌_类型"] = 载荷类型
                状态["大模式"] = 载荷类型
                状态["songs子文件夹"] = 载荷类型

            if 载荷模式:
                状态["选歌_模式"] = 载荷模式
                状态["子模式"] = 载荷模式

            try:
                状态.pop("选歌_BGM", None)
            except Exception:
                pass

            return {"切换到": "加载页", "载荷": 载荷, "禁用黑屏过渡": True}

        if 退出状态 == "RESELECT_MAIN":
            try:
                状态.pop("选歌_类型", None)
                状态.pop("选歌_模式", None)
                状态.pop("选歌_BGM", None)
                状态["大模式"] = ""
                状态["子模式"] = ""
                状态["songs子文件夹"] = ""
            except Exception:
                pass
            return {"切换到": "大模式", "禁用黑屏过渡": True}

        try:
            状态.pop("选歌_BGM", None)
        except Exception:
            pass

        return {"切换到": "子模式", "禁用黑屏过渡": True}


# =========================
# 数据结构
# =========================
@dataclass
class 歌曲信息:
    序号: int
    类型: str
    模式: str
    歌曲文件夹: str
    歌曲路径: str
    sm路径: str
    mp3路径: Optional[str]
    封面路径: Optional[str]
    歌名: str
    星级: int
    bpm: Optional[int]
    是否VIP: bool = False
    游玩次数: int = 0
    是否NEW: bool = False
    是否HOT: bool = False


# =========================
# 基础工具
# =========================
def 安全加载图片(路径: str, 透明: bool = True) -> Optional[pygame.Surface]:
    try:
        if (not 路径) or (not os.path.isfile(路径)):
            return None
        图 = pygame.image.load(路径)
        return 图.convert_alpha() if 透明 else 图.convert()
    except Exception:
        return None


def 处理透明像素_用左上角作为背景(原图: pygame.Surface) -> pygame.Surface:
    """
    用左上角像素颜色当背景色，做“色键抠图”，输出带 alpha 的新 Surface。
    适合：素材 PNG 没有透明通道，但背景是纯色（常见黑底/白底）。
    风险：如果左上角颜色属于有效内容，也会被误抠。
    """
    try:
        if 原图 is None:
            return 原图
        背景色 = 原图.get_at((0, 0))
        背景rgb = (int(背景色.r), int(背景色.g), int(背景色.b))

        临时 = 原图.convert()
        临时.set_colorkey(背景rgb)

        结果 = pygame.Surface(原图.get_size(), pygame.SRCALPHA)
        结果.fill((0, 0, 0, 0))
        结果.blit(临时, (0, 0))
        return 结果.convert_alpha()
    except Exception:
        try:
            return 原图.convert_alpha()
        except Exception:
            return 原图


# =========================
# 选歌界面 UI 资源缓存（避免每帧读盘）
# =========================

_UI原图缓存: Dict[str, Optional[pygame.Surface]] = {}
_UI缩放缓存: Dict[Tuple[str, int, int, bool], Optional[pygame.Surface]] = {}

# =========================
# ✅ 序号标签纸（缩略图/大图）手动可调参数
# =========================

# --- 缩略图序号背景（标签纸） ---
_缩略图_序号背景_缩放 = 1.5  # ✅ 背景整体缩放（相对“基准高”）
_缩略图_序号背景_x偏移 = 20  # ✅ 背景基于锚点的x偏移（像素）
_缩略图_序号背景_y偏移 = -20  # ✅ 背景基于锚点的y偏移（像素）←想上移就更负

# --- 缩略图序号数字（内容） ---
_缩略图_序号数字_缩放 = 1.6  # ✅ 数字大小缩放（相对“数字高”）
_缩略图_序号数字_x偏移 = -20  # ✅ 数字基于“右下对齐位置”的x偏移（像素）
_缩略图_序号数字_y偏移 = -20  # ✅ 数字基于“右下对齐位置”的y偏移（像素）
_缩略图_序号数字_右内边距占比 = 0.12  # ✅ 右下对齐时的“右侧内边距”
_缩略图_序号数字_下内边距占比 = 0.12  # ✅ 右下对齐时的“下侧内边距”

# --- 大图序号背景（标签纸） ---
_大图_序号背景_缩放 = 1.70
_大图_序号背景_x偏移 = 0
_大图_序号背景_y偏移 = 0

# --- 大图序号数字（内容） ---
_大图_序号数字_缩放 = 1.00
_大图_序号数字_x偏移 = 10
_大图_序号数字_y偏移 = 10

# --- 显示格式（想改“序号内容”就改这里） ---
_序号显示格式_缩略图 = "{:02d}"  # 01 02 03...
_序号显示格式_大图 = "{:02d}"  # 想大图显示不一样也行

# =========================
# ✅ 设置页：手动可调参数（按你要求：组级/控件级都能调）
# =========================

_设置页_面板宽占比 = 0.88
_设置页_面板高占比 = 0.78
_设置页_面板整体缩放 = 1.00
_设置页_面板_x偏移 = 0
_设置页_面板_y偏移 = 0

# 左侧“设置列表”大组
_设置页_左区_x占比 = 0.1
_设置页_左区_y占比 = 0.07
_设置页_左区_宽占比 = 0.15
_设置页_左区_行高占比 = 0.07
_设置页_左区_行间距像素 = 10

# ✅ 每一行单独微调（xy）
_设置页_左区_行偏移覆盖 = {
    "调速": (0, 0),
    "变速": (0, 0),
    "变速类型": (0, 0),  # 你这里叫“谱面”，我用“变速类型”避免和“变速”冲突；下面会映射
    "隐藏": (0, 0),
    "轨迹": (0, 0),
    "方向": (0, 0),
    "大小": (0, 0),
    "箭头": (0, 0),
}

# 右侧“背景选择”大组
_设置页_右区_x占比 = 0.52
_设置页_右区_y占比 = 0.18
_设置页_右区_宽占比 = 0.42
_设置页_右区_高占比 = 0.70
_设置页_右区_额外偏移 = (0, 0)

# 右侧预览图边距（像素）
_设置页_右区_预览内边距 = 10
# 右侧预览框额外偏移（相对默认中心）
_设置页_右区_预览框_偏移 = (0, 0)
# 右侧预览框缩放（1.0=默认）
_设置页_右区_预览框_宽缩放 = 1.0
_设置页_右区_预览框_高缩放 = 1.0
# 右侧大箭头（左右分别可调）
_设置页_右区_左大箭头_偏移 = (0, 0)
_设置页_右区_右大箭头_偏移 = (0, 0)
_设置页_右区_左大箭头_缩放 = 1.0
_设置页_右区_右大箭头_缩放 = 1.0

# ✅ 设置页：箭头候选“左下预览框”（原版是一个大方框）
_设置页_箭头预览_x占比 = 0.12
_设置页_箭头预览_y占比 = 0.74
_设置页_箭头预览_宽占比 = 0.1
_设置页_箭头预览_高占比 = 0.20
_设置页_箭头预览_额外偏移 = (0, 0)
_设置页_箭头预览_内边距 = 0


# =========================
# ✅ 设置页：资源/布局/绘制/交互
# =========================
def _设置页_持久化文件路径(self) -> str:
    return os.path.join(_取运行根目录(), "json", "选歌设置.json")


def _设置页_从参数文本提取(参数文本: str, 键名: str) -> str:
    return 设置参数文本提取值(str(参数文本 or ""), str(键名 or ""))


def _设置页_构建参数文本(
    self,
    设置参数: Optional[dict] = None,
    背景文件名: str = "",
    箭头文件名: str = "",
) -> str:
    return 构建设置参数文本(
        设置参数=设置参数,
        背景文件名=背景文件名,
        箭头文件名=箭头文件名,
    )


def _设置页_读取持久化设置(self) -> dict:
    路径 = _设置页_持久化文件路径(self)
    if (not 路径) or (not os.path.isfile(路径)):
        return {}
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码) as f:
                数据 = json.load(f)
            return dict(数据) if isinstance(数据, dict) else {}
        except Exception:
            continue
    return {}


def _设置页_写入持久化设置(self, 数据: dict) -> bool:
    try:
        路径 = _设置页_持久化文件路径(self)
        if not 路径:
            return False
        os.makedirs(os.path.dirname(路径), exist_ok=True)
        with open(路径, "w", encoding="utf-8") as f:
            json.dump(dict(数据 or {}), f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _设置页_加载持久化设置(self):
    数据 = _设置页_读取持久化设置(self)
    if not isinstance(数据, dict) or not 数据:
        return

    索引表 = 数据.get("索引", {})
    if not isinstance(索引表, dict):
        索引表 = {}

    def _应用索引(属性名: str, 键名: str, 选项数量: int):
        if 选项数量 <= 0:
            return
        try:
            值 = int(索引表.get(键名, getattr(self, 属性名, 0)) or 0)
        except Exception:
            值 = int(getattr(self, 属性名, 0) or 0)
        值 = max(0, min(选项数量 - 1, 值))
        setattr(self, 属性名, 值)

    _应用索引("设置_调速索引", "调速", len(getattr(self, "设置_调速选项", [])))
    if "背景模式" not in 索引表 and "变速" in 索引表:
        try:
            索引表["背景模式"] = int(索引表.get("变速", 0) or 0)
        except Exception:
            pass
    _应用索引("设置_变速索引", "背景模式", len(getattr(self, "设置_变速选项", [])))
    _应用索引("设置_谱面索引", "谱面", len(getattr(self, "设置_谱面选项", [])))
    _应用索引("设置_隐藏索引", "隐藏", len(getattr(self, "设置_隐藏选项", [])))
    _应用索引("设置_轨迹索引", "轨迹", len(getattr(self, "设置_轨迹选项", [])))
    _应用索引("设置_方向索引", "方向", len(getattr(self, "设置_方向选项", [])))
    _应用索引("设置_大小索引", "大小", len(getattr(self, "设置_大小选项", [])))
    _应用索引("设置_箭头索引", "箭头", len(getattr(self, "设置_箭头候选路径列表", [])))
    _应用索引(
        "设置_背景索引", "背景", len(getattr(self, "设置_背景大图文件名列表", []))
    )

    参数 = 数据.get("设置参数", {})
    if not isinstance(参数, dict):
        参数 = {}

    def _按值匹配(属性名: str, 选项列表: List[str], 候选值: str):
        候选值 = str(候选值 or "").strip()
        if (not 候选值) or (not 选项列表):
            return
        try:
            idx = list(选项列表).index(候选值)
            setattr(self, 属性名, int(idx))
        except Exception:
            pass

    调速值 = str(参数.get("调速", "") or "").strip().replace("x", "X")
    if 调速值.startswith("X"):
        调速值 = 调速值[1:]
    _按值匹配("设置_调速索引", list(getattr(self, "设置_调速选项", [])), 调速值)

    _按值匹配(
        "设置_变速索引",
        list(getattr(self, "设置_变速选项", [])),
        str(参数.get("背景模式", 参数.get("变速", "")) or ""),
    )
    _按值匹配(
        "设置_谱面索引",
        list(getattr(self, "设置_谱面选项", [])),
        str(参数.get("谱面", 参数.get("变速类型", "")) or ""),
    )
    _按值匹配(
        "设置_隐藏索引",
        list(getattr(self, "设置_隐藏选项", [])),
        str(参数.get("隐藏", "") or ""),
    )
    _按值匹配(
        "设置_轨迹索引",
        list(getattr(self, "设置_轨迹选项", [])),
        str(参数.get("轨迹", "") or ""),
    )
    _按值匹配(
        "设置_方向索引",
        list(getattr(self, "设置_方向选项", [])),
        str(参数.get("方向", "") or ""),
    )
    _按值匹配(
        "设置_大小索引",
        list(getattr(self, "设置_大小选项", [])),
        str(参数.get("大小", "") or ""),
    )

    参数文本 = str(数据.get("设置参数文本", "") or "")
    背景文件名 = str(数据.get("背景文件名", 参数.get("背景", "")) or "")
    箭头文件名 = str(数据.get("箭头文件名", 参数.get("箭头", "")) or "")
    if not 背景文件名:
        背景文件名 = _设置页_从参数文本提取(参数文本, "背景")
    if not 箭头文件名:
        箭头文件名 = _设置页_从参数文本提取(参数文本, "箭头")

    背景列表 = list(getattr(self, "设置_背景大图文件名列表", []))
    if 背景文件名 and 背景列表:
        try:
            self.设置_背景索引 = max(
                0, min(len(背景列表) - 1, int(背景列表.index(背景文件名)))
            )
        except Exception:
            pass

    箭头列表 = list(getattr(self, "设置_箭头候选路径列表", []))
    if 箭头文件名 and 箭头列表:
        for i, p in enumerate(箭头列表):
            if os.path.basename(str(p or "")) == 箭头文件名:
                self.设置_箭头索引 = int(i)
                break


def _设置页_保存持久化设置(self) -> bool:
    设置参数 = dict(getattr(self, "设置_参数", {}) or {})
    背景文件名 = str(getattr(self, "设置_背景大图文件名", "") or "")
    箭头文件名 = str(getattr(self, "设置_箭头文件名", "") or "")

    数据 = {
        "设置参数": 设置参数,
        "背景文件名": 背景文件名,
        "箭头文件名": 箭头文件名,
        "设置参数文本": _设置页_构建参数文本(
            self, 设置参数=设置参数, 背景文件名=背景文件名, 箭头文件名=箭头文件名
        ),
        "索引": {
            "调速": int(getattr(self, "设置_调速索引", 0) or 0),
            "背景模式": int(getattr(self, "设置_变速索引", 0) or 0),
            "变速": int(getattr(self, "设置_变速索引", 0) or 0),
            "谱面": int(getattr(self, "设置_谱面索引", 0) or 0),
            "隐藏": int(getattr(self, "设置_隐藏索引", 0) or 0),
            "轨迹": int(getattr(self, "设置_轨迹索引", 0) or 0),
            "方向": int(getattr(self, "设置_方向索引", 0) or 0),
            "大小": int(getattr(self, "设置_大小索引", 0) or 0),
            "箭头": int(getattr(self, "设置_箭头索引", 0) or 0),
            "背景": int(getattr(self, "设置_背景索引", 0) or 0),
        },
    }
    return _设置页_写入持久化设置(self, 数据)


def _确保设置页资源(self):
    if getattr(self, "_设置页_资源已初始化", False):
        return
    self._设置页_资源已初始化 = True

    # 状态
    self.是否设置页 = False
    self._设置页_打开开始时间 = 0.0
    self._设置页_关闭开始时间 = 0.0
    self._设置页_打开动画时长 = 0.28
    self._设置页_关闭动画时长 = 0.22
    self._设置页_动画状态 = "closed"
    self._设置页_面板基础矩形 = pygame.Rect(0, 0, 10, 10)
    self._设置页_面板绘制矩形 = pygame.Rect(0, 0, 10, 10)
    self._设置页_最后绘制表面 = None
    self._设置页_最后缩放 = 1.0
    self._设置页_上次屏幕尺寸 = (0, 0)

    # 选项
    self.设置_调速选项 = 设置菜单默认调速选项()
    self.设置_变速选项 = ["图片", "视频"]
    self.设置_谱面选项 = ["正常", "未知"]
    self.设置_隐藏选项 = ["关闭", "半隐", "全隐"]
    self.设置_轨迹选项 = ["正常", "摇摆", "旋转"]
    self.设置_方向选项 = ["关闭", "反向"]
    self.设置_大小选项 = ["正常", "放大"]

    # 默认索引
    self.设置_调速索引 = 0
    self.设置_变速索引 = 0
    self.设置_谱面索引 = 0
    self.设置_隐藏索引 = 0
    self.设置_轨迹索引 = 0
    self.设置_方向索引 = 0
    self.设置_大小索引 = 0

    # 箭头候选
    self.设置_箭头候选路径列表 = []
    self._设置页_箭头候选原图缓存 = {}
    箭头候选目录 = _资源路径("UI-img", "选歌界面资源", "设置", "设置-箭头候选")
    if os.path.isdir(箭头候选目录):
        for 文件名 in sorted(os.listdir(箭头候选目录)):
            if 文件名.lower().endswith(".png"):
                self.设置_箭头候选路径列表.append(os.path.join(箭头候选目录, 文件名))
    self.设置_箭头索引 = 0

    # 背景候选：直接读取 冷资源/backimages/背景图 下的原图
    self.设置_背景缩略图路径列表 = []
    self.设置_背景大图文件名列表 = []
    self._设置页_背景缩略图原图缓存 = {}
    背景目录 = _资源路径("冷资源", "backimages", "背景图")
    if os.path.isdir(背景目录):
        支持后缀 = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
        for 文件名 in sorted(os.listdir(背景目录)):
            小写名 = str(文件名 or "").lower()
            if not 小写名.endswith(支持后缀):
                continue
            绝对路径 = os.path.join(背景目录, 文件名)
            if not os.path.isfile(绝对路径):
                continue
            self.设置_背景缩略图路径列表.append(绝对路径)
            self.设置_背景大图文件名列表.append(str(文件名))
    self.设置_背景索引 = 0

    # 参数输出
    self.设置_参数 = {}
    self.设置_背景大图文件名 = ""
    self.设置_箭头文件名 = ""
    try:
        self._设置页_加载持久化设置()
    except Exception:
        pass
    self._设置页_同步参数()
    try:
        self._设置页_保存持久化设置()
    except Exception:
        pass

    # 资源图
    self._设置页_缩放缓存 = {}
    self._设置页_背景图原图 = 安全加载图片(
        _资源路径("UI-img", "选歌界面资源", "设置", "设置背景图.png"),
        透明=True,
    )

    self._设置页_左小箭头原图 = 安全加载图片(
        _资源路径("UI-img", "选歌界面资源", "设置", "左小箭头.png"),
        透明=True,
    )
    self._设置页_右小箭头原图 = 安全加载图片(
        _资源路径("UI-img", "选歌界面资源", "设置", "右小箭头.png"),
        透明=True,
    )
    if self._设置页_右小箭头原图 is None and self._设置页_左小箭头原图 is not None:
        try:
            self._设置页_右小箭头原图 = pygame.transform.flip(
                self._设置页_左小箭头原图, True, False
            )
        except Exception:
            self._设置页_右小箭头原图 = None

    self._设置页_左大箭头原图 = 安全加载图片(
        _资源路径("UI-img", "选歌界面资源", "设置", "左大箭头.png"),
        透明=True,
    )
    self._设置页_右大箭头原图 = 安全加载图片(
        _资源路径("UI-img", "选歌界面资源", "设置", "右大箭头.png"),
        透明=True,
    )
    if self._设置页_右大箭头原图 is None and self._设置页_左大箭头原图 is not None:
        try:
            self._设置页_右大箭头原图 = pygame.transform.flip(
                self._设置页_左大箭头原图, True, False
            )
        except Exception:
            self._设置页_右大箭头原图 = None

    # 布局缓存
    self._设置页_行矩形表 = {}
    self._设置页_控件矩形表 = {}
    self._设置页_背景区矩形 = pygame.Rect(0, 0, 10, 10)
    self._设置页_背景控件矩形 = {
        "左": pygame.Rect(0, 0, 1, 1),
        "右": pygame.Rect(0, 0, 1, 1),
        "预览": pygame.Rect(0, 0, 1, 1),
    }

    self._设置页_箭头预览矩形 = pygame.Rect(0, 0, 10, 10)
    self._设置页_箭头预览控件矩形 = {
        "左": pygame.Rect(0, 0, 1, 1),
        "右": pygame.Rect(0, 0, 1, 1),
    }

    # 背景缩放缓存
    self._设置页_背景缩放缓存图 = None
    self._设置页_背景缩放缓存尺寸 = (0, 0)

    # ✅ 自动加载你已保存的布局覆盖 json（不再提供编辑/保存入口）
    try:
        if hasattr(self, "_设置页_加载布局覆盖"):
            self._设置页_加载布局覆盖(是否提示=False)
    except Exception:
        pass


def _设置页_同步参数(self):
    # ✅ 你要“存变量”，这里统一写入 self.设置_参数 + 单独的背景/箭头文件名
    self.设置_参数 = {
        "调速": f"X{self.设置_调速选项[self.设置_调速索引]}",
        "背景模式": self.设置_变速选项[self.设置_变速索引],
        "谱面": self.设置_谱面选项[self.设置_谱面索引],
        "隐藏": self.设置_隐藏选项[self.设置_隐藏索引],
        "轨迹": self.设置_轨迹选项[self.设置_轨迹索引],
        "方向": self.设置_方向选项[self.设置_方向索引],
        "大小": self.设置_大小选项[self.设置_大小索引],
    }

    if self.设置_箭头候选路径列表:
        当前箭头路径 = self.设置_箭头候选路径列表[self.设置_箭头索引]
        self.设置_箭头文件名 = os.path.basename(当前箭头路径)
    else:
        self.设置_箭头文件名 = ""

    if self.设置_背景大图文件名列表:
        self.设置_背景大图文件名 = self.设置_背景大图文件名列表[self.设置_背景索引]
    else:
        self.设置_背景大图文件名 = ""


def _设置页_取缩放图(
    self, 缓存键前缀: str, 原图: Optional[pygame.Surface], 目标宽: int, 目标高: int
) -> Optional[pygame.Surface]:
    if 原图 is None:
        return None
    目标宽 = max(1, int(目标宽))
    目标高 = max(1, int(目标高))
    缓存键 = (str(缓存键前缀), 目标宽, 目标高)

    if 缓存键 in self._设置页_缩放缓存:
        return self._设置页_缩放缓存.get(缓存键)

    try:
        缩放图 = pygame.transform.smoothscale(原图, (目标宽, 目标高)).convert_alpha()
    except Exception:
        缩放图 = None

    self._设置页_缩放缓存[缓存键] = 缩放图
    return 缩放图


def _重算设置页布局(self):
    self._确保设置页资源()

    当前屏宽, 当前屏高 = self.屏幕.get_size()
    if (
        getattr(self, "_设置页_上次屏幕尺寸", (0, 0)) == (当前屏宽, 当前屏高)
        and self._设置页_面板基础矩形.w > 20
    ):
        return
    self._设置页_上次屏幕尺寸 = (当前屏宽, 当前屏高)

    面板宽 = int(当前屏宽 * float(_设置页_面板宽占比) * float(_设置页_面板整体缩放))
    面板高 = int(当前屏高 * float(_设置页_面板高占比) * float(_设置页_面板整体缩放))

    面板宽 = max(700, min(面板宽, 当前屏宽 - 40))
    面板高 = max(420, min(面板高, 当前屏高 - 40))

    中心x = 当前屏宽 // 2 + int(_设置页_面板_x偏移)
    中心y = 当前屏高 // 2 + int(_设置页_面板_y偏移)

    self._设置页_面板基础矩形 = pygame.Rect(0, 0, 面板宽, 面板高)
    self._设置页_面板基础矩形.center = (中心x, 中心y)

    局部面板 = pygame.Rect(0, 0, 面板宽, 面板高)

    # ----------------------------
    # 左侧列表区域
    # ----------------------------
    左起x = int(局部面板.w * float(_设置页_左区_x占比))
    左起y = int(局部面板.h * float(_设置页_左区_y占比))
    左宽 = int(局部面板.w * float(_设置页_左区_宽占比))
    行高 = max(32, int(局部面板.h * float(_设置页_左区_行高占比)))
    行间距 = int(_设置页_左区_行间距像素)

    行键列表 = list(设置菜单行键列表())

    self._设置页_行矩形表 = {}
    当前y = 左起y
    for 行键 in 行键列表:
        dx, dy = _设置页_左区_行偏移覆盖.get(行键, (0, 0))
        行矩形 = pygame.Rect(左起x + int(dx), 当前y + int(dy), 左宽, 行高)
        self._设置页_行矩形表[行键] = 行矩形
        当前y += 行高 + 行间距

    self._设置页_控件矩形表 = {}
    for 行键, 行矩形 in self._设置页_行矩形表.items():
        小箭边长 = max(18, int(行矩形.h * 0.68))
        左箭 = pygame.Rect(行矩形.x, 行矩形.centery - 小箭边长 // 2, 小箭边长, 小箭边长)
        右箭 = pygame.Rect(
            行矩形.right - 小箭边长, 行矩形.centery - 小箭边长 // 2, 小箭边长, 小箭边长
        )
        内容 = pygame.Rect(
            左箭.right + 8, 行矩形.y, 行矩形.w - 小箭边长 * 2 - 16, 行矩形.h
        )
        self._设置页_控件矩形表[行键] = {"左": 左箭, "右": 右箭, "内容": 内容}

    # ----------------------------
    # 左下：箭头预览框
    # ----------------------------
    try:
        预览w = max(60, int(局部面板.w * float(_设置页_箭头预览_宽占比)))
        预览h = max(60, int(局部面板.h * float(_设置页_箭头预览_高占比)))
        预览x = int(局部面板.w * float(_设置页_箭头预览_x占比)) + int(
            _设置页_箭头预览_额外偏移[0]
        )
        预览y = int(局部面板.h * float(_设置页_箭头预览_y占比)) + int(
            _设置页_箭头预览_额外偏移[1]
        )

        列表底 = max([r.bottom for r in self._设置页_行矩形表.values()] + [0])
        预览y = max(预览y, 列表底 + max(6, int(局部面板.h * 0.01)))

        r = pygame.Rect(预览x, 预览y, 预览w, 预览h).clip(局部面板.inflate(-10, -10))
        if r.w < 30 or r.h < 30:
            r = pygame.Rect(预览x, 预览y, max(30, 预览w), max(30, 预览h)).clip(
                局部面板.inflate(-10, -10)
            )
        self._设置页_箭头预览矩形 = r
    except Exception:
        self._设置页_箭头预览矩形 = pygame.Rect(0, 0, 10, 10)

    # ----------------------------
    # ✅ 预览框左右箭头：保证尺寸不为 0
    # ----------------------------
    try:
        预览框 = self._设置页_箭头预览矩形
        箭边长 = max(34, int(预览框.h * 0.62))
        箭边长 = min(箭边长, max(34, int(预览框.w * 0.45)))
        间距 = max(8, int(箭边长 * 0.18))

        左箭x = 预览框.x - 间距 - 箭边长
        右箭x = 预览框.right + 间距

        # 如果太靠边：塞进预览框左右内侧（确保可见）
        if 左箭x < 0:
            左箭x = 预览框.x + 6
        if (右箭x + 箭边长) > 局部面板.w:
            右箭x = max(0, 预览框.right - 箭边长 - 6)

        左箭 = pygame.Rect(左箭x, 预览框.centery - 箭边长 // 2, 箭边长, 箭边长)
        右箭 = pygame.Rect(右箭x, 预览框.centery - 箭边长 // 2, 箭边长, 箭边长)

        # 最低限：别被 clip 成 1x1
        左箭 = 左箭.clip(局部面板.inflate(-2, -2))
        右箭 = 右箭.clip(局部面板.inflate(-2, -2))
        if 左箭.w < 10 or 左箭.h < 10:
            左箭 = pygame.Rect(预览框.x + 6, 预览框.centery - 18, 36, 36).clip(
                局部面板.inflate(-2, -2)
            )
        if 右箭.w < 10 or 右箭.h < 10:
            右箭 = pygame.Rect(预览框.right - 42, 预览框.centery - 18, 36, 36).clip(
                局部面板.inflate(-2, -2)
            )

        self._设置页_箭头预览控件矩形 = {"左": 左箭, "右": 右箭}
    except Exception:
        self._设置页_箭头预览控件矩形 = {
            "左": pygame.Rect(0, 0, 1, 1),
            "右": pygame.Rect(0, 0, 1, 1),
        }

    # ----------------------------
    # 右侧背景区域
    # ----------------------------
    右起x = int(局部面板.w * float(_设置页_右区_x占比)) + int(_设置页_右区_额外偏移[0])
    右起y = int(局部面板.h * float(_设置页_右区_y占比)) + int(_设置页_右区_额外偏移[1])
    右宽 = int(局部面板.w * float(_设置页_右区_宽占比))
    右高 = int(局部面板.h * float(_设置页_右区_高占比))
    self._设置页_背景区矩形 = pygame.Rect(右起x, 右起y, 右宽, 右高)

    大箭边长基准 = max(26, int(self._设置页_背景区矩形.h * 0.18))
    左箭缩放 = float(max(0.3, min(3.0, float(_设置页_右区_左大箭头_缩放))))
    右箭缩放 = float(max(0.3, min(3.0, float(_设置页_右区_右大箭头_缩放))))
    左箭边长 = max(16, int(round(float(大箭边长基准) * 左箭缩放)))
    右箭边长 = max(16, int(round(float(大箭边长基准) * 右箭缩放)))
    左大箭 = pygame.Rect(
        int(self._设置页_背景区矩形.x + int(_设置页_右区_左大箭头_偏移[0])),
        int(
            self._设置页_背景区矩形.centery
            - 左箭边长 // 2
            + int(_设置页_右区_左大箭头_偏移[1])
        ),
        int(左箭边长),
        int(左箭边长),
    )
    右大箭 = pygame.Rect(
        int(
            self._设置页_背景区矩形.right
            - 右箭边长
            + int(_设置页_右区_右大箭头_偏移[0])
        ),
        int(
            self._设置页_背景区矩形.centery
            - 右箭边长 // 2
            + int(_设置页_右区_右大箭头_偏移[1])
        ),
        int(右箭边长),
        int(右箭边长),
    )

    内边距 = int(_设置页_右区_预览内边距)
    预览基准区 = pygame.Rect(
        int(左大箭.right + 10),
        int(self._设置页_背景区矩形.y + 内边距),
        int(max(10, self._设置页_背景区矩形.w - 左大箭.w - 右大箭.w - 20)),
        int(max(10, self._设置页_背景区矩形.h - 内边距 * 2)),
    )
    预览宽缩放 = float(max(0.2, min(3.0, float(_设置页_右区_预览框_宽缩放))))
    预览高缩放 = float(max(0.2, min(3.0, float(_设置页_右区_预览框_高缩放))))
    预览区 = pygame.Rect(
        0,
        0,
        int(max(10, round(float(预览基准区.w) * 预览宽缩放))),
        int(max(10, round(float(预览基准区.h) * 预览高缩放))),
    )
    预览区.center = (
        int(预览基准区.centerx + int(_设置页_右区_预览框_偏移[0])),
        int(预览基准区.centery + int(_设置页_右区_预览框_偏移[1])),
    )

    self._设置页_背景控件矩形 = {"左": 左大箭, "右": 右大箭, "预览": 预览区}


def _设置页_缓出(self, 进度: float) -> float:
    try:
        进度 = float(进度)
    except Exception:
        进度 = 1.0
    if 进度 < 0.0:
        进度 = 0.0
    if 进度 > 1.0:
        进度 = 1.0
    # easeOutQuad
    return 1.0 - (1.0 - 进度) * (1.0 - 进度)


def _设置页_缓入(self, 进度: float) -> float:
    try:
        进度 = float(进度)
    except Exception:
        进度 = 1.0
    if 进度 < 0.0:
        进度 = 0.0
    if 进度 > 1.0:
        进度 = 1.0
    return 进度 * 进度 * 进度


def _设置页_立即隐藏(self):
    self.是否设置页 = False
    self._设置页_动画状态 = "closed"
    self._设置页_最后绘制表面 = None


def _设置页_取动画参数(self) -> dict:
    if not bool(getattr(self, "是否设置页", False)):
        return {"是否可见": False}

    现在 = time.time()
    状态 = str(getattr(self, "_设置页_动画状态", "open") or "open")

    if 状态 == "closing":
        开始 = float(getattr(self, "_设置页_关闭开始时间", 0.0) or 0.0)
        时长 = float(getattr(self, "_设置页_关闭动画时长", 0.22) or 0.22)
        if 开始 <= 0.0 or 时长 <= 0.0:
            _设置页_立即隐藏(self)
            return {"是否可见": False}

        进度 = (现在 - 开始) / max(0.001, 时长)
        if 进度 >= 1.0:
            _设置页_立即隐藏(self)
            return {"是否可见": False}

        缓进度 = self._设置页_缓入(进度)
        return {
            "是否可见": True,
            "缩放": 1.0 - 0.05 * 缓进度,
            "透明度": 1.0 - 缓进度,
            "遮罩透明度": 170 * (1.0 - 缓进度),
            "y偏移": int(20 * 缓进度),
        }

    开始 = float(getattr(self, "_设置页_打开开始时间", 0.0) or 0.0)
    时长 = float(getattr(self, "_设置页_打开动画时长", 0.28) or 0.28)
    if 开始 <= 0.0 or 时长 <= 0.0:
        self._设置页_动画状态 = "open"
        return {
            "是否可见": True,
            "缩放": 1.0,
            "透明度": 1.0,
            "遮罩透明度": 170,
            "y偏移": 0,
        }

    进度 = (现在 - 开始) / max(0.001, 时长)
    if 进度 >= 1.0:
        self._设置页_动画状态 = "open"
        return {
            "是否可见": True,
            "缩放": 1.0,
            "透明度": 1.0,
            "遮罩透明度": 170,
            "y偏移": 0,
        }

    缓进度 = self._设置页_缓出(进度)
    return {
        "是否可见": True,
        "缩放": 0.94 + 0.06 * 缓进度,
        "透明度": 缓进度,
        "遮罩透明度": 170 * 缓进度,
        "y偏移": int((1.0 - 缓进度) * 24),
    }


def _设置页_点在有效面板区域(self, 屏幕点) -> bool:
    面板绘制矩形 = getattr(self, "_设置页_面板绘制矩形", None)
    if not isinstance(面板绘制矩形, pygame.Rect):
        return False
    if not 面板绘制矩形.collidepoint(屏幕点):
        return False

    面板表面 = getattr(self, "_设置页_最后绘制表面", None)
    if not isinstance(面板表面, pygame.Surface):
        return True

    局部x = int(屏幕点[0] - 面板绘制矩形.x)
    局部y = int(屏幕点[1] - 面板绘制矩形.y)
    if (
        局部x < 0
        or 局部y < 0
        or 局部x >= int(面板表面.get_width())
        or 局部y >= int(面板表面.get_height())
    ):
        return False

    try:
        return int(面板表面.get_at((局部x, 局部y)).a) > 12
    except Exception:
        return True


def 打开设置页(self):
    self._确保设置页资源()
    # 每次打开都重读一次布局覆盖，便于外部调试器实时打磨
    try:
        if hasattr(self, "_设置页_加载布局覆盖"):
            self._设置页_加载布局覆盖(是否提示=False)
    except Exception:
        pass
    # 关闭其它面板，避免状态叠加
    try:
        self.是否星级筛选页 = False
        self.是否模式选择页 = False
    except Exception:
        pass

    # ✅ 强制重算（避免“重新打开错乱/不刷新”）
    try:
        self._设置页_上次屏幕尺寸 = (0, 0)
    except Exception:
        pass

    self._重算设置页布局()
    self.是否设置页 = True
    self._设置页_动画状态 = "opening"
    self._设置页_打开开始时间 = time.time()
    self._设置页_关闭开始时间 = 0.0


def 关闭设置页(self, 立即: bool = False):
    self._确保设置页资源()
    if bool(立即):
        _设置页_立即隐藏(self)
        return
    if not bool(getattr(self, "是否设置页", False)):
        return
    if str(getattr(self, "_设置页_动画状态", "") or "") == "closing":
        return
    self._设置页_动画状态 = "closing"
    self._设置页_关闭开始时间 = time.time()


def _设置页_切换选项(self, 行键: str, 方向: int):
    self._确保设置页资源()
    try:
        方向 = int(方向)
    except Exception:
        方向 = 0
    if 方向 == 0:
        return

    # 行键 -> 实际索引/选项表
    if 行键 == "调速":
        总数 = len(self.设置_调速选项)
        if 总数 > 0:
            self.设置_调速索引 = (self.设置_调速索引 + 方向) % 总数

    elif 行键 == "变速":
        总数 = len(self.设置_变速选项)
        if 总数 > 0:
            self.设置_变速索引 = (self.设置_变速索引 + 方向) % 总数

    elif 行键 == "变速类型":
        总数 = len(self.设置_谱面选项)
        if 总数 > 0:
            self.设置_谱面索引 = (self.设置_谱面索引 + 方向) % 总数

    elif 行键 == "隐藏":
        总数 = len(self.设置_隐藏选项)
        if 总数 > 0:
            self.设置_隐藏索引 = (self.设置_隐藏索引 + 方向) % 总数

    elif 行键 == "轨迹":
        总数 = len(self.设置_轨迹选项)
        if 总数 > 0:
            self.设置_轨迹索引 = (self.设置_轨迹索引 + 方向) % 总数

    elif 行键 == "方向":
        总数 = len(self.设置_方向选项)
        if 总数 > 0:
            self.设置_方向索引 = (self.设置_方向索引 + 方向) % 总数

    elif 行键 == "大小":
        总数 = len(self.设置_大小选项)
        if 总数 > 0:
            self.设置_大小索引 = (self.设置_大小索引 + 方向) % 总数

    elif 行键 == "箭头":
        总数 = len(self.设置_箭头候选路径列表)
        if 总数 > 0:
            self.设置_箭头索引 = (self.设置_箭头索引 + 方向) % 总数

    self._设置页_同步参数()
    try:
        self._设置页_保存持久化设置()
    except Exception:
        pass


def _设置页_切换背景(self, 方向: int):
    self._确保设置页资源()
    try:
        方向 = int(方向)
    except Exception:
        方向 = 0
    if 方向 == 0:
        return
    总数 = len(self.设置_背景缩略图路径列表)
    if 总数 <= 0:
        return
    self.设置_背景索引 = (self.设置_背景索引 + 方向) % 总数
    self._设置页_同步参数()
    try:
        self._设置页_保存持久化设置()
    except Exception:
        pass


def _设置页_布局覆盖文件路径(self) -> str:
    脚本目录 = _取项目根目录()
    return os.path.join(脚本目录, "json", "设置页布局覆盖.json")


def _设置页_加载布局覆盖(self, 是否提示: bool = True) -> bool:
    try:
        import json
    except Exception:
        return False

    目标文件 = _设置页_布局覆盖文件路径(self)
    if not os.path.isfile(目标文件):
        if 是否提示:
            try:
                self._显示调试提示(
                    "未找到 设置页布局覆盖.json（先 Ctrl+S 保存一次）", 1.6
                )
            except Exception:
                pass
        return False

    try:
        with open(目标文件, "r", encoding="utf-8") as f:
            数据 = json.load(f)
    except Exception:
        return False

    if not isinstance(数据, dict):
        return False

    g = globals()

    # ✅ 先处理行偏移覆盖（dict）
    if "_设置页_左区_行偏移覆盖" in 数据:
        try:
            v = 数据.get("_设置页_左区_行偏移覆盖")
            原 = g.get("_设置页_左区_行偏移覆盖", {})
            if not isinstance(原, dict):
                原 = {}

            可见行键 = set(设置菜单行键列表())

            if isinstance(v, dict):
                for 行键, 偏移 in v.items():
                    行键 = str(行键)
                    if 行键 not in 可见行键:
                        continue
                    if isinstance(偏移, (list, tuple)) and len(偏移) >= 2:
                        原[行键] = (int(偏移[0]), int(偏移[1]))

            g["_设置页_左区_行偏移覆盖"] = 原
        except Exception:
            pass

    # ✅ 再覆盖其它 _设置页_ 开头的标量/tuple/list
    for k, v in 数据.items():
        if not (isinstance(k, str) and k.startswith("_设置页_")):
            continue
        if k == "_设置页_左区_行偏移覆盖":
            continue
        if k not in g:
            continue

        原值 = g.get(k)
        try:
            if isinstance(原值, float):
                g[k] = float(v)
            elif isinstance(原值, int):
                g[k] = int(v)
            elif isinstance(原值, str):
                g[k] = str(v)
            elif isinstance(原值, (tuple, list)):
                if isinstance(v, list):
                    g[k] = tuple(v) if isinstance(原值, tuple) else list(v)
        except Exception:
            continue

    # ✅ 强制重算布局
    try:
        self._设置页_上次屏幕尺寸 = (0, 0)
        self._重算设置页布局()
    except Exception:
        pass

    if 是否提示:
        try:
            self._显示调试提示("已加载：设置页布局覆盖.json", 1.2)
        except Exception:
            pass
    return True


def _设置页_处理事件(self, 事件):
    self._确保设置页资源()
    self._重算设置页布局()

    if str(getattr(self, "_设置页_动画状态", "") or "") == "closing":
        return

    面板绘制矩形 = getattr(self, "_设置页_面板绘制矩形", None)
    if not isinstance(面板绘制矩形, pygame.Rect):
        面板绘制矩形 = self._设置页_面板基础矩形

    当前缩放 = float(getattr(self, "_设置页_最后缩放", 1.0) or 1.0)
    当前缩放 = max(0.001, 当前缩放)

    def _转局部坐标(屏幕点):
        局部x = int((屏幕点[0] - 面板绘制矩形.x) / 当前缩放)
        局部y = int((屏幕点[1] - 面板绘制矩形.y) / 当前缩放)
        return (局部x, 局部y)

    # ESC：关闭设置页
    if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
        self.关闭设置页()
        return

    # 只处理左键点击
    if 事件.type != pygame.MOUSEBUTTONDOWN or 事件.button != 1:
        return

    # 点到面板外或透明像素：关闭
    if not self._设置页_点在有效面板区域(事件.pos):
        self.关闭设置页()
        return

    局部点 = _转局部坐标(事件.pos)

    # ✅ 左下：箭头预览左右切换
    try:
        控件 = getattr(self, "_设置页_箭头预览控件矩形", None)
        if isinstance(控件, dict):
            if 控件.get("左", pygame.Rect(0, 0, 0, 0)).collidepoint(局部点):
                self._播放按钮音效()
                self._设置页_切换选项("箭头", -1)
                return
            if 控件.get("右", pygame.Rect(0, 0, 0, 0)).collidepoint(局部点):
                self._播放按钮音效()
                self._设置页_切换选项("箭头", +1)
                return
    except Exception:
        pass

    # ✅ 右侧：背景大箭头
    背景控件 = self._设置页_背景控件矩形
    if 背景控件["左"].collidepoint(局部点):
        self._播放按钮音效()
        self._设置页_切换背景(-1)
        return
    if 背景控件["右"].collidepoint(局部点):
        self._播放按钮音效()
        self._设置页_切换背景(+1)
        return

    # ✅ 左侧：每行的小箭头
    for 行键, 控件 in self._设置页_控件矩形表.items():
        if 控件["左"].collidepoint(局部点):
            self._播放按钮音效()
            self._设置页_切换选项(行键, -1)
            return
        if 控件["右"].collidepoint(局部点):
            self._播放按钮音效()
            self._设置页_切换选项(行键, +1)
            return


def 绘制设置页(self):
    self._确保设置页资源()
    self._重算设置页布局()

    动画参数 = _设置页_取动画参数(self)
    if not bool(动画参数.get("是否可见", False)):
        return

    # 遮罩
    遮罩 = pygame.Surface((self.宽, self.高), pygame.SRCALPHA)
    遮罩.fill(
        (
            0,
            0,
            0,
            int(max(0, min(255, 动画参数.get("遮罩透明度", 170)))),
        )
    )
    self.屏幕.blit(遮罩, (0, 0))

    面板矩形 = self._设置页_面板基础矩形
    面板画布 = pygame.Surface((面板矩形.w, 面板矩形.h), pygame.SRCALPHA)

    # 背景图
    if self._设置页_背景图原图 is not None:
        目标尺寸 = (面板矩形.w, 面板矩形.h)
        if (
            self._设置页_背景缩放缓存图 is None
            or self._设置页_背景缩放缓存尺寸 != 目标尺寸
        ):
            try:
                self._设置页_背景缩放缓存图 = pygame.transform.smoothscale(
                    self._设置页_背景图原图, 目标尺寸
                ).convert_alpha()
                self._设置页_背景缩放缓存尺寸 = 目标尺寸
            except Exception:
                self._设置页_背景缩放缓存图 = None
                self._设置页_背景缩放缓存尺寸 = (0, 0)

        if self._设置页_背景缩放缓存图 is not None:
            面板画布.blit(self._设置页_背景缩放缓存图, (0, 0))
    else:
        面板画布.fill((10, 20, 40, 235))

    示例行 = next(iter(self._设置页_行矩形表.values()), pygame.Rect(0, 0, 200, 50))
    标签字号 = max(16, int(示例行.h * 0.46))
    选项字号 = max(16, int(示例行.h * 0.50))
    标签字体 = 获取字体(标签字号, 是否粗体=False)
    选项字体 = 获取字体(选项字号, 是否粗体=True)
    小字字体 = 获取字体(max(14, int(示例行.h * 0.34)), 是否粗体=False)

    # 左侧每行：小箭头 + 文字
    for 行键, 控件 in self._设置页_控件矩形表.items():
        左箭 = 控件["左"]
        右箭 = 控件["右"]
        内容 = 控件["内容"]

        左箭图 = self._设置页_取缩放图(
            f"设置_左小_{行键}", self._设置页_左小箭头原图, 左箭.w, 左箭.h
        )
        右箭图 = self._设置页_取缩放图(
            f"设置_右小_{行键}", self._设置页_右小箭头原图, 右箭.w, 右箭.h
        )

        if 左箭图 is not None:
            面板画布.blit(左箭图, 左箭.topleft)
        if 右箭图 is not None:
            面板画布.blit(右箭图, 右箭.topleft)

        显示名 = 设置菜单行显示名(行键)

        绘制文本(
            面板画布,
            显示名,
            标签字体,
            (235, 245, 255),
            (内容.x + 10, 内容.centery),
            对齐="midleft",
        )

        值 = 设置菜单行值(行键, getattr(self, "设置_参数", {}))

        绘制文本(
            面板画布,
            值,
            选项字体,
            (255, 255, 255),
            (内容.right - 10, 内容.centery),
            对齐="midright",
        )

    # 左下：箭头候选预览 + 左右切换
    预览框 = getattr(self, "_设置页_箭头预览矩形", pygame.Rect(0, 0, 10, 10))
    if isinstance(预览框, pygame.Rect) and 预览框.w > 10 and 预览框.h > 10:
        当前候选路径 = None
        if self.设置_箭头候选路径列表:
            当前候选路径 = self.设置_箭头候选路径列表[self.设置_箭头索引]

        候选图 = None
        if 当前候选路径:
            候选图 = self._设置页_箭头候选原图缓存.get(当前候选路径)
            if 候选图 is None:
                候选图 = 安全加载图片(当前候选路径, 透明=True)
                self._设置页_箭头候选原图缓存[当前候选路径] = 候选图

        if 候选图 is not None:
            内边距 = int(_设置页_箭头预览_内边距)
            可用 = 预览框.inflate(-内边距 * 2, -内边距 * 2)
            ow, oh = 候选图.get_size()
            比例 = min(可用.w / max(1, ow), 可用.h / max(1, oh))
            nw = max(1, int(ow * 比例))
            nh = max(1, int(oh * 比例))
            try:
                候选缩放 = pygame.transform.smoothscale(
                    候选图, (nw, nh)
                ).convert_alpha()
                x = 可用.centerx - nw // 2
                y = 可用.centery - nh // 2
                面板画布.blit(候选缩放, (x, y))
            except Exception:
                pass
        else:
            绘制文本(
                面板画布,
                "无箭头候选",
                小字字体,
                (255, 220, 120),
                预览框.center,
                对齐="center",
            )

        # 左右切换箭头
        try:
            控件 = getattr(self, "_设置页_箭头预览控件矩形", None)
            if isinstance(控件, dict):
                左r = 控件.get("左", pygame.Rect(0, 0, 0, 0))
                右r = 控件.get("右", pygame.Rect(0, 0, 0, 0))
                左图 = self._设置页_取缩放图(
                    "设置_箭头预览_左", self._设置页_左大箭头原图, 左r.w, 左r.h
                )
                右图 = self._设置页_取缩放图(
                    "设置_箭头预览_右", self._设置页_右大箭头原图, 右r.w, 右r.h
                )
                if 左图 is not None and 左r.w > 2 and 左r.h > 2:
                    面板画布.blit(左图, 左r.topleft)
                if 右图 is not None and 右r.w > 2 and 右r.h > 2:
                    面板画布.blit(右图, 右r.topleft)
        except Exception:
            pass

        # 显示箭头文件名
        try:
            名称 = os.path.splitext(str(getattr(self, "设置_箭头文件名", "") or ""))[0]
            if 名称:
                绘制文本(
                    面板画布,
                    名称,
                    小字字体,
                    (220, 240, 255),
                    (
                        预览框.centerx,
                        min(面板画布.get_height() - 6, 预览框.bottom + 18),
                    ),
                    对齐="midtop",
                )
        except Exception:
            pass

    # 右侧背景选择：大箭头 + 缩略图预览
    背景控件 = self._设置页_背景控件矩形
    左大箭 = 背景控件["左"]
    右大箭 = 背景控件["右"]
    预览区 = 背景控件["预览"]

    左大箭图 = self._设置页_取缩放图(
        "设置_左大", self._设置页_左大箭头原图, 左大箭.w, 左大箭.h
    )
    右大箭图 = self._设置页_取缩放图(
        "设置_右大", self._设置页_右大箭头原图, 右大箭.w, 右大箭.h
    )

    if 左大箭图 is not None:
        面板画布.blit(左大箭图, 左大箭.topleft)
    if 右大箭图 is not None:
        面板画布.blit(右大箭图, 右大箭.topleft)

    当前缩略图路径 = None
    if self.设置_背景缩略图路径列表:
        当前缩略图路径 = self.设置_背景缩略图路径列表[self.设置_背景索引]

    缩略图 = None
    if 当前缩略图路径:
        缩略图 = self._设置页_背景缩略图原图缓存.get(当前缩略图路径)
        if 缩略图 is None:
            缩略图 = 安全加载图片(当前缩略图路径, 透明=True)
            self._设置页_背景缩略图原图缓存[当前缩略图路径] = 缩略图

    if 缩略图 is not None:
        try:
            绘制_cover裁切预览(面板画布, 缩略图, 预览区)
        except Exception:
            pass
    else:
        绘制文本(
            面板画布,
            "无背景图",
            小字字体,
            (255, 220, 120),
            预览区.center,
            对齐="center",
        )

    动画缩放 = float(动画参数.get("缩放", 1.0) or 1.0)
    动画透明 = int(255 * float(动画参数.get("透明度", 1.0) or 1.0))
    动画透明 = max(0, min(255, 动画透明))

    self._设置页_最后缩放 = float(动画缩放)

    if 动画缩放 != 1.0:
        画宽 = max(1, int(面板画布.get_width() * 动画缩放))
        画高 = max(1, int(面板画布.get_height() * 动画缩放))
        try:
            面板画布2 = pygame.transform.smoothscale(
                面板画布, (画宽, 画高)
            ).convert_alpha()
        except Exception:
            面板画布2 = 面板画布
    else:
        面板画布2 = 面板画布

    try:
        面板画布2.set_alpha(动画透明)
    except Exception:
        pass

    绘制矩形 = 面板画布2.get_rect()
    绘制矩形.center = 面板矩形.center
    绘制矩形.y += int(动画参数.get("y偏移", 0) or 0)
    self._设置页_面板绘制矩形 = 绘制矩形
    self._设置页_最后绘制表面 = 面板画布2
    self.屏幕.blit(面板画布2, 绘制矩形.topleft)


def _资源路径(*片段: str) -> str:
    脚本目录 = _取项目根目录()
    return os.path.join(脚本目录, *片段)


def 获取UI原图(路径: str, 透明: bool = True) -> Optional[pygame.Surface]:
    if not 路径:
        return None
    key = f"{路径}|{'A' if 透明 else 'O'}"
    if key in _UI原图缓存:
        return _UI原图缓存[key]
    图 = 安全加载图片(路径, 透明=透明)
    _UI原图缓存[key] = 图
    return 图


def 获取UI缩放图(
    路径: str, 目标宽: int, 目标高: int, 透明: bool = True
) -> Optional[pygame.Surface]:
    if (not 路径) or 目标宽 <= 0 or 目标高 <= 0:
        return None
    key = (f"{路径}|{'A' if 透明 else 'O'}", int(目标宽), int(目标高), bool(透明))
    if key in _UI缩放缓存:
        return _UI缩放缓存[key]

    原图 = 获取UI原图(路径, 透明=透明)
    if 原图 is None:
        _UI缩放缓存[key] = None
        return None

    try:
        缩放 = pygame.transform.smoothscale(原图, (int(目标宽), int(目标高)))
        缩放 = 缩放.convert_alpha() if 透明 else 缩放.convert()
    except Exception:
        缩放 = None

    _UI缩放缓存[key] = 缩放
    return 缩放


# =========================
# ✅ UI容器等比缩放缓存（contain/cover/stretch）
# =========================
_UI容器缓存: Dict[Tuple[str, int, int, bool, str], Optional[pygame.Surface]] = {}


def 获取UI容器图(
    路径: str, 目标宽: int, 目标高: int, 缩放模式: str = "stretch", 透明: bool = True
) -> Optional[pygame.Surface]:
    """
    返回一个“容器尺寸=目标宽高”的 Surface：
    - stretch：直接拉伸到容器
    - contain：等比完整展示，四周透明留边
    - cover  ：等比铺满容器，裁切超出部分
    """
    if (not 路径) or 目标宽 <= 0 or 目标高 <= 0:
        return None

    模式 = str(缩放模式 or "stretch").strip().lower()
    if 模式 not in ("stretch", "contain", "cover"):
        模式 = "stretch"

    key = (f"{路径}|{'A' if 透明 else 'O'}", int(目标宽), int(目标高), bool(透明), 模式)
    if key in _UI容器缓存:
        return _UI容器缓存.get(key)

    原图 = 获取UI原图(路径, 透明=透明)
    if 原图 is None:
        _UI容器缓存[key] = None
        return None

    ow, oh = 原图.get_size()
    if ow <= 0 or oh <= 0:
        _UI容器缓存[key] = None
        return None

    try:
        if 模式 == "stretch":
            out = pygame.transform.smoothscale(原图, (int(目标宽), int(目标高)))
            out = out.convert_alpha() if 透明 else out.convert()
            _UI容器缓存[key] = out
            return out

        # contain / cover 都做“先等比缩放 -> 再贴到容器画布”
        if 模式 == "contain":
            比例 = min(float(目标宽) / float(ow), float(目标高) / float(oh))
        else:  # cover
            比例 = max(float(目标宽) / float(ow), float(目标高) / float(oh))

        nw = max(1, int(ow * 比例))
        nh = max(1, int(oh * 比例))
        缩放图 = pygame.transform.smoothscale(原图, (nw, nh)).convert_alpha()

        画布 = pygame.Surface((int(目标宽), int(目标高)), pygame.SRCALPHA)
        画布.fill((0, 0, 0, 0))
        x = (int(目标宽) - nw) // 2
        y = (int(目标高) - nh) // 2
        # x/y 允许为负，pygame 会自动裁剪
        画布.blit(缩放图, (x, y))

        _UI容器缓存[key] = 画布.convert_alpha()
        return _UI容器缓存[key]
    except Exception:
        _UI容器缓存[key] = None
        return None


# =========================
# ✅ 全局：读取 json/选歌布局.json（给歌曲卡片等“非self方法”使用）
# =========================
_选歌布局_缓存: dict | None = None
_选歌布局_修改时间: float = -1.0


def _选歌布局_文件路径() -> str:
    return os.path.join(_取项目根目录(), "json", "选歌布局.json")


def 读取选歌布局配置() -> dict:
    global _选歌布局_缓存, _选歌布局_修改时间
    路径 = _选歌布局_文件路径()

    try:
        mt = os.path.getmtime(路径) if os.path.isfile(路径) else 0.0
    except Exception:
        mt = 0.0

    if _选歌布局_缓存 is not None and float(_选歌布局_修改时间) == float(mt):
        return _选歌布局_缓存

    数据 = {}
    if os.path.isfile(路径):
        try:
            import json

            with open(路径, "r", encoding="utf-8") as f:
                数据 = json.load(f)
        except Exception:
            数据 = {}

    if not isinstance(数据, dict):
        数据 = {}

    _选歌布局_缓存 = 数据
    _选歌布局_修改时间 = float(mt)
    return 数据


def 取选歌布局值(键路径: str, 默认值):
    配置 = 读取选歌布局配置()
    当前 = 配置
    for 片段 in str(键路径 or "").split("."):
        if not 片段:
            continue
        if not isinstance(当前, dict) or 片段 not in 当前:
            return 默认值
        当前 = 当前.get(片段)
    return 默认值 if 当前 is None else 当前


def 取选歌布局像素(
    键路径: str, 默认像素: int, 屏宽: int, 屏高: int, 最小: int = None, 最大: int = None
) -> int:
    原 = 取选歌布局值(键路径, 默认像素)

    def _解析成浮点(v) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = v.strip().lower()
            m = re.match(r"^(-?\d+(?:\.\d+)?)\s*(w|h|min)$", s)
            if m:
                数 = float(m.group(1))
                单位 = m.group(2)
                if 单位 == "w":
                    基准 = float(屏宽)
                elif 单位 == "h":
                    基准 = float(屏高)
                else:
                    基准 = float(min(int(屏宽), int(屏高)))
                return 数 * 基准
            return float(s)
        return float(默认像素)

    try:
        值 = int(round(_解析成浮点(原)))
    except Exception:
        值 = int(默认像素)

    if 最小 is not None:
        值 = max(int(最小), 值)
    if 最大 is not None:
        值 = min(int(最大), 值)
    return 值


# ===== 按高度缩放缓存（新增：放在 _按高等比缩放 上方也行）=====
_按高缩放缓存: Dict[Tuple[int, int], Optional[pygame.Surface]] = {}


def _按高等比缩放(图: pygame.Surface, 目标高: int) -> Optional[pygame.Surface]:
    if 图 is None:
        return None
    try:
        目标高 = int(目标高)
    except Exception:
        return None
    if 目标高 <= 0:
        return None

    try:
        ow, oh = 图.get_size()
    except Exception:
        return None
    if ow <= 0 or oh <= 0:
        return None

    缓存键 = (int(id(图)), int(目标高))
    if 缓存键 in _按高缩放缓存:
        return _按高缩放缓存.get(缓存键)

    比例 = float(目标高) / float(oh)
    nw = max(1, int(ow * 比例))

    try:
        缩放图 = pygame.transform.smoothscale(图, (nw, int(目标高))).convert_alpha()
    except Exception:
        缩放图 = None

    _按高缩放缓存[缓存键] = 缩放图

    # ✅ 防御：避免缓存无限增长（窗口频繁 resize 时尤其明显）
    if len(_按高缩放缓存) > 1800:
        _按高缩放缓存.clear()

    return 缩放图


def 绘制序号标签_图片(
    屏幕: pygame.Surface,
    锚点矩形: pygame.Rect,
    内部序号从0: int,
    是否大图: bool,
):
    """
    修复点：
    - ❌ 原来用 (format后)[-2:] 截断，100 变 00
    - ✅ 不截断，支持 2 位/3 位/更多位数字渲染
    - ✅ 数字过宽时自动缩小，尽量塞进标签纸
    """
    标签纸路径 = _资源路径(
        "UI-img",
        "选歌界面资源",
        "数字-选歌序号",
        "大号标签纸.png" if 是否大图 else "小号标签纸.png",
    )
    数字目录 = _资源路径("UI-img", "选歌界面资源", "数字-选歌序号")

    标签纸原图 = 获取UI原图(标签纸路径, 透明=True)
    if 标签纸原图 is None:
        return

    # =========================
    # ✅ 读取“缩略图/大图”两套参数
    # =========================
    if 是否大图:
        背景缩放 = float(_大图_序号背景_缩放)
        背景x偏移 = int(_大图_序号背景_x偏移)
        背景y偏移 = int(_大图_序号背景_y偏移)

        数字缩放 = float(_大图_序号数字_缩放)
        数字x偏移 = int(_大图_序号数字_x偏移)
        数字y偏移 = int(_大图_序号数字_y偏移)

        显示格式 = str(_序号显示格式_大图)
    else:
        背景缩放 = float(_缩略图_序号背景_缩放)
        背景x偏移 = int(_缩略图_序号背景_x偏移)
        背景y偏移 = int(_缩略图_序号背景_y偏移)

        数字缩放 = float(_缩略图_序号数字_缩放)
        数字x偏移 = int(_缩略图_序号数字_x偏移)
        数字y偏移 = int(_缩略图_序号数字_y偏移)

        显示格式 = str(_序号显示格式_缩略图)

    背景缩放 = max(0.05, min(5.0, 背景缩放))
    数字缩放 = max(0.05, min(5.0, 数字缩放))

    # =========================
    # 1) 背景（标签纸）缩放
    # =========================
    if 是否大图:
        基准高占比 = 0.16
    else:
        基准高占比 = 0.30

    基准高 = max(8, int(锚点矩形.h * 基准高占比))
    标签高 = max(8, int(基准高 * 背景缩放))

    标签纸图 = _按高等比缩放(标签纸原图, 标签高)
    if 标签纸图 is None:
        return

    标签w, 标签h = 标签纸图.get_size()

    # =========================
    # 2) 背景定位
    # =========================
    if 是否大图:
        基础偏移x = -int(标签w * 0.18)
        基础偏移y = -int(标签h * 0.12)
        标签x = 锚点矩形.left + 基础偏移x + 背景x偏移
        标签y = 锚点矩形.top + 基础偏移y + 背景y偏移
    else:
        标签x = int(锚点矩形.left - 标签w / 2) + 背景x偏移
        标签y = int(锚点矩形.top) + 背景y偏移

    屏幕.blit(标签纸图, (标签x, 标签y))

    # =========================
    # 3) 序号内容（✅ 不截断）
    # =========================
    显示值 = int(内部序号从0) + 1
    try:
        显示串 = str(显示格式.format(显示值))
    except Exception:
        显示串 = str(显示值)

    # 只保留数字（防御：万一 format 里带空格/其它符号）
    显示串 = "".join([ch for ch in 显示串 if ch.isdigit()])
    if not 显示串:
        return

    # =========================
    # 4) 数字缩放（先按标签高给一个基准）
    # =========================
    if 是否大图:
        数字基准高 = max(8, int(标签h / 3))
    else:
        数字基准高 = max(6, int(标签h / 6))

    初始数字高 = max(5, int(数字基准高 * 数字缩放))

    def _生成数字图列表(数字高: int):
        数字图列表_: List[pygame.Surface] = []
        for ch in 显示串:
            数字路径 = os.path.join(数字目录, f"{ch}.png")
            原 = 获取UI原图(数字路径, 透明=True)
            if 原 is None:
                return None
            缩 = _按高等比缩放(原, max(1, int(数字高)))
            if 缩 is None:
                return None
            数字图列表_.append(缩)
        return 数字图列表_

    # ✅ 自动缩小直到“宽度能塞进标签纸”
    数字高 = int(初始数字高)
    数字图列表 = _生成数字图列表(数字高)
    if not 数字图列表:
        return

    for _ in range(16):
        间距 = max(1, int(数字高 * 0.10))
        总宽 = (
            sum([d.get_width() for d in 数字图列表])
            + max(0, len(数字图列表) - 1) * 间距
        )

        # 可用宽：缩略图右下对齐要留边；大图居中也别贴边
        可用宽 = int(标签w * 0.86)
        if 总宽 <= 可用宽:
            break

        新数字高 = max(3, int(数字高 * 0.92))
        if 新数字高 == 数字高:
            break
        数字高 = 新数字高
        数字图列表 = _生成数字图列表(数字高)
        if not 数字图列表:
            return

    间距 = max(1, int(数字高 * 0.10))
    总宽 = sum([d.get_width() for d in 数字图列表]) + max(0, len(数字图列表) - 1) * 间距

    # =========================
    # 5) 数字定位
    # =========================
    if 是否大图:
        起始x = 标签x + (标签w - 总宽) // 2 + 数字x偏移
        起始y = 标签y + (标签h - 数字高) // 2 + 数字y偏移
    else:
        右内边距 = max(2, int(标签w * float(_缩略图_序号数字_右内边距占比)))
        下内边距 = max(2, int(标签h * float(_缩略图_序号数字_下内边距占比)))

        起始x = 标签x + 标签w - 右内边距 - 总宽 + 数字x偏移
        起始y = 标签y + 标签h - 下内边距 - 数字高 + 数字y偏移

        起始x = max(标签x, 起始x)
        起始y = max(标签y, 起始y)

    x = int(起始x)
    y = int(起始y)
    for i, 图 in enumerate(数字图列表):
        屏幕.blit(图, (x, y))
        x += 图.get_width()
        if i != len(数字图列表) - 1:
            x += 间距


def 绘制星星行_图片(
    屏幕: pygame.Surface,
    区域: pygame.Rect,
    星数: int,
    星星路径: str,
    星星缩放倍数: float,
    每行最大: int = 10,
    动态光效路径: Optional[str] = None,
    光效周期秒: float = 2.0,
    基准高占比: float = 1.0,
    行间距占比: float = 0.35,
):
    """
    ✅ 规则改为：
    - 星数 <= 每行最大：单排居中
    - 星数 > 每行最大：下排固定放 每行最大(默认10)，超出的全部放上排
      （上排可能 >10，会自动缩小以塞进区域）
    """
    星数 = max(0, int(星数))
    if 星数 <= 0:
        return

    星原图 = 获取UI原图(星星路径, 透明=True)
    if 星原图 is None:
        return

    try:
        基准高占比 = float(基准高占比)
    except Exception:
        基准高占比 = 1.0
    基准高占比 = max(0.05, min(2.0, 基准高占比))

    try:
        行间距占比 = float(行间距占比)
    except Exception:
        行间距占比 = 0.35
    行间距占比 = max(0.0, min(2.0, 行间距占比))

    def _按目标高生成星图(目标高_: int) -> Optional[pygame.Surface]:
        return _按高等比缩放(星原图, max(1, int(目标高_)))

    # ---------- 初算星星尺寸 ----------
    基准高 = max(6, int(区域.h * 基准高占比))
    目标高 = max(6, int(基准高 * float(星星缩放倍数)))

    星图 = _按目标高生成星图(目标高)
    if 星图 is None:
        return

    # ---------- 行分配：下10，上剩余 ----------
    if 星数 <= 每行最大:
        上排数 = 星数
        下排数 = 0
        行数 = 1
    else:
        下排数 = int(每行最大)
        上排数 = int(星数 - 每行最大)
        行数 = 2

    # ---------- 自动缩小：同时满足“高度”和“最大行宽” ----------
    for _ in range(18):
        星w, 星h = 星图.get_size()
        间距 = max(1, int(星w * 0.10))
        行距 = max(0, int(星h * 行间距占比))

        上排宽 = (上排数 * 星w + max(0, 上排数 - 1) * 间距) if 上排数 > 0 else 0
        下排宽 = (下排数 * 星w + max(0, 下排数 - 1) * 间距) if 下排数 > 0 else 0
        最大行宽 = max(上排宽, 下排宽, 1)

        总高 = 星h if 行数 == 1 else (星h * 2 + 行距)

        if (总高 <= 区域.h) and (最大行宽 <= 区域.w):
            break

        # 缩小一档
        新目标高 = max(3, int(星h * 0.92))
        星图2 = _按目标高生成星图(新目标高)
        if 星图2 is None:
            break
        星图 = 星图2

    星w, 星h = 星图.get_size()
    间距 = max(1, int(星w * 0.10))
    行距 = max(0, int(星h * 行间距占比))
    总高 = 星h if 行数 == 1 else (星h * 2 + 行距)

    起始y = 区域.y + (区域.h - 总高) // 2

    def _绘制一行(数量: int, y: int):
        if 数量 <= 0:
            return pygame.Rect(区域.centerx, y, 1, 星h)
        总宽 = 数量 * 星w + (数量 - 1) * 间距
        x0 = 区域.centerx - 总宽 // 2
        for i in range(数量):
            屏幕.blit(星图, (x0 + i * (星w + 间距), y))
        return pygame.Rect(x0, y, 总宽, 星h)

    if 行数 == 1:
        行矩形 = _绘制一行(上排数, 起始y)
        # 单排：动态光效扫这一排
        光效行矩形 = 行矩形
    else:
        # ✅ 上排先画（超出的）
        上排y = 起始y
        上排矩形 = _绘制一行(上排数, 上排y)

        # ✅ 下排固定10颗
        下排y = 上排y + 星h + 行距
        下排矩形 = _绘制一行(下排数, 下排y)

        # 动态光效默认扫“下排”（更符合你说的“10颗在下”视觉中心）
        光效行矩形 = 下排矩形 if 下排数 > 0 else 上排矩形

    # ---------- 动态光效 ----------
    if 动态光效路径 and os.path.isfile(动态光效路径) and 光效行矩形.w > 2:
        光原图 = 获取UI原图(动态光效路径, 透明=True)
        if 光原图 is None:
            return

        光高 = max(1, int(星h * 1.10))
        光图 = _按高等比缩放(光原图, 光高)
        if 光图 is None:
            return

        now = time.time()
        t = (now % float(光效周期秒)) / float(光效周期秒)

        扫描宽 = max(1, int(光效行矩形.w * 0.55))
        光图 = pygame.transform.smoothscale(光图, (扫描宽, 光高)).convert_alpha()

        x0 = 光效行矩形.left - 扫描宽
        x1 = 光效行矩形.right
        光x = int(x0 + (x1 - x0) * t)
        光y = 光效行矩形.y + int((星h - 光高) * 0.50)

        屏幕.blit(光图, (光x, 光y), special_flags=pygame.BLEND_RGBA_ADD)


# ===== 字体缓存（新增：放在 获取字体 函数上方也行）=====
_字体对象缓存: Dict[Tuple[str, int, bool], pygame.font.Font] = {}
_字体默认路径缓存: Dict[bool, str] = {}  # key: 是否粗体 -> 路径（空串表示用默认字体）


def 获取字体(字号: int, 是否粗体: bool = False) -> pygame.font.Font:
    # ✅ 只初始化一次
    try:
        if not pygame.font.get_init():
            pygame.font.init()
    except Exception:
        try:
            pygame.font.init()
        except Exception:
            pass

    try:
        字号 = int(字号)
    except Exception:
        字号 = 18
    字号 = max(6, min(256, 字号))

    是否粗体 = bool(是否粗体)

    # ✅ 只探测一次可用字体路径
    if 是否粗体 not in _字体默认路径缓存:
        普通候选 = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\arial.ttf",
        ]
        粗体候选 = [
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]

        for 标记, 候选 in [(False, 普通候选), (True, 粗体候选)]:
            路径 = ""
            for 字体路径 in 候选:
                try:
                    if os.path.isfile(字体路径):
                        路径 = 字体路径
                        break
                except Exception:
                    continue
            _字体默认路径缓存[标记] = 路径

    字体路径 = _字体默认路径缓存.get(是否粗体, "")

    缓存键 = (字体路径, 字号, 是否粗体)
    if 缓存键 in _字体对象缓存:
        return _字体对象缓存[缓存键]

    try:
        if 字体路径:
            字体 = pygame.font.Font(字体路径, 字号)
        else:
            字体 = pygame.font.Font(None, 字号)
    except Exception:
        字体 = pygame.font.Font(None, 字号)

    _字体对象缓存[缓存键] = 字体
    return 字体


def 绘制圆角矩形(
    屏幕: pygame.Surface, 矩形: pygame.Rect, 颜色, 圆角: int, 线宽: int = 0
):
    pygame.draw.rect(屏幕, 颜色, 矩形, width=线宽, border_radius=圆角)


def 绘制超粗文本(
    屏幕: pygame.Surface,
    文本: str,
    字体: pygame.font.Font,
    颜色,
    位置: tuple,
    对齐: str = "topleft",
    粗细: int = 3,
):
    """
    用多次偏移叠加实现“很粗”的字，不依赖字体文件是否有 bold。
    粗细建议 2~5，太大可能发糊。
    """
    文本面 = 字体.render(文本, True, 颜色)
    文本矩形 = 文本面.get_rect()
    setattr(文本矩形, 对齐, 位置)

    # 叠加偏移：越多越粗
    for dx in range(-粗细, 粗细 + 1):
        for dy in range(-粗细, 粗细 + 1):
            if dx == 0 and dy == 0:
                continue
            屏幕.blit(文本面, (文本矩形.x + dx, 文本矩形.y + dy))

    # 最后绘制一次正位，保证清晰
    屏幕.blit(文本面, 文本矩形)
    return 文本矩形


def 绘制文本(
    屏幕: pygame.Surface,
    文本: str,
    字体: pygame.font.Font,
    颜色,
    位置: tuple,
    对齐: str = "topleft",
):
    文本面 = 字体.render(文本, True, 颜色)
    文本矩形 = 文本面.get_rect()
    setattr(文本矩形, 对齐, 位置)
    屏幕.blit(文本面, 文本矩形)
    return 文本矩形


def 渲染紧凑文本(
    文本: str,
    字体: pygame.font.Font,
    颜色,
    字符间距: int = 0,
) -> pygame.Surface:
    字符面列表: List[pygame.Surface] = []
    总宽 = 0
    最大高 = 0
    间距 = int(字符间距)

    for 字符 in str(文本 or ""):
        字符面 = 字体.render(str(字符), True, 颜色).convert_alpha()
        字符面列表.append(字符面)
        总宽 += int(字符面.get_width())
        最大高 = max(最大高, int(字符面.get_height()))

    if not 字符面列表:
        return pygame.Surface((1, 1), pygame.SRCALPHA)

    总宽 += 间距 * max(0, len(字符面列表) - 1)
    总宽 = max(1, int(总宽))
    最大高 = max(1, int(最大高))
    画布 = pygame.Surface((总宽, 最大高), pygame.SRCALPHA)

    当前x = 0
    for idx, 字符面 in enumerate(字符面列表):
        当前y = 最大高 - int(字符面.get_height())
        画布.blit(字符面, (当前x, 当前y))
        当前x += int(字符面.get_width())
        if idx < len(字符面列表) - 1:
            当前x += 间距

    return 画布


def 安全读取文本(文件路径: str) -> str:
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(文件路径, "r", encoding=编码, errors="strict") as f:
                return f.read()
        except Exception:
            continue
    with open(文件路径, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def 解析显示BPM(sm文本: str) -> Optional[int]:
    匹配 = re.search(r"#DISPLAYBPM\s*:\s*([^;]+)\s*;", sm文本, flags=re.IGNORECASE)
    if not 匹配:
        return None
    原始 = 匹配.group(1).strip()
    数字匹配 = re.search(r"(\d+)", 原始)
    if not 数字匹配:
        return None
    try:
        return int(数字匹配.group(1))
    except Exception:
        return None


def 解析SM标题(sm文本: str) -> str:
    匹配 = re.search(r"#TITLE\s*:\s*([^;]+)\s*;", sm文本, flags=re.IGNORECASE)
    if not 匹配:
        return ""
    return str(匹配.group(1) or "").strip()


def 从文件夹名解析歌名星级(文件夹名: str) -> Tuple[str, int]:
    """
    严格按末尾 #数字 解析星级：#几 就画几颗星
    ✅ 规则：星级范围钳制到 1~20（你要求最大 20 星）
    示例：FANCY_CLUB#1+1=0_1706#4  => 星级=4，歌名=1+1=0_1706
    """
    星级 = 3
    末尾星级匹配 = re.search(r"#\s*(\d+)\s*$", 文件夹名)
    if 末尾星级匹配:
        try:
            星级 = int(末尾星级匹配.group(1))
        except Exception:
            星级 = 3
    else:
        前缀星级匹配 = re.match(r"^\(\s*(\d+)\s*\)\s*", 文件夹名)
        if 前缀星级匹配:
            try:
                星级 = int(前缀星级匹配.group(1))
            except Exception:
                星级 = 3

    parts = 文件夹名.split("#")
    if len(parts) >= 2:
        if 末尾星级匹配:
            中间 = "#".join(parts[1:-1]) if len(parts) > 2 else parts[1]
        else:
            中间 = "#".join(parts[1:])
    else:
        中间 = 文件夹名

    中间 = 中间.strip()
    中间 = re.sub(r"^\(\s*\d+\s*\)\s*", "", 中间)
    中间 = re.sub(r"^\d+\s*", "", 中间)
    中间 = re.sub(r"^[\-_ ]+", "", 中间)
    歌名 = 中间 if 中间 else 文件夹名

    # ✅ 星级钳制 1~20
    try:
        星级 = int(星级)
    except Exception:
        星级 = 3
    星级 = max(1, min(20, 星级))

    return 歌名, 星级


def 解析歌曲元数据(sm路径: str, 类型名: str, 模式名: str) -> Optional["歌曲信息"]:
    if (not sm路径) or (not os.path.isfile(sm路径)):
        return None

    歌曲路径 = os.path.dirname(sm路径)
    歌曲文件夹 = os.path.basename(歌曲路径)
    if str(歌曲文件夹 or "").strip().lower() in {"backup", "backups"}:
        return None
    sm文本 = 安全读取文本(sm路径)

    音频路径 = 找文件(歌曲路径, (".ogg", ".mp3", ".wav"))
    封面路径 = 找封面(歌曲路径)
    bpm = 解析显示BPM(sm文本)
    歌名, 星级 = 从文件夹名解析歌名星级(歌曲文件夹)

    if "#" not in str(歌曲文件夹 or ""):
        sm标题 = 解析SM标题(sm文本)
        if sm标题:
            歌名 = sm标题

    return 歌曲信息(
        序号=0,
        类型=str(类型名 or ""),
        模式=str(模式名 or ""),
        歌曲文件夹=歌曲文件夹,
        歌曲路径=歌曲路径,
        sm路径=sm路径,
        mp3路径=音频路径,
        封面路径=封面路径,
        歌名=歌名,
        星级=max(1, int(星级 or 1)),
        bpm=bpm,
        是否VIP=bool(int(星级 or 0) >= 5),
        游玩次数=0,
    )


def 找文件(目录: str, 扩展名集合: Tuple[str, ...]) -> Optional[str]:
    if not os.path.isdir(目录):
        return None
    for 文件名 in os.listdir(目录):
        低 = 文件名.lower()
        if any(低.endswith(ext) for ext in 扩展名集合):
            return os.path.join(目录, 文件名)
    return None


def 找封面(歌曲路径: str) -> Optional[str]:
    """
    优先 bann.*，找不到再退回任意 jpg/png/webp
    """
    if not os.path.isdir(歌曲路径):
        return None
    for 文件名 in os.listdir(歌曲路径):
        低 = 文件名.lower()
        if 低.startswith("bann.") and (
            低.endswith(".jpg")
            or 低.endswith(".jpeg")
            or 低.endswith(".png")
            or 低.endswith(".webp")
        ):
            return os.path.join(歌曲路径, 文件名)
    return 找文件(歌曲路径, (".jpg", ".jpeg", ".png", ".webp"))


def 扫描songs目录(songs根目录: str) -> Dict[str, Dict[str, List[歌曲信息]]]:
    结果: Dict[str, Dict[str, List[歌曲信息]]] = {}
    if not os.path.isdir(songs根目录):
        return 结果

    临时收集: Dict[Tuple[str, str], List[歌曲信息]] = {}

    for 根, 目录列表, 文件列表 in os.walk(songs根目录):
        for 文件名 in 文件列表:
            if not 文件名.lower().endswith(".sm"):
                continue

            sm路径 = os.path.join(根, 文件名)
            相对 = os.path.relpath(sm路径, songs根目录)
            parts = 相对.split(os.sep)
            if len(parts) < 4:
                continue

            类型名 = parts[0]
            模式名 = parts[1]
            歌 = 解析歌曲元数据(sm路径, 类型名, 模式名)
            if 歌 is None:
                continue

            键 = (类型名, 模式名)
            if 键 not in 临时收集:
                临时收集[键] = []

            临时收集[键].append(歌)

    def _排序键(歌: 歌曲信息):
        try:
            星 = int(getattr(歌, "星级", 0) or 0)
        except Exception:
            星 = 0
        名 = str(getattr(歌, "歌名", "") or "").strip().lower()
        夹 = str(getattr(歌, "歌曲文件夹", "") or "").strip().lower()
        smn = (
            str(os.path.basename(str(getattr(歌, "sm路径", "") or ""))).strip().lower()
        )
        return (星, 名, 夹, smn)

    for (类型名, 模式名), 列表 in 临时收集.items():
        # ✅ 你要求：默认按星级从少到多
        列表.sort(key=_排序键)

        # ✅ 内部序号从 0 开始（与显示顺序一致）
        for i, 歌 in enumerate(列表, start=0):
            歌.序号 = i

        if 类型名 not in 结果:
            结果[类型名] = {}
        结果[类型名][模式名] = 列表

    return 结果


def 扫描songs_指定路径(
    songs根目录: str, 类型名: str, 模式名: str
) -> Dict[str, Dict[str, List[歌曲信息]]]:
    结果: Dict[str, Dict[str, List[歌曲信息]]] = {}

    if not os.path.isdir(songs根目录):
        return 结果

    def _归一(s: str) -> str:
        return re.sub(r"\s+", "", str(s or "")).strip().lower()

    目标类型 = 类型名.strip()
    目标模式 = 模式名.strip()

    类型目录 = os.path.join(songs根目录, 目标类型)
    if not os.path.isdir(类型目录):
        try:
            for 名 in os.listdir(songs根目录):
                if os.path.isdir(os.path.join(songs根目录, 名)) and _归一(名) == _归一(
                    目标类型
                ):
                    目标类型 = 名
                    类型目录 = os.path.join(songs根目录, 目标类型)
                    break
        except Exception:
            return 结果

    if not os.path.isdir(类型目录):
        return 结果

    模式目录 = os.path.join(类型目录, 目标模式)
    if not os.path.isdir(模式目录):
        try:
            for 名 in os.listdir(类型目录):
                if os.path.isdir(os.path.join(类型目录, 名)) and _归一(名) == _归一(
                    目标模式
                ):
                    目标模式 = 名
                    模式目录 = os.path.join(类型目录, 目标模式)
                    break
        except Exception:
            return 结果

    if not os.path.isdir(模式目录):
        return 结果

    收集: List[歌曲信息] = []

    for 根, 目录列表, 文件列表 in os.walk(模式目录):
        for 文件名 in 文件列表:
            if not 文件名.lower().endswith(".sm"):
                continue

            sm路径 = os.path.join(根, 文件名)
            try:
                相对 = os.path.relpath(sm路径, songs根目录)
                parts = 相对.split(os.sep)
            except Exception:
                continue

            if len(parts) < 4:
                continue

            类型名_实际 = parts[0]
            模式名_实际 = parts[1]
            歌 = 解析歌曲元数据(sm路径, 类型名_实际, 模式名_实际)
            if 歌 is not None:
                收集.append(歌)

    def _排序键(歌: 歌曲信息):
        try:
            星 = int(getattr(歌, "星级", 0) or 0)
        except Exception:
            星 = 0
        名 = str(getattr(歌, "歌名", "") or "").strip().lower()
        夹 = str(getattr(歌, "歌曲文件夹", "") or "").strip().lower()
        smn = (
            str(os.path.basename(str(getattr(歌, "sm路径", "") or ""))).strip().lower()
        )
        return (星, 名, 夹, smn)

    收集.sort(key=_排序键)
    for i, 歌 in enumerate(收集, start=0):
        歌.序号 = i

    if 收集:
        结果[收集[0].类型] = {收集[0].模式: 收集}
    else:
        结果 = {}

    return 结果


# =========================
# 图像：圆角蒙版裁切 + 缓存
# =========================


class 图像缓存:
    def __init__(self):
        self._缓存: Dict[Tuple[str, int, int, int, str], pygame.Surface] = {}

    def 获取(
        self, 路径: str, 目标宽: int, 目标高: int, 圆角: int, 模式: str
    ) -> Optional[pygame.Surface]:
        return self._缓存.get((路径, 目标宽, 目标高, 圆角, 模式))

    def 写入(
        self,
        路径: str,
        目标宽: int,
        目标高: int,
        圆角: int,
        模式: str,
        图: pygame.Surface,
    ):
        self._缓存[(路径, 目标宽, 目标高, 圆角, 模式)] = 图

    def 清理远端(self, 保留key集合: Set[Tuple[str, int, int, int, str]]):
        删除键 = [k for k in list(self._缓存.keys()) if k not in 保留key集合]
        for k in 删除键:
            try:
                del self._缓存[k]
            except Exception:
                pass


def 生成圆角蒙版(宽: int, 高: int, 圆角: int) -> pygame.Surface:
    蒙版 = pygame.Surface((宽, 高), pygame.SRCALPHA)
    蒙版.fill((0, 0, 0, 0))
    pygame.draw.rect(
        蒙版, (255, 255, 255, 255), pygame.Rect(0, 0, 宽, 高), border_radius=圆角
    )
    return 蒙版


def 载入并缩放封面(
    路径: str, 目标宽: int, 目标高: int, 圆角: int, 模式: str
) -> Optional[pygame.Surface]:
    """
    模式:
      - cover   : 填满，可能裁切（缩略图用）

      - contain : 完整展示，不裁切（大图用）
    """
    try:
        原图 = pygame.image.load(路径).convert_alpha()
    except Exception:
        return None

    ow, oh = 原图.get_size()
    if ow <= 0 or oh <= 0:
        return None

    if 模式 == "contain":
        比例 = min(目标宽 / ow, 目标高 / oh)
        新宽 = max(1, int(ow * 比例))
        新高 = max(1, int(oh * 比例))
        缩放 = pygame.transform.smoothscale(原图, (新宽, 新高))

        画布 = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
        画布.fill((0, 0, 0, 0))
        x = (目标宽 - 新宽) // 2
        y = (目标高 - 新高) // 2
        画布.blit(缩放, (x, y))

        蒙版 = 生成圆角蒙版(目标宽, 目标高, 圆角)
        画布.blit(蒙版, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return 画布

    # cover
    比例 = max(目标宽 / ow, 目标高 / oh)
    新宽 = max(1, int(ow * 比例))
    新高 = max(1, int(oh * 比例))
    缩放 = pygame.transform.smoothscale(原图, (新宽, 新高))

    x = (新宽 - 目标宽) // 2
    y = (新高 - 目标高) // 2
    裁切 = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
    裁切.blit(缩放, (0, 0), area=pygame.Rect(x, y, 目标宽, 目标高))

    蒙版 = 生成圆角蒙版(目标宽, 目标高, 圆角)
    裁切.blit(蒙版, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return 裁切


class 渐隐放大点击特效:
    """
    0.5s 渐隐放大（alpha: 0->255），scale: 0.92 -> 1.06 -> 1.00
    兼容 _启动过渡() 的接口：
      - 触发()
      - 是否动画中()
      - 绘制按钮(屏幕, 原图, 基准矩形)
    """

    def __init__(self, 总时长: float = 0.5):
        self.总时长 = float(总时长)
        self._开始时间 = 0.0
        self._动画中 = False

    def 触发(self):
        self._开始时间 = time.time()
        self._动画中 = True

    def 是否动画中(self) -> bool:
        if not self._动画中:
            return False
        if (time.time() - self._开始时间) >= max(0.001, self.总时长):
            self._动画中 = False
            return False
        return True

    def _夹紧(self, x: float, a: float, b: float) -> float:
        return a if x < a else (b if x > b else x)

    def _缓出(self, t: float) -> float:
        # easeOutQuad
        t = self._夹紧(t, 0.0, 1.0)
        return 1.0 - (1.0 - t) * (1.0 - t)

    def 绘制按钮(
        self, 屏幕: pygame.Surface, 原图: pygame.Surface, 基准矩形: pygame.Rect
    ):
        if 原图 is None:
            return

        现在 = time.time()
        t = (现在 - self._开始时间) / max(0.001, self.总时长)
        t = self._夹紧(t, 0.0, 1.0)

        # scale：0.92 -> 1.06 -> 1.00
        if t < 0.6:
            k1 = t / 0.6
            scale = 0.92 + (1.06 - 0.92) * self._缓出(k1)
        else:
            k2 = (t - 0.6) / 0.4
            scale = 1.06 + (1.00 - 1.06) * self._缓出(k2)

        # alpha：0 -> 255
        alpha = int(255 * self._缓出(t))
        alpha = max(0, min(255, alpha))

        ww = max(1, int(基准矩形.w * scale))
        hh = max(1, int(基准矩形.h * scale))
        x = 基准矩形.centerx - ww // 2
        y = 基准矩形.centery - hh // 2

        try:
            图 = pygame.transform.smoothscale(原图, (ww, hh)).convert_alpha()
            图.set_alpha(alpha)
            屏幕.blit(图, (x, y))
        except Exception:
            # 兜底：不让异常打断主循环
            pass


# =========================
# UI 组件
# =========================
class 按钮:
    def __init__(self, 名称: str, 矩形: pygame.Rect):
        self.名称 = 名称
        self.矩形 = 矩形
        self.悬停 = False
        self.按下 = False

        # === 按钮背景图：统一皮肤 ===
        self._背景图_原图: Optional[pygame.Surface] = None
        self._背景图_缓存: Optional[pygame.Surface] = None
        self._背景图_缓存尺寸: Tuple[int, int] = (0, 0)

        self._加载按钮背景图()

    def _加载按钮背景图(self):
        """
        统一按钮背景：UI-img/选歌界面资源/默认按钮背景.png
        相对脚本目录加载，避免工作目录变化导致找不到资源。
        """
        try:
            脚本目录 = _取项目根目录()
            路径 = os.path.join(脚本目录, "UI-img", "选歌界面资源", "默认按钮背景.png")
            if os.path.isfile(路径):
                self._背景图_原图 = pygame.image.load(路径).convert_alpha()
            else:
                self._背景图_原图 = None
        except Exception:
            self._背景图_原图 = None

        self._背景图_缓存 = None
        self._背景图_缓存尺寸 = (0, 0)

    def _获取缩放背景图(self) -> Optional[pygame.Surface]:
        if self._背景图_原图 is None:
            return None

        目标尺寸 = (max(1, int(self.矩形.w)), max(1, int(self.矩形.h)))
        if self._背景图_缓存 is None or self._背景图_缓存尺寸 != 目标尺寸:
            try:
                self._背景图_缓存 = pygame.transform.smoothscale(
                    self._背景图_原图, 目标尺寸
                )
                self._背景图_缓存尺寸 = 目标尺寸
            except Exception:
                self._背景图_缓存 = None
                self._背景图_缓存尺寸 = (0, 0)

        return self._背景图_缓存

    def 处理事件(self, 事件) -> bool:
        if 事件.type == pygame.MOUSEMOTION:
            self.悬停 = self.矩形.collidepoint(事件.pos)

        elif 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            if self.矩形.collidepoint(事件.pos):
                self.按下 = True

        elif 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            命中 = self.矩形.collidepoint(事件.pos)
            触发 = self.按下 and 命中
            self.按下 = False
            return 触发

        return False

    def 绘制(self, 屏幕: pygame.Surface, 字体: pygame.font.Font):
        圆角 = 18  # 仅用于回退绘制（不画边框）

        # 1) 背景（图片优先，失败回退纯色）
        背景图 = self._获取缩放背景图()
        if 背景图 is not None:
            屏幕.blit(背景图, self.矩形.topleft)

            # 状态反馈（不画边框）：悬停/按下加透明叠层
            if self.悬停 or self.按下:
                叠层 = pygame.Surface((self.矩形.w, self.矩形.h), pygame.SRCALPHA)
                if self.按下:
                    叠层.fill((0, 0, 0, 85))
                else:
                    叠层.fill((255, 255, 255, 18))
                屏幕.blit(叠层, self.矩形.topleft)
        else:
            # 回退：纯色底（不画边框）
            背景色 = (55, 120, 210)
            if self.悬停:
                背景色 = (70, 140, 240)
            if self.按下:
                背景色 = (35, 95, 180)
            绘制圆角矩形(屏幕, self.矩形, 背景色, 圆角=圆角)

        # 2) 文本：字体保留，颜色强制白色
        绘制文本(
            屏幕,
            self.名称,
            字体,
            (255, 255, 255),
            self.矩形.center,
            对齐="center",
        )


class 星级筛选按钮:
    """
    ✅ 星级筛选专用按钮（新样式）：
    - 只显示：数字 + 单颗星图标
    - 圆角卡片
    - 点击：触发过渡后立即应用筛选并关闭面板
    """

    def __init__(self, 宿主: "选歌游戏", 星级: int, 矩形: pygame.Rect):
        self.宿主 = 宿主
        self.星级 = int(星级)
        self.矩形 = 矩形

        self.悬停 = False
        self.按下 = False

    def 处理事件(self, 事件) -> bool:
        if 事件.type == pygame.MOUSEMOTION:
            self.悬停 = self.矩形.collidepoint(事件.pos)
            return False

        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            if self.矩形.collidepoint(事件.pos):
                self.按下 = True
            return False

        if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            命中 = self.矩形.collidepoint(事件.pos)
            触发 = bool(self.按下 and 命中)
            self.按下 = False
            if 触发:
                self._触发选择()
            return False

        return False

    def _触发选择(self):
        if self.宿主 is None:
            return

        # 1) 先对“当前屏幕上的按钮区域截图”做 0.5s 渐隐放大
        try:
            特效 = getattr(self.宿主, "_特效_星级筛选", None)
            if 特效 is None:
                特效 = getattr(self.宿主, "_特效_按钮", None)
            self.宿主._启动过渡(特效, self.矩形, lambda: None)
        except Exception:
            pass

        # 2) 立刻应用筛选并关闭面板
        try:
            self.宿主.设置星级筛选(self.星级)
            self.宿主.关闭星级筛选页()
        except Exception:
            pass

    def _获取单星图(self, 目标高: int) -> Optional[pygame.Surface]:
        目标高 = max(8, int(目标高))
        try:
            缓存 = getattr(self.宿主, "_星级筛选_单星缓存", None)
            if not isinstance(缓存, dict):
                缓存 = {}
                setattr(self.宿主, "_星级筛选_单星缓存", 缓存)
        except Exception:
            缓存 = {}

        if 目标高 in 缓存:
            return 缓存.get(目标高)

        星星路径 = _资源路径("UI-img", "选歌界面资源", "小星星", "小星星.png")
        星原图 = 获取UI原图(星星路径, 透明=True)
        if 星原图 is None:
            缓存[目标高] = None
            return None

        星图 = _按高等比缩放(星原图, 目标高)
        缓存[目标高] = 星图
        return 星图

    def 绘制(self, 屏幕: pygame.Surface, _字体: pygame.font.Font):
        r = self.矩形

        # 背景（圆角）
        圆角 = max(14, int(min(r.w, r.h) * 0.18))
        if self.按下:
            背景色 = (10, 18, 30, 230)
        elif self.悬停:
            背景色 = (25, 45, 75, 235)
        else:
            背景色 = (18, 32, 55, 225)

        底 = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        底.fill((0, 0, 0, 0))
        pygame.draw.rect(底, 背景色, pygame.Rect(0, 0, r.w, r.h), border_radius=圆角)

        # 细边框（更像菜单按钮）
        边框色 = (180, 220, 255, 160) if not self.按下 else (255, 220, 120, 200)
        pygame.draw.rect(
            底, 边框色, pygame.Rect(0, 0, r.w, r.h), width=2, border_radius=圆角
        )

        屏幕.blit(底, r.topleft)

        # 内容：数字 + 单星（整体居中）
        数字字号 = max(24, int(r.h * 0.52))
        数字字体 = 获取字体(数字字号, 是否粗体=True)

        数字串 = str(self.星级)
        数字白 = 数字字体.render(数字串, True, (255, 255, 255))
        数字黑 = 数字字体.render(数字串, True, (0, 0, 0))

        星高 = max(12, int(r.h * 0.26))
        星图 = self._获取单星图(星高)

        间距 = max(6, int(r.w * 0.04))
        组宽 = 数字白.get_width()

        if 星图 is not None:
            组宽 = 组宽 + 间距 + 星图.get_width()

        起点x = r.centerx - 组宽 // 2
        中心y = r.centery

        # 数字（带阴影）
        数字r = 数字白.get_rect()
        数字r.midleft = (起点x, 中心y)
        屏幕.blit(数字黑, (数字r.x + 2, 数字r.y + 2))
        屏幕.blit(数字白, 数字r.topleft)

        # 星
        if 星图 is not None:
            星r = 星图.get_rect()
            星r.midleft = (数字r.right + 间距, 中心y)
            屏幕.blit(星图, 星r.topleft)
        else:
            # 兜底：没星图就画一个小五角星（非常简化）
            try:
                cx = 数字r.right + 间距 + int(星高 * 0.6)
                cy = 中心y
                半径 = int(星高 * 0.55)
                点 = []
                for i in range(10):
                    角 = math.pi / 2 + i * math.pi / 5
                    rr2 = 半径 if i % 2 == 0 else int(半径 * 0.45)
                    点.append(
                        (cx + int(math.cos(角) * rr2), cy - int(math.sin(角) * rr2))
                    )
                pygame.draw.polygon(屏幕, (255, 210, 80), 点)
            except Exception:
                pass


class 图片按钮:
    def __init__(
        self,
        图片路径: str,
        矩形: pygame.Rect,
        是否水平翻转: bool = False,
        是否垂直翻转: bool = False,
    ):
        self.图片路径 = str(图片路径 or "")
        self.矩形 = 矩形
        self.是否水平翻转 = bool(是否水平翻转)
        self.是否垂直翻转 = bool(是否垂直翻转)

        self.悬停 = False
        self.按下 = False

        self._原图: Optional[pygame.Surface] = None
        self._缓存图: Optional[pygame.Surface] = None
        # ✅ 缓存键包含翻转状态
        self._缓存键: Tuple[int, int, bool, bool] = (0, 0, False, False)

        self._加载原图()

    def _加载原图(self):
        try:
            图 = 安全加载图片(self.图片路径, 透明=True)
            self._原图 = 图
        except Exception:
            self._原图 = None

        self._缓存图 = None
        self._缓存键 = (0, 0, False, False)

    def _获取缩放图(self) -> Optional[pygame.Surface]:
        if self._原图 is None:
            return None

        目标宽 = max(1, int(self.矩形.w))
        目标高 = max(1, int(self.矩形.h))
        键 = (目标宽, 目标高, bool(self.是否水平翻转), bool(self.是否垂直翻转))

        if self._缓存图 is not None and self._缓存键 == 键:
            return self._缓存图

        try:
            图 = self._原图
            # ✅ 先翻转（基于原图），再缩放（更清晰，方向也不会错）
            if self.是否水平翻转 or self.是否垂直翻转:
                图 = pygame.transform.flip(图, self.是否水平翻转, self.是否垂直翻转)

            缩放图 = pygame.transform.smoothscale(图, (目标宽, 目标高)).convert_alpha()
        except Exception:
            缩放图 = None

        self._缓存图 = 缩放图
        self._缓存键 = 键
        return 缩放图

    def 处理事件(self, 事件) -> bool:
        if 事件.type == pygame.MOUSEMOTION:
            self.悬停 = self.矩形.collidepoint(事件.pos)

        elif 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            if self.矩形.collidepoint(事件.pos):
                self.按下 = True

        elif 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            命中 = self.矩形.collidepoint(事件.pos)
            触发 = self.按下 and 命中
            self.按下 = False
            return 触发

        return False

    def 绘制(self, 屏幕: pygame.Surface, *_忽略参数, **_忽略关键字):
        图 = self._获取缩放图()
        if 图 is not None:
            屏幕.blit(图, self.矩形.topleft)
        else:
            pygame.draw.rect(屏幕, (40, 80, 160), self.矩形, border_radius=14)

        if self.悬停 or self.按下:
            叠层 = pygame.Surface((self.矩形.w, self.矩形.h), pygame.SRCALPHA)
            叠层.fill((0, 0, 0, 85) if self.按下 else (255, 255, 255, 18))
            屏幕.blit(叠层, self.矩形.topleft)


class 底部图文按钮:
    def __init__(
        self,
        图片路径: str,
        矩形: pygame.Rect,
        底部文字: str,
        是否处理透明像素: bool = False,
    ):
        self.图片路径 = str(图片路径 or "")
        self.矩形 = 矩形
        self.底部文字 = str(底部文字 or "")
        self.是否处理透明像素 = bool(是否处理透明像素)

        # ✅ 新增：文字y偏移（负数=往上覆盖到图标上）
        self.文字y偏移 = 0

        self.悬停 = False
        self.按下 = False

        self._原图: Optional[pygame.Surface] = None
        self._缓存图: Optional[pygame.Surface] = None
        self._缓存尺寸: Tuple[int, int] = (0, 0)

        self._加载原图()

    def _加载原图(self):
        try:
            图 = 安全加载图片(self.图片路径, 透明=True)
            if 图 is None:
                self._原图 = None
                return

            # ✅ 你现在要求：不要去除透明像素
            # 这里保留能力，但只在你显式传 True 时才做（默认你会改成 False）
            if self.是否处理透明像素:
                图 = 处理透明像素_用左上角作为背景(图)

            self._原图 = 图
        except Exception:
            self._原图 = None

        self._缓存图 = None
        self._缓存尺寸 = (0, 0)

    def _获取缩放图_按区域contain(
        self, 区域w: int, 区域h: int, 放大倍率: float = 1.0
    ) -> Optional[pygame.Surface]:
        if self._原图 is None:
            return None

        区域w = max(1, int(区域w))
        区域h = max(1, int(区域h))

        try:
            放大倍率 = float(放大倍率)
        except Exception:
            放大倍率 = 1.0
        放大倍率 = max(0.50, min(2.00, 放大倍率))

        缓存键 = (区域w, 区域h, int(放大倍率 * 1000))
        if self._缓存图 is not None and self._缓存尺寸 == 缓存键:
            return self._缓存图

        try:
            ow, oh = self._原图.get_size()
            if ow <= 0 or oh <= 0:
                self._缓存图 = None
                self._缓存尺寸 = 缓存键
                return None

            # 先按 contain 放进区域
            比例 = min(区域w / ow, 区域h / oh)
            nw = max(1, int(ow * 比例))
            nh = max(1, int(oh * 比例))

            # 再“可控放大”，但绝不超过区域
            可再放大 = min(区域w / max(1, nw), 区域h / max(1, nh))
            最终放大 = min(放大倍率, 可再放大)
            nw2 = max(1, int(nw * 最终放大))
            nh2 = max(1, int(nh * 最终放大))

            缩放图 = pygame.transform.smoothscale(
                self._原图, (nw2, nh2)
            ).convert_alpha()
        except Exception:
            缩放图 = None

        self._缓存图 = 缩放图
        self._缓存尺寸 = 缓存键
        return 缩放图

    def 处理事件(self, 事件) -> bool:
        if 事件.type == pygame.MOUSEMOTION:
            self.悬停 = self.矩形.collidepoint(事件.pos)

        elif 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            if self.矩形.collidepoint(事件.pos):
                self.按下 = True

        elif 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            命中 = self.矩形.collidepoint(事件.pos)
            触发 = self.按下 and 命中
            self.按下 = False
            return 触发

        return False

    def 绘制(self, 屏幕: pygame.Surface, 字体: pygame.font.Font):
        总矩形 = self.矩形

        # ✅ 图标区：永远用“宽度”做正方形
        图标边长 = max(1, int(总矩形.w))
        图标区 = pygame.Rect(总矩形.x, 总矩形.y, 总矩形.w, 图标边长)

        # 1) 画图标（尽量填满）
        try:
            图 = self._获取缩放图_按区域contain(图标区.w, 图标区.h, 放大倍率=1.22)
        except TypeError:
            图 = self._获取缩放图_按区域contain(图标区.w, 图标区.h)

        if 图 is not None:
            gx = 图标区.centerx - 图.get_width() // 2
            gy = 图标区.centery - 图.get_height() // 2
            屏幕.blit(图, (gx, gy))
        else:
            pygame.draw.rect(屏幕, (40, 80, 160), 图标区, border_radius=14)

        # 2) 交互反馈（先盖一层，再画字）
        if self.悬停 or self.按下:
            叠层 = pygame.Surface((图标区.w, 图标区.h), pygame.SRCALPHA)
            叠层.fill((0, 0, 0, 85) if self.按下 else (255, 255, 255, 18))
            屏幕.blit(叠层, 图标区.topleft)

        # 3) ✅ 文字：覆盖在图标底部中间，并允许“往上挪”
        if self.底部文字:
            文本 = str(self.底部文字)

            try:
                白字 = 字体.render(文本, True, (255, 255, 255))
                黑影 = 字体.render(文本, True, (0, 0, 0))

                文高 = 白字.get_height()

                # ✅ 默认：往上覆盖一点点（负数=往上）
                默认上移 = -max(2, int(文高 * 0.25))

                # ✅ 手动偏移：你想再往上/往下，直接改 self.文字y偏移
                try:
                    手动偏移 = int(getattr(self, "文字y偏移", 0))
                except Exception:
                    手动偏移 = 0

                文矩形 = 白字.get_rect()
                文矩形.midbottom = (
                    图标区.centerx,
                    图标区.bottom + 默认上移 + 手动偏移,
                )

                # 防御：别掉出屏幕底部（否则你又说看不到）
                屏高 = int(屏幕.get_height())
                if 文矩形.bottom > 屏高 - 2:
                    文矩形.bottom = 屏高 - 2

                # 阴影 + 正文
                屏幕.blit(黑影, (文矩形.x + 2, 文矩形.y + 2))
                屏幕.blit(白字, 文矩形.topleft)
            except Exception:
                pass


class 歌曲卡片:
    def __init__(self, 歌曲: 歌曲信息, 矩形: pygame.Rect):
        self.歌曲 = 歌曲
        self.矩形 = 矩形
        self.悬停 = False
        self.踏板高亮 = False
        self.封面矩形 = pygame.Rect(0, 0, 1, 1)

    def _计算封面矩形(self, 锚点矩形: pygame.Rect, 屏宽: int, 屏高: int) -> pygame.Rect:
        # ✅ 由 JSON 控制封面内边距/下移
        内边距占比 = 取选歌布局值("缩略图.封面.内边距占比", 0.01)
        try:
            内边距占比 = float(内边距占比)
        except Exception:
            内边距占比 = 0.01
        内边距占比 = max(0.0, min(0.20, 内边距占比))

        内边距最小 = 取选歌布局像素(
            "缩略图.封面.内边距最小", 8, 屏宽, 屏高, 最小=0, 最大=9999
        )
        内边距 = max(int(内边距最小), int(min(锚点矩形.w, 锚点矩形.h) * 内边距占比))

        封面 = 锚点矩形.inflate(-内边距 * 2, -内边距 * 2)

        下移像素 = 取选歌布局像素(
            "缩略图.封面.下移像素", 8, 屏宽, 屏高, 最小=-9999, 最大=9999
        )
        下移最大占比 = 取选歌布局值("缩略图.封面.下移最大占比", 0.35)
        try:
            下移最大占比 = float(下移最大占比)
        except Exception:
            下移最大占比 = 0.35
        下移最大占比 = max(0.0, min(0.90, 下移最大占比))

        最大下移 = max(0, int(封面.h * 下移最大占比))
        下移像素 = max(-最大下移, min(int(下移像素), 最大下移))

        封面.y += 下移像素
        if 下移像素 > 0:
            封面.h = max(1, 封面.h - 下移像素)
        return 封面

    def 更新布局(self, 矩形: pygame.Rect):
        self.矩形 = 矩形

    def 处理事件(self, 事件):
        if 事件.type == pygame.MOUSEMOTION:
            self.悬停 = self.矩形.collidepoint(事件.pos)

    def 是否点击(self, 事件) -> bool:
        return (
            事件.type == pygame.MOUSEBUTTONDOWN
            and 事件.button == 1
            and self.矩形.collidepoint(事件.pos)
        )

    def 绘制(self, 屏幕: pygame.Surface, 小字体: pygame.font.Font, 图缓存: "图像缓存"):
        屏宽, 屏高 = 屏幕.get_size()
        是否高亮 = bool(self.悬停 or self.踏板高亮)
        基准矩形 = self.矩形.copy()
        if 是否高亮:
            缩放 = 1.08 if bool(self.踏板高亮) else 1.04
            新宽 = max(1, int(self.矩形.w * 缩放))
            新高 = max(1, int(self.矩形.h * 缩放))
            基准矩形.size = (新宽, 新高)
            基准矩形.center = self.矩形.center

        # =========================
        # 1) 缩略图框（支持等比缩放模式）
        # =========================
        框路径 = _资源路径("UI-img", "选歌界面资源", "缩略图小.png")

        框宽缩放 = 取选歌布局值("缩略图.框.宽缩放", 0.97)
        框高缩放 = 取选歌布局值("缩略图.框.高缩放", 1.05)
        try:
            框宽缩放 = float(框宽缩放)
        except Exception:
            框宽缩放 = 0.97
        try:
            框高缩放 = float(框高缩放)
        except Exception:
            框高缩放 = 1.05
        框宽缩放 = max(0.20, min(3.0, 框宽缩放))
        框高缩放 = max(0.20, min(3.0, 框高缩放))

        框绘制宽 = max(1, int(基准矩形.w * 框宽缩放))
        框绘制高 = max(1, int(基准矩形.h * 框高缩放))

        框x偏移 = 取选歌布局像素(
            "缩略图.框.x偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
        )
        框y偏移 = 取选歌布局像素(
            "缩略图.框.y偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
        )

        框缩放模式 = (
            str(取选歌布局值("缩略图.框.缩放模式", "stretch") or "stretch")
            .strip()
            .lower()
        )
        框图 = 获取UI容器图(框路径, 框绘制宽, 框绘制高, 缩放模式=框缩放模式, 透明=True)

        框x = 基准矩形.x + int(框x偏移)
        框y = 基准矩形.y + int(框y偏移)

        边框锚点矩形 = (
            pygame.Rect(框x, 框y, 框绘制宽, 框绘制高) if 框图 is not None else 基准矩形
        )

        # =========================
        # 2) 封面矩形（基于锚点）
        # =========================
        self.封面矩形 = self._计算封面矩形(边框锚点矩形, 屏宽, 屏高)

        # =========================
        # 3) 封面等比缩放模式（contain/cover）
        # =========================
        封面缩放模式 = (
            str(取选歌布局值("缩略图.封面.缩放模式", "contain") or "contain")
            .strip()
            .lower()
        )
        if 封面缩放模式 not in ("contain", "cover"):
            封面缩放模式 = "contain"

        封面圆角 = 取选歌布局像素("缩略图.封面.圆角", 0, 屏宽, 屏高, 最小=0, 最大=200)

        封面图 = None
        if self.歌曲.封面路径:
            封面图 = 图缓存.获取(
                self.歌曲.封面路径,
                self.封面矩形.w,
                self.封面矩形.h,
                int(封面圆角),
                封面缩放模式,
            )
            if 封面图 is None:
                封面图 = 载入并缩放封面(
                    self.歌曲.封面路径,
                    self.封面矩形.w,
                    self.封面矩形.h,
                    int(封面圆角),
                    封面缩放模式,
                )
                if 封面图 is not None:
                    图缓存.写入(
                        self.歌曲.封面路径,
                        self.封面矩形.w,
                        self.封面矩形.h,
                        int(封面圆角),
                        封面缩放模式,
                        封面图,
                    )

        if 封面图 is not None:
            屏幕.blit(封面图, self.封面矩形.topleft)
        else:
            pygame.draw.rect(屏幕, (30, 30, 40), self.封面矩形)

        # =========================
        # 4) 信息条（高度可控）
        # =========================
        信息条高占比 = 取选歌布局值("缩略图.信息条.高占比", 0.26)
        try:
            信息条高占比 = float(信息条高占比)
        except Exception:
            信息条高占比 = 0.26
        信息条高占比 = max(0.05, min(0.80, 信息条高占比))

        信息条高 = max(18, int(self.封面矩形.h * 信息条高占比))
        信息条 = pygame.Rect(
            self.封面矩形.x, self.封面矩形.bottom - 信息条高, self.封面矩形.w, 信息条高
        )
        黑条 = pygame.Surface((信息条.w, 信息条.h), pygame.SRCALPHA)
        黑条.fill((0, 0, 0, 150))
        屏幕.blit(黑条, 信息条.topleft)

        # 星星（缩放倍数可控）
        星星缩放倍数 = 取选歌布局值("缩略图.星星.缩放倍数", 0.5)
        try:
            星星缩放倍数 = float(星星缩放倍数)
        except Exception:
            星星缩放倍数 = 0.5
        星星缩放倍数 = max(0.05, min(5.0, 星星缩放倍数))

        星左内边距 = 取选歌布局像素(
            "缩略图.星星.左内边距", 8, 屏宽, 屏高, 最小=0, 最大=9999
        )
        星右内边距 = 取选歌布局像素(
            "缩略图.星星.右内边距", 16, 屏宽, 屏高, 最小=0, 最大=9999
        )
        星上内边距 = 取选歌布局像素(
            "缩略图.星星.上内边距", 2, 屏宽, 屏高, 最小=-9999, 最大=9999
        )
        星高占比 = 取选歌布局值("缩略图.星星.区域高占比", 0.62)
        try:
            星高占比 = float(星高占比)
        except Exception:
            星高占比 = 0.62
        星高占比 = max(0.10, min(1.0, 星高占比))

        小星星路径 = _资源路径("UI-img", "选歌界面资源", "小星星", "小星星.png")
        星星区域 = pygame.Rect(
            信息条.x + int(星左内边距),
            信息条.y + int(星上内边距),
            max(10, 信息条.w - int(星左内边距) - int(星右内边距)),
            max(6, int(信息条.h * 星高占比)),
        )
        绘制星星行_图片(
            屏幕=屏幕,
            区域=星星区域,
            星数=self.歌曲.星级,
            星星路径=小星星路径,
            星星缩放倍数=float(星星缩放倍数),
            每行最大=10,
        )

        # =========================
        # 5) BPM：字号/位置全可控
        # =========================
        游玩次数 = 0
        try:
            游玩次数 = int(max(0, int(getattr(self.歌曲, "游玩次数", 0) or 0)))
        except Exception:
            游玩次数 = 0
        bpm文本 = f"BPM:{self.歌曲.bpm}" if self.歌曲.bpm else "BPM:?"
        默认字号 = max(10, int(信息条.h * 0.55))
        bpm字号 = 取选歌布局像素(
            "缩略图.BPM.字号", int(默认字号), 屏宽, 屏高, 最小=8, 最大=120
        )

        bpm右内边距 = 取选歌布局像素(
            "缩略图.BPM.右内边距",
            max(10, int(边框锚点矩形.w * 0.08)),
            屏宽,
            屏高,
            最小=0,
            最大=9999,
        )
        bpm下内边距 = 取选歌布局像素(
            "缩略图.BPM.下内边距", 2, 屏宽, 屏高, 最小=-9999, 最大=9999
        )
        bpmx偏移 = 取选歌布局像素(
            "缩略图.BPM.x偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
        )
        bpmy偏移 = 取选歌布局像素(
            "缩略图.BPM.y偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
        )
        游玩和BPM间距 = 取选歌布局像素(
            "缩略图.游玩次数.BPM间距",
            max(10, int(信息条.h * 0.20)),
            屏宽,
            屏高,
            最小=0,
            最大=9999,
        )
        游玩左内边距 = 取选歌布局像素(
            "缩略图.游玩次数.左内边距",
            max(8, int(信息条.w * 0.08)),
            屏宽,
            屏高,
            最小=0,
            最大=99999,
        )
        游玩中心x偏移 = 取选歌布局像素(
            "缩略图.游玩次数.中心x偏移",
            -max(6, int(信息条.w * 0.03)),
            屏宽,
            屏高,
            最小=-9999,
            最大=9999,
        )
        游玩x偏移 = 取选歌布局像素(
            "缩略图.游玩次数.x偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
        )
        游玩y偏移 = 取选歌布局像素(
            "缩略图.游玩次数.y偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
        )
        游玩标签字号 = 取选歌布局像素(
            "缩略图.游玩次数.标签字号",
            max(8, int(bpm字号 * 0.84)),
            屏宽,
            屏高,
            最小=8,
            最大=120,
        )
        游玩数字字号 = 取选歌布局像素(
            "缩略图.游玩次数.数字字号",
            max(8, int(bpm字号 * 0.94)),
            屏宽,
            屏高,
            最小=8,
            最大=120,
        )
        游玩标签字间距 = 取选歌布局像素(
            "缩略图.游玩次数.字间距", -1, 屏宽, 屏高, 最小=-8, 最大=12
        )
        游玩数值间距 = 取选歌布局像素(
            "缩略图.游玩次数.值间距", 2, 屏宽, 屏高, 最小=0, 最大=40
        )
        游玩标签基线偏移 = 取选歌布局像素(
            "缩略图.游玩次数.标签基线偏移", 0, 屏宽, 屏高, 最小=-20, 最大=20
        )
        游玩数字基线偏移 = 取选歌布局像素(
            "缩略图.游玩次数.数字基线偏移", 0, 屏宽, 屏高, 最小=-20, 最大=20
        )

        try:
            bpm字体 = 获取字体(int(bpm字号), 是否粗体=True)
            bpm文面 = bpm字体.render(bpm文本, True, (255, 255, 255))
            bpm文宽 = bpm文面.get_width()
            bpm文高 = bpm文面.get_height()

            bpm文x = 信息条.right - int(bpm右内边距) - bpm文宽 + int(bpmx偏移)
            bpm文y = 信息条.bottom - int(bpm下内边距) - bpm文高 + int(bpmy偏移)

            bpm文x = max(信息条.x + 2, min(信息条.right - 2 - bpm文宽, bpm文x))
            bpm文y = max(信息条.y, min(信息条.bottom - bpm文高, bpm文y))

            游玩标签字体 = 获取字体(int(游玩标签字号), 是否粗体=True)
            游玩数字字体 = 获取字体(int(游玩数字字号), 是否粗体=True)
            游玩标签面 = 渲染紧凑文本(
                "游玩次数:",
                游玩标签字体,
                (235, 235, 235),
                字符间距=int(游玩标签字间距),
            )
            游玩数字面 = 渲染紧凑文本(
                str(游玩次数),
                游玩数字字体,
                (235, 235, 235),
                字符间距=0,
            )
            游玩块宽 = (
                int(游玩标签面.get_width())
                + int(游玩数值间距)
                + int(游玩数字面.get_width())
            )
            游玩块理想x = (
                int(星星区域.centerx)
                - int(游玩块宽 * 0.56)
                + int(游玩中心x偏移)
                + int(游玩x偏移)
            )
            游玩块最小x = int(信息条.x + int(游玩左内边距))
            游玩块最大x = int(bpm文x - int(游玩和BPM间距) - int(游玩块宽))
            if 游玩块最大x < 游玩块最小x:
                游玩块x = int(max(信息条.x + 2, 游玩块最大x))
            else:
                游玩块x = int(max(游玩块最小x, min(游玩块最大x, 游玩块理想x)))

            基线y = int(bpm文y + bpm文高 + int(游玩y偏移))
            游玩标签y = int(
                基线y - int(游玩标签面.get_height()) + int(游玩标签基线偏移)
            )
            游玩数字y = int(
                基线y - int(游玩数字面.get_height()) + int(游玩数字基线偏移)
            )
            游玩标签y = max(
                信息条.y, min(信息条.bottom - int(游玩标签面.get_height()), 游玩标签y)
            )
            游玩数字y = max(
                信息条.y, min(信息条.bottom - int(游玩数字面.get_height()), 游玩数字y)
            )

            屏幕.blit(游玩标签面, (游玩块x, 游玩标签y))
            屏幕.blit(
                游玩数字面,
                (游玩块x + int(游玩标签面.get_width()) + int(游玩数值间距), 游玩数字y),
            )
            屏幕.blit(bpm文面, (bpm文x, bpm文y))
        except Exception:
            pass

        # =========================
        # 6) 盖框图（最后盖，避免封面压住框）
        # =========================
        if 框图 is not None:
            屏幕.blit(框图, (框x, 框y))

        # =========================
        # 7) 序号（仍走你现有的序号参数体系）
        # =========================
        绘制序号标签_图片(
            屏幕,
            边框锚点矩形,
            内部序号从0=self.歌曲.序号,
            是否大图=False,
        )

        # =========================
        # 8) VIP / NEW（尺寸/偏移可控，允许超框）
        # =========================
        if self.歌曲.是否VIP:
            vip路径 = _资源路径("UI-img", "选歌界面资源", "vip.png")
            vip原 = 获取UI原图(vip路径, 透明=True)
            if vip原 is not None:
                vip高占比 = 取选歌布局值("缩略图.VIP.高占比", 0.15)
                try:
                    vip高占比 = float(vip高占比)
                except Exception:
                    vip高占比 = 0.15
                vip高占比 = max(0.02, min(0.80, vip高占比))

                vip高 = max(10, int(边框锚点矩形.h * vip高占比))
                vip图 = _按高等比缩放(vip原, vip高)
                if vip图 is not None:
                    vipw, viph = vip图.get_size()
                    vipx偏移 = 取选歌布局像素(
                        "缩略图.VIP.x偏移",
                        -int(vipw * 0.30),
                        屏宽,
                        屏高,
                        最小=-9999,
                        最大=9999,
                    )
                    vipy偏移 = 取选歌布局像素(
                        "缩略图.VIP.y偏移",
                        -int(viph * 0.25),
                        屏宽,
                        屏高,
                        最小=-9999,
                        最大=9999,
                    )
                    vx = 边框锚点矩形.right - vipw + int(vipx偏移)
                    vy = 边框锚点矩形.top + int(vipy偏移)
                    屏幕.blit(vip图, (vx, vy))

        try:
            if bool(getattr(self.歌曲, "是否HOT", False)):
                hot路径 = _资源路径("UI-img", "选歌界面资源", "热门.png")
                hot原 = 获取UI原图(hot路径, 透明=True)
                if hot原 is not None:
                    hot高占比 = 取选歌布局值("缩略图.HOT.高占比", 0.20)
                    try:
                        hot高占比 = float(hot高占比)
                    except Exception:
                        hot高占比 = 0.20
                    hot高占比 = max(0.02, min(0.80, hot高占比))

                    hot高 = max(12, int(边框锚点矩形.h * hot高占比))
                    hot图 = _按高等比缩放(hot原, hot高)
                    if hot图 is not None:
                        hotw, _hoth = hot图.get_size()
                        hot右内边距 = 取选歌布局像素(
                            "缩略图.HOT.右内边距",
                            max(4, int(hot高 * 0.08)),
                            屏宽,
                            屏高,
                            最小=-9999,
                            最大=9999,
                        )
                        hot上内边距 = 取选歌布局像素(
                            "缩略图.HOT.上内边距",
                            max(4, int(hot高 * 0.06)),
                            屏宽,
                            屏高,
                            最小=-9999,
                            最大=9999,
                        )
                        hotx偏移 = 取选歌布局像素(
                            "缩略图.HOT.x偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
                        )
                        hoty偏移 = 取选歌布局像素(
                            "缩略图.HOT.y偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
                        )
                        if bool(getattr(self.歌曲, "是否VIP", False)):
                            hotx偏移 -= int(hotw * 0.82)

                        hx = (
                            边框锚点矩形.right - hotw - int(hot右内边距) + int(hotx偏移)
                        )
                        hy = 边框锚点矩形.top + int(hot上内边距) + int(hoty偏移)
                        屏幕.blit(hot图, (hx, hy))
        except Exception:
            pass

        try:
            if bool(getattr(self.歌曲, "是否NEW", False)):
                new路径 = _资源路径("UI-img", "选歌界面资源", "NEW绿色.png")
                new原 = 获取UI原图(new路径, 透明=True)
                if new原 is not None:
                    new高占比 = 取选歌布局值("缩略图.NEW.高占比", 0.22)
                    try:
                        new高占比 = float(new高占比)
                    except Exception:
                        new高占比 = 0.22
                    new高占比 = max(0.02, min(0.80, new高占比))

                    new高 = max(12, int(边框锚点矩形.h * new高占比))
                    new图 = _按高等比缩放(new原, new高)
                    if new图 is not None:
                        neww, newh = new图.get_size()
                        new右内边距 = 取选歌布局像素(
                            "缩略图.NEW.右内边距",
                            max(4, int(new高 * 0.10)),
                            屏宽,
                            屏高,
                            最小=-9999,
                            最大=9999,
                        )
                        new下内边距 = 取选歌布局像素(
                            "缩略图.NEW.下内边距",
                            max(4, int(new高 * 0.10)),
                            屏宽,
                            屏高,
                            最小=-9999,
                            最大=9999,
                        )
                        newx偏移 = 取选歌布局像素(
                            "缩略图.NEW.x偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
                        )
                        newy偏移 = 取选歌布局像素(
                            "缩略图.NEW.y偏移", 0, 屏宽, 屏高, 最小=-9999, 最大=9999
                        )

                        nx = (
                            边框锚点矩形.right - neww - int(new右内边距) + int(newx偏移)
                        )
                        ny = (
                            边框锚点矩形.bottom
                            - newh
                            - int(new下内边距)
                            + int(newy偏移)
                        )
                        屏幕.blit(new图, (nx, ny))
        except Exception:
            pass


# =========================
# 主程序
# =========================


class 选歌游戏:

    def __init__(
        self,
        songs根目录: str,
        背景音乐路径: str,
        logo路径: str,
        指定类型名: str = "",
        指定模式名: str = "",
        玩家数: int = 1,
        是否继承已有窗口: Optional[bool] = None,  # ✅ 新增：None=自动判断
    ):
        pygame.init()

        self.音频可用 = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            self.音频可用 = False

        pygame.display.set_caption("e舞成名 选歌界面（Pygame）")

        self.上下文: dict = {}

        传入songs根目录 = (
            os.path.abspath(str(songs根目录 or "").strip())
            if str(songs根目录 or "").strip()
            else ""
        )
        if 传入songs根目录 and os.path.isdir(传入songs根目录):
            self.songs根目录 = 传入songs根目录
        else:
            self.songs根目录 = _取songs根目录()

        self.背景音乐路径 = 背景音乐路径
        self.logo路径 = logo路径
        self.玩家数 = 2 if 玩家数 == 2 else 1
        self.指定类型名 = str(指定类型名 or "").strip()
        self.指定模式名 = str(指定模式名 or "").strip()

        self._需要退出 = False
        self._返回状态 = "NORMAL"
        self._调试提示文本 = ""
        self._调试提示截止 = 0.0

        现有屏幕 = None
        try:
            if pygame.display.get_init():
                现有屏幕 = pygame.display.get_surface()
        except Exception:
            现有屏幕 = None

        if 是否继承已有窗口 is None:
            self._是否嵌入模式 = bool(现有屏幕 is not None)
        else:
            self._是否嵌入模式 = bool(是否继承已有窗口)

        if self._是否嵌入模式 and (现有屏幕 is not None):
            self.屏幕 = 现有屏幕
            self.宽, self.高 = self.屏幕.get_size()
        else:
            try:
                os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
            except Exception:
                pass

            信息 = pygame.display.Info()
            默认宽, 默认高 = self._计算默认窗口尺寸(信息)
            self.屏幕 = pygame.display.set_mode((默认宽, 默认高), pygame.RESIZABLE)
            self.宽, self.高 = self.屏幕.get_size()

        self.时钟 = pygame.time.Clock()

        self._设计宽 = 2048
        self._设计高 = 1152

        脚本目录 = _取项目根目录()
        self._top栏背景原图 = 安全加载图片(
            os.path.join(脚本目录, "UI-img", "top栏", "top栏背景.png"), 透明=True
        )
        self._top_rect = pygame.Rect(0, 0, 1, 1)
        self._top图: Optional[pygame.Surface] = None
        self._top标题rect = pygame.Rect(0, 0, 1, 1)
        self._top标题图: Optional[pygame.Surface] = None
        self._top缓存尺寸 = (0, 0)

        self.标题字体 = 获取字体(40)
        self.标题粗体 = 获取字体(42)
        self.按钮字体 = 获取字体(30)
        self.按钮粗体 = 获取字体(32)
        self.正文字体 = 获取字体(24)
        self.正文字体粗 = 获取字体(26)
        self.小字体 = 获取字体(18)

        self.顶部高 = 78
        self.底部高 = 220

        self.当前页 = 0
        self.每页数量 = 8

        self.是否详情页 = False
        self.当前选择原始索引 = 0
        self.详情大框矩形 = pygame.Rect(0, 0, 0, 0)

        self.是否星级筛选页 = False
        self.当前筛选星级: Optional[int] = None
        self.星级按钮列表: List[Tuple[int, 按钮]] = []
        self.筛选页面板矩形 = pygame.Rect(0, 0, 0, 0)

        self.是否模式选择页 = False
        self.模式选择面板矩形 = pygame.Rect(0, 0, 0, 0)
        self.按钮_选择花式 = 按钮("Fancy 花式", pygame.Rect(0, 0, 0, 0))
        self.按钮_选择竞速 = 按钮("Speed 竞速", pygame.Rect(0, 0, 0, 0))
        self.按钮_关闭模式选择 = 按钮("返回", pygame.Rect(0, 0, 0, 0))

        self.图缓存 = 图像缓存()
        self.预加载队列 = []
        self._待清理保留key集合 = None

        self.动画中 = False
        self.动画开始时间 = 0.0
        self.动画持续 = 1.0
        self.动画方向 = 0
        self.动画目标页 = 0
        self.动画旧页卡片 = []
        self.动画新页卡片 = []
        self.当前页卡片 = []
        self._踏板选中视图索引: Optional[int] = None

        self.按钮_歌曲分类 = 按钮("歌曲分类", pygame.Rect(0, 0, 0, 0))
        self.按钮_ALL = 按钮("ALL", pygame.Rect(0, 0, 0, 0))
        self.按钮_2P加入 = 按钮("2P加入", pygame.Rect(0, 0, 0, 0))
        self.按钮_设置 = 按钮("设置", pygame.Rect(0, 0, 0, 0))
        self.按钮_重选模式 = 按钮("重选模式", pygame.Rect(0, 0, 0, 0))

        self.数据树 = {}
        if self.指定类型名 and self.指定模式名:
            try:
                self.数据树 = 扫描songs_指定路径(
                    self.songs根目录, self.指定类型名, self.指定模式名
                )
            except Exception:
                self.数据树 = {}

        if not self.数据树:
            try:
                self.数据树 = 扫描songs目录(self.songs根目录)
            except Exception:
                self.数据树 = {}

        self._同步歌曲游玩记录()

        self.类型列表 = sorted(self.数据树.keys())
        self.当前类型索引 = 0
        self.当前模式索引 = 0
        self.模式列表 = []

        匹配后的类型名 = _在现有名称中匹配(self.类型列表, self.指定类型名)
        if 匹配后的类型名:
            self.当前类型索引 = self.类型列表.index(匹配后的类型名)
            self.指定类型名 = 匹配后的类型名

        当前类型 = self.类型列表[self.当前类型索引] if self.类型列表 else ""
        self.模式列表 = sorted(self.数据树.get(当前类型, {}).keys())

        匹配后的模式名 = _在现有名称中匹配(self.模式列表, self.指定模式名)
        if 匹配后的模式名:
            self.当前模式索引 = self.模式列表.index(匹配后的模式名)
            self.指定模式名 = 匹配后的模式名
        else:
            self.当前模式索引 = 0

        self.背景图_原图 = None
        self.背景图_缩放缓存 = None
        self.背景图_缩放尺寸 = (0, 0)

        self._加载背景图()
        self._加载选歌布局覆盖(是否提示=False)

        self.重算布局()
        self.确保播放背景音乐()
        self.安排预加载(基准页=self.当前页)

    def _布局配置文件路径(self) -> str:
        return os.path.join(_取项目根目录(), "json", "选歌布局.json")

    def _加载布局配置(self, 是否提示: bool = False) -> dict:
        """
        ✅ 支持热更新：文件修改时间变化就重新载入
        ✅ 支持值写法：164 / "164" / "0.03w" / "0.02h" / "0.04min"
        """
        try:
            import json
        except Exception:
            return {}

        路径 = self._布局配置文件路径()
        try:
            修改时间 = os.path.getmtime(路径) if os.path.isfile(路径) else 0.0
        except Exception:
            修改时间 = 0.0

        if getattr(self, "_布局配置_缓存", None) is not None and float(
            getattr(self, "_布局配置_修改时间", 0.0) or 0.0
        ) == float(修改时间):
            return self._布局配置_缓存

        数据 = {}
        if os.path.isfile(路径):
            try:
                with open(路径, "r", encoding="utf-8") as f:
                    数据 = json.load(f)
            except Exception:
                数据 = {}

        if not isinstance(数据, dict):
            数据 = {}

        self._布局配置_缓存 = 数据
        self._布局配置_修改时间 = float(修改时间)

        if 是否提示:
            try:
                if 数据:
                    self._显示调试提示("已加载：json/选歌布局.json", 1.1)
                else:
                    self._显示调试提示(
                        "选歌布局.json 为空或读取失败，使用默认布局", 1.4
                    )
            except Exception:
                pass

        return 数据

    def 调试_热刷新选歌布局(self, 是否提示: bool = True):
        # ✅ 强制让下一次读取不走 mtime 缓存
        try:
            self._布局配置_修改时间 = -1.0
            self._布局配置_缓存 = None
        except Exception:
            pass

        # ✅ 全局布局缓存（给“非self绘制函数”用的那套）
        try:
            global _选歌布局_缓存, _选歌布局_修改时间
            _选歌布局_缓存 = None
            _选歌布局_修改时间 = -1.0
        except Exception:
            pass

        # ✅ 清 UI 缓存（框图/容器图/缩放图）
        try:
            global _UI缩放缓存, _UI容器缓存, _UI原图缓存
            if isinstance(_UI缩放缓存, dict):
                _UI缩放缓存.clear()
            if "_UI容器缓存" in globals() and isinstance(_UI容器缓存, dict):
                _UI容器缓存.clear()
            if isinstance(_UI原图缓存, dict):
                _UI原图缓存.clear()
        except Exception:
            pass

        # ✅ 清封面缓存（contain/cover/尺寸变化都重新算）
        try:
            if (
                hasattr(self, "图缓存")
                and hasattr(self.图缓存, "_缓存")
                and isinstance(self.图缓存._缓存, dict)
            ):
                self.图缓存._缓存.clear()
        except Exception:
            pass

        # ✅ 让 top/背景也重新生成（否则你会怀疑“怎么只变了一半”）
        try:
            self._top缓存尺寸 = (0, 0)
        except Exception:
            pass
        try:
            self.背景图_缩放缓存 = None
            self.背景图_缩放尺寸 = (0, 0)
        except Exception:
            pass

        # ✅ 关键：重算布局 + 重建卡片
        try:
            self.重算布局()
            self.当前页卡片 = self.生成指定页卡片(int(getattr(self, "当前页", 0) or 0))
            self.安排预加载(基准页=int(getattr(self, "当前页", 0) or 0))
        except Exception:
            pass

        if 是否提示:
            try:
                self._显示调试提示("F5热刷新：已重载 json/选歌布局.json + 清缓存", 1.2)
            except Exception:
                pass

    def _取布局值(self, 键路径: str, 默认值):
        配置 = self._加载布局配置(是否提示=False)
        当前 = 配置
        for 片段 in str(键路径 or "").split("."):
            if not 片段:
                continue
            if not isinstance(当前, dict) or 片段 not in 当前:
                return 默认值
            当前 = 当前.get(片段)
        return 默认值 if 当前 is None else 当前

    def _取布局像素(
        self, 键路径: str, 默认像素: int, 最小: int = None, 最大: int = None
    ) -> int:
        原 = self._取布局值(键路径, 默认像素)

        def _解析成浮点(v) -> float:
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                s = v.strip().lower()
                m = re.match(r"^(-?\d+(?:\.\d+)?)\s*(w|h|min)$", s)
                if m:
                    数 = float(m.group(1))
                    单位 = m.group(2)
                    if 单位 == "w":
                        基准 = float(getattr(self, "宽", 0) or 0)
                    elif 单位 == "h":
                        基准 = float(getattr(self, "高", 0) or 0)
                    else:
                        基准 = float(
                            min(
                                int(getattr(self, "宽", 0) or 0),
                                int(getattr(self, "高", 0) or 0),
                            )
                        )
                    return 数 * 基准
                return float(s)
            return float(默认像素)

        try:
            值 = int(round(_解析成浮点(原)))
        except Exception:
            值 = int(默认像素)

        if 最小 is not None:
            值 = max(int(最小), 值)
        if 最大 is not None:
            值 = min(int(最大), 值)
        return 值

    # -------------------------
    # 调试工具
    # -------------------------
    def _加载选歌布局覆盖(self, 是否提示: bool = True) -> bool:
        try:
            import json
        except Exception:
            return False

        目标文件 = os.path.join(_取项目根目录(), "json", "选歌布局覆盖.json")
        if not os.path.isfile(目标文件):
            return False

        try:
            with open(目标文件, "r", encoding="utf-8") as f:
                数据 = json.load(f)
        except Exception:
            return False

        if not isinstance(数据, dict):
            return False

        g = globals()
        允许前缀 = ("_缩略图", "_大图", "_序号")

        def _遍历叶子(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, dict):
                        for kk, vv in _遍历叶子(v):
                            yield kk, vv
                    else:
                        yield k, v

        已覆盖 = 0

        for k, v in _遍历叶子(数据):
            if not isinstance(k, str):
                continue
            if k not in g:
                continue
            if not any(k.startswith(p) for p in 允许前缀):
                continue

            原值 = g.get(k)
            try:
                if isinstance(原值, float):
                    g[k] = float(v)
                elif isinstance(原值, int):
                    g[k] = int(v)
                elif isinstance(原值, str):
                    g[k] = str(v)
                elif isinstance(原值, dict) and isinstance(v, dict):
                    g[k] = dict(v)
                elif isinstance(原值, (tuple, list)) and isinstance(v, (tuple, list)):
                    g[k] = tuple(v) if isinstance(原值, tuple) else list(v)
                else:
                    # 类型不匹配就跳过，避免把系统弄崩
                    continue
                已覆盖 += 1
            except Exception:
                continue

        # ✅ 强制让你“下一帧看到变化”：清掉缩放缓存（否则有些图可能还用旧缓存）
        try:
            _UI缩放缓存.clear()
        except Exception:
            pass

        if 是否提示:
            try:
                if 已覆盖 > 0:
                    self._显示调试提示(f"已加载：选歌布局覆盖.json（{已覆盖}项）", 1.2)
                else:
                    self._显示调试提示(
                        "选歌布局覆盖.json 已读取，但未命中可覆盖项", 1.4
                    )
            except Exception:
                pass

        return True

    def _计算默认窗口尺寸(self, 信息: pygame.display.Info) -> Tuple[int, int]:
        """
        默认非满屏：按屏幕的 80% 开一个可视窗口，并限制上下界。
        """
        try:
            屏宽 = int(getattr(信息, "current_w", 1280) or 1280)
            屏高 = int(getattr(信息, "current_h", 720) or 720)
        except Exception:
            屏宽, 屏高 = 1280, 720

        默认宽 = int(屏宽 * 0.80)
        默认高 = int(屏高 * 0.80)

        默认宽 = max(1000, min(默认宽, 1500))
        默认高 = max(650, min(默认高, 950))

        # 防止超出屏幕
        默认宽 = min(默认宽, max(960, 屏宽))
        默认高 = min(默认高, max(600, 屏高))
        return 默认宽, 默认高

    def _显示调试提示(self, 文本: str, 秒: float = 1.2):
        self._调试提示文本 = str(文本)
        self._调试提示截止 = time.time() + float(秒)

    # -------------------------
    # 数据访问
    # -------------------------

    def 当前类型名(self) -> str:
        if not self.类型列表:
            return "无类型"
        return self.类型列表[self.当前类型索引]

    def 当前模式名(self) -> str:
        if not self.模式列表:
            return "无模式"
        return self.模式列表[self.当前模式索引]

    def 当前原始歌曲列表(self) -> List[歌曲信息]:
        if not self.类型列表 or not self.模式列表:
            return []
        try:
            列表 = self.数据树[self.当前类型名()][self.当前模式名()]
        except Exception:
            return []

        # ✅ 确保 NEW 标记已计算
        try:
            self._确保NEW标记(列表)
        except Exception:
            pass

        return 列表

    def _同步歌曲游玩记录(self):
        根目录 = os.path.abspath(
            os.path.dirname(self.songs根目录)
            if str(self.songs根目录 or "").strip()
            else _取运行根目录()
        )
        try:
            索引 = 读取歌曲记录索引(根目录)
        except Exception:
            索引 = {}

        self._歌曲记录索引 = dict(索引) if isinstance(索引, dict) else {}

        for 类型映射 in self.数据树.values():
            if not isinstance(类型映射, dict):
                continue
            for 列表 in 类型映射.values():
                if not isinstance(列表, list):
                    continue
                for 歌 in 列表:
                    try:
                        键 = 取歌曲记录键(str(getattr(歌, "sm路径", "") or ""), 根目录)
                    except Exception:
                        键 = ""
                    项 = self._歌曲记录索引.get(键, {})
                    try:
                        游玩次数 = int(max(0, int((项 or {}).get("游玩次数", 0) or 0)))
                    except Exception:
                        游玩次数 = 0
                    try:
                        setattr(歌, "游玩次数", 游玩次数)
                        setattr(歌, "是否HOT", bool(游玩次数 > 2))
                    except Exception:
                        pass

    def _确保NEW标记(self, 原始列表: Optional[List[歌曲信息]] = None):
        if 原始列表 is None:
            try:
                原始列表 = self.数据树[self.当前类型名()][self.当前模式名()]
            except Exception:
                原始列表 = []

        try:
            缓存键 = (self.当前类型名(), self.当前模式名(), id(原始列表), len(原始列表))
        except Exception:
            缓存键 = None

        if getattr(self, "_NEW标记_缓存键", None) == 缓存键:
            return

        self._NEW标记_缓存键 = 缓存键
        self._更新当前模式NEW标记(原始列表)

    def _更新当前模式NEW标记(self, 原始列表: List[歌曲信息]):
        """
        规则：
        - 同“歌名”(解析后的 歌.歌名) 出现多个版本时
        - 最高星级的版本标记为 是否NEW=True（其余 False）
        """
        名称计数: Dict[str, int] = {}
        名称最大星: Dict[str, int] = {}

        for 歌 in 原始列表:
            名键 = re.sub(r"\s+", "", str(getattr(歌, "歌名", "") or "")).lower()
            if not 名键:
                名键 = re.sub(
                    r"\s+", "", str(getattr(歌, "歌曲文件夹", "") or "")
                ).lower()

            星 = 0
            try:
                星 = int(getattr(歌, "星级", 0) or 0)
            except Exception:
                星 = 0

            名称计数[名键] = 名称计数.get(名键, 0) + 1
            名称最大星[名键] = max(名称最大星.get(名键, 0), 星)

        for 歌 in 原始列表:
            名键 = re.sub(r"\s+", "", str(getattr(歌, "歌名", "") or "")).lower()
            if not 名键:
                名键 = re.sub(
                    r"\s+", "", str(getattr(歌, "歌曲文件夹", "") or "")
                ).lower()

            星 = 0
            try:
                星 = int(getattr(歌, "星级", 0) or 0)
            except Exception:
                星 = 0

            是否多版本 = 名称计数.get(名键, 0) >= 2
            是否最高星 = 星 == 名称最大星.get(名键, 星)

            try:
                setattr(歌, "是否NEW", bool(是否多版本 and 是否最高星))
            except Exception:
                pass

    def 绘制NEW标签_大图(self):
        """
        ✅ 叠加绘制（z轴在最上层）：
        - NEW：允许超出详情大框边界
        - VIP：允许超出详情大框边界
        """
        if not bool(getattr(self, "是否详情页", False)):
            return

        原始 = self.当前原始歌曲列表()
        if not 原始:
            return

        idx = int(getattr(self, "当前选择原始索引", 0) or 0)
        if idx < 0 or idx >= len(原始):
            return
        歌 = 原始[idx]

        大框 = getattr(self, "详情大框矩形", None)
        if not isinstance(大框, pygame.Rect) or 大框.w <= 10 or 大框.h <= 10:
            return

        alpha = int(getattr(self, "_详情浮层_alpha", 255) or 255)
        alpha = max(0, min(255, alpha))

        # ========= VIP =========
        if bool(getattr(歌, "是否VIP", False)):
            vip路径 = _资源路径("UI-img", "选歌界面资源", "vip.png")
            vip原 = 获取UI原图(vip路径, 透明=True)
            if vip原 is not None:
                vip高占比 = self._取布局值("详情大图.VIP.高占比", 0.20)
                try:
                    vip高占比 = float(vip高占比)
                except Exception:
                    vip高占比 = 0.20
                vip高占比 = max(0.02, min(0.90, vip高占比))

                vip高 = max(12, int(大框.h * vip高占比))
                vip图 = _按高等比缩放(vip原, vip高)
                if vip图 is not None:
                    try:
                        vip图.set_alpha(alpha)
                    except Exception:
                        pass

                    vipw, viph = vip图.get_size()
                    vipx偏移 = self._取布局像素(
                        "详情大图.VIP.x偏移", -int(vipw * 0.20), 最小=-99999, 最大=99999
                    )
                    vipy偏移 = self._取布局像素(
                        "详情大图.VIP.y偏移", -int(viph * 0.35), 最小=-99999, 最大=99999
                    )

                    vx = 大框.right - vipw + int(vipx偏移)
                    vy = 大框.top + int(vipy偏移)
                    self.屏幕.blit(vip图, (vx, vy))

        # ========= NEW =========
        if bool(getattr(歌, "是否NEW", False)):
            new路径 = _资源路径("UI-img", "选歌界面资源", "NEW绿色.png")
            new原 = 获取UI原图(new路径, 透明=True)
            if new原 is not None:
                new高占比 = self._取布局值("详情大图.NEW.高占比", 0.26)
                try:
                    new高占比 = float(new高占比)
                except Exception:
                    new高占比 = 0.26
                new高占比 = max(0.02, min(0.90, new高占比))

                new高 = max(14, int(大框.h * new高占比))
                new图 = _按高等比缩放(new原, new高)
                if new图 is None:
                    return

                try:
                    new图.set_alpha(alpha)
                except Exception:
                    pass

                neww, newh = new图.get_size()

                new右内边距 = self._取布局像素(
                    "详情大图.NEW.右内边距",
                    max(6, int(new高 * 0.10)),
                    最小=-99999,
                    最大=99999,
                )
                new下内边距 = self._取布局像素(
                    "详情大图.NEW.下内边距",
                    max(6, int(new高 * 0.10)),
                    最小=-99999,
                    最大=99999,
                )
                newx偏移 = self._取布局像素(
                    "详情大图.NEW.x偏移", +int(neww * 0.15), 最小=-99999, 最大=99999
                )  # 默认略往外
                newy偏移 = self._取布局像素(
                    "详情大图.NEW.y偏移", +int(newh * 0.15), 最小=-99999, 最大=99999
                )  # 默认略往外

                nx = 大框.right - neww - int(new右内边距) + int(newx偏移)
                ny = 大框.bottom - newh - int(new下内边距) + int(newy偏移)
                self.屏幕.blit(new图, (nx, ny))

    def 当前歌曲列表与映射(self) -> Tuple[List[歌曲信息], List[int]]:
        """
        返回：(显示用歌曲列表, 显示索引 -> 原始索引 映射)
        """
        原始 = self.当前原始歌曲列表()
        if not 原始:
            return [], []
        if self.当前筛选星级 is None:
            映射 = list(range(len(原始)))
            return 原始, 映射

        过滤列表: List[歌曲信息] = []
        映射: List[int] = []
        for i, 歌 in enumerate(原始):
            if int(歌.星级) == int(self.当前筛选星级):
                过滤列表.append(歌)
                映射.append(i)
        return 过滤列表, 映射

    def 总页数(self) -> int:
        列表, _映射 = self.当前歌曲列表与映射()
        return max(1, math.ceil(len(列表) / self.每页数量))

    def _播放开始游戏音效(self):
        """
        ✅ 尽量不打断 pygame.mixer.music（它在播预览MP3/背景BGM）
        这里用你项目里的 公用按钮音效（通常走 Sound 通道）。
        """
        try:
            if getattr(self, "_开始游戏音效_对象", None) is not None:
                self._开始游戏音效_对象.播放()
        except Exception:
            # 兜底：静默失败，避免影响主循环
            pass

    def _生成加载页载荷(self) -> dict:
        # ✅ 先确保设置页默认参数存在
        try:
            if hasattr(self, "_确保设置页资源"):
                self._确保设置页资源()
        except Exception:
            pass

        原始列表 = []
        try:
            原始列表 = self.当前原始歌曲列表()
        except Exception:
            原始列表 = []

        歌 = None
        try:
            当前索引 = int(getattr(self, "当前选择原始索引", 0) or 0)
            if 0 <= 当前索引 < len(原始列表):
                歌 = 原始列表[当前索引]
        except Exception:
            歌 = None

        # ✅ 设置参数：优先用持久化 json，其次才用内存参数
        try:
            if hasattr(self, "_设置页_保存持久化设置"):
                self._设置页_保存持久化设置()
        except Exception:
            pass

        设置参数 = {}
        背景文件名 = ""
        箭头文件名 = ""
        设置参数文本 = ""

        try:
            if hasattr(self, "_设置页_读取持久化设置"):
                持久化数据 = self._设置页_读取持久化设置()
            else:
                持久化数据 = {}
        except Exception:
            持久化数据 = {}

        if isinstance(持久化数据, dict):
            try:
                v = 持久化数据.get("设置参数", {})
                if isinstance(v, dict):
                    设置参数 = dict(v)
            except Exception:
                pass
            try:
                背景文件名 = str(持久化数据.get("背景文件名", "") or "")
            except Exception:
                背景文件名 = ""
            try:
                箭头文件名 = str(持久化数据.get("箭头文件名", "") or "")
            except Exception:
                箭头文件名 = ""
            try:
                设置参数文本 = str(持久化数据.get("设置参数文本", "") or "")
            except Exception:
                设置参数文本 = ""

        if not 设置参数:
            try:
                临时参数 = getattr(self, "设置_参数", None)
                if isinstance(临时参数, dict):
                    设置参数 = dict(临时参数)
            except Exception:
                设置参数 = {}

        if not 背景文件名:
            try:
                背景文件名 = str(getattr(self, "设置_背景大图文件名", "") or "")
            except Exception:
                背景文件名 = ""
        if not 箭头文件名:
            try:
                箭头文件名 = str(getattr(self, "设置_箭头文件名", "") or "")
            except Exception:
                箭头文件名 = ""

        if not 设置参数文本:
            try:
                设置参数文本 = self._设置页_构建参数文本(
                    设置参数=设置参数,
                    背景文件名=背景文件名,
                    箭头文件名=箭头文件名,
                )
            except Exception:
                设置参数文本 = "设置参数：默认"

        # ✅ 歌曲信息（兜底）
        sm路径 = "未知"
        封面路径 = ""
        歌名 = "Loading..."
        星级 = 0
        bpm = None
        游玩次数 = 0
        类型 = ""
        模式 = ""
        歌曲文件夹 = ""
        原始歌曲文件夹 = ""

        if 歌 is not None:
            try:
                sm路径 = str(getattr(歌, "sm路径", "") or "未知")
            except Exception:
                sm路径 = "未知"
            try:
                封面路径 = str(getattr(歌, "封面路径", "") or "")
            except Exception:
                封面路径 = ""
            try:
                歌名 = str(getattr(歌, "歌名", "") or "Loading...")
            except Exception:
                歌名 = "Loading..."
            try:
                星级 = int(getattr(歌, "星级", 0) or 0)
            except Exception:
                星级 = 0
            try:
                bpm = getattr(歌, "bpm", None)
                bpm = int(bpm) if bpm is not None else None
            except Exception:
                bpm = None
            try:
                游玩次数 = int(max(0, int(getattr(歌, "游玩次数", 0) or 0)))
            except Exception:
                游玩次数 = 0

            # ✅ 这三个用于 StepMania runtime pack 命名/建目录
            try:
                类型 = str(getattr(歌, "类型", "") or "")
            except Exception:
                类型 = ""
            try:
                模式 = str(getattr(歌, "模式", "") or "")
            except Exception:
                模式 = ""
            try:
                歌曲文件夹 = str(getattr(歌, "歌曲文件夹", "") or "")
            except Exception:
                歌曲文件夹 = ""

            # ✅ 原始歌曲文件夹：直接取 sm 所在目录（里面有 .sm）
            try:
                if sm路径 and os.path.isfile(sm路径):
                    原始歌曲文件夹 = os.path.dirname(sm路径)
            except Exception:
                原始歌曲文件夹 = ""

        人气 = 0
        try:
            人气 = int(bpm or 0)
        except Exception:
            人气 = 0

        状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
        当前关卡 = 取当前关卡(状态, 1)
        累计S数 = 取累计S数(状态)
        已赠送第四把 = 是否赠送第四把(状态)

        return {
            "sm路径": sm路径,
            "封面路径": 封面路径,
            "歌名": 歌名,
            "星级": int(星级),
            "bpm": bpm,
            "人气": int(人气),
            "游玩次数": int(游玩次数),
            "设置参数": dict(设置参数),
            "设置参数文本": str(设置参数文本),
            # ✅ 给 StepMania 用
            "类型": 类型,
            "模式": 模式,
            "歌曲文件夹": 歌曲文件夹,
            "原始歌曲文件夹": 原始歌曲文件夹,
            "选歌原始索引": int(当前索引 if 歌 is not None else -1),
            "当前关卡": int(当前关卡),
            "局数": int(当前关卡),
            "累计S数": int(累计S数),
            "是否赠送第四把": bool(已赠送第四把),
        }

    def _写入加载页json(self, 载荷: dict):
        try:
            import json
        except Exception:
            return

        try:
            根目录 = _取运行根目录()
            目录 = os.path.join(根目录, "json")
            os.makedirs(目录, exist_ok=True)
            路径 = os.path.join(目录, "加载页.json")
            with open(路径, "w", encoding="utf-8") as 文件:
                json.dump(dict(载荷 or {}), 文件, ensure_ascii=False, indent=2)
        except Exception:
            return

    def _记录并处理大图确认点击(self):
        现在时间 = time.time()
        上次触发 = float(getattr(self, "_大图确认_上次触发时间", 0.0) or 0.0)

        if 上次触发 > 0.0 and (现在时间 - 上次触发) < 0.25:
            return

        self._大图确认_上次触发时间 = 现在时间

        # 1) 播放开始音效（你原逻辑）
        self._播放开始游戏音效()

        # 2) 生成加载页载荷（给新场景展示）
        try:
            self._加载页_载荷 = self._生成加载页载荷()
        except Exception:
            self._加载页_载荷 = {}

        # ✅ 2.1 关键：落盘，加载页/谱面播放器都能兜底读取
        try:
            self._写入加载页json(self._加载页_载荷)
        except Exception:
            pass

        # 3) 退出选歌，交给上层切场景
        self._返回状态 = "GO_LOADING"
        self._需要退出 = True

    def 显示消息提示(self, 文本: str, 持续秒: float = 2.0):
        self._消息提示_文本 = str(文本 or "")
        self._消息提示_截止时间 = time.time() + float(max(0.1, 持续秒))

    def _绘制消息提示(self):
        文本 = str(getattr(self, "_消息提示_文本", "") or "")
        截止 = float(getattr(self, "_消息提示_截止时间", 0.0) or 0.0)
        if (not 文本) or time.time() >= 截止:
            return

        屏幕 = self.屏幕
        w, h = 屏幕.get_size()

        try:
            字体 = getattr(self, "正文字体粗", None) or getattr(self, "正文字体", None)
            if 字体 is None:
                字体 = 获取字体(26, 是否粗体=True)
        except Exception:
            字体 = 获取字体(26, 是否粗体=True)

        最大宽 = int(w * 0.72)
        内边距x = 26
        内边距y = 18
        圆角 = 18

        # 简单自动换行（按像素宽）
        行列表 = []
        当前行 = ""
        for 字 in 文本:
            if 字 == "\n":
                行列表.append(当前行)
                当前行 = ""
                continue
            测试 = 当前行 + 字
            try:
                if 字体.size(测试)[0] <= 最大宽:
                    当前行 = 测试
                else:
                    if 当前行:
                        行列表.append(当前行)
                    当前行 = 字
            except Exception:
                当前行 = 测试

        if 当前行:
            行列表.append(当前行)

        # 渲染每行
        行面列表 = []
        文本宽 = 0
        文本高 = 0
        for 行 in 行列表:
            try:
                白 = 字体.render(行, True, (255, 255, 255))
                黑 = 字体.render(行, True, (0, 0, 0))
                行面列表.append((白, 黑))
                文本宽 = max(文本宽, 白.get_width())
                文本高 += 白.get_height()
            except Exception:
                continue

        if not 行面列表:
            return

        背景宽 = min(w - 60, 文本宽 + 内边距x * 2)
        背景高 = min(h - 60, 文本高 + 内边距y * 2)

        # 位置：偏下中间（别挡住top栏）
        背景x = (w - 背景宽) // 2
        背景y = int(h * 0.58) - 背景高 // 2
        背景y = max(int(getattr(self, "顶部高", 80) + 18), 背景y)

        背景矩形 = pygame.Rect(背景x, 背景y, 背景宽, 背景高)

        # 半透明背景 + 边框
        背景面 = pygame.Surface((背景矩形.w, 背景矩形.h), pygame.SRCALPHA)
        背景面.fill((0, 0, 0, 180))
        屏幕.blit(背景面, 背景矩形.topleft)
        try:
            pygame.draw.rect(
                屏幕, (255, 220, 120), 背景矩形, width=2, border_radius=圆角
            )
        except Exception:
            pass

        # 绘制文字（带轻微黑影）
        当前y = 背景矩形.y + 内边距y
        for 白, 黑 in 行面列表:
            x = 背景矩形.centerx - 白.get_width() // 2
            屏幕.blit(黑, (x + 2, 当前y + 2))
            屏幕.blit(白, (x, 当前y))
            当前y += 白.get_height()

    # -------------------------
    # 音频
    # -------------------------

    def _背景音乐被全局关闭(self) -> bool:
        try:
            状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
        except Exception:
            状态 = {}
        if not isinstance(状态, dict):
            状态 = {}
        try:
            return bool(状态.get("非游戏菜单背景音乐关闭", False))
        except Exception:
            return False

    def 确保播放背景音乐(self):
        if not self.音频可用:
            return
        if self._背景音乐被全局关闭():
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            return
        if not self.背景音乐路径 or not os.path.isfile(self.背景音乐路径):
            return
        try:
            if pygame.mixer.music.get_busy():
                return
            pygame.mixer.music.load(self.背景音乐路径)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def 播放歌曲mp3(self, mp3路径: Optional[str]):
        if not self.音频可用:
            return
        if self._背景音乐被全局关闭():
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        if not mp3路径 or not os.path.isfile(mp3路径):
            return
        try:
            pygame.mixer.music.load(mp3路径)
            pygame.mixer.music.play()
        except Exception:
            pass

    # -------------------------
    # 布局
    # -------------------------

    def 重算布局(self):
        self._确保公共交互()

        self.宽, self.高 = self.屏幕.get_size()
        self._top缓存尺寸 = (0, 0)

        self._确保top栏缓存()

        if self.背景图_原图 is None:
            self._加载背景图()

        # ========= 底部槽位（JSON可控）=========
        槽边长 = self._取布局像素("底部.槽边长", 164, 最小=80, 最大=320)

        标签占比 = self._取布局值("底部.标签区高占比", 0.26)
        try:
            标签占比 = float(标签占比)
        except Exception:
            标签占比 = 0.26
        标签占比 = max(0.05, min(0.60, 标签占比))

        标签区高 = max(34, int(槽边长 * 标签占比))
        槽总高 = 槽边长 + 标签区高

        底部最小高 = self._取布局像素("底部.底部最小高", 220, 最小=120, 最大=9999)
        底部额外高 = self._取布局像素("底部.底部额外高", 40, 最小=0, 最大=9999)
        self.底部高 = max(底部最小高, 槽总高 + 底部额外高)

        self.中间区域 = pygame.Rect(
            0, self.顶部高, self.宽, self.高 - self.顶部高 - self.底部高
        )

        槽y = self.高 - self.底部高 + (self.底部高 - 槽总高) // 2

        左起 = self._取布局像素("底部.左起", 28, 最小=0, 最大=9999)
        左组间距 = self._取布局像素("底部.左组间距", 12, 最小=0, 最大=9999)
        右组间距 = self._取布局像素("底部.右组间距", 26, 最小=0, 最大=9999)
        右外边距 = self._取布局像素("底部.右外边距", 40, 最小=0, 最大=9999)

        槽_歌曲分类 = pygame.Rect(左起, 槽y, 槽边长, 槽总高)
        槽_ALL = pygame.Rect(槽_歌曲分类.right + 左组间距, 槽y, 槽边长, 槽总高)
        槽_重开 = pygame.Rect(槽_ALL.right + 左组间距, 槽y, 槽边长, 槽总高)

        右起 = self.宽 - 右外边距 - 槽边长
        槽_设置 = pygame.Rect(右起, 槽y, 槽边长, 槽总高)
        槽_P加入 = pygame.Rect(右起 - 右组间距 - 槽边长, 槽y, 槽边长, 槽总高)

        # ===== 资源路径 =====
        歌曲分类图路径 = _资源路径("UI-img", "选歌界面资源", "歌曲分类.png")
        ALL图路径 = _资源路径("UI-img", "选歌界面资源", "all按钮.png")
        设置图路径 = _资源路径("UI-img", "选歌界面资源", "设置.png")

        # ✅ 1P/2P 联动：缺谁就显示谁加入
        当前玩家数 = 2 if int(getattr(self, "玩家数", 1)) == 2 else 1
        需要显示加入 = 2 if 当前玩家数 == 1 else 1
        P加入底文 = f"{需要显示加入}P加入"

        P加入候选 = [
            _资源路径("UI-img", "选歌界面资源", f"{需要显示加入}p加入.png"),
            _资源路径("UI-img", "选歌界面资源", f"{需要显示加入}P加入.png"),
            _资源路径("UI-img", "选歌界面资源", "1p加入.png"),
        ]
        P加入图路径 = P加入候选[-1]
        for p in P加入候选:
            if os.path.isfile(p):
                P加入图路径 = p
                break

        # ===== 确保底部按钮类型 =====
        if (not hasattr(self, "按钮_歌曲分类")) or (
            not isinstance(self.按钮_歌曲分类, 底部图文按钮)
        ):
            self.按钮_歌曲分类 = 底部图文按钮(
                图片路径=歌曲分类图路径,
                矩形=pygame.Rect(0, 0, 0, 0),
                底部文字="歌曲分类",
                是否处理透明像素=False,
            )

        if (not hasattr(self, "按钮_ALL")) or (not isinstance(self.按钮_ALL, 图片按钮)):
            self.按钮_ALL = 图片按钮(
                图片路径=ALL图路径,
                矩形=pygame.Rect(0, 0, 0, 0),
                是否水平翻转=False,
                是否垂直翻转=False,
            )

        if (not hasattr(self, "按钮_2P加入")) or (
            not isinstance(self.按钮_2P加入, 底部图文按钮)
        ):
            self.按钮_2P加入 = 底部图文按钮(
                图片路径=P加入图路径,
                矩形=pygame.Rect(0, 0, 0, 0),
                底部文字=P加入底文,
                是否处理透明像素=False,
            )
        else:
            try:
                self.按钮_2P加入.图片路径 = str(P加入图路径)
                self.按钮_2P加入.底部文字 = str(P加入底文)
                self.按钮_2P加入._加载原图()
            except Exception:
                pass

        if (not hasattr(self, "按钮_设置")) or (
            not isinstance(self.按钮_设置, 底部图文按钮)
        ):
            self.按钮_设置 = 底部图文按钮(
                图片路径=设置图路径,
                矩形=pygame.Rect(0, 0, 0, 0),
                底部文字="设置",
                是否处理透明像素=False,
            )

        if not hasattr(self, "按钮_重选模式"):
            self.按钮_重选模式 = 按钮("重开", pygame.Rect(0, 0, 0, 0))
        else:
            try:
                self.按钮_重选模式.名称 = "重开"
            except Exception:
                pass

        # ===== 设置最终矩形 =====
        self.按钮_歌曲分类.矩形 = 槽_歌曲分类
        self.按钮_2P加入.矩形 = 槽_P加入
        self.按钮_设置.矩形 = 槽_设置

        统一文字偏移 = self._取布局像素("底部.统一文字偏移", -6, 最小=-9999, 最大=9999)
        try:
            self.按钮_歌曲分类.文字y偏移 = 统一文字偏移
            self.按钮_2P加入.文字y偏移 = 统一文字偏移
            self.按钮_设置.文字y偏移 = 统一文字偏移
        except Exception:
            pass

        # ALL / 重开：只占上半部图标区
        槽_ALL_图标区 = pygame.Rect(槽_ALL.x, 槽_ALL.y, 槽边长, 槽边长)
        槽_重开_图标区 = pygame.Rect(槽_重开.x, 槽_重开.y, 槽边长, 槽边长)

        ALL缩放 = self._取布局值("底部.ALL缩放", 0.5)
        重开缩放 = self._取布局值("底部.重开缩放", 0.5)
        try:
            ALL缩放 = float(ALL缩放)
        except Exception:
            ALL缩放 = 0.5
        try:
            重开缩放 = float(重开缩放)
        except Exception:
            重开缩放 = 0.5
        ALL缩放 = max(0.1, min(2.0, ALL缩放))
        重开缩放 = max(0.1, min(2.0, 重开缩放))

        ALL边长 = max(30, int(槽边长 * ALL缩放))
        重开边长 = max(30, int(槽边长 * 重开缩放))

        ALL矩形 = pygame.Rect(0, 0, ALL边长, ALL边长)
        ALL矩形.center = 槽_ALL_图标区.center
        self.按钮_ALL.矩形 = ALL矩形

        重开矩形 = pygame.Rect(0, 0, 重开边长, 重开边长)
        重开矩形.center = 槽_重开_图标区.center
        self.按钮_重选模式.矩形 = 重开矩形

        # ========= 模式选择面板（JSON可控）=========
        最大宽 = self._取布局像素("模式选择面板.最大宽", 920, 最小=300, 最大=9999)
        最大高 = self._取布局像素("模式选择面板.最大高", 460, 最小=200, 最大=9999)

        宽占比 = self._取布局值("模式选择面板.宽占比", 0.75)
        高占比 = self._取布局值("模式选择面板.高占比", 0.55)
        try:
            宽占比 = float(宽占比)
        except Exception:
            宽占比 = 0.75
        try:
            高占比 = float(高占比)
        except Exception:
            高占比 = 0.55
        宽占比 = max(0.20, min(0.98, 宽占比))
        高占比 = max(0.20, min(0.98, 高占比))

        面板宽 = min(最大宽, int(self.宽 * 宽占比))
        面板高 = min(最大高, int(self.高 * 高占比))
        面板x = (self.宽 - 面板宽) // 2
        面板y = (self.高 - 面板高) // 2
        self.模式选择面板矩形 = pygame.Rect(面板x, 面板y, 面板宽, 面板高)

        内边距 = self._取布局像素("模式选择面板.内边距", 28, 最小=0, 最大=9999)
        区域 = self.模式选择面板矩形.inflate(-内边距 * 2, -内边距 * 2)

        按钮高 = self._取布局像素("模式选择面板.按钮高", 120, 最小=40, 最大=9999)
        按钮间距 = self._取布局像素("模式选择面板.按钮间距", 18, 最小=0, 最大=9999)
        标题下移 = self._取布局像素("模式选择面板.标题下移", 120, 最小=0, 最大=9999)

        按钮宽 = max(10, (区域.w - 按钮间距) // 2)
        bx = 区域.x
        by = 区域.y + 标题下移

        self.按钮_选择花式.矩形 = pygame.Rect(bx, by, 按钮宽, 按钮高)
        self.按钮_选择竞速.矩形 = pygame.Rect(
            bx + 按钮宽 + 按钮间距, by, 按钮宽, 按钮高
        )

        关闭宽 = self._取布局像素("模式选择面板.关闭按钮宽", 180, 最小=60, 最大=9999)
        关闭高 = self._取布局像素("模式选择面板.关闭按钮高", 60, 最小=30, 最大=9999)
        关闭下边距 = self._取布局像素(
            "模式选择面板.关闭按钮下边距", 86, 最小=0, 最大=9999
        )
        self.按钮_关闭模式选择.矩形 = pygame.Rect(
            self.模式选择面板矩形.centerx - 关闭宽 // 2,
            self.模式选择面板矩形.bottom - 关闭下边距,
            关闭宽,
            关闭高,
        )

        # ========= 卡片网格（让每页数量跟随列行）=========
        try:
            列数 = int(self._取布局值("卡片网格.列数", 4))
        except Exception:
            列数 = 4
        try:
            行数 = int(self._取布局值("卡片网格.行数", 2))
        except Exception:
            行数 = 2
        列数 = max(1, min(12, 列数))
        行数 = max(1, min(12, 行数))
        self.每页数量 = int(列数 * 行数)

        self.当前页卡片 = self.生成指定页卡片(self.当前页)
        self._重算星级筛选页布局()

        # 详情页左右按钮（保留）
        下一首图路径 = _资源路径("UI-img", "选歌界面资源", "下一首.png")
        if (not hasattr(self, "按钮_详情上一首")) or (
            not isinstance(self.按钮_详情上一首, 图片按钮)
        ):
            self.按钮_详情上一首 = 图片按钮(
                图片路径=下一首图路径,
                矩形=pygame.Rect(0, 0, 0, 0),
                是否水平翻转=True,
                是否垂直翻转=False,
            )
        if (not hasattr(self, "按钮_详情下一首")) or (
            not isinstance(self.按钮_详情下一首, 图片按钮)
        ):
            self.按钮_详情下一首 = 图片按钮(
                图片路径=下一首图路径,
                矩形=pygame.Rect(0, 0, 0, 0),
                是否水平翻转=False,
                是否垂直翻转=False,
            )

    def _加载背景图(self):
        try:
            脚本目录 = _取项目根目录()
            路径 = os.path.join(脚本目录, "冷资源", "backimages", "选歌界面.png")
            if os.path.isfile(路径):
                self.背景图_原图 = pygame.image.load(路径).convert()
            else:
                self.背景图_原图 = None
        except Exception:
            self.背景图_原图 = None

    def _确保top栏缓存(self):
        self._确保top栏资源()

        w, h = self.屏幕.get_size()
        if getattr(self, "_top缓存尺寸", (0, 0)) == (w, h):
            return
        self._top缓存尺寸 = (w, h)

        # ✅ 用 ui/top栏.py 统一生成 top 栏（中间标题用 歌曲选择.png）
        self._top_rect, self._top图, self._top标题rect, self._top标题图 = 生成top栏(
            屏幕=self.屏幕,
            top背景原图=self._top栏背景原图,
            标题原图=self._top中间标题原图,
            设计宽=self._设计宽,
            设计高=self._设计高,
            top设计高=150,
            top背景宽占比=1.0,
            top背景高占比=1.0,
            标题最大宽占比=0.5,
            标题最大高占比=0.5,
            标题整体缩放=1.0,
            标题上移比例=0.1,
        )

        # ✅ 让布局用 top 真高度（避免你中间区域算错）
        self.顶部高 = max(78, int(self._top_rect.h))

    def _确保top栏资源(self):
        if getattr(self, "_top资源已初始化", False):
            return

        self._top资源已初始化 = True

        # ===== 设计基准（给 ui/top栏.py 缩放用）=====
        if not hasattr(self, "_设计宽"):
            self._设计宽 = 2048
        if not hasattr(self, "_设计高"):
            self._设计高 = 1152

        脚本目录 = _取项目根目录()

        # ===== top栏背景（统一皮肤）=====
        self._top栏背景原图 = None
        try:
            路径 = os.path.join(脚本目录, "UI-img", "top栏", "top栏背景.png")
            if os.path.isfile(路径):
                self._top栏背景原图 = pygame.image.load(路径).convert_alpha()
        except Exception:
            self._top栏背景原图 = None

        # ===== 中间标题：歌曲选择.png =====
        self._top中间标题原图 = None
        try:
            路径 = os.path.join(脚本目录, "UI-img", "top栏", "歌曲选择.png")
            if os.path.isfile(路径):
                self._top中间标题原图 = pygame.image.load(路径).convert_alpha()
        except Exception:
            self._top中间标题原图 = None

        # ===== 左上角：类型/模式 图片绑定表 =====
        # 类型（大模式）
        self._top类型图片路径表 = {
            "花式": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "大模式-花式.png"
            ),
            "竞速": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "大模式-竞速.png"
            ),
            "派对": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "大模式-派对模式.png"
            ),
            "diy": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "大模式-diy.png"
            ),
            "wef": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "大模式-wef.png"
            ),
        }

        # 模式（子模式）
        self._top模式图片路径表 = {
            "表演": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "表演模式.png"
            ),
            "学习": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "学习模式.png"
            ),
            "疯狂": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "疯狂模式.png"
            ),
            "混音": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "混音模式.png"
            ),
            "情侣": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "情侣模式.png"
            ),
            "club": os.path.join(
                脚本目录, "UI-img", "选歌界面资源", "top栏小标题", "双踏板模式.png"
            ),
        }

        # ===== 缓存 =====
        self._top小标题原图缓存 = {}  # 路径 -> 原图
        self._top小标题缩放缓存 = {}  # (路径, 目标高, 额外缩放) -> 缩放后图

        # =========================================================
        # ✅ 手动可调参数（你要调位置/缩放就改这里）
        # =========================================================
        self._top左上_x屏宽占比 = 0.10  # ✅ 整体向右移动屏宽10%
        self._top左上_y像素 = 0  # ✅ 纵轴=0（贴top上边）
        self._top类型模式间距 = 13  # ✅ 类型图 与 模式图 之间的间距

        self._top小标题目标高占比 = (
            0.45  # 相对top栏高度的目标高度（先自动fit，再乘手动缩放）
        )
        self._top类型_缩放 = 1.10
        self._top模式_缩放 = 1.10
        self._top类型_偏移 = (0, 0)  # (dx, dy)
        self._top模式_偏移 = (0, 0)

        # 可选：按“具体类型/模式”覆盖缩放和偏移（你后面发现某张图偏大/偏小就填这里）
        self._top类型_缩放覆盖 = {}  # 例：{"派对": 0.92}
        self._top类型_偏移覆盖 = {}  # 例：{"派对": (0, 2)}
        self._top模式_缩放覆盖 = {}  # 例：{"club": 0.90}
        self._top模式_偏移覆盖 = {}  # 例：{"club": (0, 1)}

    def _归一化类型名(self, 类型名: str) -> str:
        s = str(类型名 or "").strip()
        低 = s.lower()

        if "花" in s or "fancy" in 低:
            return "花式"
        if "竞" in s or "speed" in 低:
            return "竞速"
        if "派对" in s or "party" in 低:
            return "派对"
        if "diy" in 低:
            return "diy"
        if "wef" in 低:
            return "wef"

        # 兜底：就返回原字符串（后面会走“缺图->文字”）
        return s

    def _归一化模式名(self, 模式名: str) -> str:
        s = str(模式名 or "").strip()
        低 = s.lower()

        if "表演" in s or "show" in 低:
            return "表演"
        if "学习" in s or "learn" in 低:
            return "学习"
        if "疯狂" in s or "crazy" in 低:
            return "疯狂"
        if "混音" in s or "mix" in 低:
            return "混音"
        if "情侣" in s:
            return "情侣"
        if "club" in 低 or "双踏板" in s:
            return "club"

        return s

    def _夹紧矩形到top内部(self, r: pygame.Rect) -> pygame.Rect:
        """
        保证左上角小标题永远“包裹在top背景内部”
        """
        top = getattr(self, "_top_rect", pygame.Rect(0, 0, self.宽, 100))
        rr = r.copy()

        if rr.w > top.w:
            rr.w = top.w
        if rr.h > top.h:
            rr.h = top.h

        rr.x = max(top.left, min(rr.x, top.right - rr.w))
        rr.y = max(top.top, min(rr.y, top.bottom - rr.h))
        return rr

    def _获取top小标题图(
        self,
        路径: str,
        目标高: int,
        额外缩放: float,
        最大宽: Optional[int] = None,
    ) -> Optional[pygame.Surface]:
        if not 路径 or (not os.path.isfile(路径)):
            return None

        # ✅ 全局：所有小标题图“宽度额外加宽 1.3 倍”
        全局宽度加宽 = 1.30

        最大宽值 = int(最大宽) if 最大宽 is not None else -1
        key = (路径, int(目标高), float(额外缩放), 最大宽值, float(全局宽度加宽))
        if key in self._top小标题缩放缓存:
            return self._top小标题缩放缓存.get(key)

        原图 = self._top小标题原图缓存.get(路径)
        if 原图 is None:
            try:
                原图 = pygame.image.load(路径).convert_alpha()
            except Exception:
                原图 = None
            self._top小标题原图缓存[路径] = 原图

        if 原图 is None:
            self._top小标题缩放缓存[key] = None
            return None

        ow, oh = 原图.get_size()
        if ow <= 0 or oh <= 0:
            self._top小标题缩放缓存[key] = None
            return None

        # ✅ 先按目标高 fit，再乘你的“额外缩放”
        比例 = (float(目标高) / float(oh)) * float(额外缩放)
        nw = max(1, int(ow * 比例))
        nh = max(1, int(oh * 比例))

        # ✅ 统一加宽：只改宽，不改高
        nw = max(1, int(nw * float(全局宽度加宽)))

        # ✅ 宽限制：超出可用宽就等比缩小（避免被裁切）
        if 最大宽值 and 最大宽值 > 0 and nw > 最大宽值:
            缩比 = float(最大宽值) / float(max(1, nw))
            nw = 最大宽值
            nh = max(1, int(nh * 缩比))  # 这里会影响高度（为避免裁切必须等比缩）

        try:
            缩放图 = pygame.transform.smoothscale(原图, (nw, nh)).convert_alpha()
        except Exception:
            缩放图 = None

        self._top小标题缩放缓存[key] = 缩放图
        return 缩放图

    def _重算星级筛选页布局(self):
        面板宽 = min(920, int(self.宽 * 0.78))
        面板高 = min(620, int(self.高 * 0.70))
        面板x = (self.宽 - 面板宽) // 2
        面板y = (self.高 - 面板高) // 2
        self.筛选页面板矩形 = pygame.Rect(面板x, 面板y, 面板宽, 面板高)

        self.星级按钮列表.clear()

        # ✅ 只取“当前模式目录真实存在”的星级
        原始 = self.当前原始歌曲列表()
        星集合: List[int] = []
        try:
            星集合 = sorted(
                {max(1, min(20, int(getattr(歌, "星级", 0) or 0))) for 歌 in 原始}
            )
        except Exception:
            星集合 = []

        if not 星集合:
            星集合 = [1, 2, 3, 4, 5]

        内边距 = 26
        区域 = self.筛选页面板矩形.inflate(-内边距 * 2, -内边距 * 2)

        标题区高 = 120
        可用 = pygame.Rect(
            区域.x, 区域.y + 标题区高, 区域.w, max(10, 区域.h - 标题区高)
        )

        # ✅ 统一按钮宽高（与星级数量无关，避免“只有4个星级时按钮巨大”）
        按钮宽 = max(120, min(190, int(可用.w * 0.18)))
        按钮高 = max(86, int(按钮宽 * 0.70))
        间距 = max(12, int(按钮宽 * 0.10))

        # ✅ 浮动布局：能放几列放几列，自动换行
        列数 = int((可用.w + 间距) // (按钮宽 + 间距))
        列数 = max(1, min(列数, len(星集合)))

        总数 = len(星集合)
        行数 = int(math.ceil(总数 / max(1, 列数)))

        总高 = 行数 * 按钮高 + max(0, 行数 - 1) * 间距
        起点y = 可用.y + max(0, (可用.h - 总高) // 2)

        索引 = 0
        for 行 in range(行数):
            本行剩余 = 总数 - 索引
            本行数量 = min(列数, max(0, 本行剩余))
            if 本行数量 <= 0:
                break

            本行总宽 = 本行数量 * 按钮宽 + max(0, 本行数量 - 1) * 间距
            起点x = 可用.centerx - 本行总宽 // 2

            y = 起点y + 行 * (按钮高 + 间距)
            for 列 in range(本行数量):
                星 = int(星集合[索引])
                x = 起点x + 列 * (按钮宽 + 间距)
                b = 星级筛选按钮(self, 星, pygame.Rect(x, y, 按钮宽, 按钮高))
                self.星级按钮列表.append((星, b))
                索引 += 1

    def 生成指定页卡片(self, 页码: int) -> List[歌曲卡片]:
        列表, _映射 = self.当前歌曲列表与映射()
        if not 列表:
            return []

        try:
            列数 = int(self._取布局值("卡片网格.列数", 4))
        except Exception:
            列数 = 4
        try:
            行数 = int(self._取布局值("卡片网格.行数", 2))
        except Exception:
            行数 = 2
        列数 = max(1, min(12, 列数))
        行数 = max(1, min(12, 行数))

        self.每页数量 = int(列数 * 行数)

        外留白 = self._取布局像素("卡片网格.外留白", 70, 最小=0, 最大=9999)
        上下留白 = self._取布局像素("卡片网格.上下留白", 36, 最小=0, 最大=9999)

        原间距x = self._取布局像素("卡片网格.原卡片间距x", 44, 最小=0, 最大=9999)
        原间距y = self._取布局像素("卡片网格.原卡片间距y", 26, 最小=0, 最大=9999)

        倍率x = self._取布局值("卡片网格.间距x倍率", 2.0)
        倍率y = self._取布局值("卡片网格.间距y倍率", 3.0)
        try:
            倍率x = float(倍率x)
        except Exception:
            倍率x = 2.0
        try:
            倍率y = float(倍率y)
        except Exception:
            倍率y = 3.0
        倍率x = max(0.0, min(10.0, 倍率x))
        倍率y = max(0.0, min(10.0, 倍率y))

        卡片间距x = int(原间距x * 倍率x)
        卡片间距y = int(原间距y * 倍率y)

        区域 = self.中间区域.inflate(-外留白 * 2, -上下留白 * 2)

        区域最小宽 = self._取布局像素("卡片网格.区域最小宽", 500, 最小=200, 最大=9999)
        区域最小高 = self._取布局像素("卡片网格.区域最小高", 200, 最小=120, 最大=9999)
        兜底留白 = self._取布局像素("卡片网格.区域兜底留白", 40, 最小=0, 最大=9999)

        if 区域.w < 区域最小宽 or 区域.h < 区域最小高:
            区域 = self.中间区域.inflate(-兜底留白, -兜底留白)

        原卡片宽最小 = self._取布局像素(
            "卡片网格.原卡片宽最小", 140, 最小=60, 最大=9999
        )
        原卡片高最小 = self._取布局像素(
            "卡片网格.原卡片高最小", 120, 最小=60, 最大=9999
        )

        原卡片宽 = max(原卡片宽最小, (区域.w - (列数 - 1) * 卡片间距x) // 列数)
        原卡片高 = max(原卡片高最小, (区域.h - (行数 - 1) * 卡片间距y) // 行数)

        宽缩放 = self._取布局值("卡片网格.卡片宽缩放", 0.95)
        高缩放 = self._取布局值("卡片网格.卡片高缩放", 1.00)
        try:
            宽缩放 = float(宽缩放)
        except Exception:
            宽缩放 = 0.95
        try:
            高缩放 = float(高缩放)
        except Exception:
            高缩放 = 1.00
        宽缩放 = max(0.30, min(1.50, 宽缩放))
        高缩放 = max(0.30, min(1.50, 高缩放))

        卡片宽最小 = self._取布局像素("卡片网格.卡片宽最小", 120, 最小=40, 最大=9999)
        卡片高最小 = self._取布局像素("卡片网格.卡片高最小", 110, 最小=40, 最大=9999)

        卡片宽 = max(卡片宽最小, int(原卡片宽 * 宽缩放))
        卡片高 = max(卡片高最小, int(原卡片高 * 高缩放))

        起始索引 = int(页码) * int(self.每页数量)
        卡片列表: List[歌曲卡片] = []

        整块宽 = 列数 * 卡片宽 + (列数 - 1) * 卡片间距x
        整块高 = 行数 * 卡片高 + (行数 - 1) * 卡片间距y

        起点x = 区域.centerx - 整块宽 // 2
        起点y = 区域.centery - 整块高 // 2

        上移占比 = self._取布局值("卡片网格.整体上移占比", 0.05)
        try:
            上移占比 = float(上移占比)
        except Exception:
            上移占比 = 0.05
        上移占比 = max(-0.50, min(0.50, 上移占比))
        起点y -= int(区域.h * 上移占比)

        for 行 in range(行数):
            for 列 in range(列数):
                相对 = 行 * 列数 + 列
                视图索引 = 起始索引 + 相对
                if 视图索引 >= len(列表):
                    continue

                x = 起点x + 列 * (卡片宽 + 卡片间距x)
                y = 起点y + 行 * (卡片高 + 卡片间距y)
                卡片列表.append(
                    歌曲卡片(列表[视图索引], pygame.Rect(x, y, 卡片宽, 卡片高))
                )

        return 卡片列表

    def 打开模式选择页(self):
        if self.是否详情页 or self.是否星级筛选页 or self.动画中:
            return
        self.是否模式选择页 = True

    def 关闭模式选择页(self):
        self.是否模式选择页 = False

    def _切换到类型(self, 目标类型关键字: str):
        """
        目标类型关键字：'花式' 或 '竞速'
        尽量在 self.类型列表 中找到匹配项并切换。
        """
        if not self.类型列表:
            return

        def _归一(s: str) -> str:
            return re.sub(r"\s+", "", str(s or "")).strip().lower()

        关键 = _归一(目标类型关键字)
        命中索引 = None

        for i, t in enumerate(self.类型列表):
            if 关键 in _归一(t):
                命中索引 = i
                break

        # 兜底：常见英文命名
        if 命中索引 is None:
            if 关键 == _归一("花式"):
                备选 = ["fancy"]
            else:
                备选 = ["speed"]
            for i, t in enumerate(self.类型列表):
                tt = _归一(t)
                if any(b in tt for b in 备选):
                    命中索引 = i
                    break

        if 命中索引 is None:
            return

        self.当前类型索引 = 命中索引

        当前类型 = self.当前类型名()
        self.模式列表 = sorted(self.数据树.get(当前类型, {}).keys())
        self.当前模式索引 = 0

        # 重置筛选/页码/卡片
        self.当前筛选星级 = None
        self.当前页 = 0
        self.当前页卡片 = self.生成指定页卡片(self.当前页)
        self.安排预加载(基准页=self.当前页)

    def 绘制模式选择页(self):
        # 半透明遮罩
        暗层 = pygame.Surface((self.宽, self.高), pygame.SRCALPHA)
        暗层.fill((0, 0, 0, 180))
        self.屏幕.blit(暗层, (0, 0))

        面板 = self.模式选择面板矩形
        面板底 = pygame.Surface((面板.w, 面板.h), pygame.SRCALPHA)
        面板底.fill((10, 20, 40, 230))
        self.屏幕.blit(面板底, 面板.topleft)
        绘制圆角矩形(self.屏幕, 面板, (180, 220, 255), 圆角=18, 线宽=3)

        绘制超粗文本(
            self.屏幕,
            "选择模式",
            获取字体(40),
            (255, 240, 80),
            (面板.centerx, 面板.y + 52),
            对齐="center",
            粗细=3,
        )

        self.按钮_选择花式.绘制(self.屏幕, 获取字体(34))
        self.按钮_选择竞速.绘制(self.屏幕, 获取字体(34))
        self.按钮_关闭模式选择.绘制(self.屏幕, 获取字体(26))

    # -------------------------
    # 懒加载 + 延迟清理
    # -------------------------

    def _计算保留key集合(self, 基准页: int) -> Set[Tuple[str, int, int, int, str]]:
        列表, _映射 = self.当前歌曲列表与映射()
        if not 列表:
            return set()

        try:
            总页 = int(self.总页数())
        except Exception:
            总页 = 1
        if 总页 <= 0:
            总页 = 1

        页集合: List[int] = []
        for 偏移 in (-1, 0, 1, 2):
            p = int(基准页) + int(偏移)
            if 0 <= p < 总页:
                页集合.append(p)

        需要key集合: Set[Tuple[str, int, int, int, str]] = set()

        屏宽, 屏高 = self.屏幕.get_size()

        # ✅ 缩略图封面：严格按“绘制时的参数”来算
        封面缩放模式 = (
            str(取选歌布局值("缩略图.封面.缩放模式", "contain") or "contain")
            .strip()
            .lower()
        )
        if 封面缩放模式 not in ("contain", "cover"):
            封面缩放模式 = "contain"

        封面圆角 = 取选歌布局像素("缩略图.封面.圆角", 0, 屏宽, 屏高, 最小=0, 最大=200)

        框宽缩放 = 取选歌布局值("缩略图.框.宽缩放", 0.97)
        框高缩放 = 取选歌布局值("缩略图.框.高缩放", 1.05)
        try:
            框宽缩放 = float(框宽缩放)
        except Exception:
            框宽缩放 = 0.97
        try:
            框高缩放 = float(框高缩放)
        except Exception:
            框高缩放 = 1.05
        框宽缩放 = max(0.20, min(3.0, 框宽缩放))
        框高缩放 = max(0.20, min(3.0, 框高缩放))

        框x偏移 = 取选歌布局像素(
            "缩略图.框.x偏移", 0, 屏宽, 屏高, 最小=-99999, 最大=99999
        )
        框y偏移 = 取选歌布局像素(
            "缩略图.框.y偏移", 0, 屏宽, 屏高, 最小=-99999, 最大=99999
        )

        for 页码 in 页集合:
            卡片列表 = self.生成指定页卡片(int(页码))
            for 卡片 in 卡片列表:
                try:
                    路径 = str(getattr(卡片.歌曲, "封面路径", "") or "")
                except Exception:
                    路径 = ""
                if (not 路径) or (not os.path.isfile(路径)):
                    continue

                # ✅ 复刻 歌曲卡片.绘制() 里“边框锚点矩形”的计算（不做任何 blit）
                try:
                    框绘制宽 = max(1, int(卡片.矩形.w * 框宽缩放))
                    框绘制高 = max(1, int(卡片.矩形.h * 框高缩放))
                    框x = int(卡片.矩形.x + 框x偏移)
                    框y = int(卡片.矩形.y + 框y偏移)
                    边框锚点矩形 = pygame.Rect(框x, 框y, 框绘制宽, 框绘制高)
                except Exception:
                    边框锚点矩形 = 卡片.矩形

                # ✅ 直接调用卡片内部的封面矩形算法（这样尺寸和绘制一致）
                try:
                    封面矩形 = 卡片._计算封面矩形(边框锚点矩形, 屏宽, 屏高)
                except Exception:
                    封面矩形 = 卡片.矩形

                w = max(1, int(封面矩形.w))
                h = max(1, int(封面矩形.h))
                需要key集合.add((路径, w, h, int(封面圆角), str(封面缩放模式)))

        # ✅ 详情页：预加载当前大图封面（尽量贴近绘制时用的封面框尺寸）
        if bool(getattr(self, "是否详情页", False)):
            原始 = self.当前原始歌曲列表()
            try:
                当前索引 = int(getattr(self, "当前选择原始索引", 0) or 0)
            except Exception:
                当前索引 = 0

            if 0 <= 当前索引 < len(原始):
                歌 = 原始[当前索引]
                try:
                    大图路径 = str(getattr(歌, "封面路径", "") or "")
                except Exception:
                    大图路径 = ""

                if 大图路径 and os.path.isfile(大图路径):
                    # 用“当前详情浮层的缩放”反推基础尺寸，尽量命中缓存
                    try:
                        当前大框 = getattr(self, "详情大框矩形", None)
                        if not isinstance(当前大框, pygame.Rect):
                            当前大框 = None
                    except Exception:
                        当前大框 = None

                    try:
                        最后缩放 = float(
                            getattr(self, "_详情浮层_最后缩放", 1.0) or 1.0
                        )
                    except Exception:
                        最后缩放 = 1.0
                    最后缩放 = max(0.001, 最后缩放)

                    if 当前大框 is not None and 当前大框.w > 10 and 当前大框.h > 10:
                        基础宽 = max(10, int(round(float(当前大框.w) / 最后缩放)))
                        基础高 = max(10, int(round(float(当前大框.h) / 最后缩放)))

                        内边距占比 = self._取布局值("详情大图.封面.内边距占比", 0.01)
                        try:
                            内边距占比 = float(内边距占比)
                        except Exception:
                            内边距占比 = 0.01
                        内边距占比 = max(0.0, min(0.20, 内边距占比))

                        内边距最小 = self._取布局像素(
                            "详情大图.封面.内边距最小", 10, 最小=0, 最大=99999
                        )
                        内边距 = max(
                            int(内边距最小), int(min(基础宽, 基础高) * 内边距占比)
                        )

                        封面框 = pygame.Rect(0, 0, 基础宽, 基础高).inflate(
                            -内边距 * 2, -内边距 * 2
                        )

                        大图缩放模式 = (
                            str(
                                self._取布局值("详情大图.封面.缩放模式", "contain")
                                or "contain"
                            )
                            .strip()
                            .lower()
                        )
                        if 大图缩放模式 not in ("contain", "cover"):
                            大图缩放模式 = "contain"
                        大图圆角 = self._取布局像素(
                            "详情大图.封面.圆角", 0, 最小=0, 最大=200
                        )

                        需要key集合.add(
                            (
                                大图路径,
                                max(1, 封面框.w),
                                max(1, 封面框.h),
                                int(大图圆角),
                                str(大图缩放模式),
                            )
                        )

        return 需要key集合

    def 安排预加载(self, 基准页: int):
        列表, _映射 = self.当前歌曲列表与映射()
        if not 列表:
            return

        # ✅ 懒初始化：已排队集合（避免重复排队）
        if not hasattr(self, "_预加载_已排队"):
            self._预加载_已排队 = set()

        需要key集合 = self._计算保留key集合(int(基准页))

        for 路径, w, h, 圆角, 模式 in list(需要key集合):
            缓存键 = (路径, int(w), int(h), int(圆角), str(模式))
            if self.图缓存.获取(路径, w, h, 圆角, 模式) is None:
                if 缓存键 not in self._预加载_已排队:
                    self.预加载队列.append((路径, w, h, 圆角, 模式))
                    self._预加载_已排队.add(缓存键)

        self._待清理保留key集合 = 需要key集合

        if not self.预加载队列 and self._待清理保留key集合 is not None:
            self.图缓存.清理远端(self._待清理保留key集合)
            self._待清理保留key集合 = None

    def 每帧执行预加载(self, 每帧数量: int = 3):
        if not hasattr(self, "_预加载_已排队"):
            self._预加载_已排队 = set()

        try:
            每帧数量 = int(每帧数量)
        except Exception:
            每帧数量 = 3
        每帧数量 = max(1, min(30, 每帧数量))

        for _ in range(每帧数量):
            if not self.预加载队列:
                break

            # ✅ O(1)：从队尾弹出
            路径, w, h, 圆角, 模式 = self.预加载队列.pop()

            try:
                self._预加载_已排队.discard(
                    (路径, int(w), int(h), int(圆角), str(模式))
                )
            except Exception:
                pass

            if self.图缓存.获取(路径, w, h, 圆角, 模式) is not None:
                continue

            图 = 载入并缩放封面(路径, w, h, 圆角, 模式)
            if 图:
                self.图缓存.写入(路径, w, h, 圆角, 模式, 图)

        if (not self.预加载队列) and (self._待清理保留key集合 is not None):
            self.图缓存.清理远端(self._待清理保留key集合)
            self._待清理保留key集合 = None

    # -------------------------
    # 翻页动画
    # -------------------------
    def 触发翻页动画(self, 目标页: int, 方向: int):
        if self.动画中 or self.是否星级筛选页:
            return

        总 = self.总页数()
        if 总 <= 1:
            return

        try:
            目标页 = int(目标页)
        except Exception:
            目标页 = self.当前页

        # ✅ 环绕：第一页往上滚/右滑 -> 末页；末页往下滚/左滑 -> 首页
        if 目标页 < 0:
            目标页 = 总 - 1
        elif 目标页 >= 总:
            目标页 = 0

        if 目标页 == self.当前页:
            return

        self.动画中 = True
        self.动画开始时间 = time.time()
        self.动画方向 = (
            int(方向) if int(方向) != 0 else (1 if 目标页 > self.当前页 else -1)
        )
        self.动画目标页 = 目标页

        self.动画旧页卡片 = self.生成指定页卡片(self.当前页)
        self.动画新页卡片 = self.生成指定页卡片(self.动画目标页)

        self.安排预加载(基准页=self.动画目标页)

    def 更新动画状态(self):
        if not self.动画中:
            return
        经过 = time.time() - self.动画开始时间
        if 经过 >= self.动画持续:
            self.动画中 = False
            self.当前页 = self.动画目标页
            self.当前页卡片 = self.生成指定页卡片(self.当前页)
            self.安排预加载(基准页=self.当前页)

    def _取当前视图索引(self, 映射: List[int]) -> int:
        try:
            return int(映射.index(int(self.当前选择原始索引)))
        except Exception:
            return 0

    def _详情切到视图索引(self, 目标视图索引: int, 方向: int):
        列表, 映射 = self.当前歌曲列表与映射()
        if not 映射:
            return

        n = len(映射)
        try:
            目标视图索引 = int(目标视图索引) % n
        except Exception:
            目标视图索引 = 0

        新原始索引 = int(映射[目标视图索引])
        原始 = self.当前原始歌曲列表()
        if not 原始:
            return

        新原始索引 = max(0, min(新原始索引, len(原始) - 1))
        self.当前选择原始索引 = 新原始索引
        self._踏板选中视图索引 = int(目标视图索引)

        # ✅ 播放预览
        try:
            歌 = 原始[self.当前选择原始索引]
            self.播放歌曲mp3(getattr(歌, "mp3路径", None))
        except Exception:
            pass

        # ✅ 同步底下缩略图页码（必要时触发翻页）
        目标页 = int(目标视图索引 // int(self.每页数量))

        if bool(getattr(self, "动画中", False)):
            # 防御：如果正在动画，强制收敛状态，避免“动画锁死导致详情切歌不同步页码”
            try:
                self.动画中 = False
                self.当前页 = int(getattr(self, "动画目标页", self.当前页))
                self.当前页卡片 = self.生成指定页卡片(self.当前页)
            except Exception:
                pass

        if 目标页 != int(self.当前页):
            # 只要跨页，就翻（满足你“第8首下一首要翻页”）
            self.触发翻页动画(目标页=目标页, 方向=int(方向))
        else:
            # 同页也预加载一下，避免大图切歌时封面没进缓存
            self.安排预加载(基准页=self.当前页)

    # -------------------------
    # 星级筛选页控制
    # -------------------------

    def 打开星级筛选页(self):
        if self.是否详情页:
            return
        self.是否星级筛选页 = True

    def 关闭星级筛选页(self):
        self.是否星级筛选页 = False

    def 设置星级筛选(self, 星级: Optional[int]):
        self.当前筛选星级 = 星级
        self.当前页 = 0
        self.当前页卡片 = self.生成指定页卡片(self.当前页)
        self.安排预加载(基准页=self.当前页)

    # -------------------------
    # 详情页控制
    # -------------------------

    def 进入详情_原始索引(self, 原始索引: int):
        原始 = self.当前原始歌曲列表()
        if not 原始:
            return

        self.当前选择原始索引 = max(0, min(原始索引, len(原始) - 1))
        self.是否详情页 = True
        try:
            _列表, 映射 = self.当前歌曲列表与映射()
            self._踏板选中视图索引 = int(映射.index(self.当前选择原始索引))
        except Exception:
            self._踏板选中视图索引 = None

        # ✅ 改：第一次点击就播，所以不需要“点击次数”
        # 只重置“上次播放时间”，防止刚切歌立刻点被节流
        self._大图确认_上次触发时间 = 0.0

        # ✅ 记录“浮动大图入场动画”开始时间（0.5秒）
        try:
            self._浮动大图入场开始毫秒 = int(pygame.time.get_ticks())
        except Exception:
            self._浮动大图入场开始毫秒 = 0
        self._浮动大图入场时长毫秒 = 500

        歌 = 原始[self.当前选择原始索引]
        self.播放歌曲mp3(歌.mp3路径)

        self.安排预加载(基准页=self.当前页)

    def 返回列表(self):
        self.是否详情页 = False
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.确保播放背景音乐()

        # 返回时定位到该歌所在页（基于“当前视图列表”）
        列表, 映射 = self.当前歌曲列表与映射()
        if 映射:
            try:
                视图索引 = 映射.index(self.当前选择原始索引)
            except Exception:
                视图索引 = 0
            self.当前页 = max(0, 视图索引 // self.每页数量)
            self._踏板选中视图索引 = int(视图索引)
        else:
            self.当前页 = 0
            self._踏板选中视图索引 = None

        self.当前页卡片 = self.生成指定页卡片(self.当前页)
        self.安排预加载(基准页=self.当前页)
        self._同步踏板卡片高亮()

    def 下一首(self):
        列表, 映射 = self.当前歌曲列表与映射()
        if not 映射:
            return

        当前视图索引 = self._取当前视图索引(映射)
        目标视图索引 = (当前视图索引 + 1) % len(映射)
        self._详情切到视图索引(目标视图索引, 方向=+1)

    def 上一首(self):
        列表, 映射 = self.当前歌曲列表与映射()
        if not 映射:
            return

        当前视图索引 = self._取当前视图索引(映射)
        目标视图索引 = (当前视图索引 - 1) % len(映射)
        self._详情切到视图索引(目标视图索引, 方向=-1)

    def _同步踏板卡片高亮(self):
        基准视图索引 = getattr(self, "_踏板选中视图索引", None)
        for idx, 卡片 in enumerate(getattr(self, "当前页卡片", []) or []):
            try:
                视图索引 = int(self.当前页) * int(self.每页数量) + int(idx)
                卡片.踏板高亮 = (
                    基准视图索引 is not None and int(基准视图索引) == 视图索引
                )
            except Exception:
                try:
                    卡片.踏板高亮 = False
                except Exception:
                    pass

    def _踏板选中缩略图(self, 方向步进: int):
        if bool(getattr(self, "动画中", False)) or bool(
            getattr(self, "是否设置页", False)
        ):
            return None
        if bool(getattr(self, "是否星级筛选页", False)):
            return None

        列表, 映射 = self.当前歌曲列表与映射()
        if not 映射:
            return None

        if bool(getattr(self, "是否详情页", False)):
            try:
                self._播放按钮音效()
            except Exception:
                pass
            if int(方向步进) < 0:
                self.上一首()
            else:
                self.下一首()
            return None

        当前视图索引 = getattr(self, "_踏板选中视图索引", None)
        if 当前视图索引 is None:
            当前视图索引 = int(self.当前页) * int(self.每页数量)
            当前视图索引 = max(0, min(int(当前视图索引), len(映射) - 1))
        else:
            当前视图索引 = (int(当前视图索引) + int(方向步进)) % len(映射)

        self._踏板选中视图索引 = int(当前视图索引)
        self.当前页 = int(
            max(0, min(len(映射) - 1, 当前视图索引)) // max(1, int(self.每页数量))
        )
        self.当前页卡片 = self.生成指定页卡片(self.当前页)
        self.安排预加载(基准页=self.当前页)
        self._同步踏板卡片高亮()

        try:
            self.当前选择原始索引 = int(映射[int(当前视图索引)])
        except Exception:
            pass

        try:
            self._播放按钮音效()
        except Exception:
            pass
        return None

    def _踏板确认当前歌曲(self):
        if bool(getattr(self, "动画中", False)) or bool(
            getattr(self, "是否设置页", False)
        ):
            return None
        if bool(getattr(self, "是否星级筛选页", False)):
            return None

        if bool(getattr(self, "是否详情页", False)):
            self._启动过渡(
                self._特效_大图确认,
                self.详情大框矩形,
                self._记录并处理大图确认点击,
            )
            return None

        列表, 映射 = self.当前歌曲列表与映射()
        if not 映射:
            return None

        当前视图索引 = getattr(self, "_踏板选中视图索引", None)
        if 当前视图索引 is None:
            当前视图索引 = int(self.当前页) * int(self.每页数量)
        当前视图索引 = max(0, min(int(当前视图索引), len(映射) - 1))

        页内索引 = int(当前视图索引) - int(self.当前页) * int(self.每页数量)
        if not (0 <= 页内索引 < len(self.当前页卡片)):
            self._踏板选中视图索引 = int(当前视图索引)
            self._同步踏板卡片高亮()
            return None

        try:
            原始索引 = int(映射[int(当前视图索引)])
        except Exception:
            原始索引 = 0
        卡片 = self.当前页卡片[int(页内索引)]
        self._踏板选中视图索引 = int(当前视图索引)
        self._同步踏板卡片高亮()
        self._启动过渡(
            self._特效_按钮,
            卡片.矩形,
            lambda: self.进入详情_原始索引(int(原始索引)),
        )
        return None

    def 处理全局踏板(self, 动作: str):
        try:
            self._确保公共交互()
        except Exception:
            pass
        try:
            if (
                getattr(self, "_过渡_特效", None) is not None
                and self._过渡_特效.是否动画中()
            ):
                return None
        except Exception:
            pass
        if 动作 == 踏板动作_左:
            return self._踏板选中缩略图(-1)
        if 动作 == 踏板动作_右:
            return self._踏板选中缩略图(+1)
        if 动作 == 踏板动作_确认:
            return self._踏板确认当前歌曲()
        return None

    # -------------------------
    # 绘制
    # -------------------------

    def 绘制背景(self):
        if self.背景图_原图 is not None:
            目标尺寸 = (self.宽, self.高)
            if self.背景图_缩放缓存 is None or self.背景图_缩放尺寸 != 目标尺寸:
                try:
                    self.背景图_缩放缓存 = pygame.transform.smoothscale(
                        self.背景图_原图, 目标尺寸
                    )
                    self.背景图_缩放尺寸 = 目标尺寸
                except Exception:
                    self.背景图_缩放缓存 = None
                    self.背景图_缩放尺寸 = (0, 0)

            if self.背景图_缩放缓存 is not None:
                self.屏幕.blit(self.背景图_缩放缓存, (0, 0))
            else:
                self.屏幕.fill((10, 10, 18))
        else:
            self.屏幕.fill((10, 10, 18))

        # 轻微暗化遮罩：保证文字可读
        暗层 = pygame.Surface((self.宽, self.高), pygame.SRCALPHA)
        暗层.fill((0, 0, 0, 60))
        self.屏幕.blit(暗层, (0, 0))

    def 绘制顶部(self):
        self._确保top栏缓存()

        # 1) top背景
        if self._top图:
            self.屏幕.blit(self._top图, self._top_rect.topleft)
        else:
            pygame.draw.rect(self.屏幕, (20, 40, 80), self._top_rect)

        # 2) 中间标题（歌曲选择.png）
        if getattr(self, "_top标题图", None) is not None:
            self.屏幕.blit(self._top标题图, self._top标题rect.topleft)

        # 3) 左上角：类型 + 模式（优先图片，缺图退文字；y=0；x=屏宽10%）
        self._绘制顶部左上类型模式()

    def 绘制底部(self):
        self._确保公共交互()

        # ✅ 底部图文按钮统一字号（重开除外）
        try:
            参考宽 = (
                int(self.按钮_歌曲分类.矩形.w)
                if hasattr(self, "按钮_歌曲分类")
                else 160
            )
            标签字号 = max(14, int(参考宽 * 0.16))
        except Exception:
            标签字号 = 22
        底部标签字体 = 获取字体(标签字号, 是否粗体=True)

        # 歌曲分类
        if isinstance(self.按钮_歌曲分类, 底部图文按钮):
            self.按钮_歌曲分类.绘制(self.屏幕, 底部标签字体)
        else:
            self.按钮_歌曲分类.绘制(self.屏幕, 底部标签字体)

        # ALL（只画图）
        if isinstance(self.按钮_ALL, 图片按钮):
            self.按钮_ALL.绘制(self.屏幕)
        else:
            self.按钮_ALL.绘制(self.屏幕, 底部标签字体)

        # 重开（例外：走你自己的按钮样式）
        重选字号 = max(12, int(self.按钮_重选模式.矩形.h * 0.26))
        self.按钮_重选模式.绘制(self.屏幕, 获取字体(重选字号, 是否粗体=True))

        # P加入（会在重算布局里根据玩家数切成 1P加入/2P加入）
        if isinstance(self.按钮_2P加入, 底部图文按钮):
            self.按钮_2P加入.绘制(self.屏幕, 底部标签字体)
        else:
            self.按钮_2P加入.绘制(self.屏幕, 底部标签字体)

        # 设置
        if isinstance(self.按钮_设置, 底部图文按钮):
            self.按钮_设置.绘制(self.屏幕, 底部标签字体)
        else:
            self.按钮_设置.绘制(self.屏幕, 底部标签字体)

        # ✅ 公共函数：联网状态图标（放底部中间，不挤左右按钮）
        try:
            from core.工具 import 绘制底部联网与信用

            联网原图 = self._获取联网原图_尽力()
            字体_credit = 获取字体(max(14, int(标签字号 * 1.3)), 是否粗体=False)

            # credit数值这里先给个占位（你后面接真实 credit 再改）
            绘制底部联网与信用(
                屏幕=self.屏幕,
                联网原图=联网原图,
                字体_credit=字体_credit,
                credit数值=str(int(self.上下文.get("状态", {}).get("投币数", 0) or 0)),
            )
        except Exception:
            pass

    def _绘制顶部左上类型模式(self):
        self._确保top栏资源()

        屏宽, _屏高 = self.屏幕.get_size()
        顶栏矩形 = self._top_rect

        起始x = 顶栏矩形.left + int(屏宽 * float(self._top左上_x屏宽占比))
        起始y = 顶栏矩形.top + int(self._top左上_y像素)

        目标高 = max(1, int(顶栏矩形.h * float(self._top小标题目标高占比)))

        类型名 = self._归一化类型名(self.当前类型名())
        模式名 = self._归一化模式名(self.当前模式名())

        # ===== 类型 =====
        类型路径 = self._top类型图片路径表.get(类型名, "")
        类型缩放 = float(self._top类型_缩放覆盖.get(类型名, self._top类型_缩放))
        类型偏移 = self._top类型_偏移覆盖.get(类型名, self._top类型_偏移)

        x = 起始x + int(类型偏移[0])
        y = 起始y + int(类型偏移[1])

        类型图 = None
        if 类型路径:
            可用宽 = max(1, 顶栏矩形.right - x)
            类型图 = self._获取top小标题图(类型路径, 目标高, 类型缩放, 最大宽=可用宽)

        if 类型图 is not None:
            类型矩形 = 类型图.get_rect(topleft=(x, y))
            类型矩形 = self._夹紧矩形到top内部(类型矩形)
            self.屏幕.blit(类型图, 类型矩形.topleft)
            x = 类型矩形.right + int(self._top类型模式间距)
        else:
            字体 = 获取字体(26, 是否粗体=False)
            文面 = 字体.render(str(类型名 or ""), True, (255, 255, 255))
            文矩形 = 文面.get_rect(topleft=(x, y))
            文矩形 = self._夹紧矩形到top内部(文矩形)
            self.屏幕.blit(文面, 文矩形.topleft)
            x = 文矩形.right + int(self._top类型模式间距)

        # ===== 模式 =====
        模式路径 = self._top模式图片路径表.get(模式名, "")
        模式缩放 = float(self._top模式_缩放覆盖.get(模式名, self._top模式_缩放))
        模式偏移 = self._top模式_偏移覆盖.get(模式名, self._top模式_偏移)

        x2 = x + int(模式偏移[0])
        y2 = 起始y + int(模式偏移[1])

        模式图 = None
        if 模式路径:
            可用宽2 = max(1, 顶栏矩形.right - x2)
            模式图 = self._获取top小标题图(模式路径, 目标高, 模式缩放, 最大宽=可用宽2)

        if 模式图 is not None:
            模式矩形 = 模式图.get_rect(topleft=(x2, y2))
            模式矩形 = self._夹紧矩形到top内部(模式矩形)
            self.屏幕.blit(模式图, 模式矩形.topleft)
        else:
            字体 = 获取字体(26, 是否粗体=False)
            文面 = 字体.render(str(模式名 or ""), True, (255, 255, 255))
            文矩形 = 文面.get_rect(topleft=(x2, y2))
            文矩形 = self._夹紧矩形到top内部(文矩形)
            self.屏幕.blit(文面, 文矩形.topleft)

    def 绘制列表页(self):
        列表, _映射 = self.当前歌曲列表与映射()
        if not 列表:
            try:
                字体 = 获取字体(28)
                文面 = 字体.render(
                    "没有扫描到歌曲，请检查歌曲目录songs文件夹，点击重开按钮退出当前模式",
                    True,
                    (255, 255, 255),
                )
                文r = 文面.get_rect(center=(self.宽 // 2, self.顶部高 + 90))
                self.屏幕.blit(文面, 文r.topleft)
            except Exception:
                pass
            return

        self._同步踏板卡片高亮()

        # ✅ 关键修复：第二个参数是字体，第三个参数才是图缓存
        for 卡片 in self.当前页卡片:
            卡片.绘制(self.屏幕, self.小字体, self.图缓存)

    def 绘制列表页_动画(self):
        t = (time.time() - self.动画开始时间) / self.动画持续
        t = max(0.0, min(1.0, t))
        t2 = t * t * (3 - 2 * t)

        dx = int(self.中间区域.w * t2) * self.动画方向
        旧偏移 = -dx
        新偏移 = self.中间区域.w - dx if self.动画方向 > 0 else -self.中间区域.w - dx

        for 卡片 in self.动画旧页卡片:
            矩形 = 卡片.矩形.move(旧偏移, 0)
            临时卡 = 歌曲卡片(卡片.歌曲, 矩形)
            # ✅ 关键修复：第二个参数是字体，第三个参数才是图缓存
            临时卡.绘制(self.屏幕, self.小字体, self.图缓存)

        for 卡片 in self.动画新页卡片:
            矩形 = 卡片.矩形.move(新偏移, 0)
            临时卡 = 歌曲卡片(卡片.歌曲, 矩形)
            # ✅ 关键修复：第二个参数是字体，第三个参数才是图缓存
            临时卡.绘制(self.屏幕, self.小字体, self.图缓存)

    def 绘制详情浮层(self):
        原始 = self.当前原始歌曲列表()
        if not 原始:
            return
        歌 = 原始[self.当前选择原始索引]

        def _夹紧(x: float, a: float, b: float) -> float:
            return a if x < a else (b if x > b else x)

        def _缓出(t: float) -> float:
            t = _夹紧(t, 0.0, 1.0)
            return 1.0 - (1.0 - t) * (1.0 - t)

        # ========= JSON：详情大图基础参数 =========
        详情浮层整体缩放 = self._取布局值("详情大图.整体缩放", 1.2)
        try:
            详情浮层整体缩放 = float(详情浮层整体缩放)
        except Exception:
            详情浮层整体缩放 = 1.2
        详情浮层整体缩放 = max(0.10, min(3.00, 详情浮层整体缩放))

        目标比例 = self._取布局值("详情大图.目标比例", 512 / 384)
        try:
            目标比例 = float(目标比例)
        except Exception:
            目标比例 = 512 / 384
        目标比例 = max(0.20, min(5.0, 目标比例))

        可用宽占比 = self._取布局值("详情大图.可用宽占比", 0.78)
        可用高占比 = self._取布局值("详情大图.可用高占比", 0.82)
        try:
            可用宽占比 = float(可用宽占比)
        except Exception:
            可用宽占比 = 0.78
        try:
            可用高占比 = float(可用高占比)
        except Exception:
            可用高占比 = 0.82
        可用宽占比 = max(0.20, min(0.98, 可用宽占比))
        可用高占比 = max(0.20, min(0.98, 可用高占比))

        最小宽 = self._取布局像素("详情大图.最小宽", 480, 最小=200, 最大=99999)
        最小高 = self._取布局像素("详情大图.最小高", 360, 最小=200, 最大=99999)

        可用宽 = int(self.中间区域.w * 可用宽占比)
        可用高 = int(self.中间区域.h * 可用高占比)

        基准宽 = min(可用宽, int(可用高 * 目标比例))
        基准宽 = min(可用宽, max(int(最小宽), 基准宽))
        基准高 = int(基准宽 / 目标比例)
        基准高 = min(可用高, max(int(最小高), 基准高))

        可用缩放上限_w = float(可用宽) / float(max(1, 基准宽))
        可用缩放上限_h = float(可用高) / float(max(1, 基准高))
        最终缩放 = min(详情浮层整体缩放, 可用缩放上限_w, 可用缩放上限_h)
        最终缩放 = max(0.10, 最终缩放)

        目标宽 = int(基准宽 * 最终缩放)
        目标高 = int(目标宽 / 目标比例)

        if 目标宽 > 可用宽:
            目标宽 = 可用宽
            目标高 = int(目标宽 / 目标比例)
        if 目标高 > 可用高:
            目标高 = 可用高
            目标宽 = int(目标高 * 目标比例)

        大框基础 = pygame.Rect(0, 0, int(目标宽), int(目标高))
        大框基础.center = (self.中间区域.centerx, self.中间区域.centery)

        # ========= 入场动画 =========
        现在毫秒 = 0
        try:
            现在毫秒 = int(pygame.time.get_ticks())
        except Exception:
            现在毫秒 = 0

        开始毫秒 = int(getattr(self, "_浮动大图入场开始毫秒", 0) or 0)
        时长毫秒 = int(getattr(self, "_浮动大图入场时长毫秒", 500) or 500)

        t = 1.0
        if 开始毫秒 > 0 and 时长毫秒 > 0:
            t = (现在毫秒 - 开始毫秒) / max(1, 时长毫秒)
            t = _夹紧(t, 0.0, 1.0)

        if t < 0.6:
            k1 = t / 0.6
            scale动画 = 0.92 + (1.06 - 0.92) * _缓出(k1)
        else:
            k2 = (t - 0.6) / 0.4
            scale动画 = 1.06 + (1.00 - 1.06) * _缓出(k2)

        alpha动画 = int(255 * _缓出(t))
        alpha动画 = max(0, min(255, alpha动画))

        # ✅ 记录下来，给“徽标叠加绘制（z轴超边框）”用
        self._详情浮层_alpha = int(alpha动画)
        self._详情浮层_最后缩放 = float(scale动画)

        # ========= 浮层绘制（局部坐标）=========
        浮层 = pygame.Surface((大框基础.w, 大框基础.h), pygame.SRCALPHA)

        # 框图（缩略图大）：支持等比缩放模式
        大框路径 = _资源路径("UI-img", "选歌界面资源", "缩略图大.png")

        框宽缩放 = self._取布局值("详情大图.框.宽缩放", 1.0)
        框高缩放 = self._取布局值("详情大图.框.高缩放", 1.0)
        try:
            框宽缩放 = float(框宽缩放)
        except Exception:
            框宽缩放 = 1.0
        try:
            框高缩放 = float(框高缩放)
        except Exception:
            框高缩放 = 1.0
        框宽缩放 = max(0.20, min(3.0, 框宽缩放))
        框高缩放 = max(0.20, min(3.0, 框高缩放))

        框绘制宽 = max(1, int(大框基础.w * 框宽缩放))
        框绘制高 = max(1, int(大框基础.h * 框高缩放))

        框x偏移 = self._取布局像素("详情大图.框.x偏移", 0, 最小=-99999, 最大=99999)
        框y偏移 = self._取布局像素("详情大图.框.y偏移", 0, 最小=-99999, 最大=99999)

        框缩放模式 = (
            str(self._取布局值("详情大图.框.缩放模式", "stretch") or "stretch")
            .strip()
            .lower()
        )
        大框图2 = 获取UI容器图(
            大框路径, 框绘制宽, 框绘制高, 缩放模式=框缩放模式, 透明=True
        )

        # 封面框（基于“局部大框”）
        内边距占比 = self._取布局值("详情大图.封面.内边距占比", 0.01)
        try:
            内边距占比 = float(内边距占比)
        except Exception:
            内边距占比 = 0.01
        内边距占比 = max(0.0, min(0.20, 内边距占比))

        内边距最小 = self._取布局像素(
            "详情大图.封面.内边距最小", 10, 最小=0, 最大=99999
        )
        内边距 = max(int(内边距最小), int(min(大框基础.w, 大框基础.h) * 内边距占比))

        封面框 = pygame.Rect(0, 0, 大框基础.w, 大框基础.h).inflate(
            -内边距 * 2, -内边距 * 2
        )

        封面缩放模式 = (
            str(self._取布局值("详情大图.封面.缩放模式", "contain") or "contain")
            .strip()
            .lower()
        )
        if 封面缩放模式 not in ("contain", "cover"):
            封面缩放模式 = "contain"
        封面圆角 = self._取布局像素("详情大图.封面.圆角", 0, 最小=0, 最大=200)

        # 1) 封面
        封面图 = None
        if 歌.封面路径 and os.path.isfile(歌.封面路径):
            封面图 = self.图缓存.获取(
                歌.封面路径, 封面框.w, 封面框.h, int(封面圆角), 封面缩放模式
            )
            if 封面图 is None:
                封面图 = 载入并缩放封面(
                    歌.封面路径, 封面框.w, 封面框.h, int(封面圆角), 封面缩放模式
                )
                if 封面图 is not None:
                    self.图缓存.写入(
                        歌.封面路径,
                        封面框.w,
                        封面框.h,
                        int(封面圆角),
                        封面缩放模式,
                        封面图,
                    )

        if 封面图 is not None:
            浮层.blit(封面图, 封面框.topleft)
        else:
            pygame.draw.rect(浮层, (15, 15, 20), 封面框)

        # 2) 信息黑盒（保留你原逻辑，未强行参数化，避免牵连过大）
        双排星星 = int(歌.星级 or 0) > 10
        盒子左右留白 = int(封面框.w * 0.10)
        盒子下留白 = int(封面框.h * 0.06)
        盒子高占比 = 0.46 if 双排星星 else 0.40
        盒子高 = int(封面框.h * 盒子高占比)

        信息盒 = pygame.Rect(
            封面框.x + 盒子左右留白,
            封面框.bottom - 盒子下留白 - 盒子高,
            封面框.w - 盒子左右留白 * 2,
            盒子高,
        )

        黑盒 = pygame.Surface((信息盒.w, 信息盒.h), pygame.SRCALPHA)
        黑盒.fill((0, 0, 0, 175))
        浮层.blit(黑盒, 信息盒.topleft)

        内容上边距 = int(信息盒.h * (0.12 if 双排星星 else 0.06))
        内容顶 = 信息盒.y + max(2, 内容上边距)
        内容可用高 = max(20, 信息盒.bottom - 内容顶)

        if 双排星星:
            星行占比 = 0.48
            名行占比 = 0.22
            线行占比 = 0.08
        else:
            星行占比 = 0.36
            名行占比 = 0.22
            线行占比 = 0.10

        星行高 = max(18, int(内容可用高 * 星行占比))
        名行高 = max(16, int(内容可用高 * 名行占比))
        线行高 = max(8, int(内容可用高 * 线行占比))
        末行高 = max(16, 内容可用高 - 星行高 - 名行高 - 线行高)

        星行 = pygame.Rect(信息盒.x, 内容顶, 信息盒.w, 星行高)
        名行 = pygame.Rect(信息盒.x, 星行.bottom, 信息盒.w, 名行高)
        线行 = pygame.Rect(信息盒.x, 名行.bottom, 信息盒.w, 线行高)
        末行 = pygame.Rect(信息盒.x, 线行.bottom, 信息盒.w, 末行高)

        大星星路径 = _资源路径("UI-img", "选歌界面资源", "小星星", "大星星.png")
        光效路径 = _资源路径("UI-img", "选歌界面资源", "小星星", "星星动态.png")

        绘制星星行_图片(
            屏幕=浮层,
            区域=星行,
            星数=歌.星级,
            星星路径=大星星路径,
            星星缩放倍数=2.2,
            每行最大=10,
            动态光效路径=光效路径,
            光效周期秒=2.0,
            基准高占比=0.30,
            行间距占比=0.00,
        )

        歌名显示 = (歌.歌名 or "").replace("_", " ")
        目标歌名字号 = max(12, int(38 * 最终缩放))
        try:
            可用文字宽 = max(40, 名行.w - int(24 * 最终缩放))
            当前字号 = int(目标歌名字号)
            while 当前字号 > 10:
                字体 = 获取字体(当前字号, 是否粗体=False)
                文宽, _文高 = 字体.size(歌名显示)
                if 文宽 <= 可用文字宽:
                    break
                当前字号 -= 1

            字体 = 获取字体(max(10, 当前字号), 是否粗体=False)
            文面 = 字体.render(歌名显示, True, (255, 255, 255))
            文r = 文面.get_rect(center=名行.center)
            浮层.blit(文面, 文r.topleft)
        except Exception:
            pass

        y线 = 线行.centery
        线宽 = max(1, int(2 * 最终缩放))
        pygame.draw.line(
            浮层,
            (160, 160, 160),
            (线行.x + int(16 * 最终缩放), y线),
            (线行.right - int(16 * 最终缩放), y线),
            线宽,
        )

        游玩次数 = 0
        try:
            游玩次数 = int(max(0, int(getattr(歌, "游玩次数", 0) or 0)))
        except Exception:
            游玩次数 = 0
        bpm值 = str(歌.bpm) if 歌.bpm else "?"
        try:
            底部字号 = max(12, int(18 * 最终缩放))
            字体2 = 获取字体(底部字号, 是否粗体=False)
            左文 = 字体2.render(f"游玩次数:{游玩次数}", True, (230, 230, 230))
            右文 = 字体2.render(f"BPM:{bpm值}", True, (230, 230, 230))

            左x = 末行.x + int(16 * 最终缩放)
            左y = 末行.y + (末行.h - 左文.get_height()) // 2
            右x = 末行.right - int(16 * 最终缩放) - 右文.get_width()
            右y = 末行.y + (末行.h - 右文.get_height()) // 2

            浮层.blit(左文, (左x, 左y))
            浮层.blit(右文, (右x, 右y))
        except Exception:
            pass

        # 3) 盖框图（支持等比缩放模式）
        if 大框图2 is not None:
            浮层.blit(大框图2, (int(框x偏移), int(框y偏移)))

        # 序号标签（锚点=局部大框）
        绘制序号标签_图片(
            浮层,
            pygame.Rect(0, 0, 大框基础.w, 大框基础.h),
            内部序号从0=歌.序号,
            是否大图=True,
        )

        # ========= 入场动画：对浮层做 scale + alpha =========
        if scale动画 != 1.0:
            画宽 = max(1, int(大框基础.w * scale动画))
            画高 = max(1, int(大框基础.h * scale动画))
            浮层2 = pygame.transform.smoothscale(浮层, (画宽, 画高)).convert_alpha()
        else:
            浮层2 = 浮层

        try:
            浮层2.set_alpha(alpha动画)
        except Exception:
            pass

        当前大框 = 浮层2.get_rect()
        当前大框.center = 大框基础.center

        self.详情大框矩形 = 当前大框
        self.屏幕.blit(浮层2, 当前大框.topleft)

        # ========= 左右按钮（JSON可控：大小/间距/y偏移/边距）=========
        下一首图路径 = _资源路径("UI-img", "选歌界面资源", "下一首.png")
        下一首原图 = 获取UI原图(下一首图路径, 透明=True)
        if 下一首原图 is not None:
            ow, oh = 下一首原图.get_size()
        else:
            ow, oh = (150, 74)

        按钮高占比 = self._取布局值("详情大图.左右按钮.目标高占比", 0.28)
        try:
            按钮高占比 = float(按钮高占比)
        except Exception:
            按钮高占比 = 0.28
        按钮高占比 = max(0.05, min(0.90, 按钮高占比))

        按钮最小高 = self._取布局像素(
            "详情大图.左右按钮.最小高", 80, 最小=20, 最大=99999
        )
        按钮最大高 = self._取布局像素(
            "详情大图.左右按钮.最大高", 99999, 最小=20, 最大=99999
        )

        外间距 = self._取布局像素(
            "详情大图.左右按钮.外间距", 18, 最小=-99999, 最大=99999
        )
        y偏移 = self._取布局像素("详情大图.左右按钮.y偏移", 0, 最小=-99999, 最大=99999)
        边距 = self._取布局像素("详情大图.左右按钮.边距", 10, 最小=0, 最大=99999)
        上一首x偏移 = self._取布局像素(
            "详情大图.左右按钮.上一首x偏移", 0, 最小=-99999, 最大=99999
        )
        下一首x偏移 = self._取布局像素(
            "详情大图.左右按钮.下一首x偏移", 0, 最小=-99999, 最大=99999
        )

        按钮目标高 = max(int(按钮最小高), int(当前大框.h * 按钮高占比))
        按钮目标高 = min(int(按钮最大高), 按钮目标高)

        按钮目标宽 = max(40, int(按钮目标高 * (float(ow) / float(max(1, oh)))))
        按钮y = 当前大框.centery - 按钮目标高 // 2 + int(y偏移)

        上一首矩形 = pygame.Rect(
            max(int(边距), 当前大框.left - int(外间距) - 按钮目标宽 + int(上一首x偏移)),
            按钮y,
            按钮目标宽,
            按钮目标高,
        )
        下一首矩形 = pygame.Rect(
            min(
                self.宽 - int(边距) - 按钮目标宽,
                当前大框.right + int(外间距) + int(下一首x偏移),
            ),
            按钮y,
            按钮目标宽,
            按钮目标高,
        )

        self.按钮_详情上一首.矩形 = 上一首矩形
        self.按钮_详情下一首.矩形 = 下一首矩形

        self.按钮_详情上一首.绘制(self.屏幕)
        self.按钮_详情下一首.绘制(self.屏幕)

    def 绘制星级筛选页(self):
        # 半透明遮罩
        暗层 = pygame.Surface((self.宽, self.高), pygame.SRCALPHA)
        暗层.fill((0, 0, 0, 170))
        self.屏幕.blit(暗层, (0, 0))

        面板 = self.筛选页面板矩形

        面板底 = pygame.Surface((面板.w, 面板.h), pygame.SRCALPHA)
        面板底.fill((10, 20, 40, 220))
        self.屏幕.blit(面板底, 面板.topleft)
        绘制圆角矩形(self.屏幕, 面板, (180, 220, 255), 圆角=18, 线宽=3)

        标题字体 = 获取字体(36)
        说明字体 = 获取字体(18)
        按钮字体 = 获取字体(18)

        绘制文本(
            self.屏幕,
            "按星级筛选",
            标题字体,
            (255, 255, 255),
            (面板.centerx, 面板.y + 36),
            对齐="center",
        )
        绘制文本(
            self.屏幕,
            "选择星级后仅展示对应星星的歌（ESC/点空白关闭）",
            说明字体,
            (210, 235, 255),
            (面板.centerx, 面板.y + 78),
            对齐="center",
        )

        # 画 1~20 星按钮（你已经在 _重算星级筛选页布局 里生成了）
        for 星, 按钮对象 in self.星级按钮列表:
            try:
                按钮对象.绘制(self.屏幕, 按钮字体)
            except TypeError:
                # 兼容你可能混进来的旧按钮类
                try:
                    按钮对象.绘制(self.屏幕, 按钮字体)
                except Exception:
                    pass

            # 当前筛选高亮（可选：更直观）
            try:
                if self.当前筛选星级 is not None and int(self.当前筛选星级) == int(星):
                    r = getattr(按钮对象, "矩形", None)
                    if isinstance(r, pygame.Rect):
                        pygame.draw.rect(
                            self.屏幕, (255, 220, 80), r, width=3, border_radius=16
                        )
            except Exception:
                pass

    def _确保公共交互(self):
        if getattr(self, "_公共交互已初始化", False):
            return
        self._公共交互已初始化 = True

        # 过渡（按钮截图缩放淡出）
        self._过渡_特效 = None
        self._过渡_图片 = None
        self._过渡_rect = pygame.Rect(0, 0, 0, 0)
        self._过渡_回调 = None
        self._过渡_曾在播放 = False

        # ✅ 星级筛选专用：0.5s 渐隐放大（像“浮动大图入场”）
        self._特效_星级筛选 = 渐隐放大点击特效(总时长=0.5)

        # ✅ 全局点击序列帧特效
        self._全局点击特效 = None

        # 公用按钮音效 + 公用点击特效
        self._按钮音效 = None
        self._特效_按钮 = None
        self._特效_大图确认 = None

        # ✅ 开始游戏音效（大图二次点击触发）
        self._开始游戏音效_对象 = None

        # ✅ “几P加入”嘲讽提示（2秒）
        self._消息提示_文本 = ""
        self._消息提示_截止时间 = 0.0

        # ✅ “浮动大图二次点击”计数器（不是双击判定，是第二次点击）
        self._大图确认_点击次数 = 0
        self._大图确认_上次点击时间 = 0.0

        # ===== 引入：ui/点击特效.py（序列帧）=====
        try:
            from ui.点击特效 import 序列帧特效资源, 全局点击特效管理器
        except Exception:
            序列帧特效资源 = None
            全局点击特效管理器 = None

        # ===== 引入：ui/按钮特效.py（截图缩放淡出 + 音效）=====
        try:
            from ui.按钮特效 import 公用按钮点击特效, 公用按钮音效
        except Exception:
            公用按钮点击特效 = None
            公用按钮音效 = None

        # -------------------------
        # 初始化：全局点击序列帧特效
        # -------------------------
        if 序列帧特效资源 and 全局点击特效管理器:
            点击特效目录 = ""
            try:
                from core.常量与路径 import 默认资源路径

                资源 = 默认资源路径()
                根目录 = str(资源.get("根", "") or "")
                if 根目录:
                    点击特效目录 = os.path.join(根目录, "UI-img", "点击特效")
            except Exception:
                点击特效目录 = ""

            if not 点击特效目录:
                try:
                    脚本目录 = _取项目根目录()
                    点击特效目录 = os.path.join(脚本目录, "UI-img", "点击特效")
                except Exception:
                    点击特效目录 = ""

            try:
                特效资源 = 序列帧特效资源(目录=点击特效目录, 扩展名=".png")
                特效ok = bool(特效资源.加载())
                帧列表 = 特效资源.帧列表 if 特效ok else []
            except Exception:
                帧列表 = []

            try:
                self._全局点击特效 = 全局点击特效管理器(
                    帧列表=帧列表,
                    每秒帧数=30,
                    缩放比例=1.0,
                )
            except Exception:
                self._全局点击特效 = None

        # -------------------------
        # 初始化：按钮音效
        # -------------------------
        音效路径 = ""
        try:
            from core.常量与路径 import 默认资源路径

            资源 = 默认资源路径()
            音效路径 = str(资源.get("按钮音效", "") or "")
        except Exception:
            音效路径 = ""

        if 公用按钮音效 and 音效路径 and os.path.isfile(音效路径):
            try:
                self._按钮音效 = 公用按钮音效(音效路径)
            except Exception:
                self._按钮音效 = None

        # -------------------------
        # 初始化：按钮点击“截图缩放淡出”特效
        # -------------------------
        if 公用按钮点击特效:
            try:
                self._特效_按钮 = 公用按钮点击特效()
                self._特效_大图确认 = 公用按钮点击特效(
                    总时长=0.35,
                    缩小阶段=0.10,
                    缩小到=0.98,
                    放大到=6.00,
                    透明起始=255,
                    透明结束=0,
                )
            except Exception:
                self._特效_按钮 = None
                self._特效_大图确认 = None

        # -------------------------
        # ✅ 初始化：开始游戏音效 backsound/开始游戏.mp3
        # -------------------------
        开始游戏路径 = _资源路径("冷资源", "backsound", "开始游戏.mp3")
        if 公用按钮音效 and os.path.isfile(开始游戏路径):
            try:
                self._开始游戏音效_对象 = 公用按钮音效(开始游戏路径)
            except Exception:
                self._开始游戏音效_对象 = None
        else:
            self._开始游戏音效_对象 = None

        if not hasattr(self, "_浮动大图入场时长毫秒"):
            self._浮动大图入场时长毫秒 = 500

    def _播放按钮音效(self):
        self._确保公共交互()
        if self._按钮音效 is None:
            return
        try:
            self._按钮音效.播放()
        except Exception:
            pass

    def _启动过渡(
        self,
        特效对象,
        目标矩形: pygame.Rect,
        回调: Callable[[], None],
        覆盖图片: Optional[pygame.Surface] = None,
    ):
        """
        ✅ 所有按钮/卡片/大图确认都走这个入口：
        - 默认播放统一按钮音效
        - 用“公用按钮点击特效”对截图做缩放
        - 特效结束后才执行回调（避免乱序）

        ✅ 例外：
        - 大图确认（开始游戏）不播放“全局按钮音效”，只由回调播放 backsound/开始游戏.mp3
        """
        self._确保公共交互()

        if 特效对象 is None:
            # 没特效就直接执行
            try:
                回调()
            except Exception:
                pass
            return

        # 正在过渡就忽略（避免连点乱序）
        if self._过渡_曾在播放 and self._过渡_特效 is not None:
            try:
                if self._过渡_特效.是否动画中():
                    return
            except Exception:
                pass

        # ✅ 是否播放全局按钮音效：大图确认要禁用
        是否播放全局按钮音效 = True
        try:
            if (
                getattr(self, "_特效_大图确认", None) is not None
                and 特效对象 is self._特效_大图确认
            ):
                是否播放全局按钮音效 = False
        except Exception:
            pass

        # 再加一道兜底：如果回调就是“大图确认处理”，也禁用全局按钮音效
        try:
            if getattr(回调, "__name__", "") == "_记录并处理大图确认点击":
                是否播放全局按钮音效 = False
        except Exception:
            pass

        # 播放统一音效（大图确认例外不播）
        if 是否播放全局按钮音效:
            self._播放按钮音效()

        if 覆盖图片 is not None:
            r = 目标矩形.copy()
            try:
                图片 = 覆盖图片.copy().convert_alpha()
            except Exception:
                图片 = 覆盖图片
        else:
            # 截图：一定要 clip 到屏幕范围，否则 subsurface 会崩
            try:
                屏幕矩形 = self.屏幕.get_rect()
                r = 目标矩形.clip(屏幕矩形)
                if r.w <= 0 or r.h <= 0:
                    r = pygame.Rect(max(0, 目标矩形.x), max(0, 目标矩形.y), 2, 2)
                    r = r.clip(屏幕矩形)
                图片 = self.屏幕.subsurface(r).copy()
            except Exception:
                r = 目标矩形.copy()
                图片 = None

        try:
            特效对象.触发()
        except Exception:
            # 特效触发失败就直接执行回调
            try:
                回调()
            except Exception:
                pass
            return

        self._过渡_特效 = 特效对象
        self._过渡_图片 = 图片
        self._过渡_rect = r
        self._过渡_回调 = 回调
        self._过渡_曾在播放 = True

    def _更新过渡(self):
        if not getattr(self, "_过渡_曾在播放", False):
            return
        if self._过渡_特效 is None:
            self._过渡_曾在播放 = False
            return

        仍在动画中 = False
        try:
            仍在动画中 = bool(self._过渡_特效.是否动画中())
        except Exception:
            仍在动画中 = False

        if not 仍在动画中:
            self._过渡_曾在播放 = False
            回调 = self._过渡_回调
            self._过渡_回调 = None
            self._过渡_图片 = None
            try:
                if 回调:
                    回调()
            except Exception:
                pass

    def _绘制过渡(self):
        if self._过渡_特效 is None or self._过渡_图片 is None:
            return
        try:
            if self._过渡_特效.是否动画中():
                self._过渡_特效.绘制按钮(self.屏幕, self._过渡_图片, self._过渡_rect)
        except Exception:
            pass

    def _获取联网原图_尽力(self) -> Optional[pygame.Surface]:
        # 优先返回已缓存
        if getattr(self, "_联网原图_缓存", None) is not None:
            return self._联网原图_缓存

        图 = None

        # 1) 优先走 core/常量与路径.py（你给的最权威路径）
        try:
            from core.常量与路径 import 默认资源路径

            资源 = 默认资源路径()
            路径 = str(资源.get("投币_联网图标", "") or "")
            图 = 安全加载图片(路径, 透明=True)
            if 图 is not None:
                self._联网原图_缓存 = 图
                return 图
        except Exception:
            pass

        # 2) 兜底：硬猜路径（兼容你可能搬目录）
        候选 = [
            _资源路径("UI-img", "联网状态", "已联网.png"),
            _资源路径("UI-img", "联网状态", "联网.png"),
            _资源路径("UI-img", "选歌界面资源", "联网图标.png"),
            _资源路径("UI-img", "投币界面", "联网图标.png"),
        ]
        for p in 候选:
            try:
                if os.path.isfile(p):
                    图 = pygame.image.load(p).convert_alpha()
                    break
            except Exception:
                continue

        self._联网原图_缓存 = 图
        return 图

    # -------------------------
    # 事件 -> 点击动效封装
    # -------------------------

    def 安排点击动作(self, 高亮矩形: pygame.Rect, 动作: Callable[[], None]):
        """
        兼容老接口：以前你可能有 self.点击动效
        现在统一走：_启动过渡(按钮特效, 截图矩形, 动作)
        """
        self._确保公共交互()
        try:
            self._启动过渡(self._特效_按钮, 高亮矩形, 动作)
        except Exception:
            try:
                动作()
            except Exception:
                pass

    def 请求回主程序重新选歌(self):
        """
        ✅ 需求：点击“重选模式”不在选歌界面内部处理，而是退出选歌界面，
        返回一个状态给主程序.py，让主程序回到模式选择重新选。
        """
        self._返回状态 = "RESELECT_MAIN"
        self._需要退出 = True

    # -------------------------
    # 主循环
    # -------------------------
    def 主循环(self):
        self._确保公共交互()

        # ✅ 初始化滑动状态（防御：旧存档/热更情况下可能不存在）
        if not hasattr(self, "_滑动_按下"):
            self._滑动_按下 = False
            self._滑动_起点 = (0, 0)
            self._滑动_已触发 = False
            self._滑动_已移动 = False

        while True:
            if self._需要退出:
                try:
                    if self.音频可用:
                        pygame.mixer.music.stop()
                except Exception:
                    pass

                if not getattr(self, "_是否嵌入模式", False):
                    try:
                        pygame.quit()
                    except Exception:
                        pass

                return self._返回状态

            self.时钟.tick(60)

            self.每帧执行预加载(每帧数量=3)
            self.更新动画状态()
            self._更新过渡()

            # ===== 绘制 =====
            self.绘制背景()
            self.绘制顶部()

            if self.动画中:
                self.绘制列表页_动画()
            else:
                self.绘制列表页()

            if self.是否详情页:
                self.绘制详情浮层()
                # ✅ 大图 NEW（不改绘制详情浮层巨型函数）
                try:
                    self.绘制NEW标签_大图()
                except Exception:
                    pass
            else:
                self.确保播放背景音乐()

            self.绘制底部()

            if self.是否星级筛选页:
                self.绘制星级筛选页()

            if bool(getattr(self, "是否设置页", False)):
                try:
                    self.绘制设置页()
                except Exception:
                    pass

            self._绘制过渡()

            try:
                if self._全局点击特效 is not None:
                    self._全局点击特效.更新并绘制(self.屏幕)
            except Exception:
                pass

            try:
                self._绘制消息提示()
            except Exception:
                pass

            if self._调试提示文本 and time.time() < self._调试提示截止:
                try:
                    文面 = self.小字体.render(self._调试提示文本, True, (255, 220, 120))
                    文r = 文面.get_rect()
                    文r.topright = (self.宽 - 12, 12)
                    self.屏幕.blit(文面, 文r.topleft)
                except Exception:
                    pass

            pygame.display.flip()

            # ===== 事件 =====
            for 事件 in pygame.event.get():
                if 事件.type == pygame.QUIT:
                    self._返回状态 = "NORMAL"
                    self._需要退出 = True
                    break

                if 事件.type == pygame.VIDEORESIZE:
                    新宽 = max(900, 事件.w)
                    新高 = max(600, 事件.h)
                    self.屏幕 = pygame.display.set_mode((新宽, 新高), pygame.RESIZABLE)
                    self.重算布局()
                    self.安排预加载(基准页=self.当前页)

                    try:
                        if bool(getattr(self, "是否设置页", False)):
                            self._重算设置页布局()
                    except Exception:
                        pass
                    continue

                # ✅ 全局点击特效（保持原逻辑）
                if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
                    try:
                        if self._全局点击特效 is not None:
                            x, y = 事件.pos
                            self._全局点击特效.触发(int(x), int(y))
                    except Exception:
                        pass

                # ✅ 过渡播放中：只允许 hover
                try:
                    if self._过渡_特效 is not None and self._过渡_特效.是否动画中():
                        if 事件.type == pygame.MOUSEMOTION:
                            pass
                        else:
                            continue
                except Exception:
                    pass

                # ✅ 设置页优先
                if bool(getattr(self, "是否设置页", False)):
                    try:
                        self._设置页_处理事件(事件)
                    except Exception:
                        pass
                    continue

                # ===== 星级筛选页优先 =====
                if self.是否星级筛选页:
                    if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
                        if not self.筛选页面板矩形.collidepoint(事件.pos):
                            self._启动过渡(
                                self._特效_按钮,
                                pygame.Rect(事件.pos[0] - 20, 事件.pos[1] - 20, 40, 40),
                                self.关闭星级筛选页,
                            )
                            continue

                    if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
                        self._启动过渡(
                            self._特效_按钮,
                            pygame.Rect(
                                self.筛选页面板矩形.centerx - 60,
                                self.筛选页面板矩形.y + 20,
                                120,
                                50,
                            ),
                            self.关闭星级筛选页,
                        )
                        continue

                    for 星, b in self.星级按钮列表:
                        b.处理事件(事件)
                    continue

                # ===== 底部按钮 =====
                if self.按钮_歌曲分类.处理事件(事件):
                    self._启动过渡(
                        self._特效_按钮, self.按钮_歌曲分类.矩形, self.打开星级筛选页
                    )

                if self.按钮_ALL.处理事件(事件):
                    self._启动过渡(
                        self._特效_按钮,
                        self.按钮_ALL.矩形,
                        lambda: self.设置星级筛选(None),
                    )

                if self.按钮_2P加入.处理事件(事件):
                    self._启动过渡(
                        self._特效_按钮,
                        self.按钮_2P加入.矩形,
                        lambda: self.显示消息提示(
                            "别做梦了你根本没有舞搭子 (*^__^*) 嘻嘻……", 持续秒=2.0
                        ),
                    )

                if self.按钮_设置.处理事件(事件):
                    self._启动过渡(
                        self._特效_按钮, self.按钮_设置.矩形, self.打开设置页
                    )

                if self.按钮_重选模式.处理事件(事件):
                    self._启动过渡(
                        self._特效_按钮,
                        self.按钮_重选模式.矩形,
                        self.请求回主程序重新选歌,
                    )
                    continue

                if self.动画中:
                    continue

                # ===== 详情页 =====
                if self.是否详情页:
                    上一首触发 = self.按钮_详情上一首.处理事件(事件)
                    下一首触发 = self.按钮_详情下一首.处理事件(事件)

                    if 上一首触发:
                        self._启动过渡(
                            self._特效_按钮,
                            self.按钮_详情上一首.矩形,
                            self.上一首,
                            覆盖图片=self.按钮_详情上一首._获取缩放图(),
                        )
                        continue
                    if 下一首触发:
                        self._启动过渡(
                            self._特效_按钮,
                            self.按钮_详情下一首.矩形,
                            self.下一首,
                            覆盖图片=self.按钮_详情下一首._获取缩放图(),
                        )
                        continue

                    if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
                        点在左右按钮 = self.按钮_详情上一首.矩形.collidepoint(
                            事件.pos
                        ) or self.按钮_详情下一首.矩形.collidepoint(事件.pos)

                        if (not 点在左右按钮) and self.详情大框矩形.collidepoint(
                            事件.pos
                        ):
                            self._启动过渡(
                                self._特效_大图确认,
                                self.详情大框矩形,
                                self._记录并处理大图确认点击,
                            )
                            continue

                        if (not 点在左右按钮) and (
                            not self.详情大框矩形.collidepoint(事件.pos)
                        ):
                            self._启动过渡(
                                self._特效_按钮,
                                pygame.Rect(事件.pos[0] - 20, 事件.pos[1] - 20, 40, 40),
                                self.返回列表,
                            )
                            continue

                    # ✅ 键盘左右切歌：取消“切场景动效”，直接切
                    if 事件.type == pygame.KEYDOWN:
                        if 事件.key == pygame.K_ESCAPE:
                            self._启动过渡(
                                self._特效_按钮, self.详情大框矩形, self.返回列表
                            )
                        elif 事件.key == pygame.K_LEFT:
                            try:
                                self._播放按钮音效()
                            except Exception:
                                pass
                            self.上一首()
                        elif 事件.key == pygame.K_RIGHT:
                            try:
                                self._播放按钮音效()
                            except Exception:
                                pass
                            self.下一首()
                    continue

                # ===== 列表页：hover =====
                if 事件.type == pygame.MOUSEMOTION:
                    for 卡片 in self.当前页卡片:
                        卡片.处理事件(事件)

                # ===== 列表页：滑动翻页（中间区域）=====
                if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
                    if self.中间区域.collidepoint(事件.pos):
                        self._滑动_按下 = True
                        self._滑动_起点 = tuple(事件.pos)
                        self._滑动_已触发 = False
                        self._滑动_已移动 = False

                if 事件.type == pygame.MOUSEMOTION:
                    if bool(getattr(self, "_滑动_按下", False)) and (
                        not bool(getattr(self, "_滑动_已触发", False))
                    ):
                        try:
                            # buttons[0]：左键是否按住
                            if (
                                hasattr(事件, "buttons")
                                and 事件.buttons
                                and (not 事件.buttons[0])
                            ):
                                pass
                            else:
                                sx, sy = getattr(self, "_滑动_起点", (0, 0))
                                dx = int(事件.pos[0] - sx)
                                dy = int(事件.pos[1] - sy)

                                if abs(dx) > 12 or abs(dy) > 12:
                                    self._滑动_已移动 = True

                                阈值 = max(60, int(self.宽 * 0.05))
                                if (abs(dx) >= 阈值) and (abs(dx) > int(abs(dy) * 1.2)):
                                    # dx<0：向左滑 => 下一页；dx>0：向右滑 => 上一页
                                    if dx < 0:
                                        self.触发翻页动画(
                                            目标页=self.当前页 + 1, 方向=+1
                                        )
                                    else:
                                        self.触发翻页动画(
                                            目标页=self.当前页 - 1, 方向=-1
                                        )

                                    self._滑动_已触发 = True
                        except Exception:
                            pass

                if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
                    if bool(getattr(self, "_滑动_按下", False)):
                        self._滑动_按下 = False

                        # 没触发翻页、且没明显移动：认为是点击（进入详情）
                        if (not bool(getattr(self, "_滑动_已触发", False))) and (
                            not bool(getattr(self, "_滑动_已移动", False))
                        ):
                            if self.中间区域.collidepoint(事件.pos):
                                列表, 映射 = self.当前歌曲列表与映射()
                                for idx, 卡片 in enumerate(self.当前页卡片):
                                    if 卡片.矩形.collidepoint(事件.pos):
                                        视图索引 = self.当前页 * self.每页数量 + idx
                                        原始索引 = (
                                            映射[视图索引]
                                            if 0 <= 视图索引 < len(映射)
                                            else 0
                                        )
                                        self._播放按钮音效()
                                        self.进入详情_原始索引(原始索引)
                                        break

                        # 清理一次性状态
                        self._滑动_已触发 = False
                        self._滑动_已移动 = False

                # ===== 鼠标滚轮翻页（支持环绕）=====
                if 事件.type == pygame.MOUSEBUTTONDOWN:
                    if 事件.button == 4:
                        self.触发翻页动画(目标页=self.当前页 - 1, 方向=-1)
                    elif 事件.button == 5:
                        self.触发翻页动画(目标页=self.当前页 + 1, 方向=+1)

                # ===== 键盘翻页（列表页）=====
                if 事件.type == pygame.KEYDOWN:
                    if 事件.key == pygame.K_LEFT:
                        self.触发翻页动画(目标页=self.当前页 - 1, 方向=-1)
                    elif 事件.key == pygame.K_RIGHT:
                        self.触发翻页动画(目标页=self.当前页 + 1, 方向=+1)
                    elif 事件.key == pygame.K_ESCAPE:
                        if self.当前筛选星级 is not None:
                            self._启动过渡(
                                self._特效_按钮,
                                pygame.Rect(
                                    self.宽 // 2 - 60, self.顶部高 // 2 - 20, 120, 40
                                ),
                                lambda: self.设置星级筛选(None),
                            )


def 绑定设置页方法到选歌游戏类():
    选歌游戏._设置页_持久化文件路径 = _设置页_持久化文件路径
    选歌游戏._设置页_从参数文本提取 = _设置页_从参数文本提取
    选歌游戏._设置页_构建参数文本 = _设置页_构建参数文本
    选歌游戏._设置页_读取持久化设置 = _设置页_读取持久化设置
    选歌游戏._设置页_写入持久化设置 = _设置页_写入持久化设置
    选歌游戏._设置页_加载持久化设置 = _设置页_加载持久化设置
    选歌游戏._设置页_保存持久化设置 = _设置页_保存持久化设置
    选歌游戏._确保设置页资源 = _确保设置页资源
    选歌游戏._设置页_同步参数 = _设置页_同步参数
    选歌游戏._设置页_取缩放图 = _设置页_取缩放图
    选歌游戏._重算设置页布局 = _重算设置页布局
    选歌游戏._设置页_缓入 = _设置页_缓入
    选歌游戏._设置页_缓出 = _设置页_缓出
    选歌游戏._设置页_点在有效面板区域 = _设置页_点在有效面板区域
    选歌游戏.打开设置页 = 打开设置页
    选歌游戏.关闭设置页 = 关闭设置页
    选歌游戏._设置页_切换选项 = _设置页_切换选项
    选歌游戏._设置页_切换背景 = _设置页_切换背景
    选歌游戏._设置页_处理事件 = _设置页_处理事件
    选歌游戏.绘制设置页 = 绘制设置页

    # 只保留“加载布局覆盖”，不再提供保存/编辑入口
    选歌游戏._设置页_布局覆盖文件路径 = _设置页_布局覆盖文件路径
    选歌游戏._设置页_加载布局覆盖 = _设置页_加载布局覆盖


绑定设置页方法到选歌游戏类()


def 选歌_绑定外部屏幕(self, 外部屏幕: pygame.Surface):
    if 外部屏幕 is None:
        return
    try:
        旧尺寸 = (int(getattr(self, "宽", 0) or 0), int(getattr(self, "高", 0) or 0))
    except Exception:
        旧尺寸 = (0, 0)

    self.屏幕 = 外部屏幕
    try:
        self.宽, self.高 = self.屏幕.get_size()
    except Exception:
        self.宽, self.高 = (0, 0)

    新尺寸 = (int(self.宽), int(self.高))
    if 新尺寸 != 旧尺寸:
        try:
            self.重算布局()
            self.安排预加载(基准页=int(getattr(self, "当前页", 0) or 0))
        except Exception:
            pass


def 选歌_帧更新(self):
    self._确保公共交互()

    if bool(getattr(self, "_需要退出", False)):
        return str(getattr(self, "_返回状态", "NORMAL") or "NORMAL")

    try:
        self.每帧执行预加载(每帧数量=3)
        self.更新动画状态()
        self._更新过渡()
    except Exception:
        pass

    if bool(getattr(self, "_需要退出", False)):
        return str(getattr(self, "_返回状态", "NORMAL") or "NORMAL")
    return None


def 选歌_帧绘制(self):
    self._确保公共交互()

    try:
        self.绘制背景()
        self.绘制顶部()

        if bool(getattr(self, "动画中", False)):
            self.绘制列表页_动画()
        else:
            self.绘制列表页()

        if bool(getattr(self, "是否详情页", False)):
            self.绘制详情浮层()
            try:
                self.绘制NEW标签_大图()
            except Exception:
                pass
        else:
            try:
                self.确保播放背景音乐()
            except Exception:
                pass

        self.绘制底部()

        if bool(getattr(self, "是否星级筛选页", False)):
            self.绘制星级筛选页()

        if bool(getattr(self, "是否设置页", False)):
            try:
                self.绘制设置页()
            except Exception:
                pass

        self._绘制过渡()

        # ⚠️ 注意：这里不做 pygame.display.flip()，交给主流程统一 flip
        try:
            if getattr(self, "_全局点击特效", None) is not None:
                self._全局点击特效.更新并绘制(self.屏幕)
        except Exception:
            pass

        try:
            self._绘制消息提示()
        except Exception:
            pass

        if getattr(self, "_调试提示文本", "") and time.time() < float(
            getattr(self, "_调试提示截止", 0.0) or 0.0
        ):
            try:
                文面 = self.小字体.render(self._调试提示文本, True, (255, 220, 120))
                文r = 文面.get_rect()
                文r.topright = (self.宽 - 12, 12)
                self.屏幕.blit(文面, 文r.topleft)
            except Exception:
                pass

    except Exception:
        # 防御：绘制异常不允许打断主循环
        pass


def 选歌_处理事件_外部(self, 事件):
    self._确保公共交互()

    if 事件 is None:
        return None

    # 让外部 resize 后的新 surface 生效（主流程已经 set_mode 了）
    if 事件.type == pygame.VIDEORESIZE:
        try:
            新屏幕 = pygame.display.get_surface()
            if 新屏幕 is not None:
                self.屏幕 = 新屏幕
            self.重算布局()
            self.安排预加载(基准页=int(getattr(self, "当前页", 0) or 0))
            if bool(getattr(self, "是否设置页", False)):
                try:
                    self._重算设置页布局()
                except Exception:
                    pass
        except Exception:
            pass
        return None

    if 事件.type == pygame.QUIT:
        self._返回状态 = "NORMAL"
        self._需要退出 = True
        return "NORMAL"

    # ✅ 全局点击特效（如果你在场景里把 _全局点击特效=None，这里就不会重复触发）
    if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
        try:
            if getattr(self, "_全局点击特效", None) is not None:
                x, y = 事件.pos
                self._全局点击特效.触发(int(x), int(y))
        except Exception:
            pass

    # ✅ 过渡播放中：只允许 hover
    try:
        if (
            getattr(self, "_过渡_特效", None) is not None
            and self._过渡_特效.是否动画中()
        ):
            if 事件.type == pygame.MOUSEMOTION:
                pass
            else:
                return None
    except Exception:
        pass

    # ✅ 设置页优先
    if bool(getattr(self, "是否设置页", False)):
        try:
            self._设置页_处理事件(事件)
        except Exception:
            pass
        return None

    # ===== 星级筛选页优先 =====
    if bool(getattr(self, "是否星级筛选页", False)):
        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            if not self.筛选页面板矩形.collidepoint(事件.pos):
                self._启动过渡(
                    self._特效_按钮,
                    pygame.Rect(事件.pos[0] - 20, 事件.pos[1] - 20, 40, 40),
                    self.关闭星级筛选页,
                )
                return None

        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
            self._启动过渡(
                self._特效_按钮,
                pygame.Rect(
                    self.筛选页面板矩形.centerx - 60,
                    self.筛选页面板矩形.y + 20,
                    120,
                    50,
                ),
                self.关闭星级筛选页,
            )
            return None

        for _星, 按钮对象 in self.星级按钮列表:
            try:
                按钮对象.处理事件(事件)
            except Exception:
                pass
        return None

    # ===== 底部按钮 =====
    try:
        if self.按钮_歌曲分类.处理事件(事件):
            self._启动过渡(
                self._特效_按钮, self.按钮_歌曲分类.矩形, self.打开星级筛选页
            )
    except Exception:
        pass

    try:
        if self.按钮_ALL.处理事件(事件):
            self._启动过渡(
                self._特效_按钮, self.按钮_ALL.矩形, lambda: self.设置星级筛选(None)
            )
    except Exception:
        pass

    try:
        if self.按钮_2P加入.处理事件(事件):
            self._启动过渡(
                self._特效_按钮,
                self.按钮_2P加入.矩形,
                lambda: self.显示消息提示(
                    "别做梦了你根本没有舞搭子 (*^__^*) 嘻嘻……", 持续秒=2.0
                ),
            )
    except Exception:
        pass

    try:
        if self.按钮_设置.处理事件(事件):
            self._启动过渡(self._特效_按钮, self.按钮_设置.矩形, self.打开设置页)
    except Exception:
        pass

    try:
        if self.按钮_重选模式.处理事件(事件):
            self._启动过渡(
                self._特效_按钮, self.按钮_重选模式.矩形, self.请求回主程序重新选歌
            )
            return None
    except Exception:
        pass

    if bool(getattr(self, "动画中", False)):
        return None

    # ===== 详情页 =====
    if bool(getattr(self, "是否详情页", False)):
        try:
            上一首触发 = self.按钮_详情上一首.处理事件(事件)
            下一首触发 = self.按钮_详情下一首.处理事件(事件)

            if 上一首触发:
                self._启动过渡(
                    self._特效_按钮,
                    self.按钮_详情上一首.矩形,
                    self.上一首,
                    覆盖图片=self.按钮_详情上一首._获取缩放图(),
                )
                return None
            if 下一首触发:
                self._启动过渡(
                    self._特效_按钮,
                    self.按钮_详情下一首.矩形,
                    self.下一首,
                    覆盖图片=self.按钮_详情下一首._获取缩放图(),
                )
                return None
        except Exception:
            pass

        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            try:
                点在左右按钮 = self.按钮_详情上一首.矩形.collidepoint(
                    事件.pos
                ) or self.按钮_详情下一首.矩形.collidepoint(事件.pos)
            except Exception:
                点在左右按钮 = False

            if (not 点在左右按钮) and self.详情大框矩形.collidepoint(事件.pos):
                self._启动过渡(
                    self._特效_大图确认, self.详情大框矩形, self._记录并处理大图确认点击
                )
                return None

            if (not 点在左右按钮) and (not self.详情大框矩形.collidepoint(事件.pos)):
                self._启动过渡(
                    self._特效_按钮,
                    pygame.Rect(事件.pos[0] - 20, 事件.pos[1] - 20, 40, 40),
                    self.返回列表,
                )
                return None

        if 事件.type == pygame.KEYDOWN:
            if 事件.key == pygame.K_ESCAPE:
                self._启动过渡(self._特效_按钮, self.详情大框矩形, self.返回列表)
                return None
            if 事件.key == pygame.K_LEFT:
                try:
                    self._播放按钮音效()
                except Exception:
                    pass
                self.上一首()
                return None
            if 事件.key == pygame.K_RIGHT:
                try:
                    self._播放按钮音效()
                except Exception:
                    pass
                self.下一首()
                return None

        return None

    # ===== 列表页 hover =====
    if 事件.type == pygame.MOUSEMOTION:
        self._踏板选中视图索引 = None
        self._同步踏板卡片高亮()
        for 卡片 in self.当前页卡片:
            try:
                卡片.处理事件(事件)
            except Exception:
                pass

    # ===== 列表页：滑动翻页 =====
    if not hasattr(self, "_滑动_按下"):
        self._滑动_按下 = False
        self._滑动_起点 = (0, 0)
        self._滑动_已触发 = False
        self._滑动_已移动 = False

    if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
        if self.中间区域.collidepoint(事件.pos):
            self._滑动_按下 = True
            self._滑动_起点 = tuple(事件.pos)
            self._滑动_已触发 = False
            self._滑动_已移动 = False

    if 事件.type == pygame.MOUSEMOTION:
        if bool(getattr(self, "_滑动_按下", False)) and (
            not bool(getattr(self, "_滑动_已触发", False))
        ):
            try:
                if hasattr(事件, "buttons") and 事件.buttons and (not 事件.buttons[0]):
                    pass
                else:
                    sx, sy = getattr(self, "_滑动_起点", (0, 0))
                    dx = int(事件.pos[0] - sx)
                    dy = int(事件.pos[1] - sy)

                    if abs(dx) > 12 or abs(dy) > 12:
                        self._滑动_已移动 = True

                    阈值 = max(60, int(self.宽 * 0.05))
                    if (abs(dx) >= 阈值) and (abs(dx) > int(abs(dy) * 1.2)):
                        if dx < 0:
                            self.触发翻页动画(目标页=self.当前页 + 1, 方向=+1)
                        else:
                            self.触发翻页动画(目标页=self.当前页 - 1, 方向=-1)
                        self._滑动_已触发 = True
            except Exception:
                pass

    if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
        if bool(getattr(self, "_滑动_按下", False)):
            self._滑动_按下 = False

            if (not bool(getattr(self, "_滑动_已触发", False))) and (
                not bool(getattr(self, "_滑动_已移动", False))
            ):
                if self.中间区域.collidepoint(事件.pos):
                    列表, 映射 = self.当前歌曲列表与映射()
                    for idx, 卡片 in enumerate(self.当前页卡片):
                        if 卡片.矩形.collidepoint(事件.pos):
                            视图索引 = self.当前页 * self.每页数量 + idx
                            原始索引 = (
                                映射[视图索引] if 0 <= 视图索引 < len(映射) else 0
                            )
                            try:
                                self._播放按钮音效()
                            except Exception:
                                pass
                            self.进入详情_原始索引(原始索引)
                            break

            self._滑动_已触发 = False
            self._滑动_已移动 = False

    # ===== 鼠标滚轮翻页 =====
    if 事件.type == pygame.MOUSEBUTTONDOWN:
        if 事件.button == 4:
            self.触发翻页动画(目标页=self.当前页 - 1, 方向=-1)
        elif 事件.button == 5:
            self.触发翻页动画(目标页=self.当前页 + 1, 方向=+1)

    # ===== 键盘翻页 / ESC 清筛选 =====
    if 事件.type == pygame.KEYDOWN:
        if 事件.key == pygame.K_LEFT:
            self.触发翻页动画(目标页=self.当前页 - 1, 方向=-1)
        elif 事件.key == pygame.K_RIGHT:
            self.触发翻页动画(目标页=self.当前页 + 1, 方向=+1)
        elif 事件.key == pygame.K_ESCAPE:
            if getattr(self, "当前筛选星级", None) is not None:
                self._启动过渡(
                    self._特效_按钮,
                    pygame.Rect(self.宽 // 2 - 60, self.顶部高 // 2 - 20, 120, 40),
                    lambda: self.设置星级筛选(None),
                )

    # ✅ 若选歌内部触发了退出
    if bool(getattr(self, "_需要退出", False)):
        return str(getattr(self, "_返回状态", "NORMAL") or "NORMAL")
    return None


def 选歌_处理事件_外部_热刷新(self, 事件):
    # ✅ F5：强制热刷新（不依赖mtime）
    try:
        if 事件 is not None and 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F5:
            try:
                self.调试_热刷新选歌布局(是否提示=True)
            except Exception:
                pass
            return None
    except Exception:
        pass

    # 其它事件交给原版处理
    try:
        return 选歌_处理事件_外部(self, 事件)
    except Exception:
        return None


def 绑定场景化方法到选歌游戏类():
    选歌游戏.绑定外部屏幕 = 选歌_绑定外部屏幕
    选歌游戏.帧更新 = 选歌_帧更新
    选歌游戏.帧绘制 = 选歌_帧绘制

    # ✅ 关键：用包装器接管 F5
    选歌游戏.处理事件_外部 = 选歌_处理事件_外部_热刷新


绑定场景化方法到选歌游戏类()


def main():
    资源根目录 = _取项目根目录()
    songs根目录 = _取songs根目录()
    背景音乐路径 = os.path.join(资源根目录, "冷资源", "backsound", "devil.mp3")
    logo路径 = os.path.join(_取运行根目录(), "res", "logo", "base.png")

    游戏 = 选歌游戏(
        songs根目录=songs根目录,
        背景音乐路径=背景音乐路径,
        logo路径=logo路径,
        是否继承已有窗口=False,
    )
    游戏.主循环()


def 运行选歌(玩家数: int, 类型名: str, 模式名: str, 背景音乐路径: str):
    songs根目录 = _取songs根目录()
    logo路径 = os.path.join(_取运行根目录(), "res", "logo", "base.png")

    游戏 = 选歌游戏(
        songs根目录=songs根目录,
        背景音乐路径=背景音乐路径,
        logo路径=logo路径,
        指定类型名=类型名,
        指定模式名=模式名,
        玩家数=玩家数,
        是否继承已有窗口=True,
    )
    return 游戏.主循环()


if __name__ == "__main__":
    main()
