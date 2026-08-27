#!/usr/bin/env python3
"""Inventory python-mini-project style folders without executing project code.

This helper is bundled with the repo skill and is intended for any checkout of
ndleah/python-mini-project or a similarly structured fork. It scans top-level
folders for README files, Python files, requirements/pyproject files, notebooks,
assets, and imports, then assigns a coarse operating category.
"""

from __future__ import annotations

import argparse
import ast
import json
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

warnings.simplefilter("ignore", SyntaxWarning)

NOISE_DIRS = {
    ".git",
    ".github",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "env",
    "node_modules",
    "site-packages",
    "skills",
    "venv",
}

GUI_IMPORTS = {"tkinter", "customtkinter", "pygame", "turtle", "curses", "vlc"}
WEB_IMPORTS = {
    "flask",
    "fastapi",
    "uvicorn",
    "socket",
    "smtplib",
    "imaplib",
    "firebase",
    "pywhatkit",
    "pyautogui",
    "spotipy",
    "pexpect",
}
DATA_MEDIA_IMPORTS = {
    "requests",
    "bs4",
    "BeautifulSoup",
    "pandas",
    "numpy",
    "matplotlib",
    "PIL",
    "cv2",
    "mediapipe",
    "torch",
    "ultralytics",
    "tensorflow",
    "keras",
    "nltk",
    "PyPDF2",
    "img2pdf",
    "qrcode",
    "pyqrcode",
    "pytube",
    "moviepy",
    "speech_recognition",
    "pyttsx3",
    "win32com",
}
UNSAFE_IMPORTS = {"os", "subprocess", "pyautogui", "keyboard", "smtplib", "imaplib", "socket", "pexpect"}

CATEGORY_OVERRIDES = {
    # Exact folder-name routes captured during skill construction. Heuristics below
    # are only a fallback for forks or newly added project folders.
    "automated_mailing": "web-network-and-automation",
    "chinese_flashcard": "games-gui-and-desktop",
    "crud_in_flask": "web-network-and-automation",
    "dictionary": "games-gui-and-desktop",
    "desktopassistant": "web-network-and-automation",
    "digit_recognizer": "data-media-ml-and-vision",
    "extractphonenumberemail": "cli-algorithms-and-utilities",
    "finance_tracker": "games-gui-and-desktop",
    "firebase_authentication_using_flask": "web-network-and-automation",
    "google_translate": "data-media-ml-and-vision",
    "img_to_ascii": "data-media-ml-and-vision",
    "ip_locator": "web-network-and-automation",
    "investment calculator": "games-gui-and-desktop",
    "mail_checker": "web-network-and-automation",
    "othello_reversi_game": "games-gui-and-desktop",
    "password generator": "games-gui-and-desktop",
    "password_generator_2": "cli-algorithms-and-utilities",
    "postgresql_dumper": "web-network-and-automation",
    "rss_manager": "web-network-and-automation",
    "simple_chatbot": "data-media-ml-and-vision",
    "simple_http_server": "web-network-and-automation",
    "smart_calculator": "games-gui-and-desktop",
    "socket_example": "web-network-and-automation",
    "speaking_dictionary": "data-media-ml-and-vision",
    "todo_app": "web-network-and-automation",
    "url_shortener": "web-network-and-automation",
    "web scraping iphone from flipkart": "data-media-ml-and-vision",
    "whatsapp_bot": "web-network-and-automation",
    "windows_shutdown": "web-network-and-automation",
    "zombie_game": "games-gui-and-desktop",
}

CATEGORY_HINTS = {
    "cli-algorithms-and-utilities": [
        "binary", "caesar", "cat", "converter", "roman", "dictionary", "diff", "email slicer",
        "morse", "execute shell", "expense", "guessing", "password_generator_2", "prefix",
        "stack", "star", "sudoku", "tower", "csv", "linked", "lorem", "minion",
        "string", "trie", "calculator", "address", "hash", "triangle", "weights",
    ],
    "games-gui-and-desktop": [
        "game", "chess", "snake", "hang", "pong", "minesweeper", "othello", "tic",
        "connect", "dice", "pet", "flashcard", "music", "typing", "finance", "investment",
        "password generator", "smart_calculator", "dictionary", "screen", "donut", "textventure",
        "zombie", "color", "egg", "caterpillar",
    ],
    "web-network-and-automation": [
        "flask", "firebase", "rss", "http", "server", "url", "socket", "mail", "whatsapp",
        "assistant", "port", "postgres", "shutdown", "spam", "locator", "website-builder", "todo",
        "automated_mailing",
    ],
    "data-media-ml-and-vision": [
        "scraping", "pdf", "image", "audio", "youtube", "speech", "textto", "speaking",
        "face", "lanes", "motion", "object", "shape", "plot", "ann", "digit", "mnist",
        "prediction", "xls", "qr", "compressor", "resize", "ascii", "nasa", "geo",
        "translate", "clip", "download",
    ],
}


@dataclass
class ProjectSummary:
    name: str
    category: str
    python_files: list[str] = field(default_factory=list)
    readmes: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    notebooks: list[str] = field(default_factory=list)
    asset_dirs: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    hazards: list[str] = field(default_factory=list)


def read_text_lossy(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-16", "utf-16le", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def collect_imports(py_files: Iterable[Path], root: Path) -> tuple[list[str], list[str]]:
    imports: set[str] = set()
    hazards: set[str] = set()
    for file_path in py_files:
        try:
            text = read_text_lossy(file_path)
            tree = ast.parse(text, filename=str(file_path.relative_to(root)))
        except Exception as exc:  # syntax is reported by check_project_static.py
            hazards.add(f"syntax/read issue in {file_path.relative_to(root)}: {type(exc).__name__}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                fn = node.func
                name = ""
                if isinstance(fn, ast.Attribute):
                    name = fn.attr
                elif isinstance(fn, ast.Name):
                    name = fn.id
                if name in {"system", "Popen", "run", "call", "bind", "listen", "mainloop", "Tk"}:
                    hazards.add(f"top-level review needed for call `{name}` in {file_path.relative_to(root)}")
        for imp in sorted(imports & UNSAFE_IMPORTS):
            hazards.add(f"import `{imp}` may have external side effects; inspect before running")
    return sorted(imports), sorted(hazards)


def normalize_name(name: str) -> str:
    return name.lower().replace("-", "_").strip()


def choose_category(name: str, imports: set[str], has_notebook: bool) -> str:
    normalized = normalize_name(name)
    if normalized in CATEGORY_OVERRIDES:
        return CATEGORY_OVERRIDES[normalized]
    lowered = name.lower().replace("_", " ").replace("-", " ")
    if imports & WEB_IMPORTS:
        return "web-network-and-automation"
    if imports & DATA_MEDIA_IMPORTS or has_notebook:
        return "data-media-ml-and-vision"
    if imports & GUI_IMPORTS:
        return "games-gui-and-desktop"
    scores = {cat: sum(1 for hint in hints if hint in lowered) for cat, hints in CATEGORY_HINTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "cli-algorithms-and-utilities"


def summarize_project(path: Path, root: Path) -> ProjectSummary:
    py_files = sorted(path.rglob("*.py"))
    readmes = sorted(p for p in path.iterdir() if p.is_file() and p.name.lower().startswith("readme"))
    requirements = sorted(
        p for p in path.iterdir()
        if p.is_file() and (p.name.lower().startswith("requirements") or p.name == "pyproject.toml")
    )
    notebooks = sorted(path.rglob("*.ipynb"))
    asset_dirs = [p.name for p in sorted(path.iterdir()) if p.is_dir() and p.name not in NOISE_DIRS]
    imports, hazards = collect_imports(py_files, root)
    category = choose_category(path.name, set(imports), bool(notebooks))
    return ProjectSummary(
        name=path.name,
        category=category,
        python_files=[str(p.relative_to(path)) for p in py_files[:12]],
        readmes=[p.name for p in readmes],
        requirements=[p.name for p in requirements],
        notebooks=[str(p.relative_to(path)) for p in notebooks[:12]],
        asset_dirs=asset_dirs[:12],
        imports=imports,
        hazards=hazards[:12],
    )


def inventory(root: Path) -> list[ProjectSummary]:
    projects: list[ProjectSummary] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir() or child.name in NOISE_DIRS or child.name.startswith("."):
            continue
        has_signal = any(child.rglob("*.py")) or any(child.rglob("*.ipynb")) or any(
            p.is_file() and p.name.lower().startswith("readme") for p in child.iterdir()
        )
        if has_signal:
            projects.append(summarize_project(child, root))
    return projects


def print_markdown(rows: list[ProjectSummary]) -> None:
    print("| Project | Category | Key files | Requirements | Imports | Hazards |")
    print("| --- | --- | --- | --- | --- | --- |")
    for row in rows:
        files = ", ".join(row.python_files[:4] + row.notebooks[:2]) or "—"
        reqs = ", ".join(row.requirements) or "—"
        imports = ", ".join(row.imports[:8]) or "—"
        hazards = "; ".join(row.hazards[:3]) or "—"
        print(f"| `{row.name}` | `{row.category}` | {files} | {reqs} | {imports} | {hazards} |")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory top-level python-mini-project folders without executing them.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Checkout root to scan; default: current directory.")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown", help="Output format.")
    parser.add_argument("--category", help="Only show one category id, e.g. games-gui-and-desktop.")
    args = parser.parse_args()
    root = args.root.resolve()
    rows = inventory(root)
    if args.category:
        rows = [r for r in rows if r.category == args.category]
    if args.format == "json":
        print(json.dumps([asdict(r) for r in rows], indent=2, sort_keys=True))
    else:
        print_markdown(rows)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)
