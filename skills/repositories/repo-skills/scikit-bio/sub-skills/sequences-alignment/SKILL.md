---
name: sequences-alignment
description: "Construct, transform, compare, and align scikit-bio biological
  sequences and TabularMSA objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# scikit-bio Sequences and Alignment

Use this sub-skill when a task involves constructing `Sequence`, `DNA`, `RNA`, or `Protein` objects; preserving or slicing sequence metadata; transforming nucleotides; translating with `GeneticCode`; scoring substitutions; creating or indexing `TabularMSA`; computing alignment scores/distances; or aligning two sequences with scikit-bio.

## Route Here For

- Creating `DNA`, `RNA`, `Protein`, or generic `Sequence` instances with metadata, positional metadata, interval metadata, lowercase handling, or validation choices.
- Inspecting grammar state such as gaps, degenerates, definites, wildcard characters, or alphabets, and using `degap`, complement, transcription, reverse transcription, or translation workflows.
- Running pairwise alignment with `pair_align`, `pair_align_nucl`, or `pair_align_prot`, then converting `PairAlignPath` results to aligned strings or `TabularMSA`.
- Building `TabularMSA` objects, indexing rows/columns, deriving consensus/conservation summaries, converting to or from `AlignPath`, and computing `align_score` or `align_dists`.
- Troubleshooting invalid characters, lowercase/validation behavior, metadata length mismatches, translation stop handling, substitution/gap scoring, or MSA shape/index errors.

## Start With

- `references/api-reference.md` for concrete signatures, defaults, and object roles.
- `references/workflows.md` for copy-ready recipes covering construction, transformation, alignment, MSA, scoring, and distance workflows.
- `references/troubleshooting.md` for diagnosis tables and repair patterns.
- `scripts/sequence_alignment_smoke.py` for a small deterministic API smoke check that prints JSON.

## Boundaries

- For file-format reading/writing, FASTA parsing, metadata serialization, or I/O registry details, use `../io-metadata/SKILL.md` and return here after sequences or `TabularMSA` objects exist.
- For tree construction or phylogenetic interpretation of alignment-derived distances, use `../trees-phylogeny/SKILL.md`.
- For distance-matrix statistics, ordination, PERMANOVA, or downstream statistical tests, use `../statistics-ordination/SKILL.md`.
- Treat deprecated `global_pairwise_align*` and `local_pairwise_align*` wrappers as legacy/educational APIs only; prefer `pair_align`, `pair_align_nucl`, and `pair_align_prot`.

## Quick Sanity Check

From this sub-skill directory with scikit-bio installed, run:

```bash
python scripts/sequence_alignment_smoke.py
```

The script itself is safe to execute from arbitrary working directories when addressed by its file path. It imports only public `skbio` APIs, constructs sequence objects, aligns short DNA sequences, builds a `TabularMSA`, and prints a compact JSON summary.
