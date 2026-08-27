#!/usr/bin/env python3
"""Validate a generated DisCo repo skill tree.

Checks:
- every SKILL.md has required operating frontmatter basics
- description is double-quoted in raw frontmatter
- Markdown links stay inside the generated skill tree and point at existing files
- public runtime files do not leak obvious local checkout/private paths
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".py",
    ".sh",
    ".mjs",
    ".js",
    ".ts",
    ".tsx",
}

FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")

# Build sensitive path tokens without embedding the exact production checkout
# path as one contiguous string in this script.
PATH_LEAK_PATTERNS = [
    "/" + "root" + "/" + "github-repos" + "/",
    "/" + "home" + "/",
    "/" + "Users" + "/",
    "C:" + "\\\\Users" + "\\\\",
]


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def _frontmatter_value(body: str, key: str) -> str | None:
    prefix = key + ":"
    for line in body.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _metadata_disco_role(body: str) -> str | None:
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "metadata:":
            for child in lines[i + 1 :]:
                if child and not child.startswith((" ", "\t")):
                    break
                stripped = child.strip()
                if stripped.startswith("disco-role:"):
                    return stripped.split(":", 1)[1].strip()
    return None


def check_skill_frontmatter(root: Path) -> list[str]:
    errors: list[str] = []
    skill_files = sorted(root.rglob("SKILL.md"))
    if not skill_files:
        return [f"{root}: no SKILL.md files found"]

    for path in skill_files:
        text = _read_text(path)
        if text is None:
            errors.append(f"{path}: not valid UTF-8 text")
            continue
        match = FRONTMATTER_RE.match(text)
        if not match:
            errors.append(f"{path}: missing YAML-style frontmatter block")
            continue
        body = match.group("body")
        name = _frontmatter_value(body, "name")
        description = _frontmatter_value(body, "description")
        disable = _frontmatter_value(body, "disable-model-invocation")
        role = _metadata_disco_role(body)

        if not name:
            errors.append(f"{path}: frontmatter missing name")
        elif name.startswith(('"', "'")) or name.endswith(('"', "'")):
            errors.append(f"{path}: name should be an unquoted canonical skill id")

        if not description:
            errors.append(f"{path}: frontmatter missing description")
        elif not (description.startswith('"') and description.endswith('"')):
            errors.append(f"{path}: description must be double-quoted")

        if disable != "true":
            errors.append(f"{path}: disable-model-invocation must be true")

        if role != "operating":
            errors.append(f"{path}: metadata.disco-role must be operating")

    return errors


def _iter_text_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix in TEXT_SUFFIXES or path.name == "SKILL.md":
            paths.append(path)
    return paths


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def check_path_leaks(root: Path) -> list[str]:
    errors: list[str] = []
    for path in _iter_text_files(root):
        text = _read_text(path)
        if text is None:
            continue
        for token in PATH_LEAK_PATTERNS:
            if token in text:
                errors.append(f"{path}: contains local/private path token {token!r}")
    return errors


def _clean_link(raw: str) -> str:
    # Drop optional Markdown title: target "title". Keep simple and conservative.
    raw = raw.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1]
    if " " in raw and not raw.startswith("#"):
        raw = raw.split()[0]
    return unquote(raw)


def check_markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*.md")):
        text = _read_text(path)
        if text is None:
            continue
        for match in MARKDOWN_LINK_RE.finditer(text):
            raw_target = _clean_link(match.group(1))
            parsed = urlparse(raw_target)
            if parsed.scheme in {"http", "https", "mailto"}:
                errors.append(f"{path}: external Markdown link escapes skill tree: {raw_target}")
                continue
            if raw_target.startswith("#"):
                continue
            target_no_anchor = raw_target.split("#", 1)[0]
            if not target_no_anchor:
                continue
            if target_no_anchor.startswith("/"):
                errors.append(f"{path}: absolute Markdown link escapes skill tree: {raw_target}")
                continue
            target_path = (path.parent / target_no_anchor).resolve()
            if not _is_within(target_path, root):
                errors.append(f"{path}: Markdown link points outside skill tree: {raw_target}")
                continue
            if not target_path.exists():
                errors.append(f"{path}: Markdown link target does not exist: {raw_target}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill_root",
        nargs="?",
        default=".",
        help="Generated skill tree root to validate (default: current directory).",
    )
    parser.add_argument(
        "--no-link-exists",
        action="store_true",
        help="Only check that links stay inside the tree; do not require targets to exist.",
    )
    args = parser.parse_args(argv)

    root = Path(args.skill_root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    errors: list[str] = []
    errors.extend(check_skill_frontmatter(root))
    errors.extend(check_path_leaks(root))
    if args.no_link_exists:
        # Temporarily monkey-patch Path.exists for link checking would be ugly;
        # instead run the normal check and filter existence-only messages.
        errors.extend(e for e in check_markdown_links(root) if "target does not exist" not in e)
    else:
        errors.extend(check_markdown_links(root))

    if errors:
        print(f"verify-skill-tree: FAILED ({len(errors)} issue(s))")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"verify-skill-tree: OK ({root})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
