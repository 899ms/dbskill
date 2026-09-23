#!/usr/bin/env python3
"""Validate the public numbered prompts shipped inside the dbs Skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


NUMBER = re.compile(r"[0-9]{3}\Z")
REQUIRED_SECTIONS = (
    "## 用户要完成的事",
    "## 需要的输入",
    "## 执行步骤",
    "## 交付结果",
    "## 验收标准",
    "## 适用边界",
)


def validate(root: Path) -> list[str]:
    prompt_root = root / "skills" / "dbs" / "numbered-prompts"
    errors: list[str] = []
    state_file = prompt_root / "allocation.json"
    if not state_file.is_file():
        return [f"缺少编号分配状态：{state_file}"]
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        next_number = state["next_number"]
        if type(next_number) is not int or not 0 <= next_number <= 1000:
            raise ValueError("next_number 必须是 0～1000 的整数")
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as error:
        return [f"编号分配状态无效：{error}"]

    numbers: list[int] = []
    for entry in sorted(prompt_root.iterdir()):
        if entry.name == "allocation.json":
            continue
        if entry.is_symlink() or not entry.is_dir() or NUMBER.fullmatch(entry.name) is None:
            errors.append(f"编号目录只允许三位数字：{entry.name}")
            continue
        numbers.append(int(entry.name))
        prompt = entry / "PROMPT.md"
        if not prompt.is_file() or prompt.is_symlink():
            errors.append(f"{entry.name} 缺少普通文件 PROMPT.md")
            continue
        text = prompt.read_text(encoding="utf-8")
        if not re.search(rf"(?m)^# {entry.name}｜\S.+$", text):
            errors.append(f"{entry.name}/PROMPT.md 首行应包含编号和标题")
        if not re.search(r"(?m)^来源：\S.*$", text):
            errors.append(f"{entry.name}/PROMPT.md 缺少非空来源")
        positions: list[int] = []
        for section in REQUIRED_SECTIONS:
            match = re.search(rf"(?m)^{re.escape(section)}\s*$", text)
            if match is None:
                errors.append(f"{entry.name}/PROMPT.md 缺少 {section}")
            else:
                positions.append(match.start())
        if len(positions) == len(REQUIRED_SECTIONS):
            if positions != sorted(positions):
                errors.append(f"{entry.name}/PROMPT.md 六个章节顺序不正确")
            for index, section in enumerate(REQUIRED_SECTIONS):
                start = positions[index] + len(section)
                end = positions[index + 1] if index + 1 < len(positions) else len(text)
                if not text[start:end].strip():
                    errors.append(f"{entry.name}/PROMPT.md 的 {section} 没有内容")
        if re.search(r"(?m)^---\s*$", text[:100]):
            errors.append(f"{entry.name}/PROMPT.md 不使用 Skill frontmatter")
        for nested in entry.rglob("*"):
            if nested.is_symlink():
                errors.append(f"{nested.relative_to(prompt_root)} 不允许符号链接")
            if nested.name == "SKILL.md":
                errors.append(f"{nested.relative_to(prompt_root)} 不得注册为独立 Skill")

    if numbers and max(numbers) >= next_number:
        errors.append("allocation.json 的 next_number 必须大于所有已分配编号")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", type=Path)
    root = parser.parse_args().root.expanduser().resolve()
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    prompt_root = root / "skills" / "dbs" / "numbered-prompts"
    count = sum(1 for entry in prompt_root.iterdir() if entry.is_dir())
    print(f"编号提示词校验通过：{count} 个编号")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
