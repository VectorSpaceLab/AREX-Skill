---
name: alignment-io
description: "Guides agents using pysam for SAM/BAM/CRAM AlignmentFile I/O,
  headers, AlignedSegment editing, fetch/count/coverage, pileup, read
  flags/tags/CIGAR, stream handling, quality helpers, and coordinate
  conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pysam alignment I/O

Use this sub-skill when a task involves SAM, BAM, or CRAM alignment files through `pysam.AlignmentFile` and `pysam.AlignedSegment`: opening files, writing headers and reads, random-access fetching, counting coverage, pileup columns, flags, tags, CIGAR handling, streaming stdin/stdout, or quality string conversion.

## Route by task

- For API signatures and object contracts, read [references/api-reference.md](references/api-reference.md).
- For practical open/fetch/write/pileup/streaming recipes, read [references/workflows.md](references/workflows.md).
- For index, coordinate, iterator, CRAM reference, header, and proxy-lifetime failures, read [references/troubleshooting.md](references/troubleshooting.md).
- To prove a local pysam install can write and read a tiny alignment without source fixtures, run `python sub-skills/alignment-io/scripts/alignment_smoke.py --help` and then run the helper with an output directory.

## Boundaries

- Use this sub-skill for `AlignmentFile`, `AlignmentHeader`, `AlignedSegment`, `PileupColumn`, `PileupRead`, `IndexedReads`, `qualitystring_to_array`, `array_to_qualitystring`, `qualities_to_qualitystring`, `reverse_complement`, and `reverse_complement_inplace`.
- For VCF/BCF headers and records, use `../variant-io/SKILL.md`.
- For tabix-indexed tables or FASTA random access/indexing, use `../tabix-fasta/SKILL.md`.
- For invoking bundled samtools/bcftools commands such as `sort`, `index`, `view`, or `mpileup`, use `../command-wrappers/SKILL.md`.
- For compilation, linking, wheel, or installation failures, use `../troubleshooting-build/SKILL.md`.

## Defaults that prevent common mistakes

- Treat pysam integer coordinates as 0-based, half-open intervals; only `region="chr:start-stop"` strings follow samtools 1-based closed-style conventions.
- Prefer `with pysam.AlignmentFile(...) as handle:` so C-backed file handles close promptly.
- Use `fetch(until_eof=True)` for unindexed sequential scans and for unmapped reads that normal indexed `fetch()` skips.
- Use `multiple_iterators=True` only when two active iterators must coexist on one file handle; it reopens the file and has a cost.
- Keep pileup iterators alive while reading `PileupColumn.pileups` or helper methods; pileup proxy data becomes invalid after the iterator advances or finishes.
- When editing `AlignedSegment.query_sequence`, preserve and restore `query_qualities` because sequence assignment invalidates qualities.
