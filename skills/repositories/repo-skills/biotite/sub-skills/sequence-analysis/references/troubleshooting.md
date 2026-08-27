# Sequence Troubleshooting

Use this guide to recover common Biotite sequence, alignment, profile, phylogeny, and sequence graphics failures.

## Invalid Symbols Or Alphabet Mismatch

Symptoms:

- `AlphabetError` while constructing a sequence or encoding a symbol.
- Alignment errors because a `SubstitutionMatrix` alphabet does not match the input sequences.
- A sequence created by assigning `.code` manually reports `sequence.is_valid() == False`.

Recovery:

1. Print or inspect the intended alphabet with `sequence.get_alphabet().get_symbols()` or `seq.NucleotideSequence.unambiguous_alphabet().get_symbols()`.
2. Normalize input before construction: uppercase letters, strip whitespace, and convert RNA `U` to DNA `T` if using `NucleotideSequence`.
3. For ambiguous nucleotide symbols such as `N`, construct with `seq.NucleotideSequence(text, ambiguous=True)` or omit the argument and let Biotite infer the alphabet.
4. For strict DNA validation, construct with `ambiguous=False` and catch `seq.AlphabetError`.
5. Use `align.SubstitutionMatrix.std_protein_matrix()` for `ProteinSequence` objects and `align.SubstitutionMatrix.std_nucleotide_matrix()` for nucleotide objects.
6. For custom sequence types, build the matrix with the same `Alphabet` objects used by the sequences.

## Ambiguous Nucleotide Handling

Symptoms:

- A nucleotide sequence unexpectedly uses an ambiguous alphabet.
- Translation or profile consensus includes ambiguous symbols.
- A CDS extracted from annotations contains ambiguous flanking bases.

Recovery:

1. Decide whether ambiguous symbols are biologically meaningful or data-quality issues.
2. If ambiguous symbols are expected, preserve them and document how downstream functions should treat them.
3. If a coding sequence must be unambiguous, extract the exact CDS portion and rebuild it with `seq.NucleotideSequence(cds_text, ambiguous=False)`.
4. For ORF searches, consider filtering translated products or reporting ambiguous input rather than forcing a misleading clean translation.
5. For consensus profiles, remember ties or mixed counts may yield ambiguous nucleotide consensus symbols.

## Sequence Length Or Alignment Shape Mismatch

Symptoms:

- Manual `Alignment` construction fails or produces unexpected symbols.
- `SequenceProfile` counts do not match expected alignment columns.
- Position-specific `SubstitutionMatrix` dimensions do not match positional sequences.

Recovery:

1. Prefer `align.Alignment.from_strings([...], seq.NucleotideSequence)` for small literal aligned strings.
2. When constructing `Alignment` directly, ensure `trace.shape == (alignment_length, number_of_sequences)` and gaps are `-1`.
3. Ensure all rows in `profile.symbols` and `profile.gaps` refer to the same number of alignment columns.
4. When creating a profile matrix, verify `score_matrix.shape == (len(positional.alphabet), len(query.alphabet))` if aligning `(positional, query)`.
5. When reordering an MSA from `align.align_multiple()`, use `alignment[:, order.tolist()]` so sequence order matches the guide tree output.

## Too Many Optimal Alignments

Symptoms:

- `align.align_optimal()` returns a very large list or takes longer than expected.
- Repetitive or low-complexity sequences produce many equivalent traces.

Recovery:

1. Pass `max_number=1` or another small cap when only one representative alignment is needed.
2. Use local alignment for motif-like tasks and global alignment for end-to-end comparisons.
3. Increase gap penalties or adjust the substitution matrix if the scoring scheme creates many ties.
4. For long or repetitive sequences, use a k-mer/seed pipeline before gapped alignment.
5. Report that the returned alignment is one of possibly many equally optimal traces if the cap hides alternatives.

## Gap Penalty, Local/Global, And Terminal-gap Confusion

Symptoms:

- Unexpected leading/trailing gaps.
- Alignment score differs from a user expectation or another tool.
- Local alignment returns only a subsequence.

Recovery:

1. Use `local=False` for full-length global alignment; use `local=True` to find the best internal matching region.
2. Use `terminal_penalty=False` for semi-global behavior where overhangs should not be penalized.
3. Use a single integer `gap_penalty=-10` for linear penalties and a tuple such as `(-10, -1)` for affine gap opening/extension.
4. Recompute with `align.score(alignment, matrix, gap_penalty=..., terminal_penalty=...)` using the exact same scoring settings.
5. For nucleotide and protein alignments, do not reuse a matrix from the wrong alphabet.

## K-mer Search Pitfalls

Symptoms:

- Too many k-mer matches or no useful seeds.
- K-mer positions appear shifted.
- Masked positions still appear in matches.

Recovery:

1. Decrease `k` to increase sensitivity; increase `k` to reduce spurious matches.
2. Remember `table.match(query)` returns `(query_pos, ref_id, ref_pos)` rows.
3. Deduplicate by diagonal with `ref_pos - query_pos` or `query_pos - ref_pos` before extension, but keep the convention consistent with the band calculation.
4. When using masks, pass masks at table construction/query time so Biotite converts base masks to affected k-mer masks.
5. Use `spacing` only when spaced k-mers are intended; otherwise positions refer to contiguous k-mers.

## Annotation Coordinate Mistakes

Symptoms:

- Extracted feature sequence is off by one.
- Sliced `AnnotatedSequence` and raw `sequence` slice differ.
- Reverse-strand feature extraction is manually reverse-complemented twice.

Recovery:

1. Treat `Location(first, last)` as inclusive biological coordinates.
2. Treat `AnnotatedSequence[start:stop]` as annotation-coordinate slicing, not raw Python zero-based slicing.
3. Use `annotated[feature]` to extract multi-location and reverse-strand features safely.
4. Inspect `location.defect` after slicing annotations to understand truncated features.
5. Only manually reverse-complement when working outside `AnnotatedSequence` feature extraction.

## Profile And Consensus Issues

Symptoms:

- Consensus contains ambiguous symbols.
- Probability or log-odds values contain zeros or infinities.
- Query-profile alignment fails with matrix dimension errors.

Recovery:

1. Confirm the input alignment contains comparable columns; profiles cannot recover a bad MSA.
2. Use `pseudocount=1` or another justified pseudocount for probability/log-odds matrices.
3. Interpret ambiguous consensus as tied or mixed support, not as a parser failure.
4. For position-specific scoring, create `seq.PositionalSequence(profile.to_consensus())` and orient the substitution matrix axes to match the order of alignment inputs.
5. Convert log-odds matrices to integer scores before passing them to `align.SubstitutionMatrix`.

## Phylogeny And Newick Problems

Symptoms:

- `Tree.from_newick()` raises a parse/file error.
- Tree labels do not match expected leaves.
- Manual tree construction raises `TreeError`.

Recovery:

1. Pass the exact `labels` list to `Tree.from_newick()` when Newick uses names instead of numeric leaf indices.
2. Keep labels/sequences outside `Tree`; leaf nodes store integer indices only.
3. Do not reuse a `TreeNode` as a child of multiple parents.
4. Do not call `.as_root()` on a node that already has a parent.
5. Validate distance matrices are square and represent pairwise distances before `upgma()` or `neighbor_joining()`.

## Optional Matplotlib For Graphics

Symptoms:

- `ImportError: No module named matplotlib`.
- Plotting works locally but fails in a headless environment.
- Sequence analysis succeeds but feature maps/logos/dendrograms fail.

Recovery:

1. Separate data creation from plotting: build `Alignment`, `Annotation`, `SequenceProfile`, or `Tree` first.
2. Import `matplotlib.pyplot` and `biotite.sequence.graphics` only inside plotting code paths.
3. In headless scripts, select a noninteractive backend before importing `pyplot`, for example `matplotlib.use("Agg")`.
4. If the task is about display backends or optional visualization packages, route to `../../interfaces-visualization/SKILL.md`.
5. If plotting is optional, return tables/Newick/consensus strings as a non-graphics fallback.

## Smoke Helper Failures

Run:

```bash
python sub-skills/sequence-analysis/scripts/sequence_alignment_smoke.py --mode all
```

If it fails:

1. Confirm `biotite`, `biotite.sequence`, and `biotite.sequence.align` import in the active Python environment.
2. Run `--mode core`, `--mode alignment`, and `--mode profile` separately to isolate the failing surface.
3. Read the assertion message; the helper intentionally uses small deterministic expected values.
4. Do not add network calls, source checkout reads, or plotting dependencies to the helper; it is designed as an offline runtime check.
