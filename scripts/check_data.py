"""检查复现所需的 Kaggle 原始数据是否齐全且结构正确。"""
from __future__ import annotations

import sys

import pandas as pd

from common import RAW_DIR


DATASET_URL = (
    "https://www.kaggle.com/datasets/shashwatwork/"
    "dataco-smart-supply-chain-for-big-data-analysis"
)
MAIN_FILE = RAW_DIR / "DataCoSupplyChainDataset.csv"
DESCRIPTION_FILE = RAW_DIR / "DescriptionDataCoSupplyChain.csv"


def main() -> int:
    missing = [path for path in (MAIN_FILE, DESCRIPTION_FILE) if not path.exists()]
    if missing:
        print("缺少复现所需的数据文件：")
        for path in missing:
            print(f"  - {path.relative_to(RAW_DIR.parent.parent)}")
        print(f"请从 Kaggle 下载并解压到 data/raw/：{DATASET_URL}")
        return 2

    header = pd.read_csv(MAIN_FILE, encoding="latin-1", nrows=5)
    required_columns = {
        "Order Item Id",
        "Order Id",
        "Product Card Id",
        "Customer Id",
        "order date (DateOrders)",
        "Sales",
        "Order Profit Per Order",
        "Late_delivery_risk",
    }
    missing_columns = sorted(required_columns.difference(header.columns))
    if missing_columns:
        print("主数据缺少关键字段：", ", ".join(missing_columns))
        return 3

    with MAIN_FILE.open("rb") as fh:
        rows = sum(chunk.count(b"\n") for chunk in iter(lambda: fh.read(1024 * 1024), b"")) - 1
    if rows != 180_519:
        print(f"主数据行数异常：{rows:,}，预期 180,519")
        return 4

    print(f"[OK] 原始数据齐全：180,519 行 × {len(header.columns)} 列，编码 latin-1")
    print("[INFO] tokenized_access_logs.csv 不参与本项目，无需下载或公开")
    return 0


if __name__ == "__main__":
    sys.exit(main())

