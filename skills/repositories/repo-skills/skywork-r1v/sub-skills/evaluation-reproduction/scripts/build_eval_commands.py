#!/usr/bin/env python3
"""Print Skywork-R1V3 evaluation commands without executing them.

This helper is intentionally side-effect free. It only prints shell commands,
required environment checks, and notes about known adaptation points.
"""

from __future__ import annotations

import argparse
import re
import shlex
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


DEFAULT_MODEL_PATH = "/path/to/r1v3-model"
DEFAULT_SERVER_NAME = "r1v3-alpha"
DEFAULT_VLLM_BASE = "http://127.0.0.1:8000/v1/chat/completions"
DEFAULT_VLLM_PORT = 8000
DEFAULT_WORK_DIR = "./outputs/Skywork-R1V3"
DEFAULT_JUDGE = "gpt-4o-2024-05-13"
DEFAULT_API_NPROC = 200
DEFAULT_EMMA_DATASET = "luckychao/EMMA"
DEFAULT_EMMA_SUBJECTS = ["Math", "Coding", "Physics", "Chemistry"]
DEFAULT_EMMA_MAX_TOKENS = 64000
DEFAULT_EMMA_SAVE_EVERY = 3
EMMA_REMOTE_MODELS = [
    "chatgpt-4o-latest",
    "claude-3-5-sonnet-latest",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-thinking-exp-1219",
]
DEFAULT_MMK12_DATASETS = ["MMK12"]


def quote(value: object) -> str:
    return shlex.quote(str(value))


def shell_join(parts: Sequence[object]) -> str:
    return " ".join(quote(part) for part in parts if part is not None and str(part) != "")


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", text.strip())
    cleaned = cleaned.strip("_")
    return cleaned or "run"


def print_block(title: str, checklist: Iterable[str], commands: Iterable[str], notes: Iterable[str] = ()) -> None:
    print(f"# {title}")
    checklist = list(checklist)
    if checklist:
        print("Required checklist:")
        for item in checklist:
            print(f"- [ ] {item}")
    notes = list(notes)
    if notes:
        print("Notes:")
        for item in notes:
            print(f"- {item}")
    print("Commands:")
    for cmd in commands:
        print(cmd)
    print()


def build_launch_server(args: argparse.Namespace) -> Tuple[List[str], List[str], List[str]]:
    env = []
    if args.cuda_visible_devices:
        env.append(f"CUDA_VISIBLE_DEVICES={args.cuda_visible_devices}")

    command = shell_join(
        env
        + [
            "python",
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            args.model_path,
            "--port",
            args.port,
            "--trust-remote-code",
            "--served-model-name",
            args.served_model_name,
            "--limit-mm-per-prompt",
            f"image={args.limit_mm_image}",
            "--max_model_len",
            args.max_model_len,
            "--gpu_memory_utilization",
            args.gpu_memory_utilization,
            "--tensor-parallel-size",
            args.tensor_parallel_size,
            "--dtype",
            args.dtype,
        ]
    )

    checklist = [
        f"A real checkpoint path replaces {DEFAULT_MODEL_PATH}",
        f"{args.tensor_parallel_size} visible GPUs are available for tensor parallelism",
        "vLLM 0.8.3, torchao, libgl1, and modelscope are installed",
        f"Port {args.port} is free before launch",
    ]
    notes = [
        "Keep the served model name fixed to r1v3-alpha so the eval client matches it.",
        "Do not run this command as a benchmark; it only starts the API server.",
    ]
    return checklist, [command], notes


def build_vlmeval(args: argparse.Namespace) -> Tuple[List[str], List[str], List[str]]:
    datasets = args.data or ["MMMU_DEV_VAL"]
    use_phyx = args.phyx or any(str(name).upper() == "PHYX" for name in datasets)
    runner = "run_phyx.py" if use_phyx else "run.py"
    use_cot = "0" if use_phyx else "1"

    env_lines = [
        'SKYWORK_EVAL_ROOT="<path-to-prepared-Skywork-R1V-or-compatible-eval-tree>"',
        'BUNDLED_EVAL_SKILL_DIR="<path-to-this-evaluation-reproduction-sub-skill>"',
        'cd "$SKYWORK_EVAL_ROOT/eval/vlmevalkit"',
        f"export LMDEPLOY_API_KEY=\"${{{args.api_key_env}:?set {args.api_key_env}}}\"",
        f"export LMDEPLOY_API_BASE=\"{args.api_base}\"",
    ]

    run_parts: List[object] = ["USE_COT=" + use_cot, "python", runner]
    run_parts += ["--data", *datasets]
    run_parts += ["--model", args.model_name, "--verbose", "--reuse", "--work-dir", args.work_dir, "--judge", args.judge, "--api-nproc", args.api_nproc]
    if args.mode != "all":
        run_parts += ["--mode", args.mode]
    if args.retry is not None:
        run_parts += ["--retry", args.retry]
    if args.ignore:
        run_parts.append("--ignore")
    if args.use_vllm:
        run_parts.append("--use-vllm")

    commands = env_lines + [shell_join(run_parts)]
    if any("MMMU" in str(name) for name in datasets):
        commands += [
            'MMMU_RESULT="<path-to-produced-MMMU-xlsx-or-jsonl>"',
            'python "$BUNDLED_EVAL_SKILL_DIR/scripts/score_boxed_answers.py" --input "$MMMU_RESULT" --val-only',
        ]
    if any("LogicVista" in str(name) for name in datasets):
        commands += [
            'LOGICVISTA_RESULT="<path-to-produced-LogicVista-xlsx-or-jsonl>"',
            'python "$BUNDLED_EVAL_SKILL_DIR/scripts/score_boxed_answers.py" --input "$LOGICVISTA_RESULT"',
        ]

    checklist = [
        f"The served vLLM API is reachable at {args.api_base}",
        f"The judge model {args.judge} is available through the configured API base",
        f"{args.api_nproc} API workers will not overload the local endpoint",
        "Dataset downloads and caches are already available for the selected benchmark(s)",
    ]
    if use_phyx:
        checklist.append("PhyX TSV is placed in the prepared evaluation tree's eval/vlmevalkit/eval_shell/LMUData directory")

    notes = [
        "The stock Skywork shell recipe uses USE_COT=1 for VLMEvalKit and USE_COT=0 for PhyX.",
        "run.py and run_phyx.py accept --data, --model, --config, --work-dir, --mode, --api-nproc, --retry, --judge, --verbose, --ignore, --reuse, --reuse-aux, and --use-vllm.",
        "If MMMU or LogicVista are selected, run the rule-based post-processing step after inference.",
    ]
    if any("MMMU" in str(name) for name in datasets):
        notes.append("MMMU post-processing keeps only val rows and normalizes the last boxed answer.")
    if any("LogicVista" in str(name) for name in datasets):
        notes.append("LogicVista post-processing uses the same boxed-answer normalization without the MMMU val filter.")

    return checklist, commands, notes


def build_emma(args: argparse.Namespace) -> Tuple[List[str], List[str], List[str]]:
    subjects = args.subjects or list(DEFAULT_EMMA_SUBJECTS)
    subject_tag = slugify("_".join(subjects))
    if args.output_path:
        output_path = args.output_path
    else:
        model_tag = slugify(Path(args.model_path).name if args.model_path else args.model)
        output_path = f"results/EMMA-mini/open-source/{model_tag}_{subject_tag}_{args.strategy}.json"

    env_lines = ['SKYWORK_EVAL_ROOT="<path-to-prepared-Skywork-R1V-or-compatible-eval-tree>"']
    if args.cuda_visible_devices:
        env_lines.append(f"export CUDA_VISIBLE_DEVICES={args.cuda_visible_devices}")
    env_lines.append('cd "$SKYWORK_EVAL_ROOT/eval/EMMA"')

    if args.model_path:
        run_command = shell_join([
            "python",
            "generate_response.py",
            "--dataset_name",
            args.dataset_name,
            "--subject",
            *subjects,
            "--split",
            args.split,
            "--strategy",
            args.strategy,
            "--output_path",
            output_path,
            "--model_path",
            args.model_path,
            "--config_path",
            args.config_path,
            "--max_tokens",
            args.max_tokens,
            "--temperature",
            args.temperature,
            "--save_every",
            args.save_every,
        ])
        if args.rerun:
            run_command += " --rerun"
    else:
        api_key_line = f"export EMMA_API_KEY=\"${{{args.api_key_env}:?set {args.api_key_env}}}\""
        env_lines.insert(0, api_key_line)
        pre_api = shell_join([
            "python",
            "generate_response.py",
            "--dataset_name",
            args.dataset_name,
            "--subject",
            *subjects,
            "--split",
            args.split,
            "--strategy",
            args.strategy,
            "--output_path",
            output_path,
            "--model",
            args.model,
        ])
        post_api = shell_join([
            "--config_path",
            args.config_path,
            "--max_tokens",
            args.max_tokens,
            "--temperature",
            args.temperature,
            "--save_every",
            args.save_every,
        ])
        run_command = pre_api + f' --api_key "${{{args.api_key_env}}}" ' + post_api
        if args.rerun:
            run_command += " --rerun"

    commands = env_lines + [run_command]
    results_dir = str(Path(output_path).parent)
    commands.append(shell_join(["python", "evaluation/evaluate.py", "--results_dir", results_dir]))
    commands.append(shell_join(["python", "evaluation/calculate_acc.py", "--results_dir", results_dir]))

    checklist = [
        f"The EMMA dataset {args.dataset_name} is available through the datasets cache",
        "The prompt template YAML is reachable from eval/EMMA/configs/gpt.yaml",
        "The selected local model path exists, or the remote API key is set if you use the remote branch",
        "The output directory is writable so incremental saves can happen",
    ]
    notes = [
        "build_query combines context, question, options, and the CoT/Direct instruction from the YAML template.",
        "verify_response skips blank outputs and strings containing Response Error.",
        "The follow-up evaluator extracts direct letters, numbers, or boxed answers and writes a _result.json companion.",
    ]
    return checklist, commands, notes


def build_mmk12(args: argparse.Namespace) -> Tuple[List[str], List[str], List[str]]:
    datasets = args.datasets or list(DEFAULT_MMK12_DATASETS)
    commands = [
        'SKYWORK_EVAL_ROOT="<path-to-prepared-Skywork-R1V-or-compatible-eval-tree>"',
        'cd "$SKYWORK_EVAL_ROOT"',
        shell_join(["python", "eval/MMK12/evaluate.py", "--datasets", ",".join(datasets), "--out-dir", args.out_dir, "--seed", args.seed]),
        shell_join(["python", "eval/MMK12/calculate_score.py", "--output_dir", args.out_dir, "--output_file", "MMK12_0618_fast_thinking_all_2k.json"]),
    ]
    checklist = [
        "A local OpenAI-compatible base URL is available for the generation client",
        "The served model is reachable under the r1v3-alpha name expected by the script",
        "The MMK12 dataset can be fetched from FanqingM/MMK12",
        "The source script is patched or wrapped so API key and base URL are not hard-coded",
    ]
    notes = [
        "The generation step batches requests with a large thread pool; lower concurrency if the endpoint becomes unstable.",
        "The scoring step extracts <answer>...</answer> first and falls back to the last boxed answer before Yes/No judging.",
        "Keep the judge response exactly Yes or No; any other text is treated as failure.",
    ]
    return checklist, commands, notes


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print Skywork-R1V3 evaluation commands without executing them.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_launch = subparsers.add_parser("launch-server", help="Print the vLLM OpenAI server command.")
    p_launch.add_argument("--model-path", default=DEFAULT_MODEL_PATH)
    p_launch.add_argument("--cuda-visible-devices", default="0,1,2,3,4,5,6,7")
    p_launch.add_argument("--port", type=int, default=DEFAULT_VLLM_PORT)
    p_launch.add_argument("--served-model-name", default=DEFAULT_SERVER_NAME)
    p_launch.add_argument("--limit-mm-image", type=int, default=60)
    p_launch.add_argument("--max-model-len", type=int, default=32768)
    p_launch.add_argument("--tensor-parallel-size", type=int, default=8)
    p_launch.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    p_launch.add_argument("--dtype", default="auto")

    p_vlmeval = subparsers.add_parser("vlmeval", help="Print the VLMEvalKit command bundle.")
    p_vlmeval.add_argument("--data", nargs="+", default=["MMMU_DEV_VAL"])
    p_vlmeval.add_argument("--work-dir", default=DEFAULT_WORK_DIR)
    p_vlmeval.add_argument("--model-name", default="R1V3-alpha")
    p_vlmeval.add_argument("--judge", default=DEFAULT_JUDGE)
    p_vlmeval.add_argument("--api-nproc", type=int, default=DEFAULT_API_NPROC)
    p_vlmeval.add_argument("--api-base", default=DEFAULT_VLLM_BASE)
    p_vlmeval.add_argument("--api-key-env", default="LMDEPLOY_API_KEY")
    p_vlmeval.add_argument("--mode", choices=["all", "infer"], default="all")
    p_vlmeval.add_argument("--retry", type=int)
    p_vlmeval.add_argument("--ignore", action="store_true")
    p_vlmeval.add_argument("--use-vllm", action="store_true")
    p_vlmeval.add_argument("--phyx", action="store_true", help="Use run_phyx.py and USE_COT=0.")

    p_emma = subparsers.add_parser("emma", help="Print the EMMA-mini command bundle.")
    p_emma.add_argument("--dataset-name", default=DEFAULT_EMMA_DATASET)
    p_emma.add_argument("--subjects", nargs="+", default=list(DEFAULT_EMMA_SUBJECTS))
    p_emma.add_argument("--split", default="test")
    p_emma.add_argument("--strategy", choices=["CoT", "Direct"], default="CoT")
    p_emma.add_argument("--config-path", default="configs/gpt.yaml")
    p_emma.add_argument("--output-path", default="")
    p_emma.add_argument("--model-path", default="")
    p_emma.add_argument("--model", choices=EMMA_REMOTE_MODELS, default=EMMA_REMOTE_MODELS[0])
    p_emma.add_argument("--api-key-env", default="EMMA_API_KEY")
    p_emma.add_argument("--max-tokens", type=int, default=DEFAULT_EMMA_MAX_TOKENS)
    p_emma.add_argument("--temperature", type=float, default=0.7)
    p_emma.add_argument("--save-every", type=int, default=DEFAULT_EMMA_SAVE_EVERY)
    p_emma.add_argument("--rerun", action="store_true")
    p_emma.add_argument("--cuda-visible-devices", default="")

    p_mmk12 = subparsers.add_parser("mmk12", help="Print the MMK12 command bundle.")
    p_mmk12.add_argument("--datasets", nargs="+", default=list(DEFAULT_MMK12_DATASETS))
    p_mmk12.add_argument("--out-dir", default="results")
    p_mmk12.add_argument("--seed", type=int, default=0)

    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()

    if args.command == "launch-server":
        checklist, commands, notes = build_launch_server(args)
        print_block("Launch vLLM server", checklist, commands, notes)
    elif args.command == "vlmeval":
        checklist, commands, notes = build_vlmeval(args)
        print_block("Run VLMEvalKit", checklist, commands, notes)
    elif args.command == "emma":
        checklist, commands, notes = build_emma(args)
        print_block("Run EMMA-mini", checklist, commands, notes)
    elif args.command == "mmk12":
        checklist, commands, notes = build_mmk12(args)
        print_block("Run MMK12", checklist, commands, notes)
    else:
        parser.error(f"Unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
