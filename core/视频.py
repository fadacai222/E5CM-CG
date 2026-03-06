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
    def __init__(
        self,
        视频路径: str,
        循环播放: bool = True,
        最大输出帧率: float | None = None,
    ):
        self.视频路径 = 视频路径
        self.循环播放 = bool(循环播放)
        self._cap = None
        self._fps = 30.0
        self._最大输出帧率 = (
            float(最大输出帧率) if 最大输出帧率 and 最大输出帧率 > 0 else None
        )
        self._上一帧数组 = None
        self._上一帧面: pygame.Surface | None = None
        self._上一帧面版本 = -1
        self._上次读帧时间 = 0.0
        self._帧版本 = 0
        self._覆盖缓存尺寸 = (0, 0)
        self._覆盖缓存版本 = -1
        self._覆盖缓存面: pygame.Surface | None = None

    def _重置覆盖缓存(self):
        self._覆盖缓存尺寸 = (0, 0)
        self._覆盖缓存版本 = -1
        self._覆盖缓存面 = None

    @staticmethod
    def _cover缩放到窗口(
        图片: pygame.Surface, 目标宽: int, 目标高: int
    ) -> pygame.Surface:
        ow, oh = 图片.get_size()
        if ow <= 0 or oh <= 0:
            return pygame.Surface((目标宽, 目标高)).convert()

        比例 = max(目标宽 / max(1, ow), 目标高 / max(1, oh))
        nw = max(1, int(round(ow * 比例)))
        nh = max(1, int(round(oh * 比例)))

        # 视频背景走普通 scale，遮罩下的观感差异很小，但 CPU 负担更低。
        if (nw, nh) == (ow, oh):
            缩放 = 图片
        else:
            缩放 = pygame.transform.scale(图片, (nw, nh)).convert()

        if (nw, nh) == (目标宽, 目标高):
            return 缩放

        x = max(0, (nw - 目标宽) // 2)
        y = max(0, (nh - 目标高) // 2)
        out = pygame.Surface((目标宽, 目标高)).convert()
        out.blit(缩放, (0, 0), area=pygame.Rect(x, y, 目标宽, 目标高))
        return out

    @staticmethod
    def _原始帧cover到窗口(frame, 目标宽: int, 目标高: int) -> pygame.Surface | None:
        try:
            帧高, 帧宽 = frame.shape[:2]
        except Exception:
            return None
        if 帧宽 <= 0 or 帧高 <= 0:
            return None

        比例 = max(目标宽 / max(1, 帧宽), 目标高 / max(1, 帧高))
        新宽 = max(1, int(round(float(帧宽) * 比例)))
        新高 = max(1, int(round(float(帧高) * 比例)))
        插值 = cv2.INTER_LINEAR if 比例 >= 1.0 else cv2.INTER_AREA

        try:
            if (新宽, 新高) == (帧宽, 帧高):
                缩放帧 = frame
            else:
                缩放帧 = cv2.resize(frame, (新宽, 新高), interpolation=插值)

            起始x = max(0, (新宽 - 目标宽) // 2)
            起始y = max(0, (新高 - 目标高) // 2)
            裁切帧 = 缩放帧[
                起始y : 起始y + int(目标高),
                起始x : 起始x + int(目标宽),
            ]
            if 裁切帧.shape[1] != int(目标宽) or 裁切帧.shape[0] != int(目标高):
                裁切帧 = cv2.resize(
                    裁切帧,
                    (int(目标宽), int(目标高)),
                    interpolation=cv2.INTER_LINEAR,
                )
            rgb = cv2.cvtColor(裁切帧, cv2.COLOR_BGR2RGB)
            return pygame.image.frombuffer(
                rgb.tobytes(), (int(目标宽), int(目标高)), "RGB"
            ).convert()
        except Exception:
            return None

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
        self._上一帧数组 = None
        self._上一帧面 = None
        self._上一帧面版本 = -1
        self._重置覆盖缓存()

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
        self._上一帧数组 = None
        self._上一帧面 = None
        self._上一帧面版本 = -1
        self._帧版本 = 0
        self._重置覆盖缓存()

    def _读取原始帧(self):
        if not _可用视频:
            return self._上一帧数组

        # 没打开成功：尝试打开；失败也返回上一帧
        if self._cap is None or (
            hasattr(self._cap, "isOpened") and (not self._cap.isOpened())
        ):
            self.打开(是否重置进度=False)
            if self._cap is None:
                return self._上一帧数组

        # 帧率节流。若限制输出帧率低于源帧率，需要跳帧而不是慢放。
        现在 = time.time()
        输出fps = float(self._fps)
        if self._最大输出帧率 is not None:
            输出fps = min(float(输出fps), float(self._最大输出帧率))
        间隔 = 1.0 / max(1.0, 输出fps)
        if self._上次读帧时间 and (现在 - self._上次读帧时间) < 间隔:
            return self._上一帧数组

        已过秒 = (
            max(间隔, float(现在 - self._上次读帧时间))
            if self._上次读帧时间
            else 间隔
        )
        目标推进帧数 = max(1, int(round(已过秒 * float(self._fps))))
        self._上次读帧时间 = 现在

        while 目标推进帧数 > 1:
            try:
                if not bool(self._cap.grab()):
                    break
            except Exception:
                break
            目标推进帧数 -= 1

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
            return self._上一帧数组

        self._上一帧数组 = frame
        self._帧版本 += 1
        return frame

    def 读取帧(self) -> pygame.Surface | None:
        frame = self._读取原始帧()
        if frame is None:
            return self._上一帧面

        if (
            self._上一帧面 is not None
            and int(self._上一帧面版本) == int(self._帧版本)
        ):
            return self._上一帧面

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            面 = pygame.image.frombuffer(
                rgb.tobytes(), (int(rgb.shape[1]), int(rgb.shape[0])), "RGB"
            ).convert()
            self._上一帧面 = 面
            self._上一帧面版本 = int(self._帧版本)
            return 面
        except Exception:
            return self._上一帧面

    def 读取覆盖帧(self, 目标宽: int, 目标高: int) -> pygame.Surface | None:
        目标宽 = max(1, int(目标宽))
        目标高 = max(1, int(目标高))

        frame = self._读取原始帧()
        if frame is None:
            if self._覆盖缓存尺寸 == (目标宽, 目标高):
                return self._覆盖缓存面
            return None

        if (
            self._覆盖缓存面 is not None
            and self._覆盖缓存尺寸 == (目标宽, 目标高)
            and self._覆盖缓存版本 == self._帧版本
        ):
            return self._覆盖缓存面

        覆盖面 = None
        if _可用视频 and cv2 is not None:
            覆盖面 = self._原始帧cover到窗口(frame, 目标宽, 目标高)
        if 覆盖面 is None:
            帧面 = self.读取帧()
            if 帧面 is None:
                return self._覆盖缓存面
            try:
                覆盖面 = self._cover缩放到窗口(帧面, 目标宽, 目标高)
            except Exception:
                覆盖面 = 帧面

        self._覆盖缓存尺寸 = (目标宽, 目标高)
        self._覆盖缓存版本 = int(self._帧版本)
        self._覆盖缓存面 = 覆盖面
        return 覆盖面


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

    def 读取覆盖帧(self, 目标宽: int, 目标高: int) -> pygame.Surface | None:
        if self._当前播放器 is None:
            self.打开(是否重置进度=False)
            if self._当前播放器 is None:
                return self._上一帧面

        尝试次数 = max(1, len(self._文件列表) if self._文件列表 else 1)
        for _ in range(尝试次数):
            if self._当前播放器 is None:
                break
            帧 = self._当前播放器.读取覆盖帧(目标宽, 目标高)
            if isinstance(帧, pygame.Surface):
                self._上一帧面 = 帧
                return 帧
            self._切到下一个视频()

        return self._上一帧面
