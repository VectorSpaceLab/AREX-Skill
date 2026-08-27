---
name: alphafold3
description: "Use this skill for AlphaFold 3 input preparation, prediction
  command planning, output interpretation, and Python API inspection. Covers the
  local AlphaFold 3 inference package, its JSON dialect, run_alphafold workflow,
  outputs, troubleshooting, and safe helper scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold 3

Use this repo skill when a user asks an agent to work with AlphaFold 3 inference workflows: preparing fold-input JSON, planning or debugging prediction runs, interpreting output directories, or writing safe Python tooling around the package.

AlphaFold 3 full prediction is operationally heavy. It requires Linux, model parameters obtained under the AlphaFold 3 terms, genetic databases, HMMER tools, compatible JAX/CUDA runtime, and an NVIDIA GPU for inference. Do not run full inference, download databases, mount disks, or fetch model weights unless the user explicitly asks and the environment is ready.

## Quick Route

- Use `sub-skills/input-preparation/` when constructing, validating, converting, or troubleshooting AlphaFold 3 input JSON.
- Use `sub-skills/running-predictions/` when planning Docker/local commands, split data-pipeline/inference runs, database/model paths, GPU flags, HMMER tools, or runtime preflight checks.
- Use `sub-skills/output-interpretation/` when inspecting result directories, ranking predictions, explaining confidence JSONs, embeddings, distograms, compression, or missing output files.
- Use `sub-skills/python-apis/` when coding against AlphaFold 3 internals such as `folding_input.Input`, `DataPipelineConfig`, `make_model_config`, `process_fold_input`, `ModelRunner`, or structure/mmCIF utilities.

## First Checks

For a local Python installation, start with a safe import/resource check rather than a prediction run:

```bash
python scripts/check_install.py
```

If the package imports fail, read `references/troubleshooting.md`. If the input JSON is the suspected problem, use `sub-skills/input-preparation/scripts/validate_fold_input.py`. If runtime paths or binaries are suspected, use `sub-skills/running-predictions/scripts/check_runtime_requirements.py`.

## Common Task Routing

| User asks for | Read first | Useful bundled helper |
| --- | --- | --- |
| “Create an AF3 JSON for a protein-ligand complex” | `sub-skills/input-preparation/SKILL.md` | `sub-skills/input-preparation/scripts/validate_fold_input.py` |
| “Convert/check AlphaFold Server JSON” | `sub-skills/input-preparation/references/input-json.md` | `sub-skills/input-preparation/scripts/validate_fold_input.py` |
| “Run only the data pipeline on CPU” | `sub-skills/running-predictions/SKILL.md` | `sub-skills/running-predictions/scripts/build_run_command.py` |
| “Debug missing HMMER/database/model paths” | `sub-skills/running-predictions/references/troubleshooting.md` | `sub-skills/running-predictions/scripts/check_runtime_requirements.py` |
| “Explain ranking_scores.csv or ipTM/pLDDT/PAE” | `sub-skills/output-interpretation/SKILL.md` | `sub-skills/output-interpretation/scripts/summarize_outputs.py` |
| “Use AlphaFold3 APIs in Python” | `sub-skills/python-apis/SKILL.md` | `sub-skills/python-apis/scripts/inspect_alphafold3_api.py` |

## Repository Facts

- Distribution/import name: `alphafold3`.
- Verified version for this skill baseline: `3.0.3`.
- Python requirement from package metadata: Python `>=3.12`.
- Main runner: `run_alphafold.py` in source distributions or containers.
- Console entry point: `build_data`, used to generate internal CCD pickle resources from packaged `components.cif` data when needed.
- Package dependencies include JAX, Haiku, RDKit, Tokamax, NumPy, zstandard, and compiled pybind extensions.

## Safety Boundaries

- Do not download full genetic databases automatically; documented full database setup is hundreds of GB.
- Do not assume model parameters are present or licensed; they must be obtained directly from Google DeepMind under the model parameter terms.
- Do not run GPU inference as a smoke test unless the user requests it and supplies weights, databases or precomputed features, and output space.
- Treat `fetch_databases.sh`, SSD mount/copy helpers, Docker build, and full `run_alphafold.py` runs as user-approved operational actions, not default validation.
- Prefer command generation, import checks, JSON validation, and output-tree inspection for safe agent assistance.

## References

- Read `references/capability-map.md` for the coverage map and ownership boundaries.
- Read `references/troubleshooting.md` for cross-cutting install/import/resource/runtime problems.
- Read `references/repo-provenance.md` to decide whether this skill may be stale against a changed AlphaFold 3 checkout.
