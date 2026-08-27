# Sequence Workflows

These recipes use only public Biotite APIs and tiny local data patterns. Route raw sequence file parsing/writing details to `../../file-io-formats/SKILL.md` and remote data acquisition to `../../database-application/SKILL.md`.

## Construct And Validate Sequences

Use this when a prompt asks why a sequence fails, how to handle ambiguous bases, or how to build custom alphabets.

```python
import biotite.sequence as seq

try:
    dna = seq.NucleotideSequence("ACGTNN", ambiguous=True)
except seq.AlphabetError as error:
    raise ValueError("Sequence contains symbols outside the selected alphabet") from error

unambiguous = seq.NucleotideSequence("ACGT", ambiguous=False)
protein = seq.ProteinSequence("ACDEFGHIKLMNPQRSTVWY")
```

Checklist:

1. Normalize RNA input by replacing `U` with `T` if using `NucleotideSequence`.
2. Decide whether ambiguous nucleotide symbols are allowed; use `ambiguous=False` to force strict `A/C/G/T` input.
3. Catch `seq.AlphabetError` at construction or `Alphabet.encode()` time and report the invalid symbol set to the user.
4. Use `sequence.is_valid()` only after manually assigning `.code`; normal constructors already validate symbols.

## Translate ORFs Or A Complete CDS

Use `translate()` for ORF discovery and `translate(complete=True)` for a known coding sequence.

```python
import biotite.sequence as seq

dna = seq.NucleotideSequence("CATATGATGTATGCAATAGGGTGAATG")
proteins, positions = dna.translate()
complete = dna.translate(complete=True)

reverse_proteins, reverse_positions = dna.reverse().complement().translate()
```

Checklist:

1. For six-frame ORF search, run both forward and reverse-complement translations.
2. For GenBank/GFF-derived CDS features, extract the feature sequence first, rebuild as `NucleotideSequence` if needed, and then translate.
3. Use `protein.remove_stops()` before comparing to annotation qualifier translations that omit stop symbols.
4. Use `seq.CodonTable.load(name_or_id)` when the organism requires a non-standard genetic code.

## Work With Annotations And Feature Slices

Create small in-memory annotations or manipulate annotations loaded elsewhere.

```python
import biotite.sequence as seq

sequence = seq.NucleotideSequence("ATGGCGTACGATTAGAAAAAAA")
feature = seq.Feature("CDS", [seq.Location(1, 15)], qual={"gene": "toy"})
annotation = seq.Annotation([feature])
annotated = seq.AnnotatedSequence(annotation, sequence)
cds = annotated[feature]
protein = cds.translate(complete=True)
```

Checklist:

1. Treat `Location(first, last)` as inclusive biological coordinates.
2. Remember that `AnnotatedSequence[start:stop]` uses annotation coordinate positions, while `annotated.sequence[start:stop]` uses Python indexing.
3. After slicing annotations, inspect `location.defect` flags if boundaries matter.
4. Feature extraction handles multi-location and reverse-strand features; do not manually reverse-complement unless needed for custom logic.

## Pairwise Global Or Local Alignment

Use optimal alignment for short to moderate sequences where exact scoring matters.

```python
import biotite.sequence as seq
import biotite.sequence.align as align

seq1 = seq.ProteinSequence("BIQTITE")
seq2 = seq.ProteinSequence("IQLITE")
matrix = align.SubstitutionMatrix.std_protein_matrix()
alignment = align.align_optimal(
    seq1,
    seq2,
    matrix,
    gap_penalty=(-10, -1),
    terminal_penalty=False,
    local=False,
    max_number=1,
)[0]

score = align.score(alignment, matrix, gap_penalty=(-10, -1), terminal_penalty=False)
identity = align.get_sequence_identity(alignment)
```

Decision guide:

| Need | Choose |
| --- | --- |
| Align full sequences end-to-end | `local=False` |
| Find best matching subsequences | `local=True` |
| Penalize all terminal gaps | `terminal_penalty=True` |
| Allow unpenalized overhangs/semi-global behavior | `terminal_penalty=False` |
| Simple scoring model | `gap_penalty=-10` |
| Distinguish opening vs extension | `gap_penalty=(-10, -1)` |
| Avoid many equivalent alignments | `max_number=1` or a small cap |

Always match the substitution matrix to both sequence alphabets. Protein sequences should normally use `std_protein_matrix()`; nucleotide sequences should normally use `std_nucleotide_matrix()`.

## Build A K-mer Search Pipeline

Use this when optimal alignment is too slow or when a prompt asks for genome/database-like local search logic.

```python
import numpy as np
import biotite.sequence as seq
import biotite.sequence.align as align

reference = seq.ProteinSequence("GIPCGESCVFIPCISSVVGCSCKSKVCYLD")
query = seq.ProteinSequence("GIPCAESCVWIPCTVTALLGCSCKDKVCYLD")

table = align.KmerTable.from_sequences(k=3, sequences=[reference], ref_ids=[0])
matches = table.match(query)

# Keep one seed per diagonal before expensive extension.
diagonals = matches[:, 2] - matches[:, 0]
_, unique_indices = np.unique(diagonals, return_index=True)
seeds = matches[unique_indices]

matrix = align.SubstitutionMatrix.std_protein_matrix()
alignments = []
for query_pos, ref_id, ref_pos in seeds:
    alignment = align.align_local_ungapped(
        reference,
        query,
        matrix,
        seed=(ref_pos, query_pos),
        threshold=20,
    )
    if alignment.score >= 30:
        diagonal = query_pos - ref_pos
        alignments.append(
            align.align_banded(
                reference,
                query,
                matrix,
                gap_penalty=-5,
                band=(diagonal - 2, diagonal + 2),
                max_number=1,
            )[0]
        )
```

Checklist:

1. Pick `k` according to sensitivity/speed trade-offs.
2. Consider spaced k-mers or k-mer selectors for noisy data.
3. Deduplicate seed diagonals before running gapped alignment.
4. Use `BucketKmerTable` when memory matters more than direct indexing speed.
5. Use `EValueEstimator` only when the scoring scheme and database length assumptions are clear.

## Multiple Alignment And Guide Trees

Use Biotite's progressive MSA for strongly related sequences, small sets, or unusual sequence alphabets. For production-scale protein/nucleotide MSA, consider external application wrappers through `../../database-application/SKILL.md`.

```python
import numpy as np
import biotite.sequence as seq
import biotite.sequence.align as align
import biotite.sequence.phylo as phylo

sequences = [
    seq.ProteinSequence("GIPCGESCVFIPCISSVVGCSCKSKVCYLD"),
    seq.ProteinSequence("GIPCAESCVWIPCTVTALLGCSCKDKVCYLD"),
    seq.ProteinSequence("GIPCGESCVWIPCISSVIGCSCKSKVCYLD"),
]

matrix = align.SubstitutionMatrix.std_protein_matrix()
alignment, order, guide_tree, distance_matrix = align.align_multiple(
    sequences,
    matrix=matrix,
    gap_penalty=-5,
)
ordered_alignment = alignment[:, order.tolist()]
```

For a custom guide tree, build a square distance matrix and pass `guide_tree=phylo.upgma(distances)` or `guide_tree=phylo.neighbor_joining(distances)` to `align_multiple()`.

## Build A Profile, Consensus, Or Position-specific Matrix

Use this after you have a valid alignment.

```python
import biotite.sequence as seq
import biotite.sequence.align as align

alignment = align.Alignment.from_strings(
    ["CGTCAT--", "--TCATGC"],
    seq.NucleotideSequence,
)
profile = seq.SequenceProfile.from_alignment(alignment)
consensus = profile.to_consensus()
probabilities = profile.probability_matrix(pseudocount=1)
log_odds = profile.log_odds_matrix(pseudocount=1)
```

For a position-specific alignment against a profile:

```python
positional = seq.PositionalSequence(consensus)
matrix = align.SubstitutionMatrix(
    positional.alphabet,
    seq.NucleotideSequence.unambiguous_alphabet(),
    (log_odds * 10).astype(int),
)
query = seq.NucleotideSequence("CGTCATGC")
alignment_to_profile = align.align_optimal(
    positional,
    query,
    matrix,
    gap_penalty=-5,
    max_number=1,
)[0]
```

Checklist:

1. `SequenceProfile.from_alignment()` expects columns that align comparable positions.
2. `profile.symbols` counts symbols; `profile.gaps` counts gaps for the same positions.
3. Add pseudocounts before probabilities/log-odds when zero counts would break downstream scoring.
4. Ensure substitution matrix axes match the order of sequences passed to `align_optimal()`.

## Create Or Use Phylogenetic Trees

Use `phylo.Tree` for guide trees, dendrograms, and simple phylogenetic clustering.

```python
import numpy as np
import biotite.sequence.phylo as phylo

labels = ["A", "B", "C", "D"]
distances = np.array([
    [0.0, 1.0, 4.0, 5.0],
    [1.0, 0.0, 4.0, 5.0],
    [4.0, 4.0, 0.0, 2.0],
    [5.0, 5.0, 2.0, 0.0],
])
tree = phylo.upgma(distances)
newick = tree.to_newick(labels=labels, include_distance=True, round_distance=2)
```

Manual tree construction:

```python
leaf_a = phylo.TreeNode(index=0)
leaf_b = phylo.TreeNode(index=1)
root = phylo.TreeNode(children=(leaf_a, leaf_b), distances=(1.0, 1.0))
tree = phylo.Tree(root=root)
```

Checklist:

1. Keep labels/sequences outside the tree and refer to them by leaf index.
2. Do not reuse a `TreeNode` in two parents; nodes are immutable once attached.
3. Use `Tree.from_newick(newick, labels=labels)` when labels appear in Newick input.
4. Validate distance matrices for shape and symmetry before UPGMA/neighbor-joining.

## Sequence Graphics Data Preparation

Use this sub-skill to create the data objects and hand off plotting only when optional plotting is available.

```python
import matplotlib.pyplot as plt
import biotite.sequence.graphics as graphics

fig, ax = plt.subplots(figsize=(4, 1), constrained_layout=True)
graphics.plot_alignment_similarity_based(ax, alignment, matrix=matrix)
```

Graphics routing:

- Alignment visualization: create `align.Alignment` here, then call sequence graphics if `matplotlib` is installed.
- Feature maps/plasmid maps: create `seq.Annotation`/`seq.AnnotatedSequence` here; parser details belong to `../../file-io-formats/SKILL.md`.
- Sequence logos: create `seq.SequenceProfile` here.
- Dendrograms: create `phylo.Tree` here.
- Display backend, notebook rendering, PyMOL/RDKit/OpenMM, or plotting environment errors: use `../../interfaces-visualization/SKILL.md`.

## Adapted Source Example Decisions

The bundled smoke helper adapts safe local-literal ideas from Biotite's sequence tutorials and example gallery: short pairwise protein alignment, translation/profile checks, and profile consensus logic. Network-backed examples that fetch Entrez/UniProt/RCSB data, sequencing examples requiring external data files, and plot-heavy gallery scripts are reference-only; reproduce their concepts with local literals unless the user explicitly asks for network or plotting setup.
