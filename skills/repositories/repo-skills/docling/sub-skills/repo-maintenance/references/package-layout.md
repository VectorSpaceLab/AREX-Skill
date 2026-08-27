# Package Layout and Metadata

Docling uses a split packaging model:

- `docling-slim` is the modular package that ships the importable `docling/` Python module, the CLI implementations, plugin defaults, and most optional feature extras.
- `docling` is the full meta-package. It depends on the matching `docling-slim[standard]` version and intentionally ships no duplicate Python modules.
- Both packages expose the `docling` and `docling-tools` scripts. The full package re-declares them so tool installers expose scripts from the named package even though the modules come from `docling-slim`.
- Supported Python is `>=3.10,<4.0`; keep public APIs typed and compatible with that range.

## Files To Check When Package Metadata Changes

- Root package metadata: `pyproject.toml`.
- Full meta-package metadata: `packages/docling/pyproject.toml`.
- Slim package README metadata: `packages/docling-slim/README.md` when public installation guidance changes.
- Lock/dependency state: `uv lock --locked` should pass for unchanged dependency resolution; update lock files only when dependency changes are intentional.
- CLI docs: regenerate generated CLI reference after changing Typer commands, defaults, option names, help text, or command grouping.

## Extras Model

`docling-slim` owns granular optional extras. Installed facts include these important families:

- Format extras: PDF, Office, web, LaTeX, email, audio, HTML rendering, XML/XBRL.
- OCR/model extras: rapid OCR, EasyOCR, Tesseract OCR, macOS OCR, local models, remote model serving, ONNX Runtime, inline VLM.
- Feature extras: chunking, extraction, service client, CLI.
- Convenience bundles: `standard` combines common local conversion, model, OCR, Office/web, chunking, extraction, service-client, and CLI support; `all` adds VLM, audio, HTML rendering, XML/XBRL, remote models, ONNX Runtime, and alternate OCR engines.

The full `docling` package re-exports backwards-compatible extras that point to version-pinned `docling-slim` extras. When changing a slim extra name, membership, or version-sensitive dependency, check whether the full package needs a matching re-export update.

## CLI Entry Points

The public entry points are:

- `docling = docling.cli.main:app`
- `docling-tools = docling.cli.tools:app`

Preserve this ownership pattern:

- `docling-slim` defines the real scripts because it owns the implementation modules.
- `docling` re-declares identical scripts only to make tool installation expose them.
- Do not make the full package ship its own duplicate `docling/` module; that reintroduces package collision risk.

## Package Collision Hazards

Avoid changes that cause both wheels to install the same `docling/` package tree. The full package should remain dependency-only for Python modules, with build configuration that bypasses wheel package selection and includes only package metadata/readme in source distributions.

Collision symptoms include:

- Installing `docling` hides or overwrites modules from `docling-slim`.
- CLI scripts import a different module tree depending on install order.
- Local workspace tests pass but wheel/tool installation fails.

When touching packaging, validate both import behavior and script availability in a clean environment if possible.

## Dependency Drift Checklist

Before finishing dependency or extras work:

1. Confirm dependency belongs in base, a granular extra, a convenience bundle, a dependency group, or the full-package re-export.
2. Check environment markers for Python version, platform, CPU/GPU, and macOS arm64-only packages.
3. Keep optional ML/VLM/ASR/backends optional; do not move heavy model dependencies into the base package accidentally.
4. Update docs or CLI help when installation guidance changes.
5. Run dependency locking/check commands appropriate for the checkout before finalizing.
