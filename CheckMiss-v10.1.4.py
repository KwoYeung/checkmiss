# ██╗      ██████╗ ██╗   ██╗
# ██║     ██╔════╝ ╚██╗ ██╔╝
# ██║     ██║  ███╗ ╚████╔╝
# ██║     ██║   ██║  ╚██╔╝
# ███████╗╚██████╔╝   ██║
# ╚══════╝ ╚═════╝    ╚═╝
# CheckMiss - Infectious Disease Report Checker
# Author & Maintainer: YueXiuCDC-LGY
# License: MIT
# Python开源免费，切勿相信非官方安装渠道。
# 致谢：本项目在旧版漏报调查程序思路基础上持续迭代完善。
import sys
import subprocess
import importlib
from pathlib import Path
import datetime
import traceback
import re
import os
import shlex
import unicodedata
import shutil
# 将运行目录固定为脚本所在目录，确保在VS Code、终端或双击运行时都能正确读取同目录文件。
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 全局版本变量
current_version = "v10.1.3"
latest_version = "未知"

# ===================== 跨平台路径锚定 =====================
# 获取脚本所在目录（兼容Mac/Win，自动处理路径分隔符）
SCRIPT_DIR = Path(sys.argv[0]).parent.absolute()  # 脚本文件夹绝对路径
# 定义核心文件路径（锚定脚本目录，自动适配Mac/Win路径分隔符）
CLINIC_LOG_FILE = SCRIPT_DIR / "医院门诊日志.csv"
FILTERED_LOG_FILE = SCRIPT_DIR / "医院门诊日志（筛选后）.csv"
REPORT_CARD_FILE = SCRIPT_DIR / "大疫情网报卡.csv"
# 输出文件路径（锚定脚本目录）
EXPORT_TXT = SCRIPT_DIR / "报卡分析报告.txt"
EXPORT_OVER_CANCEL = SCRIPT_DIR / "医院门诊日志（疑似过度抵消）.csv"
EXPORT_REPORTED = SCRIPT_DIR / "结果(已报告卡).csv"
EXPORT_MISSING = SCRIPT_DIR / "结果(可疑漏报卡).csv"
EXPORT_DUPLICATE = SCRIPT_DIR / "结果(一卡多匹).csv"

# ===================== 颜色美化类 =====================
class Color:
    """终端颜色美化常量"""
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    PURPLE = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[37m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # 快捷提示样式
    INFO = f"{BLUE}{BOLD}[信息]{RESET}"
    SUCCESS = f"{GREEN}{BOLD}[成功]{RESET}"
    WARNING = f"{YELLOW}{BOLD}[警告]{RESET}"
    ERROR = f"{RED}{BOLD}[错误]{RESET}"
    PROCESS = f"{PURPLE}{BOLD}[进程]{RESET}"

# ===================== 依赖库检查/安装函数 =====================
def check_version(lib_name):
    """返回指定依赖库的已安装版本；未安装时返回None。"""
    package_to_module = {
        'python-dateutil': 'dateutil',
        'pandas': 'pandas',
        'chardet': 'chardet',
        'tqdm': 'tqdm',
        'requests': 'requests',
        'prettytable': 'prettytable',
        'packaging': 'packaging'
    }
    module_name = package_to_module.get(lib_name, lib_name)
    try:
        module = importlib.import_module(module_name)
        return module.__version__
    except ModuleNotFoundError:
        return None

def install_from_source(lib, source):
    """使用用户选择的 PyPI 镜像源安装缺失依赖。"""
    source_mapping = {
        "Python官方源": "https://pypi.python.org/simple",
        "清华大学源": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "中国科技大学源": "https://pypi.mirrors.ustc.edu.cn/simple/",
        "阿里云源": "https://mirrors.aliyun.com/pypi/simple/",
        "腾讯云源": "https://mirror.ccs.tencentyun.com/pypi/simple",
        "华为云源": "https://mirrors.huaweicloud.com/repository/pypi/simple"
    }
    source_url = source_mapping.get(source)
    if source_url:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-i", source_url, lib],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

def install_libraries(libs):
    """启动时检查运行所需依赖；缺失时引导用户选择镜像源安装。"""
    sources = {
        "1": "Python官方源",
        "2": "清华大学源",
        "3": "中国科技大学源",
        "4": "阿里云源",
        "5": "腾讯云源",
        "6": "华为云源",
        "7": "退出程序"
    }

    if 'tqdm' not in libs:
        libs = ['tqdm'] + libs

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"""===============================================
[系统信息] Python 版本：{python_version}
===============================================""")
    print(f"{Color.INFO} 开始检测所需库...\n")

    installed = {lib: check_version(lib) for lib in libs}
    missing = [lib for lib in libs if installed[lib] is None]

    if not missing:
        print(f"{Color.SUCCESS} 所有库已安装：")
        key_dependencies = ['pandas', 'python-dateutil', 'chardet', 'requests', 'prettytable', 'packaging']
        for lib in key_dependencies:
            print(f" - {lib}: {installed[lib]}")
        return True

    print(f"{Color.WARNING} 以下库未找到：{', '.join(missing)}")

    while True:
        print("""\n===========================================
* 均为公开源，请选择并开始安装依赖库（必装）
* 因网络环境导致失败请换源尝试
* 均无法正常安装可使用wifi尝试
===========================================
请选择安装源或退出（输入对应数字）:""")
        for key, source in sources.items():
            print(f"{key}. {source}")

        choice = input("输入步骤（1/2/3/4/5/6/7）：").strip()

        if choice == "7":
            print(f"{Color.INFO} 安装已取消，程序退出")
            sys.exit(0)

        if choice not in sources:
            print(f"{Color.ERROR} 输入无效，请重新输入")
            continue

        selected_source = sources[choice]
        if selected_source == "退出程序":
            sys.exit(0)

        print(f"\n{Color.PROCESS} 使用源：{selected_source}")

        try:
            import importlib.util
            tqdm_spec = importlib.util.find_spec("tqdm")
        except AttributeError:
            print(f"{Color.ERROR} 出现错误：无法使用 importlib.util 查找模块，请检查 Python 环境。")
            continue

        if tqdm_spec is None and 'tqdm' in missing:
            try:
                print(f"{Color.PROCESS} 优先安装 tqdm")
                install_from_source('tqdm', selected_source)
                print(f"{Color.SUCCESS} tqdm 已安装")
            except subprocess.CalledProcessError as e:
                print(f"{Color.ERROR} tqdm 安装失败：{e.stdout}。可能是网络问题，请重新选择源进行安装。")
                continue

        try:
            import importlib.util
            tqdm_spec = importlib.util.find_spec("tqdm")
        except AttributeError:
            print(f"{Color.ERROR} 出现错误：无法使用 importlib.util 查找模块，请检查 Python 环境。")
            continue

        if tqdm_spec is not None:
            from tqdm import tqdm
            progress_bar = tqdm(missing, desc="安装进度", unit="库", dynamic_ncols=True)
        else:
            print(f"{Color.ERROR} tqdm未安装")
            progress_bar = missing

        for lib in progress_bar:
            if isinstance(progress_bar, tqdm):
                progress_bar.set_postfix({"当前库": lib})
            try:
                install_from_source(lib, selected_source)
                installed[lib] = check_version(lib)
                if isinstance(progress_bar, tqdm):
                    progress_bar.set_postfix({"状态": f"成功({installed[lib]})"})
                else:
                    print(f"{Color.SUCCESS} {lib} 版本：{installed[lib]}")
            except subprocess.CalledProcessError as e:
                if isinstance(progress_bar, tqdm):
                    progress_bar.set_postfix({"状态": "失败"})
                print(f"{Color.ERROR} {lib} 错误信息：{e.stdout}。可能是网络问题，请重新选择源进行安装。")

        missing_after = [lib for lib in libs if installed[lib] is None]
        if not missing_after:
            print(f"\n{Color.SUCCESS} 所有依赖库安装成功！")
            print(f"{Color.INFO} 已安装库版本：")
            key_dependencies = ['pandas', 'python-dateutil', 'chardet', 'requests', 'prettytable', 'packaging']
            for lib in key_dependencies:
                print(f" - {lib}: {installed[lib]}")
            return True
        else:
            print(f"\n{Color.WARNING} 以下库安装失败：{', '.join(missing_after)}，请重新选择源进行安装。")

# ===================== 版本检查函数 =====================
def check_update():
    """检查Gitee Release版本，并显示Python与依赖库环境信息。"""
    global latest_version
    
    try:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        required_libs = ['pandas', 'chardet', 'python-dateutil', 'requests', 'tqdm', 'prettytable', 'packaging']
        installed = {lib: check_version(lib) for lib in required_libs}
        lib_status = "\n".join([f"  ├─ {lib}: {ver if ver else f'{Color.RED}未安装{Color.RESET}'}" for lib, ver in installed.items()])
        lib_status += f"\n {Color.SUCCESS}{Color.BOLD}{Color.GREEN}检查完成{Color.RESET}"

        import requests
        url = "https://gitee.com/api/v5/repos/nagoyaaaaa/checkmiss/releases/latest"
        headers = {
            "User-Agent": f"CheckMiss/{current_version}"
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        latest_version = data['tag_name']

        print(f"{Color.BLUE}{'━'*60}{Color.RESET}")
        from packaging.version import Version, InvalidVersion
        try:
            has_new_version = Version(latest_version.lstrip("vV")) > Version(current_version.lstrip("vV"))
        except InvalidVersion:
            has_new_version = False
            print(f"{Color.WARNING} 无法识别版本号格式：当前版本={current_version}，仓库版本={latest_version}")

        if has_new_version:
            print(f"{Color.WARNING} 版本更新提醒 🚨")
            print(f"  当前版本：{Color.RED}{current_version}{Color.RESET} | 最新版本：{Color.GREEN}{latest_version}{Color.RESET}")
            print(f"  下载地址：https://gitee.com/nagoyaaaaa/checkmiss/releases")
            print()

            # ===================== 从 Release 下载附件 =====================
            choice = input(f"{Color.INFO} 是否自动下载最新版到当前目录？(y/n)：{Color.RESET}").strip().lower()
            if choice == "y":
                try:
                    # 直接从 API 获取下载地址
                    assets = data.get("assets", [])
                    if len(assets) == 0:
                        print(f"{Color.ERROR} 新版本未上传文件，请手动下载")
                    else:
                        # 取上传的第一个文件
                        file_url = assets[0]["browser_download_url"]
                        file_name = assets[0]["name"]

                        # 下载
                        res = requests.get(file_url, headers=headers, timeout=20)
                        res.raise_for_status()

                        with open(file_name, "wb") as f:
                            f.write(res.content)

                        print(f"{Color.SUCCESS} ✅ 下载成功！")
                        print(f"  已保存：{file_name}")

                except Exception as e:
                    print(f"{Color.ERROR} ❌ 下载失败：{str(e)}")
            # ===========================================================================

        else:
            print(f"{Color.SUCCESS} 版本状态 ✔️")
            print(f"  当前版本：{Color.GREEN}{current_version}{Color.RESET} | 最新版本：{Color.GREEN}{latest_version}{Color.RESET}")
            print(f"  当前已是最新版本！")

        print(f"{Color.BLUE}{'━'*60}{Color.RESET}")
        print(f"{Color.INFO} 系统信息：")
        print(f"  Python 版本：{Color.BOLD}{python_version}{Color.RESET}")
        print(f"{Color.INFO} 依赖库状态：")
        print(lib_status)
        input(f"\n{Color.INFO} 按任意键返回主菜单...")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            latest_version = current_version
            print(f"{Color.BLUE}{'━'*60}{Color.RESET}")
            print(f"{Color.WARNING} 版本检查提示 ⚠️")
            print(f"  当前版本：{Color.GREEN}{current_version}{Color.RESET} | 仓库版本：{Color.GRAY}暂无发布版本{Color.RESET}")
            print(f"{Color.BLUE}{'━'*60}{Color.RESET}")
            print(f"{Color.INFO} 系统信息：")
            print(f"  Python 版本：{Color.BOLD}{python_version}{Color.RESET}")
            print(lib_status)
            input(f"\n{Color.WARNING} 按任意键返回主菜单...")
        else:
            print(f"{Color.ERROR} 版本检查失败：HTTP {e.response.status_code}")
            input(f"\n{Color.INFO} 按任意键返回主菜单...")

    except Exception as e:
        print(f"{Color.ERROR} 检查更新失败：{str(e)}")
        print(f"  原因：无网络 / Gitee 访问超时")
        input(f"\n{Color.INFO} 按任意键返回主菜单...")

# ===================== 解析函数 =====================
def clean_date(date_str):
    """清洗并标准化日期/时间字段；无法解析时返回 pandas.NaT。"""
    try:
        # 处理可能的空字符串或特殊标记
        if pd.isna(date_str) or str(date_str).strip().lower() in ['无', 'none', 'null', '']:
            return pd.NaT
            
        # 尝试多种日期格式解析
        date_formats = [
            '%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日',
            '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
            '%Y年%m月%d日 %H:%M:%S', '%m-%d-%Y', '%d-%m-%Y',
            '%m/%d/%Y', '%d/%m/%Y'
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.datetime.strptime(str(date_str).strip(), fmt)
                if date_obj.time() == datetime.time(0, 0, 0):
                    return date_obj.strftime('%Y-%m-%d')
                else:
                    return date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
        
        # 最后尝试自动解析
        date_obj = parse(str(date_str).strip(), dayfirst=False, yearfirst=True, fuzzy=True)
        if date_obj.time() == datetime.time(0, 0, 0):
            return date_obj.strftime('%Y-%m-%d')
        else:
            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        if not hasattr(clean_date, 'error_samples'):
            clean_date.error_samples = []
        if len(clean_date.error_samples) < 5:
            clean_date.error_samples.append(str(date_str))
        return pd.NaT

def read_data(data_path):
    """读取CSV文件并自动处理编码、分隔符、表头清洗和日期字段清洗。"""
    import pandas as pd
    import chardet
    from pathlib import Path
    import sys

    # ===================== 前置校验：文件合法性 =====================
    # 检查文件是否存在
    if not Path(data_path).exists():
        raise Exception(f"{Color.ERROR} 无法读取文件 {Path(data_path).name}：文件不存在")
    # 检查文件是否为空
    if Path(data_path).stat().st_size == 0:
        raise Exception(f"{Color.ERROR} 无法读取文件 {Path(data_path).name}：文件为空（0字节）")
    
    # 读取原始字节数据（用于编码检测）
    raw_data = b''
    with open(data_path, 'rb') as f:
        raw_data = f.read()
    if not raw_data:
        raise Exception(f"{Color.ERROR} 无法读取文件 {Path(data_path).name}：读取后内容为空")

    # ===================== 编码检测 =====================
    # Windows/Excel导出的CSV可能带BOM；BOM优先级高于chardet，避免UTF-8被误判为GBK。
    if raw_data.startswith(b'\xef\xbb\xbf'):
        detected_encoding = 'utf-8-sig'
    elif raw_data.startswith((b'\xff\xfe', b'\xfe\xff')):
        detected_encoding = 'utf-16'
    else:
        result = chardet.detect(raw_data)
        detected_encoding = result.get('encoding')

    encoding_map = {
        'UTF-8-SIG': 'utf-8-sig',
        'UTF-8': 'utf-8',
        'ASCII': 'utf-8',
        'GB2312': 'gb18030',
        'GBK': 'gb18030',
        'GB18030': 'gb18030',
        'ISO-8859-1': 'gb18030',
        'Windows-1254': 'gb18030',
        'Windows-1252': 'gb18030',
        'cp1252': 'gb18030',
        None: 'gb18030'
    }
    detected_encoding = encoding_map.get(detected_encoding, detected_encoding)

    # 不只依赖一次自动判断：通过官方必需字段验证候选编码的表头。
    known_headers = {
        '姓名', '身份证', '诊断', '就诊时间',
        '患者姓名', '有效证件号', '疾病名称', '报告卡录入时间', '卡片ID'
    }
    candidate_encodings = []
    for candidate in [
        detected_encoding, 'utf-8-sig', 'utf-8', 'gb18030', 'gbk', 'utf-16'
    ]:
        if candidate and candidate not in candidate_encodings:
            candidate_encodings.append(candidate)

    encoding = detected_encoding
    best_header_score = -1
    for candidate in candidate_encodings:
        try:
            header_test = pd.read_csv(
                data_path,
                sep=None,
                engine='python',
                encoding=candidate,
                quotechar='"',
                nrows=0
            )
            cleaned_headers = {
                re.sub(r'[\ufeff\u200b\u200c\u200d\u2060]', '', str(col))
                .replace('\u3000', ' ')
                .replace('\xa0', ' ')
                .strip()
                for col in header_test.columns
            }
            header_score = len(cleaned_headers & known_headers)
            if header_score > best_header_score:
                best_header_score = header_score
                encoding = candidate
            # 门诊或网报文件只要命中其全部关键字段，即可确定编码。
            if (
                {'姓名', '身份证', '诊断', '就诊时间'} <= cleaned_headers
                or {
                    '患者姓名', '有效证件号', '疾病名称',
                    '报告卡录入时间', '卡片ID'
                } <= cleaned_headers
            ):
                encoding = candidate
                break
        except (UnicodeDecodeError, UnicodeError, LookupError):
            continue
        except Exception:
            # 分隔符或坏行问题交由后续正式读取及备用方案处理。
            continue

    # 判断是哪个文件
    fname = str(data_path)
    if "门诊日志" in fname:
        label = "医院门诊日志文件"
    elif "网报卡" in fname:
        label = "大疫情网报卡文件"
    else:
        label = "文件"

    # 安全输出，永远不报错
    try:
        display_sep = sep if sep is not None else ","
    except:
        display_sep = ","

    print(f"{Color.INFO} [{label}] 自动检测分隔符：{repr(display_sep)}，编码：{encoding}")

    # ===================== pandas版本兼容参数配置 =====================
    pd_version = tuple(map(int, pd.__version__.split('.')[:2]))
    # 基础参数（移除low_memory，避免与python引擎冲突）
    read_csv_kwargs = {
        'sep': None,  # 自动检测分隔符
        'engine': 'python',  # 保持python引擎以兼容更多分隔符
        'encoding': encoding,
        'quotechar': '"',
        'skip_blank_lines': True,
        # 移除low_memory（python引擎不支持）
    }
    # 适配pandas 2.0+的坏行处理参数
    if pd_version >= (2, 0):
        read_csv_kwargs['on_bad_lines'] = 'warn'  # 坏行仅警告，不中断
    else:
        read_csv_kwargs['error_bad_lines'] = False  # pandas 2.0以前的坏行处理参数

    # ===================== 统一按文本读取 =====================
    # 本程序后续本来就会将各列转为字符串；从读取阶段统一为文本，
    # 可避免身份证、卡片ID等长数字被转成科学计数法或丢失15位后的精度。
    try:
        # 先仅读取表头，同时验证CSV表头可正常识别。
        header_df = pd.read_csv(
            data_path,
            **read_csv_kwargs,
            nrows=0  # 只读取表头，不读数据
        )
        read_csv_kwargs['dtype'] = str
    except Exception as e:
        print(f"{Color.WARNING} 表头检测失败：{str(e)}")
        read_csv_kwargs['dtype'] = str

    # ===================== 主读取逻辑 =====================
    data = None
    try:
        # 自动检测分隔符
        data = pd.read_csv(data_path, **read_csv_kwargs)
        # 处理仅表头无数据的情况
        if len(data) == 0:
            print(f"{Color.WARNING} 文件 {Path(data_path).name} 仅包含表头，无数据行")
    except Exception as e:
        print(f"{Color.WARNING} 主读取方案失败：{str(e)}，尝试备用编码/分隔符组合")
        # 备用方案：遍历常见编码+分隔符组合
        backup_encodings = ['GBK', 'utf-8', 'utf-8-sig', 'GB18030', 'ISO-8859-1', 'Windows-1252', 'ascii']
        backup_seps = [',', ';', '\t', '|']
        for enc in backup_encodings:
            for sep in backup_seps:
                try:
                    backup_kwargs = read_csv_kwargs.copy()
                    backup_kwargs['encoding'] = enc
                    backup_kwargs['sep'] = sep  # 手动指定分隔符
                    data = pd.read_csv(data_path, **backup_kwargs)
                    print(f"{Color.SUCCESS} 备用方案成功：编码={enc}，分隔符={repr(sep)}")
                    break
                except Exception:
                    continue
            if data is not None:
                break

    # ===================== 最终校验 =====================
    if data is None:
        raise Exception(
            f"{Color.ERROR} 无法读取文件 {Path(data_path).name}，所有编码/分隔符组合均失败\n"
            f"建议检查：1.文件是否为标准CSV 2.列数是否统一 3.是否存在特殊字符/格式错乱"
        )

    # ===================== 数据清洗 =====================
    # 清洗列名：保留官方字段名称，只移除BOM、零宽字符和首尾空白。
    data.columns = [
        re.sub(r'[\ufeff\u200b\u200c\u200d\u2060]', '', str(col))
        .replace('\u3000', ' ')
        .replace('\xa0', ' ')
        .strip()
        for col in data.columns
    ]
    # 转换所有列为字符串类型
    for col in data.columns:
        if data[col].dtype != 'object':
            data[col] = data[col].astype(str)
    data.fillna("无", inplace=True)
    
    # 处理日期列
    time_cols = [COLUMN_MAPPING['clinic']['visit_time'], COLUMN_MAPPING['report']['report_time']]
    for time_col in time_cols:
        if time_col in data.columns:
            data[time_col] = data[time_col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            data[time_col] = data[time_col].apply(clean_date)
            
            invalid_count = data[time_col].isna().sum()
            total_count = len(data)
            if invalid_count > 0:
                print(f"{Color.WARNING} {Path(data_path).name}的{time_col}列存在{invalid_count}/{total_count}条无效日期")
                if hasattr(clean_date, 'error_samples'):
                    print(f"{Color.WARNING} 无法解析的日期示例：{clean_date.error_samples[:5]}")
    
    return data

def select_data(data, output_file):
    """步骤1：清洗门诊诊断文本，提取传染病相关信号，并输出筛选后门诊日志。"""
    required_cols = {COLUMN_MAPPING['clinic']['visit_time'], COLUMN_MAPPING['clinic']['diagnosis']}
    missing_cols = required_cols - set(data.columns)
    if missing_cols:
        raise ValueError(
            f"{Color.ERROR} 缺少关键列：{missing_cols}\n"
            f"{Color.INFO} 当前文件包含的列：{list(data.columns)}\n"
            "请检查文件是否符合格式要求：\n"
            "1. 使用正确的CSV格式\n"
            "2. 列名包含中文标点符号\n"
            "3. 文件编码为UTF-8或GBK"
        )
    raw_data_count = len(data)
    # 在筛选和排序前记录原始门诊CSV行号，便于从分析结果返回原文件核对。
    if "源数据行号" not in data.columns:
        data.insert(0, "源数据行号", data.index + 2)
    print(f"{Color.INFO} 原始数据：{raw_data_count}条，开始清洗诊断列...")

    DELIMITERS = r'[，、；;.。！!？？|#/\\～~()（）「」『』【】［］\[\]﹝﹞〈〉«»‹›,;:："“”‘’\'`´]'
    NUMBER_PATTERN = r'''
        (?:^|[\s,，、；;.。！!？？|#/\\～~()（）])
        \s*
        (?:
            \d+\s*[\.．] |
            [一二三四五六七八九十百千]+\s*[\.．、] |
            [\(（]\s*[\d一二三四五六七八九十百千]+\s*[\)）]
        )
        \s*
    '''

    def clean_diagnosis(text):
        cleaned = re.sub(NUMBER_PATTERN, ',', text, flags=re.VERBOSE)
        cleaned = re.sub(DELIMITERS, ',', cleaned)
        cleaned = re.sub(r'\s+', '', cleaned)
        cleaned = re.sub(r',+', ',', cleaned)
        return cleaned.strip(',')

    data[COLUMN_MAPPING['clinic']['diagnosis']] = (
        data[COLUMN_MAPPING['clinic']['diagnosis']]
        .astype(str)
        .apply(clean_diagnosis)
    )
    print(f"{Color.SUCCESS} ✅ 诊断列自动清洗完成，仅保留逗号分隔")

    # ===================== 门诊诊断初筛词库 =====================
    # 说明：
    # 1. 该词库用于步骤1门诊诊断初筛，目标是尽量提取诊断文本中的传染病相关信号。
    # 2. 结构为“疾病等级 → 病种/诊断组 → 诊断词或正则片段”，便于后续维护和排查。
    # 3. 每个词条按正则片段处理，因此 (?<!禽)流感、非典(?!型) 等写法可以直接使用。
    # 4. 程序会自动把同一等级下的所有词条编译为 disease_levels 正则，用于统计各等级命中数。
    disease_level_terms = {
        "甲类": {
            "鼠疫": ["鼠疫"],
            "霍乱": ["霍乱"],
        },
        "乙类": {
            "新型冠状病毒感染": ["新型冠状病毒感染", "新冠"],
            "传染性非典型肺炎": ["传染性非典型肺炎", "非典(?!型)", "SARS"],
            "艾滋病": ["艾滋病", "HIV", "AIDS", "获得性免疫", "艾滋", "爱滋"],
            "病毒性肝炎/未分型": ["肝炎未分型", "病毒性肝炎", "传染性肝炎"],
            "甲型肝炎": ["甲肝", "甲型肝炎", "甲型病毒性肝炎"],
            "乙型肝炎": ["乙肝", "乙型肝炎", "乙型病毒性肝炎"],
            "丙型肝炎": ["丙肝", "丙型肝炎", "丙型病毒性肝炎"],
            "丁型肝炎": ["丁肝", "丁型肝炎", "丁型病毒性肝炎"],
            "戊型肝炎": ["戊肝", "戊型肝炎", "戊型病毒性肝炎"],
            "脊髓灰质炎": ["脊髓灰质炎病毒", "脊髓灰质炎", "脊灰", "小儿麻痹", "小儿麻痹症"],
            "人感染新亚型流感/禽流感": ["人感染新亚型流感", "禽流感", "(?!.*h1n1)H\\d+N\\d+", "动物源性流感", "欧亚禽类"],
            "麻疹": ["(?<!荨)麻疹"],
            "流行性出血热": ["流行性出血热", "出血热"],
            "狂犬病": ["狂犬病", "狂犬"],
            "流行性乙型脑炎": ["流行性乙型脑炎", "乙脑"],
            "登革热": ["登革热", "登革"],
            "猴痘": ["猴痘"],
            "炭疽": ["炭疽"],
            "痢疾": ["细菌性痢疾", "阿米巴性痢疾", "阿米巴痢疾", "菌痢", "志贺", "阿米巴"],
            "肺结核": ["肺结核", "利福平耐药", "病原学阳性", "病原学阴性", "涂阳", "仅培阳", "肺结核无病原学", "未痰检", "结核性胸膜炎", "胸膜结核", "菌阴"],
            "伤寒/副伤寒": ["伤寒", "副伤寒"],
            "流行性脑脊髓膜炎": ["流行性脑脊髓膜炎", "流脑", "流行性脑脊髓炎", "流行性脑膜炎"],
            "百日咳": ["百日咳"],
            "白喉": ["白喉"],
            "新生儿破伤风": ["新生儿破伤风", "新破"],
            "猩红热": ["猩红热"],
            "布鲁氏菌病": ["布鲁氏菌病", "布病", "布鲁氏菌", "布鲁氏菌感染"],
            "淋病": ["淋病"],
            "梅毒": ["梅毒(?!个人史)"],
            "钩端螺旋体病": ["钩端螺旋体病", "钩体"],
            "血吸虫病": ["血吸虫病"],
            "疟疾": ["疟疾", "三日疟", "恶性疟", "间日疟", "卵形疟", "疟", "诺氏疟", "疟原虫", "疟原虫混合感染"],
            "基孔肯雅热": ["基孔肯雅热", "基孔"],
            "发热伴血小板减少综合征": ["发热伴血小板減少综合征", "新型布尼亚", "布尼亚", "大别班达病毒感染", "大别班达", "SFTS"],
        },
        "丙类": {
            "流行性感冒": ["流行性感冒", "(?<!禽)流感", "(?<!禽)流感病毒", "病毒性流感", "病毒性感冒", "甲流", "乙流", "H1N1"],
            "流行性腮腺炎": ["流行性腮腺炎", "流腮", "痄腮", "炸腮"],
            "风疹": ["风疹"],
            "急性出血性结膜炎": ["急性出血性结膜炎", "急出血", "红眼病", "出血性急性结膜炎"],
            "麻风病": ["麻风病", "麻风"],
            "斑疹伤寒": ["流行性斑疹伤寒", "地方性斑疹伤寒", "斑疹伤寒", "立克次体"],
            "黑热病": ["黑热病", "杜氏利什曼"],
            "包虫病": ["包虫病", "包虫", "棘球蚴病", "棘球蚴", "棘球"],
            "丝虫病": ["丝虫病", "丝虫"],
            "手足口病": ["手足口病", "手足口"],
            "感染性腹泻": [
                "轮状", "札如", "诺如", "沙门", "大肠杆菌", "EPEC", "致泻性弧菌", "弯曲菌", "耶尔森菌",
                "肠腺病毒", "隐孢子虫", "蓝氏贾第鞭毛虫",
                "(?<!非)(?:感染性|细菌性|病毒性|传染性)[^,]{0,10}(?:腹泻|胃肠炎|肠炎|肠道)",
                "(?:腹泻|胃肠炎|肠炎|肠道)[^,]{0,10}(?<!非)(?:感染性|细菌性|病毒性|传染性)",
            ],
        },
        "需要关注的其他传染病": {
            "中东呼吸综合征": ["中东呼吸综合征", "MERS"],
            "埃博拉出血热": ["埃博拉出血热", "埃博拉"],
            "黄热病": ["黄热病"],
            "裂谷热": ["裂谷热"],
            "西尼罗热": ["西尼罗热"],
            "拉沙热": ["拉沙热"],
            "马尔堡病": ["马尔堡"],
            "寨卡病毒病": ["寨卡"],
            "森林脑炎": ["森林脑炎"],
            "儿童不明原因急性肝炎": ["儿童不明原因急性肝炎"],
            "不明原因肺炎": ["不明原因肺炎"],
            "水痘": ["水痘"],
            "恙虫病": ["恙虫病", "恙虫"],
            "肝吸虫病": ["肝吸虫病", "肝吸虫", "华支睾"],
            "尖锐湿疣": ["尖锐湿疣", "湿疣", "外阴湿疣", "肛周湿疣", "生殖器湿疣"],
            "生殖器疱疹": ["生殖器疱疹", "外阴疱疹", "肛周疱疹"],
            "生殖道沙眼衣原体": ["生殖道沙眼衣原体", "生殖道衣原体", "沙眼衣原体生殖道"],
        },
    }

    def compile_level_terms(level_terms):
        disease_levels_compiled = {}
        for level, disease_groups in level_terms.items():
            terms = [
                term
                for term_list in disease_groups.values()
                for term in term_list
            ]
            disease_levels_compiled[level] = re.compile(
                "|".join(terms),
                re.UNICODE | re.VERBOSE | re.IGNORECASE
            )
        return disease_levels_compiled

    disease_levels = compile_level_terms(disease_level_terms)

    # ===================== 初筛排除词库 =====================
    # 排除词库用于抵消明确不应纳入传染病初筛的诊断表达，
    # 例如陈旧性病史、携带者、个人史、非目标疾病名称等。
    exclude_pattern = re.compile(r"""
        陈旧性肺结核|
        乙[^,]*?携带者|
        肝硬化失代偿期|
        肝炎恢复期|
        乙肝.*失代偿期|
        乙型肝炎.*失代偿期|
        肝炎.*失代偿期|
        热淋病|气淋病|尿淋病|石淋病|血淋病|劳淋病|
        荨麻疹|
        脊[^,]*?灰[^,]*?后遗症|
        流感嗜血杆菌|副流感病毒|
        类百日咳综合征|类白喉综合征|
        梅毒史|梅毒个人史
    """, re.UNICODE | re.VERBOSE | re.IGNORECASE)

    level_columns = [f"{level}匹配" for level in disease_levels.keys()]
    data[level_columns] = 0
    data["排除匹配"] = 0
    data["疾病等级"] = ""
    data["匹配字段"] = ""
    data["排除字段"] = ""

    from tqdm import tqdm
    for idx, row in tqdm(data.iterrows(), total=len(data), desc="疾病匹配"):
        diagnosis = row[COLUMN_MAPPING['clinic']['diagnosis']]
        current_levels = []
        matched_terms = []

        # 按疾病等级词库统计诊断文本中的传染病相关命中项。
        for level, pattern in disease_levels.items():
            matches = pattern.findall(diagnosis)
            match_count = len(matches)
            if match_count > 0:
                data.loc[idx, f"{level}匹配"] = match_count
                current_levels.append(level)
                matched_terms.extend(matches)
        data.loc[idx, "疾病等级"] = "、".join(current_levels) if current_levels else ""
        data.loc[idx, "匹配字段"] = "，".join(list(set(matched_terms))) if matched_terms else ""

        # 匹配可抵消传染病信号的排除表达。
        exclude_matches = exclude_pattern.findall(diagnosis)
        unique_excludes = list(set(exclude_matches))
        data.loc[idx, "排除字段"] = "，".join(unique_excludes) if unique_excludes else ""
        # “排除字段”保留去重结果，方便阅读；“排除匹配”按原始出现次数计数，
        # 与甲/乙/丙类匹配数保持一致，便于人工理解“匹配-排除”的口径。
        data.loc[idx, "排除匹配"] = len(exclude_matches)

    # ===================== 有效信号计算：匹配词与排除词包含抵消 =====================
    # 规则：若某个匹配词被任一排除表达完整包含，则认为该匹配词在本条诊断中被抵消。
    # 示例：“陈旧性肺结核”中的“肺结核”会被“陈旧性肺结核”抵消。
    def calculate_final_match(row):
        matched_text = str(row["匹配字段"])
        exclude_text = str(row["排除字段"])
        
        matched_list = [i.strip() for i in matched_text.split("，") if i.strip()]
        exclude_list = [i.strip() for i in exclude_text.split("，") if i.strip()]
        
        valid_terms = []
        for term in matched_list:
            keep = True
            for exc in exclude_list:
                if term in exc:  # 匹配词 被 排除词 包含 → 抵消
                    keep = False
                    break
            if keep:
                valid_terms.append(term)
        return len(valid_terms)

    # 计算最终有效匹配数
    data["门诊诊断有效信号数"] = data.apply(calculate_final_match, axis=1)
    data["疑似过度抵消提示"] = ""
    over_cancel_mask = (
        data["匹配字段"].fillna("").astype(str).str.strip().ne("")
        & data["排除字段"].fillna("").astype(str).str.strip().ne("")
        & (data["门诊诊断有效信号数"] == 0)
    )
    data.loc[over_cancel_mask, "疑似过度抵消提示"] = (
        "匹配字段被排除字段完全抵消，建议人工复核是否存在同病种独立诊断；"
        "如确认误抵消，可维护排除正则或匹配正则"
    )

    # 单独输出疑似过度抵消记录。它们不会进入“筛选后”文件，因此必须另表提示。
    over_cancel_data = data[over_cancel_mask].copy()
    over_cancel_data = over_cancel_data.loc[:, ~over_cancel_data.columns.str.contains('^Unnamed')]
    over_cancel_data.to_csv(EXPORT_OVER_CANCEL, index=False, encoding='utf-8-sig', chunksize=1000)

    data_selected = data[data["门诊诊断有效信号数"] >= 1].copy()

    # 输出初筛结果及诊断初筛统计。
    filtered_count = len(data_selected)
    disease_distribution = data_selected[level_columns].sum().to_dict()
    print(f"{Color.INFO} 🔍 筛选结果：{filtered_count}条有效记录")
    print(f"{Color.INFO} 🧭 疑似过度抵消记录：{len(over_cancel_data)}条，保存至 {EXPORT_OVER_CANCEL.resolve()}")

    data_selected = data_selected.sort_values(COLUMN_MAPPING['clinic']['visit_time']).reset_index(drop=True)
    data_selected = data_selected.loc[:, ~data_selected.columns.str.contains('^Unnamed')]
    data_selected.to_csv(output_file, index=False, encoding='utf-8', chunksize=1000)
    print(f"{Color.SUCCESS} ✅ 步骤1完成：初筛结果保存至 {output_file.resolve()}")

    return raw_data_count, filtered_count, disease_distribution

def match_two_database(data_path1, data_path2, data1=None, data2=None):
    """步骤2前半段：按姓名和证件号匹配门诊记录与大疫情网报卡，生成身份候选卡池。"""
    # 已在文件选择阶段读取并验证时直接复用，避免大文件重复读取。
    if data1 is None:
        data1 = read_data(data_path1)
    if data2 is None:
        data2 = read_data(data_path2)
    
    if len(data1) == 0:
        raise Exception(f"{Color.ERROR} 门诊日志文件 {data_path1.name} 仅含表头无数据，无法匹配")
    if len(data2) == 0:
        raise Exception(f"{Color.ERROR} 网报卡文件 {data_path2.name} 仅含表头无数据，无法匹配")
    
    required_clinic_cols = {
        COLUMN_MAPPING['clinic']['name'],
        COLUMN_MAPPING['clinic']['id'],
        COLUMN_MAPPING['clinic']['diagnosis'],
        COLUMN_MAPPING['clinic']['visit_time']
    }
    required_report_cols = {
        COLUMN_MAPPING['report']['name'],
        COLUMN_MAPPING['report']['id'],
        COLUMN_MAPPING['report']['disease'],
        COLUMN_MAPPING['report']['report_time'],
        COLUMN_MAPPING['report']['card_id']
    }
    missing_clinic_cols = required_clinic_cols - set(data1.columns)
    missing_report_cols = required_report_cols - set(data2.columns)
    if missing_clinic_cols:
        raise ValueError(f"{Color.ERROR} 医院门诊日志缺少必要列：{missing_clinic_cols}")
    if missing_report_cols:
        raise ValueError(f"{Color.ERROR} 大疫情网报卡缺少必要列：{missing_report_cols}")

    # 为每条筛选后门诊记录生成程序内部关联号，便于在多个输出文件之间追踪同一条记录。
    # 该编号仅用于本次程序输出，不等同于医院院内业务记录号。
    data1 = data1.reset_index(drop=True)
    run_date = datetime.datetime.now().strftime("%Y%m%d")
    # 兼容旧版本生成、尚未包含原始行号的筛选文件。
    if "源数据行号" not in data1.columns:
        data1.insert(0, "源数据行号", data1.index + 2)
    data1.insert(
        0,
        "程序关联号",
        [f"CM-{run_date}-{i:06d}" for i in range(1, len(data1) + 1)]
    )

    # 原始姓名和证件号不覆盖；以下清洗列只用于程序内部匹配。
    clinic_name_key = "__门诊姓名清洗"
    clinic_id_key = "__门诊证件号清洗"
    report_name_key = "__网报姓名清洗"
    report_name_compat_key = "__网报姓名后缀兼容"
    report_id_key = "__网报证件号清洗"

    def clean_match_name(name):
        # 仅用于程序内部匹配：统一全角/半角、大小写、空白和不可见字符。
        # 不覆盖原始姓名列，避免影响用户回查原始数据。
        text = "" if pd.isna(name) else str(name)
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]', '', text)
        text = re.sub(r'\s+', '', text)
        return text.strip().upper()

    data1[clinic_name_key] = data1[COLUMN_MAPPING['clinic']['name']].apply(clean_match_name)
    data1[clinic_id_key] = (
        data1[COLUMN_MAPPING['clinic']['id']]
        .astype(str).str.replace(r'\.0$', '', regex=True)
        .str.replace(r'[^\dA-Za-z]', '', regex=True).str.upper()
    )
    data2[report_name_key] = data2[COLUMN_MAPPING['report']['name']].apply(clean_match_name)
    data2[report_id_key] = (
        data2[COLUMN_MAPPING['report']['id']]
        .astype(str).str.replace(r'\.0$', '', regex=True)
        .str.replace(r'[^\dA-Za-z号]', '', regex=True)
        .str.replace(r'号', '', regex=True).str.upper()
    )

    def remove_chinese_name_suffix(name):
        # 仅处理“至少两个纯中文字符＋一个英文字母”的网报姓名。
        # 外国人姓名、拼音姓名及中英文混合姓名均保持不变。
        match = re.fullmatch(r'([\u3400-\u9FFF]{2,})[A-Z]', str(name))
        return match.group(1) if match else str(name)

    data2[report_name_compat_key] = data2[report_name_key].apply(remove_chinese_name_suffix)
    
    # 包含卡片ID列
    data2 = data2[[
        COLUMN_MAPPING['report']['name'], 
        COLUMN_MAPPING['report']['report_time'],
        COLUMN_MAPPING['report']['disease'], 
        COLUMN_MAPPING['report']['id'],
        COLUMN_MAPPING['report']['card_id'],
        report_name_key,
        report_name_compat_key,
        report_id_key
    ]].sort_values(COLUMN_MAPPING['report']['report_time']).reset_index(drop=True)

    print(f"{Color.INFO} 数据合并中...")

    # 第一级：清洗后的姓名＋证件号完全匹配。
    exact_match = data1.merge(
        data2,
        how='inner',
        left_on=[clinic_name_key, clinic_id_key],
        right_on=[report_name_key, report_id_key]
    )
    exact_match["姓名匹配方式"] = "完全匹配"

    # 第二级：中文姓名后缀兼容作为补充候选。
    # 同一门诊记录即使已经完全匹配到历史卡，也要继续纳入“姓名+a/A/B/C...”卡，
    # 否则会漏掉同一患者不同病程在大疫情网中使用后缀区分的当天报卡。
    suffix_match = data1.merge(
        data2,
        how='inner',
        left_on=[clinic_name_key, clinic_id_key],
        right_on=[report_name_compat_key, report_id_key]
    )
    suffix_match["姓名匹配方式"] = "中文姓名后缀兼容"

    data_match_candidates = pd.concat(
        [exact_match, suffix_match],
        ignore_index=True,
        sort=False
    )
    if len(data_match_candidates) > 0:
        # 同一张卡可能同时满足完全匹配和后缀兼容匹配，优先保留“完全匹配”的标记。
        data_match_candidates["__姓名匹配优先级"] = data_match_candidates["姓名匹配方式"].map({
            "完全匹配": 0,
            "中文姓名后缀兼容": 1
        }).fillna(9)
        data_match_candidates = (
            data_match_candidates
            .sort_values(["程序关联号", COLUMN_MAPPING['report']['card_id'], "__姓名匹配优先级"])
            .drop_duplicates(["程序关联号", COLUMN_MAPPING['report']['card_id']], keep="first")
            .drop(columns="__姓名匹配优先级")
        )

    # 两级均未匹配的门诊记录仍保留，用于输出可疑漏报。
    matched_program_ids = set(data_match_candidates["程序关联号"]) if len(data_match_candidates) > 0 else set()
    no_match = data1[~data1["程序关联号"].isin(matched_program_ids)].copy()
    for report_col in [
        COLUMN_MAPPING['report']['name'],
        COLUMN_MAPPING['report']['report_time'],
        COLUMN_MAPPING['report']['disease'],
        COLUMN_MAPPING['report']['id'],
        COLUMN_MAPPING['report']['card_id']
    ]:
        no_match[report_col] = pd.NA
    no_match["姓名匹配方式"] = "未匹配"

    data_match = pd.concat(
        [data_match_candidates, no_match],
        ignore_index=True,
        sort=False
    )
    helper_columns = [
        clinic_name_key, clinic_id_key, report_name_key,
        report_name_compat_key, report_id_key
    ]
    data_match.drop(
        columns=[col for col in helper_columns if col in data_match.columns],
        inplace=True
    )
    data_match = data_match.loc[:, ~data_match.columns.str.contains('^Unnamed')]
    data_match = data_match.reset_index(drop=True)
    return data_match


# ===================== 候选卡多层判定配置 =====================
# 这里只用于候选卡关联、排序和复诊期限判断，不替换步骤1的赋值匹配与排除逻辑。
# 每条诊断可同时获得多个标签，不强制归为唯一标准病种。
# 维护提示：
# - 左侧键名是程序内部使用的疾病标签，尽量使用与大疫情网病种接近且便于人工理解的名称。
# - 右侧正则用于把门诊匹配字段和网报疾病名称映射到同一套标签。
# - 若报告中出现“标签维护提示”，通常需要在此处补充相应疾病标签或同义表达。
DISEASE_SIGNAL_PATTERNS = {
    "病毒性肝炎": re.compile(r"肝炎未分型|病毒性肝炎|甲肝|甲型肝炎|乙肝|乙型肝炎|丙肝|丙型肝炎|丁肝|丁型肝炎|戊肝|戊型肝炎|传染性肝炎", re.I),
    "甲型肝炎": re.compile(r"甲肝|甲型肝炎|甲型病毒性肝炎", re.I),
    "乙型肝炎": re.compile(r"乙肝|乙型肝炎|乙型病毒性肝炎", re.I),
    "丙型肝炎": re.compile(r"丙肝|丙型肝炎|丙型病毒性肝炎", re.I),
    "丁型肝炎": re.compile(r"丁肝|丁型肝炎|丁型病毒性肝炎", re.I),
    "戊型肝炎": re.compile(r"戊肝|戊型肝炎|戊型病毒性肝炎", re.I),
    "艾滋病/HIV": re.compile(r"艾滋病|HIV|AIDS|获得性免疫|艾滋|爱滋", re.I),
    "胎传梅毒": re.compile(r"胎传梅毒|先天梅毒", re.I),
    "梅毒": re.compile(r"梅毒(?!个人史)", re.I),
    "脊髓灰质炎": re.compile(r"脊髓灰质炎病毒|脊髓灰质炎|脊灰|小儿麻痹", re.I),
    "麻疹": re.compile(r"(?<!荨)麻疹", re.I),
    "狂犬病": re.compile(r"狂犬病|狂犬", re.I),
    "新生儿破伤风": re.compile(r"新生儿破伤风|新破", re.I),
    "肺结核": re.compile(r"肺结核|利福平耐药|病原学阳性|病原学阴性|涂阳|仅培阳|未痰检|结核性胸膜炎|胸膜结核|菌阴", re.I),
    "麻风病": re.compile(r"麻风病|麻风", re.I),
    "流行性腮腺炎": re.compile(r"流行性腮腺炎|流腮|痄腮|炸腮", re.I),
    "水痘": re.compile(r"水痘", re.I),
    "AFP": re.compile(r"\bAFP\b|急性弛缓性麻痹", re.I),
    "流行性感冒": re.compile(r"流行性感冒|(?<!禽)流感|病毒性流感|病毒性感冒|甲流|乙流|H1N1", re.I),
    "禽流感": re.compile(r"人感染新亚型流感|禽流感|(?!.*h1n1)H\d+N\d+|动物源性流感|欧亚禽类", re.I),
    "新型冠状病毒感染": re.compile(r"新型冠状病毒感染|新冠", re.I),
    "传染性非典型肺炎": re.compile(r"传染性非典型肺炎|非典(?!型)|SARS", re.I),
    "痢疾": re.compile(r"细菌性痢疾|阿米巴性痢疾|阿米巴痢疾|菌痢|志贺|阿米巴", re.I),
    "伤寒副伤寒": re.compile(r"伤寒|副伤寒", re.I),
    "流行性脑脊髓膜炎": re.compile(r"流行性脑脊髓膜炎|流脑|流行性脑脊髓炎|流行性脑膜炎", re.I),
    "百日咳": re.compile(r"百日咳", re.I),
    "白喉": re.compile(r"白喉", re.I),
    "猩红热": re.compile(r"猩红热", re.I),
    "布鲁氏菌病": re.compile(r"布鲁氏菌病|布病|布鲁氏菌", re.I),
    "淋病": re.compile(r"淋病", re.I),
    "疟疾": re.compile(r"疟疾|三日疟|恶性疟|间日疟|卵形疟|诺氏疟|疟原虫", re.I),
    "手足口病": re.compile(r"手足口病|手足口", re.I),
    "感染性腹泻": re.compile(r"轮状|札如|诺如|沙门|大肠杆菌|EPEC|致泻性弧菌|弯曲菌|耶尔森菌|肠腺病毒|隐孢子虫|蓝氏贾第鞭毛虫|感染性腹泻|病毒性腹泻|细菌性腹泻", re.I),
    "风疹": re.compile(r"风疹", re.I),
    "猴痘": re.compile(r"猴痘", re.I),
    "登革热": re.compile(r"登革热|登革", re.I),
    "基孔肯雅热": re.compile(r"基孔肯雅热|基孔", re.I),
    "鼠疫": re.compile(r"鼠疫", re.I),
    "霍乱": re.compile(r"霍乱", re.I),
    "流行性出血热": re.compile(r"流行性出血热|出血热", re.I),
    "流行性乙型脑炎": re.compile(r"流行性乙型脑炎|乙脑", re.I),
    "炭疽": re.compile(r"炭疽", re.I),
    "钩端螺旋体病": re.compile(r"钩端螺旋体病|钩体", re.I),
    "血吸虫病": re.compile(r"血吸虫病", re.I),
    "发热伴血小板减少综合征": re.compile(r"发热伴血小板減少综合征|发热伴血小板减少综合征|新型布尼亚|布尼亚|大别班达|SFTS", re.I),
    "急性出血性结膜炎": re.compile(r"急性出血性结膜炎|急出血|红眼病|出血性急性结膜炎", re.I),
    "斑疹伤寒": re.compile(r"流行性斑疹伤寒|地方性斑疹伤寒|斑疹伤寒|立克次体", re.I),
    "黑热病": re.compile(r"黑热病|杜氏利什曼", re.I),
    "包虫病": re.compile(r"包虫病|包虫|棘球蚴病|棘球蚴|棘球", re.I),
    "丝虫病": re.compile(r"丝虫病|丝虫", re.I),
    "中东呼吸综合征": re.compile(r"中东呼吸综合征|MERS", re.I),
    "埃博拉出血热": re.compile(r"埃博拉出血热|埃博拉", re.I),
    "黄热病": re.compile(r"黄热病", re.I),
    "裂谷热": re.compile(r"裂谷热", re.I),
    "西尼罗热": re.compile(r"西尼罗热", re.I),
    "拉沙热": re.compile(r"拉沙热", re.I),
    "马尔堡病": re.compile(r"马尔堡", re.I),
    "寨卡病毒病": re.compile(r"寨卡", re.I),
    "森林脑炎": re.compile(r"森林脑炎", re.I),
    "恙虫病": re.compile(r"恙虫病|恙虫", re.I),
    "肝吸虫病": re.compile(r"肝吸虫病|肝吸虫|华支睾", re.I),
    "尖锐湿疣": re.compile(r"尖锐湿疣|外阴湿疣|肛周湿疣|生殖器湿疣", re.I),
    "生殖器疱疹": re.compile(r"生殖器疱疹|外阴疱疹|肛周疱疹", re.I),
    "生殖道沙眼衣原体": re.compile(r"生殖道沙眼衣原体|生殖道衣原体|沙眼衣原体生殖道", re.I)
}

REVISIT_RULES = {
    "乙型肝炎": ("终身规则", None),
    "艾滋病/HIV": ("终身规则", None),
    "胎传梅毒": ("终身规则", None),
    "脊髓灰质炎": ("终身规则", None),
    "麻疹": ("终身规则", None),
    "狂犬病": ("终身规则", None),
    "新生儿破伤风": ("终身规则", None),
    "麻风病": ("终身规则", None),
    "流行性腮腺炎": ("终身规则", None),
    "水痘": ("终身规则", None),
    "AFP": ("终身规则", None),
    "丙型肝炎": ("3年规则", 3 * 365),
    "肺结核": ("1年规则", 365)
}

# 宽泛标签用于处理“病毒性肝炎”等父级概念；当具体型别存在时，避免仅因父级标签相同而误判。
BROAD_DISEASE_SIGNALS = {"病毒性肝炎"}
HEPATITIS_SPECIFIC_SIGNALS = {
    "甲型肝炎", "乙型肝炎", "丙型肝炎", "丁型肝炎", "戊型肝炎"
}


def extract_disease_signals(text):
    """提取多个疾病关联标签；不改变原始赋值匹配字段。"""
    text = "" if pd.isna(text) else str(text)
    return {name for name, pattern in DISEASE_SIGNAL_PATTERNS.items() if pattern.search(text)}


def display_disease_signals(signals):
    """存在明确肝炎型别时，不重复展示父级“病毒性肝炎”标签。"""
    display_signals = set(signals)
    if display_signals & HEPATITIS_SPECIFIC_SIGNALS:
        display_signals.discard("病毒性肝炎")
    return "、".join(sorted(display_signals))


def normalized_signal_list(signals):
    """主结果按疾病信号拆分；有明确肝炎型别时，不再单独生成父级病毒性肝炎信号。"""
    display_signals = set(signals)
    if display_signals & HEPATITIS_SPECIFIC_SIGNALS:
        display_signals.discard("病毒性肝炎")
    return sorted(display_signals)


def split_assignment_terms(value):
    """拆分步骤1输出的匹配字段，供标签维护提示和兜底相关性判断使用。"""
    if pd.isna(value):
        return set()
    return {term.strip().upper() for term in re.split(r"[，,、；;]", str(value)) if term.strip()}


def get_revisit_rule(common_signals):
    """明确标签使用专项规则；不能明确型别时采用30天保守规则。"""
    priority = [
        "乙型肝炎", "丙型肝炎", "艾滋病/HIV", "胎传梅毒", "脊髓灰质炎",
        "麻疹", "狂犬病", "新生儿破伤风", "肺结核", "麻风病",
        "流行性腮腺炎", "水痘", "AFP"
    ]
    for signal in priority:
        if signal in common_signals:
            rule_name, days = REVISIT_RULES[signal]
            return signal, rule_name, days
    return "未明确专项病种", "默认30天规则", 30


def get_tag_maintenance_hint(row):
    """当步骤1匹配字段未能映射到疾病标签时，生成维护提示。"""
    clinic_text = f"{row.get(COLUMN_MAPPING['clinic']['diagnosis'], '')}，{row.get('匹配字段', '')}"
    clinic_terms = split_assignment_terms(row.get("匹配字段", ""))
    unmapped_clinic_terms = sorted(
        term for term in clinic_terms
        if not extract_disease_signals(term)
    )
    return (
        "门诊匹配字段未能映射为疾病标签，建议维护疾病标签库："
        + "、".join(unmapped_clinic_terms)
        if unmapped_clinic_terms else ""
    )


def evaluate_signal_relation(row):
    """按单个门诊疾病信号评价一张身份候选卡。"""
    signal = row.get("门诊疾病信号", "")
    report_text = row.get(COLUMN_MAPPING['report']['disease'], '')
    clinic_signals = set() if signal == "未映射疾病信号" else {signal}
    report_signals = extract_disease_signals(report_text)
    common_signals = clinic_signals & report_signals
    clinic_hepatitis_types = clinic_signals & HEPATITIS_SPECIFIC_SIGNALS
    report_hepatitis_types = report_signals & HEPATITIS_SPECIFIC_SIGNALS
    hepatitis_type_conflict = bool(
        clinic_hepatitis_types
        and report_hepatitis_types
        and clinic_hepatitis_types.isdisjoint(report_hepatitis_types)
    )

    report_terms = split_assignment_terms(report_text)
    term_related = any(
        signal and signal != "未映射疾病信号"
        and (signal.upper() in report_term or report_term in signal.upper())
        for report_term in report_terms
    )

    specific_common_signals = common_signals - BROAD_DISEASE_SIGNALS
    if hepatitis_type_conflict:
        relation = "型别冲突"
        relation_score = 0
    elif specific_common_signals:
        relation = "强相关"
        relation_score = 3
    elif common_signals or term_related:
        relation = "可能相关"
        relation_score = 2
    else:
        relation = "仅身份相关"
        relation_score = 1

    rule_signal, rule_name, rule_days = get_revisit_rule(common_signals)
    return {
        "门诊疾病标签": signal if signal != "未映射疾病信号" else "",
        "网报疾病标签": display_disease_signals(report_signals),
        "共同疾病标签": "" if hepatitis_type_conflict else display_disease_signals(common_signals),
        "疾病相关程度": relation,
        "疾病相关分": relation_score,
        "型别冲突说明": (
            f"门诊型别：{'、'.join(sorted(clinic_hepatitis_types))}；"
            f"网报型别：{'、'.join(sorted(report_hepatitis_types))}"
            if hepatitis_type_conflict else ""
        ),
        "复诊规则病种": rule_signal,
        "适用复诊规则": "不适用（型别冲突）" if hepatitis_type_conflict else rule_name,
        "复诊规则天数": 0 if hepatitis_type_conflict else rule_days
    }


def build_candidate_results(data_match, time_unit):
    """生成“就诊记录×门诊疾病信号”粒度主结果，以及复核用候选卡明细。"""
    visit_col = COLUMN_MAPPING['clinic']['visit_time']
    report_col = COLUMN_MAPPING['report']['report_time']
    card_col = COLUMN_MAPPING['report']['card_id']

    work = data_match.copy()
    work[visit_col] = pd.to_datetime(work[visit_col], errors="coerce")
    work[report_col] = pd.to_datetime(work[report_col], errors="coerce")

    # 一条筛选后门诊记录可能匹配多张网报卡。先还原门诊侧唯一记录，
    # 再统计每条门诊记录在身份层面匹配到多少张候选卡。
    report_cols = {
        COLUMN_MAPPING['report']['name'],
        COLUMN_MAPPING['report']['id'],
        COLUMN_MAPPING['report']['disease'],
        COLUMN_MAPPING['report']['report_time'],
        COLUMN_MAPPING['report']['card_id']
    }
    clinic_columns = [col for col in work.columns if col not in report_cols]
    clinic_base = work[clinic_columns].drop_duplicates("程序关联号", keep="first").copy()

    identity_counts = (
        work[work[card_col].notna()]
        .groupby("程序关联号")[card_col]
        .size()
        .rename("身份候选卡数")
    )
    clinic_base = clinic_base.merge(identity_counts, how="left", on="程序关联号")
    clinic_base["身份候选卡数"] = clinic_base["身份候选卡数"].fillna(0).astype(int)

    # 主结果采用“就诊记录 × 门诊疾病信号”粒度。
    # 例如“戊肝、肝吸虫病”会拆成两个主结果行，分别独立判定是否已有对应报卡。
    signal_records = []
    for _, row in clinic_base.iterrows():
        clinic_text = f"{row.get(COLUMN_MAPPING['clinic']['diagnosis'], '')}，{row.get('匹配字段', '')}"
        clinic_signals = normalized_signal_list(extract_disease_signals(clinic_text))
        if not clinic_signals:
            clinic_signals = ["未映射疾病信号"]
        tag_hint = get_tag_maintenance_hint(row)
        for seq, signal in enumerate(clinic_signals, start=1):
            signal_row = row.to_dict()
            signal_row["疾病信号序号"] = seq
            signal_row["门诊疾病信号"] = signal
            signal_row["疾病信号关联号"] = f"{row['程序关联号']}-D{seq:02d}"
            signal_row["门诊疾病标签"] = "" if signal == "未映射疾病信号" else signal
            signal_row["标签维护提示"] = tag_hint if tag_hint else ""
            signal_records.append(signal_row)
    signal_base = pd.DataFrame(signal_records)

    # 将疾病信号主表与身份候选卡池组合，供后续逐个判断“该疾病信号与该卡是否相关”。
    identity_candidate_cols = [
        "程序关联号",
        COLUMN_MAPPING['report']['name'],
        COLUMN_MAPPING['report']['id'],
        COLUMN_MAPPING['report']['disease'],
        COLUMN_MAPPING['report']['report_time'],
        COLUMN_MAPPING['report']['card_id'],
        "姓名匹配方式"
    ]
    identity_candidates = work[work[card_col].notna()][
        [col for col in identity_candidate_cols if col in work.columns]
    ].copy()
    candidate_rows = signal_base.merge(identity_candidates, how="inner", on="程序关联号")

    if len(candidate_rows) > 0:
        # 对每个“疾病信号 × 身份候选卡”计算疾病相关程度、时间间隔和复诊规则状态。
        relation_details = candidate_rows.apply(evaluate_signal_relation, axis=1, result_type="expand")
        for col in relation_details.columns:
            candidate_rows[col] = relation_details[col]

        delta = candidate_rows[report_col] - candidate_rows[visit_col]
        candidate_rows["时间间隔天"] = delta.dt.days
        candidate_rows["时间间隔小时"] = delta.dt.total_seconds() // 3600
        candidate_rows["时间间隔"] = (
            candidate_rows["时间间隔天"]
            if time_unit == "d"
            else candidate_rows["时间间隔小时"]
        )
        candidate_rows["时间有效"] = (
            candidate_rows[visit_col].notna() & candidate_rows[report_col].notna()
        ).astype(int)
        candidate_rows["负时间差"] = (candidate_rows[report_col] < candidate_rows[visit_col]).astype(int)

        report_dates = candidate_rows[report_col].dt.normalize()
        visit_dates = candidate_rows[visit_col].dt.normalize()
        lower_dates = visit_dates - pd.to_timedelta(
            candidate_rows["复诊规则天数"].fillna(0), unit="D"
        )
        candidate_rows["规则期内"] = (
            (candidate_rows["时间有效"] == 1)
            & (
                (candidate_rows["负时间差"] == 0)
                | (
                    (candidate_rows["适用复诊规则"] == "终身规则")
                    & (report_dates <= visit_dates)
                )
                | (
                    (candidate_rows["适用复诊规则"] != "终身规则")
                    & (report_dates >= lower_dates)
                    & (report_dates <= visit_dates)
                )
            )
        ).astype(int)

        threshold = 1 if time_unit == "d" else 48
        candidate_rows["基础及时"] = (
            (candidate_rows["时间间隔"] <= threshold)
            & (
                (candidate_rows["负时间差"] == 0)
                | (candidate_rows["规则期内"] == 1)
            )
        ).astype(int)
        candidate_rows["原始基础及时"] = (candidate_rows["时间间隔"] <= threshold).astype(int)
        candidate_rows["可作为主要依据"] = (
            (candidate_rows["疾病相关分"] >= 2)
            & (candidate_rows["时间有效"] == 1)
            & (
                (candidate_rows["负时间差"] == 0)
                | (candidate_rows["规则期内"] == 1)
            )
        ).astype(int)
        candidate_rows["绝对时间距离"] = candidate_rows["时间间隔小时"].abs()
        candidate_rows["候选标签"] = candidate_rows.apply(
            lambda row: "、".join(
                label for condition, label in [
                    (row["疾病相关程度"] == "强相关", "疾病强相关"),
                    (row["疾病相关程度"] == "可能相关", "疾病可能相关"),
                    (row["疾病相关程度"] == "仅身份相关", "仅身份相关"),
                    (row["疾病相关程度"] == "型别冲突", "明确型别冲突"),
                    (row["负时间差"] == 1, "负时间差"),
                    (row["时间有效"] == 0, "时间无效"),
                    (row["规则期内"] == 1 and row["负时间差"] == 1, "规则期内历史/同次诊疗候选"),
                    (row["基础及时"] == 1, "基础及时"),
                    (row["时间间隔"] > threshold, "迟报候选")
                ] if condition
            ),
            axis=1
        )

        # 每个疾病信号只推荐一个最佳候选卡；未入选的相关候选仅作为复核材料。
        candidate_rows = candidate_rows.sort_values(
            ["疾病信号关联号", "可作为主要依据", "疾病相关分", "基础及时", "绝对时间距离", report_col],
            ascending=[True, False, False, False, True, True]
        )
        candidate_rows["候选排名"] = candidate_rows.groupby("疾病信号关联号").cumcount() + 1
        candidate_rows["一卡多匹"] = candidate_rows.duplicated(subset=card_col, keep=False).astype(int)
        candidate_rows["是否最佳候选"] = (
            (candidate_rows["候选排名"] == 1)
            & (candidate_rows["可作为主要依据"] == 1)
        ).astype(int)
        candidate_rows["未选为最佳卡的原因"] = candidate_rows.apply(
            lambda row: "" if row["是否最佳候选"] == 1 else (
                f"明确肝炎型别冲突：{row['型别冲突说明']}"
                if row["疾病相关程度"] == "型别冲突" else
                "仅姓名和证件号一致，疾病信号不足"
                if row["疾病相关分"] < 2 else
                "就诊时间或报告时间无效"
                if row["时间有效"] == 0 else
                "负时间差且超出适用复诊期限"
                if row["负时间差"] == 1 and row["规则期内"] == 0 else
                "存在疾病关联度更高或时间距离更近的候选卡"
            ),
            axis=1
        )

    if len(candidate_rows) == 0:
        # 没有任何身份候选卡时，所有疾病信号均进入可疑漏报主结果。
        signal_base["基础匹配卡数"] = signal_base["身份候选卡数"]
        signal_base["疾病相关候选卡数"] = 0
        signal_base["原始基础及时卡数"] = 0
        signal_base["其他候选卡数"] = 0
        signal_base["优化判定"] = "可疑漏报"
        signal_base["判定说明"] = "姓名和证件号未匹配到报卡"
        return signal_base, candidate_rows

    original_timely_counts = (
        candidate_rows[
            (candidate_rows["疾病相关分"] >= 2)
            & (candidate_rows["原始基础及时"] == 1)
        ]
        .groupby("疾病信号关联号")["原始基础及时"]
        .sum()
        .rename("原始基础及时卡数")
    )
    signal_base = signal_base.merge(original_timely_counts, how="left", on="疾病信号关联号")
    signal_base["原始基础及时卡数"] = signal_base["原始基础及时卡数"].fillna(0).astype(int)

    related_counts = (
        candidate_rows[candidate_rows["疾病相关分"] >= 2]
        .groupby("疾病信号关联号")[card_col]
        .size()
        .rename("疾病相关候选卡数")
    )
    signal_base = signal_base.merge(related_counts, how="left", on="疾病信号关联号")
    signal_base["疾病相关候选卡数"] = signal_base["疾病相关候选卡数"].fillna(0).astype(int)
    signal_base["基础匹配卡数"] = signal_base["身份候选卡数"]

    # 合并最佳候选卡字段到疾病信号主结果。
    best = candidate_rows[candidate_rows["是否最佳候选"] == 1].copy()
    best_columns = [
        "疾病信号关联号", card_col, COLUMN_MAPPING['report']['disease'], report_col,
        "时间间隔", "门诊疾病标签", "网报疾病标签", "共同疾病标签",
        "疾病相关程度", "复诊规则病种", "适用复诊规则",
        "候选标签", "一卡多匹"
    ]
    best = best[best_columns].rename(columns={
        card_col: "最佳候选卡ID",
        COLUMN_MAPPING['report']['disease']: "最佳候选卡疾病",
        report_col: "最佳候选卡报告时间",
        "时间间隔": "最佳候选卡时间间隔",
        "候选标签": "最佳候选卡标签"
    })
    signal_base = signal_base.merge(best, how="left", on="疾病信号关联号")

    # 无最佳候选时仍带出排名第一的参考候选，便于人工判断为什么未被程序采纳。
    reference = candidate_rows[candidate_rows["候选排名"] == 1].copy()
    reference_columns = [
        "疾病信号关联号", card_col, COLUMN_MAPPING['report']['disease'], report_col,
        "时间间隔", "疾病相关程度", "复诊规则病种", "适用复诊规则",
        "候选标签", "未选为最佳卡的原因", "型别冲突说明"
    ]
    reference = reference[reference_columns].rename(columns={
        card_col: "参考候选卡ID",
        COLUMN_MAPPING['report']['disease']: "参考候选卡疾病",
        report_col: "参考候选卡报告时间",
        "时间间隔": "参考候选卡时间间隔",
        "疾病相关程度": "参考候选疾病相关程度",
        "复诊规则病种": "参考复诊规则病种",
        "适用复诊规则": "参考适用复诊规则",
        "候选标签": "参考候选卡标签",
        "未选为最佳卡的原因": "参考候选未入选原因",
        "型别冲突说明": "参考候选型别冲突说明"
    })
    signal_base = signal_base.merge(reference, how="left", on="疾病信号关联号")

    signal_base["复诊规则病种"] = signal_base["复诊规则病种"].fillna(
        signal_base["参考复诊规则病种"]
    )
    signal_base["适用复诊规则"] = signal_base["适用复诊规则"].fillna(
        signal_base["参考适用复诊规则"]
    )
    selected_count = signal_base["最佳候选卡ID"].notna().astype(int)
    signal_base["其他候选卡数"] = (signal_base["疾病相关候选卡数"] - selected_count).clip(lower=0)

    # 将最佳候选卡状态转换为主结果判定：及时、迟报、负时间差合规候选或可疑漏报。
    threshold = 1 if time_unit == "d" else 48
    signal_base["优化判定"] = signal_base.apply(
        lambda row: "可疑漏报"
        if pd.isna(row.get("最佳候选卡ID")) else
        "负时间差合规候选"
        if "负时间差" in str(row.get("最佳候选卡标签", "")) else
        "及时报告"
        if row.get("最佳候选卡时间间隔") <= threshold else
        "迟报",
        axis=1
    )
    signal_base["判定说明"] = signal_base.apply(
        lambda row: (
            "该门诊疾病信号未找到疾病相关且时间规则可接受的报卡；请结合参考候选和原始数据人工复核"
            if row["优化判定"] == "可疑漏报" and row["身份候选卡数"] > 0 else
            "姓名和证件号未匹配到报卡"
            if row["优化判定"] == "可疑漏报" else
            f"按{row.get('疾病相关程度', '')}、{row.get('适用复诊规则', '')}及时间距离推荐；负时间差不自动排除"
        ),
        axis=1
    )
    return signal_base, candidate_rows


def protect_excel_text(value):
    """让Excel直接打开CSV时按文本显示长ID，避免科学计数法和15位精度限制。"""
    if pd.isna(value) or str(value).strip() in {"", "无", "nan", "None"}:
        return ""
    text = str(value).strip()
    # 清理由历史数值读取可能产生的 .0；不会改变包含字母的卡片ID。
    text = re.sub(r"^(\d+)\.0$", r"\1", text)
    text = text.replace('"', '""')
    return f'="{text}"'


def analysis(data_match, export_txt, export_reported, export_missing, export_duplicate, time_unit,
             raw_data_count, filtered_count, disease_distribution):
    # 步骤2必须依赖卡片ID回查原始网报卡，因此缺失时直接停止分析。
    if COLUMN_MAPPING['report']['card_id'] not in data_match.columns:
        raise ValueError(f"{Color.ERROR} 合并数据中缺少卡片ID列，请检查大疫情网报卡是否包含该列")
        
    required_time_cols = {COLUMN_MAPPING['report']['report_time'], COLUMN_MAPPING['clinic']['visit_time']}
    if required_time_cols.difference(data_match.columns):
        print(f"{Color.ERROR} ❌ 错误：合并数据缺少必要时间列")
        return

    main_result, candidate_details = build_candidate_results(data_match, time_unit)
    reported = main_result[main_result["优化判定"] != "可疑漏报"].reset_index(drop=True)
    not_reported = main_result[main_result["优化判定"] == "可疑漏报"].reset_index(drop=True)
    candidate_file = files["候选卡明细"]

    # 仅在输出副本中增加Excel文本保护；内部计算仍使用原始卡片ID。
    reported_output = reported.copy()
    not_reported_output = not_reported.copy()
    candidate_output = candidate_details.copy()
    if len(candidate_output) > 0:
        review_mask = (
            (
                (candidate_output.get("疾病相关分", 0) >= 2)
                | (candidate_output.get("疾病相关程度", "") == "型别冲突")
            )
            & (
                (candidate_output.get("是否最佳候选", 0) != 1)
                | candidate_output.get("未选为最佳卡的原因", pd.Series("", index=candidate_output.index))
                    .fillna("").astype(str).str.strip().ne("")
            )
        )
        candidate_output = candidate_output[review_mask].copy()
    if "最佳候选卡ID" in reported_output.columns:
        reported_output["最佳候选卡ID"] = reported_output["最佳候选卡ID"].apply(protect_excel_text)
    if "最佳候选卡ID" in not_reported_output.columns:
        not_reported_output["最佳候选卡ID"] = not_reported_output["最佳候选卡ID"].apply(protect_excel_text)
    if "参考候选卡ID" in reported_output.columns:
        reported_output["参考候选卡ID"] = reported_output["参考候选卡ID"].apply(protect_excel_text)
    if "参考候选卡ID" in not_reported_output.columns:
        not_reported_output["参考候选卡ID"] = not_reported_output["参考候选卡ID"].apply(protect_excel_text)
    if COLUMN_MAPPING['report']['card_id'] in candidate_output.columns:
        candidate_output[COLUMN_MAPPING['report']['card_id']] = candidate_output[
            COLUMN_MAPPING['report']['card_id']
        ].apply(protect_excel_text)

    reported_output.to_csv(export_reported, index=False, encoding='utf-8-sig', chunksize=1000)
    not_reported_output.to_csv(export_missing, index=False, encoding='utf-8-sig', chunksize=1000)
    candidate_output.to_csv(candidate_file, index=False, encoding='utf-8-sig', chunksize=1000)

    dup_col = COLUMN_MAPPING['report']['card_id']
    valid_candidates = candidate_output[candidate_output[dup_col].notna()].copy()
    duplicates = valid_candidates[
        valid_candidates.duplicated(subset=dup_col, keep=False)
    ].sort_values(dup_col)
    duplicate_count = len(duplicates)
    negative_delta = int((valid_candidates.get("负时间差", 0) == 1).sum())
    timely = int((reported["优化判定"] == "及时报告").sum())
    late = int((reported["优化判定"] == "迟报").sum())
    negative_compliant = int((reported["优化判定"] == "负时间差合规候选").sum())
    total_records = len(main_result)
    unique_visit_records = main_result["程序关联号"].nunique() if "程序关联号" in main_result.columns else total_records
    suspected_missing = len(not_reported)
    suspected_missing_rate = suspected_missing / total_records if total_records else 0
    confirmed_or_compliant = len(reported)
    timely_rate_among_confirmed = timely / confirmed_or_compliant if confirmed_or_compliant else 0
    timely_rate_among_total = timely / total_records if total_records else 0
    timely_or_compliant = timely + negative_compliant
    report_rate = confirmed_or_compliant / total_records if total_records else 0
    timely_or_compliant_rate = timely_or_compliant / confirmed_or_compliant if confirmed_or_compliant else 0
    completion_count = confirmed_or_compliant
    completion_rate = completion_count / confirmed_or_compliant if confirmed_or_compliant else 0
    accuracy_count = confirmed_or_compliant
    accuracy_rate = accuracy_count / confirmed_or_compliant if confirmed_or_compliant else 0
    online_report_count = confirmed_or_compliant
    consistency_count = confirmed_or_compliant
    consistency_rate = consistency_count / online_report_count if online_report_count else 0
    valid_id_complete_count = confirmed_or_compliant
    valid_id_complete_rate = valid_id_complete_count / confirmed_or_compliant if confirmed_or_compliant else 0

    identity_matched_count = int((main_result["身份候选卡数"] > 0).sum()) if "身份候选卡数" in main_result else 0
    no_identity_matched_count = total_records - identity_matched_count
    original_timely_count = int((main_result["原始基础及时卡数"] > 0).sum()) if "原始基础及时卡数" in main_result else 0
    suspected_with_candidates = int((not_reported["身份候选卡数"] > 0).sum()) if "身份候选卡数" in not_reported else 0
    suspected_without_candidates = suspected_missing - suspected_with_candidates
    total_identity_candidates = int(main_result["身份候选卡数"].sum()) if "身份候选卡数" in main_result else 0

    suffix_name_candidates = int((candidate_details.get("姓名匹配方式", pd.Series(dtype=str)) == "中文姓名后缀兼容").sum())
    exact_name_candidates = int((candidate_details.get("姓名匹配方式", pd.Series(dtype=str)) == "完全匹配").sum())
    tag_hint_count = 0
    if "标签维护提示" in main_result.columns:
        tag_hint_count = int(main_result["标签维护提示"].fillna("").astype(str).str.strip().ne("").sum())

    over_cancel_count = None
    if EXPORT_OVER_CANCEL.exists():
        try:
            over_cancel_count = len(pd.read_csv(EXPORT_OVER_CANCEL, dtype=str))
        except Exception:
            over_cancel_count = None

    def format_counts(series):
        if series is None or len(series) == 0:
            return "  无\n"
        return "".join(f"  - {idx}：{val} 条\n" for idx, val in series.items())

    judgment_counts = main_result["优化判定"].value_counts(dropna=False)
    relation_counts = (
        candidate_details["疾病相关程度"].value_counts(dropna=False)
        if "疾病相关程度" in candidate_details.columns else pd.Series(dtype=int)
    )
    name_match_counts = (
        candidate_details["姓名匹配方式"].value_counts(dropna=False)
        if "姓名匹配方式" in candidate_details.columns else pd.Series(dtype=int)
    )

    print(f"{Color.INFO} 🔍 优化后已报/合规候选：{len(reported)} 条")
    print(f"{Color.INFO} 🔍 优化后可疑漏报：{len(not_reported)} 条")
    print(f"{Color.INFO} 🔎 复核用候选卡明细：{len(candidate_output)} 条，保存至 {candidate_file.resolve()}")
    if duplicate_count > 0:
        print(f"{Color.WARNING} ⚠️ 候选明细中发现{duplicate_count}条一卡多匹条目")
    if negative_delta > 0:
        print(f"{Color.WARNING} ⚠️ 发现{negative_delta}条负时间差候选，已保留且未自动排除")
    
    # 如需单独导出一卡多匹明细，可取消下一行注释。
    # duplicates.to_csv(export_duplicate, index=False, encoding='utf-8', chunksize=1000)
    
    # 生成文本报告。报告开头为填表快速统计区，后续为详细复核统计。
    # 程序结果用于辅助调查，最终结论仍需结合原始资料人工确认。
    fill_table_summary = (
            f"{'='*60}\n"
            f"【填表快速统计区】\n"
            f"{'='*60}\n"
            f"医疗机构名称：请手工填写\n\n"
            f"实查门诊住院检验影像病例总数：{total_records}\n"
            f"门诊住院检验影像网络报告病例总数：{confirmed_or_compliant}\n"
            f"报告率(%)：{report_rate:.2%}\n"
            f"门诊住院检验影像报告及时病例总数：{timely_or_compliant}\n"
            f"报告及时率(%)：{timely_or_compliant_rate:.2%}\n\n"
            f"实查质（电子）报告卡数：{confirmed_or_compliant}\n"
            f"填写完整的纸质（电子）报告卡数：{completion_count}（需人工核实）\n"
            f"完整率(%)：{completion_rate:.2%}（需人工核实）\n"
            f"填写准确的纸质报告卡数：{accuracy_count}（需人工核实）\n"
            f"准确率(%)：{accuracy_rate:.2%}（需人工核实）\n"
            f"纸质报告卡中进行网络报告卡数：{online_report_count}\n"
            f"纸质报告卡与大疫情中报告一致的报告卡数：{consistency_count}（需人工核实）\n"
            f"一致率(%)：{consistency_rate:.2%}（需人工核实）\n"
            f"填写有效证件号完整的报告卡数：{valid_id_complete_count}（需人工核实）\n"
            f"有效证件号填写完整率(%)：{valid_id_complete_rate:.2%}（需人工核实）\n\n"
            f"实查门诊住院病例总数：{total_records}\n"
            f"门诊住院病例网络报告总数：{confirmed_or_compliant}\n"
            f"门诊住院部门报告率(%)：{report_rate:.2%}\n"
            f"门诊住院报告及时病例数：{timely_or_compliant}\n"
            f"门诊住院报告及时率(%)：{timely_or_compliant_rate:.2%}\n"
            f"实查门诊病例数：{total_records}\n"
            f"门诊漏报数：{suspected_missing}\n"
            f"门诊迟报数：{late}\n"
            f"实查住院病例数：0\n"
            f"住院漏报数：0\n"
            f"住院迟报数：0\n"
            f"备注：本次运行统一按门诊字段口径统计；如为住院/影像/检验数据，请将本区数字作为该批次结果自行归总。\n\n"
            )

    report = (
            fill_table_summary +
            f"{'='*60}\n"  # 顶部总分隔线
            f"传染病报卡辅助分析报告（{current_version}）\n"
            f"{'='*60}\n\n"
            f"重要说明：\n"
            f"  本报告为程序根据姓名、证件号、疾病标签、报告时间和复诊规则生成的辅助核查结果，\n"
            f"  不等同于最终漏报调查结论。涉及“可疑漏报”“迟报候选”“型别冲突”“标签维护提示”等情形，\n"
            f"  均需结合原始门诊记录和大疫情网报卡进行人工复核。\n\n"

            f"【一、门诊诊断初筛统计】\n"
            f"{'─'*40}\n"
            f"原始门诊记录数：{raw_data_count} 条\n"
            f"赋值匹配后进入分析的记录数：{filtered_count} 条\n"
            f"初筛进入分析占比：{filtered_count / raw_data_count if raw_data_count else 0:.2%}\n"
            f"疑似过度抵消记录：{over_cancel_count if over_cancel_count is not None else '未读取'} 条\n"
            f"疾病等级项数分布：{disease_distribution}\n\n"

            f"【二、身份候选卡匹配统计】\n"
            f"{'─'*40}\n"
            f"本次参与报卡分析的就诊记录数：{unique_visit_records} 条\n"
            f"拆分后的门诊疾病信号数：{total_records} 条\n"
            f"身份匹配到至少1张网报卡的疾病信号：{identity_matched_count} 条\n"
            f"未匹配到身份候选卡的疾病信号：{no_identity_matched_count} 条\n"
            f"身份候选卡累计数（按疾病信号重复计）：{total_identity_candidates} 张\n"
            f"存在原始基础及时卡的疾病信号：{original_timely_count} 条\n"
            f"复核用候选卡明细导出条目：{len(candidate_output)} 条\n"
            f"一卡多匹候选条目：{duplicate_count} 条\n"
            f"负时间差候选条目：{negative_delta} 条\n\n"

            f"【三、姓名匹配方式统计（候选卡明细口径）】\n"
            f"{'─'*40}\n"
            f"{format_counts(name_match_counts)}"
            f"其中完全匹配候选：{exact_name_candidates} 条；中文姓名后缀兼容候选：{suffix_name_candidates} 条\n\n"

            f"【四、疾病相关程度统计（候选卡明细口径）】\n"
            f"{'─'*40}\n"
            f"{format_counts(relation_counts)}"
            f"标签维护提示条目：{tag_hint_count} 条\n\n"

            f"【五、程序优化判定统计（一条门诊疾病信号一条主结果）】\n"
            f"{'─'*40}\n"
            f"{format_counts(judgment_counts)}"
            f"程序认为已报告/合规候选：{confirmed_or_compliant} 条\n"
            f"  - 及时报告：{timely} 条\n"
            f"  - 迟报：{late} 条\n"
            f"  - 负时间差合规候选：{negative_compliant} 条\n"
            f"程序可疑漏报：{suspected_missing} 条\n"
            f"  - 有身份候选卡但未形成可用最佳候选：{suspected_with_candidates} 条\n"
            f"  - 未匹配到身份候选卡：{suspected_without_candidates} 条\n"
            f"程序可疑漏报占比（疾病信号口径）：{suspected_missing_rate:.2%}\n"
            f"及时报告占已报告/合规候选比例：{timely_rate_among_confirmed:.2%}\n"
            f"及时报告占全部分析记录比例：{timely_rate_among_total:.2%}\n\n"

            f"【六、输出文件说明】\n"
            f"{'─'*40}\n"
            f"结果(已报告卡).csv：按“就诊记录×门诊疾病信号”输出，已找到可用最佳候选卡或合规候选的疾病信号。\n"
            f"结果(可疑漏报卡).csv：按“就诊记录×门诊疾病信号”输出，未找到可用最佳候选卡的疾病信号。\n"
            f"结果(候选卡明细).csv：仅导出需要复核的相关候选/冲突/未入选候选，不重复导出已在主结果清楚表达的成功最佳卡。\n"
            f"医院门诊日志（疑似过度抵消）.csv：步骤1中匹配字段被排除字段完全抵消的记录，供维护正则库。\n\n"

            f"【七、人工复核提示】\n"
            f"{'─'*40}\n"
            f"1. “程序可疑漏报”不是最终漏报结论，需人工核实是否存在院内诊断变更、网报订正、跨门诊/住院报卡等情况。\n"
            f"2. “迟报”按程序选出的最佳候选卡和当前时间精度计算，若最佳候选卡不符合实际，应查看候选卡明细。\n"
            f"3. “负时间差合规候选”可能对应门诊转住院、先报卡后出院等业务场景，程序不自动判错。\n"
            f"4. “标签维护提示”说明门诊赋值匹配已识别疾病信号，但疾病标签库未完全覆盖，建议用于后续维护。\n"
            f"5. “疑似过度抵消记录”不会进入主分析结果，建议定期抽查，避免排除正则过宽导致漏筛。\n"
            f"{'='*60}"  # 底部总分隔线
            )

    if negative_delta > 0:
        # 警告信息单独排版，突出显示
        report += f"\n\n{'!'*60}\n"
        report += f"提示：发现 {negative_delta} 条负时间差候选，程序已保留且未自动判为错误。"
        report += f"\n{'!'*60}"

    with open(export_txt, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"{Color.SUCCESS} ✅ 步骤2完成：分析报告保存至 {export_txt.resolve()}")

def show_instructions():
    doc = f"""
{Color.BLUE}{'='*60}{Color.RESET}
{Color.GREEN}{Color.BOLD}【传染病报卡分析系统使用说明】{Color.RESET}
{Color.GRAY}*Python开源免费
官网：https://www.python.org/
{Color.RED}切勿相信其他下载渠道{Color.RESET}
{Color.BLUE}{'='*60}{Color.RESET}  
{Color.PURPLE}功能：{Color.RESET}自动筛选传染病门诊数据并分析报卡及时性
{Color.PURPLE}系统支持：{Color.RESET}Windows，MacOs，Linux
{Color.BLUE}{'-'*60}{Color.RESET} 
{Color.PURPLE}已测试通过Python版本：{Color.RESET}[3.9.6],[3.13.3]，[3.14+]
{Color.BLUE}{'-'*60}{Color.RESET} 
{Color.YELLOW}▶ 操作步骤：{Color.RESET}
1.  准备文件：
  - 医院门诊日志.csv{Color.RED}（必须列：姓名、身份证、诊断、就诊时间）{Color.RESET}
  - 大疫情网报卡.csv{Color.RED}（必须列：患者姓名、有效证件号、疾病名称、报告卡录入时间、卡片id）{Color.RESET}

2.  文件读取方式：
  - 步骤1可使用同目录默认门诊日志，也可通过弹窗选择任意门诊CSV
  - 步骤2固定读取步骤1生成的“医院门诊日志（筛选后）.csv”，只需要选择大疫情网报卡CSV
  - Linux无图形环境时，可将文件拖入终端或输入完整路径
  - 选择后程序会先验证必须字段，验证通过才继续运行

3.  同目录默认文件结构：
   ■ 文件夹
   ┣━ 医院门诊日志.csv
   ┣━ 大疫情网报卡.csv
   └─ [本程序].py

4.  运行脚本并选择运行步骤
{Color.BLUE}{'-'*60}{Color.RESET} 
{Color.YELLOW}▶ 执行结果逻辑：{Color.RESET}
 ■ 步骤1
    ■ 医院门诊日志（筛选后）.csv
    └─ 输出“门诊诊断有效信号数”>0的条目
{Color.RED}*  对筛选逻辑有疑问可咨询相关人员了解{Color.RESET}

 ■ 步骤2
 ├─ ■ 结果(已报告卡).csv
 │  ├─ 使用大疫情网数据与筛选后数据匹配
 │  └─ 每条就诊保留程序推荐的最佳候选卡
 │      * （姓名+身份证）与（患者姓名+有效证件号）精确全量匹配
 │      * 完全匹配失败时，支持“纯中文姓名+单个英文字母”网报后缀兼容
 │      * 外国人及中英文混合姓名不会删除英文字符
 │      * 结合原赋值信号、疾病相关度、时间距离和复诊期限推荐
 │      * 负时间差保留，不自动排除{Color.RESET}
 ├─ ■ 结果(可疑漏报卡).csv
 │  └─ 未找到可作为主要依据的候选卡
 └─ ■ 结果(候选卡明细).csv
    ├─ 保存姓名+身份证命中的全部历史卡
    ├─ 可用程序关联号返回查看同一就诊的所有候选卡
    └─ 程序关联号仅用于本次输出关联，不属于医院院内业务编号
{Color.BLUE}{'='*60}{Color.RESET}
"""
    print(doc)
    input(f"\n{Color.INFO} 按任意键返回主菜单...")

# ===================== 终端菜单渲染函数 =====================
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
MENU_CONTENT_WIDTH = 98


def strip_ansi(text):
    """移除终端颜色控制字符，用于计算显示宽度。"""
    return ANSI_PATTERN.sub("", str(text))


def display_width(text):
    """估算终端显示宽度；中文、框线和全角符号按2列计算。"""
    width = 0
    for char in strip_ansi(text):
        if unicodedata.east_asian_width(char) in {"F", "W"}:
            width += 2
        else:
            width += 1
    return width


def pad_display(text, target_width, align='c'):
    """按可见宽度补空格，同时保留字符串中的颜色控制字符。"""
    text = str(text).lstrip(" ")
    visible_width = display_width(text)
    padding = max(target_width - visible_width, 0)
    if align == 'l':
        return text + " " * padding
    if align == 'r':
        return " " * padding + text
    left = padding // 2
    right = padding - left
    return " " * left + text + " " * right


def create_table(rows, align='c', width=MENU_CONTENT_WIDTH):
    """创建固定宽度菜单框，避免不同分组因内容长短产生大小不一。"""
    top = "┌" + "─" * (width + 2) + "┐"
    bottom = "└" + "─" * (width + 2) + "┘"
    rendered_rows = [
        "│ " + pad_display(row, width, align=align) + " │"
        for row in rows
    ]
    return "\n".join([top, *rendered_rows, bottom])


def try_set_windows_terminal_size(cols=122, lines=35):
    """Windows双击运行.py时，尝试设置控制台窗口尺寸；不支持时静默跳过。"""
    if os.name != "nt":
        return
    try:
        os.system(f"mode con: cols={cols} lines={lines} >nul 2>nul")
        os.system(f"title CheckMiss {current_version} >nul 2>nul")
    except Exception:
        pass


def terminal_width_warning(min_width=106):
    """终端过窄时给出提示；外部终端窗口大小无法在所有系统中可靠强制修改。"""
    columns = shutil.get_terminal_size(fallback=(120, 30)).columns
    if columns < min_width:
        return (
            f"{Color.WARNING} 当前终端宽度约 {columns} 列，建议调整到 {min_width} 列以上，"
            f"以避免菜单或结果提示自动换行。{Color.RESET}\n"
        )
    return ""

# ===================== 全局业务配置 =====================
# 列名映射
COLUMN_MAPPING = {
    'clinic': {
        'name': '姓名',
        'id': '身份证',
        'diagnosis': '诊断',
        'visit_time': '就诊时间'
    },
    'report': {
        'name': '患者姓名',
        'id': '有效证件号',
        'disease': '疾病名称',
        'report_time': '报告卡录入时间',
        'card_id': '卡片ID'
    }
}

# 定义文件路径
files = {
    "门诊日志": Path("医院门诊日志.csv"),
    "初筛结果": Path("医院门诊日志（筛选后）.csv"),
    "网报卡": Path("大疫情网报卡.csv"),
    "结果文本": Path("报卡分析报告.txt"),
    "已报卡": Path("结果(已报告卡).csv"),
    "漏报卡": Path("结果(可疑漏报卡).csv"),
    "候选卡明细": Path("结果(候选卡明细).csv"),
    "重复条目": Path("结果(一卡多匹重复条目).csv")
}

# 初始化全局统计状态变量
stat_raw_data_count = None
stat_filtered_count = None
stat_disease_dist = None


# ===================== 跨平台文件选择与字段验证 =====================
def show_file_dialog_message(title, message, error=False):
    """尽量显示置顶提示框；无图形环境时静默退回终端提示。"""
    root = None
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        try:
            root.attributes("-topmost", True)
            root.lift()
            root.update()
        except Exception:
            pass
        if error:
            messagebox.showerror(title, message, parent=root)
        else:
            messagebox.showinfo(title, message, parent=root)
        return True
    except Exception as e:
        print(f"{Color.WARNING} 图形提示窗口不可用：{type(e).__name__}: {e}")
        return False
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


def choose_csv_with_dialog(role_name, required_cols):
    """弹窗选择CSV；Linux无图形环境或Tk不可用时返回None，由终端接管。"""
    required_text = "、".join(required_cols)
    notice = (
        f"下一步请选择【{role_name}】CSV文件。\n\n"
        f"必须包含字段：\n{required_text}"
    )
    root = None
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox

        root = tk.Tk()
        root.title(f"CheckMiss - 选择{role_name}")
        # macOS对完全隐藏的父窗口支持不稳定。保留一个几乎不可见的1×1父窗口，
        # 可避免文件选择框闪现后失去焦点或藏到VS Code后面。
        root.geometry("1x1+0+0")
        root.resizable(False, False)
        root.update_idletasks()
        try:
            root.attributes("-topmost", True)
            root.lift()
            root.focus_force()
            root.update()
        except Exception:
            pass
        messagebox.showinfo(f"选择{role_name}", notice, parent=root)
        try:
            root.lift()
            root.focus_force()
            root.update()
        except Exception:
            pass
        selected = filedialog.askopenfilename(
            parent=root,
            title=f"请选择【{role_name}】CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        return Path(selected) if selected else False
    except Exception as e:
        print(
            f"{Color.WARNING} 图形文件选择窗口不可用："
            f"{type(e).__name__}: {e}"
        )
        return None
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


def parse_terminal_path(raw_path):
    """兼容Linux/macOS将文件拖入终端后产生的引号或反斜杠转义。"""
    raw_path = raw_path.strip()
    if not raw_path:
        return None
    try:
        parsed = shlex.split(raw_path)
        if parsed:
            return Path(parsed[0]).expanduser()
    except ValueError:
        pass
    return Path(raw_path.strip("'\"")).expanduser()


def choose_csv_from_terminal(role_name, required_cols):
    required_text = "、".join(required_cols)
    print(
        f"\n{Color.WARNING} 当前环境无法打开图形文件选择窗口。\n"
        f"{Color.INFO} 请将【{role_name}】CSV文件拖入终端，或输入完整路径。\n"
        f"{Color.INFO} 必须字段：{required_text}\n"
        f"{Color.INFO} 直接回车可取消并返回主菜单。"
    )
    return parse_terminal_path(input("文件路径："))


def infer_csv_role(columns):
    """根据表头推断CSV文件角色，仅用于选错文件时给出友好提示。"""
    headers = set(map(str, columns))
    clinic_cols = {
        COLUMN_MAPPING['clinic']['name'],
        COLUMN_MAPPING['clinic']['id'],
        COLUMN_MAPPING['clinic']['diagnosis'],
        COLUMN_MAPPING['clinic']['visit_time']
    }
    report_cols = {
        COLUMN_MAPPING['report']['name'],
        COLUMN_MAPPING['report']['id'],
        COLUMN_MAPPING['report']['disease'],
        COLUMN_MAPPING['report']['report_time'],
        COLUMN_MAPPING['report']['card_id']
    }
    if clinic_cols <= headers:
        return "筛选后医院门诊日志"
    if report_cols <= headers:
        return "大疫情网报卡文件"
    if len(headers & clinic_cols) >= 2 and len(headers & report_cols) == 0:
        return "可能是医院门诊日志"
    if len(headers & report_cols) >= 3 and len(headers & clinic_cols) == 0:
        return "可能是大疫情网报卡文件"
    return "未知文件类型"


def request_and_validate_csv(default_path, role_name, required_cols):
    """选择、读取并验证文件；返回(path, data)，取消时返回(None, None)。"""
    required_cols = list(required_cols)
    while True:
        if Path(default_path).exists():
            print(
                f"\n{Color.INFO} 【{role_name}】文件来源：\n"
                f"  1. 使用同目录默认文件：{Path(default_path).name}\n"
                f"  2. 自己选择CSV文件\n"
                f"  3. 取消并返回主菜单"
            )
            choice = input("输入选项（1/2/3）：").strip()
            if choice == "1":
                selected_path = Path(default_path)
            elif choice == "2":
                selected_path = choose_csv_with_dialog(role_name, required_cols)
                if selected_path is None:
                    selected_path = choose_csv_from_terminal(role_name, required_cols)
                elif selected_path is False:
                    return None, None
            elif choice == "3":
                return None, None
            else:
                print(f"{Color.ERROR} 请输入1、2或3")
                continue
        else:
            print(
                f"\n{Color.WARNING} 未找到【{role_name}】同目录默认文件："
                f"{Path(default_path).name}\n"
                f"{Color.INFO} 请先选择下一步操作：\n"
                f"  1. 自己选择【{role_name}】CSV文件\n"
                f"  2. 取消并返回主菜单"
            )
            choice = input("输入选项（1/2）：").strip()
            if choice == "1":
                selected_path = choose_csv_with_dialog(role_name, required_cols)
                if selected_path is None:
                    selected_path = choose_csv_from_terminal(role_name, required_cols)
                elif selected_path is False:
                    return None, None
            elif choice == "2":
                return None, None
            else:
                print(f"{Color.ERROR} 请输入1或2")
                continue

        if selected_path is None:
            return None, None
        if not selected_path.exists() or not selected_path.is_file():
            error_message = f"文件不存在或不是有效文件：\n{selected_path}"
            print(f"{Color.ERROR} {error_message}")
            show_file_dialog_message("文件选择错误", error_message, error=True)
            continue
        if selected_path.suffix.lower() != ".csv":
            error_message = f"请选择CSV文件，当前文件为：\n{selected_path.name}"
            print(f"{Color.ERROR} {error_message}")
            show_file_dialog_message("文件格式错误", error_message, error=True)
            continue

        try:
            selected_data = read_data(selected_path)
        except Exception as e:
            error_message = f"无法读取【{role_name}】：\n{str(e)}"
            print(f"{Color.ERROR} {error_message}")
            show_file_dialog_message("文件读取失败", error_message, error=True)
            continue

        missing_cols = set(required_cols) - set(selected_data.columns)
        if missing_cols:
            inferred_role = infer_csv_role(selected_data.columns)
            if inferred_role != "未知文件类型" and inferred_role != role_name:
                error_message = (
                    f"当前正在选择【{role_name}】，但所选文件表头更像【{inferred_role}】。\n\n"
                    f"你可能选错了文件，请重新选择【{role_name}】CSV。\n\n"
                    f"【{role_name}】必须字段：\n"
                    f"{'、'.join(required_cols)}\n\n"
                    f"当前识别字段：\n{'、'.join(map(str, selected_data.columns))}"
                )
                print(f"{Color.ERROR} {error_message}")
                show_file_dialog_message("疑似选错文件", error_message, error=True)
                continue
            error_message = (
                f"【{role_name}】缺少必须字段：\n"
                f"{'、'.join(sorted(missing_cols))}\n\n"
                f"当前识别字段：\n{'、'.join(map(str, selected_data.columns))}"
            )
            print(f"{Color.ERROR} {error_message}")
            show_file_dialog_message("字段验证失败", error_message, error=True)
            continue

        print(f"{Color.SUCCESS} 已选择并验证【{role_name}】：{selected_path.resolve()}")
        return selected_path, selected_data


def read_and_validate_default_csv(default_path, role_name, required_cols):
    """步骤内固定读取默认文件；不弹窗选择，避免用户误选其他角色文件。"""
    default_path = Path(default_path)
    required_cols = list(required_cols)
    if not default_path.exists() or not default_path.is_file():
        raise FileNotFoundError(
            f"未找到【{role_name}】默认文件：{default_path.name}\n"
            f"请先运行步骤1生成该文件，或确认文件位于程序同目录。"
        )
    selected_data = read_data(default_path)
    missing_cols = set(required_cols) - set(selected_data.columns)
    if missing_cols:
        inferred_role = infer_csv_role(selected_data.columns)
        role_hint = (
            f"\n当前文件表头更像【{inferred_role}】。"
            if inferred_role != "未知文件类型" and inferred_role != role_name else ""
        )
        raise ValueError(
            f"【{role_name}】默认文件字段验证失败：{default_path.name}\n"
            f"缺少必须字段：{'、'.join(sorted(missing_cols))}"
            f"{role_hint}\n\n"
            f"当前识别字段：\n{'、'.join(map(str, selected_data.columns))}"
        )
    print(f"{Color.SUCCESS} 已自动读取并验证【{role_name}】：{default_path.resolve()}")
    return default_path, selected_data


def main():
    global stat_raw_data_count, stat_filtered_count, stat_disease_dist
    try_set_windows_terminal_size()
    while True:
        try:
            # 主菜单分组内容。
            group1 = [
                f"{Color.GREEN}{Color.BOLD} ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███╗   ███╗██╗███████╗███████╗{Color.RESET}",
                f"{Color.GREEN}{Color.BOLD}██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝████╗ ████║██║██╔════╝██╔════╝{Color.RESET}",
                f"{Color.GREEN}{Color.BOLD}██║     ███████║█████╗  ██║     █████╔╝ ██╔████╔██║██║███████╗███████╗{Color.RESET}",
                f"{Color.GREEN}{Color.BOLD}██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██║╚██╔╝██║██║╚════██║╚════██║{Color.RESET}",
                f"{Color.GREEN}{Color.BOLD}╚██████╗██║  ██║███████╗╚██████╗██║  ██╗██║ ╚═╝ ██║██║███████║███████║{Color.RESET}",
                f"{Color.GREEN}{Color.BOLD} ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚══════╝╚══════╝{Color.RESET}",
                f"{Color.CYAN}{Color.BOLD}CheckMiss 传染病报卡分析工具 · {current_version}{Color.RESET}",
                f"{Color.CYAN}Author & Maintainer: YueXiuCDC-LGY · MIT License{Color.RESET}"
            ]

            group2 = [
                f"{Color.RED}疾控中心/医疗机构{Color.RESET}",
                f"{Color.RED}【内部使用】{Color.RESET}",
                f"{Color.RESET}* * * 报错请先查看说明文档排查 * * *{Color.RESET}"
            ]

            # group3 左对齐
            group3 = [
                f"{Color.YELLOW}#表头列名必须严格一致；步骤2固定读取步骤1生成的筛选后文件{Color.RESET}",
                f"{Color.YELLOW}{Color.RED}*同目录自动读取时才要求使用默认文件名*{Color.RESET}",
                f"{Color.YELLOW}■ 默认文件及必须字段{Color.RESET}",
                f"{Color.YELLOW}├─ ※【医院门诊日志.csv】 ➡➡ 首行为表头{Color.RESET}",
                f"{Color.YELLOW}│    必须列：{Color.RED}姓名、身份证、诊断、就诊时间{Color.RESET}",
                f"{Color.YELLOW}└─ ※【大疫情网报卡.csv】 ➡➡ 导出后无需修改{Color.RESET}",
                f"{Color.YELLOW}     必须列：{Color.RED}患者姓名、有效证件号、疾病名称、报告卡录入时间、卡片ID{Color.RESET}"
            ]

            # group4 左对齐
            group4 = [
                f"{Color.BOLD}■ 步骤{Color.RESET}",
                f"{Color.BLUE}{Color.BOLD}1.{Color.RESET}{Color.BLUE}{Color.BOLD} 根据字段初筛门诊日志数据{Color.RESET}",
                f"{Color.BLUE}{Color.BOLD}2.{Color.RESET}{Color.BLUE}{Color.BOLD} 分析报卡及时性（需先完成步骤1）{Color.RESET}",
                f"{Color.YELLOW}{Color.BOLD}3.{Color.RESET}{Color.YELLOW}{Color.BOLD} 查看说明文档{Color.RESET}",
                f"{Color.PURPLE}{Color.BOLD}4.{Color.RESET}{Color.PURPLE}{Color.BOLD} 检查更新并显示版本信息{Color.RESET}",
                f"{Color.GREEN}{Color.BOLD}5.{Color.RESET}{Color.GREEN}{Color.BOLD} 退出程序{Color.RESET}"
            ]

            # 使用prettytable渲染终端菜单。
            table1 = create_table(group1, align='c')
            table2 = create_table(group2, align='c')
            table3 = create_table(group3, align='l')  
            table4 = create_table(group4, align='l')

            # 组合表格并获取输入
            combined = f"{terminal_width_warning()}{table1}\n{table2}\n{table3}\n{table4}"
            step = input(f"{combined}\n {Color.INFO} 输入步骤: {Color.RESET}").strip()

            if step == '5':
                print(f"{Color.INFO} 程序退出...")
                break

            if step == '1':
                clinic_required_cols = [
                    COLUMN_MAPPING['clinic']['name'],
                    COLUMN_MAPPING['clinic']['id'],
                    COLUMN_MAPPING['clinic']['diagnosis'],
                    COLUMN_MAPPING['clinic']['visit_time']
                ]
                clinic_path, data = request_and_validate_csv(
                    files['门诊日志'],
                    "医院门诊日志",
                    clinic_required_cols
                )
                if clinic_path is None:
                    print(f"{Color.INFO} 已取消文件选择，返回主菜单")
                    continue
                # 执行筛选，结果输出到锚定路径
                stat_raw_data_count, stat_filtered_count, stat_disease_dist = select_data(data, files["初筛结果"])
                input(f"\n{Color.INFO} 按任意键返回主菜单...{Color.RESET}")

            elif step == '2':
                clinic_required_cols = [
                    COLUMN_MAPPING['clinic']['name'],
                    COLUMN_MAPPING['clinic']['id'],
                    COLUMN_MAPPING['clinic']['diagnosis'],
                    COLUMN_MAPPING['clinic']['visit_time']
                ]
                report_required_cols = [
                    COLUMN_MAPPING['report']['name'],
                    COLUMN_MAPPING['report']['id'],
                    COLUMN_MAPPING['report']['disease'],
                    COLUMN_MAPPING['report']['report_time'],
                    COLUMN_MAPPING['report']['card_id']
                ]

                try:
                    filtered_path, filtered_data = read_and_validate_default_csv(
                        files['初筛结果'],
                        "筛选后医院门诊日志",
                        clinic_required_cols
                    )
                except Exception as e:
                    error_message = (
                        f"{str(e)}\n\n"
                        f"步骤2固定读取步骤1生成的【{Path(files['初筛结果']).name}】，"
                        f"不再手动选择该文件。"
                    )
                    print(f"{Color.ERROR} {error_message}")
                    show_file_dialog_message("筛选后文件不可用", error_message, error=True)
                    input(f"\n{Color.INFO} 按任意键返回主菜单...{Color.RESET}")
                    continue

                print(f"{Color.INFO} 步骤2将使用上述筛选后文件；接下来请选择【大疫情网报卡】。")
                report_path, report_data = request_and_validate_csv(
                    files['网报卡'],
                    "大疫情网报卡",
                    report_required_cols
                )
                if report_path is None:
                    print(f"{Color.INFO} 已取消文件选择，返回主菜单")
                    continue
                
                time_unit = input(f"{Color.INFO} 输入时间精度（d=天/h=小时）: {Color.RESET}").strip().lower()
                while time_unit not in {'d', 'h'}:
                    time_unit = input(f"{Color.ERROR} 错误：请输入 d 或 h: {Color.RESET}").strip().lower()
                
                data_match = match_two_database(
                    filtered_path,
                    report_path,
                    data1=filtered_data,
                    data2=report_data
                )
                if data_match is not None:
                    analysis(
                        data_match, 
                        files["结果文本"], 
                        files["已报卡"], 
                        files["漏报卡"], 
                        files["重复条目"], 
                        time_unit=time_unit,
                        raw_data_count=stat_raw_data_count if stat_raw_data_count is not None else len(filtered_data),
                        filtered_count=stat_filtered_count if stat_filtered_count is not None else len(filtered_data),
                        disease_distribution=stat_disease_dist if stat_disease_dist is not None else {}
                    )
                input(f"\n{Color.INFO} 按任意键返回主菜单...{Color.RESET}")

            elif step == '3':
                show_instructions()

            elif step == '4':
                check_update()

            else:
                raise ValueError(f"{Color.ERROR} 请输入有效步骤（1/2/3/4/5）{Color.RESET}")
        
        # 统一捕获常见异常，避免终端窗口直接退出。
        except FileNotFoundError as e:
            print(f"\n{Color.ERROR} 文件错误：{str(e)}")
            input(f"{Color.INFO} 按任意键返回主菜单...{Color.RESET}")
        except ValueError as e:
            print(f"\n{Color.ERROR} 输入错误：{str(e)}")
            input(f"{Color.INFO} 按任意键返回主菜单...{Color.RESET}")
        except Exception as e:
            print(f"\n{Color.ERROR} 程序异常：{str(e)}")
            # 调试时可临时打印完整堆栈：print(f"{Color.WARNING} 异常详情：{traceback.format_exc()}")
            input(f"{Color.INFO} 按任意键返回主菜单...{Color.RESET}")

# ===================== 程序入口 =====================
if __name__ == "__main__":
    # 先检查依赖库
    required_libs = ['pandas', 'python-dateutil', 'chardet', 'requests', 'prettytable', 'tqdm', 'packaging']
    if install_libraries(required_libs):
        # 依赖安装完成后导入剩余模块（避免提前导入报错）
        import pandas as pd
        import chardet
        from dateutil.parser import parse
        from tqdm import tqdm
        # 启动主菜单
        main()
