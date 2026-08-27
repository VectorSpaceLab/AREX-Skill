---
name: onnx
description: "Routes ONNX model-format, Python API, validation,
  reference-evaluator, backend-test, and operator-spec maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ONNX

Use this repo skill when a task involves the `onnx` Python package, ONNX `ModelProto`/`GraphProto`/`TensorProto` files, ONNX model serialization, checker or shape inference failures, ONNX text syntax, `ReferenceEvaluator`, backend test data, or maintainer work on ONNX operator schemas and generated artifacts.

ONNX is a runtime-agnostic model interchange format. This skill focuses on the ONNX package and standard itself, not on exporter-specific framework code or hardware-runtime inference engines.

## Start Here

1. Read `references/repo-provenance.md` before deciding whether this skill is current for a particular ONNX checkout or release.
2. Install released ONNX for ordinary model work:

   ```bash
   python -m pip install onnx
   # optional, only for image/reference workflows that need Pillow:
   python -m pip install 'onnx[reference]'
   ```

3. For an ONNX source checkout, prefer the repository's reproducible build path when available:

   ```bash
   pixi run install
   pixi run pytest
   ```

   Otherwise use an isolated Python environment and `python -m pip install -e . -v`. C++ changes require rebuilding.
4. Run `python scripts/onnx_environment_smoke.py --help`, then `python scripts/onnx_environment_smoke.py` to verify that the active Python can import ONNX, build a tiny model, check it, infer shapes, and run the reference evaluator.
5. Read `references/troubleshooting.md` for cross-cutting install/import, optional dependency, data-file, CLI, and workflow failures.

## Route by Task

| User task | Read |
| --- | --- |
| Create a model, build nodes/graphs/tensors, save/load `*.onnx`, inspect model IO, use JSON/textproto/onnxtxt/protobuf formats, compose/extract models, or manage external data and large tensors | `sub-skills/model-authoring/SKILL.md` |
| Validate a model or node, diagnose `ValidationError`, run shape/type inference, parse or print ONNX text, convert opsets, inline functions, or use `check-model`/`check-node` | `sub-skills/validation-and-conversion/SKILL.md` |
| Execute a model with ONNX's pure-Python `ReferenceEvaluator`, compare expected outputs, inspect reference op behavior, implement a backend interface, or generate bounded backend-test data | `sub-skills/reference-and-backend-tests/SKILL.md` |
| Add or update an ONNX operator, write a function body, add C++ shape inference, edit `.in.proto` sources, update reference ops/node tests/version adapters, regenerate docs/protos, or run maintainer gates | `sub-skills/operator-spec-maintenance/SKILL.md` |

## Common Routing Decisions

- If the user has a broken ONNX file and asks whether it is legal, start with `validation-and-conversion` before editing the model.
- If the user asks how to create or transform an ONNX file, start with `model-authoring`; then call `validation-and-conversion` for checker and shape-inference gates.
- If the user asks whether an ONNX model computes the expected values without a framework runtime, start with `reference-and-backend-tests`.
- If the user is modifying operator definitions, shape inference, tests, generated docs, or protobuf schemas in an ONNX checkout, start with `operator-spec-maintenance` even when Python API checks are also needed.
- If a task is about PyTorch, TensorFlow, scikit-learn, ONNX Runtime, TensorRT, or OpenVINO export/execution behavior, use this ONNX skill only for the standard-format artifact and validation layer; use the exporter/runtime skill for framework-specific behavior.

## Shared References

- `references/troubleshooting.md` covers install/import, package extras, CLI/API misuse, external data, large-model, build, and optional backend failure surfaces.
- `references/build-test-troubleshooting.md` explains ONNX build/test/lint choices for future source-checkout tasks.
- `references/repo-provenance.md` records the source snapshot and refresh baseline.
- `references/repo-routing-metadata.json` is structured router metadata for managed repo-skill import.

## Shared Script

- `scripts/onnx_environment_smoke.py` performs a source-free ONNX import/API smoke in the active Python environment. Use it after installing ONNX or before relying on this skill in a new environment.

## Safety and Scope Boundaries

- Do not treat a successful ONNX checker run as proof that a hardware runtime such as ONNX Runtime, TensorRT, OpenVINO, or a framework exporter will execute the model; ONNX validation proves format/schema consistency, not backend kernel support.
- Do not run large model downloads, backend real-model tests, fuzzers, release scripts, or long C++ builds unless the user explicitly needs that workflow.
- For models larger than the single-protobuf size limit, prefer path-based checker and shape-inference APIs and external data; do not load huge models into memory just to validate them.
- Treat optional dependencies such as Pillow for image-reference workflows as conditional, not baseline ONNX requirements.
- When editing ONNX itself, edit source-of-truth files and regenerate generated artifacts; do not hand-edit generated proto or generated operator documentation as the primary change.
