# CheckMiss 依赖库一键卸载工具
# 用途：当 CheckMiss 运行时出现第三方依赖库异常，可先运行本脚本卸载相关依赖，
#      然后重新运行 CheckMiss 主程序，让主程序重新检测并安装依赖。
#
# 注意：
# 1. 本脚本只卸载 CheckMiss 使用的第三方依赖库。
# 2. 不会卸载 Python、pip、setuptools，也不会删除任何业务数据文件。
# 3. 卸载完成后，请关闭窗口，再重新运行 CheckMiss 主程序。

import subprocess
import sys


DEPENDENCIES = [
    "pandas",
    "python-dateutil",
    "chardet",
    "requests",
    "prettytable",
    "tqdm",
    "packaging",
]


def print_header():
    print("=" * 70)
    print("CheckMiss 依赖库一键卸载工具")
    print("=" * 70)
    print(f"当前 Python：{sys.executable}")
    print("\n将卸载以下依赖库：")
    for lib in DEPENDENCIES:
        print(f"  - {lib}")
    print("\n不会卸载 Python、pip、setuptools，也不会删除任何数据文件。")
    print("卸载完成后，请重新运行 CheckMiss 主程序，让它重新检测并安装依赖。")
    print("=" * 70)


def uninstall_dependency(package_name):
    print(f"\n[处理] 正在卸载：{package_name}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        output = result.stdout.strip()
        if output:
            print(output)
        return result.returncode == 0
    except Exception as exc:
        print(f"[错误] {package_name} 卸载异常：{exc}")
        return False


def main():
    print_header()
    confirm = input("\n确认卸载以上依赖库？请输入 YES 继续，其他任意输入取消：").strip()
    if confirm != "YES":
        print("\n已取消卸载。")
        input("按回车键退出...")
        return

    failed = []
    for package_name in DEPENDENCIES:
        ok = uninstall_dependency(package_name)
        if not ok:
            failed.append(package_name)

    print("\n" + "=" * 70)
    if failed:
        print("[提示] 以下依赖库可能未完全卸载：")
        for package_name in failed:
            print(f"  - {package_name}")
        print("\n如反复失败，可尝试：")
        print("1. 以管理员身份运行本脚本；")
        print("2. 手动执行：python -m pip uninstall 库名")
    else:
        print("[完成] CheckMiss 相关依赖库卸载流程已完成。")

    print("\n下一步：关闭当前窗口，重新运行 CheckMiss 主程序。")
    print("主程序会重新检测依赖，并提示选择安装源进行安装。")
    print("=" * 70)
    input("按回车键退出...")


if __name__ == "__main__":
    main()
