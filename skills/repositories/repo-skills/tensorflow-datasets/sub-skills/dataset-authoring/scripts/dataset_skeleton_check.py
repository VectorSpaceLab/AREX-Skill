#!/usr/bin/env python3
"""Standalone TFDS dataset skeleton validator.

This script intentionally uses only the Python standard library. It does not
import tensorflow_datasets or any source-checkout code, so it can be used on a
candidate dataset folder before package installation is working.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
TODO_RE = re.compile(
    r"(?:\bTODO(?:\([^)]*\))?:?|TODO-[A-Za-z0-9_-]+|todo-data-url|"
    r"DATASET_HOMEPAGE|DATA_ARCHIVE_URL|TRAIN_ARCHIVE_URL|TEST_ARCHIVE_URL|"
    r"dataset-homepage|add_fake_data|BibTeX citation|"
    r"remove tags which do not apply|Markdown description)",
    re.IGNORECASE,
)
ABSOLUTE_PATH_RE = re.compile(
    r"(?P<quote>['\"])(?:/(?:[^/'\"\\s]+/){2,}|[A-Za-z]:[\\/])"
)
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".bib",
    ".txt",
    ".tsv",
    ".csv",
    ".json",
    ".toml",
    ".cfg",
    ".ini",
}
MAX_TEXT_BYTES = 1_000_000
CHECKSUM_FILENAMES = ("checksums.tsv", "checksum.tsv")


@dataclass
class Check:
    status: str
    name: str
    message: str
    path: str | None = None


class Reporter:
    def __init__(self, root: Path, *, strict: bool = False):
        self.root = root
        self.strict = strict
        self.checks: list[Check] = []

    def add(self, status: str, name: str, message: str, path: Path | None = None) -> None:
        self.checks.append(Check(status=status, name=name, message=message, path=self.rel(path)))

    def pass_(self, name: str, message: str, path: Path | None = None) -> None:
        self.add("PASS", name, message, path)

    def warn(self, name: str, message: str, path: Path | None = None, *, strict_error: bool = False) -> None:
        self.add("ERROR" if (self.strict and strict_error) else "WARN", name, message, path)

    def error(self, name: str, message: str, path: Path | None = None) -> None:
        self.add("ERROR", name, message, path)

    def info(self, name: str, message: str, path: Path | None = None) -> None:
        self.add("INFO", name, message, path)

    def rel(self, path: Path | None) -> str | None:
        if path is None:
            return None
        try:
            return str(path.resolve().relative_to(self.root.resolve()))
        except Exception:
            return str(path)

    @property
    def ok(self) -> bool:
        return not any(check.status == "ERROR" for check in self.checks)


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return ""
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def is_text_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in TEXT_SUFFIXES


def find_text_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if is_text_file(path):
            yield path


def has_regex(text: str, pattern: str, flags: int = 0) -> bool:
    return re.search(pattern, text, flags) is not None


def add_file_check(reporter: Reporter, path: Path, label: str) -> bool:
    if path.is_file():
        reporter.pass_(label, "file exists", path)
        return True
    reporter.error(label, "required file is missing", path)
    return False


def add_dir_check(reporter: Reporter, path: Path, label: str) -> bool:
    if path.is_dir():
        reporter.pass_(label, "directory exists", path)
        return True
    reporter.error(label, "required directory is missing", path)
    return False


def first_existing_file(root: Path, filenames: Iterable[str]) -> Path | None:
    for filename in filenames:
        path = root / filename
        if path.is_file():
            return path
    return None


def collect_todos(root: Path) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if TODO_RE.search(path.name):
            hits.append((path, 0, path.name))
            continue
        if not is_text_file(path):
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), start=1):
            if TODO_RE.search(line):
                hits.append((path, line_no, line.strip()[:160]))
    return hits


def format_todo_hit(reporter: Reporter, path: Path, line_no: int, line: str) -> str:
    location = reporter.rel(path)
    if line_no <= 0:
        return f"{location}: {line}"
    return f"{location}:{line_no}: {line}"


def report_todos(
    reporter: Reporter,
    root: Path,
    *,
    mode: str,
    allow_todos: bool,
    max_todos: int | None,
) -> None:
    hits = collect_todos(root)
    if max_todos is not None and len(hits) > max_todos:
        reporter.error(
            "todo-count",
            f"found {len(hits)} TODO/template markers, above --max-todos={max_todos}",
        )
    if not hits:
        reporter.pass_("todo-markers", "no unresolved template TODO markers found")
        return

    preview = "; ".join(
        format_todo_hit(reporter, path, line_no, line) for path, line_no, line in hits[:8]
    )
    if len(hits) > 8:
        preview += f"; ... {len(hits) - 8} more"
    message = f"found {len(hits)} TODO/template markers: {preview}"
    if mode == "implementation" and not allow_todos:
        reporter.error("todo-markers", message)
    else:
        reporter.warn("todo-markers", message)


def infer_dataset_name(root: Path, provided: str | None) -> str:
    if provided:
        return provided
    builders = sorted(root.glob("*_dataset_builder.py"))
    if len(builders) == 1:
        return builders[0].name[: -len("_dataset_builder.py")]
    return root.name


def find_builder_file(root: Path, name: str, reporter: Reporter) -> Path | None:
    expected = root / f"{name}_dataset_builder.py"
    if expected.is_file():
        return expected
    builders = sorted(root.glob("*_dataset_builder.py"))
    if len(builders) == 1:
        reporter.warn(
            "builder-name",
            f"expected {expected.name}, using discovered {builders[0].name}",
            builders[0],
            strict_error=True,
        )
        return builders[0]
    if not builders:
        reporter.error("builder-file", f"missing {expected.name}", expected)
    else:
        reporter.error(
            "builder-file",
            "multiple builder files found; pass --dataset-name to disambiguate",
        )
    return None


def find_test_file(root: Path, name: str, reporter: Reporter) -> Path | None:
    expected = root / f"{name}_dataset_builder_test.py"
    if expected.is_file():
        return expected
    tests = sorted(root.glob("*_dataset_builder_test.py"))
    if len(tests) == 1:
        reporter.warn(
            "test-name",
            f"expected {expected.name}, using discovered {tests[0].name}",
            tests[0],
            strict_error=True,
        )
        return tests[0]
    reporter.error("test-file", f"missing {expected.name}", expected)
    return None


def check_name(name: str, reporter: Reporter) -> None:
    if SNAKE_CASE_RE.match(name) and "__" not in name and not name.endswith("_"):
        reporter.pass_("dataset-name", f"{name!r} is snake_case")
    else:
        reporter.error(
            "dataset-name",
            f"{name!r} is not a valid lower snake_case dataset/collection name",
        )


def check_common_text_hazards(reporter: Reporter, path: Path, text: str) -> None:
    if ABSOLUTE_PATH_RE.search(text):
        reporter.warn(
            "absolute-path",
            "text appears to contain a local absolute path; avoid machine-specific paths",
            path,
            strict_error=True,
        )
    if has_regex(text, r"\bos\.(listdir|walk|makedirs|mkdir|remove|rename)\b"):
        reporter.warn(
            "portable-filesystem",
            "uses os filesystem functions; TFDS tests prefer path-like or portable file APIs",
            path,
        )
    if has_regex(text, r"\bos\.path\.(exists|isdir|isfile)\b"):
        reporter.warn(
            "portable-filesystem",
            "uses os.path filesystem checks; prefer path-like methods",
            path,
        )
    if has_regex(text, r"(?<!\.)\bopen\("):
        reporter.warn(
            "portable-filesystem",
            "uses builtin open(); prefer path.open() or a portable file wrapper",
            path,
        )


def validate_dataset(root: Path, args: argparse.Namespace, reporter: Reporter) -> str:
    name = infer_dataset_name(root, args.dataset_name)
    check_name(name, reporter)

    add_file_check(reporter, root / "__init__.py", "init-file")
    add_file_check(reporter, root / "README.md", "readme")
    add_file_check(reporter, root / "CITATIONS.bib", "citations")
    add_file_check(reporter, root / "TAGS.txt", "tags")
    add_dir_check(reporter, root / "dummy_data", "dummy-data-dir")

    checksum_path = first_existing_file(root, CHECKSUM_FILENAMES)
    checksum_expected_path = root / CHECKSUM_FILENAMES[0]
    if checksum_path is not None:
        reporter.pass_("checksum-file", f"{checksum_path.name} exists", checksum_path)
        if checksum_path.name == "checksum.tsv":
            reporter.info(
                "checksum-file-name",
                "checksum.tsv is accepted for compatibility, but TFDS canonical filename is checksums.tsv",
                checksum_path,
            )
    else:
        reporter.warn(
            "checksum-file",
            "missing checksums.tsv; downloadable datasets should keep a checksum file beside the builder",
            checksum_expected_path,
            strict_error=True,
        )

    builder_path = find_builder_file(root, name, reporter)
    test_path = find_test_file(root, name, reporter)

    dummy_dir = root / "dummy_data"
    if dummy_dir.is_dir():
        files = [p for p in dummy_dir.rglob("*") if p.is_file()]
        if not files:
            reporter.error("dummy-data-content", "dummy_data is empty", dummy_dir)
        elif args.mode == "implementation" and all(TODO_RE.search(p.name) for p in files):
            reporter.error(
                "dummy-data-content",
                "dummy_data only contains TODO placeholder files",
                dummy_dir,
            )
        else:
            reporter.pass_("dummy-data-content", f"dummy_data contains {len(files)} file(s)", dummy_dir)

    if builder_path and builder_path.is_file():
        text = read_text(builder_path)
        check_common_text_hazards(reporter, builder_path, text)
        if has_regex(text, r"class\s+\w+\s*\([^\)]*GeneratorBasedBuilder"):
            reporter.pass_("builder-class", "builder subclasses GeneratorBasedBuilder", builder_path)
        else:
            reporter.error("builder-class", "missing GeneratorBasedBuilder subclass", builder_path)
        for method in ["_info", "_split_generators", "_generate_examples"]:
            if has_regex(text, rf"def\s+{method}\s*\("):
                reporter.pass_(method, f"defines {method}", builder_path)
            else:
                reporter.error(method, f"missing {method}", builder_path)
        if "tfds.core.Version" in text or re.search(r"\bVersion\(", text):
            reporter.pass_("version", "declares a Version", builder_path)
        else:
            reporter.error("version", "missing VERSION declaration", builder_path)
        if "RELEASE_NOTES" in text:
            reporter.pass_("release-notes", "declares RELEASE_NOTES", builder_path)
        else:
            reporter.warn("release-notes", "missing RELEASE_NOTES", builder_path, strict_error=True)
        if "dataset_info_from_configs" in text or "DatasetInfo" in text:
            reporter.pass_("dataset-info", "returns DatasetInfo metadata", builder_path)
        else:
            reporter.error("dataset-info", "_info should return DatasetInfo metadata", builder_path)
        if "FeaturesDict" in text:
            reporter.pass_("features", "declares FeaturesDict", builder_path)
        else:
            reporter.warn("features", "no FeaturesDict found", builder_path, strict_error=True)
        if "dl_manager" in text:
            reporter.pass_("download-manager", "_split_generators mentions dl_manager", builder_path)
        else:
            reporter.warn("download-manager", "_split_generators should accept/use dl_manager or delete it explicitly", builder_path)
        if re.search(r"return\s*{", text):
            reporter.pass_("split-return", "uses dict return style for splits", builder_path)
        elif "SplitGenerator" in text:
            reporter.warn(
                "split-return",
                "uses legacy SplitGenerator; new builders should return a {split: generator} dict",
                builder_path,
            )
        else:
            reporter.warn("split-return", "could not identify split return style", builder_path)
        if re.search(r"\byield\b", text):
            reporter.pass_("example-yield", "_generate_examples appears to yield examples", builder_path)
        else:
            reporter.error("example-yield", "_generate_examples should yield (key, example) pairs", builder_path)
        if re.search(r"yield\s+['\"]key['\"]", text):
            reporter.warn("stable-key", "template constant key is still present", builder_path, strict_error=True)
        if re.search(r"ClassLabel\s*\([^)]*num_classes\s*=", text) and not re.search(r"ClassLabel\s*\([^)]*(names|names_file)\s*=", text, re.DOTALL):
            reporter.warn("class-label-names", "ClassLabel uses num_classes without label names", builder_path)
        if re.search(r"Image\s*\(\s*\)", text):
            reporter.warn("image-shape", "Image connector has no explicit shape", builder_path)
        if "manual_dir" in text and "MANUAL_DOWNLOAD_INSTRUCTIONS" not in text:
            reporter.error("manual-download", "manual_dir used without MANUAL_DOWNLOAD_INSTRUCTIONS", builder_path)
        if re.search(r"dl_manager\.(download|download_and_extract)\s*\(", text) and checksum_path is None:
            reporter.warn(
                "download-checksums",
                "builder downloads data but checksums.tsv is missing",
                builder_path,
                strict_error=True,
            )
        if "BUILDER_CONFIGS" in text:
            reporter.info("builder-configs", "builder declares BUILDER_CONFIGS; ensure config versions and test coverage are intentional", builder_path)

    if test_path and test_path.is_file():
        text = read_text(test_path)
        check_common_text_hazards(reporter, test_path, text)
        if "DatasetBuilderTestCase" in text:
            reporter.pass_("test-base", "test uses DatasetBuilderTestCase", test_path)
        else:
            reporter.error("test-base", "test should inherit DatasetBuilderTestCase", test_path)
        if "DATASET_CLASS" in text:
            reporter.pass_("dataset-class", "test sets DATASET_CLASS", test_path)
        else:
            reporter.error("dataset-class", "test missing DATASET_CLASS", test_path)
        if "SPLITS" in text:
            reporter.pass_("splits", "test declares SPLITS", test_path)
        else:
            reporter.error("splits", "test missing SPLITS", test_path)
        if "test_main" in text:
            reporter.pass_("test-main", "test has a test_main entry point", test_path)
        else:
            reporter.warn("test-main", "test lacks a test_main entry point", test_path)
        if "SKIP_CHECKSUMS = True" in text:
            reporter.warn("skip-checksums", "test skips checksum validation; require a documented reason", test_path)

    report_todos(
        reporter,
        root,
        mode=args.mode,
        allow_todos=args.allow_todos,
        max_todos=args.max_todos,
    )
    return name


def find_collection_file(root: Path, name: str, reporter: Reporter) -> Path | None:
    expected = root / f"{name}.py"
    if expected.is_file():
        return expected
    candidates = [
        p
        for p in sorted(root.glob("*.py"))
        if p.name != "__init__.py" and not p.name.endswith("_test.py")
    ]
    if len(candidates) == 1:
        reporter.warn(
            "collection-file-name",
            f"expected {expected.name}, using discovered {candidates[0].name}",
            candidates[0],
            strict_error=True,
        )
        return candidates[0]
    if not candidates:
        reporter.error("collection-file", f"missing {expected.name}", expected)
    else:
        reporter.error("collection-file", "multiple collection .py files found; pass --dataset-name")
    return None


def validate_collection(root: Path, args: argparse.Namespace, reporter: Reporter) -> str:
    name = args.dataset_name or root.name
    check_name(name, reporter)
    add_file_check(reporter, root / "__init__.py", "init-file")
    collection_path = find_collection_file(root, name, reporter)

    description_path = root / "description.md"
    citations_path = root / "citations.bib"
    test_path = root / f"{name}_test.py"

    if description_path.is_file():
        reporter.pass_("collection-description-file", "description.md exists", description_path)
    else:
        reporter.info("collection-description-file", "description.md absent; inline description must be present")
    if citations_path.is_file():
        reporter.pass_("collection-citations-file", "citations.bib exists", citations_path)
    else:
        reporter.info("collection-citations-file", "citations.bib absent; citation may be inline or intentionally omitted")
    if test_path.is_file():
        reporter.pass_("collection-test-file", "collection test exists", test_path)
    else:
        reporter.warn("collection-test-file", "collection test is missing", test_path, strict_error=True)

    if collection_path and collection_path.is_file():
        text = read_text(collection_path)
        check_common_text_hazards(reporter, collection_path, text)
        if "DatasetCollection" in text:
            reporter.pass_("collection-class", "uses DatasetCollection", collection_path)
        else:
            reporter.error("collection-class", "missing DatasetCollection subclass", collection_path)
        if re.search(r"def\s+info\s*\(", text):
            reporter.pass_("collection-info", "defines info property", collection_path)
        else:
            reporter.error("collection-info", "missing info property", collection_path)
        if "DatasetCollectionInfo" in text:
            reporter.pass_("collection-info-type", "uses DatasetCollectionInfo", collection_path)
        else:
            reporter.error("collection-info-type", "info should return DatasetCollectionInfo", collection_path)
        if "release_notes" in text:
            reporter.pass_("collection-release-notes", "declares release notes", collection_path)
        else:
            reporter.error("collection-release-notes", "missing release_notes", collection_path)
        if "description" in text or description_path.is_file():
            reporter.pass_("collection-description", "description is inline or in side file", collection_path)
        else:
            reporter.error("collection-description", "missing collection description", collection_path)
        if re.search(r"def\s+datasets\s*\(", text):
            reporter.pass_("collection-datasets", "defines datasets property", collection_path)
        else:
            reporter.error("collection-datasets", "missing datasets property", collection_path)
        if "references_for" in text or "DatasetReference" in text:
            reporter.pass_("collection-references", "uses dataset references", collection_path)
        else:
            reporter.error("collection-references", "datasets should map to DatasetReference objects", collection_path)
        if re.search(r"['\"]\d+\.\d+\.\d+['\"]\s*:", text):
            reporter.pass_("collection-version-keys", "appears to use semantic version keys", collection_path)
        else:
            reporter.warn("collection-version-keys", "no semantic collection version keys detected", collection_path, strict_error=True)

    if test_path.is_file():
        text = read_text(test_path)
        check_common_text_hazards(reporter, test_path, text)
        if "DatasetCollectionTestBase" in text:
            reporter.pass_("collection-test-base", "test uses DatasetCollectionTestBase", test_path)
        else:
            reporter.error("collection-test-base", "test should inherit DatasetCollectionTestBase", test_path)
        if "DATASET_COLLECTION_CLASS" in text:
            reporter.pass_("collection-test-class", "test sets DATASET_COLLECTION_CLASS", test_path)
        else:
            reporter.error("collection-test-class", "test missing DATASET_COLLECTION_CLASS", test_path)

    report_todos(
        reporter,
        root,
        mode=args.mode,
        allow_todos=args.allow_todos,
        max_todos=args.max_todos,
    )
    return name


def infer_kind(root: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if list(root.glob("*_dataset_builder.py")):
        return "dataset"
    for path in root.glob("*.py"):
        if path.name == "__init__.py" or path.name.endswith("_test.py"):
            continue
        text = read_text(path)
        if "DatasetCollection" in text or "DatasetCollectionInfo" in text:
            return "collection"
    return "dataset"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a TFDS custom dataset or dataset collection folder shape "
            "and unresolved template TODO markers without importing TFDS."
        )
    )
    parser.add_argument("path", type=Path, help="Dataset or collection folder to validate.")
    parser.add_argument(
        "--kind",
        choices=["auto", "dataset", "collection"],
        default="auto",
        help="What to validate. Default: infer from files.",
    )
    parser.add_argument(
        "--mode",
        choices=["scaffold", "implementation"],
        default="implementation",
        help="In implementation mode unresolved TODO/template markers fail unless --allow-todos is set.",
    )
    parser.add_argument(
        "--dataset-name",
        help="Expected lower snake_case dataset or collection name. Defaults to folder/builder name.",
    )
    parser.add_argument(
        "--allow-todos",
        action="store_true",
        help="Report TODO/template markers as warnings instead of errors in implementation mode.",
    )
    parser.add_argument(
        "--max-todos",
        type=int,
        help="Fail if more than this many TODO/template markers are found.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Upgrade selected skeleton warnings, such as missing checksum/test side files, to errors.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def print_text(result: dict) -> None:
    status = "OK" if result["ok"] else "FAILED"
    print(f"TFDS skeleton check: {status}")
    print(f"kind: {result['kind']}")
    print(f"name: {result['name']}")
    print(f"path: {result['path']}")
    counts = result["counts"]
    print(
        "checks: "
        f"{counts.get('PASS', 0)} pass, "
        f"{counts.get('WARN', 0)} warn, "
        f"{counts.get('ERROR', 0)} error, "
        f"{counts.get('INFO', 0)} info"
    )
    for check in result["checks"]:
        path = f" ({check['path']})" if check.get("path") else ""
        print(f"[{check['status']}] {check['name']}: {check['message']}{path}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.path.expanduser()
    reporter = Reporter(root, strict=args.strict)

    if not root.exists():
        reporter.error("path", "folder does not exist", root)
        kind = args.kind if args.kind != "auto" else "dataset"
        name = args.dataset_name or root.name
    elif not root.is_dir():
        reporter.error("path", "path is not a directory", root)
        kind = args.kind if args.kind != "auto" else "dataset"
        name = args.dataset_name or root.name
    else:
        reporter.pass_("path", "folder exists", root)
        kind = infer_kind(root, args.kind)
        if kind == "collection":
            name = validate_collection(root, args, reporter)
        else:
            name = validate_dataset(root, args, reporter)

    counts: dict[str, int] = {}
    for check in reporter.checks:
        counts[check.status] = counts.get(check.status, 0) + 1
    result = {
        "ok": reporter.ok,
        "kind": kind,
        "name": name,
        "path": str(root),
        "counts": counts,
        "checks": [asdict(check) for check in reporter.checks],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0 if reporter.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
