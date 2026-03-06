import json
import os
import sys
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pygame
from core.工具 import 绘制底部联网与信用
from scenes.场景基类 import 场景基类
from ui.准备就绪动画 import (
    读取准备动画设置,
    加载准备动画图片,
    计算准备动画时间轴,
    计算准备动画区域,
    计算准备动画总时长,
    绘制准备就绪动画,
)


_项目根目录_缓存: str | None = None


def _取项目根目录() -> str:
    global _项目根目录_缓存
    if _项目根目录_缓存:
        return _项目根目录_缓存

    try:
        if getattr(sys, "frozen", False):
            起点 = os.path.dirname(os.path.abspath(sys.executable))
        else:
            起点 = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        起点 = os.getcwd()

    当前 = os.path.abspath(起点)
    for _ in range(10):
        if (
            os.path.isdir(os.path.join(当前, "core"))
            and os.path.isdir(os.path.join(当前, "ui"))
            and os.path.isdir(os.path.join(当前, "songs"))
        ):
            _项目根目录_缓存 = 当前
            return 当前
        上级 = os.path.dirname(当前)
        if 上级 == 当前:
            break
        当前 = 上级

    _项目根目录_缓存 = os.path.abspath(起点)
    return _项目根目录_缓存


def _安全读文本(路径: str) -> str:
    if not 路径 or (not os.path.isfile(路径)):
        return ""
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码, errors="strict") as f:
                return f.read()
        except Exception:
            continue
    try:
        with open(路径, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _安全读json(路径: str):
    if not 路径 or (not os.path.isfile(路径)):
        return None
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码, errors="strict") as f:
                return json.load(f)
        except Exception:
            continue
    try:
        with open(路径, "r", encoding="utf-8", errors="ignore") as f:
            return json.load(f)
    except Exception:
        return None


def _从设置参数文本提取(参数文本: str, 键名: str) -> str:
    try:
        参数文本 = str(参数文本 or "")
        m = re.search(rf"{re.escape(键名)}\s*=\s*([^\s]+)", 参数文本)
        if not m:
            return ""
        return str(m.group(1)).strip()
    except Exception:
        return ""


def _解析调速倍率(调速字符串: str) -> float:
    s = str(调速字符串 or "").strip()
    s = s.replace("x", "X")
    m = re.search(r"X\s*([0-9]+(?:\.[0-9]+)?)", s)
    if not m:
        try:
            return max(0.1, float(s))
        except Exception:
            return 3.0
    try:
        return max(0.1, float(m.group(1)))
    except Exception:
        return 3.0


def _解析大小倍率(设置参数: dict, 参数文本: str) -> float:
    # 你说“大小=设置参数文本”，所以优先从 参数文本 取；取不到再用 dict
    文本值 = _从设置参数文本提取(参数文本, "大小")
    候选 = 文本值 if 文本值 else str(设置参数.get("大小", "") or "")
    候选 = str(候选).strip()

    if not 候选:
        return 1.0

    if "放大" in 候选:
        return 1.0
    if "正常" in 候选:
        return 0.8

    # 允许：1.2 / 120% / 0.95
    try:
        if 候选.endswith("%"):
            v = float(候选[:-1].strip()) / 100.0
            return max(0.5, min(2.0, v))
        v = float(候选)
        return max(0.5, min(2.0, v))
    except Exception:
        return 1.0


def _解析背景模式(设置参数: dict, 参数文本: str) -> str:
    文本值 = _从设置参数文本提取(参数文本, "背景模式")
    候选 = 文本值 if 文本值 else str(
        设置参数.get("背景模式", 设置参数.get("变速", ""))
        or ""
    )
    候选 = str(候选).strip()
    if "视频" in 候选:
        return "视频"
    return "图片"


def _规范击中特效方案(方案: str) -> str:
    文本 = str(方案 or "").strip()
    if ("2" in 文本) or ("特效2" in 文本):
        return "击中特效2"
    return "击中特效1"


def _读取选歌设置json() -> dict:
    try:
        路径 = os.path.join(_取项目根目录(), "json", "选歌设置.json")
        数据 = _安全读json(路径)
        return dict(数据) if isinstance(数据, dict) else {}
    except Exception:
        return {}


def _构建设置参数文本(设置参数: dict, 背景文件名: str = "", 箭头文件名: str = "") -> str:
    参数 = dict(设置参数 or {})
    参数片段: List[str] = []
    顺序键 = ["背景模式", "谱面", "隐藏", "轨迹", "方向", "大小"]
    if ("背景模式" not in 参数) and ("变速" in 参数):
        参数["背景模式"] = 参数.get("变速")
    try:
        for 键 in 顺序键:
            if 键 in 参数:
                参数片段.append(f"{键}={参数.get(键)}")
        for 键, 值 in 参数.items():
            if 键 in 顺序键:
                continue
            参数片段.append(f"{键}={值}")
    except Exception:
        参数片段 = []

    if 背景文件名:
        参数片段.append(f"背景={背景文件名}")
    if 箭头文件名:
        参数片段.append(f"箭头={箭头文件名}")
    return "设置参数：" + ("  ".join(参数片段) if 参数片段 else "默认")


def _找同目录音频_按优先级(谱面路径: str) -> Optional[str]:
    目录 = os.path.dirname(os.path.abspath(谱面路径))
    if not os.path.isdir(目录):
        return None

    扩展优先 = [".ogg", ".mp3", ".wav"]
    全部候选: List[str] = []
    for 文件名 in os.listdir(目录):
        路径 = os.path.join(目录, 文件名)
        if not os.path.isfile(路径):
            continue
        低 = 文件名.lower()
        if any(低.endswith(ext) for ext in 扩展优先):
            全部候选.append(路径)

    if not 全部候选:
        return None

    基名 = os.path.splitext(os.path.basename(谱面路径))[0].lower()

    def _打分(p: str) -> Tuple[int, int, int]:
        fn = os.path.basename(p).lower()
        ext = os.path.splitext(fn)[1].lower()
        ext分 = {".ogg": 3, ".mp3": 2, ".wav": 1}.get(ext, 0)
        命中分 = 2 if (基名 and 基名 in fn) else 0
        大小 = int(os.path.getsize(p) / 1024)
        return (ext分, 命中分, 大小)

    全部候选.sort(key=_打分, reverse=True)
    return 全部候选[0]


def _解析_sm_music(sm文本: str, sm文件路径: str) -> Optional[str]:
    """
    优先读 #MUSIC:xxx;
    若是相对路径，按 sm 同目录拼接。
    """
    try:
        m = re.search(r"#MUSIC\s*:\s*([^;]+)\s*;", sm文本, flags=re.IGNORECASE)
        if not m:
            return None
        v = str(m.group(1)).strip().strip('"').strip("'")
        if not v:
            return None
        if os.path.isabs(v) and os.path.isfile(v):
            return v
        目录 = os.path.dirname(os.path.abspath(sm文件路径))
        p = os.path.join(目录, v)
        if os.path.isfile(p):
            return p
        # 有些谱面写的是子路径大小写混乱，Windows一般无所谓；这里仍做一次 exists
        if os.path.exists(p) and os.path.isfile(p):
            return p
        return None
    except Exception:
        return None


def _解析_offset(sm文本: str) -> float:
    try:
        m = re.search(r"#OFFSET\s*:\s*([^;]+)\s*;", sm文本, flags=re.IGNORECASE)
        if not m:
            return 0.0
        return float(m.group(1).strip())
    except Exception:
        return 0.0


def _深搜控件字典_按id(节点, 目标id: str) -> Optional[dict]:
    目标id = str(目标id or "").strip()
    if not 目标id:
        return None

    try:
        if isinstance(节点, dict):
            if str(节点.get("id", "") or "") == 目标id:
                return 节点
            for v in 节点.values():
                命中 = _深搜控件字典_按id(v, 目标id)
                if 命中 is not None:
                    return 命中
        elif isinstance(节点, list):
            for item in 节点:
                命中 = _深搜控件字典_按id(item, 目标id)
                if 命中 is not None:
                    return 命中
    except Exception:
        return None

    return None


def _取_stage背景矩形_屏幕坐标(
    谱面渲染器对象,
    屏幕尺寸: Tuple[int, int],
) -> Optional[pygame.Rect]:
    """
    ✅ 优先从 谱面渲染器._布局管理器_谱面渲染器._布局数据 里找 id="Stage背景"
    ✅ 找不到则用你给的默认坐标（设计坐标），按 1920x1080 做缩放
    """
    屏幕宽, 屏幕高 = int(屏幕尺寸[0]), int(屏幕尺寸[1])

    # 1) 优先：用渲染器内部布局管理器（缩放方式完全一致）
    try:
        布局 = getattr(谱面渲染器对象, "_布局管理器_谱面渲染器", None)
        if 布局 is not None and hasattr(布局, "取全局缩放"):
            比例 = float(布局.取全局缩放((屏幕宽, 屏幕高)))
            if 比例 <= 0:
                比例 = 1.0

            布局数据 = getattr(布局, "_布局数据", None)
            控件 = _深搜控件字典_按id(布局数据, "Stage背景")
            if isinstance(控件, dict):
                x = float(控件.get("x", 0.0))
                y = float(控件.get("y", 0.0))
                w = float(控件.get("w", 0.0))
                h = float(控件.get("h", 0.0))
                if w > 0 and h > 0:
                    return pygame.Rect(
                        int(x * 比例),
                        int(y * 比例),
                        int(w * 比例),
                        int(h * 比例),
                    )
    except Exception:
        pass

    # 2) 兜底：你提供的默认 Stage背景 参数（按 1920x1080 估算缩放）
    try:
        设计宽, 设计高 = 1920.0, 1080.0
        比例 = min(float(屏幕宽) / 设计宽, float(屏幕高) / 设计高)
        if 比例 <= 0:
            比例 = 1.0

        x = 1012.8444003964323
        y = -81.62824960883351
        w = 216.13899582481562
        h = 207.39766777724358

        return pygame.Rect(
            int(x * 比例),
            int(y * 比例),
            int(w * 比例),
            int(h * 比例),
        )
    except Exception:
        return None


from typing import Optional


def _提取sm标签值(sm文本: str, 标签名: str) -> str:
    """
    ✅ 兼容“有分号 / 没分号”的 SM 标签提取：
    - 从 #TAG: 后开始取
    - 遇到 ';' 结束
    - 若该标签没有分号：遇到“换行 + 可选空白 + #”（新标签起始）也视为结束
    - 支持标签值跨多行
    - 会删除每一行里的 // 注释
    """
    try:
        文本 = str(sm文本 or "").replace("\r\n", "\n").replace("\r", "\n")
        标签 = str(标签名 or "").strip()
        if (not 文本) or (not 标签):
            return ""

        # 用行首匹配更安全，避免误撞到 #NOTES 数据里奇怪的内容
        m = re.search(rf"(?im)^\s*#{re.escape(标签)}\s*:\s*", 文本)
        if not m:
            return ""

        i = int(m.end())
        j = i
        n = len(文本)

        while j < n:
            ch = 文本[j]
            if ch == ";":
                break

            if ch == "\n":
                # 没分号时：下一行（允许空白）如果以 # 开头，认为新标签开始
                k = j + 1
                while k < n and 文本[k] in (" ", "\t"):
                    k += 1
                if k < n and 文本[k] == "#":
                    break
            j += 1

        原始值 = 文本[i:j]
        if not 原始值:
            return ""

        # 逐行去掉 // 注释
        行列表 = 原始值.split("\n")
        去注释后 = []
        for 行 in 行列表:
            if "//" in 行:
                行 = 行.split("//", 1)[0]
            去注释后.append(行)

        值 = "".join(去注释后).strip()
        return 值
    except Exception:
        return ""


def _解析_displaybpm(sm文本: str) -> Optional[float]:
    """
    ✅ 优先解析 #DISPLAYBPM:131;
    - 只取第一个数字
    - 解析失败返回 None
    """
    try:
        原始 = _提取sm标签值(sm文本, "DISPLAYBPM")
        原始 = str(原始 or "").strip()
        if not 原始:
            return None

        数字们 = re.findall(r"-?\d+(?:\.\d+)?", 原始)
        if not 数字们:
            return None

        v = float(数字们[0])
        if v <= 0:
            return None
        return v
    except Exception:
        return None


def _解析_bpms(sm文本: str) -> List[Tuple[float, float]]:
    """
    ✅ 计时优先 BPMS，其次 DISPLAYBPM 兜底
    返回：[(开始beat, bpm), ...]，至少 1 条
    """
    原始 = _提取sm标签值(sm文本, "BPMS")
    结果: List[Tuple[float, float]] = []

    if 原始:
        body = str(原始).strip().strip(";").strip()
        for part in body.split(","):
            p = str(part or "").strip()
            if (not p) or ("=" not in p):
                continue
            a, b = p.split("=", 1)
            try:
                beat = float(a.strip())
                数字们 = re.findall(r"-?\d+(?:\.\d+)?", str(b))
                if not 数字们:
                    continue
                bpm = float(数字们[0])
                if bpm <= 0:
                    continue
                结果.append((float(beat), float(bpm)))
            except Exception:
                continue

    if 结果:
        # 去重 + 排序（同 beat 取最后一个）
        临时: Dict[float, float] = {}
        for beat, bpm in 结果:
            临时[float(beat)] = float(bpm)
        out = [(k, 临时[k]) for k in sorted(临时.keys())]
        return out

    # ✅ BPMS 没有/解析失败 -> DISPLAYBPM 兜底成常速
    显示bpm = _解析_displaybpm(sm文本)
    if 显示bpm is not None:
        return [(0.0, float(显示bpm))]

    return [(0.0, 120.0)]


def _生成时间轴段(bpms: List[Tuple[float, float]]) -> List[Tuple[float, float, float]]:
    """
    段: (段起beat, 段起秒, bpm)
    """
    段: List[Tuple[float, float, float]] = []
    for i, (beat, bpm) in enumerate(bpms):
        if i == 0:
            段.append((float(beat), 0.0, float(bpm)))
            continue
        上beat, 上秒, 上bpm = 段[-1]
        deltaBeat = float(beat) - float(上beat)
        if deltaBeat < 0:
            continue
        增量秒 = deltaBeat * (60.0 / float(上bpm)) if 上bpm > 0 else 0.0
        段.append((float(beat), float(上秒) + float(增量秒), float(bpm)))
    return 段 if 段 else [(0.0, 0.0, 120.0)]


def _beat转秒(beat: float, 段: List[Tuple[float, float, float]]) -> float:
    # 二分找 <= beat 的最后一段
    lo, hi = 0, len(段) - 1
    idx = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if 段[mid][0] <= beat:
            idx = mid
            lo = mid + 1
        else:
            hi = mid - 1
    段起beat, 段起秒, bpm = 段[idx]
    delta = float(beat) - float(段起beat)
    return float(段起秒) + (delta * (60.0 / float(bpm)) if bpm > 0 else 0.0)


@dataclass
class 音符事件:
    轨道序号: int
    开始秒: float
    结束秒: float
    开始beat: float
    结束beat: float
    类型: str  # "tap" / "hold"


def _解析_sm_notes_选谱面(sm文本: str, 优先double: bool = False) -> Tuple[str, int, str]:
    """
    选中一个 #NOTES 块返回 (notedata第6段, 列数, charttype)
    默认优先 pump-single；当 优先double=True 时优先 pump-double。
    """
    notes块列表 = []
    for m in re.finditer(r"#NOTES\s*:(.*?);", sm文本, flags=re.IGNORECASE | re.DOTALL):
        notes块列表.append(m.group(1))

    候选: List[Tuple[str, str, int]] = []
    for blk in notes块列表:
        parts = blk.split(":")
        if len(parts) < 6:
            continue
        charttype = (parts[0] or "").strip().lower()
        notedata = parts[5] or ""
        列数 = 5
        try:
            纯 = str(notedata or "").replace("\r", "")
            for 小节 in 纯.split(","):
                行们 = [
                    ln.strip()
                    for ln in 小节.split("\n")
                    if ln.strip() and (not ln.strip().startswith("//"))
                ]
                if 行们:
                    列数 = max(1, len(行们[0]))
                    break
        except Exception:
            列数 = 5
        候选.append((charttype, notedata, int(列数)))

    if not 候选:
        return "", 5, ""

    # 根据玩法偏好选谱面，最后兜底按列数最大的 chart。
    选中chart: Tuple[str, str, int]
    选中chart = 候选[0]
    if bool(优先double):
        for c in 候选:
            if "pump-double" in c[0]:
                选中chart = c
                break
        else:
            for c in 候选:
                if "pump-single" in c[0]:
                    选中chart = c
                    break
    else:
        for c in 候选:
            if "pump-single" in c[0]:
                选中chart = c
                break
        else:
            for c in 候选:
                if "pump-double" in c[0]:
                    选中chart = c
                    break

    if not (str(选中chart[0] or "").strip()):
        选中chart = max(候选, key=lambda it: int(it[2]))

    纯 = (选中chart[1] or "").replace("\r", "")
    列数 = int(max(1, int(选中chart[2] or 5)))
    return 纯, 列数, str(选中chart[0] or "")


def _构建_sm事件列表(
    sm路径: str, 优先double: bool = False
) -> Tuple[List[音符事件], float, float, int, str]:
    """
    返回：(事件列表, offset, 总时长秒, 列数, charttype)

    ✅ 关键修复：事件时间轴直接应用 SM OFFSET
    - SM 里通常是：note_song_time = beat_to_seconds(beat) - offset
    - 所以我们把 offset 折算进事件秒，后续“谱面秒 == 音频秒”最稳

    ✅ 时间轴按 BPMS 走
    """
    sm文本 = _安全读文本(sm路径)
    if not sm文本:
        return [], 0.0, 0.0, 5, ""

    offset = _解析_offset(sm文本)
    bpms = _解析_bpms(sm文本)
    bpm段 = _生成时间轴段(bpms)

    notedata, 列数, charttype = _解析_sm_notes_选谱面(sm文本, 优先double=bool(优先double))
    if not notedata:
        return [], offset, 0.0, 5, ""

    小节列表 = [m.strip() for m in notedata.split(",")]
    事件: List[音符事件] = []

    未闭合: Dict[int, Tuple[float, float]] = {}  # 轨道 -> (开始秒, 开始beat)
    最大秒 = 0.0

    for 小节序号, 小节 in enumerate(小节列表):
        行们 = [
            ln.strip()
            for ln in 小节.split("\n")
            if ln.strip() and (not ln.strip().startswith("//"))
        ]
        if not 行们:
            continue

        分割数 = len(行们)

        for 行序号, 行 in enumerate(行们):
            if len(行) < 列数:
                continue

            beat = float(小节序号) * 4.0 + (float(行序号) / float(max(1, 分割数))) * 4.0

            # ✅ 核心：把 offset 折算进事件秒
            t = _beat转秒(beat, bpm段) - float(offset)

            for 列 in range(列数):
                ch = 行[列]
                if ch == "0":
                    continue

                if ch == "1":
                    事件.append(
                        音符事件(
                            轨道序号=int(列),
                            开始秒=float(t),
                            结束秒=float(t),
                            开始beat=float(beat),
                            结束beat=float(beat),
                            类型="tap",
                        )
                    )
                    最大秒 = max(最大秒, float(t))
                    continue

                if ch in ("2", "4"):  # hold/roll 头
                    未闭合[int(列)] = (float(t), float(beat))
                    最大秒 = max(最大秒, float(t))
                    continue

                if ch == "3":  # hold 尾
                    if int(列) in 未闭合:
                        st秒, stbeat = 未闭合.pop(int(列))
                        ed秒 = float(t)
                        edbeat = float(beat)

                        if ed秒 < st秒:
                            st秒, ed秒 = ed秒, st秒
                            stbeat, edbeat = edbeat, stbeat

                        事件.append(
                            音符事件(
                                轨道序号=int(列),
                                开始秒=float(st秒),
                                结束秒=float(ed秒),
                                开始beat=float(stbeat),
                                结束beat=float(edbeat),
                                类型="hold",
                            )
                        )
                        最大秒 = max(最大秒, ed秒)
                    continue

                # 其他类型先忽略（M/K/L 等）

    事件.sort(key=lambda e: e.开始秒)
    总时长 = max(0.0, 最大秒 + 2.0)
    return 事件, float(offset), float(总时长), int(列数), str(charttype or "")


class 皮肤资源:
    """
    ✅ 只用文件夹皮肤
    ✅ 右上/右下缺图时：用左侧水平翻转兜底（含判定区）
    """

    def __init__(self, 皮肤目录: str):
        self.皮肤目录 = os.path.abspath(str(皮肤目录 or ""))
        self._缓存: Dict[str, pygame.Surface] = {}
        self._翻转缓存: Dict[str, pygame.Surface] = {}

        # 预构建：忽略大小写查找
        self._文件表小写: Dict[str, str] = {}
        try:
            if os.path.isdir(self.皮肤目录):
                for n in os.listdir(self.皮肤目录):
                    p = os.path.join(self.皮肤目录, n)
                    if os.path.isfile(p):
                        self._文件表小写[n.lower()] = n
        except Exception:
            self._文件表小写 = {}

    def _找文件_忽略大小写(self, 文件名: str) -> Optional[str]:
        if not 文件名:
            return None
        key = 文件名.lower()
        真名 = self._文件表小写.get(key)
        if 真名:
            p = os.path.join(self.皮肤目录, 真名)
            return p if os.path.isfile(p) else None
        p2 = os.path.join(self.皮肤目录, 文件名)
        return p2 if os.path.isfile(p2) else None

    def _读png(self, 文件名: str) -> Optional[pygame.Surface]:
        if 文件名 in self._缓存:
            return self._缓存[文件名]
        路径 = self._找文件_忽略大小写(文件名)
        if not 路径:
            return None
        try:
            图 = pygame.image.load(路径).convert_alpha()
            self._缓存[文件名] = 图
            return 图
        except Exception:
            return None

    @staticmethod
    def _解析网格(文件名: str) -> Tuple[int, int]:
        base = os.path.basename(文件名).lower()
        m = re.findall(r"(\d+)\s*x\s*(\d+)\.png$", base)
        if not m:
            return (1, 1)
        a, b = m[-1]
        return (max(1, int(a)), max(1, int(b)))

    @staticmethod
    def _裁帧(图: pygame.Surface, 列: int, 行: int, 帧索引: int) -> pygame.Surface:
        w, h = 图.get_width(), 图.get_height()
        单w = max(1, w // max(1, 列))
        单h = max(1, h // max(1, 行))
        总帧 = max(1, 列 * 行)
        帧索引 = max(0, min(总帧 - 1, int(帧索引)))
        行号 = 帧索引 // 列
        列号 = 帧索引 % 列
        rect = pygame.Rect(列号 * 单w, 行号 * 单h, 单w, 单h)
        return 图.subsurface(rect).copy()

    def _翻转(self, 图: pygame.Surface, 键: str) -> pygame.Surface:
        if 键 in self._翻转缓存:
            return self._翻转缓存[键]
        翻 = pygame.transform.flip(图, True, False)
        self._翻转缓存[键] = 翻
        return 翻

    def 取点按(self, 方向名: str) -> Optional[pygame.Surface]:
        候选名 = [
            f"{方向名} Tap Note 3x2.png",
            f"{方向名} Tap Note (doubleres) 3x2.png",
        ]
        图 = None
        用名 = ""
        for nm in 候选名:
            图 = self._读png(nm)
            if 图:
                用名 = nm
                break
        if 图:
            列, 行 = self._解析网格(用名)
            return self._裁帧(图, 列, 行, 帧索引=0)

        if 方向名 == "UpRight":
            左 = self.取点按("UpLeft")
            return self._翻转(左, "Flip:UpLeft:Tap") if 左 else None
        if 方向名 == "DownRight":
            左 = self.取点按("DownLeft")
            return self._翻转(左, "Flip:DownLeft:Tap") if 左 else None
        return None

    def 取判定区(self, 方向名: str) -> Optional[pygame.Surface]:
        # Center / UpLeft / DownLeft 优先读 png；右侧用翻转兜底
        if 方向名 in ("Center", "UpLeft", "DownLeft"):
            候选名 = [
                f"{方向名} Ready Receptor 1x3.png",
                f"{方向名} Ready Receptor (doubleres) 1x3.png",
            ]
            图 = None
            用名 = ""
            for nm in 候选名:
                图 = self._读png(nm)
                if 图:
                    用名 = nm
                    break
            if 图:
                列, 行 = self._解析网格(用名)
                # 取中间帧更像“Ready”
                return self._裁帧(图, 列, 行, 帧索引=1)

            # 再兜底 outline
            outline = self._读png("Center Outline Receptor.png")
            return outline

        if 方向名 == "UpRight":
            左 = self.取判定区("UpLeft")
            return self._翻转(左, "Flip:UpLeft:Receptor") if 左 else None
        if 方向名 == "DownRight":
            左 = self.取判定区("DownLeft")
            return self._翻转(左, "Flip:DownLeft:Receptor") if 左 else None
        return None

    def 取长按身体(self, 方向名: str) -> Optional[pygame.Surface]:
        候选名 = [
            f"{方向名} Hold Body Active 6x1.png",
            f"{方向名} Hold Body active (doubleres) 6x1.png",
            f"{方向名} Hold Body Active (doubleres) 6x1.png",
        ]
        图 = None
        用名 = ""
        for nm in 候选名:
            图 = self._读png(nm)
            if 图:
                用名 = nm
                break
        if 图:
            列, 行 = self._解析网格(用名)
            return self._裁帧(图, 列, 行, 帧索引=0)

        if 方向名 == "UpRight":
            左 = self.取长按身体("UpLeft")
            return self._翻转(左, "Flip:UpLeft:HoldBody") if 左 else None
        if 方向名 == "DownRight":
            左 = self.取长按身体("DownLeft")
            return self._翻转(左, "Flip:DownLeft:HoldBody") if 左 else None
        return None

    def 取长按尾巴(self, 方向名: str) -> Optional[pygame.Surface]:
        候选名 = [
            f"{方向名} Hold BottomCap Active 6x1.png",
            f"{方向名} Hold BottomCap active (doubleres) 6x1.png",
            f"{方向名} Hold BottomCap Active (doubleres) 6x1.png",
        ]
        图 = None
        用名 = ""
        for nm in 候选名:
            图 = self._读png(nm)
            if 图:
                用名 = nm
                break
        if 图:
            列, 行 = self._解析网格(用名)
            return self._裁帧(图, 列, 行, 帧索引=0)

        if 方向名 == "UpRight":
            左 = self.取长按尾巴("UpLeft")
            return self._翻转(左, "Flip:UpLeft:HoldCap") if 左 else None
        if 方向名 == "DownRight":
            左 = self.取长按尾巴("DownLeft")
            return self._翻转(左, "Flip:DownLeft:HoldCap") if 左 else None
        return None


class 场景_谱面播放器(场景基类):
    名称 = "谱面播放器"
    目标帧率 = 120

    def __init__(self, 上下文: dict):
        super().__init__(上下文)

        self._载荷: Dict = {}

        self._sm路径: str = ""
        self._sm文本: str = ""

        self._事件: List[音符事件] = []

        self._谱面总时长秒: float = 0.0
        self._offset: float = 0.0

        self._播放中: bool = False
        self._起始系统秒: float = 0.0
        self._暂停时刻谱面秒: float = 0.0
        self._当前谱面秒: float = 0.0

        # ✅ 新：玩法判定/计分（逻辑拆出去）
        self._判定系统 = None
        self._计分系统 = None
        self._是否自动模式: bool = False  # F2切换：自动判定（用来调UI/对齐音频）
        self._输入补偿秒: float = 0.0  # 你后续可做“延迟校准”（默认0）

        # 判定光
        self._判定光: List[float] = [0.0] * 5
        self._判定光衰减每秒: float = 2.8

        # 音频
        self._音频路径: Optional[str] = None
        self._音频可用: bool = False
        self._音频已开始: bool = False
        self._音频暂停中: bool = False
        self._音频开始系统秒: float = 0.0

        # 轨道/皮肤
        self._轨道方向名 = ["DownLeft", "UpLeft", "Center", "UpRight", "DownRight"]
        self._轨道数: int = 5
        self._谱面列数: int = 5
        self._谱面chart类型: str = ""
        self._是否双踏板模式: bool = False

        self._皮肤目录: str = ""
        self._皮肤: Optional[皮肤资源] = None
        self._点按图: List[Optional[pygame.Surface]] = [None] * 5
        self._长按身体图: List[Optional[pygame.Surface]] = [None] * 5
        self._长按尾巴图: List[Optional[pygame.Surface]] = [None] * 5
        self._判定区图: List[Optional[pygame.Surface]] = [None] * 5

        # 背景
        self._背景原图: Optional[pygame.Surface] = None
        self._背景图片路径: str = ""
        self._背景缩放缓存: Optional[pygame.Surface] = None
        self._背景缩放尺寸: Tuple[int, int] = (0, 0)
        self._背景视频路径: str = ""
        self._背景视频播放器 = None
        self._背景暗层缓存: Optional[pygame.Surface] = None
        self._背景暗层尺寸: Tuple[int, int] = (0, 0)

        # 字体
        self._字体: Optional[pygame.font.Font] = None
        self._小字体: Optional[pygame.font.Font] = None

        # 布局
        self._屏幕尺寸: Tuple[int, int] = (0, 0)
        self._血条高度: int = 64
        self._血条区域: pygame.Rect = pygame.Rect(0, 0, 0, 0)

        self._信息高度: int = 22
        self._信息y: int = 0

        self._顶部y: int = 0
        self._判定线y: int = 0
        self._底部y: int = 0

        self._轨道总宽: int = 560
        self._轨道起x: int = 0
        self._单轨宽: int = 0

        # 视觉参数
        self._卷轴速度倍率: float = 3.0
        self._滚动速度px每秒: float = 1260.0
        self._尺寸倍率: float = 1.0
        self._箭头默认缩放: float = 1.2
        self._轨迹模式: str = "正常"
        self._隐藏模式: str = "关闭"
        self._方向模式: str = "关闭"
        self._背景模式: str = "图片"
        self._谱面设置: str = "正常"
        self._击中特效方案: str = "击中特效1"

        # 血条/HP
        self._总血量上限HP: int = 1200
        self._显示血量上限HP: int = 1000
        self._隐藏血量HP: int = 200
        self._初始血量HP: int = 700
        self._判定统计 = {"perfect": 0, "cool": 0, "good": 0, "miss": 0}
        self._总血量HP: int = int(self._初始血量HP)

        # 兼容旧逻辑的显示比例缓存
        self._血量: float = 0.50
        self._入场系统秒: float = time.perf_counter()

        # 满血爆炸（暂时保留，不影响玩法）
        self._爆炸剩余秒: float = 0.0
        self._爆炸粒子: List[Tuple[float, float, float, float, float]] = []
        self._已触发满血爆炸: bool = False

        # 头像缓存
        self._头像图缓存 = None
        self._头像图_缓存key: str = ""

        self._错误提示: str = ""
        self._上次系统秒: float = time.perf_counter()
        self._歌曲名: str = ""
        self._星级: int = 0
        self._操作反馈文本: str = ""
        self._操作反馈剩余秒: float = 0.0
        self._操作反馈总秒: float = 1.35
        self._布局调试设置路径: str = os.path.join(
            _取项目根目录(), "json", "谱面布局调试器_设置.json"
        )
        self._布局调试设置_mtime: float = -2.0
        self._调试背景蒙板不透明度: float = 224.0 / 255.0
        self._调试血条颜色: Tuple[int, int, int] = (181, 23, 203)
        self._调试血条亮度: float = 1.0
        self._调试血条不透明度: float = 0.5
        self._调试血条晃荡速度: float = 2.7
        self._调试血条晃荡幅度: float = 5.0
        self._调试暴走血条速度: float = 150.0
        self._调试暴走血条不透明度: float = 1.0
        self._调试暴走血条羽化: float = 8.0
        self._调试头像框特效速度: float = 30.0
        self._调试圆环频谱最大长度: int = 16
        self._调试圆环频谱启用旋转: bool = False
        self._调试圆环频谱背景板转速: float = 36.0
        self._调试圆环频谱变化落差: float = 1.0
        self._调试圆环频谱线条数量: int = 200
        self._调试圆环频谱线条粗细: int = 2
        self._调试圆环频谱线条间隔: int = 1
        self._调试双踏板左X偏移: float = 0.0
        self._调试双踏板右X偏移: float = 0.0
        self._调试双踏板左Y偏移: float = 0.0
        self._调试双踏板右Y偏移: float = 0.0
        self._双踏板强制判定线y: Optional[int] = None
        self._双踏板入场Y锁定至秒: float = 0.0
        self._双踏板入场锁定判定线y: Optional[int] = None
        self._双踏板入场待首帧校正: bool = False
        self._性能模式: bool = False
        self._准备动画设置路径: str = os.path.join(
            _取项目根目录(), "json", "准备就绪动画_设置.json"
        )
        self._准备动画设置: Dict[str, float] = {}
        self._准备动画背景无蒙版: Optional[pygame.Surface] = None
        self._准备动画基础场景图: Optional[pygame.Surface] = None
        self._准备动画判定区图层: Optional[pygame.Surface] = None
        self._准备动画判定区矩形: Optional[pygame.Rect] = None
        self._准备动画绘制缓存: Dict[str, Any] = {}
        self._准备动画图: Dict[int, pygame.Surface] = {}
        self._准备音效 = None
        self._准备音效通道 = None
        self._准备音效已播放 = False
        self._默认背景视频目录: str = os.path.join(
            _取项目根目录(), "backmovies", "游戏中"
        )
        self._背景暗层alpha: int = 224
        self._背景暗层缓存alpha: int = -1
        self._视频背景关闭: bool = False
        self._暂停菜单开启: bool = False
        self._暂停菜单索引: int = 0
        self._暂停菜单打开前播放中: bool = False
        self._暂停菜单项矩形: List[pygame.Rect] = []
        self._暂停菜单关闭按钮: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self._联网原图: Optional[pygame.Surface] = None
        self._双踏板左轨道中心列表: List[int] = []
        self._双踏板右轨道中心列表: List[int] = []
        self._事件左渲染: List[音符事件] = []
        self._事件右渲染: List[音符事件] = []
        self._谱面渲染器_右 = None

        self._按键到轨道: Dict[int, int] = {}
        self._轨道到按键列表: Dict[int, List[int]] = {}
        self._刷新按键映射()

    def _同步渲染器按键反馈映射(self):
        try:
            双踏板 = bool(getattr(self, "_是否双踏板模式", False))
            左映射: Dict[int, List[int]] = {}
            for i in range(5):
                左映射[i] = list(getattr(self, "_轨道到按键列表", {}).get(i, []) or [])
            if self._谱面渲染器 is not None and hasattr(self._谱面渲染器, "设置按键反馈映射"):
                self._谱面渲染器.设置按键反馈映射(左映射)

            if 双踏板 and getattr(self, "_谱面渲染器_右", None) is not None:
                右映射: Dict[int, List[int]] = {}
                for i in range(5):
                    右映射[i] = list(
                        getattr(self, "_轨道到按键列表", {}).get(i + 5, []) or []
                    )
                if hasattr(self._谱面渲染器_右, "设置按键反馈映射"):
                    self._谱面渲染器_右.设置按键反馈映射(右映射)
        except Exception:
            pass

    def _刷新按键映射(self):
        方向文本 = str(getattr(self, "_方向模式", "关闭") or "关闭").strip()
        是否反向 = bool("反向" in 方向文本)

        if bool(getattr(self, "_是否双踏板模式", False)):
            # 左手：Z/C/S/Q/E -> 左侧5轨（0..4）
            # 右手：1/3/5/7/9 -> 右侧5轨（5..9）
            按键到轨道 = {
                pygame.K_z: 0,
                pygame.K_c: 4,
                pygame.K_s: 2,
                pygame.K_q: 1,
                pygame.K_e: 3,
                pygame.K_1: 5,
                pygame.K_KP1: 5,
                pygame.K_3: 9,
                pygame.K_KP3: 9,
                pygame.K_5: 7,
                pygame.K_KP5: 7,
                pygame.K_7: 6,
                pygame.K_KP7: 6,
                pygame.K_9: 8,
                pygame.K_KP9: 8,
            }
            轨道到按键列表 = {
                0: [pygame.K_z],
                1: [pygame.K_q],
                2: [pygame.K_s],
                3: [pygame.K_e],
                4: [pygame.K_c],
                5: [pygame.K_1, pygame.K_KP1],
                6: [pygame.K_7, pygame.K_KP7],
                7: [pygame.K_5, pygame.K_KP5],
                8: [pygame.K_9, pygame.K_KP9],
                9: [pygame.K_3, pygame.K_KP3],
            }

            if 是否反向:
                按键到轨道[pygame.K_1] = 8
                按键到轨道[pygame.K_KP1] = 8
                按键到轨道[pygame.K_9] = 5
                按键到轨道[pygame.K_KP9] = 5
                按键到轨道[pygame.K_3] = 6
                按键到轨道[pygame.K_KP3] = 6
                按键到轨道[pygame.K_7] = 9
                按键到轨道[pygame.K_KP7] = 9
                轨道到按键列表[5] = [pygame.K_9, pygame.K_KP9]
                轨道到按键列表[6] = [pygame.K_3, pygame.K_KP3]
                轨道到按键列表[8] = [pygame.K_1, pygame.K_KP1]
                轨道到按键列表[9] = [pygame.K_7, pygame.K_KP7]

            self._按键到轨道 = 按键到轨道
            self._轨道到按键列表 = 轨道到按键列表
            self._同步渲染器按键反馈映射()
            return

        # 单踏板：数字键映射（兼容小键盘）
        按键到轨道 = {
            pygame.K_1: 0,
            pygame.K_KP1: 0,
            pygame.K_3: 4,
            pygame.K_KP3: 4,
            pygame.K_5: 2,
            pygame.K_KP5: 2,
            pygame.K_7: 1,
            pygame.K_KP7: 1,
            pygame.K_9: 3,
            pygame.K_KP9: 3,
        }
        轨道到按键列表 = {
            0: [pygame.K_1, pygame.K_KP1],
            1: [pygame.K_7, pygame.K_KP7],
            2: [pygame.K_5, pygame.K_KP5],
            3: [pygame.K_9, pygame.K_KP9],
            4: [pygame.K_3, pygame.K_KP3],
        }

        if 是否反向:
            按键到轨道[pygame.K_1] = 3
            按键到轨道[pygame.K_KP1] = 3
            按键到轨道[pygame.K_9] = 0
            按键到轨道[pygame.K_KP9] = 0
            按键到轨道[pygame.K_3] = 1
            按键到轨道[pygame.K_KP3] = 1
            按键到轨道[pygame.K_7] = 4
            按键到轨道[pygame.K_KP7] = 4
            轨道到按键列表[0] = [pygame.K_9, pygame.K_KP9]
            轨道到按键列表[1] = [pygame.K_3, pygame.K_KP3]
            轨道到按键列表[3] = [pygame.K_1, pygame.K_KP1]
            轨道到按键列表[4] = [pygame.K_7, pygame.K_KP7]

        self._按键到轨道 = 按键到轨道
        self._轨道到按键列表 = 轨道到按键列表
        self._同步渲染器按键反馈映射()

    def _拆分双踏板渲染事件(self):
        self._事件左渲染 = []
        self._事件右渲染 = []
        for e in list(getattr(self, "_事件", []) or []):
            try:
                轨道 = int(getattr(e, "轨道序号", -1))
            except Exception:
                continue
            if 0 <= 轨道 < 5:
                self._事件左渲染.append(e)
            elif 5 <= 轨道 < 10:
                self._事件右渲染.append(
                    音符事件(
                        轨道序号=int(轨道 - 5),
                        开始秒=float(getattr(e, "开始秒", 0.0) or 0.0),
                        结束秒=float(getattr(e, "结束秒", 0.0) or 0.0),
                        开始beat=float(getattr(e, "开始beat", 0.0) or 0.0),
                        结束beat=float(getattr(e, "结束beat", 0.0) or 0.0),
                        类型=str(getattr(e, "类型", "tap") or "tap"),
                    )
                )

    def _同步双踏板渲染器(self):
        if not bool(getattr(self, "_是否双踏板模式", False)):
            self._谱面渲染器_右 = None
            return
        try:
            from ui.谱面渲染器 import 谱面渲染器
        except Exception:
            self._谱面渲染器_右 = None
            return
        if self._谱面渲染器_右 is None:
            try:
                self._谱面渲染器_右 = 谱面渲染器()
            except Exception:
                self._谱面渲染器_右 = None
                return
        try:
            if self._谱面渲染器_右 is not None and str(self._皮肤目录 or "").strip():
                self._谱面渲染器_右.设置皮肤(self._皮肤目录)
        except Exception:
            pass
        try:
            self._应用击中特效方案到渲染器()
        except Exception:
            pass
        self._同步渲染器按键反馈映射()

    def _触发轨道按下反馈(self, 轨道: int):
        try:
            轨道 = int(轨道)
        except Exception:
            return
        if not bool(getattr(self, "_是否双踏板模式", False)):
            try:
                if self._谱面渲染器 is not None:
                    self._谱面渲染器.触发按下反馈(int(轨道))
            except Exception:
                pass
            return
        try:
            if 0 <= 轨道 < 5 and self._谱面渲染器 is not None:
                self._谱面渲染器.触发按下反馈(int(轨道))
            elif 5 <= 轨道 < 10 and self._谱面渲染器_右 is not None:
                self._谱面渲染器_右.触发按下反馈(int(轨道 - 5))
        except Exception:
            pass

    def _触发轨道击中特效(self, 轨道: int, 判定: str, 发生谱面秒: Optional[float] = None):
        判定 = str(判定 or "").lower()
        if not 判定 or 判定 == "miss":
            return
        if 发生谱面秒 is None:
            try:
                发生谱面秒 = float(getattr(self, "_当前谱面秒", 0.0) or 0.0)
            except Exception:
                发生谱面秒 = 0.0
        try:
            轨道 = int(轨道)
        except Exception:
            return
        if not bool(getattr(self, "_是否双踏板模式", False)):
            try:
                if self._谱面渲染器 is not None:
                    self._谱面渲染器.触发击中特效(int(轨道), 判定, float(发生谱面秒))
            except Exception:
                pass
            return
        try:
            if 0 <= 轨道 < 5 and self._谱面渲染器 is not None:
                self._谱面渲染器.触发击中特效(int(轨道), 判定, float(发生谱面秒))
            elif 5 <= 轨道 < 10 and self._谱面渲染器_右 is not None:
                self._谱面渲染器_右.触发击中特效(int(轨道 - 5), 判定, float(发生谱面秒))
        except Exception:
            pass

    def _按回报播放计数动画_到渲染器(self, 回报列表, 起始连击: int, 目标渲染器):
        if (not 回报列表) or (目标渲染器 is None):
            return
        当前连击 = int(max(0, 起始连击))
        for 回报 in 回报列表:
            判定 = str(getattr(回报, "判定", "") or "").lower()
            类型 = str(getattr(回报, "类型", "") or "")
            try:
                连击增量 = int(max(0, int(getattr(回报, "连击增量", 0) or 0)))
            except Exception:
                连击增量 = 0

            if not 判定:
                continue

            if 判定 == "miss":
                当前连击 = 0
                目标渲染器.触发计数动画("miss", 0)
                continue

            if 类型 == "hold_tick":
                if 连击增量 <= 0:
                    continue
                for 子combo in range(当前连击 + 1, 当前连击 + 连击增量 + 1):
                    目标渲染器.触发计数动画(判定, int(子combo))
                当前连击 += int(连击增量)
                continue

            当前连击 += int(max(1, 连击增量))
            目标渲染器.触发计数动画(判定, int(当前连击))

    def _取双踏板轨道中心列表(self) -> Tuple[List[int], List[int]]:
        屏幕宽 = int(max(1, self._屏幕尺寸[0] if self._屏幕尺寸 else 0))
        if 屏幕宽 <= 0:
            return ([], [])

        实际缩放 = float(self._箭头默认缩放) * float(self._尺寸倍率)
        箭头宽 = int(self._取箭头目标宽(实际缩放))
        间距 = int(max(22, int(箭头宽 * 0.88)))
        槽宽 = int(max(箭头宽 + 10, int(箭头宽 * 1.08)))
        组宽 = int(槽宽 + 4 * 间距)

        边距 = int(max(20, 屏幕宽 * 0.02))
        中缝 = int(max(22, 屏幕宽 * 0.02))
        最大组宽 = int(max(200, (屏幕宽 - 边距 * 2 - 中缝) // 2))
        if 组宽 > 最大组宽:
            缩放 = float(max(0.5, 最大组宽 / float(max(1, 组宽))))
            间距 = int(max(18, int(间距 * 缩放)))
            槽宽 = int(max(30, int(槽宽 * 缩放)))
            组宽 = int(槽宽 + 4 * 间距)

        左起x = int((屏幕宽 - (组宽 * 2 + 中缝)) // 2)
        右起x = int(左起x + 组宽 + 中缝)

        左中心 = [int(左起x + 槽宽 // 2 + i * 间距) for i in range(5)]
        右中心 = [int(右起x + 槽宽 // 2 + i * 间距) for i in range(5)]
        偏左x = float(getattr(self, "_调试双踏板左X偏移", 0.0) or 0.0)
        偏右x = float(getattr(self, "_调试双踏板右X偏移", 0.0) or 0.0)
        左中心 = [int(round(float(v) + 偏左x)) for v in 左中心]
        右中心 = [int(round(float(v) + 偏右x)) for v in 右中心]
        self._双踏板左轨道中心列表 = list(左中心)
        self._双踏板右轨道中心列表 = list(右中心)
        return (左中心, 右中心)

    def _刷新布局调试设置(self, 强制: bool = False):
        路径 = str(getattr(self, "_布局调试设置路径", "") or "").strip()
        try:
            mtime = float(os.path.getmtime(路径)) if (路径 and os.path.isfile(路径)) else -1.0
        except Exception:
            mtime = -1.0

        if (not 强制) and float(mtime) == float(getattr(self, "_布局调试设置_mtime", -2.0)):
            return

        self._布局调试设置_mtime = float(mtime)
        数据 = _安全读json(路径)
        if not isinstance(数据, dict):
            self._应用圆环频谱调试设置()
            return

        try:
            self._调试背景蒙板不透明度 = float(
                max(
                    0.0,
                    min(
                        1.0,
                        float(
                            数据.get("调试背景蒙板不透明度", self._调试背景蒙板不透明度)
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            颜色 = 数据.get("调试血条颜色", None)
            if isinstance(颜色, (list, tuple)) and len(颜色) >= 3:
                self._调试血条颜色 = (
                    int(max(0, min(255, 颜色[0]))),
                    int(max(0, min(255, 颜色[1]))),
                    int(max(0, min(255, 颜色[2]))),
                )
        except Exception:
            pass

        try:
            self._调试血条亮度 = float(
                max(0.1, min(4.0, float(数据.get("调试血条亮度", self._调试血条亮度))))
            )
        except Exception:
            pass
        try:
            self._调试血条不透明度 = float(
                max(
                    0.0,
                    min(1.0, float(数据.get("调试血条不透明度", self._调试血条不透明度))),
                )
            )
        except Exception:
            pass
        try:
            self._调试血条晃荡速度 = float(
                max(
                    0.0,
                    min(12.0, float(数据.get("调试血条晃荡速度", self._调试血条晃荡速度))),
                )
            )
        except Exception:
            pass
        try:
            self._调试血条晃荡幅度 = float(
                max(
                    0.0,
                    min(40.0, float(数据.get("调试血条晃荡幅度", self._调试血条晃荡幅度))),
                )
            )
        except Exception:
            pass
        try:
            self._调试暴走血条速度 = float(
                max(
                    0.0,
                    min(600.0, float(数据.get("调试暴走血条速度", self._调试暴走血条速度))),
                )
            )
        except Exception:
            pass
        try:
            self._调试暴走血条不透明度 = float(
                max(
                    0.0,
                    min(
                        1.0,
                        float(
                            数据.get(
                                "调试暴走血条不透明度", self._调试暴走血条不透明度
                            )
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试暴走血条羽化 = float(
                max(
                    0.0,
                    min(80.0, float(数据.get("调试暴走血条羽化", self._调试暴走血条羽化))),
                )
            )
        except Exception:
            pass
        try:
            self._调试头像框特效速度 = float(
                max(
                    1.0,
                    min(
                        120.0,
                        float(
                            数据.get("调试头像框特效速度", self._调试头像框特效速度)
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试圆环频谱最大长度 = int(
                max(
                    6,
                    min(
                        96,
                        int(数据.get("圆环频谱最大长度", self._调试圆环频谱最大长度)),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试圆环频谱启用旋转 = bool(
                数据.get("圆环频谱启用旋转", self._调试圆环频谱启用旋转)
            )
        except Exception:
            pass
        try:
            self._调试圆环频谱背景板转速 = float(
                max(
                    -360.0,
                    min(
                        360.0,
                        float(
                            数据.get("圆环频谱背景板转速", self._调试圆环频谱背景板转速)
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试圆环频谱变化落差 = float(
                max(
                    0.0,
                    min(
                        2.0,
                        float(
                            数据.get("圆环频谱变化落差", self._调试圆环频谱变化落差)
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试圆环频谱线条数量 = int(
                max(
                    24,
                    min(
                        720,
                        int(
                            数据.get("圆环频谱线条数量", self._调试圆环频谱线条数量)
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试圆环频谱线条粗细 = int(
                max(
                    1,
                    min(
                        12,
                        int(数据.get("圆环频谱线条粗细", self._调试圆环频谱线条粗细)),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试圆环频谱线条间隔 = int(
                max(
                    1,
                    min(
                        8,
                        int(数据.get("圆环频谱线条间隔", self._调试圆环频谱线条间隔)),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试双踏板左X偏移 = float(
                max(
                    -600.0,
                    min(
                        600.0,
                        float(
                            数据.get("调试双踏板左X偏移", self._调试双踏板左X偏移)
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试双踏板右X偏移 = float(
                max(
                    -600.0,
                    min(
                        600.0,
                        float(
                            数据.get("调试双踏板右X偏移", self._调试双踏板右X偏移)
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试双踏板左Y偏移 = float(
                max(
                    -260.0,
                    min(
                        260.0,
                        float(
                            数据.get("调试双踏板左Y偏移", self._调试双踏板左Y偏移)
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._调试双踏板右Y偏移 = float(
                max(
                    -260.0,
                    min(
                        260.0,
                        float(
                            数据.get("调试双踏板右Y偏移", self._调试双踏板右Y偏移)
                        ),
                    ),
                )
            )
        except Exception:
            pass
        try:
            self._刷新双踏板强制判定线y()
        except Exception:
            pass
        try:
            旧alpha = int(getattr(self, "_背景暗层alpha", 224) or 224)
            新alpha = int(
                max(
                    0,
                    min(255, round(float(self._调试背景蒙板不透明度) * 255.0)),
                )
            )
            self._背景暗层alpha = int(新alpha)
            if 新alpha != 旧alpha:
                self._背景暗层缓存alpha = -1
        except Exception:
            pass

        self._应用圆环频谱调试设置()

    def _应用圆环频谱调试设置(self):
        try:
            对象 = getattr(self, "_圆环频谱舞台装饰", None)
            if 对象 is not None:
                if hasattr(对象, "设置调试外延最大长度"):
                    对象.设置调试外延最大长度(int(self._调试圆环频谱最大长度))
                if hasattr(对象, "设置调试频谱参数"):
                    对象.设置调试频谱参数(
                        启用旋转=bool(self._调试圆环频谱启用旋转),
                        变化落差=float(self._调试圆环频谱变化落差),
                        线条数量=int(self._调试圆环频谱线条数量),
                        线条粗细=int(self._调试圆环频谱线条粗细),
                        线条间隔=int(self._调试圆环频谱线条间隔),
                    )
        except Exception:
            pass

    def _背景亮度档位alpha(self) -> List[int]:
        # 按“20%一档”，并满足你要求的 0% 后回到 70%
        return [179, 128, 77, 26, 0]

    def _保存背景遮罩alpha到设置(self):
        值 = int(max(0, min(255, int(getattr(self, "_背景暗层alpha", 0) or 0))))
        try:
            self._载荷["背景遮罩alpha"] = int(值)
        except Exception:
            pass

        try:
            路径 = os.path.join(_取项目根目录(), "json", "选歌设置.json")
            数据 = _读取选歌设置json()
            if not isinstance(数据, dict):
                数据 = {}
            数据["背景遮罩alpha"] = int(值)
            os.makedirs(os.path.dirname(路径), exist_ok=True)
            临时 = 路径 + ".tmp"
            with open(临时, "w", encoding="utf-8") as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            os.replace(临时, 路径)
        except Exception:
            pass

    def _应用击中特效方案到渲染器(self):
        self._击中特效方案 = _规范击中特效方案(
            getattr(self, "_击中特效方案", "击中特效1")
        )
        for 渲染器 in (
            getattr(self, "_谱面渲染器", None),
            getattr(self, "_谱面渲染器_右", None),
        ):
            try:
                if 渲染器 is not None and hasattr(渲染器, "设置兜底击中特效方案"):
                    渲染器.设置兜底击中特效方案(str(self._击中特效方案))
            except Exception:
                pass

    @staticmethod
    def _循环选项值(当前值: str, 候选项: List[str]) -> str:
        候选 = [str(v) for v in list(候选项 or []) if str(v or "").strip()]
        if not 候选:
            return str(当前值 or "")
        当前 = str(当前值 or "")
        try:
            索引 = 候选.index(当前)
        except Exception:
            索引 = 0
        return 候选[(int(索引) + 1) % len(候选)]

    def _取当前大小选项文本(self) -> str:
        return "放大" if float(getattr(self, "_尺寸倍率", 1.0) or 1.0) >= 0.95 else "正常"

    def _保存游戏视觉设置到选歌json(self):
        try:
            路径 = os.path.join(_取项目根目录(), "json", "选歌设置.json")
            数据 = _读取选歌设置json()
            if not isinstance(数据, dict):
                数据 = {}
            参数 = dict(数据.get("设置参数", {}) or {})
            参数["调速"] = f"X{float(getattr(self, '_卷轴速度倍率', 4.0) or 4.0):.1f}"
            参数["背景模式"] = "视频" if (not bool(getattr(self, "_视频背景关闭", True))) else "图片"
            参数["谱面"] = str(getattr(self, "_谱面设置", "正常") or "正常")
            参数["隐藏"] = str(getattr(self, "_隐藏模式", "关闭") or "关闭")
            参数["轨迹"] = str(getattr(self, "_轨迹模式", "正常") or "正常")
            参数["方向"] = str(getattr(self, "_方向模式", "关闭") or "关闭")
            参数["大小"] = self._取当前大小选项文本()
            参数["击中特效"] = _规范击中特效方案(
                str(getattr(self, "_击中特效方案", "击中特效1") or "击中特效1")
            )
            数据["设置参数"] = dict(参数)
            数据["击中特效方案"] = str(参数.get("击中特效", "击中特效1"))

            背景文件名 = str(数据.get("背景文件名", "") or "")
            箭头文件名 = str(数据.get("箭头文件名", "") or "")
            数据["设置参数文本"] = _构建设置参数文本(
                参数, 背景文件名=背景文件名, 箭头文件名=箭头文件名
            )

            os.makedirs(os.path.dirname(路径), exist_ok=True)
            临时路径 = 路径 + ".tmp"
            with open(临时路径, "w", encoding="utf-8") as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            os.replace(临时路径, 路径)

            self._载荷["设置参数"] = dict(参数)
            self._载荷["设置参数文本"] = str(数据.get("设置参数文本", "") or "")
        except Exception:
            pass

    def _菜单切换调速(self):
        选项 = ["3.0", "3.5", "4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0"]
        try:
            当前值 = float(getattr(self, "_卷轴速度倍率", 4.0) or 4.0)
        except Exception:
            当前值 = 4.0
        try:
            当前索引 = min(range(len(选项)), key=lambda i: abs(float(选项[i]) - 当前值))
        except Exception:
            当前索引 = 0
        新值 = float(选项[(int(当前索引) + 1) % len(选项)])
        self._卷轴速度倍率 = float(新值)
        self._滚动速度px每秒 = float(420.0 * self._卷轴速度倍率)
        self._保存游戏视觉设置到选歌json()

    def _菜单切换背景模式(self):
        当前 = "视频" if (not bool(getattr(self, "_视频背景关闭", True))) else "图片"
        新值 = self._循环选项值(当前, ["图片", "视频"])
        self._背景模式 = str(新值)
        self._视频背景关闭 = bool(self._背景模式 != "视频")
        self._载荷["关闭视频背景"] = bool(self._视频背景关闭)
        self._应用背景视频状态()
        self._保存游戏视觉设置到选歌json()

    def _菜单切换谱面(self):
        self._谱面设置 = self._循环选项值(
            str(getattr(self, "_谱面设置", "正常") or "正常"), ["正常", "未知"]
        )
        self._保存游戏视觉设置到选歌json()

    def _菜单切换隐藏(self):
        self._隐藏模式 = self._循环选项值(
            str(getattr(self, "_隐藏模式", "关闭") or "关闭"),
            ["关闭", "半隐", "全隐"],
        )
        self._保存游戏视觉设置到选歌json()

    def _菜单切换轨迹(self):
        self._轨迹模式 = self._循环选项值(
            str(getattr(self, "_轨迹模式", "正常") or "正常"),
            ["正常", "摇摆", "旋转"],
        )
        self._保存游戏视觉设置到选歌json()

    def _菜单切换方向(self):
        self._方向模式 = self._循环选项值(
            str(getattr(self, "_方向模式", "关闭") or "关闭"),
            ["关闭", "反向"],
        )
        self._刷新按键映射()
        self._保存游戏视觉设置到选歌json()

    def _菜单切换大小(self):
        当前 = self._取当前大小选项文本()
        新值 = self._循环选项值(当前, ["正常", "放大"])
        self._尺寸倍率 = 0.8 if str(新值) == "正常" else 1.0
        self._保存游戏视觉设置到选歌json()

    def _菜单切换击中特效(self):
        当前 = _规范击中特效方案(str(getattr(self, "_击中特效方案", "") or ""))
        新值 = "击中特效2" if 当前 == "击中特效1" else "击中特效1"
        self._击中特效方案 = str(新值)
        self._应用击中特效方案到渲染器()
        self._保存游戏视觉设置到选歌json()

    def _切换背景亮度档位(self):
        档位 = list(self._背景亮度档位alpha())
        if not 档位:
            return
        当前 = int(max(0, min(255, int(getattr(self, "_背景暗层alpha", 0) or 0))))
        try:
            当前索引 = min(range(len(档位)), key=lambda i: abs(int(档位[i]) - 当前))
        except Exception:
            当前索引 = 0
        新索引 = int((int(当前索引) + 1) % len(档位))
        新值 = int(max(0, min(255, int(档位[新索引]))))
        self._背景暗层alpha = int(新值)
        self._背景暗层缓存alpha = -1
        self._保存背景遮罩alpha到设置()

    def _刷新双踏板强制判定线y(self):
        if not bool(getattr(self, "_是否双踏板模式", False)):
            self._双踏板强制判定线y = None
            return
        try:
            左偏 = float(getattr(self, "_调试双踏板左Y偏移", 0.0) or 0.0)
            右偏 = float(getattr(self, "_调试双踏板右Y偏移", 0.0) or 0.0)
            基准偏 = (左偏 + 右偏) * 0.5
        except Exception:
            基准偏 = 0.0
        try:
            self._双踏板强制判定线y = int(
                round(float(getattr(self, "_判定线y", 0) or 0) + float(基准偏))
            )
        except Exception:
            self._双踏板强制判定线y = int(getattr(self, "_判定线y", 0) or 0)

    def _取当前判定线y(self, 侧: str = "左") -> int:
        try:
            基准y = int(getattr(self, "_判定线y", 0) or 0)
        except Exception:
            基准y = 0

        # 双踏板模式强制同Y，优先级最高
        if bool(getattr(self, "_是否双踏板模式", False)):
            try:
                self._刷新双踏板强制判定线y()
            except Exception:
                pass
            try:
                强制y = getattr(self, "_双踏板强制判定线y", None)
                if 强制y is not None:
                    return int(强制y)
            except Exception:
                pass

        偏移键 = "_调试双踏板右Y偏移" if str(侧) == "右" else "_调试双踏板左Y偏移"
        try:
            偏移 = float(getattr(self, 偏移键, 0.0) or 0.0)
        except Exception:
            偏移 = 0.0
        return int(round(float(基准y) + float(偏移)))

    def _启动双踏板入场Y校正(self, 当前系统秒: float):
        if not bool(getattr(self, "_是否双踏板模式", False)):
            self._双踏板强制判定线y = None
            self._双踏板入场Y锁定至秒 = 0.0
            self._双踏板入场锁定判定线y = None
            self._双踏板入场待首帧校正 = False
            return

        try:
            self._刷新布局调试设置(强制=True)
        except Exception:
            pass

        try:
            self._刷新双踏板强制判定线y()
            self._双踏板入场锁定判定线y = int(
                getattr(self, "_双踏板强制判定线y", getattr(self, "_判定线y", 0) or 0)
            )
        except Exception:
            self._双踏板入场锁定判定线y = int(getattr(self, "_判定线y", 0) or 0)

        self._双踏板入场Y锁定至秒 = float(当前系统秒) + 0.55
        self._双踏板入场待首帧校正 = True

        for 渲染器 in (getattr(self, "_谱面渲染器", None), getattr(self, "_谱面渲染器_右", None)):
            if 渲染器 is None:
                continue
            try:
                setattr(渲染器, "_判定区层缓存", None)
                setattr(渲染器, "_判定区层签名", None)
                setattr(渲染器, "_notes静态层缓存", None)
                setattr(渲染器, "_notes静态层签名", None)
            except Exception:
                continue

    def 进入(self, 载荷=None):
        self._载荷 = dict(载荷) if isinstance(载荷, dict) else {}
        self._刷新布局调试设置(强制=True)
        self._错误提示 = ""
        默认背景遮罩alpha = int(round(255.0 * 0.70))
        try:
            选歌设置缓存 = _读取选歌设置json()
            if isinstance(选歌设置缓存, dict):
                默认背景遮罩alpha = int(
                    max(
                        0,
                        min(
                            255,
                            int(
                                选歌设置缓存.get(
                                    "背景遮罩alpha",
                                    默认背景遮罩alpha,
                                )
                                or 默认背景遮罩alpha
                            ),
                        ),
                    )
                )
        except Exception:
            默认背景遮罩alpha = int(round(255.0 * 0.70))
        self._是否自动模式 = bool(
            self._载荷.get("自动播放", self._载荷.get("自动模式", False))
        )
        self._性能模式 = bool(self._载荷.get("性能模式", False))
        self._视频背景关闭 = bool(self._载荷.get("关闭视频背景", False))
        try:
            self._背景暗层alpha = int(
                max(
                    0,
                    min(
                        255,
                        int(self._载荷.get("背景遮罩alpha", 默认背景遮罩alpha) or 0),
                    ),
                )
            )
        except Exception:
            self._背景暗层alpha = int(默认背景遮罩alpha)
        self._背景暗层缓存alpha = -1
        self._暂停菜单开启 = False
        self._暂停菜单索引 = 0
        self._暂停菜单打开前播放中 = False
        self._显示按键提示 = bool(self._载荷.get("显示按键提示", False))
        self._显示准备动画 = bool(self._载荷.get("显示准备动画", True))
        self._准备动画开始秒 = 0.0
        self._准备动画设置 = 读取准备动画设置(self._准备动画设置路径)
        try:
            # 让准备动画蒙版与当前游戏背景蒙版一致，避免亮度断层
            self._准备动画设置["背景蒙版透明度"] = float(
                max(0, min(255, int(self._背景暗层alpha or 0)))
            )
        except Exception:
            pass
        self._准备动画总时长 = 计算准备动画总时长(self._准备动画设置)
        self._准备动画已完成 = not self._显示准备动画
        self._准备动画背景无蒙版 = None
        self._准备动画基础场景图 = None
        self._准备动画判定区图层 = None
        self._准备动画判定区矩形 = None
        self._准备动画绘制缓存 = {}
        self._准备音效 = None
        self._准备音效通道 = None
        self._准备音效已播放 = False
        self._双踏板强制判定线y = None
        self._双踏板入场Y锁定至秒 = 0.0
        self._双踏板入场锁定判定线y = None
        self._双踏板入场待首帧校正 = False

        # ✅ 确保项目根目录在 sys.path（解决 core/ui 导入失败）
        try:
            根目录 = _取项目根目录()
            if 根目录 and (根目录 not in sys.path):
                sys.path.insert(0, 根目录)
        except Exception:
            根目录 = ""

        # ✅ 渲染器（懒加载）
        try:
            from ui.谱面渲染器 import 谱面渲染器

            if not hasattr(self, "_谱面渲染器") or self._谱面渲染器 is None:
                self._谱面渲染器 = 谱面渲染器()
        except Exception as 异常:
            self._谱面渲染器 = None
            self._错误提示 = f"渲染器初始化失败：{type(异常).__name__} {异常}"

        # ✅ 手装饰默认隐藏（F3可切换）
        self._显示手装饰 = False

        try:
            音乐 = self.上下文.get("音乐", None)
            if 音乐 is not None:
                getattr(音乐, "停止")()
        except Exception:
            pass

        self._初始化音频设备()

        设置参数 = {}
        参数文本 = ""
        设置背景文件名 = ""
        设置箭头文件名 = ""

        选歌设置 = _读取选歌设置json()
        if isinstance(选歌设置, dict):
            try:
                v = 选歌设置.get("设置参数", None)
                if isinstance(v, dict):
                    设置参数 = dict(v)
            except Exception:
                设置参数 = {}
            try:
                参数文本 = str(选歌设置.get("设置参数文本", "") or "")
            except Exception:
                参数文本 = ""
            try:
                设置背景文件名 = str(选歌设置.get("背景文件名", "") or "")
            except Exception:
                设置背景文件名 = ""
            try:
                设置箭头文件名 = str(选歌设置.get("箭头文件名", "") or "")
            except Exception:
                设置箭头文件名 = ""

        if not 设置参数:
            try:
                v = self._载荷.get("设置参数", None)
                if isinstance(v, dict):
                    设置参数 = dict(v)
            except Exception:
                设置参数 = {}

        if not 参数文本:
            参数文本 = str(self._载荷.get("设置参数文本", "") or "")
        if not 参数文本:
            参数文本 = _构建设置参数文本(
                设置参数, 背景文件名=设置背景文件名, 箭头文件名=设置箭头文件名
            )

        self._歌曲名 = str(
            self._载荷.get("歌名", self._载荷.get("歌曲名", "")) or ""
        ).strip()
        try:
            self._星级 = int(self._载荷.get("星级", 0) or 0)
        except Exception:
            self._星级 = 0

        提示文本 = str(self._载荷.get("操作反馈文本", "") or "").strip()
        if 提示文本:
            self._设置操作反馈(提示文本)

        self._卷轴速度倍率 = _解析调速倍率(
            str(设置参数.get("调速", "X4.0") or "X4.0")
        )
        self._滚动速度px每秒 = float(420.0 * self._卷轴速度倍率)
        self._尺寸倍率 = _解析大小倍率(设置参数, 参数文本)
        self._轨迹模式 = str(
            设置参数.get("轨迹", _从设置参数文本提取(参数文本, "轨迹")) or "正常"
        ).strip() or "正常"
        self._方向模式 = str(
            设置参数.get("方向", _从设置参数文本提取(参数文本, "方向")) or "关闭"
        ).strip() or "关闭"
        self._隐藏模式 = str(
            设置参数.get("隐藏", _从设置参数文本提取(参数文本, "隐藏")) or "关闭"
        ).strip() or "关闭"
        self._谱面设置 = str(
            设置参数.get("谱面", _从设置参数文本提取(参数文本, "谱面")) or "正常"
        ).strip() or "正常"
        self._击中特效方案 = _规范击中特效方案(
            str(
                设置参数.get(
                    "击中特效",
                    (
                        选歌设置.get("击中特效方案", "")
                        if isinstance(选歌设置, dict)
                        else ""
                    ),
                )
                or _从设置参数文本提取(参数文本, "击中特效")
                or "击中特效1"
            )
        )
        self._背景模式 = _解析背景模式(设置参数, 参数文本)

        # ESC 菜单里的“视频背景开关”默认值读选歌设置（默认图片=关闭视频）。
        默认关闭视频 = bool(self._背景模式 != "视频")
        if "关闭视频背景" in self._载荷:
            try:
                self._视频背景关闭 = bool(self._载荷.get("关闭视频背景", 默认关闭视频))
            except Exception:
                self._视频背景关闭 = bool(默认关闭视频)
        else:
            self._视频背景关闭 = bool(默认关闭视频)

        背景文件 = _从设置参数文本提取(参数文本, "背景")
        if not 背景文件:
            背景文件 = str(设置背景文件名 or "")
        self._加载背景(背景文件)
        self._默认背景视频目录 = os.path.join(
            _取项目根目录(), "backmovies", "游戏中"
        )
        self._应用背景视频状态()
        self._加载联网图标()
        self._准备动画图 = 加载准备动画图片(_取项目根目录())
        self._加载准备动画音效()

        # ✅ 皮肤编号（默认 03）
        箭头文件 = _从设置参数文本提取(参数文本, "箭头")
        if not 箭头文件:
            箭头文件 = str(设置箭头文件名 or "")
        箭头编号 = "03"
        数字匹配 = re.search(r"(\d{1,3})", str(箭头文件 or ""))
        if 数字匹配:
            try:
                数字 = int(数字匹配.group(1))
                if 1 <= 数字 <= 99:
                    箭头编号 = f"{数字:02d}"
            except Exception:
                pass

        self._皮肤目录 = os.path.join(
            _取项目根目录(), "UI-img", "游戏界面", "箭头", 箭头编号
        )

        # ✅ 路径自检（你现在最需要这个）
        关键1 = os.path.join(self._皮肤目录, "arrow", "skin.json")
        关键2 = os.path.join(self._皮肤目录, "key", "skin.json")
        if not os.path.isfile(关键1):
            self._错误提示 = (
                self._错误提示 + " | " if self._错误提示 else ""
            ) + f"缺少：{关键1}"
        if not os.path.isfile(关键2):
            self._错误提示 = (
                self._错误提示 + " | " if self._错误提示 else ""
            ) + f"缺少：{关键2}"

        # ✅ 让渲染器加载皮肤（目录优先；找不到会自己尝试 03.zip）
        if self._谱面渲染器 is not None:
            try:
                self._谱面渲染器.设置皮肤(self._皮肤目录)
                self._应用击中特效方案到渲染器()
            except Exception as 异常:
                self._错误提示 = (
                    self._错误提示 + " | " if self._错误提示 else ""
                ) + f"皮肤加载失败：{type(异常).__name__} {异常}"

        模式文本 = str(
            self._载荷.get("模式", self._载荷.get("子模式", self._载荷.get("类型", "")))
            or ""
        )
        模式文本小写 = 模式文本.lower()
        优先双踏板 = bool(("双踏" in 模式文本) or ("double" in 模式文本小写))

        self._sm路径 = str(self._载荷.get("sm路径", "") or "").strip()

        self._事件 = []
        self._事件左渲染 = []
        self._事件右渲染 = []
        self._谱面列数 = 5
        self._谱面chart类型 = ""
        self._是否双踏板模式 = bool(优先双踏板)
        self._轨道数 = 10 if self._是否双踏板模式 else 5
        self._刷新按键映射()
        self._同步双踏板渲染器()
        self._谱面总时长秒 = 0.0
        self._offset = 0.0
        self._音频路径 = None

        if (not self._sm路径) or (not os.path.isfile(self._sm路径)):
            self._错误提示 = (
                self._错误提示 + " | " if self._错误提示 else ""
            ) + f"找不到SM：{self._sm路径 or '空'}"
        else:
            self._sm文本 = _安全读文本(self._sm路径)
            try:
                事件, 偏移, 总时长, 列数, charttype = _构建_sm事件列表(
                    self._sm路径, 优先double=bool(优先双踏板)
                )
                self._谱面列数 = int(max(1, int(列数 or 5)))
                self._谱面chart类型 = str(charttype or "")
                self._是否双踏板模式 = bool(
                    优先双踏板
                    or self._谱面列数 >= 10
                    or ("pump-double" in str(self._谱面chart类型).lower())
                )
                self._轨道数 = 10 if self._是否双踏板模式 else 5
                self._刷新按键映射()
                self._同步双踏板渲染器()
                self._事件 = [
                    e
                    for e in 事件
                    if 0 <= int(getattr(e, "轨道序号", -1)) < int(self._轨道数)
                ]
                self._offset = float(偏移)
                self._谱面总时长秒 = float(总时长)
            except Exception as 异常:
                self._事件 = []
                self._事件左渲染 = []
                self._事件右渲染 = []
                self._谱面列数 = 5
                self._谱面chart类型 = ""
                self._是否双踏板模式 = False
                self._轨道数 = 5
                self._刷新按键映射()
                self._同步双踏板渲染器()
                self._offset = 0.0
                self._谱面总时长秒 = 0.0
                self._错误提示 = (
                    self._错误提示 + " | " if self._错误提示 else ""
                ) + f"解析SM失败：{type(异常).__name__} {异常}"

            self._音频路径 = _解析_sm_music(self._sm文本, self._sm路径)
            if not self._音频路径:
                self._音频路径 = _找同目录音频_按优先级(self._sm路径)

            if not self._歌曲名:
                try:
                    self._歌曲名 = os.path.splitext(os.path.basename(self._sm路径))[0]
                except Exception:
                    self._歌曲名 = ""
            if self._星级 <= 0:
                try:
                    目录名 = os.path.basename(os.path.dirname(self._sm路径))
                    m = re.search(r"#(\d+)$", str(目录名))
                    if m:
                        self._星级 = int(m.group(1))
                except Exception:
                    self._星级 = 0

        self._事件.sort(key=lambda e: float(e.开始秒))
        self._拆分双踏板渲染事件()

        self._入场系统秒 = time.perf_counter()
        self._总血量HP = int(self._初始血量HP)
        self._同步旧血量比例()

        self._音频已开始 = False
        self._音频暂停中 = False
        self._音频开始系统秒 = 0.0

        # ✅ 把“当前背景音乐路径”塞进上下文资源（给后续调试/扩展用）
        try:
            资源 = self.上下文.get("资源", None)
            if isinstance(资源, dict):
                资源["背景音乐路径"] = str(self._音频路径 or "")
        except Exception:
            pass

        # ✅ 圆环频谱装饰（只在本场景用）
        if bool(self._性能模式):
            self._圆环频谱舞台装饰 = None
        else:
            try:
                from ui.圆环频谱叠加 import 圆环频谱舞台装饰

                self._圆环频谱舞台装饰 = 圆环频谱舞台装饰()
                self._应用圆环频谱调试设置()
                if self._音频路径 and os.path.isfile(self._音频路径):
                    # 这里会尝试解码 mp3/ogg/wav -> sndarray（失败会抛异常，我们捕获后降级）
                    self._圆环频谱舞台装饰.绑定音频(str(self._音频路径))
            except Exception as 异常:
                self._圆环频谱舞台装饰 = None
                self._错误提示 = (
                    self._错误提示 + " | " if self._错误提示 else ""
                ) + f"圆环频谱初始化失败（mp3解码/加载问题）：{type(异常).__name__} {异常}"

        self._初始化字体()

        self._上次系统秒 = time.perf_counter()
        self._重算布局(强制=True)
        try:
            self._启动双踏板入场Y校正(float(time.perf_counter()))
        except Exception:
            pass
        self._预热渲染缓存()
        self._判定统计 = {"perfect": 0, "cool": 0, "good": 0, "miss": 0}

        # ✅ 玩法初始化（保持你原来逻辑）
        try:
            from core.玩法.判定系统 import 判定系统, 判定参数
            from core.玩法.计分系统 import 计分系统
            from core.玩法.谱面构建 import 构建判定谱面, 输入音符事件

            bpms = _解析_bpms(self._sm文本)
            bpm段 = _生成时间轴段(bpms)

            def _beat转秒_闭包(beat: float) -> float:
                return _beat转秒(float(beat), bpm段)

            输入事件列表 = [
                输入音符事件(
                    轨道序号=int(e.轨道序号),
                    开始秒=float(e.开始秒),
                    结束秒=float(e.结束秒),
                    开始beat=float(e.开始beat),
                    结束beat=float(e.结束beat),
                    类型=str(e.类型),
                )
                for e in self._事件
            ]

            判定音符列表, 总分 = 构建判定谱面(输入事件列表, _beat转秒_闭包)

            self._判定系统 = 判定系统(
                判定参数(),
                输入补偿秒=float(self._输入补偿秒),
                自动模式=bool(self._是否自动模式),
            )
            self._判定系统.加载谱面(判定音符列表)

            self._计分系统 = 计分系统(int(总分))

            self._判定音符列表缓存 = 判定音符列表
            self._谱面总分缓存 = int(总分)

        except Exception as 异常:
            self._判定系统 = None
            self._计分系统 = None
            self._错误提示 = (
                self._错误提示 + " | " if self._错误提示 else ""
            ) + f"玩法初始化失败：{type(异常).__name__} {异常}"
            try:
                import traceback

                traceback.print_exc()
            except Exception:
                pass

        self.设定谱面时间(0.0)
        if self._显示准备动画:
            self._播放中 = False
            self._暂停时刻谱面秒 = 0.0
            self._准备动画开始秒 = time.perf_counter()
        else:
            self.播放()

    def 退出(self):
        try:
            if self._准备音效通道 is not None:
                self._准备音效通道.stop()
        except Exception:
            pass
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        try:
            if self._背景视频播放器 is not None and hasattr(
                self._背景视频播放器, "关闭"
            ):
                self._背景视频播放器.关闭()
        except Exception:
            pass

    def 更新(self):
        现在系统秒 = time.perf_counter()
        时间差 = float(现在系统秒 - float(self._上次系统秒))
        if 时间差 < 0:
            时间差 = 0.0
        if 时间差 > 0.20:
            时间差 = 0.20
        self._上次系统秒 = 现在系统秒

        # 渲染器更新（按键回弹 / key_effect 动画 / 计数动画组）
        try:
            if hasattr(self, "_谱面渲染器") and self._谱面渲染器 is not None:
                self._谱面渲染器.更新(float(时间差))
            if (
                bool(getattr(self, "_是否双踏板模式", False))
                and hasattr(self, "_谱面渲染器_右")
                and self._谱面渲染器_右 is not None
            ):
                self._谱面渲染器_右.更新(float(时间差))
        except Exception:
            pass

        if self._显示准备动画 and (not self._准备动画已完成):
            准备经过秒 = float(现在系统秒 - float(self._准备动画开始秒 or 0.0))
            if not bool(self._准备音效已播放):
                try:
                    时间轴 = 计算准备动画时间轴(dict(self._准备动画设置 or {}))
                    if 准备经过秒 >= float(时间轴.get("引导开始", 0.0)):
                        self._播放准备动画音效()
                        self._准备音效已播放 = True
                except Exception:
                    pass
            if (现在系统秒 - float(self._准备动画开始秒 or 0.0)) >= float(
                self._准备动画总时长
            ):
                self._准备动画已完成 = True
                self._准备动画基础场景图 = None
                self._准备动画背景无蒙版 = None
                self._准备动画判定区图层 = None
                self._准备动画判定区矩形 = None
                self._准备动画绘制缓存 = {}
                try:
                    # 准备动画结束后强制重算一次布局，避免双踏板左右初始帧错位。
                    self._重算布局(强制=True)
                except Exception:
                    pass
                try:
                    self._启动双踏板入场Y校正(float(现在系统秒))
                except Exception:
                    pass
                self.播放()
            return None

        if self._播放中:
            self._当前谱面秒 = float(time.perf_counter() - float(self._起始系统秒))

        # 玩法更新（miss + hold tick）
        if self._判定系统 is not None and self._计分系统 is not None:
            按下数组 = pygame.key.get_pressed()

            def _轨道是否按下(轨道序号: int) -> bool:
                键列表 = self._轨道到按键列表.get(int(轨道序号), [])
                for k in 键列表:
                    try:
                        if 按下数组[k]:
                            return True
                    except Exception:
                        continue
                return False

            回报列表 = self._判定系统.更新(float(self._当前谱面秒), _轨道是否按下)

            # ✅ 先结算（保证 当前连击/最近判定 最新）
            结算前连击 = int(getattr(self._计分系统, "当前连击", 0) or 0)
            self._计分系统.批量结算(回报列表)
            self._记录判定统计(回报列表)

            if 回报列表:
                # 1) tap/hold_head：击中特效
                try:
                    for 回报 in 回报列表:
                        判定 = str(getattr(回报, "判定", "") or "").lower()
                        类型 = str(getattr(回报, "类型", "") or "")
                        轨道 = int(getattr(回报, "轨道序号", -1))
                        if 判定 != "miss" and 类型 in ("tap", "hold_head"):
                            self._触发轨道击中特效(
                                int(轨道), 判定, 发生谱面秒=float(self._当前谱面秒)
                            )
                except Exception:
                    pass

                try:
                    if bool(getattr(self, "_是否双踏板模式", False)):
                        左回报 = []
                        右回报 = []
                        for 回报 in 回报列表:
                            try:
                                轨道 = int(getattr(回报, "轨道序号", -1))
                            except Exception:
                                continue
                            if 0 <= 轨道 < 5:
                                左回报.append(回报)
                            elif 5 <= 轨道 < 10:
                                右回报.append(回报)
                        self._按回报播放计数动画_到渲染器(
                            左回报, 结算前连击, self._谱面渲染器
                        )
                        self._按回报播放计数动画_到渲染器(
                            右回报, 结算前连击, getattr(self, "_谱面渲染器_右", None)
                        )
                    else:
                        self._按回报播放计数动画(回报列表, 结算前连击)
                except Exception:
                    pass
                if self._应用血量回报(回报列表):
                    return self._立即失败结束()

        if self._操作反馈剩余秒 > 0.0:
            self._操作反馈剩余秒 = max(0.0, self._操作反馈剩余秒 - 时间差)

        # 结束逻辑（保持）
        if self._音频可用 and self._音频路径 and os.path.isfile(self._音频路径):
            if self._音频已开始 and (not self._音频暂停中):
                try:
                    if not pygame.mixer.music.get_busy():
                        if (time.perf_counter() - float(self._音频开始系统秒)) > 0.6:
                            return {
                                "切换到": "结算",
                                "载荷": self._构建结算载荷(失败=False),
                                "禁用黑屏过渡": True,
                            }
                except Exception:
                    pass
        else:
            if self._谱面总时长秒 > 0 and self._当前谱面秒 >= (
                self._谱面总时长秒 + 2.0
            ):
                return {
                    "切换到": "结算",
                    "载荷": self._构建结算载荷(失败=False),
                    "禁用黑屏过渡": True,
                }

        return None

    def 处理事件(self, 事件):
        if bool(self._暂停菜单开启):
            if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
                self._关闭暂停菜单(恢复播放=True)
                return None
            return self._处理暂停菜单按键(事件)

        if 事件.type != pygame.KEYDOWN:
            return None

        if 事件.key == pygame.K_ESCAPE:
            self._打开暂停菜单()
            return None

        if 事件.key == pygame.K_F2:
            self._是否自动模式 = not bool(self._是否自动模式)
            if self._判定系统 is not None:
                try:
                    self._判定系统.自动模式 = bool(self._是否自动模式)
                except Exception:
                    pass
            self._设置操作反馈(
                f"F2:自动播放已{'开启' if self._是否自动模式 else '关闭'}"
            )
            return None

        if 事件.key == pygame.K_SPACE:
            if self._播放中:
                self.暂停()
                self._设置操作反馈("SPACE:谱面播放已暂停")
            else:
                self.播放()
                self._设置操作反馈("SPACE:谱面播放已继续")
            return None

        if 事件.key == pygame.K_r:
            新载荷 = dict(self._载荷)
            新载荷["操作反馈文本"] = "R:歌曲重载成功"
            return {
                "切换到": "谱面播放器",
                "载荷": 新载荷,
                "禁用黑屏过渡": True,
            }

        # 数字键玩法
        轨道 = self._按键到轨道.get(事件.key, None)
        if 轨道 is not None:
            # 按下反馈：判定区缩放回弹
            self._触发轨道按下反馈(int(轨道))

            if self._判定系统 is not None and self._计分系统 is not None:
                回报列表 = self._判定系统.处理按下(
                    int(轨道), float(self._当前谱面秒)
                )

                # ✅ 击中特效：只对非 miss 且 tap/hold_head 播放
                try:
                    for 回报 in 回报列表:
                        判定 = str(getattr(回报, "判定", "") or "").lower()
                        类型 = str(getattr(回报, "类型", "") or "")
                        轨道2 = int(getattr(回报, "轨道序号", -1))
                        if 判定 != "miss" and 类型 in ("tap", "hold_head"):
                            self._触发轨道击中特效(
                                int(轨道2), 判定, 发生谱面秒=float(self._当前谱面秒)
                            )
                except Exception:
                    pass

                # ✅ 先结算
                结算前连击 = int(getattr(self._计分系统, "当前连击", 0) or 0)
                self._计分系统.批量结算(回报列表)
                self._记录判定统计(回报列表)

                if 回报列表:
                    try:
                        if bool(getattr(self, "_是否双踏板模式", False)):
                            左回报 = []
                            右回报 = []
                            for 回报 in 回报列表:
                                try:
                                    轨道2 = int(getattr(回报, "轨道序号", -1))
                                except Exception:
                                    continue
                                if 0 <= 轨道2 < 5:
                                    左回报.append(回报)
                                elif 5 <= 轨道2 < 10:
                                    右回报.append(回报)
                            self._按回报播放计数动画_到渲染器(
                                左回报, 结算前连击, self._谱面渲染器
                            )
                            self._按回报播放计数动画_到渲染器(
                                右回报, 结算前连击, getattr(self, "_谱面渲染器_右", None)
                            )
                        else:
                            self._按回报播放计数动画(回报列表, 结算前连击)
                    except Exception:
                        pass
                    if self._应用血量回报(回报列表):
                        return self._立即失败结束()

        return None

    def 绘制(self):
        屏幕: pygame.Surface = self.上下文["屏幕"]
        self._刷新布局调试设置()
        屏幕宽, 屏幕高 = 屏幕.get_size()

        if (屏幕宽, 屏幕高) != tuple(self._屏幕尺寸):
            self._重算布局(强制=True)

        self._绘制背景(屏幕)

        if self._字体 is None or self._小字体 is None:
            self._初始化字体()

        血量显示 = float(self._取血量显示比例())
        可见血量HP = int(self._取可见血量HP())
        Note层灰度 = bool(self._总血量HP < 201)
        血条暴走 = bool(可见血量HP >= int(self._显示血量上限HP))

        判定 = "-"
        连击 = 0
        分数 = 0
        百分比 = "0.00%"
        if self._计分系统 is not None:
            判定 = str(getattr(self._计分系统, "最近判定", "") or "-")
            连击 = int(getattr(self._计分系统, "当前连击", 0) or 0)
            分数 = int(getattr(self._计分系统, "当前分", 0) or 0)
            try:
                百分比 = str(self._计分系统.取百分比字符串())
            except Exception:
                百分比 = "0.00%"

        实际箭头缩放 = float(self._箭头默认缩放) * float(self._尺寸倍率)
        箭头目标宽 = int(self._取箭头目标宽(实际箭头缩放))
        双踏板模式 = bool(getattr(self, "_是否双踏板模式", False))
        轨道中心列表 = [
            int(self._轨道起x + self._轨道槽宽 // 2 + i * self._轨道中心间距)
            for i in range(5 if 双踏板模式 else self._轨道数)
        ]
        右侧轨道中心列表: List[int] = []
        if 双踏板模式:
            左中心, 右中心 = self._取双踏板轨道中心列表()
            if len(左中心) == 5 and len(右中心) == 5:
                轨道中心列表 = list(左中心)
                右侧轨道中心列表 = list(右中心)

        if self._谱面渲染器 is None:
            if self._小字体:
                文 = self._小字体.render(
                    "谱面渲染器为空（导入失败）", True, (255, 120, 120)
                )
                屏幕.blit(文, (18, 18))
            self._绘制底部币值(屏幕)
            self._绘制暂停菜单(屏幕)
            return

        # ✅ 玩家信息（从个人资料.json）
        头像图 = self._取头像图_懒加载()
        玩家昵称 = self._取昵称_懒加载()
        段位图 = self._取段位图_懒加载()

        try:
            玩家序号 = int(self._载荷.get("玩家序号", 1) or 1)
        except Exception:
            玩家序号 = 1
        玩家序号 = 1 if 玩家序号 != 2 else 2

        try:
            当前关卡 = int(self._载荷.get("当前关卡", self._载荷.get("局数", 1)) or 1)
        except Exception:
            当前关卡 = 1
        当前关卡 = int(max(0, min(9, 当前关卡)))

        # ✅ 圆环频谱对象（已在进入()里创建并绑定音频）
        圆环频谱对象 = getattr(self, "_圆环频谱舞台装饰", None)

        try:
            from ui.谱面渲染器 import 渲染输入

            当前系统秒 = float(time.perf_counter())
            if bool(双踏板模式) and bool(getattr(self, "_双踏板入场待首帧校正", False)):
                try:
                    self._刷新布局调试设置(强制=True)
                except Exception:
                    pass
                try:
                    self._刷新双踏板强制判定线y()
                    self._双踏板入场锁定判定线y = int(self._取当前判定线y("左"))
                except Exception:
                    self._双踏板入场锁定判定线y = int(self._判定线y)
                self._双踏板入场待首帧校正 = False

            左判定线y = int(self._取当前判定线y("左"))
            右判定线y = int(self._取当前判定线y("右"))
            if (
                bool(双踏板模式)
                and float(当前系统秒) <= float(getattr(self, "_双踏板入场Y锁定至秒", 0.0) or 0.0)
                and getattr(self, "_双踏板入场锁定判定线y", None) is not None
            ):
                try:
                    锁定y = int(getattr(self, "_双踏板入场锁定判定线y"))
                    左判定线y = 锁定y
                    右判定线y = 锁定y
                except Exception:
                    pass

            事件列表_左 = (
                list(getattr(self, "_事件左渲染", []) or [])
                if 双踏板模式
                else list(getattr(self, "_事件", []) or [])
            )
            输入 = 渲染输入(
                当前谱面秒=float(self._当前谱面秒),
                总时长秒=float(self._谱面总时长秒),
                轨道中心列表=轨道中心列表,
                判定线y=int(左判定线y),
                底部y=int(self._底部y),
                滚动速度px每秒=float(self._滚动速度px每秒),
                箭头目标宽=int(箭头目标宽),
                事件列表=事件列表_左,
                显示_判定=str(判定),
                显示_连击=int(连击),
                显示_分数=int(分数),
                显示_百分比=str(百分比),
                血条区域=self._血条区域,
                血量显示=float(血量显示),
                头像图=头像图,
                总血量HP=int(self._总血量HP),
                可见血量HP=int(可见血量HP),
                Note层灰度=bool(Note层灰度),
                血条暴走=bool(血条暴走),
                玩家序号=int(玩家序号),
                玩家昵称=str(玩家昵称 or ""),
                段位图=段位图,
                当前关卡=int(当前关卡),
                歌曲名=str(self._歌曲名 or ""),
                星级=int(max(0, self._星级)),
                血条待机演示=False,
                显示手装饰=bool(getattr(self, "_显示手装饰", False)),
                错误提示=str(self._错误提示 or ""),
                轨迹模式=str(getattr(self, "_轨迹模式", "正常") or "正常"),
                隐藏模式=str(getattr(self, "_隐藏模式", "关闭") or "关闭"),
                大小倍率=float(getattr(self, "_尺寸倍率", 1.0) or 1.0),
                # ✅ 关键：把对象传给渲染器，让 JSON 控件负责“画”
                圆环频谱对象=圆环频谱对象,
            )
            self._准备动画渲染输入 = 输入
            def _注入调试参数(渲染输入对象):
                渲染输入对象.调试_血条颜色 = [
                    int(self._调试血条颜色[0]),
                    int(self._调试血条颜色[1]),
                    int(self._调试血条颜色[2]),
                    int(
                        max(
                            0,
                            min(255, round(float(self._调试血条不透明度) * 255.0)),
                        )
                    ),
                ]
                渲染输入对象.调试_血条亮度 = float(self._调试血条亮度)
                渲染输入对象.调试_血条不透明度 = float(self._调试血条不透明度)
                渲染输入对象.调试_血条晃荡速度 = float(self._调试血条晃荡速度)
                渲染输入对象.调试_血条晃荡幅度 = float(self._调试血条晃荡幅度)
                渲染输入对象.调试_暴走血条速度 = float(self._调试暴走血条速度)
                渲染输入对象.调试_暴走血条不透明度 = float(self._调试暴走血条不透明度)
                渲染输入对象.调试_暴走血条羽化 = float(self._调试暴走血条羽化)
                渲染输入对象.调试_头像框特效速度 = float(self._调试头像框特效速度)
                渲染输入对象.调试_圆环频谱_启用旋转 = bool(self._调试圆环频谱启用旋转)
                渲染输入对象.调试_圆环频谱_背景板旋转速度 = float(self._调试圆环频谱背景板转速)
                渲染输入对象.调试_圆环频谱_变化落差 = float(self._调试圆环频谱变化落差)
                渲染输入对象.调试_圆环频谱_线条数量 = int(self._调试圆环频谱线条数量)
                渲染输入对象.调试_圆环频谱_线条粗细 = int(self._调试圆环频谱线条粗细)
                渲染输入对象.调试_圆环频谱_线条间隔 = int(self._调试圆环频谱线条间隔)
                渲染输入对象.性能模式 = bool(self._性能模式)

            _注入调试参数(输入)
            self._谱面渲染器.渲染(屏幕, 输入, self._字体, self._小字体)

            if (
                双踏板模式
                and len(右侧轨道中心列表) == 5
                and getattr(self, "_谱面渲染器_右", None) is not None
            ):
                try:
                    setattr(self._谱面渲染器_右, "_最近渲染谱面秒", float(self._当前谱面秒))
                except Exception:
                    pass
                输入右 = 渲染输入(
                    当前谱面秒=float(self._当前谱面秒),
                    总时长秒=float(self._谱面总时长秒),
                    轨道中心列表=list(右侧轨道中心列表),
                    判定线y=int(右判定线y),
                    底部y=int(self._底部y),
                    滚动速度px每秒=float(self._滚动速度px每秒),
                    箭头目标宽=int(箭头目标宽),
                    事件列表=list(getattr(self, "_事件右渲染", []) or []),
                    显示_判定=str(判定),
                    显示_连击=int(连击),
                    显示_分数=int(分数),
                    显示_百分比=str(百分比),
                    血条区域=self._血条区域,
                    血量显示=float(血量显示),
                    头像图=头像图,
                    总血量HP=int(self._总血量HP),
                    可见血量HP=int(可见血量HP),
                    Note层灰度=bool(Note层灰度),
                    血条暴走=bool(血条暴走),
                    玩家序号=2,
                    玩家昵称=str(玩家昵称 or ""),
                    段位图=段位图,
                    当前关卡=int(当前关卡),
                    歌曲名=str(self._歌曲名 or ""),
                    星级=int(max(0, self._星级)),
                    血条待机演示=False,
                    显示手装饰=False,
                    错误提示="",
                    轨迹模式=str(getattr(self, "_轨迹模式", "正常") or "正常"),
                    隐藏模式=str(getattr(self, "_隐藏模式", "关闭") or "关闭"),
                    大小倍率=float(getattr(self, "_尺寸倍率", 1.0) or 1.0),
                    圆环频谱对象=None,
                )
                _注入调试参数(输入右)
                if bool(Note层灰度):
                    右notes层 = pygame.Surface(屏幕.get_size(), pygame.SRCALPHA)
                    self._谱面渲染器_右._绘制notes层(
                        右notes层, 输入右, 绘制击中特效=False
                    )
                    屏幕.blit(pygame.transform.grayscale(右notes层), (0, 0))
                    self._谱面渲染器_右._绘制击中特效(屏幕, 输入右)
                else:
                    self._谱面渲染器_右._绘制notes层(屏幕, 输入右)
            if bool(getattr(self, "_显示按键提示", False)):
                self._绘制按键提示(屏幕)
            self._绘制操作反馈(屏幕)
            self._绘制底部币值(屏幕)
            if bool(getattr(self, "_显示准备动画", False)) and (not bool(getattr(self, "_准备动画已完成", True))):
                需刷新基础场景图 = False
                try:
                    if (self._准备动画基础场景图 is None) or (
                        self._准备动画基础场景图.get_size() != 屏幕.get_size()
                    ):
                        需刷新基础场景图 = True
                except Exception:
                    需刷新基础场景图 = True
                if 需刷新基础场景图:
                    try:
                        self._准备动画基础场景图 = 屏幕.copy()
                    except Exception:
                        self._准备动画基础场景图 = None
            self._绘制准备动画(屏幕)
            self._绘制暂停菜单(屏幕)

        except Exception as 异常:
            try:
                import traceback

                traceback.print_exc()
            except Exception:
                pass

            if self._小字体:
                文 = self._小字体.render(
                    f"渲染异常：{type(异常).__name__} {异常}", True, (255, 120, 120)
                )
                屏幕.blit(文, (18, 18))
                文2 = self._小字体.render(
                    "检查：ui/谱面渲染器.py 是否存在、皮肤目录是否包含各分包 skin.json/skin.png",
                    True,
                    (255, 180, 120),
                )
                屏幕.blit(文2, (18, 38))

    def _设置操作反馈(self, 文本: str):
        文本 = str(文本 or "").strip()
        if not 文本:
            return
        self._操作反馈文本 = 文本
        self._操作反馈剩余秒 = float(
            max(0.5, getattr(self, "_操作反馈总秒", 1.35) or 1.35)
        )

    def _打开暂停菜单(self):
        if bool(self._暂停菜单开启):
            return
        self._暂停菜单开启 = True
        self._暂停菜单索引 = 0
        self._暂停菜单打开前播放中 = bool(self._播放中)
        self._暂停菜单项矩形 = []
        self._暂停菜单关闭按钮 = pygame.Rect(0, 0, 0, 0)
        if bool(self._播放中):
            self.暂停()
        self._设置操作反馈("ESC:已暂停")

    def _关闭暂停菜单(self, 恢复播放: bool = True):
        if not bool(self._暂停菜单开启):
            return
        应恢复 = bool(恢复播放 and self._暂停菜单打开前播放中)
        self._暂停菜单开启 = False
        self._暂停菜单打开前播放中 = False
        if 应恢复 and (not bool(self._播放中)):
            self.播放()
            self._设置操作反馈("ESC:继续游戏")

    def _取暂停菜单项文本(self) -> List[str]:
        背景状态 = "图片" if bool(self._视频背景关闭) else "视频"
        性能状态 = "已开启" if bool(self._性能模式) else "已关闭"
        调速文本 = f"X{float(getattr(self, '_卷轴速度倍率', 4.0) or 4.0):.1f}"
        击中特效显示 = "特效2" if ("2" in str(getattr(self, "_击中特效方案", ""))) else "特效1"
        return [
            f"调速（{调速文本}）",
            f"背景（{背景状态}）",
            f"谱面（{str(getattr(self, '_谱面设置', '正常') or '正常')}）",
            f"隐藏（{str(getattr(self, '_隐藏模式', '关闭') or '关闭')}）",
            f"轨迹（{str(getattr(self, '_轨迹模式', '正常') or '正常')}）",
            f"方向（{str(getattr(self, '_方向模式', '关闭') or '关闭')}）",
            f"大小（{self._取当前大小选项文本()}）",
            f"击中特效（{击中特效显示}）",
            "切换背景亮度",
            f"极简性能模式（{性能状态}）",
            "退出本局",
            "退出到桌面",
        ]

    def _处理暂停菜单按键(self, 事件):
        菜单项 = self._取暂停菜单项文本()
        if not 菜单项:
            return None

        if 事件.type == pygame.KEYDOWN:
            if 事件.key in (
                pygame.K_LEFT,
                pygame.K_UP,
                pygame.K_KP1,
                pygame.K_KP7,
            ):
                self._暂停菜单索引 = (int(self._暂停菜单索引) - 1) % len(菜单项)
                return None
            if 事件.key in (
                pygame.K_RIGHT,
                pygame.K_DOWN,
                pygame.K_KP3,
                pygame.K_KP9,
            ):
                self._暂停菜单索引 = (int(self._暂停菜单索引) + 1) % len(菜单项)
                return None

            if 事件.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_KP5):
                return self._执行暂停菜单确认()
            return None

        if 事件.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(getattr(self, "_暂停菜单项矩形", []) or []):
                if rect.collidepoint(事件.pos):
                    self._暂停菜单索引 = int(idx)
                    break
            return None

        if 事件.type == pygame.MOUSEBUTTONDOWN and int(getattr(事件, "button", 0)) == 1:
            if getattr(self, "_暂停菜单关闭按钮", pygame.Rect(0, 0, 0, 0)).collidepoint(
                事件.pos
            ):
                self._关闭暂停菜单(恢复播放=True)
                return None
            for idx, rect in enumerate(getattr(self, "_暂停菜单项矩形", []) or []):
                if rect.collidepoint(事件.pos):
                    self._暂停菜单索引 = int(idx)
                    return self._执行暂停菜单确认()
            return None
        return None

    def _执行暂停菜单确认(self):
        项列表 = self._取暂停菜单项文本()
        if not 项列表:
            return None
        选项索引 = int(max(0, min(len(项列表) - 1, int(self._暂停菜单索引))))

        if 选项索引 == 0:
            self._菜单切换调速()
            self._设置操作反馈(f"调速已切换：X{float(self._卷轴速度倍率):.1f}")
            return None

        if 选项索引 == 1:
            self._菜单切换背景模式()
            self._设置操作反馈(
                f"背景模式已切换：{'视频' if (not self._视频背景关闭) else '图片'}"
            )
            return None

        if 选项索引 == 2:
            self._菜单切换谱面()
            self._设置操作反馈(f"谱面模式：{self._谱面设置}")
            return None

        if 选项索引 == 3:
            self._菜单切换隐藏()
            self._设置操作反馈(f"隐藏模式：{self._隐藏模式}")
            return None

        if 选项索引 == 4:
            self._菜单切换轨迹()
            self._设置操作反馈(f"轨迹模式：{self._轨迹模式}")
            return None

        if 选项索引 == 5:
            self._菜单切换方向()
            self._设置操作反馈(f"方向模式：{self._方向模式}")
            return None

        if 选项索引 == 6:
            self._菜单切换大小()
            self._设置操作反馈(f"大小模式：{self._取当前大小选项文本()}")
            return None

        if 选项索引 == 7:
            self._菜单切换击中特效()
            self._设置操作反馈(
                f"兜底击中特效：{'特效2' if '2' in str(self._击中特效方案) else '特效1'}"
            )
            return None

        if 选项索引 == 8:
            self._切换背景亮度档位()
            self._设置操作反馈("背景亮度已切换")
            return None

        if 选项索引 == 9:
            self._性能模式 = not bool(self._性能模式)
            self._载荷["性能模式"] = bool(self._性能模式)
            self._应用背景视频状态()
            if bool(self._性能模式):
                self._圆环频谱舞台装饰 = None
            else:
                try:
                    from ui.圆环频谱叠加 import 圆环频谱舞台装饰

                    self._圆环频谱舞台装饰 = 圆环频谱舞台装饰()
                    self._应用圆环频谱调试设置()
                    if self._音频路径 and os.path.isfile(self._音频路径):
                        self._圆环频谱舞台装饰.绑定音频(str(self._音频路径))
                except Exception:
                    self._圆环频谱舞台装饰 = None
            self._设置操作反馈(
                f"极简性能模式已{'开启' if self._性能模式 else '关闭'}"
            )
            return None

        if 选项索引 == 10:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self._暂停菜单开启 = False
            return {"切换到": "选歌", "禁用黑屏过渡": True}

        self._暂停菜单开启 = False
        return {"退出程序": True}

    def _取可见血量HP(self) -> int:
        return int(
            max(
                0,
                min(
                    int(self._显示血量上限HP),
                    int(self._总血量HP) - int(self._隐藏血量HP),
                ),
            )
        )

    def _取血量显示比例(self) -> float:
        if int(self._显示血量上限HP) <= 0:
            return 0.0
        return float(self._取可见血量HP()) / float(self._显示血量上限HP)

    def _同步旧血量比例(self):
        self._血量 = float(max(0.0, min(1.0, self._取血量显示比例())))

    def _按判定取HP变化(self, 判定: str) -> int:
        判定 = str(判定 or "").lower()
        if 判定 in ("perfect", "cool", "good"):
            return 20
        if 判定 == "miss":
            return -40
        return 0

    def _应用血量回报(self, 回报列表) -> bool:
        if not 回报列表:
            return False

        新HP = int(self._总血量HP)
        for 回报 in 回报列表:
            新HP += int(self._按判定取HP变化(getattr(回报, "判定", "")))

        self._总血量HP = int(max(0, min(int(self._总血量上限HP), 新HP)))
        self._同步旧血量比例()
        return bool(self._总血量HP <= 0)

    def _立即失败结束(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        return {
            "切换到": "结算",
            "载荷": self._构建结算载荷(失败=True),
            "禁用黑屏过渡": True,
        }

    def _记录判定统计(self, 回报列表):
        if not 回报列表:
            return
        if not isinstance(getattr(self, "_判定统计", None), dict):
            self._判定统计 = {"perfect": 0, "cool": 0, "good": 0, "miss": 0}
        for 回报 in 回报列表:
            判定 = str(getattr(回报, "判定", "") or "").lower().strip()
            if 判定 in self._判定统计:
                try:
                    self._判定统计[判定] = int(self._判定统计.get(判定, 0) or 0) + 1
                except Exception:
                    self._判定统计[判定] = 1

    def _构建结算载荷(self, 失败: bool = False) -> dict:
        分数 = 0
        最大连击 = 0
        百分比 = "0.00%"
        if self._计分系统 is not None:
            try:
                分数 = int(getattr(self._计分系统, "当前分", 0) or 0)
            except Exception:
                分数 = 0
            try:
                最大连击 = int(getattr(self._计分系统, "最大连击", 0) or 0)
            except Exception:
                最大连击 = 0
            try:
                百分比 = str(self._计分系统.取百分比字符串())
            except Exception:
                百分比 = "0.00%"

        百分比数值 = 0.0
        try:
            百分比数值 = float(str(百分比).replace("%", "").strip() or 0.0)
        except Exception:
            百分比数值 = 0.0

        if 失败:
            评级 = "F"
        elif 百分比数值 >= 95.0:
            评级 = "S"
        elif 百分比数值 >= 90.0:
            评级 = "A"
        elif 百分比数值 >= 85.0:
            评级 = "B"
        elif 百分比数值 >= 80.0:
            评级 = "C"
        elif 百分比数值 >= 70.0:
            评级 = "E"
        else:
            评级 = "F"

        判定统计 = dict(getattr(self, "_判定统计", {}) or {})
        perfect数 = int(判定统计.get("perfect", 0) or 0)
        cool数 = int(判定统计.get("cool", 0) or 0)
        good数 = int(判定统计.get("good", 0) or 0)
        miss数 = int(判定统计.get("miss", 0) or 0)

        return {
            "曲目名": str(self._歌曲名 or ""),
            "sm路径": str(self._载荷.get("sm路径", "") or ""),
            "模式": str(self._载荷.get("模式", self._载荷.get("大模式", "竞速")) or "竞速"),
            "类型": str(self._载荷.get("类型", self._载荷.get("大模式", "竞速")) or "竞速"),
            "本局最高分": int(分数),
            "本局最大combo": int(最大连击),
            "歌曲时长秒": float(self._谱面总时长秒 or 0.0),
            "谱面总分": int(getattr(self, "_谱面总分缓存", 0) or 0),
            "百分比": str(百分比),
            "百分比数值": float(max(0.0, 百分比数值)),
            "评级": str(评级),
            "是否评价S": bool((not 失败) and 评级 == "S"),
            "失败": bool(失败),
            "perfect数": int(perfect数),
            "cool数": int(cool数),
            "good数": int(good数),
            "miss数": int(miss数),
            "是否全连": bool(miss数 <= 0),
            "封面路径": str(self._载荷.get("封面路径", "") or ""),
            "星级": int(self._载荷.get("星级", 0) or 0),
            "背景图片路径": str(getattr(self, "_背景图片路径", "") or ""),
            "背景视频路径": str(getattr(self, "_背景视频路径", "") or ""),
            "选歌原始索引": int(self._载荷.get("选歌原始索引", -1) or -1),
        }

    def _按回报播放计数动画(self, 回报列表, 起始连击: int):
        self._按回报播放计数动画_到渲染器(
            回报列表, 起始连击, getattr(self, "_谱面渲染器", None)
        )

    def _绘制按键提示(self, 屏幕: pygame.Surface):
        if self._小字体 is None:
            return

        状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
        if not isinstance(状态, dict):
            状态 = {}
        投币键显示 = str(状态.get("投币快捷键显示", "F1") or "F1").upper()

        行列表 = [
            f"{投币键显示} 投币",
            "F2 自动播放",
            "SPACE 暂停/继续",
            "R 重载歌曲",
            "ESC 暂停菜单",
        ]
        if bool(getattr(self, "_是否双踏板模式", False)):
            行列表.append("左手 Z/C/S/Q/E  右手 1/3/5/7/9")
        else:
            行列表.append("1/3/5/7/9 打击轨道")

        文图列表 = []
        最大宽 = 0
        总高 = 0
        for 文本 in 行列表:
            try:
                图 = self._小字体.render(str(文本), True, (225, 235, 255)).convert_alpha()
            except Exception:
                continue
            文图列表.append(图)
            最大宽 = max(最大宽, int(图.get_width()))
            总高 += int(图.get_height()) + 4

        if not 文图列表:
            return

        内边距 = 10
        盒宽 = int(最大宽 + 内边距 * 2)
        盒高 = int(max(24, 总高 + 内边距 * 2 - 4))
        rect = pygame.Rect(18, int(屏幕.get_height() - 18 - 盒高), 盒宽, 盒高)

        try:
            背板 = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            背板.fill((0, 0, 0, 150))
            屏幕.blit(背板, rect.topleft)
            pygame.draw.rect(屏幕, (90, 120, 150), rect, width=1, border_radius=8)
        except Exception:
            pass

        y = int(rect.y + 内边距)
        for 图 in 文图列表:
            屏幕.blit(图, (int(rect.x + 内边距), y))
            y += int(图.get_height()) + 4

    def _绘制操作反馈(self, 屏幕: pygame.Surface):
        if self._小字体 is None:
            return
        if self._操作反馈剩余秒 <= 0.0 or (not self._操作反馈文本):
            return

        比率 = float(
            max(0.0, min(1.0, self._操作反馈剩余秒 / max(0.001, self._操作反馈总秒)))
        )
        透明 = int(255 * (0.35 + 0.65 * 比率))
        try:
            文图 = self._小字体.render(
                str(self._操作反馈文本), True, (255, 255, 255)
            ).convert_alpha()
            文图.set_alpha(透明)
        except Exception:
            return

        内边距x = 12
        内边距y = 8
        rect = pygame.Rect(
            int(屏幕.get_width() - 文图.get_width() - 内边距x * 2 - 18),
            92,
            int(文图.get_width() + 内边距x * 2),
            int(文图.get_height() + 内边距y * 2),
        )
        try:
            背板 = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            背板.fill((0, 30, 36, int(150 * 比率)))
            屏幕.blit(背板, rect.topleft)
            pygame.draw.rect(屏幕, (0, 239, 251), rect, width=1, border_radius=8)
        except Exception:
            pass

        屏幕.blit(
            文图,
            (
                int(rect.x + (rect.w - 文图.get_width()) // 2),
                int(rect.y + (rect.h - 文图.get_height()) // 2),
            ),
        )

    def _绘制底部币值(self, 屏幕: pygame.Surface):
        try:
            字体_credit = (
                (self.上下文.get("字体", {}) or {}).get("投币_credit字")
                if isinstance(self.上下文, dict)
                else None
            )
        except Exception:
            字体_credit = None
        if not isinstance(字体_credit, pygame.font.Font):
            return
        try:
            状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
            投币数 = int((状态 or {}).get("投币数", 0) or 0)
        except Exception:
            投币数 = 0
        try:
            绘制底部联网与信用(
                屏幕=屏幕,
                联网原图=getattr(self, "_联网原图", None),
                字体_credit=字体_credit,
                credit数值=str(max(0, 投币数)),
                文本=f"CREDIT：{max(0, 投币数)}/3",
            )
        except Exception:
            pass

    def _绘制暂停菜单(self, 屏幕: pygame.Surface):
        self._暂停菜单项矩形 = []
        self._暂停菜单关闭按钮 = pygame.Rect(0, 0, 0, 0)
        if not bool(self._暂停菜单开启):
            return
        if self._小字体 is None:
            return
        try:
            屏宽, 屏高 = 屏幕.get_size()
            项列表 = self._取暂停菜单项文本()
            项数量 = max(1, len(项列表))
            遮罩 = pygame.Surface((屏宽, 屏高), pygame.SRCALPHA)
            遮罩.fill((0, 0, 0, 178))
            屏幕.blit(遮罩, (0, 0))

            面板宽 = int(max(760, min(1180, 屏宽 * 0.78)))
            面板高 = int(max(340, min(int(屏高 * 0.86), 210 + 项数量 * 42)))
            面板 = pygame.Rect(
                int((屏宽 - 面板宽) // 2),
                int((屏高 - 面板高) // 2),
                int(面板宽),
                int(面板高),
            )
            pygame.draw.rect(屏幕, (12, 18, 30), 面板, border_radius=16)
            pygame.draw.rect(屏幕, (72, 116, 188), 面板, width=2, border_radius=16)

            标题字 = self._字体 if self._字体 is not None else self._小字体
            标题面 = 标题字.render("PAUSE MENU", True, (240, 246, 255)).convert_alpha()
            屏幕.blit(标题面, (面板.x + 24, 面板.y + 18))
            self._暂停菜单关闭按钮 = pygame.Rect(
                int(面板.right - 46), int(面板.y + 14), 30, 30
            )
            pygame.draw.rect(
                屏幕, (58, 68, 96), self._暂停菜单关闭按钮, border_radius=8
            )
            pygame.draw.rect(
                屏幕,
                (180, 200, 236),
                self._暂停菜单关闭按钮,
                width=1,
                border_radius=8,
            )
            关字符 = 标题字.render("×", True, (240, 246, 255)).convert_alpha()
            屏幕.blit(
                关字符,
                关字符.get_rect(center=self._暂停菜单关闭按钮.center).topleft,
            )

            状态 = self.上下文.get("状态", {}) if isinstance(self.上下文, dict) else {}
            if not isinstance(状态, dict):
                状态 = {}
            投币键显示 = str(状态.get("投币快捷键显示", "F1") or "F1").upper()
            提示行 = [
                f"{投币键显示}投币",
                "小键盘1/3左右选，5确认（提示）",
                "鼠标点击选项，右上角×关闭",
                "游戏中小键盘1/3/5/7/9控制踏板",
            ]
            y = int(面板.y + 68)
            for 文本 in 提示行:
                行面 = self._小字体.render(str(文本), True, (210, 224, 246)).convert_alpha()
                屏幕.blit(行面, (面板.x + 24, y))
                y += int(行面.get_height()) + 3

            选项字 = self._字体 if self._字体 is not None else self._小字体
            y = int(max(面板.y + 166, y + 8))
            for idx, 项 in enumerate(项列表):
                选中 = idx == int(self._暂停菜单索引)
                前缀 = "▶ " if 选中 else "   "
                颜色 = (255, 235, 128) if 选中 else (225, 233, 248)
                项面 = 选项字.render(f"{前缀}{项}", True, 颜色).convert_alpha()
                行rect = pygame.Rect(
                    int(面板.x + 24),
                    int(y - 4),
                    int(max(280, 项面.get_width() + 22)),
                    int(项面.get_height() + 8),
                )
                if 选中:
                    pygame.draw.rect(屏幕, (42, 58, 90), 行rect, border_radius=8)
                屏幕.blit(项面, (int(行rect.x + 8), int(行rect.y + 4)))
                self._暂停菜单项矩形.append(行rect)
                y += int(项面.get_height()) + 10
        except Exception:
            pass

    # ---------------- 判定：可操作模式用 ----------------
    def _尝试命中(self, 轨道: int):
        if not self._事件:
            return

        当前秒 = float(self._当前谱面秒)
        窗口 = float(self._命中窗口秒)

        try:
            import bisect

            左边 = bisect.bisect_left(self._开始秒列表, 当前秒 - 窗口)
            右边 = bisect.bisect_right(self._开始秒列表, 当前秒 + 窗口)
        except Exception:
            左边 = max(0, self._下一丢失检查索引 - 16)
            右边 = min(len(self._事件), self._下一丢失检查索引 + 64)

        最佳索引 = -1
        最佳差值 = 999.0

        for 索引 in range(int(左边), int(右边)):
            if self._事件状态[索引] != 0:
                continue
            事件 = self._事件[索引]
            if int(事件.轨道序号) != int(轨道):
                continue
            差值 = abs(float(事件.开始秒) - 当前秒)
            if 差值 <= 窗口 and 差值 < 最佳差值:
                最佳差值 = 差值
                最佳索引 = 索引

        if 最佳索引 >= 0:
            self._事件状态[最佳索引] = 1
            self._触发判定光(int(轨道))

            # ✅ 可操作模式命中 +5
            self._血量 = min(1.0, float(self._血量) + 0.05)
            if (float(self._血量) >= 1.0) and (not self._已触发满血爆炸):
                self._触发满血爆炸()

    def _处理自动丢失(self):
        if not self._事件:
            return
        当前秒 = float(self._当前谱面秒)
        窗口 = float(self._丢失窗口秒)

        while self._下一丢失检查索引 < len(self._事件):
            索引 = int(self._下一丢失检查索引)
            事件 = self._事件[索引]
            st = float(事件.开始秒)
            if st + 窗口 > 当前秒:
                break

            if self._事件状态[索引] == 0:
                self._事件状态[索引] = -1
                # ✅ 可操作模式丢失 -5
                self._血量 = max(0.0, float(self._血量) - 0.05)

            self._下一丢失检查索引 += 1

    # ---------------- 音频控制 ----------------
    def _初始化音频设备(self):
        self._音频可用 = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self._音频可用 = True
        except Exception:
            self._音频可用 = False

    def 播放(self):
        if self._播放中:
            return
        self._播放中 = True
        self._起始系统秒 = time.perf_counter() - float(self._暂停时刻谱面秒)

        if (
            (not self._音频可用)
            or (not self._音频路径)
            or (not os.path.isfile(self._音频路径))
        ):
            return

        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        try:
            pygame.mixer.music.load(self._音频路径)
        except Exception:
            self._错误提示 = (
                self._错误提示 or "音频加载失败（mp3可能缺解码，优先换ogg）"
            )
            return

        # ✅ 核心修复：事件秒已应用 offset，所以音频起点=谱面秒（不再 -offset）
        音频起点 = max(0.0, float(self._暂停时刻谱面秒))

        try:
            pygame.mixer.music.play(start=音频起点)
        except TypeError:
            # ✅ 不支持 seek：只能从 0 播放，为了不“音画各走各的”，强制把谱面也回到 0
            if 音频起点 > 0.001:
                self._错误提示 = (
                    self._错误提示 + " | " if self._错误提示 else ""
                ) + "当前环境不支持音频seek（mp3常见），已强制从头播放"
                self.设定谱面时间(0.0)
            try:
                pygame.mixer.music.play()
            except Exception:
                self._错误提示 = self._错误提示 or "音频播放失败"
                return
        except Exception:
            try:
                pygame.mixer.music.play()
            except Exception:
                self._错误提示 = self._错误提示 or "音频播放失败"
                return

        self._音频已开始 = True
        self._音频暂停中 = False
        self._音频开始系统秒 = time.perf_counter()

    def 暂停(self):
        if not self._播放中:
            return
        self._播放中 = False
        self._暂停时刻谱面秒 = float(self._当前谱面秒)
        if self._音频可用:
            try:
                pygame.mixer.music.pause()
                self._音频暂停中 = True
            except Exception:
                pass

    def 设定谱面时间(self, 新秒: float):
        新秒 = float(max(0.0, float(新秒)))
        self._当前谱面秒 = 新秒
        self._暂停时刻谱面秒 = 新秒
        self._起始系统秒 = time.perf_counter() - 新秒

        # seek 时：为了避免“跳时间后还能判到过去的 note”，这里直接重置玩法状态
        try:
            if self._计分系统 is not None:
                self._计分系统.重置()
            if self._判定系统 is not None and hasattr(self, "_判定音符列表缓存"):
                try:
                    self._判定系统.加载谱面(self._判定音符列表缓存)
                except Exception:
                    pass
        except Exception:
            pass

        self._判定光 = [0.0] * 5

    # ---------------- 判定光 ----------------
    def _触发判定光(self, 轨道: int):
        if 0 <= int(轨道) < len(self._判定光):
            self._判定光[int(轨道)] = 1.0

    def _更新判定光(self, 时间差: float):
        衰减 = float(self._判定光衰减每秒) * float(max(0.0, 时间差))
        for i in range(len(self._判定光)):
            self._判定光[i] = max(0.0, float(self._判定光[i]) - 衰减)

    # ---------------- 爆炸 ----------------
    def _触发满血爆炸(self):
        self._已触发满血爆炸 = True
        self._爆炸剩余秒 = 0.75
        self._爆炸粒子 = []
        try:
            import random
        except Exception:
            return

        r = self._血条区域
        cx = float(r.x + r.w * 0.72)
        cy = float(r.y + r.h * 0.50)

        粒子数 = 46
        for _ in range(粒子数):
            速度 = 260.0 + random.random() * 380.0
            速度x = (random.random() * 2 - 1) * 速度
            速度y = (random.random() * 2 - 1) * 速度 * 0.85
            life = 0.35 + random.random() * 0.45
            self._爆炸粒子.append((cx, cy, 速度x, 速度y, life))

    def _绘制爆炸(self, 屏幕: pygame.Surface):
        if not self._爆炸粒子:
            return
        for x, y, vx, vy, life in self._爆炸粒子:
            透明度 = int(220 * max(0.0, min(1.0, float(life) / 0.75)))
            半径 = int(2 + 6 * max(0.0, min(1.0, float(life))))
            pygame.draw.circle(
                屏幕, (255, 240, 190, 透明度), (int(x), int(y)), max(1, 半径)
            )

    # ---------------- 字体/背景/皮肤/布局 ----------------
    def _初始化字体(self):
        try:
            from core.工具 import 获取字体  # type: ignore

            self._字体 = 获取字体(20, 是否粗体=False)
            self._小字体 = 获取字体(16, 是否粗体=False)
            return
        except Exception:
            pass

        pygame.font.init()
        try:
            self._字体 = pygame.font.SysFont("Microsoft YaHei", 20)
            self._小字体 = pygame.font.SysFont("Microsoft YaHei", 16)
        except Exception:
            self._字体 = pygame.font.Font(None, 20)
            self._小字体 = pygame.font.Font(None, 16)

    def _加载背景(self, 背景文件名: str):
        根目录 = _取项目根目录()
        背景文件名 = str(背景文件名 or "").strip()
        self._背景图片路径 = ""

        候选路径: List[str] = []
        if 背景文件名:
            候选路径.append(os.path.join(根目录, "冷资源", "backimages", "背景图", 背景文件名))
            候选路径.append(os.path.join(根目录, "冷资源", "backimages", 背景文件名))
        候选路径.append(os.path.join(根目录, "冷资源", "backimages", "选歌界面.png"))

        背景图 = None
        for p in 候选路径:
            if p and os.path.isfile(p):
                try:
                    背景图 = pygame.image.load(p).convert()
                    self._背景图片路径 = str(p)
                    break
                except Exception:
                    continue

        self._背景原图 = 背景图
        self._背景缩放缓存 = None
        self._背景缩放尺寸 = (0, 0)

    def _加载背景视频(self, 视频来源: str):
        视频来源 = str(视频来源 or "").strip()
        self._背景视频路径 = ""
        try:
            if self._背景视频播放器 is not None and hasattr(
                self._背景视频播放器, "关闭"
            ):
                self._背景视频播放器.关闭()
        except Exception:
            pass
        self._背景视频播放器 = None

        if not 视频来源:
            return

        try:
            if os.path.isdir(视频来源):
                from core.视频 import 全局视频顺序循环播放器

                播放器 = 全局视频顺序循环播放器(视频来源)
                播放器.打开(是否重置进度=True)
                self._背景视频播放器 = 播放器
                self._背景视频路径 = 视频来源
                return

            if not os.path.isfile(视频来源):
                return

            from core.视频 import 全局视频循环播放器

            self._背景视频播放器 = 全局视频循环播放器(视频来源)
            self._背景视频播放器.打开(是否重置进度=True)
            self._背景视频路径 = 视频来源
        except Exception as 异常:
            self._背景视频播放器 = None
            self._背景视频路径 = ""
            self._错误提示 = (
                self._错误提示 + " | " if self._错误提示 else ""
            ) + f"背景视频初始化失败：{type(异常).__name__} {异常}"

    def _应用背景视频状态(self):
        if bool(self._性能模式) or bool(self._视频背景关闭):
            self._加载背景视频("")
        else:
            self._加载背景视频(str(self._默认背景视频目录 or ""))

    def _加载联网图标(self):
        self._联网原图 = None
        try:
            资源 = self.上下文.get("资源", {}) if isinstance(self.上下文, dict) else {}
            if not isinstance(资源, dict):
                return
            路径 = str(资源.get("投币_联网图标", "") or "")
            if 路径 and os.path.isfile(路径):
                self._联网原图 = pygame.image.load(路径).convert_alpha()
        except Exception:
            self._联网原图 = None

    def _绘制cover背景面(self, 屏幕: pygame.Surface, 原图: pygame.Surface):
        if not isinstance(原图, pygame.Surface):
            return

        屏宽, 屏高 = 屏幕.get_size()
        原宽 = int(max(1, 原图.get_width()))
        原高 = int(max(1, 原图.get_height()))
        比例 = max(float(屏宽) / float(原宽), float(屏高) / float(原高))
        新宽 = int(max(1, round(float(原宽) * 比例)))
        新高 = int(max(1, round(float(原高) * 比例)))

        try:
            图2 = pygame.transform.smoothscale(原图, (新宽, 新高)).convert()
        except Exception:
            try:
                图2 = pygame.transform.scale(原图, (新宽, 新高)).convert()
            except Exception:
                return

        x = int((屏宽 - 新宽) // 2)
        y = int((屏高 - 新高) // 2)
        屏幕.blit(图2, (x, y))

    def _绘制背景(self, 屏幕: pygame.Surface):
        w, h = 屏幕.get_size()
        已绘制背景 = False

        try:
            if self._背景视频播放器 is not None and hasattr(
                self._背景视频播放器, "读取帧"
            ):
                视频帧 = self._背景视频播放器.读取帧()
                if isinstance(视频帧, pygame.Surface):
                    self._绘制cover背景面(屏幕, 视频帧)
                    已绘制背景 = True
        except Exception:
            已绘制背景 = False

        if not 已绘制背景:
            if self._背景原图 is None:
                屏幕.fill((15, 15, 18))
            else:
                self._绘制cover背景面(屏幕, self._背景原图)

        if bool(getattr(self, "_显示准备动画", False)) and (not bool(getattr(self, "_准备动画已完成", True))):
            需刷新无蒙版 = False
            try:
                if (self._准备动画背景无蒙版 is None) or (
                    self._准备动画背景无蒙版.get_size() != 屏幕.get_size()
                ):
                    需刷新无蒙版 = True
            except Exception:
                需刷新无蒙版 = True
            if 需刷新无蒙版:
                try:
                    self._准备动画背景无蒙版 = 屏幕.copy()
                except Exception:
                    self._准备动画背景无蒙版 = None

        目标暗层alpha = int(
            max(0, min(255, int(getattr(self, "_背景暗层alpha", 224) or 0)))
        )
        if (
            (self._背景暗层缓存 is None)
            or (self._背景暗层尺寸 != (w, h))
            or (int(getattr(self, "_背景暗层缓存alpha", -1)) != 目标暗层alpha)
        ):
            try:
                self._背景暗层缓存 = pygame.Surface((w, h), pygame.SRCALPHA)
                self._背景暗层缓存.fill((0, 0, 0, 目标暗层alpha))
                self._背景暗层尺寸 = (w, h)
                self._背景暗层缓存alpha = int(目标暗层alpha)
            except Exception:
                self._背景暗层缓存 = None
                self._背景暗层尺寸 = (0, 0)
                self._背景暗层缓存alpha = -1

        if self._背景暗层缓存 is not None:
            屏幕.blit(self._背景暗层缓存, (0, 0))

    def _加载准备动画资源(self):
        self._准备动画图 = 加载准备动画图片(_取项目根目录())
        self._加载准备动画音效()

    def _加载准备动画音效(self):
        self._准备音效 = None
        try:
            音效路径 = os.path.join(_取项目根目录(), "冷资源", "backsound", "准备就绪音效.mp3")
            if pygame.mixer.get_init() and os.path.isfile(音效路径):
                self._准备音效 = pygame.mixer.Sound(音效路径)
        except Exception:
            self._准备音效 = None

    def _播放准备动画音效(self):
        try:
            if self._准备音效通道 is not None:
                self._准备音效通道.stop()
        except Exception:
            pass
        try:
            if self._准备音效 is not None:
                self._准备音效通道 = self._准备音效.play()
        except Exception:
            self._准备音效通道 = None

    def _绘制准备动画(self, 屏幕: pygame.Surface):
        if (not self._显示准备动画) or bool(self._准备动画已完成):
            return

        双踏板模式 = bool(getattr(self, "_是否双踏板模式", False))
        经过秒 = max(0.0, float(time.perf_counter() - float(self._准备动画开始秒 or 0.0)))
        区域 = 计算准备动画区域(
            屏幕.get_size(),
            int(self._轨道起x),
            int(self._轨道总宽),
            int(self._取当前判定线y("左")),
            int(self._箭头基准宽),
            self._血条区域,
        )
        if 双踏板模式:
            # 双踏板模式取消准备阶段“判定区裁切”效果，避免双侧判定区被局部裁切。
            区域["判定区"] = pygame.Rect(0, 0, 0, 0)
            self._准备动画判定区图层 = None
            self._准备动画判定区矩形 = None
        else:
            try:
                渲染器 = getattr(self, "_谱面渲染器", None)
                渲染输入 = getattr(self, "_准备动画渲染输入", None)
                if (
                    渲染器 is not None
                    and 渲染输入 is not None
                ):
                    屏幕尺寸 = tuple(int(v) for v in 屏幕.get_size())
                    需重建判定区层 = False
                    try:
                        旧层 = getattr(self, "_准备动画判定区图层", None)
                        if (not isinstance(旧层, pygame.Surface)) or 旧层.get_size() != 屏幕尺寸:
                            需重建判定区层 = True
                    except Exception:
                        需重建判定区层 = True

                    if 需重建判定区层 and hasattr(渲染器, "取准备动画判定区图层"):
                        try:
                            层, 实际判定区 = 渲染器.取准备动画判定区图层(屏幕, 渲染输入)
                            self._准备动画判定区图层 = 层 if isinstance(层, pygame.Surface) else None
                            self._准备动画判定区矩形 = (
                                实际判定区.copy()
                                if isinstance(实际判定区, pygame.Rect)
                                else None
                            )
                        except Exception:
                            self._准备动画判定区图层 = None
                            self._准备动画判定区矩形 = None

                    if (
                        self._准备动画判定区矩形 is None
                        and hasattr(渲染器, "取准备动画判定区矩形")
                    ):
                        实际判定区 = 渲染器.取准备动画判定区矩形(屏幕, 渲染输入)
                        if isinstance(实际判定区, pygame.Rect):
                            self._准备动画判定区矩形 = 实际判定区.copy()

                    if isinstance(self._准备动画判定区矩形, pygame.Rect):
                        if self._准备动画判定区矩形.w > 0 and self._准备动画判定区矩形.h > 0:
                            区域["判定区"] = self._准备动画判定区矩形.copy()
            except Exception:
                pass

        try:
            动画设置 = dict(getattr(self, "_准备动画设置", {}) or {})
            动画设置["背景蒙版透明度"] = float(
                max(0, min(255, int(getattr(self, "_背景暗层alpha", 224) or 0)))
            )
        except Exception:
            动画设置 = dict(getattr(self, "_准备动画设置", {}) or {})
        绘制准备就绪动画(
            屏幕=屏幕,
            基础场景图=getattr(self, "_准备动画基础场景图", None),
            背景无蒙版图=getattr(self, "_准备动画背景无蒙版", None),
            准备图片=dict(getattr(self, "_准备动画图", {}) or {}),
            设置=动画设置,
            经过秒=float(经过秒),
            判定区矩形=区域["判定区"],
            顶部HUD矩形=区域["顶部HUD"],
            判定区图层=(None if 双踏板模式 else getattr(self, "_准备动画判定区图层", None)),
            运行缓存=getattr(self, "_准备动画绘制缓存", None),
        )

    def _加载皮肤图(self):
        if not os.path.isdir(self._皮肤目录):
            self._错误提示 = self._错误提示 or f"找不到箭头皮肤目录：{self._皮肤目录}"
            self._皮肤 = None
            return

        self._皮肤 = 皮肤资源(self._皮肤目录)
        for i, 方向名 in enumerate(self._轨道方向名):
            self._点按图[i] = self._皮肤.取点按(方向名)
            self._判定区图[i] = self._皮肤.取判定区(方向名)
            self._长按身体图[i] = self._皮肤.取长按身体(方向名)
            self._长按尾巴图[i] = self._皮肤.取长按尾巴(方向名)

    def _重算布局(self, 强制: bool = False):
        屏幕: pygame.Surface = self.上下文["屏幕"]
        w, h = 屏幕.get_size()
        if (not 强制) and (self._屏幕尺寸 == (w, h)):
            return

        self._屏幕尺寸 = (w, h)

        # ✅ 头像框更大：由“屏幕宽 5%” -> “屏幕宽 6%”，并把血条高度再抬一点
        头像边 = int(max(64, min(180, w * 0.06)))
        self._血条高度 = int(max(int(头像边 * 1.15), 72))
        self._血条区域 = pygame.Rect(18, 10, w - 36, self._血条高度)

        self._信息高度 = 22
        self._信息y = int(self._血条区域.bottom + 6)

        # ✅ 判定区紧贴血条/信息
        self._顶部y = int(self._信息y + self._信息高度 + 6)
        self._判定线y = int(self._顶部y + max(56, int(h * 0.08)))
        self._底部y = int(h - 24)

        # =========================
        # ✅ 五键紧凑：中心间距更小，但箭头尺寸不缩水
        # =========================
        self._箭头基准宽 = int(max(64, min(118, w * 0.072)))

        实际缩放 = float(self._箭头默认缩放) * float(self._尺寸倍率)
        箭头宽 = int(max(28, int(self._箭头基准宽 * 实际缩放)))

        紧凑系数 = 0.88
        self._轨道中心间距 = int(max(24, int(箭头宽 * 紧凑系数)))
        self._轨道槽宽 = int(max(箭头宽 + 10, int(箭头宽 * 1.08)))

        轨道数 = 5 if bool(getattr(self, "_是否双踏板模式", False)) else int(self._轨道数)
        轨道总宽 = int(self._轨道槽宽 + (轨道数 - 1) * self._轨道中心间距)

        最大总宽 = int(max(260, w - 40))
        if 轨道总宽 > 最大总宽:
            缩放 = 最大总宽 / float(max(1, 轨道总宽))
            self._轨道槽宽 = int(max(40, int(self._轨道槽宽 * 缩放)))
            self._轨道中心间距 = int(max(22, int(self._轨道中心间距 * 缩放)))
            轨道总宽 = int(self._轨道槽宽 + (轨道数 - 1) * self._轨道中心间距)

        self._轨道总宽 = int(轨道总宽)
        self._轨道起x = int((w - self._轨道总宽) // 2)

        self._单轨宽 = int(self._轨道槽宽)
        try:
            self._刷新双踏板强制判定线y()
        except Exception:
            pass

        self._背景缩放缓存 = None
        self._背景缩放尺寸 = (0, 0)
        self._预热渲染缓存()

    def _取箭头目标宽(self, 实际箭头缩放: float) -> int:
        # ✅ 解耦：箭头宽度跟“箭头基准宽”走，不再跟轨道宽走
        基准 = int(getattr(self, "_箭头基准宽", 0) or 0)
        if 基准 <= 0:
            # 兜底（极端情况下才会走到）
            基准 = int(max(48, min(120, int(self._单轨宽 * 0.60))))

        目标宽 = int(max(22, int(float(基准) * float(实际箭头缩放))))
        return 目标宽

    def _预热渲染缓存(self):
        if not hasattr(self, "_谱面渲染器") or self._谱面渲染器 is None:
            return
        try:
            屏幕: pygame.Surface = self.上下文["屏幕"]
        except Exception:
            return

        try:
            实际箭头缩放 = float(self._箭头默认缩放) * float(self._尺寸倍率)
        except Exception:
            实际箭头缩放 = 1.0

        箭头目标宽 = int(self._取箭头目标宽(实际箭头缩放))
        try:
            游戏区参数 = self._谱面渲染器._取游戏区参数()
        except Exception:
            游戏区参数 = {}

        try:
            游戏缩放 = float(游戏区参数.get("缩放", 1.0) or 1.0)
        except Exception:
            游戏缩放 = 1.0
        try:
            判定区宽度系数 = float(游戏区参数.get("判定区宽度系数", 1.0) or 1.0)
        except Exception:
            判定区宽度系数 = 1.0
        try:
            特效宽度系数 = float(游戏区参数.get("击中特效宽度系数", 3.0) or 3.0)
        except Exception:
            特效宽度系数 = 3.0

        判定区宽 = int(max(24, round(float(箭头目标宽) * 游戏缩放 * 判定区宽度系数)))
        特效宽 = int(max(40, round(float(箭头目标宽) * 游戏缩放 * 特效宽度系数 * 1.25)))
        try:
            self._谱面渲染器.预热性能缓存(
                屏幕.get_size(),
                int(箭头目标宽),
                int(判定区宽),
                int(特效宽),
            )
        except Exception:
            pass
        if bool(getattr(self, "_是否双踏板模式", False)) and getattr(
            self, "_谱面渲染器_右", None
        ) is not None:
            try:
                self._谱面渲染器_右.预热性能缓存(
                    屏幕.get_size(),
                    int(箭头目标宽),
                    int(判定区宽),
                    int(特效宽),
                )
            except Exception:
                pass

    def _画点按(
        self, 屏幕: pygame.Surface, 轨道: int, x中心: int, y: float, 实际箭头缩放: float
    ):
        if y < float(self._判定线y):
            return
        图 = self._点按图[int(轨道)]
        if 图:
            目标宽 = self._取箭头目标宽(实际箭头缩放)
            比例 = 目标宽 / float(max(1, 图.get_width()))
            目标高 = int(图.get_height() * 比例)
            缩放图 = pygame.transform.smoothscale(图, (目标宽, 目标高))
            屏幕.blit(缩放图, (int(x中心 - 目标宽 // 2), int(y - 目标高 // 2)))

    def _画长按(
        self,
        屏幕: pygame.Surface,
        轨道: int,
        x中心: int,
        y开始: float,
        y结束: float,
        实际箭头缩放: float,
    ):
        y1 = float(min(y开始, y结束))
        y2 = float(max(y开始, y结束))
        y1 = max(y1, float(self._判定线y))

        if y2 <= y1:
            return

        身体图 = self._长按身体图[int(轨道)]
        尾巴图 = self._长按尾巴图[int(轨道)]

        目标宽 = self._取箭头目标宽(实际箭头缩放)

        if 身体图:
            比例 = 目标宽 / float(max(1, 身体图.get_width()))
            单块高 = int(max(8, 身体图.get_height() * 比例))
            缩放身体 = pygame.transform.smoothscale(身体图, (目标宽, 单块高))
            当前y = int(y1)
            while 当前y < int(y2):
                屏幕.blit(缩放身体, (int(x中心 - 目标宽 // 2), int(当前y)))
                当前y += int(单块高)

        if 尾巴图:
            比例 = 目标宽 / float(max(1, 尾巴图.get_width()))
            目标高 = int(max(8, 尾巴图.get_height() * 比例))
            缩放尾 = pygame.transform.smoothscale(尾巴图, (目标宽, 目标高))
            屏幕.blit(缩放尾, (int(x中心 - 目标宽 // 2), int(y2 - 目标高 // 2)))

        self._画点按(屏幕, 轨道, x中心, y开始, 实际箭头缩放)

    def _绘制血条(self, 屏幕: pygame.Surface, 区域: pygame.Rect):
        屏幕宽 = int(self._屏幕尺寸[0])

        头像边 = int(max(区域.h, max(1, int(屏幕宽 * 0.05))))
        头像边 = int(min(头像边, 区域.h))
        头像区 = pygame.Rect(int(区域.x), int(区域.y), int(头像边), int(头像边))

        条区 = pygame.Rect(
            int(头像区.right + 12),
            int(区域.y + int(区域.h * 0.18)),
            int(区域.w - 头像区.w - 24),
            int(max(16, int(区域.h * 0.64))),
        )

        # ✅ 去边框：不画外层框
        # 头像
        头像图 = self._取头像图_懒加载()
        if 头像图 is not None:
            目标 = pygame.transform.smoothscale(
                头像图, (头像区.w, 头像区.h)
            ).convert_alpha()
            圆罩 = pygame.Surface((头像区.w, 头像区.h), pygame.SRCALPHA)
            圆罩.fill((0, 0, 0, 0))
            pygame.draw.circle(
                圆罩,
                (255, 255, 255, 255),
                (头像区.w // 2, 头像区.h // 2),
                头像区.w // 2,
            )
            目标.blit(圆罩, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            屏幕.blit(目标, 头像区.topleft)
        else:
            pygame.draw.circle(屏幕, (80, 80, 90), 头像区.center, 头像区.w // 2)

        # 血条底
        pygame.draw.rect(屏幕, (28, 28, 34), 条区, border_radius=12)

        # 仍保留你原来的“50%±10%”演示动画（你后续再改成真实血量）
        try:
            import math

            相位 = float(time.perf_counter() - float(self._入场系统秒))
            血量显示 = 0.50 + 0.10 * math.sin(2.0 * math.pi * 2.0 * 相位)
            血量显示 = float(max(0.0, min(1.0, 血量显示)))
        except Exception:
            血量显示 = float(max(0.0, min(1.0, self._血量)))

        填充宽 = int(条区.w * 血量显示)
        填充区 = pygame.Rect(int(条区.x), int(条区.y), int(max(0, 填充宽)), int(条区.h))

        r = int(220 - 90 * 血量显示)
        g = int(80 + 150 * 血量显示)
        b = 70
        pygame.draw.rect(屏幕, (r, g, b), 填充区, border_radius=12)

        if self._小字体 is not None:
            文 = self._小字体.render(
                f"HP {int(血量显示 * 100):3d}%", True, (240, 240, 245)
            )
            屏幕.blit(
                文,
                (
                    int(条区.right - 文.get_width() - 10),
                    int(条区.y + (条区.h - 文.get_height()) // 2),
                ),
            )

    def _取头像图_懒加载(self):
        try:
            if not hasattr(self, "_头像图缓存"):
                self._头像图缓存 = None
                self._头像图_缓存key = ""

            data = self._取个人资料json_懒加载()
            头像文件 = str((data or {}).get("头像文件", "") or "").strip()
            if not 头像文件:
                self._头像图缓存 = None
                self._头像图_缓存key = ""
                return None

            根目录 = ""
            try:
                资源 = self.上下文.get("资源", {}) or {}
                根目录 = str(资源.get("根", "") or "")
            except Exception:
                根目录 = ""

            if not 根目录:
                根目录 = _取项目根目录()

            头像路径 = self._解析个人资料资源路径(头像文件)
            if not os.path.isfile(头像路径):
                self._头像图缓存 = None
                self._头像图_缓存key = ""
                return None

            json路径 = os.path.join(根目录, "UI-img", "个人中心-个人资料", "个人资料.json")
            json_mtime = (
                float(os.path.getmtime(json路径)) if os.path.isfile(json路径) else -1.0
            )
            头像_mtime = float(os.path.getmtime(头像路径))

            缓存key = f"{头像路径}|{json_mtime:.6f}|{头像_mtime:.6f}"
            if str(getattr(self, "_头像图_缓存key", "") or "") == 缓存key:
                return getattr(self, "_头像图缓存", None)

            图 = pygame.image.load(头像路径).convert_alpha()
            self._头像图缓存 = 图
            self._头像图_缓存key = 缓存key
            return 图
        except Exception:
            try:
                self._头像图缓存 = None
                self._头像图_缓存key = ""
            except Exception:
                pass
            return None

    def _取个人资料json_懒加载(self) -> dict:
        """
        读取：UI-img\\个人中心-个人资料\\个人资料.json
        缓存策略：按 json 的 mtime 作为 key
        """
        try:
            # 懒创建缓存字段（不强依赖 __init__）
            if not hasattr(self, "_个人资料json_缓存"):
                self._个人资料json_缓存 = {}
                self._个人资料json_缓存key = ""

            根目录 = ""
            try:
                资源 = self.上下文.get("资源", {}) or {}
                根目录 = str(资源.get("根", "") or "")
            except Exception:
                根目录 = ""

            if not 根目录:
                try:
                    根目录 = _取项目根目录()
                except Exception:
                    根目录 = ""

            资料目录 = os.path.join(根目录, "UI-img", "个人中心-个人资料")
            资料路径 = os.path.join(资料目录, "个人资料.json")
            if not os.path.isfile(资料路径):
                self._个人资料json_缓存 = {}
                self._个人资料json_缓存key = ""
                return {}

            json_mtime = float(os.path.getmtime(资料路径))
            缓存key = f"{资料路径}|{json_mtime:.6f}"
            if str(getattr(self, "_个人资料json_缓存key", "") or "") == 缓存key:
                return dict(getattr(self, "_个人资料json_缓存", {}) or {})

            import json

            with open(资料路径, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                data = {}

            self._个人资料json_缓存 = dict(data)
            self._个人资料json_缓存key = 缓存key
            return dict(self._个人资料json_缓存)

        except Exception:
            try:
                self._个人资料json_缓存 = {}
                self._个人资料json_缓存key = ""
            except Exception:
                pass
            return {}

    def _取昵称_懒加载(self) -> str:
        try:
            data = self._取个人资料json_懒加载()
            昵称 = str((data or {}).get("昵称", "") or "").strip()
            return 昵称
        except Exception:
            return ""

    def _解析个人资料资源路径(self, 路径值: str) -> str:
        try:
            文本 = str(路径值 or "").strip()
            if not 文本:
                return ""
            if os.path.isabs(文本):
                return 文本
            根目录 = ""
            try:
                资源 = self.上下文.get("资源", {}) or {}
                根目录 = str(资源.get("根", "") or "")
            except Exception:
                根目录 = ""
            if not 根目录:
                根目录 = _取项目根目录()
            文本 = 文本.replace("/", os.sep).replace("\\", os.sep)
            if 文本.startswith(f"UI-img{os.sep}") or 文本.startswith(f"json{os.sep}"):
                return os.path.join(根目录, 文本)
            return os.path.join(根目录, "UI-img", "个人中心-个人资料", os.path.basename(文本))
        except Exception:
            return ""

    def _取段位图_懒加载(self) -> Optional[pygame.Surface]:
        """
        读取个人资料.json 中的进度.段位路径
        缓存策略：按 png mtime
        """
        try:
            if not hasattr(self, "_段位图缓存"):
                self._段位图缓存 = None
                self._段位图缓存key = ""

            data = self._取个人资料json_懒加载()
            进度 = (data or {}).get("进度", {}) if isinstance((data or {}).get("进度", {}), dict) else {}
            段位值 = 进度.get("段位", "")
            路径 = self._解析个人资料资源路径(str(段位值 or ""))
            if not os.path.isfile(路径):
                self._段位图缓存 = None
                self._段位图缓存key = ""
                return None

            mtime = float(os.path.getmtime(路径))
            key = f"{路径}|{mtime:.6f}"
            if str(getattr(self, "_段位图缓存key", "") or "") == key:
                return getattr(self, "_段位图缓存", None)

            图 = pygame.image.load(路径).convert_alpha()
            self._段位图缓存 = 图
            self._段位图缓存key = key
            return 图
        except Exception:
            try:
                self._段位图缓存 = None
                self._段位图缓存key = ""
            except Exception:
                pass
            return None

    @staticmethod
    def _秒格式化(t: float) -> str:
        t = float(max(0.0, t))
        m = int(t // 60)
        s = t - m * 60
        return f"{m:02d}:{s:05.2f}"
