# Cross-Cutting Troubleshooting

## Purpose

Use this reference for Hail issues that cut across multiple sub-skills. Workflow-specific failures live in each sub-skill's own `references/troubleshooting.md`.

## Fast Triage

1. Run `scripts/check_hail_environment.py --json` or `scripts/check_hail_environment.py` from a neutral working directory.
2. Confirm `import hail as hl`, `hl.version()` or `hl.__version__`, `import hailtop`, and `python -m hailtop.hailctl --help` work.
3. Confirm Java and PySpark if the user will run a Hail Query backend.
4. Confirm the task's data/backend route: Table, dense MatrixTable, VDS, Batch/CLI, or setup.
5. Avoid cloud-mutating commands until the user provides credentials, billing project, bucket/tmpdir, and permission to incur cloud side effects.

## Route by Symptom

| Symptom | Likely owner | First reference |
| --- | --- | --- |
| `import hail` succeeds but version metadata or package resources are missing | Setup/import shadowing | `sub-skills/setup-and-backends/references/troubleshooting.md` |
| `hl.init()` fails with Java, Spark, Py4J, JAR, tmpdir, or version mismatch errors | Setup/backend startup | `sub-skills/setup-and-backends/references/troubleshooting.md` |
| `hailctl config` profile, auth, billing, remote tmpdir, Dataproc, HDInsight, or Batch CLI errors | Batch and CLI | `sub-skills/batch-and-cli/references/troubleshooting.md` |
| `hl.import_table` delimiter/header/type/key errors or expression index failures | Tables and expressions | `sub-skills/tables-and-expressions/references/troubleshooting.md` |
| VCF/BGEN/PLINK import, contig/reference mismatch, `split_multi_hts`, QC, association, or VEP failures | Dense genomics analysis | `sub-skills/genomics-analysis/references/troubleshooting.md` |
| VDS combiner, local alleles, `END`/`LEN`, sparse/dense conversion, or GVCF schema failures | Variant datasets | `sub-skills/variant-datasets/references/troubleshooting.md` |

## Common Causes and Fixes

| Problem | Cause | Recovery |
| --- | --- | --- |
| Partial `hail` import | Current directory or `PYTHONPATH` points at a raw source tree that shadows the installed package | Change to a neutral directory, clean `PYTHONPATH`, reinstall `hail`, and rerun the diagnostic. |
| Missing `hail.version` or `hailtop.version` | Raw checkout lacks generated build files | Use an installed wheel/package or the repository's build flow; do not treat missing generated source files as missing public APIs. |
| Hail Python/JAR version mismatch | Python package and backend JAR were built from different versions | Reinstall matching Hail package/JAR or rebuild both from the same source revision. |
| `pyspark`/`py4j` import failures | Runtime dependencies missing or incompatible | Install the public `hail` package dependencies; Hail expects Spark/PySpark 3.5.x for this baseline. |
| Java startup errors | Java unavailable, wrong major version, or Spark cannot launch | Install a compatible Java runtime, verify `java -version`, and retry a minimal `hl.init(backend='local')` only after import diagnostics pass. |
| Requester-pays reads fail | Missing billing project or bucket allow-list config | Configure requester-pays through `hl.init(..., gcs_requester_pays_configuration=...)` or `hailctl config` as appropriate. |
| Cloud command fails before submission | Missing credentials, billing project, remote tmpdir, region, or service access | Use `sub-skills/batch-and-cli/` to set up config/auth and classify command side effects before rerunning. |
| Large workflow appears to hang | Expensive parse, shuffle, densification, collect, or cloud job | Inspect schema/plan first; cache native formats; use filters/checkpoints; avoid densifying VDS or collecting entries unless necessary. |

## What Not To Do

- Do not instruct future agents to open original repository docs, tests, scripts, or notebooks to complete normal runtime tasks.
- Do not paste local environment prefixes, activation commands, absolute checkout paths, API keys, or private bucket names into reusable instructions.
- Do not run `hailctl dataproc start`, `hailctl hdinsight start`, `hailctl batch submit`, or service Batch jobs as diagnostics unless the user explicitly authorizes cloud side effects.
- Do not classify skipped native tests as passing. If a test requires a backend, cloud, credentials, or large data, record a skip reason and use a synthetic usability case to cover the behavior.
