---
name: training-models
description: "Choose DeePMD-kit model families/backends and draft, launch,
  restart, fine-tune, monitor, and freeze training workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# DeePMD-kit Training Models

Use this sub-skill when the user wants to choose a DeePMD-kit model family, draft a training input, launch or restart `dp train`, monitor training progress, fine-tune from a checkpoint or pretrained model, run multi-task/pretrained workflows, or freeze a trained checkpoint.

Keep this route model-aware, backend-aware, and validation-oriented. Training may be expensive; prefer bounded smoke runs, command drafting, and config review before launching long jobs.

## Route Before Acting

- For raw data conversion, data-system layout, `type_map` construction, missing labels, or validation split decisions, route to [data-config](../data-config/SKILL.md).
- For testing a frozen model, descriptor evaluation, model deviation, Python `DeepPot` use, conversion, compression, or bias changes after training, route to [inference-model-ops](../inference-model-ops/SKILL.md).
- For LAMMPS, i-PI, C/C++ API, custom operator builds, or deployment packaging, route to [integrations-development](../integrations-development/SKILL.md).
- Stay here for model selection, training-input structure, training/fine-tuning command design, learning-curve interpretation, checkpoint handling, distributed launch shape, and `dp freeze` immediately after training.

## First Questions To Resolve

1. **Backend:** TensorFlow (`tf`), PyTorch (`pt`), JAX (`jax`), or Paddle (`pd`). Default to explicit backend flags in commands, even when TensorFlow would be default.
2. **Target:** quick baseline, production potential, large atomic model, property/tensor/DOS model, spin/Hessian/DPLR workflow, fine-tuning, or pretrained/multi-task training.
3. **Data readiness:** DeePMD data already exists, labels are known, and train/validation systems are separated; otherwise route to `data-config` first.
4. **Compute budget:** CPU smoke check, single GPU, multi-GPU, multi-node, or no execution requested.
5. **Deployment target:** Python inference, LAMMPS, model deviation, or only training/freeze. Use this to choose backend and freeze output.

## References

Read these bundled references as needed:

- [model-selection.md](references/model-selection.md) for model-family and backend selection.
- [training-workflows.md](references/training-workflows.md) for input structure, train/restart/fine-tune/freeze commands, multi-task, pretrained, and distributed workflows.
- [troubleshooting.md](references/troubleshooting.md) for common training failures and recovery actions.

Use the bundled helper to draft commands without running training:

```bash
python scripts/draft_training_command.py --backend pt --input input.json --skip-neighbor-stat
```

## Backend Command Rules

- TensorFlow: use `dp --tf train input.json`; checkpoints normally freeze to `.pb`.
- PyTorch: use `dp --pt train input.json`; checkpoints commonly end in `.pt` and frozen models in `.pth`.
- JAX: use `dp --jax train input.json`; confirm the selected model supports JAX before drafting.
- Paddle: use `dp --pd train input.json`; frozen output is a prefix that produces Paddle model files.
- `pytorch-exportable` / `pt-expt` is a parser alias for exportable PyTorch workflows; use only when the user specifically asks for that backend path.

## Model-Family Shortlist

- Choose `se_e2_a` for a robust DeepPot-SE baseline, compatibility, small-to-medium systems, or quick validation.
- Choose `se_e2_r` when radial-only features are sufficient and a lighter descriptor is desired.
- Choose `se_e3` or `se_e3_tebd` when three-body/angular information is important.
- Choose `se_atten` / DPA-1 for attention-based pretrainable models and larger chemical diversity.
- Choose DPA-2 for large atomic model or multi-task pretraining workflows with shared descriptors and task heads.
- Choose DPA-3 for high-accuracy large atomic model work, dynamic neighbor settings, and built-in pretrained fine-tuning workflows.
- Choose DPA-4 / SeZM for PyTorch equivariant message-passing workflows when the installed version supports it.
- Choose `hybrid` when combining multiple descriptors with different cutoffs is central to the experiment.
- Choose `linear` or `pairtab` when combining frozen models or empirical pair potentials with DeePMD components.
- Choose DPLR only for long-range electrostatic workflows with Wannier-center/dipole prerequisites.
- Choose spin, DOS, property, tensor, or Hessian workflows only when the matching labels and backend support are present.

## Safe Training Workflow

1. Confirm the selected backend is installed with `dp --<backend> -h` and inspect the available subcommands if needed.
2. Draft or review `input.json` / YAML with a complete `model`, `learning_rate`, `loss` or `loss_dict`, and `training` section.
3. Ensure `type_map` matches the data and, for fine-tuning, is compatible with the pretrained model.
4. Run or plan `neighbor-stat` / automatic `sel` unless `sel` is fixed and the user explicitly wants `--skip-neighbor-stat`.
5. For smoke validation, reduce `numb_steps`, `disp_freq`, and `save_freq`; do not use tutorial water data as production evidence.
6. Launch training only when the user asked to run it and the cost is bounded or accepted.
7. Monitor `lcurve.out` and console summaries for decreasing validation RMSE, finite losses, expected labels, and checkpoint creation.
8. Freeze from the checkpoint after training with the same backend family, then route post-freeze testing to `inference-model-ops`.

## Restart, Init, And Fine-Tune

- Use `--restart CHECKPOINT_PREFIX` to continue the same run, preserving optimizer/training state where supported.
- Use `--init-model CHECKPOINT_PREFIX` to initialize model weights for a new run without treating it as the same training trajectory.
- Use `--finetune MODEL` to adapt a frozen or checkpoint pretrained model and update the energy bias according to target data.
- Use `--use-pretrain-script` when the pretrained PyTorch/Paddle model embeds a compatible model definition and the new input should inherit descriptor/fitting settings.
- Use `--model-branch BRANCH` for multi-task pretrained fine-tuning; use `RANDOM` only when a randomly initialized fitting head is intended.
- Do not confuse checkpoints with frozen deployment models: checkpoints resume or initialize training; frozen models are primarily for inference/deployment and may need backend-specific handling.

## Multi-Task And Pretrained Routing

- PyTorch is the primary multi-task training backend. Confirm the input uses `shared_dict`, `model_dict`, `loss_dict`, and `training.data_dict` instead of single-task sections.
- Each task key must have matching model, loss, and data entries. Optional task sampling belongs in `training.model_prob` or epoch-based task controls.
- For multi-task freeze, select a head with `dp --pt freeze -o model_branch.pth --head BRANCH` or the `--model-branch` alias.
- For built-in pretrained models, inspect available names with `dp pretrained download -h`. Downloading may touch the network; ask before downloading unless the user confirmed cached/offline availability.
- For DPA3 fine-tuning from a built-in pretrained model, confirm model name, cache state, target `type_map`, and branch/head constraints before drafting the train command.

## Parallel Training

- TensorFlow distributed training uses Horovod/MPI launchers such as `horovodrun -np N dp --tf train input.json`.
- PyTorch distributed training uses `torchrun --nproc_per_node=N --no-python dp --pt train input.json`.
- Paddle distributed training uses `python -m paddle.distributed.launch` with an explicit GPU list and environment tuning.
- Distributed launch does not fix bad data/configs. First validate a single-process command unless the issue is distributed-only.
- In PyTorch, ZeRO stages are configured in the training input and require distributed launch; start with stage 0/1 unless memory pressure requires more.

## Monitoring Checklist

- `lcurve.out` exists and receives rows at `disp_freq`.
- Training and validation errors are finite and trend down after the early transient.
- Energy, force, virial, tensor, DOS, property, spin, or Hessian columns match the chosen loss and available labels.
- Checkpoints appear at `save_freq` with the expected backend-specific suffix/prefix.
- CPU-only runs are treated as smoke tests unless the user explicitly accepts long runtime.
- Tutorial water data is used only for workflow testing, not as production-quality model evidence.

## Completion Criteria

Before handing off, report the selected model family/backend, input file status, exact command drafted or run, neighbor-stat decision, checkpoint/freeze target, monitoring outcome, and any route-outs needed for data validation or post-freeze inference.
