# Hail Package Map

## Purpose

Use this reference to identify the right Hail sub-skill, package surface, and bundled helper before answering a user request.

## Public Surfaces

| Surface | Import or command | Use for | Skill owner |
| --- | --- | --- | --- |
| Hail Query context | `import hail as hl`; `hl.init`, `hl.init_local`, `hl.init_spark`, `hl.init_batch` | Starting/stopping Hail, backend selection, logs/tmp/reference config, requester-pays, debug info | `sub-skills/setup-and-backends/` |
| Hail Tables and expressions | `hl.Table`, `hl.import_table`, `hl.read_table`, `hl.agg`, expression methods | Tabular ETL, keyed joins, row aggregations, schemas, exports, expression-scope debugging | `sub-skills/tables-and-expressions/` |
| Dense genomics MatrixTables | `hl.MatrixTable`, `hl.import_vcf`, `hl.variant_qc`, `hl.sample_qc`, `hl.linear_regression_rows`, `hl.vep` | VCF/PLINK/BGEN import, QC, annotations, PCA, association, VEP, genetics types | `sub-skills/genomics-analysis/` |
| Sparse sequencing VDS | `hl.vds`, `VariantDataset`, `hl.vds.read_vds`, `hl.vds.new_combiner` | GVCF combining, sparse reference/variant data, local alleles, VDS QC, dense conversion | `sub-skills/variant-datasets/` |
| Hail Batch Python API | `import hailtop.batch as hb`, `hb.Batch`, `LocalBackend`, `ServiceBackend` | DAG construction, local/service execution, resources, files, dependencies, scatter/gather | `sub-skills/batch-and-cli/` |
| Hail command line | `hailctl` or `python -m hailtop.hailctl` | Version/config/auth/batch/dataproc/hdinsight/describe commands | `sub-skills/batch-and-cli/` |
| Hailtop utilities | `hailtop.fs`, `hailtop.aiotools`, `hailtop.config`, `hailtop.auth` | Support APIs used by Hail Batch, cloud FS, auth/config helpers | Usually `sub-skills/batch-and-cli/`; setup overlap in `sub-skills/setup-and-backends/` |

## Common Routing Decisions

- If the user says `Table`, `group_by`, `hl.agg`, keyed joins, delimited text, or expression index errors, start with `sub-skills/tables-and-expressions/SKILL.md`.
- If the user says VCF, PLINK, BGEN, genotype, `MatrixTable`, variant/sample QC, association test, PCA, VEP, `Locus`, or `Call`, start with `sub-skills/genomics-analysis/SKILL.md`.
- If the user says GVCF, VDS, sparse, `VariantDataset`, `LGT`, `LA`, `END`, combiner, or `to_dense_mt`, start with `sub-skills/variant-datasets/SKILL.md`.
- If the user says Batch, DAG, jobs, `hailtop.batch`, `LocalBackend`, `ServiceBackend`, `hailctl`, Dataproc, HDInsight, billing project, or remote tmpdir, start with `sub-skills/batch-and-cli/SKILL.md`.
- If the user says installation, `hl.init`, Java, Spark, Py4J, JAR, Python version, requester-pays config, backend selection, import shadowing, or version mismatch, start with `sub-skills/setup-and-backends/SKILL.md`.

## Selected Capabilities Outside This Skill

Hail's monorepo includes service deployments, Kubernetes manifests, CI systems, websites, release tooling, Docker base images, and maintainer scripts. Those are intentionally outside this user-facing package skill unless they appear through the public `hail`, `hailtop`, or packaged `hailctl` surfaces.

## Script Ownership

| Bundled script | Owner | Safe default |
| --- | --- | --- |
| `scripts/check_hail_environment.py` | Root/setup shared diagnostic | Read-only diagnostics; no backend initialization unless requested |
| `sub-skills/tables-and-expressions/scripts/table_pipeline_template.py` | Tables and expressions | Dry-run/template mode |
| `sub-skills/genomics-analysis/scripts/matrixtable_recipe_template.py` | Genomics analysis | Dry-run/template mode |
| `sub-skills/variant-datasets/scripts/vds_recipe_template.py` | Variant datasets | Dry-run/template mode |
| `sub-skills/batch-and-cli/scripts/batch_local_smoke.py` | Batch and CLI | Help/dry-run unless `--run` is selected |
