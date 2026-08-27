---
name: setup-and-backends
description: "Install and import Hail, choose local/Spark/Batch query backends,
  configure initialization, and diagnose setup failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Hail Setup and Backends

Use this sub-skill when the task involves installing or importing `hail`, choosing a Hail Query backend, calling `hl.init`, `hl.init_local`, `hl.init_spark`, or `hl.init_batch`, configuring logs/tmp/reference/requester-pays options, stopping or reinitializing Hail, or diagnosing startup failures around Java, PySpark, Spark classpaths, generated Hail assets, backend JARs, package shadowing, or Batch query configuration.

## Start Here

- Read [Backend Setup](references/backend-setup.md) for backend choice, minimal initialization patterns, shutdown, tmp/log/reference/requester-pays configuration, and safe diagnostics.
- Read [API Reference](references/api-reference.md) for verified setup/backend signatures and parameter notes.
- Read [Troubleshooting](references/troubleshooting.md) for symptom-to-fix guidance on import, generated assets, Java/Spark/PySpark, tmp paths, requester-pays, and backend selection.
- For a read-only environment check, run or adapt the root diagnostic script at [check_hail_environment.py](../../scripts/check_hail_environment.py).
- For package ownership and cross-skill routing, use the root package map at [Package Map](../../references/package-map.md) and root [Troubleshooting](../../references/troubleshooting.md).

## Route Elsewhere

- Table imports, keyed joins, schema manipulation, aggregations, expression typing, and tabular exports belong in [Tables and Expressions](../tables-and-expressions/SKILL.md) after Hail is initialized.
- Dense `MatrixTable` genomic workflows, VCF/PLINK/BGEN import, QC, GWAS, PCA, VEP/Nirvana, and reference genome analysis belong in [Genomics Analysis](../genomics-analysis/SKILL.md).
- Sparse sequencing workflows using `hail.vds`, VDS combiner planning, sparse local allele fields, and dense/VDS conversions belong in [Variant Datasets](../variant-datasets/SKILL.md).
- Hail Batch DAG authoring, `hailtop.batch` `LocalBackend`/`ServiceBackend`, `hailctl batch`, and broad CLI/cloud operations belong in [Batch and CLI](../batch-and-cli/SKILL.md).

## Working Rules

- Prefer a normal installed `hail` distribution and run Python from a neutral working directory; avoid source checkout paths or local folders that can shadow the installed package.
- Choose `backend='local'`, `backend='spark'`, or `backend='batch'` explicitly when scripts must be reproducible; `hl.init` otherwise consults environment and `hailctl config` before defaulting.
- Call `hl.stop()` before changing backend, Spark configuration, tmp/log paths, requester-pays settings, or default reference in the same Python process; `idempotent=True` prevents repeated init errors but does not apply new configuration.
- Treat Python `>=3.10`, Java 11, PySpark/Spark 3.5.x compatibility, and matching Hail Python/JAR versions as setup prerequisites for backend startup.
- Keep credentials, billing projects, requester-pays projects, bucket names, and local paths as user-provided placeholders in reusable instructions.
