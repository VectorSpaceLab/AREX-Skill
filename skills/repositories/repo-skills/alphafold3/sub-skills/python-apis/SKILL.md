---
name: python-apis
description: "Use when coding against AlphaFold 3 Python internals for input
  parsing, data pipeline/model config construction, model runner hooks,
  structure/mmCIF utilities, or generated resource inspection without running
  full inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold 3 Python APIs

Use this sub-skill when a task needs Python-level AlphaFold 3 internals rather than command-line operation.

## Route Here For

- Inspecting `alphafold3` package availability, version, JSON dialect/version, and key callable signatures.
- Parsing or emitting fold-input JSON with `alphafold3.common.folding_input.Input`.
- Constructing data-pipeline configuration objects or calling pipeline-only helpers safely.
- Building model configuration objects, wiring `ModelRunner`, or understanding inference hooks without accidentally starting model inference.
- Working with `alphafold3.structure` and mmCIF/CCD utilities at a high level.
- Diagnosing generated CCD pickle resources, package-data, C++ extension, JAX/GPU, model-directory, or resource-generation failures.

## Do Not Handle Here

- For command-line prediction recipes, flags, output directory behavior, and split data-pipeline/inference runs, use `../running-predictions/`.
- For AlphaFold 3 JSON schema, ligand/user CCD authoring, custom MSA/template fields, and input examples, use `../input-preparation/`.
- For ranking scores, confidence JSON, embeddings, distograms, and output interpretation, use `../output-interpretation/`.

## Primary References

- Start with `references/api-reference.md` for verified signatures, safe snippets, and API caveats.
- Use `references/troubleshooting.md` for import/resource/JAX/model-dir failure modes.
- Run `scripts/inspect_alphafold3_api.py --help` to inspect an installed AlphaFold 3 package without performing inference.

## Safety Rules

- Treat most Python APIs outside the JSON input classes as internal implementation surfaces; verify signatures against the installed package before generating durable code.
- Never instantiate `ModelRunner.run_inference`, `predict_structure`, or `process_fold_input` with a non-`None` model runner during harmless inspection.
- Prefer pipeline-only or parse-only examples when no model weights, GPU, databases, or external binaries are explicitly available.
