import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pygame

import 谱面布局调试器 as 布局调试器
from core.工具 import 获取字体
from ui.谱面渲染器 import 谱面渲染器, 渲染输入
from ui.准备就绪动画 import (
    默认准备动画设置,
    读取准备动画设置,
    保存准备动画设置,
    加载准备动画图片,
    计算准备动画时间轴,
    绘制准备就绪动画,
)
from ui.调试_谱面渲染器_渲染控件 import 调试状态, 谱面渲染器布局管理器


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
    布局管理器: 谱面渲染器布局管理器
    皮肤包: Any
    准备渲染器: 谱面渲染器
    头像图: Optional[pygame.Surface]
    玩家昵称: str
    段位图: Optional[pygame.Surface]
    背景原图: Optional[pygame.Surface]
    准备图片: Dict[int, pygame.Surface]
    准备音效: Optional[pygame.mixer.Sound]


@dataclass
class 调试器状态:
    选中参数索引: int = 0
    参数滚动: int = 0
    播放中: bool = False
    播放开始系统秒: float = 0.0
    预览秒: float = 0.0
    准备音效已播放: bool = False
    循环播放: bool = False
    拖动时间轴: bool = False
    背景缓存尺寸: Tuple[int, int] = (0, 0)
    背景缓存图: Optional[pygame.Surface] = None
    准备绘制缓存: Dict[str, object] = field(default_factory=dict)
    准备音效通道: Any = None


参数定义列表: List[参数定义] = [
    参数定义("黑屏退场周期", "黑屏退场", "s", 0.01, 0.05, 0.05, 2.00),
    参数定义("背景展示周期", "背景展示", "s", 0.01, 0.05, 0.05, 3.00),
    参数定义("背景蒙版展示周期", "蒙版展示", "s", 0.01, 0.05, 0.05, 1.50),
    参数定义("判定区显示周期", "判定区展示", "s", 0.01, 0.05, 0.05, 1.50),
    参数定义("血条组入场周期", "血条组入场", "s", 0.01, 0.05, 0.05, 2.00),
    参数定义("场景引导入场周期", "引导入场", "s", 0.01, 0.05, 0.05, 1.50),
    参数定义("背景板入场周期", "条幅入场", "s", 0.01, 0.05, 0.05, 1.50),
    参数定义("背景板高度比例", "条幅高度", "", 0.01, 0.05, 0.35, 2.20),
    参数定义("背景板装饰运动速度", "箭头速度", "px/s", 1.0, 10.0, 40.0, 900.0, 1),
    参数定义("背景板装饰高度比例", "箭头高度", "", 0.01, 0.05, 0.10, 1.20),
    参数定义("提示1缩放幅度", "READY 拉伸", "", 0.01, 0.05, 0.01, 1.00),
    参数定义("提示1缩放周期", "READY 时长", "s", 0.01, 0.05, 0.05, 2.50),
    参数定义("提示1高度比例", "READY 高度", "", 0.01, 0.05, 0.20, 0.95),
    参数定义("提示2缩放幅度", "START 拉伸", "", 0.01, 0.05, 0.01, 1.00),
    参数定义("提示2缩放周期", "START 时长", "s", 0.01, 0.05, 0.05, 3.00),
    参数定义("提示2高度比例", "START 高度", "", 0.01, 0.05, 0.20, 0.95),
    参数定义("场景引导出场周期", "引导退场", "s", 0.01, 0.05, 0.05, 1.50),
    参数定义("场景引导暗度", "场景暗度", "", 0.01, 0.05, 0.00, 1.00),
    参数定义("背景蒙版透明度", "蒙版透明度", "", 1.0, 8.0, 0.0, 255.0, 0),
    参数定义("提示间隔周期", "提示间隔", "s", 0.01, 0.05, 0.00, 1.00),
]


def _求并集矩形(项列表: List[dict]) -> Optional[pygame.Rect]:
    矩形们: List[pygame.Rect] = []
    for 项 in 项列表:
        if not isinstance(项, dict):
            continue
        矩形 = 项.get("rect")
        if isinstance(矩形, pygame.Rect):
            矩形们.append(矩形)
    if not 矩形们:
        return None
    结果 = 矩形们[0].copy()
    for 矩形 in 矩形们[1:]:
        结果.union_ip(矩形)
    return 结果


def _扩成顶部条区域(矩形: Optional[pygame.Rect], 屏幕尺寸: Tuple[int, int]) -> pygame.Rect:
    屏宽, 屏高 = int(max(1, 屏幕尺寸[0])), int(max(1, 屏幕尺寸[1]))
    if not isinstance(矩形, pygame.Rect):
        return pygame.Rect(0, 0, 屏宽, max(160, int(屏高 * 0.14)))
    return pygame.Rect(0, 0, 屏宽, min(屏高, int(矩形.bottom + 26)))


def _载入背景原图(背景路径: Optional[str]) -> Optional[pygame.Surface]:
    if not 背景路径 or (not os.path.isfile(背景路径)):
        return None
    try:
        return pygame.image.load(背景路径).convert()
    except Exception:
        return None


def _载入准备音效(项目根: str) -> Optional[pygame.mixer.Sound]:
    准备音效路径 = os.path.join(项目根, "冷资源", "backsound", "准备就绪音效.mp3")
    try:
        if pygame.mixer.get_init() and os.path.isfile(准备音效路径):
            return pygame.mixer.Sound(准备音效路径)
    except Exception:
        return None
    return None


def _取默认箭头皮肤路径(项目根: str) -> str:
    皮肤编号列表 = 布局调试器._收集可用箭头皮肤编号(项目根)
    if "02" in 皮肤编号列表:
        目标编号 = "02"
    elif "03" in 皮肤编号列表:
        目标编号 = "03"
    else:
        目标编号 = str((皮肤编号列表 or ["03"])[0])
    return os.path.join(项目根, "UI-img", "游戏界面", "箭头", 目标编号)


def _创建调试资源(项目根: str) -> 调试资源:
    字体 = 获取字体(20, False)
    小字体 = 获取字体(16, False)
    布局路径 = os.path.join(项目根, "json", "谱面渲染器_布局.json")
    头像图, 玩家昵称 = 布局调试器._尝试加载头像与昵称(项目根)
    准备渲染器 = 谱面渲染器()
    try:
        准备渲染器.设置皮肤(_取默认箭头皮肤路径(项目根))
    except Exception:
        pass
    return 调试资源(
        字体=字体,
        小字体=小字体,
        布局管理器=谱面渲染器布局管理器(布局路径),
        皮肤包=布局调试器._加载皮肤包(项目根),
        准备渲染器=准备渲染器,
        头像图=头像图,
        玩家昵称=玩家昵称,
        段位图=布局调试器._尝试加载段位图(项目根),
        背景原图=_载入背景原图(布局调试器._尝试加载背景图(项目根)),
        准备图片=加载准备动画图片(项目根),
        准备音效=_载入准备音效(项目根),
    )


def _停止准备音效(状态: 调试器状态):
    try:
        if 状态.准备音效通道 is not None:
            状态.准备音效通道.stop()
    except Exception:
        pass
    状态.准备音效通道 = None


def _同步音效标记(状态: 调试器状态, 时间轴: Dict[str, float]):
    状态.准备音效已播放 = 状态.预览秒 >= float(时间轴.get("引导开始", 0.0))


def _设定预览秒(
    状态: 调试器状态,
    时间轴: Dict[str, float],
    目标秒: float,
    保持播放: bool = False,
):
    总时长 = float(时间轴.get("总时长", 0.0))
    状态.预览秒 = max(0.0, min(float(目标秒), 总时长))
    _停止准备音效(状态)
    _同步音效标记(状态, 时间轴)
    if 保持播放:
        状态.播放中 = True
        状态.播放开始系统秒 = float(pygame.time.get_ticks()) / 1000.0 - 状态.预览秒
    else:
        状态.播放中 = False


def _重播(状态: 调试器状态, 时间轴: Dict[str, float]):
    状态.拖动时间轴 = False
    状态.播放开始系统秒 = float(pygame.time.get_ticks()) / 1000.0
    状态.预览秒 = 0.0
    状态.播放中 = True
    状态.准备音效已播放 = False
    _停止准备音效(状态)


def _切换播放暂停(状态: 调试器状态, 时间轴: Dict[str, float]):
    if 状态.播放中:
        状态.播放中 = False
        _停止准备音效(状态)
        return
    _设定预览秒(状态, 时间轴, 状态.预览秒, 保持播放=True)


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
        设置[定义.键] = float(默认准备动画设置().get(定义.键, 0.0))
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
        and 状态.背景缓存尺寸 == 目标尺寸
    ):
        return 状态.背景缓存图
    try:
        原宽, 原高 = 图像.get_size()
        比例 = max(
            float(目标尺寸[0]) / float(max(1, 原宽)),
            float(目标尺寸[1]) / float(max(1, 原高)),
        )
        新宽 = max(2, int(round(原宽 * 比例)))
        新高 = max(2, int(round(原高 * 比例)))
        缩放图 = pygame.transform.smoothscale(图像, (新宽, 新高)).convert()
        结果 = pygame.Surface(目标尺寸).convert()
        结果.blit(缩放图, 缩放图.get_rect(center=(目标尺寸[0] // 2, 目标尺寸[1] // 2)))
        状态.背景缓存尺寸 = 目标尺寸
        状态.背景缓存图 = 结果
        return 结果
    except Exception:
        状态.背景缓存图 = None
        状态.背景缓存尺寸 = (0, 0)
        return None


def _构建准备动画预览(
    屏幕尺寸: Tuple[int, int],
    状态: 调试器状态,
    资源: 调试资源,
) -> Tuple[pygame.Surface, 渲染输入]:
    屏宽, 屏高 = int(max(1, 屏幕尺寸[0])), int(max(1, 屏幕尺寸[1]))
    背景图 = _画cover缓存(状态, 资源.背景原图, (屏宽, 屏高))
    if 背景图 is None:
        背景图 = pygame.Surface((屏宽, 屏高)).convert()
        背景图.fill((18, 18, 24))
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
    轨道中心列表 = [
        int(轨道起x + 轨道槽宽 // 2 + i * 轨道中心间距) for i in range(5)
    ]
    血条区域 = pygame.Rect(0, 0, 屏宽, max(160, int(屏高 * 0.14)))
    输入 = 渲染输入(
        当前谱面秒=0.0,
        总时长秒=85.0,
        轨道中心列表=轨道中心列表,
        判定线y=int(判定线y),
        底部y=int(底部y),
        滚动速度px每秒=620.0,
        箭头目标宽=int(箭头目标宽),
        事件列表=[],
        显示_判定="",
        显示_连击=0,
        显示_分数=0,
        显示_百分比="0.00%",
        血条区域=血条区域,
        血量显示=0.5,
        头像图=资源.头像图,
        总血量HP=1000,
        可见血量HP=500,
        Note层灰度=False,
        血条暴走=False,
        玩家序号=1,
        玩家昵称=资源.玩家昵称,
        段位图=资源.段位图,
        当前关卡=1,
        歌曲名="ARE YOU READY TEST",
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
        圆环频谱对象=None,
    )
    return 背景图, 输入


def _计算控制布局(
    屏幕尺寸: Tuple[int, int],
    状态: 调试器状态,
) -> Dict[str, Any]:
    屏宽, 屏高 = int(max(1, 屏幕尺寸[0])), int(max(1, 屏幕尺寸[1]))
    面板 = pygame.Rect(16, 16, 430, max(420, 屏高 - 32))
    按钮高 = 34
    小按钮宽 = 102
    大按钮宽 = 面板.w - 24 - 小按钮宽 * 2 - 8 * 2
    播放按钮 = pygame.Rect(面板.x + 12, 面板.y + 12, 大按钮宽, 按钮高)
    暂停按钮 = pygame.Rect(播放按钮.right + 8, 播放按钮.y, 小按钮宽, 按钮高)
    重置按钮 = pygame.Rect(暂停按钮.right + 8, 播放按钮.y, 小按钮宽, 按钮高)
    循环框 = pygame.Rect(面板.x + 12, 播放按钮.bottom + 12, 20, 20)
    状态文本位置 = (面板.x + 12, 循环框.bottom + 10)
    时间轴标签位置 = (面板.x + 12, 循环框.bottom + 38)
    时间轴 = pygame.Rect(面板.x + 12, 循环框.bottom + 62, 面板.w - 24, 14)
    参数区起始y = 时间轴.bottom + 22
    帮助区高 = 74
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

    行布局: List[Dict[str, Any]] = []
    当前y = 参数视口.y
    起始索引 = int(状态.参数滚动)
    for 索引 in range(起始索引, min(len(参数定义列表), 起始索引 + 可见行数)):
        行rect = pygame.Rect(参数视口.x, 当前y, 参数视口.w, 行高)
        减rect = pygame.Rect(行rect.right - 76, 行rect.y + 4, 30, 26)
        加rect = pygame.Rect(行rect.right - 36, 行rect.y + 4, 30, 26)
        行布局.append(
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
        "播放按钮": 播放按钮,
        "暂停按钮": 暂停按钮,
        "重置按钮": 重置按钮,
        "循环框": 循环框,
        "状态文本位置": 状态文本位置,
        "时间轴标签位置": 时间轴标签位置,
        "时间轴": 时间轴,
        "参数视口": 参数视口,
        "参数行": 行布局,
        "帮助起始y": 面板.bottom - 帮助区高,
        "可见行数": 可见行数,
    }


def _时间轴位置转秒(
    x坐标: int,
    时间轴rect: pygame.Rect,
    时间轴: Dict[str, float],
) -> float:
    if 时间轴rect.w <= 1:
        return 0.0
    比例 = (float(x坐标) - float(时间轴rect.x)) / float(max(1, 时间轴rect.w))
    比例 = max(0.0, min(1.0, 比例))
    return 比例 * float(时间轴.get("总时长", 0.0))


def _绘制按钮(
    屏幕: pygame.Surface,
    字体: pygame.font.Font,
    矩形: pygame.Rect,
    文本: str,
    背景色: Tuple[int, int, int],
    边框色: Tuple[int, int, int],
):
    pygame.draw.rect(屏幕, 背景色, 矩形, border_radius=8)
    pygame.draw.rect(屏幕, 边框色, 矩形, width=1, border_radius=8)
    文图 = 字体.render(文本, True, (255, 255, 255))
    屏幕.blit(
        文图,
        (
            矩形.x + (矩形.w - 文图.get_width()) // 2,
            矩形.y + (矩形.h - 文图.get_height()) // 2,
        ),
    )


def _绘制控制面板(
    屏幕: pygame.Surface,
    资源: 调试资源,
    状态: 调试器状态,
    设置: Dict[str, float],
    时间轴: Dict[str, float],
    布局: Dict[str, Any],
):
    面板 = 布局["面板"]
    面板底 = pygame.Surface((面板.w, 面板.h), pygame.SRCALPHA)
    面板底.fill((7, 10, 18, 208))
    屏幕.blit(面板底, 面板.topleft)
    pygame.draw.rect(屏幕, (216, 225, 246), 面板, width=1, border_radius=12)

    _绘制按钮(屏幕, 资源.字体, 布局["播放按钮"], "从头播放", (74, 119, 210), (180, 205, 255))
    暂停文本 = "暂停" if 状态.播放中 else "继续"
    _绘制按钮(屏幕, 资源.字体, 布局["暂停按钮"], 暂停文本, (58, 72, 110), (170, 186, 228))
    _绘制按钮(屏幕, 资源.字体, 布局["重置按钮"], "恢复默认", (110, 76, 58), (238, 194, 162))

    循环框 = 布局["循环框"]
    pygame.draw.rect(屏幕, (88, 92, 118), 循环框, border_radius=4)
    pygame.draw.rect(屏幕, (220, 228, 255), 循环框, width=1, border_radius=4)
    if 状态.循环播放:
        pygame.draw.line(
            屏幕,
            (255, 255, 255),
            (循环框.x + 4, 循环框.y + 10),
            (循环框.x + 8, 循环框.bottom - 5),
            2,
        )
        pygame.draw.line(
            屏幕,
            (255, 255, 255),
            (循环框.x + 8, 循环框.bottom - 5),
            (循环框.right - 4, 循环框.y + 5),
            2,
        )
    循环图 = 资源.小字体.render("循环播放", True, (240, 242, 248))
    屏幕.blit(
        循环图,
        (循环框.right + 8, 循环框.y + (循环框.h - 循环图.get_height()) // 2),
    )

    总时长 = float(时间轴.get("总时长", 0.0))
    状态文本 = (
        f"当前 {状态.预览秒:.2f}s / {总时长:.2f}s"
        f"  {'播放中' if 状态.播放中 else '暂停中'}"
    )
    状态图 = 资源.小字体.render(状态文本, True, (240, 240, 245))
    屏幕.blit(状态图, 布局["状态文本位置"])

    时间轴标签图 = 资源.小字体.render("时间轴", True, (245, 245, 252))
    屏幕.blit(时间轴标签图, 布局["时间轴标签位置"])

    时间轴rect = 布局["时间轴"]
    pygame.draw.rect(屏幕, (52, 58, 78), 时间轴rect, border_radius=7)
    pygame.draw.rect(屏幕, (122, 136, 188), 时间轴rect, width=1, border_radius=7)
    if 总时长 > 0.0:
        进度宽 = int(round(时间轴rect.w * max(0.0, min(1.0, 状态.预览秒 / 总时长))))
        if 进度宽 > 0:
            已播rect = pygame.Rect(时间轴rect.x, 时间轴rect.y, 进度宽, 时间轴rect.h)
            pygame.draw.rect(屏幕, (183, 92, 228), 已播rect, border_radius=7)
        for 键, 名称, 颜色 in (
            ("引导开始", "IN", (126, 210, 255)),
            ("提示1开始", "READY", (255, 212, 102)),
            ("提示2开始", "START", (255, 146, 170)),
            ("引导结束", "OUT", (180, 255, 188)),
        ):
            秒 = float(时间轴.get(键, 0.0))
            比例 = max(0.0, min(1.0, 秒 / 总时长))
            x = int(round(时间轴rect.x + 时间轴rect.w * 比例))
            pygame.draw.line(屏幕, 颜色, (x, 时间轴rect.y - 5), (x, 时间轴rect.bottom + 5), 1)
            标记图 = 资源.小字体.render(名称, True, 颜色)
            屏幕.blit(标记图, (x - 标记图.get_width() // 2, 时间轴rect.y - 20))
    手柄x = int(round(时间轴rect.x + 时间轴rect.w * max(0.0, min(1.0, 状态.预览秒 / max(0.001, 总时长)))))
    pygame.draw.circle(屏幕, (248, 248, 255), (手柄x, 时间轴rect.centery), 7)
    pygame.draw.circle(屏幕, (128, 86, 215), (手柄x, 时间轴rect.centery), 7, 1)

    参数标题 = 资源.字体.render("参数", True, (255, 245, 170))
    屏幕.blit(参数标题, (布局["参数视口"].x, 布局["参数视口"].y - 28))
    滚动信息 = f"{状态.选中参数索引 + 1}/{len(参数定义列表)}"
    滚动图 = 资源.小字体.render(滚动信息, True, (205, 214, 236))
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
        "Space 暂停/继续，Enter 重播，R 恢复默认",
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
):
    设置.clear()
    设置.update(默认准备动画设置())
    保存准备动画设置(设置路径, 设置)
    _设定预览秒(状态, 计算准备动画时间轴(设置), 0.0, 保持播放=False)


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

    资源 = _创建调试资源(项目根)
    状态 = 调试器状态()

    while True:
        时钟.tick(60)
        时间轴 = 计算准备动画时间轴(设置)
        总时长 = float(时间轴.get("总时长", 0.0))

        if 状态.播放中 and (not 状态.拖动时间轴):
            当前系统秒 = float(pygame.time.get_ticks()) / 1000.0
            状态.预览秒 = max(0.0, 当前系统秒 - float(状态.播放开始系统秒))
            if (not 状态.准备音效已播放) and 状态.预览秒 >= float(时间轴.get("引导开始", 0.0)):
                try:
                    if 资源.准备音效 is not None:
                        状态.准备音效通道 = 资源.准备音效.play()
                except Exception:
                    状态.准备音效通道 = None
                状态.准备音效已播放 = True
            if 状态.预览秒 >= 总时长:
                if 状态.循环播放 and 总时长 > 0.0:
                    _重播(状态, 时间轴)
                else:
                    _设定预览秒(状态, 时间轴, 总时长, 保持播放=False)

        布局 = _计算控制布局(屏幕.get_size(), 状态)

        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                _停止准备音效(状态)
                pygame.quit()
                return

            if 事件.type == pygame.VIDEORESIZE:
                屏幕 = pygame.display.set_mode(
                    (max(960, 事件.w), max(540, 事件.h)),
                    pygame.RESIZABLE,
                )
                布局 = _计算控制布局(屏幕.get_size(), 状态)
                continue

            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    _停止准备音效(状态)
                    pygame.quit()
                    return
                if 事件.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    保存准备动画设置(设置路径, 设置)
                elif 事件.key == pygame.K_RETURN:
                    _重播(状态, 时间轴)
                elif 事件.key in (pygame.K_SPACE, pygame.K_p):
                    _切换播放暂停(状态, 时间轴)
                elif 事件.key == pygame.K_r:
                    _重置为默认设置(设置, 设置路径, 状态)
                elif 事件.key == pygame.K_HOME:
                    _设定预览秒(状态, 时间轴, 0.0, 保持播放=False)
                elif 事件.key == pygame.K_END:
                    _设定预览秒(状态, 时间轴, 总时长, 保持播放=False)
                elif 事件.key == pygame.K_UP:
                    状态.选中参数索引 = max(0, int(状态.选中参数索引) - 1)
                elif 事件.key == pygame.K_DOWN:
                    状态.选中参数索引 = min(
                        len(参数定义列表) - 1,
                        int(状态.选中参数索引) + 1,
                    )
                elif 事件.key == pygame.K_LEFT:
                    当前定义 = 参数定义列表[int(状态.选中参数索引)]
                    if _调整参数(设置, 当前定义, -1, bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)):
                        保存准备动画设置(设置路径, 设置)
                elif 事件.key == pygame.K_RIGHT:
                    当前定义 = 参数定义列表[int(状态.选中参数索引)]
                    if _调整参数(设置, 当前定义, +1, bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)):
                        保存准备动画设置(设置路径, 设置)
                布局 = _计算控制布局(屏幕.get_size(), 状态)
                continue

            if 事件.type == pygame.MOUSEBUTTONDOWN:
                if 事件.button == 1:
                    if 布局["播放按钮"].collidepoint(事件.pos):
                        _重播(状态, 时间轴)
                        continue
                    if 布局["暂停按钮"].collidepoint(事件.pos):
                        _切换播放暂停(状态, 时间轴)
                        continue
                    if 布局["重置按钮"].collidepoint(事件.pos):
                        _重置为默认设置(设置, 设置路径, 状态)
                        continue
                    if 布局["循环框"].collidepoint(事件.pos):
                        状态.循环播放 = not bool(状态.循环播放)
                        continue
                    if 布局["时间轴"].collidepoint(事件.pos):
                        状态.拖动时间轴 = True
                        _设定预览秒(
                            状态,
                            时间轴,
                            _时间轴位置转秒(事件.pos[0], 布局["时间轴"], 时间轴),
                            保持播放=False,
                        )
                        continue
                    for 行 in 布局["参数行"]:
                        索引 = int(行["索引"])
                        定义: 参数定义 = 行["定义"]
                        if 行["减rect"].collidepoint(事件.pos):
                            状态.选中参数索引 = 索引
                            if _调整参数(设置, 定义, -1, False):
                                保存准备动画设置(设置路径, 设置)
                            break
                        if 行["加rect"].collidepoint(事件.pos):
                            状态.选中参数索引 = 索引
                            if _调整参数(设置, 定义, +1, False):
                                保存准备动画设置(设置路径, 设置)
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
                _设定预览秒(
                    状态,
                    时间轴,
                    _时间轴位置转秒(事件.pos[0], 布局["时间轴"], 时间轴),
                    保持播放=False,
                )
                continue

        背景图, 准备渲染输入 = _构建准备动画预览(
            屏幕.get_size(),
            状态,
            资源,
        )
        资源.准备渲染器.绘制准备动画底层(
            屏幕,
            准备渲染输入,
            设置,
            float(状态.预览秒),
            背景无蒙版图=背景图,
            绘制判定组=True,
        )
        绘制准备就绪动画(
            屏幕=屏幕,
            基础场景图=None,
            背景无蒙版图=None,
            准备图片=资源.准备图片,
            设置=设置,
            经过秒=float(状态.预览秒),
            判定区矩形=pygame.Rect(0, 0, 0, 0),
            顶部HUD矩形=pygame.Rect(0, 0, 0, 0),
            顶部HUD图层=None,
            判定区图层=None,
            运行缓存=状态.准备绘制缓存,
            仅前景=True,
        )
        _绘制控制面板(屏幕, 资源, 状态, 设置, 时间轴, 布局)
        pygame.display.flip()


if __name__ == "__main__":
    主函数()
