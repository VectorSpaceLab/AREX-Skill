#!/usr/bin/env python3
"""Create a tiny local text corpus for Semantra command construction or smoke tests.

This helper does not run Semantra, download models, or require network access.
It only writes a few UTF-8 text files that are safe to index with Semantra.

Examples:
  python create_tiny_corpus.py --output-dir /tmp/semantra-corpus
  python create_tiny_corpus.py --output-dir /tmp/semantra-corpus --overwrite
"""

from __future__ import annotations

import argparse
from pathlib import Path

DOCUMENTS = {
    "astronomy_notes.txt": """Stars form in molecular clouds. Gravity compresses gas until fusion begins.\nAstronomers compare spectra to learn temperature, velocity, and composition.\n""",
    "library_notes.txt": """A library catalog helps readers find books by subject, author, and title.\nSemantic search can connect a vague theme to a passage even when words differ.\n""",
    "policy_notes.txt": """The city council debated transit funding, housing permits, and public health.\nA later memo compared economic growth with environmental safeguards.\n""",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, help="Directory to create the text files in.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite files if they already exist. Without this flag, existing files are left unchanged and the command fails.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    existing = [name for name in DOCUMENTS if (output_dir / name).exists()]
    if existing and not args.overwrite:
        print("Refusing to overwrite existing files:")
        for name in existing:
            print(f"  {output_dir / name}")
        print("Re-run with --overwrite if these tiny fixture files may be replaced.")
        return 2

    for name, text in DOCUMENTS.items():
        path = output_dir / name
        path.write_text(text, encoding="utf-8")
        print(path)

    print("\nExample Semantra command after installing Semantra:")
    print(f"  semantra --no-server --model minilm --semantra-dir {output_dir / 'cache'} {output_dir}/*.txt")
    print("Note: running that command may download the selected embedding model if it is not cached.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
