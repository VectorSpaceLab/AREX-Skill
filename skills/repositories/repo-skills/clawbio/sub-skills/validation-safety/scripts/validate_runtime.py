#!/usr/bin/env python3
"""Static validation for a generated ClawBio operating-skill tree.

This helper is intentionally read-only and standard-library-only. It checks
required operating-skill frontmatter, relative Markdown links, and a small set
of obvious local-path or secret leaks. It does not import or execute skills,
run tests/demos/benchmarks, start services, or make network requests.

Usage:
    python scripts/validate_runtime.py [ROOT]
    python scripts/validate_runtime.py ROOT --allow-missing-links
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


LINK_RE = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")
ABSOLUTE_PATH_RE = re.compile(
    r"(?:" + "|".join(re.escape("/" + part + "/") for part in (
        "root", "home", "Users", "workspace", "private", "production" + "_batches"
    )) + r"|[A-Za-z]:\\\\)"
)
CHECKOUT_RE = re.compile(r"(?:github" + r"-repos|production" + r"[_-]batches)")
ENV_MARKER_RE = re.compile(
    r"(?:" + "|".join(
        re.escape(marker)
        for marker in (
            "DISCO_" + "CODING_AGENT_DIR",
            "CONDA" + "_PREFIX",
            "VIRTUAL" + "_ENV",
        )
    ) + r")"
)
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+"
)
SECRET_TOKEN_RE = re.compile(r"\b(?:sk-|gh[pousr]_)[A-Za-z0-9_-]{8,}\b")


def _frontmatter(path: Path) -> tuple[list[str] | None, list[str]]:
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return None, [f"{path}: cannot read ({exc})"]
    if not lines or lines[0] != "---":
        return None, [f"{path}: frontmatter must start with ---"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None, [f"{path}: frontmatter has no closing ---"]
    return lines[1:end], errors


def _check_frontmatter(path: Path, expected_name: str) -> list[str]:
    body, errors = _frontmatter(path)
    if body is None:
        return errors

    # Keep this deliberately exact: generated operating skills have one small,
    # stable frontmatter contract rather than permissive YAML interpretation.
    nonblank = [line for line in body if line.strip()]
    expected = [
        f"name: {expected_name}",
        None,  # description is checked for double quotes below
        "disable-model-invocation: true",
        "metadata:",
        "  disco-role: operating",
    ]
    if not nonblank or nonblank[0] != expected[0]:
        errors.append(f"{path}: name must be {expected[0]!r}")
    description_lines = [line for line in nonblank if line.startswith("description:")]
    if len(description_lines) != 1:
        errors.append(f"{path}: requires one description line")
    elif not re.fullmatch(r'description: "(?:[^"\\]|\\.)*"', description_lines[0]):
        errors.append(f"{path}: description must be double-quoted")
    if "disable-model-invocation: true" not in nonblank:
        errors.append(f"{path}: requires disable-model-invocation: true")
    if "metadata:" not in nonblank or "  disco-role: operating" not in nonblank:
        errors.append(f"{path}: requires metadata.disco-role: operating")

    allowed = {expected[0], "disable-model-invocation: true", "metadata:", "  disco-role: operating"}
    allowed.update(description_lines)
    unexpected = [line for line in nonblank if line not in allowed]
    if unexpected:
        errors.append(f"{path}: unexpected frontmatter fields: {unexpected!r}")
    return errors


def _check_links(path: Path, root: Path, allow_missing: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"{path}: cannot scan links ({exc})"], warnings
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().strip("<>")
        if not target or target.startswith("#"):
            continue
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
            errors.append(f"{path}: external link is not self-contained: {target}")
            continue
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        if target_path.startswith(("/", "~")):
            errors.append(f"{path}: absolute link is not allowed: {target}")
            continue
        resolved = (path.parent / target_path).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            errors.append(f"{path}: link escapes generated root: {target}")
            continue
        if not resolved.exists():
            message = f"{path}: missing internal link target: {target}"
            if allow_missing:
                warnings.append(message)
            else:
                errors.append(message)
    return errors, warnings


def _check_privacy(path: Path, root: Path) -> list[str]:
    del root  # retained in the signature to make call sites explicit
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"{path}: cannot scan privacy markers ({exc})"]
    errors: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if ABSOLUTE_PATH_RE.search(line):
            errors.append(f"{path}:{lineno}: possible absolute checkout/path leak")
        if CHECKOUT_RE.search(line):
            errors.append(f"{path}:{lineno}: possible checkout identity leak")
        if ENV_MARKER_RE.search(line):
            errors.append(f"{path}:{lineno}: local environment marker is not allowed")
        if SECRET_ASSIGNMENT_RE.search(line) or SECRET_TOKEN_RE.search(line):
            errors.append(f"{path}:{lineno}: possible credential/secret leak")
    return errors


def validate(root: Path, allow_missing_links: bool = False) -> tuple[list[str], list[str]]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    if not root.is_dir():
        return [f"root is not a directory: {root}"], warnings

    skill_files = sorted(root.rglob("SKILL.md"))
    if not skill_files:
        errors.append(f"no SKILL.md found under {root}")

    for path in skill_files:
        expected_name = root.name if path.parent == root else path.parent.name
        errors.extend(_check_frontmatter(path, expected_name))

    runtime_files = [p for p in sorted(root.rglob("*")) if p.is_file()]
    for path in runtime_files:
        if path.name == "SKILL.md" or path.suffix.lower() in {".md", ".py", ".json", ".sh"}:
            link_errors, link_warnings = _check_links(path, root, allow_missing_links)
            errors.extend(link_errors)
            warnings.extend(link_warnings)
        errors.extend(_check_privacy(path, root))
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="generated root skill directory (default: enclosing clawbio tree)",
    )
    parser.add_argument(
        "--allow-missing-links",
        action="store_true",
        help="report unresolved draft links as warnings instead of errors",
    )
    args = parser.parse_args(argv)
    errors, warnings = validate(args.root, allow_missing_links=args.allow_missing_links)
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"FAIL: {len(errors)} static validation error(s)", file=sys.stderr)
        return 1
    if warnings:
        print(f"PASS: static checks passed with {len(warnings)} draft link warning(s)")
    else:
        print("PASS: static frontmatter, link, and privacy checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
