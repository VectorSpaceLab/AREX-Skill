#!/usr/bin/env python3
"""Build safe sd-scripts training command templates without executing them."""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable


FAMILY_SCRIPTS = {
    "sd1": "train_network.py",
    "sd2": "train_network.py",
    "sdxl": "sdxl_train_network.py",
    "sd3": "sd3_train_network.py",
    "flux": "flux_train_network.py",
    "chroma": "flux_train_network.py",
    "lumina": "lumina_train_network.py",
    "hunyuan-image": "hunyuan_image_train_network.py",
    "anima": "anima_train_network.py",
}

NETWORK_MODULES = {
    "lora": "networks.lora",
    "flux-lora": "networks.lora_flux",
    "loha": "networks.loha",
    "lokr": "networks.lokr",
}


def add_flag(command: list[str], flag: str, value: str | int | float | None = None) -> None:
    command.append(flag)
    if value is not None:
        command.append(str(value))


def add_if(command: list[str], flag: str, value: str | None) -> None:
    if value:
        add_flag(command, flag, value)


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def build_command(args: argparse.Namespace) -> list[str]:
    family = args.family
    kind = args.kind

    if kind == "dreambooth":
        script = "train_db.py"
    elif kind == "fine-tune":
        script = "fine_tune.py"
    elif kind == "textual-inversion":
        script = "train_textual_inversion.py"
    elif kind == "leco":
        script = "sdxl_train_leco.py" if family == "sdxl" else "train_leco.py"
    elif kind == "lllite":
        script = "sdxl_train_control_net_lllite.py"
        if family != "sdxl":
            raise SystemExit("ControlNet-LLLite training is SDXL-only in sd-scripts templates.")
    else:
        script = FAMILY_SCRIPTS[family]

    command = ["accelerate", "launch", "--num_cpu_threads_per_process", str(args.num_cpu_threads_per_process), script]

    add_if(command, "--pretrained_model_name_or_path", args.pretrained_model)

    if kind in {"lora", "loha", "lokr"}:
        network_key = args.network_module or ("flux-lora" if family in {"flux", "chroma"} else kind)
        add_flag(command, "--network_module", NETWORK_MODULES[network_key])
        add_flag(command, "--network_dim", args.network_dim)
        add_flag(command, "--network_alpha", args.network_alpha)
    elif kind == "lllite":
        add_flag(command, "--network_dim", args.network_dim)
        add_flag(command, "--cond_emb_dim", args.cond_emb_dim)

    add_if(command, "--dataset_config", args.dataset_config)
    add_if(command, "--train_data_dir", args.train_data_dir)
    add_if(command, "--reg_data_dir", args.reg_data_dir)
    add_if(command, "--prompts_file", args.prompts_file)

    if kind == "textual-inversion":
        add_if(command, "--token_string", args.token_string)
        add_if(command, "--init_word", args.init_word)
        add_flag(command, "--num_vectors_per_token", args.num_vectors_per_token)

    add_if(command, "--clip_l", args.clip_l)
    add_if(command, "--clip_g", args.clip_g)
    add_if(command, "--t5xxl", args.t5xxl)
    add_if(command, "--vae", args.vae)
    add_if(command, "--ae", args.ae)
    add_if(command, "--gemma2", args.gemma2)

    if family == "sd2" and args.sd2_v_parameterization:
        add_flag(command, "--v2")
        add_flag(command, "--v_parameterization")

    if family == "chroma":
        add_flag(command, "--model_type", "chroma")
        add_flag(command, "--guidance_scale", "0.0")
        add_flag(command, "--apply_t5_attn_mask")
        if not args.timestep_sampling:
            args.timestep_sampling = "sigmoid"
    elif family == "flux":
        add_flag(command, "--guidance_scale", args.guidance_scale or "1.0")
        if not args.timestep_sampling:
            args.timestep_sampling = "flux_shift"

    if family in {"flux", "chroma"} and not args.model_prediction_type:
        args.model_prediction_type = "raw"

    add_if(command, "--timestep_sampling", args.timestep_sampling)
    add_if(command, "--model_prediction_type", args.model_prediction_type)
    add_if(command, "--t5xxl_max_token_length", args.t5xxl_max_token_length)

    add_if(command, "--output_dir", args.output_dir)
    add_if(command, "--output_name", args.output_name)
    add_flag(command, "--save_model_as", args.save_model_as)

    if args.max_train_epochs is not None:
        add_flag(command, "--max_train_epochs", args.max_train_epochs)
    if args.max_train_steps is not None:
        add_flag(command, "--max_train_steps", args.max_train_steps)
    if args.save_every_n_epochs is not None:
        add_flag(command, "--save_every_n_epochs", args.save_every_n_epochs)

    add_flag(command, "--learning_rate", args.learning_rate)
    add_flag(command, "--optimizer_type", args.optimizer_type)
    add_flag(command, "--mixed_precision", args.mixed_precision)

    if args.cache_latents and not args.train_inpainting:
        add_flag(command, "--cache_latents")
    if args.cache_latents_to_disk and not args.train_inpainting:
        add_flag(command, "--cache_latents_to_disk")
    if args.cache_text_encoder_outputs:
        add_flag(command, "--cache_text_encoder_outputs")
    if args.cache_text_encoder_outputs_to_disk:
        add_flag(command, "--cache_text_encoder_outputs_to_disk")
    if args.gradient_checkpointing:
        add_flag(command, "--gradient_checkpointing")
    if args.xformers:
        add_flag(command, "--xformers")
    if args.sdpa:
        add_flag(command, "--sdpa")
    if args.fp8_base and family not in {"hunyuan-image", "anima"}:
        add_flag(command, "--fp8_base")
    if args.fp8_scaled and family == "hunyuan-image":
        add_flag(command, "--fp8_scaled")
    if args.blocks_to_swap is not None:
        add_flag(command, "--blocks_to_swap", args.blocks_to_swap)
    if args.train_inpainting:
        add_flag(command, "--train_inpainting")
    if args.compile and family == "anima":
        add_flag(command, "--compile")

    if args.validation_split is not None:
        add_flag(command, "--validation_split", args.validation_split)
    if args.validate_every_n_steps is not None:
        add_flag(command, "--validate_every_n_steps", args.validate_every_n_steps)
    if args.validate_every_n_epochs is not None:
        add_flag(command, "--validate_every_n_epochs", args.validate_every_n_epochs)
    if args.max_validation_steps is not None:
        add_flag(command, "--max_validation_steps", args.max_validation_steps)
    if args.validation_seed is not None:
        add_flag(command, "--validation_seed", args.validation_seed)

    add_if(command, "--sample_prompts", args.sample_prompts)
    if args.sample_every_n_epochs is not None:
        add_flag(command, "--sample_every_n_epochs", args.sample_every_n_epochs)

    for item in args.network_args:
        add_flag(command, "--network_args", item)

    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", required=True, choices=sorted(FAMILY_SCRIPTS))
    parser.add_argument(
        "--kind",
        default="lora",
        choices=["lora", "loha", "lokr", "dreambooth", "fine-tune", "textual-inversion", "leco", "lllite"],
    )
    parser.add_argument("--pretrained_model")
    parser.add_argument("--dataset_config")
    parser.add_argument("--train_data_dir")
    parser.add_argument("--reg_data_dir")
    parser.add_argument("--prompts_file")
    parser.add_argument("--output_dir", default="output")
    parser.add_argument("--output_name", default="training_run")
    parser.add_argument("--save_model_as", default="safetensors")
    parser.add_argument("--network_module", choices=sorted(NETWORK_MODULES))
    parser.add_argument("--network_dim", default=32, type=int)
    parser.add_argument("--network_alpha", default=16, type=float)
    parser.add_argument("--network_args", nargs="*", default=[])
    parser.add_argument("--cond_emb_dim", default=32, type=int)
    parser.add_argument("--clip_l")
    parser.add_argument("--clip_g")
    parser.add_argument("--t5xxl")
    parser.add_argument("--vae")
    parser.add_argument("--ae")
    parser.add_argument("--gemma2")
    parser.add_argument("--token_string")
    parser.add_argument("--init_word")
    parser.add_argument("--num_vectors_per_token", default=4, type=int)
    parser.add_argument("--learning_rate", default="1e-4")
    parser.add_argument("--optimizer_type", default="AdamW8bit")
    parser.add_argument("--mixed_precision", default="bf16", choices=["no", "fp16", "bf16"])
    parser.add_argument("--max_train_epochs", type=int, default=10)
    parser.add_argument("--max_train_steps", type=int)
    parser.add_argument("--save_every_n_epochs", type=int, default=1)
    parser.add_argument("--num_cpu_threads_per_process", type=int, default=1)
    parser.add_argument("--cache_latents", action="store_true")
    parser.add_argument("--cache_latents_to_disk", action="store_true")
    parser.add_argument("--cache_text_encoder_outputs", action="store_true")
    parser.add_argument("--cache_text_encoder_outputs_to_disk", action="store_true")
    parser.add_argument("--gradient_checkpointing", action="store_true", default=True)
    parser.add_argument("--no_gradient_checkpointing", action="store_false", dest="gradient_checkpointing")
    parser.add_argument("--xformers", action="store_true")
    parser.add_argument("--sdpa", action="store_true")
    parser.add_argument("--fp8_base", action="store_true")
    parser.add_argument("--fp8_scaled", action="store_true")
    parser.add_argument("--blocks_to_swap", type=int)
    parser.add_argument("--sd2_v_parameterization", action="store_true")
    parser.add_argument("--guidance_scale")
    parser.add_argument("--timestep_sampling")
    parser.add_argument("--model_prediction_type")
    parser.add_argument("--t5xxl_max_token_length")
    parser.add_argument("--train_inpainting", action="store_true")
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--validation_split", type=float)
    parser.add_argument("--validate_every_n_steps", type=int)
    parser.add_argument("--validate_every_n_epochs", type=int)
    parser.add_argument("--max_validation_steps", type=int)
    parser.add_argument("--validation_seed", type=int)
    parser.add_argument("--sample_prompts")
    parser.add_argument("--sample_every_n_epochs", type=int)
    parser.add_argument("--format", choices=["single-line", "multiline"], default="multiline")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.train_inpainting and (args.cache_latents or args.cache_latents_to_disk):
        print("# Note: --train_inpainting is incompatible with latent caching; latent cache flags were omitted.")
    if args.family == "chroma" and args.clip_l:
        print("# Note: Chroma does not use CLIP-L; --clip_l was ignored by this template.")
        args.clip_l = None
    if args.family == "anima" and (args.fp8_base or args.fp8_scaled):
        print("# Note: Anima fp8 flags are unsupported; fp8 flags were omitted.")
    command = build_command(args)
    if args.format == "single-line":
        print(quote_command(command))
    else:
        lines = [shlex.quote(command[0])]
        lines[0] += " \\\n"
        for index, part in enumerate(command[1:], start=1):
            suffix = " \\\n" if index < len(command) - 1 else ""
            lines.append(f"  {shlex.quote(part)}{suffix}")
        print("".join(lines))


if __name__ == "__main__":
    main()
