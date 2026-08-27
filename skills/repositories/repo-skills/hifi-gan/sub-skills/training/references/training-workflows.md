# HiFi-GAN training and fine-tuning workflows

## Purpose

Use this reference to launch, resume, fine-tune, validate, and debug HiFi-GAN training with the skill's self-contained `scripts/train_hifigan.py` entrypoint. It distills the training behavior from `README.md`, `train.py`, `env.py`, `meldataset.py`, `models.py`, `utils.py`, and bundles the required source/config files under the root `scripts/hifigan_runtime/` directory.

## Standard training launch

The bundled wrapper runs copied HiFi-GAN training source and resolves `--config v1`, `--config v2`, or `--config v3` to the bundled config files. If you omit `--config`, it defaults to V1.

```bash
python scripts/train_hifigan.py --config v1
```

Documented variants:

```bash
python scripts/train_hifigan.py --config v2 --checkpoint_path cp_hifigan_v2
python scripts/train_hifigan.py --config v3 --checkpoint_path cp_hifigan_v3
```

Useful launch options forwarded to the bundled training source:

| Option | Default | Training meaning |
| --- | --- | --- |
| `--config` | bundled V1 in wrapper | JSON hyperparameter/config file; use `v1`, `v2`, `v3`, a bundled config filename, or an explicit custom config path. |
| `--input_wavs_dir` | `LJSpeech-1.1/wavs` | Directory containing `.wav` files whose basenames appear in the first column of the filelists. |
| `--input_training_file` | `LJSpeech-1.1/training.txt` | Training filelist. First pipe-delimited field is converted to `<input_wavs_dir>/<id>.wav`. |
| `--input_validation_file` | `LJSpeech-1.1/validation.txt` | Validation filelist with the same schema as training. Must contain at least one valid wav. |
| `--checkpoint_path` | `cp_hifigan` | Directory for copied `config.json`, TensorBoard logs, and checkpoints. Existing matching checkpoints trigger automatic resume. |
| `--training_epochs` | `3100` | Epoch count for the outer training loop. Use a much smaller value only for smoke/debug runs. |
| `--stdout_interval` | `5` | Step interval for console loss logging and fresh `mel_error` computation. |
| `--checkpoint_interval` | `5000` | Step interval for `g_????????` and `do_????????` checkpoint saves. No checkpoint is written at step 0. |
| `--summary_interval` | `100` | Step interval for TensorBoard scalar logging under `<checkpoint_path>/logs`. |
| `--validation_interval` | `1000` | Step interval for validation; because `steps == 0` satisfies the modulo check, validation also runs on the first training step. |
| `--input_mels_dir` | `ft_dataset` | Fine-tuning mel `.npy` directory used only when `--fine_tuning True` is active. |
| `--fine_tuning` | `False` | Enables mel `.npy` input loading. Because the parser uses `type=bool`, do not pass `--fine_tuning False`; omit the flag for false. |
| `--group_name` | `None` | Parsed but not used by the training code. |

## Dataset/filelist flow

1. Place wavs in a directory such as `LJSpeech-1.1/wavs`.
2. Write `training.txt` and `validation.txt` as pipe-delimited rows. The first field is the audio id **without** `.wav`.
3. Launch with matching `--input_wavs_dir`, `--input_training_file`, and `--input_validation_file`.

Example minimal rows:

```text
LJ001-0001|Raw text is ignored by train.py|Normalized text is ignored by train.py
LJ001-0002|Another utterance|Another utterance
```

`meldataset.get_dataset_filelist()` ignores the text columns and constructs paths by appending `.wav` to the first field. A row whose first field is `LJ001-0001.wav` will look for `LJ001-0001.wav.wav` and fail.

## Config selection workflow

1. Pick the generator family:
   - V1 (`config_v1.json`): full-size generator, `resblock: "1"`, `upsample_initial_channel: 512`; use when quality is prioritized and GPU memory allows it.
   - V2 (`config_v2.json`): same upsample pattern and resblock type as V1, but `upsample_initial_channel: 128`; use as a smaller/faster documented variant.
   - V3 (`config_v3.json`): compact generator, `resblock: "2"`, `upsample_rates: [8, 8, 4]`, `upsample_initial_channel: 256`; use as the small-footprint documented variant.
2. Keep data audio at `sampling_rate: 22050` unless you intentionally create a matching custom config and resample all wavs.
3. Keep `num_mels: 80` for this repository unless you also modify `models.py`; `Generator.conv_pre` is hard-coded for 80 input channels.
4. Keep the product of `upsample_rates` equal to `hop_size` so generated waveform length aligns with training segments and validation mel losses.
5. Adjust `batch_size` for memory, but remember `train.py` divides it by the number of visible CUDA devices.

## Checkpoint and resume behavior

On rank 0, the bundled training source creates `--checkpoint_path`, prints it, and copies the selected config to `<checkpoint_path>/config.json` via `env.build_env()`.

Checkpoint files:

| File pattern | Contents | Notes |
| --- | --- | --- |
| `g_????????` | Generator state dict | Saved when `steps % checkpoint_interval == 0 and steps != 0`. |
| `do_????????` | Multi-period/multi-scale discriminator state dicts, both optimizers, step, epoch | Required with a matching `g_` checkpoint for automatic resume. |
| `config.json` | Copy of the launch config | Used as a run record, not automatically read on resume unless passed again with `--config`. |
| `logs/` | TensorBoard event files | Created by `SummaryWriter(os.path.join(checkpoint_path, "logs"))`. |

Resume is automatic when both latest `g_????????` and `do_????????` exist in the checkpoint directory. To start a fresh run, use an empty/new `--checkpoint_path` or move old checkpoint files aside. If only one side exists, the code starts from scratch while leaving the files in place, which can mislead later inspection.

## Validation and TensorBoard behavior

- Validation is rank-0 only and uses `MelDataset(..., split=False, batch_size=1, drop_last=True)`.
- Validation runs at step 0 and every `--validation_interval` steps after that.
- For the first five validation batches, TensorBoard receives ground-truth audio/spectrograms at step 0 and generated audio/spectrograms at every validation event.
- Scalars include `training/gen_loss_total`, `training/mel_spec_error`, and `validation/mel_spec_error`.
- Use a non-empty validation filelist; an empty loader leaves the validation loop index undefined.

Typical log inspection:

```bash
tensorboard --logdir cp_hifigan/logs
```

## Fine-tuning workflow with mel `.npy` inputs

Fine-tuning consumes both wavs and precomputed mel arrays:

1. Generate teacher-forced mel-spectrograms externally, usually from a text-to-mel model.
2. Name each mel file exactly after the wav basename, changing only the extension:

   ```text
   wav: LJ001-0001.wav
   mel: LJ001-0001.npy
   ```

3. Place mel files in `ft_dataset` or pass a custom `--input_mels_dir`.
4. Launch with a truthy flag:

   ```bash
   python scripts/train_hifigan.py --fine_tuning True --config v1 --input_mels_dir ft_dataset
   ```

Fine-tuning data facts from `meldataset.py`:

- For a wav path `<input_wavs_dir>/<id>.wav`, the mel loader opens `<input_mels_dir>/<id>.npy`.
- A mel array may be shaped `[80, frames]` or `[1, 80, frames]`; 2-D arrays are unsqueezed.
- For training crops, `frames_per_seg = ceil(segment_size / hop_size)`. Long audio needs a mel with more than `frames_per_seg` frames because the code samples a random start with an exclusive upper margin.
- The mel frame rate, sample rate, `num_mels`, `hop_size`, `fmin`, and `fmax` must match the selected config and wav preprocessing.

## Distributed GPU training notes

The bundled training source is CUDA-oriented and has no CPU training branch: `train()` always constructs `torch.device('cuda:<rank>')`.

Single-GPU run:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/train_hifigan.py --config v1 --checkpoint_path cp_hifigan_v1_gpu0
```

Single-node multi-GPU run:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 python scripts/train_hifigan.py --config v1 --checkpoint_path cp_hifigan_v1_4gpu
```

Important details:

- When CUDA is available, `main()` overwrites `h.num_gpus` with `torch.cuda.device_count()`; the `num_gpus` value inside the JSON configs is not the source of truth.
- The global config `batch_size` is divided by the visible GPU count using integer division. Ensure the result is at least 1 and fits memory.
- Multi-GPU uses `mp.spawn()` and `DistributedDataParallel` with `dist_backend` and `dist_url` from the JSON config. Use a free `dist_url` port if several jobs run on the same host.
- Rank 0 writes checkpoints and TensorBoard logs; other ranks train but do not write these artifacts.
- As written, the rank calculation is local-rank only; treat the code as single-node DDP unless you intentionally patch it for multi-node rank offsets.

## Bundled smoke workflow

The sub-skill bundles a deterministic tiny fixture generator and a smoke launcher:

```bash
python scripts/make_ljspeech_fixture.py --out-dir ./scratch/hifigan_fixture --with-mels
python scripts/smoke_train_tiny.py --dry-run
python scripts/smoke_train_tiny.py
python scripts/smoke_train_tiny.py --fine-tuning
```

The smoke launcher writes a deliberately tiny config for a functional GPU pass; it is not a quality training recipe. Use it to validate wiring, CUDA, TensorBoard import, filelist/mel naming, checkpoint writes, and modern PyTorch/librosa/torch.compile shims before investing in full training.
