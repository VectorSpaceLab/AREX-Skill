---
name: specialized-analyses-and-graphics
description: "Routes Biopython motif, restriction enzyme, clustering, phenotype,
  population genetics, graphics, protein-analysis, and long-tail module tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Specialized Analyses and Graphics

Use this sub-skill when the user asks for Biopython workflows outside the core sequence/alignment/structure/database paths: motif/PWM/PSSM work, restriction enzyme analysis, clustering numeric data, phenotype microarray data, GenePop population genetics, GenomeDiagram or other graphics, protein property calculations, and long-tail modules such as CAPS, COMPASS, NMR, SCOP, Pathway, and Bio.Data constants.

## Route here for

- Creating, parsing, formatting, reverse-complementing, scoring, and scanning motifs with `Bio.motifs`, including JASPAR flat files and PWM/PSSM thresholds.
- Restriction enzyme searches, digests, enzyme batches, circular-vs-linear maps, and `Analysis` filters with `Bio.Restriction`.
- Numeric clustering with `Bio.Cluster`: distance matrices, k-means/medians, k-medoids, hierarchical clustering, SOMs, centroids, PCA, masks, and distance-code choices.
- Phenotype Microarray records with `Bio.phenotype`: `pm-json`/`pm-csv`, `PlateRecord`, `WellRecord`, interpolation, control subtraction, and optional curve fitting.
- Population-genetics data in GenePop format with `Bio.PopGen.GenePop`.
- `Bio.Graphics` and `Bio.Graphics.GenomeDiagram` diagrams when optional graphics dependencies are available.
- Protein summaries with `Bio.SeqUtils.ProtParam.ProteinAnalysis` and related `Bio.SeqUtils`/`Bio.Data` helpers.
- Long-tail Biopython modules where this sub-skill is the closest owner: `Bio.CAPS`, `Bio.Compass`, `Bio.NMR`, `Bio.SCOP`, and `Bio.Pathway`.

## Route away

- Core `Seq`, `SeqRecord`, `SeqFeature`, coordinate, translation, transcription, and basic `SeqUtils` tasks: use `../sequence-objects-and-features/SKILL.md`.
- File conversion with `SeqIO`, `AlignIO`, compression, indexing, or general format tables: use `../file-io-and-format-conversion/SKILL.md`.
- Alignments, BLAST/SearchIO, phylogenetic trees, and external aligner guidance: use `../alignment-search-and-phylogeny/SKILL.md`.
- PDB/mmCIF structure parsing, writing, superposition, and structure geometry: use `../structural-bioinformatics/SKILL.md`.
- Online JASPAR SQL database access, Entrez/KEGG/web services, BioSQL, credentials, and network policy: use `../web-databases-and-biosql/SKILL.md`.

## First steps

1. Identify the target module and whether the request is offline, network/database-backed, or graphics/optional-dependency-backed.
2. For motifs or restriction enzymes, read `references/motif-restriction-reference.md` before writing code.
3. For clustering, phenotype, GenePop, graphics, protein-analysis, or long-tail modules, read `references/specialized-workflows.md`.
4. If an import, format, optional dependency, JASPAR, graphics, fitting, or clustering error appears, read `references/troubleshooting.md`.
5. When validating an installed Biopython environment for this sub-skill, run the offline smoke check:

```bash
python scripts/specialized_modules_smoke.py
```

The smoke script uses only tiny in-memory data and avoids network calls, credentials, graphics rendering, database servers, and original repository files.

## Operating cautions

- Treat `Bio.Graphics`, ReportLab bitmap rendering, JASPAR SQL database access, phenotype curve fitting, and external/web tools as optional until explicitly available.
- Prefer deterministic clustering examples by supplying `initialid` for k-means/k-medians/k-medoids or by using hierarchical clustering/distance matrices.
- Keep motif `read()` for exactly-one-motif inputs and `parse()` for multi-motif inputs.
- Restriction cut locations are biological one-based cut positions; do not reinterpret them as zero-based Python slice offsets without documenting the conversion.
