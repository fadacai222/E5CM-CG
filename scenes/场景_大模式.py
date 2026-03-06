import os
import time
import pygame

try:
    import cv2

    _可用视频 = True
except Exception:
    cv2 = None
    _可用视频 = False

from core.工具 import 绘制文本, cover缩放, 安全加载图片
from scenes.场景基类 import 场景基类, 场景切换请求
from ui.按钮 import 图片按钮
from ui.按钮特效 import 公用按钮音效
from ui.top栏 import 生成top栏
from core.工具 import 绘制渐隐放大图
from ui.场景过渡 import 公用放大过渡器


class 场景_大模式(场景基类):
    名称 = "大模式"

    _设计宽 = 2048
    _设计高 = 1152

    # ✅ 用一次性定时器来“动效播完再切场景”，不依赖 main.py 调用 update()
    _事件_延迟切场景 = pygame.USEREVENT + 23

    def __init__(self, 上下文: dict):
        super().__init__(上下文)
        资源 = self.上下文["资源"]
        根 = 资源.get("根", os.getcwd())

        # ✅ 全局背景视频（main.py 注入：上下文["背景视频"]）
        self._背景视频 = self.上下文.get("背景视频")

        self._联网原图 = 安全加载图片(资源.get("投币_联网图标", ""), 透明=True)
        self._按钮音效 = 公用按钮音效(资源.get("按钮音效", ""))

        # 大模式：不叠遮罩（你已经确认遮罩会压黑）
        self._遮罩图 = None

        # top栏
        self._top栏原图 = 安全加载图片(
            os.path.join(根, "UI-img", "top栏", "top栏背景.png"), 透明=True
        )
        self._top标题原图 = 安全加载图片(
            os.path.join(根, "UI-img", "top栏", "模式选择.png"), 透明=True
        )
        self._rect_top栏 = pygame.Rect(0, 0, 1, 1)
        self._top栏图 = None
        self._rect_top标题 = pygame.Rect(0, 0, 1, 1)
        self._top标题图 = None
        self._按钮当前偏移x: dict[str, float] = {}
        self._选中开始毫秒: int = 0
        self._推开时长毫秒 = 320
        self._推开屏幕边距 = 24
        self._推开间距缩放 = 1.0

        # 五个模式配置
        self._模式列表 = [
            {
                "键": "花式",
                "按钮图": os.path.join(
                    根, "UI-img", "大模式选择界面", "按钮", "花式模式按钮.png"
                ),
                "banner图": os.path.join(
                    根, "UI-img", "大模式选择界面", "花式模式.png"
                ),
                "文案": "花式模式：是一种花里胡哨的模式",
                "songs子目录": "花式",
            },
            {
                "键": "竞速",
                "按钮图": os.path.join(
                    根, "UI-img", "大模式选择界面", "按钮", "竞速模式按钮.png"
                ),
                "banner图": os.path.join(
                    根, "UI-img", "大模式选择界面", "竞速模式.png"
                ),
                "文案": "竞速模式：是一种速度很快的模式",
                "songs子目录": "竞速",
            },
            {
                "键": "派对",
                "按钮图": os.path.join(
                    根, "UI-img", "大模式选择界面", "按钮", "派对模式按钮.png"
                ),
                "banner图": os.path.join(
                    根, "UI-img", "大模式选择界面", "派对模式.png"
                ),
                "文案": "派对模式：不清楚这里原本是啥",
                "songs子目录": "派对",
            },
            {
                "键": "DIY",
                "按钮图": os.path.join(
                    根, "UI-img", "大模式选择界面", "按钮", "DIY乐谱模式按钮.png"
                ),
                "banner图": os.path.join(根, "UI-img", "大模式选择界面", "diy模式.png"),
                "文案": "diy乐谱模式：你能搞到.sm文件吗？",
                "songs子目录": "diy",
            },
            {
                "键": "WEF",
                "按钮图": os.path.join(
                    根, "UI-img", "大模式选择界面", "按钮", "wef模式按钮.png"
                ),
                "banner图": os.path.join(根, "UI-img", "大模式选择界面", "wef模式.png"),
                "文案": "wef联赛模式：不知道我还没玩过 所以这里没有内容",
                "songs子目录": "wef",
            },
        ]

        # 小按钮（仍用 图片按钮 做点击判定；绘制我们自己 blit，避免投影）
        self._按钮列表: list[图片按钮] = []
        self._按钮键列表: list[str] = []
        for cfg in self._模式列表:
            b = 图片按钮(cfg["键"], cfg["按钮图"])
            b.重新加载图片()
            self._按钮列表.append(b)
            self._按钮键列表.append(cfg["键"])

        # banner 资源
        self._banner原图字典: dict[str, pygame.Surface | None] = {}
        for cfg in self._模式列表:
            self._banner原图字典[cfg["键"]] = 安全加载图片(cfg["banner图"], 透明=True)

        self._当前选择键: str | None = None
        self._当前文案 = ""
        self._当前banner原图: pygame.Surface | None = None

        self._rect_banner槽位 = pygame.Rect(0, 0, 1, 1)
        self._rect_banner命中 = pygame.Rect(0, 0, 1, 1)

        # 缓存/布局
        self._缓存尺寸 = (0, 0)
        self._按钮基准rect: list[pygame.Rect] = [
            pygame.Rect(0, 0, 1, 1) for _ in self._按钮列表
        ]

        # 入场动画 + 慢跳
        self._入场开始 = 0.0
        self._入场时长 = 0.7
        self._入场下移像素 = 120
        self._跳动周期 = 2.0
        self._单个跳动时长 = 0.3
        self._跳动幅度 = 8

        # banner 点击允许进入（仅花式/竞速）
        self._可进入子模式集合 = {"花式", "竞速"}

        # toast
        self._提示文本 = ""
        self._提示截止时间 = 0.0

        # ✅ banner 点击动效
        from ui.按钮特效 import 公用按钮点击特效

        self._banner按钮特效 = 公用按钮点击特效(
            总时长=0.3, 缩小阶段=0.1, 缩小到=0.90, 放大到=4.00, 透明起始=255, 透明结束=0
        )
        self._banner特效开始时间 = 0.0

        # ✅ 延迟切场景目标
        self._延迟目标场景: str | None = None

    # ---------------- 生命周期 ----------------
    def 进入(self, 载荷=None):
        bgm = (
            self.上下文["资源"].get("back_music_ui")
            or self.上下文["资源"].get("音乐_UI")
            or self.上下文["资源"].get("投币_BGM")
        )
        if bgm:
            self.上下文["音乐"].播放循环(bgm)

        self._入场开始 = time.time()
        self._当前选择键 = None
        self._当前文案 = ""
        self._当前banner原图 = None
        self._提示文本 = ""
        self._提示截止时间 = 0.0
        self._延迟目标场景 = None
        self._按钮当前偏移x = {cfg["键"]: 0.0 for cfg in self._模式列表}
        self._选中开始毫秒 = 0

        # ✅ banner 当前帧缓存：给“点击后放大过渡”用
        self._banner当前图: pygame.Surface | None = None
        self._banner当前rect: pygame.Rect | None = None

        # ✅ 公用放大过渡器（按钮点击特效同款）
        self._全屏放大过渡 = 公用放大过渡器(总时长毫秒=400)

        # ✅ 防止重复触发
        self._正在放大切场景 = False

        pygame.time.set_timer(self._事件_延迟切场景, 0)

        self._缓存尺寸 = (0, 0)
        self.重算布局()

    def 退出(self):
        # ✅ 不关闭全局视频
        pygame.time.set_timer(self._事件_延迟切场景, 0)

    # ---------------- 工具 ----------------
    def _更新推开动画(self):
        if not self._当前选择键:
            return

        from core.工具 import 计算推开偏移字典

        现在 = pygame.time.get_ticks()
        t = (现在 - int(self._选中开始毫秒)) / max(1, int(self._推开时长毫秒))
        t = max(0.0, min(1.0, float(t)))
        k = 1.0 - (1.0 - t) ** 3  # easeOutCubic

        目标rect列表 = [self._按钮基准rect[i] for i in range(len(self._按钮列表))]
        键列表 = self._按钮键列表[:]
        选中索引 = (
            max(0, 键列表.index(self._当前选择键)) if self._当前选择键 in 键列表 else 0
        )

        屏幕宽, _h = self.上下文["屏幕"].get_size()

        dx列表 = 计算推开偏移字典(
            按钮目标矩形列表=目标rect列表,
            选中索引=选中索引,
            推开进度k=k,
            屏幕宽=屏幕宽,
            屏幕边距=int(self._推开屏幕边距),
            间距缩放=float(self._推开间距缩放),
        )

        for i, 键 in enumerate(键列表):
            if 键 == self._当前选择键:
                self._按钮当前偏移x[键] = 0.0
            else:
                self._按钮当前偏移x[键] = float(dx列表[i])

    def _确保缓存(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()
        if (w, h) == self._缓存尺寸:
            return
        self._缓存尺寸 = (w, h)

        # ✅ top栏：大模式用 self._top栏原图 + self._top标题原图
        self._rect_top栏, self._top栏图, self._rect_top标题, self._top标题图 = (
            生成top栏(
                屏幕=屏幕,
                top背景原图=self._top栏原图,
                标题原图=self._top标题原图,
                设计宽=self._设计宽,
                设计高=self._设计高,
                top设计高=150,
                top背景宽占比=1.0,
                top背景高占比=1.0,
                标题最大宽占比=0.5,
                标题最大高占比=0.5,
                标题整体缩放=1.0,
                标题上移比例=0.1,
            )
        )

    # ---------------- 布局 ----------------
    def 重算布局(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()

        数量 = len(self._按钮列表)
        if 数量 <= 0:
            return

        按边 = int(min(w, h) * 0.22)
        按边 = max(170, min(240, 按边))
        按宽 = int(按边 * 1.05)
        按高 = int(按边 * 1.00)

        间距 = int(w * 0.015)
        间距 = max(14, min(28, 间距))
        总宽 = 数量 * 按宽 + (数量 - 1) * 间距
        起始x = (w - 总宽) // 2

        y = int(h * 0.62)
        y = min(y, h - 按高 - int(h * 0.14))

        for i, b in enumerate(self._按钮列表):
            r = pygame.Rect(起始x + i * (按宽 + 间距), y, 按宽, 按高)
            self._按钮基准rect[i] = r
            b.设置矩形(r)

        # banner 更大
        banner_w = int(w * 0.95)
        banner_w = max(860, min(banner_w, int(w * 1.5)))
        banner_h = int(h * 0.44)
        banner_h = max(320, min(banner_h, int(h * 0.62)))

        banner_x = (w - banner_w) // 2
        banner_y = self._按钮基准rect[0].top - banner_h - int(h * 0.04)
        banner_y = max(int(h * 0.12), banner_y)

        self._rect_banner槽位 = pygame.Rect(banner_x, banner_y, banner_w, banner_h)
        self._rect_banner命中 = self._rect_banner槽位.copy()

    # ---------------- 选择 ----------------
    def _设置选择(self, 键: str):
        self._当前选择键 = 键
        self._当前banner原图 = self._banner原图字典.get(键)
        self._banner特效开始时间 = time.time()

        for cfg in self._模式列表:
            if cfg["键"] == 键:
                self._当前文案 = cfg["文案"]
                self.上下文["状态"]["大模式"] = cfg["键"]
                self.上下文["状态"]["songs子文件夹"] = cfg["songs子目录"]
                break

    # ---------------- 绘制 ----------------
    def _画背景(self):
        屏幕 = self.上下文["屏幕"]
        w, h = 屏幕.get_size()

        屏幕.fill((0, 0, 0))

        # ✅ 全局连续视频
        帧 = self._背景视频.读取帧() if self._背景视频 else None
        if 帧 is not None:
            屏幕.blit(cover缩放(帧, w, h), (0, 0))
        else:
            # 兜底背景图
            背景图 = self.上下文.get("缓存", {}).get("背景图_模式")
            if 背景图:
                屏幕.blit(cover缩放(背景图, w, h), (0, 0))

        # =========================
        # ✅ 满屏黑色半透明遮罩：只压暗背景，不影响后续 UI
        # =========================
        try:
            alpha = int(getattr(self, "_背景压暗_alpha", 120))
        except Exception:
            alpha = 120
        alpha = max(0, min(255, alpha))

        if alpha > 0:
            # 缓存遮罩面，避免每帧创建大 Surface
            需要重建 = False
            try:
                if getattr(self, "_背景压暗遮罩尺寸", None) != (w, h):
                    需要重建 = True
                if int(getattr(self, "_背景压暗遮罩alpha", -1)) != int(alpha):
                    需要重建 = True
            except Exception:
                需要重建 = True

            if 需要重建 or (getattr(self, "_背景压暗遮罩面", None) is None):
                遮罩面 = pygame.Surface((w, h), pygame.SRCALPHA)
                遮罩面.fill((0, 0, 0, alpha))
                self._背景压暗遮罩面 = 遮罩面
                self._背景压暗遮罩尺寸 = (w, h)
                self._背景压暗遮罩alpha = int(alpha)

            try:
                屏幕.blit(self._背景压暗遮罩面, (0, 0))
            except Exception:
                pass

        self._确保缓存()

    def _画底部credit(self):
        from core.工具 import 绘制底部联网与信用

        屏幕 = self.上下文["屏幕"]
        字体_credit = self.上下文["字体"]["投币_credit字"]
        绘制底部联网与信用(
            屏幕=屏幕,
            联网原图=self._联网原图,
            字体_credit=字体_credit,
            credit数值=str(int(self.上下文.get("状态", {}).get("投币数", 0) or 0)),
        )

    def _获取入场偏移(self) -> int:
        t = time.time() - self._入场开始
        if t <= 0:
            return self._入场下移像素
        if t >= self._入场时长:
            return 0
        k = 1.0 - (t / self._入场时长)
        return int(self._入场下移像素 * k)

    def _获取跳动偏移(self, 索引: int) -> int:
        if (time.time() - self._入场开始) < self._入场时长:
            return 0

        数量 = len(self._按钮列表)
        if 数量 <= 0:
            return 0

        t = time.time()
        周期 = self._跳动周期
        单 = self._单个跳动时长

        总窗 = 数量 * 单
        if 总窗 >= 周期:
            周期 = 总窗 + 0.2

        tt = t % 周期
        起 = 索引 * 单
        末 = 起 + 单
        if not (起 <= tt < 末):
            return 0

        p = (tt - 起) / max(0.0001, 单)
        a = (p / 0.5) if p < 0.5 else ((1.0 - p) / 0.5)
        return -int(self._跳动幅度 * a)

    def _画按钮(self):
        屏幕 = self.上下文["屏幕"]
        入场偏移 = 0
        t = (time.time() - self._入场开始) / max(0.0001, float(self._入场时长))
        t = max(0.0, min(1.0, t))
        # scale 0.92->1.00, alpha 0->255
        scale = 0.92 + (1.00 - 0.92) * (1.0 - (1.0 - t) ** 3)
        alpha = int(255 * (1.0 - (1.0 - t) ** 3))
        alpha = max(0, min(255, alpha))

        for i, b in enumerate(self._按钮列表):
            键 = self._按钮键列表[i]
            if self._当前选择键 == 键:
                continue

            基 = self._按钮基准rect[i]
            跳 = self._获取跳动偏移(i)
            dx = float(self._按钮当前偏移x.get(键, 0.0))
            r = pygame.Rect(int(基.x + dx), 基.y + 入场偏移 + 跳, 基.w, 基.h)
            b.设置矩形(r)

            if getattr(b, "图片", None) is not None:
                nw = max(1, int(r.w * scale))
                nh = max(1, int(r.h * scale))
                图 = pygame.transform.smoothscale(b.图片, (nw, nh)).convert_alpha()
                图.set_alpha(alpha)
                图r = 图.get_rect()
                图r.center = r.center
                屏幕.blit(图, 图r.topleft)
            else:
                pygame.draw.rect(屏幕, (255, 255, 255), r, width=2)

        for i, b in enumerate(self._按钮列表):
            b.设置矩形(self._按钮基准rect[i])

    def _画banner与文案(self):
        屏幕 = self.上下文["屏幕"]
        屏宽, 屏高 = 屏幕.get_size()

        # ✅ 场景1/场景2 统一字号：都用同一个字体对象
        字体_文案 = self.上下文["字体"]["小字"]

        # ✅ 统一文案Y计算：永远按“banner槽位 + 按钮顶”这套（场景1/2一致）
        槽位矩形 = getattr(self, "_rect_banner槽位", None)
        if not isinstance(槽位矩形, pygame.Rect):
            槽位矩形 = pygame.Rect(0, int(屏高 * 0.18), 屏宽, int(屏高 * 0.35))

        try:
            按钮顶边 = int(self._按钮基准rect[0].top)
        except Exception:
            按钮顶边 = int(屏高 * 0.62)

        文案y = 槽位矩形.bottom + int((按钮顶边 - 槽位矩形.bottom) * 0.40)
        文案y = max(槽位矩形.bottom + 6, min(文案y, 按钮顶边 - 12))

        # ✅ 整体往上挪几个像素（你说偏下）：可调参数，默认 10
        try:
            文案整体上移像素 = int(getattr(self, "_文案整体上移像素", 10))
        except Exception:
            文案整体上移像素 = 10
        文案y = int(文案y - 文案整体上移像素)
        文案y = max(槽位矩形.bottom + 6, min(文案y, 按钮顶边 - 12))

        # ✅ 文案遮罩（全屏宽黑色半透明）：场景1/2都要
        try:
            文案遮罩透明度 = int(getattr(self, "_文案遮罩alpha", 150))
        except Exception:
            文案遮罩透明度 = 150
        文案遮罩透明度 = max(0, min(255, 文案遮罩透明度))

        try:
            文案字高 = int(字体_文案.get_height())
        except Exception:
            文案字高 = 24

        文案上下内边距 = max(10, int(文案字高 * 0.60))
        文案遮罩条高 = max(32, 文案字高 + 文案上下内边距 * 2)
        文案遮罩条y = int(文案y - 文案遮罩条高 // 2)

        # ✅ 缓存遮罩条，避免每帧创建大Surface
        需要重建遮罩 = False
        try:
            if getattr(self, "_文案遮罩缓存参数", None) != (
                屏宽,
                文案遮罩条高,
                文案遮罩透明度,
            ):
                需要重建遮罩 = True
        except Exception:
            需要重建遮罩 = True

        if 需要重建遮罩 or (getattr(self, "_文案遮罩条面", None) is None):
            文案遮罩条面 = pygame.Surface((屏宽, 文案遮罩条高), pygame.SRCALPHA)
            文案遮罩条面.fill((0, 0, 0, 文案遮罩透明度))
            self._文案遮罩条面 = 文案遮罩条面
            self._文案遮罩缓存参数 = (屏宽, 文案遮罩条高, 文案遮罩透明度)

        # =========================
        # 场景1：未选中任何模式
        # =========================
        if not self._当前选择键:
            # 没选中时清理缓存，避免误用旧图
            self._banner当前图 = None
            self._banner当前rect = None

            默认文案 = "请点击选择您喜欢的游戏模式"

            # ✅ 先画遮罩，再画字（白色）
            if 文案遮罩透明度 > 0:
                try:
                    屏幕.blit(self._文案遮罩条面, (0, 文案遮罩条y))
                except Exception:
                    pass

            绘制文本(
                屏幕,
                默认文案,
                字体_文案,
                (255, 255, 255),
                (屏宽 // 2, 文案y),
                "center",
            )
            return

        # =========================
        # 场景2：已选中模式（banner + 文案）
        # =========================
        实际矩形 = 槽位矩形.copy()
        可画图 = None

        if self._当前banner原图:
            槽宽, 槽高 = 槽位矩形.size
            原宽, 原高 = self._当前banner原图.get_size()
            缩放比例 = min(槽宽 / max(1, 原宽), 槽高 / max(1, 原高))
            新宽 = max(1, int(原宽 * 缩放比例))
            新高 = max(1, int(原高 * 缩放比例))
            可画图 = pygame.transform.smoothscale(
                self._当前banner原图, (新宽, 新高)
            ).convert_alpha()
            实际矩形 = 可画图.get_rect()
            实际矩形.center = 槽位矩形.center
            self._rect_banner命中 = 实际矩形
        else:
            self._rect_banner命中 = 槽位矩形.copy()

        # ✅ 缓存：用于点击后“公用放大过渡器”起始图
        self._banner当前图 = 可画图
        self._banner当前rect = 实际矩形.copy()

        # ✅ 你现在的“展示动效”（保留不动）
        if 可画图 is not None:
            动效进度 = (time.time() - float(self._banner特效开始时间)) / 0.26
            动效进度 = max(0.0, min(1.0, 动效进度))

            基准宽 = int(实际矩形.w)
            动效后矩形 = 绘制渐隐放大图(
                屏幕=屏幕,
                原图=可画图,
                基准rect=实际矩形,
                进度t=动效进度,
                基准宽=基准宽,
                上移像素=0,
            )
            self._rect_banner命中 = 动效后矩形
            self._banner当前rect = 动效后矩形.copy()

        # ✅ 场景2：文案配置不变，但字号与场景1一致（同一字体对象）
        if self._当前文案:
            if 文案遮罩透明度 > 0:
                try:
                    屏幕.blit(self._文案遮罩条面, (0, 文案遮罩条y))
                except Exception:
                    pass

            绘制文本(
                屏幕,
                self._当前文案,
                字体_文案,
                (251, 200, 106),
                (屏宽 // 2, 文案y),
                "center",
            )

    def 绘制(self):
        屏幕 = self.上下文["屏幕"]
        小字 = self.上下文["字体"]["小字"]

        self._画背景()

        if self._top栏图:
            屏幕.blit(self._top栏图, self._rect_top栏.topleft)
        if self._top标题图:
            屏幕.blit(self._top标题图, self._rect_top标题.topleft)

        w, h = 屏幕.get_size()
        绘制文本(屏幕, "ESC 返回", 小字, (230, 245, 255), (w - 18, 14), "topright")

        self._画banner与文案()
        self._更新推开动画()
        self._画按钮()
        self._画底部credit()

        if self._提示文本 and time.time() < self._提示截止时间:
            绘制文本(
                屏幕,
                self._提示文本,
                小字,
                (219, 206, 155),
                (w // 2, int(h * 0.15)),
                "center",
            )

        # ✅ 放到最后：全屏放大过渡盖住一切
        if getattr(self, "_全屏放大过渡", None) is not None:
            if self._全屏放大过渡.是否进行中():
                self._全屏放大过渡.更新并绘制(屏幕)

    # ---------------- 事件 ----------------

    def 处理事件(self, 事件):
        if 事件.type == pygame.VIDEORESIZE:
            self.重算布局()
            return None

        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
            return 场景切换请求("玩家选择", 动作="REPLACE")

        # ✅ 延迟切场景事件（用来在“放大过渡结束”时切场景）
        if 事件.type == self._事件_延迟切场景:
            pygame.time.set_timer(self._事件_延迟切场景, 0)
            self._正在放大切场景 = False
            if self._延迟目标场景:
                目标 = self._延迟目标场景
                self._延迟目标场景 = None
                return {"切换到": 目标, "禁用黑屏过渡": True}
            return None

        # ✅ 过渡进行中：屏蔽交互（避免重复点击/状态错乱）
        if getattr(self, "_全屏放大过渡", None) is not None:
            if self._全屏放大过渡.是否进行中():
                return None

        # ✅ 点击 banner：允许进子模式时，启动“公用放大过渡器”
        if self._当前选择键 and 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            if self._rect_banner命中.collidepoint(事件.pos):
                self._按钮音效.播放()

                if self._当前选择键 in self._可进入子模式集合:
                    # 防止重复触发
                    if getattr(self, "_正在放大切场景", False):
                        return None
                    self._正在放大切场景 = True

                    # ✅ 起始图/rect：用 _画banner与文案 缓存的“当前实际绘制版本”
                    起始图 = getattr(self, "_banner当前图", None)
                    起始rect = getattr(self, "_banner当前rect", None)

                    # 兜底：如果缓存缺失，就用命中rect + 当前banner原图临时缩放一张
                    if 起始rect is None:
                        起始rect = self._rect_banner命中.copy()

                    if 起始图 is None and self._当前banner原图 is not None:
                        起始图 = pygame.transform.smoothscale(
                            self._当前banner原图,
                            (max(1, 起始rect.w), max(1, 起始rect.h)),
                        ).convert_alpha()

                    if (
                        起始图 is not None
                        and getattr(self, "_全屏放大过渡", None) is not None
                    ):
                        self._全屏放大过渡.开始(起始图, 起始rect)

                        self._延迟目标场景 = "子模式"
                        pygame.time.set_timer(
                            self._事件_延迟切场景,
                            int(getattr(self._全屏放大过渡, "总时长毫秒", 520)),
                            loops=1,
                        )
                    else:
                        # 兜底：真没图就退回原来的 timer 切场景
                        self._延迟目标场景 = "子模式"
                        pygame.time.set_timer(self._事件_延迟切场景, 300, loops=1)

                else:
                    self._提示文本 = "我还没写，所以点不动"
                    self._提示截止时间 = time.time() + 1.5
                return None

        # 小按钮：点谁选谁
        for i, b in enumerate(self._按钮列表):
            键 = self._按钮键列表[i]
            if self._当前选择键 == 键:
                continue

            if b.处理事件(事件):
                self._按钮音效.播放()
                self._选中开始毫秒 = pygame.time.get_ticks()
                if 键 not in self._按钮当前偏移x:
                    self._按钮当前偏移x[键] = 0.0
                self._设置选择(键)
                return None

        return None
