# Troubleshooting

## Purpose

Use this for cross-cutting install/import, CLI, model-package, configuration, and optional backend failures. Workflow-specific recovery lives in the nearest sub-skill troubleshooting file.

## Import or installation failures

### `ModuleNotFoundError: No module named 'argostranslate'`

Likely causes:

- The package is not installed in the active Python environment.
- The command is using a different Python than the one used for installation.

Recovery:

```bash
python -m pip install argostranslate
python -I -c "from importlib.metadata import version; print(version('argostranslate'))"
python scripts/check_runtime.py
```

Use `python -m pip` from the exact environment that will run translation.

### Missing compiled/runtime dependencies

Failures importing `ctranslate2`, `sentencepiece`, `minisbd`, `onnxruntime`, or `spacy` usually mean the base package dependencies are incomplete or installed for the wrong Python.

Recovery:

```bash
python -m pip install --upgrade --force-reinstall argostranslate
python -m pip check
python scripts/check_runtime.py
```

If this happens in an editable checkout, reinstall from that checkout with `python -m pip install -e .`.

## CLI does not behave as expected

### `argos-translate` prints the input unchanged

If you pass text without both `--from-lang` and `--to-lang`, the CLI uses identity translation. Re-run with both language flags:

```bash
argos-translate --from-lang en --to-lang es "Hello world"
```

### `unrecognized arguments: --from` or `--to`

Current installed help uses `--from-lang` / `--to-lang` and short flags `-f` / `-t`. Older examples may show `--from` / `--to`.

### `'en' is not an installed language.`

The language code was not found in installed packages. Use the package-management sub-skill to update/search/install a matching package.

```bash
argospm update
argospm search -f en -t es
argospm install translate-en_es
```

### `No translation installed from en to es`

Both language codes may exist, but no direct or pivot path was loaded. Install a direct package or enough intermediate packages for pivoting.

## Package-management failures

### `Package not found`

Likely causes:

- Stale or missing local package index.
- Wrong `argospm` package name.
- Filters hide the desired package.

Recovery:

```bash
argospm update
argospm search -f en -t es
argospm install translate-en_es
```

### Download fails during package install

Likely causes:

- Network unavailable.
- Package index URL is wrong.
- A download link in the index is stale.

Recovery:

1. Check `ARGOS_PACKAGE_INDEX` in `references/configuration.md`.
2. Re-run `argospm update`.
3. If a local `.argosmodel` archive is available, validate it with `sub-skills/package-management/scripts/check_argosmodel.py` and install it with Python `package.install_from_path()`.

### `Not a valid Argos Model (must be a zip archive)`

The path passed to `package.install_from_path()` is not a zip archive. Validate with:

```bash
python sub-skills/package-management/scripts/check_argosmodel.py path/to/file.argosmodel
```

### `FileNotFoundError ... no metadata.json`

The installed package directory is missing `metadata.json`. The archive may be corrupted or extracted into an unexpected layout. Inspect the archive before reinstalling.

## Package/cache directory problems

Symptoms:

- Permission errors when importing settings or installing packages.
- Packages install but are not discovered.
- A process uses one package directory while another uses a different one.

Recovery:

1. Read `references/configuration.md` for default state paths.
2. Set `ARGOS_PACKAGES_DIR` before import if you need a custom writable package directory.
3. Use `argospm list` and `package.get_installed_packages()` from the same environment to confirm discovery.
4. Avoid destructive cleanup scripts unless the user explicitly wants to remove cached and installed packages.

## Sentence-boundary and optional backend failures

### `NotImplementedError` after `ARGOS_CHUNK_TYPE=NONE`

The docs list `NONE`, but current package translation code does not assign a sentencizer for this mode. Use `DEFAULT`, `ARGOSTRANSLATE`, or `MINISBD` unless the target version has changed and has been verified.

### Stanza mode fails

`ARGOS_CHUNK_TYPE=STANZA` requires the optional `stanza` dependency and compatible packaged resources. Install the extra and verify a tiny translation before relying on it:

```bash
python -m pip install "argostranslate[stanza]"
```

### SpaCy mode tries to download a model

`ARGOS_CHUNK_TYPE=SPACY` may use a cached multilingual SpaCy model when no package-provided SpaCy resources exist. If network access is unavailable, choose `MINISBD` or provide the necessary package resources.

## GPU/device failures

### CUDA device requested but unavailable

If `ARGOS_DEVICE_TYPE=cuda` fails, likely causes include CPU-only CTranslate2 runtime, missing/hidden NVIDIA GPU, incompatible driver, or no CUDA support in the environment.

Recovery:

1. Confirm CPU translation works first with `ARGOS_DEVICE_TYPE=cpu`.
2. Verify the target environment has a compatible CTranslate2 GPU runtime and visible CUDA device.
3. Do not count CPU success as GPU verification; run an actual CUDA smoke and tiny translation in the target environment.

## Remote provider failures

`ARGOS_MODEL_PROVIDER=LIBRETRANSLATE` and `ARGOS_MODEL_PROVIDER=OPENAI` are networked provider paths. They may need reachable endpoints and credentials such as `LIBRETRANSLATE_API_KEY` or `OPENAI_API_KEY`.

Recovery:

- Treat these as remote-service workflows, not offline translation.
- Verify endpoint availability and credentials outside the offline package path.
- Avoid writing API keys into code, config files, logs, or generated artifacts.

## When to stop

Stop and ask for human input when the next step would install a large model package, delete local package/cache directories, use a credentialed remote provider, switch to GPU/CUDA packages, or change a user's existing environment in a way that could break other work.
