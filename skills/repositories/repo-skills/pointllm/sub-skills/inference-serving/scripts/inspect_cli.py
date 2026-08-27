#!/usr/bin/env python3
"""Print PointLLM inference CLI contracts without importing PointLLM.

This deliberately does not execute the native launchers: they import the full
runtime before argparse, which can require optional packages and CUDA. Use this
for an offline flag/help inspection only.
"""
from __future__ import annotations

import argparse
import json
from typing import Dict

CLIS: Dict[str, dict] = {
    "PointLLM_chat.py": {
        "command": "python run_installed_cli.py PointLLM_chat.py",
        "flags": {
            "--model_name": "STRING (default RunsenXu/PointLLM_7B_v1.2)",
            "--data_path": "STRING (default data/objaverse_data)",
            "--torch_dtype": "float32|float16|bfloat16 (default float32)",
        },
        "notes": "Interactive Objaverse object-id chat; q quits, exit ends a conversation.",
    },
    "chat_gradio.py": {
        "command": "python run_installed_cli.py chat_gradio.py",
        "flags": {
            "--model_name": "STRING (default RunsenXu/PointLLM_7B_v1.2)",
            "--data_path": "STRING (default data/objaverse_data)",
            "--pointnum": "INT (default 8192; handler's FPS branch is literal 8192)",
            "--log_file": "STRING (default serving_workdirs/serving_log.txt)",
            "--tmp_dir": "STRING (default serving_workdirs/tmp)",
            "--port": "INT (default 7810)",
        },
        "notes": "Binds 0.0.0.0 and launches share=False; Object ID may use the network.",
    },
    "eval_objaverse.py": {
        "command": "python run_installed_cli.py eval_objaverse.py",
        "flags": {
            "--model_name": "STRING (default RunsenXu/PointLLM_7B_v1.2)",
            "--data_path": "STRING (default data/objaverse_data)",
            "--anno_path": "STRING (default data/anno_data/PointLLM_brief_description_val_200_GT.json)",
            "--pointnum": "INT (default 8192)",
            "--use_color": "store_true (source default True)",
            "--batch_size": "INT (default 6)",
            "--shuffle": "BOOL (default False; omit textual False)",
            "--num_workers": "INT (default 10)",
            "--prompt_index": "INT (default 0; classification 0/1, captioning 2)",
            "--start_eval": "store_true (default False)",
            "--gpt_type": "four supported GPT names (default gpt-4-0613)",
            "--task_type": "captioning|classification (default captioning)",
        },
        "notes": "Batched Objaverse generation; source loads bfloat16 and CUDA.",
    },
    "eval_modelnet_cls.py": {
        "command": "python run_installed_cli.py eval_modelnet_cls.py",
        "flags": {
            "--model_name": "STRING (default RunsenXu/PointLLM_7B_v1.2)",
            "--split": "train|test (default test)",
            "--use_color": "store_true (source default True)",
            "--batch_size": "INT (default 30)",
            "--shuffle": "BOOL (default False; omit textual False)",
            "--num_workers": "INT (default 20)",
            "--subset_nums": "INT (default -1)",
            "--prompt_index": "INT (default 0; choices 0/1)",
            "--start_eval": "store_true (default False)",
            "--gpt_type": "four supported GPT names (default gpt-3.5-turbo-0613)",
        },
        "notes": "Batched ModelNet40 generation; no-shuffle is required by the source.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?", choices=sorted(CLIS), help="one CLI name; omit with --all")
    parser.add_argument("--all", action="store_true", help="print all four contracts")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args()
    if not args.all and args.name is None:
        parser.error("choose a CLI name or --all")
    selected = CLIS if args.all else {args.name: CLIS[args.name]}
    if args.json:
        print(json.dumps(selected, indent=2, sort_keys=True))
        return 0
    for name, spec in selected.items():
        print(f"=== {name} ===")
        print(spec["command"] + " --help")
        for flag, contract in spec["flags"].items():
            print(f"  {flag}: {contract}")
        print(f"  note: {spec['notes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
