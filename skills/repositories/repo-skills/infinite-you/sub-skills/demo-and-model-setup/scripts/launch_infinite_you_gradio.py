#!/usr/bin/env python3
"""Launch a self-contained InfiniteYou Gradio demo from the bundled skill runtime.

This is a safe replacement entry point for the repository demo. It uses the
bundled `runtime/pipelines` implementation by default and does not import the
original source `app.py`. By default it requires local model paths; pass
--allow-downloads only when the user has approved model downloads and license
requirements.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_MODEL_DIR = "./models/InfiniteYou"
DEFAULT_BASE_MODEL_PATH = "./models/FLUX.1-dev"
REMOTE_BASE_MODEL_ID = "black-forest-labs/FLUX.1-dev"
REMOTE_INFINITE_YOU_ID = "ByteDance/InfiniteYou"
MODEL_VERSIONS = ("aes_stage2", "sim_stage1")


def skill_root() -> Path:
    return Path(__file__).resolve().parents[3]


def bundled_runtime_root() -> Path:
    return skill_root() / "runtime"


def configure_no_network_checks() -> None:
    os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
    os.environ.setdefault("ALBUMENTATIONS_DISABLE_VERSION_CHECK", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def configure_implementation_path(implementation_root: str | None = None) -> dict[str, Any]:
    runtime = bundled_runtime_root()
    report: dict[str, Any] = {
        "bundled_runtime": str(runtime),
        "implementation_root": implementation_root,
        "selected": None,
        "warnings": [],
        "errors": [],
    }
    if not (runtime / "pipelines" / "pipeline_infu_flux.py").is_file():
        report["errors"].append(f"Bundled runtime is incomplete: {runtime}")
    else:
        sys.path.insert(0, str(runtime))
        report["selected"] = str(runtime)

    if implementation_root:
        root = Path(implementation_root).expanduser().resolve()
        if not root.is_dir():
            report["errors"].append(f"--implementation-root does not exist or is not a directory: {implementation_root}")
        elif not (root / "pipelines" / "pipeline_infu_flux.py").is_file():
            report["errors"].append("--implementation-root must contain pipelines/pipeline_infu_flux.py")
        else:
            sys.path.insert(0, str(root))
            report["selected"] = str(root)
            report["warnings"].append("Using an implementation override instead of the bundled runtime.")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch or preflight a self-contained InfiniteYou Gradio demo.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--implementation-root", "--repo-root", dest="implementation_root", help="Optional override root containing pipelines/. Omit for the bundled runtime.")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, help="Local InfiniteYou model root or, with --allow-downloads, a repo id/fallback source.")
    parser.add_argument("--base-model-path", default=DEFAULT_BASE_MODEL_PATH, help="Local FLUX base model directory or, with --allow-downloads, a gated Hugging Face repo id.")
    parser.add_argument("--allow-downloads", action="store_true", help="Permit upstream model downloads/fallbacks during pipeline construction.")
    parser.add_argument("--server-name", default="localhost", help="Gradio bind host. Keep localhost unless external exposure is intended.")
    parser.add_argument("--server-port", type=int, default=None, help="Optional Gradio port.")
    parser.add_argument("--share", action="store_true", help="Enable Gradio share link. Use only with explicit approval.")
    parser.add_argument("--check-only", action="store_true", help="Validate imports, CUDA, and local model layout without launching a server.")
    parser.add_argument("--json", action="store_true", help="Emit check-only JSON.")
    return parser.parse_args()


def looks_like_local_path(value: str) -> bool:
    if value in {REMOTE_BASE_MODEL_ID, REMOTE_INFINITE_YOU_ID}:
        return False
    if value.startswith((".", "/", "~")):
        return True
    first = value.split(os.sep, 1)[0]
    return first in {"models", "model", "checkpoints", "weights", "path"}


def required_model_paths(model_dir: str) -> list[tuple[str, str]]:
    root = Path(model_dir).expanduser()
    rows: list[tuple[str, str]] = []
    for version in MODEL_VERSIONS:
        variant = root / "infu_flux_v1.0" / version
        rows.append((str(variant / "InfuseNetModel"), "dir"))
        rows.append((str(variant / "image_proj_model.bin"), "file"))
    rows.append((str(root / "supports" / "insightface"), "dir"))
    return rows


def path_ok(path: str, kind: str) -> bool:
    p = Path(path).expanduser()
    return p.is_dir() if kind == "dir" else p.is_file()


def build_check(args: argparse.Namespace) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    implementation = configure_implementation_path(args.implementation_root)
    warnings.extend(implementation["warnings"])
    errors.extend(implementation["errors"])

    imports: dict[str, Any] = {}
    for name in ["torch", "gradio", "PIL.Image", "pillow_heif", "pipelines.pipeline_infu_flux"]:
        try:
            module = __import__(name, fromlist=["*"])
            imports[name] = {"ok": True, "file": getattr(module, "__file__", None), "version": getattr(module, "__version__", None)}
        except Exception as exc:
            imports[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            errors.append(f"import failed: {name}")

    cuda: dict[str, Any] = {}
    if imports.get("torch", {}).get("ok"):
        import torch

        cuda = {
            "available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
            "torch_version": torch.__version__,
            "torch_cuda_runtime": torch.version.cuda,
        }
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            cuda["device0"] = torch.cuda.get_device_name(0)
    else:
        cuda = {"available": False}
    if not cuda.get("available"):
        errors.append("CUDA is unavailable; demo generation requires CUDA.")

    model_paths = []
    if looks_like_local_path(args.model_dir):
        for path, kind in required_model_paths(args.model_dir):
            ok = path_ok(path, kind)
            model_paths.append({"path": path, "kind": kind, "exists": ok})
            if not ok and not args.allow_downloads:
                errors.append(f"missing required model {kind}: {path}")
    elif not args.allow_downloads:
        errors.append("model-dir is not local; set a local model directory or explicitly pass --allow-downloads.")
    else:
        warnings.append("model-dir is not local; launch may rely on upstream download/fallback behavior.")

    if args.base_model_path == REMOTE_BASE_MODEL_ID:
        warnings.append("FLUX.1-dev is gated; license acceptance and Hugging Face authentication may be required.")
    elif looks_like_local_path(args.base_model_path):
        p = Path(args.base_model_path).expanduser()
        if not p.is_dir() and not args.allow_downloads:
            errors.append(f"local FLUX base model directory is missing: {args.base_model_path}")
    elif not args.allow_downloads:
        errors.append("base-model-path is not local; set a local FLUX path or explicitly pass --allow-downloads.")

    return {
        "ok": not errors,
        "implementation": implementation,
        "imports": imports,
        "cuda": cuda,
        "model_paths": model_paths,
        "warnings": warnings,
        "errors": errors,
        "server_name": args.server_name,
        "server_port": args.server_port,
    }


def emit_check(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"InfiniteYou Gradio preflight: {'OK' if report['ok'] else 'NOT OK'}")
    print(f"Implementation source: {report['implementation'].get('selected')}")
    print(f"CUDA available: {report['cuda'].get('available')}")
    if report["warnings"]:
        print("Warnings:")
        for item in report["warnings"]:
            print(f"  - {item}")
    if report["errors"]:
        print("Errors:", file=sys.stderr)
        for item in report["errors"]:
            print(f"  - {item}", file=sys.stderr)


def build_demo(args: argparse.Namespace):
    import gradio as gr
    import torch
    from pillow_heif import register_heif_opener
    from pipelines.pipeline_infu_flux import InfUFluxPipeline

    register_heif_opener()

    loaded: dict[str, Any] = {
        "model_version": None,
        "enable_realism": None,
        "enable_anti_blur": None,
        "pipeline": None,
    }

    def prepare_pipeline(model_version: str, enable_realism: bool, enable_anti_blur: bool):
        if (
            loaded["pipeline"] is not None
            and loaded["model_version"] == model_version
            and loaded["enable_realism"] == enable_realism
            and loaded["enable_anti_blur"] == enable_anti_blur
        ):
            return loaded["pipeline"]

        pipeline = loaded["pipeline"]
        if pipeline is None or loaded["model_version"] != model_version:
            del pipeline
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            model_path = str(Path(args.model_dir) / "infu_flux_v1.0" / model_version)
            pipeline = InfUFluxPipeline(
                base_model_path=args.base_model_path,
                infu_model_path=model_path,
                insightface_root_path=str(Path(args.model_dir) / "supports" / "insightface"),
                image_proj_num_tokens=8,
                infu_flux_version="v1.0",
                model_version=model_version,
            )
            loaded["pipeline"] = pipeline
            loaded["model_version"] = model_version

        try:
            pipeline.pipe.delete_adapters(["realism", "anti_blur"])
        except Exception:
            pass
        loras = []
        lora_root = Path(args.model_dir) / "supports" / "optional_loras"
        if enable_realism:
            loras.append([str(lora_root / "flux_realism_lora.safetensors"), "realism", 1.0])
        if enable_anti_blur:
            loras.append([str(lora_root / "flux_anti_blur_lora.safetensors"), "anti_blur", 1.0])
        pipeline.load_loras(loras)
        loaded["enable_realism"] = enable_realism
        loaded["enable_anti_blur"] = enable_anti_blur
        return pipeline

    def generate_image(
        input_image,
        control_image,
        prompt,
        seed,
        width,
        height,
        guidance_scale,
        num_steps,
        infusenet_conditioning_scale,
        infusenet_guidance_start,
        infusenet_guidance_end,
        enable_realism,
        enable_anti_blur,
        model_version,
    ):
        pipeline = prepare_pipeline(model_version, enable_realism, enable_anti_blur)
        if seed == 0:
            seed = torch.seed() & 0xFFFFFFFF
        try:
            image = pipeline(
                id_image=input_image,
                prompt=prompt,
                control_image=control_image,
                seed=int(seed),
                width=int(width),
                height=int(height),
                guidance_scale=float(guidance_scale),
                num_steps=int(num_steps),
                infusenet_conditioning_scale=float(infusenet_conditioning_scale),
                infusenet_guidance_start=float(infusenet_guidance_start),
                infusenet_guidance_end=float(infusenet_guidance_end),
            )
        except Exception as exc:
            raise gr.Error(str(exc))
        return gr.update(value=image, label=f"Generated Image, seed = {seed}")

    with gr.Blocks(title="InfiniteYou-FLUX") as demo:
        gr.Markdown(
            "# InfiniteYou-FLUX\n"
            "Self-contained generated-skill launcher using the bundled InfiniteYou runtime. "
            "Use only with consented identity images and license-compliant model files."
        )
        with gr.Row():
            with gr.Column(scale=3):
                with gr.Row():
                    ui_id_image = gr.Image(label="Identity Image", type="pil", height=370)
                    ui_control_image = gr.Image(label="Control Image [Optional]", type="pil", height=370)
                ui_prompt_text = gr.Textbox(label="Prompt", value="Portrait, 4K, high quality, cinematic")
                ui_model_version = gr.Dropdown(label="Model Version", choices=list(MODEL_VERSIONS), value="aes_stage2")
                ui_btn_generate = gr.Button("Generate")
                with gr.Accordion("Advanced", open=False):
                    ui_num_steps = gr.Number(label="num steps", value=30)
                    ui_seed = gr.Number(label="seed (0 for random)", value=0)
                    ui_width = gr.Number(label="width", value=864)
                    ui_height = gr.Number(label="height", value=1152)
                    ui_guidance_scale = gr.Number(label="guidance scale", value=3.5)
                    ui_infusenet_conditioning_scale = gr.Slider(0.0, 1.0, value=1.0, step=0.05, label="infusenet conditioning scale")
                    ui_infusenet_guidance_start = gr.Slider(0.0, 1.0, value=0.0, step=0.05, label="infusenet guidance start")
                    ui_infusenet_guidance_end = gr.Slider(0.0, 1.0, value=1.0, step=0.05, label="infusenet guidance end")
                with gr.Accordion("LoRAs [Optional]", open=False):
                    ui_enable_realism = gr.Checkbox(label="Enable realism LoRA", value=False)
                    ui_enable_anti_blur = gr.Checkbox(label="Enable anti-blur LoRA", value=False)
            with gr.Column(scale=2):
                image_output = gr.Image(label="Generated Image", interactive=False, height=550, format="png")
                gr.Markdown(
                    "**Tips:** `aes_stage2` is the default for alignment/aesthetics; `sim_stage1` favors identity similarity. "
                    "If VRAM is tight, use the CLI wrapper with `--cpu-offload --quantize-8bit` instead of the demo."
                )
        ui_btn_generate.click(
            generate_image,
            inputs=[
                ui_id_image,
                ui_control_image,
                ui_prompt_text,
                ui_seed,
                ui_width,
                ui_height,
                ui_guidance_scale,
                ui_num_steps,
                ui_infusenet_conditioning_scale,
                ui_infusenet_guidance_start,
                ui_infusenet_guidance_end,
                ui_enable_realism,
                ui_enable_anti_blur,
                ui_model_version,
            ],
            outputs=[image_output],
            concurrency_id="gpu",
        )
    return demo


def main() -> int:
    configure_no_network_checks()
    args = parse_args()
    check = build_check(args)
    if args.check_only:
        emit_check(check, args.json)
        return 0 if check["ok"] else 1
    if not check["ok"]:
        emit_check(check, False)
        return 1
    if args.share:
        print("Warning: --share exposes a public Gradio link. Use only with explicit approval.", file=sys.stderr)
    demo = build_demo(args)
    launch_kwargs: dict[str, Any] = {"server_name": args.server_name, "share": args.share}
    if args.server_port is not None:
        launch_kwargs["server_port"] = args.server_port
    demo.queue()
    demo.launch(**launch_kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
