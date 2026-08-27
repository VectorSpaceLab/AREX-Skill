# Translation Troubleshooting

## Purpose

Use this when translation APIs or `argos-translate` fail after the package imports successfully.

## Empty language list

Symptom:

```python
from argostranslate import translate
print(translate.get_installed_languages())  # []
```

Likely cause: no installed `.argosmodel` translation packages in the active package directory.

Recovery:

1. Use `argospm list` to confirm installed packages.
2. Use the package-management sub-skill to update/search/install packages.
3. Confirm `ARGOS_PACKAGES_DIR` points to the same directory for install and translation.

## CLI says a language is not installed

Symptom:

```text
'en' is not an installed language.
```

Recovery:

```bash
argospm update
argospm search -f en -t es
argospm install translate-en_es
argospm list
```

Then retry:

```bash
argos-translate -f en -t es "Hello world"
```

If the package was installed from Python, restart the long-running process or clear `translate.get_installed_languages.cache_clear()`.

## No translation path exists

Symptom:

```text
No translation installed from en to es
```

Likely causes:

- Source and target languages exist, but the direct pair is missing.
- Pivot packages are insufficient for a composite translation path.
- The target package installed into a different package directory.

Recovery:

1. Inspect installed package names with `argospm list`.
2. Install a direct package such as `translate-en_es`, or install both sides of a pivot path.
3. Use object inspection from `workflows.md` to print each language's `translations_from`.

## CLI echoes the input

Symptom: `argos-translate "Hello"` prints `Hello`.

Cause: the CLI uses identity translation when text is present but both language flags are not provided.

Recovery: rerun with both flags.

```bash
argos-translate --from-lang en --to-lang es "Hello"
```

## Translation crashes when loading the model

Likely causes:

- Corrupt or incomplete installed package.
- Missing `model/` directory, tokenizer file, or package metadata.
- CTranslate2 cannot load the model with the selected device/compute type.

Recovery:

1. Inspect the source archive or package directory with `sub-skills/package-management/scripts/check_argosmodel.py` when you have the archive.
2. Reinstall the package from a known-good archive or package index.
3. Set `ARGOS_DEVICE_TYPE=cpu` and `ARGOS_COMPUTE_TYPE=auto` to separate model/package errors from device-specific errors.
4. Retry a tiny translation before using long text.

## Sentence-boundary mode fails

### `ARGOS_CHUNK_TYPE=STANZA`

Stanza mode requires the optional Stanza package and compatible resources. Install the extra and verify a tiny translation:

```bash
python -m pip install "argostranslate[stanza]"
export ARGOS_CHUNK_TYPE=STANZA
```

If package-provided Stanza resources are missing, use `MINISBD` or `ARGOSTRANSLATE` unless the task explicitly requires Stanza.

### `ARGOS_CHUNK_TYPE=SPACY`

SpaCy mode may require a cached multilingual model. If the cache is not initialized and downloads are not allowed, use `MINISBD`.

### `ARGOS_CHUNK_TYPE=NONE`

Avoid this mode for package translation in this version. The code can raise `NotImplementedError` because no sentencizer is assigned.

## CUDA/device errors

Symptoms can include CTranslate2 device errors, CUDA runtime failures, or successful CPU import followed by translation failure when `ARGOS_DEVICE_TYPE=cuda`.

Recovery:

1. Verify CPU mode first:

   ```bash
   ARGOS_DEVICE_TYPE=cpu argos-translate -f en -t es "Hello"
   ```

2. Verify the target environment has a visible compatible CUDA device and CTranslate2 GPU support.
3. Only then set `ARGOS_DEVICE_TYPE=cuda` or `auto`.
4. If CUDA is optional for the user's task, return to CPU mode instead of blocking.

## Long text or repeated text behaves poorly

Facts:

- Translation splits input into paragraphs and sentence chunks.
- `CachedTranslation` caches paragraph-level hypotheses for repeated text.
- `ARGOS_BATCH_SIZE`, `ARGOS_BEAM_SIZE`, thread settings, and sentence-boundary mode can affect performance and output shape.

Recovery:

1. Test a single sentence first.
2. Test a paragraph with the intended `ARGOS_CHUNK_TYPE`.
3. Tune `ARGOS_BATCH_SIZE` and `ARGOS_COMPUTE_TYPE` only after correctness is verified.
4. Avoid comparing output strings exactly across different chunkers, devices, or compute types.

## Remote provider path fails

If `ARGOS_MODEL_PROVIDER=LIBRETRANSLATE` or `OPENAI` is set, failures may come from endpoint availability, credentials, remote API format, or quota. Confirm that the task explicitly wants a remote provider; otherwise unset `ARGOS_MODEL_PROVIDER` and use local packages.
