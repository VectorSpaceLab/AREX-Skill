# Training workflows

## Modular YAML trainer

The modular stack's entry point is:

```bash
python -m fastvideo.train.entrypoint.train --config train.yaml --dry-run
```

Use `--dry-run` to parse/build without starting training. A real run requires
model weights, precomputed data, one or more suitable GPUs, output storage, and
possibly W&B credentials. Dotted configuration overrides belong in the launcher
or the schema-supported YAML workflow; keep optimizer/sampler settings under
their owning sections.

The composition model is `Method × Model × [Callback...] × Config`. Fine-tuning,
DMD2, self-forcing, knowledge distillation, consistency, and RL methods are
selected independently from model-family wrappers. Reward classes should
return one scalar per sample and explicitly define which image/video frames they
score.

## Legacy stack

The legacy monolithic stack remains authoritative for shipped Wan/LTX-2/
Matrix-Game recipes. It uses distributed launchers and flat legacy arguments.
Use it only when following an existing shipped recipe; do not import from
`fastvideo.train` into `fastvideo.training` or the reverse.

## Resource controls

For OOM, reduce batch/frame/latent dimensions, use gradient accumulation,
sequence/tensor/HSDP sharding, checkpointing, LoRA, or fewer validation samples.
For reproducibility record config, seed, model revision, dataset revision,
world size, precision, and checkpoint path. Keep output checkpoints separate
from input data and avoid destructive overwrite.
