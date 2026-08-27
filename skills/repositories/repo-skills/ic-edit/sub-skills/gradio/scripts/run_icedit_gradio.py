#!/usr/bin/env python3
"""Bundled Gradio launcher for the ICEdit normal and MoE demo paths."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import gradio as gr
import numpy as np
import torch
from PIL import Image

try:
    import spaces
except Exception:  # pragma: no cover - local fallback for non-Spaces use
    class _SpacesFallback:
        @staticmethod
        def GPU(fn):
            return fn

    spaces = _SpacesFallback()

MAX_SEED = np.iinfo(np.int32).max
MAX_IMAGE_SIZE = 1024
DEFAULT_FLUX_PATH = "black-forest-labs/flux.1-fill-dev"
DEFAULT_LORA_PATHS = {
    "normal": "RiverZ/normal-lora",
    "moe": "sanaka87/ICEdit-MoE-LoRA",
}
EXAMPLE_PRESETS = [
    ("girl.png", "Make her hair dark green and her clothes checked.", 304897401),
    ("boy.png", "Change the sunglasses to a Christmas hat.", 748891420),
    ("kaori.jpg", "Make it a sketch.", 484817364),
]

HELPER_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_EXAMPLES_DIR = HELPER_ROOT / "references" / "examples"
BUNDLED_CONFIG_PATH = Path(__file__).resolve().with_name("config.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the ICEdit Gradio demo for the normal or MoE path."
    )
    parser.add_argument(
        "--mode",
        choices=("normal", "moe"),
        default="normal",
        help="Select the normal Gradio path or the MoE variant.",
    )
    parser.add_argument(
        "--server-name",
        "--server_name",
        default="127.0.0.1",
        help="Host interface for Gradio.",
    )
    parser.add_argument("--port", type=int, default=7860, help="Port for the Gradio app.")
    parser.add_argument("--share", action="store_true", help="Create a public Gradio share link.")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open the browser after launch.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved launch plan and exit before loading the model.",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="ICEdit checkout root used to locate the vendored icedit/ package in MoE mode.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="gradio_results",
        help="Directory where edited images are saved.",
    )
    parser.add_argument(
        "--flux-path",
        type=str,
        default=None,
        help="Flux base model repo id or local path.",
    )
    parser.add_argument(
        "--lora-path",
        type=str,
        default=None,
        help="ICEdit LoRA repo id or local path.",
    )
    parser.add_argument(
        "--transformer",
        type=str,
        default=None,
        help="Optional GGUF transformer file for FluxTransformer2DModel.",
    )
    parser.add_argument(
        "--text-encoder-2",
        "--text_encoder_2",
        dest="text_encoder_2",
        type=str,
        default=None,
        help="Optional GGUF text-encoder file for T5EncoderModel.",
    )
    parser.add_argument(
        "--enable-model-cpu-offload",
        action="store_true",
        help="Enable CPU offload for lower-VRAM launches.",
    )
    return parser.parse_args()


def apply_mode_defaults(args: argparse.Namespace) -> None:
    if args.flux_path is None:
        args.flux_path = DEFAULT_FLUX_PATH
    if args.lora_path is None:
        args.lora_path = DEFAULT_LORA_PATHS[args.mode]


def discover_repo_root(explicit: str | None) -> Path:
    if explicit:
        repo_root = Path(explicit).expanduser().resolve()
        if not repo_root.is_dir():
            raise FileNotFoundError(f"ICEdit repo root not found: {repo_root}")
        vendored = repo_root / "icedit"
        if not vendored.is_dir():
            raise FileNotFoundError(
                f"MoE mode requires the repo-local icedit/ package under: {vendored}"
            )
        return repo_root

    search_starts = [Path.cwd().resolve(), Path(__file__).resolve()]
    for start in search_starts:
        for candidate in (start, *start.parents):
            if (
                (candidate / "README.md").is_file()
                and (candidate / "assets").is_dir()
                and (candidate / "icedit").is_dir()
            ):
                return candidate

    raise FileNotFoundError(
        "Could not auto-detect the ICEdit checkout for MoE mode; pass --repo-root /path/to/ICEdit."
    )


def validate_optional_file(path_value: str | None, label: str) -> None:
    if not path_value:
        return
    path = Path(path_value).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")


def maybe_print_dry_run(args: argparse.Namespace, repo_root: Path | None) -> None:
    print("ICEdit Gradio dry run")
    print(f"  mode: {args.mode}")
    if repo_root is not None:
        print(f"  repo_root: {repo_root}")
        print(f"  vendored_icedit: {repo_root / 'icedit'}")
    print(f"  server_name: {args.server_name}")
    print(f"  port: {args.port}")
    print(f"  share: {args.share}")
    print(f"  open_browser: {not args.no_browser}")
    print(f"  output_dir: {Path(args.output_dir).expanduser()}")
    print(f"  flux_path: {args.flux_path}")
    print(f"  lora_path: {args.lora_path}")
    print(f"  transformer: {args.transformer or '<normal pretrained transformer>'}")
    print(f"  text_encoder_2: {args.text_encoder_2 or '<normal pretrained text encoder>'}")
    print(f"  cpu_offload: {args.enable_model_cpu_offload}")
    print("  presets: girl.png, boy.png, kaori.jpg")


def load_runtime_modules(mode: str, repo_root: Path | None):
    if mode == "moe":
        if repo_root is None:
            raise ValueError("MoE mode requires an ICEdit repo root.")
        vendored = repo_root / "icedit"
        if not vendored.is_dir():
            raise FileNotFoundError(f"MoE mode requires the repo-local icedit/ package under: {vendored}")
        vendored_str = str(vendored)
        if vendored_str not in sys.path:
            sys.path.insert(0, vendored_str)

    from diffusers import FluxFillPipeline, FluxTransformer2DModel, GGUFQuantizationConfig
    from transformers import T5EncoderModel

    return FluxFillPipeline, FluxTransformer2DModel, GGUFQuantizationConfig, T5EncoderModel


def load_example_rows() -> list[list[object]]:
    rows: list[list[object]] = []
    for filename, prompt, seed in EXAMPLE_PRESETS:
        image_path = BUNDLED_EXAMPLES_DIR / filename
        if not image_path.is_file():
            raise FileNotFoundError(f"Bundled preset image missing: {image_path}")
        rows.append([str(image_path), prompt, seed])
    return rows


def build_pipeline(args: argparse.Namespace, runtime_modules):
    FluxFillPipeline, FluxTransformer2DModel, GGUFQuantizationConfig, T5EncoderModel = runtime_modules

    if not BUNDLED_CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Bundled GGUF config missing: {BUNDLED_CONFIG_PATH}")

    if args.transformer:
        transformer_path = Path(args.transformer).expanduser()
        if not transformer_path.exists():
            raise FileNotFoundError(f"Transformer file not found: {transformer_path}")
        transformer = FluxTransformer2DModel.from_single_file(
            str(transformer_path),
            config=str(BUNDLED_CONFIG_PATH),
            quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
            torch_dtype=torch.bfloat16,
        )
    else:
        transformer = FluxTransformer2DModel.from_pretrained(
            args.flux_path,
            subfolder="transformer",
            torch_dtype=torch.bfloat16,
        )

    if args.text_encoder_2:
        text_encoder_2_path = Path(args.text_encoder_2).expanduser()
        if not text_encoder_2_path.exists():
            raise FileNotFoundError(f"Text-encoder GGUF file not found: {text_encoder_2_path}")
        text_encoder_2 = T5EncoderModel.from_pretrained(
            args.flux_path,
            subfolder="text_encoder_2",
            gguf_file=str(text_encoder_2_path),
            torch_dtype=torch.bfloat16,
        )
    else:
        text_encoder_2 = T5EncoderModel.from_pretrained(
            args.flux_path,
            subfolder="text_encoder_2",
            torch_dtype=torch.bfloat16,
        )

    pipe = FluxFillPipeline.from_pretrained(
        args.flux_path,
        transformer=transformer,
        text_encoder_2=text_encoder_2,
        torch_dtype=torch.bfloat16,
    )
    pipe.load_lora_weights(args.lora_path, adapter_name="icedit")
    pipe.set_adapters("icedit", 1.0)

    if args.enable_model_cpu_offload:
        pipe.enable_model_cpu_offload()
    else:
        pipe = pipe.to("cuda")

    return pipe


def build_demo(pipe, args: argparse.Namespace):
    current_lora_scale = 1.0
    example_rows = load_example_rows()

    def save_result(image: Image.Image) -> Path:
        output_dir = Path(args.output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        index = sum(1 for _ in output_dir.glob("result_*.png"))
        output_path = output_dir / f"result_{index}.png"
        image.save(output_path)
        return output_path

    @spaces.GPU
    def infer(
        edit_image,
        prompt,
        seed=666,
        randomize_seed=False,
        width=1024,
        height=1024,
        guidance_scale=50,
        num_inference_steps=28,
        lora_scale=1.0,
        progress=gr.Progress(track_tqdm=True),
    ):
        nonlocal current_lora_scale

        if lora_scale != current_lora_scale:
            print(
                f"[INFO] LoRA scale changed from {current_lora_scale} to {lora_scale}, reloading adapter"
            )
            pipe.set_adapters("icedit", lora_scale)
            current_lora_scale = lora_scale

        image = edit_image
        if image.size[0] != 512:
            print("[WARNING] The demo expects width 512; resizing input to width 512.")
            new_width = 512
            scale = new_width / image.size[0]
            new_height = int(image.size[1] * scale)
            new_height = (new_height // 8) * 8
            image = image.resize((new_width, new_height))
            print(f"[WARNING] Resized the image to {new_width} x {new_height}")

        image = image.convert("RGB")
        width, height = image.size
        image = image.resize((512, int(512 * height / width)))
        combined_image = Image.new("RGB", (width * 2, height))
        combined_image.paste(image, (0, 0))
        mask_array = np.zeros((height, width * 2), dtype=np.uint8)
        mask_array[:, width:] = 255
        mask = Image.fromarray(mask_array)
        instruction = (
            "A diptych with two side-by-side images of the same scene. On the right, "
            f"the scene is exactly the same as on the left but {prompt}"
        )

        if randomize_seed:
            seed = random.randint(0, MAX_SEED)

        output_image = pipe(
            prompt=instruction,
            image=combined_image,
            mask_image=mask,
            height=height,
            width=width * 2,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=torch.Generator().manual_seed(seed),
        ).images[0]

        w, h = output_image.size
        output_image = output_image.crop((w // 2, 0, w, h))
        save_result(output_image)
        return output_image, seed

    css = """
    #col-container {
        margin: 0 auto;
        max-width: 1000px;
    }
    """

    with gr.Blocks(css=css) as demo:
        with gr.Column(elem_id="col-container"):
            gr.Markdown(
                """# IC-Edit
A browser-based demo for the ICEdit image-editing workflow.

- Upload an image or pick a bundled preset.
- Enter the edit instruction only; the helper injects the diptych prompt internally.
- Adjust LoRA scale, seed, guidance scale, and sampling steps from the UI.
"""
            )
            with gr.Row():
                with gr.Column():
                    edit_image = gr.Image(
                        label="Upload image for editing",
                        type="pil",
                        sources=["upload", "webcam"],
                        image_mode="RGB",
                        height=600,
                    )
                    prompt = gr.Text(
                        label="Prompt",
                        show_label=False,
                        max_lines=1,
                        placeholder="Enter your prompt",
                        container=False,
                    )
                    run_button = gr.Button("Run")

                result = gr.Image(label="Result", show_label=False)

            with gr.Accordion("Advanced Settings", open=True):
                seed = gr.Slider(
                    label="Seed",
                    minimum=0,
                    maximum=MAX_SEED,
                    step=1,
                    value=0,
                )
                randomize_seed = gr.Checkbox(label="Randomize seed", value=True)

                with gr.Row():
                    width = gr.Slider(
                        label="Width",
                        minimum=512,
                        maximum=MAX_IMAGE_SIZE,
                        step=32,
                        value=1024,
                        visible=False,
                    )
                    height = gr.Slider(
                        label="Height",
                        minimum=512,
                        maximum=MAX_IMAGE_SIZE,
                        step=32,
                        value=1024,
                        visible=False,
                    )

                with gr.Row():
                    guidance_scale = gr.Slider(
                        label="Guidance Scale",
                        minimum=1,
                        maximum=100,
                        step=0.5,
                        value=50,
                    )
                    num_inference_steps = gr.Slider(
                        label="Number of inference steps",
                        minimum=1,
                        maximum=50,
                        step=1,
                        value=28,
                    )

                lora_scale = gr.Slider(
                    label="LoRA Scale",
                    minimum=0,
                    maximum=1.0,
                    step=0.01,
                    value=1.0,
                )

            def process_example(edit_image, prompt, seed):
                result, seed_out = infer(
                    edit_image,
                    prompt,
                    seed,
                    False,
                    1024,
                    1024,
                    50,
                    28,
                    1.0,
                )
                return result, seed_out

            gr.Examples(
                examples=example_rows,
                inputs=[edit_image, prompt, seed],
                outputs=[result, seed],
                fn=process_example,
                cache_examples=False,
            )

        gr.on(
            triggers=[run_button.click, prompt.submit],
            fn=infer,
            inputs=[
                edit_image,
                prompt,
                seed,
                randomize_seed,
                width,
                height,
                guidance_scale,
                num_inference_steps,
                lora_scale,
            ],
            outputs=[result, seed],
        )

    return demo


def main() -> int:
    args = parse_args()
    apply_mode_defaults(args)

    repo_root = None
    if args.mode == "moe":
        repo_root = discover_repo_root(args.repo_root)

    validate_optional_file(args.transformer, "Transformer GGUF file")
    validate_optional_file(args.text_encoder_2, "Text-encoder GGUF file")

    if args.dry_run:
        maybe_print_dry_run(args, repo_root)
        return 0

    runtime_modules = load_runtime_modules(args.mode, repo_root)
    pipe = build_pipeline(args, runtime_modules)
    demo = build_demo(pipe, args)
    demo.launch(
        server_name=args.server_name,
        server_port=args.port,
        share=args.share,
        inbrowser=not args.no_browser,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
