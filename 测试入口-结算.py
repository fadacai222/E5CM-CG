import json
import os
import shutil
import sys
import time
from typing import Dict, List, Tuple

import pygame

import scenes.场景_结算 as 结算场景模块
from core.常量与路径 import 默认资源路径
from core.对局状态 import 初始化对局流程, 设置对局流程
from core.工具 import 获取字体
from core.等级经验 import (
    经验数据版本,
    取升下一级所需经验,
    处理歌曲经验结算,
    规范化模式进度,
)
from scenes.场景_结算 import 场景_结算


_原始更新歌曲最高分 = 结算场景模块.更新歌曲最高分

默认模式列表 = ("竞速", "花式")
默认起始等级 = 1
默认起始经验比例 = 0.0
默认音符数 = 832
默认歌曲时长秒 = 142.0
默认第三首分数 = 47764800


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


def _写入json(路径: str, 数据: dict):
    os.makedirs(os.path.dirname(os.path.abspath(路径)), exist_ok=True)
    with open(路径, "w", encoding="utf-8") as 文件:
        json.dump(数据, 文件, ensure_ascii=False, indent=2)


def _创建窗口(尺寸: Tuple[int, int], 标志: int) -> pygame.Surface:
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


def _转绝对路径(项目根: str, 路径: str) -> str:
    文本 = str(路径 or "").strip()
    if not 文本:
        return ""
    if os.path.isabs(文本):
        return 文本
    return os.path.abspath(os.path.join(项目根, 文本.replace("/", os.sep)))


def _读取加载页资源(项目根: str) -> dict:
    数据 = _读取json(os.path.join(项目根, "json", "加载页.json"))
    return {
        "曲目名": str(数据.get("歌曲名", "") or "ALL PERFECT x3 Debug Song"),
        "sm路径": str(数据.get("sm路径", "") or "songs/_debug_/allperfect_x3/test.sm"),
        "封面路径": _转绝对路径(项目根, str(数据.get("封面路径", "") or "")),
        "背景图片路径": _转绝对路径(项目根, str(数据.get("背景图路径", "") or "")),
        "背景视频路径": _转绝对路径(项目根, str(数据.get("背景视频路径", "") or "")),
        "星级": int(数据.get("星级", 7) or 7),
        "选歌原始索引": int(数据.get("选歌原始索引", -1) or -1),
    }


def _构建模式起始进度(等级: int, 经验比例: float, *, 累计首数: int = 0, 累计歌曲: int = 0) -> dict:
    等级 = max(1, min(70, int(等级 or 1)))
    所需经验 = int(取升下一级所需经验(等级))
    if 所需经验 <= 0:
        当前经验 = 0.0
    else:
        当前经验 = float(max(0.0, min(1.0, float(经验比例 or 0.0)))) * float(所需经验)
    return {
        "等级": int(等级),
        "经验": float(当前经验),
        "累计歌曲": int(max(0, 累计歌曲)),
        "累计首数": int(max(0, 累计首数)),
    }


def _格式化进度(模式进度: dict) -> str:
    数据 = 规范化模式进度(dict(模式进度 or {}), 经验版本=经验数据版本)
    等级 = int(数据.get("等级", 1) or 1)
    经验 = float(数据.get("经验", 0.0) or 0.0)
    所需经验 = int(取升下一级所需经验(等级))
    if 所需经验 <= 0:
        return f"Lv{等级} MAX"
    百分比 = float(经验) / float(max(1, 所需经验)) * 100.0
    return f"Lv{等级} {经验:.2f}/{所需经验} ({百分比:.1f}%)"


def _格式化倍率(倍率) -> str:
    try:
        数值 = float(倍率 or 0.0)
    except Exception:
        数值 = 0.0
    if abs(数值 - round(数值)) <= 1e-6:
        return str(int(round(数值)))
    return f"{数值:.1f}".rstrip("0").rstrip(".")


def _构建三把allperfect歌曲列表() -> List[dict]:
    return [
        {
            "当前关卡": 1,
            "评级": "S",
            "perfect数": int(默认音符数),
            "cool数": 0,
            "good数": 0,
            "miss数": 0,
            "本局最高分": int(默认第三首分数),
            "本局最大combo": int(默认音符数),
            "百分比": "100.00%",
            "百分比数值": 100.0,
        },
        {
            "当前关卡": 2,
            "评级": "S",
            "perfect数": int(默认音符数),
            "cool数": 0,
            "good数": 0,
            "miss数": 0,
            "本局最高分": int(默认第三首分数),
            "本局最大combo": int(默认音符数),
            "百分比": "100.00%",
            "百分比数值": 100.0,
        },
        {
            "当前关卡": 3,
            "评级": "S",
            "perfect数": int(默认音符数),
            "cool数": 0,
            "good数": 0,
            "miss数": 0,
            "本局最高分": int(默认第三首分数),
            "本局最大combo": int(默认音符数),
            "百分比": "100.00%",
            "百分比数值": 100.0,
        },
    ]


def _模拟正式局(
    *,
    模式键: str,
    起始进度: dict,
    歌曲列表: List[dict],
    处理到关卡: int,
) -> tuple[dict, dict, List[dict]]:
    状态 = {"投币数": 3, "每局所需信用": 3}
    初始化对局流程(状态)
    当前进度 = 规范化模式进度(dict(起始进度 or {}), 经验版本=经验数据版本)
    结果列表: List[dict] = []

    for 歌曲 in 歌曲列表:
        当前关卡 = int(歌曲.get("当前关卡", 1) or 1)
        输入进度 = dict(当前进度)
        输入进度["累计首数"] = int(输入进度.get("累计首数", 0) or 0) + 1
        输入进度["累计歌曲"] = int(输入进度.get("累计歌曲", 0) or 0) + 1
        结算结果 = 处理歌曲经验结算(
            状态,
            模式键=模式键,
            模式进度=输入进度,
            当前关卡=当前关卡,
            评级=str(歌曲.get("评级", "S") or "S"),
            cool数=int(歌曲.get("cool数", 0) or 0),
            good数=int(歌曲.get("good数", 0) or 0),
            miss数=int(歌曲.get("miss数", 0) or 0),
        )
        当前进度 = 规范化模式进度(
            结算结果.get("模式进度", 输入进度),
            经验版本=经验数据版本,
        )
        结果列表.append(
            {
                "当前关卡": int(当前关卡),
                "输入进度": dict(输入进度),
                "输出进度": dict(当前进度),
                "结算结果": dict(结算结果 or {}),
            }
        )
        if 当前关卡 >= int(处理到关卡):
            break

    return 状态, 当前进度, 结果列表


def _构建个人资料数据(模式键: str, 场景起始进度: dict) -> dict:
    花式 = _构建模式起始进度(1, 0.0)
    竞速 = _构建模式起始进度(1, 0.0)
    if 模式键 == "花式":
        花式 = dict(场景起始进度)
    else:
        竞速 = dict(场景起始进度)
    return {
        "昵称": "结算经验调试",
        "头像文件": "",
        "统计": {},
        "进度": {
            "花式": 花式,
            "竞速": 竞速,
            "最大等级": 70,
            "经验版本": int(经验数据版本),
            "段位": "UI-img/个人中心-个人资料/等级/1.png",
        },
    }


def _重建沙盒目录(项目根: str, 模式键: str, 起始等级: int, 起始经验比例: float) -> str:
    沙盒根目录 = os.path.join(项目根, "installer_output", "结算测试沙盒")
    if os.path.isdir(沙盒根目录):
        shutil.rmtree(沙盒根目录, ignore_errors=True)
    os.makedirs(os.path.join(沙盒根目录, "json"), exist_ok=True)

    场景起始进度 = _构建模式起始进度(
        起始等级,
        起始经验比例,
        累计首数=2,
        累计歌曲=2,
    )
    _写入json(
        os.path.join(沙盒根目录, "json", "个人资料.json"),
        _构建个人资料数据(模式键, 场景起始进度),
    )
    _写入json(os.path.join(沙盒根目录, "json", "歌曲记录索引.json"), {})
    return 沙盒根目录


def _配置场景写入沙盒(沙盒根目录: str):
    结算场景模块._公共取运行根目录 = lambda: 沙盒根目录

    def _写入沙盒歌曲记录(_项目根: str, sm路径: str, 歌名: str, 分数: int) -> dict:
        return _原始更新歌曲最高分(沙盒根目录, sm路径, 歌名, 分数)

    结算场景模块.更新歌曲最高分 = _写入沙盒歌曲记录


def _构建第三首结算载荷(项目根: str, 模式键: str, 资源信息: dict) -> dict:
    return {
        "玩家序号": 1,
        "曲目名": f"{资源信息['曲目名']} [三把AP测试]",
        "sm路径": str(资源信息["sm路径"] or ""),
        "模式": str(模式键),
        "类型": str(模式键),
        "本局最高分": int(默认第三首分数),
        "本局最大combo": int(默认音符数),
        "歌曲时长秒": float(默认歌曲时长秒),
        "谱面总分": int(默认第三首分数),
        "百分比": "100.00%",
        "百分比数值": 100.0,
        "评级": "S",
        "是否评价S": True,
        "失败": False,
        "当前关卡": 3,
        "局数": 3,
        "结算前S数": 2,
        "结算后S数": 3,
        "累计S数": 3,
        "三把S赠送": True,
        "是否赠送第四把": True,
        "perfect数": int(默认音符数),
        "cool数": 0,
        "good数": 0,
        "miss数": 0,
        "是否全连": True,
        "全连": True,
        "封面路径": str(资源信息["封面路径"] or ""),
        "星级": int(资源信息["星级"] or 7),
        "背景图片路径": str(资源信息["背景图片路径"] or ""),
        "背景视频路径": str(资源信息["背景视频路径"] or ""),
        "选歌原始索引": int(资源信息["选歌原始索引"] or -1),
    }


def _构建调试报告(
    *,
    模式键: str,
    起始等级: int,
    起始经验比例: float,
) -> dict:
    项目根 = _取项目根目录()
    资源信息 = _读取加载页资源(项目根)
    歌曲列表 = _构建三把allperfect歌曲列表()
    起始进度 = _构建模式起始进度(起始等级, 起始经验比例)

    摘要状态, 摘要最终进度, 摘要结果列表 = _模拟正式局(
        模式键=模式键,
        起始进度=起始进度,
        歌曲列表=歌曲列表,
        处理到关卡=3,
    )
    场景状态, _, _ = _模拟正式局(
        模式键=模式键,
        起始进度=起始进度,
        歌曲列表=歌曲列表,
        处理到关卡=2,
    )
    设置对局流程(场景状态, 当前把数=3, 累计S数=2, 赠送第四把=False)

    第三首结果 = dict(摘要结果列表[-1]["结算结果"] or {})
    正式局歌曲 = list(第三首结果.get("正式局歌曲", []) or [])
    经验结算 = (
        dict(第三首结果.get("经验结算", {}) or {})
        if isinstance(第三首结果.get("经验结算", {}), dict)
        else {}
    )

    return {
        "项目根": 项目根,
        "模式键": 模式键,
        "起始等级": int(起始等级),
        "起始经验比例": float(起始经验比例),
        "起始进度": dict(起始进度),
        "摘要状态": 摘要状态,
        "场景状态": 场景状态,
        "摘要最终进度": dict(摘要最终进度),
        "摘要结果列表": 摘要结果列表,
        "第三首结果": 第三首结果,
        "经验结算": 经验结算,
        "正式局歌曲": 正式局歌曲,
        "资源信息": 资源信息,
        "第三首载荷": _构建第三首结算载荷(项目根, 模式键, 资源信息),
    }


def _构建场景上下文(项目根: str, 屏幕: pygame.Surface, 时钟: pygame.time.Clock, 状态: dict) -> dict:
    资源 = 默认资源路径()
    资源["根"] = 项目根
    return {
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


def _重建结算场景(
    屏幕: pygame.Surface,
    时钟: pygame.time.Clock,
    模式键: str,
    起始等级: int,
    起始经验比例: float,
) -> tuple[场景_结算, dict, str]:
    报告 = _构建调试报告(
        模式键=模式键,
        起始等级=起始等级,
        起始经验比例=起始经验比例,
    )
    沙盒根目录 = _重建沙盒目录(
        报告["项目根"],
        模式键=模式键,
        起始等级=起始等级,
        起始经验比例=起始经验比例,
    )
    _配置场景写入沙盒(沙盒根目录)
    上下文 = _构建场景上下文(报告["项目根"], 屏幕, 时钟, dict(报告["场景状态"]))
    场景对象 = 场景_结算(上下文)
    场景对象.进入(dict(报告["第三首载荷"]))

    try:
        if bool(场景对象._是否显示奖励小窗()):
            场景对象._进入系统秒 = time.perf_counter() - float(场景对象._流程1时长秒) - 0.02
    except Exception:
        pass

    return 场景对象, 报告, 沙盒根目录


def _打印调试结果(报告: dict):
    第三首结果 = dict(报告.get("第三首结果", {}) or {})
    经验结算 = dict(报告.get("经验结算", {}) or {})
    正式局歌曲 = list(报告.get("正式局歌曲", []) or [])

    print("=" * 72)
    print(f"模式: {报告['模式键']}")
    print(f"起始进度: {_格式化进度(报告['起始进度'])}")
    for 索引, 单曲 in enumerate(正式局歌曲, start=1):
        print(
            f"第{索引}把: 基础{int(单曲.get('基础经验', 0) or 0)}"
            f" x 连S{_格式化倍率(单曲.get('连续S倍率', 0))}"
            f" x 奖励{_格式化倍率(单曲.get('奖励倍率', 0))}"
            f" = {int(单曲.get('最终经验', 0) or 0)}"
        )
    print(f"正式局总经验: {int(第三首结果.get('正式局总经验', 0) or 0)}")
    print(f"实际入账经验: {int(第三首结果.get('经验增加值', 0) or 0)}")
    print(f"升级次数: {int(经验结算.get('升级次数', 0) or 0)}")
    print(f"结算后进度: {_格式化进度(经验结算.get('模式进度', {}))}")
    print("=" * 72)


def _绘制调试覆盖层(
    屏幕: pygame.Surface,
    标题字体: pygame.font.Font,
    正文字体: pygame.font.Font,
    报告: dict,
    沙盒根目录: str,
):
    第三首结果 = dict(报告.get("第三首结果", {}) or {})
    经验结算 = dict(报告.get("经验结算", {}) or {})
    正式局歌曲 = list(报告.get("正式局歌曲", []) or [])
    模式键 = str(报告.get("模式键", "竞速") or "竞速")
    起始等级 = int(报告.get("起始等级", 1) or 1)
    起始经验比例 = float(报告.get("起始经验比例", 0.0) or 0.0)

    行列表 = [
        "正式局三把 ALL PERFECT 经验调试",
        "TAB 切模式  ↑↓ 改起始等级  ←→ 改起始经验比例  R/F5 重建  SPACE 重看奖励动画  ESC 退出",
        f"当前模式: {模式键}",
        f"起始等级/经验: Lv{起始等级} / {int(round(起始经验比例 * 100.0))}%",
        f"起始进度: {_格式化进度(报告.get('起始进度', {}))}",
    ]
    for 索引, 单曲 in enumerate(正式局歌曲, start=1):
        行列表.append(
            f"第{索引}把 AP: 基础{int(单曲.get('基础经验', 0) or 0)}"
            f" x 连S{_格式化倍率(单曲.get('连续S倍率', 0))}"
            f" x 奖励{_格式化倍率(单曲.get('奖励倍率', 0))}"
            f" = {int(单曲.get('最终经验', 0) or 0)}"
        )
    行列表.extend(
        [
            f"正式局总经验: {int(第三首结果.get('正式局总经验', 0) or 0)}",
            f"实际入账经验: {int(第三首结果.get('经验增加值', 0) or 0)}",
            f"升级次数: {int(经验结算.get('升级次数', 0) or 0)}",
            f"结算后进度: {_格式化进度(经验结算.get('模式进度', {}))}",
            f"沙盒目录: {沙盒根目录}",
        ]
    )

    图列表: List[pygame.Surface] = []
    for 索引, 文本 in enumerate(行列表):
        字体 = 标题字体 if 索引 == 0 else 正文字体
        颜色 = (255, 240, 160) if 索引 == 0 else (235, 235, 235)
        图列表.append(字体.render(文本, True, 颜色).convert_alpha())

    面板宽 = min(
        屏幕.get_width() - 24,
        max((图.get_width() for 图 in 图列表), default=0) + 20,
    )
    面板高 = sum(图.get_height() for 图 in 图列表) + 10 + max(0, len(图列表) - 1) * 4
    面板 = pygame.Surface((max(1, 面板宽), max(1, 面板高)), pygame.SRCALPHA)
    面板.fill((0, 0, 0, 170))
    屏幕.blit(面板, (12, 12))

    y = 18
    for 图 in 图列表:
        屏幕.blit(图, (22, y))
        y += 图.get_height() + 4


def 主函数():
    项目根 = _取项目根目录()
    if 项目根 not in sys.path:
        sys.path.insert(0, 项目根)

    pygame.init()
    pygame.display.set_caption("测试入口 - 结算场景（三把 ALL PERFECT 经验调试）")

    屏幕 = _创建窗口((1280, 720), pygame.RESIZABLE)
    时钟 = pygame.time.Clock()
    标题字体 = 获取字体(20, True)
    正文字体 = 获取字体(18, False)

    当前模式索引 = 0
    当前起始等级 = int(默认起始等级)
    当前起始经验比例 = float(默认起始经验比例)
    当前场景, 当前报告, 沙盒根目录 = _重建结算场景(
        屏幕,
        时钟,
        默认模式列表[当前模式索引],
        当前起始等级,
        当前起始经验比例,
    )
    _打印调试结果(当前报告)

    def _重建():
        nonlocal 当前场景, 当前报告, 沙盒根目录
        try:
            当前场景.退出()
        except Exception:
            pass
        当前场景, 当前报告, 沙盒根目录 = _重建结算场景(
            屏幕,
            时钟,
            默认模式列表[当前模式索引],
            当前起始等级,
            当前起始经验比例,
        )
        _打印调试结果(当前报告)

    def _重看奖励动画():
        try:
            if bool(当前场景._是否显示奖励小窗()):
                当前场景._进入系统秒 = time.perf_counter() - float(当前场景._流程1时长秒) - 0.02
        except Exception:
            pass

    运行中 = True
    while 运行中:
        时钟.tick_busy_loop(120)

        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                运行中 = False
                break

            if 事件.type == pygame.VIDEORESIZE:
                屏幕 = _创建窗口(
                    (max(960, int(事件.w)), max(540, int(事件.h))),
                    pygame.RESIZABLE,
                )
                当前场景.上下文["屏幕"] = 屏幕
                continue

            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    运行中 = False
                    break
                if 事件.key in (pygame.K_r, pygame.K_F5):
                    _重建()
                    continue
                if 事件.key == pygame.K_SPACE:
                    _重看奖励动画()
                    continue
                if 事件.key == pygame.K_TAB:
                    当前模式索引 = (当前模式索引 + 1) % len(默认模式列表)
                    _重建()
                    continue
                if 事件.key in (pygame.K_UP, pygame.K_KP8):
                    当前起始等级 = min(70, 当前起始等级 + 1)
                    _重建()
                    continue
                if 事件.key in (pygame.K_DOWN, pygame.K_KP2):
                    当前起始等级 = max(1, 当前起始等级 - 1)
                    _重建()
                    continue
                if 事件.key in (pygame.K_LEFT, pygame.K_KP4):
                    当前起始经验比例 = max(0.0, 当前起始经验比例 - 0.25)
                    _重建()
                    continue
                if 事件.key in (pygame.K_RIGHT, pygame.K_KP6):
                    当前起始经验比例 = min(1.0, 当前起始经验比例 + 0.25)
                    _重建()
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
        _绘制调试覆盖层(
            屏幕=屏幕,
            标题字体=标题字体,
            正文字体=正文字体,
            报告=当前报告,
            沙盒根目录=沙盒根目录,
        )
        pygame.display.flip()

    try:
        当前场景.退出()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    主函数()
