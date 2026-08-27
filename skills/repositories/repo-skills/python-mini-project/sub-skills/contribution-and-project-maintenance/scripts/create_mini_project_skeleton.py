#!/usr/bin/env python3
"""Create a safe starter skeleton for a python-mini-project folder.

The script only writes a project folder, README.md, main.py, and optional
requirements.txt. It never executes project code.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Sequence

DEFAULT_DESCRIPTION = "Starter scaffold for the mini-project."
DEFAULT_AUTHOR = "Add the author name or handle here."
VALID_FOLDER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9 _.-]*[A-Za-z0-9])?$")


def slugify_folder_name(raw: str) -> str:
    """Derive a safe folder name from a display name."""

    name = raw.strip()
    if name.lower().endswith(".py"):
        name = name[:-3]
    name = re.sub(r"[^A-Za-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "Mini_Project"


def humanize_title(name: str) -> str:
    """Convert a folder-like name into a readable README title."""

    text = name.strip()
    if text.lower().endswith(".py"):
        text = text[:-3]
    text = re.sub(r"[_-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.title() if text else "Mini Project"


def validate_folder_name(name: str) -> None:
    """Reject path traversal, hidden names, and awkward folder names."""

    if not name or not name.strip():
        raise ValueError("folder name must not be empty")
    if name != name.strip():
        raise ValueError("folder name must not have leading or trailing spaces")
    if name in {".", ".."}:
        raise ValueError("folder name must not be '.' or '..'")
    if "/" in name or "\\" in name:
        raise ValueError("folder name must not contain path separators")
    if ":" in name:
        raise ValueError("folder name must not contain ':'")
    if name.startswith("."):
        raise ValueError("folder name must not start with a dot")
    if not VALID_FOLDER_RE.match(name):
        raise ValueError(
            "folder name may contain only letters, digits, spaces, underscores, hyphens, and dots"
        )


def unique_nonempty(values: Sequence[str]) -> list[str]:
    """Return unique, stripped requirement lines in first-seen order."""

    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        line = value.strip()
        if not line:
            continue
        if "\n" in line or "\r" in line:
            raise ValueError("requirements must be single-line package specifiers")
        if line not in seen:
            seen.add(line)
            items.append(line)
    return items


def render_readme(
    title: str,
    description: str,
    requirements: Sequence[str],
    demo: str,
    author: str,
) -> str:
    """Render a simple README that follows the repo's mini-project template."""

    lines: list[str] = [f"# {title}", "", "## Description", description.strip() or DEFAULT_DESCRIPTION, ""]

    lines.append("## Requirements")
    if requirements:
        lines.append("Runtime dependencies for this project:")
        lines.extend(f"- {item}" for item in requirements)
        lines.extend(
            [
                "",
                "Install them with:",
                "```bash",
                "python -m pip install -r requirements.txt",
                "```",
            ]
        )
    else:
        lines.append("This starter currently uses only the Python standard library.")

    lines.extend(["", "## How to run", "```bash", "python main.py", "```"])
    if demo.strip():
        lines.extend(["", "## Demo", f"Demo asset: {demo.strip()}"])
    lines.extend(["", "## Author", author.strip() or DEFAULT_AUTHOR])
    return "\n".join(lines).rstrip() + "\n"


def render_main(title: str) -> str:
    """Render a safe placeholder entry point."""

    message = f"Replace this starter with the {title} implementation."
    return (
        '"""Starter entry point for this mini-project."""\n\n'
        "from __future__ import annotations\n\n\n"
        "def main() -> int:\n"
        '    """Run the placeholder starter."""\n'
        f"    print({message!r})\n"
        "    return 0\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    raise SystemExit(main())\n"
    )


def render_requirements(requirements: Sequence[str]) -> str:
    """Render a normalized requirements.txt body."""

    return "\n".join(requirements) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a safe mini-project skeleton with README.md, main.py, and optional requirements.txt.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python create_mini_project_skeleton.py 'Dice Stimulator'\n"
            "  python create_mini_project_skeleton.py 'My Project' --requirement requests --requirement rich\n"
            "  python create_mini_project_skeleton.py 'My Project' --root . --force\n"
        ),
    )
    parser.add_argument(
        "project_name",
        help="Display name for the mini-project. Used to derive the folder name when --folder-name is not provided.",
    )
    parser.add_argument(
        "--folder-name",
        help="Explicit project folder name. If omitted, a safe underscore form is derived from project_name.",
    )
    parser.add_argument(
        "--title",
        help="README title. If omitted, a readable title is derived from the folder name.",
    )
    parser.add_argument(
        "--description",
        default=DEFAULT_DESCRIPTION,
        help="Short README description for the project.",
    )
    parser.add_argument(
        "--author",
        default=DEFAULT_AUTHOR,
        help="Author or contributor line for the README.",
    )
    parser.add_argument(
        "--demo",
        default="",
        help="Optional demo note or relative asset path for the README Demo section.",
    )
    parser.add_argument(
        "--requirement",
        action="append",
        default=[],
        metavar="PKG",
        help="Add one runtime dependency line to requirements.txt. Repeat this flag for multiple packages.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root where the new project folder will be created.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite README.md, main.py, and requirements.txt if they already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the planned files without writing anything.",
    )
    return parser.parse_args(argv)


def ensure_writable_target(project_dir: Path, force: bool) -> None:
    if project_dir.exists():
        if not project_dir.is_dir():
            raise SystemExit(f"Target path exists but is not a directory: {project_dir}")
        if any(project_dir.iterdir()) and not force:
            raise SystemExit(
                f"Target folder already exists and is not empty: {project_dir}. Use --force to overwrite the starter files."
            )


def write_text_file(path: Path, content: str, force: bool) -> str:
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing file without --force: {path}")
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return str(path)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    root = Path(args.root).expanduser()
    if not root.exists():
        raise SystemExit(f"Root directory does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Root path is not a directory: {root}")

    folder_name = args.folder_name if args.folder_name else slugify_folder_name(args.project_name)
    validate_folder_name(folder_name)

    project_dir = root / folder_name
    ensure_writable_target(project_dir, args.force)

    title = args.title.strip() if args.title else humanize_title(folder_name)
    description = args.description.strip() if args.description else DEFAULT_DESCRIPTION
    author = args.author.strip() if args.author else DEFAULT_AUTHOR
    demo = args.demo.strip()
    requirements = unique_nonempty(args.requirement)

    planned_files = [project_dir / "README.md", project_dir / "main.py"]
    if requirements:
        planned_files.append(project_dir / "requirements.txt")

    if args.dry_run:
        print(f"Would create project folder: {project_dir}")
        for path in planned_files:
            print(f"Would write: {path}")
        return 0

    project_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    written.append(write_text_file(project_dir / "README.md", render_readme(title, description, requirements, demo, author), args.force))
    written.append(write_text_file(project_dir / "main.py", render_main(title), args.force))
    if requirements:
        written.append(write_text_file(project_dir / "requirements.txt", render_requirements(requirements), args.force))

    for path in written:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
