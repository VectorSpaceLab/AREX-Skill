#!/usr/bin/env python3
"""Read-only validation for the legacy Caffe demo assets.

This helper deliberately uses only the Python standard library. It checks
filenames, descriptor text, label structure, and generated-file presence; it
does not import TensorRT/CUDA, open model weights, execute binaries, download
anything, or write files.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


LABEL_RE = re.compile(r"^n\d{8}\s+\S")
DIM_RE = re.compile(r"dim:\s*1\s+dim:\s*3\s+dim:\s*224\s+dim:\s*224")
MTCNN_INPUT_RE = re.compile(r"dim:\s*1\s+dim:\s*3\s+dim:\s*710\s+dim:\s*384")


class Report:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.ok: List[str] = []

    def check_file(self, path: Path, kind: str) -> bool:
        if not path.is_file():
            self.errors.append(f"missing {kind}: {path}")
            return False
        try:
            size = path.stat().st_size
        except OSError as exc:
            self.errors.append(f"cannot stat {kind} {path}: {exc}")
            return False
        if size == 0:
            self.errors.append(f"empty {kind}: {path}")
            return False
        self.ok.append(f"{kind}: {path} ({size} bytes)")
        return True

    def warn_file(self, path: Path, kind: str) -> bool:
        if not path.is_file():
            self.warnings.append(f"missing generated {kind}: {path}")
            return False
        try:
            size = path.stat().st_size
        except OSError as exc:
            self.warnings.append(f"cannot stat generated {kind} {path}: {exc}")
            return False
        if size == 0:
            self.warnings.append(f"empty generated {kind}: {path}")
            return False
        self.ok.append(f"generated {kind}: {path} ({size} bytes)")
        return True


def check_descriptor(report: Report, path: Path, required: Tuple[str, ...]) -> None:
    if not report.check_file(path, "Caffe descriptor"):
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        report.errors.append(f"cannot read Caffe descriptor {path}: {exc}")
        return
    missing = [marker for marker in required if marker not in text]
    if path.name == "deploy.prototxt" and not DIM_RE.search(text):
        missing.append("input dims 1x3x224x224")
    if path.name == "det1_relu.prototxt" and not MTCNN_INPUT_RE.search(text):
        missing.append("PNet input dims 1x3x710x384")
    if missing:
        report.errors.append(
            f"descriptor {path} lacks expected markers: {', '.join(missing)}"
        )
    else:
        report.ok.append(f"descriptor markers: {path}")


def check_labels(report: Report, path: Path) -> None:
    if not report.check_file(path, "ImageNet labels"):
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        report.errors.append(f"cannot read ImageNet labels {path}: {exc}")
        return
    if len(lines) != 1000:
        report.errors.append(f"ImageNet labels {path} has {len(lines)} rows; expected 1000")
        return
    malformed = [index + 1 for index, line in enumerate(lines) if not LABEL_RE.match(line)]
    if malformed:
        report.errors.append(
            f"ImageNet labels {path} has malformed synset rows: {malformed[:5]}"
        )
    if not malformed:
        report.ok.append(f"ImageNet labels: {path} (1000 synset/label rows)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only validation of GoogLeNet/MTCNN legacy model assets."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="repository root to inspect (default: current directory)",
    )
    parser.add_argument(
        "--require-runtime",
        action="store_true",
        help="treat missing engines and the pytrt extension as errors",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repo_root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: repository root is not a directory: {root}", file=sys.stderr)
        return 2

    report = Report()
    print(f"legacy-model-assets: inspecting {root}")
    print("mode: source + generated-runtime presence (read-only)")

    check_descriptor(
        report,
        root / "googlenet" / "deploy.prototxt",
        ("name: \"GoogleNet\"", 'top: "data"', 'top: "prob"'),
    )
    report.check_file(root / "googlenet" / "deploy.caffemodel", "GoogLeNet Caffe weights")
    check_labels(report, root / "googlenet" / "synset_words.txt")

    mtcnn_specs = {
        "det1_relu": ("PNet", 'top: "prob1"', 'top: "conv4-2"', "dim:1 dim:3 dim:710 dim:384"),
        "det2_relu": ("RNet", 'top: "prob1"', 'top: "conv5-2"', "dim:1 dim:3 dim:24 dim:24"),
        "det3_relu": ("ONet", 'top: "prob1"', 'top: "conv6-2"', 'top: "conv6-3"'),
    }
    for stem, markers in mtcnn_specs.items():
        check_descriptor(report, root / "mtcnn" / f"{stem}.prototxt", markers)
        report.check_file(root / "mtcnn" / f"{stem}.caffemodel", f"MTCNN {stem} weights")

    print("\nsource checks:")
    for item in report.ok:
        if not item.startswith("generated "):
            print(f"  OK   {item}")

    print("\ngenerated runtime checks:")
    runtime_ok = True
    for relative in (
        Path("googlenet/deploy.engine"),
        Path("mtcnn/det1.engine"),
        Path("mtcnn/det2.engine"),
        Path("mtcnn/det3.engine"),
    ):
        runtime_ok = report.warn_file(root / relative, "TensorRT engine") and runtime_ok

    extensions = sorted(root.glob("pytrt*.so"))
    if extensions and all(path.is_file() and path.stat().st_size > 0 for path in extensions):
        for path in extensions:
            report.ok.append(f"generated pytrt extension: {path} ({path.stat().st_size} bytes)")
        print("  OK   generated pytrt extension: " + ", ".join(str(p) for p in extensions))
    else:
        runtime_ok = False
        report.warnings.append(f"missing generated pytrt extension: {root / 'pytrt*.so'}")

    for item in report.ok:
        if item.startswith("generated ") and "pytrt extension" not in item:
            print(f"  OK   {item}")
    for warning in report.warnings:
        print(f"  WARN {warning}")

    if report.errors:
        print("\nerrors:")
        for error in report.errors:
            print(f"  ERROR {error}")
    else:
        print("\nsource result: PASS")

    if args.require_runtime and not runtime_ok:
        report.errors.append("required generated runtime assets are incomplete")
        print("runtime result: FAIL (required by --require-runtime)")
    elif runtime_ok:
        print("runtime result: PASS (presence only; compatibility is not proven)")
    else:
        print("runtime result: WARN (engines/pytrt absent; source checks still passed)")

    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
