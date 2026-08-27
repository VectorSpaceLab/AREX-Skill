# `gget.mutate` operating contract

Evidence: `gget_mutate.py`, `docs/src/en/mutate.md`, `tests/test_mutate.py`,
and `tests/fixtures/test_mutate.json`. The implementation is nucleotide-oriented;
complex variant screening is explicitly directed by the docs to kvar.

## Inputs and sequence IDs

Live signature:

```text
mutate(sequences: str | list[str], mutations: str | list[str],
mut_column='mutation', seq_id_column='seq_ID', mut_id_column=None,
gtf=None, gtf_transcript_id_column=None, k=30, min_seq_len=None,
optimize_flanking_regions=False, remove_seqs_with_wt_kmers=False,
max_ambiguous=None, merge_identical=True, update_df=False,
update_df_out=None, store_full_sequences=False, translate=False,
translate_start=None, translate_end=None, out=None, verbose=True) -> Any
```

`sequences` may be a FASTA path, one nucleotide string, or list of strings.
For FASTA, `read_fasta` supplies titles and sequences. The sequence key used
for joins is the first token of a title, then the portion before the first dot;
for example `>ENST1.4 description` joins as `ENST1`. This deliberately removes
Ensembl version numbers. In-memory lists receive synthetic IDs `seq1`, `seq2`,
etc.; a table using `seq_ID` must use those IDs unless a file is used.
Accepted sequence characters are `ATGCUNatgcun.-`; other characters trigger a
warning and can make inversion behavior unreliable. `N` is ambiguous, not a
wild-type base to guess.

`mutations` may be a CSV/TSV path, pandas DataFrame, one annotation string, or
list of annotation strings. A single string is applied to every input sequence.
A list of length greater than one must have exactly as many entries as input
sequences; list entries receive generated `mut1`, `mut2`, ... IDs. A table must
contain the selected mutation and sequence-ID columns; `mut_ID` is optional and
`mut_id_column` selects a different ID column. Missing sequence IDs are dropped
with a warning; zero remaining joins raise a `ValueError`.

## Annotation and generation

The parser recognizes `c.` and `g.` forms and the live fixtures exercise:

- substitution: `c.35G>A` (the reference base must match the FASTA base);
- deletion: `c.35del`, `c.35_40del`;
- insertion: `c.4_5insT`, `c.65_66insTTTTT`;
- replacement: `c.38delinsAAA`, including ranges;
- duplication: `c.35dup`, `c.35_37dup`;
- inversion: `c.35_38inv` (reverse complement is generated).

Positions are one-based in the annotation and adjusted to zero-based indices
internally. `k` is the flank length (default 30); near a sequence end, the
available sequence is used, and if `k` exceeds total length the whole available
sequence may be retained. `min_seq_len` removes mutant fragments shorter than
that length. `optimize_flanking_regions` trims overlaps between mutant sequence
and flank where possible. `remove_seqs_with_wt_kmers` removes fragments sharing
an appropriate `(k+1)`-mer with the wild-type fragment; long duplications can
also be removed. `max_ambiguous` removes outputs with more than that many `N`s.
`merge_identical=True` groups identical mutant sequences and joins their
headers with semicolons; set it false when one output per mutation is needed.

The transform rejects or counts uncertain/unsupported cases instead of
inventing coordinates: `?`, parenthesized ambiguous positions, intronic `+/-`,
post-translational `*`, malformed/unknown annotations, wrong substitution
wild-type bases, and positions outside sequence length. The module reports
counters in logs; rerun with corrected records and do not treat a shortened
result as proof all rows succeeded.

## Outputs and mutation table schema

- `out=None`, `update_df=False`: returns a list of non-empty mutant sequence
  strings. No FASTA headers are returned in this mode.
- `out='mutants.fa'`: writes FASTA records and returns no sequence list. The
  current implementation builds headers as `>[seq_ID]:[mut_ID]` before removing
  the leading `>` for file writing, so a file header is `seq_ID:mut_ID`. Older
  docs/examples describe an underscore; test the live output when downstream
  parsers depend on the delimiter.
- `update_df=True`: returns the retained mutation DataFrame when `out=None` and
  writes an updated table. For a CSV/TSV input and no `update_df_out`, the file
  defaults to the input basename plus `_updated`; otherwise use an explicit new
  path. Never use the input path as the update destination.

The updated table always retains the selected ID/mutation columns and adds
`header`, `mutation_type`, `wt_sequence`, `mutant_sequence`, coordinate columns,
and source table columns. `store_full_sequences=True` adds full wild-type and
mutant nucleotide columns. `translate=True` is valid only with both
`update_df=True` and `store_full_sequences=True`; it adds
`wt_sequence_aa_full` and `mutant_sequence_aa_full`. Translation starts at 0
and ends at the sequence length by default. Integer `translate_start`/
`translate_end` define a shared frame for in-memory inputs; for a table input,
string values name per-row columns (default fallback names are
`translate_start`/`translate_end`). Codons not in the table, including
incomplete/ambiguous codons, become `X`.

If `gtf` is supplied, `mutations` must be a CSV/TSV path and
`gtf_transcript_id_column` must identify the transcript column. The table's
`seq_ID` column then contains chromosome identifiers; transcript coordinates
are merged from transcript features in the GTF, with missing boundaries filled
by 0/9999999 and strand by `.`. Use this only when the input FASTA is genomic
and preserve the original GTF/table.

## Minimal safe examples

```python
import gget

# One mutation applied to one sequence; returns list[str].
mutants = gget.mutate("ATCGCTAAGCT", "c.4G>T", verbose=False)

# One mutation per sequence; write a new FASTA.
gget.mutate(["ATCGCTAAGCT", "TAGCTA"], ["c.4G>T", "c.1_3inv"],
            k=3, out="mutants.fa", verbose=False)
```

The source fixture verifies substitution, end/edge handling, deletion,
insertion, delins, duplication, inversion, invalid-coordinate counters, CSV
joins, and repeat-aware flanks. Use a tiny local fixture to verify new options
rather than invoking external services.
