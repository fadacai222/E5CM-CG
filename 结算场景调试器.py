import json
import os
import sys
from typing import Dict, List, Tuple

import pygame

from core.常量与路径 import 默认资源路径
from core.工具 import 获取字体
from core.音频 import 音乐管理
from scenes.场景_结算 import 场景_结算


def _项目根() -> str:
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.getcwd()


def _设置文件() -> str:
    return os.path.join(_项目根(), "json", "结算调试器_设置.json")


def _默认载荷() -> Dict[str, object]:
    根 = _项目根()
    背景 = os.path.join(根, "冷资源", "backimages", "选歌界面.png")
    封面 = os.path.join(
        根,
        "songs",
        "竞速",
        "混音",
        "SPEED_REMIX#Korean_Girls_Pop_Song_Party#7",
        "bann.jpg",
    )
    return {
        "背景路径": 背景 if os.path.isfile(背景) else "",
        "封面路径": 封面 if os.path.isfile(封面) else "",
        "曲目名": "Korean Girls Pop Song Party",
        "星级": 7,
        "perfect数": 832,
        "cool数": 832,
        "good数": 832,
        "miss数": 832,
        "本局最大combo": 832,
        "本局最高分": 47764800,
        "百分比数值": 100.0,
        "评级": "s",
        "全连": True,
        "模式": "竞速",
        "类型": "竞速",
        "选歌原始索引": 0,
    }


def _读设置() -> Dict[str, object]:
    路径 = _设置文件()
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


def _写设置(数据: Dict[str, object]) -> bool:
    try:
        路径 = _设置文件()
        os.makedirs(os.path.dirname(路径), exist_ok=True)
        with open(路径, "w", encoding="utf-8") as f:
            json.dump(dict(数据 or {}), f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _计算面板矩形(屏宽: int, 屏高: int) -> pygame.Rect:
    面板尺寸 = int(max(360, min(int(屏高 * 0.82), int(屏宽 * 0.48), 700)))
    return pygame.Rect(
        max(28, int(屏宽 * 0.06)),
        max(20, (屏高 - 面板尺寸) // 2),
        面板尺寸,
        面板尺寸,
    )


def _构建命名框(面板: pygame.Rect) -> List[Tuple[str, pygame.Rect]]:
    def px(x: float) -> int:
        return 面板.left + int(面板.w * (float(x) / 512.0))

    def py(y: float) -> int:
        return 面板.top + int(面板.h * (float(y) / 512.0))

    命名框: List[Tuple[str, pygame.Rect]] = []
    命名框.append(("结算面板", 面板.copy()))
    命名框.append(
        ("封面区", pygame.Rect(px(58), py(138), px(184) - px(58), py(272) - py(138)))
    )
    命名框.append(
        ("星级行", pygame.Rect(px(46), py(296), px(214) - px(46), py(322) - py(296)))
    )
    命名框.append(
        ("歌名行", pygame.Rect(px(46), py(332), px(214) - px(46), py(370) - py(332)))
    )
    命名框.append(
        (
            "右侧统计",
            pygame.Rect(px(256), py(132), px(452) - px(256), py(410) - py(132)),
        )
    )
    命名框.append(
        ("总分区", pygame.Rect(px(118), py(420), px(468) - px(118), py(480) - py(420)))
    )
    命名框.append(
        ("评级区", pygame.Rect(px(28), py(392), px(188) - px(28), py(505) - py(392)))
    )
    命名框.append(
        ("顶部状态", pygame.Rect(px(188), py(52), px(388) - px(188), py(112) - py(52)))
    )
    命名框.append(
        ("新纪录标", pygame.Rect(px(370), py(10), px(514) - px(370), py(96) - py(10)))
    )
    return 命名框


def 主函数():
    根 = _项目根()
    if 根 not in sys.path:
        sys.path.insert(0, 根)

    pygame.init()
    pygame.display.set_caption("结算场景调试器")
    屏幕 = pygame.display.set_mode((1366, 768), pygame.RESIZABLE)
    时钟 = pygame.time.Clock()

    资源 = 默认资源路径()
    音乐 = 音乐管理()
    上下文 = {
        "屏幕": 屏幕,
        "时钟": 时钟,
        "资源": 资源,
        "音乐": 音乐,
        "字体": {
            "大字": 获取字体(64),
            "中字": 获取字体(30),
            "小字": 获取字体(20),
            "投币_credit字": 获取字体(28),
        },
        "状态": {"投币数": 0},
    }

    默认载荷 = _默认载荷()
    设置数据 = _读设置()
    载荷 = dict(默认载荷)
    for k in list(默认载荷.keys()):
        if k in 设置数据:
            载荷[k] = 设置数据.get(k)

    场景 = 场景_结算(上下文)
    场景.进入(dict(载荷))

    提示字体 = 获取字体(18)
    显示命名框 = bool(设置数据.get("调试_显示命名框", True))
    显示图层面板 = bool(设置数据.get("调试_显示图层面板", True))
    图层可见设置 = 设置数据.get("调试_图层可见", {})
    图层可见: Dict[str, bool] = (
        dict(图层可见设置) if isinstance(图层可见设置, dict) else {}
    )
    图层滚动 = 0
    选中索引 = 0
    字段列表: List[Tuple[str, int]] = [
        ("perfect数", 1),
        ("cool数", 1),
        ("good数", 1),
        ("miss数", 1),
        ("本局最大combo", 1),
        ("本局最高分", 1000),
        ("百分比数值", 1),
        ("星级", 1),
    ]

    def _重进场():
        nonlocal 场景
        try:
            场景.退出()
        except Exception:
            pass
        场景 = 场景_结算(上下文)
        场景.进入(dict(载荷))

    def _取当前图层项() -> List[Tuple[str, pygame.Rect]]:
        面板 = _计算面板矩形(*屏幕.get_size())
        项 = _构建命名框(面板)
        if not isinstance(项, list):
            return []
        return [(str(n), r) for n, r in 项 if isinstance(r, pygame.Rect)]

    def _确保图层可见键():
        当前名 = [n for n, _ in _取当前图层项()]
        for n in 当前名:
            if n not in 图层可见:
                图层可见[n] = True

    def _计算图层面板交互区域():
        nonlocal 图层滚动
        if not bool(显示图层面板):
            return None, {}, {}, []
        屏宽, 屏高 = 屏幕.get_size()
        面板宽 = int(max(220, min(340, 屏宽 * 0.23)))
        面板高 = int(max(220, min(int(屏高 * 0.55), 屏高 - 24)))
        面板 = pygame.Rect(
            int(屏宽 - 面板宽 - 12), int(屏高 - 面板高 - 12), int(面板宽), int(面板高)
        )
        行高 = 28
        头高 = 54
        可视行数 = int(max(3, (面板.h - 头高 - 12) // 行高))
        图层项 = _取当前图层项()
        最大滚动 = int(max(0, len(图层项) - 可视行数))
        图层滚动 = int(max(0, min(图层滚动, 最大滚动)))
        可视项 = 图层项[图层滚动 : 图层滚动 + 可视行数]
        行rect表: Dict[str, pygame.Rect] = {}
        眼睛rect表: Dict[str, pygame.Rect] = {}
        for i, (名称, _) in enumerate(可视项):
            y = int(面板.y + 头高 + i * 行高)
            行rect = pygame.Rect(
                int(面板.x + 8), int(y), int(面板.w - 16), int(行高 - 2)
            )
            眼睛rect = pygame.Rect(
                int(行rect.x + 6), int(行rect.y + 4), 22, int(行rect.h - 8)
            )
            行rect表[名称] = 行rect
            眼睛rect表[名称] = 眼睛rect
        return 面板, 行rect表, 眼睛rect表, 可视项

    运行中 = True
    while 运行中:
        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                运行中 = False
                break
            if 事件.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if 事件.key == pygame.K_ESCAPE:
                    运行中 = False
                    break
                if 事件.key == pygame.K_SPACE:
                    _重进场()
                    continue
                if 事件.key == pygame.K_b:
                    显示命名框 = not bool(显示命名框)
                    continue
                if 事件.key == pygame.K_l:
                    显示图层面板 = not bool(显示图层面板)
                    continue
                if 事件.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                    保存数据 = dict(载荷)
                    保存数据["调试_显示命名框"] = bool(显示命名框)
                    保存数据["调试_显示图层面板"] = bool(显示图层面板)
                    保存数据["调试_图层可见"] = dict(图层可见)
                    _写设置(保存数据)
                    continue
                if 事件.key == pygame.K_TAB:
                    选中索引 = (
                        选中索引 + (-1 if (mods & pygame.KMOD_SHIFT) else 1)
                    ) % len(字段列表)
                    continue
                if 事件.key in (
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                    pygame.K_UP,
                    pygame.K_DOWN,
                ):
                    字段名, 步长 = 字段列表[选中索引]
                    方向 = 0
                    if 事件.key in (pygame.K_RIGHT, pygame.K_UP):
                        方向 = 1
                    elif 事件.key in (pygame.K_LEFT, pygame.K_DOWN):
                        方向 = -1
                    倍率 = 10 if (mods & pygame.KMOD_SHIFT) else 1
                    调整 = int(步长 * 倍率 * 方向)
                    if 字段名 == "百分比数值":
                        try:
                            当前 = float(载荷.get(字段名, 0.0) or 0.0)
                        except Exception:
                            当前 = 0.0
                        载荷[字段名] = max(0.0, min(100.0, 当前 + float(调整)))
                    elif 字段名 == "星级":
                        try:
                            当前 = int(载荷.get(字段名, 0) or 0)
                        except Exception:
                            当前 = 0
                        载荷[字段名] = max(0, min(99, 当前 + 调整))
                    else:
                        try:
                            当前 = int(载荷.get(字段名, 0) or 0)
                        except Exception:
                            当前 = 0
                        载荷[字段名] = max(0, 当前 + 调整)
                    _重进场()
                    continue
                if 事件.key == pygame.K_r:
                    try:
                        miss = int(载荷.get("miss数", 0) or 0)
                    except Exception:
                        miss = 0
                    载荷["全连"] = bool(miss == 0)
                    _重进场()
                    continue
                if 事件.key == pygame.K_1:
                    载荷["评级"] = "f"
                    _重进场()
                    continue
                if 事件.key == pygame.K_2:
                    载荷["评级"] = "a"
                    _重进场()
                    continue
                if 事件.key == pygame.K_3:
                    载荷["评级"] = "s"
                    _重进场()
                    continue
            if (
                事件.type == pygame.MOUSEBUTTONDOWN
                and int(getattr(事件, "button", 0)) == 1
            ):
                _确保图层可见键()
                面板rect, 行rect表, 眼睛rect表, _ = _计算图层面板交互区域()
                if isinstance(面板rect, pygame.Rect) and 面板rect.collidepoint(
                    事件.pos
                ):
                    for 名称, 眼睛rect in 眼睛rect表.items():
                        if 眼睛rect.collidepoint(事件.pos):
                            图层可见[名称] = not bool(图层可见.get(名称, True))
                            break
                    continue
            if 事件.type == pygame.MOUSEWHEEL:
                面板rect, _, _, 可视项 = _计算图层面板交互区域()
                if (
                    isinstance(面板rect, pygame.Rect)
                    and 面板rect.collidepoint(pygame.mouse.get_pos())
                    and 可视项
                ):
                    if int(getattr(事件, "y", 0)) > 0:
                        图层滚动 = max(0, int(图层滚动) - 1)
                    elif int(getattr(事件, "y", 0)) < 0:
                        图层滚动 = int(图层滚动) + 1
                    continue

            try:
                ret = 场景.处理事件(事件)
                if isinstance(ret, dict) and str(ret.get("切换到", "") or ""):
                    _重进场()
            except Exception:
                pass

        if not 运行中:
            break

        try:
            场景.更新()
            场景.绘制()
        except Exception:
            pass

        _确保图层可见键()
        if 显示命名框:
            try:
                面板 = _计算面板矩形(*屏幕.get_size())
                for 名称, rect in _构建命名框(面板):
                    if not bool(图层可见.get(str(名称), True)):
                        continue
                    pygame.draw.rect(屏幕, (255, 235, 80), rect, 2)
                    t = 提示字体.render(str(名称), True, (255, 255, 180))
                    屏幕.blit(t, (rect.x + 2, max(0, rect.y - t.get_height() - 1)))
            except Exception:
                pass

        if 显示图层面板:
            try:
                面板rect, 行rect表, 眼睛rect表, 可视项 = _计算图层面板交互区域()
                if isinstance(面板rect, pygame.Rect):
                    背板 = pygame.Surface((面板rect.w, 面板rect.h), pygame.SRCALPHA)
                    背板.fill((8, 12, 22, 190))
                    屏幕.blit(背板, 面板rect.topleft)
                    pygame.draw.rect(
                        屏幕, (120, 150, 220), 面板rect, width=1, border_radius=8
                    )
                    标题图 = 提示字体.render("图层", True, (255, 245, 170))
                    屏幕.blit(标题图, (面板rect.x + 10, 面板rect.y + 8))
                    提示图 = 提示字体.render("点小眼睛开关", True, (190, 210, 240))
                    屏幕.blit(提示图, (面板rect.x + 10, 面板rect.y + 28))
                    for 名称, _ in 可视项:
                        行rect = 行rect表.get(名称)
                        眼睛rect = 眼睛rect表.get(名称)
                        if 行rect is None or 眼睛rect is None:
                            continue
                        pygame.draw.rect(屏幕, (20, 30, 48), 行rect, border_radius=6)
                        pygame.draw.rect(
                            屏幕, (64, 84, 118), 行rect, width=1, border_radius=6
                        )
                        pygame.draw.rect(
                            屏幕, (210, 220, 232), 眼睛rect, width=1, border_radius=8
                        )
                        可见 = bool(图层可见.get(str(名称), True))
                        if 可见:
                            pygame.draw.ellipse(
                                屏幕,
                                (110, 220, 170),
                                眼睛rect.inflate(-6, -8),
                                width=2,
                            )
                        else:
                            pygame.draw.line(
                                屏幕,
                                (235, 80, 80),
                                (眼睛rect.x + 3, 眼睛rect.bottom - 3),
                                (眼睛rect.right - 3, 眼睛rect.y + 3),
                                2,
                            )
                        文本图 = 提示字体.render(str(名称), True, (235, 240, 252))
                        屏幕.blit(文本图, (眼睛rect.right + 8, 行rect.y + 4))
            except Exception:
                pass

        try:
            # 左上调试提示
            lines = [
                "SPACE 重播结算动画  TAB 切字段  方向键改值  Shift*10",
                "B 命名框  L 图层面板  Ctrl+S 保存  R 同步全连  1/2/3 切评级(F/A/S)",
            ]
            名称, _ = 字段列表[选中索引]
            当前值 = 载荷.get(名称, 0)
            lines.append(f"当前字段: {名称} = {当前值}")
            y = 8
            for ln in lines:
                s = 提示字体.render(ln, True, (245, 245, 255)).convert_alpha()
                bg = pygame.Surface(
                    (s.get_width() + 10, s.get_height() + 4), pygame.SRCALPHA
                )
                bg.fill((0, 0, 0, 150))
                屏幕.blit(bg, (8, y))
                屏幕.blit(s, (13, y + 2))
                y += s.get_height() + 6
        except Exception:
            pass

        pygame.display.flip()
        时钟.tick(120)

    try:
        场景.退出()
    except Exception:
        pass
    try:
        音乐.停止()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    主函数()
