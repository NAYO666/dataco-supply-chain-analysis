"""提交前检查：阻止真实 .env、原始数据、绝对路径和明显 IP 泄漏进入 Git。"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from common import PROJECT_ROOT


EXCLUDED_DIRS = {".git", "data", "tmp", "plan", "anaconda_projects", ".ipynb_checkpoints"}
EXCLUDED_NAMES = {"D1_探索.ipynb"}
TEXT_SUFFIXES = {".py", ".sql", ".md", ".txt", ".yml", ".yaml", ".json", ".ipynb", ".example"}
WINDOWS_ABSOLUTE = re.compile(r"[A-Za-z]:\\(?:Users|kaggle|anaconda|Program Files)", re.I)
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
SAFE_LOCAL_IPS = {"127.0.0.1", "0.0.0.0"}


def candidate_files() -> list[Path]:
    files = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name == ".env" or path.name in EXCLUDED_NAMES or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        files.append(path)
    return files


def main() -> int:
    issues: list[str] = []
    if (PROJECT_ROOT / ".env").exists() and ".env" not in (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8"):
        issues.append(".gitignore 未排除 .env")

    for path in candidate_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative = path.relative_to(PROJECT_ROOT)
        if WINDOWS_ABSOLUTE.search(text):
            issues.append(f"{relative}: 包含本机绝对路径")
        public_ips = {ip for ip in IPV4.findall(text) if ip not in SAFE_LOCAL_IPS}
        if public_ips and relative != Path(".env.example"):
            issues.append(f"{relative}: 包含需复核的 IPv4 地址 {sorted(public_ips)}")
        if re.search(r"MYSQL_PWD\s*=\s*(?!your_password_here\b)\S+", text):
            issues.append(f"{relative}: 疑似包含真实 MYSQL_PWD")

    if (PROJECT_ROOT / ".git").exists():
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", ".env"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if tracked.returncode == 0:
            issues.append(".env 已被 Git 跟踪")

    if issues:
        print("[FAIL] 安全检查发现问题：")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("[OK] 未发现真实凭据、公开数据文件、本机绝对路径或 IP 泄漏")
    return 0


if __name__ == "__main__":
    sys.exit(main())
