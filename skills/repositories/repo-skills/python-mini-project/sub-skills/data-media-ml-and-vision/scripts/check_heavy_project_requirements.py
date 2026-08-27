#!/usr/bin/env python3
"""Static checker for heavy data/media/vision project requirements.

The checker never imports or executes project code. It reads source files,
notebooks, requirements files, and pyproject metadata to summarize external
imports, dependency clues, and backend risks.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover - optional dependency
    tomllib = None


IGNORED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".ipynb_checkpoints",
    ".venv",
    "venv",
    "env",
    "skills",
    "node_modules",
    "build",
    "dist",
}

SPECIAL_LOCAL_IMPORTS = {"app", "password", "secret", "token", "credentials"}

PACKAGE_HINTS = {
    "PIL": "pillow",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "PyPDF2": "pypdf2",
    "PyDictionary": "pydictionary",
    "speech_recognition": "speechrecognition",
    "chart_studio": "chart-studio",
    "sklearn": "scikit-learn",
    "win32com": "pywin32",
    "gtts": "gtts",
}

PROJECT_HINT_IMPORTS = {
    "cv2",
    "requests",
    "bs4",
    "beautifulsoup4",
    "pandas",
    "pillow",
    "img2pdf",
    "qrcode",
    "pyqrcode",
    "pypng",
    "pywhatkit",
    "pytube",
    "moviepy",
    "pyttsx3",
    "speechrecognition",
    "speech_recognition",
    "wikipedia",
    "mediapipe",
    "torch",
    "ultralytics",
    "tensorflow",
    "keras",
    "nltk",
    "folium",
    "chart_studio",
    "cufflinks",
    "scikit-learn",
    "flask",
    "fastapi",
    "win32com",
    "easygui",
    "validators",
    "pywin32",
}

HAZARD_ORDER = [
    "network",
    "credentials",
    "display",
    "audio",
    "codec",
    "camera",
    "video-input",
    "model-download",
    "tensorflow-pin",
    "notebook",
    "windows-com",
    "service-deployment",
]

SOURCE_HINTS = [
    (re.compile(r"VideoCapture\s*\(\s*0\s*\)"), "camera", "default webcam access"),
    (re.compile(r"VideoCapture\s*\(\s*[\"'].*\.(?:mp4|avi|mov|mkv)[\"']\s*\)"), "video-input", "local video-file input"),
    (re.compile(r"cv2\.imshow\s*\("), "display", "OpenCV display window"),
    (re.compile(r"\bTk\s*\(|\btkinter\b", re.IGNORECASE), "display", "Tkinter window"),
    (re.compile(r"\beasygui\b", re.IGNORECASE), "display", "easygui dialog"),
    (re.compile(r"\bYOLO\s*\("), "model-download", "YOLO model construction"),
    (re.compile(r"Dispatch\s*\(\s*[\"']Excel\.Application[\"']\s*\)"), "windows-com", "Excel COM automation"),
    (re.compile(r"\bfrom\s+google\.colab\b|\bgoogle\.colab\b"), "notebook", "Google Colab notebook"),
]

IMPORT_HINTS = {
    "requests": ("network", "HTTP requests"),
    "bs4": ("network", "HTML scraping"),
    "beautifulsoup4": ("network", "HTML scraping"),
    "pytube": ("network", "YouTube download"),
    "wikipedia": ("network", "Wikipedia lookup"),
    "speechrecognition": ("network", "speech recognition API"),
    "speech_recognition": ("network", "speech recognition API"),
    "smtplib": ("network", "SMTP mail"),
    "imaplib": ("network", "IMAP mail"),
    "pyttsx3": ("audio", "text-to-speech"),
    "speechrecognition": ("audio", "speech-to-text"),
    "speech_recognition": ("audio", "speech-to-text"),
    "pyaudio": ("audio", "microphone access"),
    "moviepy": ("codec", "media transcoding"),
    "cv2": ("camera", "OpenCV video/image processing"),
    "mediapipe": ("camera", "vision landmarks"),
    "torch": ("model-download", "PyTorch / YOLO inference"),
    "ultralytics": ("model-download", "YOLO inference"),
    "tensorflow": ("tensorflow-pin", "TensorFlow runtime"),
    "keras": ("tensorflow-pin", "Keras runtime"),
    "folium": ("notebook", "notebook map plotting"),
    "chart_studio": ("notebook", "Plotly notebook plotting"),
    "cufflinks": ("notebook", "Plotly notebook plotting"),
    "sklearn": ("notebook", "machine-learning utilities"),
    "scikit-learn": ("notebook", "machine-learning utilities"),
    "win32com": ("windows-com", "Excel COM"),
    "flask": ("service-deployment", "Flask app"),
    "fastapi": ("service-deployment", "FastAPI app"),
}

STD_LIB = {name.lower() for name in getattr(sys, "stdlib_module_names", set())}
STD_LIB.update(
    {
        "tkinter",
        "unittest",
        "argparse",
        "ast",
        "json",
        "re",
        "sys",
        "os",
        "pathlib",
        "io",
        "time",
        "shutil",
        "mimetypes",
        "email",
        "pprint",
        "re",
        "dataclasses",
        "typing",
        "collections",
        "itertools",
    }
)


@dataclass
class ProjectSummary:
    path: str
    source_files: list[str] = field(default_factory=list)
    notebook_files: list[str] = field(default_factory=list)
    requirement_files: list[str] = field(default_factory=list)
    external_imports: list[str] = field(default_factory=list)
    local_imports: list[str] = field(default_factory=list)
    requirement_packages: list[str] = field(default_factory=list)
    missing_from_requirements: list[str] = field(default_factory=list)
    extra_requirements: list[str] = field(default_factory=list)
    hazards: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)


@dataclass
class RequirementEntry:
    name: str
    raw: str
    source: str


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIR_NAMES for part in path.parts)


def iter_project_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if is_ignored(path):
            continue
        if path.is_file():
            if path.name.endswith("-checkpoint.ipynb"):
                continue
            yield path


def read_text_guessing(path: Path) -> str:
    encodings = ("utf-8", "utf-8-sig", "utf-16", "utf-16le", "latin-1")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except Exception as exc:  # pragma: no cover - fallback path
            last_error = exc
    raise last_error  # type: ignore[misc]


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except Exception:
        return str(path)


def normalize_import_root(module_name: str) -> str:
    return module_name.split(".", 1)[0].strip()


def import_to_package(import_root: str) -> str:
    return PACKAGE_HINTS.get(import_root, import_root).lower()


def is_stdlib_module(import_root: str) -> bool:
    return import_root.lower() in STD_LIB


def parse_source_imports(source: str, filename: str, notebook: bool = False) -> tuple[set[str], list[str]]:
    text = source
    if notebook:
        stripped_lines = []
        for line in text.splitlines():
            probe = line.lstrip()
            if probe.startswith(("%", "!", "?")):
                continue
            stripped_lines.append(line)
        text = "\n".join(stripped_lines)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(text, filename=filename)
    except SyntaxError as exc:
        imports: set[str] = set()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("import "):
                tail = line[len("import ") :]
                for part in tail.split(","):
                    name = part.strip().split(" as ", 1)[0].strip()
                    if name:
                        imports.add(normalize_import_root(name))
            elif line.startswith("from "):
                match = re.match(r"from\s+([A-Za-z0-9_.]+)\s+import", line)
                if match:
                    imports.add(normalize_import_root(match.group(1)))
        return imports, [f"{filename}: syntax error fallback used ({exc.msg})"]

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(normalize_import_root(alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(normalize_import_root(node.module))
    return imports, []


def extract_imports_from_text_blob(text: str) -> set[str]:
    imports: set[str] = set()
    for match in re.finditer(r"\bfrom\s+([A-Za-z0-9_.]+)\s+import\b", text):
        imports.add(normalize_import_root(match.group(1)))
    for match in re.finditer(r"\bimport\s+([A-Za-z0-9_.]+)", text):
        name = match.group(1).split(",", 1)[0].split(" as ", 1)[0].strip()
        if name:
            imports.add(normalize_import_root(name))
    return imports


def parse_notebook(path: Path) -> tuple[set[str], list[str]]:
    try:
        text = read_text_guessing(path)
    except Exception as exc:
        return set(), [f"{path.name}: notebook read failed ({exc})"]

    if path.stat().st_size > 2_000_000:
        imports = extract_imports_from_text_blob(text.replace("\\n", "\n"))
        return imports, [f"{path.name}: large notebook scanned with regex fallback"]

    try:
        data = json.loads(text)
    except Exception as exc:
        imports = extract_imports_from_text_blob(text.replace("\\n", "\n"))
        return imports, [f"{path.name}: notebook parse failed ({exc}); regex fallback used"]

    imports: set[str] = set()
    errors: list[str] = []
    for index, cell in enumerate(data.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        cell_imports, cell_errors = parse_source_imports(
            source,
            filename=f"{path.name}:cell{index}",
            notebook=True,
        )
        imports.update(cell_imports)
        errors.extend(cell_errors)
    return imports, errors


def parse_requirement_line(line: str) -> RequirementEntry | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith(("-r ", "--", ".", "git+", "http://", "https://")):
        return None

    stripped = stripped.split("#", 1)[0].strip()
    if not stripped:
        return None

    match = re.match(r"^([A-Za-z0-9_.-]+)(.*)$", stripped)
    if not match:
        return None

    name = match.group(1)
    rest = match.group(2).strip()
    if not rest:
        return RequirementEntry(name=name, raw=line.rstrip(), source="requirements")

    if rest.startswith((":", "=", "[", ";")):
        return RequirementEntry(name=name, raw=line.rstrip(), source="requirements")
    if rest.startswith((">", "<", "!", "~")):
        return RequirementEntry(name=name, raw=line.rstrip(), source="requirements")
    if rest.lower().startswith("pip install"):
        return RequirementEntry(name=name, raw=line.rstrip(), source="requirements")

    return None


def parse_requirements_file(path: Path) -> list[RequirementEntry]:
    entries: list[RequirementEntry] = []
    try:
        text = read_text_guessing(path)
    except Exception:
        return entries

    if path.name == "pyproject.toml":
        if tomllib is None:
            return entries
        try:
            data = tomllib.loads(text)
        except Exception:
            return entries

        project = data.get("project", {})
        for item in project.get("dependencies", []) or []:
            if isinstance(item, str):
                parsed = parse_requirement_line(item)
                if parsed:
                    entries.append(parsed)
        poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        if isinstance(poetry, dict):
            for name, spec in poetry.items():
                if str(name).lower() == "python":
                    continue
                raw = f"{name}{spec if isinstance(spec, str) else ''}"
                parsed = parse_requirement_line(raw)
                if parsed:
                    entries.append(parsed)
        return entries

    for line in text.splitlines():
        parsed = parse_requirement_line(line)
        if parsed:
            entries.append(parsed)
    return entries


def collect_local_import_names(root: Path, files: list[Path]) -> set[str]:
    names: set[str] = set()
    for path in files:
        if path.suffix == ".py":
            names.add(path.stem.lower())
            parent = path.parent
            while parent != root and parent != parent.parent:
                init_file = parent / "__init__.py"
                if init_file.exists():
                    names.add(parent.name.lower())
                if parent.parent == root.parent:
                    break
                parent = parent.parent
        elif path.name == "__init__.py":
            names.add(path.parent.name.lower())
    return names


def note_from_requirement(entry: RequirementEntry) -> str | None:
    raw = entry.raw.lower()
    name = entry.name.lower()
    if "tensorflow" in raw or "keras" in raw or "cudatoolkit" in raw or "cudnn" in raw:
        return f"TensorFlow/Keras pin: {entry.raw.strip()}"
    if "pywin32" in raw or name == "pywin32":
        return f"Windows COM pin: {entry.raw.strip()}"
    if "ultralytics" in raw or "opencv-python" in raw:
        return f"Vision stack pin: {entry.raw.strip()}"
    if "pyaudio" in raw or "speechrecognition" in raw or "gtts" in raw:
        return f"Audio stack clue: {entry.raw.strip()}"
    if "requests" in raw or "beautifulsoup" in raw or "bs4" in raw or "pytube" in raw:
        return f"Network stack clue: {entry.raw.strip()}"
    return None


def classify_hazards(
    all_imports: set[str],
    external_imports: set[str],
    local_imports: set[str],
    requirement_entries: list[RequirementEntry],
    file_texts: list[str],
    notebook_count: int,
) -> tuple[list[str], list[str]]:
    hazards: set[str] = set()
    notes: list[str] = []
    requirement_names = {entry.name.lower() for entry in requirement_entries}

    for import_root in sorted(all_imports):
        lower_root = import_root.lower()
        package = import_to_package(import_root)
        tag, description = IMPORT_HINTS.get(lower_root, (None, None))
        if tag:
            hazards.add(tag)
            notes.append(f"{import_root}: {description}")
        if package in {"requests", "beautifulsoup4", "pytube", "wikipedia", "speechrecognition", "gtts", "pydictionary"}:
            hazards.add("network")
        if package in {"pyttsx3", "speechrecognition", "pyaudio", "gtts", "moviepy"}:
            hazards.add("audio")
        if package in {"moviepy"}:
            hazards.add("codec")
        if package in {"opencv-python", "mediapipe"}:
            hazards.add("camera")
        if package in {"tensorflow", "keras", "torch", "ultralytics"}:
            hazards.add("model-download")
        if package in {"tensorflow", "keras"}:
            hazards.add("tensorflow-pin")
        if package in {"flask", "fastapi"}:
            hazards.add("service-deployment")
        if lower_root in {"smtplib", "imaplib"}:
            hazards.add("network")
            notes.append(f"{import_root}: mail/network delivery")
        if lower_root == "tkinter":
            hazards.add("display")
            notes.append("tkinter: desktop UI window")

    if any(name in {"flask", "fastapi"} for name in requirement_names):
        hazards.add("service-deployment")
        notes.append("service stack present in requirements")
    if any(name in {"tensorflow", "keras", "cudatoolkit", "cudnn"} for name in requirement_names):
        hazards.add("tensorflow-pin")
    if any(name in {"ultralytics", "torch", "opencv-python", "mediapipe"} for name in requirement_names):
        hazards.add("model-download")
    if any(name in {"pyaudio", "speechrecognition", "gtts", "pyttsx3", "moviepy"} for name in requirement_names):
        hazards.add("audio")
    if any(name in {"requests", "beautifulsoup4", "bs4", "pytube", "wikipedia", "gtts"} for name in requirement_names):
        hazards.add("network")
    if any(name in {"pywin32", "win32com"} for name in requirement_names):
        hazards.add("windows-com")

    joined_text = "\n".join(file_texts)
    for regex, tag, description in SOURCE_HINTS:
        if regex.search(joined_text):
            hazards.add(tag)
            notes.append(f"{tag}: {description}")
    if any(ext in joined_text for ext in (".pt", ".h5", ".keras", ".onnx", ".pb")):
        hazards.add("model-download")
        notes.append("model-download: model artifact extension detected")

    if any(name in {"password", "secret", "token", "credentials"} for name in local_imports):
        notes.append("credential helper module present")
        hazards.add("credentials")
    if notebook_count:
        hazards.add("notebook")
        notes.append(f"{notebook_count} notebook file(s) detected")

    ordered_hazards = [tag for tag in HAZARD_ORDER if tag in hazards]
    ordered_notes = list(dict.fromkeys(notes))
    return ordered_hazards, ordered_notes


TEXT_HINT_LIMIT = 200_000


def summarize_project(root: Path, base: Path | None = None) -> ProjectSummary:
    base = base or Path.cwd()
    files = [p for p in iter_project_files(root)]
    source_files = [p for p in files if p.suffix == ".py"]
    notebook_files = [p for p in files if p.suffix == ".ipynb"]
    requirement_files = [p for p in files if p.name in {"requirements.txt", "requirement.txt", "pyproject.toml"}]

    all_imports: set[str] = set()
    external_imports: set[str] = set()
    local_imports: set[str] = set()
    parse_errors: list[str] = []
    file_texts: list[str] = []

    local_names = collect_local_import_names(root, files)

    for path in source_files:
        try:
            text = read_text_guessing(path)
        except Exception as exc:
            parse_errors.append(f"{display_path(path, base)}: read failed ({exc})")
            continue
        file_texts.append(text[:TEXT_HINT_LIMIT])
        imports, errors = parse_source_imports(text, filename=path.name)
        parse_errors.extend(errors)
        for import_root in imports:
            lower_root = import_root.lower()
            all_imports.add(import_root)
            if lower_root in local_names or lower_root in SPECIAL_LOCAL_IMPORTS:
                local_imports.add(lower_root)
            elif lower_root == "google":
                # Colab notebook clue, not an external package for this checker.
                continue
            elif not is_stdlib_module(import_root):
                external_imports.add(import_root)

    for path in notebook_files:
        imports, errors = parse_notebook(path)
        parse_errors.extend(errors)
        try:
            file_texts.append(read_text_guessing(path)[:TEXT_HINT_LIMIT])
        except Exception:
            pass
        for import_root in imports:
            lower_root = import_root.lower()
            all_imports.add(import_root)
            if lower_root in local_names or lower_root in SPECIAL_LOCAL_IMPORTS:
                local_imports.add(lower_root)
            elif lower_root == "google":
                continue
            elif not is_stdlib_module(import_root):
                external_imports.add(import_root)

    requirement_entries: list[RequirementEntry] = []
    for path in requirement_files:
        requirement_entries.extend(parse_requirements_file(path))

    requirement_packages = []
    seen_requirements: set[str] = set()
    for entry in requirement_entries:
        normalized = entry.name.lower()
        if normalized in STD_LIB:
            continue
        if normalized not in seen_requirements:
            seen_requirements.add(normalized)
            requirement_packages.append(normalized)

    required_packages_from_imports = []
    for import_root in sorted(external_imports):
        package = import_to_package(import_root)
        if package not in required_packages_from_imports:
            required_packages_from_imports.append(package)

    requirement_set = {pkg.lower() for pkg in requirement_packages}
    missing_from_requirements = [pkg for pkg in required_packages_from_imports if pkg not in requirement_set]
    extra_requirements = [pkg for pkg in requirement_packages if pkg not in set(required_packages_from_imports)]

    hazards, notes = classify_hazards(
        all_imports=all_imports,
        external_imports=external_imports,
        local_imports=local_imports,
        requirement_entries=requirement_entries,
        file_texts=file_texts,
        notebook_count=len(notebook_files),
    )

    for entry in requirement_entries:
        note = note_from_requirement(entry)
        if note:
            notes.append(note)

    if missing_from_requirements:
        notes.append("missing requirement clue(s): " + ", ".join(missing_from_requirements))
    if extra_requirements:
        notes.append("declared but unmatched requirement clue(s): " + ", ".join(extra_requirements))

    notes = list(dict.fromkeys(notes))
    notes = sorted(notes, key=str.lower)

    return ProjectSummary(
        path=display_path(root, base),
        source_files=[display_path(p, base) for p in source_files],
        notebook_files=[display_path(p, base) for p in notebook_files],
        requirement_files=[display_path(p, base) for p in requirement_files],
        external_imports=sorted({pkg.lower() for pkg in required_packages_from_imports}),
        local_imports=sorted(local_imports),
        requirement_packages=sorted(requirement_packages),
        missing_from_requirements=sorted(missing_from_requirements),
        extra_requirements=sorted(extra_requirements),
        hazards=hazards,
        notes=notes,
        parse_errors=sorted(dict.fromkeys(parse_errors)),
    )


def discover_roots(base: Path) -> list[Path]:
    roots: list[Path] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir() or is_ignored(child):
            continue
        if any(True for _ in child.rglob("*.py")) or any(True for _ in child.rglob("*.ipynb")) or any(
            (child / name).exists() for name in ("requirements.txt", "requirement.txt", "pyproject.toml")
        ):
            roots.append(child)
    if roots:
        return roots
    return [base]


def summarize_as_text(summaries: list[ProjectSummary]) -> str:
    blocks: list[str] = []
    for summary in summaries:
        lines = [f"Project: {summary.path}"]
        if summary.source_files:
            lines.append("  source_files: " + ", ".join(summary.source_files))
        if summary.notebook_files:
            lines.append("  notebook_files: " + ", ".join(summary.notebook_files))
        if summary.requirement_files:
            lines.append("  requirement_files: " + ", ".join(summary.requirement_files))
        lines.append("  external_imports: " + (", ".join(summary.external_imports) if summary.external_imports else "none"))
        lines.append("  local_imports: " + (", ".join(summary.local_imports) if summary.local_imports else "none"))
        lines.append(
            "  requirement_packages: "
            + (", ".join(summary.requirement_packages) if summary.requirement_packages else "none")
        )
        lines.append(
            "  missing_from_requirements: "
            + (", ".join(summary.missing_from_requirements) if summary.missing_from_requirements else "none")
        )
        lines.append(
            "  extra_requirements: "
            + (", ".join(summary.extra_requirements) if summary.extra_requirements else "none")
        )
        lines.append("  hazards: " + (", ".join(summary.hazards) if summary.hazards else "none"))
        if summary.notes:
            lines.append("  notes:")
            for note in summary.notes:
                lines.append(f"    - {note}")
        if summary.parse_errors:
            lines.append("  parse_errors:")
            for error in summary.parse_errors:
                lines.append(f"    - {error}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize heavy project requirements, imports, and backend risks without executing code.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python check_heavy_project_requirements.py\n"
            "  python check_heavy_project_requirements.py 'Object_Detection' 'digit-recognizer'\n"
            "  python check_heavy_project_requirements.py --format json 'Web scraping for book names'\n"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Project directories or files to analyze. If omitted, the current directory is auto-discovered.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Default: text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    cwd = Path.cwd()

    if args.paths:
        roots: list[Path] = []
        for item in args.paths:
            path = Path(item)
            if path.is_file():
                roots.append(path.parent)
            else:
                roots.append(path)
    else:
        roots = discover_roots(cwd)

    summaries = [summarize_project(root.resolve(), base=cwd) for root in roots]

    if args.format == "json":
        payload = [summary.__dict__ for summary in summaries]
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(summarize_as_text(summaries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
