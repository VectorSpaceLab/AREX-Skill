---
name: "argos-translate"
description: "Routes Argos Translate workflows for offline machine translation,
  package installation, CLI usage, runtime settings, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Argos Translate

Use this skill when a request names **Argos Translate**, `argostranslate`, `argos-translate`, `argospm`, `.argosmodel`, language-pair packages, offline translation, or the package/configuration errors that come with them.

## What this skill covers

- Translating text from Python or the `argos-translate` CLI.
- Loading installed language pairs and understanding translation objects.
- Updating the package index and installing/removing language packages.
- Reading and changing runtime settings such as device selection, sentence-boundary mode, and package/cache locations.
- Troubleshooting missing dependencies, missing packages, invalid archives, and optional backend errors.

## Start here

1. Read `references/api-reference.md` for the verified public modules, classes, and functions.
2. Read `references/cli-reference.md` for the supported `argos-translate` and `argospm` commands.
3. Read `references/configuration.md` before changing environment variables or config files.
4. Read `references/troubleshooting.md` when imports, package installs, CLI calls, or translation setup fail.
5. Read `references/repo-provenance.md` when you need to check whether this skill still matches the current checkout.

## Install and minimal check

- Install from PyPI: `pip install argostranslate`
- Or from a local checkout: `pip install -e .`
- For local verification work, also install `pytest`.

Minimal smoke check:

```bash
python -I -c "from importlib.metadata import version; print(version('argostranslate'))"
python -I -c "from argostranslate import package, translate; print(package.__name__, translate.__name__)"
```

If the package import or CLI help fails, run `scripts/check_runtime.py` from the installed environment before debugging anything else.

## Route map

### Translation workflows
Use `sub-skills/translation/` when the task is about:

- Translating text from Python.
- Using `argos-translate` with `--from-lang` and `--to-lang`.
- Reading from stdin versus a positional text argument.
- Understanding installed language pairs and translation lookup.
- Optional device, chunking, or remote-provider settings that affect translation behavior.
- Sentence-boundary behavior or tag-preserving translation behavior.

### Package-management workflows
Use `sub-skills/package-management/` when the task is about:

- `argospm update`, `search`, `install`, `list`, or `remove`.
- Installing a local `.argosmodel` archive.
- Inspecting package metadata or package contents.
- Package directory layout, cached downloads, or stale index/package errors.

## Shared runtime helpers

- `scripts/check_runtime.py` — run this to inspect the installed package, signatures, and basic translation smoke behavior.
- `scripts/completion.bash` — read or source this if you want Argos Translate shell completion for `argos-translate` and `argospm`.

## When to read more

- Read `references/package-format.md` before changing how `.argosmodel` files are inspected or installed.
- Read `references/configuration.md` before setting `ARGOS_DEVICE_TYPE`, `ARGOS_CHUNK_TYPE`, `ARGOS_PACKAGE_INDEX`, or package/cache directories.
- Read `references/cli-reference.md` whenever the exact command syntax matters.
- Read `references/troubleshooting.md` whenever the failure mentions a missing wheel, missing model package, invalid archive, or optional backend.

## What not to route here

- The separate `argos-translate-gui` repository and GUI-specific workflows.
- Generic Python packaging advice that does not depend on Argos Translate behavior.
- Maintainer-only release scripts, snap publishing, or PyPI upload workflows.

## Evidence basis

This skill was distilled from the repository source, README, docs, tests, and installed-package inspection for Argos Translate 1.11.1. Read `references/repo-provenance.md` before treating it as current for a different checkout.
