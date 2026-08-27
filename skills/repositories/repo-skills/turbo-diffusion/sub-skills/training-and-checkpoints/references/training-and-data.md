# Training And Data Setup

This reference covers TurboDiffusion rCM/SLA training setup reasoning and debug-only command construction. Treat full training and dataset synthesis as skip-expensive unless the user explicitly authorizes GPU/model/data work.

## What the training path does

TurboDiffusion provides Wan2.1 training code built on the rCM training stack. The selected training families are:

- **SLA training**: white-box Sparse-Linear Attention training that aligns an SLA-enabled model with the full-attention pretrained teacher. The public registry is `registry_sla`; the main experiments are `wan2pt1_1pt3B_res480p_t2v_SLA` and `wan2pt1_14B_res480p_t2v_SLA` plus `_debug` variants.
- **rCM distillation**: timestep distillation based on the rCM flow. The public registry is `registry_distill`; the main experiments are `wan2pt1_1pt3B_res480p_t2v_rCM` and `wan2pt1_14B_res480p_t2v_rCM` plus `_debug` variants.

Both paths use FSDP-style distributed checkpointing, Wan2.1 VAE/text encoder assets, and WebDataset-style tar shards containing latent/video conditioning tensors.

## Additional training dependencies

The base runtime dependencies are not enough for real training. A training environment also needs the training/config/data/logging stack:

- `megatron-core`
- `hydra-core`
- `wandb`
- `webdataset`
- `transformer_engine[pytorch]` installed without build isolation when required by the CUDA/PyTorch stack

The source package also uses top-level imports such as `rcm`, `imaginaire`, and `scripts`. In a source-layout checkout, set `PYTHONPATH` to the package source directory before running public scripts. In an installed environment, verify whether those top-level modules are packaged as expected; the source-layout `PYTHONPATH` setting is the documented reliable workaround.

## Required layout before real training

Use placeholders and user-provided roots; do not hardcode private machine paths.

```text
<workdir>/
  assets/
    checkpoints/
      Wan2.1-T2V-1.3B.dcp          # or Wan2.1-T2V-14B.dcp for 14B
      Wan2.1_VAE.pth
      models_t5_umt5-xxl-enc-bf16.pth
      umT5_wan_negative_emb.pt
    datasets/
      Wan2.1_14B_480p_16:9_Euler-step100_shift-3.0_cfg-5.0_seed-0_250K/
        shard*.tar
  outputs/                         # IMAGINAIRE_OUTPUT_ROOT or equivalent output root
```

Checklist:

1. `IMAGINAIRE_OUTPUT_ROOT` points to a writable output directory.
2. `model.config.teacher_ckpt` points to a DCP directory, not a `.pth` file.
3. `model.config.tokenizer.vae_pth` points to the Wan2.1 VAE `.pth`.
4. `model.config.text_encoder_path` points to the umT5 encoder checkpoint.
5. `model.config.neg_embed_path` points to the precomputed negative embedding.
6. `dataloader_train.tar_path_pattern` matches at least one `.tar` shard.
7. Decide WANDB policy before real training: authenticated online logging, offline mode, or callback/config override. Never embed API keys in generated commands.

## DCP prerequisite

FSDP training loads teacher checkpoints through PyTorch Distributed Checkpoint (DCP). Convert a pretrained `.pth` teacher checkpoint to DCP before training:

```bash
python -m torch.distributed.checkpoint.format_utils torch_to_dcp \
  <checkpoint-root>/Wan2.1-T2V-1.3B.pth \
  <checkpoint-root>/Wan2.1-T2V-1.3B.dcp
```

For 14B, substitute the 14B teacher checkpoint names. After training, convert saved DCP directories back to `.pth` with the DCP-to-PTH workflow in [checkpoint-workflows.md](checkpoint-workflows.md).

## Dry-run command first

For training setup tasks, first render a dry-run command with [../scripts/build_training_dryrun_command.py](../scripts/build_training_dryrun_command.py). The command composes the config and writes a config YAML; it does not start training.

Example command-builder use:

```bash
python <skill-root>/sub-skills/training-and-checkpoints/scripts/build_training_dryrun_command.py \
  --registry registry_sla \
  --model-size 1.3B \
  --checkpoint-root assets/checkpoints \
  --dataset-root 'assets/datasets/Wan2.1_14B_480p_16:9_Euler-step100_shift-3.0_cfg-5.0_seed-0_250K'
```

The generated public command has this shape:

```bash
PYTHONPATH=<package-source-dir> IMAGINAIRE_OUTPUT_ROOT=<output-root> \
  torchrun --nproc_per_node=<N> -m scripts.train \
  --config=<package-source-dir>/rcm/configs/<registry>.py \
  --dryrun -- \
  experiment=<experiment-name> \
  model.config.teacher_ckpt=<checkpoint-root>/<teacher>.dcp \
  model.config.tokenizer.vae_pth=<checkpoint-root>/Wan2.1_VAE.pth \
  model.config.text_encoder_path=<checkpoint-root>/models_t5_umt5-xxl-enc-bf16.pth \
  model.config.neg_embed_path=<checkpoint-root>/umT5_wan_negative_emb.pt \
  dataloader_train.tar_path_pattern='<dataset-root>/shard*.tar'
```

Keep `--dryrun` in place until the user explicitly asks for real training and all expensive prerequisites are acknowledged.

## Debug experiments still need real assets for real training

The `_debug` experiments reduce iterations and logging intervals, but they do not remove all runtime requirements. For actual training, even a debug experiment still needs:

- CUDA-capable PyTorch and compatible distributed launch.
- Model and tokenizer checkpoints in the configured roots.
- A DCP teacher checkpoint, not only a `.pth` checkpoint.
- A dataset shard glob that matches actual tar files.
- Training extras and WANDB/offline logging policy.

If the user asks for "SLA debug training" but has not supplied DCP conversion, WANDB/offline policy, or data shards, stop at the dry-run/config command and list the missing prerequisites.

## WebDataset shard schema

The training dataloader expects a glob pattern such as `<dataset-root>/shard*.tar`. Each sample inside a tar shard is grouped by a common prefix and should contain:

- `<sample>.latent.pt` loaded as `latents`
- `<sample>.embed.pt` loaded as `t5_text_embeddings`
- `<sample>.prompt.txt` loaded as `prompts`

A quick non-mutating validation can inspect tar member names without decoding tensors:

```bash
python - <<'PY'
import glob, tarfile
pattern = '<dataset-root>/shard*.tar'
paths = sorted(glob.glob(pattern))
print('matched_shards', len(paths))
if paths:
    with tarfile.open(paths[0], 'r') as tar:
        names = tar.getnames()[:20]
    print('\n'.join(names))
PY
```

Do not synthesize datasets by default. Dataset synthesis is itself a CUDA/model-generation workload and should be treated as skip-expensive.

## Minimum handoff for a real training request

Before allowing real training, collect and record:

- Training family: `registry_sla` or `registry_distill`.
- Experiment name and whether `_debug` is intended.
- GPU count and distributed launch parameters.
- Checkpoint root, teacher DCP path, VAE path, text encoder path, negative embedding path.
- Dataset shard pattern and sample count/sanity check.
- Output root and overwrite/resume policy.
- WANDB policy: online credentials already available in the user's environment, offline mode, or callback/config override.
- Whether post-training DCP-to-PTH conversion and merge/export are requested.
