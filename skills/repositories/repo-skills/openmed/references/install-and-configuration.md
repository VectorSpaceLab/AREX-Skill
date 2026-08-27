# Install and configuration

Read this before changing an OpenMed environment, selecting extras, enabling
optional backends, or running local model workflows.

## Basic install choices

```bash
pip install openmed
pip install "openmed[cli]"
pip install "openmed[service,mcp]"
pip install "openmed[hf]"
pip install "openmed[multimodal]"
```

For repository development use the repo's preferred tooling, for example an
editable install with development extras, then run the focused tests that match
your change. For package use, prefer targeted extras over installing every
optional dependency.

## Minimal no-download smoke

A safe smoke should import the package, inspect the CLI, and use fixture loaders
rather than downloading models:

```bash
python scripts/check_openmed_environment.py --json
python scripts/openmed_quickstart_smoke.py --json
```

If you run these from a copied skill directory, ensure `openmed` is installed in
the current Python environment.

## Model and cache configuration

Use `OpenMedConfig` and `ModelLoader` when you need explicit control over model
paths, cache behavior, backend selection, or offline operation. Recommended
pattern:

1. Decide whether model artifacts may be downloaded.
2. If downloads are allowed, prefetch during setup rather than at PHI runtime.
3. If downloads are not allowed, set local-only/offline behavior and point to a
   pre-staged local model path or cache.
4. Verify model and tokenizer assets before processing PHI.
5. Release or unload cached models when a long-running process no longer needs
   them.

`include_remote` on listing helpers is retained for compatibility; live remote
discovery should not be assumed.

## Privacy-safe configuration

- Default to local processing after artifacts are present.
- Do not enable telemetry, remote providers, or external integrations for PHI
  workflows unless the user explicitly accepts the boundary.
- Do not store raw PHI in result caches, temp files, audit reports, logs, or
  generated examples.
- Prefer offsets, hashes, counts, risk scores, source provenance, and synthetic
  examples in artifacts.
- Keep re-identification mappings and surrogate vault keys separate from
  de-identified outputs.

## Backend and extra selection

| Task | Typical extras/backends |
| --- | --- |
| CLI help and basic Python APIs | base or `cli` |
| REST/gRPC/GraphQL service | `service` |
| MCP tool server | `mcp` |
| Hugging Face-backed NER or model prefetch | `hf`, maybe `gliner` |
| Apple Silicon / Swift / MLX | `mlx` and platform toolchain |
| CoreML export | `coreml` and Apple tooling where applicable |
| ONNX / Android / browser export | `onnx`, `onnx-runtime`, platform toolchains |
| Real OCR or document readers | `multimodal`; `ocr-paddle` only for PaddleOCR |
| Tables and risk workflows | `pandas`, `polars`, `duckdb`, or selected distributed extra |
| Service/EHR/framework connectors | selected `fhir`, `openmrs`, `langchain`, `haystack`, `llamaindex`, `spacy`, SQL/distributed extras |

Do not treat CPU importability as proof of CUDA, MPS, CoreML, ONNX Runtime,
OpenVINO, OCR, Android, Swift, or browser behavior. Probe the selected backend
and record unavailable optional paths as limitations.

## Restricted assets

OpenMed source code is permissively licensed, but many model, terminology, and
benchmark assets have independent terms. Do not bundle or commit restricted
assets such as UMLS, SNOMED CT, CPT, MIMIC, i2b2, n2c2, or private EHR data.
Use user-supplied keys, local snapshots, or out-of-process bridges and document
what was not verified.

## Focused validation examples

- Import/package: `python -c "import openmed; print(openmed.__version__)"`.
- CLI: `openmed --help` and then the subcommand's `--help`.
- Privacy: use a synthetic note and assert expected labels/spans.
- Clinical: use a fixture loader or local model and assert offsets/labels.
- Structured risk: use a tiny synthetic table and assert risk thresholds.
- Service/MCP: import app/tool registry or run schema/help checks before
  starting a listener.
- Backend: run the backend probe script before model downloads or exports.
