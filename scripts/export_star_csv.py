"""把 MySQL 星型表导出为 Power BI 可读取的 CSV。"""
from __future__ import annotations

import pandas as pd

from common import STAR_DIR, ensure_output_dirs, mysql_engine


TABLES = ["fact_order_item", "dim_customer", "dim_product", "dim_date"]


def main() -> None:
    ensure_output_dirs()
    engine = mysql_engine()
    for table in TABLES:
        frame = pd.read_sql(f"SELECT * FROM `{table}`", engine)
        output = STAR_DIR / f"{table}.csv"
        frame.to_csv(output, index=False, encoding="utf-8")
        print(f"[导出] {table}: {len(frame):,} 行 -> {output.relative_to(STAR_DIR.parent.parent)}")
    print("[OK] 四张星型表 CSV 已生成")


if __name__ == "__main__":
    main()

