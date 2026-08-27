---
name: scikit-bio
description: "Use scikit-bio for bioinformatics sequences, alignments,
  phylogenetic trees, diversity metrics, biological tables, IO, metadata,
  distance statistics, ordination, compositional analysis, and embeddings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# scikit-bio

Use this repo skill when a task involves scikit-bio Python APIs for biological sequence data, phylogenetic trees, community ecology diversity, BIOM-style tables, bioinformatics file formats, sample metadata, distance-matrix statistics, ordination, compositional data analysis, or protein/sequence embeddings.

## Install and Import Check

scikit-bio is a Python package with public APIs rather than a command-line application. Prefer conda when compiled scientific dependencies are difficult to resolve:

```bash
conda install -c conda-forge scikit-bio
# or
python -m pip install scikit-bio
```

Minimal import check:

```bash
python - <<'PY'
import skbio
from skbio import DNA, TreeNode, DistanceMatrix
print(skbio.__version__, DNA("ACGT").gc_content(), TreeNode.read(["(a,b);"]).count(tips=True))
PY
```

Run `scripts/check_skbio_environment.py` when diagnosing installation, imports, or expected public API availability.

## Route by Task

- `sub-skills/io-metadata/SKILL.md` — read/write FASTA, FASTQ, Newick, BIOM, distance matrices, ordination, sample metadata, GFF3, GenBank/EMBL, BLAST tables, taxonomy dumps, and diagnose IO registry routes or metadata validation.
- `sub-skills/sequences-alignment/SKILL.md` — create and validate `Sequence`, `DNA`, `RNA`, `Protein`, `GeneticCode`, `SubstitutionMatrix`, `TabularMSA`, pairwise alignment, alignment scoring, and sequence-distance workflows.
- `sub-skills/trees-phylogeny/SKILL.md` — parse, navigate, write, build, compare, and repair `TreeNode` phylogenies, Newick trees, NJ/UPGMA/GME/BME construction, NNI, consensus, and tree constraints for diversity metrics.
- `sub-skills/diversity-tables/SKILL.md` — compute alpha/beta diversity, Faith PD, UniFrac, block beta diversity, metric discovery, table-like count inputs, BIOM-backed `Table`, and table augmentation.
- `sub-skills/statistics-ordination/SKILL.md` — use `DistanceMatrix`, PERMANOVA, ANOSIM, PERMDISP, Mantel, BioEnv, PCoA/CA/CCA/RDA, compositional transforms, ANCOM/ANCOM-BC, and embedding conversions.

## Common Workflows

- **Parse data then analyze**: start with `io-metadata`, then route parsed sequence/tree/table/distance objects to the owning sub-skill.
- **Sequence or alignment task**: start with `sequences-alignment`; use `io-metadata` only for file routes and `statistics-ordination` for downstream distance-matrix statistics.
- **Phylogenetic diversity task**: use `trees-phylogeny` to validate rooted trees, branch lengths, duplicate tips, and taxa order, then use `diversity-tables` for Faith PD or UniFrac.
- **Community ecology task**: use `diversity-tables` to create `Series` or `DistanceMatrix` outputs, then use `statistics-ordination` for PERMANOVA, ordination, or compositional follow-up.
- **Metadata-heavy task**: use `io-metadata` to load/filter/merge `SampleMetadata`, then pass aligned IDs to `statistics-ordination` or `diversity-tables`.

## Package Facts and Guardrails

- Requires Python 3.10 or newer and compiled scientific dependencies such as NumPy, pandas, SciPy, h5py, BIOM format, statsmodels, patsy, requests, decorator, natsort, and array-api-compat.
- Public top-level imports include `Sequence`, `DNA`, `RNA`, `Protein`, `GeneticCode`, `SubstitutionMatrix`, `DistanceMatrix`, `TabularMSA`, `TreeNode`, `nj`, `read`, `write`, `OrdinationResults`, `Table`, `SampleMetadata`, `get_config`, and `set_config`.
- Most workflows are pure Python API calls. Do not invent a scikit-bio CLI; use import/API smoke checks and focused pytest candidates when working in a repository checkout.
- Preserve ID alignment carefully. Many failures come from mismatched sample IDs, feature/taxon IDs, distance-matrix IDs, tree tip names, or metadata indexes.
- Keep validation enabled unless inputs have already been checked. `validate=False` may improve performance but can produce confusing downstream errors or invalid results.

## Cross-Cutting References

- `references/troubleshooting.md` for install/import issues, dependency conflicts, ID alignment, validation, optional backend, and no-CLI expectations.
- `references/repo-provenance.md` before deciding whether this generated skill matches a current scikit-bio checkout or should be refreshed.
- `references/repo-routing-metadata.json` contains structured `repo-skills-router` metadata used during managed import.
