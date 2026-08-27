# DeepKE repo-skill provenance

## Source baseline

- Schema: `disco.repo-provenance.v1`
- Repository: `zjunlp/DeepKE`
- Remote URL: `https://github.com/zjunlp/DeepKE.git`
- Branch observed during skill creation: `main`
- Source commit used as refresh baseline: `77083bf1d9ccc386c02d5b7643f4f4d2251f4c30`
- Working tree state at final generation: no tracked source modifications observed; untracked generated skill/review artifacts were present under `skills/`; temporary editable-install package metadata generated during environment preparation was removed from the final working tree.
- Python package name/version verified during inspection: `deepke==2.2.7`
- Generated skill id: `deepke`

## Evidence used

The skill was distilled from repository package metadata, README files, documentation index/config, example READMEs, source package imports, conversion scripts, and MCP wrapper files. Evidence areas included:

- Root package metadata and requirements.
- Standard NER/RE/AE/EE examples, few-shot/cross-domain/multimodal/document examples, and cnSchema docs.
- Data preparation helpers for NER weak supervision, RE distant supervision, and package-level data conversion.
- Triple-extraction examples for PRGC, PURE, ASP, cnSchema, and MT5/CCKS conversion.
- DeepKE-LLM examples including OneKE, InstructKGC, LLMICL, UnleashLLMRE, CodeKGC, and CPM-Bee.
- MCP tools including server/client behavior and TSV conversion.

## Inspection and verification baseline

A private Python 3.11 inspection environment verified the DeepKE package installation, dependency consistency, representative package imports, and pure helper smoke checks. CPU-only import/conversion checks were sufficient for safe bundled scripts and docs, but not for full GPU or large-model runtime claims.

Verified during creation:

- `python -m pip check` completed with no broken requirements in the inspection environment.
- Representative DeepKE imports succeeded for supervised NER/RE/AE/EE, triple-extraction packages, transformation helpers, and the MCP server module.
- Tiny smoke checks succeeded for weak-supervision preparation, distant-supervision labeling, MT5 prediction conversion, InstructKGC-style instruction conversion, and MCP TSV conversion.
- Generated bundled scripts were compiled and smoke-tested where they perform safe local conversions or diagnostics.

## Known unresolved runtime limits

The following were intentionally documented instead of executed because they require unavailable or user-controlled resources:

- CUDA/GPU-backed training or inference.
- ASP with NVIDIA Apex.
- MT5/DeepSpeed large-model training or prediction.
- OneKE and other local large-model checkpoint loading.
- OpenAI-compatible API calls and cost-bearing LLM prompting.
- Full native MCP server operation against trained DeepKE predictor checkpoints.
- Real datasets, large checkpoints, credentials, or remote downloads.

These limits do not block use of the generated skill for routing, planning, diagnostics, and safe conversion helpers. They do block any claim that every DeepKE model workflow was fully runtime-verified.

## Refresh guidance

Refresh this skill when:

- The source commit changes and examples/configs/dependencies are updated.
- DeepKE-LLM or MCP APIs change.
- The package version changes from `2.2.7`.
- New model families, extraction workflows, or data converters are added.
- A future environment verifies previously blocked GPU/Apex/DeepSpeed/API workflows and the runtime guidance should be upgraded.

Do not add private checkout paths, environment prefixes, API keys, or local checkpoint locations to this public provenance file.
