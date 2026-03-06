import os
import sys
import math
from typing import Any, Dict, List, Optional, Tuple

import json

import pygame


def _取项目根目录() -> str:
    起点候选 = []
    try:
        if getattr(sys, "frozen", False):
            起点候选.append(os.path.dirname(os.path.abspath(sys.executable)))
        else:
            起点候选.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    起点候选.append(os.getcwd())

    for 起点 in 起点候选:
        当前 = os.path.abspath(起点)
        for _ in range(14):
            if (
                os.path.isdir(os.path.join(当前, "core"))
                and os.path.isdir(os.path.join(当前, "ui"))
                and os.path.isdir(os.path.join(当前, "songs"))
            ):
                return 当前
            上级 = os.path.dirname(当前)
            if 上级 == 当前:
                break
            当前 = 上级

    return os.path.abspath(起点候选[0])


def _安全读json(路径: str) -> dict:
    if (not 路径) or (not os.path.isfile(路径)):
        return {}
    import json

    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码) as f:
                obj = json.load(f)
            return obj if isinstance(obj, dict) else {}
        except Exception:
            continue
    try:
        with open(路径, "r", encoding="utf-8", errors="ignore") as f:
            obj = json.load(f)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _加载皮肤包(项目根: str, 箭头编号: str = "03") -> Any:
    class _空皮肤:
        pass

    箭头根目录 = os.path.join(项目根, "UI-img", "游戏界面", "箭头")
    皮肤目录 = os.path.join(
        箭头根目录, str(箭头编号 or "03")
    )
    if not os.path.isdir(皮肤目录):
        try:
            候选编号 = _收集可用箭头皮肤编号(项目根)
            if 候选编号:
                皮肤目录 = os.path.join(箭头根目录, str(候选编号[0]))
        except Exception:
            pass
    if not os.path.isdir(皮肤目录):
        return _空皮肤()

    try:
        from ui.谱面渲染器 import _皮肤包  # type: ignore

        皮肤包对象 = _皮肤包()
        皮肤包对象.加载(皮肤目录)
        return 皮肤包对象
    except Exception:
        return _空皮肤()


def _收集可用箭头皮肤编号(项目根: str) -> List[str]:
    根目录 = os.path.join(项目根, "UI-img", "游戏界面", "箭头")
    if not os.path.isdir(根目录):
        return ["03"]

    结果: List[str] = []
    try:
        for 名 in os.listdir(根目录):
            子目录 = os.path.join(根目录, 名)
            if not os.path.isdir(子目录):
                continue
            if os.path.isfile(os.path.join(子目录, "arrow", "skin.json")):
                结果.append(str(名))
    except Exception:
        return ["03"]

    if not 结果:
        return ["03"]

    def _排序键(v: str) -> Tuple[int, str]:
        s = str(v or "")
        return (0, f"{int(s):06d}") if s.isdigit() else (1, s.lower())

    return sorted(list(set(结果)), key=_排序键)


def _尝试加载头像与昵称(项目根: str) -> Tuple[Optional[pygame.Surface], str]:
    资料目录 = os.path.join(项目根, "UI-img", "个人中心-个人资料")
    资料路径 = os.path.join(资料目录, "个人资料.json")
    资料 = _安全读json(资料路径)
    昵称 = str((资料 or {}).get("昵称", "") or "").strip() or "布局调试"

    头像文件 = str((资料 or {}).get("头像文件", "") or "").strip()
    if not 头像文件:
        return None, 昵称

    if os.path.isabs(头像文件):
        头像路径 = 头像文件
    else:
        头像路径 = (
            os.path.join(项目根, 头像文件.replace("/", os.sep).replace("\\", os.sep))
            if 头像文件.startswith("UI-img/")
            else os.path.join(资料目录, os.path.basename(头像文件))
        )
    if not os.path.isfile(头像路径):
        return None, 昵称

    try:
        头像图 = pygame.image.load(头像路径).convert_alpha()
        return 头像图, 昵称
    except Exception:
        return None, 昵称


def _尝试加载段位图(项目根: str, 等级: int = 7) -> Optional[pygame.Surface]:
    资料目录 = os.path.join(项目根, "UI-img", "个人中心-个人资料")
    资料路径 = os.path.join(资料目录, "个人资料.json")
    资料 = _安全读json(资料路径) or {}
    进度 = 资料.get("进度", {}) if isinstance(资料.get("进度", {}), dict) else {}
    段位值 = str(进度.get("段位", "") or "").strip()
    if 段位值:
        if os.path.isabs(段位值):
            路径 = 段位值
        else:
            路径 = os.path.join(
                项目根, 段位值.replace("/", os.sep).replace("\\", os.sep)
            )
    else:
        路径 = os.path.join(
            项目根, "UI-img", "个人中心-个人资料", "等级", f"{int(等级)}.png"
        )
    if not os.path.isfile(路径):
        return None
    try:
        return pygame.image.load(路径).convert_alpha()
    except Exception:
        return None


def _尝试加载背景图(项目根: str) -> Optional[str]:
    # 你没给具体背景选择逻辑，调试器先用一个稳定兜底
    候选 = [
        os.path.join(项目根, "冷资源", "backimages", "选歌界面.png"),
    ]
    for 路径 in 候选:
        if os.path.isfile(路径):
            return 路径
    return None


def _构建调试上下文(
    强制显示: bool,
    当前秒: float,
    头像图: Optional[pygame.Surface],
    段位图: Optional[pygame.Surface],
    玩家昵称: str,
    歌曲名: str,
    歌曲星级文本: str,
    屏幕尺寸: Tuple[int, int],
    布局管理器: Any,
    模拟普通击中特效: bool,
    模拟hold击中特效循环: bool,
    模拟满血暴走: bool,
    调试血量显示: float,
    调试血条颜色: Tuple[int, int, int],
    调试血条亮度: float,
    调试血条不透明度: float,
    调试血条晃荡速度: float,
    调试血条晃荡幅度: float,
    调试暴走血条速度: float,
    调试头像框特效速度: float,
    模拟调速倍率: float = 4.0,
    模拟隐藏模式: str = "关闭",
    模拟轨迹模式: str = "摇摆",
    模拟方向模式: str = "关闭",
    模拟大小模式: str = "正常",
    模拟双踏板模式: bool = False,
    半隐入口比例: float = 0.5,
    摇摆幅度倍率: float = 1.0,
    旋转速度度每秒: float = 450.0,
    隐藏控件ids: Optional[List[str]] = None,
    圆环频谱对象: Any = None,
    调试暴走血条不透明度: float = 1.0,
    调试暴走血条羽化: float = 8.0,
    圆环频谱启用旋转: bool = False,
    圆环频谱背景板转速: float = 36.0,
    圆环频谱变化落差: float = 1.0,
    圆环频谱线条数量: int = 200,
    圆环频谱线条粗细: int = 2,
    圆环频谱线条间隔: int = 1,
) -> Dict[str, Any]:
    屏宽 = int(max(1, 屏幕尺寸[0]))
    屏高 = int(max(1, 屏幕尺寸[1]))

    try:
        比例 = float(布局管理器.取全局缩放((屏宽, 屏高)))
    except Exception:
        比例 = 1.0
    if 比例 <= 0:
        比例 = 1.0

    游戏区参数 = {
        "y偏移": -12.0,
        "缩放": 1.0,
        "hold宽度系数": 0.96,
        "判定区宽度系数": 1.0,
        "击中特效宽度系数": 3.0,
        "击中特效偏移x": 0.0,
        "击中特效偏移y": 0.0,
    }
    try:
        取参数 = getattr(布局管理器, "_取游戏区参数_可写", None)
        if callable(取参数):
            原值 = 取参数()
            if isinstance(原值, dict):
                游戏区参数.update(原值)
    except Exception:
        pass

    头像边 = int(max(64, min(180, 屏宽 * 0.06)))
    血条高度 = int(max(int(头像边 * 1.15), 72))
    信息高度 = 22
    顶部y = int(10 + 血条高度 + 6 + 信息高度 + 6)
    判定线y = int(顶部y + max(56, int(屏高 * 0.08)))
    底部y = int(屏高 - 24)

    箭头默认缩放 = 1.2
    箭头基准宽 = int(max(64, min(118, 屏宽 * 0.072)))
    箭头目标宽 = int(max(28, int(箭头基准宽 * 箭头默认缩放)))

    轨道中心间距 = int(max(24, int(箭头目标宽 * 0.88)))
    轨道槽宽 = int(max(箭头目标宽 + 10, int(箭头目标宽 * 1.08)))
    轨道总宽 = int(轨道槽宽 + 4 * 轨道中心间距)
    最大总宽 = int(max(260, 屏宽 - 40))
    if 轨道总宽 > 最大总宽:
        缩放 = 最大总宽 / float(max(1, 轨道总宽))
        轨道槽宽 = int(max(40, int(轨道槽宽 * 缩放)))
        轨道中心间距 = int(max(22, int(轨道中心间距 * 缩放)))
        轨道总宽 = int(轨道槽宽 + 4 * 轨道中心间距)

    轨道起x = int((屏宽 - 轨道总宽) // 2)
    轨道中心列表 = [int(轨道起x + 轨道槽宽 // 2 + i * 轨道中心间距) for i in range(5)]

    游戏缩放 = float(游戏区参数.get("缩放", 1.0) or 1.0)
    y偏移 = float(游戏区参数.get("y偏移", -12.0) or -12.0)
    hold宽度系数 = float(游戏区参数.get("hold宽度系数", 0.96) or 0.96)
    判定区宽度系数 = float(游戏区参数.get("判定区宽度系数", 1.0) or 1.0)
    特效宽度系数 = float(游戏区参数.get("击中特效宽度系数", 3.0) or 3.0)
    特效偏移x = float(游戏区参数.get("击中特效偏移x", 0.0) or 0.0)
    特效偏移y = float(游戏区参数.get("击中特效偏移y", 0.0) or 0.0)
    hold箭头宽 = int(max(16, int(float(箭头目标宽) * 游戏缩放 * hold宽度系数)))

    轨道中心列表_布局 = [float(x) / 比例 for x in 轨道中心列表]
    判定线y_游戏_布局 = float(判定线y + y偏移) / 比例
    底部y_游戏_布局 = float(底部y + y偏移) / 比例
    音符区高度_布局 = float(max(10.0, 底部y_游戏_布局 - 判定线y_游戏_布局))
    音符区中心y_布局 = float(判定线y_游戏_布局 + 音符区高度_布局 * 0.5)

    判定区_receptor宽_布局 = (float(箭头目标宽) * 判定区宽度系数 * 游戏缩放) / 比例
    判定区_receptor宽_布局 = float(max(12.0, 判定区_receptor宽_布局))

    左手x_布局 = float(轨道中心列表_布局[0] - 轨道中心间距 / 比例)
    右手x_布局 = float(轨道中心列表_布局[4] + 轨道中心间距 / 比例)

    判定线y_特效_布局 = float(判定线y + y偏移 + 特效偏移y) / 比例
    特效目标宽_布局 = (float(箭头目标宽) * 特效宽度系数 * 游戏缩放 * 1.25) / 比例
    特效目标宽_布局 = float(max(40.0, 特效目标宽_布局))

    是否显示击中特效 = bool(模拟普通击中特效) or bool(模拟hold击中特效循环)
    播放倍率 = 2.0 if bool(模拟hold击中特效循环) else 1.0
    帧号 = int((float(当前秒) * 60.0 * 播放倍率) % 18.0)
    特效序列 = {
        0: ("image_084", False),
        1: ("image_085", False),
        2: ("image_086", False),
        3: ("image_085", True),
        4: ("image_084", True),
    }

    调试血量显示 = float(max(0.0, min(1.0, 调试血量显示)))
    可见血量HP = int(round(调试血量显示 * 1000.0))
    总血量HP = 0 if 调试血量显示 <= 0.001 else int(min(1200, 200 + 可见血量HP))

    调试隐藏控件ids = set([str(v) for v in list(隐藏控件ids or []) if str(v or "").strip()])
    if bool(模拟双踏板模式):
        调试隐藏控件ids.add("判定区组")
        调试隐藏控件ids.add("特效层组")

    上下文 = {
        "_调试强制显示": bool(强制显示),
        "_调试隐藏控件ids": sorted(list(调试隐藏控件ids)),
        "调试_时间秒": float(当前秒),
        "当前谱面秒": float(当前秒),
        "玩家序号": 1,
        "玩家昵称": str(玩家昵称 or "布局调试"),
        "当前关卡": 1,
        "显示_分数": 123456,
        "倒计时": "01:23",
        "血量最终显示": float(调试血量显示),
        "总血量HP": int(总血量HP),
        "可见血量HP": int(可见血量HP),
        "血条暴走": bool(模拟满血暴走),
        "调试_血条晃荡速度": float(max(0.0, 调试血条晃荡速度)),
        "调试_血条晃荡幅度": float(max(0.0, 调试血条晃荡幅度)),
        "调试_暴走血条速度": float(max(0.0, 调试暴走血条速度)),
        "调试_暴走血条不透明度": float(max(0.0, min(1.0, 调试暴走血条不透明度))),
        "调试_暴走血条羽化": float(max(0.0, min(80.0, 调试暴走血条羽化))),
        "调试_头像框特效速度": float(max(1.0, 调试头像框特效速度)),
        "头像图": 头像图,
        "段位图": 段位图,
        "歌曲名": str(歌曲名 or ""),
        "歌曲星级文本": str(歌曲星级文本 or ""),
        "计数_启用": True,
        "计数_缩放": 1.0,
        "计数_透明": 1.0,
        "计数_combo": 23,
        "计数_判定帧": "text_pf1_perfect.png",
        "模拟_调速倍率": float(max(3.0, min(5.0, 模拟调速倍率))),
        "模拟_隐藏模式": str(模拟隐藏模式 or "关闭"),
        "模拟_轨迹模式": str(模拟轨迹模式 or "摇摆"),
        "模拟_方向模式": str(模拟方向模式 or "关闭"),
        "模拟_大小模式": str(模拟大小模式 or "正常"),
        "模拟_双踏板模式": bool(模拟双踏板模式),
        "模拟_半隐入口比例": float(max(0.1, min(0.95, 半隐入口比例))),
        "模拟_摇摆幅度倍率": float(max(0.2, min(4.0, 摇摆幅度倍率))),
        "模拟_旋转速度度每秒": float(max(30.0, min(1440.0, 旋转速度度每秒))),
        "轨道中心列表_布局": 轨道中心列表_布局,
        "判定线y_游戏_布局": float(判定线y_游戏_布局),
        "底部y_游戏_布局": float(底部y_游戏_布局),
        "音符区高度_布局": float(音符区高度_布局),
        "音符区中心y_布局": float(音符区中心y_布局),
        "轨道中心间距_布局": float(轨道中心间距 / 比例),
        "计数组中心x_布局": float(
            轨道中心列表_布局[2]
            if len(轨道中心列表_布局) >= 3
            else (float(屏宽) * 0.5 / float(比例))
        ),
        "判定区_receptor宽_布局": float(判定区_receptor宽_布局),
        "左手x_布局": float(左手x_布局),
        "右手x_布局": float(右手x_布局),
        "判定线y_特效_布局": float(判定线y_特效_布局),
        "特效目标宽_布局": float(特效目标宽_布局),
        "击中特效偏移x_布局": float(特效偏移x / 比例),
        "调试_hold_轨道中心列表": [int(x) for x in 轨道中心列表],
        "调试_hold_判定线y": int(判定线y + y偏移),
        "调试_hold_底部y": int(底部y + y偏移),
        "调试_hold_箭头宽": int(hold箭头宽),
        "判定区_缩放_0": 1.0,
        "判定区_缩放_1": 1.0,
        "判定区_缩放_2": 1.0,
        "判定区_缩放_3": 1.0,
        "判定区_缩放_4": 1.0,
        "圆环频谱_启用": True,
        "圆环频谱对象": 圆环频谱对象,
        "调试_圆环频谱_启用旋转": bool(圆环频谱启用旋转),
        "调试_圆环频谱_背景板旋转速度": float(圆环频谱背景板转速),
        "调试_圆环频谱_变化落差": float(max(0.0, min(2.0, 圆环频谱变化落差))),
        "调试_圆环频谱_线条数量": int(max(24, min(720, 圆环频谱线条数量))),
        "调试_圆环频谱_线条粗细": int(max(1, min(12, 圆环频谱线条粗细))),
        "调试_圆环频谱_线条间隔": int(max(1, min(8, 圆环频谱线条间隔))),
    }

    for 轨道序号, (前缀, 是否翻转) in 特效序列.items():
        上下文[f"特效帧_{轨道序号}"] = (
            f"{前缀}_{帧号:04d}.png" if 是否显示击中特效 else ""
        )
        上下文[f"特效翻转_{轨道序号}"] = bool(是否翻转) if 是否显示击中特效 else False

    return 上下文


def 主函数():
    项目根 = _取项目根目录()
    if 项目根 and (项目根 not in sys.path):
        sys.path.insert(0, 项目根)

    布局路径 = os.path.join(项目根, "json", "谱面渲染器_布局.json")

    pygame.init()
    pygame.display.set_caption("谱面布局调试")
    屏幕 = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    时钟 = pygame.time.Clock()

    try:
        from ui.调试_谱面渲染器_渲染控件 import 谱面渲染器布局管理器, 调试状态
    except Exception as 异常:
        raise RuntimeError(
            f"导入 ui/调试_谱面渲染器_渲染控件.py 失败：{type(异常).__name__} {异常}"
        )

    try:
        from core.工具 import 获取字体  # type: ignore

        字体 = 获取字体(18, 是否粗体=False)
    except Exception:
        字体 = pygame.font.SysFont("Microsoft YaHei", 18)

    布局管理器 = 谱面渲染器布局管理器(布局路径)
    try:
        计数组定义 = getattr(布局管理器, "_控件索引", {}).get("计数动画组", None)
        if isinstance(计数组定义, dict):
            x定义 = 计数组定义.get("x", None)
            if (not isinstance(x定义, dict)) or (
                str(x定义.get("键") or "") != "计数组中心x_布局"
            ):
                计数组定义["x"] = {"键": "计数组中心x_布局"}
    except Exception:
        pass
    可用箭头皮肤编号 = _收集可用箭头皮肤编号(项目根)
    模拟箭头编号 = "03" if "03" in 可用箭头皮肤编号 else 可用箭头皮肤编号[0]
    皮肤包 = _加载皮肤包(项目根, 模拟箭头编号)
    模拟hold渲染器 = None
    try:
        from ui.谱面渲染器 import 谱面渲染器

        模拟hold渲染器 = 谱面渲染器()
        setattr(模拟hold渲染器, "_皮肤包", 皮肤包)
    except Exception:
        模拟hold渲染器 = None
    调试圆环频谱对象 = None
    try:
        from ui.圆环频谱叠加 import 圆环频谱舞台装饰

        调试圆环频谱对象 = 圆环频谱舞台装饰()
    except Exception:
        调试圆环频谱对象 = None

    头像图, 玩家昵称 = _尝试加载头像与昵称(项目根)
    段位图 = _尝试加载段位图(项目根, 等级=7)
    调试歌曲名 = "一往情深"
    调试歌曲星级文本 = "7★"

    背景路径 = _尝试加载背景图(项目根)
    背景原图: Optional[pygame.Surface] = None
    背景缩放图: Optional[pygame.Surface] = None
    背景缩放尺寸: Tuple[int, int] = (0, 0)
    if 背景路径:
        try:
            背景原图 = pygame.image.load(背景路径).convert()
        except Exception:
            背景原图 = None

    选中控件id = ""
    显示全部边框 = False
    强制显示 = True
    模拟普通击中特效 = False
    模拟hold击中特效循环 = False
    模拟长按击中 = False
    显示血条头预览 = False
    模拟满血暴走 = False
    调试背景蒙板不透明度 = 224.0 / 255.0
    调试血量显示 = 0.5
    调试血条颜色 = (181, 23, 203)
    调试血条亮度 = 1.0
    调试血条不透明度 = 0.5
    调试血条晃荡速度 = 2.7
    调试血条晃荡幅度 = 5.0
    调试暴走血条速度 = 150.0
    调试暴走血条不透明度 = 1.0
    调试暴走血条羽化 = 8.0
    调试头像框特效速度 = 30.0
    圆环频谱最大长度 = 16
    圆环频谱启用旋转 = False
    圆环频谱背景板转速 = 36.0
    圆环频谱变化落差 = 1.0
    圆环频谱线条数量 = 200
    圆环频谱线条粗细 = 2
    圆环频谱线条间隔 = 1
    模拟谱面循环播放 = True
    模拟谱面命中状态 = True
    模拟谱面调速倍率 = 4.0
    模拟谱面隐藏模式 = "关闭"
    模拟谱面轨迹模式 = "摇摆"
    模拟谱面方向模式 = "关闭"
    模拟谱面大小模式 = "正常"
    模拟双踏板模式 = False
    模拟双踏板左X偏移 = 0.0
    模拟双踏板右X偏移 = 0.0
    模拟双踏板左Y偏移 = 0.0
    模拟双踏板右Y偏移 = 0.0
    模拟半隐入口比例 = 0.50
    模拟摇摆幅度倍率 = 1.00
    模拟旋转速度度每秒 = 450.0
    左侧面板折叠 = False
    右侧面板折叠 = False
    模拟面板折叠 = False
    调试颜色输入文本 = (
        f"#{调试血条颜色[0]:02X}{调试血条颜色[1]:02X}{调试血条颜色[2]:02X}"
    )
    调试颜色输入激活 = False
    调试设置路径 = os.path.join(项目根, "json", "谱面布局调试器_设置.json")
    try:
        if 调试圆环频谱对象 is not None and hasattr(
            调试圆环频谱对象, "设置调试外延最大长度"
        ):
            调试圆环频谱对象.设置调试外延最大长度(圆环频谱最大长度)
        if 调试圆环频谱对象 is not None and hasattr(
            调试圆环频谱对象, "设置调试频谱参数"
        ):
            调试圆环频谱对象.设置调试频谱参数(
                启用旋转=bool(圆环频谱启用旋转),
                变化落差=float(圆环频谱变化落差),
                线条数量=int(圆环频谱线条数量),
                线条粗细=int(圆环频谱线条粗细),
                线条间隔=int(圆环频谱线条间隔),
            )
    except Exception:
        pass
    隐藏控件ids: set[str] = set()
    图层面板滚动 = 0
    显示图层面板 = True
    撤销栈: List[Dict[str, Any]] = []
    选中调试项id = ""
    模拟箭头原图缓存: Dict[Tuple[str, int], Optional[pygame.Surface]] = {}
    模拟箭头缩放缓存: Dict[Tuple[str, int, int], Optional[pygame.Surface]] = {}

    拖拽中 = False
    拖拽已记录撤销 = False
    上次鼠标 = (0, 0)
    文本字间距面板开启 = True
    文本字间距目标控件id = ""
    文本字间距面板锚点 = (0, 0)

    def _同步调试颜色文本():
        nonlocal 调试颜色输入文本
        调试颜色输入文本 = f"#{int(调试血条颜色[0]):02X}{int(调试血条颜色[1]):02X}{int(调试血条颜色[2]):02X}"

    def _取文本控件字间距(控件id: str) -> int:
        控件 = getattr(布局管理器, "_控件索引", {}).get(str(控件id or ""))
        if not isinstance(控件, dict):
            return 0
        if str(控件.get("类型") or "") != "文本":
            return 0
        try:
            return int(_取数(控件.get("字间距"), 0))
        except Exception:
            return 0

    def _是否文本控件(控件id: str) -> bool:
        控件 = getattr(布局管理器, "_控件索引", {}).get(str(控件id or ""))
        return isinstance(控件, dict) and str(控件.get("类型") or "") == "文本"

    def _按点命中文本控件(
        屏幕点: Tuple[int, int],
        上下文: Dict[str, Any],
        关联控件id: str = "",
    ) -> str:
        try:
            构建清单 = getattr(布局管理器, "_构建渲染清单", None)
            if not callable(构建清单):
                return ""
            渲染表 = 构建清单(屏幕.get_size(), 上下文, 仅绘制根id=None)
        except Exception:
            return ""

        if not isinstance(渲染表, list):
            return ""

        点x, 点y = int(屏幕点[0]), int(屏幕点[1])
        try:
            渲染表.sort(key=lambda 项: int(_取数((项 or {}).get("z"), 0)))
        except Exception:
            pass

        for 项 in reversed(渲染表):
            if not isinstance(项, dict):
                continue
            矩形 = 项.get("rect")
            if (not isinstance(矩形, pygame.Rect)) or (not 矩形.collidepoint(点x, 点y)):
                continue
            控件定义 = 项.get("def")
            if not isinstance(控件定义, dict):
                continue
            if str(控件定义.get("类型") or "") == "文本":
                return str(项.get("id") or "")

        # 变量文本（例如“{倒计时}”）在复杂层级下可能先命中到兄弟布局。
        # 这里按“关联控件 -> 同组文本”再兜底一次。
        关联控件id = str(关联控件id or "").strip()
        if not 关联控件id:
            return ""

        try:
            子索引 = getattr(布局管理器, "_子列表索引", {}) or {}
        except Exception:
            子索引 = {}
        if not isinstance(子索引, dict):
            子索引 = {}

        父映射: Dict[str, str] = {}
        for 父id, 子列表 in 子索引.items():
            if not isinstance(子列表, list):
                continue
            for 子id in 子列表:
                try:
                    父映射[str(子id)] = str(父id)
                except Exception:
                    continue

        关联父id = str(父映射.get(关联控件id, "") or "")
        if not 关联父id:
            return ""

        目标文本id列表: List[str] = []
        for 子id in list(子索引.get(关联父id, []) or []):
            子id = str(子id or "")
            if not 子id:
                continue
            if _是否文本控件(子id):
                目标文本id列表.append(子id)
        if not 目标文本id列表:
            return ""

        文本项列表: List[Dict[str, Any]] = []
        for 项 in 渲染表:
            if not isinstance(项, dict):
                continue
            if str(项.get("id") or "") in 目标文本id列表:
                文本项列表.append(项)
        if not 文本项列表:
            return ""

        for 项 in reversed(文本项列表):
            矩形 = 项.get("rect")
            if isinstance(矩形, pygame.Rect) and 矩形.collidepoint(点x, 点y):
                return str(项.get("id") or "")

        # 没点中具体文本时，返回同组第一个文本（便于直接调变量文本字间距）
        try:
            文本项列表.sort(key=lambda it: int(_取数((it or {}).get("z"), 0)), reverse=True)
        except Exception:
            pass
        return str((文本项列表[0] or {}).get("id") or "")

    def _打开文本字间距面板(控件id: str, 锚点: Tuple[int, int]):
        nonlocal 文本字间距面板开启, 文本字间距目标控件id, 文本字间距面板锚点
        if not _是否文本控件(控件id):
            return
        文本字间距目标控件id = str(控件id)
        文本字间距面板锚点 = (int(锚点[0]), int(锚点[1]))
        文本字间距面板开启 = True

    def _关闭文本字间距面板():
        nonlocal 文本字间距面板开启, 文本字间距目标控件id
        文本字间距面板开启 = True
        文本字间距目标控件id = ""

    def _计算文本字间距面板布局():
        if not bool(文本字间距面板开启):
            return None, None, None, None
        面板宽 = 360
        面板高 = 96
        屏宽, 屏高 = 屏幕.get_size()
        x = int(max(12, (屏宽 - 面板宽) // 2))
        y = int(max(12, 屏高 - 面板高 - 12))
        面板 = pygame.Rect(x, y, 面板宽, 面板高)
        减 = pygame.Rect(int(x + 16), int(y + 44), 44, 30)
        加 = pygame.Rect(int(x + 面板宽 - 60), int(y + 44), 44, 30)
        关 = pygame.Rect(int(x + 面板宽 - 28), int(y + 8), 20, 20)
        return 面板, 减, 加, 关

    def _绘制文本字间距面板():
        if not bool(文本字间距面板开启):
            return
        面板, 减, 加, 关 = _计算文本字间距面板布局()
        if 面板 is None:
            return
        try:
            底 = pygame.Surface((面板.w, 面板.h), pygame.SRCALPHA)
            底.fill((12, 18, 30, 220))
            屏幕.blit(底, 面板.topleft)
            pygame.draw.rect(屏幕, (145, 175, 235), 面板, 1, border_radius=6)
            pygame.draw.rect(屏幕, (100, 130, 180), 减, 1, border_radius=4)
            pygame.draw.rect(屏幕, (100, 130, 180), 加, 1, border_radius=4)
            pygame.draw.rect(屏幕, (165, 115, 115), 关, 1, border_radius=3)

            标题 = 字体.render("文本控制面板（单击文本选区）", True, (235, 240, 250))
            当前值 = _取文本控件字间距(文本字间距目标控件id)
            目标文本 = (
                f"目标: {str(文本字间距目标控件id)}"
                if _是否文本控件(文本字间距目标控件id)
                else "目标: 未选中文本"
            )
            目标图 = 字体.render(目标文本, True, (188, 208, 236))
            值图 = 字体.render(f"{当前值:+d}px", True, (255, 216, 90))
            减图 = 字体.render("-", True, (235, 240, 250))
            加图 = 字体.render("+", True, (235, 240, 250))
            关图 = 字体.render("x", True, (235, 180, 180))
            屏幕.blit(标题, (int(面板.x + 12), int(面板.y + 10)))
            屏幕.blit(目标图, (int(面板.x + 12), int(面板.y + 30)))
            屏幕.blit(值图, (int(面板.centerx - 值图.get_width() // 2), int(面板.y + 49)))
            屏幕.blit(减图, (int(减.centerx - 减图.get_width() // 2), int(减.centery - 减图.get_height() // 2)))
            屏幕.blit(加图, (int(加.centerx - 加图.get_width() // 2), int(加.centery - 加图.get_height() // 2)))
            屏幕.blit(关图, (int(关.centerx - 关图.get_width() // 2), int(关.centery - 关图.get_height() // 2)))
        except Exception:
            pass

    def _尝试应用颜色文本() -> bool:
        nonlocal 调试血条颜色
        文本 = str(调试颜色输入文本 or "").strip().upper()
        if 文本.startswith("#"):
            文本 = 文本[1:]
        if len(文本) != 6:
            return False
        if any(ch not in "0123456789ABCDEF" for ch in 文本):
            return False
        try:
            调试血条颜色 = (
                int(文本[0:2], 16),
                int(文本[2:4], 16),
                int(文本[4:6], 16),
            )
            return True
        except Exception:
            return False

    def _收集调试设置() -> Dict[str, Any]:
        return {
            "强制显示": bool(强制显示),
            "显示全部边框": bool(显示全部边框),
            "模拟普通击中特效": bool(模拟普通击中特效),
            "模拟hold击中特效循环": bool(模拟hold击中特效循环),
            "模拟长按击中": bool(模拟长按击中),
            "模拟满血暴走": bool(模拟满血暴走),
            "调试背景蒙板不透明度": float(调试背景蒙板不透明度),
            "调试血量显示": float(调试血量显示),
            "调试血条晃荡速度": float(调试血条晃荡速度),
            "调试血条晃荡幅度": float(调试血条晃荡幅度),
            "调试暴走血条速度": float(调试暴走血条速度),
            "调试暴走血条不透明度": float(调试暴走血条不透明度),
            "调试暴走血条羽化": float(调试暴走血条羽化),
            "调试头像框特效速度": float(调试头像框特效速度),
            "圆环频谱最大长度": int(圆环频谱最大长度),
            "圆环频谱启用旋转": bool(圆环频谱启用旋转),
            "圆环频谱背景板转速": float(圆环频谱背景板转速),
            "圆环频谱变化落差": float(圆环频谱变化落差),
            "圆环频谱线条数量": int(圆环频谱线条数量),
            "圆环频谱线条粗细": int(圆环频谱线条粗细),
            "圆环频谱线条间隔": int(圆环频谱线条间隔),
            "模拟谱面循环播放": bool(模拟谱面循环播放),
            "模拟谱面命中状态": bool(模拟谱面命中状态),
            "模拟谱面调速倍率": float(模拟谱面调速倍率),
            "模拟谱面隐藏模式": str(模拟谱面隐藏模式),
            "模拟谱面轨迹模式": str(模拟谱面轨迹模式),
            "模拟谱面方向模式": str(模拟谱面方向模式),
            "模拟谱面大小模式": str(模拟谱面大小模式),
            "模拟双踏板模式": bool(模拟双踏板模式),
            "调试双踏板左X偏移": float(模拟双踏板左X偏移),
            "调试双踏板右X偏移": float(模拟双踏板右X偏移),
            "调试双踏板左Y偏移": float(模拟双踏板左Y偏移),
            "调试双踏板右Y偏移": float(模拟双踏板右Y偏移),
            "模拟半隐入口比例": float(模拟半隐入口比例),
            "模拟摇摆幅度倍率": float(模拟摇摆幅度倍率),
            "模拟旋转速度度每秒": float(模拟旋转速度度每秒),
            "模拟箭头编号": str(模拟箭头编号),
            "左侧面板折叠": bool(左侧面板折叠),
            "右侧面板折叠": bool(右侧面板折叠),
            "模拟面板折叠": bool(模拟面板折叠),
        }

    def _保存调试设置():
        try:
            os.makedirs(os.path.dirname(调试设置路径), exist_ok=True)
            with open(调试设置路径, "w", encoding="utf-8") as f:
                json.dump(_收集调试设置(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _加载调试设置():
        nonlocal 强制显示, 显示全部边框, 显示图层面板
        nonlocal 模拟普通击中特效, 模拟hold击中特效循环, 模拟长按击中, 模拟满血暴走
        nonlocal 调试背景蒙板不透明度
        nonlocal 调试血量显示, 调试血条颜色, 调试血条亮度, 调试血条不透明度
        nonlocal 调试血条晃荡速度, 调试血条晃荡幅度, 调试暴走血条速度
        nonlocal 调试暴走血条不透明度, 调试暴走血条羽化
        nonlocal 调试头像框特效速度, 圆环频谱最大长度
        nonlocal 圆环频谱启用旋转, 圆环频谱背景板转速, 圆环频谱变化落差
        nonlocal 圆环频谱线条数量, 圆环频谱线条粗细, 圆环频谱线条间隔
        nonlocal 模拟谱面循环播放, 模拟谱面命中状态, 模拟谱面调速倍率
        nonlocal 模拟谱面隐藏模式, 模拟谱面轨迹模式, 模拟谱面方向模式, 模拟谱面大小模式
        nonlocal 模拟双踏板模式, 模拟双踏板左X偏移, 模拟双踏板右X偏移
        nonlocal 模拟双踏板左Y偏移, 模拟双踏板右Y偏移
        nonlocal 模拟半隐入口比例, 模拟摇摆幅度倍率, 模拟旋转速度度每秒
        nonlocal 模拟箭头编号, 左侧面板折叠, 右侧面板折叠, 模拟面板折叠
        数据 = _安全读json(调试设置路径)
        if not isinstance(数据, dict):
            return
        try:
            强制显示 = bool(数据.get("强制显示", 强制显示))
            显示全部边框 = bool(数据.get("显示全部边框", 显示全部边框))
            显示图层面板 = True
            模拟普通击中特效 = bool(数据.get("模拟普通击中特效", 模拟普通击中特效))
            模拟hold击中特效循环 = bool(
                数据.get("模拟hold击中特效循环", 模拟hold击中特效循环)
            )
            模拟长按击中 = bool(数据.get("模拟长按击中", 模拟长按击中))
            模拟满血暴走 = bool(数据.get("模拟满血暴走", 模拟满血暴走))
            模拟谱面循环播放 = bool(数据.get("模拟谱面循环播放", 模拟谱面循环播放))
            模拟谱面命中状态 = bool(数据.get("模拟谱面命中状态", 模拟谱面命中状态))
            模拟谱面调速倍率 = float(
                max(3.0, min(5.0, 数据.get("模拟谱面调速倍率", 模拟谱面调速倍率)))
            )
            模拟谱面隐藏模式 = str(
                数据.get("模拟谱面隐藏模式", 模拟谱面隐藏模式) or "关闭"
            ).strip() or "关闭"
            模拟谱面轨迹模式 = str(
                数据.get("模拟谱面轨迹模式", 模拟谱面轨迹模式) or "摇摆"
            ).strip() or "摇摆"
            模拟谱面方向模式 = str(
                数据.get("模拟谱面方向模式", 模拟谱面方向模式) or "关闭"
            ).strip() or "关闭"
            模拟谱面大小模式 = str(
                数据.get("模拟谱面大小模式", 模拟谱面大小模式) or "正常"
            ).strip() or "正常"
            模拟双踏板模式 = bool(数据.get("模拟双踏板模式", 模拟双踏板模式))
            模拟双踏板左X偏移 = float(
                max(-600.0, min(600.0, 数据.get("调试双踏板左X偏移", 模拟双踏板左X偏移)))
            )
            模拟双踏板右X偏移 = float(
                max(-600.0, min(600.0, 数据.get("调试双踏板右X偏移", 模拟双踏板右X偏移)))
            )
            模拟双踏板左Y偏移 = float(
                max(-260.0, min(260.0, 数据.get("调试双踏板左Y偏移", 模拟双踏板左Y偏移)))
            )
            模拟双踏板右Y偏移 = float(
                max(-260.0, min(260.0, 数据.get("调试双踏板右Y偏移", 模拟双踏板右Y偏移)))
            )
            模拟半隐入口比例 = float(
                max(0.1, min(0.95, 数据.get("模拟半隐入口比例", 模拟半隐入口比例)))
            )
            模拟摇摆幅度倍率 = float(
                max(0.2, min(4.0, 数据.get("模拟摇摆幅度倍率", 模拟摇摆幅度倍率)))
            )
            模拟旋转速度度每秒 = float(
                max(
                    30.0,
                    min(
                        1440.0,
                        数据.get("模拟旋转速度度每秒", 模拟旋转速度度每秒),
                    ),
                )
            )
            读取箭头编号 = str(数据.get("模拟箭头编号", 模拟箭头编号) or "").strip()
            if 读取箭头编号 in 可用箭头皮肤编号:
                模拟箭头编号 = 读取箭头编号
            左侧面板折叠 = bool(数据.get("左侧面板折叠", 左侧面板折叠))
            右侧面板折叠 = bool(数据.get("右侧面板折叠", 右侧面板折叠))
            模拟面板折叠 = bool(数据.get("模拟面板折叠", 模拟面板折叠))
            调试背景蒙板不透明度 = float(
                max(
                    0.0,
                    min(1.0, 数据.get("调试背景蒙板不透明度", 调试背景蒙板不透明度)),
                )
            )
            调试血量显示 = float(
                max(0.0, min(1.0, 数据.get("调试血量显示", 调试血量显示)))
            )
            颜色 = 数据.get("调试血条颜色", 调试血条颜色)
            if isinstance(颜色, (list, tuple)) and len(颜色) >= 3:
                调试血条颜色 = (
                    int(max(0, min(255, 颜色[0]))),
                    int(max(0, min(255, 颜色[1]))),
                    int(max(0, min(255, 颜色[2]))),
                )
            调试血条晃荡速度 = float(
                max(0.0, min(12.0, 数据.get("调试血条晃荡速度", 调试血条晃荡速度)))
            )
            调试血条晃荡幅度 = float(
                max(0.0, min(40.0, 数据.get("调试血条晃荡幅度", 调试血条晃荡幅度)))
            )
            调试暴走血条速度 = float(
                max(0.0, min(600.0, 数据.get("调试暴走血条速度", 调试暴走血条速度)))
            )
            调试暴走血条不透明度 = float(
                max(
                    0.0,
                    min(1.0, 数据.get("调试暴走血条不透明度", 调试暴走血条不透明度)),
                )
            )
            调试暴走血条羽化 = float(
                max(0.0, min(80.0, 数据.get("调试暴走血条羽化", 调试暴走血条羽化)))
            )
            调试头像框特效速度 = float(
                max(1.0, min(120.0, 数据.get("调试头像框特效速度", 调试头像框特效速度)))
            )
            圆环频谱最大长度 = int(
                max(6, min(96, 数据.get("圆环频谱最大长度", 圆环频谱最大长度)))
            )
            圆环频谱启用旋转 = bool(数据.get("圆环频谱启用旋转", 圆环频谱启用旋转))
            圆环频谱背景板转速 = float(
                max(
                    -360.0,
                    min(360.0, 数据.get("圆环频谱背景板转速", 圆环频谱背景板转速)),
                )
            )
            圆环频谱变化落差 = float(
                max(
                    0.0,
                    min(2.0, 数据.get("圆环频谱变化落差", 圆环频谱变化落差)),
                )
            )
            圆环频谱线条数量 = int(
                max(
                    24,
                    min(720, 数据.get("圆环频谱线条数量", 圆环频谱线条数量)),
                )
            )
            圆环频谱线条粗细 = int(
                max(1, min(12, 数据.get("圆环频谱线条粗细", 圆环频谱线条粗细)))
            )
            圆环频谱线条间隔 = int(
                max(1, min(8, 数据.get("圆环频谱线条间隔", 圆环频谱线条间隔)))
            )
        except Exception:
            pass

        try:
            if str(模拟箭头编号 or "") not in 可用箭头皮肤编号:
                模拟箭头编号 = "03" if "03" in 可用箭头皮肤编号 else 可用箭头皮肤编号[0]
        except Exception:
            模拟箭头编号 = "03"
        _同步调试颜色文本()
        try:
            if 调试圆环频谱对象 is not None and hasattr(
                调试圆环频谱对象, "设置调试外延最大长度"
            ):
                调试圆环频谱对象.设置调试外延最大长度(圆环频谱最大长度)
            if 调试圆环频谱对象 is not None and hasattr(
                调试圆环频谱对象, "设置调试频谱参数"
            ):
                调试圆环频谱对象.设置调试频谱参数(
                    启用旋转=bool(圆环频谱启用旋转),
                    变化落差=float(圆环频谱变化落差),
                    线条数量=int(圆环频谱线条数量),
                    线条粗细=int(圆环频谱线条粗细),
                    线条间隔=int(圆环频谱线条间隔),
                )
        except Exception:
            pass

    _加载调试设置()
    try:
        皮肤包 = _加载皮肤包(项目根, 模拟箭头编号)
        if 模拟hold渲染器 is not None:
            setattr(模拟hold渲染器, "_皮肤包", 皮肤包)
    except Exception:
        pass

    def _记录撤销():
        nonlocal 撤销栈
        try:
            快照 = 布局管理器.导出快照()
        except Exception:
            快照 = None
        if not isinstance(快照, dict):
            return
        撤销栈.append(快照)
        if len(撤销栈) > 80:
            撤销栈 = 撤销栈[-80:]

    def _撤销一步():
        nonlocal 选中控件id, 拖拽中, 拖拽已记录撤销
        if not 撤销栈:
            return
        try:
            快照 = 撤销栈.pop()
            布局管理器.导入快照(快照)
        except Exception:
            return
        if 选中控件id and (not 布局管理器.是否存在控件(选中控件id)):
            选中控件id = ""
        拖拽中 = False
        拖拽已记录撤销 = False

    def _切换控件可见(控件id: str):
        nonlocal 选中控件id, 拖拽中, 拖拽已记录撤销
        控件id = str(控件id or "")
        if not 控件id:
            return
        if 控件id in 隐藏控件ids:
            隐藏控件ids.remove(控件id)
        else:
            隐藏控件ids.add(控件id)
            if str(选中控件id or "") == 控件id:
                选中控件id = ""
                拖拽中 = False
                拖拽已记录撤销 = False

    def _取开关项():
        return [
            ("force_show", "强制显示", bool(强制显示)),
            ("show_all_borders", "显示全部边框", bool(显示全部边框)),
            ("full_blood_fx", "满血暴走血条", bool(模拟满血暴走)),
            ("normal_hit_fx", "普通击中特效", bool(模拟普通击中特效)),
            ("hold_loop", "Hold特效循环", bool(模拟hold击中特效循环)),
            ("simulate_hold_hit", "模拟长按击中", bool(模拟长按击中)),
        ]

    模拟调速候选 = [3.0, 3.5, 4.0, 4.5, 5.0]
    模拟隐藏候选 = ["关闭", "半隐", "全隐"]
    模拟轨迹候选 = ["摇摆", "旋转"]
    模拟方向候选 = ["关闭", "反向"]
    模拟大小候选 = ["正常", "放大"]

    def _循环枚举值(候选: List[Any], 当前值: Any, 方向增量: int) -> Any:
        if not 候选:
            return 当前值
        try:
            当前索引 = 候选.index(当前值)
        except Exception:
            当前索引 = 0
        新索引 = (int(当前索引) + int(方向增量)) % len(候选)
        return 候选[新索引]

    def _切换模拟箭头编号(方向增量: int):
        nonlocal 模拟箭头编号, 皮肤包, 模拟hold渲染器
        if not 可用箭头皮肤编号:
            return
        try:
            当前索引 = 可用箭头皮肤编号.index(str(模拟箭头编号))
        except Exception:
            当前索引 = 0
        新索引 = (int(当前索引) + int(方向增量)) % len(可用箭头皮肤编号)
        模拟箭头编号 = str(可用箭头皮肤编号[新索引])
        模拟箭头原图缓存.clear()
        模拟箭头缩放缓存.clear()
        try:
            皮肤包 = _加载皮肤包(项目根, 模拟箭头编号)
            if 模拟hold渲染器 is not None:
                setattr(模拟hold渲染器, "_皮肤包", 皮肤包)
        except Exception:
            pass

    def _取模拟箭头原图(轨道序号: int) -> Optional[pygame.Surface]:
        缓存键 = (str(模拟箭头编号), int(轨道序号))
        if 缓存键 in 模拟箭头原图缓存:
            return 模拟箭头原图缓存[缓存键]

        轨道序号 = int(max(0, min(4, int(轨道序号))))
        方向名 = ["DownLeft", "UpLeft", "Center", "UpRight", "DownRight"][轨道序号]
        新方位名 = ["lb", "lt", "cc", "rt", "rb"][轨道序号]
        候选帧名 = [
            f"arrow_body_{新方位名}.png",
            f"arrow_mask_{新方位名}.png",
            f"{方向名} Tap Note 3x2.png",
            f"{方向名} Tap Note (doubleres) 3x2.png",
            f"{方向名} Tap Note (doubleres) 1x1.png",
        ]

        图: Optional[pygame.Surface] = None
        try:
            图集 = getattr(皮肤包, "arrow", None)
            if 图集 is not None and hasattr(图集, "取"):
                for 帧名 in 候选帧名:
                    图 = getattr(图集, "取")(帧名)
                    if isinstance(图, pygame.Surface):
                        break
        except Exception:
            图 = None

        if 图 is None:
            key帧名 = ["key_bl.png", "key_tl.png", "key_cc.png", "key_tr.png", "key_br.png"][
                轨道序号
            ]
            try:
                图集2 = getattr(皮肤包, "key", None)
                if 图集2 is not None and hasattr(图集2, "取"):
                    图 = getattr(图集2, "取")(key帧名)
            except Exception:
                图 = None

        模拟箭头原图缓存[缓存键] = 图 if isinstance(图, pygame.Surface) else None
        return 模拟箭头原图缓存[缓存键]

    def _取模拟箭头图(轨道序号: int, 目标宽: int) -> Optional[pygame.Surface]:
        目标宽 = int(max(16, 目标宽))
        缓存键 = (str(模拟箭头编号), int(轨道序号), int(目标宽))
        if 缓存键 in 模拟箭头缩放缓存:
            return 模拟箭头缩放缓存[缓存键]

        原图 = _取模拟箭头原图(轨道序号)
        if 原图 is None:
            模拟箭头缩放缓存[缓存键] = None
            return None

        try:
            ow = int(max(1, 原图.get_width()))
            oh = int(max(1, 原图.get_height()))
            nh = int(max(12, round(目标宽 * (float(oh) / float(ow)))))
            图2 = pygame.transform.smoothscale(原图, (int(目标宽), int(nh))).convert_alpha()
            模拟箭头缩放缓存[缓存键] = 图2
        except Exception:
            模拟箭头缩放缓存[缓存键] = None
        return 模拟箭头缩放缓存[缓存键]

    def _取模拟项列表() -> List[Tuple[str, str]]:
        return [
            ("模拟_循环播放", f"循环播放: {'是' if 模拟谱面循环播放 else '否'}"),
            ("模拟_命中状态", f"命中状态: {'是' if 模拟谱面命中状态 else '否'}"),
            ("模拟_调速", f"调速: X{模拟谱面调速倍率:.1f}"),
            ("模拟_隐藏", f"隐藏: {模拟谱面隐藏模式}"),
            ("模拟_轨迹", f"轨迹: {模拟谱面轨迹模式}"),
            ("模拟_方向", f"方向: {模拟谱面方向模式}"),
            ("模拟_大小", f"大小: {模拟谱面大小模式}"),
            ("模拟_双踏板", f"双踏板模式: {'开' if 模拟双踏板模式 else '关'}"),
            ("模拟_双踏板左X", f"双踏板左X偏移: {模拟双踏板左X偏移:+.0f}px"),
            ("模拟_双踏板右X", f"双踏板右X偏移: {模拟双踏板右X偏移:+.0f}px"),
            ("模拟_双踏板左Y", f"双踏板左Y偏移: {模拟双踏板左Y偏移:+.0f}px"),
            ("模拟_双踏板右Y", f"双踏板右Y偏移: {模拟双踏板右Y偏移:+.0f}px"),
            ("模拟_箭头", f"箭头: {模拟箭头编号}"),
            ("模拟_半隐入口", f"半隐入口: {int(round(模拟半隐入口比例 * 100.0))}%屏高"),
            ("模拟_摇摆幅度", f"摇摆幅度: {模拟摇摆幅度倍率:.2f}x"),
            ("模拟_旋转速度", f"旋转速度: {模拟旋转速度度每秒:.0f}°/s"),
        ]

    def _调整模拟项(调试项id: str, 增量: int, 大步进: bool) -> bool:
        nonlocal 模拟谱面循环播放, 模拟谱面命中状态
        nonlocal 模拟谱面调速倍率, 模拟谱面隐藏模式, 模拟谱面轨迹模式
        nonlocal 模拟谱面方向模式, 模拟谱面大小模式
        nonlocal 模拟双踏板模式, 模拟双踏板左X偏移, 模拟双踏板右X偏移
        nonlocal 模拟双踏板左Y偏移, 模拟双踏板右Y偏移
        nonlocal 模拟半隐入口比例, 模拟摇摆幅度倍率, 模拟旋转速度度每秒

        sid = str(调试项id or "")
        if sid == "模拟_循环播放":
            模拟谱面循环播放 = not bool(模拟谱面循环播放)
            return True
        if sid == "模拟_命中状态":
            模拟谱面命中状态 = not bool(模拟谱面命中状态)
            return True
        if sid == "模拟_调速":
            模拟谱面调速倍率 = float(
                _循环枚举值(模拟调速候选, float(模拟谱面调速倍率), int(增量))
            )
            return True
        if sid == "模拟_隐藏":
            模拟谱面隐藏模式 = str(
                _循环枚举值(模拟隐藏候选, str(模拟谱面隐藏模式), int(增量))
            )
            return True
        if sid == "模拟_轨迹":
            模拟谱面轨迹模式 = str(
                _循环枚举值(模拟轨迹候选, str(模拟谱面轨迹模式), int(增量))
            )
            return True
        if sid == "模拟_方向":
            模拟谱面方向模式 = str(
                _循环枚举值(模拟方向候选, str(模拟谱面方向模式), int(增量))
            )
            return True
        if sid == "模拟_大小":
            模拟谱面大小模式 = str(
                _循环枚举值(模拟大小候选, str(模拟谱面大小模式), int(增量))
            )
            return True
        if sid == "模拟_双踏板":
            模拟双踏板模式 = not bool(模拟双踏板模式)
            return True
        if sid == "模拟_双踏板左X":
            步进 = 20.0 if 大步进 else 5.0
            模拟双踏板左X偏移 = float(
                max(-600.0, min(600.0, 模拟双踏板左X偏移 + float(增量) * 步进))
            )
            return True
        if sid == "模拟_双踏板右X":
            步进 = 20.0 if 大步进 else 5.0
            模拟双踏板右X偏移 = float(
                max(-600.0, min(600.0, 模拟双踏板右X偏移 + float(增量) * 步进))
            )
            return True
        if sid == "模拟_双踏板左Y":
            步进 = 10.0 if 大步进 else 2.0
            模拟双踏板左Y偏移 = float(
                max(-260.0, min(260.0, 模拟双踏板左Y偏移 + float(增量) * 步进))
            )
            return True
        if sid == "模拟_双踏板右Y":
            步进 = 10.0 if 大步进 else 2.0
            模拟双踏板右Y偏移 = float(
                max(-260.0, min(260.0, 模拟双踏板右Y偏移 + float(增量) * 步进))
            )
            return True
        if sid == "模拟_箭头":
            _切换模拟箭头编号(int(增量))
            return True
        if sid == "模拟_半隐入口":
            步进 = 0.10 if 大步进 else 0.02
            模拟半隐入口比例 = float(
                max(0.1, min(0.95, 模拟半隐入口比例 + float(增量) * 步进))
            )
            return True
        if sid == "模拟_摇摆幅度":
            步进 = 0.20 if 大步进 else 0.05
            模拟摇摆幅度倍率 = float(
                max(0.2, min(4.0, 模拟摇摆幅度倍率 + float(增量) * 步进))
            )
            return True
        if sid == "模拟_旋转速度":
            步进 = 120.0 if 大步进 else 30.0
            模拟旋转速度度每秒 = float(
                max(30.0, min(1440.0, 模拟旋转速度度每秒 + float(增量) * 步进))
            )
            return True
        return False

    def _计算模拟面板布局() -> Tuple[pygame.Rect, pygame.Rect, pygame.Rect, Dict[str, pygame.Rect]]:
        屏宽, 屏高 = 屏幕.get_size()
        面板边距 = 12
        面板宽 = int(max(330, min(420, 屏宽 * 0.31)))
        行高 = 30
        标题高 = 36
        项列表 = _取模拟项列表()
        面板高 = int(标题高 + 10 + len(项列表) * 行高 + 14)
        面板rect = pygame.Rect(int(面板边距), int(面板边距), int(面板宽), int(面板高))

        顶部横杠rect = pygame.Rect(
            int(面板rect.centerx - 22),
            int(面板rect.y + 6),
            44,
            10,
        )
        尾巴rect = pygame.Rect(
            int(面板rect.x),
            int(面板rect.y + 2),
            28,
            86,
        )

        行rect表: Dict[str, pygame.Rect] = {}
        当前y = int(面板rect.y + 标题高)
        for 项id, _ in 项列表:
            行rect表[str(项id)] = pygame.Rect(
                int(面板rect.x + 10),
                int(当前y),
                int(面板rect.w - 20),
                int(行高 - 3),
            )
            当前y += 行高
        return 面板rect, 顶部横杠rect, 尾巴rect, 行rect表

    def _绘制模拟面板():
        面板rect, 顶部横杠rect, 尾巴rect, 行rect表 = _计算模拟面板布局()
        if bool(模拟面板折叠):
            try:
                底 = pygame.Surface((尾巴rect.w, 尾巴rect.h), pygame.SRCALPHA)
                底.fill((0, 0, 0, 145))
                屏幕.blit(底, 尾巴rect.topleft)
                pygame.draw.rect(屏幕, (215, 225, 255), 尾巴rect, width=1, border_radius=8)
                pygame.draw.line(
                    屏幕,
                    (255, 245, 170),
                    (int(尾巴rect.x + 6), int(尾巴rect.y + 14)),
                    (int(尾巴rect.right - 6), int(尾巴rect.y + 14)),
                    width=2,
                )
                文图 = 字体.render("模拟", True, (235, 235, 245))
                屏幕.blit(文图, (int(尾巴rect.x + 3), int(尾巴rect.y + 28)))
            except Exception:
                pass
            return

        try:
            面板底 = pygame.Surface((面板rect.w, 面板rect.h), pygame.SRCALPHA)
            面板底.fill((0, 0, 0, 160))
            屏幕.blit(面板底, 面板rect.topleft)
            pygame.draw.rect(屏幕, (215, 225, 255), 面板rect, width=1, border_radius=10)
            pygame.draw.line(
                屏幕,
                (255, 245, 170),
                (int(顶部横杠rect.x + 2), int(顶部横杠rect.centery)),
                (int(顶部横杠rect.right - 2), int(顶部横杠rect.centery)),
                width=2,
            )
            标题图 = 字体.render("谱面设置功能模拟", True, (255, 245, 170))
            屏幕.blit(标题图, (int(面板rect.x + 12), int(面板rect.y + 12)))
        except Exception:
            pass

        for 项id, 文本 in _取模拟项列表():
            rect = 行rect表.get(str(项id))
            if rect is None:
                continue
            try:
                if str(选中调试项id or "") == str(项id):
                    选中底 = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    选中底.fill((78, 110, 150, 110))
                    屏幕.blit(选中底, rect.topleft)
                pygame.draw.rect(屏幕, (88, 100, 122), rect, width=1, border_radius=6)
                图 = 字体.render(str(文本), True, (236, 238, 245))
                屏幕.blit(图, (int(rect.x + 8), int(rect.y + (rect.h - 图.get_height()) // 2)))
            except Exception:
                pass

            if str(项id) == "模拟_箭头":
                try:
                    缩略图 = _取模拟箭头图(2, 30)
                    if isinstance(缩略图, pygame.Surface):
                        x = int(rect.right - 缩略图.get_width() - 8)
                        y = int(rect.y + (rect.h - 缩略图.get_height()) // 2)
                        屏幕.blit(缩略图, (x, y))
                except Exception:
                    pass

    def _注入模拟命中特效(上下文: Dict[str, Any], 当前秒: float):
        if (not bool(模拟谱面循环播放)) or (not bool(模拟谱面命中状态)):
            return
        if bool(模拟双踏板模式):
            return
        try:
            判定线y = float(上下文.get("调试_hold_判定线y", 0.0) or 0.0)
            底部y = float(上下文.get("调试_hold_底部y", 0.0) or 0.0)
        except Exception:
            return
        if 底部y <= 判定线y + 12:
            return

        速度 = float(max(60.0, 420.0 * float(模拟谱面调速倍率)))
        travel = float(max(0.05, (底部y - 判定线y) / 速度))
        beat间隔秒 = 0.5
        轨道序 = [0, 1, 2, 3, 4] if ("反向" not in str(模拟谱面方向模式)) else [4, 3, 2, 1, 0]

        for i in range(5):
            上下文[f"特效帧_{i}"] = ""
            上下文[f"特效翻转_{i}"] = False

        前缀表 = {
            0: ("image_084", False),
            1: ("image_085", False),
            2: ("image_086", False),
            3: ("image_085", True),
            4: ("image_084", True),
        }
        当前拍 = int(math.floor(float(当前秒) / beat间隔秒))
        for 偏移拍 in range(0, 6):
            拍号 = int(当前拍 - 偏移拍)
            if 拍号 < 0:
                continue
            轨道 = int(轨道序[拍号 % 5])
            命中秒 = float(拍号 * beat间隔秒 + travel)
            dt = float(当前秒 - 命中秒)
            if dt < 0.0 or dt > 0.16:
                continue
            帧号 = int((dt * 60.0 * 2.0) % 18.0)
            前缀, 翻转 = 前缀表.get(轨道, ("image_086", False))
            上下文[f"特效帧_{轨道}"] = f"{前缀}_{帧号:04d}.png"
            上下文[f"特效翻转_{轨道}"] = bool(翻转)
            try:
                上下文[f"判定区_缩放_{轨道}"] = 1.08
            except Exception:
                pass

    def _绘制模拟循环箭头(上下文: Dict[str, Any], 当前秒: float):
        if bool("全隐" in str(模拟谱面隐藏模式 or "")):
            return

        try:
            轨道中心列表 = [int(v) for v in list(上下文.get("调试_hold_轨道中心列表", []) or [])[:5]]
            判定线y = float(上下文.get("调试_hold_判定线y", 0.0) or 0.0)
            底部y = float(上下文.get("调试_hold_底部y", 0.0) or 0.0)
            基准宽 = int(max(20, int(上下文.get("调试_hold_箭头宽", 80) or 80)))
        except Exception:
            return

        if len(轨道中心列表) < 5 or 底部y <= 判定线y + 16:
            return

        宽倍率 = 0.8 if ("正常" in str(模拟谱面大小模式 or "正常")) else 1.0
        箭头宽 = int(max(18, round(float(基准宽) * 宽倍率)))
        速度 = float(max(60.0, 420.0 * float(模拟谱面调速倍率)))
        beat间隔秒 = 0.5
        轨道序 = [0, 1, 2, 3, 4] if ("反向" not in str(模拟谱面方向模式)) else [4, 3, 2, 1, 0]
        travel = float(max(0.05, (底部y - 判定线y) / 速度))
        半隐阈值 = float(屏幕.get_height()) * float(max(0.1, min(0.95, 模拟半隐入口比例)))
        双踏板模式 = bool(模拟双踏板模式)
        group列表: List[Tuple[List[int], float, int]] = []
        if 双踏板模式:
            try:
                屏宽 = int(屏幕.get_width())
                间距 = 0
                if len(轨道中心列表) >= 2:
                    间距 = int(max(18, int(abs(轨道中心列表[1] - 轨道中心列表[0]))))
                if 间距 <= 0:
                    间距 = int(max(18, int(箭头宽 * 0.86)))
                组宽 = int(间距 * 4)
                中缝 = int(max(24, 屏宽 * 0.02))
                左起x = int((屏宽 - (组宽 * 2 + 中缝)) * 0.5 + float(模拟双踏板左X偏移))
                右起x = int(左起x + 组宽 + 中缝 + float(模拟双踏板右X偏移))
                左中心 = [int(左起x + i * 间距) for i in range(5)]
                右中心 = [int(右起x + i * 间距) for i in range(5)]
                group列表.append((左中心, float(模拟双踏板左Y偏移), 0))
                group列表.append((右中心, float(模拟双踏板右Y偏移), 1))
            except Exception:
                group列表 = [(轨道中心列表, 0.0, 0)]
        else:
            group列表 = [(轨道中心列表, 0.0, 0)]

        当前拍 = int(math.floor(float(当前秒) / beat间隔秒))
        起拍 = int(max(0, 当前拍 - 30))
        终拍 = int(当前拍 + 8)
        for 轨道中心组, y偏移, 组索引 in group列表:
            if len(轨道中心组) < 5:
                continue
            判定线y_g = float(判定线y + y偏移)
            底部y_g = float(底部y + y偏移)

            # 关闭循环播放时也保留静态锚点，避免“箭头层全消失”影响对齐。
            if (not bool(模拟谱面循环播放)) or bool(双踏板模式):
                for 轨道 in range(5):
                    try:
                        基图 = _取模拟箭头图(轨道, int(max(18, 箭头宽 * 0.92)))
                        if isinstance(基图, pygame.Surface):
                            静态图 = 基图.copy()
                            静态图.set_alpha(120 if 组索引 == 0 else 105)
                            屏幕.blit(
                                静态图,
                                (
                                    int(round(float(轨道中心组[轨道]) - 静态图.get_width() * 0.5)),
                                    int(round(float(判定线y_g) - 静态图.get_height() * 0.5)),
                                ),
                            )
                    except Exception:
                        continue
            if not bool(模拟谱面循环播放):
                continue

            for 拍号 in range(起拍, 终拍):
                轨道 = int(轨道序[(拍号 + 组索引) % 5])
                x中心 = float(轨道中心组[轨道])
                起始秒 = float(拍号) * beat间隔秒
                y = float(底部y_g) - (float(当前秒) - 起始秒) * 速度
                if y < -float(箭头宽) or y > float(底部y_g + 箭头宽):
                    continue

                命中秒 = float(起始秒 + travel)
                if bool(模拟谱面命中状态) and float(当前秒) >= 命中秒 and y <= float(判定线y_g):
                    continue
                if ("半隐" in str(模拟谱面隐藏模式 or "")) and y > 半隐阈值:
                    continue

                旋转角 = 0.0
                if "摇摆" in str(模拟谱面轨迹模式 or ""):
                    主振幅 = max(12.0, float(箭头宽) * 0.52) * float(模拟摇摆幅度倍率)
                    主相位 = (
                        float(当前秒) * (math.pi * 2.0) * 2.05
                        + float(起始秒) * 0.55
                        + float(轨道) * 0.72
                        + float(组索引) * 0.38
                    )
                    次相位 = float(主相位) * 0.52 + float(轨道) * 0.35
                    x中心 = float(x中心) + math.sin(主相位) * 主振幅 + math.sin(次相位) * (
                        主振幅 * 0.22
                    )
                elif "旋转" in str(模拟谱面轨迹模式 or ""):
                    旋转角 = float(
                        (float(当前秒) * float(模拟旋转速度度每秒) + float(起始秒) * 140.0 + float(轨道) * 35.0)
                        % 360.0
                    )

                图 = _取模拟箭头图(轨道, 箭头宽)
                if 图 is None:
                    continue
                图2 = 图
                if abs(float(旋转角)) > 0.01:
                    try:
                        图2 = pygame.transform.rotate(图, -float(旋转角)).convert_alpha()
                    except Exception:
                        图2 = 图

                try:
                    屏幕.blit(
                        图2,
                        (
                            int(round(x中心 - float(图2.get_width()) * 0.5)),
                            int(round(y - float(图2.get_height()) * 0.5)),
                        ),
                    )
                except Exception:
                    continue

    def _计算左下面板布局() -> (
        Tuple[
            pygame.Rect,
            pygame.Rect,
            pygame.Rect,
            Dict[str, pygame.Rect],
            Dict[str, pygame.Rect],
        ]
    ):
        面板边距 = 12
        内边距 = 12
        复选框边长 = 18
        复选框文字距 = 10
        行距 = 8
        分组距 = 10

        信息文本 = [
            f"选中: {选中控件id or 选中调试项id or '-'}",
            "拖动=位置  方向键=微调  +/-=层级/血条参数",
            "滚轮=等比  Shift=宽/大步进  Ctrl=高  Alt=字号",
            "单击文本=字间距面板",
            "Ctrl+S=保存  ESC=退出",
        ]
        调试项数量 = 9

        开关项 = _取开关项()

        try:
            标题宽 = 字体.size("调试面板")[0]
        except Exception:
            标题宽 = 120

        内容宽 = int(标题宽)
        for _, 标签, _值 in 开关项:
            try:
                文本宽 = 字体.size(标签)[0]
            except Exception:
                文本宽 = 120
            内容宽 = max(内容宽, int(复选框边长 + 复选框文字距 + 文本宽))

        for 文本 in 信息文本:
            try:
                内容宽 = max(内容宽, int(字体.size(文本)[0]))
            except Exception:
                pass

        try:
            字高 = int(max(18, 字体.get_height()))
        except Exception:
            字高 = 22

        面板宽 = int(max(280, 内容宽 + 内边距 * 2))
        面板高 = int(
            内边距
            + 字高
            + 分组距
            + len(开关项) * (max(复选框边长, 字高) + 行距)
            - 行距
            + 分组距
            + (字高 + 8) * 调试项数量
            - (8 * max(0, 调试项数量 - 1) - 行距 * max(0, 调试项数量 - 1))
            + 分组距
            + len(信息文本) * (字高 + 4)
            - 4
            + 内边距
        )

        屏宽, 屏高 = 屏幕.get_size()
        面板rect = pygame.Rect(
            面板边距,
            int(屏高 - 面板高 - 面板边距),
            面板宽,
            面板高,
        )
        顶部横杠rect = pygame.Rect(
            int(面板rect.centerx - 22),
            int(面板rect.y + 6),
            44,
            10,
        )
        尾巴rect = pygame.Rect(
            int(面板rect.x),
            int(面板rect.bottom - 104),
            28,
            96,
        )

        行rect表: Dict[str, pygame.Rect] = {}
        当前y = int(面板rect.y + 内边距 + 字高 + 分组距)
        行高 = int(max(复选框边长, 字高))
        for 开关id, _标签, _值 in 开关项:
            行rect表[开关id] = pygame.Rect(
                int(面板rect.x + 内边距),
                int(当前y),
                int(面板rect.w - 内边距 * 2),
                int(行高),
            )
            当前y += int(行高 + 行距)

        调试rect表: Dict[str, pygame.Rect] = {}
        调试rect表["调试_圆环频谱长度"] = pygame.Rect(
            int(面板rect.x + 内边距),
            int(当前y + 2),
            int(面板rect.w - 内边距 * 2),
            int(字高 + 6),
        )
        当前y = int(调试rect表["调试_圆环频谱长度"].bottom + 行距)
        调试rect表["调试_血量"] = pygame.Rect(
            int(面板rect.x + 内边距),
            int(当前y),
            int(面板rect.w - 内边距 * 2),
            int(字高 + 6),
        )
        当前y = int(调试rect表["调试_血量"].bottom + 行距)
        for 调试id in (
            "调试_背景蒙板不透明度",
            "调试_血条晃荡速度",
            "调试_血条晃荡幅度",
            "调试_暴走血条速度",
            "调试_暴走血条不透明度",
            "调试_暴走血条羽化",
            "调试_头像框特效速度",
        ):
            调试rect表[调试id] = pygame.Rect(
                int(面板rect.x + 内边距),
                int(当前y),
                int(面板rect.w - 内边距 * 2),
                int(字高 + 6),
            )
            当前y = int(调试rect表[调试id].bottom + 行距)

        return 面板rect, 顶部横杠rect, 尾巴rect, 行rect表, 调试rect表

    def _绘制左下面板():
        面板rect, 顶部横杠rect, 尾巴rect, 行rect表, 调试rect表 = _计算左下面板布局()

        if bool(左侧面板折叠):
            try:
                面板底 = pygame.Surface((尾巴rect.w, 尾巴rect.h), pygame.SRCALPHA)
                面板底.fill((0, 0, 0, 145))
                屏幕.blit(面板底, 尾巴rect.topleft)
                pygame.draw.rect(屏幕, (215, 225, 255), 尾巴rect, width=1, border_radius=8)
                pygame.draw.line(
                    屏幕,
                    (255, 245, 170),
                    (int(尾巴rect.x + 6), int(尾巴rect.y + 14)),
                    (int(尾巴rect.right - 6), int(尾巴rect.y + 14)),
                    width=2,
                )
                文图 = 字体.render("调试", True, (235, 235, 245))
                屏幕.blit(文图, (int(尾巴rect.x + 3), int(尾巴rect.y + 28)))
            except Exception:
                pass
            return

        try:
            面板底 = pygame.Surface((面板rect.w, 面板rect.h), pygame.SRCALPHA)
            面板底.fill((0, 0, 0, 155))
            屏幕.blit(面板底, 面板rect.topleft)
            pygame.draw.rect(屏幕, (215, 225, 255), 面板rect, width=1, border_radius=10)
            pygame.draw.line(
                屏幕,
                (255, 245, 170),
                (int(顶部横杠rect.x + 2), int(顶部横杠rect.centery)),
                (int(顶部横杠rect.right - 2), int(顶部横杠rect.centery)),
                width=2,
            )
        except Exception:
            pass

        标题x = int(面板rect.x + 12)
        标题y = int(面板rect.y + 10)
        try:
            标题图 = 字体.render("调试面板", True, (255, 245, 170))
            屏幕.blit(标题图, (标题x, 标题y))
        except Exception:
            pass

        开关项 = _取开关项()
        复选框边长 = 18
        for 开关id, 标签, 是否开启 in 开关项:
            行rect = 行rect表.get(开关id)
            if 行rect is None:
                continue

            复选框rect = pygame.Rect(行rect.x, 行rect.y, 复选框边长, 复选框边长)
            try:
                pygame.draw.rect(
                    屏幕, (240, 240, 245), 复选框rect, width=2, border_radius=4
                )
                if 是否开启:
                    内框 = 复选框rect.inflate(-6, -6)
                    pygame.draw.rect(屏幕, (100, 220, 140), 内框, border_radius=3)
            except Exception:
                pass

            try:
                文图 = 字体.render(str(标签), True, (235, 235, 245))
                文y = int(行rect.y + (行rect.h - 文图.get_height()) // 2)
                屏幕.blit(文图, (复选框rect.right + 10, 文y))
            except Exception:
                pass

        调试项文本 = {
            "调试_圆环频谱长度": (
                f"频谱最大长度: {int(圆环频谱最大长度)}  点击后 +/- 调整",
                (95, 105, 120),
                (235, 235, 245),
                (90, 95, 145, 110),
            ),
            "调试_血量": (
                f"血量: {int(round(调试血量显示 * 100.0))}%  点击后 +/- 每次10%",
                (120, 98, 118),
                (245, 235, 245),
                (140, 96, 128, 110),
            ),
            "调试_背景蒙板不透明度": (
                f"背景蒙板不透明度: {int(round(调试背景蒙板不透明度 * 100.0))}%",
                (98, 120, 128),
                (235, 245, 250),
                (86, 128, 146, 110),
            ),
            "调试_血条晃荡速度": (
                f"血条晃荡频率: {调试血条晃荡速度:.2f}",
                (128, 112, 78),
                (245, 240, 228),
                (150, 126, 82, 110),
            ),
            "调试_血条晃荡幅度": (
                f"血条晃荡幅度: {调试血条晃荡幅度:.1f}px",
                (108, 96, 142),
                (240, 235, 245),
                (118, 96, 150, 110),
            ),
            "调试_暴走血条速度": (
                f"暴走血条速度: {调试暴走血条速度:.1f}px/s",
                (132, 92, 72),
                (245, 236, 228),
                (150, 98, 78, 110),
            ),
            "调试_暴走血条不透明度": (
                f"暴走血条不透明度: {int(round(调试暴走血条不透明度 * 100.0))}%",
                (120, 92, 132),
                (244, 234, 245),
                (136, 98, 150, 110),
            ),
            "调试_暴走血条羽化": (
                f"暴走血条羽化: {调试暴走血条羽化:.1f}px",
                (96, 112, 146),
                (236, 242, 250),
                (98, 118, 158, 110),
            ),
            "调试_头像框特效速度": (
                f"头像特效速度: {调试头像框特效速度:.1f}fps",
                (72, 124, 132),
                (235, 243, 245),
                (72, 144, 162, 110),
            ),
        }
        for 调试id, (文本, 边框色, 字色, 选中色) in 调试项文本.items():
            rect = 调试rect表.get(调试id)
            if rect is None:
                continue
            try:
                if str(选中调试项id or "") == 调试id:
                    选中底 = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    选中底.fill(选中色)
                    屏幕.blit(选中底, rect.topleft)
                pygame.draw.rect(屏幕, 边框色, rect, width=1, border_radius=6)
                图 = 字体.render(文本, True, 字色)
                屏幕.blit(
                    图,
                    (
                        int(rect.x + 8),
                        int(rect.y + (rect.h - 图.get_height()) // 2),
                    ),
                )
            except Exception:
                pass

        信息文本 = [
            f"选中: {选中控件id or 选中调试项id or '-'}",
            "拖动=位置  方向键=微调  +/-=层级/血条参数",
            "滚轮=等比  Shift=宽/大步进  Ctrl=高  Alt=字号",
            "单击文本=字间距面板",
            "Ctrl+S=保存  ESC=退出",
        ]
        信息y = int(max(rect.bottom for rect in 调试rect表.values()) + 10)
        for 文本 in 信息文本:
            try:
                图 = 字体.render(文本, True, (235, 235, 245))
                屏幕.blit(图, (面板rect.x + 12, 信息y))
                信息y += 图.get_height() + 4
            except Exception:
                pass

    def _绘制血条头预览(当前秒: float):
        if not bool(显示血条头预览):
            return

        屏宽, 屏高 = 屏幕.get_size()
        预览rect = pygame.Rect(
            int(max(16, 屏宽 * 0.38)),
            int(max(16, 屏高 * 0.12)),
            220,
            180,
        )
        头rect = pygame.Rect(
            int(预览rect.x + 136),
            int(预览rect.y + 48),
            36,
            82,
        )
        血条rect = pygame.Rect(
            int(预览rect.x + 26),
            int(预览rect.y + 50),
            148,
            78,
        )
        填充宽 = int(max(0, min(血条rect.w, round(float(血条rect.w) * 调试血量显示))))

        try:
            底 = pygame.Surface((预览rect.w, 预览rect.h), pygame.SRCALPHA)
            底.fill((8, 10, 16, 185))
            屏幕.blit(底, 预览rect.topleft)
            pygame.draw.rect(屏幕, (220, 230, 255), 预览rect, width=1, border_radius=10)
        except Exception:
            pass

        try:
            标题图 = 字体.render("血条头独立预览", True, (255, 245, 170))
            屏幕.blit(标题图, (int(预览rect.x + 12), int(预览rect.y + 10)))
        except Exception:
            pass

        try:
            pygame.draw.rect(屏幕, (34, 34, 40), 血条rect, border_radius=12)
            pygame.draw.rect(屏幕, (76, 58, 88), 血条rect, width=2, border_radius=12)
            if 填充宽 > 0:
                pygame.draw.rect(
                    屏幕,
                    (210, 62, 214),
                    pygame.Rect(血条rect.x, 血条rect.y, 填充宽, 血条rect.h),
                    border_radius=12,
                )
            pygame.draw.rect(屏幕, (236, 192, 242), 头rect, width=1, border_radius=10)
            pygame.draw.line(
                屏幕,
                (255, 255, 255),
                (int(血条rect.x + 10), int(血条rect.y + 10)),
                (int(血条rect.right - 10), int(血条rect.y + 10)),
                width=1,
            )
        except Exception:
            pass

        try:
            控件定义 = getattr(布局管理器, "_控件索引", {}).get("血条头波浪", {})
            if not isinstance(控件定义, dict):
                控件定义 = {}
            预览定义 = dict(控件定义)
            预览定义["玩家键"] = "玩家序号"
            预览上下文 = {
                "当前谱面秒": float(当前秒),
                "调试_时间秒": float(当前秒),
                "玩家序号": 1,
                "血量最终显示": float(调试血量显示),
                "血条填充区域x": int(血条rect.x),
                "血条填充区域y": int(血条rect.y),
                "血条填充区域w": int(血条rect.w),
                "血条填充区域h": int(血条rect.h),
            }
            绘制函数 = getattr(布局管理器, "_绘制血条头波浪", None)
            if callable(绘制函数):
                绘制函数(屏幕, 头rect, 预览定义, 预览上下文)
        except Exception as 异常:
            try:
                提示文本 = f"预览绘制失败: {type(异常).__name__}"
                提示图 = 字体.render(提示文本, True, (255, 120, 120))
                屏幕.blit(提示图, (int(预览rect.x + 12), int(预览rect.bottom - 30)))
            except Exception:
                pass

    def _截断文本(文本: str, 最大宽: int) -> str:
        文本 = str(文本 or "")
        try:
            if 字体.size(文本)[0] <= int(最大宽):
                return 文本
        except Exception:
            return 文本
        后缀 = "..."
        for 长度 in range(len(文本), 0, -1):
            候选 = f"{文本[:长度]}{后缀}"
            try:
                if 字体.size(候选)[0] <= int(最大宽):
                    return 候选
            except Exception:
                continue
        return 后缀

    def _取图层项():
        try:
            return list(布局管理器.取调试图层列表())
        except Exception:
            return []

    def _计算右侧图层面板布局() -> Tuple[
        pygame.Rect,
        pygame.Rect,
        pygame.Rect,
        Dict[str, pygame.Rect],
        Dict[str, pygame.Rect],
        List[Dict[str, Any]],
    ]:
        nonlocal 图层面板滚动
        if not bool(显示图层面板):
            return pygame.Rect(0, 0, 0, 0), pygame.Rect(0, 0, 0, 0), pygame.Rect(0, 0, 0, 0), {}, {}, []
        屏宽, 屏高 = 屏幕.get_size()
        面板边距 = 12
        内边距 = 12
        面板宽 = int(max(320, min(430, 屏宽 * 0.28)))
        面板高 = int(max(240, min(420, (屏高 - 面板边距 * 3) * 0.52)))
        面板rect = pygame.Rect(
            int(屏宽 - 面板宽 - 面板边距),
            int(屏高 - 面板高 - 面板边距),
            面板宽,
            面板高,
        )
        顶部横杠rect = pygame.Rect(
            int(面板rect.centerx - 22),
            int(面板rect.y + 6),
            44,
            10,
        )
        尾巴rect = pygame.Rect(
            int(面板rect.right - 28),
            int(面板rect.bottom - 104),
            28,
            96,
        )

        try:
            字高 = int(max(18, 字体.get_height()))
        except Exception:
            字高 = 22
        标题高 = int(字高 + 8)
        行高 = int(max(22, 字高 + 4))
        可视起y = int(面板rect.y + 内边距 + 标题高 + 8)
        可视高 = int(max(80, 面板rect.h - (可视起y - 面板rect.y) - 内边距))
        可视行数 = int(max(1, 可视高 // 行高))

        图层项 = _取图层项()
        最大滚动 = int(max(0, len(图层项) - 可视行数))
        图层面板滚动 = int(max(0, min(图层面板滚动, 最大滚动)))
        可视项 = 图层项[图层面板滚动 : 图层面板滚动 + 可视行数]

        行rect表: Dict[str, pygame.Rect] = {}
        眼睛rect表: Dict[str, pygame.Rect] = {}
        当前y = 可视起y
        for 项 in 可视项:
            控件id = str(项.get("id") or "")
            行rect = pygame.Rect(
                int(面板rect.x + 内边距),
                int(当前y),
                int(面板rect.w - 内边距 * 2),
                int(行高),
            )
            行rect表[控件id] = 行rect
            眼睛rect表[控件id] = pygame.Rect(
                int(行rect.x),
                int(行rect.y + (行rect.h - 16) // 2),
                18,
                16,
            )
            当前y += 行高

        return 面板rect, 顶部横杠rect, 尾巴rect, 行rect表, 眼睛rect表, 可视项

    def _绘制右侧图层面板():
        if not bool(显示图层面板):
            return
        面板rect, 顶部横杠rect, 尾巴rect, 行rect表, 眼睛rect表, 可视项 = _计算右侧图层面板布局()
        if bool(右侧面板折叠):
            try:
                面板底 = pygame.Surface((尾巴rect.w, 尾巴rect.h), pygame.SRCALPHA)
                面板底.fill((0, 0, 0, 145))
                屏幕.blit(面板底, 尾巴rect.topleft)
                pygame.draw.rect(屏幕, (215, 225, 255), 尾巴rect, width=1, border_radius=8)
                pygame.draw.line(
                    屏幕,
                    (255, 245, 170),
                    (int(尾巴rect.x + 6), int(尾巴rect.y + 14)),
                    (int(尾巴rect.right - 6), int(尾巴rect.y + 14)),
                    width=2,
                )
                文图 = 字体.render("图层", True, (235, 235, 245))
                屏幕.blit(文图, (int(尾巴rect.x + 3), int(尾巴rect.y + 28)))
            except Exception:
                pass
            return
        try:
            面板底 = pygame.Surface((面板rect.w, 面板rect.h), pygame.SRCALPHA)
            面板底.fill((0, 0, 0, 165))
            屏幕.blit(面板底, 面板rect.topleft)
            pygame.draw.rect(屏幕, (215, 225, 255), 面板rect, width=1, border_radius=10)
            pygame.draw.line(
                屏幕,
                (255, 245, 170),
                (int(顶部横杠rect.x + 2), int(顶部横杠rect.centery)),
                (int(顶部横杠rect.right - 2), int(顶部横杠rect.centery)),
                width=2,
            )
        except Exception:
            pass

        try:
            标题图 = 字体.render("图层", True, (255, 245, 170))
            屏幕.blit(标题图, (面板rect.x + 12, 面板rect.y + 10))
        except Exception:
            pass

        try:
            提示图 = 字体.render("点眼睛隐藏  点行选择", True, (210, 220, 230))
            屏幕.blit(提示图, (面板rect.x + 70, 面板rect.y + 10))
        except Exception:
            pass

        for 项 in 可视项:
            控件id = str(项.get("id") or "")
            行rect = 行rect表.get(控件id)
            眼睛rect = 眼睛rect表.get(控件id)
            if 行rect is None or 眼睛rect is None:
                continue

            是否隐藏 = bool(控件id in 隐藏控件ids)
            是否选中 = str(选中控件id or "") == 控件id
            深度 = int(max(0, int(项.get("depth", 0) or 0)))
            类型 = str(项.get("类型") or "")
            z值 = int(项.get("z", 0) or 0)
            缩进 = int(min(深度, 8) * 14)
            文本色 = (140, 145, 155) if 是否隐藏 else (235, 235, 245)

            try:
                if 是否选中:
                    选中底 = pygame.Surface((行rect.w, 行rect.h), pygame.SRCALPHA)
                    选中底.fill((80, 110, 150, 110))
                    屏幕.blit(选中底, 行rect.topleft)
                pygame.draw.rect(屏幕, (65, 70, 78), 行rect, width=1, border_radius=6)
            except Exception:
                pass

            try:
                pygame.draw.rect(
                    屏幕, (220, 225, 230), 眼睛rect, width=1, border_radius=8
                )
                if not 是否隐藏:
                    中心 = (int(眼睛rect.centerx), int(眼睛rect.centery))
                    pygame.draw.ellipse(
                        屏幕, (110, 220, 180), 眼睛rect.inflate(-4, -6), width=2
                    )
                    pygame.draw.circle(屏幕, (110, 220, 180), 中心, 2)
                else:
                    pygame.draw.line(
                        屏幕,
                        (180, 90, 90),
                        (int(眼睛rect.x + 2), int(眼睛rect.bottom - 2)),
                        (int(眼睛rect.right - 2), int(眼睛rect.y + 2)),
                        width=2,
                    )
            except Exception:
                pass

            文本x = int(眼睛rect.right + 10 + 缩进)
            标签 = f"{控件id} [{类型}]  z={z值}"
            最大文本宽 = int(max(40, 行rect.right - 文本x - 8))
            标签 = _截断文本(标签, 最大文本宽)
            try:
                文图 = 字体.render(标签, True, 文本色)
                文y = int(行rect.y + (行rect.h - 文图.get_height()) // 2)
                屏幕.blit(文图, (文本x, 文y))
            except Exception:
                pass

        try:
            图层总数 = len(_取图层项())
            面板信息 = f"{图层总数} layers"
            if 图层总数 > len(可视项):
                面板信息 += f"  scroll {图层面板滚动 + 1}"
            信息图 = 字体.render(面板信息, True, (210, 220, 230))
            屏幕.blit(
                信息图,
                (int(面板rect.x + 12), int(面板rect.bottom - 信息图.get_height() - 10)),
            )
        except Exception:
            pass

    def _绘制背景():
        nonlocal 背景缩放图, 背景缩放尺寸
        w, h = 屏幕.get_size()
        if 背景原图 is None:
            屏幕.fill((16, 16, 20))
            return
        if 背景缩放图 is None or 背景缩放尺寸 != (w, h):
            try:
                背景缩放图 = pygame.transform.smoothscale(背景原图, (w, h)).convert()
                背景缩放尺寸 = (w, h)
            except Exception:
                背景缩放图 = None
                背景缩放尺寸 = (0, 0)
        if 背景缩放图 is not None:
            屏幕.blit(背景缩放图, (0, 0))
            暗层 = pygame.Surface((w, h), pygame.SRCALPHA)
            暗层透明度 = int(
                max(0, min(255, round(float(调试背景蒙板不透明度) * 255.0)))
            )
            暗层.fill((0, 0, 0, 暗层透明度))
            屏幕.blit(暗层, (0, 0))
        else:
            屏幕.fill((16, 16, 20))

    def _同步模拟hold锚点(上下文: Dict[str, Any]):
        try:
            构建清单 = getattr(布局管理器, "_构建渲染清单", None)
            if not callable(构建清单):
                return
            项列表 = 构建清单(屏幕.get_size(), 上下文, 仅绘制根id="判定区组")
        except Exception:
            return

        if not isinstance(项列表, list):
            return

        判定区状态表: Dict[str, Dict[str, Any]] = {}
        for 项 in 项列表:
            if not isinstance(项, dict):
                continue
            控件id = str(项.get("id") or "")
            if 控件id.startswith("判定区_"):
                判定区状态表[控件id] = 项

        中心x列表: List[int] = []
        中心y列表: List[int] = []
        箭头宽列表: List[int] = []

        try:
            参数 = getattr(布局管理器, "_取游戏区参数_可写", lambda: {})()
        except Exception:
            参数 = {}

        try:
            hold宽度系数 = float((参数 or {}).get("hold宽度系数", 0.96) or 0.96)
        except Exception:
            hold宽度系数 = 0.96
        try:
            判定区宽度系数 = float((参数 or {}).get("判定区宽度系数", 1.0) or 1.0)
        except Exception:
            判定区宽度系数 = 1.0

        宽度比 = float(max(0.1, hold宽度系数 / max(0.01, 判定区宽度系数)))

        for 轨道序号 in range(5):
            状态 = 判定区状态表.get(f"判定区_{轨道序号}")
            if not isinstance(状态, dict):
                return
            矩形 = 状态.get("rect")
            if not isinstance(矩形, pygame.Rect):
                return
            中心x列表.append(int(矩形.centerx))
            中心y列表.append(int(矩形.centery))
            箭头宽列表.append(int(max(16, 矩形.w * 宽度比)))

        上下文["调试_hold_轨道中心列表"] = 中心x列表
        上下文["调试_hold_判定线y列表"] = 中心y列表
        if 中心y列表:
            上下文["调试_hold_判定线y"] = int(
                中心y列表[2] if len(中心y列表) >= 3 else 中心y列表[0]
            )
        上下文["调试_hold_箭头宽列表"] = 箭头宽列表

    def _同步血条填充锚点(上下文: Dict[str, Any]):
        try:
            构建清单 = getattr(布局管理器, "_构建渲染清单", None)
            if not callable(构建清单):
                return
            项列表 = 构建清单(屏幕.get_size(), 上下文, 仅绘制根id="顶部HUD")
        except Exception:
            return

        if not isinstance(项列表, list):
            return

        血条值矩形 = None
        for 项 in 项列表:
            if not isinstance(项, dict):
                continue
            if str(项.get("id") or "") != "血条值":
                continue
            矩形 = 项.get("rect")
            if isinstance(矩形, pygame.Rect):
                血条值矩形 = 矩形.copy()
                break

        if not isinstance(血条值矩形, pygame.Rect):
            return

        控件定义 = getattr(布局管理器, "_控件索引", {}).get("血条值", {})
        内边距 = 控件定义.get("内边距", {}) if isinstance(控件定义, dict) else {}
        l = int(float((内边距 or {}).get("l", 0) or 0))
        t = int(float((内边距 or {}).get("t", 0) or 0))
        r = int(float((内边距 or {}).get("r", 0) or 0))
        b = int(float((内边距 or {}).get("b", 0) or 0))
        内矩形 = pygame.Rect(
            int(血条值矩形.x + l),
            int(血条值矩形.y + t),
            int(max(2, 血条值矩形.w - l - r)),
            int(max(2, 血条值矩形.h - t - b)),
        )
        上下文["血条填充区域x"] = int(内矩形.x)
        上下文["血条填充区域y"] = int(内矩形.y)
        上下文["血条填充区域w"] = int(内矩形.w)
        上下文["血条填充区域h"] = int(内矩形.h)

    def _绘制模拟长按击中(上下文: Dict[str, Any], 当前秒: float):
        if (not 模拟长按击中) or 模拟hold渲染器 is None:
            return

        try:
            图集 = getattr(getattr(模拟hold渲染器, "_皮肤包", None), "arrow", None)
        except Exception:
            图集 = None
        if 图集 is None:
            return

        try:
            轨道中心原值 = 上下文.get("调试_hold_轨道中心列表", []) or []
            轨道中心列表 = [int(float(x)) for x in list(轨道中心原值)[:5]]
            底部y = int(float(上下文.get("调试_hold_底部y", 0) or 0))
            判定线y列表原值 = 上下文.get("调试_hold_判定线y列表", []) or []
            判定线y列表 = [int(float(y)) for y in list(判定线y列表原值)[:5]]
            箭头宽列表原值 = 上下文.get("调试_hold_箭头宽列表", []) or []
            箭头宽列表 = [int(float(w)) for w in list(箭头宽列表原值)[:5]]
            判定线y = int(float(上下文.get("调试_hold_判定线y", 0) or 0))
            箭头宽 = int(float(上下文.get("调试_hold_箭头宽", 0) or 0))
        except Exception:
            return

        if len(轨道中心列表) < 5 or 箭头宽 <= 0:
            return

        while len(判定线y列表) < 5:
            判定线y列表.append(int(判定线y))
        while len(箭头宽列表) < 5:
            箭头宽列表.append(int(箭头宽))

        周期秒 = 2.4
        相位列表: List[float] = [0.00, 0.20, 0.40, 0.60, 0.80]

        图层 = pygame.Surface(屏幕.get_size(), pygame.SRCALPHA)
        for 轨道序号, x中心 in enumerate(轨道中心列表[:5]):
            当前判定线y = int(判定线y列表[轨道序号])
            当前箭头宽 = int(max(16, 箭头宽列表[轨道序号]))
            可视高度 = int(max(60, 底部y - 当前判定线y))
            最短长度 = int(
                max(当前箭头宽 * 1.2, min(可视高度 * 0.16, 当前箭头宽 * 2.1))
            )
            最长长度 = int(max(最短长度 + 12, min(可视高度 * 0.72, 当前箭头宽 * 6.2)))
            起始y = float(当前判定线y - max(8, int(当前箭头宽 * 0.28)))
            上边界 = -int(max(40, 当前箭头宽 * 2))
            下边界 = int(底部y + max(40, 当前箭头宽 * 2))
            进度 = ((float(当前秒) / 周期秒) + 相位列表[轨道序号]) % 1.0
            当前长度 = int(最短长度 + (最长长度 - 最短长度) * (1.0 - 进度))
            y结束 = float(当前判定线y + 当前长度)
            try:
                getattr(模拟hold渲染器, "_画hold")(
                    图层,
                    图集,
                    int(轨道序号),
                    int(x中心),
                    float(起始y),
                    float(y结束),
                    int(当前箭头宽),
                    int(当前判定线y),
                    True,
                    int(上边界),
                    int(下边界),
                    True,
                )
            except Exception:
                continue

        try:
            图层.set_alpha(210)
        except Exception:
            pass
        屏幕.blit(图层, (0, 0))

    def _处理滚轮(滚轮方向: int):
        nonlocal 选中控件id
        if not 选中控件id:
            return

        按键状态 = pygame.key.get_mods()
        步进像素 = int(12 * int(滚轮方向))

        是否按住shift = bool(按键状态 & pygame.KMOD_SHIFT)
        是否按住ctrl = bool(按键状态 & pygame.KMOD_CTRL)
        是否按住alt = bool(按键状态 & pygame.KMOD_ALT)

        if 是否按住alt:
            _记录撤销()
            布局管理器.改字号(选中控件id, int(滚轮方向))
            return

        if 是否按住shift and (not 是否按住ctrl):
            _记录撤销()
            布局管理器.缩放控件(选中控件id, float(步进像素), 0.0, 屏幕.get_size())
            return

        if 是否按住ctrl and (not 是否按住shift):
            _记录撤销()
            布局管理器.缩放控件(选中控件id, 0.0, float(步进像素), 屏幕.get_size())
            return

        _记录撤销()
        布局管理器.缩放控件(
            选中控件id, float(步进像素), float(步进像素), 屏幕.get_size()
        )

    while True:
        时钟.tick(60)
        当前秒 = float(pygame.time.get_ticks()) / 1000.0
        if bool(文本字间距面板开启) and (
            文本字间距目标控件id
            and (not _是否文本控件(文本字间距目标控件id))
        ):
            文本字间距目标控件id = ""

        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                pygame.quit()
                return

            if 事件.type == pygame.VIDEORESIZE:
                新宽 = int(max(640, 事件.w))
                新高 = int(max(360, 事件.h))
                屏幕 = pygame.display.set_mode((新宽, 新高), pygame.RESIZABLE)

            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if 事件.key == pygame.K_z and (
                    pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    _撤销一步()
                    continue
                if 事件.key == pygame.K_s and (
                    pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    try:
                        布局管理器.保存()
                    except Exception:
                        pass
                    _保存调试设置()
                if 选中控件id and 事件.key == pygame.K_b:
                    控件 = getattr(布局管理器, "_控件索引", {}).get(str(选中控件id))
                    if isinstance(控件, dict) and str(控件.get("类型") or "") == "文本":
                        _记录撤销()
                        控件["粗体"] = not bool(控件.get("粗体", False))
                    continue
                if 事件.key in (
                    pygame.K_EQUALS,
                    pygame.K_KP_PLUS,
                    pygame.K_MINUS,
                    pygame.K_KP_MINUS,
                ):
                    增量 = 1 if 事件.key in (pygame.K_EQUALS, pygame.K_KP_PLUS) else -1
                    大步进 = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                    if str(选中调试项id or "") == "调试_血量":
                        调试血量显示 = float(
                            max(0.0, min(1.0, 调试血量显示 + 0.1 * float(增量)))
                        )
                        _保存调试设置()
                        continue
                    if str(选中调试项id or "") == "调试_背景蒙板不透明度":
                        步进 = 0.10 if 大步进 else 0.05
                        调试背景蒙板不透明度 = float(
                            max(0.0, min(1.0, 调试背景蒙板不透明度 + 增量 * 步进))
                        )
                        _保存调试设置()
                        continue
                    if str(选中调试项id or "") == "调试_血条晃荡速度":
                        步进 = 0.5 if 大步进 else 0.1
                        调试血条晃荡速度 = float(
                            max(0.0, min(12.0, 调试血条晃荡速度 + 增量 * 步进))
                        )
                        _保存调试设置()
                        continue
                    if str(选中调试项id or "") == "调试_血条晃荡幅度":
                        步进 = 2.0 if 大步进 else 0.5
                        调试血条晃荡幅度 = float(
                            max(0.0, min(40.0, 调试血条晃荡幅度 + 增量 * 步进))
                        )
                        _保存调试设置()
                        continue
                    if str(选中调试项id or "") == "调试_暴走血条速度":
                        步进 = 20.0 if 大步进 else 5.0
                        调试暴走血条速度 = float(
                            max(0.0, min(600.0, 调试暴走血条速度 + 增量 * 步进))
                        )
                        _保存调试设置()
                        continue
                    if str(选中调试项id or "") == "调试_暴走血条不透明度":
                        步进 = 0.10 if 大步进 else 0.05
                        调试暴走血条不透明度 = float(
                            max(
                                0.0,
                                min(1.0, 调试暴走血条不透明度 + 增量 * 步进),
                            )
                        )
                        _保存调试设置()
                        continue
                    if str(选中调试项id or "") == "调试_暴走血条羽化":
                        步进 = 2.0 if 大步进 else 0.5
                        调试暴走血条羽化 = float(
                            max(0.0, min(80.0, 调试暴走血条羽化 + 增量 * 步进))
                        )
                        _保存调试设置()
                        continue
                    if str(选中调试项id or "") == "调试_头像框特效速度":
                        步进 = 5.0 if 大步进 else 1.0
                        调试头像框特效速度 = float(
                            max(1.0, min(120.0, 调试头像框特效速度 + 增量 * 步进))
                        )
                        _保存调试设置()
                        continue
                    if str(选中调试项id or "") == "调试_圆环频谱长度":
                        圆环频谱最大长度 = int(
                            max(6, min(96, int(圆环频谱最大长度) + 增量))
                        )
                        try:
                            if 调试圆环频谱对象 is not None and hasattr(
                                调试圆环频谱对象, "设置调试外延最大长度"
                            ):
                                调试圆环频谱对象.设置调试外延最大长度(圆环频谱最大长度)
                        except Exception:
                            pass
                        _保存调试设置()
                        continue
                    if _调整模拟项(str(选中调试项id or ""), 增量, 大步进):
                        _保存调试设置()
                        continue
                    if 选中控件id:
                        _记录撤销()
                        布局管理器.改层级(选中控件id, 增量)
                        continue
                if 选中控件id and 事件.key in (
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                    pygame.K_UP,
                    pygame.K_DOWN,
                ):
                    步进 = 10 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 1
                    dx = 0
                    dy = 0
                    if 事件.key == pygame.K_LEFT:
                        dx = -步进
                    elif 事件.key == pygame.K_RIGHT:
                        dx = 步进
                    elif 事件.key == pygame.K_UP:
                        dy = -步进
                    elif 事件.key == pygame.K_DOWN:
                        dy = 步进
                    if dx != 0 or dy != 0:
                        _记录撤销()
                        布局管理器.移动控件(
                            选中控件id, float(dx), float(dy), 屏幕.get_size()
                        )
                        continue

            if 事件.type == pygame.MOUSEBUTTONDOWN:
                if 事件.button == 1:
                    if bool(文本字间距面板开启):
                        面板, 减, 加, 关 = _计算文本字间距面板布局()
                        if isinstance(面板, pygame.Rect):
                            if isinstance(关, pygame.Rect) and 关.collidepoint(事件.pos):
                                _关闭文本字间距面板()
                                continue
                            if isinstance(减, pygame.Rect) and 减.collidepoint(事件.pos):
                                if _是否文本控件(文本字间距目标控件id):
                                    _记录撤销()
                                    布局管理器.改字间距(str(文本字间距目标控件id), -1)
                                continue
                            if isinstance(加, pygame.Rect) and 加.collidepoint(事件.pos):
                                if _是否文本控件(文本字间距目标控件id):
                                    _记录撤销()
                                    布局管理器.改字间距(str(文本字间距目标控件id), +1)
                                continue

                    模拟面板rect, 模拟横杠rect, 模拟尾巴rect, 模拟行rect表 = _计算模拟面板布局()
                    if bool(模拟面板折叠):
                        if 模拟尾巴rect.collidepoint(事件.pos):
                            模拟面板折叠 = False
                            _保存调试设置()
                            拖拽中 = False
                            拖拽已记录撤销 = False
                            continue
                    else:
                        if 模拟横杠rect.collidepoint(事件.pos):
                            模拟面板折叠 = True
                            _保存调试设置()
                            拖拽中 = False
                            拖拽已记录撤销 = False
                            continue
                        if 模拟面板rect.collidepoint(事件.pos):
                            for 模拟项id, rect in 模拟行rect表.items():
                                if not rect.collidepoint(事件.pos):
                                    continue
                                选中调试项id = str(模拟项id)
                                选中控件id = ""
                                if str(模拟项id) in {
                                    "模拟_循环播放",
                                    "模拟_命中状态",
                                    "模拟_调速",
                                    "模拟_隐藏",
                                    "模拟_轨迹",
                                    "模拟_方向",
                                    "模拟_大小",
                                    "模拟_双踏板",
                                    "模拟_箭头",
                                }:
                                    _调整模拟项(str(模拟项id), +1, False)
                                    _保存调试设置()
                                拖拽中 = False
                                拖拽已记录撤销 = False
                                break
                            else:
                                选中控件id = ""
                                选中调试项id = ""
                            continue

                    面板rect, 左横杠rect, 左尾巴rect, 行rect表, 调试rect表 = _计算左下面板布局()
                    if bool(左侧面板折叠):
                        if 左尾巴rect.collidepoint(事件.pos):
                            左侧面板折叠 = False
                            _保存调试设置()
                            拖拽中 = False
                            拖拽已记录撤销 = False
                            continue
                    elif 左横杠rect.collidepoint(事件.pos):
                        左侧面板折叠 = True
                        _保存调试设置()
                        拖拽中 = False
                        拖拽已记录撤销 = False
                        continue

                    if (not bool(左侧面板折叠)) and 面板rect.collidepoint(事件.pos):
                        已命中调试项 = False
                        for 调试id, rect in 调试rect表.items():
                            if rect.collidepoint(事件.pos):
                                选中调试项id = str(调试id)
                                选中控件id = ""
                                调试颜色输入激活 = bool(调试id == "调试_血条颜色_hex")
                                if 调试颜色输入激活:
                                    _同步调试颜色文本()
                                已命中调试项 = True
                                break
                        if 已命中调试项:
                            拖拽中 = False
                            拖拽已记录撤销 = False
                            continue
                        if 行rect表.get("force_show") and 行rect表[
                            "force_show"
                        ].collidepoint(事件.pos):
                            选中调试项id = ""
                            强制显示 = not bool(强制显示)
                            _保存调试设置()
                        elif 行rect表.get("show_all_borders") and 行rect表[
                            "show_all_borders"
                        ].collidepoint(事件.pos):
                            选中调试项id = ""
                            显示全部边框 = not bool(显示全部边框)
                            _保存调试设置()
                        elif 行rect表.get("full_blood_fx") and 行rect表[
                            "full_blood_fx"
                        ].collidepoint(事件.pos):
                            选中调试项id = ""
                            模拟满血暴走 = not bool(模拟满血暴走)
                            _保存调试设置()
                        elif 行rect表.get("normal_hit_fx") and 行rect表[
                            "normal_hit_fx"
                        ].collidepoint(事件.pos):
                            选中调试项id = ""
                            模拟普通击中特效 = not bool(模拟普通击中特效)
                            _保存调试设置()
                        elif 行rect表.get("hold_loop") and 行rect表[
                            "hold_loop"
                        ].collidepoint(事件.pos):
                            选中调试项id = ""
                            模拟hold击中特效循环 = not bool(模拟hold击中特效循环)
                            _保存调试设置()
                        elif 行rect表.get("simulate_hold_hit") and 行rect表[
                            "simulate_hold_hit"
                        ].collidepoint(事件.pos):
                            选中调试项id = ""
                            模拟长按击中 = not bool(模拟长按击中)
                            _保存调试设置()
                        拖拽中 = False
                        拖拽已记录撤销 = False
                        continue

                    图层面板rect, 右横杠rect, 右尾巴rect, 图层行rect表, 图层眼睛rect表, _ = (
                        _计算右侧图层面板布局()
                    )
                    if bool(右侧面板折叠):
                        if 右尾巴rect.collidepoint(事件.pos):
                            右侧面板折叠 = False
                            _保存调试设置()
                            拖拽中 = False
                            拖拽已记录撤销 = False
                            continue
                    elif 右横杠rect.collidepoint(事件.pos):
                        右侧面板折叠 = True
                        _保存调试设置()
                        拖拽中 = False
                        拖拽已记录撤销 = False
                        continue

                    if (not bool(右侧面板折叠)) and 图层面板rect.collidepoint(事件.pos):
                        for 控件id, 眼睛rect in 图层眼睛rect表.items():
                            if 眼睛rect.collidepoint(事件.pos):
                                _切换控件可见(控件id)
                                break
                        else:
                            for 控件id, 行rect in 图层行rect表.items():
                                if 行rect.collidepoint(事件.pos):
                                    选中控件id = str(控件id or "")
                                    选中调试项id = ""
                                    break
                        拖拽中 = False
                        拖拽已记录撤销 = False
                        continue

                    鼠标点 = (int(事件.pos[0]), int(事件.pos[1]))
                    上下文 = _构建调试上下文(
                        强制显示,
                        当前秒,
                        头像图,
                        段位图,
                        玩家昵称,
                        调试歌曲名,
                        调试歌曲星级文本,
                        屏幕.get_size(),
                        布局管理器,
                        模拟普通击中特效,
                        模拟hold击中特效循环,
                        模拟满血暴走,
                        调试血量显示,
                        调试血条颜色,
                        调试血条亮度,
                        调试血条不透明度,
                        调试血条晃荡速度,
                        调试血条晃荡幅度,
                        调试暴走血条速度,
                        调试头像框特效速度,
                        模拟调速倍率=模拟谱面调速倍率,
                        模拟隐藏模式=模拟谱面隐藏模式,
                        模拟轨迹模式=模拟谱面轨迹模式,
                        模拟方向模式=模拟谱面方向模式,
                        模拟大小模式=模拟谱面大小模式,
                        半隐入口比例=模拟半隐入口比例,
                        摇摆幅度倍率=模拟摇摆幅度倍率,
                        旋转速度度每秒=模拟旋转速度度每秒,
                        隐藏控件ids=sorted(list(隐藏控件ids)),
                        圆环频谱对象=调试圆环频谱对象,
                        调试暴走血条不透明度=调试暴走血条不透明度,
                        调试暴走血条羽化=调试暴走血条羽化,
                        圆环频谱启用旋转=圆环频谱启用旋转,
                        圆环频谱背景板转速=圆环频谱背景板转速,
                        圆环频谱变化落差=圆环频谱变化落差,
                        圆环频谱线条数量=圆环频谱线条数量,
                        圆环频谱线条粗细=圆环频谱线条粗细,
                        圆环频谱线条间隔=圆环频谱线条间隔,
                    )
                    _同步模拟hold锚点(上下文)
                    _同步血条填充锚点(上下文)
                    选中控件id = 布局管理器.命中控件(
                        鼠标点, 屏幕.get_size(), 上下文, 仅绘制根id=None
                    )
                    选中调试项id = ""
                    文本控件id = _按点命中文本控件(
                        鼠标点, 上下文, 关联控件id=str(选中控件id or "")
                    )
                    if 文本控件id:
                        选中控件id = str(文本控件id)
                        _打开文本字间距面板(str(文本控件id), 鼠标点)
                    elif _是否文本控件(str(选中控件id or "")):
                        _打开文本字间距面板(str(选中控件id or ""), 鼠标点)
                    else:
                        _关闭文本字间距面板()
                    拖拽中 = bool(选中控件id)
                    拖拽已记录撤销 = False
                    上次鼠标 = 鼠标点
                if 事件.button == 4:
                    if bool(文本字间距面板开启):
                        面板, _, _, _ = _计算文本字间距面板布局()
                        if isinstance(面板, pygame.Rect) and 面板.collidepoint(pygame.mouse.get_pos()):
                            if _是否文本控件(文本字间距目标控件id):
                                _记录撤销()
                                布局管理器.改字间距(str(文本字间距目标控件id), +1)
                            continue
                    图层面板rect, _, _, _, _, 可视项 = _计算右侧图层面板布局()
                    if (
                        (not bool(右侧面板折叠))
                        and 图层面板rect.collidepoint(pygame.mouse.get_pos())
                        and len(可视项) > 0
                    ):
                        图层面板滚动 = max(0, int(图层面板滚动) - 1)
                    else:
                        _处理滚轮(+1)
                if 事件.button == 5:
                    if bool(文本字间距面板开启):
                        面板, _, _, _ = _计算文本字间距面板布局()
                        if isinstance(面板, pygame.Rect) and 面板.collidepoint(pygame.mouse.get_pos()):
                            if _是否文本控件(文本字间距目标控件id):
                                _记录撤销()
                                布局管理器.改字间距(str(文本字间距目标控件id), -1)
                            continue
                    图层面板rect, _, _, _, _, 可视项 = _计算右侧图层面板布局()
                    if (
                        (not bool(右侧面板折叠))
                        and 图层面板rect.collidepoint(pygame.mouse.get_pos())
                        and len(可视项) > 0
                    ):
                        图层面板滚动 = int(图层面板滚动) + 1
                    else:
                        _处理滚轮(-1)

            if 事件.type == pygame.MOUSEBUTTONUP:
                if 事件.button == 1:
                    拖拽中 = False
                    拖拽已记录撤销 = False

            if 事件.type == pygame.MOUSEMOTION:
                if 拖拽中 and 选中控件id:
                    当前鼠标 = (int(事件.pos[0]), int(事件.pos[1]))
                    dx = float(当前鼠标[0] - 上次鼠标[0])
                    dy = float(当前鼠标[1] - 上次鼠标[1])
                    上次鼠标 = 当前鼠标
                    if (not 拖拽已记录撤销) and (dx != 0.0 or dy != 0.0):
                        _记录撤销()
                        拖拽已记录撤销 = True
                    布局管理器.移动控件(选中控件id, dx, dy, 屏幕.get_size())

            if 事件.type == pygame.MOUSEWHEEL:
                if bool(文本字间距面板开启):
                    面板, _, _, _ = _计算文本字间距面板布局()
                    if (
                        isinstance(面板, pygame.Rect)
                        and 面板.collidepoint(pygame.mouse.get_pos())
                        and int(getattr(事件, "y", 0)) != 0
                    ):
                        if _是否文本控件(文本字间距目标控件id):
                            _记录撤销()
                            布局管理器.改字间距(
                                str(文本字间距目标控件id), int(getattr(事件, "y", 0))
                            )
                        continue
                图层面板rect, _, _, _, _, 可视项 = _计算右侧图层面板布局()
                if (
                    (not bool(右侧面板折叠))
                    and 图层面板rect.collidepoint(pygame.mouse.get_pos())
                    and len(可视项) > 0
                ):
                    if int(事件.y) > 0:
                        图层面板滚动 = max(0, int(图层面板滚动) - 1)
                    elif int(事件.y) < 0:
                        图层面板滚动 = int(图层面板滚动) + 1
                else:
                    _处理滚轮(int(事件.y))

        _绘制背景()

        上下文 = _构建调试上下文(
            强制显示,
            当前秒,
            头像图,
            段位图,
            玩家昵称,
            调试歌曲名,
            调试歌曲星级文本,
            屏幕.get_size(),
            布局管理器,
            模拟普通击中特效,
            模拟hold击中特效循环,
            模拟满血暴走,
            调试血量显示,
            调试血条颜色,
            调试血条亮度,
            调试血条不透明度,
            调试血条晃荡速度,
            调试血条晃荡幅度,
            调试暴走血条速度,
            调试头像框特效速度,
            模拟调速倍率=模拟谱面调速倍率,
            模拟隐藏模式=模拟谱面隐藏模式,
            模拟轨迹模式=模拟谱面轨迹模式,
            模拟方向模式=模拟谱面方向模式,
            模拟大小模式=模拟谱面大小模式,
            模拟双踏板模式=模拟双踏板模式,
            半隐入口比例=模拟半隐入口比例,
            摇摆幅度倍率=模拟摇摆幅度倍率,
            旋转速度度每秒=模拟旋转速度度每秒,
            隐藏控件ids=sorted(list(隐藏控件ids)),
            圆环频谱对象=调试圆环频谱对象,
            调试暴走血条不透明度=调试暴走血条不透明度,
            调试暴走血条羽化=调试暴走血条羽化,
            圆环频谱启用旋转=圆环频谱启用旋转,
            圆环频谱背景板转速=圆环频谱背景板转速,
            圆环频谱变化落差=圆环频谱变化落差,
            圆环频谱线条数量=圆环频谱线条数量,
            圆环频谱线条粗细=圆环频谱线条粗细,
            圆环频谱线条间隔=圆环频谱线条间隔,
        )
        _同步模拟hold锚点(上下文)
        _同步血条填充锚点(上下文)
        _注入模拟命中特效(上下文, 当前秒)
        调试 = 调试状态(
            显示全部边框=bool(显示全部边框), 选中控件id=str(选中控件id or "")
        )

        _绘制模拟循环箭头(上下文, 当前秒)
        try:
            布局管理器.绘制(屏幕, 上下文, 皮肤包, 调试=调试, 仅绘制根id=None)
        except Exception:
            pass

        _绘制模拟长按击中(上下文, 当前秒)
        _绘制模拟面板()
        _绘制左下面板()
        _绘制右侧图层面板()
        _绘制文本字间距面板()

        pygame.display.flip()


if __name__ == "__main__":
    主函数()
