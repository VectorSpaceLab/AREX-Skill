# Sequences and Alignment API Reference

This reference distills the scikit-bio 0.7.4-dev sequence and alignment APIs needed for routine agent work. Prefer the public imports shown here; do not depend on private modules.

## Imports

```python
from skbio import DNA, RNA, Protein, Sequence
from skbio.sequence import GeneticCode, SubstitutionMatrix
from skbio.alignment import (
    AlignPath,
    PairAlignPath,
    TabularMSA,
    align_dists,
    align_score,
    pair_align,
    pair_align_nucl,
    pair_align_prot,
)
```

Many public objects are also re-exported from `skbio` itself, but importing sequence utilities from `skbio.sequence` and alignment utilities from `skbio.alignment` keeps intent clear.

## Core Sequence Constructors

| API | Signature / common call | Use |
| --- | --- | --- |
| `Sequence` | `Sequence(sequence, metadata=None, positional_metadata=None, interval_metadata=None, lowercase=False)` | Generic immutable sequence with no biological alphabet validation. Useful for unrestricted strings/tokens and metadata behavior. |
| `DNA` | `DNA(sequence, metadata=None, positional_metadata=None, interval_metadata=None, lowercase=False, validate=True)` | IUPAC DNA grammar with definite bases, degenerates, gaps, wildcard `N`, nucleotide transforms, and translation through RNA. |
| `RNA` | `RNA(sequence, metadata=None, positional_metadata=None, interval_metadata=None, lowercase=False, validate=True)` | IUPAC RNA grammar with wildcard `N`, reverse transcription, translation, and six-frame translation. |
| `Protein` | `Protein(sequence, metadata=None, positional_metadata=None, interval_metadata=None, lowercase=False, validate=True)` | IUPAC protein grammar including stop `*`, gaps, degenerates, and wildcard `X`. |

Constructor notes:

- `metadata` is per-object metadata and is shallow-copied; mutable values can still be shared.
- `positional_metadata` must have one row/value per sequence position; slicing filters positional metadata alongside sequence positions.
- `interval_metadata` stores interval features over positions. Slicing can drop or adjust intervals depending on the operation; verify feature coordinates after slicing.
- `lowercase=True` uppercases lowercase input. `lowercase="column"` uppercases input and records original lowercase positions as a Boolean positional metadata column.
- `validate=True` checks biological alphabets for `DNA`, `RNA`, and `Protein`. Use `validate=False` only when input is already trusted or when intentionally staging nonstandard/dirty data before cleaning.

## Sequence Grammar and Inspection

| API / attribute | Applies to | Purpose |
| --- | --- | --- |
| `str(seq)` / `print(seq)` | all sequence objects | Extract the sequence string without reopening input files. |
| `seq.values` | all sequence objects | Read-only NumPy byte array view of sequence data. |
| `seq.metadata`, `seq.positional_metadata`, `seq.interval_metadata` | all sequence objects | Access annotation layers. |
| `seq.has_metadata()`, `seq.has_positional_metadata()`, `seq.has_interval_metadata()` | all sequence objects | Check whether annotation layers are populated. |
| `seq.gaps()`, `seq.has_gaps()` | grammared biological sequences | Locate and summarize gap characters such as `-` and `.`. |
| `seq.degenerates()`, `seq.has_degenerates()` | grammared biological sequences | Locate ambiguity codes such as nucleotide `R`, `Y`, or wildcard `N`. |
| `seq.definites()`, `seq.has_definites()` | grammared biological sequences | Locate non-degenerate alphabet characters. |
| `seq.observed_chars` | all sequence objects | Get characters observed in the sequence. |
| `DNA.degenerate_map`, `RNA.degenerate_map`, `Protein.degenerate_map` | classes | Resolve degenerate symbols to possible definites. |
| `DNA.gap_chars`, `RNA.gap_chars`, `Protein.gap_chars` | classes | Inspect accepted gap characters. |
| `DNA.wildcard_char`, `RNA.wildcard_char`, `Protein.wildcard_char` | classes | Inspect wildcard character (`N` for nucleotides, `X` for proteins). |

Indexing and slicing return sequence objects, not raw characters. Integer indexing returns a length-1 sequence. Most slices are views over sequence data and carry object metadata; positional metadata is sliced to matching positions.

## Sequence Transforms

| API | Use | Metadata behavior |
| --- | --- | --- |
| `seq.degap()` | Remove all gap characters from a grammared sequence. | Keeps object metadata and filters positional metadata. |
| `dna.complement()` / `rna.complement()` | Complement nucleotide sequence. | Keeps compatible metadata. |
| `dna.reverse_complement()` / `rna.reverse_complement()` | Reverse-complement nucleotide sequence. | Keeps compatible metadata with positions reversed. |
| `dna.transcribe()` | Convert coding DNA `T` to RNA `U`. | Keeps metadata, positional metadata, and interval metadata. |
| `rna.reverse_transcribe()` | Convert RNA `U` to coding DNA `T`. | Keeps metadata, positional metadata, and interval metadata. |
| `dna.translate(...)` / `rna.translate(...)` | Translate to `Protein`. | Keeps object metadata, drops positional metadata. |
| `dna.translate_six_frames(...)` / `rna.translate_six_frames(...)` | Yield proteins in frames `1, 2, 3, -1, -2, -3`. | Keeps object metadata, drops positional metadata. |

Translation details:

- `RNA.translate(genetic_code=1, *args, **kwargs)` accepts an NCBI table id or a `GeneticCode` object.
- `DNA.translate(*args, **kwargs)` transcribes first, then uses RNA translation.
- `GeneticCode.from_ncbi(table_id=1)` returns a named NCBI genetic code.
- `GeneticCode.translate(sequence, reading_frame=1, start="ignore", stop="ignore")` accepts `start` and `stop` policies of `"ignore"`, `"optional"`, or `"require"`.
- Translation rejects gapped sequences and invalid reading frames; degenerate codons translate only when supported by the translation logic, so clean or validate before translating.

## Substitution Matrices

| API | Purpose |
| --- | --- |
| `SubstitutionMatrix(alphabet, scores, **kwargs)` | Build a square scoring matrix for characters or other scalar symbols. |
| `SubstitutionMatrix.identity(alphabet, match, mismatch, dtype="float32")` | Create a simple identity matrix for match/mismatch scoring. |
| `SubstitutionMatrix.by_name(name)` | Load predefined matrices such as `"NUC.4.4"` or `"BLOSUM62"`. |
| `matrix.alphabet` / `matrix.scores` / `matrix.is_ascii` | Inspect alphabet, score array, and fast ASCII compatibility. |
| `matrix[a, b]` | Look up a substitution score. |
| `seq.to_indices(matrix)` | Map sequence characters to matrix row/column indices. |

Use `"NUC.4.4"` for nucleotide alignments involving degenerate nucleotide symbols. Use `"BLOSUM62"` for common protein alignment scoring.

## Pairwise Alignment APIs

| API | Signature / defaults | Use |
| --- | --- | --- |
| `pair_align` | `pair_align(seq1, seq2, /, mode="global", sub_score=(1.0, -1.0), gap_cost=2.0, free_ends=True, trim_ends=False, max_paths=1, atol=1e-5, keep_matrices=False)` | General dynamic-programming pairwise alignment for biological sequences, strings, bytes, token lists, and numeric sequences. |
| `pair_align_nucl` | `pair_align_nucl(seq1, seq2, /, **kwargs)` with defaults `sub_score=(2.0, -3.0)`, `gap_cost=(5.0, 2.0)` | Nucleotide convenience wrapper with BLASTN-like scoring defaults. |
| `pair_align_prot` | `pair_align_prot(seq1, seq2, /, **kwargs)` with defaults `sub_score="BLOSUM62"`, `gap_cost=(11.0, 1.0)` | Protein convenience wrapper with BLASTP-like scoring defaults. |
| `PairAlignResult` | named tuple with `.score`, `.paths`, `.matrices` | Result from `pair_align*`. `.paths` is `None` when `max_paths=0`, an empty list for local alignments with no positive score, or a list of optimal `PairAlignPath` objects. |

Alignment parameter semantics:

- `mode="global"` aligns end to end; with default `free_ends=True` it behaves as overlap/semi-global alignment with terminal gaps unpenalized.
- `mode="local"` performs Smith-Waterman-like local alignment and ignores `free_ends` semantics.
- `sub_score` can be `(match, mismatch)`, a `SubstitutionMatrix`, or a matrix name string such as `"NUC.4.4"` or `"BLOSUM62"`.
- `gap_cost` can be a single linear gap penalty or `(gap_open, gap_extend)` for affine penalties.
- scikit-bio affine gap cost is `open + extend * k` for a gap of length `k`; when copying parameters from tools that use `open + extend * (k - 1)`, subtract `extend` from the source opening penalty.
- `free_ends` can be `bool`, `(seq1_free, seq2_free)`, or `(seq1_lead, seq1_trail, seq2_lead, seq2_trail)`.
- `trim_ends=True` removes penalty-free terminal gaps from returned paths and is useful for locating short queries in longer targets.
- `max_paths=1` returns one optimal path efficiently; `max_paths=None` can enumerate all optimal paths and can be very expensive; `max_paths=0` skips traceback and returns only a score.
- `keep_matrices=True` returns dynamic-programming matrices for diagnostics or teaching, not routine production workflows.

## Alignment Path APIs

| API | Purpose |
| --- | --- |
| `PairAlignPath.from_cigar(cigar, starts=None)` | Construct a two-sequence path from CIGAR text/bytes. Supports `M`, `I`, `D`, `P`, and maps `=`, `X`, `N`, `S`, `H` to path states. |
| `path.to_cigar()` | Convert `PairAlignPath` to compact CIGAR with `M`, `I`, and `D`. |
| `path.to_cigar((seq1, seq2))` | Emit `=` and `X` for exact matches/mismatches when original sequences are supplied. |
| `path.to_aligned((seq1, seq2), gap_char="-", flanking=None)` | Insert gaps and return aligned strings or sequence-like values. |
| `path.ranges`, `path.starts`, `path.stops` | 0-based half-open aligned ranges in original sequences. |
| `AlignPath.from_aligned(aligned, gap_chars="-", starts=None)` | Infer a multi-sequence alignment path from aligned strings/sequences. |
| `AlignPath.from_tabular(msa, starts=None)` | Convert a `TabularMSA` to a compact path. |
| `TabularMSA.from_path_seqs(path, seqs)` | Convert an alignment path plus original sequences to a `TabularMSA`. |

`AlignPath` and `PairAlignPath` store gap-placement operations, not sequence data. Keep the original sequences if you need aligned strings or an MSA later.

## TabularMSA

| API | Signature / use |
| --- | --- |
| `TabularMSA` | `TabularMSA(sequences, metadata=None, positional_metadata=None, minter=None, index=None)` |
| `msa.dtype` | Sequence class stored in rows, or `None` for an empty MSA. |
| `msa.shape` | Named tuple `Shape(sequence=<rows>, position=<columns>)`. |
| `msa.index` | Pandas index of sequence labels; reset by `del msa.index`. |
| `msa.iloc[...]` | Position/integer slicing similar to pandas. `msa.iloc[0]` returns a row sequence; `msa.iloc[:, 1]` returns a column `Sequence`. |
| `msa.loc[...]` | Label-based sequence-axis and position-axis slicing. |
| `msa.iter_positions(reverse=False, ignore_metadata=False)` | Iterate columns as `Sequence` objects. |
| `msa.consensus()` | Return consensus sequence of the same dtype. |
| `msa.conservation(...)` | Compute per-position conservation scores. |
| `msa.reassign_index(mapping=None, minter=None)` | Return a copy with reassigned row labels. |

Construction rules:

- All rows must be `GrammaredSequence` objects, all of the same concrete class, and all of the same length.
- `index` length must equal the number of sequences, labels must be hashable, and `index` cannot be combined with `minter`.
- `minter` can be a callable or a metadata key such as `"id"`; each sequence must provide the needed metadata when using a key.
- `positional_metadata` on the MSA must have one value per alignment position, not per sequence.

## Alignment Scoring and Distances

| API | Signature / use |
| --- | --- |
| `align_score` | `align_score(alignment, sub_score=(1.0, -1.0), gap_cost=2.0, free_ends=True, gap_chars="-.")` |
| `align_dists` | `align_dists(alignment, metric, shared_by_all=True, **kwargs)` |

`align_score` accepts a `TabularMSA`, a list of aligned strings/sequences, or `(AlignPath, iterable_of_original_sequences)`. For two rows it returns a pairwise score; for three or more rows it returns a sum-of-pairs score. Supply the same `sub_score`, `gap_cost`, and `free_ends` settings used to create the alignment when validating a score.

`align_dists` requires a `TabularMSA` and returns a `DistanceMatrix`. `metric` can be a named metric from `skbio.sequence.distance` such as `"pdist"` or `"jc69"`, or a callable. With `shared_by_all=True`, positions invalid in any sequence are removed for all pairwise calculations; with `False`, deletion is pair-specific. Use the statistics/ordination sub-skill for downstream analysis of the returned matrix.

## Legacy Pairwise Wrappers

Deprecated educational wrappers remain importable from `skbio.alignment`: `global_pairwise_align_nucleotide`, `global_pairwise_align_protein`, `global_pairwise_align`, `local_pairwise_align_nucleotide`, `local_pairwise_align_protein`, and `local_pairwise_align`. They return older alignment structures and follow older scoring conventions. For new work, use `pair_align`, `pair_align_nucl`, or `pair_align_prot` and mention legacy wrappers only when maintaining old code or explaining historical tests.
