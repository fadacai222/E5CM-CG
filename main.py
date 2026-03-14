import os
import sys
import time
import json
import inspect
import webbrowser
import pygame
from typing import Optional

try:
    import cv2
except Exception:
    cv2 = None

from core.常量与路径 import 默认资源路径, 取运行根目录
from core.对局状态 import 取每局所需信用
from core.渲染后端 import 创建显示后端, 取桌面尺寸
from core.踏板控制 import 解析踏板动作
from core.工具 import 获取字体
from core.音频 import 音乐管理
from core.视频 import 全局视频循环播放器, 选择第一个视频
from core.软件版本 import 规范版本比较值, 规范版本号, 读取当前版本号
from scenes.场景_投币 import 场景_投币
from scenes.场景_登陆磁卡 import 场景_登陆磁卡
from scenes.场景_个人资料 import 场景_个人资料
from scenes.场景_大模式 import 场景_大模式
from scenes.场景_子模式 import 场景_子模式
from scenes.场景_选歌 import 场景_选歌
from scenes.场景_加载页 import 场景_加载页
from scenes.场景_结算 import 场景_结算
from scenes.场景_谱面播放器 import 场景_谱面播放器
from ui.点击特效 import 序列帧特效资源, 全局点击特效管理器
from ui.场景过渡 import 公共黑屏过渡,公共丝滑入场
from ui.select_scene_esc_menu_host import SelectSceneEscMenuHost


更新接口地址 = "https://e5cg.vip/api/update"


def _songs目录含有曲包(songs根目录: str) -> bool:
    路径 = os.path.abspath(str(songs根目录 or "").strip()) if str(songs根目录 or "").strip() else ""
    if not 路径 or (not os.path.isdir(路径)):
        return False

    目标扩展名 = {".sm", ".ssc", ".dwi", ".json"}
    try:
        for 根目录, _子目录, 文件列表 in os.walk(路径):
            for 文件名 in 文件列表:
                _, 扩展名 = os.path.splitext(str(文件名 or ""))
                if str(扩展名 or "").lower() in 目标扩展名:
                    return True
    except Exception:
        return False
    return False


def _弹窗提示缺少曲包(songs根目录: str):
    路径 = os.path.abspath(str(songs根目录 or "").strip()) if str(songs根目录 or "").strip() else ""
    if 路径:
        try:
            os.makedirs(路径, exist_ok=True)
        except Exception:
            pass

    标题 = "缺少曲包"
    正文 = "检测到您没有曲包，请下载曲包并解压，覆盖到软件根目录songs文件夹。"
    操作步骤 = [
        "1. 下载所有part的曲包",
        "2. 解压第一个压缩包，会获得全部的歌曲文件",
        "3. 打开songs文件夹",
        "4. 把曲包拖进去",
        "5. 重启软件",
    ]

    try:
        import tkinter as tk
    except Exception:
        tk = None

    if tk is None:
        print(正文)
        print("下载曲包：https://e5cg.vip")
        for 文本 in 操作步骤:
            print(文本)
        return

    try:
        根窗 = tk.Tk()
        根窗.withdraw()

        弹窗 = tk.Toplevel(根窗)
        弹窗.title(标题)
        弹窗.resizable(False, False)
        弹窗.attributes("-topmost", True)
        弹窗.configure(bg="#0f1726")
        弹窗.protocol("WM_DELETE_WINDOW", 弹窗.destroy)

        外框 = tk.Frame(弹窗, bg="#0f1726", padx=18, pady=16)
        外框.pack(fill="both", expand=True)

        tk.Label(
            外框,
            text=正文,
            justify="left",
            anchor="w",
            fg="#f3f7ff",
            bg="#0f1726",
            font=("Microsoft YaHei UI", 12, "bold"),
            wraplength=520,
        ).pack(fill="x")

        if 路径:
            tk.Label(
                外框,
                text=f"songs文件夹：{路径}",
                justify="left",
                anchor="w",
                fg="#9fb4d9",
                bg="#0f1726",
                font=("Microsoft YaHei UI", 10),
                wraplength=520,
            ).pack(fill="x", pady=(8, 0))

        tk.Label(
            外框,
            text="操作提示：",
            justify="left",
            anchor="w",
            fg="#ffe066",
            bg="#0f1726",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(fill="x", pady=(14, 6))

        for 文本 in 操作步骤:
            tk.Label(
                外框,
                text=文本,
                justify="left",
                anchor="w",
                fg="#d7e2f5",
                bg="#0f1726",
                font=("Microsoft YaHei UI", 10),
                wraplength=520,
            ).pack(fill="x", pady=1)

        按钮区 = tk.Frame(外框, bg="#0f1726")
        按钮区.pack(fill="x", pady=(16, 0))

        def _下载曲包():
            try:
                webbrowser.open("https://e5cg.vip")
            except Exception:
                pass

        tk.Button(
            按钮区,
            text="1.下载曲包，https://e5cg.vip",
            command=_下载曲包,
            padx=14,
            pady=8,
            bg="#1d6cff",
            fg="#ffffff",
            activebackground="#2a7fff",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(side="left")

        tk.Button(
            按钮区,
            text="关闭",
            command=弹窗.destroy,
            padx=14,
            pady=8,
            bg="#243248",
            fg="#f3f7ff",
            activebackground="#30415d",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10),
        ).pack(side="right")

        弹窗.update_idletasks()
        宽 = int(弹窗.winfo_width() or 560)
        高 = int(弹窗.winfo_height() or 320)
        屏宽 = int(弹窗.winfo_screenwidth() or 宽)
        屏高 = int(弹窗.winfo_screenheight() or 高)
        x = max(0, (屏宽 - 宽) // 2)
        y = max(0, (屏高 - 高) // 2)
        弹窗.geometry(f"{宽}x{高}+{x}+{y}")
        弹窗.deiconify()
        弹窗.grab_set()
        弹窗.focus_force()
        根窗.wait_window(弹窗)
        根窗.destroy()
    except Exception:
        try:
            根窗.destroy()
        except Exception:
            pass
        print(正文)
        print("下载曲包：https://e5cg.vip")
        for 文本 in 操作步骤:
            print(文本)


def _格式化字节大小(字节数: object) -> str:
    try:
        值 = float(字节数 or 0)
    except Exception:
        值 = 0.0

    单位列表 = ["B", "KB", "MB", "GB"]
    单位索引 = 0
    while 值 >= 1024.0 and 单位索引 < len(单位列表) - 1:
        值 /= 1024.0
        单位索引 += 1

    if 单位索引 == 0:
        return f"{int(值)}{单位列表[单位索引]}"
    return f"{值:.1f}{单位列表[单位索引]}"


def _清理下载文件名(文本: object) -> str:
    值 = str(文本 or "").strip()
    if not 值:
        return ""

    非法字符 = '<>:"/\\|?*'
    return "".join("_" if ch in 非法字符 else ch for ch in 值).strip(" .")


def _启动安装包(安装包路径: str):
    路径 = os.path.abspath(str(安装包路径 or "").strip())
    if not 路径 or (not os.path.isfile(路径)):
        raise FileNotFoundError(f"未找到安装包：{路径}")

    if sys.platform == "win32" and hasattr(os, "startfile"):
        os.startfile(路径)
        return

    import subprocess

    subprocess.Popen([路径])


def _后台检查软件更新(当前版本号: str, 结果容器: dict):
    import urllib.request

    请求 = urllib.request.Request(
        更新接口地址,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": f"E5CM-CG/{规范版本号(当前版本号, 默认值='unknown')}",
        },
    )

    try:
        with urllib.request.urlopen(请求, timeout=5) as 响应:
            编码 = 响应.headers.get_content_charset() or "utf-8"
            文本 = 响应.read().decode(编码, errors="ignore")

        对象 = json.loads(文本)
        if not isinstance(对象, dict):
            raise ValueError("更新接口返回的不是 JSON 对象")

        更新信息 = {
            "version": str(对象.get("version", "") or "").strip(),
            "versionLabel": str(对象.get("versionLabel", "") or "").strip(),
            "downloadUrl": str(对象.get("downloadUrl", "") or "").strip(),
            "updateContent": str(对象.get("updateContent", "") or "").strip(),
            "publishedAt": str(对象.get("publishedAt", "") or "").strip(),
        }
        远端版本号 = str(更新信息.get("version", "") or "").strip()

        结果容器["查询成功"] = True
        结果容器["错误"] = ""
        结果容器["数据"] = 更新信息
        结果容器["发现新版本"] = bool(
            远端版本号
            and 规范版本比较值(远端版本号) != 规范版本比较值(当前版本号)
        )
    except Exception as 异常:
        结果容器["查询成功"] = False
        结果容器["错误"] = str(异常 or "")
        结果容器["数据"] = None
        结果容器["发现新版本"] = False
    finally:
        结果容器["已完成"] = True


def _弹窗下载新版安装包(更新信息: dict, 父窗体=None) -> bool:
    下载链接 = str(更新信息.get("downloadUrl", "") or "").strip()
    if not 下载链接:
        return False

    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        return False

    根窗 = None
    自建根窗 = 父窗体 is None
    状态 = {
        "已完成": False,
        "成功": False,
        "取消": False,
        "已下载字节": 0,
        "总字节": 0,
        "错误": "",
        "保存路径": "",
        "已启动安装器": False,
    }
    已处理完成 = {"值": False}
    进度条已启动 = {"值": False}

    try:
        if 自建根窗:
            根窗 = tk.Tk()
            根窗.withdraw()
        else:
            根窗 = 父窗体

        弹窗 = tk.Toplevel(根窗)
        弹窗.title("下载更新")
        弹窗.resizable(False, False)
        弹窗.attributes("-topmost", True)
        弹窗.configure(bg="#0f1726")

        外框 = tk.Frame(弹窗, bg="#0f1726", padx=18, pady=16)
        外框.pack(fill="both", expand=True)

        标题变量 = tk.StringVar(value="正在准备下载更新包...")
        详情变量 = tk.StringVar(value=str(下载链接))

        tk.Label(
            外框,
            textvariable=标题变量,
            justify="left",
            anchor="w",
            fg="#f3f7ff",
            bg="#0f1726",
            font=("Microsoft YaHei UI", 12, "bold"),
            wraplength=520,
        ).pack(fill="x")

        tk.Label(
            外框,
            textvariable=详情变量,
            justify="left",
            anchor="w",
            fg="#9fb4d9",
            bg="#0f1726",
            font=("Microsoft YaHei UI", 10),
            wraplength=520,
        ).pack(fill="x", pady=(8, 12))

        进度条 = ttk.Progressbar(外框, orient="horizontal", length=520, mode="determinate")
        进度条.pack(fill="x")

        按钮区 = tk.Frame(外框, bg="#0f1726")
        按钮区.pack(fill="x", pady=(16, 0))

        def _关闭或取消():
            if bool(状态.get("已完成", False)):
                弹窗.destroy()
                return
            状态["取消"] = True
            标题变量.set("正在取消下载...")

        取消按钮 = tk.Button(
            按钮区,
            text="取消",
            command=_关闭或取消,
            padx=14,
            pady=8,
            bg="#243248",
            fg="#f3f7ff",
            activebackground="#30415d",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10),
        )
        取消按钮.pack(side="right")
        弹窗.protocol("WM_DELETE_WINDOW", _关闭或取消)

        def _下载线程():
            import tempfile
            import urllib.parse
            import urllib.request

            目标路径 = ""
            临时路径 = ""

            try:
                下载目录 = os.path.join(tempfile.gettempdir(), "E5CM-CG_Update")
                os.makedirs(下载目录, exist_ok=True)

                解析结果 = urllib.parse.urlparse(下载链接)
                文件名 = os.path.basename(urllib.parse.unquote(解析结果.path or ""))
                文件名 = _清理下载文件名(文件名)
                if not 文件名:
                    安全版本号 = _清理下载文件名(
                        str(更新信息.get("version", "") or "")
                    ) or str(int(time.time()))
                    文件名 = f"E5CM-CG_Setup_{安全版本号}.exe"
                if not 文件名.lower().endswith(".exe"):
                    文件名 += ".exe"

                目标路径 = os.path.join(下载目录, 文件名)
                临时路径 = 目标路径 + ".part"
                状态["保存路径"] = 目标路径
                状态["已下载字节"] = 0

                请求 = urllib.request.Request(
                    下载链接,
                    method="GET",
                    headers={"User-Agent": "E5CM-CG-Updater"},
                )

                with urllib.request.urlopen(请求, timeout=15) as 响应:
                    try:
                        状态["总字节"] = max(
                            0,
                            int(响应.headers.get("Content-Length", "0") or 0),
                        )
                    except Exception:
                        状态["总字节"] = 0

                    with open(临时路径, "wb") as 文件:
                        while True:
                            if bool(状态.get("取消", False)):
                                raise RuntimeError("下载已取消")

                            数据块 = 响应.read(262144)
                            if not 数据块:
                                break

                            文件.write(数据块)
                            状态["已下载字节"] = int(
                                状态.get("已下载字节", 0) or 0
                            ) + len(数据块)

                if bool(状态.get("取消", False)):
                    raise RuntimeError("下载已取消")

                if os.path.isfile(目标路径):
                    try:
                        os.remove(目标路径)
                    except Exception:
                        pass
                os.replace(临时路径, 目标路径)
                状态["成功"] = True
            except Exception as 异常:
                状态["错误"] = str(异常 or "下载失败")
                for 路径 in (临时路径, 目标路径):
                    if 路径 and os.path.isfile(路径):
                        try:
                            os.remove(路径)
                        except Exception:
                            pass
            finally:
                状态["已完成"] = True

        def _刷新进度():
            已下载字节 = int(状态.get("已下载字节", 0) or 0)
            总字节 = int(状态.get("总字节", 0) or 0)

            if not bool(状态.get("已完成", False)):
                if 总字节 > 0:
                    if bool(进度条已启动.get("值", False)):
                        try:
                            进度条.stop()
                        except Exception:
                            pass
                        进度条已启动["值"] = False
                    进度条.configure(mode="determinate", maximum=max(1, 总字节))
                    进度条["value"] = min(已下载字节, 总字节)
                    百分比 = min(100.0, 已下载字节 * 100.0 / max(1, 总字节))
                    标题变量.set(f"正在下载更新包... {百分比:.1f}%")
                    详情变量.set(
                        f"{_格式化字节大小(已下载字节)} / {_格式化字节大小(总字节)}"
                    )
                else:
                    if not bool(进度条已启动.get("值", False)):
                        进度条.configure(mode="indeterminate")
                        进度条.start(12)
                        进度条已启动["值"] = True
                    标题变量.set("正在下载更新包...")
                    详情变量.set(f"已下载 {_格式化字节大小(已下载字节)}")

                弹窗.after(120, _刷新进度)
                return

            if bool(进度条已启动.get("值", False)):
                try:
                    进度条.stop()
                except Exception:
                    pass
                进度条已启动["值"] = False

            if bool(已处理完成.get("值", False)):
                return
            已处理完成["值"] = True

            if bool(状态.get("成功", False)):
                标题变量.set("下载完成，正在启动安装包...")
                详情变量.set(str(状态.get("保存路径", "") or ""))
                取消按钮.configure(state="disabled")
                try:
                    _启动安装包(str(状态.get("保存路径", "") or ""))
                    状态["已启动安装器"] = True
                    弹窗.after(180, 弹窗.destroy)
                except Exception as 异常:
                    标题变量.set("安装包启动失败")
                    详情变量.set(str(异常 or ""))
                    取消按钮.configure(state="normal", text="关闭")
                return

            if bool(状态.get("取消", False)):
                标题变量.set("下载已取消")
            else:
                标题变量.set("下载失败")
            详情变量.set(str(状态.get("错误", "") or ""))
            取消按钮.configure(state="normal", text="关闭")

        import threading

        下载线程 = threading.Thread(
            target=_下载线程,
            name="E5CM-CG-UpdateDownload",
            daemon=True,
        )
        下载线程.start()

        弹窗.update_idletasks()
        宽 = int(弹窗.winfo_width() or 560)
        高 = int(弹窗.winfo_height() or 220)
        屏宽 = int(弹窗.winfo_screenwidth() or 宽)
        屏高 = int(弹窗.winfo_screenheight() or 高)
        x = max(0, (屏宽 - 宽) // 2)
        y = max(0, (屏高 - 高) // 2)
        弹窗.geometry(f"{宽}x{高}+{x}+{y}")
        弹窗.deiconify()
        弹窗.grab_set()
        弹窗.focus_force()

        弹窗.after(120, _刷新进度)
        根窗.wait_window(弹窗)
        return bool(状态.get("已启动安装器", False))
    finally:
        if 自建根窗 and 根窗 is not None:
            try:
                根窗.destroy()
            except Exception:
                pass


def _弹窗提示软件更新(当前版本号: str, 更新信息: dict) -> bool:
    远端版本号 = str(更新信息.get("version", "") or "").strip()
    if not 远端版本号:
        return False

    try:
        import tkinter as tk
    except Exception:
        return False

    根窗 = None
    结果 = {"已启动安装器": False}

    try:
        根窗 = tk.Tk()
        根窗.withdraw()

        弹窗 = tk.Toplevel(根窗)
        弹窗.title("发现新版本")
        弹窗.resizable(False, False)
        弹窗.attributes("-topmost", True)
        弹窗.configure(bg="#0f1726")
        弹窗.protocol("WM_DELETE_WINDOW", 弹窗.destroy)

        外框 = tk.Frame(弹窗, bg="#0f1726", padx=18, pady=16)
        外框.pack(fill="both", expand=True)

        版本提示 = str(更新信息.get("versionLabel", "") or "").strip()
        更新内容 = str(更新信息.get("updateContent", "") or "").strip() or "暂无更新说明"
        下载链接 = str(更新信息.get("downloadUrl", "") or "").strip()

        tk.Label(
            外框,
            text="发现新版本",
            justify="left",
            anchor="w",
            fg="#f3f7ff",
            bg="#0f1726",
            font=("Microsoft YaHei UI", 14, "bold"),
        ).pack(fill="x")

        tk.Label(
            外框,
            text=f"当前版本：{规范版本号(当前版本号, 默认值='未知版本')}",
            justify="left",
            anchor="w",
            fg="#9fb4d9",
            bg="#0f1726",
            font=("Microsoft YaHei UI", 10),
        ).pack(fill="x", pady=(8, 0))

        tk.Label(
            外框,
            text=f"新版本版本号：{远端版本号}",
            justify="left",
            anchor="w",
            fg="#ffe066",
            bg="#0f1726",
            font=("Microsoft YaHei UI", 11, "bold"),
            wraplength=520,
        ).pack(fill="x", pady=(10, 0))

        if 版本提示 and 版本提示 != 远端版本号:
            tk.Label(
                外框,
                text=f"更新提示：{版本提示}",
                justify="left",
                anchor="w",
                fg="#9fb4d9",
                bg="#0f1726",
                font=("Microsoft YaHei UI", 10),
                wraplength=520,
            ).pack(fill="x", pady=(6, 0))

        tk.Label(
            外框,
            text=f"本次更新功能：\n{更新内容}",
            justify="left",
            anchor="w",
            fg="#d7e2f5",
            bg="#0f1726",
            font=("Microsoft YaHei UI", 10),
            wraplength=520,
        ).pack(fill="x", pady=(12, 0))

        按钮区 = tk.Frame(外框, bg="#0f1726")
        按钮区.pack(fill="x", pady=(18, 0))

        def _立即更新():
            try:
                弹窗.grab_release()
            except Exception:
                pass
            弹窗.withdraw()
            成功 = _弹窗下载新版安装包(更新信息, 父窗体=根窗)
            if 成功:
                结果["已启动安装器"] = True
                弹窗.destroy()
                return
            if 弹窗.winfo_exists():
                弹窗.deiconify()
                try:
                    弹窗.grab_set()
                except Exception:
                    pass
                弹窗.focus_force()

        更新按钮 = tk.Button(
            按钮区,
            text="立即更新",
            command=_立即更新,
            padx=14,
            pady=8,
            bg="#1d6cff",
            fg="#ffffff",
            activebackground="#2a7fff",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        更新按钮.pack(side="left")
        if not 下载链接:
            更新按钮.configure(state="disabled")

        tk.Button(
            按钮区,
            text="稍后再说",
            command=弹窗.destroy,
            padx=14,
            pady=8,
            bg="#243248",
            fg="#f3f7ff",
            activebackground="#30415d",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10),
        ).pack(side="right")

        弹窗.update_idletasks()
        宽 = int(弹窗.winfo_width() or 560)
        高 = int(弹窗.winfo_height() or 280)
        屏宽 = int(弹窗.winfo_screenwidth() or 宽)
        屏高 = int(弹窗.winfo_screenheight() or 高)
        x = max(0, (屏宽 - 宽) // 2)
        y = max(0, (屏高 - 高) // 2)
        弹窗.geometry(f"{宽}x{高}+{x}+{y}")
        弹窗.deiconify()
        弹窗.grab_set()
        弹窗.focus_force()
        根窗.wait_window(弹窗)
        return bool(结果.get("已启动安装器", False))
    finally:
        if 根窗 is not None:
            try:
                根窗.destroy()
            except Exception:
                pass


def _切换英文输入法():
    """自动切换系统输入法为英文（仅 Windows）"""
    if sys.platform != "win32":
        return

    try:
        import ctypes
        import time

        # 方法 1: 直接使用 ctypes 调用 Windows ActivateKeyboardLayout API
        try:
            User32 = ctypes.windll.user32
            # 英文（美国）= 0x04090409
            english_layout = 0x04090409
            result = User32.ActivateKeyboardLayout(english_layout, 0)
            time.sleep(0.3)
            if result:
                return
        except Exception:
            pass

        # 方法 2: 使用 PostMessage 发送输入法切换消息到当前窗口
        try:
            User32 = ctypes.windll.user32
            hwnd = User32.GetForegroundWindow()
            WM_INPUTLANGCHANGEREQUEST = 0x0050
            english_layout = 0x04090409
            User32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, english_layout)
            time.sleep(0.3)
            return
        except Exception:
            pass

        # 方法 3: 使用 subprocess 调用 VBScript 进行切换
        try:
            import subprocess
            import tempfile
            import os

            vbs_script = """Set objWShell = CreateObject("WScript.Shell")
objWShell.SendKeys "%({SPACE})"
WScript.Sleep 500
For i = 1 To 10
    objWShell.SendKeys chr(38) & "E"
    WScript.Sleep 50
Next
"""
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".vbs", delete=False
            ) as f:
                f.write(vbs_script)
                script_path = f.name

            subprocess.Popen(
                ["cscript", script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000 if sys.platform == "win32" else 0,
            )

            # 异步删除脚本，不等待
            try:
                os.unlink(script_path)
            except:
                pass
            return
        except Exception:
            pass

    except Exception:
        pass


def _绘制opencv缺失提示(
    屏幕: pygame.Surface,
    字体对象,
):
    if cv2 is not None:
        return
    if 屏幕 is None:
        return
    if 字体对象 is None:
        return

    try:
        提示文本 = "没装opencv"
        阴影色 = (0, 0, 0)
        前景色 = (255, 120, 120)
        背景色 = (20, 20, 20, 170)

        文本面 = 字体对象.render(提示文本, True, 前景色)
        阴影面 = 字体对象.render(提示文本, True, 阴影色)

        外边距x = 12
        外边距y = 10
        内边距x = 10
        内边距y = 6

        背景宽 = 文本面.get_width() + 内边距x * 2
        背景高 = 文本面.get_height() + 内边距y * 2

        背景面 = pygame.Surface((背景宽, 背景高), pygame.SRCALPHA)
        pygame.draw.rect(
            背景面,
            背景色,
            pygame.Rect(0, 0, 背景宽, 背景高),
            border_radius=8,
        )

        屏幕.blit(背景面, (外边距x, 外边距y))
        屏幕.blit(
            阴影面,
            (外边距x + 内边距x + 1, 外边距y + 内边距y + 1),
        )
        屏幕.blit(
            文本面,
            (外边距x + 内边距x, 外边距y + 内边距y),
        )
    except Exception:
        pass


def 主函数():
    显示后端 = None

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

    def _取运行根目录() -> str:
        return 取运行根目录()

    def _同步屏幕引用():
        nonlocal 屏幕
        if 显示后端 is None:
            return
        try:
            屏幕 = 显示后端.取绘制屏幕()
        except Exception:
            return
        try:
            上下文["屏幕"] = 屏幕
        except Exception:
            pass

    def _切换全屏():
        nonlocal 是否全屏, 上次窗口尺寸, 屏幕

        try:
            当前w, 当前h = 上下文["屏幕"].get_size()
        except Exception:
            当前w, 当前h = 1920, 1080

        if not 是否全屏:
            上次窗口尺寸 = (int(当前w), int(当前h))
            if 显示后端 is not None:
                目标w, 目标h = 显示后端.取桌面尺寸()
                显示后端.调整窗口模式((目标w, 目标h), pygame.FULLSCREEN)
            是否全屏 = True
        else:
            恢复w, 恢复h = 上次窗口尺寸
            恢复w = int(max(960, int(恢复w)))
            恢复h = int(max(540, int(恢复h)))
            if 显示后端 is not None:
                显示后端.调整窗口模式((恢复w, 恢复h), pygame.RESIZABLE)
            是否全屏 = False

        _同步屏幕引用()

    def _播放开场幻灯片(图片目录: str):
        if (not 图片目录) or (not os.path.isdir(图片目录)):
            return

        图片路径列表 = []
        try:
            for 文件名 in sorted(os.listdir(图片目录)):
                小写名 = str(文件名).lower()
                if 小写名.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
                    图片路径列表.append(os.path.join(图片目录, 文件名))
        except Exception:
            图片路径列表 = []

        if not 图片路径列表:
            return

        def _加载并缩放图片(图片路径: str, 目标尺寸: tuple[int, int]) -> pygame.Surface | None:
            try:
                原图 = pygame.image.load(图片路径)
            except Exception:
                return None

            try:
                if 原图.get_alpha() is not None:
                    原图 = 原图.convert_alpha()
                else:
                    原图 = 原图.convert()
            except Exception:
                pass

            try:
                原宽, 原高 = 原图.get_size()
                目标宽, 目标高 = 目标尺寸
                if 原宽 <= 0 or 原高 <= 0 or 目标宽 <= 0 or 目标高 <= 0:
                    return 原图

                缩放比例 = min(目标宽 / 原宽, 目标高 / 原高)
                新宽 = max(1, int(round(原宽 * 缩放比例)))
                新高 = max(1, int(round(原高 * 缩放比例)))

                if 新宽 == 原宽 and 新高 == 原高:
                    return 原图

                return pygame.transform.smoothscale(原图, (新宽, 新高))
            except Exception:
                return 原图

        def _绘制居中图片(屏幕面: pygame.Surface, 图片面: pygame.Surface, 透明度: int):
            if 图片面 is None:
                return
            try:
                图片副本 = 图片面.copy()
                图片副本.set_alpha(max(0, min(255, int(透明度))))
            except Exception:
                图片副本 = 图片面

            屏幕宽, 屏幕高 = 屏幕面.get_size()
            图片宽, 图片高 = 图片副本.get_size()
            位置x = (屏幕宽 - 图片宽) // 2
            位置y = (屏幕高 - 图片高) // 2
            屏幕面.blit(图片副本, (位置x, 位置y))

        def _提交开场帧():
            if 显示后端 is not None:
                显示后端.呈现()
                return
            pygame.display.flip()

        def _处理开场事件():
            for 原始事件 in pygame.event.get():
                事件列表 = (
                    显示后端.处理事件(原始事件)
                    if 显示后端 is not None
                    else [原始事件]
                )
                for 事件 in 事件列表:
                    if 事件.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit(0)

                    if 事件.type == pygame.KEYDOWN:
                        if 事件.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit(0)
                        if 事件.key == pygame.K_F11:
                            _切换全屏()
                            continue

                    if 事件.type == pygame.VIDEORESIZE and (not 是否全屏):
                        新w = int(max(960, int(getattr(事件, "w", 0) or 0)))
                        新h = int(max(540, int(getattr(事件, "h", 0) or 0)))
                        if 显示后端 is not None:
                            显示后端.调整窗口模式((新w, 新h), pygame.RESIZABLE)
                            _同步屏幕引用()

        渐显秒 = 2.0
        停留秒 = 1.0
        切换秒 = 0.9
        收尾渐隐秒 = 1.5
        
        播放时钟 = pygame.time.Clock()
        已缓存图片 = {}
        当前屏幕尺寸 = 上下文["屏幕"].get_size()

        def _取缓存图片(图片路径: str) -> pygame.Surface | None:
            nonlocal 当前屏幕尺寸
            最新尺寸 = 上下文["屏幕"].get_size()
            if 最新尺寸 != 当前屏幕尺寸:
                当前屏幕尺寸 = 最新尺寸
                已缓存图片.clear()

            缓存键 = f"{图片路径}|{当前屏幕尺寸[0]}x{当前屏幕尺寸[1]}"
            if 缓存键 in 已缓存图片:
                return 已缓存图片[缓存键]

            图片面 = _加载并缩放图片(图片路径, 当前屏幕尺寸)
            if 图片面 is not None:
                已缓存图片[缓存键] = 图片面
            return 图片面

        if len(图片路径列表) == 1:
            当前图片路径 = 图片路径列表[0]
            开始时间 = time.perf_counter()
            while True:
                _处理开场事件()
                已过秒 = time.perf_counter() - 开始时间
                总秒 = 渐显秒 + 停留秒 + 收尾渐隐秒

                if 已过秒 >= 总秒:
                    break

                if 已过秒 < 渐显秒:
                    透明度 = int(255 * (已过秒 / max(0.001, 渐显秒)))
                elif 已过秒 < 渐显秒 + 停留秒:
                    透明度 = 255
                else:
                    收尾进度 = (已过秒 - 渐显秒 - 停留秒) / max(0.001, 收尾渐隐秒)
                    透明度 = int(255 * (1.0 - 收尾进度))

                当前图片面 = _取缓存图片(当前图片路径)

                上下文["屏幕"].fill((0, 0, 0))
                if 当前图片面 is not None:
                    _绘制居中图片(上下文["屏幕"], 当前图片面, 透明度)
                _提交开场帧()
                播放时钟.tick(60)
            return

        第一个图片路径 = 图片路径列表[0]
        开始时间 = time.perf_counter()

        while True:
            _处理开场事件()
            已过秒 = time.perf_counter() - 开始时间
            if 已过秒 >= 渐显秒 + 停留秒:
                break

            if 已过秒 < 渐显秒:
                当前透明度 = int(255 * (已过秒 / max(0.001, 渐显秒)))
            else:
                当前透明度 = 255

            当前图片面 = _取缓存图片(第一个图片路径)

            上下文["屏幕"].fill((0, 0, 0))
            if 当前图片面 is not None:
                _绘制居中图片(上下文["屏幕"], 当前图片面, 当前透明度)
            _提交开场帧()
            播放时钟.tick(60)

        for 索引 in range(len(图片路径列表) - 1):
            当前图片路径 = 图片路径列表[索引]
            下一张图片路径 = 图片路径列表[索引 + 1]

            当前图片面 = _取缓存图片(当前图片路径)
            下一张图片面 = _取缓存图片(下一张图片路径)

            切换开始时间 = time.perf_counter()
            while True:
                _处理开场事件()
                已过秒 = time.perf_counter() - 切换开始时间
                if 已过秒 >= 切换秒:
                    break

                进度 = max(0.0, min(1.0, 已过秒 / max(0.001, 切换秒)))
                当前透明度 = int(255 * (1.0 - 进度))
                下一张透明度 = int(255 * 进度)

                上下文["屏幕"].fill((0, 0, 0))
                if 当前图片面 is not None:
                    _绘制居中图片(上下文["屏幕"], 当前图片面, 当前透明度)
                if 下一张图片面 is not None:
                    _绘制居中图片(上下文["屏幕"], 下一张图片面, 下一张透明度)
                _提交开场帧()
                播放时钟.tick(60)

            if 索引 + 1 < len(图片路径列表) - 1:
                停留开始时间 = time.perf_counter()
                while True:
                    _处理开场事件()
                    已过秒 = time.perf_counter() - 停留开始时间
                    if 已过秒 >= 停留秒:
                        break

                    下一张图片面 = _取缓存图片(下一张图片路径)
                    上下文["屏幕"].fill((0, 0, 0))
                    if 下一张图片面 is not None:
                        _绘制居中图片(上下文["屏幕"], 下一张图片面, 255)
                    _提交开场帧()
                    播放时钟.tick(60)

        最后一张图片路径 = 图片路径列表[-1]
        结尾停留开始时间 = time.perf_counter()
        while True:
            _处理开场事件()
            已过秒 = time.perf_counter() - 结尾停留开始时间
            if 已过秒 >= 停留秒:
                break

            最后一张图片面 = _取缓存图片(最后一张图片路径)
            上下文["屏幕"].fill((0, 0, 0))
            if 最后一张图片面 is not None:
                _绘制居中图片(上下文["屏幕"], 最后一张图片面, 255)
            _提交开场帧()
            播放时钟.tick(60)

        收尾开始时间 = time.perf_counter()
        while True:
            _处理开场事件()
            已过秒 = time.perf_counter() - 收尾开始时间
            if 已过秒 >= 收尾渐隐秒:
                break

            收尾进度 = max(0.0, min(1.0, 已过秒 / max(0.001, 收尾渐隐秒)))
            最后一张透明度 = int(255 * (1.0 - 收尾进度))

            最后一张图片面 = _取缓存图片(最后一张图片路径)
            上下文["屏幕"].fill((0, 0, 0))
            if 最后一张图片面 is not None:
                _绘制居中图片(上下文["屏幕"], 最后一张图片面, 最后一张透明度)
            _提交开场帧()
            播放时钟.tick(60)

        上下文["屏幕"].fill((0, 0, 0))
        _提交开场帧()

    def _退出程序():
        音乐.停止()
        try:
            背景视频.关闭()
        except Exception:
            pass
        try:
            if 显示后端 is not None:
                显示后端.关闭()
        except Exception:
            pass
        pygame.quit()
        sys.exit(0)

    def _规范渲染后端偏好(值: object, 默认值: str = "gpu") -> str:
        文本 = str(值 or 默认值).strip().lower()
        if 文本 in ("gpu", "gpu-sdl2", "sdl2"):
            return "gpu"
        if 文本 in ("software", "cpu"):
            return "software"
        return str(默认值)

    def _读取启动调试设置() -> dict:
        默认设置 = {
            "默认渲染后端": "gpu",
            "默认GPU谱面管线": True,
            "显示性能调试信息": False,
            "显示启动幻灯片": True,
            "显示谱面开场动画": True,
            "全局静音": False,
            "开发默认选歌载荷启用": True,
            "开发默认选歌类型": "竞速",
            "开发默认选歌模式": "混音",
        }
        设置路径 = os.path.join(_取运行根目录(), "json", "全局设置.json")
        数据 = {}
        try:
            if os.path.isfile(设置路径):
                with open(设置路径, "r", encoding="utf-8") as 文件:
                    对象 = json.load(文件)
                if isinstance(对象, dict):
                    数据 = dict(对象)
        except Exception:
            数据 = {}

        结果 = dict(默认设置)
        结果["默认渲染后端"] = _规范渲染后端偏好(
            数据.get("默认渲染后端", 默认设置["默认渲染后端"]),
            默认值=str(默认设置["默认渲染后端"]),
        )
        结果["默认GPU谱面管线"] = bool(
            数据.get("默认GPU谱面管线", 默认设置["默认GPU谱面管线"])
        )
        结果["显示性能调试信息"] = bool(
            数据.get("显示性能调试信息", 默认设置["显示性能调试信息"])
        )
        结果["显示启动幻灯片"] = bool(
            数据.get("显示启动幻灯片", 默认设置["显示启动幻灯片"])
        )
        结果["显示谱面开场动画"] = bool(
            数据.get("显示谱面开场动画", 默认设置["显示谱面开场动画"])
        )
        结果["全局静音"] = bool(
            数据.get("全局静音", 默认设置["全局静音"])
        )
        结果["开发默认选歌载荷启用"] = bool(
            数据.get(
                "开发默认选歌载荷启用",
                默认设置["开发默认选歌载荷启用"],
            )
        )
        结果["开发默认选歌类型"] = str(
            数据.get("开发默认选歌类型", 默认设置["开发默认选歌类型"]) or "竞速"
        ).strip() or "竞速"
        结果["开发默认选歌模式"] = str(
            数据.get("开发默认选歌模式", 默认设置["开发默认选歌模式"]) or "混音"
        ).strip() or "混音"
        return 结果

    # _切换英文输入法()

    启动调试设置 = _读取启动调试设置()
    当前版本号 = 读取当前版本号(_取运行根目录())
    更新检查状态 = {
        "线程已启动": False,
        "已完成": False,
        "已提示": False,
        "查询成功": False,
        "发现新版本": False,
        "错误": "",
        "数据": None,
    }
    os.environ.setdefault(
        "E5CM_GPU_PIPELINE",
        "1" if bool(启动调试设置.get("默认GPU谱面管线", True)) else "0",
    )

    try:
        import threading

        threading.Thread(
            target=_后台检查软件更新,
            args=(当前版本号, 更新检查状态),
            name="E5CM-CG-UpdateCheck",
            daemon=True,
        ).start()
        更新检查状态["线程已启动"] = True
    except Exception:
        更新检查状态["线程已启动"] = False
        更新检查状态["已完成"] = True

    songs根目录 = os.path.join(_取运行根目录(), "songs")
    if not _songs目录含有曲包(songs根目录):
        _弹窗提示缺少曲包(songs根目录)
        return

    pygame.init()
    窗口标题 = "e舞成名重构版"

    def _取渲染模式文本(后端对象) -> str:
        return "GPU" if bool(getattr(后端对象, "是否GPU", False)) else "CPU"

    def _取渲染后端偏好值(后端对象) -> str:
        return "gpu" if bool(getattr(后端对象, "是否GPU", False)) else "software"

    def _刷新窗口标题(后端对象):
        try:
            后端对象.设置标题(f"{窗口标题} ---{_取渲染模式文本(后端对象)}")
        except Exception:
            pass

    def _取当前实际渲染后端偏好() -> str:
        if 显示后端 is None:
            return str(状态.get("默认渲染后端", "gpu") or "gpu")
        return _取渲染后端偏好值(显示后端)

    默认窗口w, 默认窗口h = 1280, 720
    桌面w, 桌面h = 取桌面尺寸((默认窗口w, 默认窗口h))
    初始w = min(默认窗口w, int(桌面w or 默认窗口w))
    初始h = min(默认窗口h, int(桌面h or 默认窗口h))
    显示后端 = 创建显示后端(
        (初始w, 初始h),
        pygame.RESIZABLE,
        窗口标题,
        偏好=str(启动调试设置.get("默认渲染后端", "gpu") or "gpu"),
    )
    _刷新窗口标题(显示后端)
    屏幕 = 显示后端.取绘制屏幕()

    # time.sleep(0.15)
    # _切换英文输入法()
    pygame.event.clear()

    def _最大化窗口():
        if 显示后端 is not None and 显示后端.最大化窗口():
            return
        if sys.platform != "win32":
            return
        try:
            import ctypes

            User32 = ctypes.windll.user32
            hwnd = User32.GetForegroundWindow()
            SW_MAXIMIZE = 3
            User32.ShowWindow(hwnd, SW_MAXIMIZE)
        except Exception:
            pass

    _最大化窗口()

    时钟 = pygame.time.Clock()
    资源 = 默认资源路径()
    运行根目录 = 取运行根目录()

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
        "每局所需信用": 3,
        "对局_当前把数": 1,
        "对局_S次数": 0,
        "对局_赠送第四把": False,
        "投币快捷键": int(pygame.K_f),
        "投币快捷键显示": "F",
        "默认渲染后端": str(启动调试设置.get("默认渲染后端", "gpu") or "gpu"),
        "默认GPU谱面管线": bool(启动调试设置.get("默认GPU谱面管线", True)),
        "显示性能调试信息": bool(启动调试设置.get("显示性能调试信息", False)),
        "显示启动幻灯片": bool(启动调试设置.get("显示启动幻灯片", False)),
        "显示谱面开场动画": bool(启动调试设置.get("显示谱面开场动画", True)),
        "全局静音": bool(启动调试设置.get("全局静音", False)),
        "开发默认选歌载荷启用": bool(
            启动调试设置.get("开发默认选歌载荷启用", True)
        ),
        "开发默认选歌类型": str(
            启动调试设置.get("开发默认选歌类型", "竞速") or "竞速"
        ),
        "开发默认选歌模式": str(
            启动调试设置.get("开发默认选歌模式", "混音") or "混音"
        ),
        "软件版本": str(当前版本号),
    }

    def _同步渲染后端状态(后端对象, 当前载荷=None):
        实际后端 = _取渲染后端偏好值(后端对象)
        实际启用GPU谱面管线 = bool(getattr(后端对象, "是否GPU", False))
        状态["默认渲染后端"] = str(实际后端)
        状态["默认GPU谱面管线"] = 实际启用GPU谱面管线
        os.environ["E5CM_RENDER_BACKEND"] = str(实际后端)
        os.environ["E5CM_GPU_PIPELINE"] = "1" if 实际启用GPU谱面管线 else "0"
        if isinstance(当前载荷, dict):
            当前载荷["启用GPU谱面管线"] = 实际启用GPU谱面管线
        _刷新窗口标题(后端对象)
        return 实际后端

    _同步渲染后端状态(显示后端)

    点击特效目录 = os.path.join(资源["根"], "UI-img", "点击特效")
    特效资源 = 序列帧特效资源(目录=点击特效目录, 扩展名=".png")
    特效ok = 特效资源.加载()
    全局点击特效 = 全局点击特效管理器(
        帧列表=特效资源.帧列表 if 特效ok else [],
        每秒帧数=60,
        缩放比例=1.0,
    )

    是否全屏 = False
    上次窗口尺寸 = 屏幕.get_size()

    上下文 = {
        "屏幕": 屏幕,
        "时钟": 时钟,
        "资源": 资源,
        "字体": 字体,
        "音乐": 音乐,
        "状态": 状态,
        "全局点击特效": 全局点击特效,
        "背景视频": None,
        "显示后端": 显示后端,
        "渲染后端名称": str(getattr(显示后端, "名称", "software") or "software"),
        "主循环最近统计": {},
        "显示后端最近统计": {},
        "显示性能调试信息": bool(启动调试设置.get("显示性能调试信息", False)),
    }

    backmovies目录 = 资源.get(
        "backmovies目录", os.path.join(资源.get("根", os.getcwd()), "backmovies")
    )
    开场动画目录 = os.path.join(backmovies目录, "开场动画")
    if bool(启动调试设置.get("显示启动幻灯片", True)):
        _播放开场幻灯片(开场动画目录)
    
    强制视频 = os.path.join(backmovies目录, "003.mp4")
    if os.path.isfile(强制视频):
        视频路径 = 强制视频
    else:
        视频路径 = 选择第一个视频(backmovies目录)

    原始背景视频播放器 = 全局视频循环播放器(视频路径)
    原始背景视频播放器.打开(是否重置进度=True)
    背景视频 = 全局视频循环播放器(视频路径)
    上下文["背景视频"] = 背景视频

    场景表 = {
        "投币": 场景_投币,
        "登陆磁卡": 场景_登陆磁卡,
        "个人资料": 场景_个人资料,
        "大模式": 场景_大模式,
        "子模式": 场景_子模式,
        "选歌": 场景_选歌,
        "加载页": 场景_加载页,
        "结算": 场景_结算,
        "谱面播放器": 场景_谱面播放器,
    }


    当前场景名 = "投币"
    当前场景 = 场景表[当前场景名](上下文)
    _安全进入场景(当前场景, None)

    过渡 = 公共黑屏过渡(渐入秒=0.2,渐出秒=0)
    入场 = 公共丝滑入场(保持黑屏秒=0.03, 渐出秒=0.3)
    
    待切换目标场景名 = None
    待切换载荷 = None

    调试提示文本 = ""
    调试提示截止 = 0.0
    非游戏菜单开启 = False
    非游戏菜单索引 = 0
    投币快捷键录入中 = False
    非游戏菜单项矩形: list[pygame.Rect] = []
    非游戏菜单背景音乐关闭 = False
    非游戏菜单背景音乐路径 = ""
    选歌ESC菜单宿主 = SelectSceneEscMenuHost(上下文)
    投币音效对象 = None
    try:
        投币音效路径 = str(资源.get("投币音效", "") or "")
        if 投币音效路径 and os.path.isfile(投币音效路径) and pygame.mixer.get_init():
            投币音效对象 = pygame.mixer.Sound(投币音效路径)
    except Exception:
        投币音效对象 = None

    投币快捷键 = int(pygame.K_f)
    投币快捷键显示 = "F"
    全局设置路径 = os.path.join(运行根目录, "json", "全局设置.json")


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

        try:
            当前投币数 = max(0, int(状态.get("投币数", 0) or 0))
        except Exception:
            当前投币数 = 0

        旧数据 = {}
        try:
            if os.path.isfile(全局设置路径):
                with open(全局设置路径, "r", encoding="utf-8") as 文件:
                    已有对象 = json.load(文件)
                if isinstance(已有对象, dict):
                    旧数据 = 已有对象
        except Exception:
            旧数据 = {}

        新数据 = dict(旧数据)
        新数据.update(
            {
                "投币快捷键": int(投币快捷键),
                "投币快捷键显示": str(投币快捷键显示),
                "投币数": int(当前投币数),
                "默认渲染后端": str(状态.get("默认渲染后端", "gpu") or "gpu"),
                "默认GPU谱面管线": bool(
                    状态.get("默认GPU谱面管线", True)
                ),
                "显示性能调试信息": bool(
                    状态.get("显示性能调试信息", False)
                ),
                "显示启动幻灯片": bool(
                    状态.get("显示启动幻灯片", True)
                ),
                "显示谱面开场动画": bool(
                    状态.get("显示谱面开场动画", True)
                ),
                "全局静音": bool(
                    状态.get("全局静音", False)
                ),
                "开发默认选歌载荷启用": bool(
                    状态.get("开发默认选歌载荷启用", True)
                ),
                "开发默认选歌类型": str(
                    状态.get("开发默认选歌类型", "竞速") or "竞速"
                ),
                "开发默认选歌模式": str(
                    状态.get("开发默认选歌模式", "混音") or "混音"
                ),
            }
        )

        新数据.pop("残余币值", None)
        新数据.pop("credit", None)

        try:
            with open(全局设置路径, "w", encoding="utf-8") as 文件:
                json.dump(新数据, 文件, ensure_ascii=False, indent=2)
        except Exception:
            pass


    def _加载全局设置():
        nonlocal 投币快捷键, 投币快捷键显示

        数据 = {}
        try:
            if os.path.isfile(全局设置路径):
                with open(全局设置路径, "r", encoding="utf-8") as 文件:
                    对象 = json.load(文件)
                if isinstance(对象, dict):
                    数据 = 对象
        except Exception:
            数据 = {}

        try:
            键值 = int(数据.get("投币快捷键", pygame.K_f))
            投币快捷键 = int(max(0, min(4096, 键值)))
        except Exception:
            投币快捷键 = int(pygame.K_f)

        投币快捷键显示 = _格式化按键名(int(投币快捷键))
        状态["投币快捷键"] = int(投币快捷键)
        状态["投币快捷键显示"] = str(投币快捷键显示)

        try:
            当前投币数 = max(0, int(数据.get("投币数", 0) or 0))
        except Exception:
            当前投币数 = 0

        状态["投币数"] = int(当前投币数)
        状态["credit"] = str(int(当前投币数))
        状态["默认渲染后端"] = _规范渲染后端偏好(
            数据.get("默认渲染后端", 状态.get("默认渲染后端", "gpu")),
            默认值=str(状态.get("默认渲染后端", "gpu") or "gpu"),
        )
        状态["默认GPU谱面管线"] = bool(
            数据.get("默认GPU谱面管线", 状态.get("默认GPU谱面管线", True))
        )
        状态["显示性能调试信息"] = bool(
            数据.get("显示性能调试信息", 状态.get("显示性能调试信息", False))
        )
        状态["显示启动幻灯片"] = bool(
            数据.get("显示启动幻灯片", 状态.get("显示启动幻灯片", True))
        )
        状态["显示谱面开场动画"] = bool(
            数据.get("显示谱面开场动画", 状态.get("显示谱面开场动画", True))
        )
        状态["全局静音"] = bool(
            数据.get("全局静音", 状态.get("全局静音", False))
        )
        状态["开发默认选歌载荷启用"] = bool(
            数据.get(
                "开发默认选歌载荷启用",
                状态.get("开发默认选歌载荷启用", True),
            )
        )
        状态["开发默认选歌类型"] = str(
            数据.get(
                "开发默认选歌类型",
                状态.get("开发默认选歌类型", "竞速"),
            )
            or "竞速"
        ).strip() or "竞速"
        状态["开发默认选歌模式"] = str(
            数据.get(
                "开发默认选歌模式",
                状态.get("开发默认选歌模式", "混音"),
            )
            or "混音"
        ).strip() or "混音"
        上下文["显示性能调试信息"] = bool(
            状态.get("显示性能调试信息", False)
        )
        os.environ["E5CM_GPU_PIPELINE"] = (
            "1" if bool(状态.get("默认GPU谱面管线", True)) else "0"
        )

    def _应用全局静音状态():
        静音 = bool(状态.get("全局静音", False))
        try:
            if pygame.mixer.get_init():
                音量 = 0.0 if 静音 else 1.0
                try:
                    pygame.mixer.music.set_volume(float(音量))
                except Exception:
                    pass
                try:
                    for i in range(int(pygame.mixer.get_num_channels())):
                        pygame.mixer.Channel(int(i)).set_volume(float(音量))
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if 投币音效对象 is not None:
                投币音效对象.set_volume(0.0 if 静音 else 1.0)
        except Exception:
            pass
        

    def _显示调试提示(文本: str, 秒: float = 1.2):
        nonlocal 调试提示文本, 调试提示截止
        调试提示文本 = 文本
        调试提示截止 = time.time() + float(秒)

    def _同步投币显示():
        try:
            投币数 = int(状态.get("投币数", 0) or 0)
        except Exception:
            投币数 = 0

        投币数 = max(0, 投币数)
        状态["投币数"] = int(投币数)
        状态["credit"] = str(int(投币数))
        _保存全局设置()
        
    _加载全局设置()
    _同步渲染后端状态(显示后端)
    _应用全局静音状态()
    _同步投币显示()

    状态["非游戏菜单背景音乐关闭"] = bool(非游戏菜单背景音乐关闭)
    开发调试菜单开启 = False
    开发调试菜单索引 = 0
    开发调试菜单项矩形: list[pygame.Rect] = []
    开发调试目标场景列表 = [
        "选歌",
        "投币",
        "登陆磁卡",
        "个人资料",
        "加载页",
        "谱面播放器",
    ]
    开发调试目标场景索引 = int(
        max(0, min(len(开发调试目标场景列表) - 1, 开发调试目标场景列表.index("选歌")))
    )

    def _取当前场景载荷() -> dict:
        try:
            值 = getattr(当前场景, "_载荷", None)
            if isinstance(值, dict):
                return dict(值)
        except Exception:
            pass
        return {}

    def _取当前开发目标场景() -> str:
        try:
            return str(开发调试目标场景列表[int(开发调试目标场景索引)] or "投币")
        except Exception:
            return "投币"

    def _解析开发载荷预设() -> dict:
        try:
            值 = 状态.get("加载页_载荷", {})
            if isinstance(值, dict):
                return dict(值)
        except Exception:
            pass
        return {}

    def _取开发默认选歌载荷() -> dict:
        if not bool(状态.get("开发默认选歌载荷启用", True)):
            return {}
        类型 = str(状态.get("开发默认选歌类型", "竞速") or "竞速").strip() or "竞速"
        模式 = str(状态.get("开发默认选歌模式", "混音") or "混音").strip() or "混音"
        return {
            "选歌类型": str(类型),
            "选歌模式": str(模式),
            "类型": str(类型),
            "模式": str(模式),
            "大模式": str(类型),
            "子模式": str(模式),
            "songs子文件夹": str(类型),
        }

    def _合并开发默认选歌载荷(载荷: Optional[dict]) -> dict:
        结果 = dict(载荷 or {}) if isinstance(载荷, dict) else {}
        for 键, 值 in _取开发默认选歌载荷().items():
            结果.setdefault(str(键), 值)
        return 结果

    def _构建开发跳转载荷(目标场景名: str):
        目标场景名 = str(目标场景名 or "").strip()
        预设载荷 = _解析开发载荷预设()
        if 目标场景名 in ("加载页", "谱面播放器"):
            载荷 = dict(预设载荷 or {})
            载荷["显示准备动画"] = bool(状态.get("显示谱面开场动画", True))
            载荷["启用GPU谱面管线"] = bool(状态.get("默认GPU谱面管线", True))
            return 载荷
        if 目标场景名 == "选歌":
            选歌载荷 = _合并开发默认选歌载荷(预设载荷)
            return {"加载页_载荷": dict(选歌载荷)} if bool(选歌载荷) else None
        return None

    def _重建当前场景并切换后端(目标后端: str):
        nonlocal 显示后端, 屏幕, 当前场景
        目标后端 = _规范渲染后端偏好(目标后端, 默认值="gpu")
        当前载荷 = _取当前场景载荷()
        目标flags = pygame.FULLSCREEN if bool(是否全屏) else pygame.RESIZABLE
        try:
            目标尺寸 = tuple(int(v) for v in 上下文["屏幕"].get_size())
        except Exception:
            目标尺寸 = (1280, 720)

        try:
            当前场景.退出()
        except Exception:
            pass
        try:
            if 显示后端 is not None:
                显示后端.关闭()
        except Exception:
            pass

        显示后端 = 创建显示后端(
            目标尺寸,
            int(目标flags),
            窗口标题,
            偏好=str(目标后端),
        )
        实际后端 = _同步渲染后端状态(显示后端, 当前载荷)
        屏幕 = 显示后端.取绘制屏幕()
        上下文["屏幕"] = 屏幕
        上下文["显示后端"] = 显示后端
        上下文["渲染后端名称"] = str(
            getattr(显示后端, "名称", 实际后端) or 实际后端
        )
        上下文["显示性能调试信息"] = bool(状态.get("显示性能调试信息", False))
        try:
            当前场景 = 场景表[当前场景名](上下文)
            _安全进入场景(当前场景, 当前载荷 if bool(当前载荷) else None)
        except Exception:
            当前场景 = 场景表["投币"](上下文)
            _安全进入场景(当前场景, None)
        _保存全局设置()
        _显示调试提示(
            f"渲染后端已切换为：{_取渲染模式文本(显示后端)}",
            1.2,
        )

    def _切换性能调试信息显示():
        状态["显示性能调试信息"] = not bool(状态.get("显示性能调试信息", False))
        上下文["显示性能调试信息"] = bool(状态["显示性能调试信息"])
        _保存全局设置()
        _显示调试提示(
            f"性能调试信息已{'显示' if bool(状态['显示性能调试信息']) else '隐藏'}",
            1.0,
        )

    def _切换全局静音():
        状态["全局静音"] = not bool(状态.get("全局静音", False))
        _应用全局静音状态()
        _保存全局设置()
        _显示调试提示(
            f"全局静音已{'开启' if bool(状态['全局静音']) else '关闭'}",
            1.0,
        )

    def _切换开发默认选歌载荷():
        当前启用 = bool(状态.get("开发默认选歌载荷启用", True))
        状态["开发默认选歌载荷启用"] = not 当前启用
        if bool(状态["开发默认选歌载荷启用"]):
            状态["开发默认选歌类型"] = str(
                状态.get("开发默认选歌类型", "竞速") or "竞速"
            ).strip() or "竞速"
            状态["开发默认选歌模式"] = str(
                状态.get("开发默认选歌模式", "混音") or "混音"
            ).strip() or "混音"
        _保存全局设置()
        if bool(状态["开发默认选歌载荷启用"]):
            _显示调试提示(
                f"选歌默认载荷：{状态['开发默认选歌类型']} / {状态['开发默认选歌模式']}",
                1.0,
            )
        else:
            _显示调试提示("选歌默认载荷已关闭", 1.0)

    def _执行开发场景跳转():
        nonlocal 当前场景名, 当前场景, 开发调试菜单开启
        目标场景名 = _取当前开发目标场景()
        载荷 = _构建开发跳转载荷(目标场景名)
        try:
            当前场景.退出()
        except Exception:
            pass
        当前场景名 = str(目标场景名)
        当前场景 = 场景表[当前场景名](上下文)
        _安全进入场景(当前场景, 载荷)
        开发调试菜单开启 = False
        _显示调试提示(f"已切换到场景：{当前场景名}", 1.0)

    def _取开发调试菜单项() -> list[str]:
        渲染文本 = _取渲染模式文本(显示后端)
        默认选歌文本 = (
            f"{str(状态.get('开发默认选歌类型', '竞速') or '竞速')} / "
            f"{str(状态.get('开发默认选歌模式', '混音') or '混音')}"
            if bool(状态.get("开发默认选歌载荷启用", True))
            else "关闭"
        )
        return [
            f"渲染模式：{渲染文本}",
            f"性能调试信息：{'显示' if bool(状态.get('显示性能调试信息', False)) else '隐藏'}",
            f"全局静音：{'开启' if bool(状态.get('全局静音', False)) else '关闭'}",
            f"选歌默认载荷：{默认选歌文本}",
            f"跳转场景：{_取当前开发目标场景()}",
            "立即切换场景",
        ]

    def _执行开发调试菜单选项(索引: int, 方向: int = 0):
        nonlocal 开发调试目标场景索引
        索引 = int(max(0, min(len(_取开发调试菜单项()) - 1, int(索引))))
        if 索引 == 0:
            当前模式 = _取当前实际渲染后端偏好()
            目标模式 = "software" if 当前模式 == "gpu" else "gpu"
            _重建当前场景并切换后端(目标模式)
            return
        if 索引 == 1:
            _切换性能调试信息显示()
            return
        if 索引 == 2:
            _切换全局静音()
            return
        if 索引 == 3:
            _切换开发默认选歌载荷()
            return
        if 索引 == 4:
            步进 = int(方向) if int(方向) != 0 else 1
            开发调试目标场景索引 = (
                int(开发调试目标场景索引) + 步进
            ) % len(开发调试目标场景列表)
            return
        if 索引 == 5:
            _执行开发场景跳转()
            return

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
        所需信用 = 取每局所需信用(状态)
        _显示调试提示(
            f"{str(状态.get('投币快捷键显示', 投币快捷键显示))}投币 +1  当前:{max(0, 当前币)}/{int(所需信用)}",
            0.8,
        )

    def _取非游戏菜单项() -> list[str]:
        菜单项 = [
            f"设置投币快捷键（当前：{str(状态.get('投币快捷键显示', 投币快捷键显示))}）",
            "开启背景音乐" if bool(非游戏菜单背景音乐关闭) else "关闭背景音乐",
        ]
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
        if 恢复路径 and os.path.isfile(恢复路径) and (str(当前场景名 or "") != "选歌"):
            try:
                音乐.播放循环(恢复路径)
            except Exception:
                pass
        非游戏菜单背景音乐关闭 = False
        状态["非游戏菜单背景音乐关闭"] = False
        _显示调试提示("背景音乐已开启", 1.0)

    def _执行非游戏菜单选项(索引: int):
        nonlocal 投币快捷键录入中
        菜单项 = _取非游戏菜单项()
        if not 菜单项:
            return
        索引 = int(max(0, min(len(菜单项) - 1, int(索引))))
        选项 = 菜单项[索引]
        if "设置投币快捷键" in 选项:
            投币快捷键录入中 = True
            _显示调试提示("请按任意键设置为投币快捷键（ESC取消）", 2.0)
            return
        if "背景音乐" in 选项:
            _切换非游戏背景音乐()
            return
        if 选项 == "退出到桌面":
            _退出程序()
            return

    def _绘制非游戏菜单():
        nonlocal 非游戏菜单项矩形
        非游戏菜单项矩形 = []
        if not 非游戏菜单开启:
            return
        try:
            屏幕面 = 上下文["屏幕"]
            w, h = 屏幕面.get_size()
            遮罩 = pygame.Surface((w, h), pygame.SRCALPHA)
            遮罩.fill((0, 0, 0, 178))
            屏幕面.blit(遮罩, (0, 0))

            菜单项 = _取非游戏菜单项()
            面板w = max(660, min(int(w * 0.46), 860))
            面板h = max(320, min(int(h * 0.66), 200 + len(菜单项) * 72))
            面板 = pygame.Rect((w - 面板w) // 2, (h - 面板h) // 2, 面板w, 面板h)

            标题字 = 上下文["字体"]["中字"]
            小字 = 上下文["字体"]["小字"]
            标题面 = 标题字.render("系统菜单", True, (245, 248, 255))
            屏幕面.blit(标题面, (面板.x + 24, 面板.y + 2))
            副标题面 = 小字.render("ESC / SYSTEM", True, (140, 172, 225))
            try:
                副标题面.set_alpha(170)
            except Exception:
                pass
            屏幕面.blit(副标题面, (面板.x + 26, 面板.y + 46))

            按钮高 = 58
            按钮间距 = 14
            选项起y = int(面板.y + 86)
            for idx, 名称 in enumerate(菜单项):
                选中 = idx == int(非游戏菜单索引)
                行rect = pygame.Rect(
                    int(面板.x + 22),
                    int(选项起y + idx * (按钮高 + 按钮间距)),
                    int(面板.w - 44),
                    int(按钮高),
                )
                底色 = (26, 34, 54) if 选中 else (18, 24, 40)
                边色 = (120, 238, 255) if 选中 else (76, 96, 136)
                pygame.draw.rect(屏幕面, 底色, 行rect, border_radius=14)
                pygame.draw.rect(
                    屏幕面,
                    边色,
                    行rect,
                    width=2 if 选中 else 1,
                    border_radius=14,
                )
                if 选中:
                    高亮 = pygame.Surface((行rect.w, 行rect.h), pygame.SRCALPHA)
                    pygame.draw.rect(
                        高亮,
                        (0, 239, 251, 34),
                        pygame.Rect(0, 0, 行rect.w, 行rect.h),
                        border_radius=14,
                    )
                    pygame.draw.rect(
                        高亮,
                        (255, 88, 170, 150),
                        pygame.Rect(0, 10, 5, 行rect.h - 20),
                        border_radius=3,
                    )
                    屏幕面.blit(高亮, 行rect.topleft)
                序号面 = 小字.render(f"{idx + 1:02d}", True, (116, 146, 196))
                屏幕面.blit(
                    序号面,
                    (
                        int(行rect.x + 16),
                        int(行rect.y + (行rect.h - 序号面.get_height()) // 2),
                    ),
                )
                项面 = 小字.render(
                    str(名称),
                    True,
                    (255, 245, 164) if 选中 else (226, 233, 246),
                )
                屏幕面.blit(
                    项面,
                    (
                        int(行rect.x + 62),
                        int(行rect.y + (行rect.h - 项面.get_height()) // 2),
                    ),
                )
                非游戏菜单项矩形.append(行rect)

            提示行 = [
                f"{str(状态.get('投币快捷键显示', 投币快捷键显示))}投币   ESC关闭",
                "鼠标点击 / 小键盘1-3切换 / 5确认",
            ]
            提示y = int(选项起y + len(菜单项) * (按钮高 + 按钮间距) + 12)
            for 文本 in 提示行:
                行面 = 小字.render(文本, True, (132, 148, 178))
                try:
                    行面.set_alpha(150)
                except Exception:
                    pass
                屏幕面.blit(行面, (面板.x + 24, 提示y))
                提示y += int(行面.get_height()) + 2

            if bool(投币快捷键录入中):
                提示 = "等待按键输入：按任意键设为投币键（ESC取消）"
                提示面 = 小字.render(提示, True, (255, 240, 140))
                屏幕面.blit(提示面, (面板.x + 24, int(面板.y + 58)))
        except Exception:
            pass

    def _绘制开发调试菜单():
        nonlocal 开发调试菜单项矩形
        开发调试菜单项矩形 = []
        if not 开发调试菜单开启:
            return
        try:
            屏幕面 = 上下文["屏幕"]
            w, h = 屏幕面.get_size()
            遮罩 = pygame.Surface((w, h), pygame.SRCALPHA)
            遮罩.fill((0, 8, 18, 190))
            屏幕面.blit(遮罩, (0, 0))

            菜单项 = _取开发调试菜单项()
            面板w = max(760, min(int(w * 0.58), 980))
            面板h = max(420, min(int(h * 0.76), 220 + len(菜单项) * 72))
            面板 = pygame.Rect((w - 面板w) // 2, (h - 面板h) // 2, 面板w, 面板h)

            标题字 = 上下文["字体"]["中字"]
            小字 = 上下文["字体"]["小字"]
            标题面 = 标题字.render("开发调试菜单", True, (245, 248, 255))
            屏幕面.blit(标题面, (面板.x + 24, 面板.y + 2))
            副标题面 = 小字.render("CTRL+F10 / DEV MENU", True, (120, 220, 255))
            try:
                副标题面.set_alpha(170)
            except Exception:
                pass
            屏幕面.blit(副标题面, (面板.x + 26, 面板.y + 46))

            按钮高 = 58
            按钮间距 = 14
            选项起y = int(面板.y + 86)
            for idx, 名称 in enumerate(菜单项):
                选中 = idx == int(开发调试菜单索引)
                行rect = pygame.Rect(
                    int(面板.x + 22),
                    int(选项起y + idx * (按钮高 + 按钮间距)),
                    int(面板.w - 44),
                    int(按钮高),
                )
                底色 = (22, 30, 48) if 选中 else (16, 22, 36)
                边色 = (120, 238, 255) if 选中 else (66, 90, 128)
                pygame.draw.rect(屏幕面, 底色, 行rect, border_radius=14)
                pygame.draw.rect(
                    屏幕面,
                    边色,
                    行rect,
                    width=2 if 选中 else 1,
                    border_radius=14,
                )
                if 选中:
                    高亮 = pygame.Surface((行rect.w, 行rect.h), pygame.SRCALPHA)
                    pygame.draw.rect(
                        高亮,
                        (0, 239, 251, 28),
                        pygame.Rect(0, 0, 行rect.w, 行rect.h),
                        border_radius=14,
                    )
                    pygame.draw.rect(
                        高亮,
                        (255, 88, 170, 150),
                        pygame.Rect(0, 10, 5, 行rect.h - 20),
                        border_radius=3,
                    )
                    屏幕面.blit(高亮, 行rect.topleft)
                序号面 = 小字.render(f"{idx + 1:02d}", True, (116, 146, 196))
                屏幕面.blit(
                    序号面,
                    (
                        int(行rect.x + 16),
                        int(行rect.y + (行rect.h - 序号面.get_height()) // 2),
                    ),
                )
                项面 = 小字.render(
                    str(名称),
                    True,
                    (255, 245, 164) if 选中 else (226, 233, 246),
                )
                屏幕面.blit(
                    项面,
                    (
                        int(行rect.x + 62),
                        int(行rect.y + (行rect.h - 项面.get_height()) // 2),
                    ),
                )
                开发调试菜单项矩形.append(行rect)

            提示行 = [
                "左右切换选项值 / 回车执行 / ESC或Ctrl+F10关闭",
                "选歌跳转会给空载荷补默认模式；加载页和谱面播放器沿用当前状态载荷",
            ]
            提示y = int(选项起y + len(菜单项) * (按钮高 + 按钮间距) + 12)
            for 文本 in 提示行:
                行面 = 小字.render(文本, True, (132, 148, 178))
                try:
                    行面.set_alpha(150)
                except Exception:
                    pass
                屏幕面.blit(行面, (面板.x + 24, 提示y))
                提示y += int(行面.get_height()) + 2
        except Exception:
            pass

    def _处理非游戏菜单按键(事件) -> bool:
        nonlocal 非游戏菜单开启, 非游戏菜单索引
        nonlocal 投币快捷键录入中, 投币快捷键, 投币快捷键显示

        if not 非游戏菜单开启:
            return False

        菜单项 = _取非游戏菜单项()

        if bool(投币快捷键录入中):
            if 事件.type == pygame.KEYDOWN:
                if 事件.key == pygame.K_ESCAPE:
                    投币快捷键录入中 = False
                    _显示调试提示("已取消修改投币快捷键", 1.0)
                    return True
                投币快捷键 = int(max(0, min(4096, int(事件.key))))
                投币快捷键显示 = _格式化按键名(int(投币快捷键))
                状态["投币快捷键"] = int(投币快捷键)
                状态["投币快捷键显示"] = str(投币快捷键显示)
                _保存全局设置()
                投币快捷键录入中 = False
                _显示调试提示(f"投币快捷键已改为：{投币快捷键显示}", 1.2)
                return True
            return True

        if 事件.type == pygame.KEYDOWN:
            if 事件.key == pygame.K_ESCAPE:
                非游戏菜单开启 = False
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
            for idx, rect in enumerate(非游戏菜单项矩形):
                if rect.collidepoint(事件.pos):
                    非游戏菜单索引 = int(idx)
                    _执行非游戏菜单选项(int(idx))
                    return True
            非游戏菜单开启 = False
            投币快捷键录入中 = False
            return True

        return True

    def _处理开发调试菜单按键(事件) -> bool:
        nonlocal 开发调试菜单开启, 开发调试菜单索引
        if not 开发调试菜单开启:
            return False

        菜单项 = _取开发调试菜单项()
        if 事件.type == pygame.KEYDOWN:
            mod = int(getattr(事件, "mod", 0) or 0)
            ctrl_f10 = bool(
                事件.key == pygame.K_F10 and (mod & pygame.KMOD_CTRL)
            )
            if 事件.key == pygame.K_ESCAPE or ctrl_f10:
                开发调试菜单开启 = False
                return True
            if 事件.key in (pygame.K_UP, pygame.K_KP7, pygame.K_LEFT, pygame.K_KP1):
                if 事件.key in (pygame.K_LEFT, pygame.K_KP1):
                    _执行开发调试菜单选项(int(开发调试菜单索引), -1)
                else:
                    开发调试菜单索引 = (int(开发调试菜单索引) - 1) % len(菜单项)
                return True
            if 事件.key in (pygame.K_DOWN, pygame.K_KP9, pygame.K_RIGHT, pygame.K_KP3):
                if 事件.key in (pygame.K_RIGHT, pygame.K_KP3):
                    _执行开发调试菜单选项(int(开发调试菜单索引), 1)
                else:
                    开发调试菜单索引 = (int(开发调试菜单索引) + 1) % len(菜单项)
                return True
            if 事件.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_KP5):
                _执行开发调试菜单选项(int(开发调试菜单索引), 0)
                return True
            return True

        if 事件.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(开发调试菜单项矩形):
                if rect.collidepoint(事件.pos):
                    开发调试菜单索引 = int(idx)
                    break
            return True

        if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
            for idx, rect in enumerate(开发调试菜单项矩形):
                if rect.collidepoint(事件.pos):
                    开发调试菜单索引 = int(idx)
                    _执行开发调试菜单选项(int(idx), 0)
                    return True
            开发调试菜单开启 = False
            return True

        return True

    def _执行场景切换():
        nonlocal 当前场景名, 当前场景, 待切换目标场景名, 待切换载荷
        nonlocal 非游戏菜单开启, 非游戏菜单索引, 投币快捷键录入中

        原场景名 = str(当前场景名 or "")
        目标 = 待切换目标场景名
        载荷 = 待切换载荷
        if 目标 == "玩家选择":
            目标 = "投币"
        if not 目标 or (目标 not in 场景表):
            return

        try:
            当前场景.退出()
        except Exception:
            pass

        当前场景名 = 目标
        当前场景 = 场景表[当前场景名](上下文)
        _安全进入场景(当前场景, 载荷)
        if str(当前场景名 or "") != "选歌" and bool(选歌ESC菜单宿主.is_open()):
            选歌ESC菜单宿主.close()

        if 原场景名 == "投币" and 当前场景名 == "登陆磁卡":
            入场.开始()

        待切换目标场景名 = None
        待切换载荷 = None
        非游戏菜单开启 = False
        非游戏菜单索引 = 0
        投币快捷键录入中 = False


    def _当前场景允许非游戏菜单() -> bool:
        return bool(当前场景名 not in ("谱面播放器", "结算"))

    def _获取当前目标帧率() -> int:
        try:
            值 = int(getattr(当前场景, "目标帧率", 60) or 60)
        except Exception:
            值 = 60
        return max(30, min(240, 值))

    def _处理场景返回结果(结果) -> bool:
        nonlocal 待切换目标场景名, 待切换载荷

        目标 = None
        载荷 = None
        禁用黑屏 = False

        if isinstance(结果, dict):
            if bool(结果.get("退出程序", False)):
                _退出程序()
            目标 = 结果.get("切换到")
            载荷 = 结果.get("载荷")
            禁用黑屏 = bool(结果.get("禁用黑屏过渡", False))
        else:
            try:
                目标 = getattr(结果, "目标场景名", None)
                载荷 = getattr(结果, "载荷", None)
            except Exception:
                目标 = None

        if 目标 == "玩家选择":
            目标 = "投币"

        if not 目标 or (目标 not in 场景表):
            return False

        待切换目标场景名 = 目标
        待切换载荷 = 载荷
        if 禁用黑屏:
            _执行场景切换()
        else:
            过渡.开始(目标)
        return True

    while True:
        循环开始秒 = time.perf_counter()
        时钟.tick(_获取当前目标帧率())

        for 原始事件 in pygame.event.get():
            事件列表 = (
                显示后端.处理事件(原始事件)
                if 显示后端 is not None
                else [原始事件]
            )
            for 事件 in 事件列表:
                if 事件.type == pygame.QUIT:
                    _退出程序()

                if 事件.type == pygame.KEYDOWN:
                    mod = int(getattr(事件, "mod", 0) or 0)
                    if 事件.key == pygame.K_F10 and (mod & pygame.KMOD_CTRL):
                        开发调试菜单开启 = not bool(开发调试菜单开启)
                        if bool(开发调试菜单开启):
                            非游戏菜单开启 = False
                            非游戏菜单索引 = 0
                            投币快捷键录入中 = False
                        continue

                if _处理开发调试菜单按键(事件):
                    continue

                if (
                    事件.type == pygame.KEYDOWN
                    and int(事件.key) == int(投币快捷键)
                    and (not bool(投币快捷键录入中))
                ):
                    _全局投币一次()
                    if (not 过渡.是否进行中()) and 当前场景名 == "投币":
                        try:
                            当前币 = int(状态.get("投币数", 0) or 0)
                        except Exception:
                            当前币 = 0
                        所需信用 = 取每局所需信用(状态)
                        if 当前币 >= int(所需信用):
                            _显示调试提示(
                                f"已满足开局条件：请选择 1P / 2P（{int(当前币)}/{int(所需信用)}）",
                                0.9,
                            )
                        else:
                            _显示调试提示(
                                f"还需 {max(0, int(所需信用) - 当前币)} 币（{int(所需信用)}币开局）",
                                0.9,
                            )
                    continue

                if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F11:
                    if not 过渡.是否进行中():
                        _切换全屏()
                    continue

                if 事件.type == pygame.VIDEORESIZE and (not 是否全屏):
                    新w = int(max(960, int(getattr(事件, "w", 0) or 0)))
                    新h = int(max(540, int(getattr(事件, "h", 0) or 0)))
                    if 显示后端 is not None:
                        显示后端.调整窗口模式((新w, 新h), pygame.RESIZABLE)
                        _同步屏幕引用()
                    上次窗口尺寸 = 上下文["屏幕"].get_size()

                # if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_F5:
                #     if not 过渡.是否进行中():
                #         _热更新当前场景()
                #     continue

                if 事件.type == pygame.MOUSEBUTTONDOWN and 事件.button == 1:
                    x, y = 事件.pos
                    全局点击特效.触发(x, y)

                if 过渡.是否进行中():
                    continue

                if str(当前场景名 or "") == "选歌":
                    if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
                        非游戏菜单开启 = False
                        投币快捷键录入中 = False
                        if bool(选歌ESC菜单宿主.is_open()):
                            选歌ESC菜单宿主.close()
                        else:
                            选歌ESC菜单宿主.open()
                        continue

                    if bool(选歌ESC菜单宿主.is_open()):
                        结果 = 选歌ESC菜单宿主.handle_event(事件)
                        if isinstance(结果, dict) and bool(结果.get("close_menu", False)):
                            选歌ESC菜单宿主.close()
                            continue
                        if _处理场景返回结果(结果):
                            continue
                        continue

                elif _当前场景允许非游戏菜单():
                    if 事件.type == pygame.KEYDOWN and 事件.key == pygame.K_ESCAPE:
                        if bool(非游戏菜单开启) and bool(投币快捷键录入中):
                            投币快捷键录入中 = False
                            _显示调试提示("已取消修改投币快捷键", 1.0)
                        else:
                            非游戏菜单开启 = not bool(非游戏菜单开启)
                            if not 非游戏菜单开启:
                                投币快捷键录入中 = False
                            非游戏菜单索引 = 0
                            状态["非游戏菜单背景音乐关闭"] = bool(非游戏菜单背景音乐关闭)
                        continue

                    if _处理非游戏菜单按键(事件):
                        continue
                else:
                    if 非游戏菜单开启:
                        非游戏菜单开启 = False
                        非游戏菜单索引 = 0
                        投币快捷键录入中 = False
                    if bool(选歌ESC菜单宿主.is_open()):
                        选歌ESC菜单宿主.close()

                踏板动作 = 解析踏板动作(事件)
                if 踏板动作 is not None:
                    处理踏板 = getattr(当前场景, "处理全局踏板", None)
                    if callable(处理踏板):
                        try:
                            踏板结果 = 处理踏板(踏板动作)
                        except Exception:
                            踏板结果 = None
                        _处理场景返回结果(踏板结果)
                        continue

                结果 = 当前场景.处理事件(事件)
                _处理场景返回结果(结果)

        if (
            bool(更新检查状态.get("已完成", False))
            and (not bool(更新检查状态.get("已提示", False)))
            and bool(更新检查状态.get("发现新版本", False))
            and (not bool(非游戏菜单开启))
            and (not bool(选歌ESC菜单宿主.is_open()))
            and (not bool(开发调试菜单开启))
            and (not 过渡.是否进行中())
            and 当前场景名 not in ("谱面播放器", "结算")
        ):
            更新检查状态["已提示"] = True
            if _弹窗提示软件更新(
                当前版本号,
                dict(更新检查状态.get("数据") or {}),
            ):
                _退出程序()

        if (not 过渡.是否进行中()) and hasattr(当前场景, "更新"):
            try:
                更新结果 = 当前场景.更新()
            except Exception:
                更新结果 = None
            _处理场景返回结果(更新结果)

        过渡.更新(_执行场景切换)
        入场.更新()

        CPU绘制开始秒 = time.perf_counter()
        上下文["GPU上传脏矩形列表"] = None
        上下文["GPU强制全量上传"] = False
        当前场景.绘制()
        if bool(选歌ESC菜单宿主.is_open()) and str(当前场景名 or "") == "选歌":
            选歌ESC菜单宿主.draw(上下文["屏幕"])
        else:
            _绘制非游戏菜单()
        _绘制开发调试菜单()
        全局点击特效.更新并绘制(上下文["屏幕"])

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
        入场.绘制(上下文["屏幕"])

        _绘制opencv缺失提示(
            屏幕=上下文["屏幕"],
            字体对象=上下文["字体"].get("小字"),
        )
        CPU绘制毫秒 = (time.perf_counter() - CPU绘制开始秒) * 1000.0

        呈现统计 = {}
        if 显示后端 is not None:
            def _绘制GPU背景(后端):
                绘制方法 = getattr(当前场景, "绘制GPU背景", None)
                if callable(绘制方法):
                    绘制方法(后端)

            def _绘制GPU叠加(后端):
                绘制方法 = getattr(当前场景, "绘制GPU叠加", None)
                if callable(绘制方法):
                    绘制方法(后端)

            GPU上传脏矩形列表 = 上下文.get("GPU上传脏矩形列表", None)
            GPU强制全量上传 = bool(上下文.get("GPU强制全量上传", False))
            try:
                if callable(getattr(过渡, "是否进行中", None)) and bool(过渡.是否进行中()):
                    GPU强制全量上传 = True
                if callable(getattr(入场, "是否进行中", None)) and bool(入场.是否进行中()):
                    GPU强制全量上传 = True
            except Exception:
                GPU强制全量上传 = True
            呈现统计 = 显示后端.呈现(
                _绘制GPU背景,
                _绘制GPU叠加,
                上传脏矩形列表=GPU上传脏矩形列表,
                强制全量上传=bool(GPU强制全量上传),
            ) or {}
        else:
            pygame.display.flip()
        帧总毫秒 = (time.perf_counter() - 循环开始秒) * 1000.0
        上下文["主循环最近统计"] = {
            "cpu_draw_ms": float(CPU绘制毫秒),
            "frame_ms": float(帧总毫秒),
        }
        上下文["显示后端最近统计"] = (
            dict(呈现统计) if isinstance(呈现统计, dict) else {}
        )


if __name__ == "__main__":
    主函数()
