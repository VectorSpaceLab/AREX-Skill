#!/usr/bin/env python3
"""
Inspect a preprocessing pickle for the attention-is-all-you-need-pytorch data
contracts.

The repository's preprocessing artifacts are Python pickles. Loading a pickle can
execute arbitrary code, so this tool is safe by default: it refuses to unpickle
unless --trust-pickle is supplied. Use it only for artifacts produced by a
trusted preprocessing run.

Examples:
  python inspect_preprocessed_pickle.py --pickle m30k_deen_shr.pkl
  python inspect_preprocessed_pickle.py --pickle m30k_deen_shr.pkl --trust-pickle --strict
  python inspect_preprocessed_pickle.py --pickle bpe_vocab.pkl --trust-pickle \
    --train-path bpe_deen/deen-train --val-path bpe_deen/deen-val
"""

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Mapping

SPECIAL_TOKENS = {
    "pad": "<blank>",
    "unk": "<unk>",
    "bos": "<s>",
    "eos": "</s>",
}
PATH_LIKE_SETTING_KEYS = {"raw_dir", "data_dir", "save_data", "codes"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Identify and summarize non-BPE vs BPE preprocessing pickles."
    )
    parser.add_argument(
        "pickle_path",
        nargs="?",
        help="Path to the preprocessing pickle. Equivalent to --pickle.",
    )
    parser.add_argument(
        "--pickle",
        dest="pickle_option",
        help="Path to the preprocessing pickle.",
    )
    parser.add_argument(
        "--trust-pickle",
        action="store_true",
        help="Actually unpickle the artifact. Only use with trusted files.",
    )
    parser.add_argument(
        "--train-path",
        help="BPE encoded training prefix without .src/.trg, e.g. bpe_deen/deen-train.",
    )
    parser.add_argument(
        "--val-path",
        help="BPE encoded validation prefix without .src/.trg, e.g. bpe_deen/deen-val.",
    )
    parser.add_argument(
        "--sample-examples",
        type=int,
        default=1,
        help="Number of embedded examples to summarize per split (default: 1).",
    )
    parser.add_argument(
        "--count-lines",
        action="store_true",
        help="Count all lines in BPE sidecar files. Off by default for large corpora.",
    )
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Show path-like values saved in settings instead of sanitized basenames.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when schema errors are detected.",
    )
    return parser.parse_args()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def qualname(obj):
    t = type(obj)
    return "%s.%s" % (t.__module__, t.__name__)


def safe_len(obj):
    try:
        return len(obj)
    except Exception:
        return None


def safe_iter_sample(seq, n):
    if n <= 0:
        return []
    out = []
    try:
        iterator = iter(seq)
        for _ in range(n):
            out.append(next(iterator))
    except StopIteration:
        pass
    except Exception as exc:
        out.append({"error": "could not iterate sample: %s" % exc})
    return out


def jsonable(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return repr(value)


def summarize_settings(settings, show_paths=False):
    if settings is None:
        return None
    raw = getattr(settings, "__dict__", None)
    if raw is None:
        return {"type": qualname(settings), "repr": repr(settings)}

    wanted = [
        "lang_src",
        "lang_trg",
        "save_data",
        "data_src",
        "data_trg",
        "raw_dir",
        "data_dir",
        "codes",
        "prefix",
        "max_len",
        "min_word_count",
        "keep_case",
        "share_vocab",
        "symbols",
        "min_frequency",
        "separator",
        "dict_input",
        "total_symbols",
    ]
    summary = {"type": qualname(settings), "fields": {}}
    for key in wanted:
        if key not in raw:
            continue
        value = raw[key]
        if key in PATH_LIKE_SETTING_KEYS and isinstance(value, str) and not show_paths:
            summary["fields"][key] = {
                "basename": os.path.basename(value),
                "is_absolute": os.path.isabs(value),
            }
        else:
            summary["fields"][key] = jsonable(value)
    other_keys = sorted(str(k) for k in raw.keys() if k not in wanted)
    if other_keys:
        summary["other_field_names"] = other_keys
    return summary


def mapping_get_no_insert(mapping, key):
    if hasattr(mapping, "get"):
        try:
            return mapping.get(key)
        except Exception:
            pass
    try:
        if key in mapping:
            return mapping[key]
    except Exception:
        return None
    return None


def summarize_field(field):
    summary = {"type": qualname(field)}
    for attr in ("pad_token", "unk_token", "init_token", "eos_token", "lower"):
        if hasattr(field, attr):
            summary[attr] = jsonable(getattr(field, attr))
    if hasattr(field, "tokenize"):
        tokenizer = getattr(field, "tokenize")
        summary["tokenize"] = getattr(tokenizer, "__name__", repr(tokenizer))

    vocab = getattr(field, "vocab", None)
    if vocab is None:
        summary["has_vocab"] = False
        summary["missing_special_tokens"] = list(SPECIAL_TOKENS.values())
        return summary

    summary["has_vocab"] = True
    summary["vocab_type"] = qualname(vocab)
    summary["vocab_size"] = safe_len(vocab)
    stoi = getattr(vocab, "stoi", {})
    itos = getattr(vocab, "itos", None)
    summary["itos_size"] = safe_len(itos) if itos is not None else None
    special_indices = {}
    missing = []
    for name, token in SPECIAL_TOKENS.items():
        idx = mapping_get_no_insert(stoi, token)
        special_indices[name] = idx
        if idx is None:
            missing.append(token)
    summary["special_indices"] = special_indices
    summary["missing_special_tokens"] = missing
    return summary


def summarize_example(example):
    result = {"type": qualname(example)}
    for attr in ("src", "trg"):
        if hasattr(example, attr):
            tokens = getattr(example, attr)
            result[attr + "_len"] = safe_len(tokens)
            try:
                result[attr + "_head"] = list(tokens[:10])
            except Exception:
                result[attr + "_head"] = repr(tokens)
        else:
            result[attr + "_missing"] = True
    return result


def summarize_split(name, examples, sample_count):
    summary = {"type": qualname(examples), "count": safe_len(examples)}
    summary["samples"] = []
    for sample in safe_iter_sample(examples, sample_count):
        if isinstance(sample, dict) and "error" in sample:
            summary["samples"].append(sample)
        else:
            summary["samples"].append(summarize_example(sample))
    return summary


def classify_data(data):
    if not isinstance(data, Mapping):
        return "unknown", ["top-level object is not a mapping"]
    keys = set(data.keys())
    has_split_keys = {"train", "valid", "test"}.issubset(keys)
    vocab = data.get("vocab")
    if isinstance(vocab, Mapping) and {"src", "trg"}.issubset(set(vocab.keys())) and has_split_keys:
        return "non_bpe_multi30k", []
    if vocab is not None and not isinstance(vocab, Mapping) and not ({"train", "valid", "test"} & keys):
        return "bpe_shared_field", []
    return "unknown", [
        "expected either non-BPE keys (vocab.src/vocab.trg plus train/valid/test) "
        "or BPE keys (settings plus a single shared vocab field)"
    ]


def check_parallel_prefix(prefix, count_lines=False):
    result = {"prefix": prefix, "files": {}}
    for suffix in ("src", "trg"):
        path = prefix + "." + suffix
        entry = {"path": path, "exists": os.path.exists(path)}
        if entry["exists"]:
            entry["size_bytes"] = os.path.getsize(path)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    first = f.readline().rstrip("\n")
                entry["first_line_tokens"] = first.split()[:20]
                if count_lines:
                    with open(path, "r", encoding="utf-8") as f:
                        entry["line_count"] = sum(1 for _ in f)
            except UnicodeDecodeError as exc:
                entry["error"] = "not valid UTF-8 text: %s" % exc
            except OSError as exc:
                entry["error"] = str(exc)
        result["files"][suffix] = entry
    if all(result["files"][s]["exists"] for s in ("src", "trg")):
        result["status"] = "present"
        if count_lines:
            src_count = result["files"]["src"].get("line_count")
            trg_count = result["files"]["trg"].get("line_count")
            result["line_counts_match"] = src_count == trg_count
    else:
        result["status"] = "missing"
    return result


def inspect_data(data, args):
    warnings = []
    errors = []
    schema, classification_errors = classify_data(data)
    errors.extend(classification_errors)

    summary = {
        "classification": schema,
        "top_level_type": qualname(data),
        "top_level_keys": sorted(str(k) for k in data.keys()) if isinstance(data, Mapping) else None,
        "settings": summarize_settings(data.get("settings") if isinstance(data, Mapping) else None, args.show_paths),
        "vocab": None,
        "splits": {},
        "external_bpe_files": {},
        "warnings": warnings,
        "errors": errors,
    }

    if not isinstance(data, Mapping):
        errors.append("cannot inspect non-mapping top-level object")
        return summary

    settings = data.get("settings")
    if settings is None:
        warnings.append("missing settings object")
    elif not hasattr(settings, "max_len"):
        warnings.append("settings.max_len is missing; train loaders expect it")

    vocab = data.get("vocab")
    if schema == "non_bpe_multi30k":
        src = vocab.get("src")
        trg = vocab.get("trg")
        src_summary = summarize_field(src)
        trg_summary = summarize_field(trg)
        summary["vocab"] = {"src": src_summary, "trg": trg_summary}
        for side, field_summary in (("src", src_summary), ("trg", trg_summary)):
            if field_summary.get("missing_special_tokens"):
                errors.append(
                    "%s field missing special tokens: %s"
                    % (side, ", ".join(field_summary["missing_special_tokens"]))
                )
        try:
            summary["vocab"]["shared_stoi"] = dict(src.vocab.stoi) == dict(trg.vocab.stoi)
        except Exception:
            summary["vocab"]["shared_stoi"] = None
        for split in ("train", "valid", "test"):
            if split not in data:
                errors.append("missing split key: %s" % split)
            else:
                summary["splits"][split] = summarize_split(
                    split, data[split], max(0, args.sample_examples)
                )
    elif schema == "bpe_shared_field":
        field_summary = summarize_field(vocab)
        summary["vocab"] = {"shared": field_summary}
        if field_summary.get("missing_special_tokens"):
            errors.append(
                "shared BPE field missing special tokens: %s"
                % ", ".join(field_summary["missing_special_tokens"])
            )
        warnings.append(
            "BPE shared-field pickles are for BPE training with external encoded files; "
            "stock translation expects the non-BPE schema."
        )
        for label, prefix in (("train", args.train_path), ("valid", args.val_path)):
            if prefix:
                summary["external_bpe_files"][label] = check_parallel_prefix(
                    prefix, count_lines=args.count_lines
                )
                if summary["external_bpe_files"][label]["status"] != "present":
                    errors.append("BPE %s prefix is missing .src or .trg files: %s" % (label, prefix))
            else:
                warnings.append("BPE %s prefix not provided; cannot check sidecar .src/.trg files" % label)
    else:
        if isinstance(vocab, Mapping):
            summary["vocab"] = {"mapping_keys": sorted(str(k) for k in vocab.keys())}
        elif vocab is not None:
            summary["vocab"] = {"object": summarize_field(vocab)}

    return summary


def load_pickle(path):
    try:
        import dill as pickle_module  # type: ignore
        loader = "dill"
    except ImportError:
        import pickle as pickle_module  # type: ignore
        loader = "pickle"
    with open(path, "rb") as f:
        return pickle_module.load(f), loader


def emit(summary, fmt):
    if fmt == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    print("classification:", summary.get("classification"))
    print("file:", summary.get("file", {}).get("path"))
    for warning in summary.get("warnings", []):
        print("warning:", warning)
    for error in summary.get("errors", []):
        print("error:", error)
    if summary.get("vocab"):
        print("vocab:", json.dumps(summary["vocab"], indent=2, sort_keys=True))
    if summary.get("splits"):
        print("splits:", json.dumps(summary["splits"], indent=2, sort_keys=True))
    if summary.get("external_bpe_files"):
        print("external_bpe_files:", json.dumps(summary["external_bpe_files"], indent=2, sort_keys=True))


def main():
    args = parse_args()
    path = args.pickle_option or args.pickle_path
    if not path:
        print("error: provide a pickle path as an argument or with --pickle", file=sys.stderr)
        return 2

    summary = {
        "schema": "attention-is-all-you-need-pytorch.preprocessed-pickle-inspection.v1",
        "file": {
            "path": path,
            "exists": os.path.exists(path),
        },
        "warnings": [],
        "errors": [],
    }
    if not os.path.exists(path):
        summary["errors"].append("pickle file does not exist")
        emit(summary, args.format)
        return 1

    summary["file"]["size_bytes"] = os.path.getsize(path)
    summary["file"]["sha256"] = sha256_file(path)

    if not args.trust_pickle:
        summary["errors"].append(
            "refusing to unpickle without --trust-pickle because Python pickle loading can execute code"
        )
        emit(summary, args.format)
        return 2

    try:
        data, loader = load_pickle(path)
        summary["pickle_loader"] = loader
    except ModuleNotFoundError as exc:
        summary["errors"].append(
            "missing module while unpickling: %s. Install the legacy dependency used to create the artifact."
            % exc.name
        )
        emit(summary, args.format)
        return 1
    except Exception as exc:
        summary["errors"].append("failed to unpickle artifact: %s" % exc)
        emit(summary, args.format)
        return 1

    details = inspect_data(data, args)
    summary.update(details)
    emit(summary, args.format)
    if args.strict and summary.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
