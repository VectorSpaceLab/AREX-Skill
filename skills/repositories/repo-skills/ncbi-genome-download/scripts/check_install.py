#!/usr/bin/env python3
"""Check an installed ncbi-genome-download package without network access.

Usage: python check_install.py
The check imports the public API and builds parser help/version facts; it does
not contact NCBI or create an output directory.
"""

from __future__ import annotations

import inspect
import shutil
import sys


def main() -> int:
    try:
        import ncbi_genome_download as ngd
        from ncbi_genome_download import NgdConfig
    except ImportError as exc:
        print(f"ncbi-genome-download import failed: {exc}", file=sys.stderr)
        print("Install with: python -m pip install ncbi-genome-download", file=sys.stderr)
        return 1

    print(f"version: {ngd.__version__}")
    print(f"module: {ngd.__name__}")
    print(f"download signature: {inspect.signature(ngd.download)}")
    print(f"CLI: {shutil.which('ncbi-genome-download') or 'not on PATH'}")
    print(f"alternate CLI: {shutil.which('ngd') or 'not on PATH'}")
    print(f"groups: {','.join(NgdConfig.get_choices('groups'))}")
    print(f"formats: {','.join(NgdConfig.get_choices('file_formats'))}")
    print(f"assembly levels: {','.join(NgdConfig.get_choices('assembly_levels'))}")
    print("dry-run API smoke:")
    print("  use download(groups='bacteria', dry_run=True) after choosing a URI/cache policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
