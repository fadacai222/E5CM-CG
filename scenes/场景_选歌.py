
import os
import sys
import json
import re
import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Callable
from core.常量与路径 import (
    取项目根目录 as _公共取项目根目录,
    取运行根目录 as _公共取运行根目录,
    取songs根目录 as _公共取songs根目录,
)
from core.歌曲记录 import 读取歌曲记录索引, 取歌曲记录键
from core.对局状态 import 取当前关卡, 取累计S数, 是否赠送第四把
from core.踏板控制 import 踏板动作_左, 踏板动作_右, 踏板动作_确认
from ui.top栏 import 生成top栏
import pygame
from scenes.场景基类 import 场景基类


def 确保项目根目录在模块路径里():
    return

确保项目根目录在模块路径里()

_项目根目录_缓存: str | None = None
_运行根目录_缓存: str | None = None
_songs根目录_缓存: str | None = None


def _取项目根目录() -> str:
    global _项目根目录_缓存
    _项目根目录_缓存 = _公共取项目根目录()
    return _项目根目录_缓存


def _取运行根目录() -> str:
    global _运行根目录_缓存
    _运行根目录_缓存 = _公共取运行根目录()
    return _运行根目录_缓存


def _取songs根目录(资源: Optional[dict] = None, 状态: Optional[dict] = None) -> str:
    global _songs根目录_缓存
    _songs根目录_缓存 = _公共取songs根目录(资源=资源, 状态=状态)
    return _songs根目录_缓存


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
        try:
            路径文本 = os.path.abspath(str(原始songs根目录 or "").strip())
        except Exception:
            路径文本 = ""
        if 路径文本 and os.path.isdir(路径文本):
            return 路径文本
        return _取songs根目录(状态=状态)

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


        self._选歌实例 = 选歌游戏(
            songs根目录=songs根目录,
            背景音乐路径=背景音乐路径,
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


_UI原图缓存: Dict[str, Optional[pygame.Surface]] = {}
# _UI缩放缓存: Dict[Tuple[str, int, int, bool], Optional[pygame.Surface]] = {}

_缩略图_序号背景_缩放 = 1.5  
_缩略图_序号背景_x偏移 = 20  
_缩略图_序号背景_y偏移 = -20  
_缩略图_序号数字_缩放 = 1.6  
_缩略图_序号数字_x偏移 = -20 
_缩略图_序号数字_y偏移 = -20 
_缩略图_序号数字_右内边距占比 = 0.12  
_缩略图_序号数字_下内边距占比 = 0.12  
_大图_序号背景_缩放 = 1.70
_大图_序号背景_x偏移 = 0
_大图_序号背景_y偏移 = 0
_大图_序号数字_缩放 = 1.00
_大图_序号数字_x偏移 = 10
_大图_序号数字_y偏移 = 10
_详情大框贴图_宽缩放 = 1.07
_详情大框贴图_高缩放 = 1.02
_详情大框贴图_x偏移 = 0
_详情大框贴图_y偏移 = 0.01
_序号显示格式_缩略图 = "{:02d}"  # 01 02 03...
_序号显示格式_大图 = "{:02d}"  # 想大图显示不一样也行


def _设置页_配置项定义() -> Dict[str, Dict[str, str]]:
    return {
        "调速": {
            "索引属性": "设置_调速索引",
            "选项属性": "设置_调速选项",
            "参数键": "调速",
            "值前缀": "X",
        },
        "变速": {
            "索引属性": "设置_变速索引",
            "选项属性": "设置_变速选项",
            "参数键": "背景模式",
            "兼容参数键": "变速",
        },
        "变速类型": {
            "索引属性": "设置_谱面索引",
            "选项属性": "设置_谱面选项",
            "参数键": "谱面",
            "兼容参数键": "变速类型",
        },
        "隐藏": {
            "索引属性": "设置_隐藏索引",
            "选项属性": "设置_隐藏选项",
            "参数键": "隐藏",
        },
        "轨迹": {
            "索引属性": "设置_轨迹索引",
            "选项属性": "设置_轨迹选项",
            "参数键": "轨迹",
        },
        "方向": {
            "索引属性": "设置_方向索引",
            "选项属性": "设置_方向选项",
            "参数键": "方向",
        },
        "大小": {
            "索引属性": "设置_大小索引",
            "选项属性": "设置_大小选项",
            "参数键": "大小",
        },
        "箭头": {
            "索引属性": "设置_箭头索引",
            "选项属性": "设置_箭头候选路径列表",
            "参数键": "箭头",
            "值类型": "文件名",
        },
        "背景": {
            "索引属性": "设置_背景索引",
            "选项属性": "设置_背景大图文件名列表",
            "参数键": "背景",
            "值类型": "原值",
        },
    }

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
    if not isinstance(数据, dict) or (not 数据):
        return

    配置定义 = _设置页_配置项定义()
    索引表 = 数据.get("索引", {})
    if not isinstance(索引表, dict):
        索引表 = {}

    参数 = 数据.get("设置参数", {})
    if not isinstance(参数, dict):
        参数 = {}

    参数文本 = str(数据.get("设置参数文本", "") or "")
    背景文件名 = str(数据.get("背景文件名", 参数.get("背景", "")) or "")
    箭头文件名 = str(数据.get("箭头文件名", 参数.get("箭头", "")) or "")
    动态背景模式 = str(
        数据.get(
            "动态背景",
            参数.get("动态背景", _设置页_从参数文本提取(参数文本, "动态背景")),
        )
        or ""
    ).strip()

    if not 背景文件名:
        背景文件名 = _设置页_从参数文本提取(参数文本, "背景")
    if not 箭头文件名:
        箭头文件名 = _设置页_从参数文本提取(参数文本, "箭头")

    for 行键, 定义 in 配置定义.items():
        索引属性 = str(定义.get("索引属性", "") or "")
        选项属性 = str(定义.get("选项属性", "") or "")
        参数键 = str(定义.get("参数键", "") or "")
        兼容参数键 = str(定义.get("兼容参数键", "") or "")
        值类型 = str(定义.get("值类型", "") or "")

        选项列表 = list(getattr(self, 选项属性, []) or [])
        if (not 索引属性) or (not 选项列表):
            continue

        默认索引 = int(getattr(self, 索引属性, 0) or 0)

        try:
            索引值 = int(索引表.get(参数键, 索引表.get(兼容参数键, 默认索引)) or 默认索引)
        except Exception:
            索引值 = 默认索引
        索引值 = max(0, min(len(选项列表) - 1, 索引值))
        setattr(self, 索引属性, 索引值)

        候选值 = ""
        if 值类型 == "文件名":
            候选值 = 箭头文件名
        elif 值类型 == "原值":
            候选值 = 背景文件名
        elif 参数键 == "背景模式" and 动态背景模式 and 动态背景模式 != "关闭":
            候选值 = "动态背景"
        else:
            候选值 = str(参数.get(参数键, 参数.get(兼容参数键, "")) or "").strip()

        if 参数键 == "调速":
            候选值 = 候选值.replace("x", "X")
            if 候选值.startswith("X"):
                候选值 = 候选值[1:]

        if not 候选值:
            continue

        if 值类型 == "文件名":
            for 序号, 路径 in enumerate(选项列表):
                if os.path.basename(str(路径 or "")) == 候选值:
                    setattr(self, 索引属性, int(序号))
                    break
            continue

        try:
            命中索引 = 选项列表.index(候选值)
            setattr(self, 索引属性, int(命中索引))
        except Exception:
            pass

def _设置页_保存持久化设置(self) -> bool:
    配置定义 = _设置页_配置项定义()

    设置参数 = dict(getattr(self, "设置_参数", {}) or {})
    背景文件名 = str(getattr(self, "设置_背景大图文件名", "") or "")
    箭头文件名 = str(getattr(self, "设置_箭头文件名", "") or "")

    索引表: Dict[str, int] = {}
    for _行键, 定义 in 配置定义.items():
        索引属性 = str(定义.get("索引属性", "") or "")
        参数键 = str(定义.get("参数键", "") or "")
        兼容参数键 = str(定义.get("兼容参数键", "") or "")
        if (not 索引属性) or (not 参数键):
            continue

        try:
            当前索引 = int(getattr(self, 索引属性, 0) or 0)
        except Exception:
            当前索引 = 0

        索引表[参数键] = 当前索引
        if 兼容参数键:
            索引表[兼容参数键] = 当前索引

    数据 = {
        "设置参数": 设置参数,
        "动态背景": str(设置参数.get("动态背景", "关闭") or "关闭"),
        "背景文件名": 背景文件名,
        "箭头文件名": 箭头文件名,
        "设置参数文本": _设置页_构建参数文本(
            self,
            设置参数=设置参数,
            背景文件名=背景文件名,
            箭头文件名=箭头文件名,
        ),
        "索引": 索引表,
    }
    return _设置页_写入持久化设置(self, 数据)


def _确保设置页资源(self):
    if getattr(self, "_设置页_资源已初始化", False):
        return
    self._设置页_资源已初始化 = True

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
    self._设置页_布局缩放 = 1.0

    self.设置_调速选项 = 设置菜单默认调速选项()
    self.设置_变速选项 = ["图片", "视频", "动态背景"]
    self.设置_谱面选项 = ["正常", "未知"]
    self.设置_隐藏选项 = ["关闭", "半隐", "全隐"]
    self.设置_轨迹选项 = ["正常", "摇摆", "旋转"]
    self.设置_方向选项 = ["关闭", "反向"]
    self.设置_大小选项 = ["正常", "放大"]

    self.设置_调速索引 = 0
    self.设置_变速索引 = 0
    self.设置_谱面索引 = 0
    self.设置_隐藏索引 = 0
    self.设置_轨迹索引 = 0
    self.设置_方向索引 = 0
    self.设置_大小索引 = 0
    self.设置_箭头索引 = 0
    self.设置_背景索引 = 0

    self.设置_箭头候选路径列表 = []
    self._设置页_箭头候选原图缓存 = {}
    箭头候选目录 = _资源路径("UI-img", "选歌界面资源", "设置", "设置-箭头候选")
    if os.path.isdir(箭头候选目录):
        for 文件名 in sorted(os.listdir(箭头候选目录)):
            if str(文件名 or "").lower().endswith(".png"):
                self.设置_箭头候选路径列表.append(os.path.join(箭头候选目录, 文件名))

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

    self._设置页_缩放缓存 = {}
    self._设置页_背景图原图 = 安全加载图片(
        _资源路径("UI-img", "选歌界面资源", "设置", "设置背景图.png"),
        透明=True,
    )
    self._设置页_动态背景预览原图 = 安全加载图片(
        _资源路径("UI-img", "动态背景", "唱片", "素材", "唱片.png"),
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

    self._设置页_背景缩放缓存图 = None
    self._设置页_背景缩放缓存尺寸 = (0, 0)

    self._设置页_调试器 = 设置页布局调试器(
        os.path.join(_取运行根目录(), "json", "选歌设置页调试.json")
    )
    

def _设置页_同步参数(self):
    配置定义 = _设置页_配置项定义()
    输出参数: Dict[str, str] = {}

    for 行键, 定义 in 配置定义.items():
        索引属性 = str(定义.get("索引属性", "") or "")
        选项属性 = str(定义.get("选项属性", "") or "")
        参数键 = str(定义.get("参数键", "") or "")
        值前缀 = str(定义.get("值前缀", "") or "")
        值类型 = str(定义.get("值类型", "") or "")

        选项列表 = list(getattr(self, 选项属性, []) or [])
        if (not 参数键) or (not 选项列表):
            continue

        try:
            当前索引 = int(getattr(self, 索引属性, 0) or 0)
        except Exception:
            当前索引 = 0
        当前索引 = max(0, min(len(选项列表) - 1, 当前索引))

        当前值 = 选项列表[当前索引]

        if 值类型 == "文件名":
            当前值 = os.path.basename(str(当前值 or ""))
        else:
            当前值 = str(当前值 or "")

        if 参数键 == "箭头":
            self.设置_箭头文件名 = 当前值
        elif 参数键 == "背景":
            self.设置_背景大图文件名 = 当前值
        elif 参数键 == "背景模式":
            if 当前值 == "动态背景":
                输出参数["背景模式"] = "图片"
                输出参数["动态背景"] = "唱片"
            else:
                输出参数["背景模式"] = 当前值
                输出参数["动态背景"] = "关闭"
        else:
            输出参数[参数键] = f"{值前缀}{当前值}" if 值前缀 else 当前值

    if not hasattr(self, "设置_箭头文件名"):
        self.设置_箭头文件名 = ""
    if not hasattr(self, "设置_背景大图文件名"):
        self.设置_背景大图文件名 = ""

    self.设置_参数 = 输出参数

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

def 绘制设置页(self):
    self._确保设置页资源()
    self._重算设置页布局()

    动画参数 = _设置页_取动画参数(self)
    if not bool(动画参数.get("是否可见", False)):
        return

    视觉参数 = dict(getattr(self, "_设置页_视觉参数", {}) or {})
    箭头预览内边距 = max(0, int(视觉参数.get("箭头预览内边距", 0) or 0))

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

    标签字号 = int(视觉参数.get("标签字号", 24) or 24)
    选项字号 = int(视觉参数.get("选项字号", 26) or 26)
    小字字号 = int(视觉参数.get("小字字号", 16) or 16)
    内容内边距 = int(视觉参数.get("内容内边距", 10) or 10)
    名称下移 = int(视觉参数.get("名称下移", 1) or 1)
    箭头名称上间距 = int(视觉参数.get("箭头名称上间距", 18) or 18)
    底部保护边距 = int(视觉参数.get("底部保护边距", 6) or 6)

    for 行键, 控件 in self._设置页_控件矩形表.items():
        左箭 = 控件["左"]
        右箭 = 控件["右"]
        内容 = 控件["内容"]

        行文字缩放 = 1.0
        try:
            if getattr(self, "_设置页_调试器", None) is not None:
                行文字缩放 = float(self._设置页_调试器.取行文字缩放(行键))
        except Exception:
            行文字缩放 = 1.0
        行文字缩放 = max(0.50, min(3.00, 行文字缩放))

        行标签字体 = 获取字体(max(8, int(round(标签字号 * 行文字缩放))), 是否粗体=False)
        行选项字体 = 获取字体(max(8, int(round(选项字号 * 行文字缩放))), 是否粗体=True)
        小字字体 = 获取字体(小字字号, 是否粗体=False)

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
        值 = 设置菜单行值(行键, getattr(self, "设置_参数", {}))

        绘制文本(
            面板画布,
            显示名,
            行标签字体,
            (235, 245, 255),
            (内容.x + 内容内边距, 内容.centery + 名称下移),
            对齐="midleft",
        )

        绘制文本(
            面板画布,
            值,
            行选项字体,
            (255, 255, 255),
            (内容.right - 内容内边距, 内容.centery),
            对齐="midright",
        )

    预览框 = getattr(self, "_设置页_箭头预览矩形", pygame.Rect(0, 0, 10, 10))
    小字字体 = 获取字体(小字字号, 是否粗体=False)

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
            内边距 = max(0, int(箭头预览内边距))
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
                        min(
                            面板画布.get_height() - 底部保护边距,
                            预览框.bottom + 箭头名称上间距,
                        ),
                    ),
                    对齐="midtop",
                )
        except Exception:
            pass

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

    当前背景模式 = 设置菜单行值("变速", getattr(self, "设置_参数", {}))
    当前缩略图路径 = None
    if self.设置_背景缩略图路径列表:
        当前缩略图路径 = self.设置_背景缩略图路径列表[self.设置_背景索引]

    缩略图 = None
    if 当前背景模式 == "动态背景":
        缩略图 = getattr(self, "_设置页_动态背景预览原图", None)
    elif 当前缩略图路径:
        缩略图 = self._设置页_背景缩略图原图缓存.get(当前缩略图路径)
        if 缩略图 is None:
            缩略图 = 安全加载图片(当前缩略图路径, 透明=True)
            self._设置页_背景缩略图原图缓存[当前缩略图路径] = 缩略图

    if 缩略图 is not None:
        try:
            if 当前背景模式 == "动态背景":
                pygame.draw.rect(面板画布, (8, 14, 22), 预览区, border_radius=12)
                可用区 = 预览区.inflate(-24, -24)
                ow, oh = 缩略图.get_size()
                比例 = min(float(可用区.w) / float(max(1, ow)), float(可用区.h) / float(max(1, oh)))
                nw = max(1, int(round(float(ow) * 比例)))
                nh = max(1, int(round(float(oh) * 比例)))
                预览图 = pygame.transform.smoothscale(缩略图, (nw, nh)).convert_alpha()
                面板画布.blit(
                    预览图,
                    (
                        int(可用区.centerx - nw // 2),
                        int(可用区.centery - nh // 2),
                    ),
                )
            else:
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

    try:
        if getattr(self, "_设置页_调试器", None) is not None:
            self._设置页_调试器.绘制覆盖(self, 面板画布)
    except Exception:
        pass

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
    
def 打开设置页(self):
    self._确保设置页资源()

    try:
        self.是否星级筛选页 = False
        self.是否模式选择页 = False
    except Exception:
        pass

    self._设置页_上次屏幕尺寸 = (0, 0)
    self._设置页_面板绘制矩形 = pygame.Rect(0, 0, 10, 10)
    self._设置页_最后绘制表面 = None
    self._设置页_最后缩放 = 1.0

    self._重算设置页布局(强制=True)
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

    配置定义 = _设置页_配置项定义()
    定义 = 配置定义.get(str(行键 or ""), None)
    if not isinstance(定义, dict):
        return

    索引属性 = str(定义.get("索引属性", "") or "")
    选项属性 = str(定义.get("选项属性", "") or "")
    if (not 索引属性) or (not 选项属性):
        return

    选项列表 = list(getattr(self, 选项属性, []) or [])
    总数 = len(选项列表)
    if 总数 <= 0:
        return

    try:
        当前索引 = int(getattr(self, 索引属性, 0) or 0)
    except Exception:
        当前索引 = 0

    当前索引 = (当前索引 + 方向) % 总数
    setattr(self, 索引属性, 当前索引)

    self._设置页_同步参数()

    try:
        self._设置页_保存持久化设置()
    except Exception:
        pass

    self._设置页_上次屏幕尺寸 = (0, 0)
    self._设置页_最后绘制表面 = None
    self._设置页_最后缩放 = 1.0
    self._重算设置页布局(强制=True)

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

    self._设置页_上次屏幕尺寸 = (0, 0)
    self._设置页_最后绘制表面 = None
    self._设置页_最后缩放 = 1.0
    self._重算设置页布局(强制=True)

def _设置页_处理事件(self, 事件):
    self._确保设置页资源()
    self._重算设置页布局()

    if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F6:
        try:
            self._设置页_调试器.切换启用()
            if hasattr(self, "显示消息提示"):
                if bool(self._设置页_调试器.是否启用):
                    self.显示消息提示("设置页调试器：已开启", 持续秒=1.2)
                else:
                    self.显示消息提示("设置页调试器：已关闭", 持续秒=1.2)
        except Exception:
            pass
        return

    try:
        if getattr(self, "_设置页_调试器", None) is not None and bool(self._设置页_调试器.是否启用):
            if self._设置页_调试器.处理事件(self, 事件):
                return
    except Exception:
        pass

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

    if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
        self.关闭设置页()
        return

    if 事件.type != pygame.MOUSEBUTTONDOWN or 事件.button != 1:
        return

    if not self._设置页_点在有效面板区域(事件.pos):
        self.关闭设置页()
        return

    局部点 = _转局部坐标(事件.pos)

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

    背景控件 = self._设置页_背景控件矩形
    if 背景控件["左"].collidepoint(局部点):
        self._播放按钮音效()
        self._设置页_切换背景(-1)
        return
    if 背景控件["右"].collidepoint(局部点):
        self._播放按钮音效()
        self._设置页_切换背景(+1)
        return

    for 行键, 控件 in self._设置页_控件矩形表.items():
        if 控件["左"].collidepoint(局部点):
            self._播放按钮音效()
            self._设置页_切换选项(行键, -1)
            return
        if 控件["右"].collidepoint(局部点):
            self._播放按钮音效()
            self._设置页_切换选项(行键, +1)
            return


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

_选歌布局_缓存: dict | None = None
_选歌布局_修改时间: float = -1.0
_选歌布局_最近检查时刻: float = -999.0

def _选歌布局_文件路径() -> str:
    return os.path.join(_取项目根目录(), "json", "选歌布局.json")

def _选歌布局_默认值() -> dict:
    return {
        "缩略图小框": {
            "_缩略图小框_宽缩放": 1.0,
            "_缩略图小框_高缩放": 1.0,
            "_缩略图小框_x偏移": 0.0,
            "_缩略图小框_y偏移": 0.2,
            "_缩略图封面_y下移像素": 8,
        },
        "缩略图大框": {
            "_缩略图大框_宽缩放": 1.1,
            "_缩略图大框_高缩放": 1.15,
            "_缩略图大框_x偏移": 0.0,
            "_缩略图大框_y偏移": 0.0,
        },
        "序号标签": {
            "_缩略图_序号背景_缩放": 1.5,
            "_缩略图_序号背景_x偏移": 20,
            "_缩略图_序号背景_y偏移": -20,
            "_缩略图_序号数字_缩放": 1.6,
            "_缩略图_序号数字_x偏移": -20,
            "_缩略图_序号数字_y偏移": -20,
            "_缩略图_序号数字_右内边距占比": 0.12,
            "_缩略图_序号数字_下内边距占比": 0.12,
            "_序号显示格式_缩略图": "{:02d}",
        },
    }

def _安全转浮点(值, 默认值: float) -> float:
    try:
        return float(值)
    except Exception:
        return float(默认值)

def _安全转整数(值, 默认值: int) -> int:
    try:
        return int(round(float(值)))
    except Exception:
        return int(默认值)

def 读取选歌布局配置() -> dict:
    global _选歌布局_缓存, _选歌布局_修改时间, _选歌布局_最近检查时刻

    当前时刻 = float(time.perf_counter())
    if (
        _选歌布局_缓存 is not None
        and (当前时刻 - float(_选歌布局_最近检查时刻)) < 0.25
    ):
        return _选歌布局_缓存

    路径 = _选歌布局_文件路径()
    try:
        修改时间 = os.path.getmtime(路径) if os.path.isfile(路径) else 0.0
    except Exception:
        修改时间 = 0.0
    _选歌布局_最近检查时刻 = 当前时刻

    if _选歌布局_缓存 is not None and float(_选歌布局_修改时间) == float(修改时间):
        return _选歌布局_缓存

    数据 = _选歌布局_默认值()

    if os.path.isfile(路径):
        for 编码 in ("utf-8-sig", "utf-8", "gbk"):
            try:
                with open(路径, "r", encoding=编码) as 文件:
                    读取数据 = json.load(文件)
                if isinstance(读取数据, dict):
                    数据 = 读取数据
                break
            except Exception:
                continue

    if not isinstance(数据, dict):
        数据 = _选歌布局_默认值()

    _选歌布局_缓存 = 数据
    _选歌布局_修改时间 = float(修改时间)
    _应用选歌布局常量(数据)
    return 数据

def _应用选歌布局常量(配置: dict):
    global _缩略图小框_宽缩放
    global _缩略图小框_高缩放
    global _缩略图小框_x偏移
    global _缩略图小框_y偏移
    global _缩略图封面_y下移像素

    global _缩略图大框_宽缩放
    global _缩略图大框_高缩放
    global _缩略图大框_x偏移
    global _缩略图大框_y偏移

    global _缩略图_序号背景_缩放
    global _缩略图_序号背景_x偏移
    global _缩略图_序号背景_y偏移
    global _缩略图_序号数字_缩放
    global _缩略图_序号数字_x偏移
    global _缩略图_序号数字_y偏移
    global _缩略图_序号数字_右内边距占比
    global _缩略图_序号数字_下内边距占比
    global _序号显示格式_缩略图

    默认值 = _选歌布局_默认值()

    小框 = 配置.get("缩略图小框", {})
    if not isinstance(小框, dict):
        小框 = {}
    小框默认 = 默认值["缩略图小框"]

    _缩略图小框_宽缩放 = max(
        0.05,
        min(
            5.0,
            _安全转浮点(
                小框.get("_缩略图小框_宽缩放", 小框默认["_缩略图小框_宽缩放"]),
                小框默认["_缩略图小框_宽缩放"],
            ),
        ),
    )
    _缩略图小框_高缩放 = max(
        0.05,
        min(
            5.0,
            _安全转浮点(
                小框.get("_缩略图小框_高缩放", 小框默认["_缩略图小框_高缩放"]),
                小框默认["_缩略图小框_高缩放"],
            ),
        ),
    )
    _缩略图小框_x偏移 = _安全转整数(
        小框.get("_缩略图小框_x偏移", 小框默认["_缩略图小框_x偏移"]),
        int(小框默认["_缩略图小框_x偏移"]),
    )
    _缩略图小框_y偏移 = _安全转浮点(
        小框.get("_缩略图小框_y偏移", 小框默认["_缩略图小框_y偏移"]),
        float(小框默认["_缩略图小框_y偏移"]),
    )
    _缩略图封面_y下移像素 = _安全转整数(
        小框.get("_缩略图封面_y下移像素", 小框默认["_缩略图封面_y下移像素"]),
        int(小框默认["_缩略图封面_y下移像素"]),
    )

    大框 = 配置.get("缩略图大框", {})
    if not isinstance(大框, dict):
        大框 = {}
    大框默认 = 默认值["缩略图大框"]

    _缩略图大框_宽缩放 = max(
        0.05,
        min(
            5.0,
            _安全转浮点(
                大框.get("_缩略图大框_宽缩放", 大框默认["_缩略图大框_宽缩放"]),
                大框默认["_缩略图大框_宽缩放"],
            ),
        ),
    )
    _缩略图大框_高缩放 = max(
        0.05,
        min(
            5.0,
            _安全转浮点(
                大框.get("_缩略图大框_高缩放", 大框默认["_缩略图大框_高缩放"]),
                大框默认["_缩略图大框_高缩放"],
            ),
        ),
    )
    _缩略图大框_x偏移 = _安全转整数(
        大框.get("_缩略图大框_x偏移", 大框默认["_缩略图大框_x偏移"]),
        int(大框默认["_缩略图大框_x偏移"]),
    )
    _缩略图大框_y偏移 = _安全转整数(
        大框.get("_缩略图大框_y偏移", 大框默认["_缩略图大框_y偏移"]),
        int(大框默认["_缩略图大框_y偏移"]),
    )

    序号 = 配置.get("序号标签", {})
    if not isinstance(序号, dict):
        序号 = {}
    序号默认 = 默认值["序号标签"]

    _缩略图_序号背景_缩放 = max(
        0.05,
        min(
            5.0,
            _安全转浮点(
                序号.get("_缩略图_序号背景_缩放", 序号默认["_缩略图_序号背景_缩放"]),
                序号默认["_缩略图_序号背景_缩放"],
            ),
        ),
    )
    _缩略图_序号背景_x偏移 = _安全转整数(
        序号.get("_缩略图_序号背景_x偏移", 序号默认["_缩略图_序号背景_x偏移"]),
        int(序号默认["_缩略图_序号背景_x偏移"]),
    )
    _缩略图_序号背景_y偏移 = _安全转整数(
        序号.get("_缩略图_序号背景_y偏移", 序号默认["_缩略图_序号背景_y偏移"]),
        int(序号默认["_缩略图_序号背景_y偏移"]),
    )
    _缩略图_序号数字_缩放 = max(
        0.05,
        min(
            5.0,
            _安全转浮点(
                序号.get("_缩略图_序号数字_缩放", 序号默认["_缩略图_序号数字_缩放"]),
                序号默认["_缩略图_序号数字_缩放"],
            ),
        ),
    )
    _缩略图_序号数字_x偏移 = _安全转整数(
        序号.get("_缩略图_序号数字_x偏移", 序号默认["_缩略图_序号数字_x偏移"]),
        int(序号默认["_缩略图_序号数字_x偏移"]),
    )
    _缩略图_序号数字_y偏移 = _安全转整数(
        序号.get("_缩略图_序号数字_y偏移", 序号默认["_缩略图_序号数字_y偏移"]),
        int(序号默认["_缩略图_序号数字_y偏移"]),
    )
    _缩略图_序号数字_右内边距占比 = max(
        0.0,
        min(
            1.0,
            _安全转浮点(
                序号.get(
                    "_缩略图_序号数字_右内边距占比",
                    序号默认["_缩略图_序号数字_右内边距占比"],
                ),
                序号默认["_缩略图_序号数字_右内边距占比"],
            ),
        ),
    )
    _缩略图_序号数字_下内边距占比 = max(
        0.0,
        min(
            1.0,
            _安全转浮点(
                序号.get(
                    "_缩略图_序号数字_下内边距占比",
                    序号默认["_缩略图_序号数字_下内边距占比"],
                ),
                序号默认["_缩略图_序号数字_下内边距占比"],
            ),
        ),
    )
    _序号显示格式_缩略图 = str(
        序号.get("_序号显示格式_缩略图", 序号默认["_序号显示格式_缩略图"])
        or 序号默认["_序号显示格式_缩略图"]
    )

def 刷新选歌布局常量():
    读取选歌布局配置()

刷新选歌布局常量()

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

_字体对象缓存: Dict[Tuple[str, int, bool], pygame.font.Font] = {}
_字体默认路径缓存: Dict[bool, str] = {}  

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
      - cover   : 等比铺满，超出裁切
      - contain : 等比完整显示，留透明边
      - stretch : 直接拉伸铺满
    """
    try:
        原图 = pygame.image.load(路径).convert_alpha()
    except Exception:
        return None

    try:
        目标宽 = max(1, int(目标宽))
        目标高 = max(1, int(目标高))
    except Exception:
        return None

    try:
        ow, oh = 原图.get_size()
    except Exception:
        return None

    if ow <= 0 or oh <= 0:
        return None

    模式 = str(模式 or "cover").strip().lower()
    if 模式 not in ("cover", "contain", "stretch"):
        模式 = "cover"

    try:
        if 模式 == "stretch":
            结果图 = pygame.transform.smoothscale(原图, (目标宽, 目标高)).convert_alpha()
            if 圆角 > 0:
                蒙版 = 生成圆角蒙版(目标宽, 目标高, 圆角)
                结果图.blit(蒙版, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            return 结果图

        if 模式 == "contain":
            比例 = min(目标宽 / ow, 目标高 / oh)
            新宽 = max(1, int(round(ow * 比例)))
            新高 = max(1, int(round(oh * 比例)))
            缩放图 = pygame.transform.smoothscale(原图, (新宽, 新高)).convert_alpha()

            结果图 = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
            结果图.fill((0, 0, 0, 0))
            x = (目标宽 - 新宽) // 2
            y = (目标高 - 新高) // 2
            结果图.blit(缩放图, (x, y))

            if 圆角 > 0:
                蒙版 = 生成圆角蒙版(目标宽, 目标高, 圆角)
                结果图.blit(蒙版, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            return 结果图

        比例 = max(目标宽 / ow, 目标高 / oh)
        新宽 = max(1, int(round(ow * 比例)))
        新高 = max(1, int(round(oh * 比例)))
        缩放图 = pygame.transform.smoothscale(原图, (新宽, 新高)).convert_alpha()

        x = (新宽 - 目标宽) // 2
        y = (新高 - 目标高) // 2

        结果图 = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
        结果图.fill((0, 0, 0, 0))
        结果图.blit(缩放图, (0, 0), area=pygame.Rect(x, y, 目标宽, 目标高))

        if 圆角 > 0:
            蒙版 = 生成圆角蒙版(目标宽, 目标高, 圆角)
            结果图.blit(蒙版, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return 结果图
    except Exception:
        return None

def 计算框体槽位布局(框体矩形: pygame.Rect, 是否大图: bool) -> dict:
    """
    稳定版槽位布局：
    - 不再用“目标像素尺寸反推倍率”的屎味算法
    - 统一按框体内部的相对比例取槽位
    - 小图/大图都保证槽位不会跑出框体
    """
    框宽 = max(1, int(框体矩形.w))
    框高 = max(1, int(框体矩形.h))

    if 是否大图:
        参数 = {
            "封面左占比": 0.05,
            "封面上占比": 0.05,
            "封面宽占比": 0.95,
            "封面高占比": 1.0,
            "信息条高占比": 0.35,
            "信息条左右内边距占比": 0.040,
            "星区上内边距占比": 0.050,
            "星区高占比": 0.3,
            "文本区左右内边距占比": 0.050,
            "底栏高占比": 0.245,
        }
    else:
        参数 = {
            "封面左占比": 0.10,
            "封面上占比": 0.060,
            "封面宽占比": 0.845,
            "封面高占比": 0.870,
            "信息条高占比": 0.315,
            "信息条左右内边距占比": 0.035,
            "星区上内边距占比": 0,
            "星区高占比": 0.6,
            "文本区左右内边距占比": 0.040,
            "底栏高占比": 0.345,
        }

    def _夹紧矩形(矩形: pygame.Rect, 外框: pygame.Rect) -> pygame.Rect:
        x = max(外框.left, min(矩形.x, 外框.right - 1))
        y = max(外框.top, min(矩形.y, 外框.bottom - 1))
        w = max(1, min(矩形.w, 外框.right - x))
        h = max(1, min(矩形.h, 外框.bottom - y))
        return pygame.Rect(x, y, w, h)

    封面矩形 = pygame.Rect(
        int(round(框体矩形.x + 框宽 * 参数["封面左占比"])),
        int(round(框体矩形.y + 框高 * 参数["封面上占比"])),
        max(1, int(round(框宽 * 参数["封面宽占比"]))),
        max(1, int(round(框高 * 参数["封面高占比"]))),
    )
    封面矩形 = _夹紧矩形(封面矩形, 框体矩形)

    信息条高 = max(14, int(round(封面矩形.h * 参数["信息条高占比"])))
    信息条矩形 = pygame.Rect(
        封面矩形.x,
        封面矩形.bottom - 信息条高,
        封面矩形.w,
        信息条高,
    )
    信息条矩形 = _夹紧矩形(信息条矩形, 封面矩形)

    信息条左右内边距 = max(
        4, int(round(信息条矩形.w * 参数["信息条左右内边距占比"]))
    )
    文本区左右内边距 = max(
        4, int(round(信息条矩形.w * 参数["文本区左右内边距占比"]))
    )

    星星区域 = pygame.Rect(
        信息条矩形.x + 信息条左右内边距,
        信息条矩形.y + max(1, int(round(信息条矩形.h * 参数["星区上内边距占比"]))),
        max(10, 信息条矩形.w - 信息条左右内边距 * 2),
        max(6, int(round(信息条矩形.h * 参数["星区高占比"]))),
    )
    星星区域 = _夹紧矩形(星星区域, 信息条矩形)

    底栏高 = max(10, int(round(信息条矩形.h * 参数["底栏高占比"])))
    底栏矩形 = pygame.Rect(
        信息条矩形.x + 文本区左右内边距,
        信息条矩形.bottom - 底栏高 - max(1, int(round(信息条矩形.h * 0.06))),
        max(10, 信息条矩形.w - 文本区左右内边距 * 2),
        底栏高,
    )
    底栏矩形 = _夹紧矩形(底栏矩形, 信息条矩形)

    中间安全间距 = max(8, int(round(底栏矩形.w * 0.05)))
    左区宽 = max(10, int(round(底栏矩形.w * 0.52)))
    左区宽 = min(左区宽, max(10, 底栏矩形.w - 中间安全间距 - 10))
    右区宽 = max(10, 底栏矩形.w - 左区宽 - 中间安全间距)

    游玩区域 = pygame.Rect(
        底栏矩形.x,
        底栏矩形.y,
        左区宽,
        底栏矩形.h,
    )
    bpm区域 = pygame.Rect(
        底栏矩形.right - 右区宽,
        底栏矩形.y,
        右区宽,
        底栏矩形.h,
    )

    游玩区域 = _夹紧矩形(游玩区域, 底栏矩形)
    bpm区域 = _夹紧矩形(bpm区域, 底栏矩形)

    return {
        "封面矩形": 封面矩形,
        "信息条矩形": 信息条矩形,
        "星星区域": 星星区域,
        "游玩区域": 游玩区域,
        "bpm区域": bpm区域,
    }

def 计算缩略图小框矩形(
    基准矩形: pygame.Rect,
    框路径: str,
) -> pygame.Rect:
    """
    小框专用：
    - 只允许等比缩放
    - 比例优先跟随“小框素材原图”
    - 宽高缩放配置不再分别直接作用到最终宽高，避免窗口一变就框体变形
    - x/y 偏移仍保留
    """
    try:
        框宽缩放 = float(_缩略图小框_宽缩放)
    except Exception:
        框宽缩放 = 1.0

    try:
        框高缩放 = float(_缩略图小框_高缩放)
    except Exception:
        框高缩放 = 1.0

    try:
        框x偏移 = int(_缩略图小框_x偏移)
    except Exception:
        框x偏移 = 0

    try:
        框y偏移 = int(round(float(_缩略图小框_y偏移) * float(基准矩形.h)))
    except Exception:
        框y偏移 = 0

    框宽缩放 = max(0.05, min(5.0, 框宽缩放))
    框高缩放 = max(0.05, min(5.0, 框高缩放))

    # ✅ 关键：小框只取一个“统一等比缩放值”
    统一缩放 = min(框宽缩放, 框高缩放)
    统一缩放 = max(0.05, min(5.0, 统一缩放))

    原框图 = 获取UI原图(框路径, 透明=True)

    # 优先使用素材真实比例；没有素材时退回当前卡片比例
    if 原框图 is not None:
        try:
            原宽, 原高 = 原框图.get_size()
        except Exception:
            原宽, 原高 = (0, 0)
    else:
        原宽, 原高 = (0, 0)

    if 原宽 <= 0 or 原高 <= 0:
        原宽 = max(1, int(基准矩形.w))
        原高 = max(1, int(基准矩形.h))

    原始比例 = float(原宽) / float(max(1, 原高))

    # ✅ 先基于“基准矩形”求一个可容纳的等比框
    候选宽 = max(1, int(round(float(基准矩形.w) * 统一缩放)))
    候选高 = max(1, int(round(float(基准矩形.h) * 统一缩放)))

    if 候选宽 <= 0 or 候选高 <= 0:
        return pygame.Rect(
            int(基准矩形.x + 框x偏移),
            int(基准矩形.y + 框y偏移),
            max(1, int(基准矩形.w)),
            max(1, int(基准矩形.h)),
        )

    if (float(候选宽) / float(max(1, 候选高))) > 原始比例:
        # 太宽了，以高为准反推宽
        框高 = 候选高
        框宽 = max(1, int(round(float(框高) * 原始比例)))
    else:
        # 太高了，以宽为准反推高
        框宽 = 候选宽
        框高 = max(1, int(round(float(框宽) / max(0.001, 原始比例))))

    # ✅ 仍然以原来的基准中心定位，偏移继续有效
    框矩形 = pygame.Rect(0, 0, 框宽, 框高)
    框矩形.center = 基准矩形.center
    框矩形.x += int(框x偏移)
    框矩形.y += int(框y偏移)

    return 框矩形

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
        self._静态缓存键 = None
        self._静态缓存图: Optional[pygame.Surface] = None

    def 更新布局(self, 矩形: pygame.Rect):
        self.矩形 = 矩形
        self._静态缓存键 = None
        self._静态缓存图 = None

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
        是否高亮 = bool(self.悬停 or self.踏板高亮)
        基准矩形 = self.矩形.copy()

        if 是否高亮:
            缩放 = 1.08 if bool(self.踏板高亮) else 1.04
            新宽 = max(1, int(round(self.矩形.w * 缩放)))
            新高 = max(1, int(round(self.矩形.h * 缩放)))
            基准矩形.size = (新宽, 新高)
            基准矩形.center = self.矩形.center

        框路径 = _资源路径("UI-img", "选歌界面资源", "缩略图小.png")

        try:
            框宽缩放 = float(_缩略图小框_宽缩放)
        except Exception:
            框宽缩放 = 1.0
        try:
            框高缩放 = float(_缩略图小框_高缩放)
        except Exception:
            框高缩放 = 1.0
        try:
            框x偏移 = int(_缩略图小框_x偏移)
        except Exception:
            框x偏移 = 0
        try:
            框y偏移 = int(round(float(_缩略图小框_y偏移) * float(基准矩形.h)))
        except Exception:
            框y偏移 = 0

        框宽缩放 = max(0.05, min(5.0, 框宽缩放))
        框高缩放 = max(0.05, min(5.0, 框高缩放))

        框矩形 = pygame.Rect(
            int(基准矩形.x + 框x偏移),
            int(基准矩形.y + 框y偏移),
            max(1, int(round(基准矩形.w * 框宽缩放))),
            max(1, int(round(基准矩形.h * 框高缩放))),
        )

        局部框矩形 = pygame.Rect(0, 0, 框矩形.w, 框矩形.h)
        局部布局 = 计算框体槽位布局(局部框矩形, 是否大图=False)

        局部封面矩形 = 局部布局["封面矩形"]
        局部信息条 = 局部布局["信息条矩形"]
        局部星星区域 = 局部布局["星星区域"]
        局部游玩区域 = 局部布局["游玩区域"]
        局部bpm区域 = 局部布局["bpm区域"]

        self.封面矩形 = pygame.Rect(
            框矩形.x + 局部封面矩形.x,
            框矩形.y + 局部封面矩形.y,
            局部封面矩形.w,
            局部封面矩形.h,
        )

        try:
            游玩次数 = int(max(0, int(getattr(self.歌曲, "游玩次数", 0) or 0)))
        except Exception:
            游玩次数 = 0

        缓存键 = (
            int(框矩形.w),
            int(框矩形.h),
            float(_选歌布局_修改时间),
            str(getattr(self.歌曲, "sm路径", "") or ""),
            str(getattr(self.歌曲, "封面路径", "") or ""),
            int(getattr(self.歌曲, "星级", 0) or 0),
            int(getattr(self.歌曲, "序号", 0) or 0),
            str(getattr(self.歌曲, "bpm", "") or ""),
            int(游玩次数),
            bool(getattr(self.歌曲, "是否VIP", False)),
            bool(getattr(self.歌曲, "是否HOT", False)),
            bool(getattr(self.歌曲, "是否NEW", False)),
        )
        局部画布 = self._静态缓存图 if self._静态缓存键 == 缓存键 else None
        if 局部画布 is None:
            局部画布 = pygame.Surface((框矩形.w, 框矩形.h), pygame.SRCALPHA)
            局部画布.fill((0, 0, 0, 0))

            封面缩放模式 = "cover"
            封面圆角 = 0

            封面图 = None
            if self.歌曲.封面路径:
                封面图 = 图缓存.获取(
                    self.歌曲.封面路径,
                    局部封面矩形.w,
                    局部封面矩形.h,
                    int(封面圆角),
                    封面缩放模式,
                )
                if 封面图 is None:
                    封面图 = 载入并缩放封面(
                        self.歌曲.封面路径,
                        局部封面矩形.w,
                        局部封面矩形.h,
                        int(封面圆角),
                        封面缩放模式,
                    )
                    if 封面图 is not None:
                        图缓存.写入(
                            self.歌曲.封面路径,
                            局部封面矩形.w,
                            局部封面矩形.h,
                            int(封面圆角),
                            封面缩放模式,
                            封面图,
                        )

            if 封面图 is not None:
                局部画布.blit(封面图, 局部封面矩形.topleft)
            else:
                pygame.draw.rect(局部画布, (30, 30, 40), 局部封面矩形)

            黑条 = pygame.Surface((局部信息条.w, 局部信息条.h), pygame.SRCALPHA)
            黑条.fill((0, 0, 0, 145))
            局部画布.blit(黑条, 局部信息条.topleft)

            小星星路径 = _资源路径("UI-img", "选歌界面资源", "小星星", "小星星.png")
            绘制星星行_图片(
                屏幕=局部画布,
                区域=局部星星区域,
                星数=self.歌曲.星级,
                星星路径=小星星路径,
                星星缩放倍数=0.42,
                每行最大=10,
            )

            bpm文本 = f"BPM:{self.歌曲.bpm}" if self.歌曲.bpm else "BPM:?"

            游玩标签字号 = max(8, int(局部信息条.h * 0.26))
            游玩数字字号 = max(8, int(局部信息条.h * 0.28))
            bpm字号 = max(9, int(局部信息条.h * 0.31))

            try:
                游玩标签字体 = 获取字体(游玩标签字号, 是否粗体=True)
                游玩数字字体 = 获取字体(游玩数字字号, 是否粗体=True)
                bpm字体 = 获取字体(bpm字号, 是否粗体=True)

                游玩标签面 = 渲染紧凑文本(
                    "游玩次数:",
                    游玩标签字体,
                    (235, 235, 235),
                    字符间距=-1,
                )
                游玩数字面 = 渲染紧凑文本(
                    str(游玩次数),
                    游玩数字字体,
                    (235, 235, 235),
                    字符间距=0,
                )
                bpm文面 = bpm字体.render(bpm文本, True, (255, 255, 255))

                游玩块宽 = int(游玩标签面.get_width()) + 2 + int(游玩数字面.get_width())
                游玩x = 局部游玩区域.x
                游玩y = 局部游玩区域.centery - max(
                    游玩标签面.get_height(),
                    游玩数字面.get_height(),
                ) // 2

                bpmx = 局部bpm区域.right - bpm文面.get_width()
                bpmy = 局部bpm区域.centery - bpm文面.get_height() // 2

                if 游玩x + 游玩块宽 > bpmx - 6:
                    压缩差值 = (游玩x + 游玩块宽) - (bpmx - 6)
                    bpmx += max(0, 压缩差值)

                局部画布.blit(游玩标签面, (游玩x, 游玩y))
                局部画布.blit(
                    游玩数字面,
                    (游玩x + int(游玩标签面.get_width()) + 2, 游玩y),
                )
                局部画布.blit(bpm文面, (bpmx, bpmy))
            except Exception:
                pass

            框图 = 获取UI容器图(
                框路径,
                框矩形.w,
                框矩形.h,
                缩放模式="stretch",
                透明=True,
            )
            if 框图 is not None:
                局部画布.blit(框图, (0, 0))

            绘制序号标签_图片(
                屏幕=局部画布,
                锚点矩形=局部框矩形,
                内部序号从0=self.歌曲.序号,
                是否大图=False,
            )

            if self.歌曲.是否VIP:
                vip路径 = _资源路径("UI-img", "选歌界面资源", "vip.png")
                vip原 = 获取UI原图(vip路径, 透明=True)
                if vip原 is not None:
                    vip高 = max(10, int(框矩形.h * 0.15))
                    vip图 = _按高等比缩放(vip原, vip高)
                    if vip图 is not None:
                        vipw, viph = vip图.get_size()
                        vx = 局部框矩形.right - vipw - max(2, int(vipw * 0.06))
                        vy = 局部框矩形.top - max(2, int(viph * -0.020))
                        局部画布.blit(vip图, (vx, vy))

            try:
                if bool(getattr(self.歌曲, "是否HOT", False)):
                    hot路径 = _资源路径("UI-img", "选歌界面资源", "热门.png")
                    hot原 = 获取UI原图(hot路径, 透明=True)
                    if hot原 is not None:
                        hot高 = max(12, int(框矩形.h * 0.18))
                        hot图 = _按高等比缩放(hot原, hot高)
                        if hot图 is not None:
                            hotw, hoth = hot图.get_size()
                            hx = 局部框矩形.right - hotw - max(4, int(hot高 * 0.10))
                            hy = 局部框矩形.top + max(4, int(hot高 * 0.06))
                            if bool(getattr(self.歌曲, "是否VIP", False)):
                                hx -= int(hotw * 0.82)
                            局部画布.blit(hot图, (hx, hy))
            except Exception:
                pass

            try:
                if bool(getattr(self.歌曲, "是否NEW", False)):
                    new路径 = _资源路径("UI-img", "选歌界面资源", "NEW绿色.png")
                    new原 = 获取UI原图(new路径, 透明=True)
                    if new原 is not None:
                        new高 = max(12, int(框矩形.h * 0.20))
                        new图 = _按高等比缩放(new原, new高)
                        if new图 is not None:
                            neww, newh = new图.get_size()
                            nx = 局部框矩形.right - neww - max(4, int(new高 * 0.10))
                            ny = 局部框矩形.bottom - newh - max(4, int(new高 * 0.10))
                            局部画布.blit(new图, (nx, ny))
            except Exception:
                pass

            self._静态缓存键 = 缓存键
            self._静态缓存图 = 局部画布

        屏幕.blit(局部画布, 框矩形.topleft)

class 选歌游戏:

    def __init__(
        self,
        songs根目录: str,
        背景音乐路径: str,
        指定类型名: str = "",
        指定模式名: str = "",
        玩家数: int = 1,
        是否继承已有窗口: Optional[bool] = None,
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
        self.玩家数 = 2 if 玩家数 == 2 else 1
        self.指定类型名 = str(指定类型名 or "").strip()
        self.指定模式名 = str(指定模式名 or "").strip()

        self._需要退出 = False
        self._返回状态 = "NORMAL"

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


        self.图缓存 = 图像缓存()
        self.预加载队列 = []
        self._待清理保留key集合 = None

        self.动画中 = False
        self.动画开始时间 = 0.0
        self.动画持续 = 0.35
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

        self._布局配置_缓存 = None
        self._布局配置_修改时间 = -1.0
        self._布局配置_最近检查时刻 = -999.0
        self._当前歌曲列表缓存键 = None
        self._当前歌曲列表缓存值: Tuple[List[歌曲信息], List[int]] = ([], [])
        self._背景暗层缓存: Optional[pygame.Surface] = None
        self._背景暗层缓存键: Tuple[int, int, int] = (0, 0, 0)
        self._背景音乐路径存在缓存键 = ""
        self._背景音乐路径存在缓存值 = False
        self._详情浮层静态缓存键 = None
        self._详情浮层静态缓存图: Optional[pygame.Surface] = None

        self._加载背景图()

        self.重算布局()
        self.确保播放背景音乐()
        self.安排预加载(基准页=self.当前页)

    def _布局配置文件路径(self) -> str:
        return os.path.join(_取项目根目录(), "json", "选歌布局.json")

    def _加载布局配置(self, 是否提示: bool = False) -> dict:
        try:
            import json
        except Exception:
            return {}

        当前时刻 = float(time.perf_counter())
        if (
            getattr(self, "_布局配置_缓存", None) is not None
            and (当前时刻 - float(getattr(self, "_布局配置_最近检查时刻", -999.0) or -999.0))
            < 0.25
        ):
            return self._布局配置_缓存

        路径 = self._布局配置文件路径()
        try:
            修改时间 = os.path.getmtime(路径) if os.path.isfile(路径) else 0.0
        except Exception:
            修改时间 = 0.0
        self._布局配置_最近检查时刻 = 当前时刻

        if getattr(self, "_布局配置_缓存", None) is not None and float(
            getattr(self, "_布局配置_修改时间", 0.0) or 0.0
        ) == float(修改时间):
            return self._布局配置_缓存

        数据 = {}
        if os.path.isfile(路径):
            try:
                with open(路径, "r", encoding="utf-8") as 文件:
                    数据 = json.load(文件)
            except Exception:
                数据 = {}

        if not isinstance(数据, dict):
            数据 = {}

        self._布局配置_缓存 = 数据
        self._布局配置_修改时间 = float(修改时间)
        return 数据
    
    def _取底部布局像素(
        self, 键路径: str, 默认设计像素: int, 最小: int = None, 最大: int = None
    ) -> int:
        """
        底部按钮专用：
        - 如果 json 里写的是普通数字（如 164），按“设计稿像素”处理，再随窗口同比缩放
        - 如果 json 里写的是字符串单位（如 0.08w / 0.12h / 0.09min），直接走原有逻辑
        - 这样能兼容旧配置，又不会让底部按钮焊死
        """
        原值 = self._取布局值(键路径, 默认设计像素)

        try:
            设计宽 = float(getattr(self, "_设计宽", 2048) or 2048)
            设计高 = float(getattr(self, "_设计高", 1152) or 1152)
            当前宽 = float(getattr(self, "宽", 0) or 0)
            当前高 = float(getattr(self, "高", 0) or 0)
            缩放 = min(
                当前宽 / max(1.0, 设计宽),
                当前高 / max(1.0, 设计高),
            )
        except Exception:
            缩放 = 1.0

        缩放 = max(0.45, min(2.20, float(缩放)))

        if isinstance(原值, str):
            文本 = str(原值 or "").strip().lower()
            if 文本:
                try:
                    return self._取布局像素(键路径, 默认设计像素, 最小=最小, 最大=最大)
                except Exception:
                    pass

        try:
            值 = int(round(float(原值) * 缩放))
        except Exception:
            值 = int(round(float(默认设计像素) * 缩放))

        if 最小 is not None:
            值 = max(int(最小), 值)
        if 最大 is not None:
            值 = min(int(最大), 值)
        return 值
    
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

    def 当前类型名(self) -> str:
        if not self.类型列表:
            return "无类型"
        return self.类型列表[self.当前类型索引]

    def 当前模式名(self) -> str:
        if not self.模式列表:
            return "无模式"
        return self.模式列表[self.当前模式索引]

    def _失效歌曲视图缓存(self):
        self._当前歌曲列表缓存键 = None
        self._当前歌曲列表缓存值 = ([], [])

    def _失效详情浮层缓存(self):
        self._详情浮层静态缓存键 = None
        self._详情浮层静态缓存图 = None

    def _构建详情浮层静态图(
        self,
        歌: 歌曲信息,
        框路径: str,
        内容基础矩形: pygame.Rect,
        局部封面框: pygame.Rect,
        局部信息条: pygame.Rect,
        局部星星区域: pygame.Rect,
        局部游玩区域: pygame.Rect,
        局部bpm区域: pygame.Rect,
        装饰贴图宽: int,
        装饰贴图高: int,
        贴图绘制x: int,
        贴图绘制y: int,
        内容偏移x: int,
        内容偏移y: int,
        总宽: int,
        总高: int,
    ) -> pygame.Surface:
        局部画布 = pygame.Surface((总宽, 总高), pygame.SRCALPHA)
        局部画布.fill((0, 0, 0, 0))

        封面图 = None
        if 歌.封面路径 and os.path.isfile(歌.封面路径):
            封面图 = self.图缓存.获取(
                歌.封面路径,
                局部封面框.w,
                局部封面框.h,
                0,
                "stretch",
            )
            if 封面图 is None:
                封面图 = 载入并缩放封面(
                    歌.封面路径,
                    局部封面框.w,
                    局部封面框.h,
                    0,
                    "stretch",
                )
                if 封面图 is not None:
                    self.图缓存.写入(
                        歌.封面路径,
                        局部封面框.w,
                        局部封面框.h,
                        0,
                        "stretch",
                        封面图,
                    )

        if 封面图 is not None:
            局部画布.blit(
                封面图,
                (局部封面框.x + 内容偏移x, 局部封面框.y + 内容偏移y),
            )
        else:
            pygame.draw.rect(
                局部画布,
                (18, 18, 24),
                pygame.Rect(
                    局部封面框.x + 内容偏移x,
                    局部封面框.y + 内容偏移y,
                    局部封面框.w,
                    局部封面框.h,
                ),
            )

        黑条 = pygame.Surface((局部信息条.w, 局部信息条.h), pygame.SRCALPHA)
        黑条.fill((0, 0, 0, 155))
        局部画布.blit(黑条, (局部信息条.x + 内容偏移x, 局部信息条.y + 内容偏移y))

        大星星路径 = _资源路径("UI-img", "选歌界面资源", "小星星", "大星星.png")
        光效路径 = _资源路径("UI-img", "选歌界面资源", "小星星", "星星动态.png")

        绘制星星行_图片(
            局部画布,
            pygame.Rect(
                局部星星区域.x + 内容偏移x,
                局部星星区域.y + 内容偏移y,
                局部星星区域.w,
                局部星星区域.h,
            ),
            歌.星级,
            大星星路径,
            1.65,
            每行最大=10,
            动态光效路径=光效路径,
            光效周期秒=2.0,
            基准高占比=0.34,
            行间距占比=0.02,
        )

        歌名显示 = str(getattr(歌, "歌名", "") or "").replace("_", " ")
        歌名字号 = max(16, int(局部信息条.h * 0.22))
        歌名字体 = 获取字体(歌名字号, 是否粗体=False)

        try:
            可用文字宽 = max(80, int(局部信息条.w * 0.84))
            当前字号 = 歌名字号
            while 当前字号 > 12:
                试字体 = 获取字体(当前字号, 是否粗体=False)
                if 试字体.size(歌名显示)[0] <= 可用文字宽:
                    break
                当前字号 -= 1
            歌名字体 = 获取字体(max(12, 当前字号), 是否粗体=False)
            歌名面 = 歌名字体.render(歌名显示, True, (255, 255, 255))

            歌名y = 局部星星区域.bottom + max(4, int(局部信息条.h * 0.03))
            歌名矩形 = 歌名面.get_rect(
                centerx=局部信息条.centerx + 内容偏移x,
                y=歌名y + 内容偏移y,
            )
            局部画布.blit(歌名面, 歌名矩形.topleft)

            线y = 歌名矩形.bottom + max(4, int(局部信息条.h * 0.03))
            pygame.draw.line(
                局部画布,
                (165, 165, 165),
                (
                    局部信息条.x + 内容偏移x + max(12, int(局部信息条.w * 0.06)),
                    线y,
                ),
                (
                    局部信息条.right + 内容偏移x - max(12, int(局部信息条.w * 0.06)),
                    线y,
                ),
                max(1, int(局部信息条.h * 0.012)),
            )
        except Exception:
            pass

        try:
            游玩次数 = int(max(0, int(getattr(歌, "游玩次数", 0) or 0)))
        except Exception:
            游玩次数 = 0

        bpm文本 = f"BPM:{歌.bpm}" if 歌.bpm else "BPM:?"
        底部字号 = max(12, int(局部信息条.h * 0.13))
        底部字体 = 获取字体(底部字号, 是否粗体=False)

        try:
            左文 = 底部字体.render(f"游玩次数:{游玩次数}", True, (230, 230, 230))
            右文 = 底部字体.render(bpm文本, True, (230, 230, 230))

            左x = 局部游玩区域.x + 内容偏移x
            左y = 局部游玩区域.centery + 内容偏移y - 左文.get_height() // 2
            右x = 局部bpm区域.right + 内容偏移x - 右文.get_width()
            右y = 局部bpm区域.centery + 内容偏移y - 右文.get_height() // 2

            局部画布.blit(左文, (左x, 左y))
            局部画布.blit(右文, (右x, 右y))
        except Exception:
            pass

        框图 = 获取UI容器图(
            框路径,
            装饰贴图宽,
            装饰贴图高,
            缩放模式="stretch",
            透明=True,
        )
        if 框图 is not None:
            局部画布.blit(框图, (贴图绘制x, 贴图绘制y))

        绘制序号标签_图片(
            屏幕=局部画布,
            锚点矩形=pygame.Rect(
                内容偏移x,
                内容偏移y,
                内容基础矩形.w,
                内容基础矩形.h,
            ),
            内部序号从0=歌.序号,
            是否大图=True,
        )
        return 局部画布

    def _取当前歌曲列表缓存键(
        self, 原始列表: Optional[List[歌曲信息]] = None
    ) -> Tuple[str, str, Optional[int], int, int]:
        if 原始列表 is None:
            原始列表 = self.当前原始歌曲列表()
        return (
            str(self.当前类型名() or ""),
            str(self.当前模式名() or ""),
            self.当前筛选星级,
            int(id(原始列表)),
            int(len(原始列表)),
        )

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
            self._当前歌曲列表缓存键 = None
            self._当前歌曲列表缓存值 = ([], [])
            return [], []
        缓存键 = self._取当前歌曲列表缓存键(原始)
        if self._当前歌曲列表缓存键 == 缓存键:
            return self._当前歌曲列表缓存值
        if self.当前筛选星级 is None:
            映射 = list(range(len(原始)))
            self._当前歌曲列表缓存键 = 缓存键
            self._当前歌曲列表缓存值 = (原始, 映射)
            return self._当前歌曲列表缓存值

        过滤列表: List[歌曲信息] = []
        映射: List[int] = []
        for i, 歌 in enumerate(原始):
            if int(歌.星级) == int(self.当前筛选星级):
                过滤列表.append(歌)
                映射.append(i)
        self._当前歌曲列表缓存键 = 缓存键
        self._当前歌曲列表缓存值 = (过滤列表, 映射)
        return self._当前歌曲列表缓存值

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
        if not self.背景音乐路径 or not self._背景音乐路径存在():
            return
        try:
            if pygame.mixer.music.get_busy():
                return
            pygame.mixer.music.load(self.背景音乐路径)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def _背景音乐路径存在(self) -> bool:
        路径 = str(getattr(self, "背景音乐路径", "") or "")
        if 路径 == str(getattr(self, "_背景音乐路径存在缓存键", "") or ""):
            return bool(getattr(self, "_背景音乐路径存在缓存值", False))
        结果 = bool(路径 and os.path.isfile(路径))
        self._背景音乐路径存在缓存键 = 路径
        self._背景音乐路径存在缓存值 = bool(结果)
        return bool(结果)

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


    def 重算布局(self):
        self._确保公共交互()

        self.宽, self.高 = self.屏幕.get_size()
        self._top缓存尺寸 = (0, 0)

        self._确保top栏缓存()

        if self.背景图_原图 is None:
            self._加载背景图()

        # ========= 底部槽位（修复：默认值按窗口同比缩放，不再焊死） =========
        槽边长 = self._取底部布局像素("底部.槽边长", 164, 最小=64, 最大=420)

        标签占比 = self._取布局值("底部.标签区高占比", 0.26)
        try:
            标签占比 = float(标签占比)
        except Exception:
            标签占比 = 0.26
        标签占比 = max(0.05, min(0.60, 标签占比))

        标签区高 = max(24, int(槽边长 * 标签占比))
        槽总高 = 槽边长 + 标签区高

        底部最小高 = self._取底部布局像素("底部.底部最小高", 220, 最小=100, 最大=9999)
        底部额外高 = self._取底部布局像素("底部.底部额外高", 40, 最小=0, 最大=9999)
        self.底部高 = max(底部最小高, 槽总高 + 底部额外高)

        self.中间区域 = pygame.Rect(
            0, self.顶部高, self.宽, self.高 - self.顶部高 - self.底部高
        )

        槽y = self.高 - self.底部高 + (self.底部高 - 槽总高) // 2

        左起 = self._取底部布局像素("底部.左起", 28, 最小=0, 最大=9999)
        左组间距 = self._取底部布局像素("底部.左组间距", 12, 最小=0, 最大=9999)
        右组间距 = self._取底部布局像素("底部.右组间距", 26, 最小=0, 最大=9999)
        右外边距 = self._取底部布局像素("底部.右外边距", 40, 最小=0, 最大=9999)

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

        统一文字偏移 = self._取底部布局像素("底部.统一文字偏移", -6, 最小=-9999, 最大=9999)
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

        ALL边长 = max(24, int(槽边长 * ALL缩放))
        重开边长 = max(24, int(槽边长 * 重开缩放))

        ALL矩形 = pygame.Rect(0, 0, ALL边长, ALL边长)
        ALL矩形.center = 槽_ALL_图标区.center
        self.按钮_ALL.矩形 = ALL矩形

        重开矩形 = pygame.Rect(0, 0, 重开边长, 重开边长)
        重开矩形.center = 槽_重开_图标区.center
        self.按钮_重选模式.矩形 = 重开矩形

        # ========= 模式选择面板（保留原逻辑） =========
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

        # ========= 卡片网格（保留原逻辑） =========
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

    def _计算保留key集合(self, 基准页: int) -> Set[Tuple[str, int, int, int, str]]:
        刷新选歌布局常量()

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
            页码 = int(基准页) + int(偏移)
            if 0 <= 页码 < 总页:
                页集合.append(页码)

        需要保留键集合: Set[Tuple[str, int, int, int, str]] = set()
        框路径 = _资源路径("UI-img", "选歌界面资源", "缩略图小.png")

        for 页码 in 页集合:
            卡片列表 = self.生成指定页卡片(int(页码))
            for 卡片 in 卡片列表:
                try:
                    路径 = str(getattr(卡片.歌曲, "封面路径", "") or "")
                except Exception:
                    路径 = ""

                if (not 路径) or (not os.path.isfile(路径)):
                    continue

                # ✅ 必须跟实际绘制使用同一套“小框等比矩形算法”
                框矩形 = 计算缩略图小框矩形(卡片.矩形, 框路径)
                布局 = 计算框体槽位布局(框矩形, 是否大图=False)
                封面矩形 = 布局["封面矩形"]

                需要保留键集合.add(
                    (
                        路径,
                        max(1, int(封面矩形.w)),
                        max(1, int(封面矩形.h)),
                        0,
                        "cover",
                    )
                )

        if bool(getattr(self, "是否详情页", False)):
            原始列表 = self.当前原始歌曲列表()
            try:
                当前索引 = int(getattr(self, "当前选择原始索引", 0) or 0)
            except Exception:
                当前索引 = 0

            if 0 <= 当前索引 < len(原始列表):
                当前歌曲 = 原始列表[当前索引]
                try:
                    大图路径 = str(getattr(当前歌曲, "封面路径", "") or "")
                except Exception:
                    大图路径 = ""

                if 大图路径 and os.path.isfile(大图路径):
                    try:
                        当前大框 = getattr(self, "详情大框矩形", None)
                        if not isinstance(当前大框, pygame.Rect):
                            当前大框 = None
                    except Exception:
                        当前大框 = None

                    try:
                        最后缩放 = float(getattr(self, "_详情浮层_最后缩放", 1.0) or 1.0)
                    except Exception:
                        最后缩放 = 1.0
                    最后缩放 = max(0.001, 最后缩放)

                    if 当前大框 is not None and 当前大框.w > 10 and 当前大框.h > 10:
                        基础宽 = max(10, int(round(float(当前大框.w) / 最后缩放)))
                        基础高 = max(10, int(round(float(当前大框.h) / 最后缩放)))

                        框基础矩形 = pygame.Rect(0, 0, 基础宽, 基础高)
                        布局 = 计算框体槽位布局(框基础矩形, 是否大图=True)
                        封面矩形 = 布局["封面矩形"]

                        需要保留键集合.add(
                            (
                                大图路径,
                                max(1, int(封面矩形.w)),
                                max(1, int(封面矩形.h)),
                                0,
                                "stretch",
                            )
                        )

        return 需要保留键集合


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

    def _确保翻页交互状态(self):
        if getattr(self, "_翻页交互已初始化", False):
            return
        self._翻页交互已初始化 = True
        self._滑动_按下 = False
        self._滑动_起点 = (0, 0)
        self._滑动_已触发 = False
        self._滑动_已移动 = False
        self._连续翻页激活 = False
        self._连续翻页方向 = 0
        self._连续翻页来源 = ""
        self._连续翻页下次触发秒 = 0.0
        self._连续翻页首次延迟秒 = 0.26
        self._连续翻页间隔秒 = 0.03

    def _停止连续翻页(self):
        self._确保翻页交互状态()
        self._连续翻页激活 = False
        self._连续翻页方向 = 0
        self._连续翻页来源 = ""
        self._连续翻页下次触发秒 = 0.0

    def _触发列表翻页(self, 步数: int):
        try:
            步数 = int(步数)
        except Exception:
            步数 = 0
        if 步数 == 0:
            return

        总页数 = int(self.总页数())
        if 总页数 <= 1:
            return

        目标页 = (int(self.当前页) + int(步数)) % int(总页数)
        方向 = 1 if int(步数) > 0 else -1
        self.触发翻页动画(目标页=目标页, 方向=方向)

    def _开始连续翻页(self, 方向: int, 来源: str, 立即触发: bool = True):
        self._确保翻页交互状态()
        方向 = 1 if int(方向) > 0 else -1
        if (
            bool(getattr(self, "_连续翻页激活", False))
            and int(getattr(self, "_连续翻页方向", 0) or 0) == int(方向)
            and str(getattr(self, "_连续翻页来源", "") or "") == str(来源 or "")
        ):
            return
        self._连续翻页激活 = True
        self._连续翻页方向 = int(方向)
        self._连续翻页来源 = str(来源 or "")
        当前秒 = float(time.perf_counter())
        self._连续翻页下次触发秒 = 当前秒 + float(
            getattr(self, "_连续翻页首次延迟秒", 0.26)
        )
        if 立即触发:
            self._触发列表翻页(int(方向))

    def _更新连续翻页(self):
        self._确保翻页交互状态()
        if not bool(getattr(self, "_连续翻页激活", False)):
            return
        if str(getattr(self, "_连续翻页来源", "") or "") == "keyboard":
            try:
                按键状态 = pygame.key.get_pressed()
            except Exception:
                按键状态 = None
            方向 = int(getattr(self, "_连续翻页方向", 0) or 0)
            是否仍按住 = bool(
                按键状态
                and (
                    按键状态[pygame.K_LEFT]
                    if int(方向) < 0
                    else 按键状态[pygame.K_RIGHT]
                )
            )
            if not bool(是否仍按住):
                self._停止连续翻页()
                return
        if bool(getattr(self, "动画中", False)):
            return
        if bool(getattr(self, "是否详情页", False)):
            self._停止连续翻页()
            return
        if bool(getattr(self, "是否星级筛选页", False)) or bool(
            getattr(self, "是否设置页", False)
        ):
            self._停止连续翻页()
            return

        当前秒 = float(time.perf_counter())
        if 当前秒 < float(getattr(self, "_连续翻页下次触发秒", 0.0) or 0.0):
            return

        self._触发列表翻页(int(getattr(self, "_连续翻页方向", 0) or 0))
        self._连续翻页下次触发秒 = 当前秒 + float(
            getattr(self, "_连续翻页间隔秒", 0.03)
        )

    def _处理列表页点击进入详情(self, 点击位置) -> bool:
        if not self.中间区域.collidepoint(点击位置):
            return False

        _列表, 映射 = self.当前歌曲列表与映射()
        for idx, 卡片 in enumerate(self.当前页卡片):
            if not 卡片.矩形.collidepoint(点击位置):
                continue
            视图索引 = self.当前页 * self.每页数量 + idx
            原始索引 = 映射[视图索引] if 0 <= 视图索引 < len(映射) else 0
            try:
                self._播放按钮音效()
            except Exception:
                pass
            self.进入详情_原始索引(int(原始索引))
            return True
        return False

    def _处理列表页输入(self, 事件) -> bool:
        self._确保翻页交互状态()

        if 事件.type == pygame.MOUSEMOTION:
            self._踏板选中视图索引 = None
            self._同步踏板卡片高亮()
            for 卡片 in self.当前页卡片:
                try:
                    卡片.处理事件(事件)
                except Exception:
                    pass

        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            if self.中间区域.collidepoint(事件.pos):
                self._滑动_按下 = True
                self._滑动_起点 = tuple(事件.pos)
                self._滑动_已触发 = False
                self._滑动_已移动 = False
                return True

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
                            self._触发列表翻页(+1 if dx < 0 else -1)
                            self._滑动_已触发 = True
                except Exception:
                    pass
                return True

        if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            if bool(getattr(self, "_滑动_按下", False)):
                self._滑动_按下 = False

                if (not bool(getattr(self, "_滑动_已触发", False))) and (
                    not bool(getattr(self, "_滑动_已移动", False))
                ):
                    self._处理列表页点击进入详情(事件.pos)

                self._滑动_已触发 = False
                self._滑动_已移动 = False
                return True

        if 事件.type == pygame.MOUSEBUTTONDOWN:
            if 事件.button == 4:
                self._停止连续翻页()
                self._触发列表翻页(-1)
                return True
            if 事件.button == 5:
                self._停止连续翻页()
                self._触发列表翻页(+1)
                return True

        if 事件.type == pygame.KEYDOWN:
            if 事件.key == pygame.K_LEFT:
                self._开始连续翻页(-1, 来源="keyboard", 立即触发=True)
                return True
            if 事件.key == pygame.K_RIGHT:
                self._开始连续翻页(+1, 来源="keyboard", 立即触发=True)
                return True
            if 事件.key == pygame.K_ESCAPE and getattr(self, "当前筛选星级", None) is not None:
                self._停止连续翻页()
                self._启动过渡(
                    self._特效_按钮,
                    pygame.Rect(self.宽 // 2 - 60, self.顶部高 // 2 - 20, 120, 40),
                    lambda: self.设置星级筛选(None),
                )
                return True

        if 事件.type == pygame.KEYUP and 事件.key in (pygame.K_LEFT, pygame.K_RIGHT):
            if str(getattr(self, "_连续翻页来源", "") or "") == "keyboard":
                self._停止连续翻页()
                return True

        return False

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

    def 打开星级筛选页(self):
        if self.是否详情页:
            return
        self.是否星级筛选页 = True

    def 关闭星级筛选页(self):
        self.是否星级筛选页 = False

    def 设置星级筛选(self, 星级: Optional[int]):
        self.当前筛选星级 = 星级
        self._失效歌曲视图缓存()
        self.当前页 = 0
        self.当前页卡片 = self.生成指定页卡片(self.当前页)
        self.安排预加载(基准页=self.当前页)

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
        暗层键 = (int(self.宽), int(self.高), 60)
        暗层 = self._背景暗层缓存 if self._背景暗层缓存键 == 暗层键 else None
        if 暗层 is None:
            暗层 = pygame.Surface((self.宽, self.高), pygame.SRCALPHA)
            暗层.fill((0, 0, 0, 60))
            self._背景暗层缓存 = 暗层
            self._背景暗层缓存键 = 暗层键
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
            原矩形 = 卡片.矩形
            try:
                卡片.矩形 = 原矩形.move(旧偏移, 0)
                卡片.绘制(self.屏幕, self.小字体, self.图缓存)
            finally:
                卡片.矩形 = 原矩形

        for 卡片 in self.动画新页卡片:
            原矩形 = 卡片.矩形
            try:
                卡片.矩形 = 原矩形.move(新偏移, 0)
                卡片.绘制(self.屏幕, self.小字体, self.图缓存)
            finally:
                卡片.矩形 = 原矩形

    def 绘制详情浮层(self):
        原始 = self.当前原始歌曲列表()
        if not 原始:
            return

        歌 = 原始[self.当前选择原始索引]

        def _夹紧(值: float, 最小值: float, 最大值: float) -> float:
            return 最小值 if 值 < 最小值 else (最大值 if 值 > 最大值 else 值)

        def _缓出(进度: float) -> float:
            进度 = _夹紧(进度, 0.0, 1.0)
            return 1.0 - (1.0 - 进度) * (1.0 - 进度)

        详情浮层整体缩放 = self._取布局值("详情大图.整体缩放", 1.12)
        try:
            详情浮层整体缩放 = float(详情浮层整体缩放)
        except Exception:
            详情浮层整体缩放 = 1.12
        详情浮层整体缩放 = max(0.10, min(3.00, 详情浮层整体缩放))

        目标比例 = self._取布局值("详情大图.目标比例", 1.38)
        try:
            目标比例 = float(目标比例)
        except Exception:
            目标比例 = 1.38
        目标比例 = max(0.20, min(5.0, 目标比例))

        可用宽占比 = self._取布局值("详情大图.可用宽占比", 0.60)
        可用高占比 = self._取布局值("详情大图.可用高占比", 0.78)
        try:
            可用宽占比 = float(可用宽占比)
        except Exception:
            可用宽占比 = 0.60
        try:
            可用高占比 = float(可用高占比)
        except Exception:
            可用高占比 = 0.78

        可用宽占比 = max(0.20, min(0.98, 可用宽占比))
        可用高占比 = max(0.20, min(0.98, 可用高占比))

        可用宽 = int(self.中间区域.w * 可用宽占比)
        可用高 = int(self.中间区域.h * 可用高占比)

        基准宽 = min(可用宽, int(可用高 * 目标比例))
        基准高 = int(基准宽 / 目标比例)

        最终缩放 = min(
            详情浮层整体缩放,
            float(可用宽) / float(max(1, 基准宽)),
            float(可用高) / float(max(1, 基准高)),
        )
        最终缩放 = max(0.10, 最终缩放)

        内容宽 = max(320, int(基准宽 * 最终缩放))
        内容高 = max(220, int(基准高 * 最终缩放))

        if 内容宽 > 可用宽:
            内容宽 = 可用宽
            内容高 = int(内容宽 / 目标比例)
        if 内容高 > 可用高:
            内容高 = 可用高
            内容宽 = int(内容高 * 目标比例)

        框路径 = _资源路径("UI-img", "选歌界面资源", "缩略图大.png")

        try:
            框宽缩放 = float(_缩略图大框_宽缩放)
        except Exception:
            框宽缩放 = 1.0
        try:
            框高缩放 = float(_缩略图大框_高缩放)
        except Exception:
            框高缩放 = 1.0
        try:
            框x偏移 = int(_缩略图大框_x偏移)
        except Exception:
            框x偏移 = 0
        try:
            框y偏移 = int(_缩略图大框_y偏移)
        except Exception:
            框y偏移 = 0

        try:
            贴图宽缩放 = float(_详情大框贴图_宽缩放)
        except Exception:
            贴图宽缩放 = 1.0
        try:
            贴图高缩放 = float(_详情大框贴图_高缩放)
        except Exception:
            贴图高缩放 = 1.0
        try:
            贴图x偏移 = int(_详情大框贴图_x偏移)
        except Exception:
            贴图x偏移 = 0
        try:
            贴图y偏移 = int(_详情大框贴图_y偏移)
        except Exception:
            贴图y偏移 = 0

        框宽缩放 = max(0.05, min(5.0, 框宽缩放))
        框高缩放 = max(0.05, min(5.0, 框高缩放))
        贴图宽缩放 = max(0.05, min(5.0, 贴图宽缩放))
        贴图高缩放 = max(0.05, min(5.0, 贴图高缩放))

        内容基础矩形 = pygame.Rect(
            0,
            0,
            max(1, int(round(内容宽 * 框宽缩放))),
            max(1, int(round(内容高 * 框高缩放))),
        )
        内容基础矩形.center = self.中间区域.center
        内容基础矩形.x += int(框x偏移)
        内容基础矩形.y += int(框y偏移)

        局部内容矩形 = pygame.Rect(0, 0, 内容基础矩形.w, 内容基础矩形.h)
        局部布局 = 计算框体槽位布局(局部内容矩形, 是否大图=True)

        局部封面框 = 局部布局["封面矩形"]
        局部信息条 = 局部布局["信息条矩形"]
        局部星星区域 = 局部布局["星星区域"]
        局部游玩区域 = 局部布局["游玩区域"]
        局部bpm区域 = 局部布局["bpm区域"]

        装饰贴图宽 = max(1, int(round(内容基础矩形.w * 贴图宽缩放)))
        装饰贴图高 = max(1, int(round(内容基础矩形.h * 贴图高缩放)))

        局部内容左 = 0
        局部内容上 = 0
        局部内容右 = 内容基础矩形.w
        局部内容下 = 内容基础矩形.h

        局部贴图左 = (内容基础矩形.w - 装饰贴图宽) // 2 + int(贴图x偏移)
        局部贴图上 = (内容基础矩形.h - 装饰贴图高) // 2 + int(贴图y偏移)
        局部贴图右 = 局部贴图左 + 装饰贴图宽
        局部贴图下 = 局部贴图上 + 装饰贴图高

        总左 = min(局部内容左, 局部贴图左)
        总上 = min(局部内容上, 局部贴图上)
        总右 = max(局部内容右, 局部贴图右)
        总下 = max(局部内容下, 局部贴图下)

        总宽 = max(1, int(总右 - 总左))
        总高 = max(1, int(总下 - 总上))

        内容偏移x = int(-总左)
        内容偏移y = int(-总上)
        贴图绘制x = int(局部贴图左 - 总左)
        贴图绘制y = int(局部贴图上 - 总上)
        try:
            游玩次数 = int(max(0, int(getattr(歌, "游玩次数", 0) or 0)))
        except Exception:
            游玩次数 = 0

        详情缓存键 = (
            float(_选歌布局_修改时间),
            float(getattr(self, "_布局配置_修改时间", 0.0) or 0.0),
            str(getattr(歌, "sm路径", "") or ""),
            str(getattr(歌, "封面路径", "") or ""),
            int(getattr(歌, "星级", 0) or 0),
            int(getattr(歌, "序号", 0) or 0),
            str(getattr(歌, "bpm", "") or ""),
            int(游玩次数),
            int(内容基础矩形.w),
            int(内容基础矩形.h),
            int(局部封面框.w),
            int(局部封面框.h),
            int(局部信息条.w),
            int(局部信息条.h),
            int(装饰贴图宽),
            int(装饰贴图高),
            int(贴图绘制x),
            int(贴图绘制y),
            int(内容偏移x),
            int(内容偏移y),
            int(总宽),
            int(总高),
        )
        局部画布 = (
            self._详情浮层静态缓存图
            if self._详情浮层静态缓存键 == 详情缓存键
            else None
        )
        if 局部画布 is None:
            局部画布 = self._构建详情浮层静态图(
                歌,
                框路径,
                内容基础矩形,
                局部封面框,
                局部信息条,
                局部星星区域,
                局部游玩区域,
                局部bpm区域,
                装饰贴图宽,
                装饰贴图高,
                贴图绘制x,
                贴图绘制y,
                内容偏移x,
                内容偏移y,
                总宽,
                总高,
            )
            self._详情浮层静态缓存键 = 详情缓存键
            self._详情浮层静态缓存图 = 局部画布

        现在毫秒 = 0
        try:
            现在毫秒 = int(pygame.time.get_ticks())
        except Exception:
            现在毫秒 = 0

        开始毫秒 = int(getattr(self, "_浮动大图入场开始毫秒", 0) or 0)
        时长毫秒 = int(getattr(self, "_浮动大图入场时长毫秒", 500) or 500)

        进度 = 1.0
        if 开始毫秒 > 0 and 时长毫秒 > 0:
            进度 = (现在毫秒 - 开始毫秒) / max(1, 时长毫秒)
            进度 = _夹紧(进度, 0.0, 1.0)

        if 进度 < 0.6:
            片段进度 = 进度 / 0.6
            入场缩放 = 0.92 + (1.06 - 0.92) * _缓出(片段进度)
        else:
            片段进度 = (进度 - 0.6) / 0.4
            入场缩放 = 1.06 + (1.00 - 1.06) * _缓出(片段进度)

        入场透明度 = int(255 * _缓出(进度))
        入场透明度 = max(0, min(255, 入场透明度))

        self._详情浮层_alpha = int(入场透明度)
        self._详情浮层_最后缩放 = float(入场缩放)

        if 入场缩放 != 1.0:
            绘制宽 = max(1, int(round(局部画布.get_width() * 入场缩放)))
            绘制高 = max(1, int(round(局部画布.get_height() * 入场缩放)))
            绘制画布 = pygame.transform.smoothscale(局部画布, (绘制宽, 绘制高)).convert_alpha()
        elif 入场透明度 < 255:
            绘制画布 = 局部画布.copy()
        else:
            绘制画布 = 局部画布

        if 入场透明度 < 255 or 绘制画布 is not 局部画布:
            try:
                绘制画布.set_alpha(入场透明度)
            except Exception:
                pass

        当前大框 = 绘制画布.get_rect(center=内容基础矩形.center)
        self.详情大框矩形 = 当前大框
        self.屏幕.blit(绘制画布, 当前大框.topleft)

        下一首图路径 = _资源路径("UI-img", "选歌界面资源", "下一首.png")
        下一首原图 = 获取UI原图(下一首图路径, 透明=True)
        if 下一首原图 is not None:
            原宽, 原高 = 下一首原图.get_size()
        else:
            原宽, 原高 = (150, 74)

        按钮高 = max(72, int(当前大框.h * 0.22))
        按钮宽 = max(36, int(按钮高 * float(原宽) / float(max(1, 原高))))
        按钮外间距 = max(24, int(self.宽 * 0.022))
        按钮y偏移 = 0

        左按钮矩形 = pygame.Rect(
            max(12, 当前大框.left - 按钮外间距 - 按钮宽),
            当前大框.centery - 按钮高 // 2 + 按钮y偏移,
            按钮宽,
            按钮高,
        )
        右按钮矩形 = pygame.Rect(
            min(self.宽 - 12 - 按钮宽, 当前大框.right + 按钮外间距),
            当前大框.centery - 按钮高 // 2 + 按钮y偏移,
            按钮宽,
            按钮高,
        )

        self.按钮_详情上一首.矩形 = 左按钮矩形
        self.按钮_详情下一首.矩形 = 右按钮矩形

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
        self._确保翻页交互状态()

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

    def 主循环(self):
        self._确保公共交互()

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
            self._更新连续翻页()
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

                if self._处理列表页输入(事件):
                    continue

class 设置页布局调试器:
    def __init__(self, 保存路径: str):
        self.保存路径 = str(保存路径 or "")
        self.是否启用 = False
        self.当前选中键: str = ""
        self.当前悬停键: str = ""
        self.拖拽中 = False
        self.拖拽起点局部 = (0, 0)
        self.拖拽起点矩形 = pygame.Rect(0, 0, 0, 0)
        self.当前组件矩形表: Dict[str, pygame.Rect] = {}
        self.覆盖数据: Dict[str, dict] = {}
        self.文字缩放数据: Dict[str, float] = {}
        self._读取保存数据()

    def 切换启用(self):
        self.是否启用 = not bool(self.是否启用)
        self.拖拽中 = False
        self.当前悬停键 = ""

    def _读取保存数据(self):
        if (not self.保存路径) or (not os.path.isfile(self.保存路径)):
            self.覆盖数据 = {}
            self.文字缩放数据 = {}
            return

        for 编码 in ("utf-8-sig", "utf-8", "gbk"):
            try:
                with open(self.保存路径, "r", encoding=编码) as 文件:
                    数据 = json.load(文件)
                if isinstance(数据, dict):
                    组件 = 数据.get("组件", {})
                    文字 = 数据.get("文字缩放", {})
                    self.覆盖数据 = dict(组件) if isinstance(组件, dict) else {}
                    self.文字缩放数据 = dict(文字) if isinstance(文字, dict) else {}
                    return
            except Exception:
                continue

        self.覆盖数据 = {}
        self.文字缩放数据 = {}

    def 保存到文件(self, 面板宽: int, 面板高: int) -> bool:
        try:
            面板宽 = max(1, int(面板宽))
            面板高 = max(1, int(面板高))
        except Exception:
            return False

        输出组件 = {}
        for 键名, 矩形 in self.当前组件矩形表.items():
            if not isinstance(矩形, pygame.Rect):
                continue
            输出组件[str(键名)] = {
                "x": float(矩形.x) / float(面板宽),
                "y": float(矩形.y) / float(面板高),
                "w": float(矩形.w) / float(面板宽),
                "h": float(矩形.h) / float(面板高),
            }

        数据 = {
            "版本": 2,
            "基准": "设置背景图.png",
            "组件": 输出组件,
            "文字缩放": dict(self.文字缩放数据 or {}),
        }

        try:
            os.makedirs(os.path.dirname(self.保存路径), exist_ok=True)
            with open(self.保存路径, "w", encoding="utf-8") as 文件:
                json.dump(数据, 文件, ensure_ascii=False, indent=2)
            self.覆盖数据 = dict(输出组件)
            return True
        except Exception:
            return False

    def _记录转矩形(self, 记录: dict, 面板宽: int, 面板高: int) -> Optional[pygame.Rect]:
        if not isinstance(记录, dict):
            return None

        try:
            x = int(round(float(记录.get("x", 0.0)) * float(面板宽)))
            y = int(round(float(记录.get("y", 0.0)) * float(面板高)))
            w = int(round(float(记录.get("w", 0.0)) * float(面板宽)))
            h = int(round(float(记录.get("h", 0.0)) * float(面板高)))
        except Exception:
            return None

        w = max(1, w)
        h = max(1, h)
        return pygame.Rect(x, y, w, h)

    def _归属行键(self, 组件键: str) -> str:
        键 = str(组件键 or "")
        if 键.startswith("行:"):
            return 键.split(":", 1)[1]
        if 键.startswith("控件:"):
            片段 = 键.split(":")
            if len(片段) >= 3:
                return str(片段[1])
        return ""

    def 取行文字缩放(self, 行键: str) -> float:
        try:
            值 = float((self.文字缩放数据 or {}).get(str(行键 or ""), 1.0) or 1.0)
        except Exception:
            值 = 1.0
        return max(0.50, min(3.00, 值))

    def _调整当前选中文字缩放(self, 滚轮方向: int):
        if not self.当前选中键:
            return

        行键 = self._归属行键(self.当前选中键)
        if not 行键:
            return

        当前值 = self.取行文字缩放(行键)
        新值 = 当前值 + (0.05 if int(滚轮方向) > 0 else -0.05)
        新值 = max(0.50, min(3.00, 新值))
        self.文字缩放数据[str(行键)] = float(round(新值, 2))

    def _收集当前组件(self, 宿主):
        组件表: Dict[str, pygame.Rect] = {}

        try:
            for 行键, 矩形 in dict(getattr(宿主, "_设置页_行矩形表", {}) or {}).items():
                if isinstance(矩形, pygame.Rect):
                    组件表[f"行:{行键}"] = 矩形.copy()
        except Exception:
            pass

        try:
            for 行键, 控件字典 in dict(getattr(宿主, "_设置页_控件矩形表", {}) or {}).items():
                if not isinstance(控件字典, dict):
                    continue
                for 子键 in ("左", "右", "内容"):
                    矩形 = 控件字典.get(子键)
                    if isinstance(矩形, pygame.Rect):
                        组件表[f"控件:{行键}:{子键}"] = 矩形.copy()
        except Exception:
            pass

        try:
            背景区 = getattr(宿主, "_设置页_背景区矩形", None)
            if isinstance(背景区, pygame.Rect):
                组件表["背景区"] = 背景区.copy()
        except Exception:
            pass

        try:
            背景控件 = dict(getattr(宿主, "_设置页_背景控件矩形", {}) or {})
            for 子键 in ("左", "右", "预览"):
                矩形 = 背景控件.get(子键)
                if isinstance(矩形, pygame.Rect):
                    组件表[f"背景控件:{子键}"] = 矩形.copy()
        except Exception:
            pass

        try:
            箭头预览 = getattr(宿主, "_设置页_箭头预览矩形", None)
            if isinstance(箭头预览, pygame.Rect):
                组件表["箭头预览区"] = 箭头预览.copy()
        except Exception:
            pass

        try:
            箭头控件 = dict(getattr(宿主, "_设置页_箭头预览控件矩形", {}) or {})
            for 子键 in ("左", "右"):
                矩形 = 箭头控件.get(子键)
                if isinstance(矩形, pygame.Rect):
                    组件表[f"箭头预览控件:{子键}"] = 矩形.copy()
        except Exception:
            pass

        self.当前组件矩形表 = 组件表

    def _写回宿主(self, 宿主):
        for 键名, 矩形 in self.当前组件矩形表.items():
            if not isinstance(矩形, pygame.Rect):
                continue

            if str(键名).startswith("行:"):
                行键 = str(键名).split(":", 1)[1]
                if 行键 in getattr(宿主, "_设置页_行矩形表", {}):
                    宿主._设置页_行矩形表[行键] = 矩形.copy()
                continue

            if str(键名).startswith("控件:"):
                _, 行键, 子键 = str(键名).split(":", 2)
                控件表 = getattr(宿主, "_设置页_控件矩形表", {})
                if 行键 in 控件表 and isinstance(控件表.get(行键), dict):
                    控件表[行键][子键] = 矩形.copy()
                continue

            if 键名 == "背景区":
                宿主._设置页_背景区矩形 = 矩形.copy()
                continue

            if str(键名).startswith("背景控件:"):
                子键 = str(键名).split(":", 1)[1]
                宿主._设置页_背景控件矩形[子键] = 矩形.copy()
                continue

            if 键名 == "箭头预览区":
                宿主._设置页_箭头预览矩形 = 矩形.copy()
                continue

            if str(键名).startswith("箭头预览控件:"):
                子键 = str(键名).split(":", 1)[1]
                宿主._设置页_箭头预览控件矩形[子键] = 矩形.copy()
                continue

    def _屏幕点转面板局部(self, 宿主, 屏幕点) -> Tuple[int, int]:
        面板绘制矩形 = getattr(宿主, "_设置页_面板绘制矩形", pygame.Rect(0, 0, 1, 1))
        当前缩放 = float(getattr(宿主, "_设置页_最后缩放", 1.0) or 1.0)
        当前缩放 = max(0.001, 当前缩放)
        局部x = int((屏幕点[0] - 面板绘制矩形.x) / 当前缩放)
        局部y = int((屏幕点[1] - 面板绘制矩形.y) / 当前缩放)
        return (局部x, 局部y)

    def _命中测试(self, 局部点) -> str:
        候选键列表 = []
        for 键名, 矩形 in self.当前组件矩形表.items():
            if isinstance(矩形, pygame.Rect) and 矩形.collidepoint(局部点):
                候选键列表.append((矩形.w * 矩形.h, str(键名)))

        if not 候选键列表:
            return ""

        候选键列表.sort(key=lambda 项: 项[0])
        return 候选键列表[0][1]

    def _钳制当前选中矩形(self, 宿主):
        if not self.当前选中键:
            return
        if self.当前选中键 not in self.当前组件矩形表:
            return
        self.当前组件矩形表[self.当前选中键] = _设置页_钳制矩形到面板(
            宿主, self.当前组件矩形表[self.当前选中键]
        )

    def _调整当前选中矩形尺寸(self, 宿主, 滚轮方向: int, 是否调宽: bool, 是否调高: bool):
        if not self.当前选中键:
            return
        if self.当前选中键 not in self.当前组件矩形表:
            return

        旧矩形 = self.当前组件矩形表[self.当前选中键].copy()

        缩放倍数 = 1.05 if int(滚轮方向) > 0 else 0.95
        新宽 = int(round(float(旧矩形.w) * 缩放倍数))
        新高 = int(round(float(旧矩形.h) * 缩放倍数))

        if 是否调宽 and (not 是否调高):
            新高 = 旧矩形.h
        elif 是否调高 and (not 是否调宽):
            新宽 = 旧矩形.w

        新宽 = max(8, 新宽)
        新高 = max(8, 新高)

        新矩形 = pygame.Rect(0, 0, 新宽, 新高)
        新矩形.center = 旧矩形.center

        self.当前组件矩形表[self.当前选中键] = _设置页_钳制矩形到面板(宿主, 新矩形)
        self._写回宿主(宿主)

    def _微调当前选中矩形(self, 宿主, dx: int, dy: int):
        if not self.当前选中键:
            return
        if self.当前选中键 not in self.当前组件矩形表:
            return

        新矩形 = self.当前组件矩形表[self.当前选中键].copy()
        新矩形.x += int(dx)
        新矩形.y += int(dy)
        self.当前组件矩形表[self.当前选中键] = _设置页_钳制矩形到面板(宿主, 新矩形)
        self._写回宿主(宿主)

    def 应用保存覆盖(self, 宿主):
        self._收集当前组件(宿主)

        try:
            面板矩形 = getattr(宿主, "_设置页_面板基础矩形", pygame.Rect(0, 0, 1, 1))
            面板宽 = max(1, int(面板矩形.w))
            面板高 = max(1, int(面板矩形.h))
        except Exception:
            面板宽 = 1
            面板高 = 1

        for 键名, 记录 in dict(self.覆盖数据 or {}).items():
            if 键名 not in self.当前组件矩形表:
                continue
            新矩形 = self._记录转矩形(记录, 面板宽, 面板高)
            if isinstance(新矩形, pygame.Rect):
                self.当前组件矩形表[键名] = _设置页_钳制矩形到面板(宿主, 新矩形)

        self._写回宿主(宿主)

    def 处理事件(self, 宿主, 事件) -> bool:
        if not bool(self.是否启用):
            return False

        self._收集当前组件(宿主)

        if 事件.type == pygame.KEYDOWN:
            if 事件.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                try:
                    面板矩形 = getattr(宿主, "_设置页_面板基础矩形", pygame.Rect(0, 0, 1, 1))
                    保存成功 = self.保存到文件(int(面板矩形.w), int(面板矩形.h))
                    if 保存成功 and hasattr(宿主, "显示消息提示"):
                        宿主.显示消息提示("设置页调试器：布局已保存", 持续秒=1.6)
                except Exception:
                    pass
                return True

            if 事件.key == pygame.K_UP:
                self._微调当前选中矩形(宿主, 0, -1)
                return True
            if 事件.key == pygame.K_DOWN:
                self._微调当前选中矩形(宿主, 0, 1)
                return True
            if 事件.key == pygame.K_LEFT:
                self._微调当前选中矩形(宿主, -1, 0)
                return True
            if 事件.key == pygame.K_RIGHT:
                self._微调当前选中矩形(宿主, 1, 0)
                return True

        if 事件.type == pygame.MOUSEMOTION:
            局部点 = self._屏幕点转面板局部(宿主, 事件.pos)
            self.当前悬停键 = self._命中测试(局部点)

            if self.拖拽中 and self.当前选中键 in self.当前组件矩形表:
                dx = int(局部点[0] - self.拖拽起点局部[0])
                dy = int(局部点[1] - self.拖拽起点局部[1])

                新矩形 = self.拖拽起点矩形.copy()
                新矩形.x += dx
                新矩形.y += dy
                self.当前组件矩形表[self.当前选中键] = _设置页_钳制矩形到面板(宿主, 新矩形)
                self._写回宿主(宿主)
            return True

        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            局部点 = self._屏幕点转面板局部(宿主, 事件.pos)
            命中键 = self._命中测试(局部点)
            self.当前选中键 = str(命中键 or "")
            if self.当前选中键 and self.当前选中键 in self.当前组件矩形表:
                self.拖拽中 = True
                self.拖拽起点局部 = (int(局部点[0]), int(局部点[1]))
                self.拖拽起点矩形 = self.当前组件矩形表[self.当前选中键].copy()
            else:
                self.拖拽中 = False
            return True

        if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            self.拖拽中 = False
            return True

        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button in (4, 5):
            局部点 = self._屏幕点转面板局部(宿主, 事件.pos)
            命中键 = self._命中测试(局部点)
            if 命中键:
                self.当前选中键 = str(命中键)

            if not self.当前选中键:
                return True

            滚轮方向 = 1 if int(事件.button) == 4 else -1
            按键状态 = pygame.key.get_mods()
            是否Ctrl = bool(按键状态 & pygame.KMOD_CTRL)
            是否Shift = bool(按键状态 & pygame.KMOD_SHIFT)
            是否Alt = bool(按键状态 & pygame.KMOD_ALT)

            if 是否Alt:
                self._调整当前选中文字缩放(滚轮方向)
                return True

            if 是否Ctrl:
                self._调整当前选中矩形尺寸(宿主, 滚轮方向, 是否调宽=False, 是否调高=True)
            elif 是否Shift:
                self._调整当前选中矩形尺寸(宿主, 滚轮方向, 是否调宽=True, 是否调高=False)
            else:
                self._调整当前选中矩形尺寸(宿主, 滚轮方向, 是否调宽=True, 是否调高=True)
            return True

        return False

    def 绘制覆盖(self, 宿主, 面板画布: pygame.Surface):
        if not bool(self.是否启用):
            return

        self._收集当前组件(宿主)

        try:
            字体 = 获取字体(18, 是否粗体=True)
            小字体 = 获取字体(14, 是否粗体=False)
        except Exception:
            return

        for 键名, 矩形 in self.当前组件矩形表.items():
            if not isinstance(矩形, pygame.Rect):
                continue

            if str(键名) == str(self.当前选中键):
                边框色 = (255, 120, 80, 255)
                填充色 = (255, 120, 80, 28)
                线宽 = 1
            elif str(键名) == str(self.当前悬停键):
                边框色 = (80, 220, 255, 255)
                填充色 = (80, 220, 255, 20)
                线宽 = 1
            else:
                边框色 = (120, 255, 140, 170)
                填充色 = (120, 255, 140, 10)
                线宽 = 1

            try:
                填充面 = pygame.Surface((矩形.w, 矩形.h), pygame.SRCALPHA)
                填充面.fill(填充色)
                面板画布.blit(填充面, 矩形.topleft)
                pygame.draw.rect(面板画布, 边框色, 矩形, width=线宽, border_radius=2)
            except Exception:
                pass

            try:
                if str(键名) == str(self.当前选中键) or str(键名) == str(self.当前悬停键):
                    标签面 = 字体.render(str(键名), True, (255, 255, 255))
                    标签底 = pygame.Surface(
                        (标签面.get_width() + 8, 标签面.get_height() + 4), pygame.SRCALPHA
                    )
                    标签底.fill((0, 0, 0, 150))
                    标签x = max(0, 矩形.x)
                    标签y = max(0, 矩形.y - 标签底.get_height())
                    面板画布.blit(标签底, (标签x, 标签y))
                    面板画布.blit(标签面, (标签x + 4, 标签y + 2))
            except Exception:
                pass

        try:
            提示文本 = "F6开关调试 | 拖动移动 | 滚轮等比缩放 | Ctrl+滚轮改高 | Shift+滚轮改宽 | Alt+滚轮改字 | 方向键1px微调 | Ctrl+S保存"
            提示面 = 小字体.render(提示文本, True, (255, 255, 255))
            提示底 = pygame.Surface((提示面.get_width() + 12, 提示面.get_height() + 8), pygame.SRCALPHA)
            提示底.fill((0, 0, 0, 170))
            面板画布.blit(提示底, (8, 8))
            面板画布.blit(提示面, (14, 12))
        except Exception:
            pass




def 设置页_布局基准配置() -> dict:
    return {
        "设计宽": 2048,
        "设计高": 1152,
        "布局缩放最小": 0.68,
        "布局缩放最大": 1.18,

        "面板宽占比": 0.82,
        "面板高占比": 0.76,
        "面板最小边距": 24,
        "面板最大宽": 1540,
        "面板最大高": 860,
        "面板最小宽": 1160,
        "面板最小高": 640,

        "内容左边距": 64,
        "内容右边距": 58,
        "内容上边距": 56,
        "内容下边距": 42,
        "左右列间距": 72,

        "左列宽占比": 0.34,
        "左列上偏移": 18,
        "左列行区高占比": 0.64,

        "行列表": ["调速", "变速", "变速类型", "隐藏", "轨迹", "方向", "大小"],
        "行间距": 16,
        "行高最小": 54,
        "行高最大": 86,

        "行内左右边距": 8,
        "小箭头宽": 28,
        "小箭头高占行高": 0.54,
        "内容左右内边距": 12,

        "右列顶部预留": 6,
        "右列上下分区间距": 28,
        "右列上区高占比": 0.58,

        "背景区左右箭头宽": 60,
        "背景区左右箭头高": 118,
        "背景区箭头与预览间距": 18,
        "背景区预览上下内边距": 20,
        "背景区左右内边距": 12,

        "箭头预览左右箭头宽": 56,
        "箭头预览左右箭头高": 108,
        "箭头预览箭头间距": 18,
        "箭头预览上下内边距": 10,
        "箭头预览底部文字间距": 18,
        "箭头预览底部保护边距": 6,
        "箭头预览内边距": 0,

        "标签字号占行高": 0.44,
        "选项字号占行高": 0.48,
        "小字字号占行高": 0.31,
        "名称下移": 1,
    }

def 计算设置页布局(屏幕宽: int, 屏幕高: int) -> dict:
    配置 = 设置页_布局基准配置()

    try:
        屏幕宽 = int(屏幕宽)
    except Exception:
        屏幕宽 = 1280

    try:
        屏幕高 = int(屏幕高)
    except Exception:
        屏幕高 = 720

    屏幕宽 = max(960, 屏幕宽)
    屏幕高 = max(600, 屏幕高)

    设计宽 = float(配置.get("设计宽", 2048) or 2048)
    设计高 = float(配置.get("设计高", 1152) or 1152)

    布局缩放 = min(float(屏幕宽) / 设计宽, float(屏幕高) / 设计高)
    布局缩放 = max(
        float(配置.get("布局缩放最小", 0.68) or 0.68),
        min(float(配置.get("布局缩放最大", 1.18) or 1.18), float(布局缩放)),
    )

    def _夹紧浮点(值, 最小值: float, 最大值: float) -> float:
        try:
            值 = float(值)
        except Exception:
            值 = float(最小值)
        return max(float(最小值), min(float(最大值), 值))

    def _夹紧整数(值, 最小值: int, 最大值: int) -> int:
        try:
            值 = int(round(float(值)))
        except Exception:
            值 = int(最小值)
        return max(int(最小值), min(int(最大值), 值))

    def _源像素转屏幕像素(值) -> int:
        try:
            return int(round(float(值) * float(布局缩放)))
        except Exception:
            return 0

    def _局部矩形(x: int, y: int, w: int, h: int) -> pygame.Rect:
        return pygame.Rect(int(x), int(y), max(1, int(w)), max(1, int(h)))

    面板宽占比 = _夹紧浮点(配置.get("面板宽占比", 0.82), 0.20, 1.20)
    面板高占比 = _夹紧浮点(配置.get("面板高占比", 0.76), 0.20, 1.20)

    面板宽 = int(round(屏幕宽 * 面板宽占比))
    面板高 = int(round(屏幕高 * 面板高占比))

    面板边距 = max(12, _源像素转屏幕像素(配置.get("面板最小边距", 24)))
    面板最小宽 = _源像素转屏幕像素(配置.get("面板最小宽", 1160))
    面板最小高 = _源像素转屏幕像素(配置.get("面板最小高", 640))
    面板最大宽 = _源像素转屏幕像素(配置.get("面板最大宽", 1540))
    面板最大高 = _源像素转屏幕像素(配置.get("面板最大高", 860))

    面板宽 = _夹紧整数(
        面板宽,
        面板最小宽,
        min(max(面板最小宽, 屏幕宽 - 面板边距 * 2), 面板最大宽),
    )
    面板高 = _夹紧整数(
        面板高,
        面板最小高,
        min(max(面板最小高, 屏幕高 - 面板边距 * 2), 面板最大高),
    )

    面板矩形 = pygame.Rect(0, 0, 面板宽, 面板高)
    面板矩形.center = (屏幕宽 // 2, 屏幕高 // 2)

    if 面板矩形.left < 面板边距:
        面板矩形.x = 面板边距
    if 面板矩形.top < 面板边距:
        面板矩形.y = 面板边距
    if 面板矩形.right > 屏幕宽 - 面板边距:
        面板矩形.x = 屏幕宽 - 面板边距 - 面板矩形.w
    if 面板矩形.bottom > 屏幕高 - 面板边距:
        面板矩形.y = 屏幕高 - 面板边距 - 面板矩形.h

    内容左边距 = _源像素转屏幕像素(配置.get("内容左边距", 64))
    内容右边距 = _源像素转屏幕像素(配置.get("内容右边距", 58))
    内容上边距 = _源像素转屏幕像素(配置.get("内容上边距", 56))
    内容下边距 = _源像素转屏幕像素(配置.get("内容下边距", 42))
    左右列间距 = _源像素转屏幕像素(配置.get("左右列间距", 72))

    内容区矩形 = pygame.Rect(
        面板矩形.x + 内容左边距,
        面板矩形.y + 内容上边距,
        max(1, 面板矩形.w - 内容左边距 - 内容右边距),
        max(1, 面板矩形.h - 内容上边距 - 内容下边距),
    )

    左列宽占比 = _夹紧浮点(配置.get("左列宽占比", 0.34), 0.15, 0.70)
    左列宽 = int(round(内容区矩形.w * 左列宽占比))
    左列宽 = max(_源像素转屏幕像素(280), min(左列宽, 内容区矩形.w - 左右列间距 - _源像素转屏幕像素(260)))

    右列宽 = max(1, 内容区矩形.w - 左列宽 - 左右列间距)

    左列矩形 = pygame.Rect(
        内容区矩形.x,
        内容区矩形.y + _源像素转屏幕像素(配置.get("左列上偏移", 18)),
        左列宽,
        max(1, 内容区矩形.h - _源像素转屏幕像素(配置.get("左列上偏移", 18))),
    )

    右列矩形 = pygame.Rect(
        左列矩形.right + 左右列间距,
        内容区矩形.y + _源像素转屏幕像素(配置.get("右列顶部预留", 6)),
        右列宽,
        max(1, 内容区矩形.h - _源像素转屏幕像素(配置.get("右列顶部预留", 6))),
    )

    行键列表 = list(配置.get("行列表", []) or [])
    行数量 = max(1, len(行键列表))
    行间距 = max(0, _源像素转屏幕像素(配置.get("行间距", 16)))
    行高最小 = max(24, _源像素转屏幕像素(配置.get("行高最小", 54)))
    行高最大 = max(行高最小, _源像素转屏幕像素(配置.get("行高最大", 86)))

    左列行区高占比 = _夹紧浮点(配置.get("左列行区高占比", 0.64), 0.20, 1.00)
    左列可用高 = max(1, int(round(左列矩形.h * 左列行区高占比)))
    行高 = (左列可用高 - (行数量 - 1) * 行间距) // 行数量
    行高 = max(行高最小, min(行高最大, 行高))

    小箭头宽 = max(12, _源像素转屏幕像素(配置.get("小箭头宽", 28)))
    小箭头高 = max(18, int(round(float(行高) * float(配置.get("小箭头高占行高", 0.54) or 0.54))))
    行内左右边距 = max(4, _源像素转屏幕像素(配置.get("行内左右边距", 8)))
    内容左右内边距 = max(4, _源像素转屏幕像素(配置.get("内容左右内边距", 12)))

    行矩形表: Dict[str, pygame.Rect] = {}
    控件矩形表: Dict[str, Dict[str, pygame.Rect]] = {}

    for 行序号, 行键 in enumerate(行键列表):
        行x = 左列矩形.x
        行y = 左列矩形.y + 行序号 * (行高 + 行间距)
        行矩形 = _局部矩形(行x, 行y, 左列矩形.w, 行高)
        行矩形表[行键] = 行矩形

        左箭矩形 = _局部矩形(
            行矩形.x + 行内左右边距,
            行矩形.centery - 小箭头高 // 2,
            小箭头宽,
            小箭头高,
        )
        右箭矩形 = _局部矩形(
            行矩形.right - 行内左右边距 - 小箭头宽,
            行矩形.centery - 小箭头高 // 2,
            小箭头宽,
            小箭头高,
        )

        内容左 = 左箭矩形.right + 内容左右内边距
        内容右 = 右箭矩形.x - 内容左右内边距
        内容矩形 = _局部矩形(
            内容左,
            行矩形.y,
            max(12, 内容右 - 内容左),
            行矩形.h,
        )

        控件矩形表[行键] = {
            "左": 左箭矩形,
            "右": 右箭矩形,
            "内容": 内容矩形,
        }

    右列上下分区间距 = max(0, _源像素转屏幕像素(配置.get("右列上下分区间距", 28)))
    右列上区高占比 = _夹紧浮点(配置.get("右列上区高占比", 0.58), 0.20, 0.85)

    背景区高 = int(round((右列矩形.h - 右列上下分区间距) * 右列上区高占比))
    背景区高 = max(_源像素转屏幕像素(220), min(背景区高, right_h := max(1, 右列矩形.h - 右列上下分区间距 - _源像素转屏幕像素(140))))
    箭头区高 = max(1, 右列矩形.h - 背景区高 - 右列上下分区间距)

    背景区矩形 = pygame.Rect(
        右列矩形.x,
        右列矩形.y,
        右列矩形.w,
        背景区高,
    )
    箭头预览矩形 = pygame.Rect(
        右列矩形.x,
        背景区矩形.bottom + 右列上下分区间距,
        右列矩形.w,
        箭头区高,
    )

    背景箭头宽 = max(18, _源像素转屏幕像素(配置.get("背景区左右箭头宽", 60)))
    背景箭头高 = max(28, _源像素转屏幕像素(配置.get("背景区左右箭头高", 118)))
    背景箭间距 = max(8, _源像素转屏幕像素(配置.get("背景区箭头与预览间距", 18)))
    背景上下内边距 = max(0, _源像素转屏幕像素(配置.get("背景区预览上下内边距", 20)))
    背景左右内边距 = max(0, _源像素转屏幕像素(配置.get("背景区左右内边距", 12)))

    背景左箭矩形 = _局部矩形(
        背景区矩形.x + 背景左右内边距,
        背景区矩形.centery - 背景箭头高 // 2,
        背景箭头宽,
        背景箭头高,
    )
    背景右箭矩形 = _局部矩形(
        背景区矩形.right - 背景左右内边距 - 背景箭头宽,
        背景区矩形.centery - 背景箭头高 // 2,
        背景箭头宽,
        背景箭头高,
    )

    背景预览矩形 = _局部矩形(
        背景左箭矩形.right + 背景箭间距,
        背景区矩形.y + 背景上下内边距,
        max(40, 背景右箭矩形.x - 背景箭间距 - (背景左箭矩形.right + 背景箭间距)),
        max(40, 背景区矩形.h - 背景上下内边距 * 2),
    )

    箭头箭头宽 = max(18, _源像素转屏幕像素(配置.get("箭头预览左右箭头宽", 56)))
    箭头箭头高 = max(28, _源像素转屏幕像素(配置.get("箭头预览左右箭头高", 108)))
    箭头箭间距 = max(8, _源像素转屏幕像素(配置.get("箭头预览箭头间距", 18)))
    箭头上下内边距 = max(0, _源像素转屏幕像素(配置.get("箭头预览上下内边距", 10)))

    箭头左箭矩形 = _局部矩形(
        箭头预览矩形.x + 背景左右内边距,
        箭头预览矩形.centery - 箭头箭头高 // 2,
        箭头箭头宽,
        箭头箭头高,
    )
    箭头右箭矩形 = _局部矩形(
        箭头预览矩形.right - 背景左右内边距 - 箭头箭头宽,
        箭头预览矩形.centery - 箭头箭头高 // 2,
        箭头箭头宽,
        箭头箭头高,
    )

    中间预览宽 = max(60, 箭头右箭矩形.x - 箭头箭间距 - (箭头左箭矩形.right + 箭头箭间距))
    中间预览高 = max(60, 箭头预览矩形.h - 箭头上下内边距 * 2)
    预览边长 = min(中间预览宽, 中间预览高)

    箭头预览核心矩形 = _局部矩形(
        箭头预览矩形.centerx - 预览边长 // 2,
        箭头预览矩形.y + 箭头上下内边距,
        预览边长,
        预览边长,
    )

    标签字号 = max(14, int(round(行高 * float(配置.get("标签字号占行高", 0.44) or 0.44))))
    选项字号 = max(16, int(round(行高 * float(配置.get("选项字号占行高", 0.48) or 0.48))))
    小字字号 = max(12, int(round(行高 * float(配置.get("小字字号占行高", 0.31) or 0.31))))

    视觉参数 = {
        "标签字号": 标签字号,
        "选项字号": 选项字号,
        "小字字号": 小字字号,
        "内容内边距": max(4, 内容左右内边距),
        "名称下移": _源像素转屏幕像素(配置.get("名称下移", 1)),
        "箭头名称上间距": max(6, _源像素转屏幕像素(配置.get("箭头预览底部文字间距", 18))),
        "底部保护边距": max(4, _源像素转屏幕像素(配置.get("箭头预览底部保护边距", 6))),
        "箭头预览内边距": max(0, _源像素转屏幕像素(配置.get("箭头预览内边距", 0))),
    }

    return {
        "布局缩放": float(布局缩放),
        "面板基础矩形": 面板矩形,
        "行矩形表": 行矩形表,
        "控件矩形表": 控件矩形表,
        "背景区矩形": 背景区矩形,
        "背景控件矩形": {
            "左": 背景左箭矩形,
            "右": 背景右箭矩形,
            "预览": 背景预览矩形,
        },
        "箭头预览矩形": 箭头预览核心矩形,
        "箭头预览控件矩形": {
            "左": 箭头左箭矩形,
            "右": 箭头右箭矩形,
        },
        "视觉参数": 视觉参数,
    }

def 设置菜单行键列表() -> List[str]:
    """
    选歌设置菜单左侧可调行（保留旧布局顺序，兼容旧 json 偏移）。
    """
    return ["调速", "变速", "变速类型", "隐藏", "轨迹", "方向", "大小"]





def 设置菜单默认调速选项() -> List[str]:
    # 固定档位：3.0 ~ 7.0（步进 0.5）
    return ["3.0", "3.5", "4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0"]




def 设置菜单行显示名(行键: str) -> str:
    键 = str(行键 or "")
    if 键 == "变速":
        return "背景"
    if 键 == "变速类型":
        return "谱面"
    return 键


def 设置菜单行值(
    行键: str,
    设置参数: Optional[Dict[str, str]] = None,
) -> str:
    参数 = dict(设置参数 or {})
    键 = str(行键 or "")
    if 键 == "变速":
        动态背景 = str(参数.get("动态背景", "") or "").strip()
        if 动态背景 and 动态背景 != "关闭":
            return "动态背景"
        return str(参数.get("背景模式", "图片") or "图片")
    if 键 == "变速类型":
        return str(参数.get("谱面", "正常") or "正常")
    if 键 == "隐藏":
        return str(参数.get("隐藏", "关闭") or "关闭")
    if 键 == "轨迹":
        return str(参数.get("轨迹", "正常") or "正常")
    if 键 == "方向":
        return str(参数.get("方向", "关闭") or "关闭")
    if 键 == "大小":
        return str(参数.get("大小", "正常") or "正常")
    if 键 == "调速":
        return str(参数.get("调速", "X4.0") or "X4.0")
    return ""


def 设置参数文本提取值(参数文本: str, 键名: str) -> str:
    try:
        文本 = str(参数文本 or "")
        m = re.search(rf"{re.escape(str(键名))}\s*=\s*([^\s]+)", 文本)
        if not m:
            return ""
        return str(m.group(1)).strip()
    except Exception:
        return ""


def 构建设置参数文本(
    设置参数: Optional[Dict[str, object]] = None,
    背景文件名: str = "",
    箭头文件名: str = "",
) -> str:
    参数 = dict(设置参数 or {})
    参数片段: List[str] = []
    顺序键 = ["调速", "背景模式", "谱面", "隐藏", "轨迹", "方向", "大小"]
    if ("背景模式" not in 参数) and ("变速" in 参数):
        参数["背景模式"] = 参数.get("变速")

    try:
        for 键 in 顺序键:
            if 键 in 参数:
                参数片段.append(f"{键}={参数.get(键)}")
        for 键, 值 in 参数.items():
            if 键 in 顺序键:
                continue
            参数片段.append(f"{键}={值}")
    except Exception:
        参数片段 = []

    if 背景文件名:
        参数片段.append(f"背景={背景文件名}")
    if 箭头文件名:
        参数片段.append(f"箭头={箭头文件名}")
    return "设置参数：" + ("  ".join(参数片段) if 参数片段 else "默认")


def 取非透明裁切矩形(图: pygame.Surface) -> pygame.Rect:
    """
    返回图像 alpha>0 的最小包围盒；若无 alpha 或找不到，则返回整图。
    """
    try:
        w, h = 图.get_size()
    except Exception:
        return pygame.Rect(0, 0, 1, 1)
    if w <= 0 or h <= 0:
        return pygame.Rect(0, 0, 1, 1)

    try:
        mask = pygame.mask.from_surface(图, threshold=1)
        bbox = mask.get_bounding_rects()
        if bbox:
            # 合并所有 rect，避免多块分离导致裁切不全
            out = bbox[0].copy()
            for r in bbox[1:]:
                out = out.union(r)
            if out.w > 0 and out.h > 0:
                return out
    except Exception:
        pass
    return pygame.Rect(0, 0, int(w), int(h))


def 绘制_cover裁切预览(
    目标面: pygame.Surface,
    原图: Optional[pygame.Surface],
    目标区域: pygame.Rect,
) -> bool:
    """
    在目标区域内按 cover 方式绘制并裁切，保证超出部分不外溢。
    """
    if 原图 is None or (not isinstance(目标区域, pygame.Rect)):
        return False
    if 目标区域.w <= 0 or 目标区域.h <= 0:
        return False

    try:
        裁切源 = 取非透明裁切矩形(原图)
        ow, oh = int(裁切源.w), int(裁切源.h)
    except Exception:
        return False
    if ow <= 0 or oh <= 0:
        return False

    比例 = max(float(目标区域.w) / float(ow), float(目标区域.h) / float(oh))
    nw = max(1, int(round(float(ow) * 比例)))
    nh = max(1, int(round(float(oh) * 比例)))

    try:
        源图 = 原图.subsurface(裁切源).copy().convert_alpha()
        图 = pygame.transform.smoothscale(源图, (nw, nh)).convert_alpha()
    except Exception:
        try:
            源图 = 原图.subsurface(裁切源).copy().convert_alpha()
            图 = pygame.transform.scale(源图, (nw, nh)).convert_alpha()
        except Exception:
            return False

    src_x = max(0, (nw - 目标区域.w) // 2)
    src_y = max(0, (nh - 目标区域.h) // 2)
    src = pygame.Rect(src_x, src_y, int(目标区域.w), int(目标区域.h))
    src = src.clip(pygame.Rect(0, 0, nw, nh))

    try:
        目标面.blit(图, 目标区域.topleft, area=src)
        return True
    except Exception:
        return False

def _设置页_钳制矩形到面板(self, 矩形: pygame.Rect) -> pygame.Rect:
    if not isinstance(矩形, pygame.Rect):
        return pygame.Rect(0, 0, 1, 1)

    try:
        面板矩形 = getattr(self, "_设置页_面板基础矩形", pygame.Rect(0, 0, 1, 1))
        面板宽 = max(1, int(面板矩形.w))
        面板高 = max(1, int(面板矩形.h))
    except Exception:
        面板宽 = 1
        面板高 = 1

    新矩形 = 矩形.copy()
    新矩形.w = max(1, int(新矩形.w))
    新矩形.h = max(1, int(新矩形.h))

    if 新矩形.w > 面板宽:
        新矩形.w = 面板宽
    if 新矩形.h > 面板高:
        新矩形.h = 面板高

    新矩形.x = max(0, min(int(新矩形.x), max(0, 面板宽 - 新矩形.w)))
    新矩形.y = max(0, min(int(新矩形.y), max(0, 面板高 - 新矩形.h)))
    return 新矩形

def _设置页_统一行按钮尺寸(self):
    行键列表 = ["调速", "变速", "变速类型", "隐藏", "轨迹", "方向", "大小"]

    try:
        调速控件 = dict(getattr(self, "_设置页_控件矩形表", {}) or {}).get("调速", {})
    except Exception:
        调速控件 = {}

    标准左 = 调速控件.get("左")
    if not isinstance(标准左, pygame.Rect):
        return

    标准宽 = max(1, int(标准左.w))
    标准高 = max(1, int(标准左.h))

    控件表 = getattr(self, "_设置页_控件矩形表", {})
    if not isinstance(控件表, dict):
        return

    for 行键 in 行键列表:
        行控件 = 控件表.get(行键)
        if not isinstance(行控件, dict):
            continue

        左矩形 = 行控件.get("左")
        右矩形 = 行控件.get("右")

        if isinstance(左矩形, pygame.Rect):
            新左 = 左矩形.copy()
            新左.size = (标准宽, 标准高)
            新左.y = 左矩形.centery - 标准高 // 2
            行控件["左"] = _设置页_钳制矩形到面板(self, 新左)

        if isinstance(右矩形, pygame.Rect):
            新右 = 右矩形.copy()
            新右.size = (标准宽, 标准高)
            新右.y = 右矩形.centery - 标准高 // 2
            行控件["右"] = _设置页_钳制矩形到面板(self, 新右)

def _设置页_钳制全部控件到面板(self):
    try:
        行矩形表 = getattr(self, "_设置页_行矩形表", {})
        if isinstance(行矩形表, dict):
            for 行键, 矩形 in list(行矩形表.items()):
                if isinstance(矩形, pygame.Rect):
                    行矩形表[行键] = _设置页_钳制矩形到面板(self, 矩形)
    except Exception:
        pass

    try:
        控件矩形表 = getattr(self, "_设置页_控件矩形表", {})
        if isinstance(控件矩形表, dict):
            for 行键, 控件 in list(控件矩形表.items()):
                if not isinstance(控件, dict):
                    continue
                for 子键 in ("左", "右", "内容"):
                    矩形 = 控件.get(子键)
                    if isinstance(矩形, pygame.Rect):
                        控件[子键] = _设置页_钳制矩形到面板(self, 矩形)
    except Exception:
        pass

    try:
        背景区 = getattr(self, "_设置页_背景区矩形", None)
        if isinstance(背景区, pygame.Rect):
            self._设置页_背景区矩形 = _设置页_钳制矩形到面板(self, 背景区)
    except Exception:
        pass

    try:
        背景控件 = getattr(self, "_设置页_背景控件矩形", {})
        if isinstance(背景控件, dict):
            for 子键 in ("左", "右", "预览"):
                矩形 = 背景控件.get(子键)
                if isinstance(矩形, pygame.Rect):
                    背景控件[子键] = _设置页_钳制矩形到面板(self, 矩形)
    except Exception:
        pass

    try:
        箭头预览区 = getattr(self, "_设置页_箭头预览矩形", None)
        if isinstance(箭头预览区, pygame.Rect):
            self._设置页_箭头预览矩形 = _设置页_钳制矩形到面板(self, 箭头预览区)
    except Exception:
        pass

    try:
        箭头预览控件 = getattr(self, "_设置页_箭头预览控件矩形", {})
        if isinstance(箭头预览控件, dict):
            for 子键 in ("左", "右"):
                矩形 = 箭头预览控件.get(子键)
                if isinstance(矩形, pygame.Rect):
                    箭头预览控件[子键] = _设置页_钳制矩形到面板(self, 矩形)
    except Exception:
        pass


def 重算设置页布局(self, 强制: bool = False):
    self._确保设置页资源()

    try:
        当前尺寸 = (int(getattr(self, "宽", 0) or 0), int(getattr(self, "高", 0) or 0))
    except Exception:
        当前尺寸 = (0, 0)

    if (not 强制) and 当前尺寸 == tuple(getattr(self, "_设置页_上次屏幕尺寸", (0, 0))):
        return

    self._设置页_上次屏幕尺寸 = 当前尺寸

    屏幕宽 = max(1, int(当前尺寸[0] or 0))
    屏幕高 = max(1, int(当前尺寸[1] or 0))

    布局 = 计算设置页布局(屏幕宽, 屏幕高)
    if not isinstance(布局, dict):
        布局 = {}

    self._设置页_布局缩放 = float(布局.get("布局缩放", 1.0) or 1.0)

    面板矩形 = 布局.get("面板基础矩形", pygame.Rect(0, 0, 10, 10))
    if not isinstance(面板矩形, pygame.Rect):
        面板矩形 = pygame.Rect(0, 0, 10, 10)
    self._设置页_面板基础矩形 = 面板矩形

    行矩形表 = 布局.get("行矩形表", {})
    if not isinstance(行矩形表, dict):
        行矩形表 = {}
    self._设置页_行矩形表 = 行矩形表

    控件矩形表 = 布局.get("控件矩形表", {})
    if not isinstance(控件矩形表, dict):
        控件矩形表 = {}
    self._设置页_控件矩形表 = 控件矩形表

    背景区矩形 = 布局.get("背景区矩形", pygame.Rect(0, 0, 10, 10))
    if not isinstance(背景区矩形, pygame.Rect):
        背景区矩形 = pygame.Rect(0, 0, 10, 10)
    self._设置页_背景区矩形 = 背景区矩形

    背景控件矩形 = 布局.get("背景控件矩形", {})
    if not isinstance(背景控件矩形, dict):
        背景控件矩形 = {}

    self._设置页_背景控件矩形 = {
        "左": 背景控件矩形.get("左", pygame.Rect(0, 0, 1, 1))
        if isinstance(背景控件矩形.get("左", None), pygame.Rect)
        else pygame.Rect(0, 0, 1, 1),
        "右": 背景控件矩形.get("右", pygame.Rect(0, 0, 1, 1))
        if isinstance(背景控件矩形.get("右", None), pygame.Rect)
        else pygame.Rect(0, 0, 1, 1),
        "预览": 背景控件矩形.get("预览", pygame.Rect(0, 0, 1, 1))
        if isinstance(背景控件矩形.get("预览", None), pygame.Rect)
        else pygame.Rect(0, 0, 1, 1),
    }

    箭头预览矩形 = 布局.get("箭头预览矩形", pygame.Rect(0, 0, 10, 10))
    if not isinstance(箭头预览矩形, pygame.Rect):
        箭头预览矩形 = pygame.Rect(0, 0, 10, 10)
    self._设置页_箭头预览矩形 = 箭头预览矩形

    箭头预览控件矩形 = 布局.get("箭头预览控件矩形", {})
    if not isinstance(箭头预览控件矩形, dict):
        箭头预览控件矩形 = {}

    self._设置页_箭头预览控件矩形 = {
        "左": 箭头预览控件矩形.get("左", pygame.Rect(0, 0, 1, 1))
        if isinstance(箭头预览控件矩形.get("左", None), pygame.Rect)
        else pygame.Rect(0, 0, 1, 1),
        "右": 箭头预览控件矩形.get("右", pygame.Rect(0, 0, 1, 1))
        if isinstance(箭头预览控件矩形.get("右", None), pygame.Rect)
        else pygame.Rect(0, 0, 1, 1),
    }

    视觉参数 = 布局.get("视觉参数", {})
    if not isinstance(视觉参数, dict):
        视觉参数 = {}
    self._设置页_视觉参数 = 视觉参数

    self._设置页_面板绘制矩形 = 面板矩形.copy()

    try:
        if getattr(self, "_设置页_调试器", None) is not None:
            self._设置页_调试器.应用保存覆盖(self)
    except Exception:
        pass

    try:
        _设置页_统一行按钮尺寸(self)
    except Exception:
        pass

    try:
        _设置页_钳制全部控件到面板(self)
    except Exception:
        pass


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
    选歌游戏._重算设置页布局 = 重算设置页布局
    选歌游戏._设置页_缓入 = _设置页_缓入
    选歌游戏._设置页_缓出 = _设置页_缓出
    选歌游戏._设置页_点在有效面板区域 = _设置页_点在有效面板区域
    选歌游戏.打开设置页 = 打开设置页
    选歌游戏.关闭设置页 = 关闭设置页
    选歌游戏._设置页_切换选项 = _设置页_切换选项
    选歌游戏._设置页_切换背景 = _设置页_切换背景
    选歌游戏._设置页_处理事件 = _设置页_处理事件
    选歌游戏.绘制设置页 = 绘制设置页
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
        self._更新连续翻页()
        self._更新过渡()
    except Exception:
        pass

    if bool(getattr(self, "_需要退出", False)):
        return str(getattr(self, "_返回状态", "NORMAL") or "NORMAL")
    return None

def 选歌_帧绘制(self):
    self._确保公共交互()

    try:
        try:
            刷新选歌布局常量()
        except Exception:
            pass
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

        try:
            if getattr(self, "_全局点击特效", None) is not None:
                self._全局点击特效.更新并绘制(self.屏幕)
        except Exception:
            pass

        try:
            self._绘制消息提示()
        except Exception:
            pass

    except Exception:
        pass

def 选歌_处理事件_外部(self, 事件):
    self._确保公共交互()

    if 事件 is None:
        return None

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

    if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
        try:
            if getattr(self, "_全局点击特效", None) is not None:
                x, y = 事件.pos
                self._全局点击特效.触发(int(x), int(y))
        except Exception:
            pass

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

    if bool(getattr(self, "是否设置页", False)):
        try:
            self._设置页_处理事件(事件)
        except Exception:
            pass
        return None

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

    self._处理列表页输入(事件)

    if bool(getattr(self, "_需要退出", False)):
        return str(getattr(self, "_返回状态", "NORMAL") or "NORMAL")
    return None

def 绑定场景化方法到选歌游戏类():
    选歌游戏.绑定外部屏幕 = 选歌_绑定外部屏幕
    选歌游戏.帧更新 = 选歌_帧更新
    选歌游戏.帧绘制 = 选歌_帧绘制
    选歌游戏.处理事件_外部 = 选歌_处理事件_外部

绑定场景化方法到选歌游戏类()

def main():
    资源根目录 = _取项目根目录()
    songs根目录 = _取songs根目录()
    背景音乐路径 = os.path.join(资源根目录, "冷资源", "backsound", "devil.mp3")


    游戏 = 选歌游戏(
        songs根目录=songs根目录,
        背景音乐路径=背景音乐路径,
        是否继承已有窗口=False,
    )
    游戏.主循环()


def 运行选歌(玩家数: int, 类型名: str, 模式名: str, 背景音乐路径: str):
    songs根目录 = _取songs根目录()

    游戏 = 选歌游戏(
        songs根目录=songs根目录,
        背景音乐路径=背景音乐路径,
        指定类型名=类型名,
        指定模式名=模式名,
        玩家数=玩家数,
        是否继承已有窗口=True,
    )
    return 游戏.主循环()


if __name__ == "__main__":
    main()
