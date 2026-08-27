# DeepFilterNet training data formats

DeepFilterNet training uses a JSON dataset configuration that points at HDF5 files in a data directory. The training dataloader combines speech and noise datasets, optionally reverberates with RIR datasets, and synthesizes noisy mixtures during training.

## HDF5 dataset layout

A DeepFilterNet training HDF5 file is expected to contain one top-level dataset-type group plus file-level attributes.

### Recognized groups

| Group | Use in training | Notes |
|---|---|---|
| `speech` | Clean speech source samples. Required for every train/valid/test split. | The dataloader samples clean speech and may apply speech augmentations/distortions. |
| `noise` | Noise source samples. Required for every train/valid/test split. | Multiple noise clips may be mixed with each speech clip. |
| `rir` | Room impulse responses. Optional. | Used only when reverb augmentation is enabled. Training warns if reverb is enabled but no RIR datasets are available. |
| `noisy` | Accepted by the HDF5 creation helper as a stored group type. | The standard training dataloader recognizes `speech`, `noise`, and `rir`; do not rely on `noisy` for normal training unless a custom consumer is verified. |

The common pattern is one logical dataset type per file, for example `TRAIN_SPEECH.hdf5` with group `speech`, `TRAIN_NOISE.hdf5` with group `noise`, and optionally `TRAIN_RIR.hdf5` with group `rir`.

### File-level attributes

HDF5 files produced by the DeepFilterNet prepare-data workflow store attributes like:

| Attribute | Meaning | Expected values / behavior |
|---|---|---|
| `db_id` | Creation timestamp-like integer id. | Informational. |
| `db_name` | HDF5 basename. | Informational. |
| `sr` | Sampling rate stored in or expected for samples. | Default preparation target is `48000`. If missing, the Rust dataloader can use an optional fallback sampling rate from advanced dataset config rows, but keeping the attr is safer. |
| `max_freq` | Maximum meaningful frequency. | Defaults to `sr // 2`; used to avoid loss computation above useful bandwidth. |
| `dtype` | PCM dtype metadata. | `int16` or `float32`; the prepare-data CLI defaults to `int16`. |
| `codec` | Storage encoding. | `pcm`, `flac`, or `vorbis`. Missing codec is treated like PCM by readers that provide a default. |

### Sample datasets and attributes

Inside the type group, each member is one audio sample. The prepare-data helper derives keys from manifest-relative file names by replacing `/` with `_`.

- PCM samples are arrays of shape `[channels, samples]` or `[samples]`, with audio data stored directly.
- FLAC/Vorbis samples are byte arrays (`uint8`) containing the encoded audio stream; `codec` tells the reader how to decode.
- Each sample should have `n_samples`. Some utility workflows also populate `n_channels`.
- Audio with fewer than roughly 100 ms of samples is suspicious; preparation warns about very short clips.
- Channel count should be at most 16. Use `--mono` during preparation when a single-channel dataset is intended.

## Audio manifest rules for prepare-data

The prepare-data CLI consumes a text file with one audio path per line:

```text
relative/path/to/clip_001.wav
relative/path/to/clip_002.wav
```

Rules that matter in practice:

- Paths are resolved relative to the manifest file's directory. Keep manifests and audio roots stable.
- Do not include blank lines or comments; they are treated as file paths and will fail existence checks.
- Use readable audio files supported by torchaudio/libsndfile in the current environment.
- Non-target sample rates are resampled to the requested `--sr` during preparation.
- Multi-channel files are kept unless `--mono` is passed; shape checks reject unexpected high channel counts.
- Keep training, validation, and test manifests disjoint unless deliberately running a tiny smoke test.

## Prepare-data CLI contract

The DeepFilterNet prepare-data command takes:

```bash
python -m df.scripts.prepare_data [OPTIONS] TYPE AUDIO_FILES HDF5_DB
```

Positional arguments:

| Argument | Meaning |
|---|---|
| `TYPE` | Dataset group to write: `speech`, `noise`, `rir`, or `noisy`. Use `speech`/`noise` and optional `rir` for standard training. |
| `AUDIO_FILES` | Text manifest containing one audio path per line. |
| `HDF5_DB` | Output HDF5 path. `.hdf5` is appended if omitted. |

Important options:

| Option | Default | Notes |
|---|---:|---|
| `--num_workers` | `4` | Multiprocessing file checking and DataLoader worker count during conversion. |
| `--sr` | `48000` | Target sample rate. DeepFilterNet model defaults assume 48 kHz. |
| `--max_freq` | `-1` | If `<=0`, stored as `sr // 2`. Useful for upsampled lower-bandwidth material. |
| `--dtype` | `int16` | `int16` or `float32` for PCM storage. Vorbis forces float-like audio before encoding. |
| `--codec` | `pcm` | `pcm`, `flac`, or `vorbis` are supported by the implementation. Codec support depends on the installed torchaudio backend. |
| `--mono` | off | Averages multi-channel audio to mono before writing. |
| `--compression` | none | HDF5 dataset compression such as `gzip`; separate from FLAC/Vorbis audio encoding. |

Example:

```bash
python -m df.scripts.prepare_data --sr 48000 --dtype int16 --codec pcm \
  speech manifests/train_speech.txt data/TRAIN_SPEECH.hdf5
```

If `python -m df.scripts.prepare_data --help` fails, install the HDF5/audio preparation dependencies before attempting conversion. See [`troubleshooting.md`](troubleshooting.md).

## `dataset.cfg` schema

The training entry point expects a JSON object with exactly the three split keys `train`, `valid`, and `test`. Each split contains a list of HDF5 dataset rows. The portable row form is:

```json
["FILENAME.hdf5", 1.0]
```

- `FILENAME.hdf5` is resolved relative to the data directory passed to training.
- `sampling_factor` is a positive number. It over/under-samples that HDF5 file when dataset length is built. `1.0` means one pass over available keys. Large factors are useful for tiny datasets or oversampling rare noise classes.
- Keep paths relative for reproducibility. Avoid absolute host-specific paths in shared configs.
- The Rust config type has advanced optional fields for fallback sample rate, fallback max frequency, cached key lists, and modified hashes. Prefer two-column rows unless you know a downstream dataloader requires those extras.

Minimal example:

```json
{
  "train": [
    ["TRAIN_SPEECH.hdf5", 1.0],
    ["TRAIN_NOISE.hdf5", 1.0],
    ["TRAIN_RIR.hdf5", 1.0]
  ],
  "valid": [
    ["VALID_SPEECH.hdf5", 1.0],
    ["VALID_NOISE.hdf5", 1.0],
    ["VALID_RIR.hdf5", 1.0]
  ],
  "test": [
    ["TEST_SPEECH.hdf5", 1.0],
    ["TEST_NOISE.hdf5", 1.0],
    ["TEST_RIR.hdf5", 1.0]
  ]
}
```

RIR rows may be omitted if `p_reverb = 0.0` or if reverb augmentation is intentionally disabled. Speech and noise rows are required for standard training.

## Safe HDF5 utility concepts

The original utility workflows include these useful concepts; prefer the bundled validator for non-mutating checks.

| Concept | Safe use |
|---|---|
| List file attrs/groups/keys | Use `scripts/validate_dataset_config.py --check-hdf5` to confirm attrs, recognized groups, sample counts, and split speech/noise coverage. |
| Extract a few samples | Useful for manual audio sanity checks, but it writes WAV files and needs codec support. Ask before creating outputs in user data directories. |
| Fix `n_samples` / `n_channels` attrs | Mutates HDF5 files. Back up datasets first and run only after confirming decoded lengths. |
| Split one TRAIN HDF5 into train/valid/test HDF5s | Mutates/replaces files. Use only on disposable copies and record random split policy. |
| Trim silence or re-encode codec | Creates new HDF5 files and can drop samples. Use only when the user requests dataset cleanup and accepts the changed data distribution. |
| Download/process public challenge data | Network, license, extraction, and large-storage side effects. Treat as reference-only; ask before running any downloader. |
| Copy/stage shared data directories | Large rsync/symlink/delete side effects and host-specific locking. Treat as reference-only; validate configs instead of bundling copy scripts. |

## Validate before training

From this sub-skill directory:

```bash
python scripts/validate_dataset_config.py --config dataset.cfg --data-dir data --require-files --check-hdf5
```

Proceed to training only when the validator reports zero errors. Warnings about optional attrs may be acceptable for known-good legacy datasets, but missing split keys, missing files, no recognized group, or no speech/noise coverage per split should stop the run.
