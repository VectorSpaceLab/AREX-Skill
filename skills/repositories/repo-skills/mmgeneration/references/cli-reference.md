# CLI Reference

## Purpose

Read this when you need the repo's main command families, flags, and when to use each script.

## Main commands

### `tools/misc/print_config.py`

Print the fully resolved config after inheritance and `--cfg-options` overrides.

```bash
python tools/misc/print_config.py CONFIG [--cfg-options KEY=VALUE ...]
```

Use this before editing or training when you want to confirm the final config tree.

### `tools/train.py`

Single-process or launcher-aware training entry point.

```bash
python tools/train.py CONFIG [--work-dir DIR] [--resume-from CKPT] [--no-validate]
                      [--gpu-id ID | --gpus N | --gpu-ids IDS ...]
                      [--seed SEED] [--diff_seed] [--deterministic]
                      [--cfg-options KEY=VALUE ...]
                      [--launcher none|pytorch|slurm|mpi]
```

Key points:

- `--work-dir` overrides the config or default work directory.
- `--resume-from` resumes from a checkpoint; `cfg.load_from` is still respected if resume is absent.
- `--no-validate` suppresses evaluation during training.
- `--launcher` controls distributed launch behavior.

### `tools/evaluation.py`

Unified evaluation and sample-generation entry point for unconditional and diffusion-style models.

```bash
python tools/evaluation.py CONFIG CKPT [--batch-size N] [--samples-path DIR]
                                     [--sample-model ema|orig]
                                     [--eval METRIC ...] [--online]
                                     [--num-samples N]
                                     [--sample-cfg KEY=VALUE ...]
```

Useful flags:

- `--eval none` means sample images only.
- `--online` keeps metric feeding in memory instead of round-tripping through disk.
- `--sample-cfg` passes custom kwargs to the model's sampling method.

### `tools/utils/translation_eval.py`

Translation-model evaluation and image-saving entry point.

```bash
python tools/utils/translation_eval.py CONFIG CKPT [--target-domain DOMAIN]
                                                   [--batch-size N]
                                                   [--samples-path DIR]
                                                   [--sample-model ema|orig]
                                                   [--eval METRIC ...]
                                                   [--online]
```

The translation path builds data from `cfg.data.test` if present, otherwise `cfg.data.train`.

### `tools/utils/inception_stat.py`

Precompute real-image inception statistics for FID and related workflows.

```bash
python tools/utils/inception_stat.py --imgsdir DIR --pklname NAME.pkl [--pkl-dir DIR]
                                     [--pipeline-cfg CFG] [--flip]
                                     [--size H W] [--batch-size N]
                                     [--num-samples N] [--no-shuffle]
                                     [--subset train|test]
                                     [--inception-style pytorch|stylegan]
                                     [--inception-pth PATH]
```

### Demo scripts

- `demo/unconditional_demo.py` — sample unconditional GANs.
- `demo/conditional_demo.py` — sample class-conditional GANs.
- `demo/translation_demo.py` — translate a single image.
- `demo/ddpm_demo.py` — sample DDPM outputs.

These are useful as command-shape references, but the generated skill should prefer the bundled helpers and sub-skill references instead of the original checkout paths.

### Application / deployment scripts

- `apps/interpolate_sample.py` and `apps/conditional_interpolate.py` — latent interpolation.
- `apps/stylegan_projector.py` — latent projection.
- `apps/modified_sefa.py` — closed-form factorization / latent editing.
- `apps/styleclip.py` — CLIP-guided style editing.
- `tools/deployment/mmgen2torchserver.py` — TorchServe `.mar` packaging.
- `tools/deployment/test_torchserver.py` — simple TorchServe request client.

## Common flag conventions

- `config` and `checkpoint` are usually positional arguments.
- `--cfg-options` accepts `KEY=VALUE` overrides in MMCV's config syntax.
- Sampling commands often accept `--sample-model ema|orig`.
- Translation commands often accept `--target-domain`.
- Distributed launchers use `--launcher` or shell wrappers for `slurm`.
