import json
import math
import os
import sys
import time
from typing import Any, Dict, Optional, Tuple

import pygame


def _项目根() -> str:
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.getcwd()


def _设置路径(根: str) -> str:
    return os.path.join(根, "json", "谱面布局调试器_设置.json")


def _默认音频路径(根: str) -> str:
    return os.path.join(
        根,
        "songs",
        "花式",
        "club",
        "FANCY_CLUB#boom_1710#4",
        "boom_1710.mp3",
    )


def _取字体(根: str, 字号: int) -> pygame.font.Font:
    pygame.font.init()
    路径 = os.path.join(根, "冷资源", "字体", "方正黑体简体.TTF")
    if os.path.isfile(路径):
        try:
            return pygame.font.Font(路径, int(字号))
        except Exception:
            pass
    return pygame.font.Font(None, int(字号))


def _安全读json(路径: str) -> Dict[str, Any]:
    if not os.path.isfile(路径):
        return {}
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码) as f:
                数据 = json.load(f)
            return dict(数据) if isinstance(数据, dict) else {}
        except Exception:
            continue
    return {}


def _安全写json(路径: str, 数据: Dict[str, Any]) -> bool:
    try:
        os.makedirs(os.path.dirname(路径), exist_ok=True)
        with open(路径, "w", encoding="utf-8") as f:
            json.dump(dict(数据 or {}), f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _取布局中的stage矩形(
    布局管理器: Any, 屏幕尺寸: Tuple[int, int], 当前秒: float
) -> Tuple[pygame.Rect, pygame.Rect]:
    默认 = pygame.Rect(int(屏幕尺寸[0] * 0.76), 8, 180, 170)
    try:
        上下文 = {
            "_调试强制显示": True,
            "_调试隐藏控件ids": [],
            "当前谱面秒": float(当前秒),
            "调试_时间秒": float(当前秒),
            "圆环频谱_启用": True,
            "玩家序号": 1,
            "当前关卡": 1,
            "显示_分数": 0,
            "倒计时": "01:23",
            "血量最终显示": 0.5,
            "歌曲名": "boom_1710",
            "歌曲星级文本": "4★",
        }
        渲染表 = 布局管理器._构建渲染清单(  # pylint: disable=protected-access
            屏幕尺寸,
            上下文,
            仅绘制根id=None,
            仅绘制控件ids=["Stage背景", "Stage圆环频谱"],
        )
        背景 = None
        频谱 = None
        for 项 in 渲染表:
            if str(项.get("id") or "") == "Stage背景":
                背景 = 项.get("rect")
            elif str(项.get("id") or "") == "Stage圆环频谱":
                频谱 = 项.get("rect")
        背景rect = 背景.copy() if isinstance(背景, pygame.Rect) else 默认.copy()
        频谱rect = 频谱.copy() if isinstance(频谱, pygame.Rect) else 背景rect.copy()
        return 背景rect, 频谱rect
    except Exception:
        return 默认.copy(), 默认.copy()


def 主函数():
    根 = _项目根()
    if 根 not in sys.path:
        sys.path.insert(0, 根)

    from ui.圆环频谱叠加 import 圆环频谱舞台装饰
    from ui.调试_谱面渲染器_渲染控件 import 谱面渲染器布局管理器

    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    pygame.display.set_caption("圆环频谱调试器")
    屏幕 = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    时钟 = pygame.time.Clock()
    字体 = _取字体(根, 20)
    小字 = _取字体(根, 16)

    设置文件 = _设置路径(根)
    设置 = _安全读json(设置文件)

    def _取值(键: str, 默认: Any) -> Any:
        return 设置.get(键, 默认)

    频谱旋转启用 = bool(_取值("圆环频谱启用旋转", False))
    背景板转速 = float(_取值("圆环频谱背景板转速", 36.0))
    变化落差 = float(_取值("圆环频谱变化落差", 1.0))
    线条数量 = int(_取值("圆环频谱线条数量", 200))
    线条粗细 = int(_取值("圆环频谱线条粗细", 2))
    线条间隔 = int(_取值("圆环频谱线条间隔", 1))
    最大长度 = int(_取值("圆环频谱最大长度", 40))

    频谱旋转启用 = bool(频谱旋转启用)
    背景板转速 = float(max(-360.0, min(360.0, 背景板转速)))
    变化落差 = float(max(0.0, min(2.0, 变化落差)))
    线条数量 = int(max(24, min(720, 线条数量)))
    线条粗细 = int(max(1, min(12, 线条粗细)))
    线条间隔 = int(max(1, min(8, 线条间隔)))
    最大长度 = int(max(6, min(96, 最大长度)))

    音频路径 = _默认音频路径(根)
    if os.path.isfile(音频路径):
        try:
            pygame.mixer.music.load(音频路径)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    board路径 = os.path.join(根, "UI-img", "游戏界面", "血条", "board.png")
    board原图: Optional[pygame.Surface] = None
    if os.path.isfile(board路径):
        try:
            board原图 = pygame.image.load(board路径).convert_alpha()
        except Exception:
            board原图 = None

    布局路径 = os.path.join(根, "json", "谱面渲染器_布局.json")
    布局管理器 = 谱面渲染器布局管理器(布局路径)

    频谱 = 圆环频谱舞台装饰()
    try:
        频谱.设置贴边形状文件("UI-img/游戏界面/血条/board.png")
    except Exception:
        pass
    if os.path.isfile(音频路径):
        try:
            频谱.绑定音频(音频路径)
        except Exception:
            pass

    控件索引 = 0
    控件项 = [
        "频谱旋转",
        "背景板转速",
        "变化落差",
        "线条数量",
        "线条粗细",
        "线条间隔",
        "最大长度",
    ]

    def _保存():
        设置["圆环频谱启用旋转"] = bool(频谱旋转启用)
        设置["圆环频谱背景板转速"] = float(背景板转速)
        设置["圆环频谱变化落差"] = float(变化落差)
        设置["圆环频谱线条数量"] = int(线条数量)
        设置["圆环频谱线条粗细"] = int(线条粗细)
        设置["圆环频谱线条间隔"] = int(线条间隔)
        设置["圆环频谱最大长度"] = int(最大长度)
        _安全写json(设置文件, 设置)

    def _应用到频谱():
        try:
            频谱.设置调试外延最大长度(int(最大长度))
        except Exception:
            pass
        try:
            频谱.设置调试频谱参数(
                启用旋转=bool(频谱旋转启用),
                变化落差=float(变化落差),
                线条数量=int(线条数量),
                线条粗细=int(线条粗细),
                线条间隔=int(线条间隔),
            )
        except Exception:
            pass

    _应用到频谱()
    _保存()

    累计角度 = 0.0
    上一秒 = time.perf_counter()
    状态提示 = ""
    状态提示截止 = 0.0

    def _提示(msg: str):
        nonlocal 状态提示, 状态提示截止
        状态提示 = str(msg or "")
        状态提示截止 = time.perf_counter() + 1.2

    运行 = True
    while 运行:
        当前系统秒 = time.perf_counter()
        dt = float(max(0.0, min(0.1, 当前系统秒 - 上一秒)))
        上一秒 = 当前系统秒
        累计角度 = float((累计角度 + 背景板转速 * dt) % 360.0)

        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                运行 = False
                break
            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    运行 = False
                    break
                if 事件.key == pygame.K_UP:
                    控件索引 = (控件索引 - 1) % len(控件项)
                    continue
                if 事件.key == pygame.K_DOWN:
                    控件索引 = (控件索引 + 1) % len(控件项)
                    continue
                if 事件.key == pygame.K_s:
                    _保存()
                    _提示("参数已保存")
                    continue
                if 事件.key == pygame.K_SPACE:
                    try:
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.pause()
                            _提示("音频已暂停")
                        else:
                            pygame.mixer.music.unpause()
                            _提示("音频已继续")
                    except Exception:
                        pass
                    continue
                if 事件.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    方向 = -1 if 事件.key == pygame.K_LEFT else 1
                    大步进 = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                    项 = 控件项[int(控件索引)]
                    if 项 == "频谱旋转":
                        频谱旋转启用 = not bool(频谱旋转启用)
                    elif 项 == "背景板转速":
                        步进 = 5.0 if 大步进 else 1.0
                        背景板转速 = float(max(-360.0, min(360.0, 背景板转速 + 方向 * 步进)))
                    elif 项 == "变化落差":
                        步进 = 0.1 if 大步进 else 0.02
                        变化落差 = float(max(0.0, min(2.0, 变化落差 + 方向 * 步进)))
                    elif 项 == "线条数量":
                        步进 = 10 if 大步进 else 2
                        线条数量 = int(max(24, min(720, 线条数量 + 方向 * 步进)))
                    elif 项 == "线条粗细":
                        步进 = 2 if 大步进 else 1
                        线条粗细 = int(max(1, min(12, 线条粗细 + 方向 * 步进)))
                    elif 项 == "线条间隔":
                        线条间隔 = int(max(1, min(8, 线条间隔 + 方向)))
                    elif 项 == "最大长度":
                        步进 = 8 if 大步进 else 1
                        最大长度 = int(max(6, min(96, 最大长度 + 方向 * 步进)))
                    _应用到频谱()
                    _保存()
                    continue

        屏幕.fill((8, 10, 14))
        当前谱面秒 = 0.0
        try:
            pos = int(pygame.mixer.music.get_pos())
            当前谱面秒 = float(max(0.0, pos / 1000.0))
        except Exception:
            当前谱面秒 = float(max(0.0, time.perf_counter() % 99999.0))

        背景rect, 频谱rect = _取布局中的stage矩形(布局管理器, 屏幕.get_size(), 当前谱面秒)

        if isinstance(board原图, pygame.Surface):
            try:
                图 = pygame.transform.smoothscale(board原图, (int(max(2, 背景rect.w)), int(max(2, 背景rect.h)))).convert_alpha()
                if abs(float(累计角度)) > 0.001:
                    图 = pygame.transform.rotozoom(图, -float(累计角度), 1.0).convert_alpha()
                x = int(背景rect.centerx - 图.get_width() // 2)
                y = int(背景rect.centery - 图.get_height() // 2)
                屏幕.blit(图, (x, y))
            except Exception:
                pass
        else:
            pygame.draw.circle(屏幕, (55, 45, 85), 背景rect.center, int(max(20, min(背景rect.w, 背景rect.h) * 0.45)))

        try:
            频谱.设置贴边形状旋转角度(math.radians(float(累计角度)))
            频谱.更新并绘制(
                屏幕=屏幕,
                目标矩形=频谱rect,
                当前播放秒=float(当前谱面秒),
            )
        except Exception:
            pass

        面板 = pygame.Rect(12, 12, 320, 280)
        面板底 = pygame.Surface((面板.w, 面板.h), pygame.SRCALPHA)
        面板底.fill((6, 10, 18, 200))
        屏幕.blit(面板底, 面板.topleft)
        pygame.draw.rect(屏幕, (90, 130, 190), 面板, 1, border_radius=6)

        行 = [
            f"频谱旋转: {'开' if 频谱旋转启用 else '关'}",
            f"背景板转速: {背景板转速:.2f}",
            f"变化落差: {变化落差:.2f}",
            f"线条数量: {线条数量}",
            f"线条粗细: {线条粗细}",
            f"线条间隔: {线条间隔}",
            f"最大长度: {最大长度}",
            "",
            "UP/DOWN 选中  LEFT/RIGHT 调整",
            "SHIFT+左右 大步进  S 保存  ESC 退出",
        ]
        y = int(面板.y + 14)
        for i, 文本 in enumerate(行):
            色 = (230, 236, 245)
            if i == int(控件索引):
                色 = (255, 220, 90)
            图 = 小字.render(str(文本), True, 色)
            屏幕.blit(图, (int(面板.x + 12), y))
            y += int(图.get_height() + 6)

        标题 = 字体.render("圆环频谱调试器", True, (140, 235, 255))
        屏幕.blit(标题, (12, int(面板.bottom + 12)))

        if 状态提示 and 当前系统秒 <= 状态提示截止:
            提示图 = 小字.render(状态提示, True, (255, 216, 120))
            屏幕.blit(提示图, (12, int(面板.bottom + 44)))

        pygame.display.flip()
        时钟.tick(120)

    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    主函数()
