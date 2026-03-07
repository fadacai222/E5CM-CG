import json
import os
import sys
from typing import Dict, List


def _规范路径(路径: str) -> str:
    try:
        return os.path.abspath(str(路径 or "").strip())
    except Exception:
        return ""


def _去重路径列表(路径列表: List[str]) -> List[str]:
    结果: List[str] = []
    已见 = set()
    for 路径 in 路径列表:
        规范后 = _规范路径(路径)
        if (not 规范后) or (规范后 in 已见):
            continue
        已见.add(规范后)
        结果.append(规范后)
    return 结果


def _向上查找目录(起点: str, 判定函数, 最大层数: int = 10) -> str:
    当前 = _规范路径(起点)
    if not 当前:
        return ""

    for _ in range(max(1, int(最大层数))):
        try:
            if 判定函数(当前):
                return 当前
        except Exception:
            pass

        上级 = os.path.dirname(当前)
        if 上级 == 当前:
            break
        当前 = 上级

    return ""


def _取运行根目录(项目根: str = "") -> str:
    try:
        已缓存 = getattr(_取运行根目录, "_缓存路径", "")
        if isinstance(已缓存, str) and 已缓存 and os.path.isdir(已缓存):
            return 已缓存
    except Exception:
        pass

    候选起点列表: List[str] = []

    if 项目根:
        候选起点列表.append(项目根)

    try:
        if getattr(sys, "frozen", False):
            候选起点列表.append(os.path.dirname(os.path.abspath(sys.executable)))
    except Exception:
        pass

    try:
        候选起点列表.append(os.getcwd())
    except Exception:
        pass

    try:
        候选起点列表.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass

    候选起点列表 = _去重路径列表(候选起点列表)

    def _是否运行根(目录: str) -> bool:
        return bool(
            os.path.isdir(os.path.join(目录, "songs"))
            or os.path.isdir(os.path.join(目录, "json"))
            or os.path.isfile(os.path.join(目录, "main.py"))
        )

    for 起点 in 候选起点列表:
        命中 = _向上查找目录(起点, _是否运行根, 最大层数=12)
        if 命中:
            setattr(_取运行根目录, "_缓存路径", 命中)
            return 命中

    for 起点 in 候选起点列表:
        if 起点 and os.path.isdir(起点):
            setattr(_取运行根目录, "_缓存路径", 起点)
            return 起点

    回退 = _规范路径(os.getcwd()) or "."
    setattr(_取运行根目录, "_缓存路径", 回退)
    return 回退


def _取资源根目录(项目根: str = "") -> str:
    try:
        已缓存 = getattr(_取资源根目录, "_缓存路径", "")
        if isinstance(已缓存, str) and 已缓存 and os.path.isdir(已缓存):
            return 已缓存
    except Exception:
        pass

    候选起点列表: List[str] = []

    if 项目根:
        候选起点列表.append(项目根)

    try:
        if getattr(sys, "frozen", False):
            临时目录 = _规范路径(getattr(sys, "_MEIPASS", ""))
            if 临时目录:
                候选起点列表.append(临时目录)
            候选起点列表.append(os.path.dirname(os.path.abspath(sys.executable)))
    except Exception:
        pass

    try:
        候选起点列表.append(os.getcwd())
    except Exception:
        pass

    try:
        候选起点列表.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass

    候选起点列表 = _去重路径列表(候选起点列表)

    def _是否资源根(目录: str) -> bool:
        return bool(
            os.path.isdir(os.path.join(目录, "UI-img"))
            or os.path.isdir(os.path.join(目录, "json"))
            or os.path.isdir(os.path.join(目录, "songs"))
        )

    for 起点 in 候选起点列表:
        命中 = _向上查找目录(起点, _是否资源根, 最大层数=12)
        if 命中:
            setattr(_取资源根目录, "_缓存路径", 命中)
            return 命中

    for 起点 in 候选起点列表:
        if 起点 and os.path.isdir(起点):
            setattr(_取资源根目录, "_缓存路径", 起点)
            return 起点

    回退 = _规范路径(os.getcwd()) or "."
    setattr(_取资源根目录, "_缓存路径", 回退)
    return 回退


def _取歌曲目录(项目根: str) -> str:
    运行根 = _取运行根目录(项目根)
    资源根 = _取资源根目录(项目根)

    候选路径列表 = _去重路径列表(
        [
            os.path.join(运行根, "songs"),
            os.path.join(str(项目根 or ""), "songs"),
            os.path.join(资源根, "songs"),
        ]
    )

    for 路径 in 候选路径列表:
        if 路径 and os.path.isdir(路径):
            return 路径

    return os.path.join(运行根, "songs")


def _主索引路径(项目根: str) -> str:
    运行根 = _取运行根目录(项目根)
    return os.path.join(运行根, "json", "歌曲记录索引.json")


def _兼容索引路径列表(项目根: str) -> List[str]:
    运行根 = _取运行根目录(项目根)
    资源根 = _取资源根目录(项目根)
    主路径 = _主索引路径(项目根)

    return _去重路径列表(
        [
            主路径,
            os.path.join(运行根, "songs", "歌曲记录索引.json"),
            os.path.join(str(项目根 or ""), "songs", "歌曲记录索引.json"),
            os.path.join(资源根, "songs", "歌曲记录索引.json"),
        ]
    )


def _读取json文件(路径: str):
    if (not 路径) or (not os.path.isfile(路径)):
        return None

    for 编码 in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(路径, "r", encoding=编码) as 文件:
                return json.load(文件)
        except Exception:
            continue
    return None


def _写入json文件(路径: str, 数据):
    try:
        os.makedirs(os.path.dirname(路径), exist_ok=True)
    except Exception:
        pass

    with open(路径, "w", encoding="utf-8") as 文件:
        json.dump(数据, 文件, ensure_ascii=False, indent=2)


def _索引路径(项目根: str) -> str:
    主路径 = _主索引路径(项目根)
    if os.path.isfile(主路径):
        return 主路径

    for 旧路径 in _兼容索引路径列表(项目根):
        if 旧路径 == 主路径:
            continue
        if os.path.isfile(旧路径):
            try:
                数据 = _读取json文件(旧路径)
                if isinstance(数据, dict):
                    _写入json文件(主路径, 数据)
                    return 主路径
            except Exception:
                continue

    return 主路径


def _提取歌曲相对路径(sm路径: str, 项目根: str) -> str:
    文本 = str(sm路径 or "").strip()
    if not 文本:
        return ""

    文本 = 文本.replace("\\", "/")

    if "/songs/" in 文本:
        return "songs/" + 文本.split("/songs/", 1)[1].lstrip("/")

    if 文本.startswith("songs/"):
        return 文本

    歌曲目录 = _取歌曲目录(项目根)
    规范sm路径 = _规范路径(sm路径)
    规范歌曲目录 = _规范路径(歌曲目录)

    if 规范sm路径 and 规范歌曲目录:
        try:
            相对路径 = os.path.relpath(规范sm路径, 规范歌曲目录).replace("\\", "/")
            if not 相对路径.startswith("../"):
                return "songs/" + 相对路径.lstrip("/")
        except Exception:
            pass

    文本 = 文本.lstrip("./").lstrip("/")
    if not 文本:
        return ""
    return "songs/" + 文本


def _歌曲键(sm路径: str, 项目根: str) -> str:
    return _提取歌曲相对路径(sm路径, 项目根)


def 取歌曲记录键(sm路径: str, 项目根: str) -> str:
    return _歌曲键(sm路径, 项目根)


def _规范歌曲记录项(项, 歌名: str = "", sm路径: str = "") -> dict:
    结果 = dict(项) if isinstance(项, dict) else {}

    try:
        结果["最高分"] = int(max(0, int(结果.get("最高分", 0) or 0)))
    except Exception:
        结果["最高分"] = 0

    try:
        结果["游玩次数"] = int(max(0, int(结果.get("游玩次数", 0) or 0)))
    except Exception:
        结果["游玩次数"] = 0

    if str(结果.get("歌名", "") or "") == "" and 歌名:
        结果["歌名"] = str(歌名 or "")

    if sm路径:
        结果["sm路径"] = str(sm路径 or "")
    elif str(结果.get("sm路径", "") or "") == "":
        结果["sm路径"] = ""

    return 结果


def _合并歌曲记录项(旧项: dict, 新项: dict, 项目根: str, 默认键: str = "") -> dict:
    旧项 = _规范歌曲记录项(
        旧项,
        歌名=str((旧项 or {}).get("歌名", "") or ""),
        sm路径=str((旧项 or {}).get("sm路径", "") or ""),
    )
    新项 = _规范歌曲记录项(
        新项,
        歌名=str((新项 or {}).get("歌名", "") or ""),
        sm路径=str((新项 or {}).get("sm路径", "") or ""),
    )

    try:
        最高分 = max(
            int(旧项.get("最高分", 0) or 0),
            int(新项.get("最高分", 0) or 0),
        )
    except Exception:
        最高分 = 0

    try:
        游玩次数 = int(max(0, int(旧项.get("游玩次数", 0) or 0))) + int(
            max(0, int(新项.get("游玩次数", 0) or 0))
        )
    except Exception:
        游玩次数 = int(max(0, int(旧项.get("游玩次数", 0) or 0)))

    歌名 = str(新项.get("歌名", "") or 旧项.get("歌名", "") or "")
    sm路径 = str(新项.get("sm路径", "") or 旧项.get("sm路径", "") or "")

    if (not sm路径) and 默认键:
        sm路径 = 默认键

    return {
        "最高分": int(max(0, 最高分)),
        "游玩次数": int(max(0, 游玩次数)),
        "歌名": 歌名,
        "sm路径": sm路径,
    }


def 读取歌曲记录索引(项目根: str) -> Dict[str, dict]:
    主路径 = _索引路径(项目根)
    数据 = _读取json文件(主路径)

    if not isinstance(数据, dict):
        for 候选路径 in _兼容索引路径列表(项目根):
            if 候选路径 == 主路径:
                continue
            数据 = _读取json文件(候选路径)
            if isinstance(数据, dict):
                break

    if not isinstance(数据, dict):
        return {}

    是否已修正 = False
    结果: Dict[str, dict] = {}

    for 原键, 原项 in 数据.items():
        项 = dict(原项) if isinstance(原项, dict) else {}
        原sm路径 = str(项.get("sm路径", "") or "").strip()
        候选sm路径 = 原sm路径 or str(原键 or "").strip()

        新键 = _歌曲键(候选sm路径, 项目根)
        if not 新键:
            新键 = str(原键 or "").replace("\\", "/")

        新项 = _规范歌曲记录项(
            项,
            歌名=str(项.get("歌名", "") or ""),
            sm路径=原sm路径 or 候选sm路径,
        )

        if str(原键 or "") != 新键:
            是否已修正 = True

        if 新键 in 结果:
            结果[新键] = _合并歌曲记录项(结果[新键], 新项, 项目根, 默认键=新键)
            是否已修正 = True
        else:
            结果[新键] = dict(新项)

    if 是否已修正:
        保存歌曲记录索引(项目根, 结果)

    return 结果


def 保存歌曲记录索引(项目根: str, 数据: Dict[str, dict]):
    结果: Dict[str, dict] = {}

    for 键, 项 in dict(数据 or {}).items():
        原项 = dict(项) if isinstance(项, dict) else {}
        原sm路径 = str(原项.get("sm路径", "") or "").strip()
        候选sm路径 = 原sm路径 or str(键 or "").strip()

        新键 = _歌曲键(候选sm路径, 项目根)
        if not 新键:
            新键 = str(键 or "").replace("\\", "/")

        新项 = _规范歌曲记录项(
            原项,
            歌名=str(原项.get("歌名", "") or ""),
            sm路径=原sm路径 or 候选sm路径,
        )

        if 新键 in 结果:
            结果[新键] = _合并歌曲记录项(结果[新键], 新项, 项目根, 默认键=新键)
        else:
            结果[新键] = dict(新项)

    主路径 = _主索引路径(项目根)
    _写入json文件(主路径, 结果)

    for 兼容路径 in _兼容索引路径列表(项目根):
        if 兼容路径 == 主路径:
            continue
        try:
            _写入json文件(兼容路径, 结果)
        except Exception:
            continue


def 取歌曲记录(项目根: str, sm路径: str, 歌名: str = "") -> dict:
    索引 = 读取歌曲记录索引(项目根)
    键 = _歌曲键(sm路径, 项目根)

    if not 键:
        return _规范歌曲记录项({}, 歌名=str(歌名 or ""), sm路径=str(sm路径 or ""))

    项 = 索引.get(键)
    if not isinstance(项, dict):
        项 = _规范歌曲记录项({}, 歌名=str(歌名 or ""), sm路径=str(sm路径 or ""))
        索引[键] = dict(项)
        保存歌曲记录索引(项目根, 索引)
    else:
        原项 = dict(项)
        项 = _规范歌曲记录项(项, 歌名=str(歌名 or ""), sm路径=str(sm路径 or ""))
        if 项 != 原项:
            索引[键] = dict(项)
            保存歌曲记录索引(项目根, 索引)

    return dict(项)


def 更新歌曲最高分(项目根: str, sm路径: str, 歌名: str, 分数: int) -> dict:
    索引 = 读取歌曲记录索引(项目根)
    键 = _歌曲键(sm路径, 项目根)

    if not 键:
        return {
            "是否新纪录": False,
            "最高分": int(max(0, int(分数 or 0))),
            "旧最高分": 0,
            "游玩次数": 1,
        }

    项 = 索引.get(键)
    if not isinstance(项, dict):
        项 = _规范歌曲记录项({}, 歌名=str(歌名 or ""), sm路径=str(sm路径 or ""))
    else:
        项 = _规范歌曲记录项(项, 歌名=str(歌名 or ""), sm路径=str(sm路径 or ""))

    try:
        旧最高分 = int(max(0, int(项.get("最高分", 0) or 0)))
    except Exception:
        旧最高分 = 0

    try:
        旧游玩次数 = int(max(0, int(项.get("游玩次数", 0) or 0)))
    except Exception:
        旧游玩次数 = 0

    新分数 = int(max(0, int(分数 or 0)))
    是否新纪录 = bool(新分数 > 旧最高分)

    项["游玩次数"] = int(旧游玩次数 + 1)
    项["歌名"] = str(歌名 or 项.get("歌名", "") or "")
    项["sm路径"] = str(sm路径 or 项.get("sm路径", "") or "")

    if 是否新纪录:
        项["最高分"] = 新分数

    索引[键] = dict(项)
    保存歌曲记录索引(项目根, 索引)

    return {
        "是否新纪录": 是否新纪录,
        "最高分": int(max(旧最高分, 新分数)),
        "旧最高分": int(旧最高分),
        "游玩次数": int(项.get("游玩次数", 0) or 0),
    }
