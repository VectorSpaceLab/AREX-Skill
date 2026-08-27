# CLI Reference

This reference lists command shapes and safe bundled helper usage for TurboDiffusion training and checkpoint workflows. Commands are public/generic templates; substitute user-provided paths and do not run expensive commands without explicit authorization.

## Source-layout import quirk

Several TurboDiffusion scripts import top-level modules such as `rcm`, `imaginaire`, `SLA`, `ops`, `scripts`, and `modify_model`. When running from a source layout, prefix commands with:

```bash
PYTHONPATH=<package-source-dir>
```

The common source directory name is `turbodiffusion`, but use the user's actual package source directory. This is a package-layout quirk, not a private setup requirement.

## Safe bundled helpers

All bundled helpers support `--help`, avoid downloads, and do not run training or model conversion.

### Build training dry-run command

```bash
python <skill-root>/sub-skills/training-and-checkpoints/scripts/build_training_dryrun_command.py --help
```

Common usage:

```bash
python <skill-root>/sub-skills/training-and-checkpoints/scripts/build_training_dryrun_command.py \
  --registry registry_sla \
  --model-size 1.3B \
  --nproc-per-node 1 \
  --checkpoint-root assets/checkpoints \
  --dataset-root 'assets/datasets/Wan2.1_14B_480p_16:9_Euler-step100_shift-3.0_cfg-5.0_seed-0_250K' \
  --output-root outputs
```

Useful options:

| Option | Meaning |
| --- | --- |
| `--registry {registry_sla,registry_distill}` | Select SLA training or rCM distillation config registry. |
| `--model-size {1.3B,14B}` | Select Wan2.1 model scale and derived teacher checkpoint/experiment defaults. |
| `--experiment <name>` | Override the derived `_debug` experiment name. |
| `--full-experiment-name` | Use the non-`_debug` experiment name while still rendering `--dryrun`. |
| `--nproc-per-node <N>` | Distributed launch process count for config composition. Defaults to `1` for safety. |
| `--master-port <port>` | Include an explicit torchrun master port. |
| `--checkpoint-root <dir>` | Root for teacher DCP, VAE, text encoder, and negative embedding defaults. |
| `--teacher-dcp <path>` | Override teacher DCP path. |
| `--vae-path <path>` | Override Wan2.1 VAE path. |
| `--text-encoder-path <path>` | Override umT5 text encoder path. |
| `--negative-embed-path <path>` | Override negative embedding path. |
| `--dataset-root <dir>` | Dataset directory used to derive `<dir>/shard*.tar`. |
| `--tar-pattern <glob>` | Override WebDataset shard glob. |
| `--extra-override KEY=VALUE` | Append extra Hydra/LazyConfig overrides after `--`. Can be repeated. |
| `--validate-layout` | Check supplied paths/globs on the current machine without running training. |
| `--one-line` | Print a single-line shell command instead of a line-broken command. |

The generated command always includes `--dryrun`. Keep it that way until the user explicitly approves real training.

### Build modify/export command

```bash
python <skill-root>/sub-skills/training-and-checkpoints/scripts/build_modify_model_command.py --help
```

Common usage for a quantized Wan2.2 high-noise I2V export command:

```bash
python <skill-root>/sub-skills/training-and-checkpoints/scripts/build_modify_model_command.py \
  --profile i2v-a14b-high-720p \
  --quant-linear \
  --attention-type sla
```

Useful options:

| Option | Meaning |
| --- | --- |
| `--profile <profile>` | Fill model/input/output defaults for common Wan2.1/Wan2.2 public checkpoint roles. |
| `--model {Wan2.1-1.3B,Wan2.1-14B,Wan2.2-A14B}` | Override model name passed to the export script. |
| `--input-path <path>` | rCM/SLA checkpoint path to read. |
| `--output-path <path>` | Destination modified inference checkpoint. |
| `--attention-type {original,sla,sagesla}` | Attention replacement mode. `sagesla` requires SpargeAttn/SageSLA support. |
| `--sla-topk <float>` | Top-k ratio for SLA/SageSLA replacement. |
| `--quant-linear` | Add `--quant_linear` for INT8 linear export. |
| `--keep-default-norms` | Add `--default_norm`, which keeps default norms instead of FastNorm replacements. |
| `--validate-inputs` | Check input path and output parent directory without running conversion. |
| `--one-line` | Print a single-line shell command. |

The rendered command can perform GPU-heavy conversion if a user runs it. The helper itself only prints the command.

### Build safetensors-to-PTH command

```bash
python <skill-root>/sub-skills/training-and-checkpoints/scripts/build_safetensors_to_pth_command.py --help
```

Common usage:

```bash
python <skill-root>/sub-skills/training-and-checkpoints/scripts/build_safetensors_to_pth_command.py \
  --model-dir checkpoints/hf_model \
  --output-path checkpoints/converted/model.pth \
  --prefix net.
```

Useful options:

| Option | Meaning |
| --- | --- |
| `--model-dir <dir>` | Directory containing `diffusion_pytorch_model.safetensors.index.json` and shard files. |
| `--output-path <path>` | Destination `.pth` file. |
| `--prefix <text>` | Optional prefix to add to every state-dict key, commonly `net.`. |
| `--validate-layout` | Check index JSON, referenced shards, and output parent directory. |
| `--one-line` | Print a single-line shell command. |

### Tiny merge arithmetic check

```bash
python <skill-root>/sub-skills/training-and-checkpoints/scripts/tiny_merge_models_check.py
```

This script creates tiny temporary `.pth` files, applies the source merge arithmetic on CPU, and asserts expected results for matching keys, shape-mismatched keys, non-tensor keys, and target-only keys. It is safe to run in a CPU environment with PyTorch installed.

Options:

| Option | Meaning |
| --- | --- |
| `--weight <float>` | Merge weight `w`; default `0.25`. |
| `--keep-dir` | Keep the temporary fixture directory and print its path. |
| `--output-dir <dir>` | Use a caller-specified fixture directory instead of a temp directory. |
| `--verbose` | Print the merged tensor values and fixture files. |

## Public training command shape

Dry-run/config composition:

```bash
PYTHONPATH=<package-source-dir> IMAGINAIRE_OUTPUT_ROOT=<output-root> \
  torchrun --nproc_per_node=<N> -m scripts.train \
  --config=<package-source-dir>/rcm/configs/<registry>.py \
  --dryrun -- \
  experiment=<experiment-name> \
  model.config.teacher_ckpt=<teacher-dcp-dir> \
  model.config.tokenizer.vae_pth=<vae-pth> \
  model.config.text_encoder_path=<umt5-pth> \
  model.config.neg_embed_path=<negative-embed-pt> \
  dataloader_train.tar_path_pattern='<dataset-root>/shard*.tar'
```

Real training uses the same shape but removes `--dryrun` only after the expensive-work gate is accepted and all prerequisites are present.

## Public checkpoint command shapes

Convert `.pth` teacher checkpoint to DCP before training:

```bash
python -m torch.distributed.checkpoint.format_utils torch_to_dcp \
  <teacher-pth> \
  <teacher-dcp-dir>
```

Convert training DCP directory back to `.pth`:

```bash
PYTHONPATH=<package-source-dir> python <package-source-dir>/scripts/dcp_to_pth.py \
  --dcp_checkpoint_dir <dcp-checkpoint-dir> \
  --save_path <output-pth>
```

Merge checkpoints by vector arithmetic:

```bash
PYTHONPATH=<package-source-dir> python <package-source-dir>/scripts/merge_models.py \
  --base <rcm-base-pth> \
  --diff_base <pretrained-or-reference-pth> \
  --diff_target <sla-tuned-pth> \
  --w 1.0 \
  --output <merged-output-pth>
```

Merge sharded safetensors into `.pth`:

```bash
PYTHONPATH=<package-source-dir> python <package-source-dir>/scripts/safetensors_to_pth.py \
  --model_dir <safetensors-model-dir> \
  --output_path <output-pth> \
  --prefix net.
```

Modify/export a checkpoint for inference:

```bash
PYTHONPATH=<package-source-dir> python <package-source-dir>/inference/modify_model.py \
  --input_path <merged-or-trained-pth> \
  --output_path <modified-output-pth> \
  --model Wan2.1-1.3B \
  --attention_type sla \
  --sla_topk 0.2 \
  --quant_linear
```

Omit `--quant_linear` for unquantized exports. Add `--default_norm` only when the user intentionally wants to keep default norm layers rather than FastNorm replacements.
