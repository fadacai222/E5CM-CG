import os
import sys
import time
from typing import Dict, Optional, List

import pygame
from core.歌曲记录 import 取歌曲记录
from core.工具 import 绘制底部联网与信用
from scenes.场景基类 import 场景基类
from ui.选歌设置菜单控件 import 构建设置参数文本


_项目根目录_缓存: str | None = None


def _取项目根目录() -> str:
    global _项目根目录_缓存
    try:
        if (
            isinstance(_项目根目录_缓存, str)
            and _项目根目录_缓存
            and os.path.isdir(_项目根目录_缓存)
        ):
            return _项目根目录_缓存
    except Exception:
        pass

    def _规范路径(路径: str) -> str:
        try:
            return os.path.abspath(str(路径 or "").strip())
        except Exception:
            return ""

    候选起点列表: List[str] = []

    try:
        if getattr(sys, "frozen", False):
            临时资源目录 = _规范路径(getattr(sys, "_MEIPASS", ""))
            if 临时资源目录:
                候选起点列表.append(临时资源目录)
            候选起点列表.append(
                _规范路径(os.path.dirname(os.path.abspath(sys.executable)))
            )
    except Exception:
        pass

    try:
        候选起点列表.append(_规范路径(os.path.dirname(os.path.abspath(__file__))))
    except Exception:
        pass

    try:
        候选起点列表.append(_规范路径(os.getcwd()))
    except Exception:
        pass

    已检查 = set()
    for 起点 in 候选起点列表:
        当前 = _规范路径(起点)
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
            _项目根目录_缓存 = _规范路径(起点)
            return _项目根目录_缓存

    _项目根目录_缓存 = _规范路径(os.getcwd()) or "."
    return _项目根目录_缓存


def _取运行根目录() -> str:
    try:
        已缓存路径 = getattr(_取运行根目录, "_缓存路径", "")
        if isinstance(已缓存路径, str) and 已缓存路径 and os.path.isdir(已缓存路径):
            return 已缓存路径
    except Exception:
        pass

    def _规范路径(路径: str) -> str:
        try:
            return os.path.abspath(str(路径 or "").strip())
        except Exception:
            return ""

    候选起点列表: List[str] = []

    try:
        if getattr(sys, "frozen", False):
            候选起点列表.append(
                _规范路径(os.path.dirname(os.path.abspath(sys.executable)))
            )
    except Exception:
        pass

    try:
        候选起点列表.append(_规范路径(os.getcwd()))
    except Exception:
        pass

    try:
        候选起点列表.append(_规范路径(os.path.dirname(os.path.abspath(__file__))))
    except Exception:
        pass

    已检查 = set()
    for 起点 in 候选起点列表:
        当前 = _规范路径(起点)
        if (not 当前) or (当前 in 已检查):
            continue
        已检查.add(当前)

        for _ in range(10):
            if (
                os.path.isdir(os.path.join(当前, "songs"))
                or os.path.isdir(os.path.join(当前, "json"))
                or os.path.isfile(os.path.join(当前, "main.py"))
            ):
                setattr(_取运行根目录, "_缓存路径", 当前)
                return 当前
            上级 = os.path.dirname(当前)
            if 上级 == 当前:
                break
            当前 = 上级

    try:
        if getattr(sys, "frozen", False):
            回退目录 = _规范路径(os.path.dirname(os.path.abspath(sys.executable)))
            setattr(_取运行根目录, "_缓存路径", 回退目录)
            return 回退目录
    except Exception:
        pass

    回退目录 = _规范路径(os.getcwd()) or "."
    setattr(_取运行根目录, "_缓存路径", 回退目录)
    return 回退目录


def _安全加载图片(路径: str, 透明: bool = True) -> Optional[pygame.Surface]:
    try:
        if (not 路径) or (not os.path.isfile(路径)):
            return None
        图 = pygame.image.load(路径)
        return 图.convert_alpha() if 透明 else 图.convert()
    except Exception:
        return None


def _contain缩放(图片: pygame.Surface, 目标宽: int, 目标高: int) -> pygame.Surface:
    ow, oh = 图片.get_size()
    ow = max(1, int(ow))
    oh = max(1, int(oh))
    目标宽 = max(1, int(目标宽))
    目标高 = max(1, int(目标高))

    比例 = min(目标宽 / ow, 目标高 / oh)
    nw = max(1, int(ow * 比例))
    nh = max(1, int(oh * 比例))
    缩放 = pygame.transform.smoothscale(图片, (nw, nh)).convert_alpha()

    画布 = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
    画布.fill((0, 0, 0, 0))
    x = (目标宽 - nw) // 2
    y = (目标高 - nh) // 2
    画布.blit(缩放, (x, y))
    return 画布


def _获取字体(字号: int, 是否粗体: bool = False) -> pygame.font.Font:
    """
    优先用 core.工具 的 获取字体；没有就回退系统字体。
    """
    try:
        from core.工具 import 获取字体  # type: ignore

        return 获取字体(int(字号), 是否粗体=bool(是否粗体))
    except Exception:
        pygame.font.init()
        try:
            return pygame.font.SysFont(
                "Microsoft YaHei", int(字号), bold=bool(是否粗体)
            )
        except Exception:
            return pygame.font.Font(None, int(字号))


def _自动换行(字体: pygame.font.Font, 文本: str, 最大宽: int) -> List[str]:
    文本 = str(文本 or "").replace("\r", "")
    最大宽 = max(1, int(最大宽))
    行列表: List[str] = []
    当前行 = ""

    for ch in 文本:
        if ch == "\n":
            行列表.append(当前行)
            当前行 = ""
            continue

        测试 = 当前行 + ch
        try:
            if 字体.size(测试)[0] <= 最大宽:
                当前行 = 测试
            else:
                if 当前行:
                    行列表.append(当前行)
                当前行 = ch
        except Exception:
            当前行 = 测试

    if 当前行:
        行列表.append(当前行)
    return 行列表


def _载荷值有效(值) -> bool:
    if 值 is None:
        return False
    if isinstance(值, str):
        文本 = 值.strip()
        return 文本.lower() not in ("", "未知", "loading...")
    if isinstance(值, (list, tuple, set, dict)):
        return len(值) > 0
    return True


def _合并载荷源(*载荷源) -> Dict:
    合并后: Dict = {}
    for 载荷 in 载荷源:
        if not isinstance(载荷, dict):
            continue
        for 键, 值 in 载荷.items():
            if _载荷值有效(值) or (键 not in 合并后):
                if isinstance(值, dict):
                    合并后[键] = dict(值)
                elif isinstance(值, list):
                    合并后[键] = list(值)
                else:
                    合并后[键] = 值
    return 合并后


class 场景_加载页(场景基类):
    名称 = "加载页"

    _设计宽 = 2048
    _设计高 = 1152

    def __init__(self, 上下文: dict):
        super().__init__(上下文)

        self._载荷: Dict = {}
        self._入场开始 = 0.0

        # ✅ 个人资料缓存（避免每帧读盘）
        self._个人资料路径: str = ""
        self._个人资料_mtime: float = 0.0
        self._个人资料数据: dict = {}

        # ✅ 渲染用字段（全部兜底）
        self._个人昵称: str = "未知"
        self._最高分: int = 0
        self._最大等级: int = 0

        # ✅ JSON 布局渲染器（运行时用）
        self._布局路径: str = ""
        self._布局渲染器 = None
        self._联网原图: Optional[pygame.Surface] = None
        self._选歌设置数据: dict = {}
        self._选歌设置参数文本: str = ""
        self._背景原图: Optional[pygame.Surface] = None
        self._背景缩放缓存: Optional[pygame.Surface] = None
        self._背景缩放尺寸 = (0, 0)
        self._星星原图: Optional[pygame.Surface] = None
        self._封面原图: Optional[pygame.Surface] = None
        self._封面缩放缓存: Optional[pygame.Surface] = None
        self._封面缩放尺寸 = (0, 0)

    def 进入(self, 载荷=None):
        self._入场开始 = time.time()

        状态载荷 = {}
        try:
            状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
            临时载荷 = (状态 or {}).get("加载页_载荷", {})
            if isinstance(临时载荷, dict):
                状态载荷 = dict(临时载荷)
        except Exception:
            状态载荷 = {}

        传入载荷 = dict(载荷) if isinstance(载荷, dict) else {}
        落盘载荷 = self._读取加载页json()
        self._载荷 = _合并载荷源(落盘载荷, 状态载荷, 传入载荷)

        self._选歌设置数据 = self._读取选歌设置json()
        self._选歌设置参数文本 = self._构建选歌设置参数文本(self._选歌设置数据)

        try:
            资源根目录 = _取项目根目录()
            运行根目录 = _取运行根目录()

            个人资料候选路径列表 = [
                os.path.join(运行根目录, "json", "个人资料.json"),
                os.path.join(资源根目录, "json", "个人资料.json"),
                os.path.join(
                    资源根目录, "UI-img", "个人中心-个人资料", "个人资料.json"
                ),
            ]
            self._个人资料路径 = str(个人资料候选路径列表[0])
            for 候选路径 in 个人资料候选路径列表:
                if 候选路径 and os.path.isfile(候选路径):
                    self._个人资料路径 = 候选路径
                    break

            布局候选路径列表 = [
                os.path.join(运行根目录, "json", "加载页_布局.json"),
                os.path.join(资源根目录, "json", "加载页_布局.json"),
            ]
            self._布局路径 = str(布局候选路径列表[0])
            for 候选路径 in 布局候选路径列表:
                if 候选路径 and os.path.isfile(候选路径):
                    self._布局路径 = 候选路径
                    break

            try:
                from ui.调试_加载页_渲染控件 import 加载页布局渲染器  # type: ignore

                self._布局渲染器 = 加载页布局渲染器(
                    self._布局路径,
                    项目根目录=资源根目录,
                )
            except Exception:
                self._布局渲染器 = None

            try:
                联网图路径 = str(
                    (self.上下文.get("资源", {}) or {}).get("投币_联网图标", "") or ""
                )
                if 联网图路径 and os.path.isfile(联网图路径):
                    self._联网原图 = pygame.image.load(联网图路径).convert_alpha()
                else:
                    self._联网原图 = None
            except Exception:
                self._联网原图 = None

        except Exception:
            self._个人资料路径 = ""
            self._布局路径 = ""
            self._布局渲染器 = None
            self._联网原图 = None

        try:
            if isinstance(self.上下文, dict):
                状态 = self.上下文.get("状态", {}) or {}
                if isinstance(状态, dict):
                    状态["加载页_载荷"] = dict(self._载荷)
        except Exception:
            pass

        self._加载资源()
        self._加载封面()
        self._刷新个人资料缓存(强制=True)

    def _读取个人资料json(self, 文件路径: str) -> dict:
        try:
            import json
        except Exception:
            return {}

        try:
            if (not 文件路径) or (not os.path.isfile(文件路径)):
                return {}

            with open(文件路径, "r", encoding="utf-8") as f:
                数据 = json.load(f)

            return dict(数据) if isinstance(数据, dict) else {}
        except Exception:
            return {}

    def _刷新个人资料缓存(self, 强制: bool = False):
        """
        ✅ 读取 UI-img\\个人中心-个人资料\\个人资料.json
        并提取：
        - 昵称 -> 记录保持者、店名
        - 当前歌曲最高分 -> 歌曲记录索引
        - 进度.最大等级
        """
        路径 = str(getattr(self, "_个人资料路径", "") or "")
        if not 路径:
            # 兜底
            self._个人昵称 = "未知"
            self._最高分 = 0
            self._最大等级 = 0
            self._个人资料数据 = {}
            return

        try:
            if not os.path.isfile(路径):
                self._个人昵称 = "未知"
                self._最高分 = 0
                self._最大等级 = 0
                self._个人资料数据 = {}
                return

            mtime = float(os.path.getmtime(路径))
            if (not 强制) and (
                mtime == float(getattr(self, "_个人资料_mtime", 0.0) or 0.0)
            ):
                return

            数据 = self._读取个人资料json(路径)
            self._个人资料数据 = 数据 if isinstance(数据, dict) else {}
            self._个人资料_mtime = mtime

            昵称 = str(self._个人资料数据.get("昵称", "") or "").strip()
            if not 昵称:
                昵称 = "未知"

            最高分 = 0
            try:
                根目录 = _取项目根目录()
                记录 = 取歌曲记录(
                    根目录,
                    str(self._载荷.get("sm路径", "") or ""),
                    str(self._载荷.get("歌名", "") or ""),
                )
                最高分 = int((记录 or {}).get("最高分", 0) or 0)
            except Exception:
                最高分 = 0

            最大等级 = 0
            try:
                最大等级 = int(
                    ((self._个人资料数据.get("进度", {}) or {}).get("最大等级", 0) or 0)
                )
            except Exception:
                最大等级 = 0

            self._个人昵称 = 昵称
            self._最高分 = max(0, int(最高分))
            self._最大等级 = max(0, int(最大等级))

        except Exception:
            self._个人昵称 = "未知"
            self._最高分 = 0
            self._最大等级 = 0
            self._个人资料数据 = {}

    def 退出(self):
        return

    def 更新(self):
        # ✅ 3 秒后自动“回车”：切到谱面播放器
        try:
            if (time.time() - float(getattr(self, "_入场开始", 0.0) or 0.0)) >= 3.0:
                return {
                    "切换到": "谱面播放器",
                    "载荷": dict(getattr(self, "_载荷", {}) or {}),
                    "禁用黑屏过渡": True,
                }
        except Exception:
            pass
        return None

    def 处理事件(self, 事件):
        if 事件.type == pygame.KEYDOWN:
            if 事件.key == pygame.K_ESCAPE:
                return {"切换到": "子模式", "禁用黑屏过渡": True}

            if 事件.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                # ✅ 进入谱面播放器：把当前载荷透传
                try:
                    载荷 = dict(getattr(self, "_载荷", {}) or {})
                except Exception:
                    载荷 = {}

                return {"切换到": "谱面播放器", "载荷": 载荷, "禁用黑屏过渡": True}

        return None

    def 绘制(self):
        屏幕: pygame.Surface = self.上下文["屏幕"]

        # ✅ 每帧轻量刷新（mtime 相同不会读盘）
        self._刷新个人资料缓存(强制=False)

        # ✅ 把载荷/个人资料“拍平”，保证布局 json 里 {占位符} 能直接用
        载荷 = dict(getattr(self, "_载荷", {}) or {})

        sm路径 = str(载荷.get("sm路径", "") or "")
        if not sm路径:
            sm路径 = "未知"

        设置参数文本 = str(getattr(self, "_选歌设置参数文本", "") or "")
        if not 设置参数文本:
            设置参数文本 = str(载荷.get("设置参数文本", "") or "")
        if not 设置参数文本:
            设置参数 = 载荷.get("设置参数", {})
            设置参数文本 = f"设置参数：{设置参数}" if 设置参数 else "设置参数：默认"

        歌名 = str(载荷.get("歌名", "") or "Loading...")
        try:
            星级 = int(载荷.get("星级", 0) or 0)
        except Exception:
            星级 = 0

        bpm = 载荷.get("bpm", None)
        try:
            bpm显示 = str(int(bpm)) if bpm is not None else "?"
        except Exception:
            bpm显示 = "?"

        人气 = 载荷.get("人气", 0)
        try:
            人气显示 = str(int(人气))
        except Exception:
            人气显示 = "0"

        昵称 = str(getattr(self, "_个人昵称", "未知") or "未知")
        最高分 = int(getattr(self, "_最高分", 0) or 0)
        最大等级 = int(getattr(self, "_最大等级", 0) or 0)
        店名 = f"{昵称}的电脑"
        舞队 = "e舞成名重构版玩家大队"

        渲染数据 = {
            # 占位符直接用
            "sm路径": sm路径,
            "设置参数文本": 设置参数文本,
            "歌名": 歌名,
            "星级": max(0, 星级),
            "bpm": bpm显示,
            "人气": 人气显示,
            "个人昵称": 昵称,
            "最高分": max(0, int(最高分)),
            "最大等级": max(0, int(最大等级)),
            "店名": 店名,
            "舞队": 舞队,
            # 给 $.载荷.xxx 用（比如封面路径）
            "载荷": 载荷,
        }

        渲染器 = getattr(self, "_布局渲染器", None)
        if 渲染器 is None:
            # ✅ 兜底：避免黑屏
            屏幕.fill((0, 0, 0))
            字体 = _获取字体(28, 是否粗体=True)
            面 = 字体.render("加载页布局渲染器未初始化", True, (255, 255, 255))
            屏幕.blit(面, (30, 30))
            return

        # ✅ 运行时不显示边框（你的要求）
        渲染器.绘制(屏幕, 渲染数据, 显示全部边框=False, 选中id=None)
        self._绘制底部币值(屏幕)

    def _绘制底部币值(self, 屏幕: pygame.Surface):
        try:
            字体_credit = (self.上下文.get("字体", {}) or {}).get("投币_credit字")
        except Exception:
            字体_credit = None
        if not isinstance(字体_credit, pygame.font.Font):
            return
        try:
            状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
            投币数 = int((状态 or {}).get("投币数", 0) or 0)
            所需信用 = int((状态 or {}).get("每局所需信用", 3) or 3)
        except Exception:
            投币数 = 0
            所需信用 = 3
        try:
            绘制底部联网与信用(
                屏幕=屏幕,
                联网原图=getattr(self, "_联网原图", None),
                字体_credit=字体_credit,
                credit数值=f"{max(0, 投币数)}/{int(max(1, 所需信用))}",
                总信用需求=int(max(1, 所需信用)),
                文本=f"CREDIT：{max(0, 投币数)}/{int(max(1, 所需信用))}",
            )
        except Exception:
            pass

    def _读取加载页json(self) -> dict:
        try:
            import json
        except Exception:
            return {}

        候选路径列表 = [
            os.path.join(_取运行根目录(), "json", "加载页.json"),
            os.path.join(_取项目根目录(), "json", "加载页.json"),
        ]

        for 路径 in 候选路径列表:
            try:
                if (not 路径) or (not os.path.isfile(路径)):
                    continue
                for 编码 in ("utf-8-sig", "utf-8", "gbk"):
                    try:
                        with open(路径, "r", encoding=编码) as 文件:
                            数据 = json.load(文件)
                        return dict(数据) if isinstance(数据, dict) else {}
                    except Exception:
                        continue
            except Exception:
                continue

        return {}

    def _读取选歌设置json(self) -> dict:
        try:
            import json
        except Exception:
            return {}

        候选路径列表 = [
            os.path.join(_取运行根目录(), "json", "选歌设置.json"),
            os.path.join(_取项目根目录(), "json", "选歌设置.json"),
        ]

        for 路径 in 候选路径列表:
            try:
                if (not 路径) or (not os.path.isfile(路径)):
                    continue
                for 编码 in ("utf-8-sig", "utf-8", "gbk"):
                    try:
                        with open(路径, "r", encoding=编码) as 文件:
                            数据 = json.load(文件)
                        return dict(数据) if isinstance(数据, dict) else {}
                    except Exception:
                        continue
            except Exception:
                continue

        return {}

    def _构建选歌设置参数文本(self, 设置数据: dict) -> str:
        if not isinstance(设置数据, dict):
            return ""
        文本 = str(设置数据.get("设置参数文本", "") or "")
        if 文本:
            return 文本

        参数 = 设置数据.get("设置参数", {})
        if not isinstance(参数, dict):
            参数 = {}
        背景文件名 = str(设置数据.get("背景文件名", "") or "")
        箭头文件名 = str(设置数据.get("箭头文件名", "") or "")
        return 构建设置参数文本(
            设置参数=参数,
            背景文件名=背景文件名,
            箭头文件名=箭头文件名,
        )

    # ---------------- 内部：资源 ----------------
    def _加载资源(self):
        根目录 = ""
        try:
            资源 = self.上下文.get("资源", {}) or {}
            根目录 = str(资源.get("根", "") or "")
        except Exception:
            根目录 = ""

        if not 根目录:
            根目录 = _取项目根目录()

        背景路径 = os.path.join(根目录, "冷资源", "backimages", "选歌界面.png")
        self._背景原图 = _安全加载图片(背景路径, 透明=False)

        星星路径 = os.path.join(
            根目录, "UI-img", "选歌界面资源", "小星星", "大星星.png"
        )
        self._星星原图 = _安全加载图片(星星路径, 透明=True)

    def _加载封面(self):
        封面路径 = str(self._载荷.get("封面路径", "") or "")
        self._封面原图 = _安全加载图片(封面路径, 透明=True)
        self._封面缩放缓存 = None
        self._封面缩放尺寸 = (0, 0)

    # ---------------- 内部：绘制 ----------------
    def _绘制背景(self, 屏幕: pygame.Surface):
        w, h = 屏幕.get_size()
        if self._背景原图 is None:
            屏幕.fill((0, 0, 0))
            return

        目标尺寸 = (int(w), int(h))
        if self._背景缩放缓存 is None or self._背景缩放尺寸 != 目标尺寸:
            try:
                self._背景缩放缓存 = pygame.transform.smoothscale(
                    self._背景原图, 目标尺寸
                ).convert()
                self._背景缩放尺寸 = 目标尺寸
            except Exception:
                self._背景缩放缓存 = None
                self._背景缩放尺寸 = (0, 0)

        if self._背景缩放缓存 is not None:
            屏幕.blit(self._背景缩放缓存, (0, 0))
        else:
            屏幕.fill((0, 0, 0))

        # 暗化遮罩，保证文字可读
        暗层 = pygame.Surface((w, h), pygame.SRCALPHA)
        暗层.fill((0, 0, 0, 70))
        屏幕.blit(暗层, (0, 0))

    def _绘制半透明底板(
        self, 屏幕: pygame.Surface, 矩形: pygame.Rect, alpha: int, 圆角: int = 18
    ):
        alpha = max(0, min(255, int(alpha)))
        圆角 = max(6, int(圆角))

        面 = pygame.Surface((矩形.w, 矩形.h), pygame.SRCALPHA)
        面.fill((0, 0, 0, 0))
        pygame.draw.rect(
            面,
            (0, 0, 0, alpha),
            pygame.Rect(0, 0, 矩形.w, 矩形.h),
            border_radius=圆角,
        )
        pygame.draw.rect(
            面,
            (160, 160, 160, min(220, alpha + 40)),
            pygame.Rect(0, 0, 矩形.w, 矩形.h),
            width=2,
            border_radius=圆角,
        )
        屏幕.blit(面, 矩形.topleft)

    def _绘制顶部信息(self, 屏幕: pygame.Surface, 顶区: pygame.Rect):
        字体 = _获取字体(max(18, int(顶区.h * 0.14)), 是否粗体=True)
        小字体 = _获取字体(max(16, int(顶区.h * 0.12)), 是否粗体=False)

        sm路径 = str(self._载荷.get("sm路径", "") or "")
        if not sm路径:
            sm路径 = "SM路径：未知"

        参数文本 = str(self._载荷.get("设置参数文本", "") or "")
        if not 参数文本:
            # 兜底：直接把 dict 打出来
            设置参数 = self._载荷.get("设置参数", {})
            参数文本 = f"设置参数：{设置参数}"

        x = 顶区.x + 18
        y = 顶区.y + 14
        最大宽 = max(60, 顶区.w - 36)

        # 第一行：SM路径
        行列表1 = _自动换行(字体, f"SM路径：{sm路径}", 最大宽)
        for 行 in 行列表1[:2]:  # 顶区别太挤，最多两行
            面 = 字体.render(行, True, (255, 255, 255))
            屏幕.blit(面, (x, y))
            y += 面.get_height() + 6

        # 第二块：设置参数
        行列表2 = _自动换行(小字体, 参数文本, 最大宽)
        for 行 in 行列表2[:4]:
            面 = 小字体.render(行, True, (235, 235, 235))
            屏幕.blit(面, (x, y))
            y += 面.get_height() + 4

    def _绘制缩略图(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        # 外框
        self._绘制半透明底板(屏幕, 区域, alpha=140, 圆角=16)

        if self._封面原图 is None:
            字体 = _获取字体(max(16, int(区域.h * 0.12)), 是否粗体=False)
            文面 = 字体.render("无封面", True, (255, 255, 255))
            rr = 文面.get_rect(center=区域.center)
            屏幕.blit(文面, rr.topleft)
            return

        目标尺寸 = (int(区域.w - 16), int(区域.h - 16))
        if self._封面缩放缓存 is None or self._封面缩放尺寸 != 目标尺寸:
            try:
                图 = self._封面原图.convert_alpha()
            except Exception:
                图 = self._封面原图
            self._封面缩放缓存 = _contain缩放(图, 目标尺寸[0], 目标尺寸[1])
            self._封面缩放尺寸 = 目标尺寸

        if self._封面缩放缓存 is not None:
            x = 区域.x + (区域.w - self._封面缩放缓存.get_width()) // 2
            y = 区域.y + (区域.h - self._封面缩放缓存.get_height()) // 2
            屏幕.blit(self._封面缩放缓存, (x, y))

    def _绘制右侧信息(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        # 星星/歌名/人气BPM 的纵向信息
        歌名 = str(self._载荷.get("歌名", "") or "Loading...")
        星级 = int(self._载荷.get("星级", 0) or 0)
        bpm = self._载荷.get("bpm", None)
        try:
            bpm显示 = str(int(bpm)) if bpm is not None else "?"
        except Exception:
            bpm显示 = "?"

        人气 = self._载荷.get("人气", 0)
        try:
            人气显示 = str(int(人气))
        except Exception:
            人气显示 = "0"

        标题白 = (255, 255, 255)

        星区 = pygame.Rect(区域.x, 区域.y, 区域.w, int(区域.h * 0.28))
        线1 = pygame.Rect(区域.x, 星区.bottom, 区域.w, max(2, int(区域.h * 0.02)))
        名区 = pygame.Rect(区域.x, 线1.bottom, 区域.w, int(区域.h * 0.20))
        线2 = pygame.Rect(区域.x, 名区.bottom, 区域.w, max(2, int(区域.h * 0.02)))
        数值区 = pygame.Rect(区域.x, 线2.bottom, 区域.w, int(区域.h * 0.20))
        线3 = pygame.Rect(区域.x, 数值区.bottom, 区域.w, max(2, int(区域.h * 0.02)))

        # 星星
        self._绘制星星行(屏幕, 星区, 星级)

        # 分割线
        self._绘制分割线(屏幕, 线1)
        self._绘制分割线(屏幕, 线2)
        self._绘制分割线(屏幕, 线3)

        # 歌名（白色）
        歌名字体 = _获取字体(max(28, int(区域.h * 0.12)), 是否粗体=False)
        歌名面 = 歌名字体.render(歌名, True, 标题白)
        rr = 歌名面.get_rect(center=名区.center)
        屏幕.blit(歌名面, rr.topleft)

        # 人气 / BPM（白色）
        数值字体 = _获取字体(max(22, int(区域.h * 0.10)), 是否粗体=False)
        左文 = 数值字体.render(f"人气：{人气显示}", True, 标题白)
        右文 = 数值字体.render(f"BPM：{bpm显示}", True, 标题白)

        左pos = (数值区.x + int(数值区.w * 0.08), 数值区.centery)
        右pos = (数值区.right - int(数值区.w * 0.08), 数值区.centery)

        左r = 左文.get_rect(midleft=左pos)
        右r = 右文.get_rect(midright=右pos)

        屏幕.blit(左文, 左r.topleft)
        屏幕.blit(右文, 右r.topleft)

    def _绘制分割线(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        y = int(区域.centery)
        x1 = int(区域.x + 区域.w * 0.02)
        x2 = int(区域.right - 区域.w * 0.02)
        pygame.draw.line(
            屏幕, (160, 160, 160), (x1, y), (x2, y), width=max(1, int(区域.h))
        )

    def _绘制星星行(self, 屏幕: pygame.Surface, 区域: pygame.Rect, 星数: int):
        星数 = max(0, int(星数))
        if 星数 <= 0:
            return

        if self._星星原图 is None:
            # 兜底：用字符星星
            字体 = _获取字体(max(18, int(区域.h * 0.60)), 是否粗体=False)
            文 = "★" * min(20, 星数)
            面 = 字体.render(文, True, (255, 220, 80))
            rr = 面.get_rect(center=区域.center)
            屏幕.blit(面, rr.topleft)
            return

        目标高 = max(10, int(区域.h * 0.55))
        try:
            星图 = pygame.transform.smoothscale(
                self._星星原图,
                (
                    int(
                        self._星星原图.get_width()
                        * (目标高 / max(1, self._星星原图.get_height()))
                    ),
                    目标高,
                ),
            ).convert_alpha()
        except Exception:
            return

        星w, 星h = 星图.get_size()
        间距 = max(2, int(星w * 0.12))

        每行最大 = 12
        if 星数 <= 每行最大:
            行1 = 星数
            行2 = 0
        else:
            行2 = 每行最大
            行1 = 星数 - 每行最大

        行高 = 星h
        行距 = max(4, int(星h * 0.25))
        总高 = 行高 if 行2 == 0 else (行高 * 2 + 行距)

        起始y = 区域.y + (区域.h - 总高) // 2

        def _画一行(数量: int, y: int):
            if 数量 <= 0:
                return
            总宽 = 数量 * 星w + max(0, 数量 - 1) * 间距
            x0 = 区域.centerx - 总宽 // 2
            for i in range(数量):
                屏幕.blit(星图, (x0 + i * (星w + 间距), y))

        _画一行(行1, 起始y)
        if 行2 > 0:
            _画一行(行2, 起始y + 行高 + 行距)

    def _绘制左下记录(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        # ✅ 每帧轻量刷新（mtime 相同不会读盘）
        self._刷新个人资料缓存(强制=False)

        绿 = (167, 226, 180)
        粉 = (224, 167, 178)

        字体 = _获取字体(max(22, int(区域.h * 0.20)), 是否粗体=False)
        行高 = int(字体.get_height() * 1.35)

        x = 区域.x + 10
        y = 区域.y + 6

        记录保持者 = str(getattr(self, "_个人昵称", "未知") or "未知")
        最高分 = int(getattr(self, "_最高分", 0) or 0)

        文1 = 字体.render(f"记录保持者：         {记录保持者}", True, 绿)
        文2 = 字体.render(f"最高分：         {最高分}", True, 粉)

        屏幕.blit(文1, (x, y))
        屏幕.blit(文2, (x, y + 行高))

    def _绘制右下记录(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        # ✅ 每帧轻量刷新（mtime 相同不会读盘）
        self._刷新个人资料缓存(强制=False)

        蓝绿 = (109, 204, 191)
        白 = (255, 255, 255)
        淡黄 = (247, 253, 235)

        字体 = _获取字体(max(22, int(区域.h * 0.20)), 是否粗体=False)
        行高 = int(字体.get_height() * 1.30)

        x = 区域.x + 10
        y = 区域.y + 6

        最大等级 = int(getattr(self, "_最大等级", 0) or 0)
        舞队 = "e舞成名重构版玩家大队"
        昵称 = str(getattr(self, "_个人昵称", "未知") or "未知")
        店名 = f"{昵称}的电脑"

        文1 = 字体.render(f"级别：{最大等级}", True, 蓝绿)
        文2 = 字体.render(f"所属舞队：{舞队}", True, 白)
        文3 = 字体.render(f"店名：{店名}", True, 淡黄)

        屏幕.blit(文1, (x, y))
        屏幕.blit(文2, (x, y + 行高))
        屏幕.blit(文3, (x, y + 行高 * 2))

    # ---------------- 内部：坐标映射 ----------------
    def _映射到屏幕_rect(self, bbox) -> pygame.Rect:
        """
        bbox: (l, t, r, b) in 设计坐标
        """
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()

        scale = min(w / self._设计宽, h / self._设计高)
        content_w = self._设计宽 * scale
        content_h = self._设计高 * scale
        ox = (w - content_w) / 2.0
        oy = (h - content_h) / 2.0

        l, t, r, b = bbox
        x = int(ox + l * scale)
        y = int(oy + t * scale)
        ww = int((r - l) * scale)
        hh = int((b - t) * scale)
        return pygame.Rect(x, y, max(1, ww), max(1, hh))
