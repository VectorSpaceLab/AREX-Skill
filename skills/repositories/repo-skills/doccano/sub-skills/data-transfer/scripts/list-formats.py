#!/usr/bin/env python3
"""Print doccano import and export formats by project type.

Run this from a doccano checkout, or set REPO_ROOT to the checkout path if the
current working directory is elsewhere.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

repo_root = Path(os.environ.get("REPO_ROOT", Path.cwd())).resolve()
sys.path.insert(0, str(repo_root / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

import django  # noqa: E402

django.setup()

from data_export.pipeline.catalog import Options as ExportOptions  # noqa: E402
from data_import.pipeline.catalog import Options as ImportOptions  # noqa: E402
from projects.models import ProjectType  # noqa: E402


def print_options(label: str, options: list[dict]) -> None:
    print(label)
    for option in options:
        display_name = option.get("display_name", option.get("name", ""))
        format_name = option.get("name", "")
        print(f"  - {display_name} -> {format_name}")


for task in ProjectType:
    print(f"[{task.value}]")
    print_options("  import", ImportOptions.filter_by_task(task.value))
    if task == ProjectType.SEQUENCE_LABELING:
        print_options("  import (relation)", ImportOptions.filter_by_task(task.value, use_relation=True))
    print_options("  export", ExportOptions.filter_by_task(task.value))
    print()
