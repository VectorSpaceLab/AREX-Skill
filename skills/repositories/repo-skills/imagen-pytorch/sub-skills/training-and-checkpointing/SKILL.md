---
name: training-and-checkpointing
description: "Use ImagenTrainer for imagen-pytorch training loops, dataloaders,
  EMA, Accelerate, checkpoint save/load, resume, and tiny trainer smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and Checkpointing

Use this sub-skill when the task mentions `ImagenTrainer`, `train_step`, `valid_step`, `add_train_dataset`, `add_train_dataloader`, `max_batch_size`, `checkpoint`, `resume`, `EMA`, `accelerate launch`, multi-GPU, or training one cascade unet at a time.

## Route First

- Model architecture, `Unet` / `Imagen` / `ElucidatedImagen` construction, image sampling shapes, low-resolution cascade semantics: [image-generation](../image-generation/SKILL.md).
- CLI config authoring and exact `imagen config`, `imagen train`, `imagen sample` command construction: [configuration-and-cli](../configuration-and-cli/SKILL.md).
- Folder datasets, Hugging Face collators, text-embedding dimensions, T5 cache/network avoidance, dataloader tuple schema: [data-and-text-conditioning](../data-and-text-conditioning/SKILL.md).
- Video and inpainting tensor ranks, masks, `video_frames`, `Unet3D`: [video-and-inpainting](../video-and-inpainting/SKILL.md).

## Operating Map

1. Start with an already-created `Imagen` or `ElucidatedImagen` instance. Prefer config-created models when checkpoints must later be loaded by CLI sampling or `load_imagen_from_checkpoint`.
2. Create exactly one `ImagenTrainer` per process for the unet being trained. Choose `only_train_unet_number` when a script is dedicated to one cascade stage. Do not set both `fp16=True` and `precision=...`.
3. Register datasets or dataloaders before the trainer is prepared. `train_step` and `valid_step` call `prepare()` lazily, so add `add_train_dataset` / `add_train_dataloader` and optional validation loaders first.
4. Train one unet number at a time. Use `train_step(unet_number=n, max_batch_size=m)` for dataloader-owned loops, or call the trainer directly on tensors followed by `update(unet_number=n)` for manual batches. `max_batch_size` performs gradient accumulation by splitting the batch.
5. Validate or sample only after the relevant dataloader/model inputs exist. Guard sampling and filesystem writes with `trainer.is_main` under Accelerate.
6. Save with `trainer.save(path)` for explicit checkpoint files, or configure `checkpoint_path` together with `checkpoint_every` for managed checkpoint folders. Resume by reconstructing the same model/trainer and calling `trainer.load(path)` before continuing.

## Read For Details

- [references/trainer-reference.md](references/trainer-reference.md): constructor invariants, lifecycle ordering, dataloader tuple handling, gradient accumulation, EMA, Accelerate, and tiny loop patterns.
- [references/checkpointing.md](references/checkpointing.md): save/load state contents, commandable checkpoints, checkpoint folders, fsspec notes, resume/fine-tune patterns.
- [references/troubleshooting.md](references/troubleshooting.md): assertion messages and recovery actions for trainer, dataloader, unet, checkpoint, and Accelerate failures.
- [scripts/tiny_trainer_smoke.py](scripts/tiny_trainer_smoke.py): standalone no-network smoke adapted from the repo trainer test; use it to confirm import, tiny trainer construction, and optionally one tiny train step.

## Verification Posture

Tiny CPU or CUDA smoke checks prove API control flow, not realistic diffusion quality. Real Imagen training, generation, and video workflows are practical CUDA-scale tasks and remain expensive even when CUDA import and allocation smoke checks pass.
