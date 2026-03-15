import os
import sys
import time
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Tuple

import pygame

import 谱面布局调试器 as 布局调试器
from core.工具 import 获取字体
from ui.结算前成就动画 import (
    默认结算前成就动画设置,
    保存结算前成就动画设置,
    结算前成就动画控制器,
    计算结算前成就动画时间轴,
    读取结算前成就动画设置,
)
from ui.谱面渲染器 import 谱面渲染器, 渲染输入


@dataclass(frozen=True)
class 参数定义:
    键: str
    标签: str
    单位: str = ""
    小步进: float = 0.01
    大步进: float = 0.10
    最小值: Optional[float] = None
    最大值: Optional[float] = None
    显示精度: int = 2


@dataclass
class 调试资源:
    字体: pygame.font.Font
    小字体: pygame.font.Font
    渲染器: 谱面渲染器
    背景原图: Optional[pygame.Surface]
    头像图: Optional[pygame.Surface]
    玩家昵称: str
    段位图: Optional[pygame.Surface]
    音效: Optional[pygame.mixer.Sound]


@dataclass
class 调试器状态:
    主题id: str = "full_perfect"
    选中参数索引: int = 0
    参数滚动: int = 0
    播放中: bool = True
    播放开始系统秒: float = 0.0
    预览秒: float = 0.0
    循环播放: bool = True
    拖动时间轴: bool = False
    背景缓存尺寸: Tuple[int, int] = (0, 0)
    背景缓存图: Optional[pygame.Surface] = None
    控制面板宽度: int = 468
    运行缓存: Dict[str, Any] = field(default_factory=dict)


参数定义列表: List[参数定义] = [
    参数定义("阶段1底板入场秒", "阶段1 底板", "s", 0.01, 0.05, 0.03, 3.00),
    参数定义("阶段2主体入场秒", "阶段2 主体", "s", 0.01, 0.05, 0.03, 3.00),
    参数定义("阶段3标签入场秒", "阶段3 标签", "s", 0.01, 0.05, 0.03, 3.00),
    参数定义("阶段4停留秒", "阶段4 停留", "s", 0.05, 0.25, 0.05, 12.00),
    参数定义("阶段5整体收尾秒", "阶段5 收尾", "s", 0.01, 0.05, 0.03, 3.00),
    参数定义("阶段6HUD回收秒", "阶段6 回收", "s", 0.01, 0.05, 0.03, 3.00),
    参数定义("底板组入场起始X偏移", "底板起始X", "px", 5.0, 25.0, -2400.0, 2400.0, 0),
    参数定义("底板组入场起始Y偏移", "底板起始Y", "px", 5.0, 25.0, -2400.0, 2400.0, 0),
    参数定义("底板组旋转角度", "底板角度", "°", 0.5, 2.0, -60.0, 60.0, 1),
    参数定义("底板组缩放倍率", "底板缩放", "x", 0.01, 0.05, 0.30, 2.40),
    参数定义("底板组箭头透明度", "箭头透明度", "", 5.0, 20.0, 0.0, 255.0, 0),
    参数定义("底板组箭头内部缩放", "箭头内缩放", "x", 0.01, 0.05, 0.10, 2.50),
    参数定义("底板组箭头速度", "箭头速度", "px/s", 5.0, 30.0, 40.0, 3000.0, 0),
    参数定义("board组缩放倍率", "Board缩放", "x", 0.01, 0.05, 0.30, 2.40),
    参数定义("board组入场起始透明度", "Board起始透明", "", 5.0, 20.0, 0.0, 255.0, 0),
    参数定义("board旋转速度", "Board转速", "°/s", 1.0, 5.0, -360.0, 360.0, 1),
    参数定义("假频谱缩放倍率", "频谱缩放", "x", 0.01, 0.05, 0.20, 8.00),
    参数定义("所有控件等比缩放", "全局缩放", "x", 0.01, 0.05, 0.30, 2.40),
    参数定义("label旋转角度", "Label角度", "°", 0.5, 2.0, -180.0, 180.0, 1),
]


def _取项目根目录() -> str:
    try:
        return 布局调试器._取项目根目录()
    except Exception:
        return os.path.dirname(os.path.abspath(__file__))


def _取默认箭头皮肤路径(项目根: str) -> str:
    try:
        皮肤编号列表 = 布局调试器._收集可用箭头皮肤编号(项目根)
    except Exception:
        皮肤编号列表 = ["02"]
    if "02" in 皮肤编号列表:
        目标编号 = "02"
    elif 皮肤编号列表:
        目标编号 = str(皮肤编号列表[0])
    else:
        目标编号 = "02"
    return os.path.join(项目根, "UI-img", "游戏界面", "箭头", 目标编号)


def _载入背景原图(项目根: str) -> Optional[pygame.Surface]:
    try:
        背景路径 = 布局调试器._尝试加载背景图(项目根)
    except Exception:
        背景路径 = ""
    if not 背景路径 or (not os.path.isfile(背景路径)):
        return None
    try:
        return pygame.image.load(背景路径).convert()
    except Exception:
        return None


def _创建调试资源(项目根: str) -> 调试资源:
    渲染器 = 谱面渲染器()
    try:
        渲染器.设置皮肤(_取默认箭头皮肤路径(项目根))
    except Exception:
        pass
    头像图, 玩家昵称 = 布局调试器._尝试加载头像与昵称(项目根)
    音效 = None
    音效路径 = os.path.join(项目根, "冷资源", "Buttonsound", "全连.mp3")
    if pygame.mixer.get_init() and os.path.isfile(音效路径):
        try:
            音效 = pygame.mixer.Sound(音效路径)
        except Exception:
            音效 = None
    return 调试资源(
        字体=获取字体(20, False),
        小字体=获取字体(16, False),
        渲染器=渲染器,
        背景原图=_载入背景原图(项目根),
        头像图=头像图,
        玩家昵称=玩家昵称,
        段位图=布局调试器._尝试加载段位图(项目根),
        音效=音效,
    )


def _画cover缓存(
    状态: 调试器状态,
    图像: Optional[pygame.Surface],
    尺寸: Tuple[int, int],
) -> Optional[pygame.Surface]:
    if 图像 is None:
        return None
    目标尺寸 = (int(max(1, 尺寸[0])), int(max(1, 尺寸[1])))
    if (
        isinstance(状态.背景缓存图, pygame.Surface)
        and tuple(状态.背景缓存尺寸) == 目标尺寸
    ):
        return 状态.背景缓存图
    try:
        源宽, 源高 = 图像.get_size()
        比例 = max(目标尺寸[0] / max(1, 源宽), 目标尺寸[1] / max(1, 源高))
        新宽 = int(max(1, round(源宽 * 比例)))
        新高 = int(max(1, round(源高 * 比例)))
        图 = pygame.transform.smoothscale(图像, (新宽, 新高)).convert()
        if 新宽 > 目标尺寸[0] or 新高 > 目标尺寸[1]:
            x = int(max(0, (新宽 - 目标尺寸[0]) // 2))
            y = int(max(0, (新高 - 目标尺寸[1]) // 2))
            图 = 图.subsurface((x, y, 目标尺寸[0], 目标尺寸[1])).copy().convert()
        状态.背景缓存尺寸 = 目标尺寸
        状态.背景缓存图 = 图
        return 图
    except Exception:
        状态.背景缓存尺寸 = (0, 0)
        状态.背景缓存图 = None
        return None


def _构建渲染输入(
    屏幕尺寸: Tuple[int, int],
    资源: 调试资源,
    隐藏顶部HUD: bool,
    隐藏判定区: bool,
) -> 渲染输入:
    屏宽, 屏高 = int(max(1, 屏幕尺寸[0])), int(max(1, 屏幕尺寸[1]))
    头像边 = int(max(64, min(180, 屏宽 * 0.06)))
    血条高度 = int(max(int(头像边 * 1.15), 72))
    血条区域 = pygame.Rect(18, 10, 屏宽 - 36, 血条高度)
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
    轨道中心列表 = [
        int(轨道起x + 轨道槽宽 // 2 + i * 轨道中心间距) for i in range(5)
    ]
    return 渲染输入(
        当前谱面秒=83.6,
        总时长秒=85.0,
        轨道中心列表=轨道中心列表,
        判定线y=int(判定线y),
        底部y=int(底部y),
        滚动速度px每秒=620.0,
        箭头目标宽=int(箭头目标宽),
        事件列表=[],
        显示_判定="perfect",
        显示_连击=1380,
        显示_分数=998766,
        显示_百分比="100.00%",
        血条区域=血条区域,
        血量显示=1.0,
        头像图=资源.头像图,
        总血量HP=1000,
        可见血量HP=1000,
        Note层灰度=False,
        血条暴走=False,
        玩家序号=1,
        玩家昵称=资源.玩家昵称,
        段位图=资源.段位图,
        当前关卡=3,
        歌曲名="SETTLEMENT ANIMATION DEBUG",
        星级=7,
        血条待机演示=False,
        显示手装饰=False,
        错误提示="",
        轨迹模式="正常",
        隐藏模式="关闭",
        大小倍率=1.0,
        GPU接管音符绘制=False,
        GPU接管判定区绘制=False,
        GPU接管击中特效绘制=False,
        GPU接管计数动画绘制=False,
        GPU接管Stage绘制=False,
        隐藏顶部HUD绘制=bool(隐藏顶部HUD),
        隐藏判定区绘制=bool(隐藏判定区),
        圆环频谱对象=None,
    )


def _格式化参数值(定义: 参数定义, 数值: float) -> str:
    if int(定义.显示精度) <= 0:
        return f"{int(round(float(数值)))}{定义.单位}"
    return f"{float(数值):.{int(定义.显示精度)}f}{定义.单位}"


def _调整参数(
    设置: Dict[str, float],
    定义: 参数定义,
    方向: int,
    大步进: bool = False,
) -> bool:
    if 定义.键 not in 设置:
        设置[定义.键] = float(默认结算前成就动画设置().get(定义.键, 0.0))
    当前值 = float(设置.get(定义.键, 0.0) or 0.0)
    步进 = 定义.大步进 if bool(大步进) else 定义.小步进
    新值 = 当前值 + float(步进) * int(方向)
    if 定义.最小值 is not None:
        新值 = max(float(定义.最小值), 新值)
    if 定义.最大值 is not None:
        新值 = min(float(定义.最大值), 新值)
    if int(定义.显示精度) <= 0:
        新值 = float(int(round(新值)))
    else:
        新值 = float(round(新值, 4))
    if abs(新值 - 当前值) < 0.0001:
        return False
    设置[定义.键] = 新值
    return True


def _确保选中项可见(状态: 调试器状态, 可见行数: int):
    可见行数 = max(1, int(可见行数))
    最大滚动 = max(0, len(参数定义列表) - 可见行数)
    状态.参数滚动 = max(0, min(int(状态.参数滚动), 最大滚动))
    if 状态.选中参数索引 < 状态.参数滚动:
        状态.参数滚动 = int(状态.选中参数索引)
    elif 状态.选中参数索引 >= 状态.参数滚动 + 可见行数:
        状态.参数滚动 = int(状态.选中参数索引) - 可见行数 + 1
    状态.参数滚动 = max(0, min(int(状态.参数滚动), 最大滚动))


def _同步动画设置(
    设置: Dict[str, float],
    设置路径: str,
    状态: 调试器状态,
    动画: 结算前成就动画控制器,
):
    保存结算前成就动画设置(设置路径, 设置)
    动画.应用设置(设置)
    总时长 = float(动画.取总时长())
    if 状态.预览秒 > 总时长:
        状态.预览秒 = 总时长
    if not bool(动画.是否激活()):
        动画.启动(状态.主题id)
    动画.设置经过秒(float(状态.预览秒))
    if 状态.播放中:
        状态.播放开始系统秒 = float(time.perf_counter()) - float(状态.预览秒)


def _设定预览秒(
    状态: 调试器状态,
    动画: 结算前成就动画控制器,
    目标秒: float,
    保持播放: bool = False,
):
    总时长 = float(动画.取总时长())
    状态.预览秒 = max(0.0, min(float(目标秒), 总时长))
    if not bool(动画.是否激活()):
        动画.启动(状态.主题id)
    动画.设置经过秒(float(状态.预览秒))
    if 保持播放:
        状态.播放中 = True
        状态.播放开始系统秒 = float(time.perf_counter()) - float(状态.预览秒)
    else:
        状态.播放中 = False


def _播放重播音效(资源: Optional[调试资源]):
    if 资源 is None or 资源.音效 is None:
        return
    try:
        资源.音效.stop()
        资源.音效.play()
    except Exception:
        pass


def _重播(状态: 调试器状态, 动画: 结算前成就动画控制器, 资源: Optional[调试资源] = None):
    状态.拖动时间轴 = False
    状态.播放开始系统秒 = float(time.perf_counter())
    状态.预览秒 = 0.0
    状态.播放中 = True
    动画.启动(状态.主题id, 状态.播放开始系统秒)
    _播放重播音效(资源)


def _切换播放暂停(状态: 调试器状态, 动画: 结算前成就动画控制器):
    if 状态.播放中:
        状态.播放中 = False
        return
    _设定预览秒(状态, 动画, 状态.预览秒, 保持播放=True)


def _时间轴位置转秒(x坐标: int, 时间轴rect: pygame.Rect, 动画: 结算前成就动画控制器) -> float:
    if 时间轴rect.w <= 0:
        return 0.0
    比例 = max(0.0, min(1.0, float(x坐标 - 时间轴rect.x) / float(时间轴rect.w)))
    return float(动画.取总时长()) * 比例


def _计算控制布局(
    屏幕尺寸: Tuple[int, int],
    状态: 调试器状态,
) -> Dict[str, Any]:
    屏宽, 屏高 = int(max(1, 屏幕尺寸[0])), int(max(1, 屏幕尺寸[1]))
    面板 = pygame.Rect(16, 16, min(状态.控制面板宽度, max(360, 屏宽 - 32)), max(420, 屏高 - 32))
    按钮高 = 34
    小按钮宽 = 94
    主按钮宽 = int(max(96, 面板.w - 24 - 小按钮宽 * 3 - 8 * 3))
    重播按钮 = pygame.Rect(面板.x + 12, 面板.y + 12, 主按钮宽, 按钮高)
    播放按钮 = pygame.Rect(重播按钮.right + 8, 重播按钮.y, 小按钮宽, 按钮高)
    主题按钮 = pygame.Rect(播放按钮.right + 8, 重播按钮.y, 小按钮宽, 按钮高)
    重置按钮 = pygame.Rect(主题按钮.right + 8, 重播按钮.y, 小按钮宽, 按钮高)
    循环框 = pygame.Rect(面板.x + 12, 重播按钮.bottom + 12, 20, 20)
    状态文本位置 = (面板.x + 12, 循环框.bottom + 10)
    时间轴标签位置 = (面板.x + 12, 循环框.bottom + 42)
    时间轴 = pygame.Rect(面板.x + 12, 循环框.bottom + 66, 面板.w - 24, 14)
    参数区起始y = 时间轴.bottom + 24
    帮助区高 = 76
    参数视口 = pygame.Rect(
        面板.x + 12,
        参数区起始y,
        面板.w - 24,
        max(72, 面板.bottom - 参数区起始y - 帮助区高 - 14),
    )
    行高 = 34
    行间距 = 4
    可见行数 = max(1, (参数视口.h + 行间距) // (行高 + 行间距))
    _确保选中项可见(状态, 可见行数)

    参数行: List[Dict[str, Any]] = []
    当前y = 参数视口.y
    起始索引 = int(状态.参数滚动)
    for 索引 in range(起始索引, min(len(参数定义列表), 起始索引 + 可见行数)):
        行rect = pygame.Rect(参数视口.x, 当前y, 参数视口.w, 行高)
        减rect = pygame.Rect(行rect.right - 76, 行rect.y + 4, 30, 26)
        加rect = pygame.Rect(行rect.right - 36, 行rect.y + 4, 30, 26)
        参数行.append(
            {
                "索引": 索引,
                "定义": 参数定义列表[索引],
                "行rect": 行rect,
                "减rect": 减rect,
                "加rect": 加rect,
            }
        )
        当前y += 行高 + 行间距

    return {
        "面板": 面板,
        "重播按钮": 重播按钮,
        "播放按钮": 播放按钮,
        "主题按钮": 主题按钮,
        "重置按钮": 重置按钮,
        "循环框": 循环框,
        "状态文本位置": 状态文本位置,
        "时间轴标签位置": 时间轴标签位置,
        "时间轴": 时间轴,
        "参数视口": 参数视口,
        "参数行": 参数行,
        "可见行数": 可见行数,
        "帮助起始y": 参数视口.bottom + 14,
    }


def _绘制按钮(
    屏幕: pygame.Surface,
    字体: pygame.font.Font,
    rect: pygame.Rect,
    文本: str,
    激活: bool = False,
):
    底色 = (86, 98, 126) if not bool(激活) else (118, 134, 174)
    描边 = (205, 214, 236) if not bool(激活) else (255, 240, 170)
    pygame.draw.rect(屏幕, 底色, rect, border_radius=6)
    pygame.draw.rect(屏幕, 描边, rect, width=1, border_radius=6)
    字图 = 字体.render(str(文本), True, (255, 255, 255))
    屏幕.blit(
        字图,
        (
            rect.x + (rect.w - 字图.get_width()) // 2,
            rect.y + (rect.h - 字图.get_height()) // 2,
        ),
    )


def _绘制控制面板(
    屏幕: pygame.Surface,
    资源: 调试资源,
    状态: 调试器状态,
    设置: Dict[str, float],
    动画: 结算前成就动画控制器,
    布局: Dict[str, Any],
):
    面板: pygame.Rect = 布局["面板"]
    面板图 = pygame.Surface((面板.w, 面板.h), pygame.SRCALPHA).convert_alpha()
    面板图.fill((0, 0, 0, 156))
    屏幕.blit(面板图, 面板.topleft)

    _绘制按钮(屏幕, 资源.小字体, 布局["重播按钮"], "重播")
    _绘制按钮(
        屏幕,
        资源.小字体,
        布局["播放按钮"],
        "暂停" if 状态.播放中 else "播放",
        激活=bool(状态.播放中),
    )
    _绘制按钮(
        屏幕,
        资源.小字体,
        布局["主题按钮"],
        "AP" if 状态.主题id == "full_perfect" else "FC",
        激活=True,
    )
    _绘制按钮(屏幕, 资源.小字体, 布局["重置按钮"], "恢复默认")

    pygame.draw.rect(屏幕, (255, 255, 255), 布局["循环框"], width=1, border_radius=4)
    if bool(状态.循环播放):
        pygame.draw.rect(
            屏幕,
            (255, 236, 150),
            布局["循环框"].inflate(-6, -6),
            border_radius=3,
        )
    循环图 = 资源.小字体.render("循环播放", True, (236, 236, 242))
    屏幕.blit(循环图, (布局["循环框"].right + 8, 布局["循环框"].y - 1))

    标题图 = 资源.字体.render("结算前成就动画调试器", True, (255, 240, 168))
    屏幕.blit(标题图, (布局["状态文本位置"][0], 布局["状态文本位置"][1]))

    状态行 = [
        f"主题: {状态.主题id}",
        f"阶段: {动画.取当前阶段名()}",
        f"时间: {状态.预览秒:05.2f}s / {动画.取总时长():05.2f}s",
    ]
    y = 布局["状态文本位置"][1] + 标题图.get_height() + 6
    for 文本 in 状态行:
        图 = 资源.小字体.render(文本, True, (236, 238, 244))
        屏幕.blit(图, (布局["状态文本位置"][0], y))
        y += int(图.get_height() + 2)

    时间轴标题 = 资源.字体.render("时间轴", True, (255, 245, 170))
    屏幕.blit(时间轴标题, 布局["时间轴标签位置"])
    时间轴rect: pygame.Rect = 布局["时间轴"]
    pygame.draw.rect(屏幕, (52, 56, 74), 时间轴rect, border_radius=7)
    pygame.draw.rect(屏幕, (142, 151, 178), 时间轴rect, width=1, border_radius=7)

    总时长 = float(max(0.001, 动画.取总时长()))
    位置x = int(round(时间轴rect.x + 时间轴rect.w * max(0.0, min(1.0, 状态.预览秒 / 总时长))))
    pygame.draw.rect(
        屏幕,
        (116, 152, 255),
        pygame.Rect(时间轴rect.x, 时间轴rect.y, max(0, 位置x - 时间轴rect.x), 时间轴rect.h),
        border_radius=7,
    )

    时间轴 = 计算结算前成就动画时间轴(设置)
    标记表 = [
        ("阶段1开始", "P1", (126, 210, 255)),
        ("阶段2开始", "P2", (255, 212, 102)),
        ("阶段3开始", "P3", (255, 170, 170)),
        ("阶段4开始", "P4", (180, 255, 188)),
        ("阶段5开始", "P5", (255, 180, 118)),
        ("阶段6开始", "P6", (198, 176, 255)),
    ]
    for 键, 名称, 颜色 in 标记表:
        秒 = float(时间轴.get(键, 0.0))
        比例 = max(0.0, min(1.0, 秒 / 总时长))
        x = int(round(时间轴rect.x + 时间轴rect.w * 比例))
        pygame.draw.line(屏幕, 颜色, (x, 时间轴rect.y - 5), (x, 时间轴rect.bottom + 5), 1)
        标记图 = 资源.小字体.render(名称, True, 颜色)
        屏幕.blit(标记图, (x - 标记图.get_width() // 2, 时间轴rect.y - 20))

    pygame.draw.circle(屏幕, (248, 248, 255), (位置x, 时间轴rect.centery), 7)
    pygame.draw.circle(屏幕, (128, 86, 215), (位置x, 时间轴rect.centery), 7, 1)

    参数标题 = 资源.字体.render("参数", True, (255, 245, 170))
    屏幕.blit(参数标题, (布局["参数视口"].x, 布局["参数视口"].y - 28))
    滚动图 = 资源.小字体.render(
        f"{状态.选中参数索引 + 1}/{len(参数定义列表)}",
        True,
        (205, 214, 236),
    )
    屏幕.blit(
        滚动图,
        (
            布局["参数视口"].right - 滚动图.get_width(),
            布局["参数视口"].y - 24,
        ),
    )

    for 行 in 布局["参数行"]:
        索引 = int(行["索引"])
        定义: 参数定义 = 行["定义"]
        行rect: pygame.Rect = 行["行rect"]
        减rect: pygame.Rect = 行["减rect"]
        加rect: pygame.Rect = 行["加rect"]

        if 索引 == int(状态.选中参数索引):
            高亮 = pygame.Surface((行rect.w, 行rect.h), pygame.SRCALPHA)
            高亮.fill((92, 114, 165, 88))
            屏幕.blit(高亮, 行rect.topleft)
        pygame.draw.rect(屏幕, (110, 122, 150), 行rect, width=1, border_radius=6)

        值文本 = _格式化参数值(定义, float(设置.get(定义.键, 0.0) or 0.0))
        文本 = 资源.小字体.render(f"{定义.标签}: {值文本}", True, (242, 242, 246))
        屏幕.blit(文本, (行rect.x + 8, 行rect.y + (行rect.h - 文本.get_height()) // 2))

        for rect, 符号 in ((减rect, "-"), (加rect, "+")):
            pygame.draw.rect(屏幕, (88, 92, 118), rect, border_radius=5)
            pygame.draw.rect(屏幕, (200, 205, 230), rect, width=1, border_radius=5)
            字图 = 资源.字体.render(符号, True, (255, 255, 255))
            屏幕.blit(
                字图,
                (
                    rect.x + (rect.w - 字图.get_width()) // 2,
                    rect.y + (rect.h - 字图.get_height()) // 2 - 1,
                ),
            )

    帮助行 = [
        "点击时间轴可跳秒，拖动可逐帧对比",
        "上下选中参数，左右微调，Shift 大步进",
        "Tab / 1 / 2 切主题，Space 播放，R 重播，L 循环",
    ]
    帮助y = 布局["帮助起始y"]
    for 文本 in 帮助行:
        图 = 资源.小字体.render(文本, True, (226, 226, 234))
        屏幕.blit(图, (面板.x + 14, 帮助y))
        帮助y += 图.get_height() + 4


def _重置为默认设置(
    设置: Dict[str, float],
    设置路径: str,
    状态: 调试器状态,
    动画: 结算前成就动画控制器,
):
    设置.clear()
    设置.update(默认结算前成就动画设置())
    _同步动画设置(设置, 设置路径, 状态, 动画)
    _设定预览秒(状态, 动画, 0.0, 保持播放=False)


def 主函数():
    pygame.init()
    pygame.font.init()
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception:
        pass

    项目根 = _取项目根目录()
    if 项目根 not in sys.path:
        sys.path.insert(0, 项目根)

    设置路径 = os.path.join(项目根, "json", "结算前成就动画_设置.json")
    设置 = 读取结算前成就动画设置(设置路径)
    if not os.path.isfile(设置路径):
        保存结算前成就动画设置(设置路径, 设置)

    屏幕 = pygame.display.set_mode((1366, 768), pygame.RESIZABLE)
    pygame.display.set_caption("结算前成就动画调试器")
    时钟 = pygame.time.Clock()

    资源 = _创建调试资源(项目根)
    状态 = 调试器状态()
    动画 = 结算前成就动画控制器(项目根)
    动画.应用设置(设置)
    _重播(状态, 动画, 资源)

    while True:
        时钟.tick(60)

        if 状态.播放中 and (not 状态.拖动时间轴):
            状态.预览秒 = float(time.perf_counter()) - float(状态.播放开始系统秒)
            if 状态.预览秒 >= float(动画.取总时长()):
                if bool(状态.循环播放):
                    _重播(状态, 动画, 资源)
                else:
                    _设定预览秒(状态, 动画, 动画.取总时长(), 保持播放=False)
            else:
                动画.设置经过秒(float(状态.预览秒))

        布局 = _计算控制布局(屏幕.get_size(), 状态)

        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                pygame.quit()
                return

            if 事件.type == pygame.VIDEORESIZE:
                屏幕 = pygame.display.set_mode(
                    (max(960, int(事件.w)), max(540, int(事件.h))),
                    pygame.RESIZABLE,
                )
                布局 = _计算控制布局(屏幕.get_size(), 状态)
                continue

            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if 事件.key == pygame.K_TAB:
                    状态.主题id = (
                        "full_combo"
                        if 状态.主题id == "full_perfect"
                        else "full_perfect"
                    )
                    _重播(状态, 动画, 资源)
                elif 事件.key == pygame.K_1:
                    状态.主题id = "full_perfect"
                    _重播(状态, 动画, 资源)
                elif 事件.key == pygame.K_2:
                    状态.主题id = "full_combo"
                    _重播(状态, 动画, 资源)
                elif 事件.key in (pygame.K_SPACE, pygame.K_p):
                    _切换播放暂停(状态, 动画)
                elif 事件.key == pygame.K_r:
                    _重播(状态, 动画, 资源)
                elif 事件.key == pygame.K_l:
                    状态.循环播放 = not bool(状态.循环播放)
                elif 事件.key == pygame.K_HOME:
                    _设定预览秒(状态, 动画, 0.0, 保持播放=False)
                elif 事件.key == pygame.K_END:
                    _设定预览秒(状态, 动画, 动画.取总时长(), 保持播放=False)
                elif 事件.key == pygame.K_UP:
                    状态.选中参数索引 = max(0, int(状态.选中参数索引) - 1)
                elif 事件.key == pygame.K_DOWN:
                    状态.选中参数索引 = min(
                        len(参数定义列表) - 1,
                        int(状态.选中参数索引) + 1,
                    )
                elif 事件.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    定义 = 参数定义列表[int(状态.选中参数索引)]
                    方向 = -1 if 事件.key == pygame.K_LEFT else 1
                    if _调整参数(
                        设置,
                        定义,
                        方向,
                        bool(pygame.key.get_mods() & pygame.KMOD_SHIFT),
                    ):
                        _同步动画设置(设置, 设置路径, 状态, 动画)
                elif 事件.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    保存结算前成就动画设置(设置路径, 设置)
                elif 事件.key == pygame.K_BACKSPACE:
                    _重置为默认设置(设置, 设置路径, 状态, 动画)
                布局 = _计算控制布局(屏幕.get_size(), 状态)
                continue

            if 事件.type == pygame.MOUSEBUTTONDOWN:
                if 事件.button == 1:
                    if 布局["重播按钮"].collidepoint(事件.pos):
                        _重播(状态, 动画, 资源)
                        continue
                    if 布局["播放按钮"].collidepoint(事件.pos):
                        _切换播放暂停(状态, 动画)
                        continue
                    if 布局["主题按钮"].collidepoint(事件.pos):
                        状态.主题id = (
                            "full_combo"
                            if 状态.主题id == "full_perfect"
                            else "full_perfect"
                        )
                        _重播(状态, 动画, 资源)
                        continue
                    if 布局["重置按钮"].collidepoint(事件.pos):
                        _重置为默认设置(设置, 设置路径, 状态, 动画)
                        continue
                    if 布局["循环框"].collidepoint(事件.pos):
                        状态.循环播放 = not bool(状态.循环播放)
                        continue
                    if 布局["时间轴"].collidepoint(事件.pos):
                        状态.拖动时间轴 = True
                        _设定预览秒(
                            状态,
                            动画,
                            _时间轴位置转秒(事件.pos[0], 布局["时间轴"], 动画),
                            保持播放=False,
                        )
                        continue
                    for 行 in 布局["参数行"]:
                        索引 = int(行["索引"])
                        定义: 参数定义 = 行["定义"]
                        if 行["减rect"].collidepoint(事件.pos):
                            状态.选中参数索引 = 索引
                            if _调整参数(设置, 定义, -1, False):
                                _同步动画设置(设置, 设置路径, 状态, 动画)
                            break
                        if 行["加rect"].collidepoint(事件.pos):
                            状态.选中参数索引 = 索引
                            if _调整参数(设置, 定义, +1, False):
                                _同步动画设置(设置, 设置路径, 状态, 动画)
                            break
                        if 行["行rect"].collidepoint(事件.pos):
                            状态.选中参数索引 = 索引
                            break
                    布局 = _计算控制布局(屏幕.get_size(), 状态)
                elif 事件.button == 4:
                    if 布局["参数视口"].collidepoint(事件.pos):
                        状态.参数滚动 = max(0, int(状态.参数滚动) - 1)
                        布局 = _计算控制布局(屏幕.get_size(), 状态)
                elif 事件.button == 5:
                    if 布局["参数视口"].collidepoint(事件.pos):
                        最大滚动 = max(0, len(参数定义列表) - int(布局["可见行数"]))
                        状态.参数滚动 = min(最大滚动, int(状态.参数滚动) + 1)
                        布局 = _计算控制布局(屏幕.get_size(), 状态)
                continue

            if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
                状态.拖动时间轴 = False
                continue

            if 事件.type == pygame.MOUSEMOTION and 状态.拖动时间轴:
                _set_preview = _时间轴位置转秒(事件.pos[0], 布局["时间轴"], 动画)
                _设定预览秒(状态, 动画, _set_preview, 保持播放=False)
                continue

        屏幕尺寸 = 屏幕.get_size()
        背景图 = _画cover缓存(状态, 资源.背景原图, 屏幕尺寸)
        if isinstance(背景图, pygame.Surface):
            屏幕.blit(背景图, (0, 0))
        else:
            屏幕.fill((16, 18, 22))

        资源.渲染器.更新(1.0 / 60.0)
        捕获输入 = _构建渲染输入(
            屏幕尺寸,
            资源,
            隐藏顶部HUD=False,
            隐藏判定区=False,
        )
        显示输入 = replace(
            捕获输入,
            隐藏顶部HUD绘制=bool(动画.需要隐藏顶部HUD()),
            隐藏判定区绘制=bool(动画.需要隐藏判定区()),
        )
        资源.渲染器.渲染(屏幕, 显示输入, 资源.字体, 资源.小字体)
        动画.绘制(屏幕, 左渲染器=资源.渲染器, 左输入=捕获输入)
        _绘制控制面板(屏幕, 资源, 状态, 设置, 动画, 布局)
        pygame.display.flip()


if __name__ == "__main__":
    主函数()
