#!/usr/bin/env python3
"""Static checker for python-mini-project folders.

The checker never imports or executes project modules. It parses Python source,
reports syntax status, top-level side-effect clues, dependency files, and common
runtime hazards so agents can decide which sub-skill and environment to use.
"""

from __future__ import annotations

import argparse
import ast
import json
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path

warnings.simplefilter("ignore", SyntaxWarning)

RISKY_CALLS = {
    "Tk": "creates a Tk window; needs display",
    "mainloop": "starts a GUI event loop",
    "set_mode": "opens a pygame display",
    "bind": "binds a socket/port",
    "listen": "listens on a socket/port",
    "Popen": "runs a subprocess",
    "run": "may run a subprocess",
    "system": "runs a shell command",
    "shutdown": "may shut down a host or service",
    "get": "may make HTTP/network calls",
    "post": "may make HTTP/network calls",
    "sendmail": "sends email",
    "login": "may authenticate to an external service",
}
RISKY_IMPORTS = {
    "tkinter": "GUI/display",
    "customtkinter": "GUI/display",
    "pygame": "GUI/audio/display",
    "turtle": "GUI/display",
    "curses": "terminal control loop",
    "socket": "network/socket",
    "requests": "HTTP/network",
    "bs4": "web scraping",
    "flask": "web service",
    "fastapi": "web service",
    "smtplib": "email send",
    "imaplib": "email account access",
    "pywhatkit": "browser/WhatsApp automation",
    "pyautogui": "desktop automation",
    "cv2": "OpenCV/camera/media",
    "mediapipe": "camera/CV runtime",
    "torch": "ML backend/model dependency",
    "tensorflow": "ML backend/model dependency",
    "keras": "ML backend/model dependency",
    "ultralytics": "YOLO model dependency/download risk",
    "win32com": "Windows COM only",
    "pexpect": "interactive process automation",
    "os": "review for host/file side effects",
    "subprocess": "review for shell/process side effects",
}


@dataclass
class FileReport:
    path: str
    syntax_ok: bool
    imports: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class ProjectReport:
    project: str
    readmes: list[str]
    requirements: list[str]
    notebooks: list[str]
    files: list[FileReport]
    summary_risks: list[str]


def read_text_lossy(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-16", "utf-16le", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def inspect_file(path: Path, root: Path) -> FileReport:
    rel = str(path.relative_to(root))
    try:
        text = read_text_lossy(path)
        tree = ast.parse(text, filename=rel)
    except Exception as exc:
        return FileReport(path=rel, syntax_ok=False, error=f"{type(exc).__name__}: {exc}")

    imports: set[str] = set()
    risks: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = dotted_name(node.func).split(".")[-1]
            if name in RISKY_CALLS:
                risks.append(f"line {node.lineno}: call `{name}` — {RISKY_CALLS[name]}")
    for imp in sorted(imports):
        if imp in RISKY_IMPORTS:
            risks.insert(0, f"import `{imp}` — {RISKY_IMPORTS[imp]}")
    return FileReport(path=rel, syntax_ok=True, imports=sorted(imports), risks=risks[:20])


def inspect_project(path: Path, root: Path) -> ProjectReport:
    files = [inspect_file(p, root) for p in sorted(path.rglob("*.py"))]
    readmes = [str(p.relative_to(root)) for p in sorted(path.iterdir()) if p.is_file() and p.name.lower().startswith("readme")]
    requirements = [
        str(p.relative_to(root))
        for p in sorted(path.iterdir())
        if p.is_file() and (p.name.lower().startswith("requirements") or p.name == "pyproject.toml")
    ]
    notebooks = [str(p.relative_to(root)) for p in sorted(path.rglob("*.ipynb"))]
    summary: set[str] = set()
    for file_report in files:
        for risk in file_report.risks:
            if risk.startswith("import `"):
                summary.add(risk)
    if notebooks:
        summary.add("contains notebooks; inspect outputs/dependencies before execution")
    if not readmes:
        summary.add("missing top-level README-style file")
    return ProjectReport(
        project=str(path.relative_to(root)),
        readmes=readmes,
        requirements=requirements,
        notebooks=notebooks,
        files=files,
        summary_risks=sorted(summary),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Static syntax/import-risk checker for python-mini-project folders.")
    parser.add_argument("projects", nargs="+", type=Path, help="Project folders to inspect, relative to --root unless absolute.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Checkout root; default: current directory.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()
    root = args.root.resolve()
    reports: list[ProjectReport] = []
    for item in args.projects:
        project = item if item.is_absolute() else root / item
        if not project.exists() or not project.is_dir():
            raise SystemExit(f"Project folder not found: {project}")
        reports.append(inspect_project(project.resolve(), root))

    if args.format == "json":
        print(json.dumps([asdict(r) for r in reports], indent=2, sort_keys=True))
    else:
        for report in reports:
            print(f"# {report.project}")
            print(f"README files: {', '.join(report.readmes) or 'none'}")
            print(f"Requirements/pyproject: {', '.join(report.requirements) or 'none'}")
            print(f"Notebooks: {', '.join(report.notebooks) or 'none'}")
            print("Summary risks:")
            for risk in report.summary_risks or ["none"]:
                print(f"- {risk}")
            print("Files:")
            for file_report in report.files:
                status = "ok" if file_report.syntax_ok else f"ERROR {file_report.error}"
                print(f"- {file_report.path}: syntax {status}; imports={', '.join(file_report.imports[:10]) or 'none'}")
                for risk in file_report.risks[:5]:
                    print(f"  - {risk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
