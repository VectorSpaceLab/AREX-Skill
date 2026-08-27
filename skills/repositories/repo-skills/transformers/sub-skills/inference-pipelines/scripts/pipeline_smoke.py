#!/usr/bin/env python3
"""Dry-run-first smoke helper for Transformers pipelines.

The default mode avoids downloads and model construction. Use --run only when
required weights and optional dependencies are available locally, or when network
access is intentionally allowed by omitting --local-files-only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from typing import Any


CLASSIFICATION_TASKS = {
    "audio-classification",
    "image-classification",
    "text-classification",
    "video-classification",
    "zero-shot-audio-classification",
    "zero-shot-image-classification",
}

GENERATION_TASKS = {
    "text-generation",
    "text2text-generation",
    "summarization",
    "translation",
    "image-to-text",
    "image-text-to-text",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Transformers pipeline arguments and optionally run one tiny inference call.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--task", required=True, help="Pipeline task id, for example text-classification.")
    parser.add_argument("--model", help="Hub id or local model directory. Prefer a local path with --local-files-only for smoke tests.")
    parser.add_argument("--text", default="A tiny Transformers pipeline smoke test.", help="Tiny text prompt/input for runnable text tasks.")
    parser.add_argument("--image", help="Local image path for image tasks when --run is set.")
    parser.add_argument("--audio", help="Local audio path for audio tasks when --run is set.")
    parser.add_argument("--video", help="Local video path for video tasks when --run is set.")
    parser.add_argument("--question", default="What is shown?", help="Question for QA or visual/document QA tasks.")
    parser.add_argument("--candidate-labels", nargs="*", default=["positive", "negative"], help="Labels for zero-shot tasks.")
    parser.add_argument("--device", default="-1", help="Pipeline device, such as -1, 0, cuda:0, or mps. Ignored when --device-map is set.")
    parser.add_argument("--device-map", help="Device map such as auto. Do not combine with --device for real runs.")
    parser.add_argument("--dtype", default="auto", help="Pipeline dtype, for example auto, float16, bfloat16, or float32.")
    parser.add_argument("--revision", help="Hub revision/tag/commit to pin model loading.")
    parser.add_argument("--local-files-only", action="store_true", help="Require local cache/files and avoid network access.")
    parser.add_argument("--trust-remote-code", action="store_true", help="Allow custom model repo code. Use only after review.")
    parser.add_argument("--run", action="store_true", help="Construct the pipeline and run one tiny call. Default is dry-run advice only.")
    return parser.parse_args()


def require_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def parse_device(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def summarize(value: Any) -> str:
    text = repr(value)
    if len(text) > 800:
        text = text[:797] + "..."
    return text


def build_pipeline_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "task": args.task,
        "dtype": args.dtype,
        "local_files_only": args.local_files_only,
        "trust_remote_code": args.trust_remote_code,
    }
    if args.model:
        kwargs["model"] = args.model
    if args.revision:
        kwargs["revision"] = args.revision
    if args.device_map:
        kwargs["device_map"] = args.device_map
    else:
        kwargs["device"] = parse_device(args.device)
    return kwargs


def sample_call(args: argparse.Namespace) -> tuple[tuple[Any, ...], dict[str, Any]]:
    task = args.task
    if task in {"text-classification", "sentiment-analysis", "fill-mask", "text-generation", "text2text-generation", "summarization", "translation"}:
        return (args.text,), {"max_new_tokens": 8} if task in GENERATION_TASKS else {}
    if task in {"zero-shot-classification"}:
        return (args.text,), {"candidate_labels": args.candidate_labels}
    if task in {"question-answering"}:
        return (), {"question": args.question, "context": args.text}
    if task in {"token-classification", "ner"}:
        return (args.text,), {}
    if task in {"image-classification", "image-segmentation", "object-detection", "depth-estimation", "image-feature-extraction"}:
        if not args.image:
            raise ValueError(f"Task {task!r} needs --image for --run.")
        return (), {"images": args.image}
    if task in {"visual-question-answering", "document-question-answering"}:
        if not args.image:
            raise ValueError(f"Task {task!r} needs --image for --run.")
        return (), {"image": args.image, "question": args.question}
    if task in {"automatic-speech-recognition", "audio-classification", "zero-shot-audio-classification"}:
        if not args.audio:
            raise ValueError(f"Task {task!r} needs --audio for --run.")
        if task == "zero-shot-audio-classification":
            return (args.audio,), {"candidate_labels": args.candidate_labels}
        return (args.audio,), {}
    if task in {"video-classification"}:
        if not args.video:
            raise ValueError(f"Task {task!r} needs --video for --run.")
        return (args.video,), {}
    return (args.text,), {}


def expected_shape_advice(task: str) -> str:
    if task in CLASSIFICATION_TASKS:
        return "Expected classification-like output: list of dicts containing label/score keys."
    if task in GENERATION_TASKS:
        return "Expected generation-like output: list of dicts, often containing generated_text or task-specific generated content."
    if task == "automatic-speech-recognition":
        return "Expected ASR output: dict containing text, optionally chunks/timestamps."
    if task in {"object-detection", "zero-shot-object-detection"}:
        return "Expected detection output: list/dicts with labels, scores, and boxes."
    if task in {"image-segmentation", "mask-generation"}:
        return "Expected segmentation output: masks plus labels/scores depending on task."
    if task in {"question-answering", "visual-question-answering", "document-question-answering"}:
        return "Expected QA output: answer dictionaries; exact keys depend on task."
    return "Expected output shape is task-specific; assert concrete keys after one representative call."


def main() -> int:
    args = parse_args()

    if not require_module("transformers"):
        print("ERROR: transformers is not importable in this Python environment.", file=sys.stderr)
        return 2

    try:
        import transformers
        from transformers import AutoConfig, pipeline
    except Exception as exc:
        print(f"ERROR: transformers import failed with {exc.__class__.__name__}: {exc}", file=sys.stderr)
        print("Advice: install the package's required runtime dependencies before pipeline validation.", file=sys.stderr)
        return 2

    print(f"transformers_version={transformers.__version__}")
    print(f"task={args.task}")
    print(f"model={args.model or '<default-model-if-running>'}")
    print(f"local_files_only={args.local_files_only}")

    if args.device_map and args.device != "-1":
        print("WARNING: --device-map is set; --device is ignored by this smoke helper to avoid placement conflicts.")

    if args.task.startswith("image") or args.task in {"object-detection", "depth-estimation", "visual-question-answering"}:
        if not require_module("PIL"):
            print("WARNING: Pillow is not importable; many image pipelines need it.")
    if args.task.startswith("audio") or args.task == "automatic-speech-recognition":
        if not require_module("torch"):
            print("WARNING: torch is not importable; most audio pipelines need a backend model framework.")
    if args.task == "video-classification":
        print("NOTE: video pipelines also need a working video decoder stack such as decord or PyAV.")

    if args.model:
        try:
            config = AutoConfig.from_pretrained(
                args.model,
                revision=args.revision,
                local_files_only=args.local_files_only,
                trust_remote_code=args.trust_remote_code,
            )
            print(f"config_ok model_type={getattr(config, 'model_type', '<unknown>')}")
        except Exception as exc:
            print(f"config_check_failed={exc.__class__.__name__}: {exc}")
            if args.local_files_only:
                print("Advice: verify the local model directory/cache contains config.json and required component files.")
            if not args.run:
                print("Dry-run complete despite config failure; use --run only after resolving config/model source issues.")
                return 0
            return 3

    kwargs = build_pipeline_kwargs(args)
    printable_kwargs = {key: ("<redacted>" if key == "token" else value) for key, value in kwargs.items()}
    print("pipeline_kwargs=" + json.dumps(printable_kwargs, sort_keys=True, default=str))
    print(expected_shape_advice(args.task))

    if not args.run:
        print("dry_run_only=true")
        print("Add --run to construct the pipeline and execute one tiny call when dependencies and model files are ready.")
        return 0

    try:
        pipe = pipeline(**kwargs)
        call_args, call_kwargs = sample_call(args)
        output = pipe(*call_args, **call_kwargs)
        print("pipeline_constructed=true")
        print("output_summary=" + summarize(output))
    except Exception as exc:
        print(f"pipeline_smoke_failed={exc.__class__.__name__}: {exc}", file=sys.stderr)
        print("Advice: remove batching/accelerators/dtype first, verify optional dependencies, then validate task/model compatibility.")
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
