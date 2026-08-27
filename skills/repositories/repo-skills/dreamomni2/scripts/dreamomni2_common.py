"""Shared DreamOmni2 helpers for bundled skill scripts.

These utilities intentionally stay small and dependency-light so the inference
and web-demo wrappers can share the same image resizing and prompt formatting
logic without depending on the source checkout layout.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence
import os
import sys

from PIL import Image


def _add_repo_root_to_path() -> Path | None:
    """Find a DreamOmni2 checkout without hardcoding the creation path."""

    candidates: list[Path] = []
    env_root = os.environ.get("DREAMOMNI2_REPO_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser().resolve())
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "dreamomni2" / "pipeline_dreamomni2.py").exists():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return candidate
    return None


REPO_ROOT = _add_repo_root_to_path()

PREFERRED_KONTEXT_RESOLUTIONS = [
    (672, 1568),
    (688, 1504),
    (720, 1456),
    (752, 1392),
    (800, 1328),
    (832, 1248),
    (880, 1184),
    (944, 1104),
    (1024, 1024),
    (1104, 944),
    (1184, 880),
    (1248, 832),
    (1328, 800),
    (1392, 752),
    (1456, 720),
    (1504, 688),
    (1568, 672),
]


def _closest_resolution(width: int, height: int) -> tuple[int, int]:
    ratio = width / height
    return min(
        PREFERRED_KONTEXT_RESOLUTIONS,
        key=lambda candidate: abs((candidate[0] / candidate[1]) - ratio),
    )


def resizeinput(img: Image.Image) -> Image.Image:
    """Resize an image to the nearest DreamOmni2/Kontext aspect bucket."""

    multiple_of = 16
    target_width, target_height = _closest_resolution(img.width, img.height)
    target_width = target_width // multiple_of * multiple_of
    target_height = target_height // multiple_of * multiple_of
    return img.resize((target_width, target_height), Image.LANCZOS)


def load_and_resize_images(image_paths: Sequence[str]) -> list[Image.Image]:
    """Load local or remote image paths with the diffusers image loader.

    The wrappers use this helper for both inference and Gradio demo uploads.
    """

    from diffusers.utils import load_image

    resized: list[Image.Image] = []
    for path in image_paths:
        resized.append(resizeinput(load_image(path)))
    return resized


def extract_vlm_text(text: str) -> str:
    """Return the raw prompt text from the VLM response.

    The source scripts trim a fenced block by character offsets. This helper
    keeps the same intent but also handles one-line and multi-line fenced text
    more defensively.
    """

    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        body = stripped[3:-3].strip()
        if body.startswith("\n"):
            body = body[1:]
        return body.strip()
    return stripped


def build_vlm_messages(image_paths: Sequence[str], instruction: str, prefix: str) -> list[dict[str, object]]:
    """Construct the Qwen2.5-VL chat message payload used by DreamOmni2."""

    content: list[dict[str, object]] = []
    for path in image_paths:
        content.append({"type": "image", "image": path})
    content.append({"type": "text", "text": f"{instruction}{prefix}"})
    return [{"role": "user", "content": content}]


def ensure_two_images(image_paths: Sequence[str]) -> None:
    """Validate the two-image workflows used by DreamOmni2."""

    if len(image_paths) != 2:
        raise ValueError(
            f"DreamOmni2 expects exactly two images for these workflows, got {len(image_paths)}"
        )


DEFAULT_BASE_MODEL = "black-forest-labs/FLUX.1-Kontext-dev"
DEFAULT_GUIDANCE_SCALE = 3.5
DEFAULT_INFERENCE_STEPS = 30
DEFAULT_MAX_NEW_TOKENS = 4096


def load_vlm_stack(vlm_path: str):
    """Load the Qwen2.5-VL stack used to produce the DreamOmni2 prompt."""

    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    vlm_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        vlm_path,
        torch_dtype="bfloat16",
        device_map="cuda",
    )
    processor = AutoProcessor.from_pretrained(vlm_path)
    return vlm_model, processor


def load_dreamomni2_pipeline(base_model_path: str, adapter_path: str, adapter_name: str):
    """Load the FLUX.1-Kontext pipeline and the requested DreamOmni2 LoRA."""

    import torch
    from dreamomni2.pipeline_dreamomni2 import DreamOmni2Pipeline

    pipe = DreamOmni2Pipeline.from_pretrained(base_model_path, torch_dtype=torch.bfloat16)
    pipe.to("cuda")
    pipe.load_lora_weights(adapter_path, adapter_name=adapter_name)
    pipe.set_adapters([adapter_name], adapter_weights=[1])
    return pipe


def infer_vlm_prompt(vlm_model, processor, image_paths: Sequence[str], instruction: str, prefix: str, device: str = "cuda") -> str:
    """Run the VLM prompt stage shared by the editing and generation flows."""

    messages = build_vlm_messages(image_paths, instruction, prefix)
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    images = load_and_resize_images(image_paths)
    inputs = processor(text=[text], images=images, videos=None, padding=True, return_tensors="pt")
    inputs = inputs.to(device)
    generated_ids = vlm_model.generate(**inputs, do_sample=False, max_new_tokens=DEFAULT_MAX_NEW_TOKENS)
    generated_ids_trimmed = [out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    return extract_vlm_text(output_text[0])


def run_dreamomni2_workflow(
    *,
    mode: str,
    image_paths: Sequence[str],
    instruction: str,
    output_path: str | Path,
    vlm_path: str,
    adapter_path: str,
    base_model_path: str = DEFAULT_BASE_MODEL,
    height: int | None = None,
    width: int | None = None,
) -> Path:
    """Run the editing or generation workflow and save the result to disk."""

    import torch

    ensure_two_images(image_paths)
    if mode not in {"edit", "generate"}:
        raise ValueError(f"mode must be 'edit' or 'generate', got {mode!r}")

    adapter_name = "edit" if mode == "edit" else "generation"
    prompt_prefix = " It is editing task." if mode == "edit" else " It is generation task."
    pipe = load_dreamomni2_pipeline(base_model_path, adapter_path, adapter_name)
    vlm_model, processor = load_vlm_stack(vlm_path)
    prompt = infer_vlm_prompt(vlm_model, processor, image_paths, instruction, prompt_prefix)
    source_imgs = load_and_resize_images(image_paths)

    image_height = height if height is not None else source_imgs[0].height
    image_width = width if width is not None else source_imgs[0].width
    result = pipe(
        images=source_imgs,
        height=image_height,
        width=image_width,
        prompt=prompt,
        num_inference_steps=DEFAULT_INFERENCE_STEPS,
        guidance_scale=DEFAULT_GUIDANCE_SCALE,
    ).images[0]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)
    return output_path
