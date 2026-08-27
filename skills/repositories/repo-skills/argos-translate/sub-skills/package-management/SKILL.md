---
name: "package-management"
description: "Guides Argos Translate package index, argospm, local .argosmodel
  installation, package inspection, and model-package troubleshooting
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Package Management

Use this sub-skill when the user needs to find, install, inspect, list, remove, or troubleshoot Argos Translate language packages.

## Scope

This sub-skill owns:

- `argospm update`, `search`, `install`, `list`, and `remove`.
- Python installation of local `.argosmodel` archives with `package.install_from_path()`.
- Package index behavior and package naming such as `translate-en_es`.
- Installed package directories and package cache behavior.
- `.argosmodel` archive validation and package metadata interpretation.
- Package-specific troubleshooting before translation.

Route actual text translation, translation-object selection, sentence-boundary behavior during translation, and `argos-translate` runtime failures to `../translation/`.

## Read these first

- `references/workflows.md` — package index, local archive, and installed-package workflows.
- `references/troubleshooting.md` — package-specific failure modes and recovery.
- `../../references/package-format.md` — `.argosmodel` archive and metadata format.
- `../../references/cli-reference.md` — exact `argospm` commands.
- `../../references/configuration.md` — package index URL and package directory settings.
- `../../references/api-reference.md` — Python APIs for package installation and discovery.
- `scripts/check_argosmodel.py` — safe local archive validator.

## Minimal decision flow

1. If the user already has a local `.argosmodel`, validate it first:

   ```bash
   python sub-skills/package-management/scripts/check_argosmodel.py translate-en_es.argosmodel
   ```

2. If using remote packages, update and search the index:

   ```bash
   argospm update
   argospm search -f en -t es
   ```

3. Install the package by index name or local archive path:

   ```bash
   argospm install translate-en_es
   ```

   or:

   ```python
   from pathlib import Path
   from argostranslate import package
   package.install_from_path(Path("translate-en_es.argosmodel"))
   ```

4. Verify discovery:

   ```bash
   argospm list
   ```

5. Switch back to `../translation/` to run a tiny translation.

## Package names and language pairs

`argospm` names combine package type and language codes. For direct translation packages, expect names like:

```text
translate-en_es
translate-de_en
translate-tr_en
```

`argospm install translate` installs all packages and can be very large. Do not run it unless the user explicitly wants all language packages and has enough disk/network budget.

## Local archive workflow

Use local archives when network access is unavailable, a package link fails, or the user supplies a downloaded `.argosmodel`.

- Validate with `sub-skills/package-management/scripts/check_argosmodel.py`.
- Install with `package.install_from_path()`.
- Confirm with `argospm list` or `package.get_installed_packages()`.
- Clear or restart translation caches before testing in an already-running Python process.

## Safety boundaries

- Installing packages writes extracted model files into the configured package directory.
- Removing packages deletes installed package directories.
- `scripts/uninstall.sh` from the source repository was not bundled because it removes cache/share directories and uninstalls the package; do destructive cleanup only after explicit user approval.
- Remote downloads and installing every language package can consume significant bandwidth and storage.

## Native verification anchors

The source repository's safe package unit-test anchor is `tests/test_package.py`, especially metadata loading and installed package object behavior. Remote index/download workflows are network-dependent and should be tested separately only when the user authorizes network use.
