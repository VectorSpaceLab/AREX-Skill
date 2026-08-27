# Training Workflow Reference

ControlNet tutorial training has three separable phases: validate a Fill50K-style dataset, initialize a ControlNet checkpoint from an SD base checkpoint, and run a PyTorch Lightning trainer with the matching ControlNet config.

## Preflight Checklist

Before starting a long run:

1. Validate the dataset with `../scripts/validate_fill50k_dataset.py`.
2. Confirm `prompt.json` rows return `jpg`, `txt`, and `hint` in the expected shapes and ranges.
3. Confirm the initialized ControlNet checkpoint exists for the SD family being trained.
4. Confirm the YAML config family matches the checkpoint family.
5. Run a small data-loader smoke test or very short training attempt before enabling expensive logging or long schedules.
6. Expect full tutorial imports/runs to require model code, data, checkpoint files, GPU memory, and possibly external tokenizer/model downloads.

## SD1.5 Tutorial Pattern

Use this pattern for SD1.5-derived ControlNet training:

| Setting | Tutorial value | Purpose |
| --- | --- | --- |
| Config | `models/cldm_v15.yaml` | ControlNet + SD1.5 architecture; expects `jpg`, `txt`, `hint`. |
| Initial checkpoint | `models/control_sd15_ini.ckpt` | SD1.5 base weights with ControlNet weights attached. |
| Batch size | `4` | Starting tutorial value; reduce for smaller GPUs. |
| Logger frequency | `300` | Image logger batch frequency. |
| Learning rate | `1e-5` | Default ControlNet fine-tuning rate. |
| `sd_locked` | `True` | Keeps original SD blocks locked to preserve base model behavior. |
| `only_mid_control` | `False` | Trains the normal ControlNet conditioning path. |
| Trainer | `pl.Trainer(gpus=1, precision=32, callbacks=[logger])` | Original Lightning 1.x style. |

Initial ControlNet checkpoint creation is handled by the model/weight utility sub-skill, not this training sub-skill. Use [model-and-weight-utilities](../../model-and-weight-utilities/SKILL.md) for the SD-to-ControlNet initialization step.

## SD2.1 Tutorial Pattern

Use this pattern for SD2.1-derived ControlNet training:

| Setting | SD2.1 value | Difference from SD1.5 |
| --- | --- | --- |
| Config | `models/cldm_v21.yaml` | Uses SD2.1/OpenCLIP text conditioning dimensions. |
| Initial checkpoint | `models/control_sd21_ini.ckpt` | Created from an SD2.1 base checkpoint. |
| Init helper | SD2.1-specific ControlNet init flow | Route checkpoint creation to model/weight utilities. |
| Dataset contract | `jpg`, `txt`, `hint` | Same as SD1.5. |
| Training knobs | Same defaults | Tune for memory and dataset behavior. |

Do not mix SD1.5 checkpoints with the SD2.1 YAML or SD2.1 checkpoints with the SD1.5 YAML. Mismatches usually appear as missing/unexpected state dict keys, shape mismatches, or text encoder conditioning errors.

## Minimal Training Skeleton

A training script adapted from the tutorial normally does the following:

```python
model = create_model(config_path).cpu()
model.load_state_dict(load_state_dict(resume_path, location="cpu"))
model.learning_rate = learning_rate
model.sd_locked = sd_locked
model.only_mid_control = only_mid_control

dataset = MyDataset(dataset_root)
dataloader = DataLoader(dataset, num_workers=0, batch_size=batch_size, shuffle=True)
logger = ImageLogger(batch_frequency=logger_freq)
trainer = pl.Trainer(gpus=1, precision=32, callbacks=[logger])
trainer.fit(model, dataloader)
```

For modern Lightning versions, `gpus=1` may need to become `accelerator="gpu", devices=1`. Keep the model and data contracts unchanged when updating trainer syntax.

## Training Knobs

| Knob | Start value | When to change |
| --- | --- | --- |
| `batch_size` | `4` in tutorial, `1` for constrained GPUs | Lower for OOM; increase or use accumulation for better effective batch. |
| `logger_freq` | `300` | Increase if logging slows training or fills disk; decrease for early qualitative monitoring. |
| `learning_rate` | `1e-5` | Lower, for example `2e-6`, when unlocking SD layers with `sd_locked=False`. |
| `sd_locked` | `True` | Keep true for most datasets; false trains more SD layers and can degrade base-model ability on weak datasets. |
| `only_mid_control` | `False` | Try true for limited compute or global/context-heavy control, but validate quality. |
| `accumulate_grad_batches` | unset | Add when batch size must stay small but a larger effective batch is desired. |
| `num_workers` | `0` in tutorial | Increase only after dataset paths and image decoding are stable. |
| `precision` | `32` in tutorial | Mixed precision may save memory but should be validated for the installed stack. |

The tutorial notes that ControlNet often shows a sudden useful convergence around a few thousand steps on Fill50K-like tasks, and that larger effective batch sizes can be more useful than simply running many extra steps after first convergence. Treat that as a planning heuristic, not a guaranteed stopping rule.

## Low Memory Strategy

For 8GB-class GPUs or OOM-prone runs:

1. Validate the dataset first so memory debugging is not confused with bad rows.
2. Set `batch_size=1`.
3. Add `accumulate_grad_batches`, such as `4`, to recover a larger effective batch at slower wall-clock speed.
4. Consider the repository's low-VRAM mode (`save_memory=True` in the runtime config) only as an experimental option.
5. Consider `only_mid_control=True` for lower compute or a narrower control path, then compare qualitative outputs.
6. Avoid `sd_locked=False` until a stable baseline exists; unlocking SD can increase memory use and can damage base-model behavior on insufficient data.

Use [gradio-inference-apps](../../gradio-inference-apps/SKILL.md) only after a checkpoint exists and the task is qualitative inference testing rather than training setup.

## Custom Dataset Adaptation

When replacing Fill50K with a custom dataset:

- Keep the returned model-facing keys `jpg`, `txt`, and `hint` unless the YAML config is intentionally changed.
- Make source/control maps with the detector/preprocessing skill when controls come from Canny, HED, depth, pose, segmentation, normals, or scribbles: [annotators-and-preprocessing](../../annotators-and-preprocessing/SKILL.md).
- Store source and target paths relative to the dataset root so training can move between machines.
- Keep source and target dimensions aligned or apply deterministic paired transforms.
- Normalize source/control maps to `[0, 1]` and targets to `[-1, 1]` after converting to RGB.
- Smoke-test several edge rows before starting a trainer.
