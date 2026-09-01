# CheckMiss

院内记录与网报卡辅助核查工具。

CheckMiss 是一个可直接用 Python 运行的 CSV 批量核查脚本，用于辅助比对院内业务记录与网报卡数据，减少人工逐条检索的工作量。项目不提供打包程序；发布版 `.py` 文件请在 GitHub Releases 或 Gitee Releases 中下载。

## 下载与运行

普通用户建议从 Releases 下载最新 `.py` 文件：

- GitHub Releases: <https://github.com/KwoYeung/checkmiss/releases>
- Gitee Releases: <https://gitee.com/KwoYeung/checkmiss/releases>

下载后可在终端运行：

```bash
python CheckMiss-v10.1.6.py
```

也可以在已配置 Python 的系统中双击运行。首次运行时，程序会检查依赖库，并按提示选择安装源。

## 当前源码

`main` 分支只保留当前推荐源码和维护工具：

- `CheckMiss-v10.1.6.py`：当前推荐版本，可直接运行。
- `一键卸载依赖库.py`：依赖异常时使用的辅助工具。
- `.github/workflows/sync-to-gitee.yml`：GitHub 到 Gitee 的同步流程。

历史可运行版本不再放在 `main` 根目录中，避免用户下载时混淆；需要回退时请查看 Releases。

## 输入文件要求

程序运行时会提示选择或读取 CSV 文件。常用字段包括：

- 院内记录：`姓名`、`身份证`、`诊断`、`就诊时间`
- 网报卡：`患者姓名`、`有效证件号`、`疾病名称`、`报告卡录入时间`、`卡片ID`

请勿将真实业务数据提交到公开仓库。

## 主要功能

- 院内记录规则筛选，并输出筛选后 CSV。
- 姓名与证件号匹配，支持中文姓名后缀兼容。
- 按疾病信号拆分主结果，适配一条记录包含多个病种提示的场景。
- 结合候选卡、报告时间、复诊周期生成辅助判定。
- 输出已报告/合规候选、可疑漏报、候选卡明细和文本统计报告。
- 对卡片 ID、疾病信号序号等字段做 Excel 文本保护，减少自动转格式问题。
- 提供独立依赖卸载工具，便于环境异常时重装依赖。

## v10.1.6 更新摘要

- 修复候选明细为空时的统计异常。
- 调整判定说明，避免通用负时间差提示造成误解。
- 更新复诊周期：梅毒 12 个月，生殖道沙眼衣原体感染 3 个月，尖锐湿疣 6 个月，生殖器疱疹终生。
- 增强肺结核相关标签识别，支持涂阳、涂（+）、菌阴、菌（-）、培阳等表达。
- 修复 `疾病信号序号` 被 Excel 识别成日期的问题。

## 同步到 Gitee

本仓库包含 GitHub Actions workflow，可在推送到 GitHub `main` 分支后同步到 Gitee。

需要在 GitHub 仓库设置中配置：

- Repository variables:
  - `GITEE_OWNER`
  - `GITEE_REPO`
- Repository secrets:
  - `GITEE_TOKEN`

## 许可证

MIT License
