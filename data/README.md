# 数据文件说明

本目录中的 CSV 不进入 Git 仓库。复现者需要从 Kaggle 的
[DataCo Smart Supply Chain](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis)
数据集下载以下两个文件并放入 `data/raw/`：

- `DataCoSupplyChainDataset.csv`
- `DescriptionDataCoSupplyChain.csv`

主数据读取编码为 `latin-1`。`tokenized_access_logs.csv` 是商品网页访问日志，含 IP
字段，当前三个业务判断未使用它，因此无需下载或公开。

运行 `python scripts/check_data.py` 可检查数据文件、字段和行数。运行完整复现流程后，
`data/star_csv/` 会自动生成 Power BI 使用的四张星型表 CSV。
