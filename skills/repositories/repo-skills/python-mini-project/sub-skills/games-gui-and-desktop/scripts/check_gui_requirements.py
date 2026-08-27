#!/usr/bin/env python3
from __future__ import annotations

"""Static checker for GUI and desktop mini-project folders.

This helper never imports or executes project code. It only reads files,
parses Python syntax, and reports GUI/game imports, dependency hints, asset
folders, support files, and likely entry points.
"""

import argparse
import ast
import json
import re
import sys
import warnings
from pathlib import Path

KNOWN_PROJECTS = [
    "Chess_Game",
    "Snake_game",
    "Connect-Four",
    "Color_Game",
    "Caterpillar_Game",
    "Convoys_GameofLife",
    "Egg_Catcher",
    "HangMan",
    "Hangman_Game",
    "Lazy_Pong",
    "Minesweeper_game",
    "Othello-Reversi-Game",
    "Screenpet",
    "Simple_dice",
    "Spinning Donut",
    "Tic_Tac_Toe",
    "TEXTVENTURE",
    "Zombie_Game",
    "Music-Player",
    "Chinese_FlashCard",
    "Finance_Tracker",
    "Investment Calculator",
    "TestTypingSpeed",
]

TEXT_SCAN_EXTENSIONS = {
    ".py",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
}

ASSET_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".wav",
    ".mp3",
    ".ogg",
    ".m4a",
    ".ttf",
    ".otf",
}

PACKAGE_ALIASES = {
    "bs4": "beautifulsoup4",
    "customtkinter": "customtkinter",
    "essential_generators": "essential-generators",
    "matplotlib": "matplotlib",
    "numpy": "numpy",
    "pandas": "pandas",
    "plotly": "plotly",
    "pygame": "pygame",
    "requests": "requests",
    "vlc": "python-vlc",
}

SIGNAL_PATTERNS = {
    "mainloop": re.compile(r"\.mainloop\s*\(", re.IGNORECASE),
    "photoimage": re.compile(r"\bPhotoImage\s*\(", re.IGNORECASE),
    "pygame_display": re.compile(r"\bpygame\.display\.set_mode\s*\(", re.IGNORECASE),
    "pygame_init": re.compile(r"\bpygame\.init\s*\(", re.IGNORECASE),
    "pygame_mixer": re.compile(r"\bpygame\.mixer\.init\s*\(", re.IGNORECASE),
    "curses_wrapper": re.compile(r"\bcurses\.wrapper\s*\(", re.IGNORECASE),
    "input_call": re.compile(r"\binput\s*\(", re.IGNORECASE),
    "plt_show": re.compile(r"\b(?:plt|pyplot)\.show\s*\(", re.IGNORECASE),
    "vlc_instance": re.compile(r"\bvlc\.Instance\s*\(", re.IGNORECASE),
    "while_true": re.compile(r"\bwhile\s+True\b"),
}

URL_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s'\"<>]+")
ABS_PATH_RE = re.compile(r"(?<!:)(?:/[^\s'\"<>]+|[A-Za-z]:[\\/][^\s'\"<>]+|\\\\[^\s'\"<>]+)")
STDLIB_MODULES = set(getattr(sys, "stdlib_module_names", set()))


def normalize_name(name: str) -> str:
    return name.lower().replace("_", "-")


def canonical_package_name(import_name: str) -> str:
    return normalize_name(PACKAGE_ALIASES.get(import_name, import_name))


def read_text_auto(path: Path) -> tuple[str | None, str | None]:
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeError:
            continue
    return None, None


def scan_python_literals(text: str) -> tuple[set[str], set[str]]:
    urls: set[str] = set()
    absolute_paths: set[str] = set()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return urls, absolute_paths
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value.strip()
            if URL_RE.search(value):
                urls.add(URL_RE.search(value).group(0))
            if (value.startswith("/") and len(value) > 1) or re.match(r"^[A-Za-z]:[\/]", value) or value.startswith("\\"):
                absolute_paths.add(value)
    return urls, absolute_paths


def parse_requirement_packages(text: str) -> list[str]:
    packages: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", ".")):
            continue
        token = re.split(r"[<>=!~;\s\[]", line, maxsplit=1)[0].strip()
        if not token:
            continue
        if "@" in token:
            token = token.split("@", 1)[0].strip()
        if token:
            packages.add(normalize_name(token))
    return sorted(packages)


def scan_text(text: str) -> tuple[set[str], set[str], set[str]]:
    urls = set(URL_RE.findall(text))
    absolute_paths: set[str] = set()
    for match in ABS_PATH_RE.finditer(text):
        value = match.group(0).strip().strip("'\"`),.;[]{}")
        if not value or value.startswith("//") or "://" in value:
            continue
        absolute_paths.add(value)

    signals = {name for name, pattern in SIGNAL_PATTERNS.items() if pattern.search(text)}
    return urls, absolute_paths, signals


def scan_python_file(path: Path) -> dict:
    text, encoding = read_text_auto(path)
    result = {
        "encoding": encoding,
        "imports": set(),
        "urls": set(),
        "absolute_paths": set(),
        "signals": set(),
        "parse_error": None,
    }
    if text is None:
        result["parse_error"] = "unreadable text"
        return result

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            result["parse_error"] = f"{exc.msg} (line {exc.lineno})"
        else:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].add(alias.name.split(".", 1)[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    result["imports"].add(node.module.split(".", 1)[0])

    urls, absolute_paths = scan_python_literals(text)
    _, _, signals = scan_text(text)
    result["urls"].update(urls)
    result["absolute_paths"].update(absolute_paths)
    result["signals"].update(signals)
    return result


def project_root_for(target: Path) -> Path:
    return target.parent if target.is_file() else target


def build_local_names(root: Path, py_files: list[Path]) -> set[str]:
    local_names: set[str] = set()
    for py in py_files:
        local_names.add(py.stem)
        try:
            rel_parent = py.parent.relative_to(root)
        except ValueError:
            continue
        for part in rel_parent.parts:
            local_names.add(part)
    return local_names


def scan_requirements(root: Path) -> tuple[list[dict], set[str], list[str]]:
    req_files = sorted(
        [*root.rglob("requirements*.txt"), *root.rglob("pyproject.toml")],
        key=lambda p: p.as_posix(),
    )
    reports: list[dict] = []
    packages: set[str] = set()
    parse_errors: list[str] = []

    for req in req_files:
        text, encoding = read_text_auto(req)
        rel = req.relative_to(root).as_posix()
        if text is None:
            reports.append({"path": rel, "encoding": None, "packages": [], "parse_error": "unreadable text"})
            parse_errors.append(f"{rel}: unreadable text")
            continue
        if req.suffix.lower() == ".toml":
            current = set(re.findall(r'^[ \t]*([A-Za-z0-9_.-]+)\s*=\s*', text, flags=re.MULTILINE))
        else:
            current = set(parse_requirement_packages(text))
        packages.update(current)
        reports.append({"path": rel, "encoding": encoding, "packages": sorted(current), "parse_error": None})

    return reports, packages, parse_errors


def scan_support_and_assets(root: Path) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    support_files: set[str] = set()
    asset_files: set[str] = set()
    asset_dirs: set[str] = set()
    remote_urls: set[str] = set()
    absolute_paths: set[str] = set()

    for path in root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()

        if suffix in {".txt", ".json", ".yaml", ".yml", ".cfg", ".ini", ".toml", ".html", ".htm"}:
            if not path.name.startswith("requirements") and path.name != "pyproject.toml":
                support_files.add(rel)

        if suffix in ASSET_EXTENSIONS:
            asset_files.add(rel)
            if path.parent != root:
                asset_dirs.add(path.parent.relative_to(root).as_posix())

        if suffix in TEXT_SCAN_EXTENSIONS:
            text, _ = read_text_auto(path)
            if text is None:
                continue
            urls, _, _ = scan_text(text)
            remote_urls.update(urls)

    return (
        sorted(support_files),
        sorted(asset_files),
        sorted(asset_dirs),
        sorted(remote_urls),
        sorted(absolute_paths),
    )


def build_stack_tags(imports: set[str], signals: set[str], remote_urls: set[str]) -> list[str]:
    tags: list[str] = []

    if imports.intersection({"tkinter", "customtkinter", "turtle"}) or signals.intersection({"mainloop", "photoimage"}):
        tags.append("tk")
    if "pygame" in imports or signals.intersection({"pygame_display", "pygame_init", "pygame_mixer"}):
        tags.append("pygame")
    if "curses" in imports or "curses_wrapper" in signals:
        tags.append("curses")
    if "vlc" in imports or "vlc_instance" in signals:
        tags.append("audio")
    if remote_urls or "requests" in imports:
        tags.append("network")
    if imports.intersection({"matplotlib", "numpy", "pandas", "plotly"}) or "plt_show" in signals:
        tags.append("data")
    if not any(tag in tags for tag in {"tk", "pygame", "audio"}):
        tags.append("terminal")

    order = ["tk", "pygame", "curses", "audio", "network", "data", "terminal"]
    return [tag for tag in order if tag in tags]


def scan_project(target: Path) -> dict:
    root = project_root_for(target)
    project_name = root.name
    if not root.exists():
        return {
            "project": project_name,
            "path": root.as_posix(),
            "stack_tags": [],
            "entry_candidates": [],
            "local_imports": [],
            "stdlib_imports": [],
            "external_imports": [],
            "requirements_files": [],
            "requirements_hints": [f"missing project root: {root.as_posix()}"] ,
            "asset_dirs": [],
            "asset_files": [],
            "support_files": [],
            "remote_urls": [],
            "absolute_paths": [],
            "signals": [],
            "warnings": [f"target does not exist: {target.as_posix()}"],
            "parse_errors": [],
        }

    py_files = [
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts and path.name != "tempCodeRunnerFile.py"
    ]
    local_names = build_local_names(root, py_files)

    imported_roots: set[str] = set()
    local_imports: set[str] = set()
    stdlib_imports: set[str] = set()
    external_imports: set[str] = set()
    signals: set[str] = set()
    remote_urls: set[str] = set()
    absolute_paths: set[str] = set()
    parse_errors: list[str] = []

    for py in py_files:
        scan = scan_python_file(py)
        if scan["parse_error"]:
            parse_errors.append(f"{py.relative_to(root).as_posix()}: {scan['parse_error']}")
        signals.update(scan["signals"])
        remote_urls.update(scan["urls"])
        absolute_paths.update(scan["absolute_paths"])
        for imported in scan["imports"]:
            if imported in local_names:
                local_imports.add(imported)
                imported_roots.add(imported)
            elif imported in STDLIB_MODULES:
                stdlib_imports.add(imported)
            else:
                external_imports.add(imported)

    requirements_files, requirement_packages, requirement_parse_errors = scan_requirements(root)
    support_files, asset_files, asset_dirs, support_urls, support_abs = scan_support_and_assets(root)
    remote_urls.update(support_urls)
    absolute_paths.update(support_abs)
    parse_errors.extend(requirement_parse_errors)

    expected_packages = {canonical_package_name(name) for name in external_imports}
    requirements_hints: list[str] = []
    if external_imports and not requirements_files:
        requirements_hints.append("missing requirements file for external imports: " + ", ".join(sorted(expected_packages)))
    else:
        missing = sorted(pkg for pkg in expected_packages if pkg not in requirement_packages)
        if missing:
            requirements_hints.append("requirements file does not mention: " + ", ".join(missing))

    entry_candidates = sorted(
        {
            py.relative_to(root).as_posix()
            for py in py_files
            if py.stem not in imported_roots
        }
    )

    warnings: list[str] = []
    if remote_urls:
        warnings.append("remote URL dependency detected")
    if absolute_paths:
        warnings.append("absolute path literals detected")
    warnings.extend(requirements_hints)
    warnings.extend(parse_errors)

    return {
        "project": project_name,
        "path": root.as_posix(),
        "stack_tags": build_stack_tags(local_imports | stdlib_imports | external_imports, signals, remote_urls),
        "entry_candidates": entry_candidates,
        "local_imports": sorted(local_imports),
        "stdlib_imports": sorted(stdlib_imports),
        "external_imports": sorted(external_imports),
        "requirements_files": requirements_files,
        "requirements_hints": requirements_hints,
        "asset_dirs": asset_dirs,
        "asset_files": asset_files,
        "support_files": support_files,
        "remote_urls": sorted(remote_urls),
        "absolute_paths": sorted(absolute_paths),
        "signals": sorted(signals),
        "warnings": warnings,
        "parse_errors": parse_errors,
    }


def render_text(report: dict) -> str:
    lines = [f"## {report['project']}", f"Path: {report['path']}"]
    lines.append(f"Stack tags: {', '.join(report['stack_tags']) if report['stack_tags'] else '-'}")
    lines.append(f"Entry candidates: {', '.join(report['entry_candidates']) if report['entry_candidates'] else '-'}")
    lines.append(f"Local imports: {', '.join(report['local_imports']) if report['local_imports'] else '-'}")
    lines.append(f"Stdlib imports: {', '.join(report['stdlib_imports']) if report['stdlib_imports'] else '-'}")
    lines.append(f"External imports: {', '.join(report['external_imports']) if report['external_imports'] else '-'}")
    if report["requirements_files"]:
        lines.append("Requirements:")
        for req in report["requirements_files"]:
            encoding = req["encoding"] or "unknown"
            if req["parse_error"]:
                lines.append(f"  - {req['path']} [{encoding}] -> {req['parse_error']}")
            else:
                packages = ", ".join(req["packages"]) if req["packages"] else "-"
                lines.append(f"  - {req['path']} [{encoding}] -> {packages}")
    else:
        lines.append("Requirements: -")
    lines.append(f"Asset dirs: {', '.join(report['asset_dirs']) if report['asset_dirs'] else '-'}")
    lines.append(f"Asset files: {', '.join(report['asset_files']) if report['asset_files'] else '-'}")
    lines.append(f"Support files: {', '.join(report['support_files']) if report['support_files'] else '-'}")
    lines.append(f"Remote URLs: {', '.join(report['remote_urls']) if report['remote_urls'] else '-'}")
    lines.append(f"Absolute paths: {', '.join(report['absolute_paths']) if report['absolute_paths'] else '-'}")
    lines.append(f"Signals: {', '.join(report['signals']) if report['signals'] else '-'}")
    lines.append(f"Warnings: {', '.join(report['warnings']) if report['warnings'] else '-'}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Statically inspect GUI/game/desktop project folders for imports, "
            "requirements hints, asset directories, and likely entry points."
        ),
        epilog=(
            "Examples:\n"
            "  python scripts/check_gui_requirements.py --known-projects\n"
            "  python scripts/check_gui_requirements.py Chess_Game 'Music-Player' --json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="*", help="Project folders or files to scan.")
    parser.add_argument(
        "--root",
        default=".",
        help="Base directory for --known-projects. Defaults to the current directory.",
    )
    parser.add_argument(
        "--known-projects",
        action="store_true",
        help="Scan the canonical project list relative to --root.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    args = parser.parse_args()

    targets: list[Path] = []
    if args.known_projects:
        base = Path(args.root)
        targets.extend(base / name for name in KNOWN_PROJECTS)
    targets.extend(Path(path) for path in args.paths)

    if not targets:
        parser.error("provide at least one path or use --known-projects")

    unique_targets: list[Path] = []
    seen: set[str] = set()
    for target in targets:
        key = target.resolve(strict=False).as_posix()
        if key not in seen:
            seen.add(key)
            unique_targets.append(target)

    reports = [scan_project(target) for target in unique_targets]

    if args.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    else:
        for index, report in enumerate(reports):
            if index:
                print()
            print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
