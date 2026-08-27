#!/usr/bin/env python3
from __future__ import annotations
import argparse
import fnmatch
from pathlib import Path
import yaml


def pattern_matches(rel_path: str, pattern: str) -> bool:
    if pattern == "**" or fnmatch.fnmatch(rel_path, pattern):
        return True
    if pattern.startswith("**/") and fnmatch.fnmatch(rel_path, pattern[3:]):
        return True
    return False


def allowed(data: dict, rel_path: str, user: str, level: str) -> bool:
    best = None
    for rule in data.get("rules") or []:
        pattern = rule.get("pattern", "**")
        if pattern_matches(rel_path, pattern):
            score = len(pattern.replace("*", ""))
            if best is None or score > best[0]:
                best = (score, rule)
    if best is None:
        return False
    access = best[1].get("access") or {}
    values = set(access.get(level) or []) | set(access.get("admin") or [])
    return "*" in values or user in values or any(v.startswith("*@") and user.endswith(v[1:]) for v in values)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a syft.pub.yaml rule for one user/path/access level")
    parser.add_argument("--policy", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--level", default="read", choices=["read", "write", "admin"])
    args = parser.parse_args()
    data = yaml.safe_load(Path(args.policy).read_text()) or {}
    ok = allowed(data, args.path, args.user, args.level)
    print("ALLOW" if ok else "DENY")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
