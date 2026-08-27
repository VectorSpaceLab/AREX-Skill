# Data and Artifact Layout

## When to read

Read this before training, resuming, generating, or writing a smoke test. The
package has simple conventions, but many failures come from empty image folders,
changed project names, or mismatched checkpoint directories.

## Training image folder

The training dataset recursively scans the directory supplied by `--data` for:

- `.jpg`
- `.jpeg`
- `.png`

The scan is recursive, so nested folders are acceptable. At least one matching
image must exist or the trainer raises:

```text
No images were found in <folder> for training
```

The trainer resizes and crops images to `--image_size`. The image size must be a
power of two; invalid values raise an assertion similar to:

```text
image size must be a power of 2 (64, 128, 256, 512, 1024)
```

Transparent mode (`--transparent`) expects/produces RGBA-style data. Without it,
images are converted to RGB.

## Output directories

By default, all paths are relative to the current working directory where the
command is invoked:

```text
results/<name>/             # generated sample grids, GIFs, FID score file
models/<name>/              # checkpoints and .config.json
fid/<name>/real|fake         # temporary FID image cache when FID is enabled
```

The `--results_dir` and `--models_dir` flags change the base directories, while
`--name` selects the project subdirectory.

## Checkpoint files

Checkpoints are saved as:

```text
models/<name>/model_<n>.pt
models/<name>/.config.json
```

`n` is the checkpoint number, computed from the current training step and
`--save_every`. Loading with `--load_from -1` chooses the latest numbered
checkpoint if one exists.

The config file stores architecture-sensitive settings such as `image_size`,
`network_capacity`, `transparent`, feature-quantization layers, attention
layers, and `no_const`. When loading a checkpoint, the trainer reads the config
before initializing the model. If a user changed these settings and wants a new
architecture, use `--new` rather than silently resuming.

## Generation artifacts

Still-sample generation writes timestamped image grids under `results/<name>/`.
The file extension is `.jpg` for ordinary RGB models and `.png` for transparent
models.

Interpolation writes:

```text
results/<name>/<num>.gif
```

If `--save_frames` is set, it also writes individual frame files under:

```text
results/<name>/<num>/
```

## FID artifacts

When `--calculate_fid_every` is enabled, real and generated images are cached
under `fid/<name>/real` and `fid/<name>/fake`, then scores are appended to:

```text
results/<name>/fid_scores.txt
```

Use `--clear_fid_cache` to rebuild the real-image cache when the underlying
training data changes.

## Self-contained fixture guidance

Do not depend on the original repository's sample images when writing reusable
runtime instructions. If a user only needs a tiny smoke folder, generate one
with this skill's bundled helper:

```bash
python sub-skills/training/scripts/make_tiny_fixture.py --output-dir /tmp/sg2-fixture --count 8 --size 64
```

The fixture is for smoke testing command wiring and CUDA availability, not for
assessing GAN quality.
