---
name: hail
description: "Use Hail for scalable genomic Tables, MatrixTables,
  VariantDatasets, Hail Batch DAGs, and hailctl setup or cloud workflow
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Hail

Use this repo skill when a task mentions Hail, `hail`, `hailtop`, `hailctl`, genomic `Table` or `MatrixTable` workflows, VCF/PLINK/BGEN imports, sparse GVCF or `VariantDataset` workflows, Hail Batch DAGs, or Hail backend setup and troubleshooting.

## First Checks

- Install the public `hail` distribution in Python 3.10 or newer, then verify `import hail as hl`, `import hailtop`, and `python -m hailtop.hailctl --help` from a neutral working directory.
- Read `references/repo-provenance.md` before deciding whether this skill is current for a local Hail checkout.
- Read `references/package-map.md` for the package layout, public APIs, and how the sub-skills divide responsibilities.
- Read `references/inspection-facts.md` for verified signatures, dependency constraints, packaged resources, and `hailctl` command families.
- Run or adapt `scripts/check_hail_environment.py` for safe import, version, CLI, Java, PySpark, packaged-resource, and optional local-init diagnostics.
- Use `references/troubleshooting.md` for cross-cutting install/import/backend issues before diving into workflow-specific troubleshooting.

## Route by User Goal

| User goal or signal | Read |
| --- | --- |
| Install Hail, debug `import hail`, choose `hl.init` backend, configure logs/tmp/reference/requester-pays, or fix Java/Spark/JAR startup failures | `sub-skills/setup-and-backends/SKILL.md` |
| Build Hail `Table` pipelines, import delimited data, key/join annotations, aggregate rows, inspect schemas, or fix expression-index errors | `sub-skills/tables-and-expressions/SKILL.md` |
| Work with dense genotype `MatrixTable`s, VCF/PLINK/BGEN import/export, sample/variant QC, splitting, PCA, association tests, VEP, loci, calls, or reference genomes | `sub-skills/genomics-analysis/SKILL.md` |
| Use `hail.vds`, sparse GVCF/VariantDataset workflows, local alleles, reference blocks, VDS combiner, `to_dense_mt`, or VDS QC | `sub-skills/variant-datasets/SKILL.md` |
| Build `hailtop.batch` DAGs, choose LocalBackend vs ServiceBackend, use `hailctl batch/config/auth/dataproc/hdinsight/describe`, or debug Batch/CLI cloud configuration | `sub-skills/batch-and-cli/SKILL.md` |

## Safe Workflow Defaults

- Start with setup: verify the installed package, working directory, Java/PySpark, `hailctl`, and backend choice before debugging workflow code.
- For local examples, prefer `backend='local'` or `hailtop.batch.LocalBackend`; treat cloud Batch, Dataproc, HDInsight, requester-pays data, and service billing as explicit user choices.
- Convert large external genomic inputs to Hail native formats (`.ht`, `.mt`, `.vds`) once, then iterate on native reads instead of reparsing VCF/PLINK/BGEN/GVCF inputs.
- Keep dense `MatrixTable` workflows and sparse VDS/GVCF workflows separate until a task explicitly asks for conversion.
- Use `describe()`, schema inspection, tiny previews, dry-run templates, and the bundled diagnostics before running expensive writes, exports, Batch submissions, or densification.

## Important Boundaries

- This skill covers user-facing Hail Python, Hailtop, Hail Batch, and packaged `hailctl` workflows. It does not cover Hail monorepo service deployment, release automation, Kubernetes infrastructure, or maintainer-only cloud operations.
- Do not tell future agents to open original repository docs, tests, notebooks, or scripts. Use the bundled references and scripts in this skill.
- Do not put credentials, billing projects, bucket names, private paths, or local environment details into reusable examples; use placeholders and ask the user for their values.
- Native repo tests and cloud examples are verification evidence, not runtime dependencies. Run only safe, short, credential-free native checks when verifying this skill.

## Bundled Helpers

- `scripts/check_hail_environment.py` inspects installed Hail/Hailtop imports, version metadata, `hailctl`, Java, PySpark, and packaged resources without initializing an expensive backend by default.
- `sub-skills/tables-and-expressions/scripts/table_pipeline_template.py` prints or dry-runs a self-contained Table pipeline template.
- `sub-skills/genomics-analysis/scripts/matrixtable_recipe_template.py` prints or dry-runs a dense MatrixTable analysis template.
- `sub-skills/variant-datasets/scripts/vds_recipe_template.py` prints or dry-runs a VDS workflow template.
- `sub-skills/batch-and-cli/scripts/batch_local_smoke.py` constructs a local-only Batch smoke/template and supports help or dry-run checks before execution.
