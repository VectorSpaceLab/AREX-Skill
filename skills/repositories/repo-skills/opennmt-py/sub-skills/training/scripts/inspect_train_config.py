#!/usr/bin/env python3
"""Sanity-check OpenNMT-py YAML training configs.

This script intentionally checks config shape and known parser constraints. It
cannot prove that a model fits memory, that optional GPU packages are installed,
or that training will converge.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency diagnostic
    print("ERROR [missing-pyyaml] Install PyYAML to read OpenNMT-py YAML configs.", file=sys.stderr)
    raise SystemExit(2) from exc


@dataclass
class Message:
    level: str
    code: str
    text: str


class Reporter:
    def __init__(self) -> None:
        self.messages: list[Message] = []

    def error(self, code: str, text: str) -> None:
        self.messages.append(Message("ERROR", code, text))

    def warn(self, code: str, text: str) -> None:
        self.messages.append(Message("WARN", code, text))

    def note(self, code: str, text: str) -> None:
        self.messages.append(Message("NOTE", code, text))

    def count(self, level: str) -> int:
        return sum(1 for msg in self.messages if msg.level == level)

    def emit(self) -> None:
        order = {"ERROR": 0, "WARN": 1, "NOTE": 2}
        for msg in sorted(self.messages, key=lambda m: (order[m.level], m.code, m.text)):
            print(f"{msg.level} [{msg.code}] {msg.text}")
        print(
            "Summary: "
            f"{self.count('ERROR')} error(s), "
            f"{self.count('WARN')} warning(s), "
            f"{self.count('NOTE')} note(s)."
        )


def is_missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def boolish(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False
    return default


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if "," in text:
            return [item.strip() for item in text.split(",") if item.strip()]
        return text.split()
    return [value]


def as_str_list(value: Any) -> list[str]:
    return [str(item) for item in as_list(value) if str(item) != ""]


def to_int(value: Any, *, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def to_float(value: Any, *, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def parse_int_list(value: Any, reporter: Reporter, code: str, field: str) -> list[int]:
    values: list[int] = []
    for item in as_list(value):
        parsed = to_int(item)
        if parsed is None:
            reporter.error(code, f"{field} contains a non-integer value: {item!r}.")
        else:
            values.append(parsed)
    return values


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise TypeError("top-level YAML document must be a mapping")
    return loaded


def is_uri(value: str) -> bool:
    return "://" in value or value.startswith("s3://")


def check_path_exists(
    field: str,
    value: Any,
    *,
    base_dir: Path,
    reporter: Reporter,
    required: bool = True,
) -> None:
    if is_missing(value):
        return
    text = str(value)
    if is_uri(text):
        reporter.note("path-uri-skipped", f"{field} uses a URI; local existence was not checked.")
        return
    path = Path(text).expanduser()
    resolved = path if path.is_absolute() else base_dir / path
    if not resolved.exists():
        level = reporter.error if required else reporter.warn
        level("path-missing", f"{field} does not exist from the selected base directory: {text}")


def check_required_training_fields(cfg: dict[str, Any], reporter: Reporter) -> None:
    for field in ["data", "src_vocab", "save_model", "train_steps", "valid_steps"]:
        if is_missing(cfg.get(field)):
            reporter.error("required-field", f"Missing required training field `{field}`.")

    share_vocab = boolish(cfg.get("share_vocab"), False)
    model_task = str(cfg.get("model_task", "seq2seq")).lower()
    if model_task == "lm":
        if not share_vocab:
            reporter.error("lm-share-vocab", "`model_task: lm` requires `share_vocab: true`.")
        if not is_missing(cfg.get("tgt_vocab")):
            reporter.warn("lm-tgt-vocab", "Language-model configs usually omit `tgt_vocab`; confirm a separate target vocab is intended.")
    elif not share_vocab and is_missing(cfg.get("tgt_vocab")):
        reporter.error("required-field", "Missing `tgt_vocab`; set it or use `share_vocab: true`.")

    train_steps = to_int(cfg.get("train_steps"))
    valid_steps = to_int(cfg.get("valid_steps"))
    single_pass = boolish(cfg.get("single_pass"), False)
    if train_steps is None and not is_missing(cfg.get("train_steps")):
        reporter.error("train-steps", "`train_steps` must be an integer.")
    elif train_steps is not None and train_steps <= 0 and not single_pass:
        reporter.error("train-steps", "`train_steps` must be positive unless `single_pass: true` is intentional.")
    elif train_steps is not None and single_pass and train_steps > 0:
        reporter.note("single-pass", "`single_pass: true` makes OpenNMT-py ignore positive `train_steps` and run one corpus pass.")

    if valid_steps is None and not is_missing(cfg.get("valid_steps")):
        reporter.error("valid-steps", "`valid_steps` must be an integer.")
    elif valid_steps is not None and valid_steps <= 0:
        reporter.error("valid-steps", "`valid_steps` must be a positive integer.")


def corpus_transforms(corpus: dict[str, Any], cfg: dict[str, Any]) -> list[str]:
    if "transforms" in corpus:
        return as_str_list(corpus.get("transforms"))
    return as_str_list(cfg.get("transforms"))


def check_data_block(
    cfg: dict[str, Any],
    reporter: Reporter,
    *,
    lambda_align: float,
    check_files: bool,
    base_dir: Path,
) -> None:
    data = cfg.get("data")
    if is_missing(data):
        return

    model_task = str(cfg.get("model_task", "seq2seq")).lower()
    incompatible_align_transforms = {
        "sentencepiece",
        "bpe",
        "onmt_tokenize",
        "tokendrop",
        "prefix",
        "bart",
    }

    if isinstance(data, str):
        reporter.warn(
            "data-scalar",
            "`data` is a scalar. Current dynamic training normally expects a corpus mapping; verify this is not an old-style config.",
        )
        return

    if not isinstance(data, dict):
        reporter.error("data-shape", "`data` must be a mapping of corpus names to corpus records.")
        return

    if not data:
        reporter.error("data-empty", "`data` mapping is empty.")
        return

    train_like = [name for name in data if str(name) != "valid"]
    if not train_like:
        reporter.error("data-no-train", "`data` must include at least one non-`valid` training corpus.")
    if "valid" not in data:
        reporter.warn("data-no-valid", "No `valid` corpus was found; validation iterator may fail or be unusable.")

    any_lm_corpus = False
    any_seq2seq_corpus = False
    for name, corpus in data.items():
        cname = str(name)
        if not isinstance(corpus, dict):
            reporter.error("data-corpus-shape", f"Corpus `{cname}` must be a mapping.")
            continue
        path_src = corpus.get("path_src")
        path_txt = corpus.get("path_txt")
        path_tgt = corpus.get("path_tgt")
        if is_missing(path_src) and is_missing(path_txt):
            reporter.error("data-path", f"Corpus `{cname}` needs `path_src` or `path_txt`.")
        if is_missing(path_tgt):
            any_lm_corpus = True
            if model_task != "lm" and is_missing(path_txt):
                reporter.warn(
                    "data-implicit-lm",
                    f"Corpus `{cname}` has no `path_tgt`; OpenNMT-py treats such corpora as language-model style input.",
                )
        else:
            any_seq2seq_corpus = True

        if check_files:
            for field in ["path_src", "path_txt", "path_tgt", "path_align"]:
                if field in corpus:
                    check_path_exists(f"data.{cname}.{field}", corpus.get(field), base_dir=base_dir, reporter=reporter)

        if lambda_align > 0.0:
            if is_missing(corpus.get("path_align")):
                reporter.error("align-path", f"Corpus `{cname}` needs `path_align` when `lambda_align > 0.0`.")
            transforms = set(corpus_transforms(corpus, cfg))
            bad = sorted(transforms & incompatible_align_transforms)
            if bad:
                reporter.error(
                    "align-transform",
                    f"Corpus `{cname}` uses transforms incompatible with alignment supervision: {', '.join(bad)}.",
                )

    if any_lm_corpus and any_seq2seq_corpus:
        reporter.warn("data-mixed-task", "Config mixes corpora with and without `path_tgt`; verify a mixed LM/seq2seq setup is intentional.")


def check_vocab_and_embedding_paths(
    cfg: dict[str, Any], reporter: Reporter, *, check_files: bool, base_dir: Path
) -> None:
    if check_files:
        for field in ["src_vocab", "tgt_vocab", "train_from", "pre_word_vecs_enc", "pre_word_vecs_dec"]:
            check_path_exists(field, cfg.get(field), base_dir=base_dir, reporter=reporter)
        for field in ["both_embeddings", "src_embeddings", "tgt_embeddings"]:
            check_path_exists(field, cfg.get(field), base_dir=base_dir, reporter=reporter)

    both = cfg.get("both_embeddings")
    src_emb = cfg.get("src_embeddings")
    tgt_emb = cfg.get("tgt_embeddings")
    raw_embedding = not is_missing(both) or not is_missing(src_emb) or not is_missing(tgt_emb)
    if not is_missing(both) and (not is_missing(src_emb) or not is_missing(tgt_emb)):
        reporter.error("embedding-exclusive", "Use `both_embeddings` or side-specific embeddings, not both.")
    if raw_embedding:
        emb_type = cfg.get("embeddings_type")
        if is_missing(emb_type):
            reporter.error("embedding-type", "Raw pretrained embeddings require `embeddings_type: GloVe` or `word2vec`.")
        elif str(emb_type) not in {"GloVe", "word2vec"}:
            reporter.error("embedding-type", "`embeddings_type` must be `GloVe` or `word2vec`.")
        if is_missing(cfg.get("save_data")):
            reporter.error("embedding-save-data", "Raw pretrained embeddings require `save_data` so derived tensors can be written.")
        if is_missing(cfg.get("word_vec_size")) and (is_missing(cfg.get("src_word_vec_size")) or is_missing(cfg.get("tgt_word_vec_size"))):
            reporter.warn("embedding-dim", "Set `word_vec_size` or side-specific vector sizes to match the pretrained embedding dimension.")


def check_distributed(cfg: dict[str, Any], reporter: Reporter) -> None:
    world_size = to_int(cfg.get("world_size", 1))
    if world_size is None:
        reporter.error("gpu-world-size", "`world_size` must be an integer.")
        return
    if world_size < 1:
        reporter.error("gpu-world-size", "`world_size` must be at least 1.")

    ranks = parse_int_list(cfg.get("gpu_ranks", []), reporter, "gpu-ranks", "gpu_ranks")
    if any(rank < 0 for rank in ranks):
        reporter.error("gpu-ranks", "`gpu_ranks` cannot contain negative ranks.")
    if len(ranks) != len(set(ranks)):
        reporter.error("gpu-ranks", "`gpu_ranks` contains duplicate ranks.")
    if len(ranks) > world_size:
        reporter.error("gpu-ranks", "`len(gpu_ranks)` must be less than or equal to `world_size`.")
    if ranks and world_size == len(ranks) and min(ranks) > 0:
        reporter.error("gpu-master-rank", "When `world_size == len(gpu_ranks)`, include master rank 0.")
    if world_size > 1 and not ranks:
        reporter.error("gpu-world-size", "`world_size > 1` with empty `gpu_ranks` will not launch useful local GPU workers.")
    if world_size > len(ranks) > 0:
        reporter.note(
            "gpu-multinode-slice",
            "`world_size` is greater than local `gpu_ranks`; this looks like a multi-node rank slice and requires matching master settings.",
        )
    if ranks and ranks != sorted(ranks):
        reporter.warn("gpu-ranks-order", "`gpu_ranks` are not sorted; verify rank-to-device mapping is intentional.")

    parallel_mode = str(cfg.get("parallel_mode", "data_parallel"))
    if parallel_mode not in {"data_parallel", "tensor_parallel"}:
        reporter.error("parallel-mode", "`parallel_mode` must be `data_parallel` or `tensor_parallel`.")
    elif parallel_mode == "tensor_parallel":
        reporter.note("tensor-parallel", "`tensor_parallel` changes model loading offsets; validate with a tiny run first.")


def check_checkpointing(cfg: dict[str, Any], reporter: Reporter) -> None:
    train_from = cfg.get("train_from")
    reset = str(cfg.get("reset_optim", "none"))
    update_vocab = boolish(cfg.get("update_vocab"), False)
    if reset not in {"none", "all", "states", "keep_states"}:
        reporter.error("reset-optim", "`reset_optim` must be one of: none, all, states, keep_states.")
    if update_vocab:
        if is_missing(train_from):
            reporter.error("update-vocab", "`update_vocab` requires `train_from`.")
        if reset not in {"states", "all"}:
            reporter.error("update-vocab", "`update_vocab` requires `reset_optim: states` or `reset_optim: all`.")
        elif reset == "all":
            reporter.warn("update-vocab-reset", "`reset_optim: all` is allowed for vocabulary update, but `states` is the usual safer default.")
    if reset != "none" and is_missing(train_from):
        reporter.warn("reset-without-checkpoint", "`reset_optim` has no effect without `train_from`.")
    if not is_missing(train_from) and reset == "none":
        reporter.note("checkpoint-resume", "`train_from` with `reset_optim: none` performs an exact optimizer-state resume.")


def check_schedules(cfg: dict[str, Any], reporter: Reporter) -> None:
    if any(field in cfg for field in ["accum_count", "accum_steps"]):
        accum_count = as_list(cfg.get("accum_count", [1]))
        accum_steps = as_list(cfg.get("accum_steps", [0]))
        if len(accum_count) != len(accum_steps):
            reporter.error("accum-schedule", "`accum_count` and `accum_steps` must have the same length.")
        for value in accum_count:
            parsed = to_int(value)
            if parsed is None or parsed <= 0:
                reporter.error("accum-schedule", "Every `accum_count` value must be a positive integer.")

    if any(field in cfg for field in ["dropout", "attention_dropout", "dropout_steps"]):
        dropout = as_list(cfg.get("dropout", [0.3]))
        attention_dropout = as_list(cfg.get("attention_dropout", [0.1]))
        dropout_steps = as_list(cfg.get("dropout_steps", [0]))
        if len(dropout) != len(dropout_steps):
            reporter.error("dropout-schedule", "`dropout` and `dropout_steps` must have the same length.")
        if len(attention_dropout) != len(dropout_steps):
            reporter.error("dropout-schedule", "`attention_dropout` and `dropout_steps` must have the same length.")


def check_model_compat(cfg: dict[str, Any], reporter: Reporter) -> None:
    position_encoding = boolish(cfg.get("position_encoding"), False)
    max_relative_positions = to_int(cfg.get("max_relative_positions", 0), default=0)
    if position_encoding and max_relative_positions not in (None, 0):
        reporter.error("position-encoding", "Do not combine `position_encoding: true` with nonzero `max_relative_positions`.")

    hidden_size = to_int(cfg.get("hidden_size"), default=-1)
    enc_hid = to_int(cfg.get("enc_hid_size"), default=500)
    dec_hid = to_int(cfg.get("dec_hid_size"), default=500)
    if hidden_size is not None and hidden_size > 0:
        enc_hid = dec_hid = hidden_size
    if enc_hid != dec_hid:
        reporter.error("hidden-size", "OpenNMT-py expects encoder and decoder hidden sizes to match.")

    if boolish(cfg.get("share_embeddings"), False) and not boolish(cfg.get("share_vocab"), False):
        reporter.warn("share-embeddings", "`share_embeddings` normally requires a shared vocabulary.")


def check_alignment(cfg: dict[str, Any], reporter: Reporter, lambda_align: float) -> None:
    if lambda_align < 0.0:
        reporter.error("lambda-align", "`lambda_align` cannot be negative.")
    if lambda_align <= 0.0:
        return

    decoder_type = str(cfg.get("decoder_type", "rnn"))
    if decoder_type != "transformer":
        reporter.error("lambda-align", "`lambda_align > 0.0` requires `decoder_type: transformer`.")

    layers = to_int(cfg.get("layers"), default=-1)
    dec_layers = to_int(cfg.get("dec_layers"), default=2)
    if layers is not None and layers > 0:
        dec_layers = layers
    if dec_layers is None or dec_layers <= 0:
        reporter.error("alignment-layer", "Could not determine a positive decoder layer count for alignment validation.")
        return

    alignment_layer = to_int(cfg.get("alignment_layer", -3), default=-3)
    if alignment_layer is None:
        reporter.error("alignment-layer", "`alignment_layer` must be an integer.")
    elif not (-dec_layers <= alignment_layer < dec_layers):
        reporter.error(
            "alignment-layer",
            f"`alignment_layer` must satisfy -dec_layers <= alignment_layer < dec_layers; got {alignment_layer} with dec_layers={dec_layers}.",
        )

    alignment_heads = to_int(cfg.get("alignment_heads", 0), default=0)
    if alignment_heads is None or alignment_heads < 0:
        reporter.error("alignment-heads", "`alignment_heads` must be a non-negative integer.")
    elif alignment_heads == 0:
        reporter.warn("alignment-heads", "Supervised alignment commonly sets `alignment_heads: 1`; `0` uses the default/average behavior.")

    if boolish(cfg.get("full_context_alignment"), False):
        reporter.note("full-context-alignment", "`full_context_alignment` can improve alignment supervision but slows training.")


def check_lora_quant(cfg: dict[str, Any], reporter: Reporter) -> None:
    lora_layers = as_str_list(cfg.get("lora_layers"))
    lora_embedding = boolish(cfg.get("lora_embedding"), False)
    quant_layers = as_str_list(cfg.get("quant_layers"))
    quant_type = str(cfg.get("quant_type", "") or "")
    train_from = cfg.get("train_from")
    override_opts = boolish(cfg.get("override_opts"), False)

    use_ckpting = as_str_list(cfg.get("use_ckpting"))
    invalid_ckpting = sorted(set(use_ckpting) - {"ffn", "mha", "lora"})
    if invalid_ckpting:
        reporter.error("use-ckpting", "`use_ckpting` only accepts ffn, mha, and lora; invalid: " + ", ".join(invalid_ckpting))
    if "lora" in use_ckpting and not (lora_layers or lora_embedding):
        reporter.warn("use-ckpting", "`use_ckpting: [lora]` has no useful effect without LoRA layers or LoRA embeddings.")

    if lora_layers or lora_embedding:
        if boolish(cfg.get("freeze_encoder"), False) or boolish(cfg.get("freeze_decoder"), False):
            reporter.error("lora-freeze", "LoRA cannot be combined with `freeze_encoder` or `freeze_decoder`.")
        rank = to_int(cfg.get("lora_rank", 2), default=2)
        alpha = to_int(cfg.get("lora_alpha", 1), default=1)
        dropout = to_float(cfg.get("lora_dropout", 0.0), default=0.0)
        if rank is None or rank <= 0:
            reporter.error("lora-rank", "`lora_rank` must be a positive integer.")
        if alpha is None or alpha <= 0:
            reporter.error("lora-alpha", "`lora_alpha` must be a positive integer.")
        if dropout is None or dropout < 0.0 or dropout >= 1.0:
            reporter.error("lora-dropout", "`lora_dropout` should satisfy 0.0 <= value < 1.0.")
        if is_missing(train_from):
            reporter.warn("lora-from-scratch", "LoRA is usually used with `train_from`; confirm from-scratch adapter training is intended.")
        elif not override_opts:
            reporter.warn("lora-override", "When adding LoRA to `train_from`, set `override_opts: true` and restate full model options, or checkpoint model options may hide LoRA settings.")
        if lora_embedding and not boolish(cfg.get("update_vocab"), False):
            reporter.note("lora-embedding", "`lora_embedding: true` makes embeddings trainable; it is especially useful when updating vocab or tuning embeddings.")

    valid_quant = {"", "bnb_8bit", "bnb_FP4", "bnb_NF4", "awq_gemm", "awq_gemv"}
    if quant_type not in valid_quant:
        reporter.error("quant-type", "Unsupported `quant_type`; use one of: bnb_8bit, bnb_FP4, bnb_NF4, awq_gemm, awq_gemv.")
    if quant_layers and not quant_type:
        reporter.error("quant-type", "Non-empty `quant_layers` requires a non-empty supported `quant_type`.")
    if quant_type and not quant_layers:
        reporter.warn("quant-layers", "`quant_type` is set but `quant_layers` is empty; no layers are selected for compression.")
    if quant_type.startswith("bnb"):
        reporter.note("quant-bnb", "bitsandbytes is required for `bnb_*` quantized layers.")
    if quant_type.startswith("awq"):
        reporter.note("quant-awq", "AutoAWQ is required for `awq_*` quantized layers.")
    if quant_layers and not is_missing(train_from) and not override_opts:
        reporter.warn("quant-override", "When adding quantization to `train_from`, set `override_opts: true` and restate full model options.")

    overlap = sorted(set(lora_layers) & set(quant_layers))
    if overlap:
        reporter.note("lora-quant-overlap", "Layers in both `lora_layers` and `quant_layers` become quantized LoRA layers: " + ", ".join(overlap))

    optim = str(cfg.get("optim", "sgd"))
    if optim in {"adamw8bit", "pagedadamw8bit", "pagedadamw32bit"}:
        reporter.note("bnb-optimizer", f"Optimizer `{optim}` requires bitsandbytes in the training runtime.")


def inspect_config(cfg: dict[str, Any], args: argparse.Namespace) -> Reporter:
    reporter = Reporter()
    lambda_align = to_float(cfg.get("lambda_align", 0.0), default=0.0)
    if lambda_align is None:
        reporter.error("lambda-align", "`lambda_align` must be a float.")
        lambda_align = 0.0

    base_dir = Path(args.base_dir).expanduser()
    check_required_training_fields(cfg, reporter)
    check_data_block(cfg, reporter, lambda_align=lambda_align, check_files=args.check_files, base_dir=base_dir)
    check_vocab_and_embedding_paths(cfg, reporter, check_files=args.check_files, base_dir=base_dir)
    check_distributed(cfg, reporter)
    check_checkpointing(cfg, reporter)
    check_schedules(cfg, reporter)
    check_model_compat(cfg, reporter)
    check_alignment(cfg, reporter, lambda_align)
    check_lora_quant(cfg, reporter)
    return reporter


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sanity-check an OpenNMT-py YAML training config.")
    parser.add_argument("config", type=Path, help="Training YAML file to inspect.")
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Also check configured data, vocab, checkpoint, and embedding paths for local existence.",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory for relative paths when --check-files is enabled (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero on warnings as well as errors.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    try:
        cfg = load_yaml(args.config)
    except FileNotFoundError:
        print(f"ERROR [config-missing] Config file not found: {args.config}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI diagnostic
        print(f"ERROR [config-parse] Could not read YAML config {args.config}: {exc}", file=sys.stderr)
        return 2

    print(f"Inspecting OpenNMT-py training config: {args.config}")
    reporter = inspect_config(cfg, args)
    reporter.emit()
    if reporter.count("ERROR") > 0:
        return 1
    if args.strict and reporter.count("WARN") > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
