#!/usr/bin/env python3
"""List the numbered prompts available in this installed dbs Skill."""

from __future__ import annotations

import re
import sys
from pathlib import Path


NUMBER = re.compile(r"[0-9]{3}\Z")
TITLE = re.compile(r"^# ([0-9]{3})｜(.+)$", re.MULTILINE)
PURPOSE = re.compile(r"^## 用户要完成的事\s*\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)


def one_line(value: str) -> str:
    return " ".join(value.replace("|", "｜").split())


def list_prompts(root: Path) -> tuple[list[tuple[str, str, str]], list[str]]:
    items: list[tuple[str, str, str]] = []
    errors: list[str] = []
    if not root.is_dir():
        return items, ["编号目录不存在"]
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or directory.is_symlink() or NUMBER.fullmatch(directory.name) is None:
            continue
        prompt = directory / "PROMPT.md"
        if not prompt.is_file() or prompt.is_symlink():
            errors.append(f"{directory.name} 缺少 PROMPT.md")
            continue
        try:
            content = prompt.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{directory.name} 不是 UTF-8 文件")
            continue
        title = TITLE.search(content)
        purpose = PURPOSE.search(content)
        if title is None or title.group(1) != directory.name or purpose is None:
            errors.append(f"{directory.name} 缺少编号标题或任务说明")
            continue
        purpose_lines = [one_line(line) for line in purpose.group(1).splitlines() if line.strip()]
        if not purpose_lines:
            errors.append(f"{directory.name} 的任务说明为空")
            continue
        items.append((directory.name, one_line(title.group(2)), purpose_lines[0]))
    return items, errors


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "numbered-prompts"
    items, errors = list_prompts(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if not items:
        print("当前安装版本还没有可用的编号隐藏款。")
        return 0
    print(f"当前安装版本共有 {len(items)} 个编号隐藏款：")
    for code, title, purpose in items:
        print(f"- /dbs {code}｜{title}：{purpose}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
