#!/usr/bin/env python3
"""Print the auto-labeling templates exposed by auto_labeling_pipeline.

The script keeps the inspection read-only and does not call any remote service.
"""

from __future__ import annotations

from auto_labeling_pipeline.menu import Options

TASK_NAMES = [
    "DocumentClassification",
    "SequenceLabeling",
    "Seq2seq",
    "IntentDetectionAndSlotFilling",
    "Speech2text",
    "ImageClassification",
    "BoundingBox",
    "Segmentation",
    "ImageCaptioning",
]

for task_name in TASK_NAMES:
    try:
        templates = Options.filter_by_task(task_name)
    except Exception:
        continue
    if not templates:
        continue
    print(f"[{task_name}]")
    for template in templates:
        print(f"  - {template.name}")
    print()
