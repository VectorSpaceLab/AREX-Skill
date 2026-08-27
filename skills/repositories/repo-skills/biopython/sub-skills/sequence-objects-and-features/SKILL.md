---
name: sequence-objects-and-features
description: "Operate Biopython Seq, MutableSeq, SeqRecord, SeqFeature,
  location, codon-table, and SeqUtils workflows without file parsing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# sequence-objects-and-features

Use this sub-skill when the task is about in-memory Biopython sequence objects, record annotations, feature locations, translation/transcription/reverse-complement logic, codon tables, or `Bio.SeqUtils` helpers.

## Route here

- Build or transform `Seq`, `MutableSeq`, or `SeqRecord` objects from already-available sequence strings or records.
- Add, inspect, slice, extract, shift, or reverse-complement `SeqFeature`, `SimpleLocation`, `CompoundLocation`, and fuzzy positions.
- Diagnose translation behavior for complete CDS features, `codon_start`, `transl_table`, start/stop codon checks, and ambiguous codons.
- Work with `SeqRecord.annotations`, `dbxrefs`, `features`, and length-checked `letter_annotations`.
- Use safe sequence utilities such as `gc_fraction`, `molecular_weight`, `nt_search`, `seq1`, `seq3`, `GC_skew`, and `CodonAdaptationIndex`.

## Route elsewhere

- Sequence/alignment/search file parsing, writing, indexing, or format conversion: use `file-io-and-format-conversion`.
- Pairwise/multiple alignments, BLAST/SearchIO result models, and phylogenetic trees: use `alignment-search-and-phylogeny`.
- PDB/mmCIF structures, SMCRA traversal, polypeptide extraction from structures, and structural superposition: use `structural-bioinformatics`.
- Online database retrieval, Entrez/KEGG web access, and BioSQL storage: use `web-databases-and-biosql`.

## Operating procedure

1. Identify the object level: raw string, `Seq`/`MutableSeq`, `SeqRecord`, `SeqFeature`, or `Location`.
2. Keep coordinates explicit: Biopython feature coordinates are Python-style zero-based, half-open intervals; reverse-strand locations still use left/right genomic boundaries.
3. Preserve annotation intentionally: slicing, concatenation, translation, and reverse-complementing do not preserve every field by default.
4. For CDS translation, inspect the genetic table, `codon_start`, length modulo three, start codon, terminal stop codon, and internal stops before changing code.
5. For non-trivial behavior or environment checks, run `scripts/sequence_feature_smoke.py`; it uses only in-memory data and should print `PASS`.

## Bundled references

- `references/sequence-feature-api.md` — verified API signatures, object relationships, coordinate rules, feature extraction recipes, and SeqUtils notes.
- `references/troubleshooting.md` — failure diagnosis for annotations, locations, reverse complements, CDS translation, and utilities.
