# Argos Model Package Format

## Purpose

Read this before installing, validating, or debugging `.argosmodel` archives and installed package directories.

## Archive and installed directory

Argos model packages are zip archives normally named with a `.argosmodel` extension. `package.install_from_path(path)` verifies that the file is a zip archive, extracts it into the configured package data directory, and clears the installed-language cache.

An installed package is a directory under the configured packages dir. `Package(package_path)` requires a `metadata.json` file at the package root.

Typical translation package contents:

```text
<package-root>/
  metadata.json
  model/                    # CTranslate2 model directory
  sentencepiece.model        # preferred tokenizer when present
  bpe.model                  # alternative tokenizer when sentencepiece.model is absent
  README.md                  # optional package description
  minisbd/                   # optional package-provided MiniSBD resources
  stanza/                    # optional package-provided Stanza resources
  spacy/                     # optional package-provided SpaCy resources
```

The code chooses `SentencePieceTokenizer` when `sentencepiece.model` exists and `BPETokenizer` when `bpe.model` exists.

## Metadata fields

`IPackage.load_metadata_from_json()` accepts sparse metadata and fills missing fields with empty strings, empty lists, or `None`. Useful fields include:

| Field | Meaning |
| --- | --- |
| `package_version` | Version of the model package. |
| `argos_version` | Argos Translate version the package targets. |
| `from_code`, `from_name` | Source language code/name for a direct translation package. |
| `to_code`, `to_name` | Target language code/name for a direct translation package. |
| `links` | Candidate download URLs for remote packages. |
| `type` | Package type; default is `translate`. |
| `languages` | Additional language records. |
| `dependencies` | Package dependencies if declared by index metadata. |
| `source_languages`, `target_languages` | Explicit source/target language records. |
| `from_codes`, `to_codes` | Multi-code fields used by some package types. |
| `target_prefix` | Optional prefix passed to CTranslate2 as a target prefix and stripped from output when present. |

`package.argospm_package_name(pkg)` produces names such as `translate-en_es` by combining `type`, `from_code`, and `to_code`.

## Local validation workflow

Use the bundled helper before installing an unknown archive:

```bash
python sub-skills/package-management/scripts/check_argosmodel.py translate-en_es.argosmodel
```

The helper checks that the file is a zip archive, that `metadata.json` is present and parseable, and whether model/tokenizer/SBD resources are present.

## Install from a local archive

```python
from pathlib import Path
from argostranslate import package

archive = Path("translate-en_es.argosmodel")
package.install_from_path(archive)
```

After install, reload languages:

```python
from argostranslate import translate

translate.get_installed_languages.cache_clear()
languages = translate.get_installed_languages()
```

`install_from_path()` already clears the installed-language cache; explicit cache clearing is useful after manual filesystem changes or debugging.

## Installed package discovery

By default, packages are searched in `settings.package_dirs`. That list starts with `settings.package_data_dir` and may include Snap-specific package directories. To inspect a specific directory without changing settings, pass it to `get_installed_packages(path=...)`.

```python
from pathlib import Path
from argostranslate import package

for pkg in package.get_installed_packages(Path("/path/to/packages")):
    print(package.argospm_package_name(pkg), pkg)
```

## Safety notes

- Installing extracts every archive member into the configured package directory. Inspect unknown archives first.
- Removing a package with `package.uninstall(pkg)` deletes the installed package directory.
- Remote package downloads depend on URLs from the package index. Treat network failures and incomplete cached downloads separately from invalid local archives.
- A valid archive can still fail translation if its model files are missing, incompatible with the current CTranslate2 runtime, or lack the tokenizer expected by the package.
