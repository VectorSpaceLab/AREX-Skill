# Configuration and layout

## Purpose

Read this when you need the bundled config inventory, the training filelist
layout, the inference input/output layout, or the checkpoint directory
contract.

## Bundled runtime and configs

The skill packages copied HiFi-GAN source under `scripts/hifigan_runtime/`, includes the source `LICENSE`, and stores the V1/V2/V3 JSON files under `scripts/hifigan_runtime/configs/`. Use the wrapper scripts in the training and inference sub-skills instead of relying on an external checkout.

## Bundled configs

| File | Role | Key differences |
| --- | --- | --- |
| `config_v1.json` | Full-size generator | `resblock = "1"`, `upsample_initial_channel = 512`, `upsample_rates = [8, 8, 2, 2]` |
| `config_v2.json` | Smaller V1-style generator | `resblock = "1"`, `upsample_initial_channel = 128`, same upsample schedule as V1 |
| `config_v3.json` | Compact generator | `resblock = "2"`, `upsample_initial_channel = 256`, `upsample_rates = [8, 8, 4]` |

Shared values across the bundled configs:

- `num_mels = 80`
- `sampling_rate = 22050`
- `hop_size = 256`
- `n_fft = 1024`
- `win_size = 1024`
- `fmin = 0`
- `fmax = 8000`

## Training layout

Default layout expected by the repo's training workflow:

```text
LJSpeech-1.1/
  wavs/
    LJ001-0001.wav
    LJ001-0002.wav
  training.txt
  validation.txt
```

Filelist rows are pipe-delimited:

```text
<id-without-extension>|<raw text>|<normalized text>
```

Only the first field matters to the training code. It is converted to
`<input_wavs_dir>/<id>.wav`, so do not include `.wav` in the filelist id.

## Fine-tuning mel layout

Default fine-tuning layout:

```text
ft_dataset/
  LJ001-0001.npy
  LJ001-0002.npy
```

- The mel basename must match the wav basename.
- Accepted shapes are `[80, frames]` or `[1, 80, frames]`.
- The channel count must stay at 80.

## Checkpoint and output layout

`sub-skills/training/scripts/train_hifigan.py` runs bundled training source and writes into the checkpoint directory:

- `config.json` — copy of the selected launch config
- `logs/` — TensorBoard event files
- `g_########` — generator checkpoints
- `do_########` — discriminator/optimizer checkpoints

`sub-skills/inference/scripts/infer_hifigan.py` expects the checkpoint directory to contain `config.json` beside the `g_########` file and writes outputs into the selected output directory:

- wav-to-wav inference writes `<stem>_generated.wav`
- mel-to-wav inference writes `<stem>_generated_e2e.wav`

## Environment note

The source repository requirements are pinned to an older stack, but the bundled runtime wrappers and smoke helpers were verified against a newer CUDA-capable torch/librosa environment.
If the library stack changes, re-read `references/troubleshooting.md` before
assuming the same compatibility behavior.
