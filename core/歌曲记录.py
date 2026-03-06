import json
import os
from typing import Dict


def _索引路径(项目根: str) -> str:
    return os.path.join(str(项目根 or os.getcwd()), "songs", "歌曲记录索引.json")


def 读取歌曲记录索引(项目根: str) -> Dict[str, dict]:
    路径 = _索引路径(项目根)
    if not os.path.isfile(路径):
        return {}
    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码) as f:
                数据 = json.load(f)
            return 数据 if isinstance(数据, dict) else {}
        except Exception:
            continue
    return {}


def 保存歌曲记录索引(项目根: str, 数据: Dict[str, dict]):
    路径 = _索引路径(项目根)
    os.makedirs(os.path.dirname(路径), exist_ok=True)
    with open(路径, "w", encoding="utf-8") as f:
        json.dump(dict(数据 or {}), f, ensure_ascii=False, indent=2)


def _歌曲键(sm路径: str, 项目根: str) -> str:
    sm路径 = str(sm路径 or "").strip()
    if not sm路径:
        return ""
    try:
        return os.path.relpath(sm路径, str(项目根 or os.getcwd())).replace("\\", "/")
    except Exception:
        return sm路径.replace("\\", "/")


def 取歌曲记录(项目根: str, sm路径: str, 歌名: str = "") -> dict:
    索引 = 读取歌曲记录索引(项目根)
    键 = _歌曲键(sm路径, 项目根)
    if not 键:
        return {"最高分": 0, "歌名": str(歌名 or ""), "sm路径": str(sm路径 or "")}
    项 = 索引.get(键)
    if not isinstance(项, dict):
        项 = {"最高分": 0, "歌名": str(歌名 or ""), "sm路径": str(sm路径 or "")}
        索引[键] = dict(项)
        保存歌曲记录索引(项目根, 索引)
    else:
        if "最高分" not in 项:
            项["最高分"] = 0
        if str(项.get("歌名", "") or "") == "" and 歌名:
            项["歌名"] = str(歌名)
        if str(项.get("sm路径", "") or "") == "" and sm路径:
            项["sm路径"] = str(sm路径)
            索引[键] = dict(项)
            保存歌曲记录索引(项目根, 索引)
    return dict(项)


def 更新歌曲最高分(项目根: str, sm路径: str, 歌名: str, 分数: int) -> dict:
    索引 = 读取歌曲记录索引(项目根)
    键 = _歌曲键(sm路径, 项目根)
    if not 键:
        return {"是否新纪录": False, "最高分": int(max(0, 分数)), "旧最高分": 0}
    项 = 索引.get(键)
    if not isinstance(项, dict):
        项 = {"最高分": 0, "歌名": str(歌名 or ""), "sm路径": str(sm路径 or "")}
    旧最高分 = int(项.get("最高分", 0) or 0)
    新分数 = int(max(0, 分数))
    是否新纪录 = bool(新分数 > 旧最高分)
    if 是否新纪录:
        项["最高分"] = 新分数
        项["歌名"] = str(歌名 or 项.get("歌名", "") or "")
        项["sm路径"] = str(sm路径 or 项.get("sm路径", "") or "")
        索引[键] = dict(项)
        保存歌曲记录索引(项目根, 索引)
    elif 键 not in 索引:
        索引[键] = dict(项)
        保存歌曲记录索引(项目根, 索引)
    return {
        "是否新纪录": 是否新纪录,
        "最高分": int(max(旧最高分, 新分数)),
        "旧最高分": int(旧最高分),
    }
