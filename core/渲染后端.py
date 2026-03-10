import os
import time
from typing import Callable, List, Optional, Tuple

import pygame

try:
    from pygame._sdl2 import video as _sdl2_video
except Exception:
    _sdl2_video = None


额外绘制回调 = Callable[["显示后端基类"], None]


def _规范尺寸(尺寸: Tuple[int, int]) -> Tuple[int, int]:
    try:
        宽 = int(max(1, int(尺寸[0])))
    except Exception:
        宽 = 1280
    try:
        高 = int(max(1, int(尺寸[1])))
    except Exception:
        高 = 720
    return 宽, 高


def _创建软件显示窗口(
    尺寸: Tuple[int, int],
    flags: int,
) -> pygame.Surface:
    请求flags = int(flags | pygame.DOUBLEBUF)
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


def 取桌面尺寸(默认尺寸: Tuple[int, int] = (1280, 720)) -> Tuple[int, int]:
    默认尺寸 = _规范尺寸(默认尺寸)

    try:
        尺寸列表 = pygame.display.get_desktop_sizes()
        if 尺寸列表:
            return _规范尺寸(tuple(尺寸列表[0]))
    except Exception:
        pass

    try:
        信息 = pygame.display.Info()
        宽 = int(信息.current_w or 默认尺寸[0])
        高 = int(信息.current_h or 默认尺寸[1])
        return _规范尺寸((宽, 高))
    except Exception:
        return 默认尺寸


class 显示后端基类:
    名称 = "software"
    是否GPU = False

    def __init__(
        self,
        尺寸: Tuple[int, int],
        flags: int,
        标题: str,
    ):
        self._标题 = str(标题 or "")
        self._flags = int(flags)
        self._屏幕尺寸 = _规范尺寸(尺寸)
        self._屏幕: Optional[pygame.Surface] = None
        self._最近呈现统计 = {
            "upload_ms": 0.0,
            "overlay_ms": 0.0,
            "present_ms": 0.0,
            "total_ms": 0.0,
        }

    def 取绘制屏幕(self) -> pygame.Surface:
        if self._屏幕 is None:
            raise RuntimeError("显示后端尚未初始化绘制屏幕")
        return self._屏幕

    def 取窗口尺寸(self) -> Tuple[int, int]:
        return _规范尺寸(self._屏幕尺寸)

    def 取桌面尺寸(self) -> Tuple[int, int]:
        return 取桌面尺寸(self._屏幕尺寸)

    def 设置标题(self, 标题: str):
        self._标题 = str(标题 or "")

    def 调整窗口模式(
        self,
        尺寸: Tuple[int, int],
        flags: int,
    ) -> pygame.Surface:
        raise NotImplementedError

    def 处理事件(self, 事件) -> List[pygame.event.Event]:
        return [事件]

    def 呈现(
        self,
        额外绘制: Optional[额外绘制回调] = None,
        上传脏矩形列表=None,
        强制全量上传: bool = False,
    ):
        raise NotImplementedError

    def 取最近呈现统计(self) -> dict:
        return dict(self._最近呈现统计 or {})

    def 取GPU渲染器(self):
        return None

    def 最大化窗口(self) -> bool:
        return False

    def 关闭(self):
        self._屏幕 = None


class 软件显示后端(显示后端基类):
    名称 = "software"
    是否GPU = False

    def __init__(
        self,
        尺寸: Tuple[int, int],
        flags: int,
        标题: str,
    ):
        super().__init__(尺寸, flags, 标题)
        self.设置标题(标题)
        self.调整窗口模式(尺寸, flags)

    def 设置标题(self, 标题: str):
        super().设置标题(标题)
        try:
            pygame.display.set_caption(self._标题)
        except Exception:
            pass

    def 调整窗口模式(
        self,
        尺寸: Tuple[int, int],
        flags: int,
    ) -> pygame.Surface:
        self._flags = int(flags)
        self._屏幕 = _创建软件显示窗口(_规范尺寸(尺寸), self._flags)
        self._屏幕尺寸 = _规范尺寸(self._屏幕.get_size())
        self.设置标题(self._标题)
        return self._屏幕

    def 呈现(
        self,
        额外绘制: Optional[额外绘制回调] = None,
        上传脏矩形列表=None,
        强制全量上传: bool = False,
    ):
        del 上传脏矩形列表, 强制全量上传
        开始秒 = time.perf_counter()
        overlay开始秒 = time.perf_counter()
        if callable(额外绘制):
            额外绘制(self)
        overlay_ms = (time.perf_counter() - overlay开始秒) * 1000.0
        present开始秒 = time.perf_counter()
        pygame.display.flip()
        present_ms = (time.perf_counter() - present开始秒) * 1000.0
        total_ms = (time.perf_counter() - 开始秒) * 1000.0
        self._最近呈现统计 = {
            "upload_ms": 0.0,
            "overlay_ms": float(overlay_ms),
            "present_ms": float(present_ms),
            "total_ms": float(total_ms),
        }
        return self.取最近呈现统计()


class SDL2GPU显示后端(显示后端基类):
    名称 = "gpu-sdl2"
    是否GPU = True

    def __init__(
        self,
        尺寸: Tuple[int, int],
        flags: int,
        标题: str,
        vsync: bool = False,
    ):
        if _sdl2_video is None:
            raise RuntimeError("当前 pygame 未提供 pygame._sdl2.video")

        super().__init__(尺寸, flags, 标题)
        self._window = None
        self._renderer = None
        self._主纹理 = None
        self._兼容显示面 = None
        self._vsync = bool(vsync)
        self._确保兼容显示窗口()
        self.设置标题(标题)
        self.调整窗口模式(尺寸, flags)

    def _确保兼容显示窗口(self):
        try:
            现有显示面 = pygame.display.get_surface()
            if isinstance(现有显示面, pygame.Surface):
                self._兼容显示面 = 现有显示面
                return
        except Exception:
            pass

        try:
            self._兼容显示面 = pygame.display.set_mode((1, 1), pygame.HIDDEN)
        except TypeError:
            self._兼容显示面 = pygame.display.set_mode((1, 1))
        except Exception:
            self._兼容显示面 = None

    def _确保窗口与渲染器(
        self,
        尺寸: Tuple[int, int],
        flags: int,
    ):
        尺寸 = _规范尺寸(尺寸)
        可调整 = bool(flags & pygame.RESIZABLE)

        if self._window is None:
            self._window = _sdl2_video.Window(
                title=self._标题,
                size=尺寸,
                resizable=可调整,
            )
        else:
            try:
                self._window.title = self._标题
            except Exception:
                pass
            try:
                self._window.resizable = 可调整
            except Exception:
                pass

        if self._renderer is None:
            try:
                self._renderer = _sdl2_video.Renderer(
                    self._window,
                    accelerated=1,
                    vsync=1 if self._vsync else 0,
                    target_texture=True,
                )
            except TypeError:
                self._renderer = _sdl2_video.Renderer(
                    self._window,
                    accelerated=1,
                    vsync=1 if self._vsync else 0,
                )

    def _重建绘制目标(self, 尺寸: Tuple[int, int]):
        尺寸 = _规范尺寸(尺寸)
        if self._屏幕 is not None and self._屏幕.get_size() == 尺寸:
            return

        self._确保兼容显示窗口()
        try:
            self._屏幕 = pygame.Surface(尺寸).convert()
        except Exception:
            self._屏幕 = pygame.Surface(尺寸)
        self._主纹理 = None
        self._屏幕尺寸 = 尺寸

    def _规范脏矩形列表(self, 脏矩形列表) -> List[pygame.Rect]:
        if self._屏幕 is None:
            return []
        屏幕矩形 = self._屏幕.get_rect()
        if 屏幕矩形.w <= 0 or 屏幕矩形.h <= 0:
            return []

        结果: List[pygame.Rect] = []
        for 项 in list(脏矩形列表 or []):
            try:
                if isinstance(项, pygame.Rect):
                    矩形 = 项.copy()
                else:
                    矩形 = pygame.Rect(项)
            except Exception:
                continue
            if 矩形.w <= 0 or 矩形.h <= 0:
                continue
            矩形 = 矩形.inflate(12, 12)
            矩形 = 矩形.clip(屏幕矩形)
            if 矩形.w <= 0 or 矩形.h <= 0:
                continue

            已合并 = False
            for 索引, 已有 in enumerate(结果):
                try:
                    if 已有.inflate(24, 24).colliderect(矩形):
                        结果[索引] = 已有.union(矩形)
                        已合并 = True
                        break
                except Exception:
                    continue
            if not 已合并:
                结果.append(矩形)

        if len(结果) > 12:
            return []

        try:
            脏面积 = sum(int(r.w) * int(r.h) for r in 结果)
            总面积 = int(屏幕矩形.w) * int(屏幕矩形.h)
            if 总面积 > 0 and float(脏面积) / float(总面积) >= 0.72:
                return []
        except Exception:
            return []
        return 结果

    def _同步主纹理(self, 脏矩形列表=None, 强制全量上传: bool = False):
        if self._renderer is None or self._屏幕 is None:
            return

        if self._主纹理 is None:
            self._主纹理 = _sdl2_video.Texture.from_surface(self._renderer, self._屏幕)
            return

        try:
            if bool(强制全量上传):
                self._主纹理.update(self._屏幕)
                return

            规范矩形列表 = self._规范脏矩形列表(脏矩形列表)
            if not 规范矩形列表:
                self._主纹理.update(self._屏幕)
                return

            for 矩形 in 规范矩形列表:
                self._主纹理.update(
                    self._屏幕,
                    area=(int(矩形.x), int(矩形.y), int(矩形.w), int(矩形.h)),
                )
        except Exception:
            self._主纹理 = _sdl2_video.Texture.from_surface(self._renderer, self._屏幕)

    def 设置标题(self, 标题: str):
        super().设置标题(标题)
        try:
            if self._window is not None:
                self._window.title = self._标题
        except Exception:
            pass

    def 调整窗口模式(
        self,
        尺寸: Tuple[int, int],
        flags: int,
    ) -> pygame.Surface:
        self._flags = int(flags)
        self._确保窗口与渲染器(尺寸, flags)

        if self._window is None:
            raise RuntimeError("SDL2 Window 初始化失败")

        if bool(self._flags & pygame.FULLSCREEN):
            try:
                self._window.set_fullscreen(True)
            except Exception:
                pass
            实际尺寸 = _规范尺寸(tuple(self._window.size))
        else:
            try:
                self._window.set_windowed()
            except Exception:
                pass
            try:
                self._window.size = _规范尺寸(尺寸)
            except Exception:
                pass
            实际尺寸 = _规范尺寸(tuple(self._window.size))

        self._重建绘制目标(实际尺寸)
        return self.取绘制屏幕()

    def 处理事件(self, 事件) -> List[pygame.event.Event]:
        if 事件 is None:
            return []

        窗口变化事件 = {
            getattr(pygame, "WINDOWRESIZED", -1),
            getattr(pygame, "WINDOWSIZECHANGED", -1),
        }
        if int(getattr(事件, "type", -1)) in 窗口变化事件:
            try:
                宽 = int(getattr(事件, "x", 0) or 0)
            except Exception:
                宽 = 0
            try:
                高 = int(getattr(事件, "y", 0) or 0)
            except Exception:
                高 = 0
            if 宽 <= 0 or 高 <= 0:
                try:
                    宽, 高 = tuple(self._window.size)
                except Exception:
                    宽, 高 = self._屏幕尺寸

            新尺寸 = _规范尺寸((宽, 高))
            尺寸已变化 = tuple(新尺寸) != tuple(self._屏幕尺寸)
            self._重建绘制目标(新尺寸)

            if 尺寸已变化 and (not bool(self._flags & pygame.FULLSCREEN)):
                return [
                    pygame.event.Event(
                        pygame.VIDEORESIZE,
                        {
                            "w": int(新尺寸[0]),
                            "h": int(新尺寸[1]),
                            "size": tuple(新尺寸),
                        },
                    )
                ]
            return []

        return [事件]

    def 呈现(
        self,
        额外绘制: Optional[额外绘制回调] = None,
        上传脏矩形列表=None,
        强制全量上传: bool = False,
    ):
        if self._renderer is None:
            return self.取最近呈现统计()

        开始秒 = time.perf_counter()
        upload开始秒 = time.perf_counter()
        self._同步主纹理(
            脏矩形列表=上传脏矩形列表,
            强制全量上传=bool(强制全量上传),
        )
        self._renderer.draw_color = (0, 0, 0, 255)
        self._renderer.clear()
        if self._主纹理 is not None:
            self._renderer.blit(self._主纹理)
        upload_ms = (time.perf_counter() - upload开始秒) * 1000.0

        overlay开始秒 = time.perf_counter()
        if callable(额外绘制):
            额外绘制(self)
        overlay_ms = (time.perf_counter() - overlay开始秒) * 1000.0

        present开始秒 = time.perf_counter()
        self._renderer.present()
        present_ms = (time.perf_counter() - present开始秒) * 1000.0
        total_ms = (time.perf_counter() - 开始秒) * 1000.0
        self._最近呈现统计 = {
            "upload_ms": float(upload_ms),
            "overlay_ms": float(overlay_ms),
            "present_ms": float(present_ms),
            "total_ms": float(total_ms),
            "upload_rects": float(
                len(self._规范脏矩形列表(上传脏矩形列表))
                if not bool(强制全量上传)
                else 0
            ),
        }
        return self.取最近呈现统计()

    def 取GPU渲染器(self):
        return self._renderer

    def 最大化窗口(self) -> bool:
        try:
            if self._window is not None and (not bool(self._flags & pygame.FULLSCREEN)):
                self._window.maximize()
                return True
        except Exception:
            pass
        return False

    def 关闭(self):
        self._主纹理 = None
        self._renderer = None
        try:
            if self._window is not None:
                self._window.destroy()
        except Exception:
            pass
        self._window = None
        super().关闭()


def 读取后端偏好(默认值: str = "software") -> str:
    文本 = str(os.environ.get("E5CM_RENDER_BACKEND", 默认值) or 默认值).strip().lower()
    if 文本 in ("gpu", "gpu-sdl2", "sdl2"):
        return "gpu"
    if 文本 in ("auto",):
        return "auto"
    return "software"


def 创建显示后端(
    尺寸: Tuple[int, int],
    flags: int,
    标题: str,
    偏好: str = "software",
) -> 显示后端基类:
    模式 = 读取后端偏好(偏好)

    if 模式 == "gpu":
        try:
            return SDL2GPU显示后端(尺寸, flags, 标题, vsync=False)
        except Exception:
            return 软件显示后端(尺寸, flags, 标题)

    if 模式 == "auto":
        try:
            return SDL2GPU显示后端(尺寸, flags, 标题, vsync=False)
        except Exception:
            return 软件显示后端(尺寸, flags, 标题)

    return 软件显示后端(尺寸, flags, 标题)
