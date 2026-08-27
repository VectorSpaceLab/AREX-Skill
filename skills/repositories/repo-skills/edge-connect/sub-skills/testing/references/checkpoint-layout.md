# Checkpoint layout

## Directory contract

A checkpoint directory is both the config home and the weight-file home for an EdgeConnect run.

Typical layout:

```text
<checkpoint-dir>/
  config.yml
  EdgeModel_gen.pth
  EdgeModel_dis.pth
  InpaintingModel_gen.pth
  InpaintingModel_dis.pth
  results/              # default test output when --output is omitted
  samples/              # training-time previews, if produced
  log_edge.dat          # training logs, if produced
  log_inpaint.dat
  log_edge_inpaint.dat
  log_joint.dat
```

Only `config.yml` and the selected stage's generator files are required for inference. Discriminator files are not loaded in `MODE=2`, but they are expected in a complete training/resume checkpoint set.

## Config file behavior

`config.yml` must live directly inside the checkpoint directory selected by `--checkpoints` or `--path`.

At test startup:

- The loader reads `<checkpoint-dir>/config.yml`.
- The runtime `PATH` value is derived from the directory containing that config.
- If `config.yml` is missing, the loader tries to copy `config.yml.example` from the launch working directory. This fallback can silently create a generic config in the wrong place; prefer creating the intended config before running.
- `main.load_config(mode=2)` then forces `MODE=2`, `INPUT_SIZE=0`, and CLI test path overrides.

Minimum test-relevant keys to review:

| Key | Why it matters in test mode |
| --- | --- |
| `MODEL` | Default stage if `--model` is omitted; CLI `--model` overrides it |
| `GPU` | Used to set visible CUDA devices before Torch chooses CUDA or CPU |
| `EDGE` | `1` computes Canny edges; `2` requires external edge input |
| `NMS` | Applies non-max suppression only for external edges |
| `SIGMA` | Canny blur control when `EDGE=1` |
| `DEBUG` | Enables `*_edge` and `*_masked` side outputs |
| `RESULTS` | Output directory if `--output` is omitted |
| `TEST_FLIST` | Test images when `--input` is omitted |
| `TEST_MASK_FLIST` | Test masks when `--mask` is omitted |
| `TEST_EDGE_FLIST` | Test edge maps when `EDGE=2` and `--edge` is omitted |

Flist construction and broader config path validation belong to the `data-preparation` sub-skill.

## Stage-to-file matrix

| Stage | Test-time name | Generator files required for inference | Discriminator files expected in a full checkpoint | Notes |
| --- | --- | --- | --- | --- |
| `--model 1` | edge | `EdgeModel_gen.pth` | `EdgeModel_dis.pth` | Produces an edge output. Missing generator means an untrained edge generator may be used. |
| `--model 2` | inpaint | `InpaintingModel_gen.pth` | `InpaintingModel_dis.pth` | Uses Canny or external edges as guidance. Missing generator means an untrained inpainting generator may be used. |
| `--model 3` | edge-inpaint | `EdgeModel_gen.pth`, `InpaintingModel_gen.pth` | `EdgeModel_dis.pth`, `InpaintingModel_dis.pth` | Predicts edges first, then inpaints. Requires both generator families. |
| `--model 4` | joint | `EdgeModel_gen.pth`, `InpaintingModel_gen.pth` | `EdgeModel_dis.pth`, `InpaintingModel_dis.pth` | Inference code is the same as stage `3`; the distinction is checkpoint training history. |

Checkpoint filenames are case-sensitive and must match exactly.

## Validate without network access

Use the bundled checker before running inference:

```bash
python scripts/check_checkpoints.py --checkpoints checkpoints/places2 --model 3
```

For strict full-checkpoint validation, also require discriminator files:

```bash
python scripts/check_checkpoints.py --checkpoints checkpoints/places2 --model 3 --require-discriminators
```

The checker does not download anything, does not import Torch, and does not inspect checkpoint tensor contents. It verifies the directory, `config.yml`, and the stage-specific filename layout so agents can catch the most common "random-looking output" failure before launch.

## Pretrained checkpoint limitations

The skill tree does not bundle pretrained weights.

The upstream project published pretrained archives through external hosting and also had a network download helper. Do not rely on that helper during skill-guided inference preparation. Instead:

1. Obtain checkpoints through a user-approved, reproducible channel outside the test command.
2. Unpack them into a checkpoint directory whose leaf contains `config.yml` and the expected weight files.
3. Run `scripts/check_checkpoints.py` for the intended stage.
4. Record which dataset/domain the weights were trained for when reporting results.

Common unpacking issue: archives may create nested dataset directories. Choose the leaf directory that directly contains `config.yml`, `EdgeModel_gen.pth`, and/or `InpaintingModel_gen.pth`; do not point `--checkpoints` at a parent directory that only contains subfolders.

## Generator vs discriminator expectations

`BaseModel.load()` checks for a generator file and loads it if present. If the generator file is absent, the model remains initialized with fresh random weights and the test run can continue with unusable output. That is why generator files are treated as required by this sub-skill.

Discriminator files are loaded only during training mode. They are useful for resuming training and for preserving a complete checkpoint bundle, but they are not required for pure `test.py` inference.

## CPU/GPU checkpoint loading

When CUDA is available, checkpoint files are loaded normally. When CUDA is unavailable, generator weights are loaded with a CPU map location. This means CPU inference can be used for small checks, but it can be slow. If a GPU run is required, verify the CUDA-capable runtime before starting a large directory inference job.
