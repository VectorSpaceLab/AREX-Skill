# Sequence object and feature troubleshooting

Use this when a Biopython sequence, record, feature, location, translation, or sequence-utility task behaves unexpectedly. Start with a tiny in-memory reproduction before involving file parsing or external data.

## First smoke check

Run the bundled smoke script in any environment with Biopython installed:

```bash
python scripts/sequence_feature_smoke.py
```

Expected output:

```text
PASS
```

The script checks `Seq` translation/reverse-complement, `SeqRecord` annotations and slicing, compound/circular feature extraction, `SeqFeature.translate`, `Bio.SeqUtils`, and a caught CDS translation failure.

## Object construction errors

### `TypeError: seq argument should be a Seq or MutableSeq object`

`SeqRecord` does not accept a plain string as `.seq`.

```python
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

record = SeqRecord(Seq("ACGT"), id="ok")
```

### Mutable versus immutable sequences

- `Seq` is immutable. In-place operations such as `Seq("ACG").reverse_complement(inplace=True)` raise `TypeError`.
- Use `MutableSeq` when in-place mutation is required, or assign the returned object from immutable operations.

## Per-letter annotation failures

### Length mismatch at creation or assignment

Every `record.letter_annotations[key]` value must have the same length as `record.seq`.

```python
record.letter_annotations["quality"] = [30] * len(record)
```

If a value has the wrong length, Biopython raises `TypeError` or `ValueError`.

### Cannot change sequence length while letter annotations exist

If non-empty per-letter annotations exist, replacing `.seq` with a different length raises:

```text
ValueError: You must empty the letter annotations first!
```

Fix:

```python
record.letter_annotations = {}
record.seq = Seq("ACGTACGT")
```

Only do this if dropping the old per-letter data is biologically valid.

## Annotation preservation surprises

### Slicing `SeqRecord`

`record[start:stop]` preserves `id`, `name`, `description`, slices per-letter annotations, and keeps only features fully contained in the slice. Most `.annotations` and `.dbxrefs` are not preserved; copy them intentionally if they still apply.

```python
sub = record[100:200]
sub.annotations["source_record"] = record.id
```

### Translation of `SeqRecord`

`record.translate()` creates a protein record and sets `annotations['molecule_type'] = 'protein'`. It does not copy features or per-letter annotations by default, because nucleotide coordinates and qualities usually no longer match protein coordinates.

If you supply `features=True` or `letter_annotations=True`, Biopython raises `TypeError`; provide explicit protein-coordinate features or protein-length letter annotations instead.

## Location coordinate mistakes

### Off-by-one errors

Biopython feature locations are zero-based and half-open:

```python
SimpleLocation(0, 3).extract(Seq("ATGAAA"))  # ATG
```

A one-based inclusive feature `123..150` becomes `SimpleLocation(122, 150)`.

### Reverse strand still uses left/right boundaries

For `SimpleLocation(start, end, strand=-1)`, `start` is still the smaller coordinate and `end` is still the larger coordinate. Biopython reverse-complements the extracted slice when extracting.

### `ValueError: End location (...) must be greater than or equal to start location`

Do not pass biologically reversed coordinates for reverse-strand features. Use `SimpleLocation(left, right, strand=-1)`.

### Origin-spanning circular features

Do not force a single `SimpleLocation` with `start > end`. Use a `CompoundLocation` with the tail part followed by the head part, and annotate the record topology if useful:

```python
record.annotations["topology"] = "circular"
wrapped = CompoundLocation([SimpleLocation(900, 1000, strand=1), SimpleLocation(0, 50, strand=1)])
```

If parsing a feature-location string, provide the sequence length and `circular=True`; otherwise an apparent origin-spanning feature should fail rather than silently guessing.

### Fuzzy or unknown positions

Fuzzy positions such as `BeforePosition`, `AfterPosition`, `WithinPosition`, and `OneOfPosition` are integer-like for many operations, but their uncertainty matters for reporting and validation. `UnknownPosition` may fail numeric comparisons and feature-preservation logic. Keep fuzzy position objects in output explanations rather than converting everything to `int()` unless the approximation is acceptable.

## Feature extraction errors

### Feature location is `None`

`SeqFeature(None, ...)` cannot be extracted:

```text
ValueError: The feature's .location is None. Check the sequence file for a valid location.
```

Fix the upstream annotation or skip that feature with a clear warning.

### External-reference location errors

Locations can reference another sequence via `ref`/`ref_db`. If a location references another record, extraction requires a `references` dictionary.

Typical failures:

```text
Feature references another sequence (...), references mandatory
Feature references another sequence (...), not found in references
```

Fix:

```python
extracted = feature.extract(parent_record, references={"OTHER.1": other_record})
```

## Reverse-complement problems

### Protein records

`SeqRecord.reverse_complement()` raises `ValueError` for records whose `annotations['molecule_type']` contains `protein`.

Fix: route protein operations to protein sequence utilities; proteins do not have nucleotide complements.

### RNA records with no `U`

A record with `Seq("ACG")` is treated as DNA by default. If it is RNA, set:

```python
record.annotations["molecule_type"] = "RNA"
```

Then reverse-complementing returns RNA bases with `U`.

### Lost identifiers or annotations after reverse complement

By default, reverse-complemented records do not preserve identifiers, descriptions, general annotations, database cross-references, or general metadata. Preserve only what remains true:

```python
rc = record.reverse_complement(id=True, name=True, description=True, annotations=True, dbxrefs=True)
```

Feature locations are flipped by default, but qualifier text is copied as-is. Manually rewrite strand-specific notes, alleles, or primer names when needed.

## CDS translation diagnosis

`SeqFeature.translate(parent)` treats `type == 'CDS'` as `cds=True` unless overridden. Complete-CDS checks can fail for several reasons.

Use a diagnostic helper before changing table or frame blindly:

```python
from Bio.Data.CodonTable import TranslationError


def diagnose_cds(feature, parent_sequence):
    extracted = feature.extract(parent_sequence)
    table = feature.qualifiers.get("transl_table", ["Standard"])[0]
    codon_start = int(feature.qualifiers.get("codon_start", [1])[0])
    offset = codon_start - 1
    coding = extracted[offset:]
    info = {
        "table": table,
        "codon_start": codon_start,
        "start_offset": offset,
        "length": len(coding),
        "length_mod_3": len(coding) % 3,
        "first_codon": str(coding[:3]),
        "final_codon": str(coding[-3:]) if len(coding) >= 3 else str(coding),
    }
    try:
        info["translation"] = str(feature.translate(parent_sequence))
    except TranslationError as err:
        info["error"] = str(err)
    return info
```

Common CDS failures:

- First codon is not a start codon for the selected table.
- Sequence length after `codon_start` is not a multiple of three.
- Final codon is not a stop codon for the selected table.
- Extra in-frame stop codon appears before the terminal stop.
- `transl_table` differs from the biological organism or source annotation.
- `codon_start` is one-based in qualifiers; `start_offset` is zero-based in the API.

Temporary bypass for exploratory work:

```python
protein = feature.translate(parent_sequence, cds=False)
```

Only use `cds=False` when the feature is partial or you have explicitly decided not to enforce complete-CDS rules.

## General translation errors and warnings

- Invalid codons such as `TA?` raise `TranslationError`.
- Ambiguous valid codons such as `TAN` or `NNN` translate as `X`.
- Non-CDS partial codons emit a warning and are likely to become stricter in future versions; trim or pad intentionally.
- Some codon tables have dual-coding stop codons. With these tables, `to_stop=True` may raise `ValueError`; inspect the table before using `to_stop`.
- The `table` argument is a codon table name/id/object, not a Python string translation map. Use `str(seq).translate(...)` only for Python character mapping.

## SeqUtils pitfalls

### `gc_fraction`

Valid `ambiguous` modes are only `remove`, `ignore`, and `weighted`.

- `remove`: remove ambiguous bases from the denominator, except bases such as `S` and `W` handled by the function.
- `ignore`: keep ambiguous bases in the denominator but do not count them as GC unless unambiguous.
- `weighted`: count ambiguous bases using mean GC weights.

### `molecular_weight`

`molecular_weight` requires unambiguous letters for the selected `seq_type`. Ambiguous bases or amino acids raise `ValueError`. Set `seq_type` explicitly to avoid treating RNA or protein strings as DNA.

### `CodonAdaptationIndex`

Input sequences are counted in codons. Illegal or incomplete codons raise errors during index construction or calculation. Validate length modulo three and restrict to DNA codons before computing CAI.

## When to route away

- If the failure involves opening, parsing, indexing, converting, or writing a file, route to the file I/O sub-skill.
- If the failure involves pairwise/multiple alignments, BLAST output, SearchIO, or trees, route to the alignment/search/phylogeny sub-skill.
- If the failure involves residues, atoms, chains, PDB/mmCIF, or structural geometry, route to the structural sub-skill.
