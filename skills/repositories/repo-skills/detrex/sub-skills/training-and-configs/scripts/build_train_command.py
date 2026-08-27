#!/usr/bin/env python3
"""Build safe detrex training/evaluation commands without executing them.

The helper is intentionally dry-run only: it prints a shell command and optional
warnings, but it never imports detrex, loads configs, starts training, submits
Slurm jobs, downloads datasets, or checks checkpoint existence.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List, Sequence


def positive_or_zero_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {text!r}") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return value


def module_to_script(module_name: str) -> str:
    if module_name.endswith(".py") or "/" in module_name:
        return module_name
    return module_name.replace(".", "/") + ".py"


def prefixed_override(token: str, *, hydra: bool) -> str:
    """Return an override token, adding Hydra's LazyConfig '+' prefix when needed."""
    if not hydra:
        return token
    if token.startswith("+") or token.startswith("~"):
        return token
    return "+" + token


def add_if_missing(overrides: List[str], token: str) -> None:
    key = token.split("=", 1)[0]
    existing_keys = [item.lstrip("+").split("=", 1)[0] for item in overrides]
    if key.lstrip("+") not in existing_keys:
        overrides.append(token)


def bool_text(hydra: bool, value: bool = True) -> str:
    if hydra:
        return "true" if value else "false"
    return "True" if value else "False"


def format_command(tokens: Sequence[str], *, multiline: bool) -> str:
    quoted = [shlex.quote(token) for token in tokens]
    if not multiline:
        return " ".join(quoted)
    if len(quoted) <= 1:
        return " ".join(quoted)
    return " \\\n  ".join(quoted)


def build_plain_command(args: argparse.Namespace, warnings: List[str]) -> List[str]:
    module_name = args.trainer_module or "tools.train_net"
    if args.entrypoint == "module":
        tokens = ["python", "-m", module_name]
    else:
        tokens = ["python", args.trainer_script or module_to_script(module_name)]

    tokens.extend(["--config-file", args.config_file])
    if args.num_gpus is not None:
        tokens.extend(["--num-gpus", str(args.num_gpus)])
    if args.num_machines is not None:
        tokens.extend(["--num-machines", str(args.num_machines)])
    if args.machine_rank is not None:
        tokens.extend(["--machine-rank", str(args.machine_rank)])
    if args.dist_url:
        tokens.extend(["--dist-url", args.dist_url])
    if args.resume:
        tokens.append("--resume")
    if args.eval_only:
        tokens.append("--eval-only")
    if args.auto_output_dir:
        warnings.append("--auto-output-dir is a Hydra launcher option; plain launcher uses train.output_dir overrides")

    overrides = collect_lazy_overrides(args, hydra=False)
    tokens.extend(overrides)
    return tokens


def build_hydra_command(args: argparse.Namespace, warnings: List[str]) -> List[str]:
    hydra_module = args.hydra_module or "tools.hydra_train_net"
    if args.entrypoint == "module":
        tokens = ["python", "-m", hydra_module]
    else:
        tokens = ["python", args.hydra_script or module_to_script(hydra_module)]

    # Hydra launcher fields are plain key=value tokens, not LazyConfig task overrides.
    tokens.append(f"config_file={args.config_file}")
    if args.num_gpus is not None:
        tokens.append(f"num_gpus={args.num_gpus}")
    if args.num_machines is not None:
        tokens.append(f"num_machines={args.num_machines}")
    if args.machine_rank is not None:
        tokens.append(f"machine_rank={args.machine_rank}")
    if args.dist_url:
        tokens.append(f"dist_url={args.dist_url}")
    if args.resume:
        tokens.append("resume=true")
    if args.eval_only:
        tokens.append("eval_only=true")
    if args.auto_output_dir:
        tokens.append("auto_output_dir=true")
    if args.slurm:
        tokens.append(f"+slurm={args.slurm}")
    if args.trainer_module and args.trainer_module != "tools.train_net":
        warnings.append(
            "Hydra launcher wraps the standard trainer; custom project trainers need their own Hydra wrapper or plain launcher"
        )

    overrides = collect_lazy_overrides(args, hydra=True)
    tokens.extend(prefixed_override(item, hydra=True) for item in overrides)
    return tokens


def collect_lazy_overrides(args: argparse.Namespace, *, hydra: bool) -> List[str]:
    overrides: List[str] = list(args.override or [])
    if args.checkpoint:
        add_if_missing(overrides, f"train.init_checkpoint={args.checkpoint}")
    if args.output_dir:
        add_if_missing(overrides, f"train.output_dir={args.output_dir}")
    if args.device:
        add_if_missing(overrides, f"train.device={args.device}")
    if args.fast_dev_run:
        add_if_missing(overrides, f"train.fast_dev_run.enabled={bool_text(hydra)}")
    if args.amp:
        add_if_missing(overrides, f"train.amp.enabled={bool_text(hydra)}")
    if args.ema:
        add_if_missing(overrides, f"train.model_ema.enabled={bool_text(hydra)}")
    if args.ema_eval_only:
        add_if_missing(overrides, f"train.model_ema.enabled={bool_text(hydra)}")
        add_if_missing(overrides, f"train.model_ema.use_ema_weights_for_eval_only={bool_text(hydra)}")
    if args.wandb:
        add_if_missing(overrides, f"train.wandb.enabled={bool_text(hydra)}")
    if args.ddp_find_unused_parameters:
        add_if_missing(overrides, f"train.ddp.find_unused_parameters={bool_text(hydra)}")
    if args.ddp_fp16_compression:
        add_if_missing(overrides, f"train.ddp.fp16_compression={bool_text(hydra)}")
    if args.clip_grad_max_norm is not None:
        add_if_missing(overrides, f"train.clip_grad.enabled={bool_text(hydra)}")
        add_if_missing(overrides, f"train.clip_grad.params.max_norm={args.clip_grad_max_norm}")
    if args.clip_grad_norm_type is not None:
        add_if_missing(overrides, f"train.clip_grad.params.norm_type={args.clip_grad_norm_type}")
    return overrides


def collect_warnings(args: argparse.Namespace, overrides: Iterable[str]) -> List[str]:
    warnings: List[str] = []
    plain_keys = [item.lstrip("+").split("=", 1)[0] for item in overrides]
    if args.eval_only and "train.init_checkpoint" not in plain_keys and not args.checkpoint:
        warnings.append("eval-only usually needs train.init_checkpoint=<checkpoint>; omit only if the config sets it")
    if args.fast_dev_run and args.eval_only:
        warnings.append("train.fast_dev_run.enabled affects training; it is normally irrelevant for eval-only")
    if args.num_machines is not None and args.num_machines > 1 and not args.dist_url and args.launcher == "plain":
        warnings.append("multi-machine plain launch normally needs an explicit reachable --dist-url")
    if args.num_gpus == 0 and args.amp:
        warnings.append("AMP training is CUDA-oriented; --num-gpus 0 with --amp is probably invalid")
    if args.slurm and args.launcher != "hydra":
        warnings.append("Slurm selection only applies to --launcher hydra")
    return warnings


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a detrex train/eval/Hydra command without executing it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--launcher", choices=["plain", "hydra"], default="plain", help="command family to build")
    parser.add_argument("--entrypoint", choices=["module", "script"], default="module", help="emit python -m module or python script.py")
    parser.add_argument("--config-file", required=True, help="LazyConfig file path as it should appear in the generated command")
    parser.add_argument("--trainer-module", default="tools.train_net", help="plain launcher trainer module, e.g. projects.dino.train_net")
    parser.add_argument("--trainer-script", default=None, help="plain launcher script path when --entrypoint script is used")
    parser.add_argument("--hydra-module", default="tools.hydra_train_net", help="Hydra launcher module")
    parser.add_argument("--hydra-script", default=None, help="Hydra launcher script path when --entrypoint script is used")

    parser.add_argument("--num-gpus", type=positive_or_zero_int, default=None, help="GPUs per machine")
    parser.add_argument("--num-machines", type=positive_or_zero_int, default=None, help="number of machines")
    parser.add_argument("--machine-rank", type=positive_or_zero_int, default=None, help="rank of this machine")
    parser.add_argument("--dist-url", default=None, help="distributed initialization URL")
    parser.add_argument("--resume", action="store_true", help="resume from train.output_dir checkpoint state")
    parser.add_argument("--eval-only", action="store_true", help="build evaluation-only command")
    parser.add_argument("--auto-output-dir", action="store_true", help="Hydra: let the launcher append train.output_dir from run dir")
    parser.add_argument("--slurm", default=None, help="Hydra: Slurm config id to emit as +slurm=<id>")

    parser.add_argument("--override", action="append", default=[], metavar="KEY=VALUE", help="raw LazyConfig override; repeatable")
    parser.add_argument("--checkpoint", default=None, help="convenience alias for train.init_checkpoint")
    parser.add_argument("--output-dir", default=None, help="convenience alias for train.output_dir")
    parser.add_argument("--device", choices=["cuda", "cpu"], default=None, help="convenience alias for train.device")
    parser.add_argument("--fast-dev-run", action="store_true", help="add train.fast_dev_run.enabled=True")
    parser.add_argument("--amp", action="store_true", help="add train.amp.enabled=True")
    parser.add_argument("--ema", action="store_true", help="add train.model_ema.enabled=True")
    parser.add_argument("--ema-eval-only", action="store_true", help="add EMA eval-only config overrides")
    parser.add_argument("--wandb", action="store_true", help="add train.wandb.enabled=True")
    parser.add_argument("--ddp-find-unused-parameters", action="store_true", help="add train.ddp.find_unused_parameters=True")
    parser.add_argument("--ddp-fp16-compression", action="store_true", help="add train.ddp.fp16_compression=True")
    parser.add_argument("--clip-grad-max-norm", type=float, default=None, help="enable clipping and set train.clip_grad.params.max_norm")
    parser.add_argument("--clip-grad-norm-type", type=float, default=None, help="set train.clip_grad.params.norm_type")
    parser.add_argument("--multiline", action="store_true", help="print command with shell line continuations")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    preliminary_overrides = collect_lazy_overrides(args, hydra=args.launcher == "hydra")
    warnings = collect_warnings(args, preliminary_overrides)

    if args.launcher == "hydra":
        tokens = build_hydra_command(args, warnings)
    else:
        tokens = build_plain_command(args, warnings)

    for message in warnings:
        print(f"warning: {message}", file=sys.stderr)
    print(format_command(tokens, multiline=args.multiline))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
