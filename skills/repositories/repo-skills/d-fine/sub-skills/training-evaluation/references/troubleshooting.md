# Training and Evaluation Troubleshooting

This page focuses on fast diagnosis for `train.py` command construction and run-time failures.

## Quick symptoms and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `Only support from_scrach or resume or tuning at one time` | Both resume and tuning were selected, or a command was built with contradictory checkpoint semantics | Choose exactly one mode: `train`, `test`, `resume`, or `tune`. For interrupted jobs use `resume`; for dataset/class changes use `tune`. |
| `total_batch_size should be divisible by world size` | DDP world size and per-run total batch size do not match | Make `train_dataloader.total_batch_size` divisible by the number of processes, or reduce `--nproc` / visible GPUs. |
| `state['ema']['module']` missing or checkpoint key mismatch | The checkpoint is not a full training state, or the wrong key family was passed to `resume`/`tune` | Use a training checkpoint such as `last.pth` or a best-state file. For tuning, the loader prefers `ema.module` and falls back to `model`. |
| Fine-tuning on a new class set loads but metrics look wrong | The dataset class count or mapping does not match the checkpoint head assumptions | Verify the dataset config first. For COCO-like custom data, keep `remap_mscoco_category: False` when required and choose the right class-count config. |
| CUDA OOM or unstable memory use | Model size, image size, batch size, or number of processes is too large | Lower `total_batch_size`, reduce input size, switch to a smaller model, or reduce `--nproc`. AMP often helps memory pressure. |
| NaNs during training, or `NaN.pth` appears | AMP instability or numeric blow-up in the model/inputs | Disable AMP, lower the learning rate, inspect the batch, and use the saved `NaN.pth` for debugging. |
| Missing `matplotlib` during import or help display | The solver imports validation/visualization code that needs matplotlib | Install `matplotlib` together with the base training dependencies. CLI help is not fully import-isolated. |
| Missing `faster_coco_eval` during `train.py` import | The package imports the detection dataset stack before argparse finishes | Install the base repo training dependencies before expecting `train.py --help` to work. |
| Checkpoints keep appearing in the wrong directory | `--output-dir` was not set or a stale directory was reused | Set a fresh output directory for a new run; reuse the same directory only for resume. |
| TensorBoard is empty | `--summary-dir` was not set and the default summary folder was not inspected | Check `<output-dir>/summary`, or pass an explicit `--summary-dir`. |

## Resume vs tuning

These two modes look similar but behave differently:

- **Resume** restores the whole solver state and is meant for the same experiment.
- **Tuning** restores model weights only and is meant for a new dataset or class layout.

If a user asks to resume and tune simultaneously, the answer should be **no**. Split it into two phases if needed:
1. resume the interrupted training run, or
2. start a separate tuning run from the resumed or pretrained checkpoint.

## Checkpoint family guide

- `last.pth`: preferred for resume.
- `checkpointXXXX.pth`: also a valid full training checkpoint.
- `best_stg1.pth` / `best_stg2.pth`: valid solver checkpoints, useful for evaluation or as a starting point if you know which stage you want.
- `eval.pth`: metrics artifact, not a training checkpoint.
- Bare model-only files may work for tuning if the state keys match, but they are not the safest resume target.

## Object365 / custom class mapping

When tuning from Objects365 weights:
- The loader tries to map classifier head weights across datasets.
- The default mapping assumes the Objects365-to-COCO style class alignment used by the repo examples.
- For a custom dataset, confirm the class-count and mapping story before trusting transfer accuracy.

Practical rule:
- If the target dataset is COCO-like, use the matching COCO or Objects365-to-COCO config family.
- If the target dataset has different categories, keep the data/config guidance in the sibling sub-skill aligned with the class count before you tune.

## AMP / EMA / output interactions

- `use_amp` comes from the runtime and optimizer includes. It can be enabled with `--use-amp` or config overrides.
- `use_ema` is a config/runtime choice, not a special training mode.
- EMA checkpoints are saved as part of the solver state and may affect which weight family is loaded on resume/tuning.
- Output directories are created automatically, so an unwritable or stale path often shows up as a checkpoint write failure rather than an early parse error.

## DDP preflight checks

Before printing a distributed command, verify:
- `CUDA_VISIBLE_DEVICES` lists the GPUs you really want.
- `--nproc_per_node` matches the topology you expect.
- `train_dataloader.total_batch_size` and `val_dataloader.total_batch_size` are divisible by the world size.
- `--master_port` is free.
- The checkpoint path is reachable on every rank if you are resuming or tuning.

## When to hand off elsewhere

- If the failure is really about dataset layout, COCO JSON structure, or class remapping, use `../data-and-configs/SKILL.md`.
- If the issue is model registry, component wiring, or backbone/decoder mismatch, use `../architecture-api/SKILL.md`.
- If the issue is ONNX / TensorRT / OpenVINO or benchmark output naming, use `../inference-export/SKILL.md`.
