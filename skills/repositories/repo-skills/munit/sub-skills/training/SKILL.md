---
name: training
description: "Construct safe MUNIT and UNIT training commands and diagnose
  outputs, checkpoints, resume, and config tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MUNIT training sub-skill

Use this sub-skill when the user needs to plan or run a MUNIT repository training job, choose between the `MUNIT` and `UNIT` trainers, understand output/checkpoint layout, resume a stopped run, or tune training/config/loss surfaces before launching a long GPU job.

This sub-skill is self-contained operating knowledge distilled from the repository training entrypoint, trainer classes, utility helpers, configs, tutorial/manual training sections, and demo shell workflows. It intentionally does not depend on reopening source files.

## Boundaries

Use this sub-skill for:

- Building a safe dry-run training command.
- Explaining the `train.py` CLI and the infinite-until-`max_iter` training loop.
- Selecting `MUNIT` versus `UNIT` and checking trainer-specific config keys.
- Understanding where logs, generated image grids, HTML, config copies, and checkpoints are written.
- Resuming from `gen_*.pt`, `dis_*.pt`, and `optimizer.pt` checkpoint directories.
- Troubleshooting CUDA-only paths, resume folders, VGG side effects, tensorboardX import failures, old PyTorch/PyYAML warnings, and display sampling errors.

Reroute instead:

- Dataset schema, folder/list validation, and data-loader repair: `../data-and-configuration/`.
- Dependency installation, legacy Docker/conda setup, CUDA compatibility, and import smoke checks: `../environment-and-setup/`.
- Generator/discriminator architecture edits or porting internals: `../model-internals/`.
- Post-training checkpointed inference, batch translation, or metrics: `../inference-and-evaluation/`.

## Critical operating facts

- Training is CUDA-oriented. The training path calls `.cuda()` on the trainer, sampled display tensors, each input batch, MUNIT style tensors, VAE noise tensors, and VGG preprocessing tensors. There is no CLI flag for CPU-only training.
- The only exposed training CLI flags are `--config`, `--output_path`, `--resume`, and `--trainer` (`MUNIT|UNIT`).
- The default trainer is `MUNIT`. `UNIT` is selectable by CLI but needs UNIT-specific KL loss weights (`recon_kl_w`, `recon_kl_cyc_w`) that are not present in the bundled MUNIT demo configs.
- The model name is the config filename stem. Training writes under `<output_path>/logs/<model_name>` and `<output_path>/outputs/<model_name>`.
- Full training is long-running and should be launched only after environment and data/config checks pass, GPU availability is intentional, and the user has authorized a long job.

## Safe command construction

The bundled helper performs static checks and prints a command without executing training:

```bash
python scripts/munit_train_command.py --help
python scripts/munit_train_command.py \
  --repo-root /path/to/user/munit-checkout \
  --config configs/demo_edges2handbags_folder.yaml \
  --output-path runs/demo_edges2handbags \
  --trainer MUNIT
```

Only after the user explicitly authorizes a real run, use the printed command from the repository root in a suitable legacy CUDA runtime. Do not treat the helper as a launcher; it never downloads data, starts CUDA, or imports the repository package.

## Reference map

- `references/workflows.md` - staged training and resume workflows, including the distilled training loop and demo-script adaptation notes.
- `references/cli-reference.md` - training CLI arguments, trainer selection, trainer update methods, and config/loss tuning surfaces.
- `references/checkpoints-and-outputs.md` - output tree, image/log/checkpoint filenames, resume behavior, and monitoring expectations.
- `references/troubleshooting.md` - failure-mode lookup for CUDA, config, display sampling, resume, VGG, logging, tensorboardX, and legacy warnings.
- `scripts/munit_train_command.py` - self-contained dry-run command builder and static validator.
