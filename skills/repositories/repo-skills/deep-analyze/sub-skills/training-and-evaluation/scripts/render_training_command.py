#!/usr/bin/env python3
"""Render safe DeepAnalyze training command plans.

The script validates required variables and prints the command that would be run
for one official DeepAnalyze training stage. It does not execute training.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import sys
from typing import Dict, Iterable, List, Sequence, Tuple


REASONING_DATA = [
    "reasoning/SKGInstruct_199989.json",
    "reasoning/TableQA_distillation_39301.json",
    "reasoning/TableQA_refinement_39301.json",
    "reasoning/TableGPT_29448.json",
    "reasoning/file_database_3833.json",
    "reasoning/file_csv_3007.json",
    "reasoning/file_xlsx_3663.json",
    "reasoning/file_any_2520.json",
    "reasoning/math_20000.json",
    "reasoning/code_20000.json",
    "reasoning/science_20000.json",
    "reasoning/instruction_following_20000.json",
    "reasoning/other_19998.json",
]

INTERATION_DATA = [
    "interation/data_pipeline_3601.json",
    "interation/data_preparation_3311.json",
    "interation/data_cleaning_1616.json",
    "interation/data_analysis_3936.json",
    "interation/data_insight_1062.json",
    "interation/research_database_818.json",
    "interation/research_xlsx_848.json",
    "interation/research_other_3505.json",
    "interation/research_data_preparation_488.json",
    "interation/research_data_analysis_1339.json",
    "interation/research_data_insight_1351.json",
    "interation/research_report_generation_4327.json",
]

RL_DATA = [
    "RL/qa.parquet",
    "RL/datatask.parquet",
    "RL/reseach.parquet",
]

PLACEHOLDER_MARKERS = [
    "path_to",
    "path-to",
    "path/to",
    "path_to_",
    "path to",
    "PATH_TO",
    "YOUR_API_KEY",
    "xxxxx",
    "<",
    ">",
]


def q(value: object) -> str:
    return shlex.quote(str(value))


def split_gpus(gpus: str) -> List[str]:
    values = [part.strip() for part in gpus.split(",") if part.strip()]
    if not values:
        raise ValueError("--gpus must contain at least one device id")
    return values


def has_placeholder(value: str) -> bool:
    low = value.lower()
    return any(marker.lower() in low for marker in PLACEHOLDER_MARKERS)


def require_value(name: str, value: str | None, errors: List[str], allow_placeholders: bool) -> None:
    if value is None or not str(value).strip():
        errors.append(f"missing required argument: {name}")
        return
    if has_placeholder(str(value)) and not allow_placeholders:
        errors.append(f"{name} still looks like a placeholder: {value!r}")


def check_paths(paths: Iterable[Path], errors: List[str]) -> None:
    for path in paths:
        if not path.exists():
            errors.append(f"required path does not exist: {path}")


def looks_like_local_path(value: str) -> bool:
    if value.startswith(("http://", "https://")):
        return False
    if Path(value).exists():
        return True
    if value.startswith(("./", "../", "/", "~")):
        return True
    return False


def join_data(data_dir: str, rels: Sequence[str]) -> List[str]:
    return [os.path.join(data_dir, rel) for rel in rels]


def sft_common_args(model: str, data_paths: Sequence[str], output_model: str, *, max_length: int, per_device_train_batch_size: int, learning_rate: str, gradient_accumulation_steps: int) -> List[str]:
    args: List[str] = [
        "swift",
        "sft",
        "--model",
        model,
        "--train_type",
        "full",
        "--dataset",
    ]
    args.extend(data_paths)
    args.extend(
        [
            "--torch_dtype",
            "bfloat16",
            "--num_train_epochs",
            "3",
            "--per_device_train_batch_size",
            str(per_device_train_batch_size),
            "--per_device_eval_batch_size",
            "4",
            "--learning_rate",
            learning_rate,
            "--gradient_accumulation_steps",
            str(gradient_accumulation_steps),
            "--packing",
            "true",
            "--eval_steps",
            "50",
            "--save_steps",
            "50",
            "--logging_steps",
            "1",
            "--max_length",
            str(max_length),
            "--warmup_ratio",
            "0.05",
            "--dataloader_num_workers",
            "8",
            "--dataset_num_proc",
            "8",
            "--save_total_limit",
            "3",
            "--response_prefix",
            "",
            "--save_only_model",
            "false",
            "--output_dir",
            output_model,
            "--deepspeed",
            "zero3",
            "--use_liger_kernel",
            "true",
            "--attn_impl",
            "flash_attn",
            "--model_type",
            "deepseek_r1_distill",
        ]
    )
    return args


def build_plan(args: argparse.Namespace) -> Tuple[Dict[str, object], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    gpu_values = split_gpus(args.gpus)

    if args.stage in {"single", "multi-coldstart"}:
        nproc = args.nproc_per_node or len(gpu_values)
        env = {
            "CUDA_VISIBLE_DEVICES": args.gpus,
            "NPROC_PER_NODE": str(nproc),
            "MASTER_PORT": str(args.master_port),
        }
        working_directory = "deepanalyze/ms-swift"
        if nproc != len(gpu_values):
            warnings.append("NPROC_PER_NODE does not match the number of visible GPU ids; verify this is intentional.")

        if args.stage == "single":
            require_value("--base-model", args.base_model, errors, args.allow_placeholders)
            require_value("--output-model", args.output_model, errors, args.allow_placeholders)
            require_value("--data-dir", args.data_dir, errors, args.allow_placeholders)
            data_paths = join_data(args.data_dir or "", REASONING_DATA)
            command = sft_common_args(
                args.base_model or "",
                data_paths,
                args.output_model or "",
                max_length=8192,
                per_device_train_batch_size=8,
                learning_rate="5e-5",
                gradient_accumulation_steps=4,
            )
            dataset_group = "reasoning"
        else:
            require_value("--previous-stage-model", args.previous_stage_model, errors, args.allow_placeholders)
            require_value("--output-model", args.output_model, errors, args.allow_placeholders)
            require_value("--data-dir", args.data_dir, errors, args.allow_placeholders)
            data_paths = join_data(args.data_dir or "", INTERATION_DATA)
            command = sft_common_args(
                args.previous_stage_model or "",
                data_paths,
                args.output_model or "",
                max_length=32768,
                per_device_train_batch_size=1,
                learning_rate="5e-6",
                gradient_accumulation_steps=32,
            )
            dataset_group = "interation"

        if args.check_files and args.data_dir:
            check_paths([Path(args.data_dir) / rel for rel in (REASONING_DATA if args.stage == "single" else INTERATION_DATA)], errors)
            model_arg = args.base_model if args.stage == "single" else args.previous_stage_model
            if model_arg and looks_like_local_path(model_arg):
                check_paths([Path(model_arg)], errors)

        plan = {
            "stage": args.stage,
            "working_directory": working_directory,
            "environment": env,
            "command": command,
            "dataset_group": dataset_group,
            "dry_run_only": True,
        }
        return plan, warnings, errors

    if args.stage == "multi-rl":
        num_gpus = args.num_gpus or len(gpu_values)
        if num_gpus != len(gpu_values):
            warnings.append("NUM_GPUS does not match the number of visible GPU ids; verify placement overrides are intentional.")
        require_value("--coldstart-model", args.coldstart_model, errors, args.allow_placeholders)
        require_value("--final-model", args.final_model, errors, args.allow_placeholders)
        require_value("--data-dir", args.data_dir, errors, args.allow_placeholders)
        require_value("--inference-backend", args.inference_backend, errors, args.allow_placeholders)

        train_data = [os.path.join(args.data_dir or "", rel) for rel in RL_DATA]
        workspace = os.path.join(args.data_dir or "", "RL", "data") + "/"
        final_model = args.final_model or ""
        command = [
            "python",
            "-m",
            "examples.deepanalyze.main_deepanalyze",
            "trainer.algorithm.advantage_estimator=grpo",
            "trainer.epochs=1",
            "data.train_data=" + json.dumps(train_data),
            f"trainer.policy.model.path={args.coldstart_model or ''}",
            "trainer.placement.colocate_all=true",
            "trainer.strategy=fsdp2",
            "trainer.policy.fsdp_config.cpu_offload=true",
            "trainer.ref.fsdp_config.cpu_offload=true",
            f"trainer.placement.policy_num_gpus_per_node={num_gpus}",
            f"trainer.placement.ref_num_gpus_per_node={num_gpus}",
            f"generator.num_inference_engines={num_gpus}",
            "generator.inference_engine_tensor_parallel_size=1",
            "trainer.train_batch_size=256",
            "trainer.micro_forward_batch_size_per_gpu=16",
            "trainer.micro_train_batch_size_per_gpu=1",
            "trainer.max_prompt_length=8000",
            "generator.max_input_length=32768",
            "generator.sampling_params.max_generate_length=32768",
            "trainer.policy.optimizer_config.lr=5e-7",
            "trainer.policy_mini_batch_size=256",
            "trainer.algorithm.use_kl_loss=false",
            f"generator.backend={args.inference_backend}",
            "generator.run_engines_locally=true",
            "generator.weight_sync_backend=nccl",
            "generator.async_engine=true",
            "generator.batched=false",
            "generator.use_conversation_multi_turn=false",
            "generator.n_samples_per_prompt=5",
            f"generator.gpu_memory_utilization={args.gpu_memory_utilization}",
            "generator.max_turns=30",
            "generator.sampling_params.temperature=0.0",
            "generator.sampling_params.top_p=0.95",
            "generator.sampling_params.stop_token_ids=[151676,151645]",
            "environment.env_class=deepanalyze",
            f"environment.skyrl_gym.deepanalyze.workspace={workspace}",
            'trainer.logger=["console","tensorboard"]',
            f"trainer.project_name={args.project_name}",
            f"trainer.run_name={args.run_name}",
            "trainer.resume_mode=latest",
            f"trainer.ckpt_path={os.path.join(final_model, 'ckpt')}",
            f"trainer.export_path={os.path.join(final_model, 'export')}",
            "trainer.eval_batch_size=8",
            "trainer.eval_before_train=false",
            "trainer.eval_interval=-1",
            "trainer.hf_save_interval=1",
            "trainer.ckpt_interval=1",
        ]
        env = {
            "CUDA_VISIBLE_DEVICES": args.gpus,
            "NUM_GPUS": str(num_gpus),
        }
        if args.check_files and args.data_dir:
            check_paths([Path(args.data_dir) / rel for rel in RL_DATA], errors)
            check_paths([Path(args.data_dir) / "RL" / "data"], errors)
            if args.coldstart_model and looks_like_local_path(args.coldstart_model):
                check_paths([Path(args.coldstart_model)], errors)

        plan = {
            "stage": args.stage,
            "working_directory": "deepanalyze/SkyRL/skyrl-train",
            "environment": env,
            "command": command,
            "dataset_group": "RL",
            "dry_run_only": True,
        }
        return plan, warnings, errors

    errors.append(f"unsupported stage: {args.stage}")
    return {}, warnings, errors


def shell_plan(plan: Dict[str, object], warnings: Sequence[str]) -> str:
    lines: List[str] = []
    lines.append("# Dry-run DeepAnalyze training command plan. Review before executing manually.")
    if warnings:
        lines.append("# Warnings:")
        for warning in warnings:
            lines.append(f"# - {warning}")
    lines.append(f"# Stage: {plan['stage']}")
    lines.append(f"# Working directory: {plan['working_directory']}")
    for key, value in (plan.get("environment") or {}).items():
        lines.append(f"export {key}={q(value)}")
    lines.append(f"cd {q(plan['working_directory'])}")
    command = [str(part) for part in plan["command"]]  # type: ignore[index]
    if len(command) <= 2:
        lines.append(" ".join(q(part) for part in command))
    else:
        lines.append(" \\\n  ".join(q(part) for part in command))
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render official DeepAnalyze training command plans without executing them.")
    parser.add_argument("stage", choices=["single", "multi-coldstart", "multi-rl"], help="Training stage to render.")
    parser.add_argument("--data-dir", help="Root of DataScience-Instruct-500K.")
    parser.add_argument("--gpus", default="0,1,2,3,4,5,6,7", help="Comma-separated CUDA device ids to expose.")
    parser.add_argument("--nproc-per-node", type=int, help="Torch distributed processes per node for SFT stages; defaults to GPU count.")
    parser.add_argument("--master-port", default="12345", help="Torch distributed master port for SFT stages.")
    parser.add_argument("--check-files", action="store_true", help="Require local model/data paths referenced by the selected stage to exist.")
    parser.add_argument("--allow-placeholders", action="store_true", help="Allow placeholder-looking values for template generation. Default rejects them.")
    parser.add_argument("--format", choices=["shell", "json"], default="shell", help="Output format.")

    parser.add_argument("--base-model", help="Single-ability SFT input model checkpoint.")
    parser.add_argument("--previous-stage-model", help="Multi-coldstart SFT input checkpoint from single-ability SFT.")
    parser.add_argument("--output-model", help="SFT output checkpoint directory.")

    parser.add_argument("--coldstart-model", help="Multi-RL input checkpoint from cold-start SFT.")
    parser.add_argument("--final-model", help="Multi-RL output root; ckpt/export are created below it.")
    parser.add_argument("--num-gpus", type=int, help="SkyRL NUM_GPUS override; defaults to visible GPU count.")
    parser.add_argument("--inference-backend", default="vllm", help="SkyRL generator backend; official DeepAnalyze value is vllm.")
    parser.add_argument("--project-name", default="deepanalyze", help="SkyRL trainer project name.")
    parser.add_argument("--run-name", default="deepanalyze_run", help="SkyRL trainer run name.")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.5, help="vLLM GPU memory utilization for SkyRL generator.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        plan, warnings, errors = build_plan(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps({"plan": plan, "warnings": warnings}, indent=2))
    else:
        print(shell_plan(plan, warnings), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
