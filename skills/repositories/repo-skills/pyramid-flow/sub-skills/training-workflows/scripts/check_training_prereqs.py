#!/usr/bin/env python3
"""Check Pyramid-Flow training prerequisites before launching long jobs.

The checks are deterministic and bounded. They do not launch torchrun, download
checkpoints, or create datasets/checkpoints. Source syntax checks, when enabled,
compile Python through py_compile into a temporary bytecode file under this
helper directory and delete it immediately.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import py_compile
import shlex
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Sequence


sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_training_commands import (  # noqa: E402
    CommandError,
    VALID_DIT_RESOLUTIONS,
    VALID_DIT_VARIANTS,
    VALID_DTYPES,
    VALID_FSDP_SHARDS,
    VALID_MODEL_NAMES,
    VALID_VAE_STAGES,
    build_causal_video_vae_argvs,
    build_pyramid_flow_ar_argv,
    build_pyramid_flow_no_ar_argv,
)


class PrereqError(ValueError):
    """Readable prerequisite failure."""


def import_module(name: str):
    try:
        return importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - environment specific.
        raise PrereqError(f"could not import {name}: {exc}") from exc


def check_backend(expected_gpus: int) -> dict[str, Any]:
    torch = import_module("torch")
    if not torch.cuda.is_available():
        raise PrereqError("CUDA is not available; Pyramid-Flow training launchers require CUDA/NCCL")
    device_count = torch.cuda.device_count()
    if device_count < expected_gpus:
        raise PrereqError(
            f"only {device_count} CUDA device(s) are visible, but the selected launcher requests {expected_gpus}"
        )
    if not torch.distributed.is_available():
        raise PrereqError("torch.distributed is unavailable; torchrun/FSDP/DDP launchers require it")
    names = []
    for index in range(device_count):
        try:
            names.append(torch.cuda.get_device_name(index))
        except Exception:  # pragma: no cover - backend specific.
            names.append("unknown")
    return {
        "torch": getattr(torch, "__version__", "unknown"),
        "cuda_available": True,
        "cuda_device_count": device_count,
        "cuda_devices": names,
        "distributed_available": True,
    }


def check_exists(raw: str, label: str, *, expect_file: bool | None = None, recovery: str | None = None) -> dict[str, str]:
    if not raw or not str(raw).strip():
        raise PrereqError(f"{label} is required")
    path = Path(raw)
    if not path.exists():
        message = f"{label} does not exist: {raw}"
        if recovery:
            message = f"{message}. {recovery}"
        raise PrereqError(message)
    if expect_file is True and not path.is_file():
        raise PrereqError(f"{label} must be a file: {raw}")
    if expect_file is False and not path.is_dir():
        raise PrereqError(f"{label} must be a directory: {raw}")
    return {"label": label, "path": raw}


def check_dit_paths(args: argparse.Namespace) -> list[dict[str, str]]:
    return [
        check_exists(args.model_path, "--model-path"),
        check_exists(args.anno_file, "--anno-file", expect_file=True),
    ]


def check_vae_paths(args: argparse.Namespace) -> list[dict[str, str]]:
    recovery = "Download the LPIPS VGG checkpoint named in docs/VAE.md and pass it with --lpips-ckpt."
    checks = [
        check_exists(args.lpips_ckpt, "--lpips-ckpt", expect_file=True, recovery=recovery),
        check_exists(args.vae_model_path, "--vae-model-path"),
        check_exists(args.video_anno, "--video-anno", expect_file=True),
    ]
    if args.stage in ("stage1", "both"):
        checks.append(check_exists(args.image_anno, "--image-anno", expect_file=True))
    if args.stage in ("stage2", "both"):
        checks.append(check_exists(args.pretrained_vae_weight, "--pretrained-vae-weight", expect_file=True))
    return checks


def resolve_row_path(raw_path: str, base_dir: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return base_dir / path


def read_jsonl(path: Path, limit: int) -> Iterable[tuple[int, dict[str, Any]]]:
    seen = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise PrereqError(f"{path}: row {line_number} is not valid JSON: {exc.msg}") from exc
            if not isinstance(row, dict):
                raise PrereqError(f"{path}: row {line_number} must be a JSON object")
            yield line_number, row
            seen += 1
            if limit and seen >= limit:
                break
    if seen == 0:
        raise PrereqError(f"annotation file has no JSON rows: {path}")


def validate_jsonl_fields(
    path: str,
    *,
    label: str,
    required: Sequence[str],
    optional_path_fields: Sequence[str] = (),
    limit: int = 10,
    check_referenced_paths: bool = False,
) -> dict[str, Any]:
    annotation = Path(path)
    rows = 0
    for line_number, row in read_jsonl(annotation, limit=limit):
        missing = [field for field in required if field not in row]
        if missing:
            raise PrereqError(f"{label}: row {line_number} missing required field(s): {', '.join(missing)}")
        for field in required:
            if not isinstance(row[field], str) or not row[field].strip():
                raise PrereqError(f"{label}: row {line_number} field {field!r} must be a non-empty string")
        if check_referenced_paths:
            for field in list(required) + list(optional_path_fields):
                if field == "text" or field not in row:
                    continue
                candidate = resolve_row_path(row[field], annotation.parent)
                if not candidate.exists():
                    raise PrereqError(f"{label}: row {line_number} field {field!r} path does not exist: {candidate}")
        rows += 1
    return {"annotation": path, "label": label, "rows_checked": rows, "required": list(required)}


def check_annotations(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.workflow == "pyramid-flow-ar":
        return [
            validate_jsonl_fields(
                args.anno_file,
                label="DiT AR video annotation",
                required=("text", "latent"),
                optional_path_fields=("video", "text_fea"),
                limit=args.annotation_limit,
                check_referenced_paths=args.check_referenced_paths,
            )
        ]
    if args.workflow == "pyramid-flow-no-ar":
        return [
            validate_jsonl_fields(
                args.anno_file,
                label="DiT non-AR image annotation",
                required=("image", "text"),
                limit=args.annotation_limit,
                check_referenced_paths=args.check_referenced_paths,
            )
        ]
    if args.workflow == "causal-video-vae":
        reports: list[dict[str, Any]] = []
        if args.stage in ("stage1", "both"):
            reports.append(
                validate_jsonl_fields(
                    args.image_anno,
                    label="VAE stage-1 image annotation",
                    required=("image",),
                    limit=args.annotation_limit,
                    check_referenced_paths=args.check_referenced_paths,
                )
            )
        reports.append(
            validate_jsonl_fields(
                args.video_anno,
                label="VAE video annotation",
                required=("video",),
                limit=args.annotation_limit,
                check_referenced_paths=args.check_referenced_paths,
            )
        )
        return reports
    raise PrereqError(f"unknown workflow: {args.workflow}")


def check_shell_syntax(repo_root: str) -> list[dict[str, str]]:
    scripts = [
        "scripts/train_pyramid_flow.sh",
        "scripts/train_pyramid_flow_without_ar.sh",
        "scripts/train_causal_video_vae.sh",
    ]
    reports: list[dict[str, str]] = []
    for rel in scripts:
        path = Path(repo_root) / rel
        if not path.exists():
            raise PrereqError(f"source shell launcher missing for syntax check: {rel}")
        result = subprocess.run(["bash", "-n", str(path)], text=True, capture_output=True)
        if result.returncode != 0:
            raise PrereqError(f"bash -n failed for {rel}: {result.stderr.strip()}")
        reports.append({"script": rel, "status": "ok"})
    return reports


def check_python_syntax(repo_root: str) -> list[dict[str, str]]:
    scripts = ["train/train_pyramid_flow.py", "train/train_video_vae.py"]
    reports: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix=".py_compile-", dir=SCRIPT_DIR) as tmp_dir:
        tmp_path = Path(tmp_dir)
        for rel in scripts:
            path = Path(repo_root) / rel
            if not path.exists():
                raise PrereqError(f"source Python training entry point missing for syntax check: {rel}")
            cfile = tmp_path / f"{Path(rel).stem}.pyc"
            py_compile.compile(str(path), cfile=str(cfile), doraise=True)
            reports.append({"script": rel, "status": "ok"})
    return reports


def build_commands(args: argparse.Namespace) -> list[list[str]]:
    if args.workflow == "pyramid-flow-ar":
        return [build_pyramid_flow_ar_argv(args)]
    if args.workflow == "pyramid-flow-no-ar":
        return [build_pyramid_flow_no_ar_argv(args)]
    if args.workflow == "causal-video-vae":
        return build_causal_video_vae_argvs(args)
    raise PrereqError(f"unknown workflow: {args.workflow}")


def add_checker_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--skip-backend", action="store_true", help="Skip CUDA/torch.distributed checks.")
    parser.add_argument("--skip-path-existence", action="store_true", help="Skip local checkpoint/annotation/LPIPS existence checks.")
    parser.add_argument("--validate-annotations", action="store_true", help="Parse a bounded sample of annotation JSONL rows.")
    parser.add_argument("--check-referenced-paths", action="store_true", help="When validating annotations, require referenced paths to exist.")
    parser.add_argument("--annotation-limit", type=int, default=10, help="Maximum non-empty JSONL rows to inspect.")
    parser.add_argument("--check-source-syntax", action="store_true", help="Run bash -n and no-bytecode Python syntax checks on source launchers.")
    parser.add_argument("--show-commands", action="store_true", help="Print the validated torchrun command(s) after checks.")
    parser.add_argument("--report-format", choices=("text", "json"), default="text")


def add_dit_args(parser: argparse.ArgumentParser, *, default_batch_size: int, default_num_frames: int, default_resolution: str, default_variant: str, default_lr: str, default_grad_accum: int) -> None:
    parser.add_argument("--gpus", type=int, default=8)
    parser.add_argument("--model-name", choices=VALID_MODEL_NAMES, default="pyramid_flux")
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--model-variant", choices=VALID_DIT_VARIANTS, default=default_variant)
    parser.add_argument("--model-dtype", choices=VALID_DTYPES, default="bf16")
    parser.add_argument("--fsdp-shard-strategy", choices=VALID_FSDP_SHARDS, default="zero2")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--anno-file", required=True)
    parser.add_argument("--batch-size", type=int, default=default_batch_size)
    parser.add_argument("--num-frames", type=int, default=default_num_frames)
    parser.add_argument("--resolution", choices=VALID_DIT_RESOLUTIONS, default=default_resolution)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=default_grad_accum)
    parser.add_argument("--gradient-checkpointing", action="store_true")
    parser.add_argument("--num-workers", type=int, default=8)
    parser.add_argument("--lr", default=default_lr)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--iters-per-epoch", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--use-sequence-parallel", action="store_true")
    parser.add_argument("--sp-group-size", type=int, default=1)
    parser.add_argument("--sp-proc-num", type=int, default=-1)
    parser.add_argument("--repo-root", default=".")
    add_checker_options(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="workflow", required=True)

    ar = subparsers.add_parser("pyramid-flow-ar", help="Check the AR temporal-pyramid DiT training launcher.")
    add_dit_args(
        ar,
        default_batch_size=4,
        default_num_frames=16,
        default_resolution="384p",
        default_variant="diffusion_transformer_384p",
        default_lr="5e-5",
        default_grad_accum=2,
    )
    ar.add_argument("--video-sync-group", type=int, default=8)

    no_ar = subparsers.add_parser("pyramid-flow-no-ar", help="Check the published non-AR/full-sequence t2i DiT launcher.")
    add_dit_args(
        no_ar,
        default_batch_size=4,
        default_num_frames=8,
        default_resolution="768p",
        default_variant="diffusion_transformer_image",
        default_lr="1e-4",
        default_grad_accum=1,
    )

    vae = subparsers.add_parser("causal-video-vae", help="Check Causal Video VAE stage-1/stage-2 launchers.")
    vae.add_argument("--stage", choices=VALID_VAE_STAGES, default="both")
    vae.add_argument("--gpus", type=int, default=8)
    vae.add_argument("--vae-model-path", required=True)
    vae.add_argument("--model-dtype", choices=VALID_DTYPES, default="bf16")
    vae.add_argument("--lpips-ckpt", required=True)
    vae.add_argument("--output-dir", required=True)
    vae.add_argument("--image-anno", default="")
    vae.add_argument("--video-anno", required=True)
    vae.add_argument("--pretrained-vae-weight", default="")
    vae.add_argument("--resolution", type=int, default=256)
    vae.add_argument("--stage1-num-frames", type=int, default=17)
    vae.add_argument("--stage2-num-frames", type=int, default=33)
    vae.add_argument("--context-size", type=int, default=2)
    vae.add_argument("--stage1-batch-size", type=int, default=2)
    vae.add_argument("--stage2-batch-size", type=int, default=2)
    vae.add_argument("--image-mix-ratio", type=float, default=0.1)
    vae.add_argument("--num-workers", type=int, default=6)
    vae.add_argument("--lr", default="1e-4")
    vae.add_argument("--lr-disc", default="1e-4")
    vae.add_argument("--epochs", type=int, default=100)
    vae.add_argument("--iters-per-epoch", type=int, default=2000)
    vae.add_argument("--seed", type=int, default=42)
    vae.add_argument("--repo-root", default=".")
    add_checker_options(vae)

    return parser


def emit_report(report: dict[str, Any], args: argparse.Namespace) -> None:
    if args.report_format == "json":
        print(json.dumps(report, indent=2))
        return

    print(f"workflow: {report['workflow']}")
    for check in report["checks"]:
        print(f"ok: {check}")
    if args.show_commands:
        print("commands:")
        for command in report["commands"]:
            print("  " + shlex.join(command))


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        commands = build_commands(args)
        report: dict[str, Any] = {"workflow": args.workflow, "checks": ["command-builder dry run"], "commands": commands}

        if not args.skip_backend:
            report["backend"] = check_backend(args.gpus)
            report["checks"].append("CUDA and torch.distributed backend")

        if not args.skip_path_existence:
            if args.workflow.startswith("pyramid-flow"):
                report["paths"] = check_dit_paths(args)
            else:
                report["paths"] = check_vae_paths(args)
            report["checks"].append("required local paths")

        if args.validate_annotations:
            report["annotations"] = check_annotations(args)
            report["checks"].append("annotation JSONL sample")

        if args.check_source_syntax:
            report["shell_syntax"] = check_shell_syntax(args.repo_root)
            report["python_syntax"] = check_python_syntax(args.repo_root)
            report["checks"].append("source shell/Python syntax")

        emit_report(report, args)
        return 0
    except (CommandError, PrereqError, py_compile.PyCompileError) as exc:
        print(f"TRAINING PREREQ CHECK FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
