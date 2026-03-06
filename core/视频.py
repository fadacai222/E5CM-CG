import os
import time

import pygame

try:
    import cv2

    _可用视频 = True
except Exception:
    cv2 = None
    _可用视频 = False


def 选择第一个视频(目录: str) -> str:
    try:
        if not 目录 or (not os.path.isdir(目录)):
            return ""
        目标路径 = os.path.join(目录, "001.背景视频.mp4")
        if os.path.isfile(目标路径):
            return 目标路径
        return ""
    except Exception:
        return ""


class 全局视频循环播放器:
    def __init__(self, 视频路径: str, 循环播放: bool = True):
        self.视频路径 = 视频路径
        self.循环播放 = bool(循环播放)
        self._cap = None
        self._fps = 30.0
        self._上一帧面: pygame.Surface | None = None
        self._上次读帧时间 = 0.0

    def 设置视频(self, 新路径: str, 是否重置进度: bool = True):
        新路径 = (新路径 or "").strip()
        if not 新路径:
            return
        新路径 = os.path.abspath(新路径)
        旧路径 = os.path.abspath(self.视频路径) if self.视频路径 else ""
        if 新路径 == 旧路径:
            # 同一路径：可选是否回到开头
            if 是否重置进度 and self._cap is not None:
                try:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                except Exception:
                    pass
            return

        self.视频路径 = 新路径
        self.打开(是否重置进度=True)

    def 打开(self, 是否重置进度: bool = True):
        if not _可用视频 or not self.视频路径:
            return

        路径 = os.path.abspath(self.视频路径)

        # 已经打开且可用：不重复打开（关键：保持进度）
        if (
            self._cap is not None
            and hasattr(self._cap, "isOpened")
            and self._cap.isOpened()
        ):
            if 是否重置进度:
                try:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                except Exception:
                    pass
            return

        self.关闭()

        cap = None
        try:
            # 多策略打开：默认 / FFMPEG / DSHOW
            cap = cv2.VideoCapture(路径)
            if cap is None or (hasattr(cap, "isOpened") and (not cap.isOpened())):
                try:
                    if cap is not None:
                        cap.release()
                except Exception:
                    pass
                cap = cv2.VideoCapture(路径, cv2.CAP_FFMPEG)

            if cap is None or (hasattr(cap, "isOpened") and (not cap.isOpened())):
                try:
                    if cap is not None:
                        cap.release()
                except Exception:
                    pass
                cap = cv2.VideoCapture(路径, cv2.CAP_DSHOW)

            if cap is not None and hasattr(cap, "isOpened") and cap.isOpened():
                self._cap = cap
            else:
                try:
                    if cap is not None:
                        cap.release()
                except Exception:
                    pass
                self._cap = None
        except Exception:
            try:
                if cap is not None:
                    cap.release()
            except Exception:
                pass
            self._cap = None

        fps = 0.0
        if self._cap is not None:
            try:
                fps = float(self._cap.get(cv2.CAP_PROP_FPS))
            except Exception:
                fps = 0.0
        self._fps = fps if fps and fps > 1 else 30.0
        self._上次读帧时间 = 0.0

        if 是否重置进度 and self._cap is not None:
            try:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            except Exception:
                pass

    def 关闭(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
        self._cap = None

    def 读取帧(self) -> pygame.Surface | None:
        if not _可用视频:
            return self._上一帧面

        # 没打开成功：尝试打开；失败也返回上一帧
        if self._cap is None or (
            hasattr(self._cap, "isOpened") and (not self._cap.isOpened())
        ):
            self.打开(是否重置进度=False)
            if self._cap is None:
                return self._上一帧面

        # 帧率节流（避免CPU爆）
        现在 = time.time()
        间隔 = 1.0 / max(1.0, self._fps)
        if self._上次读帧时间 and (现在 - self._上次读帧时间) < 间隔:
            return self._上一帧面
        self._上次读帧时间 = 现在

        ok, frame = self._cap.read()
        if not ok or frame is None:
            if bool(self.循环播放):
                # 回到开头继续（循环）
                try:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = self._cap.read()
                except Exception:
                    ok, frame = False, None
            else:
                ok, frame = False, None

        if not ok or frame is None:
            return None

        try:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            面 = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            self._上一帧面 = 面
            return 面
        except Exception:
            return self._上一帧面


class 全局视频顺序循环播放器:
    """
    目录播放：
    - 按文件名排序顺序播放
    - 播放到最后一个后回到第一个
    """

    def __init__(self, 视频目录: str):
        self.视频目录 = str(视频目录 or "")
        self._文件列表: list[str] = []
        self._当前索引: int = 0
        self._当前播放器: 全局视频循环播放器 | None = None
        self._上一帧面: pygame.Surface | None = None

    @staticmethod
    def _收集视频文件(目录: str) -> list[str]:
        try:
            if not 目录 or (not os.path.isdir(目录)):
                return []
            候选后缀 = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v")
            文件列表: list[str] = []
            for 名称 in os.listdir(目录):
                路径 = os.path.join(目录, 名称)
                if (not os.path.isfile(路径)) or (not str(名称).lower().endswith(候选后缀)):
                    continue
                文件列表.append(路径)
            文件列表.sort(key=lambda p: os.path.basename(p).lower())
            return 文件列表
        except Exception:
            return []

    def 刷新列表(self):
        self._文件列表 = self._收集视频文件(self.视频目录)
        if self._当前索引 >= len(self._文件列表):
            self._当前索引 = 0

    def 打开(self, 是否重置进度: bool = True):
        self.刷新列表()
        if not self._文件列表:
            self.关闭()
            return
        if self._当前播放器 is None:
            self._当前索引 = 0 if 是否重置进度 else int(max(0, self._当前索引))
            当前路径 = self._文件列表[self._当前索引]
            self._当前播放器 = 全局视频循环播放器(当前路径, 循环播放=False)
            self._当前播放器.打开(是否重置进度=True)
            return
        if 是否重置进度:
            self._当前索引 = 0
            当前路径 = self._文件列表[self._当前索引]
            self._当前播放器.设置视频(当前路径, 是否重置进度=True)

    def 设置目录(self, 新目录: str, 是否重置进度: bool = True):
        新目录 = str(新目录 or "").strip()
        if not 新目录:
            return
        if os.path.abspath(新目录) == os.path.abspath(self.视频目录):
            if 是否重置进度:
                self.打开(是否重置进度=True)
            return
        self.视频目录 = 新目录
        self._当前索引 = 0
        self.关闭()
        self.打开(是否重置进度=True)

    def 关闭(self):
        if self._当前播放器 is not None:
            try:
                self._当前播放器.关闭()
            except Exception:
                pass
        self._当前播放器 = None

    def _切到下一个视频(self):
        if not self._文件列表:
            self._当前播放器 = None
            return
        self._当前索引 = (int(self._当前索引) + 1) % len(self._文件列表)
        当前路径 = self._文件列表[self._当前索引]
        if self._当前播放器 is None:
            self._当前播放器 = 全局视频循环播放器(当前路径, 循环播放=False)
            self._当前播放器.打开(是否重置进度=True)
        else:
            self._当前播放器.设置视频(当前路径, 是否重置进度=True)

    def 读取帧(self) -> pygame.Surface | None:
        if self._当前播放器 is None:
            self.打开(是否重置进度=False)
            if self._当前播放器 is None:
                return self._上一帧面

        # 最多尝试一轮：避免某个坏文件卡死
        尝试次数 = max(1, len(self._文件列表) if self._文件列表 else 1)
        for _ in range(尝试次数):
            if self._当前播放器 is None:
                break
            帧 = self._当前播放器.读取帧()
            if isinstance(帧, pygame.Surface):
                self._上一帧面 = 帧
                return 帧
            self._切到下一个视频()

        return self._上一帧面
