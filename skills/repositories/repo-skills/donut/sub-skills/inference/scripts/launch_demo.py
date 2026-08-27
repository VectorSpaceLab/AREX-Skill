#!/usr/bin/env python3
"""Launch the bundled Gradio demo for a Donut checkpoint."""

import argparse

from run_inference import build_task_prompt, coerce_pil_image, load_donut_model, predict_with_prompt


def build_parser():
    parser = argparse.ArgumentParser(
        description="Launch the Donut Gradio demo for a local or Hub checkpoint."
    )
    parser.add_argument(
        "--model",
        "--pretrained-path",
        dest="model",
        default="naver-clova-ix/donut-base-finetuned-docvqa",
        help="Hugging Face model ID or local checkpoint directory.",
    )
    parser.add_argument(
        "--task",
        default="docvqa",
        help="Task token family used to build the demo prompt.",
    )
    parser.add_argument(
        "--host",
        "--url",
        dest="host",
        default=None,
        help="Gradio bind address. Use 0.0.0.0 for remote access.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Gradio port.",
    )
    parser.add_argument(
        "--sample-image",
        dest="sample_image",
        help="Optional local image path to seed the demo examples.",
    )
    parser.add_argument(
        "--sample-question",
        dest="sample_question",
        default=None,
        help="Optional question text for a DocVQA sample example.",
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
        "--share",
        action="store_true",
        help="Ask Gradio to create a temporary public share link.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional demo title.",
    )
    return parser


def make_predict_fn(model, task):
    def _predict(image_like, question=None):
        try:
            prompt = build_task_prompt(task, question if task == "docvqa" else None)
            image = coerce_pil_image(image_like)
            return predict_with_prompt(model, image, prompt, return_json=True)
        except Exception as exc:  # pragma: no cover - user-facing demo path
            return {"error": str(exc)}

    return _predict


def build_examples(task, sample_image, sample_question):
    if not sample_image:
        return None
    if task == "docvqa":
        if not sample_question or not str(sample_question).strip():
            return None
        return [[sample_image, str(sample_question).strip()]]
    return [[sample_image]]


def main(argv=None):
    parser = build_parser()
    args, _ = parser.parse_known_args(argv)

    try:
        model, resolved_device = load_donut_model(
            args.model,
            device=args.device,
            local_files_only=args.local_files_only,
        )
    except Exception as exc:
        raise SystemExit(f"Failed to load Donut checkpoint {args.model!r}: {exc}") from exc

    import gradio as gr

    task = args.task.strip().lower()
    predict_fn = make_predict_fn(model, task)

    if task == "docvqa":
        inputs = [gr.Image(type="numpy", label="Image"), gr.Textbox(label="Question")]
    else:
        inputs = gr.Image(type="numpy", label="Image")

    examples = build_examples(task, args.sample_image, args.sample_question)
    title = args.title or f"Donut {task} demo ({resolved_device})"

    demo = gr.Interface(
        fn=predict_fn,
        inputs=inputs,
        outputs=gr.JSON(label="Prediction"),
        title=title,
        examples=examples,
    )
    demo.launch(server_name=args.host, server_port=args.port, share=args.share)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
