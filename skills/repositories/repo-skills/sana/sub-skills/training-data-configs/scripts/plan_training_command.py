#!/usr/bin/env python3
"""Safe Sana training command planner.

Prints command templates and warnings only. It does not launch training, import
CUDA libraries, load checkpoints, or download Hugging Face assets.
"""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path

DEFAULTS = {
    "image": "configs/sana_config/512ms/Sana_600M_img512.yaml",
    "image-fsdp": "configs/sana1-5_config/1024ms/Sana_1600M_1024px_AdamW_fsdp.yaml",
    "sprint": "configs/sana_sprint_config/1024ms/SanaSprint_1600M_1024px_allqknorm_bf16_scm_ladd.yaml",
    "video": "configs/sana_video_config/Sana_2000M_480px_AdamW_fsdp.yaml",
    "video-720p": "configs/sana_video_config/Sana_2000M_720px_ltx2vae_AdamW_fsdp.yaml",
    "wm-bidirectional": "configs/sana_wm/stage1/sana_wm_stage1_sekai_bidirectional_cp2_fsdp2.yaml",
    "wm-chunk": "configs/sana_wm/stage1/sana_wm_stage1_sekai_chunk_causal_cp2_fsdp2.yaml",
    "wm-ode": "configs/sana_wm/distill/ode_t43.yaml",
    "wm-self-forcing-t43": "configs/sana_wm/distill/self_forcing_t43.yaml",
    "wm-self-forcing-t121": "configs/sana_wm/distill/self_forcing_t121.yaml",
    "streaming-bidir": "configs/sana_streaming/train/sana_streaming_bidirectional_2b_720p.yaml",
    "streaming-long-441": "configs/sana_streaming/train/sana_streaming_long_441_2b_720p.yaml",
    "streaming-long-969": "configs/sana_streaming/train/sana_streaming_long_969_2b_720p.yaml",
    "longsana-self-forcing": "configs/sana_video_config/longsana/480ms/self_forcing.yaml",
    "longsana-long": "configs/sana_video_config/longsana/480ms/longsana.yaml",
    "longsana-ode": "configs/sana_video_config/longsana/480ms/ode.yaml",
}


def q(value: str) -> str:
    return shlex.quote(str(value))


def compact(parts: list[str]) -> list[str]:
    return [part for part in parts if str(part).strip()]


def line_join(parts: list[str]) -> str:
    parts = compact(parts)
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return " \\\n  ".join(parts)


def print_block(title: str, command: str) -> None:
    print(f"\n## {title}\n")
    print("```bash")
    print(command)
    print("```")


def warn(messages: list[str], message: str) -> None:
    messages.append(message)


def data_override(args: argparse.Namespace, dict_mode: bool = False) -> str:
    if not args.data_dir:
        return ""
    if dict_mode:
        payload = json.dumps({args.dataset_name: args.data_dir})
        return f"--data.data_dir={q(payload)}"
    return f"--data.data_dir={q('[' + args.data_dir + ']')}"


def image_command(args: argparse.Namespace, warnings: list[str]) -> str:
    fsdp = args.family == "image-fsdp" or args.fsdp
    config = args.config or (DEFAULTS["image-fsdp"] if fsdp else DEFAULTS["image"])
    parts = ["bash", "train_scripts/train.sh", q(config), f"--np={args.gpus}"]
    if args.data_dir:
        parts.append(data_override(args))
    parts.append(f"--data.type={args.data_type}")
    if args.data_type == "SanaImgDataset":
        parts.extend(["--model.multi_scale=false", "--data.load_vae_feat=false"])
    else:
        parts.append("--model.multi_scale=true")
        if args.load_vae_feat:
            parts.append("--data.load_vae_feat=true")
        else:
            warn(warnings, "SanaWebDatasetMS without --data.load_vae_feat may encode VAE online and use more VRAM.")
    if fsdp:
        parts.append("--train.use_fsdp=true")
    if args.load_from:
        parts.append(f"--model.load_from={q(args.load_from)}")
    parts.extend([
        f"--work_dir={q(args.work_dir)}",
        f"--train.train_batch_size={args.batch_size}",
        f"--train.num_workers={args.num_workers}",
    ])
    warn(warnings, "train_scripts/train.sh injects --resume_from=latest, --report_to=tensorboard, and --debug=true; use a fresh work_dir for clean starts.")
    return line_join(parts)


def sprint_command(args: argparse.Namespace, warnings: list[str]) -> str:
    config = args.config or DEFAULTS["sprint"]
    parts = ["bash", "train_scripts/train_scm_ladd.sh", q(config), f"--np={args.gpus}"]
    if args.data_dir:
        parts.append(data_override(args))
    parts.extend([
        "--data.type=SanaWebDatasetMS",
        "--model.multi_scale=true",
        "--data.load_vae_feat=true" if args.load_vae_feat else "--data.load_vae_feat=false",
        f"--work_dir={q(args.work_dir)}",
        f"--train.train_batch_size={args.batch_size}",
        f"--train.num_workers={args.num_workers}",
    ])
    warn(warnings, "Sprint sCM/LADD is normally planned with SanaWebDatasetMS and precomputed VAE features.")
    warn(warnings, "train_scm_ladd.sh injects --resume_from=latest, --report_to=tensorboard, and --debug=true.")
    return line_join(parts)


def video_command(args: argparse.Namespace, warnings: list[str]) -> str:
    config = args.config or (DEFAULTS["video-720p"] if args.family == "video-720p" or args.resolution == "720p" else DEFAULTS["video"])
    parts = ["bash", "train_video_scripts/train_video_ivjoint.sh", q(config), f"--np={args.gpus}"]
    if args.data_dir:
        parts.append(data_override(args, dict_mode=True))
    parts.extend([
        f"--work_dir={q(args.work_dir)}",
        f"--train.train_batch_size={args.batch_size}",
        f"--train.num_workers={args.num_workers}",
    ])
    if args.no_joint_image:
        parts.append("--train.joint_training_interval=0")
    if args.visualize:
        parts.append("--train.visualize=true")
    else:
        parts.append("--train.visualize=false")
    warn(warnings, "Video data_dir is dict-valued; a copied YAML is safer than shell dict overrides for production.")
    warn(warnings, "train_video_ivjoint.sh exports DISABLE_XFORMERS=1 and DEBUG_MODE=1 and injects --resume_from=latest.")
    if "720" in config:
        warn(warnings, "720p LTX2 VAE recipes require 128-channel latents and dimensions divisible by 32.")
    return line_join(parts)


def lora_command(args: argparse.Namespace, warnings: list[str]) -> str:
    model = args.model_name or "Efficient-Large-Model/Sana_1600M_1024px_BF16_diffusers"
    instance = args.data_dir or "data/dreambooth/my_subject"
    parts = [
        f"export MODEL_NAME={q(model)}",
        f"export INSTANCE_DIR={q(instance)}",
        f"export OUTPUT_DIR={q(args.output_dir or args.work_dir)}",
        "",
        line_join([
            "accelerate", "launch", f"--num_processes", str(args.gpus), "--main_process_port", str(args.master_port),
            "train_scripts/train_dreambooth_lora_sana.py",
            "--pretrained_model_name_or_path=\"$MODEL_NAME\"",
            "--instance_data_dir=\"$INSTANCE_DIR\"",
            "--output_dir=\"$OUTPUT_DIR\"",
            "--mixed_precision=bf16",
            f"--instance_prompt={q(args.instance_prompt)}",
            f"--resolution={args.image_size}",
            f"--train_batch_size={args.batch_size}",
            f"--gradient_accumulation_steps={args.grad_accum}",
            "--use_8bit_adam" if args.use_8bit_adam else "",
            f"--learning_rate={args.learning_rate}",
            f"--report_to={args.report_to}",
            "--lr_scheduler=constant",
            "--lr_warmup_steps=0",
            f"--max_train_steps={args.max_steps}",
            f"--validation_prompt={q(args.validation_prompt)}" if args.validation_prompt else "",
            f"--validation_epochs={args.validation_epochs}" if args.validation_prompt else "",
            f"--seed={args.seed}",
            "--cache_latents" if args.cache_latents else "",
            "--offload" if args.offload else "",
            f"--lora_layers={q(args.lora_layers)}" if args.lora_layers else "",
            "--push_to_hub" if args.push_to_hub else "",
        ])
    ]
    warn(warnings, "Run accelerate config first. PEFT >= 0.14.0 is required.")
    if args.report_to == "wandb":
        warn(warnings, "wandb logging requires wandb login or WANDB_MODE=offline.")
    if args.push_to_hub:
        warn(warnings, "Verify subject-image rights before pushing LoRA adapters to the Hub.")
    return "\n".join(p for p in parts if p is not None)


def longsana_command(args: argparse.Namespace, warnings: list[str]) -> str:
    key = {
        "longsana-ode": "longsana-ode",
        "longsana": "longsana-self-forcing",
        "longsana-self-forcing": "longsana-self-forcing",
        "longsana-long": "longsana-long",
    }.get(args.family, "longsana-self-forcing")
    config = args.config or DEFAULTS[key]
    parts = ["torchrun", f"--nproc_per_node={args.gpus}"]
    if args.nnodes > 1:
        parts.extend([f"--nnodes={args.nnodes}", f"--rdzv_id={q(args.rdzv_id)}", "--rdzv_backend=c10d", f"--rdzv_endpoint={q(args.rdzv_endpoint)}"])
    else:
        parts.append(f"--master_port={args.master_port}")
    parts.extend([
        "train_video_scripts/train_longsana.py",
        "--config_path", q(config),
        "--logdir", q(args.work_dir),
        "--max_iters", str(args.max_iters),
    ])
    if args.disable_wandb:
        parts.append("--disable-wandb")
    if args.no_auto_resume:
        parts.append("--no-auto-resume")
    warn(warnings, "LongSANA ODE/self-forcing/long stages depend on stage-specific data and checkpoint chaining configured in YAML.")
    return line_join(parts)


def wm_stage1_command(args: argparse.Namespace, warnings: list[str]) -> str:
    config = args.config or DEFAULTS["wm-chunk" if args.wm_variant == "chunk" else "wm-bidirectional"]
    parts = [
        "torchrun",
        f"--nproc_per_node={args.gpus}",
        f"--master_port={args.master_port}",
        "train_video_scripts/train_sana_wm_stage1.py",
        "--config_path", q(config),
    ]
    warn(warnings, "SANA-WM Stage-1 public data is about 235 GB and non-commercial research use only.")
    warn(warnings, "Set data.hf_dataset_local_dir/data.data_dir/data.vae_cache_dir in a copied YAML for custom or shared storage.")
    warn(warnings, "CP/FSDP2 recipes require GPU count compatible with train.cp_size.")
    return line_join(parts)


def wm_distill_command(args: argparse.Namespace, warnings: list[str]) -> str:
    key = {"wm-ode": "wm-ode", "wm-self-forcing-t43": "wm-self-forcing-t43", "wm-self-forcing-t121": "wm-self-forcing-t121"}.get(args.family, "wm-ode")
    config = args.config or DEFAULTS[key]
    parts = [
        "torchrun",
        f"--nproc_per_node={args.gpus}",
        f"--master_port={args.master_port}",
        "train_video_scripts/train_longsana.py",
        "--config_path", q(config),
        "--disable-wandb" if args.disable_wandb else "",
        "--max_iters", str(args.max_iters),
    ]
    warn(warnings, "WM distillation stages are chained; copy YAML and set data_path/model_path/checkpoints before launch.")
    warn(warnings, "Self-forcing WM configs use CP4/DP2 on the public 8-GPU recipe.")
    return line_join([p for p in parts if p])


def streaming_command(args: argparse.Namespace, warnings: list[str]) -> str:
    if args.streaming_stage == "bidirectional" or args.family == "streaming-bidir":
        config = args.config or DEFAULTS["streaming-bidir"]
        parts = [
            "torchrun",
            f"--nproc_per_node={args.gpus}",
            f"--master_port={args.master_port}",
            "train_video_scripts/train_video_ivjoint_chunk.py",
            f"--config_path={q(config)}",
        ]
        warn(warnings, "Bidirectional Streaming V2V expects manifest.jsonl plus source/target zipped pairs.")
        return line_join(parts)
    key = "streaming-long-969" if args.streaming_stage == "long-969" or args.family == "streaming-long-969" else "streaming-long-441"
    config = args.config or DEFAULTS[key]
    parts = [
        "DISABLE_XFORMERS=1",
        "torchrun",
        f"--nproc_per_node={args.gpus}",
        f"--master_port={args.master_port}",
        "train_video_scripts/train_longsana.py",
        "--config_path", q(config),
        "--logdir", q(args.work_dir),
        "--disable-wandb" if args.disable_wandb else "",
        "--max_iters", str(args.max_iters),
    ]
    warn(warnings, "Long V2V requires local SANA-Streaming and bidirectional checkpoints before training.")
    if key == "streaming-long-969":
        warn(warnings, "The 969-stage config expects the 441-stage checkpoint unless edited.")
    return line_join([p for p in parts if p])


def sol_rl_command(args: argparse.Namespace, warnings: list[str]) -> str:
    config_spec = args.config_spec or "configs/sol_rl/sana.py:sana_diffusionnft_pickscore"
    launcher = args.launcher or "train_scripts/sol_rl/run_sana_single_node_8gpu.sh"
    env = [
        f"WANDB_MODE={q(args.wandb_mode)}",
        f"NPROC_PER_NODE={args.gpus}",
        f"CUDA_VISIBLE_DEVICES={q(args.cuda_visible_devices)}" if args.cuda_visible_devices else "",
        f"CONFIG_SPEC={q(config_spec)}",
    ]
    if "run_sana" in launcher:
        env.append("DISABLE_XFORMERS=1")
    overrides = [
        f"--config.logdir={q(args.logdir)}" if args.logdir else "",
        f"--config.run_name={q(args.run_name)}" if args.run_name else "",
        f"--config.save_dir={q(args.work_dir)}",
        f"--config.resume_from={q(args.work_dir)}",
    ]
    if args.debug:
        overrides.extend([
            "--config.num_epochs=1",
            "--config.debug=True",
            "--config.resume=False",
            "--config.rollout_sample_num_steps=2",
            "--config.sample.num_image_per_prompt=2",
            "--config.sample.best_of_n=2",
            "--config.sample.full_rollout_num=2",
            "--config.sample.rollout_batch_size=2",
            "--config.sample.per_prompt_iter_num=1",
            "--config.sample.per_gpu_to_process_prompts=1",
            "--config.sample.per_gpu_total_samples_to_train=2",
            "--config.sample.test_batch_size=1",
            "--config.train.batch_size=1",
            "--config.train.gradient_accumulation_steps=1",
            "--config.train.n_batch_per_epoch=1",
            "--config.train.num_inner_epochs=1",
            "--config.enable_debug_image_save=False",
        ])
    command = line_join([p for p in env if p] + ["bash", launcher] + [p for p in overrides if p])
    warn(warnings, "Sol-RL rewards may download models; HPSv2 requires manual reward_ckpts files.")
    config_name = config_spec.split(":")[-1]
    if any(name in config_name for name in ["naive_quant", "sol_rl"]):
        warn(warnings, "This Sol-RL family uses NVFP4/Transformer Engine requirements.")
    return command


def cosmos_rl_command(args: argparse.Namespace, warnings: list[str]) -> str:
    config = args.config or "./configs/sana/sana-image-sft-lora.toml"
    dataset_tool = args.cosmos_tool or "cosmos_rl.tools.dataset.diffusers_dataset"
    command = line_join(["cosmos-rl", "--config", q(config), q(dataset_tool)])
    warn(warnings, "Cosmos-RL is an external integration; verify the Cosmos-RL install and config tree separately.")
    warn(warnings, "RL modes require async reward service variables such as REMOTE_REWARD_TOKEN and reward URLs.")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", required=True, choices=[
        "image", "image-fsdp", "sprint", "lora", "video", "video-720p", "longsana", "longsana-ode", "longsana-self-forcing", "longsana-long",
        "wm-stage1", "wm-ode", "wm-self-forcing-t43", "wm-self-forcing-t121", "streaming-v2v", "streaming-bidir", "streaming-long-441", "streaming-long-969", "sol-rl", "cosmos-rl"
    ])
    parser.add_argument("--config", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--data-type", default="SanaImgDataset", choices=["SanaImgDataset", "SanaWebDatasetMS"])
    parser.add_argument("--dataset-name", default="default")
    parser.add_argument("--work-dir", default="output/sana_planned_run")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--gpus", type=int, default=1)
    parser.add_argument("--nnodes", type=int, default=1)
    parser.add_argument("--master-port", type=int, default=29500)
    parser.add_argument("--rdzv-id", default="sana_train")
    parser.add_argument("--rdzv-endpoint", default="$MASTER_ADDR")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--max-iters", type=int, default=10)
    parser.add_argument("--load-from", default=None)
    parser.add_argument("--load-vae-feat", action="store_true")
    parser.add_argument("--fsdp", action="store_true")
    parser.add_argument("--resolution", default="480p", choices=["480p", "720p"])
    parser.add_argument("--no-joint-image", action="store_true")
    parser.add_argument("--visualize", action="store_true")
    parser.add_argument("--disable-wandb", action="store_true", default=True)
    parser.add_argument("--enable-wandb", dest="disable_wandb", action="store_false")
    parser.add_argument("--no-auto-resume", action="store_true")
    parser.add_argument("--wm-variant", default="chunk", choices=["bidirectional", "chunk"])
    parser.add_argument("--streaming-stage", default="bidirectional", choices=["bidirectional", "long-441", "long-969"])
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--instance-prompt", default="a photo of sks subject")
    parser.add_argument("--validation-prompt", default="A photo of sks subject in a cinematic scene")
    parser.add_argument("--validation-epochs", type=int, default=25)
    parser.add_argument("--image-size", type=int, default=1024)
    parser.add_argument("--learning-rate", default="1e-4")
    parser.add_argument("--report-to", default="wandb", choices=["wandb", "tensorboard", "none", "comet_ml", "all"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--use-8bit-adam", action="store_true", default=True)
    parser.add_argument("--cache-latents", action="store_true")
    parser.add_argument("--offload", action="store_true")
    parser.add_argument("--lora-layers", default=None)
    parser.add_argument("--push-to-hub", action="store_true")
    parser.add_argument("--config-spec", default=None)
    parser.add_argument("--launcher", default=None)
    parser.add_argument("--wandb-mode", default="offline")
    parser.add_argument("--cuda-visible-devices", default=None)
    parser.add_argument("--logdir", default="output/sol_rl_logs")
    parser.add_argument("--run-name", default="")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--cosmos-tool", default=None)
    args = parser.parse_args()

    warnings: list[str] = []
    family = args.family
    if family in {"image", "image-fsdp"}:
        command = image_command(args, warnings)
    elif family == "sprint":
        command = sprint_command(args, warnings)
    elif family == "lora":
        command = lora_command(args, warnings)
    elif family in {"video", "video-720p"}:
        command = video_command(args, warnings)
    elif family.startswith("longsana"):
        command = longsana_command(args, warnings)
    elif family == "wm-stage1":
        command = wm_stage1_command(args, warnings)
    elif family in {"wm-ode", "wm-self-forcing-t43", "wm-self-forcing-t121"}:
        command = wm_distill_command(args, warnings)
    elif family in {"streaming-v2v", "streaming-bidir", "streaming-long-441", "streaming-long-969"}:
        if family == "streaming-bidir":
            args.streaming_stage = "bidirectional"
        elif family == "streaming-long-441":
            args.streaming_stage = "long-441"
        elif family == "streaming-long-969":
            args.streaming_stage = "long-969"
        command = streaming_command(args, warnings)
    elif family == "sol-rl":
        command = sol_rl_command(args, warnings)
    elif family == "cosmos-rl":
        command = cosmos_rl_command(args, warnings)
    else:
        raise AssertionError(f"Unhandled family {family}")

    print("# Sana training command plan")
    print(f"Family: {family}")
    print(f"This script only prints commands and warnings; it does not execute training.\n")
    print_block("Planned command", command)

    if args.data_dir:
        print("\n## Suggested safe data validation\n")
        mode = {
            "image": "image-pair" if args.data_type == "SanaImgDataset" else "wids",
            "image-fsdp": "wids",
            "sprint": "wids",
            "lora": "lora",
            "video": "sana-zip-video",
            "video-720p": "sana-zip-video",
            "streaming-v2v": "streaming-v2v",
            "streaming-bidir": "streaming-v2v",
        }.get(family, "auto")
        validation = line_join([
            "python", "skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py",
            "--path", q(args.data_dir), "--mode", mode,
        ])
        print("```bash")
        print(validation)
        print("```")

    if warnings:
        print("\n## Warnings and follow-up checks\n")
        for item in warnings:
            print(f"- {item}")
    print("\n## Not verified by this planner\n")
    print("- CUDA availability, checkpoint compatibility, Hugging Face access, VAE/text encoder loading, distributed process groups, reward services, training convergence, and output quality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
