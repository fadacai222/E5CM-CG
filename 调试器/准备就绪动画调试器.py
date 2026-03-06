import os
from typing import Dict, List, Optional, Tuple

import pygame

import 谱面布局调试器 as 布局调试器
from core.工具 import 获取字体
from ui.准备就绪动画 import (
    读取准备动画设置,
    保存准备动画设置,
    加载准备动画图片,
    计算准备动画时间轴,
    绘制准备就绪动画,
)
from ui.调试_谱面渲染器_渲染控件 import 调试状态, 谱面渲染器布局管理器


def _画cover(图: Optional[pygame.Surface], 尺寸: Tuple[int, int]) -> Optional[pygame.Surface]:
    if 图 is None:
        return None
    w, h = int(max(1, 尺寸[0])), int(max(1, 尺寸[1]))
    try:
        ow, oh = 图.get_size()
        比例 = max(float(w) / float(max(1, ow)), float(h) / float(max(1, oh)))
        nw = max(2, int(ow * 比例))
        nh = max(2, int(oh * 比例))
        out = pygame.transform.smoothscale(图, (nw, nh)).convert()
        结果 = pygame.Surface((w, h)).convert()
        结果.blit(out, out.get_rect(center=(w // 2, h // 2)).topleft)
        return 结果
    except Exception:
        return None


def _求并集矩形(项列表: List[dict]) -> Optional[pygame.Rect]:
    矩形们: List[pygame.Rect] = []
    for 项 in 项列表:
        if not isinstance(项, dict):
            continue
        rr = 项.get("rect")
        if isinstance(rr, pygame.Rect):
            矩形们.append(rr)
    if not 矩形们:
        return None
    out = 矩形们[0].copy()
    for rr in 矩形们[1:]:
        out.union_ip(rr)
    return out


def _扩成顶部条区域(矩形: Optional[pygame.Rect], 屏幕尺寸: Tuple[int, int]) -> pygame.Rect:
    屏宽, 屏高 = int(max(1, 屏幕尺寸[0])), int(max(1, 屏幕尺寸[1]))
    if not isinstance(矩形, pygame.Rect):
        return pygame.Rect(0, 0, 屏宽, max(160, int(屏高 * 0.14)))
    return pygame.Rect(0, 0, 屏宽, min(屏高, int(矩形.bottom + 26)))


def 主函数():
    pygame.init()
    pygame.font.init()
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception:
        pass

    项目根 = 布局调试器._取项目根目录()
    设置路径 = os.path.join(项目根, "json", "准备就绪动画_设置.json")
    设置 = 读取准备动画设置(设置路径)
    if not os.path.isfile(设置路径):
        保存准备动画设置(设置路径, 设置)

    屏幕 = pygame.display.set_mode((1366, 768), pygame.RESIZABLE)
    pygame.display.set_caption("准备就绪动画调试器")
    时钟 = pygame.time.Clock()

    字体 = 获取字体(20, False)
    小字体 = 获取字体(16, False)

    布局路径 = os.path.join(项目根, "json", "谱面渲染器_布局.json")
    布局管理器 = 谱面渲染器布局管理器(布局路径)
    皮肤包 = 布局调试器._加载皮肤包(项目根)
    头像图, 玩家昵称 = 布局调试器._尝试加载头像与昵称(项目根)
    段位图 = 布局调试器._尝试加载段位图(项目根)
    背景路径 = 布局调试器._尝试加载背景图(项目根)
    背景原图 = None
    if 背景路径 and os.path.isfile(背景路径):
        try:
            背景原图 = pygame.image.load(背景路径).convert()
        except Exception:
            背景原图 = None
    准备图片 = 加载准备动画图片(项目根)
    准备音效 = None
    准备音效通道 = None
    准备音效路径 = os.path.join(项目根, "冷资源", "backsound", "准备就绪音效.mp3")
    try:
        if pygame.mixer.get_init() and os.path.isfile(准备音效路径):
            准备音效 = pygame.mixer.Sound(准备音效路径)
    except Exception:
        准备音效 = None

    参数项 = [
        ("黑屏退场周期", "黑屏退场周期", "s"),
        ("背景展示周期", "背景展示周期", "s"),
        ("背景蒙版展示周期", "背景蒙版展示周期", "s"),
        ("判定区显示周期", "判定区显示周期", "s"),
        ("血条组入场周期", "血条组入场周期", "s"),
        ("场景引导入场周期", "场景引导入场周期", "s"),
        ("背景板入场周期", "背景板入场周期", "s"),
        ("背景板装饰运动速度", "背景板装饰速度", "px/s"),
        ("提示1缩放幅度", "提示1缩放幅度", ""),
        ("提示1缩放周期", "提示1缩放周期", "s"),
        ("提示2缩放幅度", "提示2缩放幅度", ""),
        ("提示2缩放周期", "提示2缩放周期", "s"),
        ("场景引导出场周期", "场景引导出场周期", "s"),
    ]
    选中参数索引 = 0
    播放中 = False
    播放开始系统秒 = 0.0
    预览秒 = 0.0
    准备音效已播放 = False
    循环播放 = False
    准备绘制缓存: Dict[str, object] = {}

    def _保存():
        保存准备动画设置(设置路径, 设置)

    def _当前选中参数键() -> str:
        if not 参数项:
            return ""
        return str(参数项[max(0, min(len(参数项) - 1, int(选中参数索引)))][0])

    def _重播():
        nonlocal 播放中, 播放开始系统秒, 预览秒, 准备音效通道, 准备音效已播放
        播放中 = True
        播放开始系统秒 = float(pygame.time.get_ticks()) / 1000.0
        预览秒 = 0.0
        准备音效已播放 = False
        try:
            if 准备音效通道 is not None:
                准备音效通道.stop()
        except Exception:
            pass

    def _调整参数(键: str, 方向: int, 大步进: bool = False):
        if 键 not in 设置:
            return
        for 参数键, _标签, 单位 in 参数项:
            if 参数键 != 键:
                continue
            当前值 = float(设置.get(键, 0.0) or 0.0)
            if 单位 == "s":
                步进 = 0.1 if 大步进 else 0.01
            elif 单位 == "px/s":
                步进 = 10.0 if 大步进 else 1.0
            else:
                步进 = 0.1 if 大步进 else 0.01
            新值 = 当前值 + float(步进) * int(方向)
            if 键.endswith("周期"):
                新值 = max(0.05, 新值)
            elif 键.endswith("速度"):
                新值 = max(1.0, 新值)
            elif 键.endswith("幅度"):
                新值 = max(0.01, 新值)
            设置[键] = float(round(新值, 4))
            _保存()
            return

    while True:
        当前系统秒 = float(pygame.time.get_ticks()) / 1000.0
        if 播放中:
            时间轴 = 计算准备动画时间轴(设置)
            总时长 = float(时间轴.get("总时长", 0.0))
            预览秒 = max(0.0, 当前系统秒 - float(播放开始系统秒))
            if (not 准备音效已播放) and 预览秒 >= float(时间轴.get("引导开始", 0.0)):
                try:
                    if 准备音效 is not None:
                        准备音效通道 = 准备音效.play()
                except Exception:
                    准备音效通道 = None
                准备音效已播放 = True
            if 预览秒 >= 总时长:
                if 循环播放:
                    _重播()
                else:
                    预览秒 = 总时长
                    播放中 = False

        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                try:
                    if 准备音效通道 is not None:
                        准备音效通道.stop()
                except Exception:
                    pass
                pygame.quit()
                return
            if 事件.type == pygame.VIDEORESIZE:
                屏幕 = pygame.display.set_mode(
                    (max(960, 事件.w), max(540, 事件.h)), pygame.RESIZABLE
                )
            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    try:
                        if 准备音效通道 is not None:
                            准备音效通道.stop()
                    except Exception:
                        pass
                    pygame.quit()
                    return
                if 事件.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    _保存()
                if 事件.key in (pygame.K_RETURN, pygame.K_SPACE):
                    _重播()
                if 事件.key == pygame.K_UP:
                    选中参数索引 = max(0, int(选中参数索引) - 1)
                if 事件.key == pygame.K_DOWN:
                    选中参数索引 = min(len(参数项) - 1, int(选中参数索引) + 1)
                if 事件.key == pygame.K_LEFT:
                    _调整参数(_当前选中参数键(), -1, bool(pygame.key.get_mods() & pygame.KMOD_SHIFT))
                if 事件.key == pygame.K_RIGHT:
                    _调整参数(_当前选中参数键(), +1, bool(pygame.key.get_mods() & pygame.KMOD_SHIFT))
            if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
                鼠标x, 鼠标y = 事件.pos
                面板rect = pygame.Rect(16, 16, 380, 屏幕.get_height() - 32)
                播放按钮rect = pygame.Rect(面板rect.x + 12, 面板rect.y + 12, 面板rect.w - 24, 36)
                循环勾选rect = pygame.Rect(面板rect.x + 12, 播放按钮rect.bottom + 10, 22, 22)
                if 播放按钮rect.collidepoint(鼠标x, 鼠标y):
                    _重播()
                    continue
                if 循环勾选rect.collidepoint(鼠标x, 鼠标y):
                    循环播放 = not bool(循环播放)
                    continue

                当前y = 循环勾选rect.bottom + 14
                for 索引, (键, 标签, 单位) in enumerate(参数项):
                    行rect = pygame.Rect(面板rect.x + 12, 当前y, 面板rect.w - 24, 34)
                    减rect = pygame.Rect(行rect.right - 76, 行rect.y + 4, 30, 26)
                    加rect = pygame.Rect(行rect.right - 36, 行rect.y + 4, 30, 26)
                    if 减rect.collidepoint(鼠标x, 鼠标y):
                        _调整参数(键, -1, False)
                        选中参数索引 = 索引
                        break
                    if 加rect.collidepoint(鼠标x, 鼠标y):
                        _调整参数(键, +1, False)
                        选中参数索引 = 索引
                        break
                    if 行rect.collidepoint(鼠标x, 鼠标y):
                        选中参数索引 = 索引
                        break
                    当前y += 38

        屏宽, 屏高 = 屏幕.get_size()
        背景图 = _画cover(背景原图, (屏宽, 屏高))
        if 背景图 is None:
            背景图 = pygame.Surface((屏宽, 屏高)).convert()
            背景图.fill((18, 18, 24))

        上下文 = 布局调试器._构建调试上下文(
            强制显示=False,
            当前秒=float(当前系统秒),
            头像图=头像图,
            段位图=段位图,
            玩家昵称=玩家昵称,
            歌曲名="ARE YOU READY TEST",
            歌曲星级文本="7星",
            屏幕尺寸=(屏宽, 屏高),
            布局管理器=布局管理器,
            模拟普通击中特效=False,
            模拟hold击中特效循环=False,
            模拟满血暴走=False,
            调试血量显示=0.5,
            调试血条颜色=(181, 23, 203),
            调试血条亮度=1.0,
            调试血条不透明度=0.5,
            调试血条晃荡速度=2.7,
            调试血条晃荡幅度=5.0,
            调试暴走血条速度=150.0,
            调试头像框特效速度=30.0,
            隐藏控件ids=[],
            圆环频谱对象=None,
        )

        基础场景图 = 背景图.copy()
        暗层 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
        暗层.fill((0, 0, 0, 224))
        基础场景图.blit(暗层, (0, 0))

        调试 = 调试状态(显示全部边框=False, 选中控件id="")
        判定区图层 = None
        try:
            布局管理器.绘制(基础场景图, 上下文, 皮肤包, 调试=调试, 仅绘制根id="判定区组")
            布局管理器.绘制(基础场景图, 上下文, 皮肤包, 调试=调试, 仅绘制根id="顶部HUD")
            判定区图层 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
            判定区图层.fill((0, 0, 0, 0))
            布局管理器.绘制(判定区图层, 上下文, 皮肤包, 调试=调试, 仅绘制根id="判定区组")
        except Exception:
            pass

        try:
            判定清单 = 布局管理器._构建渲染清单((屏宽, 屏高), 上下文, 仅绘制根id="判定区组")
        except Exception:
            判定清单 = []
        try:
            HUD清单 = 布局管理器._构建渲染清单((屏宽, 屏高), 上下文, 仅绘制根id="顶部HUD")
        except Exception:
            HUD清单 = []
        try:
            血条清单 = 布局管理器._构建渲染清单(
                (屏宽, 屏高),
                上下文,
                仅绘制控件ids=[
                    "头像框背景",
                    "头像图",
                    "VIP装饰",
                    "头像框特效",
                    "VIP粒子效果",
                    "玩家标签",
                    "玩家昵称",
                    "血条框",
                    "血条值",
                    "血条暴走区域",
                ],
            )
        except Exception:
            血条清单 = []

        判定区rect = _求并集矩形(判定清单) or pygame.Rect(
            int(屏宽 * 0.24), int(屏高 * 0.22), int(屏宽 * 0.52), int(屏高 * 0.14)
        )
        血条组rect = _扩成顶部条区域(_求并集矩形(血条清单), (屏宽, 屏高))
        if 血条组rect.h <= 0:
            顶部HUDrect = _扩成顶部条区域(_求并集矩形(HUD清单), (屏宽, 屏高))
        else:
            顶部HUDrect = 血条组rect

        绘制准备就绪动画(
            屏幕=屏幕,
            基础场景图=基础场景图,
            背景无蒙版图=背景图,
            准备图片=准备图片,
            设置=设置,
            经过秒=float(预览秒),
            判定区矩形=判定区rect,
            顶部HUD矩形=顶部HUDrect,
            判定区图层=判定区图层,
            运行缓存=准备绘制缓存,
        )

        面板rect = pygame.Rect(16, 16, 380, 屏高 - 32)
        面板底 = pygame.Surface((面板rect.w, 面板rect.h), pygame.SRCALPHA)
        面板底.fill((0, 0, 0, 170))
        屏幕.blit(面板底, 面板rect.topleft)
        pygame.draw.rect(屏幕, (220, 228, 255), 面板rect, width=1, border_radius=10)

        播放按钮rect = pygame.Rect(面板rect.x + 12, 面板rect.y + 12, 面板rect.w - 24, 36)
        pygame.draw.rect(屏幕, (80, 130, 220), 播放按钮rect, border_radius=8)
        播放文字 = 字体.render("播放 / 重播（Space）", True, (255, 255, 255))
        屏幕.blit(
            播放文字,
            (
                播放按钮rect.x + (播放按钮rect.w - 播放文字.get_width()) // 2,
                播放按钮rect.y + (播放按钮rect.h - 播放文字.get_height()) // 2,
            ),
        )

        循环勾选rect = pygame.Rect(面板rect.x + 12, 播放按钮rect.bottom + 10, 22, 22)
        pygame.draw.rect(屏幕, (88, 92, 118), 循环勾选rect, border_radius=4)
        pygame.draw.rect(屏幕, (220, 228, 255), 循环勾选rect, width=1, border_radius=4)
        if 循环播放:
            pygame.draw.line(屏幕, (255, 255, 255), (循环勾选rect.x + 4, 循环勾选rect.y + 11), (循环勾选rect.x + 9, 循环勾选rect.bottom - 5), 2)
            pygame.draw.line(屏幕, (255, 255, 255), (循环勾选rect.x + 9, 循环勾选rect.bottom - 5), (循环勾选rect.right - 4, 循环勾选rect.y + 5), 2)
        循环图 = 小字体.render("循环播放", True, (242, 242, 246))
        屏幕.blit(循环图, (循环勾选rect.right + 8, 循环勾选rect.y + (循环勾选rect.h - 循环图.get_height()) // 2))

        时间轴 = 计算准备动画时间轴(设置)
        总时长 = float(时间轴.get("总时长", 0.0))
        状态图 = 小字体.render(
            f"当前: {预览秒:.2f}s / 总长: {总时长:.2f}s  {'播放中' if 播放中 else '已停止'}",
            True,
            (240, 240, 245),
        )
        屏幕.blit(状态图, (面板rect.x + 14, 循环勾选rect.bottom + 8))

        当前y = 循环勾选rect.bottom + 34
        for 索引, (键, 标签, 单位) in enumerate(参数项):
            行rect = pygame.Rect(面板rect.x + 12, 当前y, 面板rect.w - 24, 34)
            if int(选中参数索引) == int(索引):
                选中底 = pygame.Surface((行rect.w, 行rect.h), pygame.SRCALPHA)
                选中底.fill((90, 110, 160, 80))
                屏幕.blit(选中底, 行rect.topleft)
            pygame.draw.rect(屏幕, (110, 122, 150), 行rect, width=1, border_radius=6)

            值文本 = f"{float(设置.get(键, 0.0)):.2f}{单位}"
            文本 = 小字体.render(f"{标签}: {值文本}", True, (242, 242, 246))
            屏幕.blit(文本, (行rect.x + 8,行rect.y + (行rect.h - 文本.get_height()) // 2))

            减rect = pygame.Rect(行rect.right - 76, 行rect.y + 4, 30, 26)
            加rect = pygame.Rect(行rect.right - 36, 行rect.y + 4, 30, 26)
            for rect, ch in ((减rect, "-"), (加rect, "+")):
                pygame.draw.rect(屏幕, (88, 92, 118), rect, border_radius=5)
                pygame.draw.rect(屏幕, (200, 205, 230), rect, width=1, border_radius=5)
                字 = 字体.render(ch, True, (255, 255, 255))
                屏幕.blit(字, (rect.x + (rect.w - 字.get_width()) // 2, rect.y + (rect.h - 字.get_height()) // 2 - 1))
            当前y += 38

        提示行 = [
            "上下方向键选中，左右微调",
            "Shift+左右 = 0.1s / 大步进",
            "勾循环后自动重播，ESC 退出",
        ]
        提示y = 面板rect.bottom - 72
        for 文本 in 提示行:
            图 = 小字体.render(文本, True, (226, 226, 234))
            屏幕.blit(图, (面板rect.x + 14, 提示y))
            提示y += 图.get_height() + 4

        pygame.display.flip()
        时钟.tick(60)


if __name__ == "__main__":
    主函数()
