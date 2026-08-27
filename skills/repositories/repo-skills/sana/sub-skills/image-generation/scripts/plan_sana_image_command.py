#!/usr/bin/env python3
"""Safe Sana image command/snippet planner.

This helper never imports Sana, starts Gradio, downloads weights, or runs image
generation. It renders command templates or Diffusers snippets plus warnings so
a future agent can review model/config/dtype choices before an expensive GPU
run.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class NativeSpec:
    config: str
    checkpoint: str
    script: str
    dtype: str
    notes: tuple[str, ...]


NATIVE_IMAGE_SPECS: dict[tuple[str, int, str], NativeSpec] = {
    ("sana", 512, "1600m"): NativeSpec(
        "configs/sana_config/512ms/Sana_1600M_img512.yaml",
        "hf://Efficient-Large-Model/Sana_1600M_512px/checkpoints/Sana_1600M_512px.pth",
        "scripts/inference.py",
        "fp16/fp32",
        ("Use 512 height/width or Sana aspect-ratio binning.",),
    ),
    ("sana", 512, "600m"): NativeSpec(
        "configs/sana_config/512ms/Sana_600M_img512.yaml",
        "hf://Efficient-Large-Model/Sana_600M_512px/checkpoints/Sana_600M_512px.pth",
        "scripts/inference.py",
        "fp16/fp32",
        ("Smallest ordinary native image model family.",),
    ),
    ("sana", 1024, "1600m"): NativeSpec(
        "configs/sana_config/1024ms/Sana_1600M_img1024.yaml",
        "hf://Efficient-Large-Model/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth",
        "scripts/inference.py",
        "bf16/fp32 or fp16 variant",
        ("Source docs also show a BF16 checkpoint label for this config family.",),
    ),
    ("sana", 1024, "600m"): NativeSpec(
        "configs/sana_config/1024ms/Sana_600M_img1024.yaml",
        "hf://Efficient-Large-Model/Sana_600M_1024px/checkpoints/Sana_600M_1024px.pth",
        "scripts/inference.py",
        "fp16/fp32",
        ("Lower VRAM than 1.6B; text rendering can be weaker.",),
    ),
    ("sana", 2048, "1600m"): NativeSpec(
        "configs/sana_config/2048ms/Sana_1600M_img2048_bf16.yaml",
        "hf://Efficient-Large-Model/Sana_1600M_2Kpx_BF16/checkpoints/Sana_1600M_2Kpx_BF16.pth",
        "scripts/inference.py",
        "bf16/fp32",
        ("2K needs substantially more VRAM than 1024px.",),
    ),
    ("sana", 4096, "1600m"): NativeSpec(
        "configs/sana_config/4096ms/Sana_1600M_img4096_bf16.yaml",
        "hf://Efficient-Large-Model/Sana_1600M_4Kpx_BF16/checkpoints/Sana_1600M_4Kpx_BF16.pth",
        "scripts/inference.py",
        "bf16/fp32",
        ("4K is high-VRAM; prefer Diffusers VAE tiling when possible.",),
    ),
    ("sana15", 1024, "1600m"): NativeSpec(
        "configs/sana1-5_config/1024ms/Sana_1600M_1024px_allqknorm_bf16_lr2e5.yaml",
        "hf://Efficient-Large-Model/SANA1.5_1.6B_1024px/checkpoints/SANA1.5_1.6B_1024px.pth",
        "scripts/inference.py",
        "bf16",
        ("Sana-1.5 all-QK-norm bf16 family.",),
    ),
    ("controlnet", 1024, "1600m"): NativeSpec(
        "configs/sana_controlnet_config/Sana_1600M_1024px_controlnet_bf16.yaml",
        "hf://Efficient-Large-Model/Sana_1600M_1024px_BF16_ControlNet_HED/checkpoints/Sana_1600M_1024px_BF16_ControlNet_HED.pth",
        "tools/controlnet/inference_controlnet.py",
        "bf16/fp32",
        ("ControlNet JSON must be a list of items with prompt and ref image/control map.",),
    ),
    ("controlnet", 1024, "600m"): NativeSpec(
        "configs/sana_controlnet_config/Sana_600M_img1024_controlnet.yaml",
        "hf://Efficient-Large-Model/Sana_600M_1024px_ControlNet_HED/checkpoints/Sana_600M_1024px_ControlNet_HED.pth",
        "tools/controlnet/inference_controlnet.py",
        "fp16/fp32",
        ("Check checkpoint availability before running this smaller ControlNet family.",),
    ),
}

SPRINT_SPECS: dict[str, NativeSpec] = {
    "1600m": NativeSpec(
        "configs/sana_sprint_config/1024ms/SanaSprint_1600M_1024px_allqknorm_bf16_scm_ladd.yaml",
        "hf://Efficient-Large-Model/Sana_Sprint_1.6B_1024px/checkpoints/Sana_Sprint_1.6B_1024px.pth",
        "scripts/inference_sana_sprint.py",
        "bf16",
        ("SCM scheduler; default native sample step count is 2.", "xformers is disabled in the Sprint native script."),
    ),
    "600m": NativeSpec(
        "configs/sana_sprint_config/1024ms/SanaSprint_600M_1024px_allqknorm_bf16_scm_ladd.yaml",
        "hf://Efficient-Large-Model/Sana_Sprint_0.6B_1024px/checkpoints/Sana_Sprint_0.6B_1024px.pth",
        "scripts/inference_sana_sprint.py",
        "bf16",
        ("SCM scheduler; lower model size than 1.6B Sprint.",),
    ),
}

# The planner focuses on the model families that have the clearest public diffusers examples.
DIFFUSERS_MODELS = {
    ("sana15", 1024, "1600m"): ("Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers", "torch.bfloat16", None),
    ("sana15", 1024, "4800m"): ("Efficient-Large-Model/SANA1.5_4.8B_1024px_diffusers", "torch.bfloat16", None),
    ("sana", 512, "1600m"): ("Efficient-Large-Model/Sana_1600M_512px_diffusers", "torch.float16", "fp16"),
    ("sana", 512, "600m"): ("Efficient-Large-Model/Sana_600M_512px_diffusers", "torch.float16", "fp16"),
    ("sana", 1024, "1600m"): ("Efficient-Large-Model/Sana_1600M_1024px_BF16_diffusers", "torch.bfloat16", "bf16"),
    ("sana", 1024, "600m"): ("Efficient-Large-Model/Sana_600M_1024px_diffusers", "torch.float16", "fp16"),
    ("sana", 2048, "1600m"): ("Efficient-Large-Model/Sana_1600M_2Kpx_BF16_diffusers", "torch.bfloat16", "bf16"),
    ("sana", 4096, "1600m"): ("Efficient-Large-Model/Sana_1600M_4Kpx_BF16_diffusers", "torch.bfloat16", "bf16"),
    ("sprint", 1024, "1600m"): ("Efficient-Large-Model/Sana_Sprint_1.6B_1024px_diffusers", "torch.bfloat16", None),
    ("sprint", 1024, "600m"): ("Efficient-Large-Model/Sana_Sprint_0.6B_1024px_diffusers", "torch.bfloat16", None),
}

GRADIO_APPS = {
    "sana": "app/app_sana.py",
    "sprint": "app/app_sana_sprint.py",
    "controlnet": "app/app_sana_controlnet_hed.py",
    "4bit": "app/app_sana_4bit.py",
    "4bit-compare": "app/app_sana_4bit_compare_bf16.py",
}


def q(value: object) -> str:
    return shlex.quote(str(value))


def add_opt(parts: list[str], name: str, value: object | None) -> None:
    if value is not None:
        parts.append(f"--{name}={q(value)}")


def render_command(parts: Iterable[str]) -> str:
    return " \\\n  ".join(parts)


def explicit_flags(argv: list[str]) -> set[str]:
    flags: set[str] = set()
    for token in argv:
        if token.startswith("--"):
            flags.add(token.split("=", 1)[0])
    return flags


def prompt_input_arg(args: argparse.Namespace) -> tuple[str, str | None]:
    if args.json_file:
        return "json_file", args.json_file
    if args.prompt_file:
        return "txt_file", args.prompt_file
    if args.prompt:
        return "txt_file", "prompts.txt"
    return "txt_file", "prompts.txt"


def prompt_file_preamble(args: argparse.Namespace) -> str:
    if args.prompt and not args.prompt_file and not args.json_file:
        return "cat > prompts.txt <<'PROMPTS'\n" + args.prompt + "\nPROMPTS\n"
    return ""


def choose_native_spec(args: argparse.Namespace) -> NativeSpec:
    if args.mode == "sprint":
        spec = SPRINT_SPECS.get(args.model_size)
        if spec is None:
            raise SystemExit(f"No Sprint spec for model size {args.model_size!r}")
        return spec
    key = (args.native_workflow, args.resolution, args.model_size)
    spec = NATIVE_IMAGE_SPECS.get(key)
    if spec is None:
        available = ", ".join(f"{k[0]}:{k[1]}:{k[2]}" for k in sorted(NATIVE_IMAGE_SPECS))
        raise SystemExit(f"No native spec for {key}. Available keys: {available}")
    return spec


def maybe_override_spec(spec: NativeSpec, args: argparse.Namespace) -> NativeSpec:
    return NativeSpec(
        config=args.config or spec.config,
        checkpoint=args.model_path or spec.checkpoint,
        script=args.script or spec.script,
        dtype=spec.dtype,
        notes=spec.notes,
    )


def common_warnings(args: argparse.Namespace, effective_pag_scale: float) -> list[str]:
    warnings = [
        "This planner is dry-run only; it does not verify CUDA, import Sana, download weights, or generate images.",
        "Real generation needs CUDA for native/Sprint/ControlNet/4-bit workflows and is strongly recommended for Diffusers.",
        "Verify Hugging Face/cache access for model, text encoder, VAE, safety checker, and optional annotator weights.",
    ]
    if args.resolution >= 2048 or (args.height and args.height >= 2048) or (args.width and args.width >= 2048):
        warnings.append("High-resolution generation can OOM; use batch size 1 and VAE tiling for 4K Diffusers.")
    if effective_pag_scale and effective_pag_scale > 1:
        warnings.append("PAG requires linear-attention Sana configs/pipelines; otherwise guidance may fall back to classifier-free.")
    return warnings


def format_plan(title: str, body: str, warnings: list[str], args: argparse.Namespace, fenced_language: str = "bash") -> str:
    out = [f"# {title}", "", f"```{fenced_language}", body.rstrip(), "```", "", "## Warnings"]
    out.extend(f"- {w}" for w in warnings)
    out.extend([
        "",
        "## After-run validation",
        "- Confirm at least one `.jpg` or `.png` was written in the planned output directory.",
        "- Open the image with PIL and check dimensions, color mode, and nonzero file size.",
        "- Record prompt, seed, model id/checkpoint, config, dtype, resolution, steps, guidance, and output path for reproducibility.",
    ])
    if args.check_files:
        out.extend(["", "## Local file checks", *local_checks(args)])
    return "\n".join(out) + "\n"


def local_checks(args: argparse.Namespace) -> list[str]:
    base = Path(args.project_dir)
    checks: list[str] = []
    for label, value in (("config", args.config), ("prompt_file", args.prompt_file), ("json_file", args.json_file)):
        if not value:
            continue
        candidate = Path(value)
        candidate = candidate if candidate.is_absolute() else base / candidate
        checks.append(f"- {label}: {'FOUND' if candidate.exists() else 'MISSING'} {value}")
    return checks or ["- No local config/prompt/json paths were supplied for checking."]


def plan_native(args: argparse.Namespace) -> str:
    spec = maybe_override_spec(choose_native_spec(args), args)
    input_name, input_value = prompt_input_arg(args)
    parts = ["python", spec.script]
    add_opt(parts, "config", spec.config)
    add_opt(parts, "model_path", spec.checkpoint)
    add_opt(parts, input_name, input_value)
    add_opt(parts, "work_dir", args.work_dir)
    add_opt(parts, "sample_nums", args.sample_nums)
    add_opt(parts, "start_index", args.start_index)
    add_opt(parts, "end_index", args.end_index)
    add_opt(parts, "bs", 1 if args.native_workflow == "controlnet" else args.batch_size)
    add_opt(parts, "cfg_scale", args.cfg_scale if "--cfg-scale" in args.explicit_flags else 4.5)
    add_opt(parts, "pag_scale", args.pag_scale if "--pag-scale" in args.explicit_flags else 1.0)
    add_opt(parts, "sampling_algo", args.sampling_algo)
    if args.step is not None:
        add_opt(parts, "step", args.step)
    if args.native_workflow == "controlnet":
        add_opt(parts, "thickness", args.thickness)
        add_opt(parts, "blend_alpha", args.blend_alpha)
    else:
        add_opt(parts, "custom_image_size", args.custom_image_size)
    add_opt(parts, "seed", args.seed if "--seed" in args.explicit_flags else 0)
    if args.tar_and_del:
        parts.append("--tar_and_del=True")

    warnings = common_warnings(args, args.pag_scale if "--pag-scale" in args.explicit_flags else 1.0)
    if args.native_workflow == "controlnet":
        warnings.extend([
            "ControlNet native script asserts batch size 1.",
            "Validate JSON with validate_controlnet_request.py before running.",
            "ref_image_path invokes HED and may need ControlNetHED.pth plus CUDA.",
        ])
    if input_value == "prompts.txt" and not args.prompt:
        warnings.append("Create prompts.txt with one prompt per line before running this command.")
    warnings.extend(spec.notes)
    return format_plan("Native Sana command", prompt_file_preamble(args) + render_command(parts), warnings, args)


def plan_sprint(args: argparse.Namespace) -> str:
    spec = maybe_override_spec(choose_native_spec(args), args)
    input_name, input_value = prompt_input_arg(args)
    parts = ["python", spec.script]
    add_opt(parts, "config", spec.config)
    add_opt(parts, "model_path", spec.checkpoint)
    add_opt(parts, input_name, input_value)
    add_opt(parts, "work_dir", args.work_dir)
    add_opt(parts, "sample_nums", args.sample_nums)
    add_opt(parts, "bs", args.batch_size)
    add_opt(parts, "cfg_scale", args.cfg_scale if "--cfg-scale" in args.explicit_flags else 1.0)
    add_opt(parts, "sampling_algo", "scm")
    add_opt(parts, "step", args.step if args.step is not None else 2)
    add_opt(parts, "max_timesteps", args.max_timesteps)
    add_opt(parts, "intermediate_timesteps", args.intermediate_timesteps)
    add_opt(parts, "seed", args.seed if "--seed" in args.explicit_flags else 0)
    warnings = common_warnings(args, 1.0) + list(spec.notes)
    if input_value == "prompts.txt" and not args.prompt:
        warnings.append("Create prompts.txt with one prompt per line before running this command.")
    return format_plan("Native SANA-Sprint command", prompt_file_preamble(args) + render_command(parts), warnings, args)


def choose_diffusers(args: argparse.Namespace) -> tuple[str, str, str | None]:
    if args.model_id:
        dtype = args.torch_dtype or (
            "torch.bfloat16"
            if args.variant == "bf16"
            else "torch.float16"
            if args.variant == "fp16"
            else "torch.bfloat16"
        )
        return args.model_id, dtype, args.variant
    family = "sprint" if args.diffusers_pipeline == "sprint" else args.model_family
    key = (family, args.resolution, args.model_size)
    model = DIFFUSERS_MODELS.get(key)
    if model is None:
        available = ", ".join(f"{k[0]}:{k[1]}:{k[2]}" for k in sorted(DIFFUSERS_MODELS))
        raise SystemExit(f"No Diffusers model for {key}. Available keys: {available}")
    return model


def plan_diffusers(args: argparse.Namespace) -> str:
    model_id, dtype, variant = choose_diffusers(args)
    prompt = args.prompt or "a cyberpunk cat with a neon sign that says Sana"
    h = args.height or args.resolution
    w = args.width or args.resolution
    steps = args.step if args.step is not None else (2 if args.diffusers_pipeline == "sprint" else 20)
    effective_pag_scale = args.pag_scale if "--pag-scale" in args.explicit_flags else (2.0 if args.diffusers_pipeline == "pag" else 1.0)
    guidance = args.cfg_scale if "--cfg-scale" in args.explicit_flags else 4.5
    warnings = common_warnings(args, effective_pag_scale)

    if args.diffusers_pipeline == "sprint":
        seed = args.seed if "--seed" in args.explicit_flags else 42
        code = f'''import torch
from diffusers import SanaSprintPipeline

pipe = SanaSprintPipeline.from_pretrained(
    {model_id!r},
    torch_dtype={dtype},
)
pipe.to("cuda:0")
image = pipe(
    prompt={prompt!r},
    num_inference_steps={int(steps)},
    generator=torch.Generator(device="cuda").manual_seed({int(seed)}),
).images[0]
image.save({args.output_file!r})'''
    elif args.quantization == "8bit":
        seed = args.seed if "--seed" in args.explicit_flags else 42
        code = f'''import torch
from diffusers import BitsAndBytesConfig as DiffusersBitsAndBytesConfig
from diffusers import SanaPipeline, SanaTransformer2DModel
from transformers import AutoModel, BitsAndBytesConfig as TransformersBitsAndBytesConfig

model_id = {model_id!r}
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
text_encoder_8bit = AutoModel.from_pretrained(
    model_id,
    subfolder="text_encoder",
    quantization_config=TransformersBitsAndBytesConfig(load_in_8bit=True),
    torch_dtype=torch.float16,
)
transformer_8bit = SanaTransformer2DModel.from_pretrained(
    model_id,
    subfolder="transformer",
    quantization_config=DiffusersBitsAndBytesConfig(load_in_8bit=True),
    torch_dtype=torch.float16,
)
pipe = SanaPipeline.from_pretrained(
    model_id,
    text_encoder=text_encoder_8bit,
    transformer=transformer_8bit,
    torch_dtype=torch.float16,
    device_map="balanced",
)
pipe.to(device)
image = pipe(
    prompt={prompt!r},
    generator=torch.Generator(device=device).manual_seed({int(seed)}),
).images[0]
image.save({args.output_file!r})'''
        warnings.append("8-bit requires compatible bitsandbytes, transformers, diffusers, CUDA, and accelerate/device_map support.")
    elif args.quantization == "4bit":
        seed = args.seed if "--seed" in args.explicit_flags else 42
        code = f'''import torch
from diffusers import SanaPipeline
from nunchaku.models.transformer_sana import NunchakuSanaTransformer2DModel

transformer = NunchakuSanaTransformer2DModel.from_pretrained("mit-han-lab/svdq-int4-sana-1600m")
pipe = SanaPipeline.from_pretrained(
    "Efficient-Large-Model/Sana_1600M_1024px_BF16_diffusers",
    transformer=transformer,
    variant="bf16",
    torch_dtype=torch.bfloat16,
).to("cuda")
pipe.text_encoder.to(torch.bfloat16)
pipe.vae.to(torch.bfloat16)
image = pipe(
    prompt={prompt!r},
    height={int(h)},
    width={int(w)},
    guidance_scale={float(guidance)},
    num_inference_steps={int(steps)},
    generator=torch.Generator(device="cuda").manual_seed({int(seed)}),
).images[0]
image.save({args.output_file!r})'''
        warnings.append("4-bit requires the Nunchaku/SVDQuant engine and CUDA; it is not a generic Diffusers load_in_4bit flag.")
    else:
        pipeline = "SanaPAGPipeline" if args.diffusers_pipeline == "pag" or effective_pag_scale > 1 else "SanaPipeline"
        seed = args.seed if "--seed" in args.explicit_flags else 42
        variant_line = f"    variant={variant!r},\n" if variant else ""
        pag_init = ',\n    pag_applied_layers="transformer_blocks.8"' if pipeline == "SanaPAGPipeline" else ""
        pag_arg = f",\n    pag_scale={effective_pag_scale}" if pipeline == "SanaPAGPipeline" else ""
        tiling = ""
        if args.vae_tiling or int(h) >= 4096 or int(w) >= 4096:
            tiling = '''
if getattr(pipe.transformer.config, "sample_size", None) == 128:
    pipe.vae.enable_tiling(
        tile_sample_min_height=1024,
        tile_sample_min_width=1024,
        tile_sample_stride_height=896,
        tile_sample_stride_width=896,
    )
'''
            warnings.append("VAE tiling is included because 4K/high-resolution decode can OOM.")
        code = f'''import torch
from diffusers import {pipeline}

pipe = {pipeline}.from_pretrained(
    {model_id!r},
{variant_line}    torch_dtype={dtype}{pag_init},
)
pipe.to("cuda")
pipe.vae.to(torch.bfloat16)
pipe.text_encoder.to(torch.bfloat16)
{tiling}
image = pipe(
    prompt={prompt!r},
    height={int(h)},
    width={int(w)},
    guidance_scale={float(guidance)},
    num_inference_steps={int(steps)},
    generator=torch.Generator(device="cuda").manual_seed({int(seed)}){pag_arg},
).images[0]
image.save({args.output_file!r})'''
    return format_plan("Diffusers Python snippet", code, warnings, args, fenced_language="python")


def plan_gradio(args: argparse.Namespace) -> str:
    app = GRADIO_APPS[args.app]
    parts = [f"DEMO_PORT={q(args.port)}", "python", app]
    if args.app in {"sana", "sprint", "controlnet"}:
        if args.config:
            add_opt(parts, "config", args.config)
        elif args.app == "sana":
            add_opt(parts, "config", "configs/sana_config/1024ms/Sana_1600M_img1024.yaml")
        elif args.app == "sprint":
            add_opt(parts, "config", SPRINT_SPECS[args.model_size].config)
        else:
            add_opt(parts, "config", NATIVE_IMAGE_SPECS[("controlnet", 1024, args.model_size)].config)
        if args.model_path:
            add_opt(parts, "model_path", args.model_path)
        elif args.app == "sprint":
            add_opt(parts, "model_path", SPRINT_SPECS[args.model_size].checkpoint)
        elif args.app == "controlnet":
            add_opt(parts, "model_path", NATIVE_IMAGE_SPECS[("controlnet", 1024, args.model_size)].checkpoint)
        else:
            add_opt(parts, "model_path", "hf://Efficient-Large-Model/Sana_1600M_1024px_BF16/checkpoints/Sana_1600M_1024px_BF16.pth")
        add_opt(parts, "image_size", args.resolution)
    if args.share:
        parts.append("--share")
    warnings = common_warnings(args, args.pag_scale if args.app == "sana" and args.pag_scale > 1 else 1.0) + [
        "Gradio apps load models and optional safety checker at startup.",
        "DEMO_PORT controls server_port; --share requests a public Gradio tunnel.",
        "Omit --share when network policy forbids public tunnels.",
    ]
    if args.app.startswith("4bit"):
        warnings.append("4-bit apps require CUDA and Nunchaku/SVDQuant dependencies before startup.")
    return format_plan("Gradio launch command", render_command(parts), warnings, args)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--mode", choices=["native", "sprint", "diffusers", "gradio"], required=True)
    parser.add_argument("--native-workflow", choices=["sana", "sana15", "controlnet"], default="sana")
    parser.add_argument("--diffusers-pipeline", choices=["sana", "pag", "sprint"], default="sana")
    parser.add_argument("--model-family", choices=["sana", "sana15"], default="sana")
    parser.add_argument("--model-size", choices=["600m", "1600m", "4800m"], default="1600m")
    parser.add_argument("--resolution", type=int, choices=[512, 1024, 2048, 4096], default=1024)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--config", default=None, help="Override native config path in the rendered command.")
    parser.add_argument("--model-path", default=None, help="Override native checkpoint/model_path in the rendered command.")
    parser.add_argument("--model-id", default=None, help="Override Diffusers model id in the rendered snippet.")
    parser.add_argument("--variant", choices=["fp16", "bf16"], default=None)
    parser.add_argument("--torch-dtype", choices=["torch.float16", "torch.bfloat16", "torch.float32"], default=None)
    parser.add_argument("--script", default=None, help="Override native script path in the rendered command.")
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--json-file", default=None)
    parser.add_argument("--work-dir", default="output/sana-plan")
    parser.add_argument("--output-file", default="sana.png")
    parser.add_argument("--sample-nums", type=int, default=1)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int, default=30000)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--cfg-scale", type=float, default=4.5)
    parser.add_argument("--pag-scale", type=float, default=1.0)
    parser.add_argument("--sampling-algo", choices=["flow_dpm-solver", "flow_euler", "dpm-solver", "sa-solver"], default="flow_dpm-solver")
    parser.add_argument("--step", type=int, default=None)
    parser.add_argument("--max-timesteps", type=float, default=1.57080)
    parser.add_argument("--intermediate-timesteps", type=float, default=1.3)
    parser.add_argument("--custom-image-size", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tar-and-del", action="store_true")
    parser.add_argument("--quantization", choices=["none", "8bit", "4bit"], default="none")
    parser.add_argument("--vae-tiling", action="store_true")
    parser.add_argument("--thickness", type=int, default=2)
    parser.add_argument("--blend-alpha", type=float, default=0.0)
    parser.add_argument("--app", choices=sorted(GRADIO_APPS), default="sana")
    parser.add_argument("--port", type=int, default=15432)
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--check-files", action="store_true", help="Check supplied local config/prompt/json paths relative to --project-dir.")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--json-summary", action="store_true", help="Emit a small JSON summary of selected mode and key inputs before the plan.")
    args = parser.parse_args(argv)
    if args.mode == "sprint":
        args.native_workflow = "sana"
    if args.mode == "native" and args.native_workflow == "controlnet" and not args.json_file:
        parser.error("--native-workflow controlnet requires --json-file")
    if args.quantization != "none" and args.mode != "diffusers":
        parser.error("--quantization is only supported with --mode diffusers")
    if args.diffusers_pipeline == "sprint" and args.mode == "diffusers":
        args.resolution = 1024
    if args.model_size == "4800m" and not (args.mode == "diffusers" and args.model_family == "sana15"):
        parser.error("--model-size 4800m is only mapped for --mode diffusers --model-family sana15")
    return args


def main(argv: list[str] | None = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else argv
    args = parse_args(raw_argv)
    args.explicit_flags = explicit_flags(raw_argv)
    if args.mode == "native":
        plan = plan_native(args)
    elif args.mode == "sprint":
        plan = plan_sprint(args)
    elif args.mode == "diffusers":
        plan = plan_diffusers(args)
    else:
        plan = plan_gradio(args)
    if args.json_summary:
        print(json.dumps({
            "mode": args.mode,
            "native_workflow": args.native_workflow,
            "diffusers_pipeline": args.diffusers_pipeline,
            "resolution": args.resolution,
            "model_size": args.model_size,
            "dry_run_only": True,
        }, indent=2))
    print(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
