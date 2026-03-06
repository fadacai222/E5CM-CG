import os
import time
import pygame

try:
    import cv2

    _可用视频 = True
except Exception:
    cv2 = None
    _可用视频 = False

from ui.按钮特效 import 公用按钮点击特效, 公用按钮音效


class 视频循环播放器:
    def __init__(self, 视频路径: str):
        self.视频路径 = 视频路径
        self._cap = None
        self._fps = 30.0
        self._上一帧面 = None
        self._上次读帧时间 = 0.0
        self._背景视频 = self.上下文.get("背景视频")

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

    def 读取帧(self):
        if not _可用视频:
            return self._上一帧面
        if self._cap is None:
            self.打开()
            if self._cap is None:
                return self._上一帧面

        现在 = time.time()
        间隔 = 1.0 / max(1.0, self._fps)
        if self._上次读帧时间 and (现在 - self._上次读帧时间) < 间隔:
            return self._上一帧面
        self._上次读帧时间 = 现在

        ok, frame = self._cap.read()
        if not ok or frame is None:
            try:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._cap.read()
            except Exception:
                ok, frame = False, None

        if not ok or frame is None:
            return self._上一帧面

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        面 = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        self._上一帧面 = 面
        return 面


class 场景_玩家选择:
    名称 = "玩家选择"

    _设计宽 = 1920
    _设计高 = 1080
    # 左上右下
    _bbox_logo = (478, 247 - 100, 1443, 689 - 100)

    _bbox_联网 = (703, 991, 767, 1046)
    _bbox_credit = (788, 1001, 1132, 1046)
    _bbox_1p = (125, 718, 368, 874)
    _bbox_2p = (1551, 718, 1795, 874)

    def __init__(self, 上下文: dict):
        self.上下文 = 上下文
        资源 = 上下文["资源"]

        # ✅ 全局背景视频（main.py 注入，跨场景不断）
        self._背景视频 = 上下文.get("背景视频")

        # 原图
        self._遮罩原图 = self._安全加载图片(资源["投币_遮罩"], 透明=True)
        self._logo原图 = self._安全加载图片(资源["投币_logo"], 透明=True)
        self._联网原图 = self._安全加载图片(资源["投币_联网图标"], 透明=True)
        self._1p原图 = self._安全加载图片(资源["1P按钮"], 透明=True)
        self._2p原图 = self._安全加载图片(资源["2P按钮"], 透明=True)

        # 缩放缓存
        self._缓存尺寸 = (0, 0)
        self._遮罩图 = None
        self._logo图 = None
        self._联网图 = None

        self._1p图 = None
        self._2p图 = None
        self._1p图_hover = None
        self._2p图_hover = None

        # rect
        self._1p_rect = pygame.Rect(0, 0, 1, 1)
        self._2p_rect = pygame.Rect(0, 0, 1, 1)

        # hover 状态
        self._hover_1p = False
        self._hover_2p = False

        # 音效
        self.按钮音效 = 公用按钮音效(资源["按钮音效"])

        # ✅ 每按钮一份点击特效
        self._1p特效 = 公用按钮点击特效(
            总时长=0.3, 缩小阶段=0.1, 缩小到=0.90, 放大到=4.00, 透明起始=255, 透明结束=0
        )
        self._2p特效 = 公用按钮点击特效(
            总时长=0.3, 缩小阶段=0.1, 缩小到=0.90, 放大到=4.00, 透明起始=255, 透明结束=0
        )

        self._开始时间 = time.time()

    # -------------------------
    # 工具
    # -------------------------
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

    def _确保缓存(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()
        if (w, h) == self._缓存尺寸:
            return
        self._缓存尺寸 = (w, h)

        # 遮罩
        if self._遮罩原图:
            self._遮罩图 = self._cover缩放(self._遮罩原图, w, h)
        else:
            暗层 = pygame.Surface((w, h), pygame.SRCALPHA)
            暗层.fill((0, 0, 0, 128))
            self._遮罩图 = 暗层

        # logo
        logo_rect = self._映射到屏幕_rect(self._bbox_logo)
        self._logo图 = (
            pygame.transform.smoothscale(
                self._logo原图, (logo_rect.w, logo_rect.h)
            ).convert_alpha()
            if self._logo原图
            else None
        )

        # 联网
        网_rect = self._映射到屏幕_rect(self._bbox_联网)
        self._联网图 = (
            pygame.transform.smoothscale(
                self._联网原图, (网_rect.w, 网_rect.h)
            ).convert_alpha()
            if self._联网原图
            else None
        )

        # 1P/2P rect
        self._1p_rect = self._映射到屏幕_rect(self._bbox_1p)
        self._2p_rect = self._映射到屏幕_rect(self._bbox_2p)

        # 1P/2P 基础图
        self._1p图 = (
            pygame.transform.smoothscale(
                self._1p原图, (self._1p_rect.w, self._1p_rect.h)
            ).convert_alpha()
            if self._1p原图
            else None
        )
        self._2p图 = (
            pygame.transform.smoothscale(
                self._2p原图, (self._2p_rect.w, self._2p_rect.h)
            ).convert_alpha()
            if self._2p原图
            else None
        )

        # hover 图缓存
        hover_scale = 1.04
        if self._1p图:
            hw = max(1, int(self._1p_rect.w * hover_scale))
            hh = max(1, int(self._1p_rect.h * hover_scale))
            self._1p图_hover = pygame.transform.smoothscale(
                self._1p图, (hw, hh)
            ).convert_alpha()
        else:
            self._1p图_hover = None

        if self._2p图:
            hw = max(1, int(self._2p_rect.w * hover_scale))
            hh = max(1, int(self._2p_rect.h * hover_scale))
            self._2p图_hover = pygame.transform.smoothscale(
                self._2p图, (hw, hh)
            ).convert_alpha()
        else:
            self._2p图_hover = None

    # -------------------------
    # 生命周期
    # -------------------------

    def 进入(self):
        # ✅ 玩家选择：BGM 强制为 backsound/排行榜.mp3（按你要求）
        资源 = self.上下文["资源"]
        根目录 = str(资源.get("根", "") or os.getcwd())
        排行榜BGM路径 = os.path.join(根目录, "冷资源", "backsound", "排行榜.mp3")

        # 避免“刚从投币满额切过来时”重复重播一次
        已播 = False
        try:
            已播 = bool(self.上下文["状态"].get("bgm_排行榜_已播放", False))
        except Exception:
            已播 = False

        if (not 已播) and os.path.isfile(排行榜BGM路径):
            try:
                self.上下文["音乐"].播放循环(排行榜BGM路径)
                self.上下文["状态"]["bgm_排行榜_已播放"] = True
            except Exception:
                pass
        elif not os.path.isfile(排行榜BGM路径):
            # 兜底：文件缺失就退回投币BGM，避免完全没声
            try:
                self.上下文["音乐"].播放循环(self.上下文["资源"]["投币_BGM"])
            except Exception:
                pass

        self._开始时间 = time.time()
        self._缓存尺寸 = (0, 0)
        self._确保缓存()

    def 退出(self):
        # ✅ 不关闭全局视频
        pass

    # -------------------------
    # 绘制
    # -------------------------
    def 绘制(self):
        屏幕 = self.上下文["屏幕"]
        self._确保缓存()

        字体_credit = self.上下文["字体"]["投币_credit字"]
        w, h = 屏幕.get_size()

        # 背景（全局视频连续）
        屏幕.fill((0, 0, 0))
        帧 = self._背景视频.读取帧() if self._背景视频 else None
        if 帧 is not None:
            背景面 = self._cover缩放(帧, w, h)
            屏幕.blit(背景面, (0, 0))

        # 遮罩
        if self._遮罩图:
            屏幕.blit(self._遮罩图, (0, 0))

        # logo
        logo_rect = self._映射到屏幕_rect(self._bbox_logo)
        if self._logo图:
            屏幕.blit(self._logo图, logo_rect.topleft)

        from core.工具 import 绘制底部联网与信用

        绘制底部联网与信用(
            屏幕=屏幕,
            联网原图=self._联网原图,  # ✅ 用原图，公共函数内部会按 1P/2P bbox 缩放缓存
            字体_credit=字体_credit,
            credit数值=str(int(self.上下文.get("状态", {}).get("投币数", 0) or 0)),
        )

        # 1P/2P
        if self._1p图:
            if self._1p特效.是否动画中():
                self._1p特效.绘制按钮(屏幕, self._1p图, self._1p_rect)
            else:
                if self._hover_1p and self._1p图_hover:
                    r = self._1p图_hover.get_rect()
                    r.center = self._1p_rect.center
                    屏幕.blit(self._1p图_hover, r.topleft)
                else:
                    屏幕.blit(self._1p图, self._1p_rect.topleft)

        if self._2p图:
            if self._2p特效.是否动画中():
                self._2p特效.绘制按钮(屏幕, self._2p图, self._2p_rect)
            else:
                if self._hover_2p and self._2p图_hover:
                    r = self._2p图_hover.get_rect()
                    r.center = self._2p_rect.center
                    屏幕.blit(self._2p图_hover, r.topleft)
                else:
                    屏幕.blit(self._2p图, self._2p_rect.topleft)

    # -------------------------
    # 事件
    # -------------------------
    def 处理事件(self, 事件):
        if 事件.type == pygame.VIDEORESIZE:
            return None

        if 事件.type == pygame.MOUSEMOTION:
            self._hover_1p = self._1p_rect.collidepoint(事件.pos)
            self._hover_2p = self._2p_rect.collidepoint(事件.pos)
            return None

        if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            if self._1p_rect.collidepoint(事件.pos):
                self.按钮音效.播放()
                self._1p特效.触发()
                self.上下文["状态"]["玩家数"] = 1
                return {"切换到": "登陆磁卡"}

            if self._2p_rect.collidepoint(事件.pos):
                self.按钮音效.播放()
                self._2p特效.触发()
                self.上下文["状态"]["玩家数"] = 2
                return {"切换到": "登陆磁卡"}

        return None
