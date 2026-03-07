import json
import os
import sys
from typing import Dict, Tuple, Optional

import pygame


def 取项目根目录() -> str:
    try:
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable))
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.getcwd()


def 安全载图(路径: str, 透明: bool = True) -> Optional[pygame.Surface]:
    try:
        if 路径 and os.path.isfile(路径):
            图像 = pygame.image.load(路径)
            return 图像.convert_alpha() if 透明 else 图像.convert()
    except Exception:
        pass
    return None


def 夹取(数值: float, 最小值: float, 最大值: float) -> float:
    return max(最小值, min(最大值, float(数值)))


def 缓出三次方(进度: float) -> float:
    临时值 = 1.0 - 夹取(进度, 0.0, 1.0)
    return 1.0 - 临时值 * 临时值 * 临时值


def 线性插值(起始值: float, 结束值: float, 进度: float) -> float:
    return float(起始值) + (float(结束值) - float(起始值)) * 夹取(进度, 0.0, 1.0)


class 升级动画调试器:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        try:
            pygame.mixer.quit()
        except Exception:
            pass

        self.项目根目录 = 取项目根目录()
        self.窗口宽 = 1365
        self.窗口高 = 768
        self.屏幕 = pygame.display.set_mode((self.窗口宽, self.窗口高))
        pygame.display.set_caption("升级动画调试器")

        self.时钟 = pygame.time.Clock()
        self.运行中 = True

        self.字体 = self.取字体(18, False)
        self.小字体 = self.取字体(14, False)
        self.大字体 = self.取字体(24, True)

        self.背景图 = None
        self.结算背景图 = None
        self.小窗背景图 = None
        self.段位图 = None
        self.升级图集: Dict[str, pygame.Surface] = {}

        self.配置文件路径 = os.path.join(self.项目根目录, "升级动画调试参数.json")
        self.是否显示辅助线 = True
        self.是否自动播放 = True
        self.当前时间 = 0.0
        self.总时长 = 1.0
        self.当前选中项 = "主图"

        self.参数 = self.加载默认参数()
        self.读取参数()
        self.加载资源()

    def 取字体(self, 字号: int, 是否粗体: bool) -> pygame.font.Font:
        候选路径 = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
        for 路径 in 候选路径:
            try:
                if os.path.isfile(路径):
                    return pygame.font.Font(路径, 字号)
            except Exception:
                pass
        try:
            return pygame.font.SysFont("Microsoft YaHei", 字号, bold=是否粗体)
        except Exception:
            return pygame.font.Font(None, 字号)

    def 加载默认参数(self) -> dict:
        return {
            "小窗": {
                "x": 338,
                "y": 293,
                "w": 656,
                "h": 340,
            },
            "主图": {
                "资源键": "升级",
                "基准中心x": 0.50,
                "基准中心y": 0.18,
                "基准宽": 280,
                "基准高": 140,
                "开始": 0.00,
                "结束": 1.00,
                "初始缩放": 0.78,
                "峰值缩放": 1.38,
                "回落缩放": 1.00,
                "峰值分界": 0.18,
                "回落分界": 0.32,
                "alpha倍率": 1.00,
            },
            "左上": {
                "资源键": "左上",
                "中心x": 0.38,
                "中心y": 0.06,
                "尺寸": 110,
                "开始": 0.22,
                "结束": 0.42,
                "起始缩放": 0.50,
                "结束缩放": 0.92,
                "alpha起": 0,
                "alpha止": 190,
            },
            "右上": {
                "资源键": "右上",
                "中心x": 0.66,
                "中心y": 0.04,
                "尺寸": 120,
                "开始": 0.10,
                "结束": 0.28,
                "起始缩放": 0.50,
                "结束缩放": 0.92,
                "alpha起": 0,
                "alpha止": 190,
            },
            "左下": {
                "资源键": "左下",
                "中心x": 0.34,
                "中心y": 0.24,
                "尺寸": 100,
                "开始": 0.22,
                "结束": 0.42,
                "起始缩放": 0.50,
                "结束缩放": 0.92,
                "alpha起": 0,
                "alpha止": 190,
            },
            "右下": {
                "资源键": "右下",
                "中心x": 0.67,
                "中心y": 0.22,
                "尺寸": 110,
                "开始": 0.38,
                "结束": 0.58,
                "起始缩放": 0.50,
                "结束缩放": 0.92,
                "alpha起": 0,
                "alpha止": 190,
            },
        }

    def 读取参数(self):
        if not os.path.isfile(self.配置文件路径):
            return
        try:
            with open(self.配置文件路径, "r", encoding="utf-8") as 文件:
                数据 = json.load(文件)
            if isinstance(数据, dict):
                self.参数.update(数据)
        except Exception:
            pass

    def 保存参数(self):
        try:
            with open(self.配置文件路径, "w", encoding="utf-8") as 文件:
                json.dump(self.参数, 文件, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def 加载资源(self):
        根 = self.项目根目录

        self.背景图 = 安全载图(
            os.path.join(根, "冷资源", "backimages", "选歌界面.png"),
            透明=False,
        )
        self.结算背景图 = 安全载图(
            os.path.join(根, "UI-img", "游戏界面", "结算", "结算背景通用.png")
        )
        self.小窗背景图 = 安全载图(
            os.path.join(根, "UI-img", "游戏界面", "结算", "结算等级小窗", "背景.png")
        )
        if self.小窗背景图 is None:
            self.小窗背景图 = 安全载图(
                os.path.join(
                    根, "UI-img", "游戏界面", "结算", "结算等级小窗", "UI_I516.png"
                )
            )

        self.段位图 = 安全载图(
            os.path.join(根, "UI-img", "个人中心-个人资料", "等级", "7.png")
        )

        升级目录 = os.path.join(
            根, "UI-img", "游戏界面", "结算", "结算等级小窗", "升级动画素材"
        )
        for 名称 in ["升级", "左上", "右上", "左下", "右下"]:
            图像 = 安全载图(os.path.join(升级目录, f"{名称}.png"))
            if 图像 is not None:
                self.升级图集[名称] = 图像

    def 缩放图(
        self, 图像: Optional[pygame.Surface], 宽: int, 高: int
    ) -> Optional[pygame.Surface]:
        if 图像 is None:
            return None
        try:
            return pygame.transform.smoothscale(
                图像, (max(2, 宽), max(2, 高))
            ).convert_alpha()
        except Exception:
            return None

    def 取小窗矩形(self) -> pygame.Rect:
        数据 = self.参数["小窗"]
        return pygame.Rect(
            int(数据["x"]),
            int(数据["y"]),
            int(数据["w"]),
            int(数据["h"]),
        )

    def 画文字(
        self, 文本: str, 坐标: Tuple[int, int], 颜色=(255, 255, 255), 字体对象=None
    ):
        if 字体对象 is None:
            字体对象 = self.字体
        图 = 字体对象.render(str(文本), True, 颜色)
        self.屏幕.blit(图, 坐标)

    def 画背景(self):
        self.屏幕.fill((0, 0, 0))
        if self.背景图 is not None:
            背景 = pygame.transform.smoothscale(self.背景图, (self.窗口宽, self.窗口高))
            self.屏幕.blit(背景, (0, 0))

        暗层 = pygame.Surface((self.窗口宽, self.窗口高), pygame.SRCALPHA)
        暗层.fill((0, 0, 0, 120))
        self.屏幕.blit(暗层, (0, 0))

        if self.结算背景图 is not None:
            结算面板 = pygame.transform.smoothscale(self.结算背景图, (650, 630))
            self.屏幕.blit(结算面板, (128, 30))

    def 画小窗(self):
        小窗矩形 = self.取小窗矩形()
        if self.小窗背景图 is not None:
            小窗图 = pygame.transform.smoothscale(self.小窗背景图, 小窗矩形.size)
            self.屏幕.blit(小窗图, 小窗矩形.topleft)
        else:
            pygame.draw.rect(self.屏幕, (40, 70, 140), 小窗矩形, border_radius=16)

        if self.段位图 is not None:
            段位图 = self.缩放图(self.段位图, 260, 90)
            if 段位图 is not None:
                段位矩形 = 段位图.get_rect(
                    center=(小窗矩形.centerx + 15, 小窗矩形.bottom - 65)
                )
                self.屏幕.blit(段位图, 段位矩形.topleft)

        pygame.draw.rect(self.屏幕, (255, 255, 255), 小窗矩形, 2, border_radius=16)

        if self.是否显示辅助线:
            pygame.draw.line(
                self.屏幕,
                (80, 180, 255),
                (小窗矩形.centerx, 小窗矩形.top),
                (小窗矩形.centerx, 小窗矩形.bottom),
                1,
            )
            pygame.draw.line(
                self.屏幕,
                (80, 180, 255),
                (小窗矩形.left, 小窗矩形.centery),
                (小窗矩形.right, 小窗矩形.centery),
                1,
            )
            self.画文字(
                "奖励窗", (小窗矩形.x + 8, 小窗矩形.y + 8), (180, 220, 255), self.小字体
            )

    def 计算主图状态(self) -> Optional[Tuple[pygame.Surface, pygame.Rect, int]]:
        参数 = self.参数["主图"]
        图像 = self.升级图集.get(str(参数["资源键"]))
        if 图像 is None:
            return None

        t = 夹取(self.当前时间, 0.0, 1.0)
        基准矩形 = self.取小窗矩形()

        if t < float(参数["峰值分界"]):
            局部进度 = t / max(0.0001, float(参数["峰值分界"]))
            缩放 = 线性插值(float(参数["初始缩放"]), float(参数["峰值缩放"]), 局部进度)
        elif t < float(参数["回落分界"]):
            局部进度 = (t - float(参数["峰值分界"])) / max(
                0.0001, float(参数["回落分界"]) - float(参数["峰值分界"])
            )
            缩放 = 线性插值(float(参数["峰值缩放"]), float(参数["回落缩放"]), 局部进度)
        else:
            缩放 = float(参数["回落缩放"])

        宽 = int(max(2, float(参数["基准宽"]) * 缩放))
        高 = int(max(2, float(参数["基准高"]) * 缩放))
        渲染图 = self.缩放图(图像, 宽, 高)
        if 渲染图 is None:
            return None

        alpha = int(255 * 缓出三次方(min(1.0, t * 1.8)) * float(参数["alpha倍率"]))
        alpha = max(0, min(255, alpha))
        try:
            渲染图 = 渲染图.copy()
            渲染图.set_alpha(alpha)
        except Exception:
            pass

        中心x = int(round(基准矩形.x + 基准矩形.w * float(参数["基准中心x"])))
        中心y = int(round(基准矩形.y + 基准矩形.h * float(参数["基准中心y"])))
        目标矩形 = 渲染图.get_rect(center=(中心x, 中心y))
        return 渲染图, 目标矩形, alpha

    def 计算角标状态(
        self, 名称: str
    ) -> Optional[Tuple[pygame.Surface, pygame.Rect, int]]:
        参数 = self.参数[名称]
        图像 = self.升级图集.get(str(参数["资源键"]))
        if 图像 is None:
            return None

        t = 夹取(self.当前时间, 0.0, 1.0)
        开始 = float(参数["开始"])
        结束 = float(参数["结束"])
        if t < 开始:
            return None

        if t <= 结束:
            局部进度 = (t - 开始) / max(0.0001, 结束 - 开始)
            缩放 = 线性插值(float(参数["起始缩放"]), float(参数["结束缩放"]), 局部进度)
            alpha = int(
                线性插值(float(参数["alpha起"]), float(参数["alpha止"]), 局部进度)
            )
        else:
            缩放 = float(参数["结束缩放"])
            alpha = int(参数["alpha止"])

        基准矩形 = self.取小窗矩形()
        基础尺寸 = float(参数["尺寸"])
        尺寸 = int(max(2, 基础尺寸 * 缩放))
        渲染图 = self.缩放图(图像, 尺寸, 尺寸)
        if 渲染图 is None:
            return None

        alpha = max(0, min(255, alpha))
        try:
            渲染图 = 渲染图.copy()
            渲染图.set_alpha(alpha)
        except Exception:
            pass

        中心x = int(round(基准矩形.x + 基准矩形.w * float(参数["中心x"])))
        中心y = int(round(基准矩形.y + 基准矩形.h * float(参数["中心y"])))
        目标矩形 = 渲染图.get_rect(center=(中心x, 中心y))
        return 渲染图, 目标矩形, alpha

    def 画升级动画(self):
        主图结果 = self.计算主图状态()
        角标结果字典 = {
            "左上": self.计算角标状态("左上"),
            "右上": self.计算角标状态("右上"),
            "左下": self.计算角标状态("左下"),
            "右下": self.计算角标状态("右下"),
        }

        绘制顺序 = ["左上", "右上", "左下", "右下"]
        for 名称 in 绘制顺序:
            结果 = 角标结果字典[名称]
            if 结果 is None:
                continue
            图像, 矩形, _ = 结果
            self.屏幕.blit(图像, 矩形.topleft)
            if self.是否显示辅助线:
                颜色 = (80, 255, 120) if self.当前选中项 == 名称 else (255, 180, 80)
                pygame.draw.rect(self.屏幕, 颜色, 矩形, 2)
                pygame.draw.circle(self.屏幕, 颜色, 矩形.center, 4)
                self.画文字(名称, (矩形.x, 矩形.y - 18), 颜色, self.小字体)

        if 主图结果 is not None:
            图像, 矩形, _ = 主图结果
            self.屏幕.blit(图像, 矩形.topleft)
            if self.是否显示辅助线:
                颜色 = (255, 80, 80) if self.当前选中项 == "主图" else (255, 220, 120)
                pygame.draw.rect(self.屏幕, 颜色, 矩形, 2)
                pygame.draw.circle(self.屏幕, 颜色, 矩形.center, 5)
                self.画文字("主图", (矩形.x, 矩形.y - 20), 颜色, self.小字体)

    def 画顶部说明(self):
        self.画文字(
            "Tab切换对象  空格播放/暂停  R重置时间  F5保存  G辅助线",
            (12, 10),
            (255, 255, 200),
        )
        self.画文字(
            "方向键: 移动位置   Q/E: 缩放/尺寸   Z/C: alpha倍率或alpha终值",
            (12, 36),
            (255, 255, 200),
        )
        self.画文字(
            "1/2: 开始时间   3/4: 结束时间   -/=: 时间倒退/前进",
            (12, 62),
            (255, 255, 200),
        )
        self.画文字("Shift = 大步长   Ctrl = 小步长", (12, 88), (255, 255, 200))

    def 画底部面板(self):
        面板矩形 = pygame.Rect(0, self.窗口高 - 170, self.窗口宽, 170)
        底板 = pygame.Surface(面板矩形.size, pygame.SRCALPHA)
        底板.fill((0, 0, 0, 170))
        self.屏幕.blit(底板, 面板矩形.topleft)

        self.画文字(
            f"当前时间: {self.当前时间:.3f} / 1.000",
            (16, self.窗口高 - 156),
            (255, 255, 255),
            self.大字体,
        )
        self.画文字(
            f"当前对象: {self.当前选中项}",
            (16, self.窗口高 - 124),
            (80, 255, 180),
            self.字体,
        )

        if self.当前选中项 == "主图":
            参数 = self.参数["主图"]
            文本列表 = [
                f"中心x={参数['基准中心x']:.3f} 中心y={参数['基准中心y']:.3f}",
                f"基准宽={参数['基准宽']:.1f} 基准高={参数['基准高']:.1f}",
                f"初始缩放={参数['初始缩放']:.3f} 峰值缩放={参数['峰值缩放']:.3f} 回落缩放={参数['回落缩放']:.3f}",
                f"峰值分界={参数['峰值分界']:.3f} 回落分界={参数['回落分界']:.3f}",
                f"alpha倍率={参数['alpha倍率']:.3f}",
            ]
        else:
            参数 = self.参数[self.当前选中项]
            文本列表 = [
                f"中心x={参数['中心x']:.3f} 中心y={参数['中心y']:.3f}",
                f"尺寸={参数['尺寸']:.1f}",
                f"开始={参数['开始']:.3f} 结束={参数['结束']:.3f}",
                f"起始缩放={参数['起始缩放']:.3f} 结束缩放={参数['结束缩放']:.3f}",
                f"alpha起={参数['alpha起']:.1f} alpha止={参数['alpha止']:.1f}",
            ]

        for 索引, 文本 in enumerate(文本列表):
            self.画文字(
                文本, (16, self.窗口高 - 94 + 索引 * 24), (220, 220, 220), self.小字体
            )

        小窗参数 = self.参数["小窗"]
        右侧文本 = [
            f"小窗 x={小窗参数['x']} y={小窗参数['y']} w={小窗参数['w']} h={小窗参数['h']}",
            "快捷键：",
            "F1/F2 调小窗宽高，F3/F4 调小窗位置",
            "S 保存，L 重新读取，0 恢复默认",
        ]
        for 索引, 文本 in enumerate(右侧文本):
            self.画文字(
                文本, (760, self.窗口高 - 150 + 索引 * 26), (200, 220, 255), self.小字体
            )

    def 调整数值(self, 键盘状态):
        大步 = 0.02
        小步 = 0.002
        像素大步 = 8
        像素小步 = 1

        if 键盘状态[pygame.K_LSHIFT] or 键盘状态[pygame.K_RSHIFT]:
            比例步长 = 大步
            像素步长 = 像素大步
        elif 键盘状态[pygame.K_LCTRL] or 键盘状态[pygame.K_RCTRL]:
            比例步长 = 小步
            像素步长 = 像素小步
        else:
            比例步长 = 0.005
            像素步长 = 3

        当前对象 = self.当前选中项

        if 当前对象 == "主图":
            参数 = self.参数["主图"]
            if 键盘状态[pygame.K_LEFT]:
                参数["基准中心x"] = 夹取(float(参数["基准中心x"]) - 比例步长, -1.0, 2.0)
            if 键盘状态[pygame.K_RIGHT]:
                参数["基准中心x"] = 夹取(float(参数["基准中心x"]) + 比例步长, -1.0, 2.0)
            if 键盘状态[pygame.K_UP]:
                参数["基准中心y"] = 夹取(float(参数["基准中心y"]) - 比例步长, -1.0, 2.0)
            if 键盘状态[pygame.K_DOWN]:
                参数["基准中心y"] = 夹取(float(参数["基准中心y"]) + 比例步长, -1.0, 2.0)
        else:
            参数 = self.参数[当前对象]
            if 键盘状态[pygame.K_LEFT]:
                参数["中心x"] = 夹取(float(参数["中心x"]) - 比例步长, -1.0, 2.0)
            if 键盘状态[pygame.K_RIGHT]:
                参数["中心x"] = 夹取(float(参数["中心x"]) + 比例步长, -1.0, 2.0)
            if 键盘状态[pygame.K_UP]:
                参数["中心y"] = 夹取(float(参数["中心y"]) - 比例步长, -1.0, 2.0)
            if 键盘状态[pygame.K_DOWN]:
                参数["中心y"] = 夹取(float(参数["中心y"]) + 比例步长, -1.0, 2.0)

        if 键盘状态[pygame.K_q]:
            if 当前对象 == "主图":
                参数["基准宽"] = max(10.0, float(参数["基准宽"]) - 像素步长)
                参数["基准高"] = max(10.0, float(参数["基准高"]) - 像素步长)
            else:
                参数["尺寸"] = max(10.0, float(参数["尺寸"]) - 像素步长)

        if 键盘状态[pygame.K_e]:
            if 当前对象 == "主图":
                参数["基准宽"] = float(参数["基准宽"]) + 像素步长
                参数["基准高"] = float(参数["基准高"]) + 像素步长
            else:
                参数["尺寸"] = float(参数["尺寸"]) + 像素步长

    def 处理单次按键(self, 键值: int):
        选择列表 = ["主图", "左上", "右上", "左下", "右下"]

        if 键值 == pygame.K_TAB:
            当前索引 = 选择列表.index(self.当前选中项)
            self.当前选中项 = 选择列表[(当前索引 + 1) % len(选择列表)]
        elif 键值 == pygame.K_SPACE:
            self.是否自动播放 = not self.是否自动播放
        elif 键值 == pygame.K_r:
            self.当前时间 = 0.0
        elif 键值 == pygame.K_g:
            self.是否显示辅助线 = not self.是否显示辅助线
        elif 键值 == pygame.K_F5 or 键值 == pygame.K_s:
            self.保存参数()
        elif 键值 == pygame.K_l:
            self.读取参数()
        elif 键值 == pygame.K_0:
            self.参数 = self.加载默认参数()
        elif 键值 == pygame.K_MINUS:
            self.当前时间 = max(0.0, self.当前时间 - 0.02)
        elif 键值 == pygame.K_EQUALS:
            self.当前时间 = min(1.0, self.当前时间 + 0.02)

        当前对象 = self.当前选中项
        if 当前对象 == "主图":
            参数 = self.参数["主图"]
            if 键值 == pygame.K_1:
                参数["峰值分界"] = 夹取(float(参数["峰值分界"]) - 0.01, 0.01, 0.95)
            elif 键值 == pygame.K_2:
                参数["峰值分界"] = 夹取(float(参数["峰值分界"]) + 0.01, 0.01, 0.95)
            elif 键值 == pygame.K_3:
                参数["回落分界"] = 夹取(
                    float(参数["回落分界"]) - 0.01, float(参数["峰值分界"]) + 0.01, 1.0
                )
            elif 键值 == pygame.K_4:
                参数["回落分界"] = 夹取(
                    float(参数["回落分界"]) + 0.01, float(参数["峰值分界"]) + 0.01, 1.0
                )
            elif 键值 == pygame.K_z:
                参数["alpha倍率"] = max(0.0, float(参数["alpha倍率"]) - 0.05)
            elif 键值 == pygame.K_c:
                参数["alpha倍率"] = min(3.0, float(参数["alpha倍率"]) + 0.05)
        else:
            参数 = self.参数[当前对象]
            if 键值 == pygame.K_1:
                参数["开始"] = 夹取(
                    float(参数["开始"]) - 0.01,
                    0.0,
                    min(0.99, float(参数["结束"]) - 0.01),
                )
            elif 键值 == pygame.K_2:
                参数["开始"] = 夹取(
                    float(参数["开始"]) + 0.01,
                    0.0,
                    min(0.99, float(参数["结束"]) - 0.01),
                )
            elif 键值 == pygame.K_3:
                参数["结束"] = 夹取(
                    float(参数["结束"]) - 0.01, float(参数["开始"]) + 0.01, 1.0
                )
            elif 键值 == pygame.K_4:
                参数["结束"] = 夹取(
                    float(参数["结束"]) + 0.01, float(参数["开始"]) + 0.01, 1.0
                )
            elif 键值 == pygame.K_z:
                参数["alpha止"] = max(0.0, float(参数["alpha止"]) - 5.0)
            elif 键值 == pygame.K_c:
                参数["alpha止"] = min(255.0, float(参数["alpha止"]) + 5.0)

        小窗参数 = self.参数["小窗"]
        if 键值 == pygame.K_F1:
            小窗参数["w"] = max(100, int(小窗参数["w"]) - 10)
        elif 键值 == pygame.K_F2:
            小窗参数["w"] = int(小窗参数["w"]) + 10
        elif 键值 == pygame.K_F3:
            小窗参数["x"] = int(小窗参数["x"]) - 10
        elif 键值 == pygame.K_F4:
            小窗参数["x"] = int(小窗参数["x"]) + 10
        elif 键值 == pygame.K_F6:
            小窗参数["h"] = max(100, int(小窗参数["h"]) - 10)
        elif 键值 == pygame.K_F7:
            小窗参数["h"] = int(小窗参数["h"]) + 10
        elif 键值 == pygame.K_F8:
            小窗参数["y"] = int(小窗参数["y"]) - 10
        elif 键值 == pygame.K_F9:
            小窗参数["y"] = int(小窗参数["y"]) + 10

    def 处理事件(self):
        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                self.运行中 = False
            elif 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    self.运行中 = False
                else:
                    self.处理单次按键(事件.key)

    def 更新(self, 帧秒: float):
        键盘状态 = pygame.key.get_pressed()
        self.调整数值(键盘状态)
        if self.是否自动播放:
            self.当前时间 += 帧秒 * 0.55
            if self.当前时间 > self.总时长:
                self.当前时间 = 0.0

    def 绘制(self):
        self.画背景()
        self.画小窗()
        self.画升级动画()
        self.画顶部说明()
        self.画底部面板()
        pygame.display.flip()

    def 运行(self):
        while self.运行中:
            帧秒 = self.时钟.tick(60) / 1000.0
            self.处理事件()
            self.更新(帧秒)
            self.绘制()
        pygame.quit()


def main():
    升级动画调试器().运行()


if __name__ == "__main__":
    main()
