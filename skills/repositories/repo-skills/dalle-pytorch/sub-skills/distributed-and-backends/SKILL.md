---
name: distributed-and-backends
description: "Choose and troubleshoot DALLE-pytorch CUDA, DeepSpeed, Horovod,
  Apex, Docker, sparse attention, and distributed checkpoint paths."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Distributed and backend workflows

Use this sub-skill for CUDA readiness, DeepSpeed, Horovod, Apex AMP, Docker GPU images, sparse attention, distributed parser flags, and checkpoint behavior.

## Read first

- `references/distributed-backends.md` for backend flags, module availability, sparse attention, precision, and checkpoint notes.
- `references/docker-and-system-setup.md` for Docker/source-build caveats.
- `references/troubleshooting.md` for backend import, CUDA, Apex, Horovod, and DeepSpeed failures.
- `scripts/check_backend_availability.py` to inspect safe backend availability without launching training.

## Typical routes

| Request | Action |
| --- | --- |
| "Can I use DeepSpeed?" | Run/describe backend availability check, confirm `deepspeed` import, decide whether sparse attention or only distributed training is needed. |
| "What does `--deepspeed` do?" | Explain parser wrapping and that `args.deepspeed` maps to the `DeepSpeed` backend when available. |
| "Use Horovod" | Confirm `horovod.torch` import and use `horovodrun`-style launch; batch size semantics differ from DeepSpeed. |
| "Install Apex or sparse attention" | Treat as CUDA/source-build task requiring explicit approval; do not run bundled source install scripts blindly. |
| "Choose `attn_types`" | Use package attention options; only `sparse` needs DeepSpeed sparse attention, while `full`, `axial_row`, `axial_col`, and `conv_like` are package-level options. |

## Boundary notes

- Single-process VAE training belongs to `../vae-training/SKILL.md`.
- Single-process DALL-E training/data/tokenizer issues belong to `../dalle-training/SKILL.md`.
- Generation belongs to `../generation-and-ranking/SKILL.md`.

## Safety rules

- Do not run source builds, `sudo apt-get`, Docker builds, or distributed launchers without explicit approval.
- A CUDA allocation smoke is not proof that full training works; it only proves torch can see a device.
- Keep DeepSpeed/Apex/Horovod optional unless the user's selected workflow requires them.
