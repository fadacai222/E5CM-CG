import os
import time
import re
import pygame


class 序列帧特效资源:
    """
    读取目录内 png 序列帧并排序：
    - 支持 UI_13FB.png / UI_I3FB.png（I 当成 1）
    - 优先按“末尾十六进制编号”排序，其次按文件名排序
    """

    def __init__(self, 目录: str, 扩展名: str = ".png"):
        self.目录 = 目录
        self.扩展名 = 扩展名.lower()
        self.帧列表: list[pygame.Surface] = []

    def _解析编号(self, 文件名: str):
        # 1) 优先匹配 _I3FB 这种：当作 0x13FB
        m = re.search(r"_I([0-9A-Fa-f]{3,6})", 文件名)
        if m:
            try:
                return int("1" + m.group(1), 16)
            except Exception:
                pass

        # 2) 匹配 _13FB / _140B 等
        m = re.search(r"_([0-9A-Fa-f]{3,6})", 文件名)
        if m:
            try:
                return int(m.group(1), 16)
            except Exception:
                pass

        # 3) 兜底：找任意一段 3~6 位 hex
        m = re.search(r"([0-9A-Fa-f]{3,6})", 文件名)
        if m:
            try:
                return int(m.group(1), 16)
            except Exception:
                pass

        return None

    def 加载(self) -> bool:
        if not self.目录 or (not os.path.isdir(self.目录)):
            return False

        文件列表 = []
        for fn in os.listdir(self.目录):
            if fn.lower().endswith(self.扩展名):
                文件列表.append(fn)

        if not 文件列表:
            return False

        带编号 = []
        无编号 = []
        for fn in 文件列表:
            num = self._解析编号(fn)
            if num is None:
                无编号.append(fn)
            else:
                带编号.append((num, fn))

        if 带编号:
            带编号.sort(key=lambda x: x[0])
            排序后 = [fn for _, fn in 带编号] + sorted(无编号)
        else:
            排序后 = sorted(文件列表)

        帧 = []
        for fn in 排序后:
            path = os.path.join(self.目录, fn)
            try:
                img = pygame.image.load(path).convert_alpha()
                帧.append(img)
            except Exception:
                continue

        if not 帧:
            return False

        self.帧列表 = 帧
        return True


class 点击特效实例:
    def __init__(self, x: int, y: int, 开始时间: float):
        self.x = x
        self.y = y
        self.开始时间 = 开始时间


class 全局点击特效管理器:
    """
    - 启动时加载全部帧
    - 触发：记录一个实例（位置+开始时间）
    - 更新绘制：按 fps 播放序列帧，播完自动销毁实例
    """

    def __init__(
        self, 帧列表: list[pygame.Surface], 每秒帧数: int = 30, 缩放比例: float = 1.0
    ):
        self.每秒帧数 = max(1, int(每秒帧数))
        self.缩放比例 = float(缩放比例)

        self._原始帧 = 帧列表[:] if 帧列表 else []
        self._缓存帧 = self._构建缩放缓存(self._原始帧, self.缩放比例)

        self._实例列表: list[点击特效实例] = []

    def _构建缩放缓存(self, 帧列表, 缩放比例):
        if not 帧列表:
            return []
        if abs(缩放比例 - 1.0) < 1e-6:
            return 帧列表

        缓存 = []
        for img in 帧列表:
            w, h = img.get_size()
            nw = max(1, int(w * 缩放比例))
            nh = max(1, int(h * 缩放比例))
            缓存.append(pygame.transform.smoothscale(img, (nw, nh)).convert_alpha())
        return 缓存

    def 触发(self, x: int, y: int):
        if not self._缓存帧:
            return
        self._实例列表.append(点击特效实例(x, y, time.time()))

    def 更新并绘制(self, 屏幕: pygame.Surface):
        if not self._缓存帧:
            return

        现在 = time.time()
        帧数 = len(self._缓存帧)
        生命周期 = 帧数 / self.每秒帧数

        新列表 = []
        for inst in self._实例列表:
            dt = 现在 - inst.开始时间
            if dt < 0 or dt >= 生命周期:
                continue

            idx = int(dt * self.每秒帧数)
            if idx < 0:
                idx = 0
            if idx >= 帧数:
                continue

            img = self._缓存帧[idx]
            r = img.get_rect()
            r.center = (inst.x, inst.y)
            屏幕.blit(img, r.topleft)

            新列表.append(inst)

        self._实例列表 = 新列表
