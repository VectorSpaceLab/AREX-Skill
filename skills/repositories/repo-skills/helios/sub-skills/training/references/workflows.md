# Training workflows

## Stage map

| Stage | Purpose | Typical config family |
| --- | --- | --- |
| Stage 1 | Adapt the architecture into an autoregressive generator | stage-1 init/post configs |
| Stage 2 | Add pyramid prediction/correction and token compression | stage-2 init/post configs |
| Stage 3 | Distill the model with DMD/ODE/GAN/self-forcing variants | stage-3 ODE/post/GAN/self-forcing configs |

## Recommended launch order

1. Validate the video metadata and latent/prompt artifacts with
   `data-preparation`.
2. Pick the nearest stage config family.
3. Run `scripts/validate_train_config.py` on the edited config.
4. Decide DDP or DeepSpeed.
5. Launch a small validation-first run before a long job.
6. Only after training succeeds, handle checkpoint/LoRA merge steps.

## DDP versus DeepSpeed

- **DDP** is the simpler baseline for ordinary distributed training.
- **DeepSpeed** is an alternative for memory-heavy and ZeRO-style workflows.
- DMD training with separate generator/critic DeepSpeed configs requires the
  corresponding generator and critic config paths.

## Checkpoint/LoRA handling

Training can load custom model checkpoints, LoRA weights, and extra Helios
components. When merging or resuming:

- keep the transformer checkpoint path, LoRA weights, and partial-component file
  aligned with the same training stage;
- preserve the config that created the checkpoint;
- verify whether EMA or ZeRO-3 state is involved before assuming a standard
  safetensors-only merge is enough.
