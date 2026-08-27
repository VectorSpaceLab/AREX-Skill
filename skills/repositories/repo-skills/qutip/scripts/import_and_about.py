#!/usr/bin/env python3
"""QuTiP import and environment summary helper.

Run after installing QuTiP:

    python import_and_about.py

It prints the imported package version and QuTiP's built-in `about()` report.
"""

from __future__ import annotations

import qutip


def main() -> int:
    print(f"qutip_version={qutip.__version__}")
    qutip.about()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
