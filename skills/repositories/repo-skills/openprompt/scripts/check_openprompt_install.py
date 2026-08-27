#!/usr/bin/env python3
"""Root OpenPrompt install/API smoke.

This wrapper delegates to the pipeline-basics smoke so future agents can run a
single root-level helper from the generated skill tree without depending on the
original repository checkout.
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "sub-skills"
        / "pipeline-basics"
        / "scripts"
        / "check_openprompt_install.py"
    )
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
