"""在 MySQL 中执行星型模型 DDL。会重建 dataco 的事实表和维表。"""
from __future__ import annotations

import re

from sqlalchemy import text

from common import PROJECT_ROOT, mysql_engine


def split_sql(script: str) -> list[str]:
    without_comments = "\n".join(re.sub(r"--.*$", "", line) for line in script.splitlines())
    return [statement.strip() for statement in without_comments.split(";") if statement.strip()]


def main() -> None:
    sql_file = PROJECT_ROOT / "sql" / "schema.sql"
    statements = split_sql(sql_file.read_text(encoding="utf-8"))
    engine = mysql_engine()
    with engine.begin() as conn:
        for index, statement in enumerate(statements, start=1):
            conn.execute(text(statement))
            print(f"[DDL {index:02d}/{len(statements):02d}] 完成")
    print("[OK] 星型模型已重建")


if __name__ == "__main__":
    main()

