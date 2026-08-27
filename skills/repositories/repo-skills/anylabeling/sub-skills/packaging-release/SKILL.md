---
name: packaging-release
description: "Operate AnyLabeling install, test, packaging, PyInstaller,
  translation/resource, CPU/GPU wheel, macOS, and pre-publish release
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Packaging and release

Use this sub-skill when the task is about installing AnyLabeling for development, proving startup compatibility, building distributable artifacts, maintaining Qt resources/translations, or preparing CPU/GPU/macOS releases.

## Route here for

- Choosing the correct install variant: default CPU package, Linux/Windows GPU package, macOS CoreML extra, or developer tooling.
- Running the local pre-publish gate: fresh install, unit tests, startup import smoke, optional real-model inference, and multi-Python checks.
- Building wheels/sdists, checking package metadata, or understanding why the GPU package rewrites `pyproject.toml` to publish as `anylabeling-gpu`.
- Building PyInstaller executables, macOS folder-mode output, and diagnosing bundled `onnxruntime` native DLL failures.
- Regenerating Qt translations/resources and checking for the PySide6 toolchain used to rebuild a PyQt6 resource module.

## Route elsewhere

- Manual annotation, label JSON, canvas behavior, and dataset export belong to `annotation-ui-and-data`.
- Auto-labeling model configs, downloads, SAM/YOLO inference, and model registry behavior belong to `auto-labeling-models`.
- PyPI upload credentials, release approval, or tag creation are outside this skill; this skill explains the checks and build mechanics but does not authorize publishing.

## Read first

- [references/packaging-and-release.md](references/packaging-and-release.md) for install variants, wheel/build behavior, PyInstaller/resource workflows, and platform notes.
- [references/pre-publish-checklist.md](references/pre-publish-checklist.md) for the recommended local gate before tagging a release.
- [references/troubleshooting.md](references/troubleshooting.md) for dependency drift, headless Qt, macOS PyQt, GPU wheel metadata, PyInstaller ORT DLL, translation tools, and real-inference skips.

## Bundled helper

- [scripts/check_language_tools.py](scripts/check_language_tools.py) checks whether the translation/resource toolchain is available without mutating generated files. Run it before following the resource regeneration recipe.

Keep release commands scoped to a disposable or intentionally prepared checkout. Some maintainer scripts mutate package metadata or generated resources; read the linked references before running them.
