import json
import os
import time
from typing import Dict, Optional, Tuple, List

import pygame


class 所见即所得布局调试器:

    def __init__(self, 上下文: dict, 保存路径: str):
        self.上下文 = 上下文
        self.保存路径 = str(保存路径 or "")

        self.是否开启 = False
        self._当前场景 = None

        # ✅ 禁用场景：个人资料已调完，禁止再开调试
        self._禁用场景名集合 = {"个人资料"}

        self._控件表: Dict[str, pygame.Rect] = {}
        self._控件名列表: List[str] = []
        self._选中控件名: Optional[str] = None

        self._拖拽中 = False
        self._缩放中 = False
        self._拖拽起点 = (0, 0)
        self._拖拽起始rect = pygame.Rect(0, 0, 1, 1)
        self._拖拽偏移 = (0, 0)

        self._鼠标命中列表: List[str] = []
        self._命中循环索引 = 0

        self._提示文本 = ""
        self._提示截止 = 0.0

        self._样式映射 = {
            "昵称锚点": ("昵称字号", "昵称粗体", None),
            "统计区": ("统计字号", "统计粗体", None),
            "介绍区": ("介绍字号", "介绍粗体", None),
            "软件信息": ("下方左字号", "下方左粗体", None),
            "软件说明": ("下方右字号", "下方右粗体", None),
            "花式标签": ("进度标签字号", "进度标签粗体", "进度标签间距"),
            "竞速标签": ("进度标签字号", "进度标签粗体", "进度标签间距"),
            "花式LV": ("进度LV字号", "进度LV粗体", "进度LV间距"),
            "竞速LV": ("进度LV字号", "进度LV粗体", "进度LV间距"),
        }

        self._确保保存目录()

    def _确保保存目录(self):
        try:
            if not self.保存路径:
                return
            d = os.path.dirname(self.保存路径)
            if d:
                os.makedirs(d, exist_ok=True)
        except Exception:
            pass

    def _提示(self, 文本: str, 秒: float = 1.4):
        self._提示文本 = str(文本)
        self._提示截止 = time.time() + float(秒)

    # ---------------- 绑定/开关 ----------------
    def 绑定场景(self, 场景对象):
        self._当前场景 = 场景对象
        self._刷新控件表()

        # ✅ 绑定时自动加载该场景的布局
        self._从文件加载并应用()

        # ✅ 默认选中一个（避免“选中为空”）
        if (self._选中控件名 not in self._控件表) and self._控件名列表:
            self._选中控件名 = self._控件名列表[0]

    def 切换开关(self):
        # ✅ 禁用场景：不允许开启
        当前场景名 = self._场景名()
        if (not self.是否开启) and (
            当前场景名 in getattr(self, "_禁用场景名集合", set())
        ):
            self.是否开启 = False
            try:
                self.上下文["布局调试_开启"] = False
            except Exception:
                pass
            self._提示(f"该页面禁止布局调试：{当前场景名}", 1.4)
            return

        self.是否开启 = not self.是否开启

        try:
            self.上下文["布局调试_开启"] = bool(self.是否开启)
        except Exception:
            pass

        if self.是否开启:
            self._刷新控件表()
            self._提示("布局调试：已开启", 1.0)
        else:
            self._拖拽中 = False
            self._缩放中 = False
            self._提示("布局调试：已关闭", 1.0)

    # ---------------- 数据读写 ----------------
    def _读取总文件(self) -> dict:
        if (not self.保存路径) or (not os.path.isfile(self.保存路径)):
            return {}
        try:
            with open(self.保存路径, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _写入总文件(self, 数据: dict):
        if not self.保存路径:
            return
        try:
            self._确保保存目录()
            with open(self.保存路径, "w", encoding="utf-8") as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _场景名(self) -> str:
        try:
            return str(
                getattr(self._当前场景, "名称", "") or self._当前场景.__class__.__name__
            )
        except Exception:
            return "unknown_scene"

    def _从文件加载并应用(self):
        if self._当前场景 is None:
            return
        if not hasattr(self._当前场景, "调试_导入布局"):
            return

        总 = self._读取总文件()
        场景键 = self._场景名()
        数据 = 总.get(场景键)
        if not isinstance(数据, dict):
            return

        try:
            self._当前场景.调试_导入布局(数据)
            self._刷新控件表()
            self._提示("布局：已加载", 1.0)
        except Exception:
            pass

    def _保存到文件(self):
        if self._当前场景 is None:
            return
        if not hasattr(self._当前场景, "调试_导出布局"):
            self._提示("场景不支持导出布局", 1.6)
            return

        try:
            数据 = self._当前场景.调试_导出布局()
        except Exception:
            数据 = None

        if not isinstance(数据, dict):
            self._提示("导出失败：无数据", 1.6)
            return

        总 = self._读取总文件()
        总[self._场景名()] = 数据
        self._写入总文件(总)
        self._提示("布局：已保存 (Ctrl+S)", 1.2)

    def _清空全部覆盖(self):
        if self._当前场景 is None:
            return
        if not hasattr(self._当前场景, "调试_导入布局"):
            return
        try:
            self._当前场景.调试_导入布局({"覆盖": {}, "样式": {}})
            self._刷新控件表()
            self._提示("已清空全部覆盖", 1.2)
        except Exception:
            pass

    def _清除选中控件覆盖(self):
        if self._当前场景 is None:
            return
        if not self._选中控件名:
            return
        if not hasattr(self._当前场景, "调试_导出布局") or not hasattr(
            self._当前场景, "调试_导入布局"
        ):
            return

        try:
            数据 = self._当前场景.调试_导出布局()
        except Exception:
            数据 = {}

        覆盖 = {}
        样式 = {}
        if isinstance(数据, dict):
            if isinstance(数据.get("覆盖"), dict):
                覆盖 = dict(数据.get("覆盖") or {})
            if isinstance(数据.get("样式"), dict):
                样式 = dict(数据.get("样式"))

        if self._选中控件名 in 覆盖:
            try:
                覆盖.pop(self._选中控件名, None)
            except Exception:
                pass

        try:
            self._当前场景.调试_导入布局({"覆盖": 覆盖, "样式": 样式})
            self._刷新控件表()
            self._提示(f"已清除：{self._选中控件名}", 1.2)
        except Exception:
            pass

    # ---------------- 控件表/命中 ----------------
    def _刷新控件表(self):
        self._控件表 = {}
        self._控件名列表 = []
        if self._当前场景 is None:
            return
        if not hasattr(self._当前场景, "调试_获取可编辑控件"):
            return
        try:
            表 = self._当前场景.调试_获取可编辑控件()
        except Exception:
            表 = None
        if not isinstance(表, dict):
            return

        for k, v in 表.items():
            if isinstance(v, pygame.Rect):
                self._控件表[str(k)] = v.copy()

        # ✅ 稳定排序：按面积从小到大（方便点选小控件）
        self._控件名列表 = sorted(
            self._控件表.keys(),
            key=lambda 名: (self._控件表[名].w * self._控件表[名].h, 名),
        )

    def _命中控件列表(self, 坐标: Tuple[int, int]) -> List[str]:
        x, y = int(坐标[0]), int(坐标[1])
        命中 = []
        for 名 in self._控件名列表:
            r = self._控件表.get(名)
            if isinstance(r, pygame.Rect) and r.collidepoint(x, y):
                命中.append(名)

        # ✅ 命中也按“面积小优先”
        命中.sort(key=lambda 名: self._控件表[名].w * self._控件表[名].h)
        return 命中

    def _选中下一个(self, 方向: int = 1):
        if not self._控件名列表:
            return
        if self._选中控件名 not in self._控件名列表:
            self._选中控件名 = self._控件名列表[0]
            return
        idx = self._控件名列表.index(self._选中控件名)
        idx = (idx + int(方向)) % len(self._控件名列表)
        self._选中控件名 = self._控件名列表[idx]

    # ---------------- 样式写回（字号/粗体/紧凑） ----------------
    def _场景_设置样式(self, 键: str, 值):
        if self._当前场景 is None:
            return
        if hasattr(self._当前场景, "调试_设置样式"):
            try:
                self._当前场景.调试_设置样式(str(键), 值)
                return
            except Exception:
                pass

        # 兜底：直接写 _调试_样式
        try:
            if not hasattr(self._当前场景, "_调试_样式") or not isinstance(
                getattr(self._当前场景, "_调试_样式"), dict
            ):
                self._当前场景._调试_样式 = {}
            self._当前场景._调试_样式[str(键)] = 值
            try:
                self._当前场景._缓存尺寸 = (0, 0)
            except Exception:
                pass
        except Exception:
            pass

    def _调整间距(self, 增量: int):
        if not self._选中控件名:
            self._提示("未选中控件", 1.0)
            return

        映射 = self._样式映射.get(self._选中控件名)
        if not (isinstance(映射, tuple) and len(映射) >= 3):
            self._提示("该控件不支持调间距(Alt+Ctrl+滚轮)", 1.4)
            return

        间距键 = 映射[2]
        if not 间距键:
            self._提示("该控件不支持调间距(Alt+Ctrl+滚轮)", 1.4)
            return

        当前 = 0
        try:
            if hasattr(self._当前场景, "_调试_样式") and isinstance(
                self._当前场景._调试_样式, dict
            ):
                v = self._当前场景._调试_样式.get(间距键)
                if isinstance(v, int):
                    当前 = int(v)
        except Exception:
            当前 = 0

        新值 = int(max(0, min(200, 当前 + int(增量))))
        self._场景_设置样式(间距键, 新值)
        self._提示(f"{间距键} = {新值}", 1.0)

    def _调整字号(self, 增量: int):
        if not self._选中控件名:
            self._提示("未选中控件", 1.0)
            return

        映射 = self._样式映射.get(self._选中控件名)

        # ✅ 兼容：映射可能是 (字号键, 粗体键) 或 (字号键, 粗体键, 间距键)
        if not (isinstance(映射, tuple) and len(映射) >= 2):
            self._提示("该控件不支持调字号(Alt+滚轮)", 1.2)
            return

        字号键 = 映射[0]
        if not 字号键:
            self._提示("该控件不支持调字号(Alt+滚轮)", 1.2)
            return

        当前 = 0
        try:
            if hasattr(self._当前场景, "调试_获取可编辑样式"):
                样式 = self._当前场景.调试_获取可编辑样式()
                if isinstance(样式, dict):
                    v = 样式.get(字号键)
                    if isinstance(v, int):
                        当前 = int(v)
        except Exception:
            当前 = 0

        新值 = int(max(6, min(200, 当前 + int(增量))))
        self._场景_设置样式(字号键, 新值)
        self._提示(f"{字号键} = {新值}", 1.0)

    def _切换粗体(self):
        if not self._选中控件名:
            self._提示("未选中控件", 1.0)
            return

        映射 = self._样式映射.get(self._选中控件名)

        # ✅ 兼容：2 元组 / 3 元组
        if not (isinstance(映射, tuple) and len(映射) >= 2):
            self._提示("该控件不支持切粗体(B)", 1.2)
            return

        粗体键 = 映射[1]
        if not 粗体键:
            self._提示("该控件不支持切粗体(B)", 1.2)
            return

        当前 = False
        try:
            if hasattr(self._当前场景, "调试_获取可编辑样式"):
                样式 = self._当前场景.调试_获取可编辑样式()
                if isinstance(样式, dict):
                    v = 样式.get(粗体键)
                    if isinstance(v, bool):
                        当前 = bool(v)
        except Exception:
            当前 = False

        新值 = not bool(当前)
        self._场景_设置样式(粗体键, 新值)
        self._提示(f"{粗体键} = {新值}", 1.0)

    def _调整紧凑(self, 增量: float):
        当前 = 0.78
        try:
            if hasattr(self._当前场景, "_调试_样式") and isinstance(
                self._当前场景._调试_样式, dict
            ):
                v = self._当前场景._调试_样式.get("紧凑系数")
                if isinstance(v, (int, float)):
                    当前 = float(v)
        except Exception:
            pass

        新值 = 当前 + float(增量)
        if 新值 < 0.55:
            新值 = 0.55
        if 新值 > 1.10:
            新值 = 1.10
        self._场景_设置样式("紧凑系数", float(round(新值, 3)))
        self._提示(f"紧凑系数 = {float(round(新值, 3))}", 1.0)

    # ---------------- 写回 rect ----------------
    def _写回rect(self, 控件名: str, rect: pygame.Rect):
        if self._当前场景 is None:
            return
        if not hasattr(self._当前场景, "调试_设置控件rect"):
            return
        try:
            self._当前场景.调试_设置控件rect(str(控件名), rect)
        except Exception:
            pass

    def _获取选中rect(self) -> Optional[pygame.Rect]:
        if not self._选中控件名:
            return None
        r = self._控件表.get(self._选中控件名)
        return r.copy() if isinstance(r, pygame.Rect) else None

    # ---------------- 事件 ----------------
    def 处理事件(self, 事件) -> bool:
        if not self.是否开启:
            return False

        # ✅ 实时刷新（控件可能每帧变化）
        self._刷新控件表()

        # ESC：退出调试
        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
            self.切换开关()
            return True

        # Ctrl+S：保存
        if (
            事件.type == pygame.KEYDOWN
            and 事件.key == pygame.K_s
            and (pygame.key.get_mods() & pygame.KMOD_CTRL)
        ):
            self._保存到文件()
            return True

        # Ctrl+L：加载
        if (
            事件.type == pygame.KEYDOWN
            and 事件.key == pygame.K_l
            and (pygame.key.get_mods() & pygame.KMOD_CTRL)
        ):
            self._从文件加载并应用()
            return True

        # Ctrl+Backspace：清空全部
        if (
            事件.type == pygame.KEYDOWN
            and 事件.key == pygame.K_BACKSPACE
            and (pygame.key.get_mods() & pygame.KMOD_CTRL)
        ):
            self._清空全部覆盖()
            return True

        # Backspace：清空当前控件
        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_BACKSPACE:
            self._清除选中控件覆盖()
            return True

        # Tab/Shift+Tab：切换选中
        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_TAB:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                self._选中下一个(-1)
            else:
                self._选中下一个(+1)
            return True

        # B：切粗体
        if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_b:
            self._切换粗体()
            return True

        # 鼠标滚轮（pygame2）
        if 事件.type == pygame.MOUSEWHEEL:
            return self._处理滚轮(事件.y)

        # 老式滚轮（button 4/5）
        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button in (4, 5):
            方向 = 1 if 事件.button == 4 else -1
            return self._处理滚轮(方向)

        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button in (1, 3):
            鼠标坐标 = getattr(事件, "pos", (0, 0))
            命中 = self._命中控件列表(鼠标坐标)
            self._鼠标命中列表 = 命中
            self._命中循环索引 = 0

            if not 命中:
                return True

            # 左键：默认选“最小面积”（更像 PS 点选）
            if 事件.button == 1:
                self._选中控件名 = 命中[0]
                self._开始拖拽(鼠标坐标)
                return True

            # 右键：循环选择（解决重叠）
            if 事件.button == 3:
                self._命中循环索引 = (self._命中循环索引 + 1) % len(命中)
                self._选中控件名 = 命中[self._命中循环索引]
                return True

        if 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
            self._拖拽中 = False
            self._缩放中 = False
            return True

        if 事件.type == pygame.MOUSEMOTION:
            if self._拖拽中:
                self._更新拖拽(getattr(事件, "pos", (0, 0)))
                return True

        return True  # ✅ 开启调试时默认吃掉事件，避免误触场景切换

    def _开始拖拽(self, 鼠标坐标: Tuple[int, int]):
        if not self._选中控件名:
            return
        r = self._控件表.get(self._选中控件名)
        if not isinstance(r, pygame.Rect):
            return

        self._拖拽中 = True
        self._拖拽起点 = (int(鼠标坐标[0]), int(鼠标坐标[1]))
        self._拖拽起始rect = r.copy()

        mx, my = self._拖拽起点
        self._拖拽偏移 = (mx - r.x, my - r.y)

        mods = pygame.key.get_mods()
        self._缩放中 = bool(mods & pygame.KMOD_SHIFT)

    def _更新拖拽(self, 鼠标坐标: Tuple[int, int]):
        if not self._选中控件名:
            return
        r = self._拖拽起始rect.copy()

        mx, my = int(鼠标坐标[0]), int(鼠标坐标[1])
        x0, y0 = self._拖拽起点

        dx = mx - x0
        dy = my - y0

        if self._缩放中:
            # Shift+拖拽：从右下角缩放（PS 风格够用）
            新w = max(20, r.w + dx)
            新h = max(20, r.h + dy)
            新rect = pygame.Rect(r.x, r.y, 新w, 新h)
        else:
            # 拖拽：移动
            ox, oy = self._拖拽偏移
            新rect = pygame.Rect(mx - ox, my - oy, r.w, r.h)

        self._控件表[self._选中控件名] = 新rect.copy()
        self._写回rect(self._选中控件名, 新rect)

    def _处理滚轮(self, 方向: int):
        import pygame

        try:
            步进 = 1 if int(方向) > 0 else -1
        except Exception:
            步进 = 0

        # ✅ 修复关键 bug：你类里叫 _当前场景，不是 _场景
        场景 = getattr(self, "_当前场景", None)
        if 场景 is None:
            return True

        mods = 0
        try:
            mods = pygame.key.get_mods()
        except Exception:
            mods = 0

        是否Ctrl = bool(mods & pygame.KMOD_CTRL)
        是否Alt = bool(mods & pygame.KMOD_ALT)
        是否Shift = bool(mods & pygame.KMOD_SHIFT)

        # ---------- 1) Ctrl+Shift：调“全局字距”（每个字之间的字距） ----------
        if 是否Ctrl and 是否Shift and (not 是否Alt):
            当前样式 = {}
            try:
                if hasattr(场景, "调试_获取可编辑样式"):
                    当前样式 = 场景.调试_获取可编辑样式() or {}
            except Exception:
                当前样式 = {}

            try:
                当前值 = int(当前样式.get("全局字距", 1))
            except Exception:
                当前值 = 1

            新值 = 当前值 + 步进
            新值 = 0 if 新值 < 0 else (40 if 新值 > 40 else 新值)

            try:
                if hasattr(场景, "调试_设置样式"):
                    场景.调试_设置样式("全局字距", int(新值))
            except Exception:
                pass

            self._提示(f"全局字距 = {新值}", 1.0)
            return True

        # ---------- 2) Alt+Ctrl：调“间距键”（你原来的水平间距） ----------
        if 是否Alt and 是否Ctrl:
            self._调整间距(步进)
            return True

        # ---------- 3) Alt+Shift：调“行距键”（统计/介绍/下方左/下方右） ----------
        if 是否Alt and 是否Shift:
            if not self._选中控件名:
                self._提示("未选中控件：先点一下文本区域", 1.2)
                return True

            行距键 = None
            if self._选中控件名 == "统计区":
                行距键 = "统计行距"
            elif self._选中控件名 == "介绍区":
                行距键 = "介绍行距"
            elif self._选中控件名 == "软件信息":
                行距键 = "下方左行距"
            elif self._选中控件名 == "软件说明":
                行距键 = "下方右行距"
            else:
                self._提示("该控件不支持行距(Alt+Shift+滚轮)", 1.2)
                return True

            当前样式 = {}
            try:
                if hasattr(场景, "调试_获取可编辑样式"):
                    当前样式 = 场景.调试_获取可编辑样式() or {}
            except Exception:
                当前样式 = {}

            try:
                当前值 = int(当前样式.get(行距键, 8))
            except Exception:
                当前值 = 8

            新值 = 当前值 + 步进
            新值 = 0 if 新值 < 0 else (160 if 新值 > 160 else 新值)

            try:
                if hasattr(场景, "调试_设置样式"):
                    场景.调试_设置样式(行距键, int(新值))
            except Exception:
                pass

            self._提示(f"{行距键} = {新值}", 1.0)
            return True

        # ---------- 4) Alt：调字号 ----------
        if 是否Alt and (not 是否Ctrl) and (not 是否Shift):
            self._调整字号(步进)
            return True

        # ---------- 6) 默认：缩放选中控件 rect（真正所见即所得） ----------
        if not self._选中控件名:
            self._提示("未选中控件：先左键点一下框", 1.0)
            return True

        r = self._控件表.get(self._选中控件名)
        if not isinstance(r, pygame.Rect):
            return True

        # 缩放步长：2%（可自行调大）
        比例 = 1.02 if 步进 > 0 else 0.98

        新 = r.copy()
        cx, cy = 新.centerx, 新.centery

        if 是否Ctrl and (not 是否Shift):
            # 只改宽
            新.w = max(20, int(新.w * 比例))
        elif 是否Shift and (not 是否Ctrl):
            # 只改高
            新.h = max(20, int(新.h * 比例))
        else:
            # 等比缩放
            新.w = max(20, int(新.w * 比例))
            新.h = max(20, int(新.h * 比例))

        新.center = (cx, cy)

        self._控件表[self._选中控件名] = 新.copy()
        self._写回rect(self._选中控件名, 新)

        self._提示(f"{self._选中控件名} 缩放: w={新.w} h={新.h}", 0.6)
        return True

    # ---------------- 绘制 ----------------

    def 更新并绘制(self, 屏幕: pygame.Surface):
        if not self.是否开启:
            return

        self._刷新控件表()

        # 画所有控件框（无文字）
        for 名 in self._控件名列表:
            r = self._控件表.get(名)
            if not isinstance(r, pygame.Rect):
                continue
            if 名 == self._选中控件名:
                pygame.draw.rect(屏幕, (255, 220, 120), r, width=2)
                # 角点提示
                pygame.draw.circle(屏幕, (255, 220, 120), r.topleft, 4)
                pygame.draw.circle(屏幕, (255, 220, 120), r.bottomright, 4)
            else:
                pygame.draw.rect(屏幕, (220, 220, 220), r, width=1)

        # 右上角操作简介
        self._绘制右上角说明(屏幕)

    def _绘制右上角说明(self, 屏幕: pygame.Surface):
        try:
            字体 = self.上下文.get("字体", {}).get("小字")
            if not isinstance(字体, pygame.font.Font):
                字体 = pygame.font.SysFont("Arial", 10)
        except Exception:
            字体 = pygame.font.SysFont("Arial", 10)

        w, _h = 屏幕.get_size()
        x = w - 12
        y = 12

        选中rect = self._获取选中rect()
        选中名 = self._选中控件名 or "未选中"

        行 = []
        行.append("【布局调试 F6】")
        行.append("左键：选中/拖动移动")
        行.append("Shift+拖动：缩放")
        行.append("右键：循环选择重叠控件")
        行.append("滚轮：等比缩放控件")
        行.append("Ctrl+滚轮：只改宽  Shift+滚轮：只改高")
        行.append("Alt+滚轮：调字号(文本控件)")
        行.append("Alt+Ctrl+滚轮：调“字间距”(文本与条/LV间距)")
        行.append("Alt+Shift+滚轮：调紧凑(全体边距)")
        行.append("B：切换粗体(若支持)")
        行.append("Tab：切换控件  Backspace：清当前控件  Ctrl+Backspace：清全部")
        行.append("Ctrl+S 保存  Ctrl+L 加载  ESC 退出调试")
        行.append("")
        if isinstance(选中rect, pygame.Rect):
            行.append(f"选中：{选中名}")
            行.append(f"x={选中rect.x} y={选中rect.y} w={选中rect.w} h={选中rect.h}")
        else:
            行.append(f"选中：{选中名}")

        if self._提示文本 and time.time() < self._提示截止:
            行.append("")
            行.append(self._提示文本)

        最大宽 = 0
        for t in 行:
            try:
                最大宽 = max(最大宽, 字体.size(t)[0])
            except Exception:
                pass
        行高 = max(18, 字体.get_height() + 2)
        高 = 行高 * len(行) + 10
        宽 = 最大宽 + 18

        背景 = pygame.Surface((宽, 高), pygame.SRCALPHA)
        背景.fill((0, 0, 0, 130))
        屏幕.blit(背景, (x - 宽, y))

        yy = y + 6
        for t in 行:
            try:
                面 = 字体.render(t, True, (235, 235, 235))
            except Exception:
                continue
            rr = 面.get_rect()
            rr.topright = (x - 8, yy)
            屏幕.blit(面, rr.topleft)
            yy += 行高
