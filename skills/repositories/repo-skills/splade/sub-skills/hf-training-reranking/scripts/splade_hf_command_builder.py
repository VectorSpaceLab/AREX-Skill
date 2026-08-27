#!/usr/bin/env python3
"""Print safe SPLADE HF training/reranking command templates.

This helper intentionally does not import SPLADE, Transformers, Torch, or Hydra.
It only formats commands and emits validation warnings for common argument
mistakes. Review the printed commands before running them in a prepared SPLADE
environment.
"""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable, List, Optional, Sequence, Tuple

VALID_TRAINING_TYPES = {"saved_pkl", "pkl_dict", "trec", "json", "triplets"}
T5_RERANKERS = {"monoT5", "duoT5", "rankT5", "PairwisePrompt"}
PLACEHOLDER_MARKERS = ("<", ">", "??", "???", "PLACEHOLDER", "TODO")


def shell_join(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if part is not None and str(part) != "")


def hydra_override(key: str, value: object) -> str:
    return f"{key}={format_hydra_value(value)}"


def format_hydra_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def hydra_list_override(key: str, values: Sequence[str]) -> str:
    return f"{key}=[{','.join(str(value) for value in values)}]"


def add_if(overrides: List[str], key: str, value: object) -> None:
    if value is not None:
        overrides.append(hydra_override(key, value))


def add_bool_if(overrides: List[str], key: str, value: object) -> None:
    if value is not None:
        overrides.append(hydra_override(key, parse_bool(value)))


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected boolean, got {value!r}")


def has_placeholder(value: object) -> bool:
    if value is None:
        return False
    text = str(value)
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def warn_placeholders(warnings: List[str], pairs: Iterable[Tuple[str, object]]) -> None:
    for label, value in pairs:
        if has_placeholder(value):
            warnings.append(f"{label} still looks like a placeholder; replace it before running.")


def warn_training_data(args: argparse.Namespace, warnings: List[str], *, allow_triplets: bool) -> None:
    training_type = getattr(args, "training_data_type", None)
    if not training_type:
        warnings.append("No training_data_type supplied; rely on the selected Hydra config or add hf.data.training_data_type explicitly.")
        return

    if training_type not in VALID_TRAINING_TYPES:
        warnings.append(
            "training_data_type must be one of saved_pkl, pkl_dict, trec, json, or triplets."
        )
        return

    if training_type == "triplets":
        if not allow_triplets:
            warnings.append("triplets is intended for splade.hf_train; reranker training uses L2I/RerankingDataset inputs.")
        if args.n_negatives != 1:
            warnings.append("triplets requires n_negatives=1 in SPLADE's HF conversion logic.")
        if not args.training_data_path:
            warnings.append("triplets should provide training_data_path unless the Hydra data config resolves TRAIN_DATA_DIR/raw.tsv.")
        return

    missing = []
    for field_name, label in (
        ("training_data_path", "training_data_path"),
        ("document_path", "document_dir"),
        ("query_path", "query_dir"),
        ("qrels_path", "qrels_path"),
    ):
        if not getattr(args, field_name, None):
            missing.append(label)
    if missing:
        warnings.append(
            "Non-triplet training usually needs " + ", ".join(missing) + "; ensure the Hydra config supplies any omitted paths."
        )


def launcher(module: str, nproc_per_node: Optional[int]) -> List[str]:
    if nproc_per_node and nproc_per_node > 1:
        return ["torchrun", "--nproc_per_node", str(nproc_per_node), "-m", module]
    return ["python", "-m", module]


def build_config_parts(args: argparse.Namespace) -> List[str]:
    parts: List[str] = []
    if args.config_name:
        parts.append(f"--config-name={args.config_name}")
    return parts


def append_common_training_overrides(args: argparse.Namespace, overrides: List[str]) -> None:
    add_if(overrides, "config.checkpoint_dir", args.checkpoint_dir)
    add_if(overrides, "config.index_dir", getattr(args, "index_dir", None))
    add_if(overrides, "config.out_dir", args.out_dir)
    add_if(overrides, "hf.data.training_data_type", args.training_data_type)
    add_if(overrides, "hf.data.training_data_path", args.training_data_path)
    add_if(overrides, "hf.data.document_dir", args.document_path)
    add_if(overrides, "hf.data.query_dir", args.query_path)
    add_if(overrides, "hf.data.qrels_path", args.qrels_path)
    add_if(overrides, "hf.data.n_negatives", args.n_negatives)
    add_if(overrides, "hf.data.n_queries", args.n_queries)
    add_if(overrides, "config.train_batch_size", args.train_batch_size)
    add_if(overrides, "config.lr", args.learning_rate)
    add_bool_if(overrides, "config.fp16", args.fp16)
    add_bool_if(overrides, "hf.training.fp16", args.fp16)
    add_bool_if(overrides, "hf.training.resume_from_checkpoint", args.resume_from_checkpoint)


def command_hf_train(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    overrides: List[str] = []

    append_common_training_overrides(args, overrides)
    add_bool_if(overrides, "hf.model.dense", args.dense)
    add_bool_if(overrides, "hf.model.shared_weights", args.shared_weights)
    add_bool_if(overrides, "hf.model.splade_doc", args.splade_doc)
    add_if(overrides, "hf.model.dense_pooling", args.dense_pooling)
    add_if(overrides, "init_dict.model_type_or_dir", args.model_or_checkpoint)
    add_if(overrides, "init_dict.model_type_or_dir_q", args.model_q)
    add_if(overrides, "config.tokenizer_type", args.tokenizer)
    add_if(overrides, "hf.training.training_loss", args.training_loss)
    add_if(overrides, "hf.training.lexical_type", args.lexical_type)
    overrides.extend(args.extra_override or [])

    warn_training_data(args, warnings, allow_triplets=True)
    warn_placeholders(
        warnings,
        (
            ("checkpoint_dir", args.checkpoint_dir),
            ("index_dir", args.index_dir),
            ("out_dir", args.out_dir),
            ("training_data_path", args.training_data_path),
            ("document_path", args.document_path),
            ("query_path", args.query_path),
            ("qrels_path", args.qrels_path),
            ("model_or_checkpoint", args.model_or_checkpoint),
            ("model_q", args.model_q),
            ("tokenizer", args.tokenizer),
        ),
    )
    if args.dense and args.lexical_type and args.lexical_type != "none":
        warnings.append("lexical_type only affects sparse SPLADE training; dense DPR mode ignores sparse regularization behavior.")
    if args.nproc_per_node and args.nproc_per_node > 1 and args.dense:
        warnings.append("Dense/separate-encoder DDP runs may need hf.training.ddp_find_unused_parameters=true.")

    command = launcher("splade.hf_train", args.nproc_per_node) + build_config_parts(args) + overrides
    return [shell_join(command)], warnings


def command_train_reranker(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    overrides: List[str] = []

    append_common_training_overrides(args, overrides)
    add_if(overrides, "config.reranker_type", args.reranker_type)
    add_if(overrides, "init_dict.model_type_or_dir", args.model_or_checkpoint)
    add_if(overrides, "config.tokenizer_type", args.tokenizer)
    add_if(overrides, "hf.data.prompt_q", args.prompt_q)
    add_if(overrides, "hf.data.prompt_d", args.prompt_d)
    add_if(overrides, "hf.training.training_loss", args.training_loss)
    overrides.extend(args.extra_override or [])

    warn_training_data(args, warnings, allow_triplets=False)
    warn_placeholders(
        warnings,
        (
            ("checkpoint_dir", args.checkpoint_dir),
            ("out_dir", args.out_dir),
            ("training_data_path", args.training_data_path),
            ("document_path", args.document_path),
            ("query_path", args.query_path),
            ("qrels_path", args.qrels_path),
            ("model_or_checkpoint", args.model_or_checkpoint),
            ("tokenizer", args.tokenizer),
        ),
    )
    if args.reranker_type in T5_RERANKERS:
        warnings.append(f"{args.reranker_type} can be large; check GPU memory, local checkpoint availability, and batch size before running.")
    if args.reranker_type == "PairwisePrompt":
        warnings.append("PairwisePrompt reranking uses trust_remote_code=True at inference time; use only trusted models.")
    if args.nproc_per_node and args.nproc_per_node > 1:
        warnings.append("Reranker training is formatted with torchrun; validate DDP support for the selected model and collator.")

    command = launcher("splade.hf_train_reranker", args.nproc_per_node) + build_config_parts(args) + overrides
    return [shell_join(command)], warnings


def command_rerank(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    overrides: List[str] = []

    add_if(overrides, "config.out_dir", args.out_dir)
    add_if(overrides, "config.reranker_type", args.reranker_type)
    add_if(overrides, "config.top_k", args.top_k)
    add_if(overrides, "config.eval_batch_size", args.eval_batch_size)
    add_if(overrides, "config.max_length", args.max_length)
    add_bool_if(overrides, "config.return_token_type_ids", args.return_token_type_ids)
    add_if(overrides, "config.tokenizer_type", args.tokenizer)
    add_if(overrides, "init_dict.model_type_or_dir", args.model_or_checkpoint)
    add_if(overrides, "config.checkpoint", args.checkpoint)

    if args.path_run:
        overrides.append(hydra_list_override("data.path_run", args.path_run))
    if args.run_name:
        overrides.append(hydra_list_override("data.run_name", args.run_name))
    if args.document_path:
        overrides.append(hydra_list_override("data.document_dir", args.document_path))
    if args.query_path:
        overrides.append(hydra_list_override("data.query_dir", args.query_path))
    if args.qrels_path:
        overrides.append(hydra_list_override("data.EVAL_QREL_PATH", args.qrels_path))
    add_bool_if(overrides, "data.docs_ir_dataset", args.docs_ir_dataset)
    add_if(overrides, "ir_datasets.dataset_path", args.ir_datasets_home)
    overrides.extend(args.extra_override or [])

    list_lengths = {
        "path_run": len(args.path_run or []),
        "run_name": len(args.run_name or []),
        "document_path": len(args.document_path or []),
        "query_path": len(args.query_path or []),
        "qrels_path": len(args.qrels_path or []),
    }
    non_zero_lengths = {name: size for name, size in list_lengths.items() if size > 0}
    if non_zero_lengths and len(set(non_zero_lengths.values())) > 1:
        warnings.append("Rerank list overrides are zipped together; path_run, run_name, document_path, query_path, and qrels_path should have equal lengths.")
    if not args.path_run:
        warnings.append("No input run supplied; add --path-run or rely on the selected Hydra rerank_runs config.")
    if args.qrels_path:
        warnings.append("Providing qrels triggers evaluation after reranking; pytrec_eval must be installed.")
    if args.reranker_type in {"monoT5", "duoT5"}:
        warnings.append(f"{args.reranker_type} uses seq2seq reranking and may require pygaggle-compatible inputs plus substantial GPU memory.")
    if args.reranker_type == "PairwisePrompt":
        warnings.append("PairwisePrompt uses trust_remote_code=True and prompt-based pairwise evaluation; use trusted models only.")
    if args.reranker_type == "rankT5" and not (args.checkpoint or args.model_or_checkpoint):
        warnings.append("rankT5 reranking needs a trained checkpoint via --checkpoint or config.checkpoint_dir/model/pytorch_model.bin.")
    if args.docs_ir_dataset and not args.ir_datasets_home:
        warnings.append("docs_ir_dataset=true requires ir_datasets and a configured ir_datasets.dataset_path.")
    warn_placeholders(
        warnings,
        (
            ("out_dir", args.out_dir),
            ("model_or_checkpoint", args.model_or_checkpoint),
            ("checkpoint", args.checkpoint),
            ("tokenizer", args.tokenizer),
            *( ("path_run", value) for value in (args.path_run or []) ),
            *( ("document_path", value) for value in (args.document_path or []) ),
            *( ("query_path", value) for value in (args.query_path or []) ),
            *( ("qrels_path", value) for value in (args.qrels_path or []) ),
        ),
    )

    command = ["python", "-m", "splade.rerank"] + build_config_parts(args) + overrides
    return [shell_join(command)], warnings


def command_post_training(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    warnings: List[str] = [
        "These are handoff templates; use the hydra-pipelines sub-skill for full index/retrieve configuration details."
    ]
    warn_placeholders(
        warnings,
        (
            ("checkpoint_dir", args.checkpoint_dir),
            ("index_dir", args.index_dir),
            ("out_dir", args.out_dir),
        ),
    )
    if not args.checkpoint_dir:
        warnings.append("Missing checkpoint_dir; HF training saves the final model under config.checkpoint_dir/model.")
    if not args.index_dir:
        warnings.append("Missing index_dir; retrieval must point to the same index_dir created by splade.index.")
    if not args.out_dir:
        warnings.append("Missing out_dir for retrieval output.")

    common = build_config_parts(args)
    index_overrides = []
    retrieve_overrides = []
    add_if(index_overrides, "config.checkpoint_dir", args.checkpoint_dir)
    add_if(index_overrides, "config.index_dir", args.index_dir)
    add_if(retrieve_overrides, "config.checkpoint_dir", args.checkpoint_dir)
    add_if(retrieve_overrides, "config.index_dir", args.index_dir)
    add_if(retrieve_overrides, "config.out_dir", args.out_dir)
    index_overrides.extend(args.extra_override or [])
    retrieve_overrides.extend(args.extra_override or [])

    return [
        shell_join(["python", "-m", "splade.index"] + common + index_overrides),
        shell_join(["python", "-m", "splade.retrieve"] + common + retrieve_overrides),
    ], warnings


def add_config_arg(parser: argparse.ArgumentParser, default: Optional[str] = None) -> None:
    parser.add_argument("--config-name", default=default, help="Hydra config name to pass as --config-name=<name>.")


def add_training_args(parser: argparse.ArgumentParser, *, include_index: bool) -> None:
    parser.add_argument("--checkpoint-dir", help="Value for config.checkpoint_dir.")
    if include_index:
        parser.add_argument("--index-dir", help="Value for config.index_dir for post-training handoff.")
    parser.add_argument("--out-dir", help="Value for config.out_dir.")
    parser.add_argument("--training-data-type", choices=sorted(VALID_TRAINING_TYPES), help="HF training data type.")
    parser.add_argument("--training-data-path", help="Training score/run/hard-negative/triplet file path.")
    parser.add_argument("--document-path", help="Collection raw TSV path for hf.data.document_dir.")
    parser.add_argument("--query-path", help="Query raw TSV path for hf.data.query_dir.")
    parser.add_argument("--qrels-path", help="Qrels JSON path for hf.data.qrels_path.")
    parser.add_argument("--n-negatives", type=int, help="Negatives per query.")
    parser.add_argument("--n-queries", type=int, help="Limit number of training queries.")
    parser.add_argument("--train-batch-size", type=int, help="Value for config.train_batch_size.")
    parser.add_argument("--learning-rate", help="Value for config.lr.")
    parser.add_argument("--fp16", type=parse_bool, help="Set config.fp16 and hf.training.fp16.")
    parser.add_argument("--resume-from-checkpoint", type=parse_bool, help="Set hf.training.resume_from_checkpoint.")
    parser.add_argument("--nproc-per-node", type=int, default=1, help="Use torchrun when greater than 1; otherwise print python -m.")
    parser.add_argument("--extra-override", action="append", default=[], help="Raw Hydra override to append; may be repeated.")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print safe SPLADE HF training, reranking, and post-training handoff command templates."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    hf_train = subparsers.add_parser("hf-train", help="Print a splade.hf_train command.")
    add_config_arg(hf_train, "config_hf_splade_sigir23_32neg_distil")
    add_training_args(hf_train, include_index=True)
    hf_train.add_argument("--dense", type=parse_bool, help="Set hf.model.dense.")
    hf_train.add_argument("--shared-weights", type=parse_bool, help="Set hf.model.shared_weights.")
    hf_train.add_argument("--splade-doc", type=parse_bool, help="Set hf.model.splade_doc.")
    hf_train.add_argument("--dense-pooling", choices=["cls", "mean"], help="Set hf.model.dense_pooling.")
    hf_train.add_argument("--model-or-checkpoint", help="Set init_dict.model_type_or_dir.")
    hf_train.add_argument("--model-q", help="Set init_dict.model_type_or_dir_q for separate query encoder.")
    hf_train.add_argument("--tokenizer", help="Set config.tokenizer_type.")
    hf_train.add_argument("--training-loss", help="Set hf.training.training_loss.")
    hf_train.add_argument("--lexical-type", choices=["none", "document", "query", "both"], help="Set hf.training.lexical_type.")
    hf_train.set_defaults(func=command_hf_train)

    train_reranker = subparsers.add_parser("hf-train-reranker", help="Print a splade.hf_train_reranker command.")
    add_config_arg(train_reranker, "config_rerank_train_T5_3b")
    add_training_args(train_reranker, include_index=False)
    train_reranker.add_argument("--reranker-type", default="rankT5", help="Value for config.reranker_type.")
    train_reranker.add_argument("--model-or-checkpoint", help="Set init_dict.model_type_or_dir.")
    train_reranker.add_argument("--tokenizer", help="Set config.tokenizer_type.")
    train_reranker.add_argument("--prompt-q", help="Set hf.data.prompt_q, for example 'Query: {}\\n'.")
    train_reranker.add_argument("--prompt-d", help="Set hf.data.prompt_d, for example 'Document: {}\\n'.")
    train_reranker.add_argument("--training-loss", help="Set hf.training.training_loss.")
    train_reranker.set_defaults(func=command_train_reranker)

    rerank = subparsers.add_parser("rerank", help="Print a splade.rerank command.")
    add_config_arg(rerank, "config_reranker_toy")
    rerank.add_argument("--out-dir", help="Value for config.out_dir.")
    rerank.add_argument("--reranker-type", default="minilm", help="Value for config.reranker_type.")
    rerank.add_argument("--model-or-checkpoint", help="Value for init_dict.model_type_or_dir.")
    rerank.add_argument("--checkpoint", help="Explicit rankT5 checkpoint file via config.checkpoint.")
    rerank.add_argument("--tokenizer", help="Value for config.tokenizer_type.")
    rerank.add_argument("--path-run", nargs="+", help="One or more run files for data.path_run.")
    rerank.add_argument("--run-name", nargs="+", help="One or more names for data.run_name.")
    rerank.add_argument("--document-path", nargs="+", help="One or more collection TSV paths or ir_datasets ids.")
    rerank.add_argument("--query-path", nargs="+", help="One or more query TSV paths.")
    rerank.add_argument("--qrels-path", nargs="+", help="One or more qrel paths; truthy values trigger evaluation.")
    rerank.add_argument("--top-k", type=int, help="Value for config.top_k.")
    rerank.add_argument("--eval-batch-size", type=int, help="Value for config.eval_batch_size.")
    rerank.add_argument("--max-length", type=int, help="Value for config.max_length.")
    rerank.add_argument("--return-token-type-ids", type=parse_bool, help="Value for config.return_token_type_ids.")
    rerank.add_argument("--docs-ir-dataset", type=parse_bool, help="Set data.docs_ir_dataset.")
    rerank.add_argument("--ir-datasets-home", help="Set ir_datasets.dataset_path when docs_ir_dataset=true.")
    rerank.add_argument("--extra-override", action="append", default=[], help="Raw Hydra override to append; may be repeated.")
    rerank.set_defaults(func=command_rerank)

    handoff = subparsers.add_parser("post-training", help="Print splade.index and splade.retrieve handoff commands.")
    add_config_arg(handoff, "config_hf_splade_sigir23_32neg_distil")
    handoff.add_argument("--checkpoint-dir", help="HF training checkpoint root; final model is expected under checkpoint_dir/model.")
    handoff.add_argument("--index-dir", help="Index output/input directory for classic SPLADE indexing/retrieval.")
    handoff.add_argument("--out-dir", help="Retrieval output directory.")
    handoff.add_argument("--extra-override", action="append", default=[], help="Raw Hydra override to append to both commands; may be repeated.")
    handoff.set_defaults(func=command_post_training)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    commands, warnings = args.func(args)

    print("# SPLADE HF command builder")
    print("# This helper only prints command templates; it does not train, rerank, import SPLADE, or download models.")
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")
    print("\nCommands:")
    for command in commands:
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
