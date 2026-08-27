#!/usr/bin/env python3
"""Check PySide6/Meshroom UI imports and QML directories without starting the GUI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Import-check Meshroom's PySide6/QML bridge without starting QApplication.")
    parser.add_argument("--repo-root", help="Optional source checkout root to inspect bundled QML paths.")
    parser.add_argument("--qml-dir", help="Optional explicit QML directory to verify.")
    args = parser.parse_args()

    if args.repo_root:
        root = Path(args.repo_root).resolve()
        sys.path.insert(0, str(root))
        qmlDir = root / "meshroom" / "ui" / "qml"
    elif args.qml_dir:
        qmlDir = Path(args.qml_dir).resolve()
    else:
        qmlDir = None

    import PySide6
    import meshroom.ui.app
    import meshroom.ui.graph
    import meshroom.ui.scene
    from PySide6 import QtCore

    print(f"PySide6: {PySide6.__version__}")
    print(f"Qt: {QtCore.qVersion()}")
    print("UI imports: ok")
    if qmlDir is not None:
        if not qmlDir.is_dir():
            print(f"QML directory missing: {qmlDir}", file=sys.stderr)
            return 1
        count = sum(1 for path in qmlDir.rglob("*") if path.suffix in {".qml", ".js"})
        print(f"QML files: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
