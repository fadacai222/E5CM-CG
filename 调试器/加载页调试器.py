import os
import time
from typing import Any, Dict, Optional, Tuple

import pygame

from ui.调试_加载页_渲染控件 import (
    取项目根目录,
    _安全读json,
    _安全写json,
    加载页布局渲染器,
)


def _取示例数据(根目录: str) -> Dict[str, Any]:
    """
    调试器用的数据：优先读 json/加载页.json（如果你项目里存在）
    否则给一份可跑的兜底。
    """
    路径 = os.path.join(根目录, "json", "加载页.json")
    数据 = _安全读json(路径)
    if 数据:
        # 你原本载荷结构可能是“整包”，这里拍平一点，方便 {占位符}
        载荷 = dict(数据)
    else:
        载荷 = {
            "sm路径": r"C:\Songs\demo\demo.sm",
            "设置参数文本": "偏移=0 | 模式=Single | 难度=Hard",
            "封面路径": "",
            "歌名": "Loading...",
            "星级": 15,
            "bpm": 128,
            "人气": 9999,
        }

    # 个人资料：调试器也给个兜底（不强制读盘）
    个人昵称 = "未知"
    最高分 = 0
    最大等级 = 0
    try:
        个人路径 = os.path.join(根目录, "UI-img", "个人中心-个人资料", "个人资料.json")
        个人 = _安全读json(个人路径)
        if isinstance(个人, dict) and 个人:
            个人昵称 = str(个人.get("昵称", "") or "").strip() or "未知"
            最高分 = int(((个人.get("统计", {}) or {}).get("最高分", 0) or 0))
            最大等级 = int(((个人.get("进度", {}) or {}).get("最大等级", 0) or 0))
    except Exception:
        pass

    昵称 = 个人昵称
    店名 = f"{昵称}的电脑"
    舞队 = "e舞成名重构版玩家大队"

    # ✅ 调试渲染用：拍平字段（保证 {占位符} 直接用）
    数据包: Dict[str, Any] = {}
    数据包.update(载荷)
    数据包.update(
        {
            "个人昵称": 昵称,
            "最高分": max(0, 最高分),
            "最大等级": max(0, 最大等级),
            "店名": 店名,
            "舞队": 舞队,
            "载荷": dict(载荷),  # 给 $.载荷.xxx 用
        }
    )
    return 数据包


def _默认布局json() -> Dict[str, Any]:
    # 你也可以不喜欢这份默认，调试器里随便拖/滚改完 Ctrl+S 就覆盖
    return {
        "版本": 1,
        "设计宽": 2048,
        "设计高": 1152,
        "控件": [
            {
                "id": "背景",
                "类型": "图",
                "源": "冷资源/backimages/选歌界面.png",
                "rect": [0, 0, 2048, 1152],
                "适配": "stretch",
                "透明": False,
            },
            {
                "id": "暗化",
                "类型": "面板",
                "rect": [0, 0, 2048, 1152],
                "颜色": [0, 0, 0, 70],
                "圆角": 0,
            },
            {
                "id": "顶底板",
                "类型": "面板",
                "rect": [120, 160, 1808, 180],
                "颜色": [0, 0, 0, 160],
                "圆角": 18,
            },
            {
                "id": "顶_SM路径",
                "类型": "文本",
                "rect": [138, 174, 1772, 64],
                "内容": "SM路径：{sm路径}",
                "字号": 34,
                "加粗": True,
                "颜色": [255, 255, 255, 255],
                "对齐": "left",
                "垂直": "top",
                "换行": True,
                "行数": 2,
                "行距": 6,
            },
            {
                "id": "顶_参数",
                "类型": "文本",
                "rect": [138, 238, 1772, 92],
                "内容": "{设置参数文本}",
                "字号": 26,
                "加粗": False,
                "颜色": [235, 235, 235, 255],
                "对齐": "left",
                "垂直": "top",
                "换行": True,
                "行数": 4,
                "行距": 4,
            },
            {
                "id": "下底板",
                "类型": "面板",
                "rect": [120, 360, 1808, 720],
                "颜色": [0, 0, 0, 120],
                "圆角": 18,
            },
            {
                "id": "封面底板",
                "类型": "面板",
                "rect": [156, 393, 506, 350],
                "颜色": [0, 0, 0, 140],
                "圆角": 16,
                "内边距": [8, 8, 8, 8],
            },
            {
                "id": "封面图",
                "类型": "图",
                "源": "$.载荷.封面路径",
                "rect": [156, 393, 506, 350],
                "适配": "contain",
                "透明": True,
                "内边距": [16, 16, 16, 16],
            },
            {
                "id": "星星行",
                "类型": "星星行",
                "rect": [716, 393, 1212, 100],
                "星图": "UI-img/选歌界面资源/小星星/大星星.png",
                "星数键": "星级",
                "单星高度": 55,
                "每行最大": 12,
                "间距": 8,
                "行距": 12,
                "透明度": 255,
                "透明": True,
            },
            {
                "id": "线1",
                "类型": "线",
                "rect": [716, 493, 1212, 4],
                "颜色": [160, 160, 160, 255],
                "厚度": 2,
            },
            {
                "id": "歌名",
                "类型": "文本",
                "rect": [716, 500, 1212, 78],
                "内容": "{歌名}",
                "字号": 46,
                "加粗": False,
                "颜色": [255, 255, 255, 255],
                "对齐": "center",
                "垂直": "middle",
                "换行": False,
                "行数": 1,
                "行距": 0,
            },
            {
                "id": "线2",
                "类型": "线",
                "rect": [716, 578, 1212, 4],
                "颜色": [160, 160, 160, 255],
                "厚度": 2,
            },
            {
                "id": "人气",
                "类型": "文本",
                "rect": [716, 586, 606, 70],
                "内容": "人气：{人气}",
                "字号": 34,
                "加粗": False,
                "颜色": [255, 255, 255, 255],
                "对齐": "left",
                "垂直": "middle",
                "换行": False,
                "行数": 1,
                "行距": 0,
                "内边距": [30, 0, 0, 0],
            },
            {
                "id": "BPM",
                "类型": "文本",
                "rect": [1312, 586, 616, 70],
                "内容": "BPM：{bpm}",
                "字号": 34,
                "加粗": False,
                "颜色": [255, 255, 255, 255],
                "对齐": "right",
                "垂直": "middle",
                "换行": False,
                "行数": 1,
                "行距": 0,
                "内边距": [0, 0, 30, 0],
            },
            {
                "id": "线3",
                "类型": "线",
                "rect": [716, 656, 1212, 4],
                "颜色": [160, 160, 160, 255],
                "厚度": 2,
            },
            {
                "id": "左_记录保持者",
                "类型": "文本",
                "rect": [156, 831, 830, 60],
                "内容": "记录保持者：{个人昵称}",
                "字号": 32,
                "加粗": False,
                "颜色": [167, 226, 180, 255],
                "对齐": "left",
                "垂直": "top",
                "换行": False,
                "行数": 1,
                "行距": 0,
                "内边距": [10, 0, 0, 0],
            },
            {
                "id": "左_最高分",
                "类型": "文本",
                "rect": [156, 891, 830, 60],
                "内容": "最高分：{最高分}",
                "字号": 32,
                "加粗": False,
                "颜色": [224, 167, 178, 255],
                "对齐": "left",
                "垂直": "top",
                "换行": False,
                "行数": 1,
                "行距": 0,
                "内边距": [10, 0, 0, 0],
            },
            {
                "id": "右_级别",
                "类型": "文本",
                "rect": [1040, 831, 888, 60],
                "内容": "级别：{最大等级}",
                "字号": 32,
                "加粗": False,
                "颜色": [109, 204, 191, 255],
                "对齐": "left",
                "垂直": "top",
                "换行": False,
                "行数": 1,
                "行距": 0,
                "内边距": [10, 0, 0, 0],
            },
            {
                "id": "右_所属舞队",
                "类型": "文本",
                "rect": [1040, 891, 888, 60],
                "内容": "所属舞队：{舞队}",
                "字号": 30,
                "加粗": False,
                "颜色": [255, 255, 255, 255],
                "对齐": "left",
                "垂直": "top",
                "换行": True,
                "行数": 1,
                "行距": 0,
                "内边距": [10, 0, 0, 0],
            },
            {
                "id": "右_店名",
                "类型": "文本",
                "rect": [1040, 951, 888, 60],
                "内容": "店名：{店名}",
                "字号": 30,
                "加粗": False,
                "颜色": [247, 253, 235, 255],
                "对齐": "left",
                "垂直": "top",
                "换行": True,
                "行数": 1,
                "行距": 0,
                "内边距": [10, 0, 0, 0],
            },
        ],
    }


def main():
    pygame.init()
    pygame.display.set_caption("调试_加载页（WYSIWYG）")

    根目录 = 取项目根目录()
    布局路径 = os.path.join(根目录, "json", "加载页_布局.json")

    if not os.path.isfile(布局路径):
        _安全写json(布局路径, _默认布局json())

    屏幕 = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    时钟 = pygame.time.Clock()

    渲染器 = 加载页布局渲染器(布局路径, 项目根目录=根目录)
    数据 = _取示例数据(根目录)

    显示全部边框 = False
    选中信息: Optional[Dict[str, Any]] = None
    正在拖动 = False
    拖动偏移_设计: Tuple[float, float] = (0.0, 0.0)

    最近提示 = ""
    最近提示_时间 = 0.0

    def 提示(文本: str):
        nonlocal 最近提示, 最近提示_时间
        最近提示 = 文本
        最近提示_时间 = time.time()

    while True:
        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                pygame.quit()
                return

            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

                if 事件.key == pygame.K_F2:
                    显示全部边框 = not 显示全部边框
                    提示(f"F2 边框：{'开' if 显示全部边框 else '关'}")

                if 事件.key == pygame.K_F5:
                    渲染器.重载布局()
                    提示("F5 已重载布局")

                # Ctrl+S 保存
                if 事件.key == pygame.K_s and (
                    pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    渲染器.保存布局()
                    提示("Ctrl+S 已保存到 json/加载页_布局.json")

            # 鼠标按下：选中
            if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
                选中信息 = 渲染器.命中控件(屏幕, 事件.pos)
                if 选中信息:
                    正在拖动 = True
                    w, h = 屏幕.get_size()
                    mx, my = 渲染器.屏幕到设计点(事件.pos, w, h)
                    dx, dy, dw, dh = 选中信息["设计rect"]
                    拖动偏移_设计 = (mx - dx, my - dy)
                    提示(f"选中：{选中信息['id']}")
                else:
                    正在拖动 = False

            if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
                正在拖动 = False

            if 事件.type == pygame.MOUSEMOTION and 正在拖动 and 选中信息:
                w, h = 屏幕.get_size()
                mx, my = 渲染器.屏幕到设计点(事件.pos, w, h)

                控件 = 选中信息["控件"]
                rect值 = 控件.get("rect", None)
                if isinstance(rect值, list) and len(rect值) == 4:
                    新x = float(mx - 拖动偏移_设计[0])
                    新y = float(my - 拖动偏移_设计[1])
                    rect值[0] = int(round(新x))
                    rect值[1] = int(round(新y))
                    # 同步当前选中信息
                    选中信息["设计rect"][0] = float(rect值[0])
                    选中信息["设计rect"][1] = float(rect值[1])

            # 滚轮：缩放/改宽高/改字号
            if 事件.type == pygame.MOUSEWHEEL and 选中信息:
                mods = pygame.key.get_mods()
                is_shift = bool(mods & pygame.KMOD_SHIFT)
                is_ctrl = bool(mods & pygame.KMOD_CTRL)
                is_alt = bool(mods & pygame.KMOD_ALT)

                控件 = 选中信息["控件"]
                rect值 = 控件.get("rect", None)
                if not (isinstance(rect值, list) and len(rect值) == 4):
                    continue

                dx, dy, dw, dh = [
                    float(rect值[0]),
                    float(rect值[1]),
                    float(rect值[2]),
                    float(rect值[3]),
                ]
                dw = max(1.0, dw)
                dh = max(1.0, dh)

                滚 = int(事件.y)
                if 滚 == 0:
                    continue

                # 以中心缩放/改宽高更顺手
                cx = dx + dw / 2.0
                cy = dy + dh / 2.0

                if is_alt:
                    # 改字号
                    原字号 = int(控件.get("字号", 24) or 24)
                    新字号 = max(6, min(240, 原字号 + 滚 * 2))
                    控件["字号"] = 新字号
                    提示(f"字号：{新字号}")
                elif is_shift:
                    # 改宽度
                    步长 = 20
                    新w = max(1.0, dw + 滚 * 步长)
                    新x = cx - 新w / 2.0
                    rect值[0] = int(round(新x))
                    rect值[2] = int(round(新w))
                    提示(f"宽：{rect值[2]}")
                elif is_ctrl:
                    # 改高度
                    步长 = 20
                    新h = max(1.0, dh + 滚 * 步长)
                    新y = cy - 新h / 2.0
                    rect值[1] = int(round(新y))
                    rect值[3] = int(round(新h))
                    提示(f"高：{rect值[3]}")
                else:
                    # 等比缩放
                    factor = 1.06**滚
                    新w = max(1.0, dw * factor)
                    新h = max(1.0, dh * factor)
                    新x = cx - 新w / 2.0
                    新y = cy - 新h / 2.0
                    rect值[0] = int(round(新x))
                    rect值[1] = int(round(新y))
                    rect值[2] = int(round(新w))
                    rect值[3] = int(round(新h))
                    提示(f"等比缩放：{rect值[2]}x{rect值[3]}")

                # 同步选中信息
                选中信息["设计rect"] = [
                    float(rect值[0]),
                    float(rect值[1]),
                    float(rect值[2]),
                    float(rect值[3]),
                ]

        屏幕.fill((0, 0, 0))
        渲染器.绘制(
            屏幕,
            数据,
            显示全部边框=显示全部边框,
            选中id=(选中信息["id"] if 选中信息 else None),
        )

        # 内置调试控件（HUD）
        try:
            字体 = pygame.font.SysFont("Microsoft YaHei", 18)
        except Exception:
            字体 = pygame.font.Font(None, 18)

        行 = []
        行.append(
            "鼠标拖动=改位置 | 滚轮=等比缩放 | Shift+滚轮=宽 | Ctrl+滚轮=高 | Alt+滚轮=字号"
        )
        行.append("Ctrl+S=保存 | F2=全边框 | F5=重载 | ESC=退出")
        if 选中信息:
            rr = 选中信息["控件"].get("rect", [0, 0, 0, 0])
            行.append(f"选中：{选中信息['id']}  rect={rr}")
        if 最近提示 and (time.time() - 最近提示_时间) < 2.0:
            行.append(f"提示：{最近提示}")

        y = 8
        for 文本 in 行:
            面 = 字体.render(文本, True, (255, 255, 255))
            屏幕.blit(面, (8, y))
            y += 面.get_height() + 2

        pygame.display.flip()
        时钟.tick(60)


if __name__ == "__main__":
    main()
