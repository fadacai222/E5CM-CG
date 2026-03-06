import os
import sys
import time
import json
import importlib
import inspect
import pygame

try:
    import cv2  # type: ignore
except Exception:
    cv2 = None

from core.常量与路径 import 默认资源路径
from core.工具 import 获取字体
from core.音频 import 音乐管理
from core.视频 import 全局视频循环播放器, 选择第一个视频
from scenes.场景_投币 import 场景_投币
from scenes.场景_玩家选择 import 场景_玩家选择
from scenes.场景_登陆磁卡 import 场景_登陆磁卡
from scenes.场景_个人资料 import 场景_个人资料
from scenes.场景_大模式 import 场景_大模式
from scenes.场景_子模式 import 场景_子模式
from scenes.场景_选歌 import 场景_选歌
from scenes.场景_加载页 import 场景_加载页
from scenes.场景_结算 import 场景_结算
from scenes.场景_谱面播放器 import 场景_谱面播放器

from ui.点击特效 import 序列帧特效资源, 全局点击特效管理器
from ui.场景过渡 import 公共黑屏过渡
from ui.布局调试器 import 所见即所得布局调试器


def _创建显示窗口(
    尺寸: tuple[int, int],
    flags: int,
) -> pygame.Surface:
    请求flags = int(flags | pygame.DOUBLEBUF)
    try:
        return pygame.display.set_mode(尺寸, 请求flags, vsync=1)
    except TypeError:
        try:
            return pygame.display.set_mode(尺寸, 请求flags)
        except Exception:
            return pygame.display.set_mode(尺寸, flags)
    except Exception:
        try:
            return pygame.display.set_mode(尺寸, 请求flags)
        except Exception:
            return pygame.display.set_mode(尺寸, flags)


def 主函数():
    def _安全进入场景(场景对象, 载荷):
        try:
            进入方法 = getattr(场景对象, "进入", None)
            if 进入方法 is None:
                return

            签名 = inspect.signature(进入方法)
            参数列表 = list(签名.parameters.values())

            有可变参数 = any(
                p.kind
                in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                for p in 参数列表
            )

            if 有可变参数:
                进入方法(载荷)
                return

            if len(参数列表) == 0:
                进入方法()
                return

            if len(参数列表) == 1 and 参数列表[0].name == "self":
                进入方法()
                return

            进入方法(载荷)
            return

        except TypeError as 异常:
            文本 = str(异常)
            if (
                ("positional argument" in 文本)
                or ("unexpected" in 文本)
                or ("takes" in 文本)
            ):
                getattr(场景对象, "进入")()
                return
            raise

    def _切换全屏():
        nonlocal 是否全屏, 上次窗口尺寸, 屏幕

        try:
            当前w, 当前h = 上下文["屏幕"].get_size()
        except Exception:
            当前w, 当前h = 1920, 1080

        if not 是否全屏:
            上次窗口尺寸 = (int(当前w), int(当前h))
            信息2 = pygame.display.Info()
            目标w = int(max(1, int(信息2.current_w or 当前w or 1920)))
            目标h = int(max(1, int(信息2.current_h or 当前h or 1080)))
            屏幕 = _创建显示窗口((目标w, 目标h), pygame.FULLSCREEN)
            是否全屏 = True
        else:
            恢复w, 恢复h = 上次窗口尺寸
            恢复w = int(max(960, int(恢复w)))
            恢复h = int(max(540, int(恢复h)))
            屏幕 = _创建显示窗口((恢复w, 恢复h), pygame.RESIZABLE)
            是否全屏 = False

        上下文["屏幕"] = 屏幕

    def _播放开场动画_cv2(视频路径: str):
        if (not 视频路径) or (not os.path.isfile(视频路径)):
            return
        if cv2 is None:
            return

        try:
            捕获 = cv2.VideoCapture(视频路径)
        except Exception:
            return

        if not 捕获 or (not 捕获.isOpened()):
            try:
                捕获.release()
            except Exception:
                pass
            return

        try:
            fps = 捕获.get(getattr(cv2, "CAP_PROP_FPS", 5))
            fps = float(fps) if fps and fps > 1 else 30.0
        except Exception:
            fps = 30.0

        每帧秒 = 1.0 / max(1.0, fps)
        上次帧系统秒 = time.perf_counter()

        while True:
            # 事件（必须处理，否则窗口会“未响应”）
            for 事件 in pygame.event.get():
                if 事件.type == pygame.QUIT:
                    try:
                        捕获.release()
                    except Exception:
                        pass
                    pygame.quit()
                    sys.exit(0)

                if 事件.type == pygame.KEYDOWN:
                    if 事件.key == pygame.K_ESCAPE:
                        try:
                            捕获.release()
                        except Exception:
                            pass
                        pygame.quit()
                        sys.exit(0)

                    if 事件.key == pygame.K_F11:
                        _切换全屏()

            现在 = time.perf_counter()
            if 现在 - 上次帧系统秒 < 每帧秒:
                time.sleep(0.001)
                continue
            上次帧系统秒 = 现在

            ok, 帧 = 捕获.read()
            if (not ok) or (帧 is None):
                break

            try:
                # BGR -> RGB
                帧 = cv2.cvtColor(帧, cv2.COLOR_BGR2RGB)
            except Exception:
                pass

            try:
                帧高, 帧宽 = 帧.shape[0], 帧.shape[1]
            except Exception:
                continue

            # 转成 pygame Surface（注意：surfarray 需要 numpy，opencv自带numpy一般没问题）
            try:
                帧面 = pygame.image.frombuffer(帧.tobytes(), (帧宽, 帧高), "RGB")
            except Exception:
                continue

            # 等比铺满屏幕（居中裁切/缩放：这里做 contain 缩放，避免裁掉内容）
            屏幕w, 屏幕h = 上下文["屏幕"].get_size()
            比例 = min(屏幕w / max(1, 帧宽), 屏幕h / max(1, 帧高))
            新宽 = max(1, int(帧宽 * 比例))
            新高 = max(1, int(帧高 * 比例))

            try:
                帧面缩放 = pygame.transform.smoothscale(帧面, (新宽, 新高))
            except Exception:
                帧面缩放 = 帧面

            x = (屏幕w - 新宽) // 2
            y = (屏幕h - 新高) // 2

            上下文["屏幕"].fill((0, 0, 0))
            上下文["屏幕"].blit(帧面缩放, (x, y))
            pygame.display.flip()

        try:
            捕获.release()
        except Exception:
            pass

    def _退出程序():
        音乐.停止()
        try:
            背景视频.关闭()
        except Exception:
            pass
        pygame.quit()
        sys.exit(0)

    pygame.init()
    pygame.display.set_caption("e舞成名 - 主流程（Pygame）")

    # ✅ 默认窗口分辨率：1920x1080（若屏幕更小则降级，避免 set_mode 失败）
    信息 = pygame.display.Info()

    # ✅ 启动默认小窗口（避免看起来像“开局全屏”）
    默认窗口w, 默认窗口h = 1280, 720
    初始w = min(默认窗口w, int(信息.current_w or 默认窗口w))
    初始h = min(默认窗口h, int(信息.current_h or 默认窗口h))
    屏幕 = _创建显示窗口((初始w, 初始h), pygame.RESIZABLE)

    时钟 = pygame.time.Clock()
    资源 = 默认资源路径()

    # ===== 上下文先建出来（给开场动画用）=====
    音乐 = 音乐管理()
    字体 = {
        "大字": 获取字体(72),
        "中字": 获取字体(36),
        "小字": 获取字体(22),
        "投币_credit字": 获取字体(28, 是否粗体=False),
        "投币_请投币字": 获取字体(48, 是否粗体=False),
    }

    状态 = {
        "玩家数": 1,
        "大模式": "",
        "子模式": "",
        "credit": "0",
        "投币数": 0,
        "投币快捷键": int(pygame.K_F1),
        "投币快捷键显示": "F1",
    }

    点击特效目录 = os.path.join(资源["根"], "UI-img", "点击特效")
    特效资源 = 序列帧特效资源(目录=点击特效目录, 扩展名=".png")
    特效ok = 特效资源.加载()
    全局点击特效 = 全局点击特效管理器(
        帧列表=特效资源.帧列表 if 特效ok else [],
        每秒帧数=60,
        缩放比例=1.0,
    )

    # ✅ 窗口状态
    是否全屏 = False
    上次窗口尺寸 = 屏幕.get_size()

    # ✅ 上下文
    上下文 = {
        "屏幕": 屏幕,
        "时钟": 时钟,
        "资源": 资源,
        "字体": 字体,
        "音乐": 音乐,
        "状态": 状态,
        "全局点击特效": 全局点击特效,
        "背景视频": None,
    }

    # ===== ✅ 1) 启动第一件事：播放开场动画（cv2）=====
    backmovies目录 = 资源.get(
        "backmovies目录", os.path.join(资源.get("根", os.getcwd()), "backmovies")
    )
    开场视频 = os.path.join(backmovies目录, "002.开场动画.mp4")
    _播放开场动画_cv2(开场视频)

    # ===== ✅ 2) 开场播完再初始化你的循环背景视频 =====
    强制视频 = os.path.join(backmovies目录, "003.mp4")
    if os.path.isfile(强制视频):
        视频路径 = 强制视频
    else:
        视频路径 = 选择第一个视频(backmovies目录)

    背景视频 = 全局视频循环播放器(视频路径)
    背景视频.打开(是否重置进度=True)
    上下文["背景视频"] = 背景视频

    场景表 = {
        "投币": 场景_投币,
        "玩家选择": 场景_玩家选择,
        "登陆磁卡": 场景_登陆磁卡,
        "个人资料": 场景_个人资料,
        "大模式": 场景_大模式,
        "子模式": 场景_子模式,
        "选歌": 场景_选歌,
        "加载页": 场景_加载页,
        "结算": 场景_结算,
        "谱面播放器": 场景_谱面播放器,
    }

    场景模块表 = {
        "投币": "scenes.场景_投币",
        "玩家选择": "scenes.场景_玩家选择",
        "登陆磁卡": "scenes.场景_登陆磁卡",
        "个人资料": "scenes.场景_个人资料",
        "大模式": "scenes.场景_大模式",
        "子模式": "scenes.场景_子模式",
        "选歌": "scenes.场景_选歌",
        "加载页": "scenes.场景_加载页",
        "结算": "scenes.场景_结算",
        "谱面播放器": "scenes.场景_谱面播放器",
    }

    当前场景名 = "投币"
    当前场景 = 场景表[当前场景名](上下文)
    _安全进入场景(当前场景, None)

    过渡 = 公共黑屏过渡(渐入秒=0.1, 渐出秒=0.1)
    待切换目标场景名 = None
    待切换载荷 = None

    布局保存文件 = os.path.join(
        str(资源.get("根", "") or os.getcwd()), "_debug", "layout_overrides.json"
    )
    布局调试器 = 所见即所得布局调试器(上下文, 保存路径=布局保存文件)
    布局调试器.绑定场景(当前场景)

    调试提示文本 = ""
    调试提示截止 = 0.0
    非游戏菜单开启 = False
    非游戏菜单索引 = 0
    非游戏菜单等待投币键 = False
    非游戏菜单项矩形: list[pygame.Rect] = []
    非游戏菜单关闭按钮 = pygame.Rect(0, 0, 0, 0)
    非游戏菜单背景音乐关闭 = False
    非游戏菜单背景音乐路径 = ""
    投币音效对象 = None
    try:
        投币音效路径 = str(资源.get("投币音效", "") or "")
        if 投币音效路径 and os.path.isfile(投币音效路径) and pygame.mixer.get_init():
            投币音效对象 = pygame.mixer.Sound(投币音效路径)
    except Exception:
        投币音效对象 = None

    投币快捷键 = int(pygame.K_F1)
    投币快捷键显示 = "F1"
    全局设置路径 = os.path.join(
        str(资源.get("根", "") or os.getcwd()), "json", "全局设置.json"
    )

    def _格式化按键名(键值: int) -> str:
        try:
            名 = str(pygame.key.name(int(键值)) or "").strip()
        except Exception:
            名 = ""
        if not 名:
            return f"KEY_{int(键值)}"
        return 名.upper()

    def _保存全局设置():
        try:
            os.makedirs(os.path.dirname(全局设置路径), exist_ok=True)
        except Exception:
            pass
        数据 = {
            "投币快捷键": int(投币快捷键),
            "投币快捷键显示": str(投币快捷键显示),
        }
        try:
            with open(全局设置路径, "w", encoding="utf-8") as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _加载全局设置():
        nonlocal 投币快捷键, 投币快捷键显示
        数据 = {}
        try:
            if os.path.isfile(全局设置路径):
                with open(全局设置路径, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                if isinstance(obj, dict):
                    数据 = obj
        except Exception:
            数据 = {}

        try:
            值 = int(数据.get("投币快捷键", pygame.K_F1))
            投币快捷键 = int(max(0, min(4096, 值)))
        except Exception:
            投币快捷键 = int(pygame.K_F1)
        投币快捷键显示 = _格式化按键名(int(投币快捷键))
        状态["投币快捷键"] = int(投币快捷键)
        状态["投币快捷键显示"] = str(投币快捷键显示)

    _加载全局设置()
    状态["非游戏菜单背景音乐关闭"] = bool(非游戏菜单背景音乐关闭)

    def _显示调试提示(文本: str, 秒: float = 1.2):
        nonlocal 调试提示文本, 调试提示截止
        调试提示文本 = 文本
        调试提示截止 = time.time() + float(秒)

    def _同步投币显示():
        try:
            投币数 = int(状态.get("投币数", 0) or 0)
        except Exception:
            投币数 = 0
        状态["credit"] = str(max(0, 投币数))

    def _选歌设置路径() -> str:
        try:
            根目录 = os.path.dirname(os.path.abspath(__file__))
        except Exception:
            根目录 = os.getcwd()
        return os.path.join(根目录, "json", "选歌设置.json")

    def _读取选歌设置() -> dict:
        路径 = _选歌设置路径()
        if not os.path.isfile(路径):
            return {}
        for 编码 in ("utf-8-sig", "utf-8", "gbk"):
            try:
                with open(路径, "r", encoding=编码, errors="strict") as f:
                    数据 = json.load(f)
                return dict(数据) if isinstance(数据, dict) else {}
            except Exception:
                continue
        return {}

    def _规范兜底击中特效方案(方案: str) -> str:
        文本 = str(方案 or "").strip()
        if ("2" in 文本) or ("特效2" in 文本):
            return "击中特效2"
        return "击中特效1"

    def _取兜底击中特效方案() -> str:
        数据 = _读取选歌设置()
        参数 = dict(数据.get("设置参数", {}) or {})
        return _规范兜底击中特效方案(
            str(
                数据.get(
                    "击中特效方案",
                    参数.get("击中特效", ""),
                )
                or ""
            )
        )

    def _写入选歌设置(数据: dict):
        路径 = _选歌设置路径()
        try:
            os.makedirs(os.path.dirname(路径), exist_ok=True)
            临时路径 = 路径 + ".tmp"
            with open(临时路径, "w", encoding="utf-8") as f:
                json.dump(dict(数据 or {}), f, ensure_ascii=False, indent=2)
            os.replace(临时路径, 路径)
        except Exception:
            pass

    def _切换兜底击中特效方案():
        数据 = _读取选歌设置()
        if not isinstance(数据, dict):
            数据 = {}
        参数 = dict(数据.get("设置参数", {}) or {})
        当前 = _规范兜底击中特效方案(
            str(数据.get("击中特效方案", 参数.get("击中特效", "")) or "")
        )
        新值 = "击中特效2" if 当前 == "击中特效1" else "击中特效1"
        参数["击中特效"] = str(新值)
        数据["设置参数"] = dict(参数)
        数据["击中特效方案"] = str(新值)

        背景文件名 = str(数据.get("背景文件名", "") or "")
        箭头文件名 = str(数据.get("箭头文件名", "") or "")
        try:
            from ui.选歌设置菜单控件 import 构建设置参数文本

            数据["设置参数文本"] = 构建设置参数文本(
                参数, 背景文件名=背景文件名, 箭头文件名=箭头文件名
            )
        except Exception:
            pass

        _写入选歌设置(数据)
        _显示调试提示(
            f"兜底击中特效已切换：{'特效2' if '2' in 新值 else '特效1'}", 1.1
        )

    def _全局投币一次():
        try:
            状态["投币数"] = int(状态.get("投币数", 0) or 0) + 1
        except Exception:
            状态["投币数"] = 1
        _同步投币显示()
        try:
            if 投币音效对象 is not None:
                投币音效对象.play()
        except Exception:
            pass
        try:
            当前币 = int(状态.get("投币数", 0) or 0)
        except Exception:
            当前币 = 0
        _显示调试提示(
            f"{str(状态.get('投币快捷键显示', 投币快捷键显示))}投币 +1  当前:{max(0, 当前币)}/3",
            0.8,
        )

    def _取非游戏菜单项() -> list[str]:
        菜单项 = [
            f"设置投币快捷键（当前：{str(状态.get('投币快捷键显示', 投币快捷键显示))}）",
            "开启背景音乐" if bool(非游戏菜单背景音乐关闭) else "关闭背景音乐",
        ]
        if str(当前场景名 or "") == "选歌":
            当前方案 = _取兜底击中特效方案()
            菜单项.append(f"兜底击中特效（{'特效2' if '2' in 当前方案 else '特效1'}）")
        菜单项.append("退出到桌面")
        return 菜单项

    def _切换非游戏背景音乐():
        nonlocal 非游戏菜单背景音乐关闭, 非游戏菜单背景音乐路径, 当前场景名
        if not bool(非游戏菜单背景音乐关闭):
            try:
                当前路径 = str(getattr(音乐, "当前路径", "") or "")
            except Exception:
                当前路径 = ""
            if 当前路径 and os.path.isfile(当前路径):
                非游戏菜单背景音乐路径 = 当前路径
            try:
                音乐.停止()
            except Exception:
                pass
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception:
                pass
            非游戏菜单背景音乐关闭 = True
            状态["非游戏菜单背景音乐关闭"] = True
            _显示调试提示("背景音乐已关闭", 1.0)
            return

        恢复路径 = str(非游戏菜单背景音乐路径 or "").strip()
        if (not 恢复路径) or (not os.path.isfile(恢复路径)):
            恢复路径 = str(资源.get("音乐_UI", "") or "").strip()
        if (
            恢复路径
            and os.path.isfile(恢复路径)
            and (str(当前场景名 or "") != "选歌")
        ):
            try:
                音乐.播放循环(恢复路径)
            except Exception:
                pass
        非游戏菜单背景音乐关闭 = False
        状态["非游戏菜单背景音乐关闭"] = False
        _显示调试提示("背景音乐已开启", 1.0)

    def _执行非游戏菜单选项(索引: int):
        nonlocal 非游戏菜单等待投币键
        菜单项 = _取非游戏菜单项()
        if not 菜单项:
            return
        索引 = int(max(0, min(len(菜单项) - 1, int(索引))))
        选项 = 菜单项[索引]
        if "设置投币快捷键" in 选项:
            非游戏菜单等待投币键 = True
            _显示调试提示("请按任意键设置为投币快捷键（ESC取消）", 2.0)
            return
        if "背景音乐" in 选项:
            _切换非游戏背景音乐()
            return
        if "兜底击中特效" in 选项:
            _切换兜底击中特效方案()
            return
        if 选项 == "退出到桌面":
            _退出程序()
            return

    def _绘制非游戏菜单():
        nonlocal 非游戏菜单项矩形, 非游戏菜单关闭按钮
        非游戏菜单项矩形 = []
        非游戏菜单关闭按钮 = pygame.Rect(0, 0, 0, 0)
        if not 非游戏菜单开启:
            return
        try:
            屏幕面 = 上下文["屏幕"]
            w, h = 屏幕面.get_size()
            遮罩 = pygame.Surface((w, h), pygame.SRCALPHA)
            遮罩.fill((0, 0, 0, 165))
            屏幕面.blit(遮罩, (0, 0))

            面板w = max(620, int(w * 0.56))
            面板h = max(250, int(h * 0.34))
            面板 = pygame.Rect((w - 面板w) // 2, (h - 面板h) // 2, 面板w, 面板h)
            pygame.draw.rect(屏幕面, (18, 22, 35), 面板, border_radius=18)
            pygame.draw.rect(屏幕面, (140, 170, 235), 面板, width=2, border_radius=18)

            标题字 = 上下文["字体"]["中字"]
            小字 = 上下文["字体"]["小字"]
            标题面 = 标题字.render("系统菜单", True, (245, 248, 255))
            屏幕面.blit(标题面, (面板.x + 24, 面板.y + 16))
            非游戏菜单关闭按钮 = pygame.Rect(int(面板.right - 46), int(面板.y + 14), 30, 30)
            pygame.draw.rect(屏幕面, (58, 68, 96), 非游戏菜单关闭按钮, border_radius=8)
            pygame.draw.rect(
                屏幕面, (180, 200, 236), 非游戏菜单关闭按钮, width=1, border_radius=8
            )
            关字符 = 标题字.render("×", True, (240, 246, 255))
            屏幕面.blit(关字符, 关字符.get_rect(center=非游戏菜单关闭按钮.center).topleft)

            提示行 = [
                f"{str(状态.get('投币快捷键显示', 投币快捷键显示))}投币",
                "小键盘1/3左右选，5确认（提示）",
                "鼠标点击选项，右上角×关闭",
                "游戏中小键盘1/3/5/7/9控制踏板",
            ]
            y = 面板.y + 68
            for 文本 in 提示行:
                行面 = 小字.render(文本, True, (208, 220, 255))
                屏幕面.blit(行面, (面板.x + 24, y))
                y += 行面.get_height() + 4

            菜单项 = _取非游戏菜单项()
            选项起y = y + 10
            for idx, 名称 in enumerate(菜单项):
                选中 = idx == int(非游戏菜单索引)
                颜色 = (255, 235, 120) if 选中 else (220, 228, 245)
                前缀 = "▶ " if 选中 else "   "
                项面 = 小字.render(f"{前缀}{名称}", True, 颜色)
                行rect = pygame.Rect(
                    int(面板.x + 18),
                    int(选项起y + idx * (项面.get_height() + 12) - 4),
                    int(max(220, 项面.get_width() + 20)),
                    int(项面.get_height() + 8),
                )
                if 选中:
                    pygame.draw.rect(屏幕面, (42, 58, 90), 行rect, border_radius=8)
                屏幕面.blit(项面, (int(行rect.x + 8), int(行rect.y + 4)))
                非游戏菜单项矩形.append(行rect)
            if bool(非游戏菜单等待投币键):
                提示 = "等待按键输入：按任意键设为投币键（ESC取消）"
                提示面 = 小字.render(提示, True, (255, 240, 140))
                屏幕面.blit(提示面, (面板.x + 24, int(面板.bottom - 提示面.get_height() - 18)))
        except Exception:
            pass

    def _处理非游戏菜单按键(事件) -> bool:
        nonlocal 非游戏菜单开启, 非游戏菜单索引
        nonlocal 非游戏菜单等待投币键, 投币快捷键, 投币快捷键显示
        if not 非游戏菜单开启:
            return False
        菜单项 = _取非游戏菜单项()

        if bool(非游戏菜单等待投币键):
            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    非游戏菜单等待投币键 = False
                    _显示调试提示("已取消修改投币快捷键", 1.0)
                    return True
                投币快捷键 = int(max(0, min(4096, int(事件.key))))
                投币快捷键显示 = _格式化按键名(int(投币快捷键))
                状态["投币快捷键"] = int(投币快捷键)
                状态["投币快捷键显示"] = str(投币快捷键显示)
                _保存全局设置()
                非游戏菜单等待投币键 = False
                _显示调试提示(f"投币快捷键已改为：{投币快捷键显示}", 1.2)
                return True
            return True

        if 事件.type == pygame.KEYDOWN:
            if 事件.key == pygame.K_ESCAPE:
                非游戏菜单开启 = False
                非游戏菜单等待投币键 = False
                return True
            if 事件.key in (pygame.K_LEFT, pygame.K_KP1, pygame.K_UP, pygame.K_KP7):
                非游戏菜单索引 = (int(非游戏菜单索引) - 1) % len(菜单项)
                return True
            if 事件.key in (
                pygame.K_RIGHT,
                pygame.K_KP3,
                pygame.K_DOWN,
                pygame.K_KP9,
            ):
                非游戏菜单索引 = (int(非游戏菜单索引) + 1) % len(菜单项)
                return True
            if 事件.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_KP5):
                _执行非游戏菜单选项(int(非游戏菜单索引))
                return True
            return True

        if 事件.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(非游戏菜单项矩形):
                if rect.collidepoint(事件.pos):
                    非游戏菜单索引 = int(idx)
                    break
            return True

        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            if 非游戏菜单关闭按钮.collidepoint(事件.pos):
                非游戏菜单开启 = False
                return True
            for idx, rect in enumerate(非游戏菜单项矩形):
                if rect.collidepoint(事件.pos):
                    非游戏菜单索引 = int(idx)
                    _执行非游戏菜单选项(int(idx))
                    return True
            return True
        return True

    def _执行场景切换():
        nonlocal 当前场景名, 当前场景, 待切换目标场景名, 待切换载荷
        nonlocal 非游戏菜单开启, 非游戏菜单索引, 非游戏菜单等待投币键
        目标 = 待切换目标场景名
        载荷 = 待切换载荷
        if not 目标 or (目标 not in 场景表):
            return

        try:
            当前场景.退出()
        except Exception:
            pass

        当前场景名 = 目标
        当前场景 = 场景表[当前场景名](上下文)
        _安全进入场景(当前场景, 载荷)

        待切换目标场景名 = None
        待切换载荷 = None
        布局调试器.绑定场景(当前场景)
        非游戏菜单开启 = False
        非游戏菜单索引 = 0
        非游戏菜单等待投币键 = False

    def _当前场景允许非游戏菜单() -> bool:
        return bool(当前场景名 not in ("谱面播放器", "结算"))

    def _热更新当前场景():
        nonlocal 当前场景, 当前场景名, 场景表
        try:
            模块名 = 场景模块表.get(当前场景名)
            if not 模块名:
                _显示调试提示(f"F5 失败：未知场景 {当前场景名}", 1.8)
                return

            类名 = 当前场景.__class__.__name__
            importlib.invalidate_caches()

            模块对象 = sys.modules.get(模块名)
            if 模块对象 is None:
                模块对象 = importlib.import_module(模块名)

            新模块 = importlib.reload(模块对象)
            新类 = getattr(新模块, 类名, None)

            if 新类 is None:
                新类候选 = None
                for v in 新模块.__dict__.values():
                    try:
                        if (
                            isinstance(v, type)
                            and getattr(v, "名称", None) == 当前场景名
                        ):
                            新类候选 = v
                            break
                    except Exception:
                        pass
                新类 = 新类候选

            if 新类 is None:
                _显示调试提示(f"F5 失败：模块{模块名}里找不到类 {类名}", 2.0)
                return

            try:
                当前场景.退出()
            except Exception:
                pass

            场景表[当前场景名] = 新类
            当前场景 = 新类(上下文)
            _安全进入场景(当前场景, None)

            布局调试器.绑定场景(当前场景)
            _显示调试提示(f"F5 热重载成功：{当前场景名}", 1.2)

        except Exception as e:
            try:
                print("F5 热重载失败：", repr(e))
            except Exception:
                pass
            _显示调试提示(f"F5 热重载失败：{type(e).__name__}", 2.0)

    def _获取当前目标帧率() -> int:
        try:
            值 = int(getattr(当前场景, "目标帧率", 60) or 60)
        except Exception:
            值 = 60
        return max(30, min(240, 值))

    while True:
        时钟.tick(_获取当前目标帧率())

        for 事件 in pygame.event.get():
            if 事件.type == pygame.QUIT:
                _退出程序()

            if (
                事件.type == pygame.KEYDOWN
                and int(事件.key) == int(投币快捷键)
                and (not bool(非游戏菜单等待投币键))
            ):
                _全局投币一次()
                if (not 过渡.是否进行中()) and 当前场景名 == "投币":
                    try:
                        当前币 = int(状态.get("投币数", 0) or 0)
                    except Exception:
                        当前币 = 0
                    if 当前币 >= 3:
                        待切换目标场景名 = "玩家选择"
                        待切换载荷 = None
                        _执行场景切换()
                    else:
                        _显示调试提示(f"还需 {max(0, 3 - 当前币)} 币（3币开局）", 0.9)
                continue

            # ✅ F11 全屏切换（全局）
            if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F11:
                if not 过渡.是否进行中():
                    _切换全屏()
                continue

            if 事件.type == pygame.VIDEORESIZE and (not 是否全屏):
                新w = int(max(960, int(getattr(事件, "w", 0) or 0)))
                新h = int(max(540, int(getattr(事件, "h", 0) or 0)))
                屏幕 = _创建显示窗口((新w, 新h), pygame.RESIZABLE)
                上下文["屏幕"] = 屏幕
                # ✅ 记录窗口尺寸，退出全屏时回到这里
                上次窗口尺寸 = 屏幕.get_size()

            if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F6:
                if not 过渡.是否进行中():
                    布局调试器.切换开关()
                continue

            if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F5:
                if not 过渡.是否进行中():
                    _热更新当前场景()
                continue

            if 布局调试器.是否开启:
                是否吃掉 = 布局调试器.处理事件(事件)
                if 是否吃掉:
                    continue

            if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
                x, y = 事件.pos
                全局点击特效.触发(x, y)

            if 过渡.是否进行中():
                continue

            if _当前场景允许非游戏菜单():
                if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
                    非游戏菜单开启 = not bool(非游戏菜单开启)
                    非游戏菜单索引 = 0
                    状态["非游戏菜单背景音乐关闭"] = bool(非游戏菜单背景音乐关闭)
                    continue
                if _处理非游戏菜单按键(事件):
                    continue
            else:
                if 非游戏菜单开启:
                    非游戏菜单开启 = False
                    非游戏菜单索引 = 0
                    非游戏菜单等待投币键 = False

            结果 = 当前场景.处理事件(事件)

            目标 = None
            载荷 = None
            if isinstance(结果, dict):
                if bool(结果.get("退出程序", False)):
                    _退出程序()
                目标 = 结果.get("切换到")
                载荷 = 结果.get("载荷")

            if 目标 and (目标 in 场景表):
                禁用黑屏 = (
                    bool(结果.get("禁用黑屏过渡", False))
                    if isinstance(结果, dict)
                    else False
                )
                待切换目标场景名 = 目标
                待切换载荷 = 载荷

                if 禁用黑屏:
                    _执行场景切换()
                else:
                    过渡.开始(目标)

        if (not 过渡.是否进行中()) and hasattr(当前场景, "更新"):
            try:
                更新结果 = 当前场景.更新()
            except Exception:
                更新结果 = None

            目标 = None
            载荷 = None
            if isinstance(更新结果, dict):
                if bool(更新结果.get("退出程序", False)):
                    _退出程序()
                目标 = 更新结果.get("切换到")
                载荷 = 更新结果.get("载荷")

            if 目标 and (目标 in 场景表):
                禁用黑屏 = (
                    bool(更新结果.get("禁用黑屏过渡", False))
                    if isinstance(更新结果, dict)
                    else False
                )
                待切换目标场景名 = 目标
                待切换载荷 = 载荷

                if 禁用黑屏:
                    _执行场景切换()
                else:
                    过渡.开始(目标)

        过渡.更新(_执行场景切换)

        当前场景.绘制()
        _绘制非游戏菜单()
        全局点击特效.更新并绘制(上下文["屏幕"])
        布局调试器.更新并绘制(上下文["屏幕"])

        if 调试提示文本 and time.time() < 调试提示截止:
            try:
                小字 = 上下文["字体"]["小字"]
                文面 = 小字.render(调试提示文本, True, (255, 220, 120))
                文r = 文面.get_rect()
                w, _h = 上下文["屏幕"].get_size()
                文r.topright = (w - 12, 44)
                上下文["屏幕"].blit(文面, 文r.topleft)
            except Exception:
                pass

        过渡.绘制(上下文["屏幕"])
        pygame.display.flip()


if __name__ == "__main__":
    主函数()
