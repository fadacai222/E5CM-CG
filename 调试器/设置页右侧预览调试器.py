import json
import os
from typing import Any, Dict, List, Optional, Tuple

import pygame

from ui.选歌设置菜单控件 import 绘制_cover裁切预览


def _项目根目录() -> str:
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.getcwd()


def _安全读json(路径: str) -> Dict[str, Any]:
    if (not 路径) or (not os.path.isfile(路径)):
        return {}
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码) as f:
                obj = json.load(f)
            return dict(obj) if isinstance(obj, dict) else {}
        except Exception:
            continue
    return {}


def _安全写json(路径: str, 数据: Dict[str, Any]) -> bool:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(路径)), exist_ok=True)
        with open(路径, "w", encoding="utf-8") as f:
            json.dump(数据, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _转tuple2(值: Any, 默认: Tuple[int, int]) -> Tuple[int, int]:
    if isinstance(值, (list, tuple)) and len(值) >= 2:
        try:
            return (int(值[0]), int(值[1]))
        except Exception:
            return 默认
    return 默认


def _读取配置(路径: str) -> Dict[str, Any]:
    数据 = _安全读json(路径)
    默认: Dict[str, Any] = {
        "_设置页_面板宽占比": 0.88,
        "_设置页_面板高占比": 0.78,
        "_设置页_面板整体缩放": 1.0,
        "_设置页_面板_x偏移": 0,
        "_设置页_面板_y偏移": 0,
        "_设置页_右区_x占比": 0.52,
        "_设置页_右区_y占比": 0.18,
        "_设置页_右区_宽占比": 0.42,
        "_设置页_右区_高占比": 0.70,
        "_设置页_右区_额外偏移": (0, 0),
        "_设置页_右区_预览内边距": 10,
        "_设置页_右区_预览框_偏移": (0, 0),
        "_设置页_右区_预览框_宽缩放": 1.0,
        "_设置页_右区_预览框_高缩放": 1.0,
        "_设置页_右区_左大箭头_偏移": (0, 0),
        "_设置页_右区_右大箭头_偏移": (0, 0),
        "_设置页_右区_左大箭头_缩放": 1.0,
        "_设置页_右区_右大箭头_缩放": 1.0,
    }
    配置 = dict(默认)
    配置.update({k: v for k, v in 数据.items() if k in 默认})
    配置["_设置页_右区_额外偏移"] = _转tuple2(
        配置.get("_设置页_右区_额外偏移"), (0, 0)
    )
    配置["_设置页_右区_预览框_偏移"] = _转tuple2(
        配置.get("_设置页_右区_预览框_偏移"), (0, 0)
    )
    配置["_设置页_右区_左大箭头_偏移"] = _转tuple2(
        配置.get("_设置页_右区_左大箭头_偏移"), (0, 0)
    )
    配置["_设置页_右区_右大箭头_偏移"] = _转tuple2(
        配置.get("_设置页_右区_右大箭头_偏移"), (0, 0)
    )
    return 配置


def _保存配置(路径: str, 当前配置: Dict[str, Any]):
    原始 = _安全读json(路径)
    if not isinstance(原始, dict):
        原始 = {}
    写入 = dict(原始)
    for k, v in 当前配置.items():
        if isinstance(v, tuple):
            写入[k] = [int(v[0]), int(v[1])]
        elif isinstance(v, float):
            写入[k] = float(v)
        elif isinstance(v, int):
            写入[k] = int(v)
        else:
            写入[k] = v
    return _安全写json(路径, 写入)


def _安全载图(路径: str, 透明: bool = True) -> Optional[pygame.Surface]:
    try:
        if 路径 and os.path.isfile(路径):
            图 = pygame.image.load(路径)
            return 图.convert_alpha() if 透明 else 图.convert()
    except Exception:
        pass
    return None


def _取字体(字号: int, 粗体: bool = False) -> pygame.font.Font:
    pygame.font.init()
    候选 = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        os.path.join(_项目根目录(), "冷资源", "字体", "方正黑体简体.TTF"),
    ]
    for p in 候选:
        try:
            if os.path.isfile(p):
                return pygame.font.Font(p, int(字号))
        except Exception:
            continue
    try:
        return pygame.font.SysFont("Microsoft YaHei", int(字号), bold=bool(粗体))
    except Exception:
        return pygame.font.Font(None, int(字号))


def _计算布局(屏宽: int, 屏高: int, cfg: Dict[str, Any]) -> Dict[str, pygame.Rect]:
    面板宽 = int(
        float(屏宽) * float(cfg.get("_设置页_面板宽占比", 0.88))
        * float(cfg.get("_设置页_面板整体缩放", 1.0))
    )
    面板高 = int(
        float(屏高) * float(cfg.get("_设置页_面板高占比", 0.78))
        * float(cfg.get("_设置页_面板整体缩放", 1.0))
    )
    面板宽 = max(700, min(面板宽, 屏宽 - 40))
    面板高 = max(420, min(面板高, 屏高 - 40))
    面板 = pygame.Rect(0, 0, int(面板宽), int(面板高))
    面板.center = (
        int(屏宽 // 2 + int(cfg.get("_设置页_面板_x偏移", 0) or 0)),
        int(屏高 // 2 + int(cfg.get("_设置页_面板_y偏移", 0) or 0)),
    )

    右区偏移 = _转tuple2(cfg.get("_设置页_右区_额外偏移"), (0, 0))
    右区 = pygame.Rect(
        int(float(面板.w) * float(cfg.get("_设置页_右区_x占比", 0.52))) + int(右区偏移[0]),
        int(float(面板.h) * float(cfg.get("_设置页_右区_y占比", 0.18))) + int(右区偏移[1]),
        int(float(面板.w) * float(cfg.get("_设置页_右区_宽占比", 0.42))),
        int(float(面板.h) * float(cfg.get("_设置页_右区_高占比", 0.70))),
    )
    大箭边长基准 = max(26, int(float(右区.h) * 0.18))

    左缩放 = float(max(0.3, min(3.0, float(cfg.get("_设置页_右区_左大箭头_缩放", 1.0)))))
    右缩放 = float(max(0.3, min(3.0, float(cfg.get("_设置页_右区_右大箭头_缩放", 1.0)))))
    左边长 = max(16, int(round(float(大箭边长基准) * 左缩放)))
    右边长 = max(16, int(round(float(大箭边长基准) * 右缩放)))
    左偏移 = _转tuple2(cfg.get("_设置页_右区_左大箭头_偏移"), (0, 0))
    右偏移 = _转tuple2(cfg.get("_设置页_右区_右大箭头_偏移"), (0, 0))

    左箭 = pygame.Rect(
        int(右区.x + 左偏移[0]),
        int(右区.centery - 左边长 // 2 + 左偏移[1]),
        int(左边长),
        int(左边长),
    )
    右箭 = pygame.Rect(
        int(右区.right - 右边长 + 右偏移[0]),
        int(右区.centery - 右边长 // 2 + 右偏移[1]),
        int(右边长),
        int(右边长),
    )

    内边距 = int(max(0, cfg.get("_设置页_右区_预览内边距", 10) or 10))
    基准预览 = pygame.Rect(
        int(左箭.right + 10),
        int(右区.y + 内边距),
        int(max(10, 右区.w - 左箭.w - 右箭.w - 20)),
        int(max(10, 右区.h - 内边距 * 2)),
    )
    预览偏移 = _转tuple2(cfg.get("_设置页_右区_预览框_偏移"), (0, 0))
    预览宽缩放 = float(max(0.2, min(3.0, float(cfg.get("_设置页_右区_预览框_宽缩放", 1.0)))))
    预览高缩放 = float(max(0.2, min(3.0, float(cfg.get("_设置页_右区_预览框_高缩放", 1.0)))))
    预览 = pygame.Rect(
        0,
        0,
        int(max(10, round(float(基准预览.w) * 预览宽缩放))),
        int(max(10, round(float(基准预览.h) * 预览高缩放))),
    )
    预览.center = (
        int(基准预览.centerx + 预览偏移[0]),
        int(基准预览.centery + 预览偏移[1]),
    )

    return {
        "面板": 面板,
        "右区": pygame.Rect(面板.x + 右区.x, 面板.y + 右区.y, 右区.w, 右区.h),
        "左箭": pygame.Rect(面板.x + 左箭.x, 面板.y + 左箭.y, 左箭.w, 左箭.h),
        "右箭": pygame.Rect(面板.x + 右箭.x, 面板.y + 右箭.y, 右箭.w, 右箭.h),
        "预览": pygame.Rect(面板.x + 预览.x, 面板.y + 预览.y, 预览.w, 预览.h),
    }


def 主函数():
    根 = _项目根目录()
    配置路径 = os.path.join(根, "json", "设置页布局覆盖.json")
    cfg = _读取配置(配置路径)

    pygame.init()
    屏幕 = pygame.display.set_mode((1600, 900), pygame.RESIZABLE)
    pygame.display.set_caption("设置页右侧预览调试器")
    时钟 = pygame.time.Clock()
    字体 = _取字体(18, False)
    小字 = _取字体(16, False)

    设置背景图 = _安全载图(
        os.path.join(根, "UI-img", "选歌界面资源", "设置", "设置背景图.png"),
        透明=True,
    )
    左箭图 = _安全载图(
        os.path.join(根, "UI-img", "选歌界面资源", "设置", "左大箭头.png"),
        透明=True,
    )
    右箭图 = _安全载图(
        os.path.join(根, "UI-img", "选歌界面资源", "设置", "右大箭头.png"),
        透明=True,
    )
    选歌背景图 = _安全载图(
        os.path.join(根, "冷资源", "backimages", "选歌界面.png"), 透明=False
    )

    背景图目录 = os.path.join(根, "冷资源", "backimages", "背景图")
    预览图路径列表: List[str] = []
    if os.path.isdir(背景图目录):
        for f in sorted(os.listdir(背景图目录)):
            if str(f).lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
                预览图路径列表.append(os.path.join(背景图目录, f))
    当前预览索引 = 0
    预览图 = _安全载图(
        预览图路径列表[0], 透明=True
    ) if 预览图路径列表 else None

    选中对象 = "预览"
    拖拽中 = False
    上次鼠标 = (0, 0)
    显示基准框 = True
    提示 = "S保存  R重载  1/2/3选对象  鼠标拖拽移动  滚轮缩放  ←↑↓→微调  ESC退出"
    提示截止 = 0.0

    def _提示(t: str, 秒: float = 1.4):
        nonlocal 提示, 提示截止
        提示 = str(t or "")
        提示截止 = pygame.time.get_ticks() / 1000.0 + float(秒)

    def _更新预览图():
        nonlocal 预览图
        if 预览图路径列表:
            预览图 = _安全载图(预览图路径列表[当前预览索引], 透明=True)

    def _移动对象(对象: str, dx: int, dy: int):
        if 对象 == "预览":
            x, y = _转tuple2(cfg.get("_设置页_右区_预览框_偏移"), (0, 0))
            cfg["_设置页_右区_预览框_偏移"] = (int(x + dx), int(y + dy))
        elif 对象 == "左箭":
            x, y = _转tuple2(cfg.get("_设置页_右区_左大箭头_偏移"), (0, 0))
            cfg["_设置页_右区_左大箭头_偏移"] = (int(x + dx), int(y + dy))
        elif 对象 == "右箭":
            x, y = _转tuple2(cfg.get("_设置页_右区_右大箭头_偏移"), (0, 0))
            cfg["_设置页_右区_右大箭头_偏移"] = (int(x + dx), int(y + dy))

    def _缩放对象(对象: str, dv: float, mod: int):
        if 对象 == "预览":
            if mod & pygame.KMOD_SHIFT:
                cfg["_设置页_右区_预览框_宽缩放"] = float(
                    max(
                        0.2,
                        min(3.0, float(cfg.get("_设置页_右区_预览框_宽缩放", 1.0)) + dv),
                    )
                )
                return
            if mod & pygame.KMOD_CTRL:
                cfg["_设置页_右区_预览框_高缩放"] = float(
                    max(
                        0.2,
                        min(3.0, float(cfg.get("_设置页_右区_预览框_高缩放", 1.0)) + dv),
                    )
                )
                return
            cfg["_设置页_右区_预览框_宽缩放"] = float(
                max(
                    0.2,
                    min(3.0, float(cfg.get("_设置页_右区_预览框_宽缩放", 1.0)) + dv),
                )
            )
            cfg["_设置页_右区_预览框_高缩放"] = float(
                max(
                    0.2,
                    min(3.0, float(cfg.get("_设置页_右区_预览框_高缩放", 1.0)) + dv),
                )
            )
            return

        if 对象 == "左箭":
            cfg["_设置页_右区_左大箭头_缩放"] = float(
                max(
                    0.3,
                    min(3.0, float(cfg.get("_设置页_右区_左大箭头_缩放", 1.0)) + dv),
                )
            )
            return
        if 对象 == "右箭":
            cfg["_设置页_右区_右大箭头_缩放"] = float(
                max(
                    0.3,
                    min(3.0, float(cfg.get("_设置页_右区_右大箭头_缩放", 1.0)) + dv),
                )
            )
            return

    运行 = True
    while 运行:
        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                运行 = False
                break
            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    运行 = False
                    break
                if 事件.key == pygame.K_1:
                    选中对象 = "预览"
                elif 事件.key == pygame.K_2:
                    选中对象 = "左箭"
                elif 事件.key == pygame.K_3:
                    选中对象 = "右箭"
                elif 事件.key == pygame.K_TAB:
                    顺序 = ["预览", "左箭", "右箭"]
                    idx = (顺序.index(选中对象) + 1) % len(顺序)
                    选中对象 = 顺序[idx]
                elif 事件.key == pygame.K_g:
                    显示基准框 = not bool(显示基准框)
                elif 事件.key == pygame.K_s:
                    if _保存配置(配置路径, cfg):
                        _提示("已保存到 json/设置页布局覆盖.json", 1.4)
                    else:
                        _提示("保存失败", 1.4)
                elif 事件.key == pygame.K_r:
                    cfg = _读取配置(配置路径)
                    _提示("已从文件重载", 1.1)
                elif 事件.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                    步进 = 10 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 1
                    dx, dy = 0, 0
                    if 事件.key == pygame.K_LEFT:
                        dx = -步进
                    elif 事件.key == pygame.K_RIGHT:
                        dx = 步进
                    elif 事件.key == pygame.K_UP:
                        dy = -步进
                    elif 事件.key == pygame.K_DOWN:
                        dy = 步进
                    _移动对象(选中对象, dx, dy)
                elif 事件.key in (pygame.K_q, pygame.K_e):
                    符号 = -1.0 if 事件.key == pygame.K_q else 1.0
                    步进 = 0.08 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 0.02
                    _缩放对象(选中对象, 符号 * 步进, pygame.key.get_mods())
                elif 事件.key in (pygame.K_COMMA, pygame.K_PERIOD):
                    if 预览图路径列表:
                        if 事件.key == pygame.K_COMMA:
                            当前预览索引 = (当前预览索引 - 1) % len(预览图路径列表)
                        else:
                            当前预览索引 = (当前预览索引 + 1) % len(预览图路径列表)
                        _更新预览图()

            elif 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
                布局 = _计算布局(*屏幕.get_size(), cfg)
                命中 = None
                for 名称 in ("预览", "左箭", "右箭"):
                    if 布局[名称].collidepoint(事件.pos):
                        命中 = 名称
                        break
                if 命中:
                    选中对象 = 命中
                    拖拽中 = True
                    上次鼠标 = (int(事件.pos[0]), int(事件.pos[1]))
            elif 事件.type == pygame.MOUSEBUTTONUP and 事件.button == 1:
                拖拽中 = False
            elif 事件.type == pygame.MOUSEMOTION and 拖拽中:
                当前 = (int(事件.pos[0]), int(事件.pos[1]))
                dx = int(当前[0] - 上次鼠标[0])
                dy = int(当前[1] - 上次鼠标[1])
                _移动对象(选中对象, dx, dy)
                上次鼠标 = 当前
            elif 事件.type == pygame.MOUSEWHEEL:
                步进 = 0.08 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 0.02
                _缩放对象(
                    选中对象, float(事件.y) * 步进, pygame.key.get_mods()
                )

        屏宽, 屏高 = 屏幕.get_size()
        if 选歌背景图 is not None:
            try:
                bg = pygame.transform.smoothscale(选歌背景图, (屏宽, 屏高)).convert()
                屏幕.blit(bg, (0, 0))
            except Exception:
                屏幕.fill((18, 26, 36))
        else:
            屏幕.fill((18, 26, 36))
        暗层 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
        暗层.fill((0, 0, 0, 130))
        屏幕.blit(暗层, (0, 0))

        布局 = _计算布局(屏宽, 屏高, cfg)
        面板 = 布局["面板"]
        if 设置背景图 is not None:
            try:
                panel_img = pygame.transform.smoothscale(设置背景图, (面板.w, 面板.h)).convert_alpha()
                屏幕.blit(panel_img, 面板.topleft)
            except Exception:
                pygame.draw.rect(屏幕, (16, 32, 74), 面板, border_radius=14)
        else:
            pygame.draw.rect(屏幕, (16, 32, 74), 面板, border_radius=14)

        if 预览图 is not None:
            try:
                绘制_cover裁切预览(屏幕, 预览图, 布局["预览"])
            except Exception:
                pygame.draw.rect(屏幕, (35, 55, 90), 布局["预览"])
        else:
            pygame.draw.rect(屏幕, (35, 55, 90), 布局["预览"])
        if 左箭图 is not None:
            try:
                图 = pygame.transform.smoothscale(左箭图, (布局["左箭"].w, 布局["左箭"].h)).convert_alpha()
                屏幕.blit(图, 布局["左箭"].topleft)
            except Exception:
                pass
        if 右箭图 is not None:
            try:
                图 = pygame.transform.smoothscale(右箭图, (布局["右箭"].w, 布局["右箭"].h)).convert_alpha()
                屏幕.blit(图, 布局["右箭"].topleft)
            except Exception:
                pass

        颜色映射 = {
            "预览": (255, 225, 120),
            "左箭": (120, 240, 170),
            "右箭": (120, 220, 255),
        }
        for 名称 in ("预览", "左箭", "右箭"):
            rect = 布局[名称]
            c = 颜色映射[名称]
            pygame.draw.rect(屏幕, c, rect, width=3 if 名称 == 选中对象 else 1)

        if 显示基准框:
            pygame.draw.rect(屏幕, (180, 180, 210), 布局["右区"], width=1)
            标签图 = 小字.render("右区基准框", True, (190, 190, 215))
            屏幕.blit(标签图, (布局["右区"].x + 4, 布局["右区"].y - 20))

        面板信息 = [
            f"当前选中: {选中对象}",
            f"预览偏移: {cfg.get('_设置页_右区_预览框_偏移')}  宽缩放: {float(cfg.get('_设置页_右区_预览框_宽缩放', 1.0)):.2f}  高缩放: {float(cfg.get('_设置页_右区_预览框_高缩放', 1.0)):.2f}",
            f"左箭 偏移: {cfg.get('_设置页_右区_左大箭头_偏移')}  缩放: {float(cfg.get('_设置页_右区_左大箭头_缩放', 1.0)):.2f}",
            f"右箭 偏移: {cfg.get('_设置页_右区_右大箭头_偏移')}  缩放: {float(cfg.get('_设置页_右区_右大箭头_缩放', 1.0)):.2f}",
            "按键: 1/2/3选对象, 鼠标拖拽移动, 滚轮缩放, Shift+滚轮大步进, Shift+滚轮(预览)=仅宽, Ctrl+滚轮(预览)=仅高",
            "按键: Q/E缩放, ←↑↓→移动, S保存, R重载, G显示/隐藏基准框, ,/.切换预览图",
        ]
        y = 12
        for line in 面板信息:
            图 = 小字.render(str(line), True, (235, 240, 255)).convert_alpha()
            屏幕.blit(图, (12, y))
            y += 图.get_height() + 4

        if (pygame.time.get_ticks() / 1000.0) < float(提示截止):
            t = 字体.render(提示, True, (255, 235, 160)).convert_alpha()
            屏幕.blit(t, (12, 屏高 - t.get_height() - 10))

        pygame.display.flip()
        时钟.tick(120)

    pygame.quit()


if __name__ == "__main__":
    主函数()
