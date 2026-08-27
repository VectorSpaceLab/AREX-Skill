#!/usr/bin/env python3
"""Deterministic offline maintainer checks for GPT-Image2-Skill.

The checker never calls image APIs, reads no API-key values, and performs no
network access. It validates repository content that commonly drifts during
maintenance:

- `pyproject.toml` package name and `gpt-image` console script
- existing skill frontmatter basics
- Reference Gallery index category links/ranges
- generated image asset inventory summaries under `docs/`

Run from a checkout root:

    python skills/disco/gpt-image-cli/sub-skills/repo-maintenance/scripts/check_repo_content.py .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

EXPECTED_PROJECT_NAME = "gpt-image-cli"
EXPECTED_CONSOLE_SCRIPT = "gpt_image_cli.cli:main"
EXPECTED_PUBLIC_SKILL_NAME = "gpt-image"

PUBLISHED_SKILL_REL = Path("skills/gpt-image/SKILL.md")
GENERATED_SUBSKILLS = {
    Path("skills/disco/gpt-image-cli/sub-skills/cli-and-api/SKILL.md"): "cli-and-api",
    Path("skills/disco/gpt-image-cli/sub-skills/prompt-gallery/SKILL.md"): "prompt-gallery",
    Path("skills/disco/gpt-image-cli/sub-skills/repo-maintenance/SKILL.md"): "repo-maintenance",
}
GALLERY_INDEX_REL = Path("skills/gpt-image/references/gallery.md")
PLUGIN_JSON_RELS = [
    Path(".claude-plugin/plugin.json"),
    Path(".claude-plugin/marketplace.json"),
]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
DEFAULT_OVERSIZE_BYTES = 5 * 1024 * 1024
FRONTMATTER_FENCE = "---"

GALLERY_ROW_RE = re.compile(
    r"^\|\s*(?P<category>.+?)\s*\|\s*\[`?(?P<label>[^`\]]+)`?\]\((?P<link>[^)]+)\)\s*\|\s*No\.\s*(?P<start>\d+)\s*[–-]\s*(?P<end>\d+)\s*\|\s*(?P<count>\d+)\s*\|\s*$"
)


@dataclass(frozen=True)
class CheckIssue:
    path: str
    message: str


@dataclass
class Report:
    checks: list[str] = field(default_factory=list)
    issues: list[CheckIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    package: dict[str, object] = field(default_factory=dict)
    skills: dict[str, object] = field(default_factory=dict)
    gallery: dict[str, object] = field(default_factory=dict)
    docs_inventory: dict[str, object] = field(default_factory=dict)
    plugin_json: dict[str, object] = field(default_factory=dict)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline maintainer checks for a GPT-Image2-Skill checkout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository checkout root to inspect.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when warnings are present.",
    )
    parser.add_argument(
        "--max-asset-mb",
        type=float,
        default=DEFAULT_OVERSIZE_BYTES / (1024 * 1024),
        help="Warn when a docs image is larger than this many MiB.",
    )
    return parser.parse_args(argv)


def add_issue(report: Report, path: Path | str, message: str) -> None:
    report.issues.append(CheckIssue(path=path.as_posix() if isinstance(path, Path) else path, message=message))


def add_warning(report: Report, message: str) -> None:
    report.warnings.append(message)


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json_file(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_frontmatter(text: str) -> tuple[str | None, str | None]:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_FENCE:
        return None, "missing opening frontmatter fence"
    for idx in range(1, len(lines)):
        if lines[idx].strip() == FRONTMATTER_FENCE:
            return "\n".join(lines[1:idx]), None
    return None, "missing closing frontmatter fence"


def frontmatter_scalar(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", frontmatter)
    if not match:
        return None
    return match.group(1).strip()


def check_pyproject(report: Report, root: Path) -> None:
    rel = Path("pyproject.toml")
    path = root / rel
    if not path.exists():
        add_issue(report, rel, "missing pyproject.toml")
        return

    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        add_issue(report, rel, f"invalid TOML: {exc}")
        return

    project = data.get("project", {}) if isinstance(data, dict) else {}
    scripts = project.get("scripts", {}) if isinstance(project, dict) else {}
    project_name = project.get("name") if isinstance(project, dict) else None
    console_script = scripts.get("gpt-image") if isinstance(scripts, dict) else None

    if project_name != EXPECTED_PROJECT_NAME:
        add_issue(
            report,
            rel,
            f"expected project.name {EXPECTED_PROJECT_NAME!r}, found {project_name!r}",
        )
    if console_script != EXPECTED_CONSOLE_SCRIPT:
        add_issue(
            report,
            rel,
            f"expected project.scripts.gpt-image {EXPECTED_CONSOLE_SCRIPT!r}, found {console_script!r}",
        )

    report.package = {
        "project_name": project_name,
        "version": project.get("version") if isinstance(project, dict) else None,
        "requires_python": project.get("requires-python") if isinstance(project, dict) else None,
        "gpt_image_console_script": console_script,
    }
    if project_name == EXPECTED_PROJECT_NAME and console_script == EXPECTED_CONSOLE_SCRIPT:
        report.checks.append(
            f"pyproject ok: {EXPECTED_PROJECT_NAME} exposes gpt-image -> {EXPECTED_CONSOLE_SCRIPT}"
        )


def check_skill_frontmatter(
    report: Report,
    root: Path,
    rel: Path,
    expected_name: str,
    *,
    require_disable_model_invocation: bool = False,
    require_disco_role: bool = False,
) -> None:
    path = root / rel
    before = len(report.issues)
    if not path.exists():
        add_issue(report, rel, "missing skill file")
        return

    frontmatter, error = extract_frontmatter(read_text(path))
    if error:
        add_issue(report, rel, error)
        return
    assert frontmatter is not None

    name = frontmatter_scalar(frontmatter, "name")
    description = frontmatter_scalar(frontmatter, "description")
    if name != expected_name:
        add_issue(report, rel, f"expected name {expected_name!r}, found {name!r}")
    if not description:
        add_issue(report, rel, "missing description")
    elif not (description.startswith('"') and description.endswith('"')):
        add_issue(report, rel, "description must be double-quoted")

    if require_disable_model_invocation and not re.search(
        r"(?m)^disable-model-invocation:\s*true\s*$", frontmatter
    ):
        add_issue(report, rel, "missing disable-model-invocation: true")

    if require_disco_role and not re.search(
        r"(?m)^metadata:\s*$[\s\S]*?^\s+disco-role:\s*operating\s*$",
        frontmatter,
    ):
        add_issue(report, rel, "missing metadata.disco-role: operating")

    report.skills[rel.as_posix()] = {
        "expected_name": expected_name,
        "name": name,
        "description_quoted": bool(description and description.startswith('"') and description.endswith('"')),
        "requires_disable_model_invocation": require_disable_model_invocation,
        "requires_disco_role": require_disco_role,
    }
    if len(report.issues) == before:
        report.checks.append(f"skill frontmatter ok: {rel.as_posix()}")


def check_all_skill_frontmatter(report: Report, root: Path) -> None:
    check_skill_frontmatter(report, root, PUBLISHED_SKILL_REL, EXPECTED_PUBLIC_SKILL_NAME)
    for rel, expected_name in sorted(GENERATED_SUBSKILLS.items(), key=lambda item: item[0].as_posix()):
        check_skill_frontmatter(
            report,
            root,
            rel,
            expected_name,
            require_disable_model_invocation=True,
            require_disco_role=True,
        )


def check_gallery_index(report: Report, root: Path) -> None:
    path = root / GALLERY_INDEX_REL
    if not path.exists():
        add_issue(report, GALLERY_INDEX_REL, "missing gallery index")
        return

    rows: list[dict[str, object]] = []
    linked_files: set[str] = set()
    seen_numbers: list[int] = []

    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        match = GALLERY_ROW_RE.match(line)
        if not match:
            continue

        category = match.group("category").strip()
        label = match.group("label").strip()
        link = match.group("link").strip()
        start = int(match.group("start"))
        end = int(match.group("end"))
        count = int(match.group("count"))

        if "://" in link or link.startswith("/"):
            add_issue(report, GALLERY_INDEX_REL, f"line {line_number}: category link must be repository-relative")
            continue

        linked_path = (path.parent / link).resolve()
        linked_rel = relpath(root, linked_path)
        if Path(label).name != Path(link).name:
            add_issue(report, GALLERY_INDEX_REL, f"line {line_number}: label/link mismatch for {category!r}")
        if not linked_path.exists():
            add_issue(report, linked_rel, f"linked category file for {category!r} is missing")
        if end < start:
            add_issue(report, GALLERY_INDEX_REL, f"line {line_number}: invalid range for {category!r}")
        elif (end - start + 1) != count:
            add_issue(
                report,
                GALLERY_INDEX_REL,
                f"line {line_number}: range {start}-{end} implies {end - start + 1}, table says {count}",
            )

        linked_files.add(linked_rel)
        seen_numbers.extend(range(start, end + 1))
        rows.append(
            {
                "category": category,
                "file": linked_rel,
                "start": start,
                "end": end,
                "count": count,
            }
        )

    if not rows:
        add_issue(report, GALLERY_INDEX_REL, "no category rows found in gallery index")
        return

    duplicates = sorted(number for number, n in Counter(seen_numbers).items() if n > 1)
    if duplicates:
        add_issue(report, GALLERY_INDEX_REL, f"duplicate prompt numbers in category ranges: {duplicates}")

    category_dir = root / GALLERY_INDEX_REL.parent
    actual_category_files = {
        relpath(root, p)
        for p in category_dir.glob("gallery-*.md")
        if p.name != GALLERY_INDEX_REL.name
    }
    unlinked = sorted(actual_category_files - linked_files)
    if unlinked:
        add_warning(report, "gallery category files not linked from index: " + ", ".join(unlinked))

    total = sum(int(row["count"]) for row in rows)
    report.gallery = {
        "categories": len(rows),
        "total_prompts": total,
        "first_prompt_number": min(seen_numbers) if seen_numbers else None,
        "last_prompt_number": max(seen_numbers) if seen_numbers else None,
        "linked_files": sorted(linked_files),
        "unlinked_category_files": unlinked,
    }
    if not any(issue.path == GALLERY_INDEX_REL.as_posix() for issue in report.issues):
        report.checks.append(f"gallery index ok: {len(rows)} categories, {total} prompts")


def collect_docs_images(report: Report, root: Path, oversize_bytes: int) -> None:
    docs_dir = root / "docs"
    if not docs_dir.exists():
        add_issue(report, Path("docs"), "missing docs directory")
        return

    image_paths = sorted(
        (p for p in docs_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda p: relpath(root, p),
    )

    by_top_level: Counter[str] = Counter()
    root_level_images: list[str] = []
    oversized: list[dict[str, object]] = []
    total_bytes = 0

    for image in image_paths:
        size = image.stat().st_size
        total_bytes += size
        docs_rel = image.relative_to(docs_dir)
        bucket = docs_rel.parts[0] if len(docs_rel.parts) > 1 else "."
        by_top_level[bucket] += 1
        if bucket == ".":
            root_level_images.append(docs_rel.as_posix())
        if size > oversize_bytes:
            oversized.append({"path": relpath(root, image), "bytes": size})

    largest_images = sorted(
        ({"path": relpath(root, image), "bytes": image.stat().st_size} for image in image_paths),
        key=lambda item: (int(item["bytes"]), str(item["path"])),
        reverse=True,
    )[:10]

    if root_level_images:
        add_warning(report, "image files found directly under docs/: " + ", ".join(root_level_images))
    if oversized:
        add_warning(
            report,
            "oversized docs image assets: "
            + ", ".join(f"{item['path']} ({item['bytes']} bytes)" for item in oversized),
        )

    report.docs_inventory = {
        "total_images": len(image_paths),
        "total_bytes": total_bytes,
        "by_top_level_directory": dict(sorted(by_top_level.items())),
        "root_level_images": root_level_images,
        "largest_images": largest_images,
        "oversized_images": oversized,
    }
    report.checks.append(
        f"docs image inventory collected: {len(image_paths)} images, {total_bytes} bytes"
    )


def check_plugin_json(report: Report, root: Path) -> None:
    parsed: dict[str, object] = {}
    for rel in PLUGIN_JSON_RELS:
        path = root / rel
        if not path.exists():
            add_warning(report, f"plugin metadata file missing: {rel.as_posix()}")
            continue
        try:
            data = load_json_file(path)
        except json.JSONDecodeError as exc:
            add_issue(report, rel, f"invalid JSON: {exc}")
            continue
        parsed[rel.as_posix()] = data
        report.checks.append(f"plugin JSON parse ok: {rel.as_posix()}")
    report.plugin_json = {"files": sorted(parsed)}


def build_report(root: Path, oversize_bytes: int) -> Report:
    report = Report()
    check_pyproject(report, root)
    check_all_skill_frontmatter(report, root)
    check_gallery_index(report, root)
    collect_docs_images(report, root, oversize_bytes)
    check_plugin_json(report, root)
    return report


def to_jsonable(report: Report) -> dict[str, object]:
    return {
        "checks": report.checks,
        "issues": [{"path": issue.path, "message": issue.message} for issue in report.issues],
        "warnings": report.warnings,
        "package": report.package,
        "skills": report.skills,
        "gallery": report.gallery,
        "docs_inventory": report.docs_inventory,
        "plugin_json": report.plugin_json,
    }


def format_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    mib = num_bytes / (1024 * 1024)
    if mib >= 1:
        return f"{mib:.2f} MiB"
    return f"{num_bytes / 1024:.1f} KiB"


def render_plain(report: Report) -> str:
    lines: list[str] = ["OK" if not report.issues else "FAIL"]

    if report.checks:
        lines.append("Checks:")
        for check in report.checks:
            lines.append(f"- {check}")

    if report.gallery:
        lines.append("Gallery summary:")
        lines.append(
            f"- {report.gallery.get('categories')} categories, "
            f"{report.gallery.get('total_prompts')} prompts, "
            f"No. {report.gallery.get('first_prompt_number')}–{report.gallery.get('last_prompt_number')}"
        )

    if report.docs_inventory:
        inventory = report.docs_inventory
        lines.append("Docs image inventory:")
        lines.append(
            f"- {inventory.get('total_images')} images, "
            f"{format_bytes(int(inventory.get('total_bytes', 0)))} total"
        )
        by_dir = inventory.get("by_top_level_directory", {})
        if isinstance(by_dir, dict) and by_dir:
            summary = ", ".join(f"{name}: {count}" for name, count in by_dir.items())
            lines.append(f"- by top-level directory: {summary}")
        largest = inventory.get("largest_images", [])
        if isinstance(largest, list) and largest:
            lines.append("- largest images:")
            for item in largest[:5]:
                if isinstance(item, dict):
                    lines.append(f"  - {item.get('path')} ({format_bytes(int(item.get('bytes', 0)))})")

    if report.warnings:
        lines.append("Warnings:")
        for warning in report.warnings:
            lines.append(f"- {warning}")

    if report.issues:
        lines.append("Issues:")
        for index, issue in enumerate(report.issues, start=1):
            lines.append(f"{index}. {issue.path}: {issue.message}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    oversize_bytes = int(args.max_asset_mb * 1024 * 1024)
    report = build_report(root, oversize_bytes)

    if args.json:
        print(json.dumps(to_jsonable(report), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_plain(report))

    if report.issues:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
