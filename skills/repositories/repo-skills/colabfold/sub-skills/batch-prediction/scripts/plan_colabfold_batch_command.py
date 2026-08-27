#!/usr/bin/env python3
"""Plan safe colabfold_batch commands without running prediction or downloads."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

MODEL_TYPES = {
    "auto",
    "alphafold2",
    "alphafold2_ptm",
    "alphafold2_multimer_v1",
    "alphafold2_multimer_v2",
    "alphafold2_multimer_v3",
    "deepfold_v1",
}

MSA_MODES = {
    "mmseqs2_uniref_env",
    "mmseqs2_uniref_env_envpair",
    "mmseqs2_uniref",
    "single_sequence",
}

PAIR_MODES = {"unpaired", "paired", "unpaired_paired"}
PAIR_STRATEGIES = {"complete", "greedy"}
RANKS = {"auto", "plddt", "ptm", "iptm", "multimer"}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def readable_path(value: str) -> str:
    path = Path(value).expanduser()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"path does not exist: {value}")
    return value


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def add_common_options(command: list[str], args: argparse.Namespace, *, prediction_step: bool) -> list[str]:
    if args.msa_mode != "mmseqs2_uniref_env":
        command.extend(["--msa-mode", args.msa_mode])
    if args.complex:
        command.extend(["--pair-mode", args.pair_mode, "--pair-strategy", args.pair_strategy])
    if args.templates:
        command.append("--templates")
        if args.custom_template_path:
            command.extend(["--custom-template-path", args.custom_template_path])
        if args.custom_template_cache_path:
            command.extend(["--custom-template-cache-path", args.custom_template_cache_path])
        if args.pdb_hit_file:
            command.extend(["--pdb-hit-file", args.pdb_hit_file])
        if args.local_pdb_path:
            command.extend(["--local-pdb-path", args.local_pdb_path])
        if args.max_template_date:
            command.extend(["--max-template-date", args.max_template_date])
        if args.max_template_hits != 20:
            command.extend(["--max-template-hits", str(args.max_template_hits)])
    if args.host_url:
        command.extend(["--host-url", args.host_url])
    if args.jobname_prefix:
        command.extend(["--jobname-prefix", args.jobname_prefix])
    if args.sort_queries_by != "length":
        command.extend(["--sort-queries-by", args.sort_queries_by])
    if prediction_step:
        command.extend(["--model-type", args.model_type])
        command.extend(["--num-models", str(args.num_models)])
        if args.num_recycle is not None:
            command.extend(["--num-recycle", str(args.num_recycle)])
        if args.recycle_early_stop_tolerance is not None:
            command.extend(["--recycle-early-stop-tolerance", str(args.recycle_early_stop_tolerance)])
        if args.num_ensemble != 1:
            command.extend(["--num-ensemble", str(args.num_ensemble)])
        if args.num_seeds != 1:
            command.extend(["--num-seeds", str(args.num_seeds)])
        if args.random_seed != 0:
            command.extend(["--random-seed", str(args.random_seed)])
        if args.rank != "auto":
            command.extend(["--rank", args.rank])
        if args.max_msa:
            command.extend(["--max-msa", args.max_msa])
        else:
            if args.max_seq is not None:
                command.extend(["--max-seq", str(args.max_seq)])
            if args.max_extra_seq is not None:
                command.extend(["--max-extra-seq", str(args.max_extra_seq)])
        if args.model_order != "1,2,3,4,5":
            command.extend(["--model-order", args.model_order])
        if args.use_dropout:
            command.append("--use-dropout")
        if args.disable_cluster_profile:
            command.append("--disable-cluster-profile")
        if args.calc_extra_ptm:
            command.append("--calc-extra-ptm")
        if args.no_use_probs_extra:
            command.append("--no-use-probs-extra")
        if args.data:
            command.extend(["--data", args.data])
        if args.use_pallas:
            command.extend(["--use-pallas", "true"])
        if args.disable_unified_memory:
            command.append("--disable-unified-memory")
        if args.recompile_padding != 10:
            command.extend(["--recompile-padding", str(args.recompile_padding)])
        if args.zip:
            command.append("--zip")
        if args.overwrite_existing_results:
            command.append("--overwrite-existing-results")
        if args.debug_logging:
            command.append("--debug-logging")
    return command


def build_plan(args: argparse.Namespace) -> dict[str, object]:
    input_path = str(Path(args.input).expanduser()) if args.absolute else args.input
    results_path = str(Path(args.results).expanduser()) if args.absolute else args.results

    commands: list[dict[str, str]] = []
    if args.af3_json:
        command = ["colabfold_batch", input_path, results_path, "--af3-json"]
        add_common_options(command, args, prediction_step=False)
        commands.append({"step": "af3-json-only", "command": quote_command(command)})
    elif args.two_step:
        msa_command = ["colabfold_batch", input_path, results_path, "--msa-only"]
        add_common_options(msa_command, args, prediction_step=False)
        commands.append({"step": "msa-only", "command": quote_command(msa_command)})
        pred_command = ["colabfold_batch", input_path, results_path]
        add_common_options(pred_command, args, prediction_step=True)
        commands.append({"step": "prediction", "command": quote_command(pred_command)})
    else:
        command = ["colabfold_batch", input_path, results_path]
        add_common_options(command, args, prediction_step=True)
        commands.append({"step": "one-step-prediction", "command": quote_command(command)})

    inferred_model = args.model_type
    if inferred_model == "auto":
        inferred_model = "alphafold2_multimer_v3" if args.complex else "alphafold2_ptm"

    notes = []
    if args.af3_json:
        notes.append("AF3 JSON mode returns before structure prediction; expect JSON and A3M, not PDB outputs.")
    elif args.two_step:
        notes.append("The MSA-only step avoids AlphaFold parameter download because it sets num_models=0.")
        notes.append("Run the prediction step in the same output directory to reuse generated MSA/template intermediates.")
    else:
        notes.append("One-step prediction may query an MSA server and may download model parameters if missing.")

    if args.msa_mode != "single_sequence" and not args.af3_json:
        notes.append("If input lacks A3M data, MSA generation may use a server unless precomputed A3M inputs are supplied.")
    if args.templates:
        notes.append("Template options require --templates; custom template and PDB-hit workflows are mutually exclusive.")
    if args.use_pallas:
        notes.append("--use-pallas requires a compatible JAX/Triton stack and bfloat16-enabled prediction.")
    if args.complex:
        notes.append("Complex planning assumes the input encodes multiple chains in a single query.")

    checks = ["colabfold_batch --help"]
    if args.af3_json:
        checks.extend([
            "Confirm MSA server or precomputed A3M policy before JSON export.",
            "Inspect generated JSON and A3M files after export.",
        ])
    else:
        checks.extend([
            "Confirm colabfold[alphafold] is installed before prediction steps.",
            "Confirm JAX backend and GPU/CPU resources before running prediction.",
            "Confirm AlphaFold parameters exist or large downloads are approved.",
            "Inspect log.txt and config.json after the first small run.",
        ])

    return {
        "inferred_model_type": inferred_model,
        "commands": commands,
        "notes": notes,
        "preflight_checks": checks,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe colabfold_batch command plans without running ColabFold.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", help="Input FASTA/CSV/A3M file or input directory.")
    parser.add_argument("results", help="Planned ColabFold output directory.")
    parser.add_argument("--complex", action="store_true", help="Plan as a multichain/complex prediction.")
    parser.add_argument("--two-step", action="store_true", help="Plan separate MSA-only and prediction commands.")
    parser.add_argument("--af3-json", action="store_true", help="Plan AF3 JSON export only.")
    parser.add_argument("--model-type", choices=sorted(MODEL_TYPES), default="auto")
    parser.add_argument("--num-models", type=positive_int, choices=range(1, 6), default=5)
    parser.add_argument("--num-recycle", type=nonnegative_int, default=None)
    parser.add_argument("--num-seeds", type=positive_int, default=1)
    parser.add_argument("--random-seed", type=nonnegative_int, default=0)
    parser.add_argument("--rank", choices=sorted(RANKS), default="auto")
    parser.add_argument("--msa-mode", choices=sorted(MSA_MODES), default="mmseqs2_uniref_env")
    parser.add_argument("--pair-mode", choices=sorted(PAIR_MODES), default="unpaired_paired")
    parser.add_argument("--pair-strategy", choices=sorted(PAIR_STRATEGIES), default="greedy")
    parser.add_argument("--templates", action="store_true")
    parser.add_argument("--custom-template-path")
    parser.add_argument("--custom-template-cache-path")
    parser.add_argument("--pdb-hit-file")
    parser.add_argument("--local-pdb-path")
    parser.add_argument("--max-template-date")
    parser.add_argument("--max-template-hits", type=positive_int, default=20)
    parser.add_argument("--recycle-early-stop-tolerance", type=float, default=None)
    parser.add_argument("--num-ensemble", type=positive_int, default=1)
    parser.add_argument("--model-order", default="1,2,3,4,5")
    parser.add_argument("--max-seq", type=positive_int, default=None)
    parser.add_argument("--max-extra-seq", type=positive_int, default=None)
    parser.add_argument("--max-msa", help="Prediction MSA depth as max_seq:max_extra_seq.")
    parser.add_argument("--use-dropout", action="store_true")
    parser.add_argument("--disable-cluster-profile", action="store_true")
    parser.add_argument("--calc-extra-ptm", action="store_true")
    parser.add_argument("--no-use-probs-extra", action="store_true")
    parser.add_argument("--data", help="Existing AlphaFold parameter data directory.")
    parser.add_argument("--host-url", help="Non-default MSA server URL.")
    parser.add_argument("--jobname-prefix")
    parser.add_argument("--sort-queries-by", choices=["none", "length", "msa_depth", "random"], default="length")
    parser.add_argument("--use-pallas", action="store_true")
    parser.add_argument("--disable-unified-memory", action="store_true")
    parser.add_argument("--recompile-padding", type=nonnegative_int, default=10)
    parser.add_argument("--zip", action="store_true")
    parser.add_argument("--overwrite-existing-results", action="store_true")
    parser.add_argument("--debug-logging", action="store_true")
    parser.add_argument("--absolute", action="store_true", help="Expand input/results to absolute user paths in printed commands.")
    parser.add_argument("--check-input-exists", action="store_true", help="Fail if the input path does not exist.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    args = parser.parse_args(argv)

    if args.two_step and args.af3_json:
        parser.error("--two-step and --af3-json are mutually exclusive")
    if not args.templates and (args.custom_template_path or args.custom_template_cache_path or args.max_template_date or args.pdb_hit_file or args.local_pdb_path):
        parser.error("template path/date options require --templates")
    if args.custom_template_path and args.pdb_hit_file:
        parser.error("--custom-template-path and --pdb-hit-file are mutually exclusive")
    if args.local_pdb_path and not args.pdb_hit_file:
        parser.error("--local-pdb-path is only useful with --pdb-hit-file")
    if args.max_msa:
        parts = args.max_msa.split(":")
        if len(parts) != 2 or not all(part.isdigit() and int(part) >= 0 for part in parts):
            parser.error("--max-msa must have the form max_seq:max_extra_seq with non-negative integers")
    if args.model_order:
        order_parts = args.model_order.split(",")
        if not order_parts or any(part not in {"1", "2", "3", "4", "5"} for part in order_parts):
            parser.error("--model-order must be a comma-separated subset/order of model numbers 1..5")
    if args.check_input_exists:
        readable_path(args.input)
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    plan = build_plan(args)
    if args.json:
        print(json.dumps(plan, indent=2))
    else:
        print(f"Inferred model type: {plan['inferred_model_type']}")
        print("\nCommands:")
        for item in plan["commands"]:
            print(f"- {item['step']}: {item['command']}")
        print("\nNotes:")
        for note in plan["notes"]:
            print(f"- {note}")
        print("\nPreflight checks:")
        for check in plan["preflight_checks"]:
            print(f"- {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
