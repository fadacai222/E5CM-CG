import os
import pygame


def 获取字体(
    字号: int, 是否粗体: bool = False, 字体文件路径: str | None = None, **额外参数
):
    """
    统一字体入口：
    - 默认使用：<项目根>/冷资源/字体/方正黑体简体.TTF
    - 若不存在：降级用 pygame 默认字体（避免崩）
    - 带缓存：避免每帧创建 Font 对象导致卡顿
    """
    import os
    import pygame

    try:
        字号 = int(字号)
    except Exception:
        字号 = 22
    字号 = max(8, min(200, 字号))
    是否粗体 = bool(是否粗体)

    # --- 函数级静态缓存（避免改模块全局） ---
    if not hasattr(获取字体, "_缓存"):
        获取字体._缓存 = {}
    if not hasattr(获取字体, "_已提示缺字体"):
        获取字体._已提示缺字体 = False

    # --- 计算默认字体路径 ---
    项目根 = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    默认字体 = os.path.join(项目根, "冷资源", "字体", "方正黑体简体.TTF")

    目标字体 = 字体文件路径 or 默认字体
    目标字体 = str(目标字体)

    键 = (目标字体, 字号, 是否粗体)
    已有 = 获取字体._缓存.get(键)
    if isinstance(已有, pygame.font.Font):
        return 已有

    # --- 创建 Font ---
    字体对象 = None
    if os.path.isfile(目标字体):
        try:
            字体对象 = pygame.font.Font(目标字体, 字号)
        except Exception:
            字体对象 = None
    else:
        if not 获取字体._已提示缺字体:
            获取字体._已提示缺字体 = True
            try:
                print(f"[字体] 未找到：{目标字体}，将降级为 pygame 默认字体")
            except Exception:
                pass

    if 字体对象 is None:
        # 降级：pygame 默认字体
        try:
            字体对象 = pygame.font.Font(None, 字号)
        except Exception:
            # 极端兜底
            pygame.font.init()
            字体对象 = pygame.font.Font(None, 字号)

    try:
        字体对象.set_bold(是否粗体)
    except Exception:
        pass

    获取字体._缓存[键] = 字体对象
    return 字体对象


def 绘制文本(屏幕, 文本, 字体, 颜色, 位置, 对齐="center"):
    面 = 字体.render(文本, True, 颜色)
    r = 面.get_rect()
    setattr(r, 对齐, 位置)
    屏幕.blit(面, r)
    return r


def cover缩放(图片: pygame.Surface, 目标宽: int, 目标高: int) -> pygame.Surface:
    ow, oh = 图片.get_size()
    if ow <= 0 or oh <= 0:
        return pygame.Surface((目标宽, 目标高))
    比例 = max(目标宽 / ow, 目标高 / oh)
    nw, nh = max(1, int(ow * 比例)), max(1, int(oh * 比例))
    缩放 = pygame.transform.smoothscale(图片, (nw, nh))
    x = (nw - 目标宽) // 2
    y = (nh - 目标高) // 2
    out = pygame.Surface((目标宽, 目标高))
    out.blit(缩放, (0, 0), area=pygame.Rect(x, y, 目标宽, 目标高))
    return out


def contain缩放(图片: pygame.Surface, 目标宽: int, 目标高: int) -> pygame.Surface:
    ow, oh = 图片.get_size()
    if ow <= 0 or oh <= 0:
        return pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
    比例 = min(目标宽 / ow, 目标高 / oh)
    nw, nh = max(1, int(ow * 比例)), max(1, int(oh * 比例))
    缩放 = pygame.transform.smoothscale(图片, (nw, nh))
    画布 = pygame.Surface((目标宽, 目标高), pygame.SRCALPHA)
    画布.fill((0, 0, 0, 0))
    x = (目标宽 - nw) // 2
    y = (目标高 - nh) // 2
    画布.blit(缩放, (x, y))
    return 画布


def 画圆角面(
    宽: int, 高: int, 颜色: tuple, 圆角: int, alpha: int = 255
) -> pygame.Surface:
    面 = pygame.Surface((宽, 高), pygame.SRCALPHA)
    c = (颜色[0], 颜色[1], 颜色[2], alpha)
    pygame.draw.rect(面, c, pygame.Rect(0, 0, 宽, 高), border_radius=圆角)
    return 面


def 安全加载图片(路径: str, 透明: bool):
    try:
        if not 路径 or (not os.path.isfile(路径)):
            return None
        图 = pygame.image.load(路径)
        return 图.convert_alpha() if 透明 else 图.convert()
    except Exception:
        return None


def 选择第一张存在的图片(候选列表: list[str]) -> str:
    for p in 候选列表:
        try:
            if p and os.path.isfile(p):
                return p
        except Exception:
            pass
    return ""


def 计算推开目标x列表(
    按钮目标矩形列表: list[pygame.Rect],
    选中索引: int,
    屏幕宽: int,
    屏幕边距: int,
    间距缩放: float,
) -> list[int]:
    """
    目标：推开时不让两侧按钮超过屏幕边距；同时允许“缩小按钮间距”避免推太远。
    返回：每个按钮“推开后”的目标 left(x) 列表（与传入顺序一一对应）。
    """
    n = len(按钮目标矩形列表)
    if n <= 0:
        return []

    # 原始宽度/间距（用相邻两个按钮 left 差估算）
    原间距 = 0
    if n >= 2:
        原间距 = 按钮目标矩形列表[1].x - 按钮目标矩形列表[0].x
    if 原间距 <= 0:
        原间距 = 按钮目标矩形列表[0].w + 16

    新间距 = max(int(原间距 * float(间距缩放)), int(按钮目标矩形列表[0].w * 0.35))

    # 以“选中按钮”为锚点，左右重新排布（间距更小）
    选中rect = 按钮目标矩形列表[选中索引]
    目标x = [r.x for r in 按钮目标矩形列表]
    目标x[选中索引] = 选中rect.x

    # 左侧从选中往左排
    for i in range(选中索引 - 1, -1, -1):
        目标x[i] = 目标x[i + 1] - 新间距

    # 右侧从选中往右排
    for i in range(选中索引 + 1, n):
        目标x[i] = 目标x[i - 1] + 新间距

    # ✅ 关键：状态2需要“选中按钮占位变大”的效果（类似 div 变大挤开旁边）
    # 这个额外挤开量就是你现在缺少的，所以 dx 一直是 0
    额外挤开 = int(按钮目标矩形列表[选中索引].w * 0.35)  # 0.45~0.70 都行，先用 0.55
    for i in range(0, n):
        if i < 选中索引:
            目标x[i] -= 额外挤开
        elif i > 选中索引:
            目标x[i] += 额外挤开

    # 现在可能整体越界：做整体平移纠正（保证最左>=边距，最右<=屏幕宽-边距）
    最左 = 目标x[0]
    最右 = 目标x[-1] + 按钮目标矩形列表[-1].w
    左越界 = 屏幕边距 - 最左
    右越界 = 最右 - (屏幕宽 - 屏幕边距)

    平移 = 0
    if 左越界 > 0 and 右越界 > 0:
        # 两边都越界：只能折中，尽量居中
        平移 = int((左越界 - 右越界) * 0.5)
    elif 左越界 > 0:
        平移 = int(左越界)
    elif 右越界 > 0:
        平移 = -int(右越界)

    if 平移 != 0:
        目标x = [x + 平移 for x in 目标x]

    # 最终再夹紧（保底）
    for i in range(n):
        目标x[i] = max(
            屏幕边距, min(目标x[i], 屏幕宽 - 屏幕边距 - 按钮目标矩形列表[i].w)
        )

    return 目标x


def 计算推开偏移字典(
    按钮目标矩形列表: list[pygame.Rect],
    选中索引: int,
    推开进度k: float,
    屏幕宽: int,
    屏幕边距: int = 24,
    间距缩放: float = 0.72,
) -> list[float]:
    """
    返回：每个按钮的 dx（float），dx = (推开后目标x - 原x) * k
    """
    k = max(0.0, min(1.0, float(推开进度k)))
    目标x列表 = 计算推开目标x列表(
        按钮目标矩形列表=按钮目标矩形列表,
        选中索引=选中索引,
        屏幕宽=屏幕宽,
        屏幕边距=屏幕边距,
        间距缩放=间距缩放,
    )
    dx列表: list[float] = []
    for i, r in enumerate(按钮目标矩形列表):
        dx列表.append((float(目标x列表[i]) - float(r.x)) * k)
    return dx列表


def 计算渐隐放大参数(进度t: float) -> tuple[float, int]:
    """
    进度t: 0~1
    返回: (scale, alpha)
    scale：0.92 -> 1.06 -> 1.00
    alpha：0 -> 255
    """
    t = max(0.0, min(1.0, float(进度t)))

    def _缓出(x: float) -> float:
        x = max(0.0, min(1.0, float(x)))
        return 1.0 - (1.0 - x) ** 3

    if t < 0.6:
        k1 = t / 0.6
        scale = 0.92 + (1.06 - 0.92) * _缓出(k1)
    else:
        k2 = (t - 0.6) / 0.4
        scale = 1.06 + (1.00 - 1.06) * _缓出(k2)

    alpha = int(255 * _缓出(t))
    alpha = max(0, min(255, alpha))
    return scale, alpha


def 绘制渐隐放大图(
    屏幕: pygame.Surface,
    原图: pygame.Surface,
    基准rect: pygame.Rect,
    进度t: float,
    基准宽: int,
    上移像素: int = 0,
) -> pygame.Rect:
    """
    把原图按“渐隐放大”绘到屏幕上：
    - 以 基准rect.center 为基准定位
    - 宽度以 基准宽 为“常态宽”
    - 上移像素：往上挪（你子模式要上移半个头就传 rect.h*0.5）

    返回：实际绘制rect（用于点击判定/后续过渡锚点）
    """
    scale, alpha = 计算渐隐放大参数(进度t)

    ow, oh = 原图.get_size()
    if ow <= 0 or oh <= 0:
        return pygame.Rect(0, 0, 1, 1)

    缩放比 = float(基准宽) / max(1.0, float(ow))
    目标宽 = max(1, int(ow * 缩放比 * scale))
    目标高 = max(1, int(oh * 缩放比 * scale))

    图2 = pygame.transform.smoothscale(原图, (目标宽, 目标高)).convert_alpha()
    图2.set_alpha(alpha)

    cx, cy = 基准rect.centerx, 基准rect.centery
    x = int(cx - 目标宽 / 2)
    y = int(cy - 目标高 / 2 - int(上移像素))

    实际 = pygame.Rect(x, y, 目标宽, 目标高)
    屏幕.blit(图2, 实际.topleft)
    return 实际


# ✅ 模块级缓存：避免每帧重复缩放联网图标
_底部联网图标缩放缓存: dict[tuple[int, int, int], pygame.Surface] = {}


def 映射bbox到屏幕矩形(
    屏幕: pygame.Surface,
    bbox: tuple[int, int, int, int],
    设计宽: int,
    设计高: int,
) -> pygame.Rect:
    """
    按 1P/2P 的映射方式（min 缩放 + 居中留边），把设计稿 bbox 映射到当前屏幕 rect。
    bbox: (l,t,r,b)
    """
    w, h = 屏幕.get_size()

    scale = min(w / max(1, 设计宽), h / max(1, 设计高))
    content_w = 设计宽 * scale
    content_h = 设计高 * scale
    ox = (w - content_w) / 2.0
    oy = (h - content_h) / 2.0

    l, t, r, b = bbox
    x = int(ox + l * scale)
    y = int(oy + t * scale)
    ww = int((r - l) * scale)
    hh = int((b - t) * scale)
    return pygame.Rect(x, y, max(1, ww), max(1, hh))


# ✅ 放在 core/工具.py 模块级（函数外）
底部联网与信用_整体缩放 = 0.82  # 0.7~1.0 之间自己调
_底部联网图标缩放缓存 = {}
_底部信用文本缓存 = {}


def 绘制底部联网与信用(
    屏幕: pygame.Surface,
    联网原图: pygame.Surface | None,
    字体_credit: pygame.font.Font,
    credit数值: str = "3/3",
    颜色: tuple[int, int, int] = (255, 255, 255),
    # ✅ 新增：整体缩放（None=用模块全局默认）
    整体缩放: float | None = None,
    # ✅ 新增：允许外部直接传完整文本（投币界面用它保持“CREDIT：”全角冒号）
    文本: str | None = None,
    # ✅ 以 1P/2P 为标准（不要改这俩默认值）
    标准设计宽: int = 1920,
    标准设计高: int = 1080,
    标准bbox_联网: tuple[int, int, int, int] = (703, 991, 767, 1046),
    标准bbox_credit: tuple[int, int, int, int] = (788, 1001, 1132, 1046),
) -> pygame.Rect:
    """
    以 1P/2P 的 bbox 为标准绘制：
    - 联网图标大小 = bbox_联网 映射后的 size（再乘整体缩放）
    - 整体（图标+文字）以 bbox_credit.center 为锚点水平居中
    - 默认文本：CREDIT:{credit数值}
    返回：最终文字 rect（便于调试）
    """
    w, h = 屏幕.get_size()

    # -------- 1) 取整体缩放（全局默认）--------
    if 整体缩放 is None:
        try:
            整体缩放 = float(globals().get("底部联网与信用_整体缩放", 1.0))
        except Exception:
            整体缩放 = 1.0
    try:
        整体缩放 = float(整体缩放)
    except Exception:
        整体缩放 = 1.0
    整体缩放 = 0.2 if 整体缩放 < 0.2 else (2.0 if 整体缩放 > 2.0 else 整体缩放)

    # -------- 2) 锚点 --------
    credit_rect = 映射bbox到屏幕矩形(屏幕, 标准bbox_credit, 标准设计宽, 标准设计高)
    锚点 = credit_rect.center

    # -------- 3) 文本（先 render，再整体缩放）--------
    credit文本值 = str(credit数值 or "").strip()
    if "/" not in credit文本值:
        try:
            credit文本值 = f"{max(0, int(float(credit文本值 or 0))):d}/3"
        except Exception:
            credit文本值 = f"{credit文本值}/3" if credit文本值 else "0/3"

    if 文本 is None:
        文本 = f"CREDIT：{credit文本值}"
    文本 = str(文本)

    # ✅ 文本缩放缓存：字体id + 文本 + 颜色 + scale
    try:
        scale_key = int(整体缩放 * 1000)
    except Exception:
        scale_key = 1000

    文本缓存键 = (
        id(字体_credit),
        文本,
        int(颜色[0]),
        int(颜色[1]),
        int(颜色[2]),
        int(scale_key),
    )

    文面 = _底部信用文本缓存.get(文本缓存键)
    if not isinstance(文面, pygame.Surface):
        文面_原 = 字体_credit.render(文本, True, 颜色)

        if abs(整体缩放 - 1.0) > 1e-3:
            目标文w = max(1, int(文面_原.get_width() * 整体缩放))
            目标文h = max(1, int(文面_原.get_height() * 整体缩放))
            try:
                文面 = pygame.transform.smoothscale(
                    文面_原, (目标文w, 目标文h)
                ).convert_alpha()
            except Exception:
                try:
                    文面 = pygame.transform.scale(
                        文面_原, (目标文w, 目标文h)
                    ).convert_alpha()
                except Exception:
                    文面 = 文面_原
        else:
            # 尽量保持原面（更清晰）
            try:
                文面 = 文面_原.convert_alpha()
            except Exception:
                文面 = 文面_原

        _底部信用文本缓存[文本缓存键] = 文面

    文r = 文面.get_rect()

    # -------- 4) 图标（按 bbox 映射，再整体缩放）--------
    网_rect = 映射bbox到屏幕矩形(屏幕, 标准bbox_联网, 标准设计宽, 标准设计高)
    间距 = max(2, int(min(w, h) * 0.006 * 整体缩放))

    图r = None
    网图 = None
    if 联网原图 is not None:
        目标w = max(1, int(网_rect.w * 整体缩放))
        目标h = max(1, int(网_rect.h * 整体缩放))
        key = (id(联网原图), 目标w, 目标h)

        网图 = _底部联网图标缩放缓存.get(key)
        if not isinstance(网图, pygame.Surface):
            try:
                if 联网原图.get_width() == 目标w and 联网原图.get_height() == 目标h:
                    网图 = 联网原图.convert_alpha()
                else:
                    网图 = pygame.transform.smoothscale(
                        联网原图, (目标w, 目标h)
                    ).convert_alpha()
            except Exception:
                网图 = None
            _底部联网图标缩放缓存[key] = 网图

        if isinstance(网图, pygame.Surface):
            图r = 网图.get_rect()

    # -------- 5) 组合居中绘制 --------
    总宽 = 文r.w + (图r.w + 间距 if 图r else 0)
    起始x = 锚点[0] - 总宽 // 2
    y中心 = 锚点[1]

    if 图r and isinstance(网图, pygame.Surface):
        图r.midleft = (起始x, y中心)
        屏幕.blit(网图, 图r.topleft)
        文r.midleft = (图r.right + 间距, y中心)
    else:
        文r.center = 锚点

    屏幕.blit(文面, 文r.topleft)
    return 文r
