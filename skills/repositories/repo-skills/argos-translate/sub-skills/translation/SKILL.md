---
name: "translation"
description: "Guides Argos Translate text translation through Python APIs, the
  argos-translate CLI, runtime settings, sentence-boundary modes, and
  translation troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Translation Workflows

Use this sub-skill when the user wants to translate text, inspect installed languages, route through `translate` APIs, use `argos-translate`, tune runtime translation settings, or debug translation failures.

## Scope

This sub-skill owns:

- Python translation with `argostranslate.translate`.
- CLI translation with `argos-translate`.
- Installed language lookup and translation-object selection.
- Device, compute, chunking, and sentence-boundary settings that affect translation runtime.
- Optional remote provider notes for LibreTranslate/OpenAI-backed paths.
- Translation-specific troubleshooting.

Route package index updates, package installation/removal, and `.argosmodel` archive inspection to `../package-management/` first.

## Read these first

- `references/workflows.md` — step-by-step Python and CLI translation workflows.
- `references/troubleshooting.md` — translation-specific failure modes and recovery.
- `../../references/api-reference.md` — verified API objects and signatures.
- `../../references/cli-reference.md` — exact CLI flags and command behavior.
- `../../references/configuration.md` — environment variables, config files, device selection, and SBD modes.
- `../../references/troubleshooting.md` — cross-cutting import, package, optional backend, and config failures.

## Minimal decision flow

1. Confirm the package imports:

   ```bash
   python scripts/check_runtime.py
   ```

2. Confirm the required source and target languages are installed:

   ```python
   from argostranslate import translate
   print([(lang.code, lang.name) for lang in translate.get_installed_languages()])
   ```

3. If either language or the language pair is missing, switch to `../package-management/` and install the required package.
4. Use Python API or CLI translation only after the language-pair package exists.
5. Set runtime variables such as `ARGOS_DEVICE_TYPE` and `ARGOS_CHUNK_TYPE` before importing translation modules in a long-running process.

## Python translation route

Use the direct helper when a package exists:

```python
from argostranslate import translate

print(translate.translate("Hello world", "en", "es"))
```

Use object-level APIs when you need to inspect languages, pivot paths, or translation classes:

```python
from argostranslate import translate

languages = {lang.code: lang for lang in translate.get_installed_languages()}
from_lang = languages["en"]
to_lang = languages["es"]
translation = from_lang.get_translation(to_lang)
print(translation.translate("Hello world"))
```

## CLI translation route

Use the installed CLI command:

```bash
argos-translate --from-lang en --to-lang es "Hello world"
echo "Text to translate" | argos-translate -f en -t es
```

Do not rely on older `--from` / `--to` aliases unless verified in the target environment. Current installed help uses `--from-lang` / `--to-lang` and `-f` / `-t`.

## Runtime-setting route

Read `../../references/configuration.md` before changing:

- `ARGOS_DEVICE_TYPE` for CPU/CUDA runtime.
- `ARGOS_COMPUTE_TYPE`, `ARGOS_BATCH_SIZE`, and thread settings for CTranslate2 behavior.
- `ARGOS_CHUNK_TYPE` for MiniSBD, SpaCy, or Stanza sentence splitting.
- `ARGOS_MODEL_PROVIDER` for non-default remote provider paths.

CUDA, Stanza, SpaCy downloads, and remote provider paths are optional runtime capabilities. Do not present them as verified unless the target environment has been explicitly tested.

## Advanced API route

Use `../../references/api-reference.md` for:

- `IdentityTranslation`, `CompositeTranslation`, and `CachedTranslation`.
- `RemoteTranslation` / LibreTranslate API adapter.
- `FewShotTranslation` and OpenAI adapter.
- `tags.translate_tags()` for simple tag-tree preservation.
- `sbd` sentencizer classes and tokenizer details.

## Native verification anchors

The source repository's safe translation unit-test anchor is `tests/test_translate.py`. End-to-end language-pair tests depend on installed model packages and may skip or require network/package setup; do not treat those skips as proof that translation works.
