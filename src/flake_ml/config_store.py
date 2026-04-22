from __future__ import annotations

from pathlib import Path
import re
from typing import Any


SECTION_PATTERN = re.compile(r"^\[(?P<section>[^\]]+)\]\s*$")
KEY_PATTERN = re.compile(r"^(?P<key>[A-Za-z0-9_]+)\s*=")


def format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".") if "." in f"{value:.6f}" else str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    raise TypeError(f"Unsupported TOML value type: {type(value)!r}")


def update_toml_section(path: str | Path, section: str, updates: dict[str, Any]) -> None:
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    section_start = None
    section_end = None
    for index, line in enumerate(lines):
        match = SECTION_PATTERN.match(line.strip())
        if not match:
            continue
        if match.group("section") == section:
            section_start = index
            continue
        if section_start is not None:
            section_end = index
            break

    if section_start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"[{section}]")
        section_start = len(lines) - 1
        section_end = len(lines)

    if section_end is None:
        section_end = len(lines)

    remaining = dict(updates)
    for index in range(section_start + 1, section_end):
        stripped = lines[index].strip()
        if not stripped or stripped.startswith("#"):
            continue
        key_match = KEY_PATTERN.match(stripped)
        if not key_match:
            continue
        key = key_match.group("key")
        if key in remaining:
            lines[index] = f"{key} = {format_toml_value(remaining.pop(key))}"

    insertion_index = section_end
    if remaining:
        new_lines = [f"{key} = {format_toml_value(value)}" for key, value in remaining.items()]
        lines[insertion_index:insertion_index] = new_lines

    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

