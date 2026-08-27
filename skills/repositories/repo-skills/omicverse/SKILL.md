---
name: omicverse
description: "OmicVerse multi-omics Python workflows for AnnData, single-cell,
  spatial, bulk, enrichment, metabolomics, proteomics, AIRR, genetics,
  alignment, MCP, CLI, and agentic analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# OmicVerse

Use this repo skill when a task involves the `omicverse` Python package, OmicVerse CLI/MCP/JARVIS tooling, or multi-omics workflows that combine AnnData, Scanpy-like preprocessing, single-cell interpretation, spatial transcriptomics, bulk/statistical omics, specialist bioinformatics domains, or agent-facing analysis services.

## Fast Triage

- If the request names `omicverse`, `ov`, `omicverse-mcp`, `ov-skill-seeker`, JARVIS, OpenClaw, OmicClaw, or an OmicVerse error, stay in this skill.
- If the task starts with `AnnData`, `.h5ad`, 10x MTX/H5, QC, HVG, PCA, neighbors, UMAP, plotting, reports, or `ov.read`, use [`sub-skills/core-analysis/SKILL.md`](sub-skills/core-analysis/SKILL.md).
- If the task asks for cell annotation, markers, SCSA, CellVote, GPTCelltype, batch correction, scVI/scANVI/totalVI, pseudobulk, trajectory, velocity, fate, SCENIC, CNV, perturbation, or lazy single-cell reports, use [`sub-skills/single-cell-workflows/SKILL.md`](sub-skills/single-cell-workflows/SKILL.md).
- If the task asks for bulk RNA-seq, differential expression, enrichment, signatures, metabolomics, proteomics, microbiome, longitudinal/time-course, PLS-DA, ORA/GSEA/GSVA/AUCell/UCell, or table-based omics statistics, use [`sub-skills/multiomics-statistics/SKILL.md`](sub-skills/multiomics-statistics/SKILL.md).
- If the task asks for Visium, Visium HD, Xenium, Nanostring, spatial coordinates/images, histology-to-ST, Tangram, STAGATE, CAST, STT, tissue zones, deconvolution, or spatial communication, use [`sub-skills/spatial-integration/SKILL.md`](sub-skills/spatial-integration/SKILL.md).
- If the task asks for AIRR/TCR/BCR, GWAS/eQTL/coloc/MR/scDRS/TWAS, molecular structures/drugs/docking, SRA/FASTQ/alignment, STAR/featureCounts, simpleaf/kb, 16S/DADA2/VSEARCH, MAFFT, or FastTree, use [`sub-skills/specialist-domains/SKILL.md`](sub-skills/specialist-domains/SKILL.md).
- If the task asks for `omicverse` CLI dispatch, `omicverse-mcp`, MCP phases/transports, registry manifests, JARVIS/gateway, smart agents, provider auth, harness/session behavior, or `ov-skill-seeker`, use [`sub-skills/agentic-and-mcp/SKILL.md`](sub-skills/agentic-and-mcp/SKILL.md).

## Install and Import Baseline

Use public installation commands in user-facing guidance; do not depend on a source checkout unless the user is explicitly developing OmicVerse.

```bash
pip install -U omicverse
python - <<'PY'
import omicverse as ov
print(ov.__version__)
print(ov.read, ov.set_seed)
PY
```

For optional surfaces, install only the needed extra or backend rather than every optional group:

```bash
pip install 'omicverse[mcp]'        # MCP server extras when not already installed
pip install 'omicverse[jarvis]'     # channel bots and JARVIS messaging
pip install 'omicverse[histo]'      # histology/spatial image stack, Python >=3.10
pip install 'omicverse[protein]'    # proteomics R-parity backends
pip install 'omicverse[genetics]'   # post-GWAS/eQTL/coloc/MR/TWAS backends
pip install 'omicverse[airr]'       # AIRR bulk/B-cell repertoire backends
pip install 'omicverse[mol]'        # structure/drug lookup helpers, Python >=3.10
pip install 'omicverse[mol-dock]'   # docking helpers; may need external Vina/RDKit stack
```

## Health Checks

Run the root health script first when the task is ambiguous or an import/CLI failure appears:

```bash
python scripts/check_omicverse_health.py --help
python scripts/check_omicverse_health.py --json
python scripts/check_omicverse_health.py --include-cli
```

Then use the nearest sub-skill checker for data-specific validation:

```bash
python sub-skills/core-analysis/scripts/inspect_core.py --json
python sub-skills/single-cell-workflows/scripts/check_single_cell_inputs.py --synthetic
python sub-skills/multiomics-statistics/scripts/check_multiomics_table.py --help
python sub-skills/spatial-integration/scripts/check_spatial_inputs.py --help
python sub-skills/specialist-domains/scripts/check_specialist_inputs.py --help
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --phase P0+P0.5 --limit 20
```

## Cross-Workflow Patterns

- Start with the data contract: `AnnData` slots for single-cell/spatial workflows, feature-by-sample tables plus metadata for bulk/metabol/protein/micro workflows, and domain-specific columns for AIRR/GWAS/alignment/molecular tasks.
- Validate before running expensive steps: check matrix dimensions, identifiers, metadata columns, coordinate/image files, optional backend imports, external binaries, network downloads, and credentials.
- Preserve raw data: keep raw counts in `.layers['counts']` or `.raw`; document any normalized/scaled layers used by downstream OmicVerse calls.
- Prefer CPU/tiny fixtures for first pass; treat GPU, histology WSI, docking, SRA downloads, and long training/inference as explicitly gated operations.
- Use OmicVerse registry/MCP after the analysis path is understood; registry tool names and schemas are helpful for agent clients but do not replace data validation.

## References

- [`references/troubleshooting.md`](references/troubleshooting.md): cross-cutting install/import, optional dependency, data/config, CLI/MCP, backend, and workflow failures.
- [`references/repo-provenance.md`](references/repo-provenance.md): source repository state, package version, and evidence paths used to generate this skill.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json): structured scenario metadata consumed by `repo-skills-router` during managed import.
