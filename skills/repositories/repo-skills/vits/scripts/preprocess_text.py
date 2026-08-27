#!/usr/bin/env python3
"""Clean VITS filelists with the repo's text cleaners.

Prereqs:
- Run from any working directory with `--repo-root` pointing at a VITS checkout.
- `phonemizer` is required for `english_cleaners` and `english_cleaners2`.
- `espeak` or `espeak-ng` is required when the selected cleaner uses the espeak backend.

Example:
  python scripts/preprocess_text.py --repo-root /path/to/vits --filelists filelists/ljs_audio_text_val_filelist.txt filelists/ljs_audio_text_test_filelist.txt
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean VITS filelists.")
    parser.add_argument("--repo-root", required=True, help="Path to the VITS checkout.")
    parser.add_argument("--out-extension", default="cleaned", help="Suffix appended to the output filelist name.")
    parser.add_argument("--text-index", default=1, type=int, help="Column index containing the text field.")
    parser.add_argument(
        "--filelists",
        nargs="+",
        required=True,
        help="One or more pipe-delimited filelists to clean.",
    )
    parser.add_argument(
        "--text-cleaners",
        nargs="+",
        default=["english_cleaners2"],
        help="Cleaner chain to apply to the text column.",
    )
    return parser.parse_args()


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, str(repo_root))

    import text
    from utils import load_filepaths_and_text

    espeak = shutil.which("espeak") or shutil.which("espeak-ng")
    if "english_cleaners2" in args.text_cleaners and espeak is None:
        print("warning: english_cleaners2 selected but no espeak binary is installed", file=sys.stderr)

    for filelist_arg in args.filelists:
        filelist = resolve_path(repo_root, filelist_arg)
        if not filelist.exists():
            raise FileNotFoundError(f"filelist not found: {filelist}")
        print(f"START: {filelist}")
        filepaths_and_text = load_filepaths_and_text(str(filelist))
        for i, row in enumerate(filepaths_and_text):
            if args.text_index >= len(row):
                raise IndexError(
                    f"text_index={args.text_index} is out of range for row {i} in {filelist}"
                )
            original_text = row[args.text_index]
            cleaned_text = text._clean_text(original_text, args.text_cleaners)
            row[args.text_index] = cleaned_text

        output = filelist.with_name(filelist.name + f".{args.out_extension}")
        with output.open("w", encoding="utf-8") as handle:
            handle.writelines(["|".join(x) + "\n" for x in filepaths_and_text])
        print(f"WROTE: {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
