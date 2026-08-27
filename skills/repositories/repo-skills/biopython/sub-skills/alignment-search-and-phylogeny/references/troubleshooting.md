# Alignment/search/phylogeny troubleshooting

Use this reference when Biopython alignment, search-result, BLAST, or tree workflows fail or produce unexpected output.

## Import and installation failures

Symptom: `ImportError` from `Bio.Align`, `_aligncore`, `_pairwisealigner`, or other compiled modules.

Likely causes and fixes:

- The package is being imported from an unbuilt source tree rather than from an installed Biopython package. Run the code in an environment where Biopython has been installed normally.
- NumPy is missing or incompatible. Install a compatible NumPy because `Bio.Align` depends on it.
- Editable/source installs may require a compiler to build C extensions. If compiled extension imports fail, reinstall Biopython and check the build log.

Symptom: a Biopython source-tree warning appears.

- Do not silence this until confirming imports actually work. It may be harmless for editable development installs, but it can also precede compiled-extension failures.

## PairwiseAligner scoring surprises

Symptom: scores are higher/lower than expected.

Checklist:

1. Confirm `aligner.mode` is `"global"` or `"local"` as intended.
2. Print the aligner to inspect all gap settings; meta-attributes such as `open_gap_score` set several more specific insertion/deletion scores.
3. Check that match, mismatch, and gap signs are correct. Gap penalties are usually negative.
4. If using a substitution matrix, confirm every sequence character is in `matrix.alphabet`.
5. Remember that `mismatch_score` defaults can be permissive; set it explicitly for nucleotide alignments.
6. Compare floating-point scores with tolerance when using fractional penalties.

Symptom: too many optimal alignments or slow alignment enumeration.

- Use `aligner.score(target, query)` when only the score is needed.
- Consume only the first few alignments from `aligner.align(...)` when the user does not need every tie.
- Avoid `len(alignments)` for cases that may have an enormous number of optimal alignments.
- Tighten gap or mismatch penalties if ties are biologically unhelpful.

Symptom: local alignment returns no useful region.

- Local alignments require a positive-scoring region. Increase match/substitution rewards or relax penalties.
- Check whether ambiguous characters are being scored as zero, mismatches, or matrix-specific values.

Symptom: old code imports `Bio.pairwise2` and emits a deprecation warning.

- Prefer `Bio.Align.PairwiseAligner` for new code.
- During migration, assert score equality and inspect tie ordering because the old API returns named tuples while the new API returns `Alignment` objects with coordinates.

## AlignIO parser/writer problems

Symptom: `read` raises because zero or multiple alignments were found.

- Use `AlignIO.read` only when exactly one alignment is expected.
- Use `AlignIO.parse` for a file/handle that may contain multiple alignments.

Symptom: unsupported format or writer failure.

- Confirm the exact lowercase format name. Verified read/parse names include `clustal`, `emboss`, `fasta-m10`, `maf`, `mauve`, `msf`, `nexus`, `phylip`, `phylip-relaxed`, `phylip-sequential`, and `stockholm`.
- Confirm write support separately; not every readable format is writable.
- For broad file conversion, indexing, compression, or FASTA/FASTQ/GenBank questions, route to the file-I/O sub-skill.

Symptom: alignment length or row access looks wrong.

- Multiple-sequence alignments require rows of equal aligned length.
- Gaps are part of the aligned representation; use source sequence records or alignment coordinates when mapping back to ungapped coordinates.

## SearchIO parse/index/write failures

Symptom: `SearchIO.read` raises `ValueError`.

- `read` requires exactly one query result. Use `SearchIO.parse` for multi-query output.

Symptom: a BLAST tabular file parses incorrectly.

- Determine whether the file has comment/header lines. Pass `comments=True` for commented BLAST tabular output.
- Confirm the columns are default or provide the format-specific field list if using custom tabular columns.

Symptom: HMMER domain-table coordinates look swapped.

- Choose the specific format name that matches the program: `hmmscan3-domtab`, `hmmsearch3-domtab`, or `phmmer3-domtab`.

Symptom: coordinates seem off by one.

- `SearchIO` normalizes coordinates to zero-based, half-open Python intervals. This differs from many search output files but is correct for Python slicing.

Symptom: `SearchIO.write` fails after filtering or conversion.

- Writers require format-specific attributes. A parser may not populate every field needed by a different writer.
- Preserve full `QueryResult`/`Hit`/`HSP`/`HSPFragment` objects when filtering.
- If a writer still lacks required attributes, produce a custom TSV/CSV summary instead of forcing a lossy format conversion.

## Bio.Blast parser problems

Symptom: `Bio.Blast.parse` or `Bio.Blast.read` says the XML is invalid/corrupted.

- Confirm the input is BLAST XML, not HTML, text, JSON, or an error page.
- If using a file-like object, open it in binary mode (`rb`).
- Use `Bio.Blast.read` only for a single BLAST record; use `Bio.Blast.parse` for multiple records.

Symptom: `Bio.Blast.write` raises a stream mode error.

- Open file-like destinations in binary write mode (`wb`) or pass a filename/path.
- Use `fmt="XML"` or `fmt="XML2"`; other output names are not accepted by `Bio.Blast.write`.

Symptom: qblast is requested.

- Treat it as a live network operation. Require explicit user approval, configured contact metadata, clear program/database/sequence parameters, and responsible polling/batching.
- Never run qblast as part of offline verification or smoke tests.
- Save the returned result stream before parsing so the search does not need to be repeated.

## Phylo tree failures

Symptom: `Phylo.read` raises for zero or multiple trees.

- Use `Phylo.parse` and handle the number of trees explicitly.

Symptom: expected clade is not found.

- Confirm whether the target is a terminal leaf or an internal clade.
- String matches in tree searches use regular-expression behavior for names; escape user-provided names with regex metacharacters or use a callable predicate.
- Some formats may store labels in annotations rather than simple `name` attributes.

Symptom: tree modification unexpectedly changes branch lengths or root.

- Methods such as `prune`, `collapse`, `root_with_outgroup`, and `root_at_midpoint` mutate in place.
- Use `copy.deepcopy(tree)` before destructive edits.
- Reassert invariants after editing: terminal names, terminal count, root name, distances, monophyly, or total branch length.

Symptom: drawing or graph conversion imports fail.

- `draw_ascii` is base-safe.
- `draw`, `to_networkx`, `to_igraph`, and some CDAO/RDF workflows need optional packages. Missing optional visualization/graph/RDF dependencies are not base Biopython failures.

## Optional external tools

External aligners, BLAST+, PAML, and related executables are not required for this sub-skill's base workflows. If a user asks to run one:

1. Check the executable with a PATH lookup.
2. Check that required databases/input files exist and are small enough for the task budget.
3. Run with explicit command arguments and bounded output paths.
4. Parse resulting files with `AlignIO`, `SearchIO`, or `Phylo` as appropriate.
5. Document the external tool version separately from Biopython behavior.
