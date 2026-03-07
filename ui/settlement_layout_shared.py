import copy
import json
import os
from typing import Any, Dict, List, Optional, Tuple

import pygame


Color = Tuple[int, int, int]
RectLike = Tuple[int, int, int, int]

DESIGN_SIZE = (1600, 900)
LAYOUT_VERSION = 2

COMMON_LAYER_IDS = {"background", "dimmer"}
PROCESS_LAYER_IDS = {
    1: {
        "panel",
        "cover",
        "stars",
        "song_title",
        "miss",
        "good",
        "cool",
        "perfect",
        "combo",
        "accuracy",
        "score",
        "grade_left",
        "grade_main",
        "grade_right",
        "top_badge",
        "new_record",
    },
    2: {
        "reward_bg",
        "reward_digits",
        "style_label",
        "style_fill",
        "style_frame",
        "style_lv",
        "speed_label",
        "speed_fill",
        "speed_frame",
        "speed_lv",
        "rank_icon",
        "rank_label",
        "upgrade_center",
        "upgrade_lt",
        "upgrade_rt",
        "upgrade_lb",
        "upgrade_rb",
    },
    3: {
        "flow3_prompt",
    },
}


def read_json(path: str) -> dict:
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


def write_json(path: str, data: dict):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
    except Exception:
        pass


def safe_load_image(path: str, use_alpha: bool = True) -> Optional[pygame.Surface]:
    try:
        if path and os.path.isfile(path):
            surface = pygame.image.load(path)
            return surface.convert_alpha() if use_alpha else surface.convert()
    except Exception:
        pass
    return None


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    try:
        from core.工具 import 获取字体  # type: ignore

        return 获取字体(int(size), 是否粗体=bool(bold))
    except Exception:
        pygame.font.init()
        try:
            return pygame.font.SysFont("Microsoft YaHei", int(size), bold=bool(bold))
        except Exception:
            return pygame.font.Font(None, int(size))


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def parse_color(value: Any, fallback: Color) -> Color:
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return (
                int(clamp(float(value[0]), 0, 255)),
                int(clamp(float(value[1]), 0, 255)),
                int(clamp(float(value[2]), 0, 255)),
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


def color_text(color: Color) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def fit_size(
    src_size: Tuple[int, int], dst_size: Tuple[int, int], mode: str
) -> Tuple[int, int]:
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


def render_text_surface(
    text: str,
    size: int,
    color: Color,
    bold: bool = False,
    stroke_color: Color = (0, 0, 0),
    stroke_width: int = 0,
    letter_spacing: int = 0,
) -> pygame.Surface:
    font = get_font(max(8, int(size)), bold=bool(bold))
    text = str(text or "")
    if not text:
        return pygame.Surface((1, 1), pygame.SRCALPHA)
    glyphs: List[pygame.Surface] = []
    for char in text:
        glyphs.append(font.render(char, True, color).convert_alpha())
    total_width = sum(g.get_width() for g in glyphs) + max(0, len(glyphs) - 1) * int(
        letter_spacing
    )
    total_height = max((g.get_height() for g in glyphs), default=max(1, size))
    stroke = max(0, int(stroke_width))
    canvas = pygame.Surface(
        (max(1, total_width + stroke * 2), max(1, total_height + stroke * 2)),
        pygame.SRCALPHA,
    )
    if stroke > 0:
        stroke_glyphs = [
            font.render(char, True, stroke_color).convert_alpha() for char in text
        ]
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


def process_layer_ids(process_index: int, include_common: bool = True) -> set:
    result = set(PROCESS_LAYER_IDS.get(int(process_index), set()))
    if include_common:
        result.update(COMMON_LAYER_IDS)
    return result


def _panel_rect(screen_size: Tuple[int, int], player_index: int = 1) -> pygame.Rect:
    screen_w, screen_h = int(screen_size[0]), int(screen_size[1])
    size = int(max(360, min(int(screen_h * 0.82), int(screen_w * 0.48), 700)))
    margin = max(28, int(screen_w * 0.06))
    x = screen_w - margin - size if int(player_index) == 2 else margin
    y = max(20, (screen_h - size) // 2)
    return pygame.Rect(int(x), int(y), int(size), int(size))


def _reward_rect(
    panel_rect: pygame.Rect, screen_size: Tuple[int, int], player_index: int = 1
) -> pygame.Rect:
    screen_w, screen_h = int(screen_size[0]), int(screen_size[1])
    width = int(min(max(380, screen_w * 0.36), 620))
    height = int(max(190, width * 0.50))
    y = int(panel_rect.centery - height // 2)
    if int(player_index) == 2:
        x = int(max(24, panel_rect.left - 24 - width))
    else:
        x = int(min(screen_w - 24 - width, panel_rect.right + 24))
    return pygame.Rect(x, y, width, height)


def _ref_rect(panel: pygame.Rect, x: float, y: float, w: float, h: float) -> List[int]:
    return [
        int(panel.left + panel.w * (x / 512.0)),
        int(panel.top + panel.h * (y / 512.0)),
        int(panel.w * (w / 512.0)),
        int(panel.h * (h / 512.0)),
    ]


def _image_layer(
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


def _text_layer(
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


def build_default_layout(
    screen_size: Tuple[int, int] = DESIGN_SIZE,
    player_index: int = 1,
) -> Dict[str, Dict[str, Any]]:
    screen_w, screen_h = int(screen_size[0]), int(screen_size[1])
    panel = _panel_rect(screen_size, player_index=player_index)
    reward = _reward_rect(panel, screen_size, player_index=player_index)
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
    prompt_w = int(min(screen_w * 0.62, 780))
    prompt_h = int(max(96, screen_h * 0.16))

    layers = {
        "background": _image_layer(
            "background", "背景图", (0, 0, screen_w, screen_h), "background", 0, "cover"
        ),
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
        "panel": _image_layer(
            "panel", "结算面板", tuple(panel), "panel", 10, "stretch"
        ),
        "cover": _image_layer(
            "cover",
            "封面区",
            tuple(_ref_rect(panel, 58, 138, 126, 134)),
            "cover",
            20,
            "cover",
        ),
        "stars": _text_layer(
            "stars",
            "星级",
            tuple(_ref_rect(panel, 48, 304, 150, 28)),
            "星级",
            22,
            value_type="stars",
            color=(242, 223, 60),
            font_size=24,
            align="left",
        ),
        "song_title": _text_layer(
            "song_title",
            "歌名",
            tuple(_ref_rect(panel, 46, 332, 168, 38)),
            "歌名",
            23,
            font_size=26,
            align="left",
        ),
        "miss": _text_layer(
            "miss",
            "MISS",
            tuple(_ref_rect(panel, 285, 129, 160, 40)),
            "miss",
            24,
            value_type="number",
            color=(255, 255, 255),
            stroke_color=(166, 19, 27),
            stroke_width=1,
            font_size=42,
            align="right",
        ),
        "good": _text_layer(
            "good",
            "GOOD",
            tuple(_ref_rect(panel, 285, 176, 160, 40)),
            "good",
            24,
            value_type="number",
            color=(255, 255, 255),
            stroke_color=(49, 74, 25),
            stroke_width=1,
            font_size=42,
            align="right",
        ),
        "cool": _text_layer(
            "cool",
            "COOL",
            tuple(_ref_rect(panel, 285, 223, 160, 40)),
            "cool",
            24,
            value_type="number",
            color=(255, 255, 255),
            stroke_color=(12, 9, 69),
            stroke_width=1,
            font_size=42,
            align="right",
        ),
        "perfect": _text_layer(
            "perfect",
            "PERFECT",
            tuple(_ref_rect(panel, 285, 271, 160, 40)),
            "perfect",
            24,
            value_type="number",
            color=(255, 255, 255),
            stroke_color=(113, 19, 61),
            stroke_width=1,
            font_size=42,
            align="right",
        ),
        "combo": _text_layer(
            "combo",
            "COMBO",
            tuple(_ref_rect(panel, 285, 318, 160, 40)),
            "combo",
            24,
            value_type="number",
            color=(255, 255, 255),
            stroke_color=(56, 33, 113),
            stroke_width=1,
            font_size=42,
            align="right",
        ),
        "accuracy": _text_layer(
            "accuracy",
            "准确率",
            tuple(_ref_rect(panel, 250, 372, 195, 40)),
            "accuracy",
            24,
            value_type="percent",
            color=(255, 255, 255),
            stroke_color=(223, 193, 61),
            stroke_width=1,
            font_size=42,
            align="right",
        ),
        "score": _text_layer(
            "score",
            "总分",
            tuple(_ref_rect(panel, 230, 428, 220, 48)),
            "score",
            24,
            value_type="number",
            font_size=44,
            align="center",
        ),
        "grade_left": _image_layer(
            "grade_left",
            "评级左",
            (
                main_grade_center[0] - side_gap - int(main_grade_w * 0.34),
                main_grade_center[1] - int(main_grade_h * 0.28),
                int(main_grade_w * 0.68),
                int(main_grade_h * 0.68),
            ),
            "grade_s",
            30,
        ),
        "grade_main": _image_layer(
            "grade_main",
            "评级主",
            (
                main_grade_center[0] - main_grade_w // 2,
                main_grade_center[1] - main_grade_h // 2,
                main_grade_w,
                main_grade_h,
            ),
            "grade_s",
            31,
        ),
        "grade_right": _image_layer(
            "grade_right",
            "评级右",
            (
                main_grade_center[0] + side_gap - int(main_grade_w * 0.34),
                main_grade_center[1] - int(main_grade_h * 0.28),
                int(main_grade_w * 0.68),
                int(main_grade_h * 0.68),
            ),
            "grade_s",
            30,
        ),
        "top_badge": _image_layer(
            "top_badge",
            "顶部标",
            (
                panel.centerx - top_badge_w // 2,
                int(panel.top + panel.h * 0.10) - top_badge_h // 2,
                top_badge_w,
                top_badge_h,
            ),
            "top_badge",
            40,
        ),
        "new_record": _image_layer(
            "new_record",
            "新纪录",
            (
                panel.right - int(panel.w * 0.04) - new_record_w // 2,
                int(panel.top + panel.h * 0.11) - new_record_h // 2,
                new_record_w,
                new_record_h,
            ),
            "new_record",
            41,
        ),
        "reward_bg": _image_layer(
            "reward_bg",
            "等级小框",
            tuple(reward),
            "reward_bg",
            50,
            "stretch",
            group="reward",
        ),
        "reward_digits": _image_layer(
            "reward_digits",
            "经验数字",
            (
                reward.x + int(reward.w * 0.09),
                reward.y + int(reward.h * 0.06),
                int(reward.w * 0.24),
                int(reward.h * 0.28),
            ),
            "digits",
            54,
            group="reward",
        ),
        "style_label": _text_layer(
            "style_label",
            "花式标签",
            (reward.x + 16, reward.y + int(reward.h * 0.40), 80, 32),
            "花式",
            55,
            font_size=18,
            align="left",
            group="reward",
        ),
        "style_fill": _image_layer(
            "style_fill",
            "花式经验值",
            (
                reward.x + int(reward.w * 0.18),
                reward.y + int(reward.h * 0.425),
                int(reward.w * 0.58),
                int(reward.h * 0.08),
            ),
            "style_fill",
            56,
            "stretch",
            group="reward",
        ),
        "style_frame": _image_layer(
            "style_frame",
            "花式经验框",
            (
                reward.x + int(reward.w * 0.18),
                reward.y + int(reward.h * 0.425),
                int(reward.w * 0.58),
                int(reward.h * 0.08),
            ),
            "style_frame",
            57,
            "stretch",
            group="reward",
        ),
        "style_lv": _text_layer(
            "style_lv",
            "花式等级",
            (reward.x + int(reward.w * 0.79), reward.y + int(reward.h * 0.40), 110, 34),
            "花式等级",
            58,
            value_type="level",
            font_size=22,
            align="left",
            group="reward",
        ),
        "speed_label": _text_layer(
            "speed_label",
            "竞速标签",
            (reward.x + 16, reward.y + int(reward.h * 0.56), 80, 32),
            "竞速",
            55,
            font_size=18,
            align="left",
            group="reward",
        ),
        "speed_fill": _image_layer(
            "speed_fill",
            "竞速经验值",
            (
                reward.x + int(reward.w * 0.18),
                reward.y + int(reward.h * 0.585),
                int(reward.w * 0.58),
                int(reward.h * 0.08),
            ),
            "speed_fill",
            56,
            "stretch",
            group="reward",
        ),
        "speed_frame": _image_layer(
            "speed_frame",
            "竞速经验框",
            (
                reward.x + int(reward.w * 0.18),
                reward.y + int(reward.h * 0.585),
                int(reward.w * 0.58),
                int(reward.h * 0.08),
            ),
            "speed_frame",
            57,
            "stretch",
            group="reward",
        ),
        "speed_lv": _text_layer(
            "speed_lv",
            "竞速等级",
            (reward.x + int(reward.w * 0.79), reward.y + int(reward.h * 0.56), 110, 34),
            "竞速等级",
            58,
            value_type="level",
            font_size=22,
            align="left",
            group="reward",
        ),
        "rank_icon": _image_layer(
            "rank_icon",
            "段位图标",
            (
                reward.x + int(reward.w * 0.12),
                reward.y + int(reward.h * 0.68),
                int(reward.h * 0.28),
                int(reward.h * 0.28),
            ),
            "rank",
            58,
            group="reward",
        ),
        "rank_label": _text_layer(
            "rank_label",
            "段位文字",
            (reward.x + int(reward.w * 0.29), reward.y + int(reward.h * 0.72), 160, 34),
            "当前段位",
            58,
            font_size=22,
            align="left",
            group="reward",
        ),
        "upgrade_center": _image_layer(
            "upgrade_center",
            "升级中",
            (reward.centerx - 86, reward.y + int(reward.h * 0.24) - 26, 172, 52),
            "upgrade_center",
            59,
            group="reward",
        ),
        "upgrade_lt": _image_layer(
            "upgrade_lt",
            "升级左上",
            (reward.centerx - 96, reward.y + int(reward.h * 0.24) - 96, 54, 54),
            "upgrade_lt",
            58,
            group="reward",
        ),
        "upgrade_rt": _image_layer(
            "upgrade_rt",
            "升级右上",
            (reward.centerx + 42, reward.y + int(reward.h * 0.24) - 96, 54, 54),
            "upgrade_rt",
            58,
            group="reward",
        ),
        "upgrade_lb": _image_layer(
            "upgrade_lb",
            "升级左下",
            (reward.centerx - 96, reward.y + int(reward.h * 0.24) + 42, 54, 54),
            "upgrade_lb",
            58,
            group="reward",
        ),
        "upgrade_rb": _image_layer(
            "upgrade_rb",
            "升级右下",
            (reward.centerx + 42, reward.y + int(reward.h * 0.24) + 42, 54, 54),
            "upgrade_rb",
            58,
            group="reward",
        ),
        "flow3_prompt": _image_layer(
            "flow3_prompt",
            "流程3提示",
            (
                screen_w // 2 - prompt_w // 2,
                screen_h // 2 - prompt_h // 2,
                prompt_w,
                prompt_h,
            ),
            "flow3_prompt",
            70,
            "contain",
        ),
    }
    return layers


def _layer_rect(layer: Dict[str, Any]) -> pygame.Rect:
    rect = layer.get("rect", [0, 0, 0, 0])
    if isinstance(rect, (list, tuple)) and len(rect) == 4:
        return pygame.Rect(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
    return pygame.Rect(0, 0, 0, 0)


def _set_layer_rect(layer: Dict[str, Any], rect: pygame.Rect):
    layer["rect"] = [int(rect.x), int(rect.y), int(rect.w), int(rect.h)]


def _deep_merge_dict(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


class SettlementLayoutStore:
    def __init__(self, layout_path: str):
        self.layout_path = os.path.abspath(str(layout_path))
        self._default_design_layers = build_default_layout(DESIGN_SIZE, player_index=1)
        self._runtime_default_cache: Dict[
            Tuple[int, int, int], Dict[str, Dict[str, Any]]
        ] = {}
        self._mtime: Optional[float] = None
        self.layers: Dict[str, Dict[str, Any]] = {}
        self.reload(force=True)

    def _normalize_layers(self, raw_layers: Any) -> Dict[str, Dict[str, Any]]:
        normalized: Dict[str, Dict[str, Any]] = {
            layer_id: copy.deepcopy(layer)
            for layer_id, layer in self._default_design_layers.items()
        }
        if isinstance(raw_layers, dict):
            for layer_id, layer in raw_layers.items():
                if not isinstance(layer, dict):
                    continue
                key = str(layer_id)
                if key in normalized:
                    normalized[key] = _deep_merge_dict(normalized[key], layer)
                else:
                    normalized[key] = copy.deepcopy(layer)
        return normalized

    def reload(self, force: bool = False):
        current_mtime = None
        try:
            if os.path.isfile(self.layout_path):
                current_mtime = float(os.path.getmtime(self.layout_path))
        except Exception:
            current_mtime = None
        if (not force) and current_mtime == self._mtime and self.layers:
            return
        data = read_json(self.layout_path)
        self.layers = self._normalize_layers(data.get("layers"))
        self._mtime = current_mtime
        if not data or int(data.get("version", 0) or 0) != int(LAYOUT_VERSION):
            self.save()

    def reload_if_changed(self):
        self.reload(force=False)

    def save(self):
        self._mtime = None
        write_json(
            self.layout_path,
            {"version": LAYOUT_VERSION, "layers": self.layers},
        )
        try:
            if os.path.isfile(self.layout_path):
                self._mtime = float(os.path.getmtime(self.layout_path))
        except Exception:
            self._mtime = None

    def reset(self):
        self.layers = self._normalize_layers({})
        self.save()

    def runtime_defaults(
        self, screen_size: Tuple[int, int], player_index: int
    ) -> Dict[str, Dict[str, Any]]:
        key = (int(screen_size[0]), int(screen_size[1]), int(player_index))
        cached = self._runtime_default_cache.get(key)
        if cached is not None:
            return cached
        layers = build_default_layout(
            (int(screen_size[0]), int(screen_size[1])), player_index=int(player_index)
        )
        self._runtime_default_cache[key] = layers
        return layers

    def runtime_layers(
        self, screen_size: Tuple[int, int], player_index: int = 1
    ) -> Dict[str, Dict[str, Any]]:
        screen_w, screen_h = int(screen_size[0]), int(screen_size[1])
        sx = screen_w / float(DESIGN_SIZE[0])
        sy = screen_h / float(DESIGN_SIZE[1])
        scale = min(sx, sy)
        default_runtime = self.runtime_defaults((screen_w, screen_h), player_index)
        runtime_layers: Dict[str, Dict[str, Any]] = {}
        for layer_id, design_layer in self.layers.items():
            layer = copy.deepcopy(design_layer)
            base_design = self._default_design_layers.get(layer_id)
            base_runtime = copy.deepcopy(default_runtime.get(layer_id, design_layer))
            design_rect = _layer_rect(design_layer)
            if base_design is not None:
                base_design_rect = _layer_rect(base_design)
                default_runtime_rect = _layer_rect(base_runtime)
                runtime_rect = pygame.Rect(
                    int(
                        round(
                            default_runtime_rect.x
                            + (design_rect.x - base_design_rect.x) * sx
                        )
                    ),
                    int(
                        round(
                            default_runtime_rect.y
                            + (design_rect.y - base_design_rect.y) * sy
                        )
                    ),
                    int(
                        round(
                            default_runtime_rect.w
                            + (design_rect.w - base_design_rect.w) * sx
                        )
                    ),
                    int(
                        round(
                            default_runtime_rect.h
                            + (design_rect.h - base_design_rect.h) * sy
                        )
                    ),
                )
            else:
                runtime_rect = pygame.Rect(
                    int(round(design_rect.x * sx)),
                    int(round(design_rect.y * sy)),
                    int(round(design_rect.w * sx)),
                    int(round(design_rect.h * sy)),
                )
            _set_layer_rect(layer, runtime_rect)
            content_offset = layer.get("content_offset", [0.0, 0.0])
            if isinstance(content_offset, (list, tuple)) and len(content_offset) == 2:
                layer["content_offset"] = [
                    float(content_offset[0]) * sx,
                    float(content_offset[1]) * sy,
                ]
            text_style = layer.get("text_style")
            if isinstance(text_style, dict):
                runtime_style = copy.deepcopy(text_style)
                runtime_style["font_size"] = max(
                    8, int(round(float(text_style.get("font_size", 24) or 24) * scale))
                )
                runtime_style["stroke_width"] = max(
                    0, int(round(float(text_style.get("stroke_width", 0) or 0) * scale))
                )
                runtime_style["letter_spacing"] = int(
                    round(float(text_style.get("letter_spacing", 0) or 0) * scale)
                )
                layer["text_style"] = runtime_style
            runtime_layers[layer_id] = layer
        return runtime_layers
