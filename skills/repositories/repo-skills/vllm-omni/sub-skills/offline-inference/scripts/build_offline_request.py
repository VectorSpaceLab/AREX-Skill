#!/usr/bin/env python3
"""Generate safe vLLM-Omni offline inference starter snippets.

This helper intentionally uses only the Python standard library. It validates
basic request-shape arguments and prints a runnable snippet; it does not import
vllm_omni, download weights, contact a server, or instantiate a model.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from typing import Any


TASKS = ("text-to-image", "image-to-image", "qwen3-omni-chat", "tts")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def py_literal(value: Any) -> str:
    return repr(value)


def maybe_param_lines(args: argparse.Namespace, *, include_frames: bool = False) -> str:
    lines: list[str] = []
    if args.height is not None:
        lines.append(f"        height={args.height},")
    if args.width is not None:
        lines.append(f"        width={args.width},")
    if include_frames:
        lines.append("        # Add num_frames=... here for video-capable models.")
    if args.num_inference_steps is not None:
        lines.append(f"        num_inference_steps={args.num_inference_steps},")
    if args.seed is not None:
        lines.append(f"        seed={args.seed},")
    if not lines:
        lines.append("        # No request-level diffusion overrides: use model/deploy defaults.")
    return "\n".join(lines)


def common_image_helpers() -> str:
    return r'''

def _mm_to_dict(mm):
    if mm is None:
        return {}
    if hasattr(mm, "to_dict") and callable(mm.to_dict):
        return mm.to_dict()
    return dict(mm) if hasattr(mm, "items") else {}


def _tensor_to_pil_images(tensor):
    """Best-effort conversion for image tensors shaped CHW/HWC/BCHW."""
    import torch
    from PIL import Image

    image = tensor.detach().to("cpu", dtype=torch.float32)
    if image.ndim == 4:
        out = []
        for single in image:
            out.extend(_tensor_to_pil_images(single))
        return out
    if image.ndim != 3:
        return []
    if image.shape[0] in (1, 3, 4):
        image = image.permute(1, 2, 0)
    if image.min().item() < 0:
        image = image / 2 + 0.5
    image = image.clamp(0, 1).mul(255).to(torch.uint8).contiguous().numpy()
    return [Image.fromarray(image)]


def _coerce_images(payload):
    from PIL import Image
    import torch

    if payload is None:
        return []
    if isinstance(payload, Image.Image):
        return [payload]
    if isinstance(payload, torch.Tensor):
        return _tensor_to_pil_images(payload)
    if isinstance(payload, (list, tuple)):
        images = []
        for item in payload:
            images.extend(_coerce_images(item))
        return images
    return []


def collect_images(outputs):
    images = []
    for output in outputs:
        images.extend(_coerce_images(getattr(output, "images", None)))
        if images:
            continue
        mm = _mm_to_dict(getattr(output, "multimodal_output", None))
        for key in ("image", "images", "model_outputs"):
            if key in mm:
                images.extend(_coerce_images(mm[key]))
                break
    return images
'''.strip()


def snippet_text_to_image(args: argparse.Namespace) -> str:
    output_file = args.output_file or "output.png"
    return textwrap.dedent(
        f'''
        # Generated vLLM-Omni offline text-to-image scaffold.
        # Running this file will load the model; this generator did not.
        import os

        from vllm_omni.entrypoints.omni import Omni
        from vllm_omni.inputs.data import OmniDiffusionSamplingParams

        {textwrap.indent(common_image_helpers(), "        ").lstrip()}

        model = {py_literal(args.model)}
        output_file = {py_literal(output_file)}
        prompt = {{"prompt": {py_literal(args.prompt)}, "modalities": ["image"]}}
        sampling_params = OmniDiffusionSamplingParams(
        {maybe_param_lines(args)}
        )

        omni = Omni(model=model)
        try:
            outputs = omni.generate(prompt, sampling_params, use_tqdm=False)
            images = collect_images(outputs)
            if not images:
                raise RuntimeError("No image output found. Check prompt modalities and model support.")
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            images[0].save(output_file)
            print(f"saved {{output_file}}")
        finally:
            omni.close()
        '''
    ).strip() + "\n"


def snippet_image_to_image(args: argparse.Namespace) -> str:
    output_file = args.output_file or "edited.png"
    return textwrap.dedent(
        f'''
        # Generated vLLM-Omni offline image-to-image/edit scaffold.
        # Edit input_image_path before running. Running this file will load the model.
        import os
        from PIL import Image

        from vllm_omni.entrypoints.omni import Omni
        from vllm_omni.inputs.data import OmniDiffusionSamplingParams

        {textwrap.indent(common_image_helpers(), "        ").lstrip()}

        model = {py_literal(args.model)}
        input_image_path = "input.png"  # TODO: replace with your local image path.
        output_file = {py_literal(output_file)}

        input_image = Image.open(input_image_path).convert("RGB")
        prompt = {{
            "prompt": {py_literal(args.prompt)},
            "modalities": ["image"],
            "multi_modal_data": {{"image": input_image}},
            # "negative_prompt": "blurry",  # Optional when the model supports it.
        }}
        sampling_params = OmniDiffusionSamplingParams(
        {maybe_param_lines(args)}
        )

        omni = Omni(model=model)
        try:
            outputs = omni.generate(prompt, sampling_params, use_tqdm=False)
            images = collect_images(outputs)
            if not images:
                raise RuntimeError("No edited image output found. Check input media and model support.")
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            images[0].save(output_file)
            print(f"saved {{output_file}}")
        finally:
            omni.close()
        '''
    ).strip() + "\n"


def snippet_qwen3_omni_chat(args: argparse.Namespace) -> str:
    output_file = args.output_file or "response.txt"
    seed_line = f"            seed={args.seed}," if args.seed is not None else "            # seed=42,"
    return textwrap.dedent(
        f'''
        # Generated vLLM-Omni Qwen3-Omni-style offline chat scaffold.
        # Running this file will load the model; add local media payloads only if needed.
        import os

        from vllm import SamplingParams
        from vllm_omni.entrypoints.omni import Omni

        model = {py_literal(args.model)}
        output_file = {py_literal(output_file)}
        user_question = {py_literal(args.prompt)}
        system = (
            "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, "
            "capable of perceiving auditory and visual inputs, as well as generating text and speech."
        )
        chat_prompt = (
            f"<|im_start|>system\\n{{system}}<|im_end|>\\n"
            "<|im_start|>user\\n"
            f"{{user_question}}<|im_end|>\\n"
            "<|im_start|>assistant\\n"
        )
        prompt = {{
            "prompt": chat_prompt,
            "modalities": ["text"],
            # To add an image: include <|vision_start|><|image_pad|><|vision_end|> in chat_prompt
            # and set "multi_modal_data": {{"image": PIL.Image.open("image.png").convert("RGB")}}.
            # To add audio: include <|audio_start|><|audio_pad|><|audio_end|> and provide (np_array, sr).
        }}
        sampling_params = SamplingParams(
            temperature=0.9,
            top_p=0.9,
            top_k=-1,
            max_tokens=512,
{seed_line}
        )

        omni = Omni(model=model, output_modalities=["text"])
        try:
            outputs = omni.generate(prompt, [sampling_params], use_tqdm=False)
            text_parts = []
            for output in outputs:
                if getattr(output, "outputs", None):
                    text = getattr(output.outputs[0], "text", None)
                    if text:
                        text_parts.append(text)
            text = "".join(text_parts).strip()
            if not text:
                raise RuntimeError("No text output found. Check output_modalities and model support.")
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text + "\\n")
            print(text)
        finally:
            omni.close()
        '''
    ).strip() + "\n"


def snippet_tts(args: argparse.Namespace) -> str:
    output_file = args.output_file or "speech.wav"
    return textwrap.dedent(
        f'''
        # Generated vLLM-Omni offline TTS scaffold.
        # The placeholder prompt_token_ids length is model-specific; adjust it if the model validates length.
        import os

        import soundfile as sf
        import torch

        from vllm_omni.entrypoints.omni import Omni

        model = {py_literal(args.model)}
        output_file = {py_literal(output_file)}
        prompt = {{
            "prompt_token_ids": [0] * 2048,
            "additional_information": {{
                "task_type": ["CustomVoice"],
                "text": [{py_literal(args.prompt)}],
                "language": ["English"],
                "speaker": ["Ryan"],
                "instruct": ["Speak clearly."],
                "max_new_tokens": [2048],
            }},
        }}

        def mm_to_dict(mm):
            if mm is None:
                return {{}}
            if hasattr(mm, "to_dict") and callable(mm.to_dict):
                return mm.to_dict()
            return dict(mm) if hasattr(mm, "items") else {{}}

        def save_wav(mm, path):
            audio = mm.get("audio")
            if audio is None:
                raise RuntimeError("No audio payload found in multimodal output.")
            sr_raw = None
            for key in ("sr", "sample_rate", "audio_sample_rate"):
                if key in mm and mm[key] is not None:
                    sr_raw = mm[key]
                    break
            if sr_raw is None:
                sr_raw = 24000
            if isinstance(sr_raw, list) and sr_raw:
                sr_raw = sr_raw[-1]
            sr = sr_raw.item() if hasattr(sr_raw, "item") else int(sr_raw)
            if isinstance(audio, list):
                audio = torch.cat(audio, dim=-1)
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            sf.write(path, audio.float().detach().cpu().numpy().flatten(), samplerate=sr, format="WAV")

        omni = Omni(model=model, output_modalities=["audio"])
        try:
            for output in omni.generate([prompt], use_tqdm=False):
                mm = None
                if getattr(output, "outputs", None):
                    mm = getattr(output.outputs[0], "multimodal_output", None)
                if not mm:
                    mm = getattr(output, "multimodal_output", None)
                save_wav(mm_to_dict(mm), output_file)
                print(f"saved {{output_file}}")
        finally:
            omni.close()
        '''
    ).strip() + "\n"


def build_snippet(args: argparse.Namespace) -> str:
    if args.task == "text-to-image":
        return snippet_text_to_image(args)
    if args.task == "image-to-image":
        return snippet_image_to_image(args)
    if args.task == "qwen3-omni-chat":
        return snippet_qwen3_omni_chat(args)
    if args.task == "tts":
        return snippet_tts(args)
    raise AssertionError(args.task)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a self-contained vLLM-Omni offline inference Python snippet. "
            "This generator itself performs no network calls, imports no vllm_omni modules, "
            "and loads no models."
        )
    )
    parser.add_argument("--task", choices=TASKS, required=True, help="Snippet type to generate.")
    parser.add_argument("--model", required=True, help="Model id or local model path to place in the snippet.")
    parser.add_argument("--prompt", required=True, help="Text prompt or text to synthesize.")
    parser.add_argument("--height", type=positive_int, default=None, help="Optional output height for diffusion snippets.")
    parser.add_argument("--width", type=positive_int, default=None, help="Optional output width for diffusion snippets.")
    parser.add_argument(
        "--num-inference-steps",
        type=positive_int,
        default=None,
        help="Optional denoising step count for diffusion snippets.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional seed to place in the snippet.")
    parser.add_argument(
        "--output-file",
        default=None,
        help="Output file path used by the generated snippet, not by this generator.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    # Ensure arguments are JSON-serializable/basic strings for clear generated code.
    json.dumps({"task": args.task, "model": args.model, "prompt": args.prompt, "output_file": args.output_file})
    sys.stdout.write(build_snippet(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
