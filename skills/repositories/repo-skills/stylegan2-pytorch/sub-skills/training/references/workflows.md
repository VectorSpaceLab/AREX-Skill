# CLI Workflows

## When to read

Read this for complete `stylegan2_pytorch` command recipes. Use
`cli-reference.md` for flag defaults and `data-layout.md` for input/output file
layouts.

## New training run

Minimum documented training command:

```bash
stylegan2_pytorch --data /path/to/images
```

A safer explicit command names the project and output locations:

```bash
stylegan2_pytorch \
  --data /path/to/images \
  --name my-project \
  --results_dir /path/to/results \
  --models_dir /path/to/models \
  --image_size 128 \
  --batch_size 5 \
  --gradient_accumulate_every 6 \
  --network_capacity 16
```

Notes:

- Use a power-of-two `--image_size` such as `64`, `128`, `256`, `512`, or
  `1024`.
- The package requires a CUDA-enabled PyTorch environment before the command can
  import.
- Keep `--name`, `--results_dir`, and `--models_dir` stable across runs that
  should share checkpoints.

## Resume versus restart

By default, the trainer loads the latest checkpoint from `models/<name>/` when
one exists.

Resume the latest checkpoint:

```bash
stylegan2_pytorch --data /path/to/images --name my-project
```

Load a specific checkpoint number:

```bash
stylegan2_pytorch --data /path/to/images --name my-project --load_from 12
```

Restart after changing architecture-sensitive settings:

```bash
stylegan2_pytorch \
  --new \
  --data /path/to/images \
  --name my-project \
  --image_size 512 \
  --batch_size 1 \
  --gradient_accumulate_every 16 \
  --network_capacity 10
```

`--new` clears the project model, result, and FID directories through the
trainer's `clear()` method, so confirm the user wants to discard that run's
existing artifacts before using it.

## Memory-sensitive training

If the user runs out of GPU memory:

1. Lower `--batch_size` first.
2. Raise `--gradient_accumulate_every` so the effective batch remains usable.
3. Lower `--network_capacity` only when necessary; it reduces memory but can
   degrade generation quality.
4. Use a smaller `--image_size` for smoke tests before attempting the final
   resolution.

Example low-memory command:

```bash
stylegan2_pytorch \
  --data /path/to/images \
  --image_size 512 \
  --batch_size 1 \
  --gradient_accumulate_every 16 \
  --network_capacity 10
```

## Low-data and differentiable augmentation

For small datasets, enable differentiable augmentation:

```bash
stylegan2_pytorch --data /path/to/images --aug_prob 0.25
```

Default augmentation types are `translation` and `cutout`. To add color:

```bash
stylegan2_pytorch --data /path/to/images --aug_prob 0.25 --aug_types '[translation,cutout,color]'
```

The source augmentation map includes these keys: `brightness`,
`lightbrightness`, `contrast`, `lightcontrast`, `saturation`, `lightsaturation`,
`color`, `lightcolor`, `offset`, `offset_h`, `offset_v`, `translation`, and
`cutout`.

## Attention, quantization, and experimental regularizers

Use these only when the user asks for them or has enough GPU memory:

```bash
# self-attention after layer 1
stylegan2_pytorch --data /path/to/images --attn_layers 1

# self-attention after layers 1 and 2
stylegan2_pytorch --data /path/to/images --attn_layers '[1,2]'

# feature quantization at layers 1 and 2
stylegan2_pytorch --data /path/to/images --fq_layers '[1,2]' --fq_dict_size 512

# top-k generator training
stylegan2_pytorch --data /path/to/images --top_k_training --generator_top_k_frac 0.5 --generator_top_k_gamma 0.99

# other experimental loss/architecture switches
stylegan2_pytorch --data /path/to/images --rel_disc_loss
stylegan2_pytorch --data /path/to/images --dual_contrast_loss
stylegan2_pytorch --data /path/to/images --no_const
```

`--cl_reg` enables contrastive regularization. In this source snapshot it is not
compatible with transparent images and is asserted as unsuitable with multi-GPU
training.

## Transparent images

For transparent image data, pass:

```bash
stylegan2_pytorch --data /path/to/rgba-images --transparent
```

Transparent mode uses RGBA tensors and produces `.png` image outputs. Do not
combine it with `--cl_reg`.

## Generate still samples

After a checkpoint exists, generate samples from the latest checkpoint:

```bash
stylegan2_pytorch --generate --name my-project
```

Generate from a specific checkpoint and truncation value:

```bash
stylegan2_pytorch --generate --name my-project --load_from 12 --trunc_psi 0.5
```

Sample images are written under `results/<name>/` with timestamped names.

## Generate interpolation GIFs

```bash
stylegan2_pytorch \
  --generate_interpolation \
  --name my-project \
  --interpolation_num_steps 100
```

To save individual frames in addition to the GIF:

```bash
stylegan2_pytorch --generate_interpolation --name my-project --save_frames
```

## FID and logging

FID is optional and imports `pytorch_fid` only when `--calculate_fid_every` is
set:

```bash
pip install pytorch-fid
stylegan2_pytorch --data /path/to/images --calculate_fid_every 5000
```

FID scores are appended to `results/<name>/fid_scores.txt`.

Aim logging is enabled with:

```bash
stylegan2_pytorch --data /path/to/images --log
```

The package can create an Aim session from Python, but viewing the UI requires a
separate Aim service setup. Treat Docker or service management as environment
work, not as part of the core training command.

## Multi-GPU training

Use `--multi_gpus` when the host has multiple CUDA devices and the PyTorch/NCCL
stack is compatible:

```bash
CUDA_VISIBLE_DEVICES=0,1 stylegan2_pytorch \
  --data /path/to/images \
  --multi_gpus \
  --batch_size 32 \
  --gradient_accumulate_every 1
```

The code splits the batch across visible devices. Keep `--cl_reg` off for
multi-GPU because the source asserts that contrastive regularization does not
work well with multi-GPU.

## Self-contained smoke workflow

When the user has no safe fixture, create one from the bundled script:

```bash
python sub-skills/training/scripts/make_tiny_fixture.py --output-dir /tmp/sg2-fixture --count 8 --size 64
```

Inspect a one-step smoke command without running it:

```bash
python sub-skills/training/scripts/train_smoke.py --data-dir /tmp/sg2-fixture --work-dir /tmp/sg2-smoke --dry-run
```

Run it only in a CUDA environment when a short GPU smoke is acceptable:

```bash
python sub-skills/training/scripts/train_smoke.py --data-dir /tmp/sg2-fixture --work-dir /tmp/sg2-smoke
```
