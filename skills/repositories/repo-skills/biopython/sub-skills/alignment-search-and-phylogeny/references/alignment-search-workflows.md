# Alignment and scoring workflows

This reference covers Biopython's installed alignment/search-facing APIs verified for the generated skill baseline: `Bio.Align`, `Bio.AlignIO`, substitution matrices, and the legacy `Bio.pairwise2` migration path. It is self-contained and uses only public Biopython modules.

## Choose the right alignment surface

| Need | Use | Notes |
|---|---|---|
| Score or generate pairwise alignments | `Bio.Align.PairwiseAligner` | Current preferred API for global/local pairwise alignment and substitution-matrix scoring. |
| Inspect an alignment returned by the new APIs | `Bio.Align.Alignment` / `PairwiseAlignments` | Alignment objects keep target/query references, coordinates, score, row strings, and support slicing/formatting. |
| Read or write multiple-sequence alignment files | `Bio.AlignIO.read`, `Bio.AlignIO.parse`, `Bio.AlignIO.write` | Use this sub-skill for alignment semantics; use the file-I/O sub-skill for broad conversion/indexing policy. |
| Convert alignment formats | `Bio.AlignIO.convert` or `Bio.Align.write`/`Bio.Align.parse` where supported | Confirm format support before converting; some formats are read-only or write-only. |
| Maintain old `pairwise2` code | `Bio.pairwise2` temporarily | Deprecated; migrate new work to `PairwiseAligner`. |
| Run ClustalW, MUSCLE, BLAST+, PAML, or other executables | External subprocess/tool-specific wrapper only after checking installation | These tools are optional and not required for base Biopython workflows. |

## Verified public signatures and formats

Installed public signatures:

```text
PairwiseAligner(scoring=None, **kwargs)
Bio.Align.parse(source, fmt)
Bio.Align.write(alignments, target, fmt, *args, **kwargs)
AlignIO.read(handle, format, seq_count=None)
AlignIO.parse(handle, format, seq_count=None)
AlignIO.write(alignments, handle, format)
AlignIO.convert(in_file, in_format, out_file, out_format, molecule_type=None)
```

`AlignIO.read` / `AlignIO.parse` formats verified in the installed baseline:

```text
clustal, emboss, fasta-m10, maf, mauve, msf, nexus, phylip,
phylip-relaxed, phylip-sequential, stockholm
```

`AlignIO.write` formats verified in the installed baseline:

```text
clustal, maf, mauve, nexus, phylip, phylip-relaxed,
phylip-sequential, stockholm
```

## PairwiseAligner workflow

Use `PairwiseAligner` when the user asks for sequence similarity scoring, a best alignment, local/global alignment, gap tuning, or protein substitution-matrix scoring.

```python
from Bio import Align

aligner = Align.PairwiseAligner()
aligner.mode = "global"          # or "local"
aligner.match_score = 2.0
aligner.mismatch_score = -1.0
aligner.open_gap_score = -2.0
aligner.extend_gap_score = -0.5

score = aligner.score("GATTACA", "GCATGCU")
alignments = aligner.align("GATTACA", "GCATGCU")
best = alignments[0]
assert best.score == score
print(best)
```

Practical rules:

- Set `mode` to `"global"` for end-to-end Needleman-Wunsch/Gotoh-style alignment and `"local"` for Smith-Waterman-style local regions.
- Use `.score(target, query)` when only the score is needed; it avoids materializing all optimal alignments.
- Use `.align(target, query)` when aligned strings/coordinates are needed; the result can contain many equally optimal alignments.
- Check `aligner.algorithm` after configuring scoring if an exact dynamic-programming variant matters.
- Scores are floating point; compare with tolerance when parameters contain fractional penalties.
- Gap scores should normally be non-positive penalties. Biopython has broad gap-score controls: `gap_score`, `open_gap_score`, `extend_gap_score`, insertion/deletion-specific scores, and left/internal/right end-gap variants.
- Local alignments report only positive-scoring regions; if a local task returns no alignments, inspect match/mismatch/gap signs first.

## Substitution matrices

Use `Bio.Align.substitution_matrices` for protein or codon scoring.

```python
from Bio import Align
from Bio.Align import substitution_matrices

names = substitution_matrices.load()
assert "BLOSUM62" in names
matrix = substitution_matrices.load("BLOSUM62")
assert matrix.alphabet.startswith("ARNDC")
assert matrix["A", "A"] == 4.0

aligner = Align.PairwiseAligner()
aligner.substitution_matrix = matrix
aligner.open_gap_score = -10.0
aligner.extend_gap_score = -0.5
score = aligner.score("MEEPQ", "MEEPQ")
```

Matrix cautions:

- Matrix keys must be present in the matrix alphabet; unexpected letters raise lookup/index errors rather than being silently treated as wildcards.
- With a substitution matrix, characters such as `X` are scored by the matrix if present; they are not automatically unknown unless the matrix encodes them that way.
- Setting a substitution matrix supersedes simple match/mismatch scoring for substitutions. Re-check scoring after changing matrices or wildcard policy.
- `substitution_matrices.load()` lists available built-in matrix names; `substitution_matrices.read(handle, dtype)` can parse a matrix from a user-provided handle.

## Alignment objects and coordinates

A `PairwiseAligner.align()` result yields `Bio.Align.Alignment` objects. Common operations:

```python
alignment = aligner.align("GAACTTT", "GATTT")[0]
print(alignment.score)
print(alignment[0])       # aligned target row, with gap characters when formatted
print(alignment[1])       # aligned query row
print(alignment.target)   # original target object/string
print(alignment.query)    # original query object/string
print(alignment.coordinates)
```

Use coordinates, not only printed strings, for robust downstream indexing. Printed alignment rows are display-friendly; coordinate arrays are safer for slicing original sequences and validating spans.

## AlignIO route notes

Use `AlignIO.read(handle, format)` only when exactly one alignment is expected; it raises if the file has zero or multiple alignments. Use `AlignIO.parse(handle, format)` for a stream of alignments. Use `AlignIO.write(alignments, handle, format)` for one or more alignments and check the returned count when available.

Minimal in-memory MSA pattern:

```python
from io import StringIO
from Bio import AlignIO

text = ">seq1\nACGT\n>seq2\nA-GT\n"
alignment = AlignIO.read(StringIO(text), "fasta")
assert len(alignment) == 2
assert alignment.get_alignment_length() == 4
```

Route broad file-format selection, FASTA/FASTQ/GenBank conversion, indexing, BGZF, or raw `SeqRecord` handling to the file-I/O sub-skill. Keep this sub-skill focused on alignment semantics and handoff from alignment file content into search/tree workflows.

## Legacy pairwise2 migration

`Bio.pairwise2` is deprecated in the verified Biopython baseline. It remains useful for understanding or migrating older code that calls functions such as `pairwise2.align.globalxx`, `globalms`, `localds`, or uses `format_alignment`.

Migration hints:

- Replace `globalxx`/`localxx` with `PairwiseAligner(mode="global"/"local")` and simple match/gap settings.
- Replace dictionary/matrix scoring such as `globalds(..., blosum62, open, extend)` with `aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")` plus gap scores.
- `pairwise2` returns named tuples `(seqA, seqB, score, start, end)`; `PairwiseAligner` returns `Alignment` objects with coordinates and source sequence references.
- If old code depends on exact tie ordering across multiple optimal alignments, treat that as a behavior-sensitive migration and assert scores/topology explicitly.
