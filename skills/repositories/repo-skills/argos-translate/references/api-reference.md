# API Reference

## Purpose

Use this when a task needs the Python API surface instead of only CLI commands. These facts were verified from the installed `argostranslate` distribution version `1.11.1` plus source inspection.

## Import roots

```python
import argostranslate
from argostranslate import package, translate, settings
```

The distribution name is `argostranslate`; the import package is also `argostranslate`. The root package does not expose a useful `__version__`; use `importlib.metadata.version("argostranslate")` for the installed distribution version.

## Package management module

Use `argostranslate.package` when you need to discover, download, install, remove, or inspect Argos model packages.

Key functions and objects:

| API | Use |
| --- | --- |
| `package.update_package_index()` | Download the remote package index into the local data directory. Requires network access. |
| `package.get_available_packages() -> list[AvailablePackage]` | Load packages from the local index, updating it first if missing. |
| `package.install_from_path(path)` | Install a local `.argosmodel` zip archive by extracting it into the package data directory. Clears the installed-language cache. |
| `package.get_installed_packages(path=None) -> list[Package]` | Return installed packages from the configured package directories or a supplied directory. |
| `package.uninstall(pkg)` | Remove an installed package directory and clear the installed-language cache. |
| `package.argospm_package_name(pkg) -> str` | Convert package metadata into names such as `translate-en_es`. |
| `package.install_package_for_language_pair(from_code, to_code) -> bool` | Find, download, and install a direct package for a language pair if available. |
| `package.load_available_packages()` | Deprecated alias; prefer `get_available_packages()`. |

Objects:

- `IPackage` is the shared metadata base for local and remote package records.
- `Package(package_path)` represents an installed package directory and requires `metadata.json` under that directory.
- `AvailablePackage(metadata)` represents a remote index entry. Its `.download()` method writes a cached `.argosmodel`; `.install()` downloads then installs and deletes the cached archive.

Package records commonly expose `package_version`, `argos_version`, `from_code`, `from_name`, `to_code`, `to_name`, `links`, `type`, `languages`, `dependencies`, `source_languages`, `target_languages`, and `target_prefix`.

## Translation module

Use `argostranslate.translate` for installed-language discovery and text translation.

Key functions and objects:

| API | Use |
| --- | --- |
| `translate.get_installed_languages() -> list[Language]` | Load languages from installed `type == "translate"` packages. Results are cached. |
| `translate.load_installed_languages()` | Deprecated alias; prefer `get_installed_languages()`. |
| `translate.get_language_from_code(code)` | Return a `Language` by ISO code, or `None` if not installed. |
| `translate.get_translation_from_codes(from_code, to_code)` | Return the translation object for a source/target code pair. Requires installed languages and translation path. |
| `translate.translate(q, from_code, to_code) -> str` | Translate one string through the selected installed translation object. |

Core classes:

- `Language(code, name)` owns `translations_from` and `translations_to`; call `from_lang.get_translation(to_lang)` to choose a translation.
- `ITranslation.translate(input_text)` calls `hypotheses(input_text, num_hypotheses=1)[0].value`.
- `PackageTranslation(from_lang, to_lang, pkg)` runs a CTranslate2 model from an installed package and the configured sentence-boundary detector.
- `IdentityTranslation(lang)` returns the input unchanged and is useful for same-language paths and smoke tests.
- `CompositeTranslation(t1, t2)` chains translations so Argos can pivot through intermediate languages.
- `CachedTranslation(underlying)` caches paragraph-level translation hypotheses for repeated text.
- `RemoteTranslation(from_lang, to_lang, api)` is the LibreTranslate-backed remote translation class; `LibreTranslateTranslation` is a compatibility alias.
- `FewShotTranslation(from_lang, to_lang, language_model)` is an optional few-shot provider path that depends on a language-model API.
- `Hypothesis(value, score)` stores a translation candidate and score.

## CLI modules

The installed console scripts call these no-argument functions:

- `argostranslate.cli.main()` powers `argos-translate`.
- `argostranslate.argospm.main()` powers `argospm`.

Do not call these functions from long-running code without controlling `sys.argv`; for scripts and users, prefer the installed console commands.

## Settings module

`argostranslate.settings` loads environment variables and a JSON settings file at import time. Importing it also creates the default data, config, cache, downloads, and package directories when possible. Read `configuration.md` before setting values such as `ARGOS_PACKAGES_DIR`, `ARGOS_DEVICE_TYPE`, or `ARGOS_CHUNK_TYPE`.

## Sentence-boundary, tokenization, and formatting helpers

- `argostranslate.sbd` provides `MiniSBDSentencizer`, `StanzaSentencizer`, and `SpacySentencizerSmall`; default behavior resolves to Argos/MiniSBD unless settings choose another chunk type.
- `argostranslate.tokenizer` provides `SentencePieceTokenizer` and `BPETokenizer`; packages choose one based on `sentencepiece.model` or `bpe.model` in the installed package directory.
- `argostranslate.tags.translate_tags(underlying_translation, tag)` can translate a simple tag tree while preserving non-translatable subtrees when injection succeeds.

## Networked provider adapters

- `argostranslate.apis.LibreTranslateAPI(url=None, api_key=None)` exposes `.translate(q, source, target)`, `.languages()`, and `.detect(q)`. It calls a remote service and needs network access.
- `argostranslate.apis.OpenAIAPI(api_key)` implements `ILanguageModel.infer(prompt)` for the older few-shot path. It is credentialed and not part of the default offline workflow.

## Minimal API examples

List installed languages:

```python
from argostranslate import translate

for language in translate.get_installed_languages():
    print(language.code, language.name)
```

Translate after the relevant package is installed:

```python
from argostranslate import translate

text = translate.translate("Hello world", "en", "es")
print(text)
```

Install from a local package archive:

```python
from pathlib import Path
from argostranslate import package

package.install_from_path(Path("translate-en_es.argosmodel"))
```

Before running real translation, ensure the required source and target language packages are installed. If they are not, use the package-management sub-skill first.
