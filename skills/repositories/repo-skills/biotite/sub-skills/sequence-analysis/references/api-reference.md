# Sequence API Reference

This reference summarizes the Biotite sequence APIs future agents most often need. It is intentionally self-contained and does not require opening Biotite source docs or tests.

## Imports

```python
import numpy as np
import biotite.sequence as seq
import biotite.sequence.align as align
import biotite.sequence.phylo as phylo
```

Import `biotite.sequence.graphics as graphics` only for plotting helpers; most graphics functions require `matplotlib` and an axes object.

## Sequence Types And Alphabets

| Task | API | Notes |
| --- | --- | --- |
| DNA/RNA-like sequence | `seq.NucleotideSequence("ACGT")` | Stores DNA symbols. Replace RNA `U` with `T` before construction. Lowercase input is capitalized. |
| Ambiguous bases | `seq.NucleotideSequence("TANNCG")` | Automatically uses the ambiguous nucleotide alphabet when ambiguous symbols appear. Use `ambiguous=False` only when invalid ambiguous symbols should fail. |
| Protein sequence | `seq.ProteinSequence("ACDE")` | Supports the 20 standard amino acids plus ambiguous amino acid symbols and a stop symbol. |
| Custom sequence | `seq.GeneralSequence(seq.Alphabet([...]), symbols)` | Use for arbitrary immutable/hashable symbols without subclassing `seq.Sequence`. |
| Custom class | subclass `seq.Sequence` and implement `get_alphabet()` | Use only if type-specific methods are needed. |
| Alphabet encoding | `alphabet.encode(symbol)`, `alphabet.encode_multiple(symbols)` | Converts symbols to integer codes. Invalid symbols raise `seq.AlphabetError`. |
| Alphabet decoding | `alphabet.decode(code)`, `alphabet.decode_multiple(codes)` | Converts integer codes back to symbols. Out-of-range codes raise `seq.AlphabetError`. |
| Common alphabet | `seq.common_alphabet([alph1, alph2])` | Returns a common alphabet when one extends the other; returns `None` if incompatible. |

Sequence objects store integer codes in `.code` and decode symbols lazily through `.symbols` or `str(sequence)`. Most user workflows should use symbols and constructors, not mutate `.code` directly, unless building advanced vectorized code.

Useful sequence operations:

```python
dna = seq.NucleotideSequence("tacagtt")
rev_comp = dna.reverse().complement()
subseq = dna[1:5]
dna_copy = dna.copy()
dna_copy[0] = "A"
frequency = dna.get_symbol_frequency()
```

## Translation And Codons

| Task | API | Notes |
| --- | --- | --- |
| Find ORFs in three forward frames | `proteins, positions = dna.translate()` | Returns protein sequences and `(start, stop)` base positions. |
| Complete one-frame translation | `protein = dna.translate(complete=True)` | Ignores start/stop ORF search and translates the full sequence. |
| Six-frame ORF scan | call `translate()` on `dna` and `dna.reverse().complement()` | Reverse-strand positions are relative to the reverse-complement sequence unless remapped by the caller. |
| Default codon table | `seq.CodonTable.default_table()` | Biotite's default follows NCBI Standard with only `ATG` as start codon. |
| Official NCBI table | `seq.CodonTable.load("Yeast Mitochondrial")` or `seq.CodonTable.load(11)` | Accepts table name or ID. |
| Codon lookup | `table["TAC"]`, `table["Y"]` | Codon returns amino acid; amino acid returns encoding codons. |
| Protein letter conversion | `seq.ProteinSequence.convert_letter_1to3("A")` | Also use corresponding 3-to-1 utilities when normalizing residue labels. |

If a translated CDS uses ambiguous nucleotide symbols, rebuild the extracted CDS as an unambiguous `NucleotideSequence` after trimming ambiguous flanks, or intentionally keep the ambiguous alphabet and handle ambiguous translation behavior.

## Annotations

| Object | Construction | Key behavior |
| --- | --- | --- |
| `seq.Location` | `seq.Location(first, last, strand=...)` | Biological positions are inclusive. Strand can be forward or reverse. |
| `seq.Feature` | `seq.Feature("CDS", [location], qual={...})` | Stores feature key, one or more locations, and qualifiers. |
| `seq.Annotation` | `seq.Annotation([feature1, feature2])` | Iterable; supports concatenation and range slicing. |
| `seq.AnnotatedSequence` | `seq.AnnotatedSequence(annotation, sequence)` | Combines features and sequence; supports slicing and feature extraction. |

Important indexing rule: `AnnotatedSequence` slicing uses base/residue positions from the annotation coordinate system, while `annotated.sequence[n:m]` uses normal Python sequence indices. A feature on the reverse strand returns the reverse-complemented sequence when used as an index.

Slicing an `Annotation` truncates features that overlap the requested interval and marks location defects such as `MISS_LEFT`, `MISS_RIGHT`, `BEYOND_LEFT`, or `BEYOND_RIGHT`. Do not silently discard defect flags when exact feature boundaries matter.

## Pairwise Alignment

Core signature verified from the installed API:

```python
align.align_optimal(
    seq1,
    seq2,
    matrix,
    gap_penalty=-10,
    terminal_penalty=True,
    local=False,
    max_number=1000,
)
```

| Task | API | Notes |
| --- | --- | --- |
| Standard protein matrix | `align.SubstitutionMatrix.std_protein_matrix()` | Standard BLOSUM62 matrix. |
| Standard nucleotide matrix | `align.SubstitutionMatrix.std_nucleotide_matrix()` | Use with nucleotide alphabets. |
| Load named matrix | `align.SubstitutionMatrix(alph1, alph2, "BLOSUM50")` | Matrix alphabets must match or extend sequence alphabets. |
| Custom score array | `align.SubstitutionMatrix(alph1, alph2, score_array)` | `score_array.shape == (len(alph1), len(alph2))`. |
| Global alignment | `align.align_optimal(a, b, matrix, local=False)` | Aligns full sequence extent. |
| Local alignment | `align.align_optimal(a, b, matrix, local=True)` | Returns highest-scoring local region(s). |
| Linear gap penalty | `gap_penalty=-10` | Same penalty for opening/extending a gap. |
| Affine gap penalty | `gap_penalty=(-10, -1)` | First value opens a gap; second extends it. |
| Terminal gaps | `terminal_penalty=False` | Treats leading/trailing gaps as unpenalized for semi-global style use. |
| Limit trace explosion | `max_number=1` | Avoids returning many equally optimal alignments. |
| Recompute score | `align.score(alignment, matrix, gap_penalty, terminal_penalty)` | Useful for alignments loaded from file formats. |
| Identity | `align.get_sequence_identity(alignment)` | Computes sequence identity over an alignment. |
| Symbols/codes | `align.get_symbols(alignment)`, `align.get_codes(alignment)` | Convert alignment trace to aligned symbol/code arrays. |

`align.align_optimal()` returns a list of `align.Alignment` objects because multiple traces can share the optimal score. Each `Alignment` stores `.sequences`, `.trace`, and `.score`; gaps are represented by `-1` in the trace.

## Heuristic Alignment And K-mers

Use heuristic search for long sequences, many sequences, or database-like scans where optimal dynamic programming is too expensive.

| Stage | API | Notes |
| --- | --- | --- |
| Enumerate k-mers | `align.KmerAlphabet(base_alphabet, k, spacing=None)` | `create_kmers(sequence.code)` returns encoded k-mers. |
| Index sequences | `align.KmerTable.from_sequences(k, sequences, ref_ids=None, spacing=None, ignore_masks=None)` | Maps k-mers to `(ref_id, position)` pairs. |
| Query table | `table.match(query_sequence)` | Returns rows like `(query_pos, ref_id, ref_pos)`. |
| Query selected k-mers | `table.match_kmer_selection(positions, kmers)` | Use with minimizers/syncmers or filtered seed positions. |
| Space-efficient table | `align.BucketKmerTable.from_sequences(...)` | Hash-bucket alternative to perfect table. |
| Ungapped extension | `align.align_local_ungapped(reference, query, matrix, seed=(ref_pos, query_pos), threshold=...)` | Fast seed extension without gaps. |
| Banded alignment | `align.align_banded(reference, query, matrix, gap_penalty=..., band=(lo, hi), max_number=...)` | Searches a diagonal band around the seed. |
| Local gapped extension | `align.align_local_gapped(...)` | Use for X-drop style local extension. |
| Significance | `align.EValueEstimator.from_samples(...)` | Estimate E-values for alignment scores. |

Choose smaller `k` for sensitivity and larger `k` for speed/specificity. K-mer masks should mark positions to ignore in the original sequence; Biotite expands them to affected k-mer positions internally.

## Multiple Alignment, Profiles, And Positional Matrices

| Task | API | Notes |
| --- | --- | --- |
| Multiple alignment | `alignment, order, guide_tree, distance_matrix = align.align_multiple(sequences, matrix, gap_penalty=-5)` | Progressive MSA; good for strongly related sequences or exotic sequence types. |
| Custom guide tree | `align.align_multiple(..., guide_tree=tree)` | Use when distances are precomputed or k-mer based. |
| Alignment ordering | `alignment = alignment[:, order.tolist()]` | Reorders columns/sequences according to the guide tree order returned by `align_multiple()`. |
| Profile from alignment | `profile = seq.SequenceProfile.from_alignment(alignment)` | Counts symbols and gaps per alignment column. |
| Consensus | `profile.to_consensus()` | Returns nucleotide/protein consensus when alphabet supports it. |
| Probability matrix | `profile.probability_matrix(pseudocount=1)` | Rows are positions; columns are alphabet symbols. |
| Sequence probability | `profile.sequence_probability(sequence, pseudocount=1)` | Scores exact sequence likelihood under the profile. |
| Log-odds matrix | `profile.log_odds_matrix(pseudocount=1)` | Typical input for position-specific scoring. |
| Profile sequence score | `profile.sequence_score(sequence, pseudocount=1)` | Sum of log-odds scores for a sequence. |
| Position placeholder | `seq.PositionalSequence(profile.to_consensus())` | Alphabet contains one symbol per position; only length is semantically required. |
| Positional matrix | `matrix.as_positional(seq1, seq2)` | Expands an ordinary substitution matrix into position-specific form. |

Profile `symbols` and `gaps` must have the same number of rows: one row per alignment column. A `SubstitutionMatrix` created from a log-odds matrix must use the positional alphabet on the positional axis and the query sequence alphabet on the symbol axis in the same orientation passed to alignment.

## Phylogenetic Trees

| Task | API | Notes |
| --- | --- | --- |
| Leaf node | `phylo.TreeNode(index=i)` | `index` refers to an external labels/sequences list. |
| Internal node | `phylo.TreeNode(children=(a, b), distances=(1.0, 2.0))` | Children and parent are immutable after creation. |
| Tree from root | `tree = phylo.Tree(root=root)` | Root must not already be a child node. |
| Newick parse | `phylo.Tree.from_newick(newick, labels=None)` | Raises file/parse errors for malformed Newick or unknown labels. |
| Newick export | `tree.to_newick(labels=None, include_distance=True, round_distance=None)` | Can omit or round distances. |
| Pair distance | `tree.get_distance(i, j, topological=False)` | Topological mode counts edges rather than branch lengths. |
| UPGMA | `phylo.upgma(distance_matrix)` | Distance matrix must be square and symmetric for meaningful results. |
| Neighbor joining | `phylo.neighbor_joining(distance_matrix)` | Produces an unrooted-style clustering represented as a Biotite tree. |
| Binary tree conversion | `phylo.as_binary(tree)` | Preserves leaf distances while converting multifurcations. |

Tree leaves store only reference indices. Keep labels or sequence objects in a separate list and pass labels to Newick/graphics routines when human-readable output is needed.

## Sequence Graphics Routing

Sequence-centered graphics live under `biotite.sequence.graphics` and usually require `matplotlib`:

| Plot | Typical API | Use when |
| --- | --- | --- |
| Alignment similarity | `graphics.plot_alignment_similarity_based(ax, alignment, matrix=matrix, symbols_per_line=...)` | Coloring by substitution similarity. |
| Alignment type | `graphics.plot_alignment_type_based(ax, alignment, color_scheme=..., labels=...)` | Coloring amino acid or nucleotide symbol classes. |
| Feature map | `graphics.plot_feature_map(ax, annotation, loc_range=..., multi_line=...)` | Visualizing `Annotation` features. |
| Sequence logo | `graphics.plot_sequence_logo(ax, profile)` | Visualizing a `SequenceProfile`. |
| Dendrogram | `graphics.plot_dendrogram(ax, tree, labels=..., orientation=...)` | Visualizing a `phylo.Tree`. |
| Plasmid map | graphics plasmid helpers | Circular DNA feature visualization. |

If a task asks only to prepare data for visualization, construct the `Alignment`, `Annotation`, `SequenceProfile`, or `Tree` here. If the task asks about display backends or optional visualization environments, route to `../interfaces-visualization/SKILL.md`.
