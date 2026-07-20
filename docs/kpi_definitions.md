# KPI 口径定义

本文档定义项目使用的核心指标、数据粒度和过滤条件。数据源为 `dataco.fact_order_item`，共 180,519 个订单行。履约指标按订单级计算，金额、数量和利润指标按订单行级聚合。

## 订单状态过滤规则

| 业务状态 | 字段条件 | 订单行数 | 指标处理 |
|---|---|---:|---|
| 发货取消 | `delivery_status = 'Shipping canceled'` | 7,754 | 不进入履约指标分母 |
| 订单未成交 | `order_status IN ('CANCELED','SUSPECTED_FRAUD')` | 7,754 | 不进入 GMV、净收入和利润率 |

取消订单没有实际交付结果，因此不计入迟发率、准时率和平均履约周期。亏损结构分析使用全量订单行，以反映数据集中记录的全部正负利润。

## 核心 KPI

### 1. 迟发率（Late Delivery Rate）

- **定义**：有效发货订单中发生迟发的订单比例。
- **分子**：`COUNT(DISTINCT order_id WHERE late_delivery_risk = 1)`。
- **分母**：`COUNT(DISTINCT order_id WHERE delivery_status <> 'Shipping canceled')`。
- **粒度**：订单级。
- **结果**：36,048 / 62,897 = **57.31%**。
- **一致性检查**：使用 `days_for_shipping_real > days_for_shipment_scheduled` 独立重算后，与 `late_delivery_risk` 的订单行级一致率为 97.5%。4,423 个差异订单行全部属于取消订单。

### 2. 准时交付率（On-Time Delivery, OTD）

- **公式**：`COUNT(DISTINCT order_id WHERE delivery_status IN ('Shipping on time','Advance shipping')) / 有效发货订单数`。
- **粒度**：订单级。
- **结果**：**42.69%**。
- **数据限制**：数据集不包含齐套交付字段，因此该指标为 OTD，不是完整 OTIF。

### 3. 平均履约周期（Average Fulfillment Cycle）

- **公式**：有效发货订单的 `AVG(days_for_shipping_real)`。
- **粒度**：订单级，同一订单只保留一个履约周期值。
- **结果**：**3.50 天**。

### 4. 销售额（GMV）

- **公式**：`SUM(sales)`。
- **粒度**：订单行级。
- **过滤条件**：`order_status NOT IN ('CANCELED','SUSPECTED_FRAUD')`。
- **结果**：**3,521.44 万**。
- **字段含义**：`sales` 为折扣前金额，用于表示交易规模。

### 5. 净收入（Net Revenue）

- **公式**：`SUM(order_item_total)`。
- **粒度**：订单行级。
- **过滤条件**：与 GMV 相同。
- **结果**：**3,164.47 万**。
- **字段含义**：`order_item_total` 为折扣后实收金额。GMV 与净收入的差额约为 357 万，对应折扣金额。

### 6. 利润率（Profit Margin）

- **公式**：`SUM(order_profit_per_order) / SUM(order_item_total)`。
- **粒度**：订单行级汇总。
- **过滤条件**：排除 `CANCELED` 和 `SUSPECTED_FRAUD`。
- **结果**：380.6 万 / 3,164.47 万 = **12.03%**。
- **计算说明**：分母使用折后净收入，与数据集行级利润率的收入基础保持一致。汇总利润率采用总利润除以总净收入，不对行级利润率直接求平均。

### 7. 亏损订单行占比（Loss Order Item Ratio）

- **公式**：`COUNT(WHERE order_profit_per_order < 0) / COUNT(*)`。
- **粒度**：订单行级。
- **过滤条件**：全量订单行。
- **结果**：33,784 / 180,519 = **18.71%**。
- **业务含义**：衡量亏损在订单行数量上的覆盖范围，不区分单笔亏损金额大小。

### 8. 盈利侵蚀率（Profit Erosion Rate）

- **亏损金额**：`SUM(order_profit_per_order WHERE order_profit_per_order < 0)`。
- **盈利金额**：`SUM(order_profit_per_order WHERE order_profit_per_order > 0)`。
- **公式**：亏损金额绝对值 ÷ 盈利金额。
- **粒度与过滤条件**：订单行级，全量订单行。
- **结果**：388.4 万 / 785.0 万 = **49.5%**。

该指标衡量负利润订单行对正利润的抵消程度。全量订单行的净利润为 396.7 万；排除未成交订单后的利润为 380.6 万，后者用于利润率计算。

### 9. 深亏订单行

- **定义**：`order_item_profit_ratio < -50%`。
- **粒度**：订单行级。
- **结果**：15,695 行，占全部订单行 **8.69%**，亏损金额 331 万，占全部亏损 **85.3%**。
- **边界规则**：利润率等于 -50% 的 108 个订单行归入中度亏损，不进入深亏订单行。

### 10. XYZ 需求波动分类

- **需求周期**：周。
- **波动指标**：周需求变异系数 `CV = σ / μ`。
- **补零范围**：每个 SKU 从首个销售周到最后一个销售周的在售窗口。
- **样本条件**：在售窗口不少于 8 周。
- **结果**：102 个可测算 SKU，其中 X 17 个、Y 70 个、Z 15 个；另有 16 个 SKU 历史不足。

## 口径汇总

| KPI | 分子或聚合项 | 分母 | 粒度 | 过滤条件 | 结果 |
|---|---|---|---|---|---|
| 迟发率 | 迟发订单数 | 有效发货订单数 | 订单级 | 排除 Shipping canceled | 57.31% |
| 准时率 | 准时或提前订单数 | 有效发货订单数 | 订单级 | 排除 Shipping canceled | 42.69% |
| 平均履约周期 | 实际配送天数合计 | 有效发货订单数 | 订单级 | 排除 Shipping canceled | 3.50 天 |
| GMV | `SUM(sales)` | — | 订单行级 | 排除未成交 | 3,521.44 万 |
| 净收入 | `SUM(order_item_total)` | — | 订单行级 | 排除未成交 | 3,164.47 万 |
| 利润率 | 总利润 | 总净收入 | 订单行级 | 排除未成交 | 12.03% |
| 亏损订单行占比 | 亏损订单行数 | 全部订单行数 | 订单行级 | 全量 | 18.71% |
| 盈利侵蚀率 | 亏损金额绝对值 | 盈利金额 | 订单行级 | 全量 | 49.5% |
