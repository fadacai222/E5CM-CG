import os
import sys
import pygame


def 获取字体(字号: int, 是否粗体: bool = False) -> pygame.font.Font:
    pygame.font.init()

    # 以“脚本/EXE所在目录”为基准，避免工作目录变化导致相对路径失效
    try:
        if hasattr(sys, "_MEIPASS"):
            基准目录 = sys._MEIPASS  # PyInstaller onefile
        elif getattr(sys, "frozen", False):
            基准目录 = os.path.dirname(sys.executable)  # frozen exe
        else:
            基准目录 = os.path.dirname(os.path.abspath(__file__))  # normal py
    except Exception:
        基准目录 = os.getcwd()

    相对字体路径 = os.path.join(基准目录, "字体", "方正黑体简体.TTF")

    # 1) 优先使用相对字体
    try:
        if os.path.isfile(相对字体路径):
            字体对象 = pygame.font.Font(相对字体路径, 字号)
            字体对象.set_bold(bool(是否粗体))
            return 字体对象
    except Exception:
        pass

    # 2) 找不到就用系统字体兜底
    普通候选 = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    粗体候选 = [
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]

    候选列表 = 粗体候选 if 是否粗体 else 普通候选

    for 字体路径 in 候选列表:
        try:
            if os.path.isfile(字体路径):
                字体对象 = pygame.font.Font(字体路径, 字号)
                # 有些字体文件并不是真粗体，这里再保险设置一次
                字体对象.set_bold(bool(是否粗体))
                return 字体对象
        except Exception:
            continue

    # 3) 最终兜底：pygame 默认字体
    字体对象 = pygame.font.Font(None, 字号)
    字体对象.set_bold(bool(是否粗体))
    return 字体对象
