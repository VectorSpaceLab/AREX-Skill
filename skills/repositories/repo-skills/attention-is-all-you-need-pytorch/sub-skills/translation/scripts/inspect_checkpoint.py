#!/usr/bin/env python3
"""Validate attention-is-all-you-need-pytorch translation checkpoint inputs.

The repository translation path loads Python pickles (PyTorch checkpoint and
optional dill data pickle). This helper is safe by default: it refuses to load
those files until --trust-inputs is supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PAD_WORD = "<blank>"
UNK_WORD = "<unk>"
BOS_WORD = "<s>"
EOS_WORD = "</s>"

REQUIRED_SETTINGS = [
    "src_vocab_size",
    "trg_vocab_size",
    "src_pad_idx",
    "trg_pad_idx",
    "proj_share_weight",
    "embs_share_weight",
    "d_k",
    "d_v",
    "d_model",
    "d_word_vec",
    "d_inner_hid",
    "n_layers",
    "n_head",
    "dropout",
]

STATE_KEY_HINTS = [
    "encoder.src_word_emb.weight",
    "decoder.trg_word_emb.weight",
    "trg_word_prj.weight",
]

_MISSING = object()


def _get(obj: Any, name: str, default: Any = _MISSING) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _as_bool(value: Any) -> bool:
    return bool(value)


def _field_vocab(field: Any) -> Any:
    return getattr(field, "vocab", None)


def _len_vocab(vocab: Any) -> int | None:
    try:
        return len(vocab)
    except Exception:
        pass
    itos = getattr(vocab, "itos", None)
    if itos is not None:
        try:
            return len(itos)
        except Exception:
            return None
    return None


def _torch_load_checkpoint(path: Path) -> Any:
    import torch

    # PyTorch versions differ: newer versions expose weights_only, older ones do
    # not. The checkpoint contains a Python settings object, so trusted loads
    # need weights_only=False where available.
    try:
        return torch.load(str(path), map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(str(path), map_location="cpu")


def _load_data_pickle(path: Path) -> Any:
    import dill as pickle

    with path.open("rb") as handle:
        return pickle.load(handle)


def validate_checkpoint(path: Path, instantiate_model: bool, repo_root: Path | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "errors": [],
        "warnings": [],
        "settings": {},
        "state_dict_key_count": None,
        "state_dict_hints": {},
        "instantiated_model": False,
    }

    if not path.exists():
        result["errors"].append(f"checkpoint does not exist: {path}")
        return result

    checkpoint = _torch_load_checkpoint(path)
    if not isinstance(checkpoint, Mapping):
        result["errors"].append(f"checkpoint root is {type(checkpoint).__name__}, expected mapping")
        return result

    for key in ("settings", "model"):
        if key not in checkpoint:
            result["errors"].append(f"missing checkpoint key: {key}")
    if result["errors"]:
        return result

    settings = checkpoint["settings"]
    model_state = checkpoint["model"]

    missing = [name for name in REQUIRED_SETTINGS if _get(settings, name, _MISSING) is _MISSING]
    if missing:
        result["errors"].append("settings missing required attributes: " + ", ".join(missing))

    for name in REQUIRED_SETTINGS + ["scale_emb_or_prj", "n_position", "epoch"]:
        value = _get(settings, name, _MISSING)
        if value is not _MISSING:
            if isinstance(value, (str, int, float, bool)) or value is None:
                result["settings"][name] = value
            else:
                result["settings"][name] = repr(value)

    def require_positive_int(name: str) -> None:
        value = _get(settings, name, _MISSING)
        if value is _MISSING:
            return
        if not isinstance(value, int) or value <= 0:
            result["errors"].append(f"settings.{name} must be a positive int, got {value!r}")

    for name in [
        "src_vocab_size",
        "trg_vocab_size",
        "d_k",
        "d_v",
        "d_model",
        "d_word_vec",
        "d_inner_hid",
        "n_layers",
        "n_head",
    ]:
        require_positive_int(name)

    for idx_name, size_name in [("src_pad_idx", "src_vocab_size"), ("trg_pad_idx", "trg_vocab_size")]:
        idx = _get(settings, idx_name, _MISSING)
        size = _get(settings, size_name, _MISSING)
        if idx is not _MISSING and size is not _MISSING:
            if not isinstance(idx, int) or idx < 0 or (isinstance(size, int) and idx >= size):
                result["errors"].append(f"settings.{idx_name}={idx!r} is not in range for {size_name}={size!r}")

    d_model = _get(settings, "d_model", _MISSING)
    d_word_vec = _get(settings, "d_word_vec", _MISSING)
    n_head = _get(settings, "n_head", _MISSING)
    if isinstance(d_model, int) and isinstance(d_word_vec, int) and d_model != d_word_vec:
        result["errors"].append("Transformer asserts d_model == d_word_vec")
    if isinstance(d_model, int) and isinstance(n_head, int) and n_head and d_model % n_head != 0:
        result["warnings"].append("d_model is not divisible by n_head; verify attention dimensions match the checkpoint")

    if _as_bool(_get(settings, "embs_share_weight", False)):
        src_size = _get(settings, "src_vocab_size", _MISSING)
        trg_size = _get(settings, "trg_vocab_size", _MISSING)
        if isinstance(src_size, int) and isinstance(trg_size, int) and src_size != trg_size:
            result["errors"].append("embs_share_weight is true but source/target vocab sizes differ")

    scale = _get(settings, "scale_emb_or_prj", "prj")
    if scale != "prj":
        result["warnings"].append(
            "checkpoint scale_emb_or_prj is not 'prj'; stock translate.py does not pass this setting and will use 'prj'"
        )

    if not isinstance(model_state, Mapping):
        result["errors"].append(f"checkpoint['model'] is {type(model_state).__name__}, expected state_dict mapping")
    else:
        result["state_dict_key_count"] = len(model_state)
        for key in STATE_KEY_HINTS:
            result["state_dict_hints"][key] = key in model_state
        missing_hints = [key for key, present in result["state_dict_hints"].items() if not present]
        if missing_hints:
            result["warnings"].append("state_dict missing common Transformer keys: " + ", ".join(missing_hints))

    if instantiate_model and not result["errors"]:
        if repo_root is None:
            result["errors"].append("--instantiate-model requires --repo-root")
        else:
            repo_root = repo_root.resolve()
            sys.path.insert(0, str(repo_root))
            try:
                from transformer.Models import Transformer

                model = Transformer(
                    _get(settings, "src_vocab_size"),
                    _get(settings, "trg_vocab_size"),
                    _get(settings, "src_pad_idx"),
                    _get(settings, "trg_pad_idx"),
                    trg_emb_prj_weight_sharing=_get(settings, "proj_share_weight"),
                    emb_src_trg_weight_sharing=_get(settings, "embs_share_weight"),
                    d_k=_get(settings, "d_k"),
                    d_v=_get(settings, "d_v"),
                    d_model=_get(settings, "d_model"),
                    d_word_vec=_get(settings, "d_word_vec"),
                    d_inner=_get(settings, "d_inner_hid"),
                    n_layers=_get(settings, "n_layers"),
                    n_head=_get(settings, "n_head"),
                    dropout=_get(settings, "dropout"),
                )
                model.load_state_dict(model_state)
                model.eval()
                result["instantiated_model"] = True
            except Exception as exc:  # pragma: no cover - reports user checkpoint/runtime mismatch
                result["errors"].append(f"model instantiation/load_state_dict failed: {type(exc).__name__}: {exc}")

    return result


def validate_data_pickle(path: Path, checkpoint_result: dict[str, Any] | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "errors": [],
        "warnings": [],
        "vocab": {},
        "test_count": None,
        "sample_has_trg": None,
    }

    if not path.exists():
        result["errors"].append(f"data pickle does not exist: {path}")
        return result

    data = _load_data_pickle(path)
    if not isinstance(data, Mapping):
        result["errors"].append(f"data pickle root is {type(data).__name__}, expected mapping")
        return result

    for key in ("vocab", "test"):
        if key not in data:
            result["errors"].append(f"data pickle missing key: {key}")
    if result["errors"]:
        return result

    vocab_root = data["vocab"]
    if not isinstance(vocab_root, Mapping):
        result["errors"].append("data['vocab'] must be a mapping with 'src' and 'trg'")
        return result

    for side in ("src", "trg"):
        if side not in vocab_root:
            result["errors"].append(f"data['vocab'] missing side: {side}")
            continue
        field = vocab_root[side]
        vocab = _field_vocab(field)
        stoi = getattr(vocab, "stoi", None)
        itos = getattr(vocab, "itos", None)
        side_info: dict[str, Any] = {
            "field_type": type(field).__name__,
            "vocab_size": _len_vocab(vocab),
            "has_stoi": isinstance(stoi, Mapping),
            "has_itos": itos is not None,
        }
        result["vocab"][side] = side_info
        if not isinstance(stoi, Mapping):
            result["errors"].append(f"{side} field lacks vocab.stoi mapping")
            continue
        if side == "trg" and itos is None:
            result["errors"].append("target field lacks vocab.itos sequence for decoding")
        required_tokens = [PAD_WORD] if side == "src" else [PAD_WORD, BOS_WORD, EOS_WORD]
        missing_tokens = [token for token in required_tokens if token not in stoi]
        if missing_tokens:
            result["errors"].append(f"{side} vocab missing required tokens: {', '.join(missing_tokens)}")
        if side == "src":
            unk_token = getattr(field, "unk_token", UNK_WORD)
            side_info["unk_token"] = unk_token
            if unk_token not in stoi:
                result["errors"].append(f"source unk_token {unk_token!r} is not present in src vocab.stoi")

    test = data["test"]
    try:
        result["test_count"] = len(test)
    except Exception:
        result["warnings"].append("could not determine len(data['test'])")

    first = None
    try:
        if result["test_count"]:
            first = test[0]
        else:
            iterator = iter(test)
            first = next(iterator)
    except StopIteration:
        result["warnings"].append("data['test'] is empty")
    except Exception as exc:
        result["warnings"].append(f"could not sample data['test']: {type(exc).__name__}: {exc}")

    if first is not None:
        if not hasattr(first, "src"):
            result["errors"].append("test examples must expose .src")
        result["sample_has_trg"] = hasattr(first, "trg")
        if not result["sample_has_trg"]:
            result["warnings"].append("sample test example lacks .trg; stock Dataset construction includes a trg field")

    if checkpoint_result and not checkpoint_result.get("errors"):
        settings = checkpoint_result.get("settings", {})
        for side, setting_name in [("src", "src_vocab_size"), ("trg", "trg_vocab_size")]:
            expected = settings.get(setting_name)
            actual = result["vocab"].get(side, {}).get("vocab_size")
            if isinstance(expected, int) and isinstance(actual, int) and expected != actual:
                result["errors"].append(
                    f"checkpoint settings.{setting_name}={expected} but data {side} vocab size is {actual}"
                )

    return result


def print_text_report(report: dict[str, Any]) -> None:
    def section(title: str) -> None:
        print(f"\n== {title} ==")

    print("attention-is-all-you-need-pytorch translation input inspection")
    section("checkpoint")
    ckpt = report["checkpoint"]
    print(f"path: {ckpt['path']}")
    for name, value in sorted(ckpt.get("settings", {}).items()):
        print(f"settings.{name}: {value}")
    if ckpt.get("state_dict_key_count") is not None:
        print(f"state_dict keys: {ckpt['state_dict_key_count']}")
    if ckpt.get("state_dict_hints"):
        for key, present in ckpt["state_dict_hints"].items():
            print(f"state key present [{present}]: {key}")
    print(f"instantiated_model: {ckpt.get('instantiated_model')}")
    for warning in ckpt.get("warnings", []):
        print(f"WARNING: {warning}")
    for error in ckpt.get("errors", []):
        print(f"ERROR: {error}")

    if report.get("data_pickle"):
        section("data pickle")
        data = report["data_pickle"]
        print(f"path: {data['path']}")
        print(f"test_count: {data.get('test_count')}")
        print(f"sample_has_trg: {data.get('sample_has_trg')}")
        for side, info in sorted(data.get("vocab", {}).items()):
            print(f"{side} vocab: {info}")
        for warning in data.get("warnings", []):
            print(f"WARNING: {warning}")
        for error in data.get("errors", []):
            print(f"ERROR: {error}")

    section("summary")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    print("status:", "OK" if not report["errors"] else "FAILED")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate translation checkpoint and optional data pickle schema for attention-is-all-you-need-pytorch."
    )
    parser.add_argument("--checkpoint", required=True, help="Path to train.py checkpoint (.chkpt).")
    parser.add_argument("--data-pkl", help="Optional preprocessing pickle used by translate.py.")
    parser.add_argument(
        "--trust-inputs",
        action="store_true",
        help="Required to load checkpoint/data pickle files. Only use for trusted files.",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root to add to sys.path when --instantiate-model is used.",
    )
    parser.add_argument(
        "--instantiate-model",
        action="store_true",
        help="Import transformer.Models from --repo-root, instantiate Transformer like translate.py, and load state_dict on CPU.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--warnings-as-errors", action="store_true", help="Exit nonzero when warnings are present.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.trust_inputs:
        parser.error("refusing to unpickle inputs without --trust-inputs")

    repo_root = Path(args.repo_root).resolve() if args.repo_root else None
    if args.instantiate_model and repo_root is None:
        parser.error("--instantiate-model requires --repo-root")
    if repo_root is not None and not repo_root.exists():
        parser.error(f"--repo-root does not exist: {repo_root}")

    report: dict[str, Any] = {"checkpoint": None, "data_pickle": None, "errors": [], "warnings": []}
    checkpoint_result = validate_checkpoint(Path(args.checkpoint), args.instantiate_model, repo_root)
    report["checkpoint"] = checkpoint_result
    if args.data_pkl:
        report["data_pickle"] = validate_data_pickle(Path(args.data_pkl), checkpoint_result)

    for section_name in ("checkpoint", "data_pickle"):
        section = report.get(section_name)
        if section:
            report["errors"].extend(section.get("errors", []))
            report["warnings"].extend(section.get("warnings", []))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    if report["errors"] or (args.warnings_as_errors and report["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
