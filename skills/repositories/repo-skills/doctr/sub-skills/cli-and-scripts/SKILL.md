---
name: cli-and-scripts
description: "Use docTR's installed OCR CLI and safe bundled helper scripts for
  single-document and batch OCR."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI and Scripts

Use this sub-skill when the task is about running docTR from a shell instead of writing a custom Python pipeline.

## Route here for

- Exact `doctr-cli` arguments, defaults, JSON output behavior, and parser/runtime errors.
- Single-file OCR with a safe helper that can run offline with `--no-pretrained` or load trained weights with `--pretrained`.
- Batch OCR over a file or directory with explicit `txt`, `json`, or `xml` output.
- CLI/script troubleshooting: missing entry point, import failures, unsupported inputs, failed output writes, model-name errors, or model download/cache issues.

## Runtime files

- Read [references/cli-reference.md](references/cli-reference.md) for the installed `doctr-cli` command, flags, defaults, output schema, and error behavior.
- Read [references/script-adaptations.md](references/script-adaptations.md) for the bundled helpers and how they differ from the repo-maintained examples.
- Read [references/troubleshooting.md](references/troubleshooting.md) when commands fail.
- Run [scripts/doctr_quick_ocr.py](scripts/doctr_quick_ocr.py) for one PDF or image.
- Run [scripts/doctr_batch_ocr.py](scripts/doctr_batch_ocr.py) for a file or directory and `txt`/`json`/`xml` outputs.
- Run [scripts/doctr_cli_env.py](scripts/doctr_cli_env.py) for a safe CLI/import/backend diagnostic report.

## Boundaries

- For equivalent Python API design, route to the core OCR/KIE sub-skill rather than expanding CLI snippets here.
- For document object schemas, rendering, hOCR/XML interpretation, Markdown/HTML export, and table/KIE result semantics, route to the document IO/export sub-skill.
- For training, evaluation, datasets, or benchmark scripts, route to the datasets/training/evaluation sub-skill.

## Safety defaults

The bundled helpers default to `--no-pretrained`, which avoids intentional model-weight downloads and is useful for parser/import/offline smoke checks. Use `--pretrained` only when the runtime is allowed to load or download trained model weights and cache them through the installed backend.
