# Training config and data reference

## Purpose

Use this reference when choosing one of the HiFi-GAN V1/V2/V3 configs, preparing LJSpeech-style inputs, checking fine-tuning mel arrays, or deciding whether the current Python/CUDA environment can support a training run.

## Config inventory

The repository provides three JSON configs for the public training entry point.

| Field | `config_v1.json` | `config_v2.json` | `config_v3.json` | Training implication |
| --- | --- | --- | --- | --- |
| `resblock` | `"1"` | `"1"` | `"2"` | V1/V2 use `ResBlock1` with three convolution pairs; V3 uses lighter `ResBlock2`. |
| `upsample_rates` | `[8, 8, 2, 2]` | `[8, 8, 2, 2]` | `[8, 8, 4]` | Product is `256` for all configs and should match `hop_size`. |
| `upsample_kernel_sizes` | `[16, 16, 4, 4]` | `[16, 16, 4, 4]` | `[16, 16, 8]` | Must stay aligned with `upsample_rates` length. |
| `upsample_initial_channel` | `512` | `128` | `256` | Main size/speed/memory difference between V1 and V2; V3 changes both width and block type. |
| `resblock_kernel_sizes` | `[3, 7, 11]` | `[3, 7, 11]` | `[3, 5, 7]` | Kernel families inside each upsampling stage. |
| `resblock_dilation_sizes` | `[[1,3,5], [1,3,5], [1,3,5]]` | same as V1 | `[[1,2], [2,6], [3,12]]` | Must match the selected `resblock` implementation. |
| `segment_size` | `8192` | `8192` | `8192` | Training crops/pads audio to this many waveform samples. |
| `num_mels` | `80` | `80` | `80` | Keep at 80 unless changing `Generator.conv_pre` in `models.py`. |
| `n_fft` / `win_size` / `hop_size` | `1024 / 1024 / 256` | same | same | Mel extraction and generator upsampling assume this relationship. |
| `sampling_rate` | `22050` | `22050` | `22050` | All wavs must match or `MelDataset` raises a sample-rate `ValueError`. |
| `fmin` / `fmax` / `fmax_for_loss` | `0 / 8000 / null` | same | same | Training mel target and loss mel settings. |
| `batch_size` | `16` | `16` | `16` | Divided by the visible CUDA device count at runtime. |
| `num_workers` | `4` | `4` | `4` | DataLoader workers; reduce for debug or constrained hosts. |
| `dist_config` | NCCL, `tcp://localhost:54321`, `world_size: 1` | same | same | Single-node DDP defaults; change the port for concurrent jobs. |

Shared optimizer/training defaults: `learning_rate: 0.0002`, `adam_b1: 0.8`, `adam_b2: 0.99`, `lr_decay: 0.999`, and `seed: 1234`.

## Selecting V1, V2, or V3

- Choose **V1** when matching the README's primary LJSpeech training recipe or prioritizing the full-size generator.
- Choose **V2** when you want the documented smaller V1-style generator with the same upsample schedule but lower channel count.
- Choose **V3** when you want the documented compact/small-footprint variant with `ResBlock2` and three upsampling stages.
- For fair comparisons, keep dataset preprocessing and checkpoint directories separate across variants.

## LJSpeech-style layout

Default layout expected by `train.py`:

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

Only the first field is used by training. `get_dataset_filelist()` converts it to `<input_wavs_dir>/<id>.wav`, so the first field must not include `.wav`.

Custom layout example:

```bash
python scripts/train_hifigan.py \
  --config v1 \
  --input_wavs_dir data/my_ljspeech/wavs \
  --input_training_file data/my_ljspeech/training.txt \
  --input_validation_file data/my_ljspeech/validation.txt \
  --checkpoint_path runs/hifigan_v1
```

## Audio requirements

`MelDataset` loads wavs with `scipy.io.wavfile.read`, scales by `MAX_WAV_VALUE = 32768.0`, and checks the file sampling rate against the config.

Checklist:

- WAV paths generated from both filelists must exist.
- WAV sample rate must equal config `sampling_rate` (`22050` for all bundled configs).
- Audio can be shorter than `segment_size`; non-fine-tuning training pads short clips.
- For normal training, audio is normalized with `librosa.util.normalize(audio) * 0.95` before mel extraction.
- For fine-tuning, that normalization is skipped before loading the external mel input.

## Fine-tuning mel `.npy` layout

Default layout:

```text
ft_dataset/
  LJ001-0001.npy
  LJ001-0002.npy
```

For each wav file, the mel filename is derived from the wav basename:

```text
<input_wavs_dir>/LJ001-0001.wav -> <input_mels_dir>/LJ001-0001.npy
```

Accepted array shapes:

- `[80, frames]` — the code unsqueezes this to `[1, 80, frames]`.
- `[1, 80, frames]` — used directly.

Shape and alignment checks:

- Channel count must match the generator input channel count (`80`).
- Frame count should match `ceil_or_floor(audio_samples / hop_size)` as produced by the same mel extraction convention; for config defaults, that is effectively one frame per 256 samples for lengths divisible by 256.
- For training crops in fine-tuning mode, long clips need more than `ceil(segment_size / hop_size)` mel frames.
- If mel names do not match wav basenames, `np.load()` fails with a missing-file error.

## Environment facts and compatibility

Verified inspection facts:

- `torch 2.3.1+cu121` imports on an NVIDIA A100-SXM4-40GB host.
- `torch.cuda.is_available()` is true.
- `torch.cuda.get_device_name(0)` succeeds.
- `torch.utils.tensorboard` imports.
- `librosa.util.normalize` is present in `librosa 0.10.2.post1`.

Source repository requirement pins are older: `torch==1.4.0`, `librosa==0.7.2`, `numpy==1.17.4`, `scipy==1.4.1`, `tensorboard==2.0`, `soundfile==0.10.3.post1`, `matplotlib==3.1.3`.

Modern-stack caveats:

- Newer PyTorch requires `return_complex` for `torch.stft`; unpatched source code may fail during mel computation.
- Newer librosa uses keyword-only `librosa.filters.mel`; source code that calls it positionally may fail.
- The bundled `scripts/train_hifigan.py` and `scripts/smoke_train_tiny.py` apply local compatibility shims for these issues, including a tiny `torch._dynamo` stub to keep AdamW on the eager path, without modifying the copied runtime source. Treat the shims as wiring/runtime support, not proof that a long production run has been made fully modernized.

## Bundled fixture helper

Create a clean tiny dataset:

```bash
python scripts/make_ljspeech_fixture.py \
  --out-dir ./scratch/hifigan_lj_fixture \
  --train-count 2 \
  --val-count 1 \
  --sample-rate 22050
```

Create a fine-tuning fixture with mels:

```bash
python scripts/make_ljspeech_fixture.py \
  --out-dir ./scratch/hifigan_ft_fixture \
  --with-mels \
  --hop-size 64
```

Create negative fixtures for later usability verification:

```bash
python scripts/make_ljspeech_fixture.py \
  --out-dir ./scratch/hifigan_missing_wav_case \
  --include-missing-wav-row

python scripts/make_ljspeech_fixture.py \
  --out-dir ./scratch/hifigan_bad_mel_case \
  --with-mels \
  --include-bad-mel-name
```

These helpers generate synthetic tones and random mel arrays only. They are meant for wiring checks and negative-case validation, not model-quality evaluation.
