# DMS Data Formats

## Input CSV

The variant prediction script reads a CSV with `pandas.read_csv` and requires a mutation column. The default mutation column is `mutant`.

Minimum useful CSV:

```csv
mutant,score
A24D,0.12
L25V,-0.31
```

Additional experimental columns are preserved in the output. The script appends one prediction column per model location.

## Mutation Notation

Each row is expected to describe a single amino-acid substitution in `AiB` form:

- `A`: one-letter wild-type residue in the supplied `--sequence`.
- `i`: integer residue number from the DMS numbering scheme.
- `B`: one-letter mutant residue.

Examples: `A24D`, `G102W`, `M1I`.

The example implementation parses mutations as `wt = row[0]`, `idx = int(row[1:-1]) - offset_idx`, and `mt = row[-1]`. It then asserts `sequence[idx] == wt` and scores that one zero-based sequence position.

## Offset Semantics

`--offset-idx` converts DMS residue numbering into zero-based Python sequence indexing:

```text
python_index = mutation_number - offset_idx
```

If the DMS labels the first character of `--sequence` as residue 24, use `--offset-idx 24`. Then mutation `A24D` checks `sequence[0] == "A"`.

Common offset examples:

| DMS first residue number | First sequence mutation | Correct `--offset-idx` |
| --- | --- | --- |
| 0 | `A0D` | `0` |
| 1 | `A1D` | `1` |
| 24 | `A24D` | `24` |

If validation reports a wild-type mismatch, first test nearby offsets before assuming the sequence is wrong.

## Multi-Mutants And Indels

The example scoring functions are built for single substitutions only. Mutation strings with separators such as `A24D:G102W`, `A24D/G102W`, deletions, insertions, stop codons, or non-integer positions are outside the script's single-mutant contract.

For multi-mutants, either decompose rows into single substitutions when scientifically appropriate or write a new scoring routine that applies all substitutions before evaluating the desired sequence-level objective.

## MSA A3M Inputs

MSA Transformer runs require `--msa-path`. The example MSA loader uses a FASTA parser and removes A3M insertions with this behavior:

- Lowercase letters are deleted.
- `.` is deleted.
- `*` is deleted.
- Uppercase aligned residues and gap characters remain.
- Only the first `--msa-samples` records are read.

The first sequence in the MSA batch is masked position-by-position and scored. Ensure it corresponds to the same target sequence/numbering used by the DMS CSV after insertion removal.

## Output CSV

The output path is written with `DataFrame.to_csv`. Existing files may be overwritten by normal pandas behavior. Each model location becomes a column name, so long local checkpoint paths can create awkward output column names.

Before launching a long run:

- Confirm the output path is intentionally disposable or versioned.
- Consider using short symlinks or concise checkpoint names if local paths would become unwieldy column headers.
- Keep the original DMS columns untouched so downstream evaluation can join predictions back to experimental measurements.
