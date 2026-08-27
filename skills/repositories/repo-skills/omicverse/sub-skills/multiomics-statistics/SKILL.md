---
name: multiomics-statistics
description: "Use for OmicVerse bulk RNA-seq, enrichment/signature scoring,
  metabolomics, proteomics, microbiome, and statistical table workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Multiomics Statistics

Use this sub-skill when the task is table-centric rather than single-cell, spatial, alignment, genetics, AIRR, molecular, CLI, or MCP runtime work. Start at the [root routing skill](../../SKILL.md) if the task crosses domains.

## When to Use

- Bulk RNA-seq differential expression, offline ORA/GSEA, WGCNA-style modules, or time-course statistics with `ov.bulk`.
- Gene-set/signature scoring on AnnData or data frames with `ov.es.aucell`, `ov.es.ucell`, `ov.es.ora`, `ov.es.decouple`, `ov.es.decoupler`, or `ov.es.consensus`.
- Metabolomics workflows from wide peak tables or MetaboAnalyst-style CSVs through QC, normalization, differential testing, PLS-DA, pathway enrichment, and biomarker panels.
- Proteomics workflows from MaxQuant, DIA-NN, FragPipe, Olink, or wide intensity tables through QC, normalization, imputation, and differential testing.
- Microbiome workflows using samples-by-taxa AnnData for alpha/beta diversity, ordination, differential abundance, meta-analysis, and paired microbe-metabolite statistics.

## Route Elsewhere

- AnnData file reading, general preprocessing, plotting basics, report/provenance, and registry discovery: [`../core-analysis/SKILL.md`](../core-analysis/SKILL.md).
- Single-cell annotation, marker ranking, trajectory, velocity, cell communication, pseudobulk, and batch integration: [`../single-cell-workflows/SKILL.md`](../single-cell-workflows/SKILL.md).
- GWAS, eQTL, AIRR, molecular structure, raw FASTQ alignment, and external binary workflows: [`../specialist-domains/SKILL.md`](../specialist-domains/SKILL.md).
- Exposing analyses through the CLI, registry, MCP, JARVIS, or gateway runtime: [`../agentic-and-mcp/SKILL.md`](../agentic-and-mcp/SKILL.md).

## Reference Map

- [`references/statistical-workflows.md`](references/statistical-workflows.md): task recipes and validation checkpoints for bulk, enrichment, metabolomics, proteomics, and microbiome workflows.
- [`references/api-reference.md`](references/api-reference.md): compact API names, signatures, outputs, and optional backend mapping.
- [`references/data-formats.md`](references/data-formats.md): expected table orientations, AnnData slots, signature/network formats, and design metadata columns.
- [`references/troubleshooting.md`](references/troubleshooting.md): errors, optional dependency messages, network-fetcher caveats, and repair actions.
- [`scripts/check_multiomics_table.py`](scripts/check_multiomics_table.py): safe CSV/TSV schema checker for feature-by-sample matrices and sample metadata.

## Safe Operating Pattern

1. Identify the omics family and validate orientation before loading data. Most `ov.metabol`, `ov.protein`, and `ov.micro` APIs expect `AnnData` with samples in rows and features in columns; many `ov.bulk.pyDEG` inputs use genes in rows and samples in columns.
2. Check sample IDs and design columns before any statistical call. Run the bundled checker for matrix-plus-metadata workflows:

   ```bash
   python sub-skills/multiomics-statistics/scripts/check_multiomics_table.py matrix.tsv --metadata metadata.tsv --sample-id-column sample --required-metadata-cols group,batch
   ```

3. Choose a conservative local workflow first. Do not assume KEGG, HMDB, ChEBI, LION, Enrichr, or other remote resources are safe or available unless the user explicitly authorizes network access.
4. Use optional backends deliberately. If `pydeseq2`, `pymfuzz`, `pydeqms`, `pyimputelcmd`, `pyproda`, `pylipidr`, `pygoslin`, or `scikit-bio` is missing, either install the narrow extra required by the workflow or switch to a pure-Python fallback documented in the API reference.
5. Keep outputs as explicit tables. Record result column semantics such as `pvalue`, `padj`, `qvalue`, `log2FC`, `P.Value`, `adj.P.Val`, `score_<method>`, and `padj_<method>` before handing off to plotting or reporting.
