#!/usr/bin/env python3
"""Offline-safe checker for HFL Chinese BERT-wwm Transformers model ids.

The script validates a bundled model-id map and imports the expected
Transformers classes. It performs no network downloads by default. Add
--allow-download only when checkpoint downloads are explicitly acceptable.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
from typing import Any, Callable

MODEL_MAP: dict[str, dict[str, str]] = {
    "hfl/chinese-roberta-wwm-ext-large": {
        "display_name": "RoBERTa-wwm-ext-large",
        "hf_id": "hfl/chinese-roberta-wwm-ext-large",
        "paddlehub_module": "chinese-roberta-wwm-ext-large",
        "source": "README download table and quick-load table",
        "class_family": "BERT",
    },
    "hfl/chinese-roberta-wwm-ext": {
        "display_name": "RoBERTa-wwm-ext",
        "hf_id": "hfl/chinese-roberta-wwm-ext",
        "paddlehub_module": "chinese-roberta-wwm-ext",
        "source": "README download table and quick-load table",
        "class_family": "BERT",
    },
    "hfl/chinese-bert-wwm-ext": {
        "display_name": "BERT-wwm-ext",
        "hf_id": "hfl/chinese-bert-wwm-ext",
        "paddlehub_module": "chinese-bert-wwm-ext",
        "source": "README download table and quick-load table",
        "class_family": "BERT",
    },
    "hfl/chinese-bert-wwm": {
        "display_name": "BERT-wwm",
        "hf_id": "hfl/chinese-bert-wwm",
        "paddlehub_module": "chinese-bert-wwm",
        "source": "README download table and quick-load table",
        "class_family": "BERT",
    },
    "hfl/rbt3": {
        "display_name": "RBT3",
        "hf_id": "hfl/rbt3",
        "paddlehub_module": "rbt3",
        "source": "README download table and quick-load table",
        "class_family": "BERT",
    },
    "hfl/rbt4": {
        "display_name": "RBT4",
        "hf_id": "hfl/rbt4",
        "paddlehub_module": "",
        "source": "README download table; omitted from quick-load tables",
        "class_family": "BERT",
    },
    "hfl/rbt6": {
        "display_name": "RBT6",
        "hf_id": "hfl/rbt6",
        "paddlehub_module": "",
        "source": "README download table; omitted from quick-load tables",
        "class_family": "BERT",
    },
    "hfl/rbtl3": {
        "display_name": "RBTL3",
        "hf_id": "hfl/rbtl3",
        "paddlehub_module": "rbtl3",
        "source": "README download table and quick-load table",
        "class_family": "BERT",
    },
}

EXIT_USAGE = 1
EXIT_INVALID_ID = 2
EXIT_IMPORT_ERROR = 3
EXIT_LOAD_ERROR = 4


@dataclass
class TransformersAPI:
    version: str
    BertTokenizer: Any
    BertModel: Any
    AutoTokenizer: Any
    AutoModel: Any
    AutoConfig: Any


def eprint(*parts: object) -> None:
    print(*parts, file=sys.stderr)


def import_transformers_api() -> TransformersAPI:
    """Import the expected Transformers classes and fail clearly on errors."""
    try:
        transformers = importlib.import_module("transformers")
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(f"failed to import transformers: {exc}") from exc

    missing: list[str] = []
    imported: dict[str, Any] = {}
    for name in ["BertTokenizer", "BertModel", "AutoTokenizer", "AutoModel", "AutoConfig"]:
        try:
            imported[name] = getattr(transformers, name)
        except Exception as exc:  # lazy imports can raise backend errors
            missing.append(f"{name}: {exc}")

    if missing:
        raise RuntimeError("failed to import required Transformers classes: " + "; ".join(missing))

    return TransformersAPI(
        version=getattr(transformers, "__version__", "unknown"),
        BertTokenizer=imported["BertTokenizer"],
        BertModel=imported["BertModel"],
        AutoTokenizer=imported["AutoTokenizer"],
        AutoModel=imported["AutoModel"],
        AutoConfig=imported["AutoConfig"],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate HFL Chinese BERT-wwm family model ids and optionally "
            "try offline/cache or explicitly-online Transformers loads. "
            "No downloads are attempted unless --allow-download is set."
        )
    )
    parser.add_argument(
        "model_id_positional",
        nargs="?",
        metavar="MODEL_ID",
        help="Supported Hugging Face id, for example hfl/chinese-bert-wwm or hfl/rbt3.",
    )
    parser.add_argument(
        "--model-id",
        dest="model_id_option",
        help="Supported Hugging Face id. If also passed positionally, both values must match.",
    )
    parser.add_argument(
        "--cache-dir",
        help="Optional Hugging Face cache directory to pass to from_pretrained.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--offline-only",
        action="store_true",
        default=False,
        help="Use local_files_only=True. This is already the default unless --allow-download is set.",
    )
    mode_group.add_argument(
        "--allow-download",
        action="store_true",
        help="Allow from_pretrained calls to contact the network and download missing files.",
    )
    parser.add_argument(
        "--try-load-config",
        action="store_true",
        help="Attempt AutoConfig.from_pretrained for the selected id.",
    )
    parser.add_argument(
        "--try-load-tokenizer",
        action="store_true",
        help="Attempt tokenizer from_pretrained for the selected id.",
    )
    parser.add_argument(
        "--try-load-model",
        action="store_true",
        help=(
            "Attempt model from_pretrained for the selected id. This may load large weights "
            "from cache or download them when --allow-download is set."
        ),
    )
    parser.add_argument(
        "--use-auto",
        action="store_true",
        help="Use AutoTokenizer/AutoModel for requested tokenizer/model loads instead of BertTokenizer/BertModel.",
    )
    parser.add_argument(
        "--revision",
        default="main",
        help="Model revision to pass to from_pretrained. Default: main.",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Print supported model ids and PaddleHub module names, then exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary on success or known validation/load failure.",
    )
    return parser


def resolve_model_id(args: argparse.Namespace) -> str | None:
    positional = args.model_id_positional
    option = args.model_id_option
    if positional and option and positional != option:
        raise ValueError(f"positional MODEL_ID {positional!r} does not match --model-id {option!r}")
    return option or positional


def print_model_table(as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(MODEL_MAP, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print("Supported HFL Chinese BERT-wwm family model ids:")
    for model_id, info in MODEL_MAP.items():
        module = info.get("paddlehub_module") or "(not listed in README PaddleHub quick-load table)"
        print(f"- {model_id}: {info['display_name']} | PaddleHub: {module} | {info['source']}")


def load_step(label: str, loader: Callable[..., Any], model_id: str, kwargs: dict[str, Any]) -> str:
    try:
        obj = loader(model_id, **kwargs)
    except Exception as exc:  # loading failures are exactly what this helper should catch
        raise RuntimeError(f"{label} load failed for {model_id!r}: {type(exc).__name__}: {exc}") from exc

    cls_name = type(obj).__name__
    # Drop large objects promptly; this script is a checker, not an inference runner.
    del obj
    return cls_name


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_models:
        print_model_table(args.json)
        return 0

    try:
        model_id = resolve_model_id(args)
    except ValueError as exc:
        eprint(f"usage error: {exc}")
        return EXIT_USAGE

    if not model_id:
        eprint("usage error: provide MODEL_ID, --model-id, or --list-models")
        return EXIT_USAGE

    if model_id not in MODEL_MAP:
        eprint(f"invalid model id: {model_id!r}")
        eprint("Run with --list-models to see supported ids.")
        if args.json:
            print(json.dumps({"ok": False, "error": "invalid_model_id", "model_id": model_id}, indent=2))
        return EXIT_INVALID_ID

    offline_only = not args.allow_download
    if args.offline_only:
        offline_only = True

    try:
        api = import_transformers_api()
    except RuntimeError as exc:
        eprint(f"import error: {exc}")
        if args.json:
            print(json.dumps({"ok": False, "error": "import_error", "detail": str(exc)}, indent=2))
        return EXIT_IMPORT_ERROR

    load_kwargs: dict[str, Any] = {
        "local_files_only": offline_only,
        "revision": args.revision,
    }
    if args.cache_dir:
        load_kwargs["cache_dir"] = args.cache_dir

    summary: dict[str, Any] = {
        "ok": True,
        "model_id": model_id,
        "model": MODEL_MAP[model_id],
        "transformers_version": api.version,
        "offline_only": offline_only,
        "cache_dir": args.cache_dir,
        "revision": args.revision,
        "class_policy": "Auto*" if args.use_auto else "BertTokenizer/BertModel",
        "loads": {},
    }

    try:
        if args.try_load_config:
            summary["loads"]["config"] = load_step("config", api.AutoConfig.from_pretrained, model_id, load_kwargs)
        if args.try_load_tokenizer:
            tokenizer_cls = api.AutoTokenizer if args.use_auto else api.BertTokenizer
            summary["loads"]["tokenizer"] = load_step("tokenizer", tokenizer_cls.from_pretrained, model_id, load_kwargs)
        if args.try_load_model:
            model_cls = api.AutoModel if args.use_auto else api.BertModel
            summary["loads"]["model"] = load_step("model", model_cls.from_pretrained, model_id, load_kwargs)
    except RuntimeError as exc:
        eprint(str(exc))
        eprint("No download was attempted." if offline_only else "Downloads were allowed for this run.")
        if args.json:
            summary["ok"] = False
            summary["error"] = "load_error"
            summary["detail"] = str(exc)
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return EXIT_LOAD_ERROR

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"OK: {model_id} is a supported HFL Chinese BERT-wwm family id.")
        print(f"Transformers: {api.version}")
        print("Class policy: use BertTokenizer/BertModel or AutoTokenizer/AutoModel; do not use RobertaTokenizer/RobertaModel.")
        print(f"Mode: {'offline/cache-only (local_files_only=True)' if offline_only else 'downloads allowed (local_files_only=False)'}")
        if args.cache_dir:
            print(f"Cache dir: {args.cache_dir}")
        if summary["loads"]:
            for label, cls_name in summary["loads"].items():
                print(f"Loaded {label}: {cls_name}")
        else:
            print("No from_pretrained loads requested; validation stopped after id and import checks.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
