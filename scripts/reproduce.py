"""从原始 CSV 到数据库、图表和 PDF 的完整复现入口。"""
from __future__ import annotations

import argparse
import subprocess
import sys

from common import PROJECT_ROOT


def run(path: str) -> None:
    command = [sys.executable, str(PROJECT_ROOT / path)]
    print("\n==>", " ".join(command))
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="复现 DataCo 供应链分析项目")
    parser.add_argument("--skip-load", action="store_true", help="复用现有 MySQL 星型表")
    parser.add_argument("--skip-analysis", action="store_true", help="不执行 Notebook")
    parser.add_argument("--skip-report", action="store_true", help="不重新生成 PDF")
    args = parser.parse_args()

    run("scripts/check_data.py")
    if not args.skip_load:
        run("notebooks/00_clean_load.py")
        run("scripts/run_schema.py")
    run("scripts/export_star_csv.py")
    run("scripts/verify_results.py")
    if not args.skip_analysis:
        run("scripts/run_analysis.py")
    if not args.skip_report:
        run("report/generate_report.py")
    run("scripts/security_check.py")
    print("\n[完成] 数据、模型、分析、图表、报告与安全检查全部通过")


if __name__ == "__main__":
    main()
