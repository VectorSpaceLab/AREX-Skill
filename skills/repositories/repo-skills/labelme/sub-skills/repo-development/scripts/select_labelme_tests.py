#!/usr/bin/env python3
"""Suggest focused labelme tests for changed paths.

The suggestions mirror evidence from the repository's tests and CI. They are
safe planning output only; run the suggested commands from a prepared checkout.
"""

from __future__ import annotations

import argparse
from pathlib import PurePosixPath

RULES = [
    (("labelme/__main__.py",), ["pytest tests/unit/__main___test.py -q", "labelme --help", "labelme --version"]),
    (("labelme/_config", "labelme/_yaml.py", "labelme/_widgets/settings_dialog.py"), ["pytest tests/unit/_config tests/unit/widgets/settings_dialog_test.py -q", "pytest tests/e2e/config_test.py -q"]),
    (("labelme/_label_file.py", "labelme/_utils/image.py"), ["pytest tests/unit/_label_file_test.py tests/unit/read_image_file_test.py -q"]),
    (("labelme/_shape.py", "labelme/_utils/shape.py", "labelme/_widgets/canvas.py"), ["pytest tests/unit/_shape_test.py tests/unit/utils/shape_test.py tests/unit/widgets/canvas_test.py -q"]),
    (("labelme/_automation", "labelme/_ai_models.py", "labelme/_widgets/_ai"), ["pytest tests/unit/_automation -q", "pytest tests/e2e/ai_text_to_annotation_test.py -q  # display/Xvfb required"]),
    (("examples/",), ["python examples/tutorial/export_json.py examples/tutorial/apc2016_obj3.json", "python examples/semantic_segmentation/labelme2voc.py examples/semantic_segmentation/data_annotated labelme-voc-output --labels examples/semantic_segmentation/labels.txt  # use a new disposable output dir"]),
    (("tools/release_notes.py",), ["pytest tests/unit/tools/release_notes_test.py -q"]),
    (("tools/update_translate.py", "labelme/translate"), ["make check_translate"]),
]
DEFAULTS = ["pytest tests/unit -q", "make lint", "make test  # full suite; GUI/display dependencies may be required"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="changed repo-relative paths")
    args = parser.parse_args()
    suggestions: list[str] = []
    for raw in args.paths:
        path = PurePosixPath(raw.replace("\\", "/"))
        text = path.as_posix()
        for prefixes, commands in RULES:
            if any(text == prefix.rstrip("/") or text.startswith(prefix) for prefix in prefixes):
                for command in commands:
                    if command not in suggestions:
                        suggestions.append(command)
    if not suggestions:
        suggestions = DEFAULTS[:]
    print("Suggested labelme verification commands:")
    for command in suggestions:
        print(f"- {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
