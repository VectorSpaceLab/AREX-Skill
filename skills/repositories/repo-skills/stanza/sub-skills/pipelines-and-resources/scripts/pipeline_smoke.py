#!/usr/bin/env python3
"""Inspect Stanza resources and optionally run a safe pipeline smoke.

The script avoids model downloads unless --allow-download is passed.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect Stanza imports, resources, torch/CUDA, and optionally run a no-download pipeline smoke."
    )
    parser.add_argument(
        "--model-dir",
        default=None,
        help="Model cache directory to inspect. Defaults to Stanza's standard cache.",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Language code to smoke.",
    )
    parser.add_argument(
        "--processors",
        default="tokenize",
        help="Comma-separated processors for the smoke pipeline.",
    )
    parser.add_argument(
        "--package",
        default="default",
        help="Package name or bundle to request.",
    )
    parser.add_argument(
        "--text",
        default="Barack Obama was born in Hawaii.",
        help="Text to process if the smoke pipeline runs.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Pipeline device to request. Use 'auto' to let Stanza choose.",
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Allow downloads if the smoke run needs missing resources.",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Proxy URL to use for both HTTP and HTTPS when downloads are allowed.",
    )
    parser.add_argument(
        "--include-test-models",
        action="store_true",
        help="Include stanza_test fixtures in the installed-model summary.",
    )
    parser.add_argument(
        "--no-pipeline",
        action="store_true",
        help="Inspect only; skip pipeline construction.",
    )
    return parser


def _print_signature(label: str, obj) -> None:
    try:
        sig = str(inspect.signature(obj))
    except (TypeError, ValueError):
        sig = "<signature unavailable>"
    print(f"[sig] {label}{sig}")


def _missing_model_error(exc: BaseException) -> bool:
    message = str(exc)
    return (
        exc.__class__.__name__ == "LanguageNotDownloadedError"
        or exc.__class__.__name__ == "ResourcesFileNotFoundError"
        or (isinstance(exc, FileNotFoundError) and "Could not find the model file" in message)
    )


def main() -> int:
    args = build_parser().parse_args()

    try:
        import stanza
        from stanza.pipeline.core import (
            DownloadMethod,
            LanguageNotDownloadedError,
            PipelineRequirementsException,
            UnsupportedProcessorError,
        )
        from stanza.resources.common import DEFAULT_MODEL_DIR, ResourcesFileNotFoundError, load_resources_json
        from stanza.resources.list_installed import list_installed
    except Exception as exc:  # pragma: no cover - import failure is a real environment issue
        print(f"[error] stanza import failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        import torch
    except Exception as exc:  # pragma: no cover - torch may be missing in some environments
        torch = None
        torch_status = f"torch import failed: {type(exc).__name__}: {exc}"
    else:
        cuda_available = torch.cuda.is_available()
        cuda_devices = torch.cuda.device_count() if cuda_available else 0
        torch_status = (
            f"torch {torch.__version__} | cuda_available={cuda_available} | "
            f"cuda_device_count={cuda_devices}"
        )

    model_dir = Path(args.model_dir or DEFAULT_MODEL_DIR).expanduser()
    resources_path = model_dir / "resources.json"

    print(f"[stanza] version={stanza.__version__} resources={stanza.__resources_version__}")
    print(f"[python] executable={sys.executable}")
    print(f"[cache] model_dir={model_dir}")
    print(f"[cache] resources_json={'present' if resources_path.exists() else 'missing'}")
    if resources_path.exists():
        try:
            resources = load_resources_json(str(model_dir))
        except Exception as exc:
            print(f"[cache] load_resources_json failed: {type(exc).__name__}: {exc}")
        else:
            print(f"[cache] resources_languages={len(resources)} lang_known={args.lang in resources}")
    print(f"[device] {torch_status}")

    _print_signature("Pipeline", stanza.Pipeline)
    _print_signature("MultilingualPipeline", stanza.MultilingualPipeline)
    _print_signature("download", stanza.download)
    _print_signature("list_installed", list_installed)

    try:
        rows = list_installed(model_dir=str(model_dir), print_table=False, include_test_models=args.include_test_models)
    except Exception as exc:
        print(f"[cache] list_installed failed: {type(exc).__name__}: {exc}")
        rows = []
    else:
        print(f"[cache] installed_rows={len(rows)}")
        matching = [row for row in rows if row.get("lang") == args.lang]
        print(f"[cache] rows_for_lang={len(matching)}")
        for row in matching[:10]:
            package = row["package"] if row["package"] is not None else "(directory)"
            version = row["version"] or "custom"
            print(f"    - {version} {row['lang']}/{row['processor']}/{package} -> {row['path']}")
        if len(matching) > 10:
            print(f"    ... {len(matching) - 10} more")

    if args.no_pipeline:
        print("[smoke] skipped by --no-pipeline")
        return 0

    if not resources_path.exists() and not args.allow_download:
        print("[smoke] skipped: resources.json is missing and downloads are disabled")
        return 0

    download_method = DownloadMethod.DOWNLOAD_RESOURCES if args.allow_download else DownloadMethod.NONE
    pipeline_kwargs = {
        "lang": args.lang,
        "dir": str(model_dir),
        "processors": args.processors,
        "package": args.package,
        "download_method": download_method,
    }
    if args.device != "auto":
        pipeline_kwargs["device"] = args.device
    if args.allow_download and args.proxy:
        pipeline_kwargs["proxies"] = {"http": args.proxy, "https": args.proxy}

    try:
        pipe = stanza.Pipeline(**pipeline_kwargs)
    except (LanguageNotDownloadedError, ResourcesFileNotFoundError) as exc:
        if args.allow_download:
            print(f"[smoke] failed: {type(exc).__name__}: {exc}")
            return 1
        print(f"[smoke] skipped: {exc}")
        return 0
    except FileNotFoundError as exc:
        if not args.allow_download and _missing_model_error(exc):
            print(f"[smoke] skipped: {exc}")
            return 0
        print(f"[smoke] failed: {type(exc).__name__}: {exc}")
        return 1
    except UnsupportedProcessorError as exc:
        print(f"[smoke] failed: unsupported processor '{exc.processor}' for language '{exc.lang}'")
        print(f"[smoke] detail: {exc}")
        return 1
    except PipelineRequirementsException as exc:
        print(f"[smoke] failed: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - a genuine unexpected failure
        print(f"[smoke] failed: {type(exc).__name__}: {exc}")
        return 1

    print(f"[smoke] pipeline_built={pipe}")
    print(f"[smoke] selected_device={getattr(pipe, 'device', '<unknown>')}")

    try:
        doc = pipe(args.text)
    except Exception as exc:  # pragma: no cover - execution failures should be surfaced
        print(f"[smoke] run failed: {type(exc).__name__}: {exc}")
        return 1

    sentence_count = len(doc.sentences)
    word_count = sum(len(sentence.words) for sentence in doc.sentences)
    print(f"[smoke] sentences={sentence_count} words={word_count}")
    if doc.sentences:
        first_tokens = [token.text for token in doc.sentences[0].tokens]
        print(f"[smoke] first_sentence_tokens={' | '.join(first_tokens)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
