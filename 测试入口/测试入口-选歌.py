import os
import sys
import pygame


def 确保项目根目录在模块路径里():
    当前文件 = os.path.abspath(__file__)
    项目根目录 = os.path.dirname(当前文件)
    if 项目根目录 not in sys.path:
        sys.path.insert(0, 项目根目录)


class 假音乐管理器:
    def 停止(self):
        return


def 主函数():
    确保项目根目录在模块路径里()

    from scenes.场景_选歌 import 场景_选歌  # noqa

    pygame.init()
    pygame.display.set_caption("调试-选歌直达（F5热刷新）")

    初始宽 = 1400
    初始高 = 860
    屏幕 = pygame.display.set_mode((初始宽, 初始高), pygame.RESIZABLE)
    时钟 = pygame.time.Clock()

    项目根目录 = os.path.dirname(os.path.abspath(__file__))

    上下文 = {
        "屏幕": 屏幕,
        "资源": {"根": 项目根目录},
        "状态": {
            "玩家数": 1,
            "选歌_类型": "花式",
            "选歌_模式": "表演",
            # 可选：强制选歌BGM（不填就走你场景里的兜底）
            # "选歌_BGM": os.path.join(项目根目录, "backsound", "devil.mp3"),
        },
        "音乐": 假音乐管理器(),
    }

    场景 = 场景_选歌(上下文)
    场景.进入()

    运行中 = True
    while 运行中:
        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                运行中 = False
                break

            # 交给场景（内部会把事件转发给选歌实例）
            try:
                场景.处理事件(事件)
            except Exception:
                pass

        try:
            场景.更新()
        except Exception:
            pass

        try:
            场景.绘制()
        except Exception:
            pass

        pygame.display.flip()
        时钟.tick(60)

    try:
        场景.退出()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    主函数()
