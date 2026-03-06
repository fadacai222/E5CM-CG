import time
import pygame


class 公共黑屏过渡:
    """
    两段式：
    - 渐入黑屏（0.1s）：alpha 0 -> 255
    - 切换发生在黑屏到达 255 时
    - 渐出黑屏（0.1s）：alpha 255 -> 0

    这样能最大程度掩盖切换时的卡顿。
    """

    def __init__(self, 渐入秒: float = 0.1, 渐出秒: float = 0.1):
        self.渐入秒 = float(渐入秒)
        self.渐出秒 = float(渐出秒)

        self._是否进行中 = False
        self._阶段 = "无"  # 无 / 渐入 / 渐出
        self._开始时间 = 0.0

        self._待切换目标场景名 = None
        self._是否已触发切换回调 = False

    def 开始(self, 目标场景名: str):
        # 若正在过渡，直接覆盖目标（避免队列堆积）
        self._是否进行中 = True
        self._阶段 = "渐入"
        self._开始时间 = time.time()
        self._待切换目标场景名 = 目标场景名
        self._是否已触发切换回调 = False

    def 是否进行中(self) -> bool:
        return self._是否进行中

    def 获取目标场景名(self):
        return self._待切换目标场景名

    def 更新(self, 触发切换回调):
        """
        由 main.py 每帧调用。
        - 当渐入完成时（黑屏最黑），调用一次 触发切换回调()
        - 然后进入渐出阶段
        """
        if not self._是否进行中:
            return

        现在 = time.time()
        if self._阶段 == "渐入":
            if (现在 - self._开始时间) >= self.渐入秒:
                # 到达全黑
                if not self._是否已触发切换回调:
                    self._是否已触发切换回调 = True
                    try:
                        触发切换回调()
                    except Exception:
                        # 回调异常也不要把主循环炸掉
                        pass

                # 开始渐出
                self._阶段 = "渐出"
                self._开始时间 = time.time()

        elif self._阶段 == "渐出":
            if (现在 - self._开始时间) >= self.渐出秒:
                # 完成
                self._是否进行中 = False
                self._阶段 = "无"
                self._待切换目标场景名 = None
                self._是否已触发切换回调 = False

    def 绘制(self, 屏幕: pygame.Surface):
        if not self._是否进行中:
            return

        现在 = time.time()
        alpha = 0

        if self._阶段 == "渐入":
            t = (现在 - self._开始时间) / max(0.001, self.渐入秒)
            t = max(0.0, min(1.0, t))
            alpha = int(255 * t)

        elif self._阶段 == "渐出":
            t = (现在 - self._开始时间) / max(0.001, self.渐出秒)
            t = max(0.0, min(1.0, t))
            alpha = int(255 * (1.0 - t))

        if alpha <= 0:
            return

        w, h = 屏幕.get_size()
        黑层 = pygame.Surface((w, h), pygame.SRCALPHA)
        黑层.fill((0, 0, 0, alpha))
        屏幕.blit(黑层, (0, 0))


class 公用放大过渡器:
    def __init__(
        self,
        总时长毫秒: int = 520,
        缩小阶段占比: float = 0.25,
        缩小到: float = 0.92,
        透明起始: int = 255,
        透明结束: int = 0,
        # ✅ 放大到全屏时加一点余量，避免边缘露黑（cover更稳）
        覆盖余量: float = 1.04,
    ):
        self.总时长毫秒 = int(总时长毫秒)
        self.缩小阶段占比 = float(缩小阶段占比)
        self.缩小到 = float(缩小到)
        self.透明起始 = int(透明起始)
        self.透明结束 = int(透明结束)
        self.覆盖余量 = float(覆盖余量)

        self._开始毫秒 = 0
        self._进行中 = False
        self._起始图: pygame.Surface | None = None
        self._起始rect = pygame.Rect(0, 0, 1, 1)

        # 动态计算出来的“放大到倍数”
        self._放大到 = 4.0

    def 开始(self, 起始图: pygame.Surface, 起始rect: pygame.Rect):
        self._起始图 = 起始图
        self._起始rect = 起始rect.copy()
        self._开始毫秒 = pygame.time.get_ticks()
        self._进行中 = True
        self._放大到 = 4.0  # 先给默认，首次绘制时会按屏幕尺寸重算

    def 是否进行中(self) -> bool:
        return bool(self._进行中)

    def 是否完成(self) -> bool:
        if not self._进行中:
            return False
        return (pygame.time.get_ticks() - self._开始毫秒) >= max(1, self.总时长毫秒)

    def _计算覆盖全屏倍数(self, 屏幕: pygame.Surface) -> float:
        sw, sh = 屏幕.get_size()
        w0 = max(1, int(self._起始rect.w))
        h0 = max(1, int(self._起始rect.h))

        # ✅ cover：至少有一边铺满，另一边允许超出
        倍数 = max(sw / w0, sh / h0) * max(1.0, float(self.覆盖余量))
        # 保底：别太小
        return max(1.0, float(倍数))

    def 更新并绘制(self, 屏幕: pygame.Surface):
        if (not self._进行中) or (self._起始图 is None):
            return

        # ✅ 动态算“放大到全屏”的倍数（屏幕改尺寸也能跟着变）
        self._放大到 = self._计算覆盖全屏倍数(屏幕)

        现在 = pygame.time.get_ticks()
        t = (现在 - self._开始毫秒) / max(1, self.总时长毫秒)
        t = max(0.0, min(1.0, float(t)))

        # 参考按钮点击特效：两段
        缩小占比 = max(0.05, min(0.95, float(self.缩小阶段占比)))

        if t < 缩小占比:
            k = t / max(0.0001, 缩小占比)
            scale = 1.0 + (self.缩小到 - 1.0) * k
            alpha = self.透明起始
        else:
            k = (t - 缩小占比) / max(0.0001, (1.0 - 缩小占比))
            scale = self.缩小到 + (self._放大到 - self.缩小到) * k
            alpha = int(self.透明起始 + (self.透明结束 - self.透明起始) * k)
            alpha = max(0, min(255, alpha))

        # ✅ 围绕起始rect中心缩放（按钮点击特效同款手感）
        ww = max(1, int(self._起始rect.w * scale))
        hh = max(1, int(self._起始rect.h * scale))
        x = int(self._起始rect.centerx - ww // 2)
        y = int(self._起始rect.centery - hh // 2)

        图2 = pygame.transform.smoothscale(self._起始图, (ww, hh)).convert_alpha()
        图2.set_alpha(alpha)

        屏幕.blit(图2, (x, y))

        if t >= 1.0:
            self._进行中 = False
