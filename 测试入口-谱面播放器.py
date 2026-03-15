import os
import sys

import pygame

from core.常量与路径 import 默认资源路径
from core.工具 import 获取字体
from core.音频 import 音乐管理
from scenes.场景_谱面播放器 import 场景_谱面播放器


def _创建显示窗口(
    尺寸: tuple[int, int],
    flags: int,
) -> pygame.Surface:
    请求flags = int(flags | pygame.DOUBLEBUF | pygame.HWSURFACE)
    try:
        return pygame.display.set_mode(尺寸, 请求flags, vsync=1)
    except TypeError:
        try:
            return pygame.display.set_mode(尺寸, 请求flags)
        except Exception:
            return pygame.display.set_mode(尺寸, flags)
    except Exception:
        try:
            return pygame.display.set_mode(尺寸, 请求flags)
        except Exception:
            return pygame.display.set_mode(尺寸, flags)


def _取项目根目录() -> str:
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.path.abspath(os.getcwd())


def _构建测试载荷(项目根: str) -> dict:
    sm路径 = os.path.join(
        项目根,
        "songs",
        "竞速",
        "混音",
        "SPEED_REMIX#Korean_Girls_Pop_Song_Party#7",
        "Korean_Girls_Pop_Song_Party [SPEED_REMIX].sm",
    )
    return {
        "sm路径": sm路径,
        "歌名": "Korean Girls Pop Song Party",
        "星级": 7,
        "玩家序号": 1,
        "当前关卡": 1,
        "自动播放": True,
        "性能模式": False,
        "显示按键提示": True,
        "设置参数": {"调速": "X4.0"},
        "设置参数文本": "调速=X4.0",
    }


def 主函数():
    项目根 = _取项目根目录()
    if 项目根 not in sys.path:
        sys.path.insert(0, 项目根)

    pygame.init()
    pygame.display.set_caption("测试入口 - 谱面播放器")

    屏幕 = _创建显示窗口((1280, 720), pygame.RESIZABLE)
    时钟 = pygame.time.Clock()
    资源 = 默认资源路径()
    音乐 = 音乐管理()

    上下文 = {
        "屏幕": 屏幕,
        "时钟": 时钟,
        "资源": 资源,
        "字体": {
            "大字": 获取字体(72),
            "中字": 获取字体(36),
            "小字": 获取字体(22),
        },
        "音乐": 音乐,
        "状态": {"玩家数": 1},
    }

    当前载荷 = _构建测试载荷(项目根)
    当前场景 = 场景_谱面播放器(上下文)
    当前场景.进入(dict(当前载荷))
    监视字体 = 获取字体(18)
    全屏中 = False
    窗口模式尺寸 = (1280, 720)

    def _重建当前场景():
        nonlocal 当前场景
        try:
            当前场景.退出()
        except Exception:
            pass
        当前场景 = 场景_谱面播放器(上下文)
        当前场景.进入(dict(当前载荷))

    def _处理场景结果(结果):
        nonlocal 当前场景, 当前载荷
        if not isinstance(结果, dict):
            return True

        目标 = str(结果.get("切换到", "") or "").strip()
        if 目标 == "谱面播放器":
            新载荷 = 结果.get("载荷", 当前载荷)
            当前载荷 = dict(新载荷) if isinstance(新载荷, dict) else dict(当前载荷)
            _重建当前场景()
            return True

        if 目标:
            return False
        return True

    def _切换全屏():
        nonlocal 屏幕, 全屏中, 窗口模式尺寸
        if not bool(全屏中):
            try:
                当前尺寸 = tuple(屏幕.get_size())
                if len(当前尺寸) >= 2:
                    窗口模式尺寸 = (
                        int(max(960, int(当前尺寸[0]))),
                        int(max(540, int(当前尺寸[1]))),
                    )
            except Exception:
                pass

            info = pygame.display.Info()
            目标w = int(max(1280, int(getattr(info, "current_w", 0) or 0)))
            目标h = int(max(720, int(getattr(info, "current_h", 0) or 0)))
            屏幕 = _创建显示窗口((目标w, 目标h), pygame.FULLSCREEN)
            全屏中 = True
        else:
            w = int(max(960, int(窗口模式尺寸[0])))
            h = int(max(540, int(窗口模式尺寸[1])))
            屏幕 = _创建显示窗口((w, h), pygame.RESIZABLE)
            全屏中 = False
        上下文["屏幕"] = 屏幕

    目标帧率 = 120
    运行中 = True
    while 运行中:
        时钟.tick_busy_loop(目标帧率)

        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                运行中 = False
                break

            if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F11:
                _切换全屏()
                continue

            if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F8:
                当前性能模式 = bool(当前载荷.get("性能模式", False))
                当前载荷["性能模式"] = not 当前性能模式
                当前载荷["操作反馈文本"] = (
                    f"F8:性能模式已{'开启' if bool(当前载荷['性能模式']) else '关闭'}"
                )
                _重建当前场景()
                continue

            if (not bool(全屏中)) and 事件.type == pygame.VIDEORESIZE:
                屏幕 = _创建显示窗口(
                    (max(960, int(事件.w)), max(540, int(事件.h))), pygame.RESIZABLE
                )
                上下文["屏幕"] = 屏幕
                try:
                    当前尺寸 = tuple(屏幕.get_size())
                    if len(当前尺寸) >= 2:
                        窗口模式尺寸 = (
                            int(max(960, int(当前尺寸[0]))),
                            int(max(540, int(当前尺寸[1]))),
                        )
                except Exception:
                    pass

            结果 = 当前场景.处理事件(事件)
            if not _处理场景结果(结果):
                运行中 = False
                break

        if not 运行中:
            break

        更新结果 = 当前场景.更新()
        if not _处理场景结果(更新结果):
            运行中 = False
            break

        当前场景.绘制()

        try:
            当前fps = float(时钟.get_fps())
        except Exception:
            当前fps = 0.0
        帧时毫秒 = (1000.0 / 当前fps) if 当前fps > 0.01 else 0.0
        try:
            文本 = f"FPS {当前fps:05.1f}  {帧时毫秒:04.1f}ms  目标{目标帧率}"
            文本2 = (
                f"F8 性能模式: {'开' if bool(当前载荷.get('性能模式', False)) else '关'}"
                f"  F11 全屏: {'开' if bool(全屏中) else '关'}"
            )
            文图 = 监视字体.render(文本, True, (255, 240, 140)).convert_alpha()
            文图2 = 监视字体.render(文本2, True, (200, 235, 255)).convert_alpha()
            背板宽 = int(max(文图.get_width(), 文图2.get_width()) + 16)
            背板高 = int(文图.get_height() + 文图2.get_height() + 18)
            背板 = pygame.Surface((背板宽, 背板高), pygame.SRCALPHA)
            背板.fill((0, 0, 0, 160))
            屏幕.blit(背板, (16, 16))
            屏幕.blit(文图, (24, 22))
            屏幕.blit(文图2, (24, int(26 + 文图.get_height())))
        except Exception:
            pass

        pygame.display.flip()

    try:
        当前场景.退出()
    except Exception:
        pass
    try:
        音乐.停止()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    主函数()
