#!/usr/bin/env python3
"""Safe parameterized Qwen-VL inference helper.

This helper is adapted from the public Qwen-VL quickstart/tutorial patterns,
but it has no dependency on bundled demo assets. It loads a user-selected model
only when the script is explicitly invoked. `--help` uses only the Python
standard library.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


_BOX_CLEAN_RE = re.compile(
    r"<ref>(.*?)</ref>(?:<box>.*?</box>)*(?:<quad>.*?</quad>)*",
    flags=re.DOTALL,
)


def clean_grounding_markup(response: str) -> str:
    """Return display text with Qwen-VL grounding tags removed.

    Keep the original response if you still need to render boxes; the tokenizer
    renderer expects the raw <ref>/<box>/<quad> markup.
    """

    return _BOX_CLEAN_RE.sub(r"\1", response).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a single Qwen-VL/Qwen-VL-Chat inference request with a user "
            "image path or URL. The command may download model weights unless "
            "--local-files-only or a local model directory is used."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--model-id",
        default="Qwen/Qwen-VL-Chat",
        help=(
            "Model ID or local snapshot directory. Typical values: "
            "Qwen/Qwen-VL-Chat, Qwen/Qwen-VL-Chat-Int4, Qwen/Qwen-VL; "
            "ModelScope mirrors use qwen/... IDs with --source modelscope."
        ),
    )
    parser.add_argument(
        "--source",
        choices=("transformers", "modelscope"),
        default="transformers",
        help="Download/load source. ModelScope first snapshots the model, then loads the local directory.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "chat", "base"),
        default="auto",
        help="Use chat API, base generate API, or infer from the model ID.",
    )
    parser.add_argument(
        "--image",
        action="append",
        required=True,
        help="Image path or URL. Repeat this flag for multi-image prompts.",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Text prompt to ask about the image(s).",
    )
    parser.add_argument(
        "--device-map",
        default="cuda",
        help='Device placement for from_pretrained, e.g. "cuda", "auto", or "cpu".',
    )
    parser.add_argument(
        "--precision",
        choices=("none", "bf16", "fp16"),
        default="none",
        help="Optional Qwen-VL loader precision flag.",
    )
    parser.add_argument(
        "--revision",
        default=None,
        help="Optional model revision for providers that support revisions.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Avoid network downloads when loading with Transformers or compatible ModelScope versions.",
    )
    parser.add_argument(
        "--no-trust-remote-code",
        dest="trust_remote_code",
        action="store_false",
        default=True,
        help="Disable trust_remote_code. Qwen-VL usually requires remote code for multimodal APIs.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional torch random seed for more reproducible generations.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=None,
        help="Optional maximum new tokens override on model.generation_config / generate.",
    )
    sample_group = parser.add_mutually_exclusive_group()
    sample_group.add_argument(
        "--do-sample",
        dest="do_sample",
        action="store_true",
        default=None,
        help="Enable sampling in generation config.",
    )
    sample_group.add_argument(
        "--no-do-sample",
        dest="do_sample",
        action="store_false",
        default=None,
        help="Disable sampling in generation config.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Optional temperature override.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="Optional nucleus sampling top-p override.",
    )
    parser.add_argument(
        "--output-image",
        default=None,
        help="If set, render grounding boxes to this image file when the response contains boxes.",
    )
    parser.add_argument(
        "--require-box",
        action="store_true",
        help="Exit nonzero if --output-image is set but no valid box image is produced.",
    )
    parser.add_argument(
        "--clean-text",
        action="store_true",
        help="Also print a copy of the response with <ref>/<box>/<quad> markup removed.",
    )
    return parser.parse_args()


def infer_mode(model_id: str, requested: str) -> str:
    if requested != "auto":
        return requested
    normalized = model_id.rstrip("/").lower()
    # The released Int4 model is a chat checkpoint; the bare Qwen-VL ID is base.
    if normalized.endswith("qwen-vl") and "chat" not in normalized:
        return "base"
    return "chat"


def provider_model_reference(args: argparse.Namespace) -> str:
    """Return a model ID or local snapshot directory for Transformers loading."""

    if args.source == "transformers":
        return args.model_id

    # Lazy import so `--help` remains available without ModelScope installed.
    from modelscope import snapshot_download  # type: ignore

    snapshot_kwargs: dict[str, Any] = {}
    if args.revision:
        snapshot_kwargs["revision"] = args.revision
    if args.local_files_only:
        snapshot_kwargs["local_files_only"] = True
    try:
        return snapshot_download(args.model_id, **snapshot_kwargs)
    except TypeError:
        if args.local_files_only:
            raise SystemExit(
                "This ModelScope version does not accept local_files_only; "
                "use a local snapshot directory with --source transformers instead."
            )
        snapshot_kwargs.pop("local_files_only", None)
        return snapshot_download(args.model_id, **snapshot_kwargs)


def build_load_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "device_map": args.device_map,
        "trust_remote_code": args.trust_remote_code,
    }
    if args.source == "transformers" and args.revision:
        kwargs["revision"] = args.revision
    if args.source == "transformers" and args.local_files_only:
        kwargs["local_files_only"] = True
    if args.precision == "bf16":
        kwargs["bf16"] = True
    elif args.precision == "fp16":
        kwargs["fp16"] = True
    return kwargs


def build_tokenizer_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"trust_remote_code": args.trust_remote_code}
    if args.source == "transformers" and args.revision:
        kwargs["revision"] = args.revision
    if args.source == "transformers" and args.local_files_only:
        kwargs["local_files_only"] = True
    return kwargs


def apply_generation_config(model: Any, model_ref: str, args: argparse.Namespace) -> dict[str, Any]:
    """Load and override GenerationConfig when available.

    Returns kwargs that are also safe to pass directly to model.generate for the
    base-model path.
    """

    from transformers.generation import GenerationConfig

    config_kwargs: dict[str, Any] = {"trust_remote_code": args.trust_remote_code}
    if args.source == "transformers" and args.revision:
        config_kwargs["revision"] = args.revision
    if args.source == "transformers" and args.local_files_only:
        config_kwargs["local_files_only"] = True

    try:
        model.generation_config = GenerationConfig.from_pretrained(model_ref, **config_kwargs)
    except Exception as exc:  # noqa: BLE001 - continue with model defaults.
        print(f"[warn] Could not load GenerationConfig: {exc}", file=sys.stderr)

    direct_generate_kwargs: dict[str, Any] = {}
    for attr in ("max_new_tokens", "do_sample", "temperature", "top_p"):
        value = getattr(args, attr)
        if value is None:
            continue
        direct_generate_kwargs[attr] = value
        if hasattr(model, "generation_config") and model.generation_config is not None:
            setattr(model.generation_config, attr, value)
    return direct_generate_kwargs


def build_query(tokenizer: Any, images: list[str], prompt: str) -> str:
    """Build the Qwen-VL multimodal prompt using the documented list format."""

    items: list[dict[str, str]] = [{"image": image} for image in images]
    items.append({"text": prompt})
    return tokenizer.from_list_format(items)


def move_inputs_to_model(inputs: Any, model: Any) -> Any:
    """Move tokenized inputs to the model's primary device when possible."""

    device = getattr(model, "device", None)
    if device is not None:
        try:
            return inputs.to(device)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] Could not move inputs to model.device={device}: {exc}", file=sys.stderr)
    return inputs


def maybe_render_boxes(tokenizer: Any, response: str, history: Any, mode: str, output_image: str | None) -> bool:
    if not output_image:
        return False

    if mode == "chat":
        image = tokenizer.draw_bbox_on_latest_picture(response, history)
    else:
        image = tokenizer.draw_bbox_on_latest_picture(response)

    if image is None:
        print("[warn] No bounding-box image was produced from the response.", file=sys.stderr)
        return False

    output_path = Path(output_image)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    print(f"[info] Saved rendered boxes to {output_path}", file=sys.stderr)
    return True


def main() -> int:
    args = parse_args()
    mode = infer_mode(args.model_id, args.mode)

    # Heavy ML imports happen only after argument parsing, so `--help` is cheap.
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if args.seed is not None:
        torch.manual_seed(args.seed)

    model_ref = provider_model_reference(args)

    tokenizer = AutoTokenizer.from_pretrained(model_ref, **build_tokenizer_kwargs(args))
    if args.source == "modelscope" and not hasattr(tokenizer, "model_dir"):
        tokenizer.model_dir = model_ref

    model = AutoModelForCausalLM.from_pretrained(model_ref, **build_load_kwargs(args)).eval()
    generate_kwargs = apply_generation_config(model, model_ref, args)

    query = build_query(tokenizer, args.image, args.prompt)

    history = None
    if mode == "chat":
        response, history = model.chat(tokenizer, query=query, history=None)
    else:
        inputs = tokenizer(query, return_tensors="pt")
        inputs = move_inputs_to_model(inputs, model)
        pred = model.generate(**inputs, **generate_kwargs)
        response = tokenizer.decode(pred.cpu()[0], skip_special_tokens=False)

    print(response)

    if args.clean_text:
        print("\n[cleaned]")
        print(clean_grounding_markup(response))

    rendered = maybe_render_boxes(tokenizer, response, history, mode, args.output_image)
    if args.output_image and args.require_box and not rendered:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
