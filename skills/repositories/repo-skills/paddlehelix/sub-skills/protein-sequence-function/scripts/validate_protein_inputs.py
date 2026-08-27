#!/usr/bin/env python3
"""Safely validate PaddleHelix protein sequence/function inputs.

This helper performs local parsing only. It does not download data, import
Paddle/PGL, create checkpoints, train, evaluate, or mutate user files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

VOCAB = {
    "<pad>": 0,
    "<mask>": 1,
    "<cls>": 2,
    "<sep>": 3,
    "<unk>": 4,
    "A": 5,
    "B": 6,
    "C": 7,
    "D": 8,
    "E": 9,
    "F": 10,
    "G": 11,
    "H": 12,
    "I": 13,
    "K": 14,
    "L": 15,
    "M": 16,
    "N": 17,
    "O": 18,
    "P": 19,
    "Q": 20,
    "R": 21,
    "S": 22,
    "T": 23,
    "U": 24,
    "V": 25,
    "W": 26,
    "X": 27,
    "Y": 28,
    "Z": 29,
}

SUPPORTED_TASKS = {"pretrain", "seq_classification", "classification", "regression"}
SUPPORTED_MODELS = {"transformer", "lstm", "resnet"}
PATH_OPTIONS = {
    "train_data": "directory",
    "valid_data": "directory",
    "eval_data": "directory",
    "predict_data": "file",
    "predict_model": "file",
    "eval_model": "file",
    "init_model": "file",
    "model_name": "file",
    "label_data_path": "file",
    "test_file": "file",
    "train_file": "file",
    "valid_file": "file",
    "protein_chain_graphs": "directory",
}
FUNCTION_WORKFLOWS = {"function-train", "function-test"}


def token_ids(sequence: str) -> List[int]:
    return [VOCAB["<cls>"]] + [VOCAB.get(char, VOCAB["<unk>"]) for char in sequence] + [VOCAB["<sep>"]]


def sequence_issues(sequence: str) -> List[str]:
    issues = []
    if not sequence:
        issues.append("sequence is empty")
    if sequence != sequence.strip():
        issues.append("sequence has leading or trailing whitespace")
    if any(char.isspace() for char in sequence):
        issues.append("sequence contains interior whitespace")
    lowercase = sorted({char for char in sequence if char.isalpha() and char.islower()})
    if lowercase:
        issues.append("lowercase letters map to <unk>: " + "".join(lowercase))
    unknown = sorted({char for char in sequence if char not in VOCAB})
    if unknown:
        display = " ".join(repr(char) for char in unknown)
        issues.append("characters outside PaddleHelix ProteinTokenizer vocab map to <unk>: " + display)
    if len(sequence) > 3000:
        issues.append("sequence length exceeds 3000, the source positional embedding limit for transformer/resnet encoders")
    return issues


def read_fasta_or_plain(path: Path) -> Tuple[List[Tuple[str, str]], List[str]]:
    records = []
    warnings = []
    current_name = None  # type: Optional[str]
    current_chunks = []  # type: List[str]
    plain_index = 1
    seen_fasta = False

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            seen_fasta = True
            if current_name is not None:
                records.append((current_name, "".join(current_chunks)))
            current_name = line[1:].strip() or f"record_{len(records) + 1}"
            current_chunks = []
            continue
        if current_name is None:
            records.append((f"plain_{plain_index}", line))
            plain_index += 1
        else:
            current_chunks.append(line)
            if seen_fasta and any(char.isspace() for char in raw_line.strip()):
                warnings.append(f"{path}: line {line_number} is inside a FASTA record but contains whitespace")

    if current_name is not None:
        records.append((current_name, "".join(current_chunks)))
    return records, warnings


def check_path(value: str, expected: str) -> Optional[str]:
    path = Path(value).expanduser()
    if expected == "file" and not path.is_file():
        return f"expected an existing file: {value}"
    if expected == "directory" and not path.is_dir():
        return f"expected an existing directory: {value}"
    return None


def load_config(path: Path) -> Tuple[Dict[str, object], List[str], List[str]]:
    errors = []
    warnings = []
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {}, [f"could not read config: {exc}"], warnings
    except json.JSONDecodeError as exc:
        return {}, [f"config is not valid JSON: {exc}"], warnings

    if not isinstance(config, dict):
        return {}, ["config root must be a JSON object"], warnings

    task = config.get("task")
    model_type = config.get("model_type", "transformer")
    if task not in SUPPORTED_TASKS:
        errors.append(f"unsupported or missing task {task!r}; expected one of {sorted(SUPPORTED_TASKS)}")
    if model_type not in SUPPORTED_MODELS:
        errors.append(f"unsupported model_type {model_type!r}; expected one of {sorted(SUPPORTED_MODELS)}")
    if "layer_num" in config and "n_layers" not in config:
        warnings.append("config uses layer_num; current model code reads n_layers")
    if "head_num" in config and "n_heads" not in config:
        warnings.append("config uses head_num; current transformer code reads n_heads")
    if task in {"seq_classification", "classification"} and "class_num" not in config:
        warnings.append("classification task has no class_num; source code will use its default")
    if task in {"seq_classification", "classification", "regression"} and "label_name" not in config:
        warnings.append("supervised task has no label_name; dataloader will use labels by default")
    return config, errors, warnings


def emit_section(title: str, lines: Iterable[str]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for line in lines:
        print(line)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", choices=["sequence", "tape-train", "tape-eval", "tape-predict", "function-train", "function-test"], default="sequence")
    parser.add_argument("--sequence", action="append", default=[], help="Protein sequence string. May be supplied multiple times.")
    parser.add_argument("--fasta", action="append", default=[], help="FASTA or plain-sequence file to validate. May be supplied multiple times.")
    parser.add_argument("--config", help="TAPE model_config JSON to validate.")
    parser.add_argument("--json-config", action="append", default=[], help="Additional JSON/config file to check for existence and valid JSON. May be supplied multiple times.")
    parser.add_argument("--show-token-ids", action="store_true", default=True, help="Print token IDs for each sequence. Enabled by default.")
    parser.add_argument("--no-token-ids", action="store_false", dest="show_token_ids", help="Suppress token ID output.")
    parser.add_argument("--train-data")
    parser.add_argument("--valid-data")
    parser.add_argument("--eval-data")
    parser.add_argument("--predict-data")
    parser.add_argument("--predict-model")
    parser.add_argument("--eval-model")
    parser.add_argument("--init-model")
    parser.add_argument("--model-name", help="Function-prediction saved model checkpoint path.")
    parser.add_argument("--label-data-path", help="Function-prediction label .npz path.")
    parser.add_argument("--test-file", help="Function-prediction test chain-list file.")
    parser.add_argument("--train-file", help="Function-prediction train chain-list file.")
    parser.add_argument("--valid-file", help="Function-prediction validation chain-list file.")
    parser.add_argument("--protein-chain-graphs", help="Function-prediction chain graph parent directory.")
    parser.add_argument("--cmap-thresh", type=int, default=10, help="Function-prediction contact-map threshold subdirectory expected under --protein-chain-graphs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = []
    warnings = []
    records = []  # type: List[Tuple[str, str]]
    json_notes = []  # type: List[str]

    for index, sequence in enumerate(args.sequence, start=1):
        records.append((f"sequence_{index}", sequence))

    for fasta_value in args.fasta:
        fasta_path = Path(fasta_value).expanduser()
        if not fasta_path.is_file():
            errors.append(f"expected an existing FASTA/plain sequence file: {fasta_value}")
            continue
        parsed_records, parse_warnings = read_fasta_or_plain(fasta_path)
        if not parsed_records:
            errors.append(f"no protein sequences found in FASTA/plain sequence file: {fasta_value}")
        records.extend(parsed_records)
        warnings.extend(parse_warnings)

    if args.predict_data:
        predict_path = Path(args.predict_data).expanduser()
        if predict_path.is_file():
            parsed_records, parse_warnings = read_fasta_or_plain(predict_path)
            if not parsed_records:
                warnings.append(f"predict_data contains no non-empty sequence records: {args.predict_data}")
            records.extend(parsed_records)
            warnings.extend(parse_warnings)

    for name, sequence in records:
        for issue in sequence_issues(sequence):
            warnings.append(f"{name}: {issue}")

    if args.config:
        config, config_errors, config_warnings = load_config(Path(args.config).expanduser())
        errors.extend(config_errors)
        warnings.extend(config_warnings)
        if config:
            emit_section("Config", [f"task={config.get('task')!r}", f"model_type={config.get('model_type', 'transformer')!r}"])

    for json_value in args.json_config:
        json_path = Path(json_value).expanduser()
        try:
            json_data = json.loads(json_path.read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"json_config: could not read {json_value}: {exc}")
        except json.JSONDecodeError as exc:
            errors.append(f"json_config: {json_value} is not valid JSON: {exc}")
        else:
            root_type = type(json_data).__name__
            json_notes.append(f"{json_value}: valid JSON root type {root_type}")

    if json_notes:
        emit_section("Optional JSON", json_notes)

    arg_map = {
        "train_data": args.train_data,
        "valid_data": args.valid_data,
        "eval_data": args.eval_data,
        "predict_data": args.predict_data,
        "predict_model": args.predict_model,
        "eval_model": args.eval_model,
        "init_model": args.init_model,
        "model_name": args.model_name,
        "label_data_path": args.label_data_path,
        "test_file": args.test_file,
        "train_file": args.train_file,
        "valid_file": args.valid_file,
        "protein_chain_graphs": args.protein_chain_graphs,
    }
    for key, value in arg_map.items():
        if not value:
            continue
        path_error = check_path(value, PATH_OPTIONS[key])
        if path_error:
            errors.append(f"{key}: {path_error}")

    if args.workflow in FUNCTION_WORKFLOWS:
        if args.label_data_path and Path(args.label_data_path).expanduser().suffix != ".npz":
            warnings.append("label_data_path is normally a .npz GO-label mapping for DeepFRI/ProteinSIGN/PTHL")
        for chain_key in ("train_file", "valid_file", "test_file"):
            chain_value = arg_map[chain_key]
            if chain_value and Path(chain_value).expanduser().is_file():
                try:
                    has_record = any(line.strip() for line in Path(chain_value).expanduser().read_text(encoding="utf-8").splitlines())
                except OSError as exc:
                    errors.append(f"{chain_key}: could not read chain-list file: {exc}")
                else:
                    if not has_record:
                        warnings.append(f"{chain_key}: chain-list file has no non-empty chain ids")
        if args.protein_chain_graphs and Path(args.protein_chain_graphs).expanduser().is_dir():
            graph_parent = Path(args.protein_chain_graphs).expanduser()
            threshold_dirs = list(dict.fromkeys([graph_parent / str(args.cmap_thresh), graph_parent / f"{args.cmap_thresh:02d}"]))
            if not any(path.is_dir() for path in threshold_dirs):
                expected = " or ".join(str(path) for path in threshold_dirs)
                errors.append(
                    "protein_chain_graphs: expected a contact-threshold subdirectory "
                    f"{expected}; app datasets join --protein-chain-graphs with --cmap-thresh, "
                    "while preprocessing may write zero-padded names"
                )

    if args.workflow == "tape-train":
        for required in ("train_data", "valid_data"):
            if not arg_map[required]:
                errors.append(f"{required}: required for tape-train workflow")
        if not args.config:
            errors.append("config: required for tape-train workflow")
    elif args.workflow == "tape-eval":
        for required in ("eval_data", "eval_model"):
            if not arg_map[required]:
                errors.append(f"{required}: required for tape-eval workflow")
        if not args.config:
            errors.append("config: required for tape-eval workflow")
    elif args.workflow == "tape-predict":
        if not records:
            errors.append("sequence/fasta/predict_data: at least one sequence source is required for tape-predict validation")
        for required in ("predict_model",):
            if not arg_map[required]:
                errors.append(f"{required}: required for tape-predict workflow")
        if not args.config:
            errors.append("config: required for tape-predict workflow")
    elif args.workflow == "function-train":
        for required in ("train_file", "valid_file", "protein_chain_graphs", "label_data_path"):
            if not arg_map[required]:
                errors.append(f"{required}: required for function-train workflow")
    elif args.workflow == "function-test":
        for required in ("model_name", "label_data_path", "test_file", "protein_chain_graphs"):
            if not arg_map[required]:
                errors.append(f"{required}: required for function-test workflow")

    if records:
        lines = []
        for name, sequence in records:
            ids = token_ids(sequence)
            unknown_count = ids.count(VOCAB["<unk>"])
            summary = f"{name}: length={len(sequence)} token_count_with_specials={len(ids)} unknown_count={unknown_count}"
            if args.show_token_ids:
                summary += f" token_ids={ids}"
            lines.append(summary)
        emit_section("Sequences", lines)

    if warnings:
        emit_section("Warnings", warnings)
    if errors:
        emit_section("Errors", errors)
        return 2

    print("\nValidation passed: no blocking issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
