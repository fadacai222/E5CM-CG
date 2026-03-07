import json
import os
import sys
import time

import pygame

from core.常量与路径 import 默认资源路径
from core.工具 import 获取字体
from scenes.场景_结算 import 场景_结算


def _取项目根目录() -> str:
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.path.abspath(os.getcwd())


def _读取json(路径: str) -> dict:
    if (not 路径) or (not os.path.isfile(路径)):
        return {}
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码) as 文件:
                数据 = json.load(文件)
            return 数据 if isinstance(数据, dict) else {}
        except Exception:
            continue
    return {}


def _创建窗口(尺寸: tuple[int, int], 标志: int) -> pygame.Surface:
    请求标志 = int(标志 | pygame.DOUBLEBUF | pygame.HWSURFACE)
    try:
        return pygame.display.set_mode(尺寸, 请求标志, vsync=1)
    except TypeError:
        try:
            return pygame.display.set_mode(尺寸, 请求标志)
        except Exception:
            return pygame.display.set_mode(尺寸, 标志)
    except Exception:
        try:
            return pygame.display.set_mode(尺寸, 请求标志)
        except Exception:
            return pygame.display.set_mode(尺寸, 标志)


def _构建测试载荷(项目根: str, 玩家序号: int = 1) -> dict:
    加载页数据 = _读取json(os.path.join(项目根, "json", "加载页.json"))
    歌曲名 = str(加载页数据.get("歌曲名", "") or "Korean Girls Pop Song Party")
    封面路径 = str(加载页数据.get("封面路径", "") or "")
    if 封面路径 and (not os.path.isabs(封面路径)):
        封面路径 = os.path.join(
            项目根, 封面路径.replace("/", os.sep).replace("\\", os.sep)
        )
    背景图片路径 = str(加载页数据.get("背景图路径", "") or "")
    if 背景图片路径 and (not os.path.isabs(背景图片路径)):
        背景图片路径 = os.path.join(
            项目根, 背景图片路径.replace("/", os.sep).replace("\\", os.sep)
        )
    背景视频路径 = str(加载页数据.get("背景视频路径", "") or "")
    if 背景视频路径 and (not os.path.isabs(背景视频路径)):
        背景视频路径 = os.path.join(
            项目根, 背景视频路径.replace("/", os.sep).replace("\\", os.sep)
        )

    return {
        "玩家序号": int(2 if int(玩家序号) == 2 else 1),
        "曲目名": 歌曲名,
        "sm路径": str(加载页数据.get("sm路径", "") or ""),
        "模式": str(加载页数据.get("模式", "竞速") or "竞速"),
        "类型": str(加载页数据.get("类型", "竞速") or "竞速"),
        "本局最高分": 47764800,
        "本局最大combo": 832,
        "歌曲时长秒": 142.0,
        "谱面总分": 47764800,
        "百分比": "98.76%",
        "百分比数值": 98.76,
        "评级": "S",
        "是否评价S": True,
        "失败": False,
        "当前关卡": 1,
        "局数": 1,
        "结算前S数": 2,
        "结算后S数": 3,
        "累计S数": 3,
        "三把S赠送": False,
        "是否赠送第四把": False,
        "perfect数": 832,
        "cool数": 0,
        "good数": 0,
        "miss数": 0,
        "是否全连": True,
        "全连": True,
        "封面路径": 封面路径,
        "星级": int(加载页数据.get("星级", 7) or 7),
        "背景图片路径": 背景图片路径,
        "背景视频路径": 背景视频路径,
        "选歌原始索引": int(加载页数据.get("选歌原始索引", -1) or -1),
    }


def _构建调试按钮(屏幕宽: int) -> list[dict]:
    按钮定义 = [
        ("自然流程", "自然流程"),
        ("经验普通", "经验普通"),
        ("花式升级", "花式升级"),
        ("竞速升级", "竞速升级"),
        ("下一把", "下一把"),
        ("继续挑战", "继续挑战"),
        ("是否续币", "是否续币"),
        ("游戏结束", "游戏结束"),
        ("赠送一把", "赠送一把"),
        ("重播当前", "重播当前"),
    ]
    按钮列表: list[dict] = []
    x = 16
    y = 78
    按钮高 = 34
    间距 = 8

    for 标题, 模式名 in 按钮定义:
        按钮宽 = max(92, 24 + len(标题) * 18)
        if x + 按钮宽 > 屏幕宽 - 16:
            x = 16
            y += 按钮高 + 8
        按钮列表.append(
            {
                "标题": 标题,
                "模式": 模式名,
                "rect": pygame.Rect(x, y, 按钮宽, 按钮高),
            }
        )
        x += 按钮宽 + 间距

    return 按钮列表


def _强制进入流程2(场景对象: 场景_结算):
    当前系统秒 = time.perf_counter()
    try:
        场景对象._进入系统秒 = 当前系统秒 - float(float(场景对象._流程1时长秒) + 0.02)
    except Exception:
        场景对象._进入系统秒 = 当前系统秒 - 3.02


def _构建奖励调试数据(场景对象: 场景_结算, 模式名: str) -> dict:
    原奖励数据 = dict(getattr(场景对象, "_奖励数据", {}) or {})
    原花式 = dict(原奖励数据.get("花式", {}) or {})
    原竞速 = dict(原奖励数据.get("竞速", {}) or {})
    段位路径 = str(原奖励数据.get("段位路径", "") or "")

    def _构建单模式数据(
        原等级: int,
        原经验: float,
        新等级: int,
        新经验: float,
    ) -> dict:
        return {
            "原等级": int(原等级),
            "原经验": float(原经验),
            "等级": int(新等级),
            "经验": float(新经验),
        }

    花式默认等级 = int(原花式.get("等级", 12) or 12)
    花式默认经验 = float(原花式.get("经验", 0.35) or 0.35)
    竞速默认等级 = int(原竞速.get("等级", 8) or 8)
    竞速默认经验 = float(原竞速.get("经验", 0.42) or 0.42)

    if 模式名 == "经验普通":
        花式数据 = _构建单模式数据(12, 0.28, 12, 0.38)
        竞速数据 = _构建单模式数据(
            竞速默认等级, 竞速默认经验, 竞速默认等级, 竞速默认经验
        )
        return {
            "经验增加值": 10,
            "是否升级": False,
            "升级模式": "",
            "花式": 花式数据,
            "竞速": 竞速数据,
            "段位路径": 段位路径,
        }

    if 模式名 == "花式升级":
        花式数据 = _构建单模式数据(12, 0.92, 13, 0.08)
        竞速数据 = _构建单模式数据(
            竞速默认等级, 竞速默认经验, 竞速默认等级, 竞速默认经验
        )
        return {
            "经验增加值": 16,
            "是否升级": True,
            "升级模式": "花式",
            "花式": 花式数据,
            "竞速": 竞速数据,
            "段位路径": 段位路径,
        }

    if 模式名 == "竞速升级":
        花式数据 = _构建单模式数据(
            花式默认等级, 花式默认经验, 花式默认等级, 花式默认经验
        )
        竞速数据 = _构建单模式数据(8, 0.94, 9, 0.10)
        return {
            "经验增加值": 16,
            "是否升级": True,
            "升级模式": "竞速",
            "花式": 花式数据,
            "竞速": 竞速数据,
            "段位路径": 段位路径,
        }

    return dict(原奖励数据 or {})


def _应用奖励调试模式(场景对象: 场景_结算, 模式名: str):
    if 模式名 not in ("经验普通", "花式升级", "竞速升级"):
        return

    _强制进入流程2(场景对象)

    try:
        场景对象._流程3退出动作 = None
        场景对象._流程3退出开始秒 = 0.0
        场景对象._流程3提示键 = ""
        场景对象._流程3阶段类型 = ""
        场景对象._流程3阶段持续秒 = 0.0
        场景对象._流程3是否显示倒计时 = False
        场景对象._流程3按钮选中 = "是"
        场景对象._流程3续币基准值 = 0
    except Exception:
        pass

    try:
        场景对象._奖励数据 = _构建奖励调试数据(场景对象, 模式名)
    except Exception:
        pass


def _强制进入流程3(场景对象: 场景_结算):
    当前系统秒 = time.perf_counter()
    try:
        场景对象._进入系统秒 = 当前系统秒 - float(
            float(场景对象._流程1时长秒) + float(场景对象._流程2时长秒) + 0.02
        )
    except Exception:
        场景对象._进入系统秒 = 当前系统秒 - 6.02


def _重置流程3调试状态(场景对象: 场景_结算, 游戏状态: dict):
    当前系统秒 = time.perf_counter()
    场景对象._流程3退出动作 = None
    场景对象._流程3退出开始秒 = 0.0
    场景对象._流程3提示键 = ""
    场景对象._流程3阶段类型 = ""
    场景对象._流程3阶段持续秒 = 0.0
    场景对象._流程3是否显示倒计时 = False
    场景对象._流程3按钮选中 = "是"
    场景对象._流程3续币基准值 = 0
    场景对象._流程3每局所需信用 = int(游戏状态.get("每局所需信用", 3) or 3)
    场景对象._流程3默认否动作 = {"类型": "投币"}
    场景对象._流程3继续动作 = {
        **场景对象._构建返回选歌动作(),
        "下一关卡": 2,
        "重开新局": False,
        "累计S数": int(getattr(场景对象, "_流程3结算后S数", 0) or 0),
        "赠送第四把": False,
        "消耗信用": int(场景对象._流程3每局所需信用),
    }
    场景对象._流程3阶段开始秒 = 当前系统秒
    try:
        场景对象._流程3计时已启动 = True
    except Exception:
        pass
    _强制进入流程3(场景对象)


def _应用流程3调试模式(场景对象: 场景_结算, 游戏状态: dict, 模式名: str):
    if 模式名 == "自然流程":
        return

    _重置流程3调试状态(场景对象, 游戏状态)

    if 模式名 == "下一把":
        游戏状态["投币数"] = 3
        场景对象._流程3阶段类型 = "自动提示"
        场景对象._流程3提示键 = "下一把"
        场景对象._流程3阶段持续秒 = 5.0
        场景对象._流程3是否显示倒计时 = False
        return

    if 模式名 == "继续挑战":
        游戏状态["投币数"] = int(游戏状态.get("每局所需信用", 3) or 3)
        场景对象._流程3阶段类型 = "继续挑战"
        场景对象._流程3提示键 = "继续挑战"
        场景对象._流程3阶段持续秒 = 10.0
        场景对象._流程3是否显示倒计时 = True
        return

    if 模式名 == "是否续币":
        游戏状态["投币数"] = 0
        场景对象._流程3阶段类型 = "续币等待"
        场景对象._流程3提示键 = "是否续币"
        场景对象._流程3阶段持续秒 = 10.0
        场景对象._流程3是否显示倒计时 = True
        场景对象._流程3续币基准值 = 0
        return

    if 模式名 == "游戏结束":
        游戏状态["投币数"] = 0
        场景对象._流程3阶段类型 = "自动提示"
        场景对象._流程3提示键 = "游戏结束"
        场景对象._流程3阶段持续秒 = 5.0
        场景对象._流程3是否显示倒计时 = False
        场景对象._流程3继续动作 = {"类型": "投币"}
        return

    if 模式名 == "赠送一把":
        游戏状态["投币数"] = 3
        场景对象._流程3阶段类型 = "自动提示"
        场景对象._流程3提示键 = "赠送一把"
        场景对象._流程3阶段持续秒 = 5.0
        场景对象._流程3是否显示倒计时 = False
        return


def _绘制调试面板(
    屏幕: pygame.Surface,
    小字体: pygame.font.Font,
    按钮字体: pygame.font.Font,
    按钮列表: list[dict],
    当前模式: str,
    玩家序号: int,
    场景对象: 场景_结算,
):
    信息1 = "F5 重建  1=1P左侧  2=2P右侧  ESC退出"
    信息2 = "F2经验普通  F3花式升级  F4竞速升级  F6下一把  F7继续挑战  F8是否续币  F9游戏结束  F10赠送一把"
    try:
        图1 = 小字体.render(信息1, True, (255, 240, 180)).convert_alpha()
        图2 = 小字体.render(信息2, True, (190, 225, 255)).convert_alpha()
        背板宽 = int(max(图1.get_width(), 图2.get_width()) + 16)
        背板高 = int(图1.get_height() + 图2.get_height() + 18)
        背板 = pygame.Surface((背板宽, 背板高), pygame.SRCALPHA)
        背板.fill((0, 0, 0, 160))
        屏幕.blit(背板, (16, 16))
        屏幕.blit(图1, (24, 22))
        屏幕.blit(图2, (24, int(26 + 图1.get_height())))
    except Exception:
        pass

    鼠标坐标 = pygame.mouse.get_pos()
    for 按钮 in 按钮列表:
        区域: pygame.Rect = 按钮["rect"]
        标题 = str(按钮["标题"])
        模式名 = str(按钮["模式"])
        是否当前 = 模式名 == 当前模式
        是否悬停 = 区域.collidepoint(鼠标坐标)

        if 是否当前:
            颜色 = (58, 126, 82, 220)
            边框色 = (180, 255, 200, 255)
        elif 是否悬停:
            颜色 = (72, 72, 96, 220)
            边框色 = (255, 255, 210, 255)
        else:
            颜色 = (28, 28, 38, 200)
            边框色 = (120, 120, 145, 255)

        按钮板 = pygame.Surface((区域.w, 区域.h), pygame.SRCALPHA)
        pygame.draw.rect(按钮板, 颜色, 按钮板.get_rect(), border_radius=10)
        pygame.draw.rect(按钮板, 边框色, 按钮板.get_rect(), width=2, border_radius=10)
        屏幕.blit(按钮板, 区域.topleft)

        try:
            文字图 = 按钮字体.render(标题, True, (245, 245, 245)).convert_alpha()
            文字区域 = 文字图.get_rect(center=区域.center)
            屏幕.blit(文字图, 文字区域.topleft)
        except Exception:
            pass

    try:
        经过秒 = max(
            0.0, float(time.perf_counter() - float(场景对象._进入系统秒 or 0.0))
        )
        流程阶段, 阶段秒 = 场景对象._取流程阶段(经过秒)
        当前提示 = str(getattr(场景对象, "_流程3提示键", "") or "无")
        当前类型 = str(getattr(场景对象, "_流程3阶段类型", "") or "无")
        剩余秒 = 0.0
        if int(流程阶段) == 3:
            try:
                剩余秒 = max(
                    0.0,
                    float(getattr(场景对象, "_流程3阶段持续秒", 0.0) or 0.0)
                    - float(场景对象._取流程3已持续秒()),
                )
            except Exception:
                剩余秒 = 0.0

        奖励数据 = dict(getattr(场景对象, "_奖励数据", {}) or {})
        花式数据 = dict(奖励数据.get("花式", {}) or {})
        竞速数据 = dict(奖励数据.get("竞速", {}) or {})

        状态文本 = [
            f"当前玩家: P{玩家序号}",
            f"当前调试模式: {当前模式}",
            f"流程阶段: {流程阶段}",
            f"流程3类型: {当前类型}",
            f"流程3提示: {当前提示}",
            f"阶段秒: {阶段秒:.2f}",
            f"剩余秒: {剩余秒:.2f}",
            f"经验增加值: {int(奖励数据.get('经验增加值', 0) or 0)}",
            f"升级模式: {str(奖励数据.get('升级模式', '') or '无')}",
            f"花式: Lv{int(花式数据.get('原等级', 0) or 0)} {float(花式数据.get('原经验', 0.0) or 0.0):.2f} -> Lv{int(花式数据.get('等级', 0) or 0)} {float(花式数据.get('经验', 0.0) or 0.0):.2f}",
            f"竞速: Lv{int(竞速数据.get('原等级', 0) or 0)} {float(竞速数据.get('原经验', 0.0) or 0.0):.2f} -> Lv{int(竞速数据.get('等级', 0) or 0)} {float(竞速数据.get('经验', 0.0) or 0.0):.2f}",
        ]

        y = 130 if len(按钮列表) <= 7 else 170
        for 文本 in 状态文本:
            文本图 = 小字体.render(文本, True, (235, 235, 235)).convert_alpha()
            文本底 = pygame.Surface(
                (文本图.get_width() + 12, 文本图.get_height() + 6), pygame.SRCALPHA
            )
            文本底.fill((0, 0, 0, 140))
            屏幕.blit(文本底, (16, y))
            屏幕.blit(文本图, (22, y + 3))
            y += 文本底.get_height() + 4
    except Exception:
        pass


def 主函数():
    项目根 = _取项目根目录()
    if 项目根 not in sys.path:
        sys.path.insert(0, 项目根)

    pygame.init()
    pygame.display.set_caption("测试入口 - 结算场景（流程2/流程3调试版）")

    屏幕 = _创建窗口((1280, 720), pygame.RESIZABLE)
    时钟 = pygame.time.Clock()
    资源 = 默认资源路径()
    状态 = {
        "玩家数": 1,
        "投币数": 3,
        "每局所需信用": 3,
    }
    上下文 = {
        "屏幕": 屏幕,
        "时钟": 时钟,
        "资源": 资源,
        "字体": {
            "大字": 获取字体(72),
            "中字": 获取字体(36),
            "小字": 获取字体(22),
            "投币_credit字": 获取字体(22),
        },
        "状态": 状态,
    }

    玩家序号 = 1
    当前调试模式 = "自然流程"
    当前载荷 = _构建测试载荷(项目根, 玩家序号=玩家序号)
    当前场景 = 场景_结算(上下文)
    当前场景.进入(dict(当前载荷))

    提示字体 = 获取字体(18)
    按钮字体 = 获取字体(18)
    按钮列表 = _构建调试按钮(屏幕.get_width())

    奖励调试模式集合 = {"经验普通", "花式升级", "竞速升级"}

    def _重建():
        nonlocal 当前场景
        try:
            当前场景.退出()
        except Exception:
            pass
        当前场景 = 场景_结算(上下文)
        当前场景.进入(dict(当前载荷))

        if 当前调试模式 in 奖励调试模式集合:
            _应用奖励调试模式(当前场景, 当前调试模式)
        else:
            _应用流程3调试模式(当前场景, 状态, 当前调试模式)

    def _切换调试模式(模式名: str):
        nonlocal 当前调试模式
        if 模式名 == "重播当前":
            _重建()
            return
        当前调试模式 = 模式名
        _重建()

    键位到模式 = {
        pygame.K_F1: "自然流程",
        pygame.K_F2: "经验普通",
        pygame.K_F3: "花式升级",
        pygame.K_F4: "竞速升级",
        pygame.K_F6: "下一把",
        pygame.K_F7: "继续挑战",
        pygame.K_F8: "是否续币",
        pygame.K_F9: "游戏结束",
        pygame.K_F10: "赠送一把",
    }

    运行中 = True
    while 运行中:
        时钟.tick_busy_loop(120)
        按钮列表 = _构建调试按钮(屏幕.get_width())

        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                运行中 = False
                break

            if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F5:
                _重建()
                continue

            if 事件.type == pygame.KEYDOWN and 事件.key in 键位到模式:
                _切换调试模式(键位到模式[事件.key])
                continue

            if 事件.type == pygame.KEYDOWN and 事件.key in (pygame.K_1, pygame.K_KP1):
                玩家序号 = 1
                当前载荷 = _构建测试载荷(项目根, 玩家序号=玩家序号)
                _重建()
                continue

            if 事件.type == pygame.KEYDOWN and 事件.key in (pygame.K_2, pygame.K_KP2):
                玩家序号 = 2
                当前载荷 = _构建测试载荷(项目根, 玩家序号=玩家序号)
                _重建()
                continue

            if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
                运行中 = False
                break

            if 事件.type == pygame.VIDEORESIZE:
                屏幕 = _创建窗口(
                    (max(960, int(事件.w)), max(540, int(事件.h))), pygame.RESIZABLE
                )
                上下文["屏幕"] = 屏幕
                按钮列表 = _构建调试按钮(屏幕.get_width())
                continue

            if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
                是否命中调试按钮 = False
                for 按钮 in 按钮列表:
                    if 按钮["rect"].collidepoint(事件.pos):
                        _切换调试模式(str(按钮["模式"]))
                        是否命中调试按钮 = True
                        break
                if 是否命中调试按钮:
                    continue

            try:
                结果 = 当前场景.处理事件(事件)
            except Exception:
                结果 = None
            if isinstance(结果, dict):
                运行中 = False
                break

        if not 运行中:
            break

        try:
            更新结果 = 当前场景.更新()
        except Exception:
            更新结果 = None
        if isinstance(更新结果, dict):
            运行中 = False
            break

        当前场景.绘制()
        _绘制调试面板(
            屏幕=屏幕,
            小字体=提示字体,
            按钮字体=按钮字体,
            按钮列表=按钮列表,
            当前模式=当前调试模式,
            玩家序号=玩家序号,
            场景对象=当前场景,
        )

        pygame.display.flip()

    try:
        当前场景.退出()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    主函数()
