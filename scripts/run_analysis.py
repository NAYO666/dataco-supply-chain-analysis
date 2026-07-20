"""用通用 python3 内核执行三份正式 Notebook，输出到 output/notebooks。"""
from __future__ import annotations

import subprocess
import sys

from common import OUTPUT_DIR, PROJECT_ROOT, ensure_output_dirs


NOTEBOOKS = [
    "01_eda.ipynb",
    "02_late_delivery_analysis.ipynb",
    "03_inventory_abc_xyz.ipynb",
]


def main() -> None:
    ensure_output_dirs()
    target = OUTPUT_DIR / "notebooks"
    for name in NOTEBOOKS:
        source = PROJECT_ROOT / "notebooks" / name
        command = [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--ExecutePreprocessor.kernel_name=python3",
            "--ExecutePreprocessor.timeout=300",
            "--output",
            f"{source.stem}.executed.ipynb",
            "--output-dir",
            str(target),
            str(source),
        ]
        print(f"[执行] {name}")
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    print(f"[OK] 已执行 Notebook 输出到 {target.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

