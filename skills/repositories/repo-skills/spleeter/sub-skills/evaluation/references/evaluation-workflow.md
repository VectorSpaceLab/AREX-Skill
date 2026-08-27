# Evaluation workflow

This workflow evaluates a Spleeter model against a MUSDB-style `test` split. Evaluation first runs normal Spleeter separation on each `mixture.wav`, then asks `musdb`/`museval` to compare the separated estimates with ground-truth source files.

For generic separation usage, route to [separation](../../separation/SKILL.md). For installation constraints, Python/TensorFlow versions, ffmpeg/ffprobe, and optional extras, see the root [installation/runtime reference](../../../references/installation-and-runtime.md). For model descriptors and cache behavior, see the root [models/configuration reference](../../../references/models-and-configuration.md).

## Dependency gate

Before running evaluation, verify all of the following:

| Requirement | Why it matters | Check |
| --- | --- | --- |
| `spleeter==2.4.2` import/CLI works | `evaluate` is a Spleeter CLI command | `python -m spleeter --version` |
| System `ffmpeg` and `ffprobe` are available | Default audio adapter uses ffmpeg subprocesses | `ffmpeg -version` and `ffprobe -version` |
| Evaluation extra is installed | `evaluate` imports `musdb` and `museval` inside the command | `python -c "import musdb, museval"` |
| TensorFlow runtime can import | Separation runs before metrics | Root install check or a small separation smoke |
| Model/cache/network policy is acceptable | Pretrained descriptors such as `spleeter:4stems` may download model assets on first use | Prewarm cache or allow network |

Install the optional evaluation dependencies with either:

```bash
pip install 'spleeter[evaluation]'
```

or install compatible `musdb` and `museval` packages into the same environment. If the extras are missing, `spleeter.__main__.py` logs `Extra dependencies musdb and museval not found`, asks to install them, and exits with status `10`.

## Run evaluation

Use an explicit output directory so audio estimates and metric JSON files are easy to inspect:

```bash
spleeter evaluate \
  --mus_dir MUSDB_ROOT \
  --output_path OUTPUT \
  --params_filename spleeter:4stems \
  --adapter spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter \
  --verbose
```

`python -m spleeter evaluate ...` is equivalent when the console entry point is unavailable. Equivalent short flags for the main path are:

```bash
spleeter evaluate -o OUTPUT -p spleeter:4stems -a spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter --mus_dir MUSDB_ROOT
```

Add `--mwf` only when multichannel Wiener filtering is desired. MWF can improve estimates for some inputs but increases processing cost.

### Parameter choices

| Option | Meaning |
| --- | --- |
| `--mus_dir MUSDB_ROOT` | Directory containing a MUSDB-style `test/<song>/` split. Required by Typer and must be a readable directory. |
| `--output_path`, `-o` | Evaluation output root. Spleeter estimates go below `audio/test`; metric JSON files go below `metrics/test`. |
| `--params_filename`, `-p` | Spleeter model descriptor or config path. Presets such as `spleeter:4stems` may require a first-run model download/cache. |
| `--adapter`, `-a` | Dotted audio adapter class. Default is `spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter`. |
| `--mwf` | Enables multichannel Wiener filtering during the separation phase. |
| `--verbose` | Enables verbose Spleeter logging. |

## Output tree

Given `--output_path eval_out`, Spleeter evaluation uses this structure:

```text
eval_out/
  audio/
    test/
      song0/
        vocals.wav
        drums.wav
        bass.wav
        other.wav
      song1/
        ...
  metrics/
    test/
      song0.json
      song1.json
```

The `audio/test/<song>/` files are Spleeter estimates produced from each input `mixture.wav`. The `metrics/test/*.json` files are `museval` results comparing those estimates to ground truth in `MUSDB_ROOT/test/<song>/`.

## Model download and cache notes

Evaluation calls the same separation path used by `spleeter separate`. Therefore:

- A pretrained descriptor such as `spleeter:2stems`, `spleeter:4stems`, or `spleeter:5stems` may download and cache model files the first time it is used.
- Network failures, blocked downloads, checksum errors, or unwritable cache locations can fail evaluation before any metrics are produced.
- If network access is restricted, prewarm or provide the model cache before evaluation, or use a local config/checkpoint that does not require downloading.
- Use the root [models/configuration reference](../../../references/models-and-configuration.md) for descriptor and cache controls.

## Runtime expectations

Evaluation is more expensive than a separation smoke test because it separates every test mixture and then computes frame-level source-separation metrics. Even tiny fake fixtures may spend time loading TensorFlow and pretrained weights. Full MUSDB test evaluation can be long and should be treated as an explicit user-approved benchmark run.

GPU support is optional acceleration only. The verified path for this skill is TensorFlow CPU; do not promise GPU availability unless the target environment separately verifies TensorFlow GPU devices and compatible CUDA libraries.

## Validation checklist

Before declaring an evaluation setup ready, check:

1. `python -m spleeter --version` reports Spleeter 2.4.2 or the intended compatible version.
2. `python -c "import musdb, museval"` succeeds, or the user has agreed to install the evaluation extra.
3. `MUSDB_ROOT/test/` contains at least one song directory.
4. Every song directory contains `mixture.wav` and ground-truth `vocals.wav`, `drums.wav`, `bass.wav`, and `other.wav` files.
5. The chosen `--params_filename` matches the expected number of sources. For 4-stem MUSDB metrics, use a 4-stem model/config such as `spleeter:4stems`.
6. First-run model downloads/cache writes are allowed or prewarmed.
7. After the run, `OUTPUT/audio/test/<song>/` contains estimates and `OUTPUT/metrics/test/*.json` contains metric files.
8. Compiled metrics include instruments `vocals`, `drums`, `bass`, `other` and metrics `SDR`, `SAR`, `SIR`, `ISR`.

Evidence basis: `spleeter/__main__.py::evaluate`, `spleeter/options.py`, `tests/test_eval.py`, `pyproject.toml`, and `README.md`.
