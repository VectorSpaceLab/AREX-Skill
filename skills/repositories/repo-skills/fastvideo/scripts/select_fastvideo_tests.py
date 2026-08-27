#!/usr/bin/env python3
"""Print FastVideo test candidates by task area.

The script does not run tests. It helps a later agent choose bounded checks and
separate safe commands from GPU/model/budget-gated commands.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

TESTS: dict[str, dict[str, list[str]]] = {
    "inference-serving": {
        "safe": [
            "python skills/disco/fastvideo/scripts/verify_fastvideo_runtime.py",
            "fastvideo --help",
            "fastvideo generate --help",
            "fastvideo serve --help",
            "fastvideo router-serve --help",
            "pytest fastvideo/tests/api/test_cli_translation.py -q",
            "pytest fastvideo/tests/attention/test_selector_role_override.py -q",
            "pytest fastvideo/tests/entrypoints/test_video_generator.py -q",
            "pytest fastvideo/tests/entrypoints/test_openai_api.py -q",
            "pytest fastvideo/tests/entrypoints/streaming/test_server.py -q",
        ],
        "gated": [
            "pytest fastvideo/tests/inference/ -q",
            "pytest fastvideo/tests/ssim/ -vs",
            "fastvideo generate --config <config.yaml>",
            "fastvideo serve --config <serve.yaml>",
        ],
    },
    "model-porting": {
        "safe": [
            "python skills/disco/fastvideo/scripts/verify_fastvideo_runtime.py",
            "pytest fastvideo/tests/api/test_cli_translation.py -q",
            "pytest fastvideo/tests/contract/test_ci_test_collection.py -q",
            "pytest fastvideo/tests/golden_gate/ -q",
            "pytest fastvideo/tests/train/models/ -q",
            "python scripts/checkpoint_conversion/wan_to_diffusers.py --help",
            "python scripts/checkpoint_conversion/convert_ltx2_weights.py --help",
        ],
        "gated": [
            "read tests/local_tests/<family>/README.md, then run only the matching command",
            "pytest fastvideo/tests/ssim/ -vs",
            "fastvideo generate --config <model-smoke-config.yaml>",
        ],
    },
    "training": {
        "safe": [
            "python skills/disco/fastvideo/scripts/verify_fastvideo_runtime.py --cuda",
            "pytest fastvideo/tests/train/methods/test_wan_finetune.py -q",
            "pytest fastvideo/tests/train/ -q",
            "pytest fastvideo/tests/dataset/ -q",
        ],
        "gated": [
            "pytest fastvideo/tests/training/ -q",
            "pytest fastvideo/tests/distributed/ -q",
            "bash examples/train/run.sh",
            "bash examples/train/run_slurm.sh",
        ],
    },
    "dreamverse": {
        "safe": [
            "python skills/disco/fastvideo/scripts/verify_fastvideo_runtime.py --dreamverse",
            "dreamverse-server --help",
            "dreamverse-mock-server --help",
            "pytest apps/dreamverse/dreamverse/tests/test_entrypoints.py -q",
            "pytest apps/dreamverse/dreamverse/tests/test_mock_server.py -q",
            "pytest apps/dreamverse/dreamverse/tests/test_gpu_pool.py -q",
            "pytest fastvideo/tests/contract/test_dreamverse_shape.py -q",
        ],
        "gated": [
            "deployment commands from apps/dreamverse/docker/README.md",
            "deployment commands from apps/dreamverse/scripts/modal/README.md",
            "launch scripts from apps/dreamverse/scripts/launch/README.md",
        ],
    },
}


def collect(area: str) -> dict[str, Any]:
    if area == "all":
        return TESTS
    return {area: TESTS[area]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Print FastVideo test candidates for a task area.")
    parser.add_argument(
        "area",
        choices=[*TESTS.keys(), "all"],
        help="Task area to select tests for.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    data = collect(args.area)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    for area, groups in data.items():
        print(f"## {area}")
        for group_name, commands in groups.items():
            print(f"\n{group_name}:")
            for command in commands:
                print(f"  - {command}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
