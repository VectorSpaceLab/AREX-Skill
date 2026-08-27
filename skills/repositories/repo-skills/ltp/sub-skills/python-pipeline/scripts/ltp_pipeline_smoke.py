#!/usr/bin/env python3
"""Safe smoke helper for high-level LTP pipeline workflows.

Default mode uses no model and performs import + sentence-split checks only.
Pass --model-path to run a tiny pipeline against a local path or model id.
Network downloads are disabled by default with --local-files-only.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List


def parse_tasks(text: str) -> List[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check LTP imports and optionally run a tiny pipeline.")
    parser.add_argument("--skip-model-load", action="store_true", help="only import ltp and run StnSplit; no model resolution")
    parser.add_argument("--model-path", help="local model path or model id; omitted unless model loading is explicitly desired")
    parser.add_argument("--sentence", default="他叫汤姆去拿外衣。", help="sentence for optional model inference")
    parser.add_argument("--tasks", default="cws,pos,ner", help="comma-separated tasks for optional pipeline run")
    parser.add_argument("--allow-download", action="store_true", help="allow Hugging Face/network resolution instead of cache-only loading")
    parser.add_argument("--local-files-only", action="store_true", help="force Hugging Face cache/local-only model loading")
    parser.add_argument("--cuda", action="store_true", help="move model to CUDA after verifying torch CUDA availability")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    result = {"imports": False, "sentence_split": None, "model_loaded": False, "pipeline": None, "errors": []}

    try:
        from ltp import LTP, StnSplit

        result["imports"] = True
        result["sentence_split"] = StnSplit().split("汤姆生病了。他去了医院。")
    except Exception as exc:
        result["errors"].append(f"import/sentence split failed: {type(exc).__name__}: {exc}")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["errors"][-1])
        return 1

    if not args.skip_model_load and args.model_path:
        try:
            local_only = args.local_files_only or not args.allow_download
            ltp = LTP(args.model_path, local_files_only=local_only)
            result["model_loaded"] = True
            if args.cuda:
                import torch

                if not torch.cuda.is_available():
                    raise RuntimeError("--cuda requested but torch.cuda.is_available() is false")
                torch.empty((1,), device="cuda")
                ltp.to("cuda")
            output = ltp.pipeline([args.sentence], tasks=parse_tasks(args.tasks))
            result["pipeline"] = {task: getattr(output, task) for task in parse_tasks(args.tasks)}
        except Exception as exc:
            result["errors"].append(f"model/pipeline smoke failed: {type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("imports: OK")
        print(f"sentence_split: {result['sentence_split']}")
        if args.model_path:
            print(f"model_loaded: {result['model_loaded']}")
            if result["pipeline"] is not None:
                print(f"pipeline: {result['pipeline']}")
        if result["errors"]:
            print("errors:")
            for error in result["errors"]:
                print(f"- {error}")

    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
