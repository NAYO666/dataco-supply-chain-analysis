"""独立复算数据模型与核心 KPI；任何关键结果不一致时返回失败。"""
from __future__ import annotations

import math

import pandas as pd

from common import STAR_DIR


EXPECTED_ROWS = {
    "fact_order_item": 180_519,
    "dim_customer": 20_652,
    "dim_product": 118,
    "dim_date": 1_127,
}


def close(actual: float, expected: float, tolerance: float = 0.01) -> None:
    if not math.isclose(actual, expected, abs_tol=tolerance):
        raise AssertionError(f"结果不一致：actual={actual}, expected={expected}")


def main() -> None:
    paths = {name: STAR_DIR / f"{name}.csv" for name in EXPECTED_ROWS}
    missing = [path for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("缺少星型 CSV，请先运行 scripts/export_star_csv.py")

    fact = pd.read_csv(paths["fact_order_item"], low_memory=False)
    customers = pd.read_csv(paths["dim_customer"])
    products = pd.read_csv(paths["dim_product"])
    dates = pd.read_csv(paths["dim_date"])
    frames = {
        "fact_order_item": fact,
        "dim_customer": customers,
        "dim_product": products,
        "dim_date": dates,
    }

    for name, expected in EXPECTED_ROWS.items():
        actual = len(frames[name])
        assert actual == expected, f"{name} 行数 {actual:,} != {expected:,}"
        assert frames[name].isna().sum().sum() == 0, f"{name} 存在空值"

    assert fact["order_item_id"].is_unique
    assert customers["customer_id"].is_unique
    assert products["product_card_id"].is_unique
    assert dates["date_key"].is_unique
    assert fact["customer_id"].isin(customers["customer_id"]).all()
    assert fact["product_card_id"].isin(products["product_card_id"]).all()
    assert fact["order_date_key"].astype(str).isin(dates["date_key"].astype(str)).all()

    valid_orders = (
        fact[fact["delivery_status"] != "Shipping canceled"]
        .drop_duplicates("order_id")
        .copy()
    )
    assert len(valid_orders) == 62_897
    assert int(valid_orders["late_delivery_risk"].sum()) == 36_048
    close(valid_orders["late_delivery_risk"].mean() * 100, 57.3127, 0.001)
    close(valid_orders["days_for_shipping_real"].mean(), 3.5015, 0.001)

    traded = ~fact["order_status"].isin(["CANCELED", "SUSPECTED_FRAUD"])
    gmv = fact.loc[traded, "sales"].sum()
    net_revenue = fact.loc[traded, "order_item_total"].sum()
    profit = fact.loc[traded, "order_profit_per_order"].sum()
    close(gmv, 35_214_429.65, 0.1)
    close(net_revenue, 31_644_665.08, 0.1)
    close(profit, 3_806_420.63, 0.1)
    close(profit / net_revenue * 100, 12.0286, 0.001)

    loss_rows = fact["order_profit_per_order"] < 0
    assert int(loss_rows.sum()) == 33_784
    close(loss_rows.mean() * 100, 18.7149, 0.001)

    print("[OK] 行数、主键、外键、空值与核心 KPI 全部通过")
    print("  迟发率（订单级）: 36,048 / 62,897 = 57.31%")
    print("  GMV / 净收入: 3,521.44 万 / 3,164.47 万")
    print("  利润率: 12.03% | 亏损订单行占比: 18.71%")


if __name__ == "__main__":
    main()

