# Models and configuration

Spleeter workflows are driven by JSON parameter dictionaries. A descriptor passed with `--params_filename/-p` or to `Separator(...)` can be either an embedded `spleeter:` resource name or a filesystem JSON path.

## Loading configs

`load_configuration(descriptor: str)` behaves as follows:

| Descriptor form | Behavior |
| --- | --- |
| `spleeter:<name>` | Loads bundled resource `<name>.json` from Spleeter's package resources. Raises a Spleeter error if the resource does not exist. |
| filesystem path | Opens that JSON path exactly. Raises a Spleeter error if the path does not exist. |

Custom training or custom checkpoint use should normally copy an evidence-backed config shape into a new JSON file and pass that file path. Embedded pretrained descriptors include placeholder CSV paths and are not ready-to-run training configs without editing.

## Embedded descriptors in Spleeter 2.4.2

| Descriptor | Model dir | Stems | Sample rate in config | F bins | Model function |
| --- | --- | --- | --- | --- | --- |
| `spleeter:2stems` | `2stems` | `vocals`, `accompaniment` | 44100 | 1024 | `unet.unet` |
| `spleeter:4stems` | `4stems` | `vocals`, `drums`, `bass`, `other` | 44100 | 1024 | `unet.unet` |
| `spleeter:5stems` | `5stems` | `vocals`, `piano`, `drums`, `bass`, `other` | 44100 | 1024 | `unet.softmax_unet` |
| `spleeter:2stems-16kHz` | `2stems` | `vocals`, `accompaniment` | 44100 | 1536 | `unet.unet` |
| `spleeter:4stems-16kHz` | `4stems` | `vocals`, `drums`, `bass`, `other` | 44100 | 1536 | `unet.unet` |
| `spleeter:5stems-16kHz` | `5stems` | `vocals`, `piano`, `drums`, `bass`, `other` | 44100 | 1536 | `unet.softmax_unet` |
| `spleeter:musdb` | `musdb_model` | `vocals`, `drums`, `bass`, `other` | 44100 | 1024 | `unet.unet` |

The `-16kHz` descriptor names are package resource names; check actual config fields rather than inferring every runtime value from the descriptor name alone.

## Model cache and provider behavior

Pretrained separation calls `create_estimator`, which loads the config and asks `ModelProvider.default()` to resolve `params["model_dir"]`. The default provider is `GithubModelProvider.from_environ()`.

Important provider details:

| Control | Default | Use |
| --- | --- | --- |
| `MODEL_PATH` environment variable | `pretrained_models` | Base directory for relative `model_dir` values. A relative model dir such as `2stems` resolves below this base. |
| `GITHUB_HOST` | `https://github.com` | Release host for downloading archives. |
| `GITHUB_REPOSITORY` | `deezer/spleeter` | Repository path for model release assets. |
| `GITHUB_RELEASE` | `v1.4.0` | Release containing pretrained model tarballs and `checksum.json`. |
| `.probe` file | none until written | Marker that a model directory is considered available. |

When a relative model directory is requested, Spleeter joins it under `MODEL_PATH`. If the model directory does not exist and its `.probe` marker is absent, the provider downloads `<model>.tar.gz`, validates its SHA-256 against the release `checksum.json`, extracts the archive, and writes `.probe`.

Operational consequences:

- First use of a pretrained descriptor may be slow and require network access.
- A checksum mismatch raises `Downloaded file is corrupted, please retry`; remove the incomplete model directory and retry after fixing the network/cache problem.
- A descriptor/model name missing from the checksum index raises `No checksum for model ...`.
- Cache directories must be writable by the process running Spleeter.
- If network access is forbidden, prewarm the model cache or use a local trained config/model directory before running separation/evaluation.
- Keep cache paths and environment variables as local runtime context; do not bake machine-specific cache paths into reusable instructions.

## Custom JSON config checklist

Before using a custom JSON config for separation or training, confirm:

1. `model_dir` points to the intended pretrained or trained checkpoint directory.
2. `instrument_list` matches the stems expected by downstream output/evaluation.
3. `mix_name`, `sample_rate`, `frame_length`, `frame_step`, `T`, `F`, `n_channels`, `separation_exponent`, and `mask_extension` are internally compatible.
4. `model.type` resolves to an available Spleeter model function such as `unet.unet` or `unet.softmax_unet`.
5. For training, `train_csv`, `validation_csv`, cache paths, checkpoint settings, and `n_chunks_per_song` are real values, not placeholders.
6. For evaluation, the descriptor/config stem count matches the metric workflow. Standard MUSDB evaluation expects `vocals`, `drums`, `bass`, and `other`.

Use [training data/config](../sub-skills/training/references/data-format-and-config.md) for training-specific validation rules and [evaluation MUSDB format](../sub-skills/evaluation/references/musdb-format-and-metrics.md) for evaluation layout.

## Environment variables should stay task-local

It is fine for a user to set `MODEL_PATH`, `GITHUB_HOST`, `GITHUB_REPOSITORY`, or `GITHUB_RELEASE` for a particular run. Treat those values as runtime inputs. Do not persist private cache locations, proxies, or custom release hosts in generated outputs unless the user explicitly asks for a task-local command.
