import subprocess
import sys
import os
import platform

# 定义要卸载的库列表
libraries = [
    'python-dateutil',
    'pandas',
    'chardet',
    'tqdm',
    'requests'
]

def ensure_pip_installed():
    """确保pip已安装，如未安装则进入自动安装"""
    # 检查pip是否可用
    pip_check = subprocess.run(
        [sys.executable, '-m', 'pip', '--version'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    if pip_check.returncode == 0:
        return True
    
    print("未检测到pip，正在尝试安装pip...")
    
    # 方法1: 使用ensurepip（Python内置模块）
    ensurepip = subprocess.run(
        [sys.executable, '-m', 'ensurepip', '--upgrade'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    
    if ensurepip.returncode == 0:
        print("pip安装成功（通过ensurepip）")
        return True
    
    # 方法2: 使用get-pip.py（避免导入urllib）
    print("尝试通过下载get-pip.py安装...")
    
    # 根据系统选择合适的下载命令
    if platform.system() == "Windows":
        download_cmd = ['powershell', '-Command', 
                       f'(New-Object System.Net.WebClient).DownloadFile("https://bootstrap.pypa.io/get-pip.py", "get-pip.py")']
    else:
        download_cmd = ['curl', '-sS', 'https://bootstrap.pypa.io/get-pip.py', '-o', 'get-pip.py']
    
    # 下载get-pip.py
    download = subprocess.run(download_cmd, stderr=subprocess.PIPE)
    if download.returncode != 0:
        print(f"下载get-pip.py失败: {download.stderr.decode()}")
        return False
    
    # 安装pip
    install = subprocess.run(
        [sys.executable, 'get-pip.py', '-i', 'https://mirrors.aliyun.com/pypi/simple/'],
        stderr=subprocess.PIPE
    )
    
    if install.returncode == 0:
        print("pip安装成功（通过get-pip.py）")
        # 清理下载的文件
        if os.path.exists("get-pip.py"):
            os.remove("get-pip.py")
        return True
    
    print(f"pip安装失败: {install.stderr.decode()}")
    return False

def get_pip_command():
    """获取适用于当前环境的pip命令"""
    # 在Windows上直接使用pip.exe
    if platform.system() == "Windows":
        pip_path = os.path.join(os.path.dirname(sys.executable), "Scripts", "pip.exe")
        if os.path.exists(pip_path):
            return [pip_path]
    
    # 非Windows系统或未找到pip.exe时使用Python模块调用方式
    return [sys.executable, "-m", "pip"]

def main():
    # 确保pip可用
    if not ensure_pip_installed():
        print("错误：无法安装pip，请手动安装后再运行此脚本")
        return
    
    pip_cmd = get_pip_command()
    
    # 卸载库
    for library in libraries:
        try:
            # 执行卸载命令
            result = subprocess.run(
                pip_cmd + ["uninstall", library, "-y"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 检查卸载结果
            if result.returncode == 0:
                if "Successfully uninstalled" in result.stdout:
                    print(f"✅ {library} 卸载成功")
                elif "not installed" in result.stdout:
                    print(f"⚠️ {library} 未安装，跳过")
                else:
                    print(f"⚠️ {library} 卸载完成，但输出信息不明确")
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                print(f"❌ 卸载 {library} 失败: {error_msg[:200]}")
                
        except Exception as e:
            print(f"❌ 卸载 {library} 时发生异常: {str(e)}")

if __name__ == "__main__":
    main()