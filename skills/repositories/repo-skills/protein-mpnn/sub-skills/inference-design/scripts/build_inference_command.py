#!/usr/bin/env python3
"""Print safe ProteinMPNN inference commands.

This helper intentionally does not import or run ProteinMPNN. It builds a shell-safe
`python protein_mpnn_run.py ...` command and catches common flag combinations that
would fail or surprise users.
"""

import argparse
import shlex
import sys
from pathlib import Path

VANILLA_MODELS = {"v_48_002", "v_48_010", "v_48_020", "v_48_030"}
SOLUBLE_MODELS = {"v_48_002", "v_48_010", "v_48_020", "v_48_030"}
CA_ONLY_MODELS = {"v_48_002", "v_48_010", "v_48_020"}


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("expected an integer >= 1")
    return parsed


def nonnegative_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("expected an integer >= 0")
    return parsed


def add_flag(command, flag, value=None):
    command.append(flag)
    if value is not None:
        command.append(str(value))


def validate_args(args):
    if bool(args.pdb_path) == bool(args.jsonl_path):
        raise SystemExit("Choose exactly one input style: --pdb-path or --jsonl-path.")
    if args.ca_only and args.use_soluble_model:
        raise SystemExit("Do not combine --ca-only and --use-soluble-model; CA-soluble weights are unavailable.")
    if not args.path_to_model_weights:
        if args.ca_only and args.model_name not in CA_ONLY_MODELS:
            raise SystemExit(f"CA-only model {args.model_name!r} is unavailable; choose one of {sorted(CA_ONLY_MODELS)}.")
        if args.use_soluble_model and args.model_name not in SOLUBLE_MODELS:
            raise SystemExit(f"Soluble model {args.model_name!r} is unavailable; choose one of {sorted(SOLUBLE_MODELS)}.")
        if not args.ca_only and not args.use_soluble_model and args.model_name not in VANILLA_MODELS:
            raise SystemExit(f"Vanilla model {args.model_name!r} is unavailable; choose one of {sorted(VANILLA_MODELS)}.")
    if args.score_only and args.mode in {"conditional", "conditional-backbone", "unconditional"}:
        raise SystemExit("Choose score-only or a probability-only mode, not both.")
    if args.path_to_fasta and not args.score_only:
        raise SystemExit("--path-to-fasta is for --score-only sequence scoring; add --score-only or remove the FASTA path.")
    if args.num_seq_per_target < args.batch_size:
        raise SystemExit("num-seq-per-target is smaller than batch-size; ProteinMPNN would run zero batches.")
    if args.num_seq_per_target % args.batch_size != 0:
        remainder = args.num_seq_per_target % args.batch_size
        print(
            f"# Warning: ProteinMPNN uses integer division; {remainder} requested sequence(s) will be dropped.",
            file=sys.stderr,
        )
    if args.path_to_model_weights and Path(args.path_to_model_weights).suffix == ".pt":
        raise SystemExit("--path-to-model-weights must be a folder containing model_name.pt, not a .pt file.")


def build_command(args):
    command = [args.python, args.runner]

    add_flag(command, "--out_folder", args.out_folder)

    if args.pdb_path:
        add_flag(command, "--pdb_path", args.pdb_path)
        if args.chains:
            add_flag(command, "--pdb_path_chains", args.chains)
    else:
        add_flag(command, "--jsonl_path", args.jsonl_path)
        optional_jsonl = [
            ("--chain_id_jsonl", args.chain_id_jsonl),
            ("--fixed_positions_jsonl", args.fixed_positions_jsonl),
            ("--tied_positions_jsonl", args.tied_positions_jsonl),
            ("--omit_AA_jsonl", args.omit_aa_jsonl),
            ("--bias_AA_jsonl", args.bias_aa_jsonl),
            ("--bias_by_res_jsonl", args.bias_by_res_jsonl),
            ("--pssm_jsonl", args.pssm_jsonl),
        ]
        for flag, value in optional_jsonl:
            if value:
                add_flag(command, flag, value)

    if args.path_to_model_weights:
        add_flag(command, "--path_to_model_weights", args.path_to_model_weights)
    if args.model_name != "v_48_020":
        add_flag(command, "--model_name", args.model_name)
    if args.ca_only:
        add_flag(command, "--ca_only")
    if args.use_soluble_model:
        add_flag(command, "--use_soluble_model")

    add_flag(command, "--num_seq_per_target", args.num_seq_per_target)
    add_flag(command, "--sampling_temp", args.sampling_temp)
    add_flag(command, "--seed", args.seed)
    add_flag(command, "--batch_size", args.batch_size)

    if args.backbone_noise != 0.0:
        add_flag(command, "--backbone_noise", args.backbone_noise)
    if args.max_length != 200000:
        add_flag(command, "--max_length", args.max_length)
    if args.omit_aas != "X":
        add_flag(command, "--omit_AAs", args.omit_aas)
    if args.suppress_print:
        add_flag(command, "--suppress_print", 1)

    if args.score_only:
        add_flag(command, "--score_only", 1)
    if args.path_to_fasta:
        add_flag(command, "--path_to_fasta", args.path_to_fasta)
    if args.save_score:
        add_flag(command, "--save_score", 1)
    if args.save_probs:
        add_flag(command, "--save_probs", 1)

    if args.mode == "conditional":
        add_flag(command, "--conditional_probs_only", 1)
    elif args.mode == "conditional-backbone":
        add_flag(command, "--conditional_probs_only", 1)
        add_flag(command, "--conditional_probs_only_backbone", 1)
    elif args.mode == "unconditional":
        add_flag(command, "--unconditional_probs_only", 1)

    if args.pssm_multi != 0.0:
        add_flag(command, "--pssm_multi", args.pssm_multi)
    if args.pssm_threshold != 0.0:
        add_flag(command, "--pssm_threshold", args.pssm_threshold)
    if args.pssm_log_odds_flag:
        add_flag(command, "--pssm_log_odds_flag", 1)
    if args.pssm_bias_flag:
        add_flag(command, "--pssm_bias_flag", 1)

    return command


def parse_args():
    parser = argparse.ArgumentParser(
        description="Print a shell-safe protein_mpnn_run.py command for common inference workflows.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--pdb-path", help="Single PDB path for direct PDB mode.")
    input_group.add_argument("--jsonl-path", help="Parsed PDB JSONL path for batch mode.")
    parser.add_argument("--chains", help="Designed chains for direct PDB mode, e.g. 'A B'.")
    parser.add_argument("--out-folder", required=True, help="ProteinMPNN output folder.")
    parser.add_argument("--runner", default="protein_mpnn_run.py", help="Path to protein_mpnn_run.py from the current working directory.")
    parser.add_argument("--python", default="python", help="Python executable token to print.")

    parser.add_argument("--model-name", default="v_48_020", help="Model basename without .pt.")
    parser.add_argument("--path-to-model-weights", help="Folder containing model_name.pt.")
    parser.add_argument("--ca-only", action="store_true", help="Use CA-only parser and weights.")
    parser.add_argument("--use-soluble-model", action="store_true", help="Use full-backbone soluble model weights.")

    parser.add_argument("--num-seq-per-target", type=positive_int, default=1, help="Requested sequences or scoring passes per target.")
    parser.add_argument("--batch-size", type=positive_int, default=1, help="Batch copies per inference batch.")
    parser.add_argument("--sampling-temp", default="0.1", help="One or more temperatures as one quoted string.")
    parser.add_argument("--seed", type=nonnegative_int, default=37, help="Nonzero deterministic seed; zero lets ProteinMPNN choose randomly.")
    parser.add_argument("--backbone-noise", type=float, default=0.0, help="Gaussian backbone noise standard deviation.")
    parser.add_argument("--max-length", type=positive_int, default=200000, help="Maximum parsed target length.")
    parser.add_argument("--omit-aas", default="X", help="Global amino acids to omit during sampling.")
    parser.add_argument("--suppress-print", action="store_true", help="Add --suppress_print 1.")

    parser.add_argument("--score-only", action="store_true", help="Score existing sequence/backbone pairs instead of designing.")
    parser.add_argument("--path-to-fasta", help="FASTA file for score-only custom sequence scoring.")
    parser.add_argument("--save-score", action="store_true", help="Save design-mode score arrays.")
    parser.add_argument("--save-probs", action="store_true", help="Save design-mode probability arrays.")
    parser.add_argument(
        "--mode",
        choices=["design", "conditional", "conditional-backbone", "unconditional"],
        default="design",
        help="Major output mode. Use --score-only separately for score-only mode.",
    )

    parser.add_argument("--chain-id-jsonl", help="Batch-mode designed/fixed chain JSONL.")
    parser.add_argument("--fixed-positions-jsonl", help="Batch-mode fixed positions JSONL.")
    parser.add_argument("--tied-positions-jsonl", help="Batch-mode tied positions JSONL.")
    parser.add_argument("--omit-aa-jsonl", help="Batch-mode per-position omitted amino acid JSONL.")
    parser.add_argument("--bias-aa-jsonl", help="Batch-mode global amino-acid bias JSONL.")
    parser.add_argument("--bias-by-res-jsonl", help="Batch-mode per-residue bias JSONL.")
    parser.add_argument("--pssm-jsonl", help="Batch-mode PSSM JSONL.")
    parser.add_argument("--pssm-multi", type=float, default=0.0, help="PSSM interpolation weight.")
    parser.add_argument("--pssm-threshold", type=float, default=0.0, help="PSSM log-odds threshold.")
    parser.add_argument("--pssm-log-odds-flag", action="store_true", help="Add --pssm_log_odds_flag 1.")
    parser.add_argument("--pssm-bias-flag", action="store_true", help="Add --pssm_bias_flag 1.")

    return parser.parse_args()


def main():
    args = parse_args()
    validate_args(args)
    command = build_command(args)
    print(" ".join(shlex.quote(part) for part in command))


if __name__ == "__main__":
    main()
