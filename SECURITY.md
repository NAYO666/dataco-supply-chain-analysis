# 安全与隐私

- 真实数据库连接信息只保存在本机 `.env`，该文件已由 `.gitignore` 排除。
- 公开仓库只提交 `.env.example`，其中只能出现占位符。
- 原始 CSV、星型 CSV、访问日志和 Jupyter 检查点不进入 Git。
- `tokenized_access_logs.csv` 含 IPv4 格式地址，当前分析不使用，不应公开。
- 如果真实密码曾进入 Git 历史，应立即更换密码，并清理完整历史；仅删除当前文件不够。
- 提交前必须运行 `python scripts/security_check.py` 和 `git diff --cached`。

Power BI 发布副本使用 CSV Import 模式。公开前应在 Power BI Desktop 的“数据源设置”中
检查数据源并清除不需要的本机权限，不在 PBIX 中配置私人数据库账号。
