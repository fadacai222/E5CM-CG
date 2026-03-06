import time
import pygame


class 公用按钮点击特效:
    """
    通用按钮点击动画：
    - 总时长 0.3s
    - 前 0.1s：缩小到 shrink_to
    - 后 0.2s：放大到 expand_to，并透明度从 255 线性降到 0
    """

    def __init__(
        self,
        总时长: float = 0.3,
        缩小阶段: float = 0.1,
        缩小到: float = 0.90,
        放大到: float = 4.00,
        透明起始: int = 255,
        透明结束: int = 0,
    ):
        self.总时长 = float(总时长)
        self.缩小阶段 = float(缩小阶段)
        self.缩小到 = float(缩小到)
        self.放大到 = float(放大到)
        self.透明起始 = int(透明起始)
        self.透明结束 = int(透明结束)

        self._动画开始 = 0.0
        self._动画中 = False

    def 触发(self):
        self._动画开始 = time.time()
        self._动画中 = True

    def 是否动画中(self) -> bool:
        if not getattr(self, "_动画中", False):
            return False
        import time as _time

        if (_time.time() - getattr(self, "_动画开始", 0.0)) >= float(
            getattr(self, "总时长", 0.3)
        ):
            self._动画中 = False
            return False
        return True

    def 计算参数(self, 当前时间: float):
        if not self._动画中:
            return 1.0, 255, False

        t = (当前时间 - self._动画开始) / max(0.001, self.总时长)
        if t >= 1.0:
            self._动画中 = False
            return 1.0, 255, True

        缩小占比 = self.缩小阶段 / max(0.001, self.总时长)

        if t < 缩小占比:
            k = t / max(0.001, 缩小占比)
            scale = 1.0 + (self.缩小到 - 1.0) * k
            alpha = self.透明起始
            return scale, alpha, False

        # 放大 + 淡出
        k = (t - 缩小占比) / max(0.001, (1.0 - 缩小占比))
        scale = self.缩小到 + (self.放大到 - self.缩小到) * k
        alpha = int(self.透明起始 + (self.透明结束 - self.透明起始) * k)
        alpha = max(0, min(255, alpha))
        return scale, alpha, False

    def 绘制按钮(
        self, 屏幕: pygame.Surface, 原图: pygame.Surface, 基准矩形: pygame.Rect
    ):
        """
        - 原图：按钮的“标准尺寸贴图”（通常等于基准矩形大小的图）
        - 基准矩形：按钮原本应该显示的位置/大小（用于居中放大）
        """
        现在 = time.time()
        scale, alpha, _结束 = self.计算参数(现在)

        if scale == 1.0 and alpha == 255:
            屏幕.blit(原图, 基准矩形.topleft)
            return

        ww = max(1, int(基准矩形.w * scale))
        hh = max(1, int(基准矩形.h * scale))
        x = 基准矩形.centerx - ww // 2
        y = 基准矩形.centery - hh // 2

        图 = pygame.transform.smoothscale(原图, (ww, hh)).convert_alpha()
        图.set_alpha(alpha)
        屏幕.blit(图, (x, y))


class 公用按钮音效:
    """
    全局按钮点击音效：加载一次，多处复用
    """

    def __init__(self, 音效路径: str):
        self._音效 = None
        try:
            self._音效 = pygame.mixer.Sound(音效路径)
        except Exception:
            self._音效 = None

    def 播放(self):
        if not self._音效:
            return
        try:
            self._音效.play()
        except Exception:
            pass
