---
name: supervised-preference-training
description: "Build and review OpenRLHF supervised/preference training plans for
  SFT, reward models, DPO, IPO, and cDPO. Use for train_sft/train_rm/train_dpo
  CLI construction, LoRA/packing/DeepSpeed/checkpoint/logging choices, and
  preflight checks before expensive GPU training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Supervised Preference Training

Use this sub-skill when the user is preparing OpenRLHF SFT, reward-model, DPO, IPO, or cDPO training and needs command construction, flag review, or risk checks. Treat all actual training launches as expensive GPU/network actions.

## Route First

- For SFT, use `openrlhf.cli.train_sft` with prompt/completion keys such as `--data.input_key` and `--data.output_key`.
- For reward-model training, use `openrlhf.cli.train_rm` with preference keys such as `--data.chosen_key` and `--data.rejected_key`.
- For DPO, IPO, and cDPO, use `openrlhf.cli.train_dpo`; add `--model.ipo_enable` for IPO and `--model.label_smoothing` for cDPO.
- For detailed dataset schema conversion, chat templates, multiturn examples, and key mapping, route to the `data-preparation` sub-skill.
- For PPO, REINFORCE++, Ray, vLLM, remote actors, and agent training, route to the `rl-agent-training` sub-skill.
- For installation, FlashAttention/Liger/RingAttention dependencies, Ray clusters, serving, Docker, and environment repair, route to `operations-and-utilities`.

## Core References

- Read `references/training-workflows.md` for SFT/RM/DPO workflow recipes, source-backed shell patterns, and preflight order.
- Read `references/cli-reference.md` for current CLI flag names and source-backed defaults.
- Read `references/troubleshooting.md` for common failure modes before recommending a training run.
- Use `scripts/build_training_command.py` to print a safe command skeleton without importing OpenRLHF or starting training.

## Command Builder

The bundled helper is safe for planning and help-only validation:

```bash
python skills/openrlhf/sub-skills/supervised-preference-training/scripts/build_training_command.py sft --model MODEL --dataset DATASET --output-dir OUT
python skills/openrlhf/sub-skills/supervised-preference-training/scripts/build_training_command.py rm --model MODEL --dataset DATASET --output-dir OUT
python skills/openrlhf/sub-skills/supervised-preference-training/scripts/build_training_command.py dpo --model MODEL --dataset DATASET --output-dir OUT --ref-model REF --beta 0.1 --label-smoothing 0.1 --nll-loss-coef 0.05
```

It prints `deepspeed --module openrlhf.cli.train_* ...` commands for review. It does not check GPU availability, download models, import OpenRLHF, or execute the result.

## Safety Checklist

Before approving or launching a generated command:

- Confirm model and dataset identifiers/paths are intended and access-controlled; Hugging Face or ModelScope names may trigger network downloads.
- Confirm dataset keys match the selected trainer; SFT uses input/output keys, RM/DPO use chosen/rejected preference keys.
- Confirm `--train.batch_size` is global and `--train.micro_batch_size` is per GPU; reduce micro-batch size or use ZeRO-3/offload/LoRA for OOM.
- Confirm optional kernels (`flash_attention_2`, Liger, RingAttention) and 4-bit/LoRA dependencies exist before using their flags.
- Confirm checkpoint behavior: `--ckpt.save_steps -1` disables periodic DeepSpeed checkpoint saves; `--ckpt.save_hf` writes HF-format saves at checkpoint intervals.
- Prefer source-backed `--model.model_name_or_path` over older README snippets that may mention `--actor.model_name_or_path` for these CLIs.

## Evidence Base

This sub-skill is based on OpenRLHF training entrypoints `openrlhf.cli.train_sft`, `openrlhf.cli.train_rm`, and `openrlhf.cli.train_dpo`; trainers `sft_trainer.py`, `rm_trainer.py`, and `dpo_trainer.py`; README SFT/RM/DPO examples; and example shell recipes for SFT, RM, DPO, and SFT LoRA. The installed package import was verified for `openrlhf` version `0.10.4`, but full dependency and GPU runtime readiness were not verified.
