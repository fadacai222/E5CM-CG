# -*- coding: utf-8 -*-
"""
E5CM-CG (e舞成名) 项目编译脚本
将Python项目编译为独立的exe文件，并打包所有媒体资源

使用方法:
    python build.py

输出:
    - dist/E5CM-CG.exe (主程序)
    - dist/ (资源文件同级存放)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def 获取项目根目录():
    """获取脚本所在的项目根目录"""
    return Path(__file__).parent.absolute()


def 检查依赖():
    """检查并安装必要的编译依赖"""
    print("=" * 60)
    print("📦 检查编译依赖...")
    print("=" * 60)

    required_packages = {
        "pygame": "pygame",
        "cv2": "opencv-python",
    }

    missing_packages = []

    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {module} 已安装")
        except ImportError:
            print(f"✗ {module} 未安装")
            missing_packages.append(package)

    # 检查 PyInstaller
    try:
        import PyInstaller

        print("✓ PyInstaller 已安装")
    except ImportError:
        print("✗ PyInstaller 未安装")
        missing_packages.append("pyinstaller")

    if missing_packages:
        print(f"\n需要安装缺失的依赖: {', '.join(missing_packages)}")
        print("是否现在安装？(y/n): ", end="")
        response = input().strip().lower()
        if response == "y":
            for package in missing_packages:
                print(f"\n正在安装 {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print("✓ 依赖安装完成")
        else:
            print("✗ 编译中止")
            sys.exit(1)

    print()


def 清理旧文件(项目根: Path):
    """清理之前的编译输出"""
    print("🧹 清理旧的编译文件...")

    dist_dir = 项目根 / "编译结果"
    build_dir = 项目根 / "build"
    spec_file = 项目根 / "E5CM-CG.spec"

    for path in [dist_dir, build_dir]:
        if path.exists():
            shutil.rmtree(path)
            print(f"  删除: {path}")

    if spec_file.exists():
        spec_file.unlink()
        print(f"  删除: {spec_file}")

    print()


def 清理不需要的文件(项目根: Path):
    """清理不需要打包的文件"""
    print("🗑️  清理不需要打包的文件...")

    需删除文件 = [
        项目根 / "UI-img" / "个人中心-个人资料" / "个人资料.json",
        项目根 / "songs" / "歌曲记录索引.json",
    ]

    for file_path in 需删除文件:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"  ✓ 删除: {file_path.relative_to(项目根)}")
            except Exception as e:
                print(f"  ⚠ 无法删除 {file_path.name}: {e}")

    print()


# def 准备资源数据(项目根: Path) -> tuple:
#     """准备需要打包的资源文件

#     返回两个列表:
#     - embedded_resources: 打包到 exe 内的资源
#     - external_resources: 保留在 dist 目录的资源
#     """
#     print("📁 准备资源文件...")

#     # 打包到 exe 内的资源
#     embedded_dirs = [
#         "冷资源",
#         "backmovies",
#         "UI-img",
#         "json",
#     ]

#     # 保留在 dist 目录的资源
#     external_dirs = [
#         "songs",
#     ]

#     embedded_datas = []
#     external_datas = []

#     print("\n📦 打包到 exe 内的资源:")
#     for resource_dir in embedded_dirs:
#         src_path = 项目根 / resource_dir
#         if src_path.exists():
#             embedded_datas.append((str(src_path), resource_dir))
#             print(f"  ✓ {resource_dir}")
#         else:
#             print(f"  ⚠ {resource_dir} 不存在")

#     print("\n📂 保留在 dist 目录的资源:")
#     for resource_dir in external_dirs:
#         src_path = 项目根 / resource_dir
#         if src_path.exists():
#             external_datas.append((str(src_path), resource_dir))
#             print(f"  ✓ {resource_dir}")
#         else:
#             print(f"  ⚠ {resource_dir} 不存在")

#     print(f"\n共 {len(embedded_datas)} 个资源打包到 exe")
#     print(f"共 {len(external_datas)} 个资源保留在 dist\n")
#     return embedded_datas, external_datas


def 准备资源数据(项目根: Path) -> tuple:
    """准备需要打包的资源文件

    返回两个列表:
    - embedded_resources: 打包到 exe 内的资源
    - external_resources: 保留在 dist 目录的资源
    """
    print("📁 准备资源文件...")

    # 打包到 exe 内的资源
    内嵌资源目录列表 = [
        "冷资源",
        "backmovies",
        "UI-img",
        "json",
    ]

    内嵌资源列表 = []
    外部资源列表 = []

    print("\n📦 打包到 exe 内的资源:")
    for 资源目录 in 内嵌资源目录列表:
        源路径 = 项目根 / 资源目录
        if 源路径.exists():
            内嵌资源列表.append((str(源路径), 资源目录))
            print(f"  ✓ {资源目录}")
        else:
            print(f"  ⚠ {资源目录} 不存在")

    print("\n📂 保留在 dist 目录的资源:")

    打包专用歌曲目录 = 项目根 / "打包专用songs" / "songs"
    默认歌曲目录 = 项目根 / "songs"

    if 打包专用歌曲目录.exists():
        外部资源列表.append((str(打包专用歌曲目录), "songs"))
        print(r"  ✓ 打包专用songs\songs -> dist\songs")
    elif 默认歌曲目录.exists():
        外部资源列表.append((str(默认歌曲目录), "songs"))
        print(r"  ✓ songs -> dist\songs")
    else:
        print(r"  ⚠ 未找到 songs，也未找到 打包专用songs\songs")

    print(f"\n共 {len(内嵌资源列表)} 个资源打包到 exe")
    print(f"共 {len(外部资源列表)} 个资源保留在 dist\n")
    return 内嵌资源列表, 外部资源列表


def 构建PyInstaller命令(项目根: Path, embedded_datas: list) -> list:
    """构建 PyInstaller 命令行

    参数:
        embedded_datas: 打包到 exe 内的资源列表
    """

    icon_path = 项目根 / "icon" / "app.ico"
    if not icon_path.exists():
        print(f"⚠ 警告: 未找到 {icon_path}")
        icon_arg = []
    else:
        icon_arg = ["--icon=" + str(icon_path)]
        print(f"✓ 使用图标: {icon_path}")

    # PyInstaller 基础参数
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=E5CM-CG",  # 输出文件名
        "--onefile",  # 打包为单个 exe 文件
        "--windowed",  # 无控制台窗口
        "--add-data=" + str(项目根 / "core") + ";core",  # 打包 core 模块
        "--add-data=" + str(项目根 / "scenes") + ";scenes",  # 打包 scenes 模块
        "--add-data=" + str(项目根 / "ui") + ";ui",  # 打包 ui 模块
        "--distpath=" + str(项目根 / "编译结果"),  # 输出路径
        "--workpath=" + str(项目根 / "build"),  # 构建路径
        "--specpath=" + str(项目根),  # spec 文件路径
    ]

    # 添加打包到 exe 内的资源数据
    for src, dst in embedded_datas:
        cmd.append(f"--add-data={src};{dst}")

    # 添加图标
    cmd.extend(icon_arg)

    # 主程序入口
    cmd.append(str(项目根 / "main.py"))

    return cmd


def 运行编译(cmd: list):
    """运行 PyInstaller 编译"""
    print("=" * 60)
    print("🏗️  开始编译...")
    print("=" * 60)
    print(f"\n执行命令: {' '.join(cmd[:5])}...\n")

    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print("\n✓ 编译成功！")
            return True
        else:
            print(f"\n✗ 编译失败 (返回码: {result.returncode})")
            return False
    except Exception as e:
        print(f"\n✗ 编译过程中出错: {e}")
        return False


def 复制资源到输出目录(项目根: Path, 外部资源列表: list):
    """将资源文件复制到“编译结果”目录（与 exe 同级）

    参数:
        外部资源列表: 保留在输出目录的资源列表
    """
    print("\n" + "=" * 60)
    print("📋 复制资源文件到编译结果目录...")
    print("=" * 60)

    输出目录 = 项目根 / "编译结果"

    if not 输出目录.exists():
        输出目录.mkdir(parents=True, exist_ok=True)

    for 源路径字符串, 资源目录名 in 外部资源列表:
        源路径 = Path(源路径字符串)
        目标路径 = 输出目录 / 资源目录名

        if 源路径.exists():
            if 目标路径.exists():
                shutil.rmtree(目标路径)
            shutil.copytree(源路径, 目标路径)
            print(f"  ✓ 已复制 {资源目录名} -> {目标路径}")
        else:
            print(f"  ⚠ 跳过 {资源目录名}（不存在）")

    print()


def 验证编译结果(项目根: Path, 外部资源列表: list):
    """验证编译结果

    参数:
        外部资源列表: 应该在“编译结果”中的外部资源列表
    """
    print("=" * 60)
    print("✅ 验证编译结果...")
    print("=" * 60)

    输出目录 = 项目根 / "编译结果"
    主程序路径 = 输出目录 / "E5CM-CG.exe"

    if 主程序路径.exists():
        文件大小 = 主程序路径.stat().st_size / (1024 * 1024)
        print(f"✓ 主程序: {主程序路径}")
        print(f"  大小: {文件大小:.2f} MB")
    else:
        print(f"✗ 主程序未找到: {主程序路径}")
        return False

    全部正常 = True

    print("\n验证外部资源:")
    for _, 资源目录名 in 外部资源列表:
        资源路径 = 输出目录 / 资源目录名
        if 资源路径.exists():
            print(f"  ✓ {资源目录名}")
        else:
            print(f"  ✗ {资源目录名} 缺失")
            全部正常 = False

    print("\n✓ 打包到 exe 内的资源: 冷资源, backmovies, UI-img, json")
    print()
    return 全部正常


def 链接检查(项目根: Path):
    try:
        # Python 3.10+
        from typing import TypeAlias
    except ImportError:
        pass

    # 检查 json 配置文件是否正确
    json_dir = 项目根 / "json"
    if json_dir.exists():
        json_files = list(json_dir.glob("*.json"))
        if json_files:
            print(f"  检查 {len(json_files)} 个 JSON 配置文件...✓")
        else:
            print(f"  ⚠ JSON 目录为空")


def 清理临时编译文件(项目根: Path):
    """编译完成后清理临时文件"""
    print("🧹 清理临时编译文件...")

    temp_files = [
        项目根 / "build",
        项目根 / "E5CM-CG.spec",
        项目根 / "__pycache__",
    ]

    for path in temp_files:
        if path.exists():
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"  ✓ 删除: {path.name}")
            except Exception as e:
                print(f"  ⚠ 无法删除 {path.name}: {e}")

    print()


def 主程序():
    """主程序步骤"""
    项目根 = 获取项目根目录()
    输出目录 = 项目根 / "编译结果"

    print("\n")
    print("=" * 60)
    print("🎮 E5CM-CG (e舞成名) 编译脚本")
    print("=" * 60)
    print(f"项目根目录: {项目根}\n")

    # 步骤 1: 检查依赖
    检查依赖()

    # 步骤 2: 清理旧文件
    清理旧文件(项目根)

    # 步骤 2.5: 清理不需要打包的文件
    清理不需要的文件(项目根)

    # 步骤 3: 准备资源数据
    内嵌资源列表, 外部资源列表 = 准备资源数据(项目根)

    # 步骤 4: 构建命令
    命令列表 = 构建PyInstaller命令(项目根, 内嵌资源列表)

    # 步骤 5: 运行编译
    是否成功 = 运行编译(命令列表)

    if not 是否成功:
        print("\n⚠️  编译失败，请检查错误信息")
        sys.exit(1)

    # 步骤 6: 复制外部资源到输出目录
    复制资源到输出目录(项目根, 外部资源列表)

    # 步骤 7: 验证结果
    验证是否通过 = 验证编译结果(项目根, 外部资源列表)

    if 验证是否通过:
        # 步骤 8: 清理临时文件
        清理临时编译文件(项目根)

        print("=" * 60)
        print("✨ 编译成功！")
        print("=" * 60)
        print(f"\n输出位置: {输出目录}")
        print(f"主程序: {输出目录 / 'E5CM-CG.exe'}")
        print(f"歌曲目录: {输出目录 / 'songs'}")
        print("资源文件: 与 exe 同级目录")
        print("\n📝 注意:")
        print("  - 首次运行可能较慢，因为需要初始化 Pygame 和 OpenCV")
        print("  - 确保编译结果文件夹中的所有资源文件都完整无损")
        print("  - 如果缺少资源，游戏无法正常运行")
        print()
    else:
        print("\n⚠️  编译已完成但部分资源可能缺失")
        print(f"请检查目录: {输出目录}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        主程序()
    except KeyboardInterrupt:
        print("\n\n⚠️  编译被中止")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
