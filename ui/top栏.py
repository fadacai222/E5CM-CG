import pygame


def _contain缩放(图片: pygame.Surface, max_w: int, max_h: int) -> pygame.Surface:
    ow, oh = 图片.get_size()
    if ow <= 0 or oh <= 0:
        return pygame.Surface((max_w, max_h), pygame.SRCALPHA)
    比例 = min(max_w / ow, max_h / oh)
    nw, nh = max(1, int(ow * 比例)), max(1, int(oh * 比例))
    return pygame.transform.smoothscale(图片, (nw, nh)).convert_alpha()


def 生成top栏(
    屏幕: pygame.Surface,
    top背景原图: pygame.Surface | None,
    标题原图: pygame.Surface | None,
    设计宽: int,
    设计高: int,
    top设计高: int = 100,
    标题左右留边比例: float = 0,
    标题上移比例: float = 0.0,
    top背景宽占比: float = 1.0,
    top背景高占比: float = 1.3,  # 1.0=使用 top设计高；0.8=背景高度变矮
    # ✅ 新增：标题图可单独控最大宽高（覆盖“左右留边/0.80高度”的默认规则）
    标题最大宽占比: float | None = None,  # 例如 0.55 表示标题最大宽=屏幕宽*0.55
    标题最大高占比: float | None = None,  # 例如 0.60 表示标题最大高=top_h*0.60
    # ✅ 新增：标题可额外整体缩放（你想让标题更大/更小）
    标题整体缩放: float = 1.0,
):
    """
    返回：
      top_rect, top背景图(已缩放), 标题rect, 标题图(已缩放)
    """

    屏幕宽, 屏幕高 = 屏幕.get_size()
    scale = min(屏幕宽 / max(1, 设计宽), 屏幕高 / max(1, 设计高))

    # top栏逻辑高度（用于布局锚点），仍按 top设计高 * scale
    top_h = max(1, int(top设计高 * scale))
    top_rect = pygame.Rect(0, 0, 屏幕宽, top_h)

    # ===================== 背景图：可单独控制宽高 =====================
    top图 = None
    if top背景原图:
        背景目标宽 = max(1, int(屏幕宽 * float(top背景宽占比)))
        背景目标高 = max(1, int(top_h * float(top背景高占比)))
        背景图 = pygame.transform.smoothscale(
            top背景原图, (背景目标宽, 背景目标高)
        ).convert_alpha()
        top图 = 背景图

        # 背景图 rect：默认居中贴在 top_rect 内（你要左对齐/右对齐再加参数也行）
        self_top背景rect = 背景图.get_rect()
        self_top背景rect.centerx = top_rect.centerx
        self_top背景rect.centery = top_rect.centery

        # 注意：这里返回的 top_rect 仍是“逻辑 top栏区域”，
        # 背景图实际绘制位置用 self_top背景rect.topleft
        # 为了不破坏你现有调用方式，我们把 top_rect 仍返回，但背景图本身是缩放后的 surface。
        # 你如果希望拿到背景rect，也可以再扩展返回值。
    else:
        self_top背景rect = top_rect.copy()

    # ===================== 标题图：可单独控制最大宽高 =====================
    标题图 = None
    标题rect = pygame.Rect(top_rect.centerx, top_rect.centery, 1, 1)

    if 标题原图:
        # 默认规则：左右留边 + 高度占 top_h 的 0.80
        if 标题最大宽占比 is None:
            max_w = max(1, int(屏幕宽 * (1.0 - 2.0 * float(标题左右留边比例))))
        else:
            max_w = max(1, int(屏幕宽 * float(标题最大宽占比)))

        if 标题最大高占比 is None:
            max_h = max(1, int(top_h * 0.80))
        else:
            max_h = max(1, int(top_h * float(标题最大高占比)))

        标题图 = _contain缩放(标题原图, max_w, max_h)

        # 标题整体缩放（可让它再大一点）
        if 标题整体缩放 and abs(float(标题整体缩放) - 1.0) > 1e-6:
            tw, th = 标题图.get_size()
            tw2 = max(1, int(tw * float(标题整体缩放)))
            th2 = max(1, int(th * float(标题整体缩放)))
            标题图 = pygame.transform.smoothscale(标题图, (tw2, th2)).convert_alpha()

        标题rect = 标题图.get_rect()
        标题rect.center = top_rect.center

        # 标题上移
        标题rect.y -= int(top_h * float(标题上移比例))

    # ===================== 返回 =====================
    # 注意：背景图的绘制位置如果要跟着 top背景宽占比 居中，你要用上面算的 self_top背景rect
    # 但为兼容旧代码，这里仍然返回 top_rect + top图（surface）；
    # 如果你需要精确背景rect，我建议你直接再加一个返回值（我也可以帮你改）。
    return top_rect, top图, 标题rect, 标题图
