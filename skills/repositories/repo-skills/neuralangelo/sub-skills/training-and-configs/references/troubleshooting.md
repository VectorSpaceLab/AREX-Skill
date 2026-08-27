# Training troubleshooting

Use this reference for failures after data has already been prepared. If the
root issue is COLMAP, video frame extraction, JSON conversion, pose quality, or
bounding-sphere adjustment, route to `data-preparation`. If the root issue is
mesh extraction, route to `mesh-extraction`.

## CUDA out of memory during training

Symptoms:

- `RuntimeError: CUDA out of memory`
- OOM soon after model construction or first train iteration
- OOM only on rank 0 when W&B image logging or validation begins

First checks:

```bash
python <skill-dir>/scripts/inspect_config_summary.py \
  --config <config.yaml> \
  --project-root . \
  --check-data
```

Then try the least invasive reductions:

```bash
--model.object.sdf.encoding.hashgrid.dict_size=21
--model.object.sdf.encoding.hashgrid.dim=4
--model.render.rand_rays=256
--data.train.batch_size=1
```

Approximate hash-grid reductions:

| GPU VRAM | Overrides |
| --- | --- |
| 8 GB | `--model.object.sdf.encoding.hashgrid.dict_size=20 --model.object.sdf.encoding.hashgrid.dim=4` |
| 12 GB | `--model.object.sdf.encoding.hashgrid.dict_size=21 --model.object.sdf.encoding.hashgrid.dim=4` |
| 16 GB | `--model.object.sdf.encoding.hashgrid.dict_size=21 --model.object.sdf.encoding.hashgrid.dim=8` |

If OOM persists, reduce per-ray work:

```bash
--model.render.num_samples.coarse=48
--model.render.num_samples.fine=8
--model.render.num_sample_hierarchy=3
--model.render.num_samples.background=16
```

Quality may drop as hash-grid capacity, sample counts, or ray counts are
reduced. Make only one category of change at a time and preserve the final
merged `config.yaml` with the run.

## CUDA out of memory during validation only

Validation renders full images and logs visualization maps. Keep training knobs
unchanged and reduce validation first:

```bash
--data.val.image_size=[200,300]
--data.val.batch_size=1
--data.val.subset=1
--data.val.max_viz_samples=4
--validation_iter=10000
--wandb_image_iter=20000
```

If the image is portrait, keep `[height, width]` ordering. Use the bundled
config inspector to confirm the final dimensions.

## `tinycudann` import or CUDA extension failure

Symptoms:

- `ModuleNotFoundError: No module named 'tinycudann'`
- CUDA architecture or compiler errors during import/build
- Hash-grid model construction fails before data loading

Checks:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__)
print('torch_cuda', torch.version.cuda)
print('cuda_available', torch.cuda.is_available())
print('device_count', torch.cuda.device_count())
PY

python - <<'PY'
import tinycudann
print('tinycudann import ok')
PY
```

Resolution:

- Use a CUDA-capable environment with compatible PyTorch and tiny-cuda-nn.
- Do not treat a CPU-only PyTorch import as proof that Neuralangelo hash-grid
  training can run.
- If the user intentionally wants a CPU-only inspection, limit it to config and
  script planning; do not promise training.

## Unknown command-line override key

Symptom:

```text
KeyError: The input key '<path>'; does not exist in the config files.
```

Cause: `recursive_update_strict` rejects command-line override paths that are
not present after parent inheritance.

Fix:

```bash
python <skill-dir>/scripts/inspect_config_summary.py \
  --config <config.yaml> \
  --project-root . \
  --override optim.params.lr=5e-4 \
  --override model.render.rand_rays=256
```

If an experimental key is truly new, add it to the YAML first. Do not rely on a
command-line override to create a new branch.

## YAML parent does not resolve

Symptoms:

- `File <parent> not exist.`
- Config inspector reports an unresolved `_parent_`

Fix:

- Run commands from the Neuralangelo project root when config parents use paths
  such as `projects/neuralangelo/configs/base.yaml`.
- If a config was moved outside the project, either pass `--project-root` to the
  inspector or edit `_parent_` so it is resolvable from the launch directory.

## Dataset JSON or image path error

Symptoms:

- `FileNotFoundError` for `<data.root>/transforms.json`
- `FileNotFoundError` for an image under `data.root`
- Empty dataset or unexpected image count

Training-side checks:

```bash
python <skill-dir>/scripts/inspect_config_summary.py \
  --config <config.yaml> \
  --project-root . \
  --check-data
```

Fixes within this sub-skill:

- Correct `data.root`.
- Correct `data.train.image_size` and `data.val.image_size` ordering.
- Set `data.num_images` when appearance embeddings are enabled.
- Set `data.train.subset` or `data.val.subset` only for debugging or intended
  subset training.

If `transforms.json` is missing or camera poses/bounds are wrong, route to
`data-preparation`.

## Appearance embedding assertion

Symptom:

```text
assert cfg_data.num_images is not None
```

Cause: `model.appear_embed.enabled: true` but `data.num_images` is null.

Fix:

```bash
--data.num_images=<number-of-training-images>
```

Use the full training image count. Do not set it to `data.val.subset`.

## DDP, NCCL, or rank issues

Symptoms:

- Process hangs before or after `Training with <N> GPUs.`
- NCCL connection errors
- One process reports a different visible device set

Checks:

```bash
python - <<'PY'
import torch
print(torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    print(i, torch.cuda.get_device_name(i))
PY
```

Fixes:

- Match `CUDA_VISIBLE_DEVICES` count to `torchrun --nproc_per_node`.
- For a one-GPU debug run, use either the normal single-process torchrun style:
  `torchrun --nproc_per_node=1 train.py ...`, or true non-DDP:
  `python train.py --single_gpu ...`.
- Avoid manually setting `--local_rank` under `torchrun`; it is supplied by the
  launcher.

## W&B authentication or unwanted online logging

Symptoms:

- W&B login prompt on a non-interactive run
- Run should be offline or disabled
- W&B group/name are unexpected

Behavior:

- `--wandb` enables online W&B unless `--debug` is also set.
- Without `--wandb`, W&B mode is disabled.
- `--wandb_name` sets the project name.
- The final two `--logdir` path components become group and run name.
- `wandb_id.txt` in the logdir is reused during resume.

Fixes:

```bash
# Disable online W&B for smoke/debug.
torchrun --nproc_per_node=1 train.py ... --debug

# Enable online W&B intentionally.
torchrun --nproc_per_node=1 train.py ... --wandb --wandb_name <project>
```

## Resume did not continue from the expected iteration

Symptoms:

- Training starts from iteration 0 despite `--resume`
- Scheduler state appears reset
- A different checkpoint loads than expected

Checklist:

- Use the original logdir when relying on `latest_checkpoint.txt`.
- Use the saved merged config: `--config=logs/<group>/<name>/config.yaml`.
- Pass `--checkpoint=<checkpoint.pt>` with `--resume` when the logdir pointer is
  absent or ambiguous.
- Do not change model dimensions, hash-grid settings, appearance embedding
  settings, optimizer type, or scheduler shape for strict resume.

## NaN or infinite training loss

The NeRF base trainer raises if total loss is NaN or Inf at scalar logging time.

Likely causes:

- Bad camera normalization or bounding sphere.
- Too aggressive learning rate or schedule changes.
- Extreme `readjust.scale` or `readjust.center`.
- Unstable AMP setting.

First response:

```bash
--optim.params.lr=5e-4
--trainer.amp_config.enabled=false
--wandb_scalar_iter=10
--validation_iter=100
```

If geometry bounds or poses are suspect, route to `data-preparation`.

## Slow training or stalls

Checks:

- Use `--show_pbar` for visible progress.
- Temporarily set `logging_iter` lower.
- Use `--profile` for a short run to produce `trace.json` under the logdir.
- Lower `data.num_workers` if host workers are unstable.
- Disable excessive validation or image logging during throughput debugging.

Example:

```bash
torchrun --nproc_per_node=1 train.py \
  --logdir=logs/profile/<scene> \
  --config=<config.yaml> \
  --show_pbar \
  --profile \
  --max_iter=20 \
  --validation_iter=20 \
  --wandb_image_iter=999999999
```

## Poor reconstruction after successful training

Training-side checks:

- Confirm the saved `config.yaml` used the intended `data.root`.
- Confirm `data.readjust.center` and `data.readjust.scale` are not defaults when
  the scene needed manual bounding-sphere adjustment.
- For appearance-varying video, consider enabling appearance embeddings and
  setting `data.num_images`.
- For indoor room-like scenes, check `inside_out`, background disabling, and
  background sample count.

If camera poses, COLMAP tracks, blur, focus, or the bounding region are suspect,
route to `data-preparation`. If the trained checkpoint is good but extracted
mesh quality is poor, route to `mesh-extraction`.
