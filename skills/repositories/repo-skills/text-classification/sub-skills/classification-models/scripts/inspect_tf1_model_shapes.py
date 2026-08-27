#!/usr/bin/env python3
"""Safely inspect tiny legacy TensorFlow 1.x classification graph shapes.

The fastTextB and TextCNN probes import one model file and construct a fresh,
tiny graph only. They never create a Session, initialize variables, load data,
restore a checkpoint, train, or access the network. The BERT probe is static and
therefore does not require TensorFlow.
"""

import argparse
import contextlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path


class InspectionError(RuntimeError):
    pass


def _positive_int(value):
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer >= 1")
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def _filter_sizes(value):
    try:
        values = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError("must be a comma-separated list of integers")
    if not values or any(item < 1 for item in values):
        raise argparse.ArgumentTypeError("all filter sizes must be >= 1")
    if len(set(values)) != len(values):
        raise argparse.ArgumentTypeError("filter sizes must be unique")
    return values


def _default_repo_root():
    # .../repo/skills/disco/text-classification/sub-skills/
    # classification-models/scripts/this_file.py
    return Path(__file__).resolve().parents[6]


def _build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny TF1 fastTextB/TextCNN graph or statically inspect a "
            "BERT classification shape contract. No sessions or data are used."
        )
    )
    parser.add_argument(
        "--model",
        choices=("fasttext", "textcnn", "bert-config"),
        required=True,
        help="Probe to perform.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(_default_repo_root()),
        help="brightmart/text_classification repository root.",
    )
    parser.add_argument("--batch-size", type=_positive_int, default=2)
    parser.add_argument("--sequence-length", type=_positive_int, default=8)
    parser.add_argument("--vocab-size", type=_positive_int, default=None)
    parser.add_argument("--embedding-size", type=_positive_int, default=8)
    parser.add_argument("--num-labels", type=_positive_int, default=4)
    parser.add_argument("--max-labels", type=_positive_int, default=3)
    parser.add_argument("--filter-sizes", type=_filter_sizes, default=[2, 3])
    parser.add_argument("--num-filters", type=_positive_int, default=4)
    parser.add_argument(
        "--bert-config",
        metavar="JSON",
        help="Optional BERT config JSON for the static probe.",
    )
    parser.add_argument("--hidden-size", type=_positive_int, default=None)
    parser.add_argument("--num-hidden-layers", type=_positive_int, default=None)
    parser.add_argument("--num-attention-heads", type=_positive_int, default=None)
    parser.add_argument("--intermediate-size", type=_positive_int, default=None)
    parser.add_argument(
        "--json", action="store_true", help="Emit one deterministic JSON object."
    )
    return parser


def _require_source(repo_root, relative_path):
    path = Path(repo_root).expanduser().resolve() / relative_path
    if not path.is_file():
        raise InspectionError(
            "required model source is unavailable: {} (check --repo-root)".format(path)
        )
    return path


def _load_tf1():
    try:
        import tensorflow as tf
    except Exception as exc:
        raise InspectionError(
            "TensorFlow import failed; fasttext/textcnn require a TensorFlow 1.x "
            "environment: {}: {}".format(type(exc).__name__, exc)
        )

    missing = []
    for name in ("Graph", "placeholder", "contrib", "train"):
        if not hasattr(tf, name):
            missing.append("tf.{}".format(name))
    if missing:
        raise InspectionError(
            "legacy model requires TensorFlow 1.x APIs unavailable in the imported "
            "TensorFlow {}: {}. TensorFlow 2.x compat mode does not restore "
            "tf.contrib.".format(
                getattr(tf, "__version__", "unknown"), ", ".join(missing)
            )
        )
    return tf


def _load_module(path, module_name):
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise ImportError("no import loader was created")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as exc:
        raise InspectionError(
            "model import failed for {}: {}: {}".format(
                path, type(exc).__name__, exc
            )
        )


def _shape(tensor):
    try:
        return tensor.shape.as_list()
    except Exception as exc:
        raise InspectionError(
            "could not determine shape for tensor {!r}: {}".format(tensor, exc)
        )


def _tensor_record(label, tensor):
    return {
        "label": label,
        "tensor": getattr(tensor, "name", label),
        "dtype": tensor.dtype.name,
        "shape": _shape(tensor),
    }


def _build_fasttext(args, source_path):
    tf = _load_tf1()
    vocab_size = args.vocab_size if args.vocab_size is not None else 32
    try:
        with tf.Graph().as_default():
            # The legacy modules print tensor details while constructing. Suppress
            # those prints so --json remains a single machine-readable document.
            with contextlib.redirect_stdout(io.StringIO()):
                module = _load_module(source_path, "_inspect_legacy_fasttext_model")
                model_class = getattr(module, "fastTextB", None)
                if model_class is None:
                    raise InspectionError("model class fastTextB is unavailable in {}".format(source_path))
                model = model_class(
                    label_size=args.num_labels,
                    learning_rate=0.001,
                    batch_size=args.batch_size,
                    decay_steps=10,
                    decay_rate=0.9,
                    num_sampled=max(1, min(2, args.num_labels)),
                    sentence_len=args.sequence_length,
                    vocab_size=vocab_size,
                    embed_size=args.embedding_size,
                    is_training=False,
                    max_label_per_example=args.max_labels,
                )
            placeholders = [
                _tensor_record("sentence", model.sentence),
                _tensor_record("labels", model.labels),
                _tensor_record("labels_multi_hot", model.labels_l1999),
            ]
            logits = _tensor_record("logits", model.logits)
            loss = _tensor_record("loss", model.loss_val)
    except InspectionError:
        raise
    except Exception as exc:
        raise InspectionError(
            "fastTextB graph construction failed: {}: {}".format(
                type(exc).__name__, exc
            )
        )

    return {
        "status": "ok",
        "model": "fasttext",
        "inspection": "tensorflow-graph-construction",
        "source": str(source_path),
        "tensorflow_version": str(getattr(tf, "__version__", "unknown")),
        "dimensions": {
            "batch_size_constructor": args.batch_size,
            "embedding_size": args.embedding_size,
            "max_labels_per_example": args.max_labels,
            "num_labels": args.num_labels,
            "sequence_length": args.sequence_length,
            "vocab_size": vocab_size,
        },
        "placeholders": placeholders,
        "logits": logits,
        "loss": loss,
        "notes": [
            "Batch dimensions remain dynamic (null/?); no Session was created.",
            "labels_multi_hot is the active sigmoid-loss target; labels is retained by the legacy sampled-loss path.",
        ],
    }


def _build_textcnn(args, source_path):
    if max(args.filter_sizes) > args.sequence_length:
        raise InspectionError(
            "largest TextCNN filter size ({}) exceeds sequence length ({})".format(
                max(args.filter_sizes), args.sequence_length
            )
        )
    tf = _load_tf1()
    vocab_size = args.vocab_size if args.vocab_size is not None else 32
    try:
        with tf.Graph().as_default():
            with contextlib.redirect_stdout(io.StringIO()):
                module = _load_module(source_path, "_inspect_legacy_textcnn_model")
                model_class = getattr(module, "TextCNN", None)
                if model_class is None:
                    raise InspectionError("model class TextCNN is unavailable in {}".format(source_path))
                model = model_class(
                    filter_sizes=list(args.filter_sizes),
                    num_filters=args.num_filters,
                    num_classes=args.num_labels,
                    learning_rate=0.001,
                    batch_size=args.batch_size,
                    decay_steps=10,
                    decay_rate=0.9,
                    sequence_length=args.sequence_length,
                    vocab_size=vocab_size,
                    embed_size=args.embedding_size,
                    multi_label_flag=True,
                )
            placeholders = [
                _tensor_record("input_x", model.input_x),
                _tensor_record("input_y_multilabel", model.input_y_multilabel),
                _tensor_record("dropout_keep_prob", model.dropout_keep_prob),
                _tensor_record("is_training_flag", model.is_training_flag),
            ]
            logits = _tensor_record("logits", model.logits)
            loss = _tensor_record("loss", model.loss_val)
    except InspectionError:
        raise
    except Exception as exc:
        raise InspectionError(
            "TextCNN graph construction failed: {}: {}".format(
                type(exc).__name__, exc
            )
        )

    return {
        "status": "ok",
        "model": "textcnn",
        "inspection": "tensorflow-graph-construction",
        "source": str(source_path),
        "tensorflow_version": str(getattr(tf, "__version__", "unknown")),
        "dimensions": {
            "batch_size_constructor": args.batch_size,
            "embedding_size": args.embedding_size,
            "filter_sizes": list(args.filter_sizes),
            "num_filters": args.num_filters,
            "num_labels": args.num_labels,
            "sequence_length": args.sequence_length,
            "vocab_size": vocab_size,
        },
        "placeholders": placeholders,
        "logits": logits,
        "loss": loss,
        "notes": [
            "The probe forces multi_label_flag=True because the legacy single-label branch references a missing input_y placeholder.",
            "No Session, variable initialization, checkpoint restore, data load, or training step was performed.",
        ],
    }


def _config_int(config, cli_value, key, default):
    value = cli_value if cli_value is not None else config.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InspectionError("BERT config field {} must be an integer >= 1".format(key))
    return value


def _inspect_bert(args, source_path):
    config = {}
    config_source = "built-in tiny defaults"
    if args.bert_config:
        config_path = Path(args.bert_config).expanduser().resolve()
        try:
            with open(str(config_path), "r", encoding="utf-8") as stream:
                config = json.load(stream)
        except (OSError, ValueError) as exc:
            raise InspectionError(
                "cannot read BERT config {}: {}: {}".format(
                    config_path, type(exc).__name__, exc
                )
            )
        if not isinstance(config, dict):
            raise InspectionError("BERT config JSON must contain an object")
        config_source = str(config_path)

    vocab_size = _config_int(config, args.vocab_size, "vocab_size", 32)
    hidden_size = _config_int(config, args.hidden_size, "hidden_size", 16)
    num_hidden_layers = _config_int(
        config, args.num_hidden_layers, "num_hidden_layers", 1
    )
    num_attention_heads = _config_int(
        config, args.num_attention_heads, "num_attention_heads", 2
    )
    intermediate_size = _config_int(
        config, args.intermediate_size, "intermediate_size", 32
    )
    if hidden_size % num_attention_heads != 0:
        raise InspectionError(
            "hidden_size ({}) must be divisible by num_attention_heads ({})".format(
                hidden_size, num_attention_heads
            )
        )
    max_positions = config.get("max_position_embeddings")
    if max_positions is not None:
        if isinstance(max_positions, bool) or not isinstance(max_positions, int) or max_positions < 1:
            raise InspectionError(
                "BERT config field max_position_embeddings must be an integer >= 1"
            )
        if args.sequence_length > max_positions:
            raise InspectionError(
                "sequence length {} exceeds max_position_embeddings {}".format(
                    args.sequence_length, max_positions
                )
            )

    def static_tensor(label, dtype, shape):
        return {"label": label, "tensor": label + ":0", "dtype": dtype, "shape": shape}

    return {
        "status": "ok",
        "model": "bert-config",
        "inspection": "static-shape-probe",
        "source": str(source_path),
        "config_source": config_source,
        "tensorflow_version": None,
        "dimensions": {
            "hidden_size": hidden_size,
            "intermediate_size": intermediate_size,
            "num_attention_heads": num_attention_heads,
            "num_hidden_layers": num_hidden_layers,
            "num_labels": args.num_labels,
            "sequence_length": args.sequence_length,
            "vocab_size": vocab_size,
        },
        "placeholders": [
            static_tensor("input_ids", "int32", [None, args.sequence_length]),
            static_tensor("input_mask", "int32", [None, args.sequence_length]),
            static_tensor("segment_ids", "int32", [None, args.sequence_length]),
            static_tensor("labels_multi_hot", "float32", [None, args.num_labels]),
        ],
        "logits": static_tensor("logits", "float32", [None, args.num_labels]),
        "loss": static_tensor("loss", "float32", []),
        "notes": [
            "Shapes describe the repository's pooled-output multi-label BERT head.",
            "This is a static config probe: TensorFlow and bert_modeling.py were not imported or executed.",
            "No data, checkpoint, Session, training, or network access was used.",
        ],
    }


def _format_shape(shape):
    if not shape:
        return "[]"
    return "[{}]".format(", ".join("?" if item is None else str(item) for item in shape))


def _print_text(result):
    for key in ("status", "model", "inspection", "source"):
        print("{}: {}".format(key, result[key]))
    if "config_source" in result:
        print("config_source: {}".format(result["config_source"]))
    print("tensorflow_version: {}".format(result["tensorflow_version"] or "not required"))
    print("dimensions:")
    for key in sorted(result["dimensions"]):
        value = result["dimensions"][key]
        if isinstance(value, list):
            value = ",".join(str(item) for item in value)
        print("  {}: {}".format(key, value))
    print("placeholders:")
    for item in result["placeholders"]:
        print(
            "  {}: shape={} dtype={} tensor={}".format(
                item["label"], _format_shape(item["shape"]), item["dtype"], item["tensor"]
            )
        )
    for key in ("logits", "loss"):
        item = result[key]
        print(
            "{}: shape={} dtype={} tensor={}".format(
                key, _format_shape(item["shape"]), item["dtype"], item["tensor"]
            )
        )
    print("notes:")
    for note in result["notes"]:
        print("  - {}".format(note))


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()

    try:
        if args.model == "fasttext":
            source_path = _require_source(
                repo_root, Path("a01_FastText") / "p6_fastTextB_model_multilabel.py"
            )
            result = _build_fasttext(args, source_path)
        elif args.model == "textcnn":
            source_path = _require_source(
                repo_root, Path("a02_TextCNN") / "p7_TextCNN_model.py"
            )
            result = _build_textcnn(args, source_path)
        else:
            source_path = _require_source(
                repo_root, Path("a00_Bert") / "bert_modeling.py"
            )
            result = _inspect_bert(args, source_path)
    except InspectionError as exc:
        if args.json:
            print(
                json.dumps(
                    {"status": "error", "model": args.model, "error": str(exc)},
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print("error: {}".format(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_text(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
