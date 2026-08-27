#!/usr/bin/env python3
"""Run a single-image Donut inference pass or compare prompt variants."""

import argparse
import json
from pathlib import Path

DEFAULT_TASK = "cord"
DOCVQA_TASK = "docvqa"


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run Donut inference on one image and print JSON results."
    )
    parser.add_argument(
        "--model",
        "--pretrained-model-name-or-path",
        dest="model",
        required=True,
        help="Hugging Face model ID or local checkpoint directory.",
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to a local document image.",
    )
    parser.add_argument(
        "--task",
        default=DEFAULT_TASK,
        help="Task token family, such as cord, rvlcdip, or docvqa.",
    )
    parser.add_argument(
        "--question",
        help="DocVQA question text. Only used when --task docvqa is selected and --prompt is not supplied.",
    )
    parser.add_argument(
        "--prompt",
        action="append",
        help="Explicit prompt string. Repeat the flag to compare prompt variants.",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Choose the execution device explicitly or let the helper pick CUDA when available.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Disable Hugging Face downloads and require a local checkpoint.",
    )
    parser.add_argument(
        "--raw-token",
        action="store_true",
        help="Return the raw decoded token string instead of parsed JSON.",
    )
    parser.add_argument(
        "--output",
        help="Optional file path for the JSON report.",
    )
    return parser


def build_task_prompt(task, question=None):
    task = (task or "").strip().lower()
    if task == DOCVQA_TASK:
        if not question or not str(question).strip():
            raise ValueError("DocVQA inference needs --question when --prompt is not supplied.")
        question = str(question).strip()
        return f"<s_docvqa><s_question>{question}</s_question><s_answer>"
    if not task:
        raise ValueError("A task name or an explicit prompt is required.")
    return f"<s_{task}>"


def coerce_pil_image(image_like):
    from PIL import Image

    if isinstance(image_like, Image.Image):
        return image_like.convert("RGB")
    if isinstance(image_like, (str, bytes, Path)):
        return Image.open(str(image_like)).convert("RGB")
    try:
        return Image.fromarray(image_like).convert("RGB")
    except Exception as exc:  # pragma: no cover - defensive path for odd inputs
        raise TypeError(
            "Expected a PIL image, a local image path, or an array-like object that PIL can convert."
        ) from exc


def load_donut_model(model_name_or_path, device="auto", local_files_only=False):
    import torch
    from donut import DonutModel

    model = DonutModel.from_pretrained(
        model_name_or_path,
        local_files_only=local_files_only,
    )

    resolved_device = device
    if resolved_device == "auto":
        resolved_device = "cuda" if torch.cuda.is_available() else "cpu"

    if resolved_device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")
        model.half()
        model.to("cuda")
    else:
        model.to("cpu")

    model.eval()
    return model, resolved_device


def predict_with_prompt(model, image_like, prompt, return_json=True):
    image = coerce_pil_image(image_like)
    output = model.inference(image=image, prompt=prompt, return_json=return_json)
    return output["predictions"][0]


def build_result_report(model_name, device, image_path, prompt_results, raw_token):
    return {
        "model": model_name,
        "device": device,
        "image": str(image_path),
        "return_json": not raw_token,
        "results": prompt_results,
    }


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.prompt:
            prompts = [prompt for prompt in args.prompt if prompt and str(prompt).strip()]
            if len(prompts) != len(args.prompt):
                parser.error("Each --prompt value must be a non-empty string.")
        else:
            prompts = [build_task_prompt(args.task, args.question)]
    except ValueError as exc:
        parser.error(str(exc))

    image_path = Path(args.image)

    try:
        model, resolved_device = load_donut_model(
            args.model,
            device=args.device,
            local_files_only=args.local_files_only,
        )
    except Exception as exc:
        raise SystemExit(f"Failed to load Donut checkpoint {args.model!r}: {exc}") from exc

    results = []
    for prompt in prompts:
        results.append(
            {
                "prompt": prompt,
                "prediction": predict_with_prompt(
                    model,
                    image_path,
                    prompt,
                    return_json=not args.raw_token,
                ),
            }
        )

    report = build_result_report(args.model, resolved_device, image_path, results, args.raw_token)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
