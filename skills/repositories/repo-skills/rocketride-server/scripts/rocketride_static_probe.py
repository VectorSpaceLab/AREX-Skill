#!/usr/bin/env python3
"""Static checks for RocketRide skill users.

This helper validates small RocketRide `.pipe` JSON snippets and RocketRide
service-definition JSON-with-comments without importing RocketRide or starting an
engine. It is intentionally conservative: it catches shape mistakes that are
useful before SDK/runtime checks, but it is not a replacement for engine-side
validation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


TRAILING_COMMA_RE = re.compile(r",(?=\s*[}\]])")


def strip_json_comments(text: str) -> str:
    """Remove // and /* */ comments without touching quoted strings."""
    out: list[str] = []
    i = 0
    in_string = False
    quote = ""
    escape = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            i += 1
            continue
        if ch in ('"', "'"):
            in_string = True
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def load_json(path: Path, *, jsonc: bool = False) -> Any:
    text = path.read_text(encoding="utf-8")
    if jsonc:
        text = strip_json_comments(text)
        text = TRAILING_COMMA_RE.sub("", text)
    return json.loads(text)


def check_pipe(path: Path) -> list[str]:
    data = load_json(path)
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["pipeline root must be a JSON object"]
    components = data.get("components") or data.get("nodes")
    if not isinstance(components, list) or not components:
        return ["pipeline must contain a non-empty components or nodes array"]
    ids: set[str] = set()
    for idx, component in enumerate(components):
        label = f"component[{idx}]"
        if not isinstance(component, dict):
            errors.append(f"{label} must be an object")
            continue
        cid = component.get("id")
        provider = component.get("provider")
        if not isinstance(cid, str) or not cid:
            errors.append(f"{label} is missing non-empty id")
        elif cid in ids:
            errors.append(f"duplicate component id {cid!r}")
        else:
            ids.add(cid)
        if not isinstance(provider, str) or not provider:
            errors.append(f"{label} {cid or ''} is missing non-empty provider")
        config = component.get("config", {})
        if config is not None and not isinstance(config, dict):
            errors.append(f"{label} {cid or ''} config must be an object when present")
        for key in ("input", "control"):
            value = component.get(key, [])
            if value is None:
                continue
            if not isinstance(value, list):
                errors.append(f"{label} {cid or ''} {key} must be a list")
                continue
            for j, conn in enumerate(value):
                if not isinstance(conn, dict):
                    errors.append(f"{label} {cid or ''} {key}[{j}] must be an object")
                    continue
                src = conn.get("from")
                if not isinstance(src, str) or not src:
                    errors.append(f"{label} {cid or ''} {key}[{j}] is missing from")
                elif src not in ids and not any(c.get("id") == src for c in components if isinstance(c, dict)):
                    errors.append(f"{label} {cid or ''} {key}[{j}] references unknown component {src!r}")
                if key == "input" and not isinstance(conn.get("lane"), str):
                    errors.append(f"{label} {cid or ''} input[{j}] is missing lane")
                if key == "control" and not isinstance(conn.get("classType"), str):
                    errors.append(f"{label} {cid or ''} control[{j}] is missing classType")
    source = data.get("source")
    if source is not None and source not in ids:
        errors.append(f"source {source!r} does not match a component id")
    return errors


def check_service(path: Path) -> list[str]:
    data = load_json(path, jsonc=True)
    if not isinstance(data, dict):
        return ["service definition root must be an object"]
    errors: list[str] = []
    for field in ("title", "protocol", "classType"):
        if field not in data:
            errors.append(f"missing {field}")
    if "protocol" in data and not str(data["protocol"]).endswith("://"):
        errors.append("protocol should normally end with ://")
    class_type = data.get("classType")
    if class_type is not None and not isinstance(class_type, (str, list)):
        errors.append("classType must be a string or list")
    lanes = data.get("lanes")
    if lanes is not None and not isinstance(lanes, dict):
        errors.append("lanes must be an object mapping input lanes to output lanes")
    preconfig = data.get("preconfig")
    if preconfig is not None and not isinstance(preconfig, dict):
        errors.append("preconfig must be an object when present")
    return errors


def check_skill_links(skill_root: Path) -> list[str]:
    errors: list[str] = []
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for md in skill_root.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for match in link_re.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (md.parent / target_path).resolve()
            try:
                resolved.relative_to(skill_root.resolve())
            except ValueError:
                errors.append(f"{md.relative_to(skill_root)} links outside skill tree: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{md.relative_to(skill_root)} has missing link target: {target}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static RocketRide .pipe/service/skill checks")
    parser.add_argument("--pipe", action="append", default=[], help="Path to a .pipe JSON file to validate")
    parser.add_argument("--service-json", action="append", default=[], help="Path to a JSON-with-comments service definition")
    parser.add_argument("--skill-root", help="Generated skill root to check for local link integrity")
    args = parser.parse_args(argv)

    total_errors: list[str] = []
    for item in args.pipe:
        path = Path(item)
        total_errors.extend(f"{path}: {err}" for err in check_pipe(path))
    for item in args.service_json:
        path = Path(item)
        total_errors.extend(f"{path}: {err}" for err in check_service(path))
    if args.skill_root:
        root = Path(args.skill_root)
        total_errors.extend(f"{root}: {err}" for err in check_skill_links(root))

    if total_errors:
        print("FAILED")
        for err in total_errors:
            print(f"- {err}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
