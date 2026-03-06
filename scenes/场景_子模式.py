import os
import math
import pygame

from core.工具 import cover缩放, 安全加载图片
from scenes.场景基类 import 场景基类, 场景切换请求
from ui.按钮 import 图片按钮
from ui.top栏 import 生成top栏
from ui.场景过渡 import 公用放大过渡器
from ui.按钮特效 import 公用按钮音效


class 场景_子模式(场景基类):
    名称 = "子模式"
    _设计宽 = 2048
    _设计高 = 1152

    def __init__(self, 上下文: dict):
        super().__init__(上下文)

        资源 = self.上下文.get("资源", {})
        self._按钮音效 = 公用按钮音效(资源.get("按钮音效", ""))

        self._背景视频 = self.上下文.get("背景视频")
        self.子模式按钮列表: list[tuple[图片按钮, str, str, str]] = []

        self._进入开始毫秒: int = 0
        self._按钮目标矩形: dict[str, pygame.Rect] = {}
        self._按钮当前偏移y: dict[str, float] = {}
        self._按钮当前偏移x: dict[str, float] = {}

        self._当前选中模式名: str | None = None
        self._选中开始毫秒: int = 0
        self._确认次数: int = 0

        self._大图标表面: pygame.Surface | None = None
        self._大图标矩形: pygame.Rect | None = None
        self._大图标路径缓存: str | None = None

        self._top栏背景原图: pygame.Surface | None = None
        self._top标题原图: pygame.Surface | None = None
        self._top_rect = pygame.Rect(0, 0, 1, 1)
        self._top图: pygame.Surface | None = None
        self._top标题rect = pygame.Rect(0, 0, 1, 1)
        self._top标题图: pygame.Surface | None = None
        self._top缓存尺寸 = (0, 0)

        self._联网原图: pygame.Surface | None = None
        self._子模式背景图表面: pygame.Surface | None = None

        self._按钮缩放缓存: dict[tuple[str, int, int], pygame.Surface] = {}

        # =========================
        # ✅ 动画参数（你要调速度/推开力度就改这里）
        # =========================
        self._入场时长毫秒 = 1200  # ✅ 入场从下往上速度：越小越快（原来 2000）
        self._入场每个延迟毫秒 = 90  # ✅ 每个按钮的错峰：越小越同时（原来 110）

        self._推开时长毫秒 = 320  # ✅ 推开动画时长（原来 360）
        self._推开屏幕边距 = 24  # ✅ 推开不越界：两侧至少留 24px
        self._推开间距缩放 = 1.0  # ✅ 推开时按钮间距压缩比例（越小越紧凑，位移越小）

        # ✅ 大图渐隐放大参数
        self._大图动画时长毫秒 = 260
        self._大图上移半个按钮 = True

        # ✅ 第一次点击：要隐藏哪个按钮
        self._首次选中隐藏模式名: str | None = None

        self._全屏放大过渡 = 公用放大过渡器(总时长毫秒=320)
        self._待进入选歌模式名: str | None = None
        self._过渡起始图: pygame.Surface | None = (
            None  # 缓存最后一帧2段图（避免每帧重算）
        )

    # -------------------------
    # 工具：动画
    # -------------------------
    def _夹紧(self, x: float, a: float, b: float) -> float:
        return max(a, min(b, x))

    def _缓出(self, t: float) -> float:
        t = self._夹紧(t, 0.0, 1.0)
        return 1 - (1 - t) ** 3  # easeOutCubic

    def _弹跳回弹(self, t: float) -> float:
        t = self._夹紧(t, 0.0, 1.0)
        s = 1.70158
        t -= 1
        return t * t * ((s + 1) * t + s) + 1

    def _插值(self, a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    # -------------------------
    # 生命周期
    # -------------------------
    def 进入(self, 载荷=None):
        # 子模式依然用 UI 音乐（如果你想强制 back_music_ui，可在这里改）
        bgm = (
            self.上下文["资源"].get("音乐_UI")
            or self.上下文["资源"].get("back_music_ui")
            or self.上下文["资源"].get("投币_BGM")
        )
        if bgm:
            self.上下文["音乐"].播放循环(bgm)

        self._进入开始毫秒 = pygame.time.get_ticks()
        self._当前选中模式名 = None
        self._选中开始毫秒 = 0
        self._确认次数 = 0
        self._大图标表面 = None
        self._大图标矩形 = None
        self._大图标路径缓存 = None

        self._按钮缩放缓存.clear()
        self._全屏放大过渡 = 公用放大过渡器(总时长毫秒=320)
        self._待进入选歌模式名 = None
        self._过渡起始图 = None

        self._预加载固定UI()
        self.重算布局()

    def 退出(self):
        # ✅ 不关闭全局视频
        pass

    def _预加载固定UI(self):
        资源 = self.上下文.get("资源", {})
        根 = 资源.get("根", "")

        # ✅ top 栏（同大模式：背景固定，标题按场景替换）
        self._top栏背景原图 = 安全加载图片(
            os.path.join(根, "UI-img", "top栏", "top栏背景.png"), 透明=True
        )
        self._top标题原图 = 安全加载图片(
            os.path.join(根, "UI-img", "top栏", "玩法选择.png"), 透明=True
        )

        # ✅ 联网图标（底部 credit 用）
        self._联网原图 = 安全加载图片(资源.get("投币_联网图标", ""), 透明=True)

        # ✅ 静态背景兜底（万一背景视频没帧）
        背景路径 = ""
        try:
            背景路径 = self.上下文["资源"].get("背景_子模式", "")
        except Exception:
            背景路径 = ""
        self._子模式背景图表面 = (
            安全加载图片(背景路径, 透明=False) if 背景路径 else None
        )

        # 强制重算 top 栏缓存
        self._top缓存尺寸 = (0, 0)
        self._确保top栏缓存()

    def _确保top栏缓存(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()
        if self._top缓存尺寸 == (w, h):
            return
        self._top缓存尺寸 = (w, h)

        # ✅ 子模式：写回子模式自己的 top 缓存字段
        self._top_rect, self._top图, self._top标题rect, self._top标题图 = 生成top栏(
            屏幕=屏幕,
            top背景原图=self._top栏背景原图,
            标题原图=self._top标题原图,
            设计宽=self._设计宽,
            设计高=self._设计高,
            top设计高=150,
            top背景宽占比=1.0,
            top背景高占比=1.0,
            标题最大宽占比=0.5,
            标题最大高占比=0.6,
            标题整体缩放=1.0,
            标题上移比例=0.1,
        )

    # -------------------------
    # 模式与资源映射
    # -------------------------
    def _构建模式列表(self) -> list[tuple[str, str, str]]:
        状态 = self.上下文["状态"]
        大模式 = 状态.get("大模式", "")

        if 大模式 == "花式":
            return [
                (
                    "学习",
                    "UI-img/玩法选择界面/按钮/学习模式按钮.png",
                    "UI-img/玩法选择界面/学习模式.png",
                ),
                (
                    "表演",
                    "UI-img/玩法选择界面/按钮/表演模式按钮.png",
                    "UI-img/玩法选择界面/表演模式.png",
                ),
                (
                    "疯狂",
                    "UI-img/玩法选择界面/按钮/疯狂模式按钮.png",
                    "UI-img/玩法选择界面/疯狂模式.png",
                ),
                (
                    "club",
                    "UI-img/玩法选择界面/按钮/club模式按钮.png",
                    "UI-img/玩法选择界面/双踏板模式.png",
                ),
                (
                    "情侣",
                    "UI-img/玩法选择界面/按钮/情侣模式按钮.png",
                    "UI-img/玩法选择界面/情侣模式.png",
                ),
                (
                    "混音",
                    "UI-img/玩法选择界面/按钮/混音模式按钮.png",
                    "UI-img/玩法选择界面/混音模式.png",
                ),
            ]

        if 大模式 == "竞速":
            return [
                (
                    "疯狂",
                    "UI-img/玩法选择界面/按钮/疯狂模式按钮.png",
                    "UI-img/玩法选择界面/疯狂模式.png",
                ),
                (
                    "club",
                    "UI-img/玩法选择界面/按钮/club模式按钮.png",
                    "UI-img/玩法选择界面/双踏板模式.png",
                ),
                (
                    "情侣",
                    "UI-img/玩法选择界面/按钮/情侣模式按钮.png",
                    "UI-img/玩法选择界面/情侣模式.png",
                ),
                (
                    "混音",
                    "UI-img/玩法选择界面/按钮/混音模式按钮.png",
                    "UI-img/玩法选择界面/混音模式.png",
                ),
            ]

        return []

    def 子模式对应选歌BGM(self, 子模式名: str) -> str:
        资源 = self.上下文["资源"]
        if "表演" in 子模式名:
            return 资源["音乐_show"]
        if "疯狂" in 子模式名:
            return 资源["音乐_devil"]
        if "混音" in 子模式名:
            return 资源["音乐_remix"]
        if "club" in 子模式名.lower():
            return 资源["音乐_club"]
        return 资源["音乐_UI"]

    # -------------------------
    # 布局
    # -------------------------

    def 重算布局(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()

        self.子模式按钮列表.clear()
        self._按钮目标矩形.clear()
        self._按钮当前偏移y.clear()
        self._按钮当前偏移x.clear()
        self._按钮缩放缓存.clear()

        模式列表 = self._构建模式列表()
        if not 模式列表:
            return

        数量 = len(模式列表)

        if 数量 == 1:
            # 单按钮场景放大一档，但仍按窗口尺寸等比缩放
            按钮边 = int(min(w, h) * 0.28)
            按钮边 = max(150, min(360, 按钮边))
        else:
            # 多按钮整体再放大一档（你给的图2尺寸）
            按钮边 = int(min(w, h) * 0.22)
            按钮边 = max(120, min(280, 按钮边))

        间距x = int(w * 0.025)
        间距x = max(6, min(36, 间距x))

        总宽 = 数量 * 按钮边 + (数量 - 1) * 间距x
        起始x = (w - 总宽) // 2

        # ✅ 垂直居中：最终落点在屏幕中线
        # 再考虑 top 栏高度（你 top设计高=150，留一点视觉空间）
        top占用 = 150
        目标y = (h // 2) - (按钮边 // 2) + int(top占用 * 0.20)
        目标y = max(int(top占用 * 0.90), min(目标y, h - 按钮边 - 24))

        for i, (模式名, 小按钮图, 大图标图) in enumerate(模式列表):
            按钮 = 图片按钮(模式名, 小按钮图)
            按钮.重新加载图片()

            目标矩形 = pygame.Rect(起始x + i * (按钮边 + 间距x), 目标y, 按钮边, 按钮边)
            按钮.设置矩形(目标矩形)

            self.子模式按钮列表.append((按钮, 模式名, 小按钮图, 大图标图))
            self._按钮目标矩形[模式名] = 目标矩形

            # ✅ 入场起始偏移：从屏幕下方上来（这里越大“起点越低”）
            self._按钮当前偏移y[模式名] = float(h - 目标y + 按钮边 + 80)
            self._按钮当前偏移x[模式名] = 0.0

        self._更新大图标矩形()
        self._top缓存尺寸 = (0, 0)
        self._确保top栏缓存()

    def _更新大图标矩形(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()
        self._大图标矩形 = pygame.Rect(
            int(w * 0.18), int(h * 0.34), int(w * 0.26), int(h * 0.26)
        )

    # -------------------------
    # 绘制：背景 / top / 底部
    # -------------------------
    def _画背景(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()

        屏幕.fill((0, 0, 0))

        # ✅ 公共连续视频
        帧 = self._背景视频.读取帧() if self._背景视频 else None
        if 帧 is not None:
            屏幕.blit(cover缩放(帧, w, h), (0, 0))
        elif self._子模式背景图表面:
            # 兜底
            屏幕.blit(cover缩放(self._子模式背景图表面, w, h), (0, 0))
        else:
            屏幕.fill((10, 12, 18))

        # ✅ 满屏黑色半透明遮罩：压暗背景（不要影响 UI，因为 UI 在后面画）
        try:
            背景遮罩透明度 = int(getattr(self, "_背景遮罩alpha", 140))
        except Exception:
            背景遮罩透明度 = 140
        背景遮罩透明度 = max(0, min(255, 背景遮罩透明度))

        if 背景遮罩透明度 > 0:
            需要重建 = False
            try:
                if getattr(self, "_背景遮罩缓存参数", None) != (w, h, 背景遮罩透明度):
                    需要重建 = True
            except Exception:
                需要重建 = True

            if 需要重建 or (getattr(self, "_背景遮罩面", None) is None):
                背景遮罩面 = pygame.Surface((w, h), pygame.SRCALPHA)
                背景遮罩面.fill((0, 0, 0, 背景遮罩透明度))
                self._背景遮罩面 = 背景遮罩面
                self._背景遮罩缓存参数 = (w, h, 背景遮罩透明度)

            try:
                屏幕.blit(self._背景遮罩面, (0, 0))
            except Exception:
                pass

    def _画顶栏(self):
        self._确保top栏缓存()
        屏幕 = self.上下文["屏幕"]

        if self._top图:
            屏幕.blit(self._top图, self._top_rect.topleft)
        else:
            pygame.draw.rect(屏幕, (8, 20, 40), self._top_rect)

        if self._top标题图:
            屏幕.blit(self._top标题图, self._top标题rect.topleft)

    def _画底部联网与credit(self):
        from core.工具 import 绘制底部联网与信用

        屏幕 = self.上下文["屏幕"]
        字体_credit = self.上下文["字体"]["投币_credit字"]
        绘制底部联网与信用(
            屏幕=屏幕,
            联网原图=self._联网原图,
            字体_credit=字体_credit,
            credit数值=str(int(self.上下文.get("状态", {}).get("投币数", 0) or 0)),
        )

    # -------------------------
    # 动画更新
    # -------------------------

    def _更新动画(self):
        现在 = pygame.time.get_ticks()

        入场时长 = int(self._入场时长毫秒)
        每个延迟 = int(self._入场每个延迟毫秒)

        # ---------- 入场：从下往上弹 ----------
        for idx, (_按钮, 模式名, _小图, _大图) in enumerate(self.子模式按钮列表):
            起 = self._进入开始毫秒 + idx * 每个延迟
            t = (现在 - 起) / max(1, 入场时长)
            if t <= 0:
                continue
            if t >= 1:
                self._按钮当前偏移y[模式名] = 0.0
            else:
                起始偏移 = float(self._按钮目标矩形[模式名].height + 220)
                y = self._插值(起始偏移, 0.0, self._弹跳回弹(t))
                self._按钮当前偏移y[模式名] = y

        # ---------- 波浪：入场结束后且未选中 ----------
        if 现在 - self._进入开始毫秒 > 入场时长 and (self._当前选中模式名 is None):
            波浪幅度 = 6.0
            波浪周期 = 1100.0
            for idx, (_按钮, 模式名, _小图, _大图) in enumerate(self.子模式按钮列表):
                相位 = idx * 0.55
                dy = math.sin((现在 / 波浪周期) * 2 * math.pi + 相位) * 波浪幅度
                self._按钮当前偏移y[模式名] = dy

        # ---------- 推开：选中后 ----------
        if self._当前选中模式名:
            from core.工具 import 计算推开偏移字典  # ✅ 公用推开算法

            推开时长 = int(self._推开时长毫秒)
            t = (现在 - self._选中开始毫秒) / max(1, 推开时长)
            t = self._夹紧(t, 0.0, 1.0)
            k = self._缓出(t)

            # 找选中索引
            选中索引 = 0
            for i, (_按钮, 模式名, _小图, _大图) in enumerate(self.子模式按钮列表):
                if 模式名 == self._当前选中模式名:
                    选中索引 = i
                    break

            # 组装目标rect列表（按当前按钮顺序）
            目标rect列表: list[pygame.Rect] = []
            模式名列表: list[str] = []
            for _按钮, 模式名, _小图, _大图 in self.子模式按钮列表:
                目标rect列表.append(self._按钮目标矩形[模式名])
                模式名列表.append(模式名)

            屏幕 = self.上下文["屏幕"]
            屏幕宽, _屏幕高 = 屏幕.get_size()

            dx列表 = 计算推开偏移字典(
                按钮目标矩形列表=目标rect列表,
                选中索引=选中索引,
                推开进度k=k,
                屏幕宽=屏幕宽,
                屏幕边距=int(self._推开屏幕边距),
                间距缩放=float(self._推开间距缩放),
            )

            for i, 模式名 in enumerate(模式名列表):
                if 模式名 == self._当前选中模式名:
                    self._按钮当前偏移x[模式名] = 0.0
                else:
                    self._按钮当前偏移x[模式名] = float(dx列表[i])

    # -------------------------
    # ✅ 去阴影按钮绘制：手动 blit 按钮图片
    # -------------------------

    def _画子模式按钮(self):
        屏幕 = self.上下文["屏幕"]

        for 按钮, 模式名, _小图, _大图 in self.子模式按钮列表:
            # ✅ 第一次点击后：隐藏被点的那个小按钮
            if self._首次选中隐藏模式名 and 模式名 == self._首次选中隐藏模式名:
                continue

            目标矩形 = self._按钮目标矩形[模式名]
            dx = self._按钮当前偏移x.get(模式名, 0.0)
            dy = self._按钮当前偏移y.get(模式名, 0.0)

            当前矩形 = pygame.Rect(
                int(目标矩形.x + dx),
                int(目标矩形.y + dy),
                目标矩形.width,
                目标矩形.height,
            )
            按钮.设置矩形(当前矩形)

            原图 = getattr(按钮, "图片", None)
            if 原图 is None:
                pygame.draw.rect(屏幕, (255, 255, 255), 当前矩形, width=2)
                continue

            key = (模式名, 当前矩形.w, 当前矩形.h)
            缓存图 = self._按钮缩放缓存.get(key)
            if 缓存图 is None:
                缓存图 = pygame.transform.smoothscale(
                    原图, (当前矩形.w, 当前矩形.h)
                ).convert_alpha()
                self._按钮缩放缓存[key] = 缓存图

            屏幕.blit(缓存图, 当前矩形.topleft)

    # -------------------------
    # 大图标绘制（本来就没阴影，保持）
    # -------------------------
    def _绘制大图标(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()
        现在 = pygame.time.get_ticks()

        大图路径 = None

        选中按钮边 = None
        目标rect = self._按钮目标矩形[self._当前选中模式名]
        dx = self._按钮当前偏移x.get(self._当前选中模式名, 0.0)
        dy = self._按钮当前偏移y.get(self._当前选中模式名, 0.0)
        当前rect = pygame.Rect(
            int(目标rect.x + dx),
            int(目标rect.y + dy),
            目标rect.w,
            目标rect.h,
        )
        for _按钮, 模式名, _小图, 大图 in self.子模式按钮列表:
            if 模式名 == self._当前选中模式名:
                大图路径 = 大图
                选中按钮边 = self._按钮目标矩形[模式名].w
                break
        if not 大图路径:
            return

        if (self._大图标表面 is None) or (self._大图标路径缓存 != 大图路径):
            try:
                self._大图标表面 = pygame.image.load(大图路径).convert_alpha()
                self._大图标路径缓存 = 大图路径
            except Exception:
                self._大图标表面 = None
                self._大图标路径缓存 = None

        if not self._大图标表面:
            return

        # ✅ 渐隐放大动画
        动画时长 = int(self._大图动画时长毫秒)
        t = (现在 - self._选中开始毫秒) / max(1, 动画时长)
        t = self._夹紧(t, 0.0, 1.0)

        # scale：0.92 -> 1.06 -> 1.00（更像“缩小再放大再归位”）
        if t < 0.6:
            k1 = t / 0.6
            scale = 0.92 + (1.06 - 0.92) * self._缓出(k1)
        else:
            k2 = (t - 0.6) / 0.4
            scale = 1.06 + (1.00 - 1.06) * self._缓出(k2)

        # alpha：0 -> 255
        alpha = int(255 * self._缓出(t))
        alpha = max(0, min(255, alpha))

        图 = self._大图标表面
        基准宽 = int(选中按钮边 * 1.2)  # ✅ 固定为原按钮缩放的 1.1 倍

        缩放比 = 基准宽 / max(1, 图.get_width())
        目标宽 = max(1, int(图.get_width() * 缩放比 * scale))
        目标高 = max(1, int(图.get_height() * 缩放比 * scale))

        图2 = pygame.transform.smoothscale(图, (目标宽, 目标高)).convert_alpha()
        图2.set_alpha(alpha)

        # # ✅ 位置：以你原来的“大图区域”中点为基准，上移半个按钮边长
        基准cx = 当前rect.centerx
        基准cy = 当前rect.centery

        上移 = int(当前rect.h * 0.5)  # ✅ 上移半个按钮高度（你要的“上方半个头”）
        x = 基准cx - 目标宽 // 2
        y = (基准cy - 目标高 // 2) - 上移

        self._大图标矩形 = pygame.Rect(x, y, 目标宽, 目标高)
        屏幕.blit(图2, (x, y))

    # -------------------------
    # 绘制主入口
    # -------------------------

    def 绘制(self):
        # ✅ 动画更新
        self._更新动画()

        # ✅ 先画背景
        self._画背景()

        # ✅ 中间层：按钮/大图标
        self._画子模式按钮()

        if self._当前选中模式名:
            self._绘制大图标()

        # ✅ 底部文字/联网
        self._画底部联网与credit()

        # ✅ 最后再画 top 栏：永远置顶，不可能被遮挡
        self._画顶栏()
        # ✅ 最顶层：放大过渡覆盖
        if self._全屏放大过渡.是否进行中():
            self._全屏放大过渡.更新并绘制(self.上下文["屏幕"])

    # -------------------------
    # 交互事件
    # -------------------------
    def 处理事件(self, 事件):
        if 事件.type == pygame.VIDEORESIZE:
            self.重算布局()
            return None

        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
            return 场景切换请求("大模式", 动作="REPLACE")

        # 点击大图标进入选歌
        if (
            self._当前选中模式名
            and 事件.type == pygame.MOUSEBUTTONDOWN
            and 事件.button == 1
        ):
            if self._大图标矩形 and self._大图标矩形.collidepoint(事件.pos):
                # ✅ 启动“放大到全屏过渡”，完成后再进入选歌（取消黑屏过渡）
                if (not self._全屏放大过渡.是否进行中()) and self._当前选中模式名:
                    self._待进入选歌模式名 = self._当前选中模式名

                    # 过渡起始图：用当前已加载的大图（原图），按当前rect缩放成一张surface作为起始图
                    if self._大图标表面:
                        self._过渡起始图 = pygame.transform.smoothscale(
                            self._大图标表面, (self._大图标矩形.w, self._大图标矩形.h)
                        ).convert_alpha()
                        self._全屏放大过渡.开始(self._过渡起始图, self._大图标矩形)

                return None

        # 小按钮点击（仍用 图片按钮 命中）
        for 按钮, 模式名, _小图, _大图 in self.子模式按钮列表:
            if 按钮.处理事件(事件):
                if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
                    self._按钮音效.播放()
                # 第一次点击：选中 + 隐藏该按钮 + 播放大图渐隐放大
                if self._当前选中模式名 != 模式名:
                    self._当前选中模式名 = 模式名
                    self._选中开始毫秒 = pygame.time.get_ticks()
                    self._确认次数 = 1

                    # ✅ 隐藏被点的按钮
                    self._首次选中隐藏模式名 = 模式名

                    # ✅ 重置大图缓存，让大图立刻切换成当前模式图
                    self._大图标表面 = None
                    self._大图标路径缓存 = None
                    return None

                # 第二次点击确认
                if self._当前选中模式名 == 模式名:
                    return self._进入选歌(模式名)

        return None

    def 更新(self):
        # ✅ 放大过渡完成后再进入下一步（避免黑屏）
        if self._待进入选歌模式名 and (not self._全屏放大过渡.是否进行中()):
            模式名 = self._待进入选歌模式名
            self._按钮音效.播放()
            self._待进入选歌模式名 = None
            self._过渡起始图 = None
            # 这里会阻塞（运行选歌），但动画已经播完了
            return self._进入选歌(模式名)
        return None

    def _进入选歌(self, 模式名: str):
        self.上下文["状态"]["子模式"] = 模式名

        # ✅ 子模式 -> 选歌：把“参数”写进状态，让选歌场景从内部读取
        try:
            类型名 = str(self.上下文["状态"].get("大模式", "") or "")
        except Exception:
            类型名 = ""

        try:
            选歌BGM = self.子模式对应选歌BGM(模式名)
        except Exception:
            选歌BGM = ""

        try:
            self.上下文["状态"]["选歌_类型"] = 类型名
            self.上下文["状态"]["选歌_模式"] = str(模式名 or "")
            self.上下文["状态"]["选歌_BGM"] = str(选歌BGM or "")
        except Exception:
            pass

        # ✅ 避免和选歌里的 pygame.mixer.music 撞车
        try:
            self.上下文["音乐"].停止()
        except Exception:
            pass

        # ✅ 交给场景管理器统一切换
        return {"切换到": "选歌", "禁用黑屏过渡": True}
