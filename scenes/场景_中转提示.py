import os
import time
from typing import Dict, Optional

import pygame

from core.对局状态 import (
    取信用数,
    取每局所需信用,
    重置游戏流程状态,
)
from core.踏板控制 import 踏板动作_左, 踏板动作_右, 踏板动作_确认
from core.工具 import 绘制底部联网与信用
from scenes.场景基类 import 场景基类
from ui.settlement_scene_shared import (
    加载结算提示资源,
    执行返回选歌 as _执行共享返回选歌,
    构建继续动作,
    构建返回选歌动作 as _构建共享返回选歌动作,
    推进对局流程,
    取资源根目录 as _取资源根目录,
    解析结算流程上下文,
)


def _安全载图(路径: str, 透明: bool = True) -> Optional[pygame.Surface]:
    try:
        if 路径 and os.path.isfile(路径):
            图 = pygame.image.load(路径)
            return 图.convert_alpha() if 透明 else 图.convert()
    except Exception:
        pass
    return None


def _获取字体(字号: int, 是否粗体: bool = False) -> pygame.font.Font:
    try:
        from core.工具 import 获取字体  # type: ignore

        return 获取字体(int(字号), 是否粗体=bool(是否粗体))
    except Exception:
        pygame.font.init()
        try:
            return pygame.font.SysFont(
                "Microsoft YaHei", int(字号), bold=bool(是否粗体)
            )
        except Exception:
            return pygame.font.Font(None, int(字号))


def _夹取(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


class 场景_中转提示(场景基类):
    名称 = "中转提示"

    def __init__(self, 上下文: dict):
        super().__init__(上下文)
        self._载荷: Dict[str, object] = {}
        self._背景截图: Optional[pygame.Surface] = None
        self._背景图: Optional[pygame.Surface] = None
        self._背景缩放缓存: Optional[pygame.Surface] = None
        self._背景缩放尺寸 = (0, 0)
        self._提示图集: Dict[str, pygame.Surface] = {}
        self._倒计时图集: Dict[str, pygame.Surface] = {}
        self._是按钮图: Optional[pygame.Surface] = None
        self._否按钮图: Optional[pygame.Surface] = None
        self._联网原图: Optional[pygame.Surface] = None

        self._进入系统秒 = 0.0
        self._阶段开始秒 = 0.0
        self._退出开始秒 = 0.0
        self._退出动作: Optional[dict] = None

        self._阶段类型 = ""
        self._提示键 = ""
        self._阶段持续秒 = 0.0
        self._是否显示倒计时 = False
        self._继续动作: Optional[dict] = None
        self._默认否动作: Optional[dict] = None
        self._按钮选中 = "是"

        self._当前关卡 = 1
        self._每局所需信用 = 3
        self._是否失败 = False
        self._结算后S数 = 0
        self._三把S赠送 = False

        self._是按钮rect = pygame.Rect(0, 0, 1, 1)
        self._否按钮rect = pygame.Rect(0, 0, 1, 1)
        self._回退字体 = _获取字体(34, True)

    def 进入(self, 载荷=None):
        self._载荷 = dict(载荷) if isinstance(载荷, dict) else {}
        self._进入系统秒 = time.perf_counter()
        self._阶段开始秒 = self._进入系统秒
        self._退出开始秒 = 0.0
        self._退出动作 = None
        self._阶段类型 = ""
        self._提示键 = ""
        self._阶段持续秒 = 0.0
        self._是否显示倒计时 = False
        self._继续动作 = None
        self._默认否动作 = None
        self._按钮选中 = "是"
        self._背景缩放缓存 = None
        self._背景缩放尺寸 = (0, 0)
        self._每局所需信用 = 取每局所需信用(self.上下文.get("状态", {}))

        self._加载资源()
        self._解析结算上下文()
        self._配置初始流程()

    def 退出(self):
        return

    def 更新(self):
        当前系统秒 = time.perf_counter()

        if self._退出动作 is not None:
            if (当前系统秒 - float(self._退出开始秒 or 当前系统秒)) >= 0.35:
                return self._构建退出结果(self._退出动作)
            return None

        if self._阶段类型 == "自动提示":
            if (当前系统秒 - float(self._阶段开始秒 or 当前系统秒)) >= float(
                self._阶段持续秒 or 0.0
            ):
                self._开始退出(dict(self._继续动作 or {}))
            return None

        if self._阶段类型 == "续币等待":
            当前信用 = 取信用数(self.上下文.get("状态", {}))
            if 当前信用 >= int(self._每局所需信用):
                self._处理续币成功()
                return None

            if (当前系统秒 - float(self._阶段开始秒 or 当前系统秒)) >= float(
                self._阶段持续秒 or 0.0
            ):
                self._播放游戏结束音效()
                self._进入自动提示(
                    提示键="游戏结束",
                    持续秒=3.0,
                    动作={"类型": "投币"},
                    显示倒计时=False,
                )
            return None

        if self._阶段类型 == "继续挑战":
            if (当前系统秒 - float(self._阶段开始秒 or 当前系统秒)) >= float(
                self._阶段持续秒 or 0.0
            ):
                self._执行否分支()
            return None

        return None

    def 处理事件(self, 事件):
        if self._退出动作 is not None:
            return None

        if self._阶段类型 != "继续挑战":
            return None

        if 事件.type == pygame.MOUSEMOTION:
            if self._是按钮rect.collidepoint(事件.pos):
                self._按钮选中 = "是"
            elif self._否按钮rect.collidepoint(事件.pos):
                self._按钮选中 = "否"
            return None

        if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            if self._是按钮rect.collidepoint(事件.pos):
                self._执行是分支()
            elif self._否按钮rect.collidepoint(事件.pos):
                self._执行否分支()
            return None

        if 事件.type == pygame.KEYDOWN:
            if 事件.key in (pygame.K_LEFT, pygame.K_KP1, pygame.K_a):
                self._按钮选中 = "是"
            elif 事件.key in (pygame.K_RIGHT, pygame.K_KP3, pygame.K_d):
                self._按钮选中 = "否"
            elif 事件.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_KP5):
                if self._按钮选中 == "是":
                    self._执行是分支()
                else:
                    self._执行否分支()
            elif 事件.key == pygame.K_y:
                self._执行是分支()
            elif 事件.key in (pygame.K_n, pygame.K_ESCAPE):
                self._执行否分支()
        return None

    def 处理全局踏板(self, 动作: str):
        if self._退出动作 is not None or self._阶段类型 != "继续挑战":
            return None
        if 动作 == 踏板动作_左:
            self._按钮选中 = "是"
            return None
        if 动作 == 踏板动作_右:
            self._按钮选中 = "否"
            return None
        if 动作 == 踏板动作_确认:
            if self._按钮选中 == "是":
                self._执行是分支()
            else:
                self._执行否分支()
        return None

    def 绘制(self):
        屏幕: pygame.Surface = self.上下文["屏幕"]
        屏宽, 屏高 = 屏幕.get_size()

        self._绘制背景(屏幕)

        进入进度 = _夹取(
            (time.perf_counter() - float(self._进入系统秒 or 0.0)) / 0.35, 0.0, 1.0
        )
        退出进度 = 1.0
        if self._退出动作 is not None:
            退出进度 = 1.0 - _夹取(
                (time.perf_counter() - float(self._退出开始秒 or 0.0)) / 0.35, 0.0, 1.0
            )
        总透明度 = _夹取(进入进度 * 退出进度, 0.0, 1.0)

        遮罩 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
        遮罩.fill((0, 0, 0, int(90 * 总透明度)))
        屏幕.blit(遮罩, (0, 0))

        提示区 = pygame.Rect(
            int(屏宽 * 0.16),
            int(屏高 * 0.12),
            int(屏宽 * 0.68),
            int(屏高 * 0.34),
        )
        self._绘制提示图(屏幕, 提示区, 总透明度)

        if self._阶段类型 == "继续挑战":
            self._绘制选择按钮(屏幕, 总透明度)

        if self._是否显示倒计时:
            self._绘制倒计时(屏幕, 总透明度)

        self._绘制底部币值(屏幕)

    def _加载资源(self):
        根目录 = _取资源根目录(self.上下文)
        (
            self._提示图集,
            self._倒计时图集,
            self._是按钮图,
            self._否按钮图,
        ) = 加载结算提示资源(根目录)

        联网图路径 = str(
            (self.上下文.get("资源", {}) or {}).get("投币_联网图标", "") or ""
        )
        self._联网原图 = _安全载图(联网图路径)

        背景截图 = self._载荷.get("结算背景截图")
        self._背景截图 = (
            背景截图.copy() if isinstance(背景截图, pygame.Surface) else None
        )

        背景路径 = str(self._载荷.get("背景图片路径", "") or "")
        if (not 背景路径) or (not os.path.isfile(背景路径)):
            背景路径 = os.path.join(根目录, "冷资源", "backimages", "选歌界面.png")
        self._背景图 = _安全载图(背景路径, 透明=False)

    def _解析结算上下文(self):
        流程上下文 = 解析结算流程上下文(self._载荷, self.上下文.get("状态", {}))
        self._当前关卡 = int(流程上下文["当前关卡"])
        self._是否失败 = bool(流程上下文["是否失败"])
        self._结算后S数 = int(流程上下文["结算后S数"])
        self._三把S赠送 = bool(流程上下文["三把S赠送"])

    def _配置初始流程(self):
        if self._三把S赠送:
            self._准备进入下一把(
                下一关卡=4,
                提示键="赠送一把",
                提示秒数=3.0,
                累计S数=3,
                赠送第四把=True,
            )
            return

        if self._当前关卡 in (1, 2):
            if not self._是否失败:
                self._准备进入下一把(
                    下一关卡=self._当前关卡 + 1,
                    提示键="下一把",
                    提示秒数=3.0,
                    累计S数=self._结算后S数,
                    赠送第四把=False,
                )
            else:
                self._进入是否继续分支(
                    下一关卡=self._当前关卡 + 1,
                    重开新局=False,
                )
            return

        self._进入是否继续分支(
            下一关卡=1,
            重开新局=True,
        )

    def _进入是否继续分支(self, *, 下一关卡: int, 重开新局: bool):
        if 取信用数(self.上下文.get("状态", {})) >= int(self._每局所需信用):
            self._进入继续挑战提示(
                下一关卡=下一关卡,
                重开新局=bool(重开新局),
            )
            return

        self._阶段类型 = "续币等待"
        self._提示键 = "是否续币"
        self._阶段开始秒 = time.perf_counter()
        self._阶段持续秒 = 10.0
        self._是否显示倒计时 = True
        self._继续动作 = 构建继续动作(
            self._构建返回选歌动作(),
            下一关卡=下一关卡,
            重开新局=重开新局,
            累计S数=self._结算后S数,
            每局所需信用=self._每局所需信用,
        )
        self._默认否动作 = {"类型": "投币"}

    def _进入继续挑战提示(self, *, 下一关卡: int, 重开新局: bool):
        self._阶段类型 = "继续挑战"
        self._提示键 = "继续挑战"
        self._阶段开始秒 = time.perf_counter()
        self._阶段持续秒 = 10.0
        self._是否显示倒计时 = True
        self._按钮选中 = "是"
        self._继续动作 = 构建继续动作(
            self._构建返回选歌动作(),
            下一关卡=下一关卡,
            重开新局=重开新局,
            累计S数=self._结算后S数,
            每局所需信用=self._每局所需信用,
            需要消耗信用=True,
        )
        self._默认否动作 = {"类型": "投币"}

    def _进入自动提示(
        self,
        *,
        提示键: str,
        持续秒: float,
        动作: dict,
        显示倒计时: bool = False,
    ):
        self._阶段类型 = "自动提示"
        self._提示键 = str(提示键 or "")
        self._阶段开始秒 = time.perf_counter()
        self._阶段持续秒 = float(max(0.1, 持续秒))
        self._继续动作 = dict(动作 or {})
        self._是否显示倒计时 = bool(显示倒计时)

    def _准备进入下一把(
        self,
        *,
        下一关卡: int,
        提示键: str,
        提示秒数: float,
        累计S数: int,
        赠送第四把: bool,
        消耗数量: int = 0,
        重开新局: bool = False,
    ):
        推进对局流程(
            self.上下文.get("状态", {}),
            下一关卡=下一关卡,
            累计S数=累计S数,
            赠送第四把=赠送第四把,
            消耗数量=消耗数量,
            重开新局=重开新局,
        )
        self._进入自动提示(
            提示键=提示键,
            持续秒=提示秒数,
            动作=self._构建返回选歌动作(),
            显示倒计时=False,
        )

    def _处理续币成功(self):
        动作 = dict(self._继续动作 or {})
        下一关卡 = int(动作.get("下一关卡", 1) or 1)
        重开新局 = bool(动作.get("重开新局", False))
        累计S数 = int(动作.get("累计S数", 0) or 0)
        self._准备进入下一把(
            下一关卡=下一关卡,
            提示键="下一把",
            提示秒数=3.0,
            累计S数=累计S数,
            赠送第四把=False,
            消耗数量=int(self._每局所需信用),
            重开新局=重开新局,
        )

    def _执行是分支(self):
        动作 = dict(self._继续动作 or {})
        下一关卡 = int(动作.get("下一关卡", 1) or 1)
        重开新局 = bool(动作.get("重开新局", False))
        累计S数 = int(动作.get("累计S数", 0) or 0)
        推进对局流程(
            self.上下文.get("状态", {}),
            下一关卡=下一关卡,
            累计S数=累计S数,
            赠送第四把=False,
            消耗数量=int(动作.get("消耗信用", 0) or 0),
            重开新局=重开新局,
        )
        self._开始退出(self._构建返回选歌动作())

    def _执行否分支(self):
        self._开始退出(dict(self._默认否动作 or {"类型": "投币"}))

    def _开始退出(self, 动作: dict):
        if self._退出动作 is not None:
            return
        self._退出动作 = dict(动作 or {})
        self._退出开始秒 = time.perf_counter()

    def _构建退出结果(self, 动作: dict):
        类型 = str((动作 or {}).get("类型", "") or "")
        if 类型 == "投币":
            重置游戏流程状态(self.上下文.get("状态", {}))
            return {"切换到": "投币", "禁用黑屏过渡": True}
        if 类型 == "选歌":
            return self._返回选歌(动作)
        return None

    def _播放游戏结束音效(self):
        try:
            if not pygame.mixer.get_init():
                return
        except Exception:
            return

        根目录 = _取资源根目录(self.上下文)
        音效路径 = os.path.join(根目录, "冷资源", "backsound", "gameover.mp3")
        try:
            if os.path.isfile(音效路径):
                pygame.mixer.music.stop()
                pygame.mixer.music.load(音效路径)
                pygame.mixer.music.play()
        except Exception:
            pass

    def _绘制背景(self, 屏幕: pygame.Surface):
        屏宽, 屏高 = 屏幕.get_size()
        if self._背景截图 is not None:
            if self._背景缩放缓存 is None or self._背景缩放尺寸 != (
                int(屏宽),
                int(屏高),
            ):
                try:
                    self._背景缩放缓存 = pygame.transform.smoothscale(
                        self._背景截图, (int(屏宽), int(屏高))
                    ).convert()
                except Exception:
                    self._背景缩放缓存 = self._背景截图
                self._背景缩放尺寸 = (int(屏宽), int(屏高))
            if self._背景缩放缓存 is not None:
                屏幕.blit(self._背景缩放缓存, (0, 0))
                return

        if self._背景图 is not None:
            try:
                if self._背景缩放缓存 is None or self._背景缩放尺寸 != (
                    int(屏宽),
                    int(屏高),
                ):
                    self._背景缩放缓存 = pygame.transform.smoothscale(
                        self._背景图, (int(屏宽), int(屏高))
                    ).convert()
                    self._背景缩放尺寸 = (int(屏宽), int(屏高))
                屏幕.blit(self._背景缩放缓存, (0, 0))
                return
            except Exception:
                pass
        屏幕.fill((0, 0, 0))

    def _绘制提示图(self, 屏幕: pygame.Surface, 区域: pygame.Rect, 透明度系数: float):
        图 = self._提示图集.get(self._提示键)
        if 图 is None:
            文面 = self._回退字体.render(self._提示键 or "提示", True, (255, 255, 255))
            文面 = 文面.convert_alpha()
            文面.set_alpha(int(255 * 透明度系数))
            屏幕.blit(文面, 文面.get_rect(center=区域.center).topleft)
            return

        比例 = min(
            区域.w / max(1, 图.get_width()),
            区域.h / max(1, 图.get_height()),
        )
        目标宽 = max(1, int(图.get_width() * 比例))
        目标高 = max(1, int(图.get_height() * 比例))
        try:
            图面 = pygame.transform.smoothscale(图, (目标宽, 目标高)).convert_alpha()
        except Exception:
            图面 = 图
        try:
            图面 = 图面.copy()
            图面.set_alpha(int(255 * 透明度系数))
        except Exception:
            pass
        rr = 图面.get_rect(center=区域.center)
        屏幕.blit(图面, rr.topleft)

    def _计算按钮布局(self, 屏宽: int, 屏高: int):
        按钮宽 = max(140, int(屏宽 * 0.11))
        按钮高 = max(72, int(按钮宽 * 0.42))
        间距 = max(20, int(按钮宽 * 0.24))
        中心y = int(屏高 * 0.60)
        self._是按钮rect = pygame.Rect(0, 0, 按钮宽, 按钮高)
        self._否按钮rect = pygame.Rect(0, 0, 按钮宽, 按钮高)
        self._是按钮rect.center = (屏宽 // 2 - (按钮宽 // 2 + 间距), 中心y)
        self._否按钮rect.center = (屏宽 // 2 + (按钮宽 // 2 + 间距), 中心y)

    def _绘制选择按钮(self, 屏幕: pygame.Surface, 透明度系数: float):
        屏宽, 屏高 = 屏幕.get_size()
        self._计算按钮布局(屏宽, 屏高)
        self._绘制按钮(
            屏幕,
            self._是按钮图,
            self._是按钮rect,
            self._按钮选中 == "是",
            透明度系数,
        )
        self._绘制按钮(
            屏幕,
            self._否按钮图,
            self._否按钮rect,
            self._按钮选中 == "否",
            透明度系数,
        )

    def _绘制按钮(
        self,
        屏幕: pygame.Surface,
        原图: Optional[pygame.Surface],
        基准rect: pygame.Rect,
        是否选中: bool,
        透明度系数: float,
    ):
        放大系数 = 1.08 if 是否选中 else 1.0
        宽 = max(1, int(基准rect.w * 放大系数))
        高 = max(1, int(基准rect.h * 放大系数))
        rr = pygame.Rect(0, 0, 宽, 高)
        rr.center = 基准rect.center

        if 是否选中:
            高亮 = pygame.Surface((rr.w + 24, rr.h + 24), pygame.SRCALPHA)
            高亮.fill((0, 0, 0, 0))
            pygame.draw.rect(
                高亮,
                (255, 214, 92, int(70 * 透明度系数)),
                pygame.Rect(0, 0, 高亮.get_width(), 高亮.get_height()),
                border_radius=24,
            )
            屏幕.blit(
                高亮,
                高亮.get_rect(center=rr.center).topleft,
            )

        if 原图 is None:
            pygame.draw.rect(
                屏幕,
                (255, 255, 255, int(255 * 透明度系数)),
                rr,
                width=2,
                border_radius=12,
            )
            return

        try:
            图面 = pygame.transform.smoothscale(原图, (宽, 高)).convert_alpha()
            图面.set_alpha(int(255 * 透明度系数))
        except Exception:
            图面 = 原图
        屏幕.blit(图面, 图面.get_rect(center=rr.center).topleft)

    def _绘制倒计时(self, 屏幕: pygame.Surface, 透明度系数: float):
        已过秒 = time.perf_counter() - float(self._阶段开始秒 or 0.0)
        剩余秒 = max(
            0,
            int(
                max(0.0, float(self._阶段持续秒 or 0.0) - float(已过秒) - 0.001) + 0.999
            ),
        )
        数字文本 = str(剩余秒)
        图列表 = [self._倒计时图集.get(ch) for ch in 数字文本]
        图列表 = [图 for 图 in 图列表 if isinstance(图, pygame.Surface)]
        if not 图列表:
            return

        屏宽, 屏高 = 屏幕.get_size()
        目标高 = max(74, int(屏高 * 0.11))
        缩放列表 = []
        总宽 = 0
        间距 = max(6, int(目标高 * 0.08))
        for 图 in 图列表:
            比例 = 目标高 / max(1, 图.get_height())
            宽 = max(1, int(图.get_width() * 比例))
            try:
                图面 = pygame.transform.smoothscale(图, (宽, 目标高)).convert_alpha()
                图面.set_alpha(int(255 * 透明度系数))
            except Exception:
                图面 = 图
            缩放列表.append(图面)
            总宽 += 图面.get_width()
        总宽 += max(0, len(缩放列表) - 1) * 间距
        x = (屏宽 - 总宽) // 2
        y = int(屏高 * 0.74)
        for 图面 in 缩放列表:
            屏幕.blit(图面, (x, y))
            x += 图面.get_width() + 间距

    def _绘制底部币值(self, 屏幕: pygame.Surface):
        try:
            字体_credit = (self.上下文.get("字体", {}) or {}).get("投币_credit字")
        except Exception:
            字体_credit = None
        if not isinstance(字体_credit, pygame.font.Font):
            return
        try:
            当前信用 = int(取信用数(self.上下文.get("状态", {})))
            绘制底部联网与信用(
                屏幕=屏幕,
                联网原图=self._联网原图,
                字体_credit=字体_credit,
                credit数值=f"{当前信用}/{int(self._每局所需信用)}",
                总信用需求=int(self._每局所需信用),
            )
        except Exception:
            pass

    def _构建返回选歌动作(self) -> dict:
        return _构建共享返回选歌动作(self._载荷, self.上下文.get("状态", {}))

    def _返回选歌(self, 动作: Optional[dict] = None):
        return _执行共享返回选歌(
            self.上下文.get("状态", {}),
            self._载荷,
            动作,
        )
