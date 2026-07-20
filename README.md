# DataCo 供应链分析与决策支持

本项目基于 Kaggle [DataCo Smart Supply Chain](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) 数据集，对 180,519 个订单行、65,752 个订单和 118 个 SKU 进行盈利、履约与库存分析。项目构建了从 pandas 清洗、MySQL 星型模型、SQL/Python 分析到 Power BI 展示的可复现链路；Power BI 核心指标均与 SQL 和 pandas 结果交叉核对一致。

## 主要分析结论

### 1. 盈利风险集中于深亏订单行

- **分析结果**：整体利润率为 12.03%，亏损订单行占比为 18.71%。按品类和区域汇总时，691 个组合中仅 60 个组合净亏，合计净亏 1.45 万，仅占全部亏损的 0.4%；SKU 层面仅 3 个 SKU 净亏。该结果表明，汇总净额无法充分反映行级亏损分布。
- **量化影响**：利润率低于 -50% 的订单行占全部订单行的 **8.69%**，贡献 **85.3% 的亏损（331 万）**；其中利润率低于 -100% 的订单行贡献 53% 的亏损。全部亏损为 388 万，盈利金额为 785 万，净利润为 397 万。
- **管理建议**：设置订单行利润率下限，对利润率低于 -100% 的交易进行拦截，对 -100% 至 -50% 的交易触发审批。敏感性分析显示，-50% 附近能够在覆盖主要亏损与控制审批范围之间取得相对平衡；可优先在 Fishing 和 Camping 品类进行验证。
- **证据**：[notebooks/01_eda.ipynb](notebooks/01_eda.ipynb) ｜ [盈利结构看板](dashboard/power%20bi/盈利结构.png)

### 2. 履约偏差主要来自承诺时效与实际能力不匹配

- **分析结果**：有效发货订单的订单级迟发率为 **57.31%**，月度趋势基本稳定，五大市场迟发率介于 56.5% 和 57.7% 之间。First Class 承诺 1 天、实际配送 2 天，因此订单级迟发率为 100%；Second Class 承诺 2 天、实际平均 4.00 天，与 Standard Class 的 3.99 天接近。
- **量化影响**：约18%的运输等级×市场×品类组合覆盖约80%的迟发订单行，迟发订单行对应 GMV 约 **2,013 万，占总 GMV 的 57.2%**。First Class 的订单级迟发率最高，但占全部迟发订单行的 27%；Standard Class 的订单级迟发率较低，但因业务量较大，占全部迟发订单行的 41%。
- **指标含义**：订单级迟发率衡量实际客户订单中发生迟发的比例；迟发订单行占比衡量各运输等级承载的迟发商品行规模。前者反映服务可靠性，后者用于确定运营改善的工作量和优先级。
- **情景测算**：在历史实际配送天数保持不变的条件下，将承诺天数调整为各运输等级的实际均值，订单级迟发率由 57.3% 降至 **31.6%**；使用历史 P80 时效作为承诺值时降至 15.9%。Second Class 和 Standard Class 的剩余迟发需要通过实际履约能力改善解决。
- **证据**：[notebooks/02_late_delivery_analysis.ipynb](notebooks/02_late_delivery_analysis.ipynb) ｜ [履约总览看板](dashboard/power%20bi/履约总览.png)

### 3. 安全库存资金的主要影响因素是需求波动、单价与提前期

- **分析结果**：在102个具有足够销售历史的可测算SKU中，A类7个SKU贡献77.6%的销售额。7 个 A 类 SKU 均属于 X 类，A 类仅占安全库存资金约 5%；B 类销售额占比为 17.9%，但安全库存资金占比约为 89%。
- **策略对比**：统一采用 95% 服务水平时，安全库存资金为 **115.2 万**；ABC-XYZ 分层服务水平策略为 **120.1 万**，较基准增加 4.2%；仅降低 C 类服务水平时为 **112.6 万**，较基准减少 2.2%。
- **管理建议**：服务水平调整对资金占用的影响有限。测算显示，B 类商品补货提前期减半可使安全库存资金降低约 29%，对应约 30 万；BZ 类可进一步评估按单采购策略。
- **方法说明**：XYZ 分类使用每个 SKU 在售窗口内补零后的周需求变异系数。窗口短于 8 周的 16 个 SKU 不参与分类，其销售额占比为 0.95%。全数据周期补零会将停售阶段误判为零需求，因此不用于正式测算。
- **证据**：[notebooks/03_inventory_abc_xyz.ipynb](notebooks/03_inventory_abc_xyz.ipynb)

## Power BI 看板

| 履约总览：迟发水平、趋势和结构 | 盈利结构：亏损规模、深度和重点品类 |
|---|---|
| ![履约总览](dashboard/power%20bi/履约总览.png) | ![盈利结构](dashboard/power%20bi/盈利结构.png) |

[power bi/power bi看板.pbix](power%20bi/power%20bi看板.pbix) 采用 Import 模式并内嵌演示数据，可直接打开查看。使用本地复现数据刷新时，参见 [Power BI 刷新说明](docs/power_bi_refresh.md)。

## 数据模型

![星型模型](docs/star_schema.svg)

MySQL 8.0 星型模型由以下四张表组成：

- `fact_order_item`：180,519 行，粒度为订单行，主键为 `order_item_id`。
- `dim_customer`：20,652 行。
- `dim_product`：118 行，包含商品大类、品类和商品三级层级。
- `dim_date`：1,127 行。

模型校验覆盖事实表行数守恒、维表行数、主外键完整性、关键字段空值和迟发标记一致性。使用 `days_for_shipping_real > days_for_shipment_scheduled` 独立计算的迟发标记与原字段一致率为 **97.5%**；4,423 个差异订单行全部属于取消订单，因此履约指标将 `Shipping canceled` 排除在分母之外。

## 核心指标口径

完整定义参见 [docs/kpi_definitions.md](docs/kpi_definitions.md)。

| 指标 | 计算口径 | 结果 |
|---|---|---|
| 迟发率 | 按 `order_id` 去重；分母排除 `Shipping canceled` | 36,048 / 62,897 = **57.31%** |
| 销售额 GMV | `SUM(sales)`；排除 `CANCELED` 和 `SUSPECTED_FRAUD` | **3,521.44 万** |
| 净收入 | `SUM(order_item_total)`；排除未成交订单 | **3,164.47 万** |
| 利润率 | 总利润 ÷ 折后净收入 | **12.03%** |
| 亏损订单行占比 | 负利润订单行数 ÷ 全部订单行数 | **18.71%** |
| 盈利侵蚀率 | 亏损金额绝对值 ÷ 盈利金额 | **49.5%** |
| 深亏订单行 | 行级利润率严格小于 -50% | 15,695 行 / **8.69%** / 331 万 |
| XYZ 分类 | 在售窗口内补零后的周需求变异系数 | X17 / Y70 / Z15 |

## 数据范围与分析限制

- 数据集不包含运费成本，亏损分析以负利润订单行为对象，不对运费进行归因。
- 数据集不包含罚金和客户流失字段，迟发影响使用受影响 GMV 表示，不等同于直接经济损失。
- 数据集不包含库存快照，库存部分为安全库存策略测算，不代表现有库存审计结果。
- 数据集不包含齐套交付字段，因此履约分析计算 OTD，无法计算完整 OTIF。
- 数据为教学模拟数据集，分析结果用于展示方法与决策框架，不代表特定企业的实际经营水平。

## 项目结构

```text
data/raw            Kaggle 原始 CSV（本地文件，不进入 Git）
data/star_csv       MySQL 星型表导出 CSV（自动生成，不进入 Git）
notebooks           数据清洗与三项专题分析
sql                 星型模型 DDL 与校验 SQL
scripts             建模、导出、校验、执行和安全检查脚本
dashboard           分析图表与 Power BI 看板截图
power bi            Power BI 项目文件
docs                指标口径、字段治理、数据模型和刷新说明
report              一页结论报告源文件、生成脚本与 PDF
output/pdf          自动生成的最终 PDF
requirements.txt    Python 依赖版本
.env.example        数据库配置模板
```

## 复现方法

前置条件：Python 3.13、MySQL 8.0，以及具有建库和建表权限的 MySQL 账号。

1. 安装 Python 环境：`python -m pip install -r requirements.txt`。也可运行 `conda env create -f environment.yml`。
2. 从 [Kaggle](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) 下载 `DataCoSupplyChainDataset.csv` 与 `DescriptionDataCoSupplyChain.csv`，放入 `data/raw/`。数据文件使用 `latin-1` 编码读取；`tokenized_access_logs.csv` 不参与本项目。
3. 将 `.env.example` 复制为 `.env`，填写本地 MySQL 连接参数。
4. 在仓库根目录运行 `python scripts/reproduce.py`。

复现脚本依次执行原始数据检查、清洗入库、星型模型重建、星型 CSV 导出、KPI 校验、Notebook 执行、18 张图表导出、PDF 生成和隐私检查。复用现有数据库时可运行 `python scripts/reproduce.py --skip-load`。

预期校验结果：事实表 180,519 行、订单级迟发率 57.31%、GMV 3,521.44 万、净收入 3,164.47 万、利润率 12.03%、亏损订单行占比 18.71%。

## 仓库内容与数据安全

- 仓库包含代码、SQL、正式 Notebook、成果图表、Power BI 文件、方法文档、`.env.example` 和最终 PDF。
- 真实 `.env`、Kaggle 原始 CSV、星型表导出 CSV、Notebook 执行副本、缓存和本地探索稿不进入 Git。
- `python scripts/security_check.py` 用于检查凭据跟踪状态、本机绝对路径、IP 地址和疑似明文密码。详细规则见 [SECURITY.md](SECURITY.md)。

## 技术栈

Python（pandas、SQLAlchemy、seaborn、scipy） · MySQL 8.0 · Power BI · Git
