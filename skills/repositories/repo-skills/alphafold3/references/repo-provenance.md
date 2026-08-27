# Repo Provenance

schema: `disco.repo-provenance.v1`

This skill was generated from AlphaFold 3 repository evidence and live package inspection.

## Source Snapshot

- Skill id: `alphafold3`
- Source commit: `7b197fe859790fc3e04d03ea70dd0b9ba48881c9`
- Branch: `main`
- Exact tag: `v3.0.3`
- Working tree state at baseline: dirty because this generated `skills/` directory was added; no pre-existing tracked source modifications were detected.
- Package distribution: `alphafold3`
- Package version verified during inspection: `3.0.3`
- Remote URL: https://github.com/google-deepmind/alphafold3

## Evidence Paths

- `pyproject.toml` for package name, Python requirement, dependencies, build backend, and `build_data` entry point.
- `README.md` for project overview, first prediction command, model parameter terms, and high-level routing to docs.
- `docs/input.md` for AlphaFold 3 input JSON dialect, entities, server conversion, MSA/template paths, user CCD, and bonded atom pairs.
- `docs/output.md` for output directory structure, confidence metrics, embeddings, distograms, and ranking guidance.
- `docs/installation.md`, `docs/performance.md`, and `docs/model_parameters.md` for Docker/local setup, databases, GPU/runtime expectations, sharding, and model parameter constraints.
- `docs/known_issues.md` for CUDA capability 7.x and MSA discrepancy troubleshooting.
- `docs/metadata_antibody_antigen.md` for antibody-antigen metadata and confidence-ranking context.
- `run_alphafold.py` for CLI flags, stage controls, model/data path flags, command behavior, and Python runner functions.
- `run_alphafold_data_test.py` and `run_alphafold_test.py` for native candidate behavior, safe/unsafe test classification, output file expectations, and API examples.
- `src/alphafold3/` for source-backed APIs, data/model/structure modules, resource generation, constants, and test data.
- `fetch_databases.sh` and `src/alphafold3/scripts/*.sh` for database and SSD helper classification; these are not bundled as runnable skill scripts because they perform large network or host-storage operations.

## Live Inspection Summary

The inspection environment verified imports and signatures for `alphafold3`, `alphafold3.common.folding_input`, `alphafold3.data.pipeline`, `alphafold3.model.model_config`, and `alphafold3.structure`. It also confirmed selected signatures for `Input.from_json`, `DataPipelineConfig`, `DataPipeline.process`, `make_model_config`, `process_fold_input`, and `ModelRunner` methods.

Full inference and native data-pipeline tests were not run during skill creation because they require model parameters, full or miniature databases, HMMER binaries, GPU resources, and potentially large outputs. These remain classified as verification candidates rather than routine skill-generation checks.

## Refresh Triggers

Refresh this skill if any of these change:

- AlphaFold 3 JSON dialect version, entity fields, server conversion behavior, or `folding_input.Input` APIs.
- `run_alphafold.py` flags, defaults, stage controls, output naming, or model runner APIs.
- Package dependencies, Python requirement, build process, generated CCD resource handling, or JAX/CUDA expectations.
- Output file layout, confidence metric names, ranking formula, embeddings/distogram behavior, or compression flags.
- Installation, database, model parameter, Docker, or performance documentation.
