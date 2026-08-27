# Sequences and Alignment Troubleshooting

Use these checks before reopening source documentation. Most issues are caused by alphabet validation, metadata lengths, MSA shape rules, or scoring-parameter mismatches.

## Diagnosis Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `DNA(...)`, `RNA(...)`, or `Protein(...)` raises an invalid character error | Input contains characters outside the class grammar. Examples: `U` in `DNA`, `T` in `RNA`, non-IUPAC letters, or unsupported protein symbols. | Use the correct class, uppercase with `lowercase=True`, replace dirty nucleotides with `N` or proteins with `X`, or use generic `Sequence` for non-biological data. Keep `validate=True` after cleaning. |
| Construction succeeds with `validate=False` but later alignment/scoring fails | Invalid symbols were deferred into `to_indices`, substitution matrix lookup, translation, or alignment encoding. | Treat `validate=False` as staging only. Clean and reconstruct with `validate=True` before biological operations. If symbols are biologically meaningful, build a `SubstitutionMatrix` covering them. |
| Lowercase input is rejected or loses case information | `lowercase=False` leaves lowercase characters unchanged; biological grammars expect uppercase alphabet symbols. | Use `lowercase=True` to uppercase, or `lowercase="was_lowercase"` to uppercase and record original lowercase positions in positional metadata. |
| Positional metadata constructor raises a length error | One or more positional metadata columns do not have exactly `len(sequence)` values. | Recompute metadata after trimming/cleaning, or construct the sequence first and assign correctly sized columns. For `TabularMSA`, positional metadata length must match alignment positions, not row count. |
| Sliced sequence metadata appears shared | `metadata` and `positional_metadata` are shallow-copied for performance; nested mutable values can be shared. | Deep-copy mutable nested metadata yourself before mutation, or replace metadata values instead of mutating in place. |
| Translation raises about gapped sequence | `GeneticCode.translate` does not translate gapped sequences. | Decide whether gaps are alignment artifacts. If yes, use `seq.degap()` before translation; if not, inspect upstream sequence construction. |
| Translation raises about start, stop, or reading frame | `start`/`stop` policy is too strict, the sequence lacks required codons, or `reading_frame` is not one of `1, 2, 3, -1, -2, -3`. | Use the intended NCBI table with `GeneticCode.from_ncbi`, choose `start`/`stop` from `"ignore"`, `"optional"`, `"require"`, and verify frame and sequence length. |
| `pair_align(..., mode=...)` raises invalid mode | Only `"global"` and `"local"` are valid. | Use `mode="global"` for end-to-end/overlap alignment or `mode="local"` for similar-region alignment. |
| Alignment score does not match `align_score` | `align_score` used different `sub_score`, `gap_cost`, or `free_ends` than the original alignment. | Recompute with the exact same scoring parameters and pass `(path, (seq1, seq2))` when validating a `PairAlignPath`. |
| Protein alignment with nucleotide matrix, or nucleotide alignment with protein matrix, fails | The substitution matrix alphabet does not cover sequence characters. | Use `"NUC.4.4"` for nucleotide degenerates and `"BLOSUM62"` for common proteins, or create a custom `SubstitutionMatrix`. |
| Gap penalties copied from another tool give unexpected scores | scikit-bio affine gap penalty is `open + extend * k`, while some tools use `open + extend * (k - 1)`. | If reproducing tools that use the second convention, subtract `extend` from the source opening penalty before calling `pair_align`. |
| `result.paths` is `None` | `pair_align(..., max_paths=0)` disables traceback. | Set `max_paths=1` for one path, a positive integer for limited alternatives, or `None` for all optimal paths if safe. |
| `result.paths` is an empty list for local alignment | Local alignment found no path with score greater than zero. | Check scoring parameters, input similarity, and whether mismatches/gaps are too punitive. Handle empty paths explicitly. |
| `TabularMSA(...)` raises about sequence types | Rows are not `GrammaredSequence` objects or mix concrete classes such as `DNA` and `RNA`. | Convert all rows to the same biological class and ensure all are `DNA`, all `RNA`, or all `Protein`. |
| `TabularMSA(...)` raises about lengths | Aligned rows are not all the same length. | Insert gaps to make aligned strings equal length, or use `PairAlignPath`/`AlignPath` conversion helpers instead of hand-padding. |
| `TabularMSA(index=...)` raises about index length or hashability | Index length differs from sequence count or labels are unhashable. | Provide one hashable label per row, or use `minter="id"` when every sequence has `metadata["id"]`. Do not pass both `index` and `minter`. |
| `align_dists` raises about metric or sequence type | Metric name is not a registered sequence distance metric, or the metric is incompatible with the MSA dtype. | Use metrics from `skbio.sequence.distance` such as `"pdist"` or nucleotide models like `"jc69"` only with compatible sequence classes. |

## Invalid Alphabet Recovery Pattern

Use this when dirty input includes meaningful degenerates plus a small number of non-IUPAC symbols:

```python
from skbio import DNA

raw = "acgtryZ--"
try:
    seq = DNA(raw, lowercase=True)
except ValueError:
    staged = DNA(raw, lowercase=True, validate=False)
    repaired = str(staged).replace("Z", "N")
    seq = DNA(repaired, validate=True)

assert seq.has_degenerates()
```

Document the tradeoff in user-facing work: replacing with `N` preserves length and marks uncertainty, while dropping characters changes coordinates and positional metadata alignment.

## Metadata Length Repair Pattern

```python
from skbio import DNA

sequence_text = "ACGT--"
quality = [30, 31, 32, 33, 5, 5]
seq = DNA(sequence_text, positional_metadata={"quality": quality})
ungapped = seq.degap()

assert str(ungapped) == "ACGT"
assert ungapped.positional_metadata["quality"].tolist() == [30, 31, 32, 33]
```

If metadata comes from an external file and lengths disagree, do not pad silently. Check whether trimming, adapter removal, or gap insertion happened before metadata generation.

## Translation Stop Handling Pattern

```python
from skbio import DNA

orf = DNA("ATGCCACTTTAA")
permissive = orf.translate(stop="ignore")
strict = orf.translate(stop="require")

assert str(permissive) == "MPL*"
assert str(strict) == "MPL"
```

Use strict stop requirements only when the sequence is expected to be a complete ORF. For partial contigs, reads, or translated search hits, `stop="ignore"` or `stop="optional"` is often more appropriate.

## Alignment Parameter Validation Pattern

```python
from skbio import DNA
from skbio.alignment import align_score, pair_align_nucl

seq1 = DNA("GATCGTC")
seq2 = DNA("ATCGCTC")
result = pair_align_nucl(seq1, seq2)
path = result.paths[0]
validated = align_score((path, (seq1, seq2)), sub_score=(2, -3), gap_cost=(5, 2))

if validated != result.score:
    raise AssertionError((result.score, validated))
```

If validation fails, check for changed scoring defaults, a hand-edited path, wrong `gap_cost`, or mismatched `free_ends` semantics. Remember `pair_align_nucl` is a wrapper over `pair_align` with BLASTN-like defaults.

## Difficult Synthetic Usability Cases

1. **Dirty degenerate nucleotide recovery:** Given `"acgtryZ--"` plus per-position quality metadata, construct a valid `DNA` object without losing coordinate length, record original lowercase positions, replace the invalid `Z` with `N`, degap for translation only, and explain why `validate=False` is not a final state.
2. **Alignment score mismatch triage:** Align two DNA sequences with `pair_align_nucl`, intentionally validate with the wrong linear `gap_cost=2`, diagnose the mismatch, then recompute `align_score((path, (seq1, seq2)), sub_score=(2, -3), gap_cost=(5, 2))` and confirm equality with `result.score`.

## Cross-Skill Escalation

- If the failure is about file format sniffing, FASTA/FASTQ/BIOM parsing, or metadata file layout, use `../io-metadata/SKILL.md`.
- If the failure appears after `align_dists` returns a `DistanceMatrix` and involves statistical testing or ordination, use `../statistics-ordination/SKILL.md`.
- If the next step is tree inference, rooting, traversal, or phylogenetic interpretation, use `../trees-phylogeny/SKILL.md`.
