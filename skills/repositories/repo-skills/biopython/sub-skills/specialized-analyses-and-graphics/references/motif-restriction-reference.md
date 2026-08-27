# Motif and Restriction Reference

## Purpose

Read this when the task involves `Bio.motifs`, JASPAR flat files, PWM/PSSM scoring, restriction enzyme searches, enzyme digests, or quick protein-property summaries. The examples are self-contained and assume only an installed Biopython package plus its base numeric dependency.

## Verified API snapshot

- `motifs.create(instances, alphabet="ACGT")` creates a `Motif` from equal-length instances.
- `motifs.parse(handle, fmt, strict=True)` reads zero or more motifs from a supported motif format.
- `motifs.read(handle, fmt, strict=True)` reads exactly one motif and raises when the handle has no motifs or multiple motifs.
- `format(motif, fmt)` and `motif.format(fmt)` support common writable formats including `pfm`, `jaspar`, `transfac`, and `clusterbuster`.
- `RestrictionBatch(first=(), suppliers=())` groups enzymes; `Analysis(restrictionbatch, sequence, linear=True)` maps a batch over a `Seq`/`MutableSeq`.
- `ProteinAnalysis(prot_sequence, monoisotopic=False)` calculates protein composition and physicochemical summaries.

## Motif creation, counts, PWM, and PSSM

Use `Bio.motifs` when the input is an aligned set of motif instances or a motif matrix, and you need a consensus, degenerate consensus, counts, PWM, PSSM, sequence scanning, or motif format conversion.

```python
from Bio import motifs
from Bio.Seq import Seq

instances = [Seq("TACAA"), Seq("TACGC"), Seq("TACAC"), Seq("TACCC")]
m = motifs.create(instances)

assert len(m) == 5
print(m.consensus)              # Seq-like consensus from highest counts
print(m.degenerate_consensus)   # IUPAC ambiguity where columns are mixed
print(m.counts["A"])            # counts row for A
print(m.counts["T", 0])         # row/column access

m.pseudocounts = 0.5
m.background = {"A": 0.3, "C": 0.2, "G": 0.2, "T": 0.3}
pssm = m.pssm
for position, score in pssm.search("TTACAATACGCT", threshold=0.0, both=True):
    print(position, score)
```

Operational notes:

- All instances passed to `motifs.create()` should have equal length.
- `m.counts` is a frequency-position matrix; use `m.counts[letter]`, `m.counts[letter, index]`, and `m.counts[:, index]` for row/column access.
- `m.pwm` normalizes counts using pseudocounts; `m.pssm` converts the PWM to log-odds using the background distribution.
- `pssm.calculate(sequence)` returns one score for same-length input or a numeric vector for longer input.
- `pssm.search(sequence, threshold=..., both=True)` yields `(position, score)` hits; reverse-strand hits are reported using negative coordinates as Biopython defines them.
- `m.relative_entropy` reports per-column information content in bits under the current background and pseudocount settings.
- `m.reverse_complement()` works for DNA/RNA motifs, not arbitrary alphabets.
- `m.weblogo(...)` is a network-backed service call; do not use it in offline validation.

## Motif formats and JASPAR boundaries

Use flat-file parsing for offline motif tasks:

```python
from io import StringIO
from Bio import motifs

pfm = """\
3 0 0 1
0 0 4 0
0 4 0 0
1 0 0 3
"""
m = motifs.read(StringIO(pfm), "pfm")
print(format(m, "jaspar"))
```

Supported `motifs.parse()`/`motifs.read()` families include:

- JASPAR-like: `pfm`, `jaspar`, `sites`, `pfm-four-columns`, `pfm-four-rows`.
- Motif finder output: `alignace`, `meme`, `minimal`, `mast`, `clusterbuster`, `xms`.
- Curated transcription-factor tables: `transfac`.

Routing rules:

- Use `motifs.read()` when a file is expected to contain exactly one motif.
- Use `motifs.parse()` when a file may contain multiple motifs or a motif-finder record.
- JASPAR flat files are owned here.
- JASPAR SQL/database connections require host, database, username, password, and network/database availability; route those tasks to the web/database sub-skill.

## Restriction enzyme workflows

Use `Bio.Restriction` when the task asks which enzymes cut a sequence, where they cut, how to digest a sequence, or how to filter enzymes by cut count/overhang/site size.

```python
from Bio.Seq import Seq
from Bio.Restriction import EcoRI, BamHI, RestrictionBatch, Analysis

seq = Seq("AAAAGAATTCTTTTGGATCC")
print(EcoRI.site)          # GAATTC
print(EcoRI.search(seq))   # one-based cut positions
print(EcoRI.catalyse(seq)) # tuple of Seq fragments; catalyze is an alias

batch = RestrictionBatch([EcoRI, BamHI])
analysis = Analysis(batch, seq, linear=True)
print(analysis.full())         # all enzymes in the batch
print(analysis.with_sites())   # enzymes with at least one cut
print(analysis.with_N_sites(1)) # enzymes cutting exactly once
print(analysis.overhang5())    # 5-prime overhang enzymes
```

Operational notes:

- Search input must be a `Seq`, `MutableSeq`, or `FormattedSeq`, not a raw string.
- Search results are biological one-based cut positions, not Python zero-based indices.
- Set `linear=False` on `search()`, `catalyse()`, or `Analysis(...)` for circular molecules.
- `RestrictionBatch(["EcoRI", EcoRI])` accepts enzyme names or enzyme classes, and `EcoRI in batch`/`"EcoRI" in batch` are valid membership checks.
- `AllEnzymes`, `CommOnly`, and supplier-based batches are convenient for broad screens, but start with a small batch for examples and tests.
- Useful filters include `with_sites()`, `without_site()`, `with_N_sites(N)`, `with_name(names)`, `with_site_size(size)`, `blunt()`, `overhang5()`, `overhang3()`, `defined()`, `between(start, end)`, and `only_between(start, end)`.

## ProteinAnalysis quick reference

Use `Bio.SeqUtils.ProtParam.ProteinAnalysis` for protein composition and simple physicochemical summaries. For sequence manipulation, translation, or validation of the protein sequence itself, route back to the sequence-objects sub-skill.

```python
from Bio.SeqUtils.ProtParam import ProteinAnalysis

analysis = ProteinAnalysis("MAIVMGRWKGAR")
print(analysis.count_amino_acids())
print(analysis.amino_acids_percent["M"])
print(analysis.molecular_weight())
print(analysis.aromaticity())
print(analysis.instability_index())
print(analysis.isoelectric_point())
print(analysis.gravy())
print(analysis.secondary_structure_fraction())
```

Common methods/properties:

- `count_amino_acids()` returns counts for standard amino acids and caches them.
- `amino_acids_percent` returns percentages in the range 0 to 100.
- `molecular_weight()`, `aromaticity()`, `instability_index()`, `isoelectric_point()`, `gravy()`, `charge_at_pH(pH)`, `secondary_structure_fraction()`, and `molar_extinction_coefficient()` calculate derived summaries.
- `protein_scale(param_dict, window, edge=1.0)` computes a sliding-window profile for user-supplied amino-acid scales.
