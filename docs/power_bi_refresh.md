# Power BI 查看与刷新说明

## 直接查看

`power bi/power bi看板.pbix` 使用 Import 模式，演示数据已经嵌入文件。下载仓库后可直接打开两页看板，无需数据库凭据，也无需先运行数据管道。

## 用自己的复现数据刷新

1. 先在仓库根目录运行 `python scripts/reproduce.py`，或至少运行到 `python scripts/export_star_csv.py`。成功后，`data/star_csv/` 中会生成：
   - `fact_order_item.csv`
   - `dim_customer.csv`
   - `dim_product.csv`
   - `dim_date.csv`
2. 在 Power BI Desktop 打开 `power bi/power bi看板.pbix`。
3. 进入“文件 → 选项和设置 → 数据源设置”，选择当前文件的数据源并点击“更改源”。把路径改到本机仓库的 `data/star_csv/`。
4. 依次确认四张表对应同名 CSV，然后点击“刷新”。刷新后核对以下指标：
   - 订单级迟发率：57.31%
   - GMV：3,521.44 万
   - 净收入：3,164.47 万
   - 利润率：12.03%
   - 亏损订单行占比：18.71%
5. 如果 Power BI 仍缓存旧位置，进入“数据源设置 → 清除权限”，再重新选择本机 `data/star_csv/` 文件。

## 凭据边界

- 推荐让 Power BI 读取自动生成的星型 CSV；这样 pbix 不需要保存 MySQL 用户名或密码。
- MySQL 凭据只保存在本机 `.env` 中；`.env` 已被 `.gitignore` 排除。
- 不要把包含个人数据库地址、网关配置或组织账号的 pbix 另存后直接提交。提交前应再次打开“数据源设置”检查数据源，并运行 `python scripts/security_check.py`。

## 口径说明

Power BI 页面中的核心指标均与 SQL 和 pandas 结果交叉核对一致。履约率按订单级去重计算；迟发量占比、GMV、利润和库存资金等可加指标按订单行级或 SKU 级聚合，详细定义见 [kpi_definitions.md](kpi_definitions.md)。
