import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pygame
from ui.settlement_layout_shared import (
    DESIGN_SIZE,
    SettlementLayoutStore,
    process_layer_ids,
)


Color = Tuple[int, int, int]
RectLike = Tuple[int, int, int, int]


def _project_root() -> str:
    candidates: List[str] = []
    try:
        if getattr(sys, "frozen", False):
            candidates.append(os.path.dirname(os.path.abspath(sys.executable)))
        else:
            candidates.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    candidates.append(os.getcwd())
    for start in candidates:
        current = os.path.abspath(start)
        for _ in range(12):
            if os.path.isdir(os.path.join(current, "core")) and os.path.isdir(
                os.path.join(current, "scenes")
            ):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
    return os.path.abspath(candidates[0] if candidates else ".")


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _ease_out_cubic(t: float) -> float:
    x = 1.0 - _clamp(t, 0.0, 1.0)
    return 1.0 - x * x * x


def _back_out(t: float) -> float:
    x = _clamp(t, 0.0, 1.0)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * pow(x - 1.0, 3) + c1 * pow(x - 1.0, 2)


def _read_json(path: str) -> dict:
    if not path or not os.path.isfile(path):
        return {}
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(path, "r", encoding=encoding) as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except Exception:
            continue
    return {}


def _write_json(path: str, data: dict):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _safe_load_image(path: str, use_alpha: bool = True) -> Optional[pygame.Surface]:
    try:
        if path and os.path.isfile(path):
            surface = pygame.image.load(path)
            return surface.convert_alpha() if use_alpha else surface.convert()
    except Exception:
        pass
    return None


def _get_font(size: int, bold: bool = False) -> pygame.font.Font:
    try:
        from core.工具 import 获取字体  # type: ignore

        return 获取字体(int(size), 是否粗体=bool(bold))
    except Exception:
        pygame.font.init()
        try:
            return pygame.font.SysFont("Microsoft YaHei", int(size), bold=bool(bold))
        except Exception:
            return pygame.font.Font(None, int(size))


def _parse_color(value: Any, fallback: Color) -> Color:
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return (
                int(_clamp(float(value[0]), 0, 255)),
                int(_clamp(float(value[1]), 0, 255)),
                int(_clamp(float(value[2]), 0, 255)),
            )
        except Exception:
            return fallback
    if isinstance(value, str):
        text = value.strip().lstrip("#")
        if len(text) == 6:
            try:
                return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
            except Exception:
                return fallback
    return fallback


def _color_text(color: Color) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def _load_preview_profile(root: str) -> Tuple[Optional[pygame.Surface], str, Optional[str], dict]:
    path = os.path.join(root, "UI-img", "个人中心-个人资料", "个人资料.json")
    data = _read_json(path)
    nickname = str(data.get("昵称", "") or "玩家")
    progress = data.get("进度", {}) if isinstance(data.get("进度"), dict) else {}
    avatar_path = str(data.get("头像文件", "") or "")
    rank_path = str(progress.get("段位", "") or "")
    avatar_surface = None
    if avatar_path:
        if not os.path.isabs(avatar_path):
            avatar_path = os.path.join(root, avatar_path.replace("/", os.sep).replace("\\", os.sep))
        avatar_surface = _safe_load_image(avatar_path)
    if rank_path and not os.path.isabs(rank_path):
        rank_path = os.path.join(root, rank_path.replace("/", os.sep).replace("\\", os.sep))
    return avatar_surface, nickname, rank_path if rank_path else None, progress


def _fit_size(src_size: Tuple[int, int], dst_size: Tuple[int, int], mode: str) -> Tuple[int, int]:
    sw, sh = src_size
    dw, dh = max(1, int(dst_size[0])), max(1, int(dst_size[1]))
    if sw <= 0 or sh <= 0:
        return (dw, dh)
    if mode == "stretch":
        return (dw, dh)
    if mode == "none":
        return (sw, sh)
    scale = min(dw / float(sw), dh / float(sh))
    if mode == "cover":
        scale = max(dw / float(sw), dh / float(sh))
    return (max(1, int(round(sw * scale))), max(1, int(round(sh * scale))))


def _render_text_surface(
    text: str,
    size: int,
    color: Color,
    bold: bool = False,
    stroke_color: Color = (0, 0, 0),
    stroke_width: int = 0,
    letter_spacing: int = 0,
) -> pygame.Surface:
    font = _get_font(max(8, int(size)), bold=bool(bold))
    text = str(text or "")
    if not text:
        return pygame.Surface((1, 1), pygame.SRCALPHA)
    glyphs: List[pygame.Surface] = []
    for char in text:
        glyphs.append(font.render(char, True, color).convert_alpha())
    total_width = sum(g.get_width() for g in glyphs) + max(0, len(glyphs) - 1) * int(letter_spacing)
    total_height = max((g.get_height() for g in glyphs), default=max(1, size))
    stroke = max(0, int(stroke_width))
    canvas = pygame.Surface((max(1, total_width + stroke * 2), max(1, total_height + stroke * 2)), pygame.SRCALPHA)
    if stroke > 0:
        stroke_glyphs = [font.render(char, True, stroke_color).convert_alpha() for char in text]
        x = stroke
        for glyph in stroke_glyphs:
            for ox in range(-stroke, stroke + 1):
                for oy in range(-stroke, stroke + 1):
                    if ox == 0 and oy == 0:
                        continue
                    canvas.blit(glyph, (x + ox, stroke + oy))
            x += glyph.get_width() + int(letter_spacing)
    x = stroke
    for glyph in glyphs:
        canvas.blit(glyph, (x, stroke))
        x += glyph.get_width() + int(letter_spacing)
    return canvas


@dataclass
class DebugPanel:
    panel_id: str
    title: str
    rect: pygame.Rect
    collapsed: bool = False
    hidden: bool = False


class SettlementLayoutDebugger:
    layout_version = 1

    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("结算场景布局调试器")
        self.root = _project_root()
        self.layout_path = os.path.join(self.root, "json", "结算场景布局.json")
        self.settings_path = os.path.join(self.root, "json", "结算场景布局调试器_设置.json")
        self.design_size = (int(DESIGN_SIZE[0]), int(DESIGN_SIZE[1]))
        self.screen = pygame.display.set_mode(self.design_size, pygame.RESIZABLE)
        self.canvas = pygame.Surface(self.design_size).convert_alpha()
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_small = _get_font(16, False)
        self.font_body = _get_font(18, False)
        self.font_body_bold = _get_font(18, True)
        self.font_title = _get_font(22, True)

        self.message = ""
        self.message_until = 0
        self.layer_scroll = 0
        self.last_click_ticks = 0
        self.last_click_layer_id = ""
        self.selection_mode = "layout"
        self.selected_ids: List[str] = []
        self.active_layer_id = ""
        self.dragging = False
        self.drag_start = (0, 0)
        self.drag_origin_rects: Dict[str, Tuple[int, int, int, int]] = {}
        self.drag_origin_offset = (0.0, 0.0)
        self.dragging_panel_id: Optional[str] = None
        self.panel_drag_origin = (0, 0)
        self.panel_origin_rect = pygame.Rect(0, 0, 0, 0)

        self.numbers_duration = 2.5
        self.grade_duration = 0.2
        self.top_duration = 0.3
        self.reward_start = self.numbers_duration + self.grade_duration + self.top_duration + 0.25
        self.reward_duration = 0.32
        self.upgrade_duration = 0.9
        self.prompt_duration = 0.45
        self.selected_process = 1
        self.process_playing = False
        self.process_time = 0.0
        self.global_time = 0.0
        self.numbers_time = 0.0
        self.level_time = 0.0
        self.prompt_time = 0.0

        self.show_bounds = True
        self.show_names = True
        self.show_help = True

        self.text_editor_open = False
        self.text_editor_layer_id = ""
        self.text_editor_fields: List[Dict[str, Any]] = []
        self.active_text_field = ""

        self.assets: Dict[str, Optional[pygame.Surface]] = {}
        self.prompt_assets: Dict[str, pygame.Surface] = {}
        self.scale_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}
        self.placeholder_cache: Dict[Tuple[str, int, int], pygame.Surface] = {}
        self.payload = self._build_preview_payload()
        self.panels = self._create_panels()
        self._load_assets()
        self.layout_store = SettlementLayoutStore(self.layout_path)
        self.layers = self.layout_store.layers
        self._restore_settings()
        self._set_process(self.selected_process, replay=False)

    def _create_panels(self) -> Dict[str, DebugPanel]:
        screen_w, screen_h = self.screen.get_size()
        return {
            "visual": DebugPanel("visual", "视觉面板", pygame.Rect(18, 18, 280, 126)),
            "badge": DebugPanel("badge", "顶部标面板", pygame.Rect(18, 152, 280, 126)),
            "function": DebugPanel("function", "流程面板", pygame.Rect(18, screen_h - 172, 320, 150)),
            "layers": DebugPanel("layers", "图层面板", pygame.Rect(screen_w - 370, screen_h - 402, 352, 384)),
        }

    def _build_preview_payload(self) -> dict:
        avatar_surface, nickname, rank_path, progress = _load_preview_profile(self.root)
        loading_data = _read_json(os.path.join(self.root, "json", "加载页.json"))
        cover_path = str(loading_data.get("封面路径", "") or "")
        if cover_path and not os.path.isabs(cover_path):
            cover_path = os.path.join(self.root, cover_path.replace("/", os.sep).replace("\\", os.sep))
        style_progress = progress.get("花式", {}) if isinstance(progress.get("花式"), dict) else {}
        speed_progress = progress.get("竞速", {}) if isinstance(progress.get("竞速"), dict) else {}
        return {
            "歌名": str(loading_data.get("歌曲名", "") or "Korean Girls Pop Song Party"),
            "封面路径": cover_path,
            "星级": int(loading_data.get("星级", 7) or 7),
            "评级": "S",
            "三把S": True,
            "新纪录": True,
            "顶标": "全连",
            "玩家昵称": nickname,
            "头像": avatar_surface,
            "miss": 2,
            "good": 9,
            "cool": 112,
            "perfect": 368,
            "combo": 1318,
            "score": 47764801,
            "accuracy": 98.76,
            "经验增加值": 10,
            "花式等级": int(style_progress.get("等级", 4) or 4),
            "花式经验": float(style_progress.get("经验", 0.2) or 0.2),
            "竞速等级": int(speed_progress.get("等级", 6) or 6),
            "竞速经验": float(speed_progress.get("经验", 0.6) or 0.6),
            "段位路径": rank_path or os.path.join(self.root, "UI-img", "个人中心-个人资料", "等级", "1.png"),
            "显示升级": True,
            "流程3提示": "下一把",
        }

    def _load_assets(self):
        root = self.root
        self.assets = {
            "background": _safe_load_image(os.path.join(root, "冷资源", "backimages", "选歌界面.png"), False),
            "panel": _safe_load_image(os.path.join(root, "UI-img", "游戏界面", "结算", "结算背景通用.png")),
            "cover": _safe_load_image(str(self.payload.get("封面路径", "") or "")),
            "grade_s": _safe_load_image(os.path.join(root, "UI-img", "游戏界面", "结算", "评价", "s.png")),
            "top_full_combo": _safe_load_image(os.path.join(root, "UI-img", "游戏界面", "结算", "评价", "全连.png")),
            "top_fail": _safe_load_image(os.path.join(root, "UI-img", "游戏界面", "结算", "评价", "失败.png")),
            "top_three_s": _safe_load_image(os.path.join(root, "UI-img", "游戏界面", "结算", "评价", "三把全连.png")),
            "new_record": _safe_load_image(os.path.join(root, "UI-img", "游戏界面", "结算", "新纪录.png")),
            "reward_bg": _safe_load_image(os.path.join(root, "UI-img", "游戏界面", "结算", "结算等级小窗", "UI_I516.png")),
            "style_frame": _safe_load_image(os.path.join(root, "UI-img", "经验条", "花式经验-框.png")),
            "style_fill": _safe_load_image(os.path.join(root, "UI-img", "经验条", "花式经验-值.png")),
            "speed_frame": _safe_load_image(os.path.join(root, "UI-img", "经验条", "竞速经验-框.png")),
            "speed_fill": _safe_load_image(os.path.join(root, "UI-img", "经验条", "竞速经验-值.png")),
            "rank": _safe_load_image(str(self.payload.get("段位路径", "") or "")),
            "upgrade_center": _safe_load_image(
                os.path.join(root, "UI-img", "游戏界面", "结算", "结算等级小窗", "升级动画素材", "升级.png")
            ),
            "upgrade_lt": _safe_load_image(
                os.path.join(root, "UI-img", "游戏界面", "结算", "结算等级小窗", "升级动画素材", "左上.png")
            ),
            "upgrade_rt": _safe_load_image(
                os.path.join(root, "UI-img", "游戏界面", "结算", "结算等级小窗", "升级动画素材", "右上.png")
            ),
            "upgrade_lb": _safe_load_image(
                os.path.join(root, "UI-img", "游戏界面", "结算", "结算等级小窗", "升级动画素材", "左下.png")
            ),
            "upgrade_rb": _safe_load_image(
                os.path.join(root, "UI-img", "游戏界面", "结算", "结算等级小窗", "升级动画素材", "右下.png")
            ),
        }
        digits_dir = os.path.join(root, "UI-img", "游戏界面", "结算", "结算等级小窗", "经验数字")
        for name in ["+", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            self.assets[f"digit_{name}"] = _safe_load_image(os.path.join(digits_dir, f"{name}.png"))
        self.prompt_assets = {}
        prompt_dir = os.path.join(root, "UI-img", "游戏界面", "结算", "提示")
        for name in ["下一把", "继续挑战", "是否续币", "游戏结束", "赠送一把"]:
            image = _safe_load_image(os.path.join(prompt_dir, f"{name}.png"))
            if image is not None:
                self.prompt_assets[name] = image

    def _load_or_create_layout(self) -> Dict[str, Dict[str, Any]]:
        data = _read_json(self.layout_path)
        layers = data.get("layers") if isinstance(data.get("layers"), dict) else {}
        if not layers:
            layers = self._default_layout()
            _write_json(
                self.layout_path,
                {"version": self.layout_version, "layers": layers},
            )
            return layers
        normalized: Dict[str, Dict[str, Any]] = {}
        for layer_id, layer in layers.items():
            if isinstance(layer, dict):
                normalized[str(layer_id)] = dict(layer)
        return normalized or self._default_layout()

    def _panel_rect(self) -> pygame.Rect:
        screen_w, screen_h = self.screen.get_size()
        size = int(min(max(360, screen_h * 0.82), screen_w * 0.48, 700))
        return pygame.Rect(max(28, int(screen_w * 0.06)), max(20, (screen_h - size) // 2), size, size)

    def _ref_rect(self, panel: pygame.Rect, x: float, y: float, w: float, h: float) -> List[int]:
        return [
            int(panel.left + panel.w * (x / 512.0)),
            int(panel.top + panel.h * (y / 512.0)),
            int(panel.w * (w / 512.0)),
            int(panel.h * (h / 512.0)),
        ]

    def _default_layout(self) -> Dict[str, Dict[str, Any]]:
        screen_w, screen_h = self.screen.get_size()
        panel = self._panel_rect()
        reward_rect = pygame.Rect(min(screen_w - 24 - 576, panel.right + 24), int(panel.centery - 288 / 2), 576, 288)
        main_grade_w = int(panel.w * 0.25)
        main_grade_h = int(panel.h * 0.21)
        main_grade_center = (
            int(panel.left + panel.w * (100.0 / 512.0)),
            int(panel.top + panel.h * (425.0 / 512.0)),
        )
        side_gap = int(main_grade_w * 0.82)
        top_badge_w = int(panel.w * 0.72)
        top_badge_h = int(panel.h * 0.12)
        new_record_w = int(max(120, panel.w * 0.42))
        new_record_h = int(max(40, panel.h * 0.10))
        def image_layer(
            layer_id: str,
            name: str,
            rect: RectLike,
            asset: str,
            z: int,
            fit: str = "contain",
            visible: bool = True,
            group: str = "",
        ) -> Dict[str, Any]:
            return {
                "id": layer_id,
                "name": name,
                "kind": "image",
                "asset": asset,
                "rect": list(rect),
                "z": z,
                "visible": visible,
                "fit": fit,
                "content_scale": [1.0, 1.0],
                "content_offset": [0.0, 0.0],
                "group": group,
            }

        def text_layer(
            layer_id: str,
            name: str,
            rect: RectLike,
            text_key: str,
            z: int,
            value_type: str = "text",
            color: Color = (255, 255, 255),
            stroke_color: Color = (0, 0, 0),
            stroke_width: int = 0,
            font_size: int = 24,
            bold: bool = False,
            letter_spacing: int = 0,
            align: str = "center",
            visible: bool = True,
            group: str = "",
        ) -> Dict[str, Any]:
            return {
                "id": layer_id,
                "name": name,
                "kind": "text",
                "rect": list(rect),
                "z": z,
                "visible": visible,
                "group": group,
                "text_key": text_key,
                "value_type": value_type,
                "content_scale": [1.0, 1.0],
                "content_offset": [0.0, 0.0],
                "fit": "none",
                "text_style": {
                    "font_size": font_size,
                    "bold": bold,
                    "color": list(color),
                    "stroke_color": list(stroke_color),
                    "stroke_width": stroke_width,
                    "letter_spacing": letter_spacing,
                    "align": align,
                },
            }

        layers = {
            "background": image_layer("background", "背景图", (0, 0, screen_w, screen_h), "background", 0, "cover"),
            "dimmer": {
                "id": "dimmer",
                "name": "背景压暗",
                "kind": "shape",
                "rect": [0, 0, screen_w, screen_h],
                "z": 5,
                "visible": True,
                "fill_color": [0, 0, 0, 120],
                "group": "",
            },
            "panel": image_layer("panel", "结算面板", tuple(panel), "panel", 10, "stretch"),
            "cover": image_layer("cover", "封面区", tuple(self._ref_rect(panel, 58, 138, 126, 134)), "cover", 20, "cover"),
            "stars": text_layer(
                "stars", "星级", tuple(self._ref_rect(panel, 48, 304, 150, 28)), "星级", 22,
                value_type="stars", color=(242, 223, 60), font_size=24, align="left"
            ),
            "song_title": text_layer(
                "song_title", "歌名", tuple(self._ref_rect(panel, 46, 332, 168, 38)), "歌名", 23,
                font_size=26, align="left"
            ),
            "miss": text_layer(
                "miss", "MISS", tuple(self._ref_rect(panel, 285, 129, 160, 40)), "miss", 24,
                value_type="number", color=(255, 255, 255), stroke_color=(166, 19, 27), stroke_width=1,
                font_size=42, align="right"
            ),
            "good": text_layer(
                "good", "GOOD", tuple(self._ref_rect(panel, 285, 176, 160, 40)), "good", 24,
                value_type="number", color=(255, 255, 255), stroke_color=(49, 74, 25), stroke_width=1,
                font_size=42, align="right"
            ),
            "cool": text_layer(
                "cool", "COOL", tuple(self._ref_rect(panel, 285, 223, 160, 40)), "cool", 24,
                value_type="number", color=(255, 255, 255), stroke_color=(12, 9, 69), stroke_width=1,
                font_size=42, align="right"
            ),
            "perfect": text_layer(
                "perfect", "PERFECT", tuple(self._ref_rect(panel, 285, 271, 160, 40)), "perfect", 24,
                value_type="number", color=(255, 255, 255), stroke_color=(113, 19, 61), stroke_width=1,
                font_size=42, align="right"
            ),
            "combo": text_layer(
                "combo", "COMBO", tuple(self._ref_rect(panel, 285, 318, 160, 40)), "combo", 24,
                value_type="number", color=(255, 255, 255), stroke_color=(56, 33, 113), stroke_width=1,
                font_size=42, align="right"
            ),
            "accuracy": text_layer(
                "accuracy", "准确率", tuple(self._ref_rect(panel, 250, 372, 195, 40)), "accuracy", 24,
                value_type="percent", color=(255, 255, 255), stroke_color=(223, 193, 61), stroke_width=1,
                font_size=42, align="right"
            ),
            "score": text_layer(
                "score", "总分", tuple(self._ref_rect(panel, 230, 428, 220, 48)), "score", 24,
                value_type="number", font_size=44, align="center"
            ),
            "grade_left": image_layer(
                "grade_left",
                "评级左",
                (main_grade_center[0] - side_gap - int(main_grade_w * 0.34), main_grade_center[1] - int(main_grade_h * 0.28), int(main_grade_w * 0.68), int(main_grade_h * 0.68)),
                "grade_s",
                30,
            ),
            "grade_main": image_layer(
                "grade_main",
                "评级主",
                (main_grade_center[0] - main_grade_w // 2, main_grade_center[1] - main_grade_h // 2, main_grade_w, main_grade_h),
                "grade_s",
                31,
            ),
            "grade_right": image_layer(
                "grade_right",
                "评级右",
                (main_grade_center[0] + side_gap - int(main_grade_w * 0.34), main_grade_center[1] - int(main_grade_h * 0.28), int(main_grade_w * 0.68), int(main_grade_h * 0.68)),
                "grade_s",
                30,
            ),
            "top_badge": image_layer(
                "top_badge",
                "顶部标",
                (panel.centerx - top_badge_w // 2, int(panel.top + panel.h * 0.10) - top_badge_h // 2, top_badge_w, top_badge_h),
                "top_full_combo",
                40,
            ),
            "new_record": image_layer(
                "new_record",
                "新纪录",
                (panel.right - int(panel.w * 0.04) - new_record_w // 2, int(panel.top + panel.h * 0.11) - new_record_h // 2, new_record_w, new_record_h),
                "new_record",
                41,
            ),
            "reward_bg": image_layer("reward_bg", "等级小框", tuple(reward_rect), "reward_bg", 50, "stretch", group="reward"),
            "reward_digits": image_layer(
                "reward_digits",
                "经验数字",
                (reward_rect.x + int(reward_rect.w * 0.09), reward_rect.y + int(reward_rect.h * 0.06), int(reward_rect.w * 0.24), int(reward_rect.h * 0.28)),
                "digits",
                54,
                group="reward",
            ),
            "style_label": text_layer(
                "style_label", "花式标签", (reward_rect.x + 16, reward_rect.y + int(reward_rect.h * 0.40), 80, 32), "花式", 55,
                font_size=18, align="left", group="reward"
            ),
            "style_fill": image_layer(
                "style_fill", "花式经验值", (reward_rect.x + int(reward_rect.w * 0.18), reward_rect.y + int(reward_rect.h * 0.425), int(reward_rect.w * 0.58), int(reward_rect.h * 0.08)), "style_fill", 56, "stretch", group="reward"
            ),
            "style_frame": image_layer(
                "style_frame", "花式经验框", (reward_rect.x + int(reward_rect.w * 0.18), reward_rect.y + int(reward_rect.h * 0.425), int(reward_rect.w * 0.58), int(reward_rect.h * 0.08)), "style_frame", 57, "stretch", group="reward"
            ),
            "style_lv": text_layer(
                "style_lv", "花式等级", (reward_rect.x + int(reward_rect.w * 0.79), reward_rect.y + int(reward_rect.h * 0.40), 110, 34), "花式等级", 58,
                value_type="level", font_size=22, align="left", group="reward"
            ),
            "speed_label": text_layer(
                "speed_label", "竞速标签", (reward_rect.x + 16, reward_rect.y + int(reward_rect.h * 0.56), 80, 32), "竞速", 55,
                font_size=18, align="left", group="reward"
            ),
            "speed_fill": image_layer(
                "speed_fill", "竞速经验值", (reward_rect.x + int(reward_rect.w * 0.18), reward_rect.y + int(reward_rect.h * 0.585), int(reward_rect.w * 0.58), int(reward_rect.h * 0.08)), "speed_fill", 56, "stretch", group="reward"
            ),
            "speed_frame": image_layer(
                "speed_frame", "竞速经验框", (reward_rect.x + int(reward_rect.w * 0.18), reward_rect.y + int(reward_rect.h * 0.585), int(reward_rect.w * 0.58), int(reward_rect.h * 0.08)), "speed_frame", 57, "stretch", group="reward"
            ),
            "speed_lv": text_layer(
                "speed_lv", "竞速等级", (reward_rect.x + int(reward_rect.w * 0.79), reward_rect.y + int(reward_rect.h * 0.56), 110, 34), "竞速等级", 58,
                value_type="level", font_size=22, align="left", group="reward"
            ),
            "rank_icon": image_layer(
                "rank_icon", "段位图标", (reward_rect.x + int(reward_rect.w * 0.12), reward_rect.y + int(reward_rect.h * 0.68), int(reward_rect.h * 0.28), int(reward_rect.h * 0.28)), "rank", 58, group="reward"
            ),
            "rank_label": text_layer(
                "rank_label", "段位文字", (reward_rect.x + int(reward_rect.w * 0.29), reward_rect.y + int(reward_rect.h * 0.72), 160, 34), "当前段位", 58,
                font_size=22, align="left", group="reward"
            ),
            "upgrade_center": image_layer(
                "upgrade_center", "升级中", (reward_rect.centerx - 86, reward_rect.y + int(reward_rect.h * 0.24) - 26, 172, 52), "upgrade_center", 59, group="reward"
            ),
            "upgrade_lt": image_layer(
                "upgrade_lt", "升级左上", (reward_rect.centerx - 96, reward_rect.y + int(reward_rect.h * 0.24) - 96, 54, 54), "upgrade_lt", 58, group="reward"
            ),
            "upgrade_rt": image_layer(
                "upgrade_rt", "升级右上", (reward_rect.centerx + 42, reward_rect.y + int(reward_rect.h * 0.24) - 96, 54, 54), "upgrade_rt", 58, group="reward"
            ),
            "upgrade_lb": image_layer(
                "upgrade_lb", "升级左下", (reward_rect.centerx - 96, reward_rect.y + int(reward_rect.h * 0.24) + 42, 54, 54), "upgrade_lb", 58, group="reward"
            ),
            "upgrade_rb": image_layer(
                "upgrade_rb", "升级右下", (reward_rect.centerx + 42, reward_rect.y + int(reward_rect.h * 0.24) + 42, 54, 54), "upgrade_rb", 58, group="reward"
            ),
        }
        return layers

    def _save_layout(self):
        self.layout_store.layers = self.layers
        self.layout_store.save()

    def _restore_settings(self):
        data = _read_json(self.settings_path)
        self.show_bounds = bool(data.get("show_bounds", True))
        self.show_names = bool(data.get("show_names", True))
        self.show_help = bool(data.get("show_help", True))
        for key, panel in self.panels.items():
            entry = data.get("panels", {}).get(key, {}) if isinstance(data.get("panels"), dict) else {}
            if isinstance(entry, dict):
                rect = entry.get("rect", [])
                if isinstance(rect, list) and len(rect) == 4:
                    panel.rect = pygame.Rect(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
                panel.collapsed = bool(entry.get("collapsed", panel.collapsed))
                panel.hidden = bool(entry.get("hidden", False))

    def _save_settings(self):
        _write_json(
            self.settings_path,
            {
                "show_bounds": self.show_bounds,
                "show_names": self.show_names,
                "show_help": self.show_help,
                "panels": {
                    key: {
                        "rect": [panel.rect.x, panel.rect.y, panel.rect.w, panel.rect.h],
                        "collapsed": panel.collapsed,
                        "hidden": panel.hidden,
                    }
                    for key, panel in self.panels.items()
                },
            },
        )

    def _set_message(self, text: str, seconds: float = 1.4):
        self.message = str(text or "")
        self.message_until = pygame.time.get_ticks() + int(seconds * 1000)

    def _reset_layout(self):
        self.layout_store.reset()
        self.layers = self.layout_store.layers
        self.selection_mode = "layout"
        self.selected_ids.clear()
        self.active_layer_id = ""
        self._set_message("已重置结算布局")

    def _sorted_layers(self) -> List[Dict[str, Any]]:
        return sorted(self.layers.values(), key=lambda layer: (int(layer.get("z", 0)), str(layer.get("id", ""))))

    def _process_duration(self, process_index: int) -> float:
        if int(process_index) == 1:
            return self.numbers_duration + self.grade_duration + self.top_duration + 0.35
        if int(process_index) == 2:
            return 0.15 + self.upgrade_duration
        return self.prompt_duration

    def _process_static_time(self, process_index: int) -> float:
        return self._process_duration(process_index)

    def _set_process(self, process_index: int, replay: bool = False):
        self.selected_process = 1 if int(process_index) not in (1, 2, 3) else int(process_index)
        self.process_playing = bool(replay)
        self.process_time = 0.0 if replay else self._process_static_time(self.selected_process)
        self._sync_preview_timeline()
        self.selected_ids.clear()
        self.active_layer_id = ""

    def _sync_preview_timeline(self):
        if self.selected_process == 1:
            self.global_time = float(self.process_time)
            self.numbers_time = min(float(self.process_time), float(self.numbers_duration))
            self.level_time = 0.0
            self.prompt_time = 0.0
        elif self.selected_process == 2:
            self.global_time = float(self._process_static_time(1))
            self.numbers_time = float(self.numbers_duration)
            self.level_time = float(self.process_time)
            self.prompt_time = 0.0
        else:
            self.global_time = float(self._process_static_time(1))
            self.numbers_time = float(self.numbers_duration)
            self.level_time = float(self._process_static_time(2))
            self.prompt_time = float(self.process_time)

    def _process_layers(self, include_common: bool = True) -> List[Dict[str, Any]]:
        allowed = process_layer_ids(self.selected_process, include_common=include_common)
        return [layer for layer in self._sorted_layers() if str(layer.get("id", "")) in allowed]

    def _current_prompt_surface(self) -> Optional[pygame.Surface]:
        key = str(self.payload.get("流程3提示", "") or "下一把")
        return self.prompt_assets.get(key) or next(iter(self.prompt_assets.values()), None)

    def _preview_rect(self) -> pygame.Rect:
        screen_w, screen_h = self.screen.get_size()
        design_w, design_h = self.design_size
        scale = min(screen_w / float(design_w), screen_h / float(design_h))
        width = max(1, int(round(design_w * scale)))
        height = max(1, int(round(design_h * scale)))
        return pygame.Rect((screen_w - width) // 2, (screen_h - height) // 2, width, height)

    def _screen_to_canvas_pos(
        self, pos: Tuple[int, int], clamp_to_viewport: bool = False
    ) -> Optional[Tuple[int, int]]:
        viewport = self._preview_rect()
        if clamp_to_viewport:
            px = min(max(int(pos[0]), viewport.left), viewport.right - 1)
            py = min(max(int(pos[1]), viewport.top), viewport.bottom - 1)
        else:
            px, py = int(pos[0]), int(pos[1])
            if not viewport.collidepoint(px, py):
                return None
        rel_x = (px - viewport.x) / float(max(1, viewport.w))
        rel_y = (py - viewport.y) / float(max(1, viewport.h))
        canvas_x = int(round(rel_x * self.design_size[0]))
        canvas_y = int(round(rel_y * self.design_size[1]))
        return (
            max(0, min(self.design_size[0] - 1, canvas_x)),
            max(0, min(self.design_size[1] - 1, canvas_y)),
        )

    def _layer_by_id(self, layer_id: str) -> Optional[Dict[str, Any]]:
        layer = self.layers.get(str(layer_id))
        return layer if isinstance(layer, dict) else None

    def _layer_rect(self, layer: Dict[str, Any]) -> pygame.Rect:
        rect = layer.get("rect", [0, 0, 0, 0])
        if isinstance(rect, (list, tuple)) and len(rect) == 4:
            return pygame.Rect(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        return pygame.Rect(0, 0, 0, 0)

    def _set_layer_rect(self, layer: Dict[str, Any], rect: pygame.Rect):
        layer["rect"] = [int(rect.x), int(rect.y), int(rect.w), int(rect.h)]

    def _layer_content_offset(self, layer: Dict[str, Any]) -> Tuple[float, float]:
        raw = layer.get("content_offset", [0.0, 0.0])
        if isinstance(raw, (list, tuple)) and len(raw) == 2:
            try:
                return float(raw[0]), float(raw[1])
            except Exception:
                return (0.0, 0.0)
        return (0.0, 0.0)

    def _set_layer_content_offset(self, layer: Dict[str, Any], offset: Tuple[float, float]):
        layer["content_offset"] = [float(offset[0]), float(offset[1])]

    def _layer_content_scale(self, layer: Dict[str, Any]) -> Tuple[float, float]:
        raw = layer.get("content_scale", [1.0, 1.0])
        if isinstance(raw, (list, tuple)) and len(raw) == 2:
            try:
                return max(0.05, float(raw[0])), max(0.05, float(raw[1]))
            except Exception:
                return (1.0, 1.0)
        return (1.0, 1.0)

    def _set_layer_content_scale(self, layer: Dict[str, Any], scale: Tuple[float, float]):
        layer["content_scale"] = [max(0.05, float(scale[0])), max(0.05, float(scale[1]))]

    def _scale_image_cached(self, surface: pygame.Surface, size: Tuple[int, int]) -> pygame.Surface:
        width, height = max(1, int(size[0])), max(1, int(size[1]))
        key = (id(surface), width, height)
        cached = self.scale_cache.get(key)
        if cached is not None:
            return cached
        scaled = pygame.transform.smoothscale(surface, (width, height))
        self.scale_cache[key] = scaled
        return scaled

    def _current_numbers_progress(self) -> float:
        return _ease_out_cubic(_clamp(self.numbers_time / float(self.numbers_duration), 0.0, 1.0))

    def _reward_progress(self) -> float:
        return _clamp(self.level_time / float(self.reward_duration), 0.0, 1.0)

    def _upgrade_progress(self) -> float:
        return _clamp(max(0.0, self.level_time - 0.15) / float(self.upgrade_duration), 0.0, 1.0)

    def _format_layer_text(self, layer: Dict[str, Any]) -> str:
        key = str(layer.get("text_key", "") or "")
        style = layer.get("text_style", {}) if isinstance(layer.get("text_style"), dict) else {}
        raw = self.payload.get(key, key)
        kind = str(layer.get("value_type", "text") or "text")
        if kind == "stars":
            return "★" * max(0, int(raw or 0))
        if kind == "number":
            target = int(raw or 0)
            return str(int(round(target * self._current_numbers_progress())))
        if kind == "percent":
            target = float(raw or 0.0)
            return f"{target * self._current_numbers_progress():05.2f}%"
        if kind == "level":
            return f"Lv : {int(raw or 0)}"
        if kind == "text":
            return str(raw or "")
        return str(raw or "")

    def _get_layer_asset(self, layer: Dict[str, Any]) -> Optional[pygame.Surface]:
        asset_name = str(layer.get("asset", "") or "")
        if asset_name == "cover":
            return self.assets.get("cover")
        if asset_name == "digits":
            return None
        if asset_name == "flow3_prompt":
            return self._current_prompt_surface()
        if layer.get("id") == "top_badge":
            top_key = str(self.payload.get("顶标", "全连") or "全连")
            if top_key == "失败":
                return self.assets.get("top_fail")
            if top_key == "三把S":
                return self.assets.get("top_three_s")
            return self.assets.get("top_full_combo")
        return self.assets.get(asset_name)

    def _placeholder_surface(self, label: str, size: Tuple[int, int]) -> pygame.Surface:
        width, height = max(32, int(size[0])), max(24, int(size[1]))
        key = (str(label), width, height)
        cached = self.placeholder_cache.get(key)
        if cached is not None:
            return cached
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((18, 26, 50, 220))
        pygame.draw.rect(surface, (120, 160, 255, 220), surface.get_rect(), 1)
        text = _render_text_surface(str(label), max(14, min(24, height // 3)), (230, 235, 255), False)
        surface.blit(text, text.get_rect(center=surface.get_rect().center))
        self.placeholder_cache[key] = surface
        return surface

    def _render_digits_surface(self) -> pygame.Surface:
        text = f"+{int(self.payload.get('经验增加值', 10) or 10)}"
        glyphs: List[pygame.Surface] = []
        for char in text:
            glyph = self.assets.get(f"digit_{char}")
            if glyph is not None:
                glyphs.append(glyph)
        if not glyphs:
            return _render_text_surface(text, 36, (245, 230, 92), True, (50, 40, 0), 1)
        target_h = max(28, max(int(g.get_height()) for g in glyphs))
        total_w = 0
        scaled_glyphs: List[pygame.Surface] = []
        for glyph in glyphs:
            ratio = target_h / float(max(1, glyph.get_height()))
            size = (max(1, int(glyph.get_width() * ratio)), target_h)
            scaled = self._scale_image_cached(glyph, size)
            scaled_glyphs.append(scaled)
            total_w += scaled.get_width()
        total_w += max(0, len(scaled_glyphs) - 1) * 2
        surface = pygame.Surface((max(1, total_w), target_h), pygame.SRCALPHA)
        x = 0
        for scaled in scaled_glyphs:
            surface.blit(scaled, (x, 0))
            x += scaled.get_width() + 2
        return surface

    def _render_layer_surface(self, layer: Dict[str, Any]) -> pygame.Surface:
        kind = str(layer.get("kind", "") or "")
        if kind == "shape":
            rect = self._layer_rect(layer)
            rgba = layer.get("fill_color", [0, 0, 0, 100])
            alpha = int(rgba[3]) if isinstance(rgba, (list, tuple)) and len(rgba) > 3 else 100
            color = _parse_color(rgba, (0, 0, 0))
            surface = pygame.Surface((max(1, rect.w), max(1, rect.h)), pygame.SRCALPHA)
            surface.fill((color[0], color[1], color[2], alpha))
            return surface
        if layer.get("id") == "reward_digits":
            return self._render_digits_surface()
        if kind == "text":
            style = layer.get("text_style", {}) if isinstance(layer.get("text_style"), dict) else {}
            return _render_text_surface(
                self._format_layer_text(layer),
                int(style.get("font_size", 24) or 24),
                _parse_color(style.get("color", [255, 255, 255]), (255, 255, 255)),
                bool(style.get("bold", False)),
                _parse_color(style.get("stroke_color", [0, 0, 0]), (0, 0, 0)),
                int(style.get("stroke_width", 0) or 0),
                int(style.get("letter_spacing", 0) or 0),
            )
        asset = self._get_layer_asset(layer)
        if asset is not None:
            return asset
        return self._placeholder_surface(str(layer.get("name", "缺图")), self._layer_rect(layer).size)

    def _fit_surface_rect(self, layer: Dict[str, Any], base_rect: pygame.Rect, surface: pygame.Surface) -> pygame.Rect:
        fit_mode = str(layer.get("fit", "contain") or "contain")
        scale_x, scale_y = self._layer_content_scale(layer)
        size = _fit_size(surface.get_size(), base_rect.size, fit_mode)
        width = max(1, int(round(size[0] * scale_x)))
        height = max(1, int(round(size[1] * scale_y)))
        offset_x, offset_y = self._layer_content_offset(layer)
        style = layer.get("text_style", {}) if isinstance(layer.get("text_style"), dict) else {}
        align = str(style.get("align", "center") or "center")
        rect = pygame.Rect(0, 0, width, height)
        if align == "left":
            rect.midleft = (base_rect.left, base_rect.centery)
        elif align == "right":
            rect.midright = (base_rect.right, base_rect.centery)
        else:
            rect.center = base_rect.center
        rect.x += int(round(offset_x))
        rect.y += int(round(offset_y))
        return rect

    def _animated_layer_rect(self, layer: Dict[str, Any]) -> pygame.Rect:
        rect = self._layer_rect(layer).copy()
        layer_id = str(layer.get("id", "") or "")
        if layer_id in {"background", "dimmer"}:
            screen_w, screen_h = self.design_size
            rect.size = (screen_w, screen_h)
            rect.topleft = (0, 0)
            return rect
        if layer.get("group") == "reward":
            t = self._reward_progress()
            hidden_x = self.design_size[0] + 12
            rect.x = int(hidden_x + (rect.x - hidden_x) * _back_out(t))
        if layer_id == "grade_main":
            t = _clamp((self.global_time - self.numbers_duration) / self.grade_duration, 0.0, 1.0)
            scale = 1.0 + (1.30 - 1.0) * (1.0 - _back_out(t))
            new_size = (max(2, int(rect.w * scale)), max(2, int(rect.h * scale)))
            hidden_center_x = -new_size[0] // 2
            center_x = int(hidden_center_x + (rect.centerx - hidden_center_x) * _back_out(t))
            rect.size = new_size
            rect.center = (center_x, rect.centery)
        elif layer_id in {"grade_left", "grade_right"}:
            t = _clamp((self.global_time - self.numbers_duration) / self.grade_duration, 0.0, 1.0)
            scale = 1.0 + (1.30 - 1.0) * (1.0 - _back_out(t))
            new_size = (max(2, int(rect.w * scale)), max(2, int(rect.h * scale)))
            hidden_center_x = -new_size[0] // 2
            center_x = int(hidden_center_x + (rect.centerx - hidden_center_x) * _back_out(t))
            rect.size = new_size
            rect.center = (center_x, rect.centery)
        elif layer_id == "top_badge":
            start = self.numbers_duration + self.grade_duration
            t = _clamp((self.global_time - start) / self.top_duration, 0.0, 1.0)
            scale = 1.0 + (1.30 - 1.0) * (1.0 - _back_out(t))
            new_size = (max(2, int(rect.w * scale)), max(2, int(rect.h * scale)))
            start_y = self._layer_rect(self.layers["panel"]).top - new_size[1]
            center_y = int(start_y + (rect.centery - start_y) * _back_out(t))
            rect.size = new_size
            rect.center = (rect.centerx, center_y)
        elif layer_id == "new_record":
            start = self.numbers_duration + 0.15
            t = _clamp((self.global_time - start) / 0.28, 0.0, 1.0)
            scale = 0.86 + 0.14 * _back_out(t)
            rect.size = (max(2, int(rect.w * scale)), max(2, int(rect.h * scale)))
            rect.center = self._layer_rect(layer).center
        elif layer_id == "flow3_prompt":
            t = _clamp(self.prompt_time / float(self.prompt_duration), 0.0, 1.0)
            scale = 1.12 - 0.12 * t
            rect.size = (max(2, int(rect.w * scale)), max(2, int(rect.h * scale)))
            rect.center = self._layer_rect(layer).center
        elif layer_id.startswith("upgrade_"):
            t = self._upgrade_progress()
            if layer_id == "upgrade_center":
                scale = 1.0 + 0.06 * (1.0 - t)
                rect.size = (max(2, int(rect.w * scale)), max(2, int(rect.h * scale)))
                rect.center = self._layer_rect(layer).center
            else:
                dx = 1 if layer_id.endswith(("rt", "rb")) else -1
                dy = 1 if layer_id.endswith(("lb", "rb")) else -1
                distance = int(self._layer_rect(self.layers["reward_bg"]).h * 0.18 * _ease_out_cubic(t))
                rect.center = (self._layer_rect(layer).centerx + dx * distance, self._layer_rect(layer).centery + dy * distance)
        return rect

    def _layer_alpha(self, layer: Dict[str, Any]) -> int:
        layer_id = str(layer.get("id", "") or "")
        if layer_id in {"background", "dimmer", "panel", "cover", "stars", "song_title", "miss", "good", "cool", "perfect", "combo", "accuracy", "score"}:
            return 255
        if layer_id in {"grade_main", "grade_left", "grade_right"}:
            return int(255 * _ease_out_cubic(_clamp((self.global_time - self.numbers_duration) / self.grade_duration, 0.0, 1.0)))
        if layer_id == "top_badge":
            start = self.numbers_duration + self.grade_duration
            return int(255 * _ease_out_cubic(_clamp((self.global_time - start) / self.top_duration, 0.0, 1.0)))
        if layer_id == "new_record":
            start = self.numbers_duration + 0.15
            return int(255 * _ease_out_cubic(_clamp((self.global_time - start) / 0.28, 0.0, 1.0)))
        if layer.get("group") == "reward":
            return int(255 * _ease_out_cubic(self._reward_progress()))
        if layer_id == "flow3_prompt":
            return int(255 * _ease_out_cubic(_clamp(self.prompt_time / float(self.prompt_duration), 0.0, 1.0)))
        return 255

    def _content_rect(self, layer: Dict[str, Any], draw_rect: Optional[pygame.Rect] = None) -> pygame.Rect:
        base_rect = draw_rect.copy() if draw_rect is not None else self._animated_layer_rect(layer)
        surface = self._render_layer_surface(layer)
        return self._fit_surface_rect(layer, base_rect, surface)

    def _draw_layer(self, screen: pygame.Surface, layer: Dict[str, Any]):
        if not bool(layer.get("visible", True)):
            return
        if str(layer.get("id", "")) in {"grade_left", "grade_right"} and not bool(self.payload.get("三把S", True)):
            return
        if str(layer.get("id", "")) == "upgrade_center" and not bool(self.payload.get("显示升级", True)):
            return
        if str(layer.get("id", "")) in {"upgrade_lt", "upgrade_rt", "upgrade_lb", "upgrade_rb"} and not bool(self.payload.get("显示升级", True)):
            return
        draw_rect = self._animated_layer_rect(layer)
        if draw_rect.right < -5000:
            return
        surface = self._render_layer_surface(layer)
        alpha = max(0, min(255, self._layer_alpha(layer)))
        if str(layer.get("kind", "")) == "shape":
            layer_surface = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
            layer_surface.blit(surface, (0, 0))
            screen.blit(layer_surface, draw_rect.topleft)
            return
        content_rect = self._fit_surface_rect(layer, draw_rect, surface)
        content_surface = surface
        if content_rect.size != surface.get_size():
            content_surface = self._scale_image_cached(surface, content_rect.size)
        if alpha < 255:
            content_surface = content_surface.copy()
            content_surface.set_alpha(alpha)
        if str(layer.get("id", "")) in {"style_fill", "speed_fill"}:
            percent_key = "花式经验" if layer["id"] == "style_fill" else "竞速经验"
            fill_value = _clamp(float(self.payload.get(percent_key, 0.0) or 0.0), 0.0, 1.0)
            reveal_width = int(content_surface.get_width() * fill_value)
            if reveal_width > 0:
                clipped = pygame.Surface(content_surface.get_size(), pygame.SRCALPHA)
                clipped.blit(content_surface, (0, 0), area=pygame.Rect(0, 0, reveal_width, content_surface.get_height()))
                screen.blit(clipped, content_rect.topleft)
            return
        screen.blit(content_surface, content_rect.topleft)

    def _draw_placeholder_cover(self, screen: pygame.Surface, rect: pygame.Rect):
        pygame.draw.rect(screen, (16, 18, 28), rect)
        pygame.draw.rect(screen, (120, 160, 255), rect, 1)
        text = _render_text_surface("NO IMAGE", 24, (235, 235, 240), False)
        screen.blit(text, text.get_rect(center=rect.center))

    def _draw_canvas(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))
        for layer in self._process_layers(include_common=True):
            if layer.get("id") == "cover" and self.assets.get("cover") is None:
                if bool(layer.get("visible", True)):
                    self._draw_placeholder_cover(screen, self._animated_layer_rect(layer))
                continue
            self._draw_layer(screen, layer)

    def _layer_hit(self, pos: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        x, y = pos
        for layer in sorted(self._process_layers(include_common=True), key=lambda item: int(item.get("z", 0)), reverse=True):
            if not bool(layer.get("visible", True)):
                continue
            if self._animated_layer_rect(layer).collidepoint(x, y):
                return layer
        return None

    def _select_layer(self, layer_id: str, append: bool = False, mode: str = "layout"):
        if not append:
            self.selected_ids = [layer_id]
        else:
            if layer_id in self.selected_ids:
                self.selected_ids.remove(layer_id)
            else:
                self.selected_ids.append(layer_id)
        self.active_layer_id = layer_id if layer_id in self.selected_ids else (self.selected_ids[-1] if self.selected_ids else "")
        self.selection_mode = mode

    def _selected_layers(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for layer_id in self.selected_ids:
            layer = self._layer_by_id(layer_id)
            if layer is not None:
                result.append(layer)
        return result

    def _require_paused_for_edit(self) -> bool:
        if not self.process_playing:
            return True
        self._set_message("先停止当前流程播放再调整布局")
        return False

    def _begin_drag(self, mouse_pos: Tuple[int, int]):
        if not self._require_paused_for_edit():
            return
        active = self._layer_by_id(self.active_layer_id)
        if active is None:
            return
        self.dragging = True
        self.drag_start = mouse_pos
        if self.selection_mode == "content":
            self.drag_origin_offset = self._layer_content_offset(active)
            self.drag_origin_rects = {}
        else:
            self.drag_origin_rects = {
                layer["id"]: tuple(self._layer_rect(layer))
                for layer in self._selected_layers()
            }

    def _update_drag(self, mouse_pos: Tuple[int, int]):
        if not self.dragging:
            return
        dx = mouse_pos[0] - self.drag_start[0]
        dy = mouse_pos[1] - self.drag_start[1]
        active = self._layer_by_id(self.active_layer_id)
        if active is None:
            return
        if self.selection_mode == "content":
            self._set_layer_content_offset(active, (self.drag_origin_offset[0] + dx, self.drag_origin_offset[1] + dy))
        else:
            for layer_id, origin in self.drag_origin_rects.items():
                layer = self._layer_by_id(layer_id)
                if layer is None:
                    continue
                rect = pygame.Rect(origin)
                rect.x += dx
                rect.y += dy
                self._set_layer_rect(layer, rect)

    def _end_drag(self):
        if self.dragging:
            self.dragging = False
            self._save_layout()

    def _adjust_selected_scale(self, wheel_y: int, width_only: bool = False, height_only: bool = False):
        if not self._require_paused_for_edit():
            return
        if wheel_y == 0:
            return
        factor = 1.01 if wheel_y > 0 else 0.99
        active = self._layer_by_id(self.active_layer_id)
        if active is None:
            return
        if self.selection_mode == "content":
            current_x, current_y = self._layer_content_scale(active)
            if width_only:
                current_x *= factor
            elif height_only:
                current_y *= factor
            else:
                current_x *= factor
                current_y *= factor
            self._set_layer_content_scale(active, (current_x, current_y))
        else:
            for layer in self._selected_layers():
                rect = self._layer_rect(layer)
                center = rect.center
                if width_only:
                    rect.w = max(4, int(round(rect.w * factor)))
                elif height_only:
                    rect.h = max(4, int(round(rect.h * factor)))
                else:
                    rect.w = max(4, int(round(rect.w * factor)))
                    rect.h = max(4, int(round(rect.h * factor)))
                rect.center = center
                self._set_layer_rect(layer, rect)
        self._save_layout()

    def _nudge_selection(self, dx: int, dy: int):
        if not self._require_paused_for_edit():
            return
        active = self._layer_by_id(self.active_layer_id)
        if active is None:
            return
        if self.selection_mode == "content":
            offset_x, offset_y = self._layer_content_offset(active)
            self._set_layer_content_offset(active, (offset_x + dx, offset_y + dy))
        else:
            for layer in self._selected_layers():
                rect = self._layer_rect(layer)
                rect.x += dx
                rect.y += dy
                self._set_layer_rect(layer, rect)
        self._save_layout()

    def _reorder_selected(self, direction: int):
        if not self.selected_ids:
            return
        for layer in self._selected_layers():
            layer["z"] = int(layer.get("z", 0) or 0) + int(direction)
        self._save_layout()

    def _align_selected_text_layers(self, axis: str):
        selected = [layer for layer in self._selected_layers() if str(layer.get("kind", "")) == "text"]
        if len(selected) < 2:
            self._set_message("至少选择两个文字图层")
            return
        anchor = self._layer_rect(selected[0])
        for layer in selected[1:]:
            rect = self._layer_rect(layer)
            if axis == "left":
                rect.left = anchor.left
            elif axis == "center_x":
                rect.centerx = anchor.centerx
            elif axis == "right":
                rect.right = anchor.right
            elif axis == "top":
                rect.top = anchor.top
            elif axis == "center_y":
                rect.centery = anchor.centery
            elif axis == "bottom":
                rect.bottom = anchor.bottom
            self._set_layer_rect(layer, rect)
        self._save_layout()
        self._set_message("文字图层已对齐")

    def _panel_title_rect(self, panel: DebugPanel) -> pygame.Rect:
        return pygame.Rect(panel.rect.x, panel.rect.y, panel.rect.w, 28)

    def _panel_content_rect(self, panel: DebugPanel) -> pygame.Rect:
        if panel.collapsed:
            return pygame.Rect(panel.rect.x, panel.rect.y + 28, panel.rect.w, 0)
        return pygame.Rect(panel.rect.x + 8, panel.rect.y + 34, panel.rect.w - 16, panel.rect.h - 42)

    def _panel_button_rects(self, panel: DebugPanel) -> Dict[str, pygame.Rect]:
        title_rect = self._panel_title_rect(panel)
        return {
            "collapse": pygame.Rect(title_rect.right - 46, title_rect.y + 5, 16, 16),
            "toggle": pygame.Rect(title_rect.right - 24, title_rect.y + 5, 16, 16),
        }

    def _panel_at(self, pos: Tuple[int, int]) -> Optional[DebugPanel]:
        for panel in reversed(list(self.panels.values())):
            if panel.hidden:
                continue
            if panel.rect.collidepoint(pos):
                return panel
        return None

    def _toggle_panel_visibility(self, panel_id: str):
        panel = self.panels.get(panel_id)
        if panel is None:
            return
        panel.collapsed = not panel.collapsed
        self._save_settings()

    def _toggle_text_editor(self, layer: Dict[str, Any]):
        style = layer.get("text_style", {}) if isinstance(layer.get("text_style"), dict) else {}
        self.text_editor_open = True
        self.text_editor_layer_id = str(layer.get("id", "") or "")
        self.text_editor_fields = [
            {"id": "text", "label": "文字", "value": self._format_layer_text(layer)},
            {"id": "font_size", "label": "字号", "value": str(int(style.get("font_size", 24) or 24))},
            {"id": "color", "label": "色值", "value": _color_text(_parse_color(style.get("color"), (255, 255, 255)))},
            {"id": "stroke_color", "label": "描边色", "value": _color_text(_parse_color(style.get("stroke_color"), (0, 0, 0)))},
            {"id": "stroke_width", "label": "描边粗细", "value": str(int(style.get("stroke_width", 0) or 0))},
            {"id": "letter_spacing", "label": "字间距", "value": str(int(style.get("letter_spacing", 0) or 0))},
            {"id": "bold", "label": "粗体", "value": "是" if bool(style.get("bold", False)) else "否"},
        ]
        self.active_text_field = "text"

    def _close_text_editor(self):
        self.text_editor_open = False
        self.text_editor_layer_id = ""
        self.text_editor_fields = []
        self.active_text_field = ""

    def _apply_text_editor(self):
        layer = self._layer_by_id(self.text_editor_layer_id)
        if layer is None:
            self._close_text_editor()
            return
        style = layer.setdefault("text_style", {})
        values = {field["id"]: str(field.get("value", "")) for field in self.text_editor_fields}
        if "text_key" in layer:
            self.payload[str(layer.get("text_key", "") or "")] = values.get("text", "")
        style["font_size"] = max(8, int(float(values.get("font_size", "24") or 24)))
        style["color"] = list(_parse_color(values.get("color", "#FFFFFF"), (255, 255, 255)))
        style["stroke_color"] = list(_parse_color(values.get("stroke_color", "#000000"), (0, 0, 0)))
        style["stroke_width"] = max(0, int(float(values.get("stroke_width", "0") or 0)))
        style["letter_spacing"] = int(float(values.get("letter_spacing", "0") or 0))
        style["bold"] = str(values.get("bold", "否")).strip() in {"是", "1", "true", "True", "Y", "y"}
        self._save_layout()
        self._close_text_editor()
        self._set_message("文字样式已更新")

    def _text_editor_rect(self) -> pygame.Rect:
        screen_w, screen_h = self.screen.get_size()
        return pygame.Rect(screen_w // 2 - 220, screen_h // 2 - 190, 440, 380)

    def _text_editor_field_rects(self) -> Dict[str, pygame.Rect]:
        editor = self._text_editor_rect()
        rects: Dict[str, pygame.Rect] = {}
        y = editor.y + 56
        for field in self.text_editor_fields:
            rects[field["id"]] = pygame.Rect(editor.x + 128, y, editor.w - 152, 30)
            y += 40
        rects["apply"] = pygame.Rect(editor.x + editor.w - 188, editor.bottom - 48, 80, 28)
        rects["cancel"] = pygame.Rect(editor.x + editor.w - 96, editor.bottom - 48, 80, 28)
        return rects

    def _handle_text_input(self, event: pygame.event.Event):
        if not self.text_editor_open or not self.active_text_field:
            return
        field = next((item for item in self.text_editor_fields if item["id"] == self.active_text_field), None)
        if field is None:
            return
        value = str(field.get("value", ""))
        if event.key == pygame.K_BACKSPACE:
            field["value"] = value[:-1]
        elif event.key == pygame.K_RETURN:
            self._apply_text_editor()
        elif event.key == pygame.K_ESCAPE:
            self._close_text_editor()
        else:
            if event.unicode:
                field["value"] = value + event.unicode

    def _handle_panel_mouse_down(self, panel: DebugPanel, pos: Tuple[int, int]) -> bool:
        button_rects = self._panel_button_rects(panel)
        if button_rects["collapse"].collidepoint(pos) or button_rects["toggle"].collidepoint(pos):
            panel.collapsed = not panel.collapsed
            self._save_settings()
            return True
        if self._panel_title_rect(panel).collidepoint(pos):
            self.dragging_panel_id = panel.panel_id
            self.panel_drag_origin = pos
            self.panel_origin_rect = panel.rect.copy()
            return True
        if panel.panel_id == "visual":
            return self._handle_visual_panel_click(panel, pos)
        if panel.panel_id == "badge":
            return self._handle_badge_panel_click(panel, pos)
        if panel.panel_id == "function":
            return self._handle_function_panel_click(panel, pos)
        if panel.panel_id == "layers":
            return self._handle_layer_panel_click(panel, pos)
        return False

    def _handle_visual_panel_click(self, panel: DebugPanel, pos: Tuple[int, int]) -> bool:
        content = self._panel_content_rect(panel)
        row_rects = [
            ("show_bounds", pygame.Rect(content.x, content.y, content.w, 28)),
            ("show_names", pygame.Rect(content.x, content.y + 32, content.w, 28)),
            ("show_help", pygame.Rect(content.x, content.y + 64, content.w, 28)),
        ]
        for field, rect in row_rects:
            if rect.collidepoint(pos):
                setattr(self, field, not bool(getattr(self, field)))
                self._save_settings()
                return True
        return False

    def _badge_button_rects(self, panel: DebugPanel) -> Dict[str, pygame.Rect]:
        content = self._panel_content_rect(panel)
        return {
            "全连": pygame.Rect(content.x, content.y, content.w, 28),
            "三把S": pygame.Rect(content.x, content.y + 32, content.w, 28),
            "失败": pygame.Rect(content.x, content.y + 64, content.w, 28),
        }

    def _handle_badge_panel_click(self, panel: DebugPanel, pos: Tuple[int, int]) -> bool:
        rects = self._badge_button_rects(panel)
        labels = {
            "全连": "全连",
            "三把S": "三把全连",
            "失败": "失败",
        }
        for key, rect in rects.items():
            if not rect.collidepoint(pos):
                continue
            self.payload["顶标"] = key
            self.payload["三把S"] = bool(key == "三把S")
            self._set_process(1, replay=False)
            self._set_message(f"顶部标已切换为{labels[key]}")
            return True
        return False

    def _function_button_rects(self, panel: DebugPanel) -> Dict[str, pygame.Rect]:
        content = self._panel_content_rect(panel)
        rects: Dict[str, pygame.Rect] = {}
        for index, process_index in enumerate((1, 2, 3)):
            row_y = content.y + index * 36
            rects[f"check_{process_index}"] = pygame.Rect(content.x, row_y + 2, 26, 26)
            rects[f"label_{process_index}"] = pygame.Rect(content.x + 34, row_y, max(40, content.w - 118), 30)
            rects[f"play_{process_index}"] = pygame.Rect(content.right - 76, row_y + 2, 68, 26)
        return rects

    def _handle_function_panel_click(self, panel: DebugPanel, pos: Tuple[int, int]) -> bool:
        rects = self._function_button_rects(panel)
        for process_index in (1, 2, 3):
            if rects[f"check_{process_index}"].collidepoint(pos) or rects[f"label_{process_index}"].collidepoint(pos):
                self._set_process(process_index, replay=False)
                return True
            if rects[f"play_{process_index}"].collidepoint(pos):
                self._set_process(process_index, replay=True)
                return True
        return False

    def _layer_panel_row_rects(self, panel: DebugPanel) -> Tuple[List[Tuple[pygame.Rect, Dict[str, Any]]], pygame.Rect]:
        content = self._panel_content_rect(panel)
        list_rect = pygame.Rect(content.x, content.y, content.w, max(60, content.h - 84))
        y = list_rect.y - self.layer_scroll
        rows: List[Tuple[pygame.Rect, Dict[str, Any]]] = []
        for layer in reversed(self._process_layers(include_common=True)):
            row = pygame.Rect(list_rect.x, y, list_rect.w, 24)
            rows.append((row, layer))
            y += 26
        return rows, list_rect

    def _layer_panel_align_buttons(self, panel: DebugPanel) -> Dict[str, pygame.Rect]:
        content = self._panel_content_rect(panel)
        top = content.bottom - 74
        labels = ["左", "中", "右", "上", "中", "下"]
        keys = ["left", "center_x", "right", "top", "center_y", "bottom"]
        rects: Dict[str, pygame.Rect] = {}
        button_w = (content.w - 10) // 3
        for idx, key in enumerate(keys[:3]):
            rects[key] = pygame.Rect(content.x + idx * (button_w + 5), top, button_w, 26)
        for idx, key in enumerate(keys[3:]):
            rects[key] = pygame.Rect(content.x + idx * (button_w + 5), top + 32, button_w, 26)
        return rects

    def _handle_layer_panel_click(self, panel: DebugPanel, pos: Tuple[int, int]) -> bool:
        rows, list_rect = self._layer_panel_row_rects(panel)
        if list_rect.collidepoint(pos):
            for row, layer in rows:
                if not row.collidepoint(pos):
                    continue
                eye_rect = pygame.Rect(row.x + 4, row.y + 4, 16, 16)
                if eye_rect.collidepoint(pos):
                    layer["visible"] = not bool(layer.get("visible", True))
                    self._save_layout()
                    return True
                append = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                self._select_layer(str(layer.get("id", "")), append=append, mode="layout")
                return True
        for key, rect in self._layer_panel_align_buttons(panel).items():
            if rect.collidepoint(pos):
                self._align_selected_text_layers(key)
                return True
        return False

    def _handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((max(960, event.w), max(540, event.h)), pygame.RESIZABLE)
            return
        if event.type == pygame.KEYDOWN:
            if self.text_editor_open:
                self._handle_text_input(event)
                return
            if event.key == pygame.K_ESCAPE:
                if self.selected_ids:
                    self.selected_ids.clear()
                    self.active_layer_id = ""
                    return
                self.running = False
                return
            if event.key == pygame.K_F1:
                self._toggle_panel_visibility("visual")
                return
            if event.key == pygame.K_F2:
                self._toggle_panel_visibility("function")
                return
            if event.key == pygame.K_F3:
                self._toggle_panel_visibility("layers")
                return
            if event.key == pygame.K_F4:
                self.show_help = not self.show_help
                self._save_settings()
                return
            if event.key == pygame.K_SPACE:
                if self.process_playing:
                    self.process_playing = False
                    self.process_time = self._process_static_time(self.selected_process)
                else:
                    self._set_process(self.selected_process, replay=True)
                self._sync_preview_timeline()
                return
            mods = pygame.key.get_mods()
            if event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
                self._save_layout()
                self._set_message("布局已保存")
                return
            if event.key == pygame.K_r and mods & pygame.KMOD_CTRL:
                self._reset_layout()
                return
            if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self._reorder_selected(1)
                return
            if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self._reorder_selected(-1)
                return
            step = 10 if mods & pygame.KMOD_SHIFT else 1
            if event.key == pygame.K_LEFT:
                self._nudge_selection(-step, 0)
                return
            if event.key == pygame.K_RIGHT:
                self._nudge_selection(step, 0)
                return
            if event.key == pygame.K_UP:
                self._nudge_selection(0, -step)
                return
            if event.key == pygame.K_DOWN:
                self._nudge_selection(0, step)
                return
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.text_editor_open:
                editor = self._text_editor_rect()
                field_rects = self._text_editor_field_rects()
                if field_rects["apply"].collidepoint(pos):
                    self._apply_text_editor()
                    return
                if field_rects["cancel"].collidepoint(pos):
                    self._close_text_editor()
                    return
                clicked_field = ""
                for field_id, rect in field_rects.items():
                    if field_id in {"apply", "cancel"}:
                        continue
                    if rect.collidepoint(pos):
                        clicked_field = field_id
                        break
                if clicked_field:
                    self.active_text_field = clicked_field
                    if clicked_field == "bold":
                        field = next((item for item in self.text_editor_fields if item["id"] == "bold"), None)
                        if field is not None:
                            field["value"] = "否" if str(field.get("value", "否")) == "是" else "是"
                    return
                if not editor.collidepoint(pos):
                    self._close_text_editor()
                return
            if event.button in (1, 3):
                panel = self._panel_at(pos)
                if panel is not None:
                    if self._handle_panel_mouse_down(panel, pos):
                        return
                canvas_pos = self._screen_to_canvas_pos(pos)
                if canvas_pos is None:
                    self.selected_ids.clear()
                    self.active_layer_id = ""
                    return
                layer = self._layer_hit(canvas_pos)
                if layer is None:
                    self.selected_ids.clear()
                    self.active_layer_id = ""
                    return
                layer_id = str(layer.get("id", "") or "")
                now = pygame.time.get_ticks()
                is_double = (
                    event.button == 1
                    and layer_id == self.last_click_layer_id
                    and now - self.last_click_ticks <= 350
                )
                self.last_click_ticks = now
                self.last_click_layer_id = layer_id
                if is_double:
                    self._select_layer(layer_id, append=False, mode="content")
                    if str(layer.get("kind", "")) == "text":
                        self._toggle_text_editor(layer)
                        return
                else:
                    append = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                    self._select_layer(layer_id, append=append, mode="layout")
                if event.button == 1:
                    self._begin_drag(canvas_pos)
                return
            if event.button in (4, 5):
                delta = 1 if event.button == 4 else -1
                panel = self._panel_at(pos)
                if panel is not None and panel.panel_id == "layers" and self._panel_content_rect(panel).collidepoint(pos):
                    self.layer_scroll = max(0, self.layer_scroll - delta * 24)
                    return
                mods = pygame.key.get_mods()
                self._adjust_selected_scale(
                    delta,
                    width_only=bool(mods & pygame.KMOD_SHIFT),
                    height_only=bool(mods & pygame.KMOD_CTRL),
                )
                return
        if event.type == pygame.MOUSEMOTION:
            if self.dragging_panel_id:
                panel = self.panels.get(self.dragging_panel_id)
                if panel is not None:
                    dx = event.pos[0] - self.panel_drag_origin[0]
                    dy = event.pos[1] - self.panel_drag_origin[1]
                    panel.rect.topleft = (self.panel_origin_rect.x + dx, self.panel_origin_rect.y + dy)
                    self._save_settings()
                return
            if self.dragging:
                canvas_pos = self._screen_to_canvas_pos(event.pos, clamp_to_viewport=True)
                if canvas_pos is not None:
                    self._update_drag(canvas_pos)
                return
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._end_drag()
                self.dragging_panel_id = None

    def _update(self, dt: float):
        if self.process_playing:
            self.process_time = min(self._process_duration(self.selected_process), self.process_time + dt)
            if self.process_time >= self._process_duration(self.selected_process) - 1e-6:
                self.process_playing = False
            self._sync_preview_timeline()

    def _draw_selection(self, screen: pygame.Surface):
        if (not self.show_bounds) and (not self.selected_ids):
            return
        selected_only = not self.show_bounds
        visible_ids = {str(layer.get("id", "")) for layer in self._process_layers(include_common=True)}
        for layer in self._sorted_layers():
            if not bool(layer.get("visible", True)):
                continue
            layer_id = str(layer.get("id", "") or "")
            selected = layer_id in self.selected_ids
            if layer_id not in visible_ids and not selected:
                continue
            if selected_only and not selected:
                continue
            draw_rect = self._animated_layer_rect(layer)
            color = (255, 210, 70) if selected else (100, 180, 255)
            border_rect = draw_rect if not (selected and self.selection_mode == "content" and layer_id == self.active_layer_id) else self._content_rect(layer, draw_rect)
            pygame.draw.rect(screen, color, border_rect, 1)
            if selected:
                pygame.draw.rect(screen, (255, 255, 255), border_rect.inflate(2, 2), 1)
            if self.show_names and (self.show_bounds or selected):
                tag = _render_text_surface(str(layer.get("name", "")), 14, color, False, (0, 0, 0), 1)
                tag_pos = (border_rect.x, max(0, border_rect.y - tag.get_height() - 2))
                screen.blit(tag, tag_pos)

    def _draw_button(self, screen: pygame.Surface, rect: pygame.Rect, text: str, active: bool = False):
        fill = (28, 44, 78, 230) if not active else (62, 102, 170, 240)
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        surface.fill(fill)
        pygame.draw.rect(surface, (180, 210, 255), surface.get_rect(), 1)
        screen.blit(surface, rect.topleft)
        label = _render_text_surface(text, 16, (245, 248, 255), False)
        screen.blit(label, label.get_rect(center=rect.center))

    def _draw_visual_panel(self, screen: pygame.Surface, panel: DebugPanel):
        content = self._panel_content_rect(panel)
        items = [
            ("显示全部布局边框", self.show_bounds),
            ("显示控件命名", self.show_names),
            ("显示帮助说明", self.show_help),
        ]
        y = content.y
        for label, active in items:
            rect = pygame.Rect(content.x, y, content.w, 28)
            self._draw_button(screen, rect, label, active)
            y += 32

    def _draw_badge_panel(self, screen: pygame.Surface, panel: DebugPanel):
        rects = self._badge_button_rects(panel)
        labels = {
            "全连": "全连",
            "三把S": "三把全连",
            "失败": "失败",
        }
        current = str(self.payload.get("顶标", "全连") or "全连")
        for key, rect in rects.items():
            self._draw_button(screen, rect, labels[key], current == key)

    def _draw_function_panel(self, screen: pygame.Surface, panel: DebugPanel):
        rects = self._function_button_rects(panel)
        for process_index in (1, 2, 3):
            checked = self.selected_process == process_index
            self._draw_button(screen, rects[f"check_{process_index}"], "√" if checked else "", checked)
            label_rect = rects[f"label_{process_index}"]
            label_surface = _render_text_surface(f"流程{process_index}", 16, (245, 248, 255), checked)
            screen.blit(label_surface, label_surface.get_rect(midleft=(label_rect.x + 2, label_rect.centery)))
            playing = checked and self.process_playing
            self._draw_button(screen, rects[f"play_{process_index}"], "播放", playing)

    def _draw_layer_panel(self, screen: pygame.Surface, panel: DebugPanel):
        rows, list_rect = self._layer_panel_row_rects(panel)
        clip_before = screen.get_clip()
        screen.set_clip(list_rect)
        for row, layer in rows:
            if row.bottom < list_rect.top or row.top > list_rect.bottom:
                continue
            surface = pygame.Surface(row.size, pygame.SRCALPHA)
            selected = str(layer.get("id", "")) in self.selected_ids
            surface.fill((42, 60, 96, 210) if selected else (20, 26, 42, 180))
            pygame.draw.rect(surface, (110, 140, 210), surface.get_rect(), 1)
            screen.blit(surface, row.topleft)
            eye_rect = pygame.Rect(row.x + 4, row.y + 4, 16, 16)
            eye = "开" if bool(layer.get("visible", True)) else "关"
            screen.blit(_render_text_surface(eye, 14, (230, 240, 255)), eye_rect.topleft)
            label = f"{int(layer.get('z', 0) or 0):02d} {layer.get('name', '')}"
            label_color = (255, 232, 112) if selected else (230, 238, 255)
            screen.blit(_render_text_surface(label, 15, label_color), (row.x + 28, row.y + 3))
        screen.set_clip(clip_before)
        for key, rect in self._layer_panel_align_buttons(panel).items():
            names = {
                "left": "左对齐",
                "center_x": "中对齐",
                "right": "右对齐",
                "top": "上对齐",
                "center_y": "中轴对齐",
                "bottom": "下对齐",
            }
            self._draw_button(screen, rect, names[key], False)

    def _draw_text_editor(self, screen: pygame.Surface):
        if not self.text_editor_open:
            return
        mask = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 120))
        screen.blit(mask, (0, 0))
        editor = self._text_editor_rect()
        surface = pygame.Surface(editor.size, pygame.SRCALPHA)
        surface.fill((14, 20, 34, 242))
        pygame.draw.rect(surface, (200, 220, 255), surface.get_rect(), 1)
        screen.blit(surface, editor.topleft)
        title = _render_text_surface("文字图层编辑", 22, (255, 255, 255), True)
        screen.blit(title, (editor.x + 16, editor.y + 14))
        rects = self._text_editor_field_rects()
        y = editor.y + 58
        for field in self.text_editor_fields:
            label = _render_text_surface(field["label"], 16, (225, 232, 245))
            screen.blit(label, (editor.x + 16, y + 6))
            input_rect = rects[field["id"]]
            self._draw_button(screen, input_rect, str(field.get("value", "")), self.active_text_field == field["id"])
            y += 40
        self._draw_button(screen, rects["apply"], "应用", False)
        self._draw_button(screen, rects["cancel"], "取消", False)

    def _draw_panel(self, screen: pygame.Surface, panel: DebugPanel):
        if panel.hidden:
            return
        body = pygame.Surface(panel.rect.size, pygame.SRCALPHA)
        body.fill((10, 14, 24, 190))
        pygame.draw.rect(body, (120, 150, 220), body.get_rect(), 1)
        screen.blit(body, panel.rect.topleft)
        title_rect = self._panel_title_rect(panel)
        title_surface = pygame.Surface((title_rect.w, title_rect.h), pygame.SRCALPHA)
        title_surface.fill((18, 26, 40, 230))
        pygame.draw.rect(title_surface, (155, 190, 255), title_surface.get_rect(), 1)
        screen.blit(title_surface, title_rect.topleft)
        screen.blit(_render_text_surface(panel.title, 17, (245, 248, 255), True), (title_rect.x + 10, title_rect.y + 4))
        button_rects = self._panel_button_rects(panel)
        self._draw_button(screen, button_rects["collapse"], "-" if not panel.collapsed else "+", False)
        self._draw_button(screen, button_rects["toggle"], "□" if not panel.collapsed else "▽", False)
        if panel.collapsed:
            return
        if panel.panel_id == "visual":
            self._draw_visual_panel(screen, panel)
        elif panel.panel_id == "badge":
            self._draw_badge_panel(screen, panel)
        elif panel.panel_id == "function":
            self._draw_function_panel(screen, panel)
        elif panel.panel_id == "layers":
            self._draw_layer_panel(screen, panel)

    def _draw_help(self, screen: pygame.Surface):
        if not self.show_help:
            return
        lines = [
            "单击选布局，双击选贴图；双击文字可编辑文字/字号/色值/描边/字间距/粗体",
            "拖动移动；滚轮等比缩放；Shift+滚轮改宽；Ctrl+滚轮改高；方向键 1px，Shift+方向键 10px",
            "顶部标面板可直接切换全连 / 三把全连 / 失败，并自动切回流程1预览效果",
            "功能面板勾选流程1/2/3切换当前流程；播放按钮只回放当前流程；空格回放或定格当前流程",
            "Shift+点图层行多选；+/- 改图层 Z；F1/F2/F3 折叠面板；Ctrl+S 保存；Ctrl+R 重置",
            "播放中不可改布局；图层选中后会强制显示对应边框",
        ]
        x = 22
        y = self.screen.get_height() - 112
        for line in lines:
            text = _render_text_surface(line, 15, (245, 245, 250), False, (0, 0, 0), 1)
            screen.blit(text, (x, y))
            y += 20

    def _draw_message(self, screen: pygame.Surface):
        if not self.message or pygame.time.get_ticks() > self.message_until:
            return
        text = _render_text_surface(self.message, 16, (255, 250, 210), True, (0, 0, 0), 1)
        rect = text.get_rect(center=(self.screen.get_width() // 2, 28))
        panel = pygame.Surface((rect.w + 20, rect.h + 10), pygame.SRCALPHA)
        panel.fill((18, 20, 30, 200))
        pygame.draw.rect(panel, (255, 235, 120), panel.get_rect(), 1)
        screen.blit(panel, (rect.x - 10, rect.y - 5))
        screen.blit(text, rect.topleft)

    def _draw(self):
        self.canvas.fill((0, 0, 0, 0))
        self._draw_canvas(self.canvas)
        self._draw_selection(self.canvas)
        self.screen.fill((0, 0, 0))
        viewport = self._preview_rect()
        scaled_canvas = pygame.transform.smoothscale(self.canvas, viewport.size)
        self.screen.blit(scaled_canvas, viewport.topleft)
        for panel in self.panels.values():
            self._draw_panel(self.screen, panel)
        self._draw_text_editor(self.screen)
        self._draw_help(self.screen)
        self._draw_message(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self._handle_event(event)
            self._update(dt)
            self._draw()
        self._save_layout()
        self._save_settings()
        pygame.quit()


def main():
    SettlementLayoutDebugger().run()


if __name__ == "__main__":
    main()
