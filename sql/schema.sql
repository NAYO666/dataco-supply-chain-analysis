-- =====================================================================
-- schema.sql — DataCo 供应链项目星型模型 DDL
-- 库：dataco   |   源：stg_orders（清洗后 staging 宽表，180519 行 × 31 列）
-- 模型：fact_order_item（事实表，粒度=订单行）
--       + dim_customer / dim_product / dim_date（3 张维表）
-- 运行：MySQL 8.0，按顺序执行（先维表→再事实表→加外键→校验）
-- =====================================================================
USE dataco;

-- ---------------------------------------------------------------------
-- 1. 维表：客户维（清洗后仅剩 客群 一个属性；一客户对一客群，20652 行）
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS fact_order_item;   -- 有外键，先删事实表再删维表
DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer AS
SELECT DISTINCT customer_id, customer_segment
FROM stg_orders;
ALTER TABLE dim_customer ADD PRIMARY KEY (customer_id);

-- ---------------------------------------------------------------------
-- 2. 维表：商品维（部门 > 品类 > 商品 三级层级 + 单价，118 行）
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product AS
SELECT DISTINCT product_card_id, product_name,
       category_id, category_name,
       department_id, department_name, product_price
FROM stg_orders;
ALTER TABLE dim_product ADD PRIMARY KEY (product_card_id);

-- ---------------------------------------------------------------------
-- 3. 维表：日期维（从 order_date 拆年/季/月/日/星期，1127 行）
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date AS
SELECT DISTINCT
       DATE(order_date)      AS date_key,    -- 去时分秒，主键
       YEAR(order_date)      AS year,
       QUARTER(order_date)   AS quarter,
       MONTH(order_date)     AS month,
       MONTHNAME(order_date) AS month_name,
       DAY(order_date)       AS day,
       DAYNAME(order_date)   AS weekday
FROM stg_orders;
ALTER TABLE dim_date ADD PRIMARY KEY (date_key);

-- ---------------------------------------------------------------------
-- 4. 事实表：order_item 粒度（180519 行）
--    = 主键 + 3 外键 + 度量值 + 履约/订单属性
-- ---------------------------------------------------------------------
CREATE TABLE fact_order_item AS
SELECT
  order_item_id,                          -- 主键（粒度键）
  order_id,                               -- 退化维（订单号）
  customer_id,                            -- FK → dim_customer
  product_card_id,                        -- FK → dim_product
  DATE(order_date) AS order_date_key,     -- FK → dim_date
  shipping_date,                          -- 保留，算履约周期
  -- 度量值（可加）
  sales, order_item_total, order_item_discount,
  order_item_quantity, order_profit_per_order,
  -- 比率（不可加，保留）
  order_item_discount_rate, order_item_profit_ratio,
  -- 履约字段
  days_for_shipping_real, days_for_shipment_scheduled,
  late_delivery_risk, delivery_status, shipping_mode,
  -- 订单级属性
  order_status, market, order_region, order_city, order_country, order_state
FROM stg_orders;
ALTER TABLE fact_order_item ADD PRIMARY KEY (order_item_id);

-- ---------------------------------------------------------------------
-- 5. 外键：把事实表连到 3 张维表（保证引用完整性 + BI 自动识别关系）
-- ---------------------------------------------------------------------
ALTER TABLE fact_order_item
  ADD CONSTRAINT fk_customer FOREIGN KEY (customer_id)     REFERENCES dim_customer(customer_id),
  ADD CONSTRAINT fk_product  FOREIGN KEY (product_card_id) REFERENCES dim_product(product_card_id),
  ADD CONSTRAINT fk_date     FOREIGN KEY (order_date_key)  REFERENCES dim_date(date_key);

-- =====================================================================
-- 校验 SQL（建完跑一遍，全过才算数）
-- =====================================================================
-- 校验1 行数守恒：两者应相等（180519）
-- SELECT (SELECT COUNT(*) FROM stg_orders) AS stg, (SELECT COUNT(*) FROM fact_order_item) AS fact;

-- 校验2 维表行数：应为 20652 / 118 / 1127
-- SELECT (SELECT COUNT(*) FROM dim_customer), (SELECT COUNT(*) FROM dim_product), (SELECT COUNT(*) FROM dim_date);

-- 校验3 引用完整性：孤儿应全为 0
-- SELECT SUM(c.customer_id IS NULL), SUM(p.product_card_id IS NULL), SUM(d.date_key IS NULL)
-- FROM fact_order_item f
-- LEFT JOIN dim_customer c ON f.customer_id=c.customer_id
-- LEFT JOIN dim_product  p ON f.product_card_id=p.product_card_id
-- LEFT JOIN dim_date     d ON f.order_date_key=d.date_key;

-- 校验4 度量值空值：应全为 0
-- SELECT SUM(sales IS NULL), SUM(order_profit_per_order IS NULL), SUM(order_date_key IS NULL) FROM fact_order_item;

-- 校验5 ⭐ 迟发标记核对：real>scheduled 重算 vs 自带 late_delivery_risk
--   结果：97.5% 一致；4423 行差异全为 Shipping canceled（取消单），
--   说明自带标记口径已排除取消订单，可信且与迟发率口径一致。
-- SELECT late_delivery_risk,
--        CASE WHEN days_for_shipping_real > days_for_shipment_scheduled THEN 1 ELSE 0 END AS late_recalc,
--        COUNT(*)
-- FROM fact_order_item
-- GROUP BY 1, 2 ORDER BY 1, 2;
