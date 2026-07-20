r"""
00_clean_load.py  —  D3：pandas 最小清洗 → 写入 MySQL staging 表
运行： python notebooks/00_clean_load.py
产出： MySQL 库 dataco 里的表 stg_orders（staging，未建模的宽表）
凭据：读取项目根目录 .env；公开仓库只提供 .env.example 占位模板。
"""
import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ── 0. 项目路径与凭据：不依赖盘符或固定安装目录 ────────────────────
ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
RAW = ROOT / "data" / "raw" / "DataCoSupplyChainDataset.csv"

if not ENV_FILE.exists():
    raise FileNotFoundError("缺少 .env：请复制 .env.example 为 .env，并填写本机 MySQL 连接信息")
if not RAW.exists():
    raise FileNotFoundError(f"缺少原始数据：{RAW}；下载方法见 data/README.md")

load_dotenv(ENV_FILE)
required_env = ["MYSQL_USER", "MYSQL_PWD", "MYSQL_HOST", "MYSQL_PORT", "MYSQL_DB"]
missing_env = [name for name in required_env if not os.getenv(name)]
if missing_env:
    raise RuntimeError(f".env 缺少配置项：{', '.join(missing_env)}")

# ── 1. 读入（DataCo 是 latin-1，不是 utf-8，这是第一个坑）───────────────
df = pd.read_csv(RAW, encoding="latin-1")
print(f"[读入] 原始 shape = {df.shape}")          # (180519, 53)

# ── 2. 删列（22 个，理由分四类，见 docs/字段清单.md）───────────────────
drop_cols = [
    # 隐私 / 打码 / 垃圾值 (8)
    "Customer Email", "Customer Password", "Product Description", "Product Image",
    "Customer Fname", "Customer Lname", "Customer Street", "Order Zipcode",
    # 客户地理冗余 (6)——分析看货发到哪，客户注册地无用
    "Customer City", "Customer Country", "Customer State",
    "Latitude", "Longitude", "Customer Zipcode",
    # 重复列 (5)——已验证与保留列完全相同，留一删一
    "Benefit per order", "Order Item Product Price", "Product Category Id",
    "Order Customer Id", "Order Item Cardprod Id",
    # 无用列 (3)——常量列 / 与三判断无关 / 可现算
    "Product Status", "Type", "Sales per customer",
]
df = df.drop(columns=drop_cols)
print(f"[删列] 删掉 {len(drop_cols)} 列，剩 {df.shape[1]} 列（应为 31）")

# ── 3. 列名统一 snake_case（BI/SQL 里带空格的列名是灾难）──────────────
def to_snake(c: str) -> str:
    c = c.strip().lower()
    c = re.sub(r"[^0-9a-z]+", "_", c)   # 非字母数字 → 下划线
    return c.strip("_")

df.columns = [to_snake(c) for c in df.columns]
# 两个日期列自动转出来是 order_date_dateorders，太丑，手动改短
df = df.rename(columns={
    "order_date_dateorders": "order_date",
    "shipping_date_dateorders": "shipping_date",
})
print(f"[改名] 列名示例：{list(df.columns[:6])} ...")

# ── 4. 两个日期字段 → datetime（原来是字符串，不转没法算履约周期）──────
for col in ["order_date", "shipping_date"]:
    df[col] = pd.to_datetime(df[col], format="%m/%d/%Y %H:%M", errors="coerce")
    n_bad = df[col].isna().sum()
    print(f"[日期] {col} 转 datetime，失败(NaT) {n_bad} 行")

# ── 5. 连接 MySQL，建库 dataco（utf8mb4）────────────────────────────────
# 密码含特殊字符，必须用 URL.create 转义，不能手拼字符串
server = URL.create("mysql+pymysql",
                    username=os.getenv("MYSQL_USER"), password=os.getenv("MYSQL_PWD"),
                    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
                    port=int(os.getenv("MYSQL_PORT", 3306)),
                    query={"charset": "utf8mb4"})
with create_engine(server).begin() as conn:
    conn.execute(text("CREATE DATABASE IF NOT EXISTS dataco "
                      "DEFAULT CHARACTER SET utf8mb4"))
print("[建库] dataco 已就绪")

# ── 6. 写入 staging 表 stg_orders ───────────────────────────────────────
db = URL.create("mysql+pymysql",
                username=os.getenv("MYSQL_USER"), password=os.getenv("MYSQL_PWD"),
                host=os.getenv("MYSQL_HOST", "127.0.0.1"),
                port=int(os.getenv("MYSQL_PORT", 3306)),
                database=os.getenv("MYSQL_DB", "dataco"),
                query={"charset": "utf8mb4"})
engine = create_engine(db)
print("[写入] 开始灌数据（18 万行，约 1-2 分钟）...")
df.to_sql("stg_orders", engine, if_exists="replace", index=False,
          chunksize=1000, method="multi")

# ── 7. 验收：staging 行数 == CSV 行数 ───────────────────────────────────
with engine.connect() as conn:
    n_db = conn.execute(text("SELECT COUNT(*) FROM stg_orders")).scalar()
ok = "[OK] 一致" if n_db == len(df) else "[FAIL] 不一致，排查"
print(f"[验收] stg_orders 行数 = {n_db}  |  DataFrame 行数 = {len(df)}  |  {ok}")
