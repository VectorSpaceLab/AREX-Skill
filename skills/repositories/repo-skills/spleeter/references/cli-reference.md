# CLI reference

Spleeter 2.4.2 exposes a Typer CLI through both the `spleeter` console command and `python -m spleeter`. Prefer `python -m spleeter` in portable instructions because it also avoids known shortcut issues on some Windows installs.

## Root command

```bash
python -m spleeter --version
python -m spleeter --help
```

Root options:

| Option | Meaning |
| --- | --- |
| `--version` | Print `Spleeter Version: <version>` and exit. |
| `--help` | Show command help. |

Root commands:

| Command | Workflow owner |
| --- | --- |
| `separate` | [separation](../sub-skills/separation/SKILL.md) |
| `train` | [training](../sub-skills/training/SKILL.md) |
| `evaluate` | [evaluation](../sub-skills/evaluation/SKILL.md) |

## `separate`

Shape:

```bash
python -m spleeter separate [OPTIONS] FILES...
```

`FILES...` are required positional audio file paths. Do not use deprecated `-i`/`--inputs`; in this version it is only a placeholder that logs an error and exits with code `20`.

| Option | Default | Meaning |
| --- | --- | --- |
| `-a`, `--adapter TEXT` | `spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter` | Dotted `AudioAdapter` class for audio I/O. |
| `-b`, `--bitrate TEXT` | `128k` | Output audio bitrate. |
| `-c`, `--codec [wav|mp3|ogg|m4a|wma|flac]` | `wav` | Output audio codec. |
| `-d`, `--duration FLOAT` | `600.0` | Maximum seconds to process after offset. |
| `-s`, `--offset FLOAT` | `0.0` | Start offset in seconds. |
| `-o`, `--output_path TEXT` | a temp `separated_audio` directory | Output directory root. |
| `-f`, `--filename_format TEXT` | `{filename}/{instrument}.{codec}` | Python-format template using `{filename}`, `{foldername}`, `{instrument}`, `{codec}`. |
| `-p`, `--params_filename TEXT` | `spleeter:2stems` | Embedded descriptor or local JSON config path. |
| `--mwf` | false | Enable multichannel Wiener filtering. |
| `--verbose` | false | Enable verbose logs. |
| `--help` | n/a | Show help for the command. |

Examples:

```bash
python -m spleeter separate -p spleeter:2stems -o separated song.wav
python -m spleeter separate -p spleeter:4stems -o separated --duration 30 song.wav
python -m spleeter separate -p spleeter:2stems -o flat -f '{filename}_{instrument}.{codec}' song_a.wav song_b.wav
```

For workflow details, read [separation workflows](../sub-skills/separation/references/workflows.md).

## `train`

Shape:

```bash
python -m spleeter train [OPTIONS]
```

| Option | Default | Meaning |
| --- | --- | --- |
| `-a`, `--adapter TEXT` | `spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter` | Audio adapter class for loading CSV-referenced training audio. |
| `-d`, `--data TEXT` | required | Directory containing audio files referenced by CSV row paths. |
| `-p`, `--params_filename TEXT` | `spleeter:2stems` | JSON config descriptor/path. For custom training, use a real filesystem JSON config, not placeholder pretrained descriptors. |
| `--verbose` | false | Enable verbose logs. |
| `--help` | n/a | Show help. |

Example:

```bash
python -m spleeter train \
  --data DATA_ROOT \
  --params_filename CONFIG.json \
  --adapter spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter \
  --verbose
```

Validate configs and CSVs first with [training](../sub-skills/training/SKILL.md).

## `evaluate`

Shape:

```bash
python -m spleeter evaluate [OPTIONS]
```

| Option | Default | Meaning |
| --- | --- | --- |
| `-a`, `--adapter TEXT` | `spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter` | Audio adapter class for evaluation separation. |
| `-o`, `--output_path TEXT` | a temp `separated_audio` directory | Evaluation output root. Estimates go under `audio/test`; metrics go under `metrics/test`. |
| `-p`, `--params_filename TEXT` | `spleeter:2stems` | Model descriptor or local config path. Use a 4-stem descriptor/config for standard MUSDB metric expectations. |
| `--mus_dir TEXT` | required | MUSDB-style dataset root containing `test/<song>/mixture.wav` and ground-truth stems. |
| `--mwf` | false | Enable multichannel Wiener filtering during the separation phase. |
| `--verbose` | false | Enable verbose logs. |
| `--help` | n/a | Show help. |

Evaluation imports optional `musdb` and `museval`. If they are missing, Spleeter logs that the extra dependencies are not found and exits with status `10`.

Example:

```bash
python -m spleeter evaluate \
  --mus_dir MUSDB_ROOT \
  --output_path eval_out \
  --params_filename spleeter:4stems \
  --verbose
```

For layout and metrics, read [evaluation](../sub-skills/evaluation/SKILL.md).
