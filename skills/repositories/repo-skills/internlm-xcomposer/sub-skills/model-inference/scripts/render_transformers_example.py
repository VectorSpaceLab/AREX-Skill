#!/usr/bin/env python3
"""Render or validate a safe InternLM-XComposer Transformers example.

This helper is stdlib-only. It never imports torch, transformers, accelerate,
PIL, or any checkpoint-backed code. It prints a user-editable example script
or a short validation report that helps confirm prompt shape, placeholder
counts, and multi-GPU rendering choices before execution in a real runtime.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import List, Sequence

CURRENT_MODEL_ID = "internlm/internlm-xcomposer2d5-7b"
LEGACY2_MODEL_ID = "internlm/internlm-xcomposer2-vl-7b"
LEGACY1_MODEL_ID = "internlm/internlm-xcomposer-7b"


@dataclass
class ValidationResult:
    ok: bool
    messages: List[str]


def count_placeholders(query: str) -> int:
    return query.count("<ImageHere>")


def pick(value, default):
    return default if value is None else value


def effective_hd_num(args: argparse.Namespace) -> int:
    if args.task == "write-artical":
        return pick(args.hd_num, 25)
    if args.task == "legacy-2-4khd":
        return pick(args.hd_num, 55)
    return pick(args.hd_num, 24)


def accelerate_import(args: argparse.Namespace) -> str:
    return "from accelerate import dispatch_model" if args.num_gpus > 1 else ""


def dispatch_model_lines(args: argparse.Namespace) -> str:
    if args.num_gpus <= 1:
        return ""
    return f"device_map = auto_configure_device_map({args.num_gpus})\nmodel = dispatch_model(model, device_map=device_map)"


def build_device_map_function(num_gpus: int, family: str) -> str:
    if num_gpus <= 1:
        return ""
    if family == "current":
        return dedent(
            """
            def auto_configure_device_map(num_gpus):
                num_trans_layers = 32
                per_gpu_layers = 38 / num_gpus
                device_map = {
                    'vit': 0,
                    'vision_proj': 0,
                    'model.tok_embeddings': 0,
                    'plora_glb_GN': 0,
                    'plora_sub_GN': 0,
                    'model.norm': num_gpus - 1,
                    'output': num_gpus - 1,
                }
                used = 3
                gpu_target = 0
                for i in range(num_trans_layers):
                    if used >= per_gpu_layers:
                        gpu_target += 1
                        used = 0
                    assert gpu_target < num_gpus
                    device_map[f'model.layers.{i}'] = gpu_target
                    used += 1
                return device_map
            """
        ).strip()
    return dedent(
        """
        def auto_configure_device_map(num_gpus):
            num_trans_layers = 32
            per_gpu_layers = 38 / num_gpus
            device_map = {
                'visual_encoder': 0,
                'ln_vision': 0,
                'Qformer': 0,
                'internlm_model.model.embed_tokens': 0,
                'internlm_model.model.norm': 0,
                'internlm_model.lm_head': 0,
                'query_tokens': 0,
                'flag_image_start': 0,
                'flag_image_end': 0,
                'internlm_proj.weight': 0,
                'internlm_proj.bias': 0,
            }
            used = 6
            gpu_target = 0
            for i in range(num_trans_layers):
                if used >= per_gpu_layers:
                    gpu_target += 1
                    used = 0
                assert gpu_target < num_gpus
                device_map[f'internlm_model.model.layers.{i}'] = gpu_target
                used += 1
            return device_map
        """
    ).strip()


def current_chat_template(args: argparse.Namespace) -> str:
    image_literal = "[]" if not args.image else repr(args.image)
    query = args.query or "Analyze the given image in a detailed manner"
    return dedent(
        f"""
        import torch
        from transformers import AutoModel, AutoTokenizer
        {accelerate_import(args)}

        torch.set_grad_enabled(False)
        model_id = {CURRENT_MODEL_ID!r}
        model = AutoModel.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        ).cuda().eval().half()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model.tokenizer = tokenizer

        {build_device_map_function(args.num_gpus, 'current')}
        {dispatch_model_lines(args)}

        query = {query!r}
        image = {image_literal}
        with torch.autocast(device_type='cuda', dtype=torch.float16):
            response, history = model.chat(
                tokenizer,
                query,
                image,
                hd_num={effective_hd_num(args)},
                do_sample={pick(args.do_sample, False)},
                num_beams={pick(args.num_beams, 3)},
                use_meta={pick(args.use_meta, True)},
            )
        print(response)
        """
    ).strip() + "\n"


def current_multi_image_template(args: argparse.Namespace) -> str:
    query = args.query or "Image1 <ImageHere>; Image2 <ImageHere>; compare the images"
    image_literal = repr(args.image)
    return dedent(
        f"""
        import torch
        from transformers import AutoModel, AutoTokenizer
        {accelerate_import(args)}

        torch.set_grad_enabled(False)
        model_id = {CURRENT_MODEL_ID!r}
        model = AutoModel.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        ).cuda().eval().half()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model.tokenizer = tokenizer

        {build_device_map_function(args.num_gpus, 'current')}
        {dispatch_model_lines(args)}

        query = {query!r}
        image = {image_literal}
        with torch.autocast(device_type='cuda', dtype=torch.float16):
            response, history = model.chat(
                tokenizer,
                query,
                image,
                hd_num={effective_hd_num(args)},
                do_sample={pick(args.do_sample, False)},
                num_beams={pick(args.num_beams, 3)},
                use_meta={pick(args.use_meta, True)},
            )
        print(response)
        """
    ).strip() + "\n"


def current_video_template(args: argparse.Namespace) -> str:
    query = args.query or "Here are some frames of a video. Describe this video in detail"
    image_literal = repr(args.image)
    return dedent(
        f"""
        import torch
        from transformers import AutoModel, AutoTokenizer
        {accelerate_import(args)}

        torch.set_grad_enabled(False)
        model_id = {CURRENT_MODEL_ID!r}
        model = AutoModel.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        ).cuda().eval().half()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model.tokenizer = tokenizer

        {build_device_map_function(args.num_gpus, 'current')}
        {dispatch_model_lines(args)}

        query = {query!r}
        image = {image_literal}
        with torch.autocast(device_type='cuda', dtype=torch.float16):
            response, history = model.chat(
                tokenizer,
                query,
                image,
                hd_num={effective_hd_num(args)},
                do_sample={pick(args.do_sample, False)},
                num_beams={pick(args.num_beams, 3)},
                use_meta={pick(args.use_meta, True)},
            )
        print(response)
        """
    ).strip() + "\n"


def current_webpage_template(args: argparse.Namespace, mode: str) -> str:
    image_literal = repr(args.image)
    task_name = args.task_name or {
        "write-webpage": "Instruction-aware Webpage Generation",
        "resume-webpage": "Resume-to-Personal Page",
        "screen-webpage": "Screenshot-to-Webpage",
    }[mode]
    common_kwargs = (
        f"image={image_literal}, "
        f"max_new_tokens={pick(args.max_new_tokens, 4800)}, "
        f"do_sample={pick(args.do_sample, True)}, "
        f"num_beams={pick(args.num_beams, 2)}, "
        f"temperature={pick(args.temperature, 1.0)}, "
        f"repetition_penalty={pick(args.repetition_penalty, 3.0)}, "
        f"seed={pick(args.seed, 202)}, "
        f"use_meta={pick(args.use_meta, False)}, "
        f"task={task_name!r}"
    )
    if mode == "write-webpage":
        call = f"response = model.write_webpage({args.query!r}, {common_kwargs})"
    elif mode == "resume-webpage":
        call = f"response = model.resume_2_webpage({args.resume_path!r}, {common_kwargs})"
    else:
        call = f"response = model.screen_2_webpage({args.query!r}, {common_kwargs})"
    return dedent(
        f"""
        import torch
        from transformers import AutoModel, AutoTokenizer

        torch.set_grad_enabled(False)
        model_id = {CURRENT_MODEL_ID!r}
        model = AutoModel.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        ).cuda().eval().half()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model.tokenizer = tokenizer

        {call}
        print(response)
        """
    ).strip() + "\n"


def current_article_template(args: argparse.Namespace) -> str:
    image_literal = repr(args.image)
    query = args.query or "Write a blog about French pastries"
    return dedent(
        f"""
        import torch
        from transformers import AutoModel, AutoTokenizer

        torch.set_grad_enabled(False)
        model_id = {CURRENT_MODEL_ID!r}
        model = AutoModel.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        ).cuda().eval().half()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model.tokenizer = tokenizer

        query = {query!r}
        image = {image_literal}
        with torch.autocast(device_type='cuda', dtype=torch.float16):
            response = model.write_artical(
                query,
                image=image,
                hd_num={effective_hd_num(args)},
                max_new_tokens={pick(args.max_new_tokens, 1024)},
                do_sample={pick(args.do_sample, True)},
                num_beams={pick(args.num_beams, 1)},
                top_p={pick(args.top_p, 0.8)},
                repetition_penalty={pick(args.repetition_penalty, 1.005)},
                max_length={pick(args.max_length, 8192)},
                seed={pick(args.seed, 8192)},
                use_meta={pick(args.use_meta, False)},
            )
        print(response)
        """
    ).strip() + "\n"


def legacy2_chat_template(args: argparse.Namespace) -> str:
    image = args.image[0] if args.image else "examples/image1.webp"
    query = args.query or "Please describe this image in detail."
    return dedent(
        f"""
        import torch
        from transformers import AutoModel, AutoTokenizer
        {accelerate_import(args)}

        torch.set_grad_enabled(False)
        model_id = {LEGACY2_MODEL_ID!r}
        model = AutoModel.from_pretrained(model_id, trust_remote_code=True).eval()
        model.half().cuda()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

        {build_device_map_function(args.num_gpus, 'legacy2')}
        {dispatch_model_lines(args)}

        text = {query!r}
        image = {image!r}
        with torch.cuda.amp.autocast():
            with torch.no_grad():
                response, history = model.chat(tokenizer, query=text, image=image, history=[], do_sample=False)
        print(response)
        """
    ).strip() + "\n"


def legacy2_4khd_template(args: argparse.Namespace) -> str:
    image = args.image[0] if args.image else "examples/image1.webp"
    query = args.query or "Please describe this image in detail."
    return dedent(
        f"""
        import torch
        from transformers import AutoModel, AutoTokenizer
        {accelerate_import(args)}

        torch.set_grad_enabled(False)
        model_id = "internlm/internlm-xcomposer2-4khd-7b"
        model = AutoModel.from_pretrained(model_id, torch_dtype=torch.bfloat16, trust_remote_code=True).cuda().eval()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model.tokenizer = tokenizer

        {build_device_map_function(args.num_gpus, 'legacy2')}
        {dispatch_model_lines(args)}

        text = {query!r}
        image = {image!r}
        with torch.cuda.amp.autocast():
            with torch.no_grad():
                response, history = model.chat(
                    tokenizer,
                    query=text,
                    image=image,
                    hd_num={effective_hd_num(args)},
                    history=[],
                    do_sample=False,
                    num_beams={pick(args.num_beams, 3)},
                )
        print(response)
        """
    ).strip() + "\n"


def legacy1_generate_template(args: argparse.Namespace) -> str:
    image = args.image[0] if args.image else "examples/images/aiyinsitan.jpg"
    query = args.query or "请介绍下爱因斯坦的生平"
    return dedent(
        f"""
        import torch
        from transformers import AutoModel, AutoTokenizer
        {accelerate_import(args)}

        torch.set_grad_enabled(False)
        model_id = {LEGACY1_MODEL_ID!r}
        model = AutoModel.from_pretrained(model_id, trust_remote_code=True).cuda().eval()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model.tokenizer = tokenizer

        {build_device_map_function(args.num_gpus, 'legacy1')}
        {dispatch_model_lines(args)}

        text = {query!r}
        image = {image!r}
        response = model.generate(text, image)
        print(response)
        """
    ).strip() + "\n"


def legacy1_chat_template(args: argparse.Namespace) -> str:
    image = args.image[0] if args.image else "examples/images/aiyinsitan.jpg"
    query = args.query or "图片里面的是谁？"
    return dedent(
        f"""
        import torch
        from transformers import AutoModel, AutoTokenizer
        {accelerate_import(args)}

        torch.set_grad_enabled(False)
        model_id = {LEGACY1_MODEL_ID!r}
        model = AutoModel.from_pretrained(model_id, trust_remote_code=True).cuda().eval()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model.tokenizer = tokenizer

        {build_device_map_function(args.num_gpus, 'legacy1')}
        {dispatch_model_lines(args)}

        text = {query!r}
        image = {image!r}
        response, history = model.chat(text=text, image=image, history=None)
        print(response)
        """
    ).strip() + "\n"


def build_rendered_script(args: argparse.Namespace) -> str:
    if args.task == "chat":
        return current_chat_template(args)
    if args.task == "multi-image":
        return current_multi_image_template(args)
    if args.task == "video":
        return current_video_template(args)
    if args.task == "write-webpage":
        return current_webpage_template(args, "write-webpage")
    if args.task == "resume-webpage":
        return current_webpage_template(args, "resume-webpage")
    if args.task == "screen-webpage":
        return current_webpage_template(args, "screen-webpage")
    if args.task == "write-artical":
        return current_article_template(args)
    if args.task == "legacy-2-chat":
        return legacy2_chat_template(args)
    if args.task == "legacy-2-4khd":
        return legacy2_4khd_template(args)
    if args.task == "legacy-1-generate":
        return legacy1_generate_template(args)
    if args.task == "legacy-1-chat":
        return legacy1_chat_template(args)
    raise ValueError(f"Unsupported task: {args.task}")


def validate(args: argparse.Namespace) -> ValidationResult:
    messages: List[str] = []
    ok = True

    if args.task == "multi-image":
        placeholder_count = count_placeholders(args.query or "")
        image_count = len(args.image)
        if image_count != placeholder_count:
            ok = False
            messages.append(f"placeholder count {placeholder_count} does not match image count {image_count}")
    elif args.task == "screen-webpage" and not args.image:
        ok = False
        messages.append("screen-webpage needs at least one image")
    elif args.task in {"chat", "video", "legacy-2-chat", "legacy-2-4khd", "legacy-1-generate", "legacy-1-chat"} and not args.image:
        messages.append("no image provided; the rendered script will fall back to the default example image/video path")

    if args.num_gpus < 1:
        ok = False
        messages.append("num-gpus must be at least 1")
    if args.hd_num is not None and args.hd_num < -1:
        ok = False
        messages.append("hd-num must be -1 or a non-negative integer")
    if args.max_new_tokens is not None and args.max_new_tokens < 1:
        ok = False
        messages.append("max-new-tokens must be positive")
    if args.max_length is not None and args.max_length < 1:
        ok = False
        messages.append("max-length must be positive")
    if args.temperature is not None and args.temperature <= 0:
        ok = False
        messages.append("temperature must be positive")
    if args.top_p is not None and not (0.0 < args.top_p <= 1.0):
        ok = False
        messages.append("top-p must be in (0, 1]")
    if args.repetition_penalty is not None and args.repetition_penalty < 1.0:
        ok = False
        messages.append("repetition-penalty should be >= 1.0")
    if args.task == "resume-webpage" and not args.resume_path:
        ok = False
        messages.append("resume-webpage needs --resume-path")

    return ValidationResult(ok=ok, messages=messages)


def render_report(args: argparse.Namespace, script: str, result: ValidationResult) -> str:
    lines = [
        "# Rendered InternLM-XComposer Transformers example",
        "",
        f"- task: `{args.task}`",
        f"- model id: `{CURRENT_MODEL_ID if args.task.startswith('write') or args.task in {'chat', 'multi-image', 'video', 'resume-webpage', 'screen-webpage'} else (LEGACY2_MODEL_ID if args.task.startswith('legacy-2') else LEGACY1_MODEL_ID)}`",
        f"- num gpus: `{args.num_gpus}`",
        f"- hd_num: `{effective_hd_num(args)}`",
        f"- images: `{len(args.image)}`",
        f"- placeholder count: `{count_placeholders(args.query or '')}`",
        f"- validation: `{ 'ok' if result.ok else 'failed' }`",
        "",
    ]
    if result.messages:
        lines.append("## Validation notes")
        lines.append("")
        for msg in result.messages:
            lines.append(f"- {msg}")
        lines.append("")
    lines.append("## Script")
    lines.append("")
    lines.append("```python")
    lines.append(script.rstrip())
    lines.append("```")
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render or validate a safe InternLM-XComposer Transformers example.")
    parser.add_argument(
        "--task",
        required=True,
        choices=[
            "chat",
            "multi-image",
            "video",
            "write-webpage",
            "resume-webpage",
            "screen-webpage",
            "write-artical",
            "legacy-2-chat",
            "legacy-2-4khd",
            "legacy-1-generate",
            "legacy-1-chat",
        ],
        help="Which example family to render.",
    )
    parser.add_argument("--query", default="", help="Prompt text used in the rendered example.")
    parser.add_argument("--image", action="append", default=[], help="Image/video path; repeat for multi-image tasks.")
    parser.add_argument("--resume-path", default="", help="Markdown resume path for resume-webpage examples.")
    parser.add_argument("--output", default="-", help="Write rendered output to this file, or '-' for stdout.")
    parser.add_argument("--format", choices=["python", "markdown"], default="python", help="Render plain code or a short validation report.")
    parser.add_argument("--validate-only", action="store_true", help="Skip rendering and print only validation notes.")
    parser.add_argument("--num-gpus", type=int, default=1)
    parser.add_argument("--hd-num", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-new-tokens", type=int, default=None)
    parser.add_argument("--max-length", type=int, default=None)
    parser.add_argument("--num-beams", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--repetition-penalty", type=float, default=None)
    parser.add_argument("--do-sample", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--use-meta", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--task-name", default="", help="Optional generated file name label for webpage tasks.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = validate(args)
    script = build_rendered_script(args)

    if args.validate_only:
        text = "\n".join(["OK" if result.ok else "FAILED", *result.messages])
    elif args.format == "markdown":
        text = render_report(args, script, result)
    else:
        text = script

    if args.output == "-":
        sys.stdout.write(text)
    else:
        Path(args.output).expanduser().write_text(text, encoding="utf-8")
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
