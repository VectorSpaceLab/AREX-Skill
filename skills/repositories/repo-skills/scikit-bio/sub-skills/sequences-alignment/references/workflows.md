# Sequences and Alignment Workflows

These recipes are self-contained and use public scikit-bio APIs. They assume sequence data is already in memory. For file parsing, use the sibling I/O sub-skill first, then return here with constructed `Sequence`, `DNA`, `RNA`, `Protein`, or `TabularMSA` objects.

## Construct Biological Sequences Safely

```python
from skbio import DNA, Protein, RNA, Sequence

plain = Sequence("sample-001")
dna = DNA(
    "acgtNN--",
    metadata={"id": "read-1"},
    positional_metadata={"quality": [30, 31, 30, 29, 10, 10, 5, 5]},
    lowercase="was_lowercase",
)
rna = RNA("AUGCCACUUUAA")
protein = Protein("MPL*")

assert str(dna) == "ACGTNN--"
assert dna.positional_metadata["was_lowercase"].tolist()[:4] == [True] * 4
```

Checklist:

1. Choose `DNA`, `RNA`, or `Protein` when alphabet validation matters; choose `Sequence` only for unrestricted strings/tokens.
2. Keep `validate=True` by default. Use `validate=False` only when data is trusted or intentionally dirty and you will clean or revalidate before biological operations.
3. Match every positional metadata column length to `len(sequence)`.
4. Store identifiers in `metadata`, not only in variable names, if later `TabularMSA(minter="id")` is useful.

## Recover from Dirty or Degenerate Nucleotide Input

```python
from skbio import DNA

raw = "acgtryswkmBDHVN--"
seq = DNA(raw, lowercase=True)

if seq.has_degenerates():
    degenerate_positions = seq.degenerates().nonzero()[0].tolist()
    # Decide whether ambiguity is biologically meaningful or should be masked/removed.

ungapped = seq.degap()
```

For truly non-IUPAC characters, do not silence validation permanently. Stage and repair explicitly:

```python
from skbio import DNA

raw = "ACGTZ"
staged = DNA(raw, validate=False)
cleaned_text = str(staged).replace("Z", "N")
cleaned = DNA(cleaned_text, validate=True)
```

Tradeoff: `validate=False` lets construction proceed but can push failures into later `to_indices`, translation, alignment, or scoring steps. Prefer replacing known bad symbols with `N` for nucleotides or `X` for proteins, or use generic `Sequence` when the data is not biological.

## Slice While Preserving Annotation Intent

```python
from skbio import DNA

seq = DNA(
    "GATTACA",
    metadata={"id": "gene-1"},
    positional_metadata={"quality": [40, 39, 38, 37, 36, 35, 34]},
)
subseq = seq[1:5]

assert str(subseq) == "ATTA"
assert subseq.metadata["id"] == "gene-1"
assert subseq.positional_metadata["quality"].tolist() == [39, 38, 37, 36]
```

Sequence indexing returns sequence objects; use `str(seq[0])` if a raw character string is needed. Object metadata is shallow-copied, so avoid mutating shared nested values unless sharing is intentional.

## Transform and Translate Nucleotide Sequences

```python
from skbio import DNA, GeneticCode, RNA

dna = DNA("ATGCCACTTTAA", metadata={"id": "orf-1"})
rna = dna.transcribe()
protein = dna.translate(stop="ignore")
protein_required_stop = dna.translate(1, stop="require")

code = GeneticCode.from_ncbi(3)
yeast_mito = RNA("AUGCCACUUUAA").translate(code, stop="require")
frames = list(dna.translate_six_frames())

assert str(rna) == "AUGCCACUUUAA"
assert str(protein) == "MPL*"
assert len(frames) == 6
```

Translation guardrails:

- Use `GeneticCode.from_ncbi(table_id)` when the genetic code is part of the biological question.
- Choose `start`/`stop` policies deliberately: `"ignore"` is permissive, `"optional"` permits but does not require start/stop evidence, and `"require"` enforces it.
- Remove gaps before translation (`seq.degap()`) or fail early with a clear message.
- Translation preserves object metadata but drops positional metadata because codons collapse three nucleotide positions into one amino acid.

## Align Two Nucleotide Sequences

```python
from skbio import DNA
from skbio.alignment import TabularMSA, align_score, pair_align_nucl

seq1 = DNA("GATCGTC", metadata={"id": "query"})
seq2 = DNA("ATCGCTC", metadata={"id": "target"})
result = pair_align_nucl(seq1, seq2)
path = result.paths[0]
aligned_strings = path.to_aligned((seq1, seq2))
msa = TabularMSA.from_path_seqs(path, (seq1, seq2))
score_check = align_score((path, (seq1, seq2)), sub_score=(2, -3), gap_cost=(5, 2))

assert result.score == score_check
print(result.score, path.to_cigar(), aligned_strings)
```

Use `pair_align_nucl` when BLASTN-like scoring is acceptable. Switch to `pair_align` when you need local alignment, custom scoring, trim behavior, all optimal paths, or matrix retention:

```python
from skbio.alignment import pair_align

local = pair_align(seq1, seq2, mode="local", sub_score="NUC.4.4", gap_cost=3)
```

## Align Proteins with Matrix Scoring

```python
from skbio import Protein
from skbio.alignment import pair_align_prot

seq1 = Protein("MKRTLKGHFVQWC")
seq2 = Protein("MQMLKTHYAQTRN")
result = pair_align_prot(seq1, seq2, mode="local")

if result.paths:
    print(result.score, result.paths[0].to_aligned((seq1, seq2)))
```

`pair_align_prot` defaults to `sub_score="BLOSUM62"` and `gap_cost=(11, 1)`. If a protein sequence contains nonstandard characters, either map them to accepted degenerate/wildcard characters or build an explicit `SubstitutionMatrix` that covers them.

## Use `pair_align` for Search-Like Placement

```python
from skbio.alignment import pair_align

query = "ACCGT"
target = "AAACGCTACCGTCCGTAGACCGTGACCGTGCGAAGC"
result = pair_align(
    query,
    target,
    mode="global",
    sub_score=(1, -2),
    gap_cost=2.5,
    free_ends=(True, False),
    trim_ends=True,
    max_paths=None,
)
hits = [path.ranges[1].tolist() for path in result.paths]
```

Interpretation: `ranges[1]` gives 0-based half-open target coordinates for each optimal hit. Avoid `max_paths=None` on long repetitive sequences unless you are prepared for many optimal paths.

## Build and Index a TabularMSA

```python
from skbio import DNA
from skbio.alignment import AlignPath, TabularMSA

seqs = [
    DNA("CGTCGTGC", metadata={"id": "a"}),
    DNA("CA--GT-C", metadata={"id": "b"}),
    DNA("CGTCGT-T", metadata={"id": "c"}),
]
msa = TabularMSA(seqs, minter="id", positional_metadata={"quality": [90] * 8})

first_row = msa.loc["a"]
second_column = msa.iloc[:, 1]
consensus = msa.consensus()
path = AlignPath.from_tabular(msa)
roundtrip = TabularMSA.from_path_seqs(path, [seq.degap() for seq in seqs])

assert msa.shape.sequence == 3
assert msa.shape.position == 8
```

MSA construction fails unless all rows are same-type `GrammaredSequence` objects with the same length. If row labels come from metadata, verify all sequences have the `minter` key.

## Score Existing Alignments

```python
from skbio import DNA, Protein
from skbio.alignment import TabularMSA, align_score

dna_score = align_score(
    [DNA("CGGTCGTAACGCGTA---CA"), DNA("CAG--GTAAG-CATACCTCA")],
    sub_score=(2, -3),
    gap_cost=(5, 2),
)

protein_msa = TabularMSA([
    Protein("MKQ-PSV"),
    Protein("MKIDTS-"),
    Protein("MVIDPSS"),
])
protein_score = align_score(protein_msa, "BLOSUM62", (11, 1))
```

When validating `pair_align*` output, use `(path, (seq1, seq2))` and the exact same scoring parameters. Mismatched parameters are a common source of apparent score discrepancies.

## Compute Distances from an Alignment

```python
from skbio import DNA
from skbio.alignment import TabularMSA, align_dists

msa = TabularMSA([
    DNA("ATC-GTATCGG"),
    DNA("ATGCG--CCGC"),
    DNA("GTGCGTACGC-"),
], index=["a", "b", "c"])

dm = align_dists(msa, "jc69", shared_by_all=True)
```

`align_dists` is for producing a `DistanceMatrix` from aligned sequences. Use the statistics/ordination sub-skill for ordination, PERMANOVA, Mantel tests, or other downstream distance-matrix analyses; use the tree sub-skill for phylogenetic inference.

## Legacy Wrapper Maintenance

When maintaining old code that calls `global_pairwise_align_nucleotide`, `local_pairwise_align_protein`, or related wrappers:

1. Keep behavior unchanged if regression compatibility is required.
2. For new code, replace with `pair_align_nucl`, `pair_align_prot`, or `pair_align`.
3. Recheck gap-penalty conventions: old wrappers and some external tools may use a different affine opening/extension equation than `pair_align`.
4. Return modern `PairAlignPath`/`TabularMSA` workflows where possible, because the current docs prefer them.
