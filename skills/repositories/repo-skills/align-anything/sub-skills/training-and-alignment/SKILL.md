---
name: training-and-alignment
description: "Route Align-Anything training modules, alignment algorithms,
  configs, datasets, launchers, and trainer troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Training and Alignment

Use this sub-skill when a task asks how to train, fine-tune, align, launch, configure, or debug Align-Anything trainer modules. It covers core trainer routing across text, image, audio, video, any-to-any, diffusion, Janus-aligned, and VLA/action flows.

## First Decision

1. Identify the requested **modality** and **algorithm**.
   - Examples: `text_to_text/sft`, `text_image_to_text/dpo`, `text_audio_to_text/ppo`, `text_video_to_text/rm`, `text_to_image/dpo`, `any_to_any/sft`, `janus/dpo_gen`, `text_video_to_action/sft`.
2. Read `references/training-workflows.md` to select the trainer module, default config identifier, expected launcher, and required model/data arguments.
3. Read `references/config-and-data.md` before editing overrides, dataset templates, multi-dataset settings, prompt/preference data, diffusion data, Janus tokenized data, or VLA data.
4. Prefer the bundled launch template instead of copying repository shell scripts:

   ```bash
   bash scripts/launch_training_template.sh --dry-run
   ```

5. If a config or override is unclear, inspect it with:

   ```bash
   python scripts/inspect_alignment_config.py --task text_to_text/sft --show --templates
   ```

6. If a launch/import/model/data failure appears, read `references/troubleshooting.md` before changing trainer code.

## Route When

- The task mentions SFT, DPO, PPO, PPO with remote reward model, RM, reward scoring, cost model, safer RLHF, GRPO, KTO, ORPO, SimPO, diffusion SFT/DPO, or vLLM PPO.
- The task mentions training configs, `train_cfgs`, `data_cfgs`, `model_cfgs`, `logger_cfgs`, LoRA, QLoRA/BnB, DeepSpeed ZeRO, `torchrun`, Slurm, `ZERO_STAGE_FILE`, or CLI overrides.
- The task asks how to format supervised, preference, prompt-only, diffusion, any-to-any, Janus, or VLA/action datasets.
- The task needs to diagnose trainer import, CUDA/DeepSpeed, batch-size divisibility, tokenizer/processor mismatch, dataset filtering, remote reward model, or checkpoint/save failures.

## Avoid When

- For model loading, serving CLIs, or multimodal inference without training, use the serving/model-loading sub-skill if available.
- For standalone remote reward server implementation details, use the remote-reward-models sub-skill if available; return here for the `ppo_remote_rm` trainer wiring.
- For project-folder preprocessing or satellite workflows such as Chameleon pre-tokenization or Janus project data creation, use `project-workflows` first, then return here to launch core trainer modules.
- Do not run heavy training, benchmark, or dataset-download commands unless the downstream Researcher has an explicit runtime, model, data, device, and output plan.

## Operating Notes

- Most core trainers are launched as Python modules. DeepSpeed-backed trainers call `deepspeed.init_distributed()` and should usually be launched with `deepspeed` or `torchrun`; diffusion trainers use Accelerate internals and are safest under `torchrun` or `accelerate launch`.
- CLI overrides are leaf-key based: repository scripts pass flags like `--model_name_or_path`, `--train_datasets`, `--train_template`, `--output_dir`, `--learning_rate`. Avoid category-prefixed overrides unless you have inspected the current override parser.
- Janus trainers are optional: representative core trainers import in the prepared runtime, while Janus trainer imports need the optional Janus-compatible package path/package.
- DeepSpeed may import with a CUDA toolkit warning when `CUDA_HOME` is absent; distinguish an import warning from a launch-time CUDA extension build or fused optimizer failure.

## Handoff Checklist

When handing a training plan to execution, include:

- Trainer module and config task identifier.
- Launcher choice (`deepspeed`, `torchrun`, `accelerate`, or Slurm wrapper) and GPU/world-size assumptions.
- Required model path(s), processor path, reward/cost/critic/remote-RM endpoint, and any optional package prerequisites.
- Dataset path(s), split/name/data-files, template(s), and whether data is supervised, preference, prompt-only, diffusion, pre-tokenized, or VLA/action.
- DeepSpeed/precision/LoRA/BnB/ZeRO overrides and output directory.
- Known unsupported or optional areas from `references/troubleshooting.md`.
