#!/usr/bin/env python3
"""Safely inspect MOABB/MNE download configuration without network access.

The check uses a temporary directory, restores the prior MNE_DATA setting, and
never calls a dataset downloader. It is runnable from any current directory.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check MOABB download-dir/provider configuration offline."
    )
    parser.add_argument(
        "--path",
        type=Path,
        help="Optional temporary check directory (created if missing).",
    )
    parser.add_argument(
        "--provider",
        choices=("auto", "nemar", "upstream"),
        default="auto",
        help="Provider value to validate; no download is attempted (default: auto).",
    )
    args = parser.parse_args()

    import mne
    from moabb import get_download_provider, set_download_dir, set_download_provider

    previous_dir = mne.get_config("MNE_DATA")
    previous_provider = get_download_provider()
    owned_temp = args.path is None
    path = args.path or Path(tempfile.mkdtemp(prefix="moabb-config-check-"))
    try:
        path.mkdir(parents=True, exist_ok=True)
        set_download_dir(str(path))
        set_download_provider(args.provider)
        observed = mne.get_config("MNE_DATA")
        if Path(observed).resolve() != path.resolve():
            raise RuntimeError(f"MNE_DATA resolved to {observed!r}, not {str(path)!r}")
        if get_download_provider() != args.provider:
            raise RuntimeError("download provider did not round-trip")
        print(f"MNE_DATA={observed}")
        print(f"provider={get_download_provider()}")
        print("network=not attempted")
        return 0
    finally:
        # Restore configuration; setting None is supported by MNE for cleanup.
        set_download_provider(previous_provider if previous_provider != "auto" else None)
        if previous_dir is None:
            mne.set_config("MNE_DATA", None, set_env=False)
        else:
            mne.set_config("MNE_DATA", previous_dir, set_env=False)
        if owned_temp:
            import shutil

            shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
