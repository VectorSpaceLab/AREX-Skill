# Configuration Reference

## Purpose

Read this before changing `ARGOS_*` variables, config files, package directories, device selection, or sentence-boundary behavior.

Argos Translate loads settings from environment variables first, then from a JSON settings file, then defaults. Set environment variables before importing `argostranslate.settings` or modules that import it.

## Default user state

By default, Argos Translate creates and uses these XDG-style locations under the current user home:

| State | Default |
| --- | --- |
| Data directory | `~/.local/share/argos-translate/` |
| Package directory | `~/.local/share/argos-translate/packages/` |
| Config directory | `~/.config/argos-translate/` |
| Settings file | `~/.config/argos-translate/settings.json` |
| Cache directory | `~/.local/cache/argos-translate/` |
| Downloads cache | `~/.local/cache/argos-translate/downloads/` |

If `XDG_DATA_HOME`, `XDG_CONFIG_HOME`, or `XDG_CACHE_HOME` are set, those bases are used. Snap packaging can also redirect the home base through Snap environment variables.

Importing `argostranslate.settings` creates these directories if possible. If imports fail due permissions, set the relevant XDG variables or `ARGOS_PACKAGES_DIR` to writable locations before import.

## Settings file shape

The settings file is JSON:

```json
{
  "ARGOS_DEBUG": "1",
  "ARGOS_PACKAGE_INDEX": "https://raw.githubusercontent.com/argosopentech/argospm-index/main/",
  "ARGOS_PACKAGES_DIR": "/path/to/packages",
  "ARGOS_DEVICE_TYPE": "cpu"
}
```

Environment variables override the JSON file. Use the same key names in the JSON file and environment.

## Package index and package directories

| Setting | Default | Effect |
| --- | --- | --- |
| `ARGOS_PACKAGE_INDEX` | `https://raw.githubusercontent.com/argosopentech/argospm-index/main/` | Base URL for `index.json`; used by `argospm update` and `package.update_package_index()`. |
| `ARGOS_DEV_MODE` | false | Switches the default remote package index to the dev index when truthy. |
| `ARGOS_PACKAGES_DIR` | data dir `packages/` | Directory where `.argosmodel` packages are extracted and later loaded. |

`package.install_from_path()` extracts archives into `settings.package_data_dir`. `package.get_installed_packages()` looks through `settings.package_dirs`, which starts with the package data dir and may add Snap package directories.

## Device and CTranslate2 runtime

| Setting | Default | Effect |
| --- | --- | --- |
| `ARGOS_DEVICE_TYPE` | `cpu` | Passed to CTranslate2 translator as the `device` parameter. Docs/source primarily support `cpu` and `cuda`; README also mentions `auto`. Validate non-CPU modes in the target runtime. |
| `ARGOS_COMPUTE_TYPE` | `auto` | If not `auto`, passed to CTranslate2 as `compute_type`. Common values include `float32`, `int8`, and `int8_float32`. |
| `ARGOS_INTER_THREADS` | `1` | Number of parallel translators. |
| `ARGOS_INTRA_THREADS` | `0` | Threads per translator; `0` lets CTranslate2 decide. |
| `ARGOS_BATCH_SIZE` | `32` | Max batch size passed to `translate_batch()`. |
| `ARGOS_BEAM_SIZE` | `4` | Minimum beam size used for translation hypotheses. |

CUDA/GPU execution is optional. Do not claim that a CUDA path is verified unless the target environment actually has compatible CTranslate2/CUDA runtime and a successful device smoke test.

## Sentence-boundary detection

`ARGOS_CHUNK_TYPE` chooses the sentencizer used before translation. Source enum values are `DEFAULT`, `ARGOSTRANSLATE`, `NONE`, `STANZA`, `SPACY`, and `MINISBD`.

| Value | Behavior / requirement |
| --- | --- |
| `DEFAULT` | Normalized to `ARGOSTRANSLATE` in settings. |
| `ARGOSTRANSLATE` | Uses package-provided SBD when available or MiniSBD fallback. |
| `MINISBD` | Uses MiniSBD, with package-provided model if present, otherwise cached MiniSBD model/fallback mapping. |
| `SPACY` | Uses a package-provided SpaCy model or cached multilingual SpaCy model; can attempt a SpaCy model download through the runtime helper path. |
| `STANZA` | Requires the optional Stanza dependency and packaged Stanza resources. Install with `pip install "argostranslate[stanza]"` when selecting this mode. |
| `NONE` | Documented in settings docs, but current package translation code can raise `NotImplementedError` because no sentencizer is assigned. Avoid it unless you have verified the exact runtime behavior. |

Set chunk type before first importing translation modules in a long-running process.

## Model provider modes

| Setting | Default | Effect |
| --- | --- | --- |
| `ARGOS_MODEL_PROVIDER` | `OPENNMT` | `OPENNMT` uses installed local packages. `LIBRETRANSLATE` and `OPENAI` use remote provider paths. |
| `LIBRETRANSLATE_API_KEY` | unset | Passed to the LibreTranslate API adapter when used. |
| `OPENAI_API_KEY` | unset | Passed to the OpenAI adapter when `ARGOS_MODEL_PROVIDER=OPENAI`. |

Remote provider modes need network access and may need credentials. They are not part of the default offline workflow.

## Debugging and experimental flags

| Setting | Default | Effect |
| --- | --- | --- |
| `ARGOS_DEBUG` | false | Enables verbose logging through `argostranslate.utils`. |
| `ARGOS_EXPERIMENTAL_ENABLED` | false | Source-level flag for experimental behavior. |

## Safe configuration workflow

1. Decide which package directory, index URL, device, and chunk type the task needs.
2. Export environment variables before importing Argos Translate in the process.
3. Run `scripts/check_runtime.py` to verify imports and default values.
4. For a language-pair task, confirm packages are installed with `argospm list` or `package.get_installed_packages()`.
5. Run a tiny translation only after the required language pair is installed.
