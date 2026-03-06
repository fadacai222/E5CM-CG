import os
import time
import pygame

try:
    import cv2

    _可用视频 = True
except Exception:
    cv2 = None
    _可用视频 = False


class 视频循环播放器:
    def __init__(self, 视频路径: str):
        self.视频路径 = 视频路径
        self._cap = None
        self._fps = 30.0
        self._上一帧面 = None
        self._上次读帧时间 = 0.0

    def 打开(self):
        if not _可用视频 or not self.视频路径:
            return
        self.关闭()
        self._cap = cv2.VideoCapture(self.视频路径)
        fps = 0.0
        try:
            fps = float(self._cap.get(cv2.CAP_PROP_FPS))
        except Exception:
            fps = 0.0
        self._fps = fps if fps and fps > 1 else 30.0
        self._上次读帧时间 = 0.0

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
        if self._cap is None:
            self.打开()
            if self._cap is None:
                return self._上一帧面

        # 帧率节流（太猛会CPU爆），但即便节流也返回上一帧，避免闪烁
        现在 = time.time()
        间隔 = 1.0 / max(1.0, self._fps)
        if self._上次读帧时间 and (现在 - self._上次读帧时间) < 间隔:
            return self._上一帧面
        self._上次读帧时间 = 现在

        ok, frame = self._cap.read()
        if not ok or frame is None:
            # 尝试回到开头
            try:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._cap.read()
            except Exception:
                ok, frame = False, None

        if not ok or frame is None:
            # 仍失败：直接返回上一帧（不黑）
            return self._上一帧面

        # BGR -> RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        面 = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        self._上一帧面 = 面
        return 面


class 场景_投币:
    名称 = "投币"

    _设计宽 = 1920
    _设计高 = 1080

    _bbox_logo = (478, 247, 1443, 689)
    _bbox_请投币 = (860, 893, 1060, 950)
    _bbox_联网 = (703, 991, 767, 1046)
    _bbox_credit = (788, 1001, 1132, 1046)
    _bbox_投币按钮 = (1653, 864, 1831, 1046)

    def __init__(self, 上下文: dict):
        self.上下文 = 上下文
        资源 = self.上下文["资源"]

        self.credit = 0
        self.credit_上限 = 3

        self._遮罩原图 = self._安全加载图片(资源["投币_遮罩"], 透明=True)
        self._logo原图 = self._安全加载图片(资源["投币_logo"], 透明=True)
        self._联网原图 = self._安全加载图片(资源["投币_联网图标"], 透明=True)
        self._按钮原图 = self._安全加载图片(资源["投币_按钮"], 透明=True)

        self._缓存尺寸 = (0, 0)
        self._遮罩图 = None
        self._logo图 = None
        self._联网图 = None
        self._按钮图 = None

        from ui.按钮特效 import 公用按钮点击特效, 公用按钮音效

        # 投币按钮点击音效（你原本就有）
        self.按钮音效 = 公用按钮音效(资源["投币音效"])
        self.按钮特效 = 公用按钮点击特效(
            总时长=0.2,
            缩小阶段=0.1,
            缩小到=0.90,
            放大到=4.00,
            透明起始=255,
            透明结束=0,
        )

        # ✅ 全局背景视频（main.py 放进上下文的那个）
        self._背景视频 = self.上下文.get("背景视频")

        # ✅ 业务：logo 默认不显示；第一次投币后立刻显示
        self._是否显示logo = False

        # ✅ 业务：投满三次只触发一次“满额音效 + BGM切换”
        self._已触发满额 = False

        # ✅ 资源：elogo.wav / 排行榜.mp3（按你要求固定路径 backsound/xxx）
        根目录 = str(资源.get("根", "") or os.getcwd())
        self._满额音效路径 = os.path.join(根目录, "冷资源", "backsound", "elogo.wav")
        self._排行榜BGM路径 = os.path.join(根目录, "冷资源", "backsound", "排行榜.mp3")

        self._满额音效 = None
        if os.path.isfile(self._满额音效路径):
            try:
                self._满额音效 = 公用按钮音效(self._满额音效路径)
            except Exception:
                self._满额音效 = None

        self._开始时间 = time.time()
        self._投币按钮_rect = pygame.Rect(0, 0, 1, 1)

    # ---------------- 生命周期 ----------------

    def 进入(self):
        # ✅ 投币界面：播放“现有投币BGM”（你资源里投币_BGM）
        # 如果你真想“完全不切歌，保持上一首”，那这里就别播；但启动时可能没音乐。
        self.上下文["音乐"].播放循环(self.上下文["资源"]["投币_BGM"])

        self.credit = 0
        self._开始时间 = time.time()
        self._缓存尺寸 = (0, 0)
        self._确保缓存()

        # ✅ 默认 logo 不显示，第一次投币后才显示
        self._是否显示logo = False
        self._已触发满额 = False

        # ✅ 用状态位避免“排行榜BGM”重复重播
        try:
            self.上下文["状态"]["bgm_排行榜_已播放"] = False
        except Exception:
            pass

    def 退出(self):
        # ✅ 不要关闭全局视频
        pass

    # ---------------- 绘制 ----------------

    def 绘制(self):
        from core.工具 import 绘制底部联网与信用  # ✅ 统一走公用函数

        屏幕 = self.上下文["屏幕"]
        self._确保缓存()

        字体_credit = self.上下文["字体"]["投币_credit字"]
        字体_请投币 = self.上下文["字体"]["投币_请投币字"]

        w, h = 屏幕.get_size()
        屏幕.fill((0, 0, 0))

        # ✅ 背景视频（连续播放）
        背景面 = self._背景视频.读取覆盖帧(w, h) if self._背景视频 else None
        if 背景面 is not None:
            屏幕.blit(背景面, (0, 0))

        if self._遮罩图:
            屏幕.blit(self._遮罩图, (0, 0))

        # ✅ 默认不显示logo；第一次投币后立刻显示
        if self._是否显示logo:
            logo_rect = self._映射到屏幕_rect(self._bbox_logo)
            if self._logo图:
                屏幕.blit(self._logo图, logo_rect.topleft)

        # 闪烁“请投币”
        现在 = time.time()
        if int(现在 - self._开始时间) % 2 == 0:
            文_rect = self._映射到屏幕_rect(self._bbox_请投币)
            self._绘制文本(
                屏幕, "请投币！", 字体_请投币, (255, 255, 255), 文_rect.center, "center"
            )

        # ✅ credit 显示（含联网图标）：统一走公用函数（全局缩放生效）
        绘制底部联网与信用(
            屏幕=屏幕,
            联网原图=self._联网原图,
            字体_credit=字体_credit,
            credit数值=str(int(self.上下文.get("状态", {}).get("投币数", 0) or 0)),
            文本=f"CREDIT：{int(self.上下文.get('状态', {}).get('投币数', 0) or 0)}/3",
            标准设计宽=self._设计宽,
            标准设计高=self._设计高,
            标准bbox_联网=self._bbox_联网,
            标准bbox_credit=self._bbox_credit,
        )
        try:
            状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
            if not isinstance(状态, dict):
                状态 = {}
            投币键显示 = str(状态.get("投币快捷键显示", "F1") or "F1").upper()
            提示 = f"{投币键显示}投币"
            提示面 = 字体_credit.render(提示, True, (255, 255, 255))
            提示rect = 提示面.get_rect()
            提示rect.topright = (w - 20, 18)
            屏幕.blit(提示面, 提示rect.topleft)

            提示字体2 = self.上下文.get("字体", {}).get("小字", 字体_credit)
            提示2 = "请窗口最大化以后再点击F11全屏"
            提示面2 = 提示字体2.render(提示2, True, (220, 220, 220))
            提示rect2 = 提示面2.get_rect()
            提示rect2.topright = (w - 20, int(提示rect.bottom + 6))
            屏幕.blit(提示面2, 提示rect2.topleft)
        except Exception:
            pass

    # ---------------- 事件 ----------------

    def 处理事件(self, 事件):
        if 事件.type == pygame.VIDEORESIZE:
            return None

        return None

    # ---------------- 工具 ----------------
    def _安全加载图片(self, 路径: str, 透明: bool):
        try:
            if not 路径 or (not os.path.isfile(路径)):
                return None
            图 = pygame.image.load(路径)
            return 图.convert_alpha() if 透明 else 图.convert()
        except Exception:
            return None

    def _映射到屏幕_rect(self, bbox):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()

        scale = min(w / self._设计宽, h / self._设计高)
        content_w = self._设计宽 * scale
        content_h = self._设计高 * scale
        ox = (w - content_w) / 2.0
        oy = (h - content_h) / 2.0

        l, t, r, b = bbox
        x = int(ox + l * scale)
        y = int(oy + t * scale)
        ww = int((r - l) * scale)
        hh = int((b - t) * scale)
        return pygame.Rect(x, y, max(1, ww), max(1, hh))

    def _cover缩放(
        self, 图片: pygame.Surface, 目标宽: int, 目标高: int
    ) -> pygame.Surface:
        ow, oh = 图片.get_size()
        if ow <= 0 or oh <= 0:
            return pygame.Surface((目标宽, 目标高))
        比例 = max(目标宽 / ow, 目标高 / oh)
        nw, nh = max(1, int(ow * 比例)), max(1, int(oh * 比例))
        缩放 = pygame.transform.smoothscale(图片, (nw, nh))
        x = (nw - 目标宽) // 2
        y = (nh - 目标高) // 2
        out = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
        out.blit(缩放, (0, 0), area=pygame.Rect(x, y, 目标宽, 目标高))
        return out

    def _绘制文本(self, 屏幕, 文本, 字体, 颜色, 位置, 对齐="center"):
        面 = 字体.render(文本, True, 颜色)
        r = 面.get_rect()
        setattr(r, 对齐, 位置)
        屏幕.blit(面, r)
        return r

    def _确保缓存(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()
        if (w, h) == self._缓存尺寸:
            return
        self._缓存尺寸 = (w, h)

        if self._遮罩原图:
            self._遮罩图 = self._cover缩放(self._遮罩原图, w, h)
        else:
            暗层 = pygame.Surface((w, h), pygame.SRCALPHA)
            暗层.fill((0, 0, 0, 128))
            self._遮罩图 = 暗层

        logo_rect = self._映射到屏幕_rect(self._bbox_logo)
        self._logo图 = (
            pygame.transform.smoothscale(self._logo原图, (logo_rect.w, logo_rect.h))
            if self._logo原图
            else None
        )

        # ✅ 注意：联网图标不在这里缩放了（交给 core.工具.绘制底部联网与信用 统一处理）
        self._联网图 = None

        btn_rect = self._映射到屏幕_rect(self._bbox_投币按钮)
        self._按钮图 = (
            pygame.transform.smoothscale(
                self._按钮原图, (btn_rect.w, btn_rect.h)
            ).convert_alpha()
            if self._按钮原图
            else None
        )
