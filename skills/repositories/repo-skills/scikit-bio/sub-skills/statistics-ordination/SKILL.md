---
name: statistics-ordination
description: "Run scikit-bio distance-matrix statistics, ordination,
  compositional analyses, and biological embedding summaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# statistics-ordination

Use this sub-skill when a task asks to test group differences from a scikit-bio `DistanceMatrix`, compare distance matrices, run ordination, transform or test compositional data, or convert biological embedding vectors into distances, ordination, or tabular summaries.

## Read First

- `references/api-reference.md` for public signatures, return objects, accepted input shapes, and result fields.
- `references/workflows.md` for copy-ready patterns covering distance tests, metadata alignment, ordination, composition transforms, ANCOM-style tests, and embeddings.
- `references/troubleshooting.md` for matrix validity, ID mismatches, permutation reproducibility, PCoA warnings, compositional zeros, differential-abundance shape issues, and backend limits.
- `scripts/stats_ordination_smoke.py` for a deterministic smoke check covering `DistanceMatrix`, `permanova`, `pcoa`, composition zero handling, and `ProteinVector` embedding utilities.

## Route Here For

- Constructing or validating `PairwiseMatrix`, `SymmetricMatrix`, `DistanceMatrix`, and random distance matrices with `randdm`.
- Running `permanova`, `anosim`, `permdisp`, `mantel`, `pwmantel`, or `bioenv` on existing distance matrices and aligned metadata.
- Running `pcoa`, `pcoa_biplot`, `ca`, `cca`, `rda`, `mmvec`, or inspecting `OrdinationResults` fields.
- Applying `closure`, `multi_replace`, `clr`, `ilr`, `alr`, `rclr`, ANCOM, ANCOM-BC, structural-zero checks, or Dirichlet-multinomial differential-abundance tests.
- Creating `SequenceEmbedding`, `ProteinVector`, or related embedding vectors and converting them with `embed_vec_to_distances`, `embed_vec_to_ordination`, `embed_vec_to_dataframe`, or `embed_vec_to_numpy`.

## Boundaries

- For count-matrix generation, alpha/beta diversity computation, BIOM-style table preparation, and sample-by-feature orientation repairs, use `../diversity-tables/SKILL.md` first and return here once distances, compositions, or table-like inputs exist.
- For metadata file loading, ID normalization from external formats, or I/O registry details, use `../io-metadata/SKILL.md` before running statistics.
- For tree construction, rooting, tree-based basis construction, or phylogenetic interpretation, use `../trees-phylogeny/SKILL.md`.
- Keep this sub-skill focused on statistical analyses, ordination outputs, compositional transforms/tests, embedding summaries, and their diagnostics.

## Public Smoke Check

Run the bundled script from any working directory after installing scikit-bio:

```bash
python scripts/stats_ordination_smoke.py
python scripts/stats_ordination_smoke.py --permutations 9 --seed 7
python scripts/stats_ordination_smoke.py --help
```

The script imports public scikit-bio APIs only, constructs a small `DistanceMatrix`, runs PERMANOVA and PCoA, applies zero replacement before CLR, creates simple `ProteinVector` objects, and prints compact JSON.
