# Biopython sequence object and feature API reference

This reference covers in-memory Biopython sequence objects and utilities. It assumes a Biopython package is importable; it does not require the original repository, network access, external executables, or sequence fixture files.

## Core imports

```python
from Bio.Seq import Seq, MutableSeq
from Bio.Seq import translate, transcribe, back_transcribe, reverse_complement
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import (
    SeqFeature,
    SimpleLocation,
    CompoundLocation,
    Location,
    ExactPosition,
    BeforePosition,
    AfterPosition,
    WithinPosition,
    OneOfPosition,
    UnknownPosition,
)
from Bio.Data.CodonTable import TranslationError
from Bio.SeqUtils import gc_fraction, molecular_weight, nt_search, seq1, seq3
```

## Verified constructor/function signatures

Inspected package facts for Biopython `1.89.dev0` include these signatures:

| Object or function | Signature |
|---|---|
| `Seq` | `(data: str | bytes | bytearray | Bio.Seq._SeqAbstractBaseClass | Bio.Seq.SequenceDataAbstractBaseClass | dict | None, length: int | None = None)` |
| `MutableSeq` | `(data)` |
| `SeqRecord` | `(seq: Seq | MutableSeq | None, id='<unknown id>', name='<unknown name>', description='<unknown description>', dbxrefs=None, features=None, annotations=None, letter_annotations=None)` |
| `SeqFeature` | `(location=None, type='', id='<unknown id>', qualifiers=None, sub_features=None)` |
| `SimpleLocation` | `(start, end, strand=None, ref=None, ref_db=None)` |
| `CompoundLocation` | `(parts, operator='join')` |
| `translate` | `(sequence, table='Standard', stop_symbol='*', to_stop=False, cds=False, gap=None)` |
| `transcribe` | `(dna)` |
| `back_transcribe` | `(rna)` |
| `reverse_complement` | `(sequence, inplace=False)` |
| `gc_fraction` | `(seq, ambiguous='remove')` |
| `molecular_weight` | `(seq, seq_type='DNA', double_stranded=False, circular=False, monoisotopic=False)` |

## `Seq` and `MutableSeq`

- `Seq` is immutable and string-like. It supports indexing, slicing, membership, counting/searching, and biological methods such as `.translate()`, `.transcribe()`, `.back_transcribe()`, `.complement()`, and `.reverse_complement()`.
- `MutableSeq` supports mutation and in-place forms for supported biological methods. Calling in-place methods on an immutable `Seq` raises `TypeError`.
- Module-level helpers preserve string inputs as strings for transcription/back-transcription, but return sequence objects for `Seq`/`MutableSeq` inputs.
- `reverse_complement()` treats `U` as `T` for DNA reverse complements. Use RNA-specific methods (`reverse_complement_rna`) when the output should contain `U`.

Minimal examples:

```python
dna = Seq("ATGGCC")
assert str(dna.translate()) == "MA"
assert str(dna.transcribe()) == "AUGGCC"
assert str(dna.reverse_complement()) == "GGCCAT"

mutable = MutableSeq("ATGGCC")
mutable.reverse_complement(inplace=True)
assert str(mutable) == "GGCCAT"
```

## Translation and codon tables

`Seq.translate()` and the module-level `translate()` accept a genetic table name, NCBI integer table id, or codon table object.

Important arguments:

- `stop_symbol`: symbol used for stop codons when `to_stop=False`.
- `to_stop=True`: stop at the first in-frame stop codon and omit the stop symbol.
- `cds=True`: enforce complete coding sequence rules.
- `gap`: single-character gap marker; a gapped codon of that character is preserved as the gap symbol.

For `cds=True`, Biopython checks:

1. the first codon is a valid start codon for the selected table;
2. the sequence length is a multiple of three;
3. the final codon is a valid stop codon;
4. there are no extra in-frame stop codons before the terminal stop.

Failures raise `Bio.Data.CodonTable.TranslationError`. Ambiguous codons that could encode an amino acid or stop are translated as `X`; invalid codons such as `TA?` raise `TranslationError`. A non-CDS sequence whose length is not a multiple of three emits a warning and translates only complete codons.

## `SeqRecord`

A `SeqRecord` stores a `Seq` or `MutableSeq` plus identifiers, annotations, feature annotations, and per-letter data.

Main fields:

- `.seq`: the sequence object; must be `Seq`, `MutableSeq`, or `None`.
- `.id`, `.name`, `.description`: plain strings used by many writers and displays.
- `.dbxrefs`: list of database cross-reference strings.
- `.annotations`: whole-record dictionary. Common keys include `molecule_type` and `topology`.
- `.features`: list of `SeqFeature` objects.
- `.letter_annotations`: restricted dictionary; every value must be a sequence exactly as long as `.seq`.

Slicing behavior:

- `record[i]` returns a single letter from `record.seq`.
- `record[start:stop]` returns a new `SeqRecord` with the sliced sequence.
- `id`, `name`, and `description` are preserved.
- Per-letter annotations are sliced to the same range.
- Only fully-contained features are preserved, and their locations are shifted to the new coordinate system.
- Whole-record annotations and `dbxrefs` are not generally preserved; `molecule_type` is the main exception.

Concatenation behavior:

- Adding a string/`Seq` to a `SeqRecord` preserves many record-level fields but drops per-letter annotations because their length can no longer be trusted.
- Adding two compatible `SeqRecord` objects concatenates sequences and attempts to combine consistent fields and features.

## `SeqFeature`, `SimpleLocation`, and `CompoundLocation`

Use `SeqFeature(location, type, id, qualifiers)` to describe an annotated span. `qualifiers` is a dictionary whose values are typically lists, especially when parsed from feature-table formats.

Coordinate rules:

- Biopython uses zero-based, half-open coordinates: `[start:end]` includes `start` and excludes `end`.
- A feature from an INSDC one-based location `123..150` corresponds to `[122:150]`.
- For reverse-strand locations, `.start` and `.end` are still the leftmost and rightmost boundaries, not biological 5-prime/3-prime coordinates.
- `strand` should be `+1`, `-1`, `0` for stranded but unknown, or `None` when strand does not apply.

Simple feature extraction:

```python
record = SeqRecord(Seq("AAACCCGGGTTT"), id="toy", annotations={"molecule_type": "DNA"})
feature = SeqFeature(SimpleLocation(3, 9, strand=1), type="domain")
assert str(feature.extract(record.seq)) == "CCCGGG"
assert str(feature.extract(record).seq) == "CCCGGG"
```

Reverse-strand extraction reverse-complements the slice:

```python
feature = SeqFeature(SimpleLocation(3, 9, strand=-1), type="domain")
assert str(feature.extract(Seq("AAACCCGGGTTT"))) == "CCCGGG"
```

A `CompoundLocation` joins multiple `SimpleLocation` parts. The `+` operator is a concise construction method:

```python
loc = SimpleLocation(0, 9, strand=1) + SimpleLocation(12, 15, strand=1)
feature = SeqFeature(loc, type="CDS", qualifiers={"transl_table": [1]})
parent = Seq("ATGAAATTTCCCTAA")
assert str(feature.extract(parent)) == "ATGAAATTTTAA"
assert str(feature.translate(parent)) == "MKF"
```

For an origin-spanning feature on a circular molecule, build the wrapped location as a compound location with the tail part followed by the head part:

```python
circular = SeqRecord(
    Seq("AAACCCGGGTTT"),
    id="circle",
    annotations={"molecule_type": "DNA", "topology": "circular"},
)
wrapped = SeqFeature(
    CompoundLocation([SimpleLocation(9, 12, strand=1), SimpleLocation(0, 3, strand=1)]),
    type="misc_feature",
)
assert str(wrapped.extract(circular.seq)) == "TTTAAA"
assert list(wrapped.location) == [9, 10, 11, 0, 1, 2]
```

`Location.fromstring(text, length=None, circular=False, stranded=True)` can parse feature-table style locations into `SimpleLocation` or `CompoundLocation`. Provide `length` and `circular=True` for origin-spanning locations; otherwise parser errors are expected for apparent wrapped coordinates.

## Fuzzy positions

Position classes retain uncertainty while still acting like integer-like boundaries for many operations:

- `ExactPosition(n)`: exact boundary.
- `BeforePosition(n)`: boundary before `n`; string form like `<n`.
- `AfterPosition(n)`: boundary after `n`; string form like `>n`.
- `WithinPosition(default, left, right)`: boundary within a range; string form like `(left.right)`.
- `OneOfPosition(default, choices=[...])`: one of several explicit choices.
- `UnknownPosition()`: unknown boundary; comparisons and numeric slicing may not be possible.

When slicing or extracting, Biopython uses the integer value of fuzzy positions. Keep the original position object if you must report uncertainty to the user.

## Feature translation

`SeqFeature.translate(parent_sequence, table='Standard', start_offset=None, stop_symbol='*', to_stop=False, cds=None, gap=None)` is a shortcut for extract-then-translate.

Key behavior:

- It extracts the feature sequence first, so strand and compound locations are honored.
- If `qualifiers['transl_table']` is present, it overrides the `table` argument.
- If `qualifiers['codon_start']` is present, it is interpreted as one-based and converted to a zero-based `start_offset`.
- If `cds` is omitted, features with `type == 'CDS'` are treated as complete CDS (`cds=True`); other feature types default to non-CDS translation.

## Reverse-complementing `SeqRecord`

`SeqRecord.reverse_complement()` returns a new record.

Defaults and cautions:

- Does not preserve `id`, `name`, `description`, `dbxrefs`, or general `.annotations` unless requested.
- Preserves and flips features by default.
- Reverses per-letter annotations by default if they exist.
- Uses RNA complement if `annotations['molecule_type']` contains `RNA`; otherwise defaults to DNA.
- Raises `ValueError` for records annotated as protein.
- Copies feature qualifiers, but does not biologically rewrite strand-specific qualifier text such as SNP descriptions.

Use explicit arguments when preserving metadata is intended:

```python
rc = record.reverse_complement(
    id=True,
    name=True,
    description=True,
    dbxrefs=True,
    annotations=True,
    letter_annotations=True,
    features=True,
)
```

## `Bio.SeqUtils` helpers

Common base-safe utilities:

- `gc_fraction(seq, ambiguous='remove')`: returns a fraction from 0 to 1. Modes are `remove`, `ignore`, and `weighted`.
- `GC_skew(seq, window=100)`: returns `(G-C)/(G+C)` per window, with zero for windows lacking G/C.
- `nt_search(seq, subseq)`: searches a DNA sequence for an ambiguous-IUPAC subsequence on the forward strand.
- `seq3(protein)`: one-letter protein sequence to three-letter codes.
- `seq1(three_letter_sequence)`: three-letter protein string to one-letter codes.
- `molecular_weight(seq, seq_type='DNA'|'RNA'|'protein', double_stranded=False, circular=False, monoisotopic=False)`: requires unambiguous letters.
- `CodonAdaptationIndex(sequences, table=standard_dna_table)`: builds a codon-usage table from complete codon sequences; `.calculate(sequence)` scores a DNA sequence; `.optimize(sequence, seq_type='DNA', strict=True)` returns preferred codons.

Example assertions:

```python
assert gc_fraction("ACTGN", ambiguous="weighted") == 0.5
assert round(molecular_weight("AGC", seq_type="DNA"), 2) == 949.61
assert seq1(seq3("MAIVMGR*")) == "MAIVMGR*"
assert nt_search("ATGCAT", "ATN")[1:] == [0]
```
