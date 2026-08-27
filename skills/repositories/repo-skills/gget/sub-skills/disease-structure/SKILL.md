---
name: disease-structure
description: "Use gget for gene-set enrichment, cancer cohort exploration, local
  COSMIC queries, Open Targets target annotations, and G2P residue/isoform maps;
  choose identifiers, filters, plots, files, and service/licensing boundaries
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Disease and structure annotations

Use this sub-skill when the task needs disease, cancer, enrichment, target,
residue, isoform, or protein-to-structure annotations from gget. It covers
`gget.enrichr`, `gget.cbio_search`, `gget.cbio_plot`, `gget.cosmic`,
`gget.opentargets`, and `gget.g2p`. These functions are wrappers around public
remote services or user-provided local files; results can change as upstream
databases are updated.

## Choose the operation

- **Gene-set enrichment:** start with `enrichr`. Use a supported shortcut only
  for human/mouse; use an exact library name for other species. Ensembl IDs
  require `ensembl=True`, and an Ensembl background requires
  `ensembl_bkg=True`. See [Enrichr](references/enrichr.md).
- **Cancer cohort discovery/heatmaps:** call `cbio_search` to obtain study IDs,
  inspect the returned IDs, then call `cbio_plot`. The latter downloads and
  caches cBioPortal data and writes a PNG; it does not return a result table.
  See [cBioPortal](references/cbio.md).
- **COSMIC:** query a local TSV with an exact, case-insensitive match. Download
  first only when the user has the required COSMIC account, permission, and
  storage. See [COSMIC](references/cosmic.md).
- **Target associations:** use `opentargets` with an Ensembl gene ID and one of
  its seven resources. Filters are exact equality on returned column names.
  See [Open Targets](references/opentargets.md).
- **Residue/isoform annotations:** use `g2p` for G2P `features`, `map`, or
  `alignment`. Resolve or pass the gene/UniProt pair explicitly; use residue
  filtering only for per-residue resources. See [G2P](references/g2p.md).

## Common execution contract

1. Record the identifier namespace and species before making a request. Keep
   Ensembl version suffixes when they are meaningful to the upstream service;
   note that Enrichr conversion strips a suffix and cBio/COSMIC have their own
   accession matching rules.
2. Run Python calls with `verbose=False` only after the first diagnostic run;
   retain the returned object and inspect its type, shape, columns, and a few
   rows before writing a downstream analysis.
3. Prefer explicit output paths in caller code. gget's `save=True` conventions
   differ by module; where a Python function has no save argument, write the
   returned DataFrame yourself.
4. Treat an empty DataFrame/list, `None`, a failed plot, a missing cache file,
   or a service error as an unresolved result—not evidence of no biology.
   Follow [troubleshooting](references/troubleshooting.md).
5. Do not place credentials in prompts, notebooks, committed code, or command
   history. COSMIC full downloads require an account and licensing review;
   public Enrichr, cBioPortal, Open Targets, G2P, and UniProt calls still need
   network access and may be rate-limited.

## Minimal Python recipes

```python
import gget

# Symbols, or Ensembl IDs with ensembl=True.
enrichment = gget.enrichr(["ACE2", "AGT", "AGTR1"], database="ontology")

# Search first; then inspect/select IDs rather than guessing a study ID.
studies = gget.cbio_search(["esophag", "ovarian"])
gget.cbio_plot(studies[:1], ["AKT1", "NOTCH3"], stratification="tissue")

# Existing, licensed/local COSMIC TSV only.
cosmic_rows = gget.cosmic("EGFR", cosmic_tsv_path="path/to/file.tsv", limit=20)

# Target disease associations; use resource-specific filters when narrowing.
diseases = gget.opentargets("ENSG00000169194", resource="diseases", limit=10)

# G2P feature rows at selected residues, with an explicit reviewed accession.
features = gget.g2p("BRCA1", uniprot_id="P38398", residues=[185, 1775, 1812])
```

Expected Python defaults are pandas DataFrames for Enrichr, COSMIC, Open
Targets, and G2P; Enrichr/COSMIC can return JSON-compatible lists with
`json=True`, and `cbio_plot` returns `True` after plotting. A remote failure can
instead raise, return an empty object, or return `None` according to the
module; never assume one universal error behavior.

## Boundaries and routing

- Route raw PDB retrieval, AlphaFold prediction, sequence retrieval, or direct
  structure download to the sequence-tools sub-skill. G2P `map` may expose a
  `PDB Ids List`, but this sub-skill only teaches the mapping.
- Route mutation sequence transformation and the detailed `gget mutate`
  workflow to specialized-workflows. COSMIC's `gget_mutate=True` export is a
  handoff, not a mutation-analysis recipe here.
- Open Targets' disease rows are EFO-mapped associations and may be phenotypes
  or measurements, not only MONDO diseases. G2P's public API does not expose
  the portal-only gnomAD, ClinVar, or HGMD overlays.
- For full signatures, resource schemas, cache/output names, constraints,
  and recovery steps, use the linked reference pages rather than guessing from
  a CLI help screen.

## Verification checklist

For a new workflow, verify: (a) the identifier namespace and species are
explicit; (b) the selected database/resource/filter names occur in the local
reference; (c) the returned type and required columns are checked; (d) output
paths are inspected; (e) a small deterministic or mocked case is retained; and
(f) network, account, license, cache, and truncation limits are recorded.

Difficult cases to test are an Enrichr Ensembl list with versioned IDs and a
small top-N assertion after conversion, plus an Open Targets diseases query
whose disease IDs seed a G2P feature request while clearly labeling the
portal-only variant-overlay gap. These cases are intentionally more demanding
than the original smoke tests.
