---
name: secretflow
description: "Guides SecretFlow workflows for runtime setup, federated data
  containers, the component CLI, preprocessing/statistics/classical ML, and
  privacy-oriented deployment tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SecretFlow

SecretFlow is a unified framework for privacy-preserving data intelligence and
machine learning. Use this skill when the task mentions the `secretflow`
package, `sf.init`, `PYU`, `SPU`, `HEU`, `TEEU`, `VDataFrame`, `HDataFrame`,
`FedNdarray`, `component`, preprocessing, statistics, classical ML, PSI,
Kuscia, or TEE-style deployment.

## Start here

- Use Python 3.10 for the most reliable runtime coverage.
- Install `secretflow` in the target environment and keep `python -m pip check`
  clean.
- Minimal import check: `python -c "import secretflow as sf; print(sf.__version__)"`
- If you are validating an installed environment, run
  `scripts/check_secretflow_install.py`.
- Read `references/repo-provenance.md` when checking whether this skill still
  matches the repository snapshot that produced it.
- Read `references/troubleshooting.md` when the install, import, CLI, backend,
  or deployment path is failing.

## Route map

### `sub-skills/runtime-data/`
Use this route for local startup, device creation, reveal/to/wait behavior,
FedNdarray, HDataFrame, VDataFrame, MixDataFrame, CSV/ORC IO, and small local
simulation flows.

Typical triggers:
- `sf.init` with `local` or a simple `cluster_config`
- `PYU`, `SPU`, `HEU`, `TEEU`
- `reveal`, `to`, `wait`
- `read_csv`, `read_orc`, `partition`
- device-mismatch or direct-to-SPU/HEU errors

### `sub-skills/component-cli/`
Use this route for the component registry and the `secretflow component`
command family, component evaluation payloads, model export, serving model
inferencer, and plugin packaging.

Typical triggers:
- `secretflow component ls|inspect|translate|get_translation|run`
- `comp_eval`, `Registry`, `NodeEvalParam`, `StorageConfig`, `DistData`
- model export or serving package generation
- plugin entry-point or component registration questions

### `sub-skills/analytics/`
Use this route for preprocessing, statistics, score-card helpers, and direct
classical ML APIs.

Typical triggers:
- `StandardScaler`
- `psi_eval`, `table_statistics`, `categorical_statistics`, `ScoreCard`
- `SSGLM`, `SSRegression`, `FlLogisticRegressionMix`,
  `FlLogisticRegressionVertical`, `HESSLogisticRegression`
- `KMeans`, `GNB`, `GPC`, `KNNClassifer`, and related model workflows

### `sub-skills/privacy-orchestration/`
Use this route for PSI, secure aggregation/comparison, Kuscia, TEEU simulation,
and deployment-mode questions.

Typical triggers:
- `psi_df`, `psi_eval`, `SPUAggregator`, `PlainComparator`
- `KusciaTaskConfig`, `get_sf_cluster_config`, `convert_domain_data_to_individual_table`
- `TEEU`, `auth_manager`, Ray/Kuscia setup, simulation/production mode choice
- deployment and orchestration troubleshooting

## Working style

- Read the nearest sub-skill first, then cross-reference the shared root
  troubleshooting guidance when something fails.
- Keep runtime instructions inside this skill tree; do not rely on the original
  repository checkout being present later.
- For backend-specific work, prefer the smallest environment that can truthfully
  cover the selected task. CPU coverage is enough for the core local runtime
  and component CLI paths in this skill; advanced GPU, Kuscia, or TEE paths are
  routed to their own guidance.

## Companion files

- `references/repo-provenance.md` — source snapshot and refresh baseline.
- `references/repo-routing-metadata.json` — router metadata for repo-skills routing.
- `references/troubleshooting.md` — cross-cutting install/import/backend issues.
- `scripts/check_secretflow_install.py` — quick environment and API smoke check.
