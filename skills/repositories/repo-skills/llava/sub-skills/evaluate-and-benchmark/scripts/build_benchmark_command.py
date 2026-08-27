#!/usr/bin/env python3
"""Print a safe LLaVA benchmark command template.

The script does not launch inference. It only prints a shell command template
for the chosen benchmark family.
"""

from __future__ import annotations

import argparse
import shlex


COMMANDS = {
    "custom": "python -m llava.eval.model_vqa",
    "vqav2": "bash scripts/v1_5/eval/vqav2.sh",
    "gqa": "bash scripts/v1_5/eval/gqa.sh",
    "vizwiz": "bash scripts/v1_5/eval/vizwiz.sh",
    "scienceqa": "bash scripts/v1_5/eval/sqa.sh",
    "textvqa": "bash scripts/v1_5/eval/textvqa.sh",
    "pope": "bash scripts/v1_5/eval/pope.sh",
    "mme": "bash scripts/v1_5/eval/mme.sh",
    "mmbench": "bash scripts/v1_5/eval/mmbench.sh",
    "mmbench-cn": "bash scripts/v1_5/eval/mmbench_cn.sh",
    "seed": "bash scripts/v1_5/eval/seed.sh",
    "llavabench": "bash scripts/v1_5/eval/llavabench.sh",
    "mmvet": "bash scripts/v1_5/eval/mmvet.sh",
    "qbench": "bash scripts/v1_5/eval/qbench.sh",
    "qbench-zh": "bash scripts/v1_5/eval/qbench_zh.sh",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a safe LLaVA benchmark command.")
    parser.add_argument("--benchmark", choices=sorted(COMMANDS), required=True)
    parser.add_argument("--model-path", help="Checkpoint or hub id for custom mode")
    parser.add_argument("--question-file", help="Question file for custom mode")
    parser.add_argument("--image-folder", help="Image folder for custom mode")
    parser.add_argument("--answers-file", help="Answer file for custom mode")
    parser.add_argument("--conv-mode", default="llava_v1")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, dest="top_p")
    parser.add_argument("--num-beams", type=int, default=1)
    parser.add_argument("--single-pred-prompt", action="store_true")
    parser.add_argument("--lang", default="en")
    args = parser.parse_args()

    if args.benchmark == "custom":
        if not all([args.model_path, args.question_file, args.image_folder, args.answers_file]):
            parser.error("custom mode requires --model-path, --question-file, --image-folder, and --answers-file")
        cmd = [
            "python",
            "-m",
            "llava.eval.model_vqa",
            "--model-path",
            args.model_path,
            "--question-file",
            args.question_file,
            "--image-folder",
            args.image_folder,
            "--answers-file",
            args.answers_file,
            "--conv-mode",
            args.conv_mode,
            "--temperature",
            str(args.temperature),
            "--num_beams",
            str(args.num_beams),
        ]
        if args.top_p is not None:
            cmd += ["--top_p", str(args.top_p)]
    else:
        cmd = [COMMANDS[args.benchmark]]
        if args.benchmark == "mmbench" and args.single_pred_prompt:
            cmd.append("--single-pred-prompt")
        if args.benchmark == "mmbench-cn" and args.lang:
            cmd += ["--lang", args.lang]

    print(shlex.join(cmd))
    if args.benchmark in {"llavabench", "mmbench", "mmbench-cn", "qbench", "qbench-zh"}:
        print("# Note: this benchmark family may require a submission upload or judge step.")
    if args.benchmark in {"llavabench"}:
        print("# Note: GPT review requires credentials and network access.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
