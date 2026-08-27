# Specialized Workflows

## Purpose

Read this for Biopython specialized modules that are not owned by the core sequence, file-I/O, alignment/search/phylogeny, structural, or web/database sub-skills. Use it to choose the right module, design a safe offline workflow, and decide when an optional dependency or sibling route is required.

## Capability map

| User task | Use | Main inputs | Outputs | Optional requirements |
|---|---|---|---|---|
| Motif counts/PWM/PSSM/JASPAR flat files | `Bio.motifs` | equal-length instances or motif file handle | `Motif`, counts, PWM/PSSM, formatted motif text, scan hits | NumPy; network only for WebLogo/JASPAR SQL, which is not owned here |
| Restriction enzyme map/digest | `Bio.Restriction` | `Seq`/`MutableSeq`, enzyme classes or names | cut positions, fragments, filtered enzyme dicts | none beyond package base |
| Numeric clustering | `Bio.Cluster` | numeric 2D arrays, optional mask/weights | clusters, tree, distance matrix, centroids, PCA | NumPy |
| Phenotype Microarray analysis | `Bio.phenotype` | `pm-json` or `pm-csv` handle/path | `PlateRecord`, `WellRecord`, JSON output, curve summaries | NumPy; SciPy for sigmoid fitting/area |
| GenePop population genetics | `Bio.PopGen.GenePop` | GenePop text handle or filename parser | `Record`, loci/population edits, split records | none for nodepend parser |
| Genome diagrams/graphics | `Bio.Graphics`, `Bio.Graphics.GenomeDiagram` | sequence features/tracks/graphs | PDF/PS/EPS/SVG or bitmap bytes/files | ReportLab; renderPM/Pillow for bitmap formats |
| Protein summaries | `Bio.SeqUtils.ProtParam` | protein sequence string or `Seq` | composition, molecular weight, pI, hydropathy, secondary-structure fractions | none beyond package base |
| Long-tail formats/models | `Bio.CAPS`, `Bio.Compass`, `Bio.NMR`, `Bio.SCOP`, `Bio.Pathway`, `Bio.Data` | module-specific records or in-memory objects | specialized parsed records, maps, constants, prototype graph/reaction objects | varies; see long-tail routing table |

## Bio.Cluster workflow

Use `Bio.Cluster` for small to medium numeric clustering and matrix operations, especially when a user asks for Biopython-native clustering rather than scikit-learn.

```python
import numpy as np
from Bio.Cluster import distancematrix, treecluster, kcluster

data = np.array([[0.0, 0.0], [0.2, 0.1], [3.0, 3.1], [3.2, 2.9]])

distances = distancematrix(data, dist="e")
tree = treecluster(data, method="a", dist="e")
labels_from_tree = tree.cut(2)
labels, error, nfound = kcluster(data, nclusters=2, initialid=[0, 0, 1, 1])
```

Key decisions:

- `data` should be a numeric rectangular `n_items x n_features` array-like object.
- `mask` marks missing values with `0`; present values use nonzero entries. Mask shape must match `data`.
- `weight` weights variables when distances are calculated.
- `transpose=False` clusters rows/items; `transpose=True` clusters columns/features.
- Use `initialid` when you need deterministic `kcluster()`/`kmedoids()` behavior; otherwise partitioning methods may use random initialization.
- `distancematrix()` returns a lower-triangular list of one-dimensional arrays, not a dense square matrix.

Common function choices:

- `distancematrix(data, ..., dist="e")`: pairwise distances.
- `clustercentroids(data, clusterid=..., method="a" or "m")`: arithmetic mean or median centroids.
- `clusterdistance(data, index1=..., index2=..., method=...)`: distance between two clusters.
- `kcluster(data, nclusters=..., method="a" or "m", dist=..., initialid=...)`: k-means or k-medians.
- `kmedoids(distance, nclusters=..., initialid=...)`: k-medoids from a distance matrix.
- `treecluster(data, method="m"/"s"/"c"/"a", dist=...)`: hierarchical clustering returning a `Tree`.
- `somcluster(data, ...)`: self-organizing map clustering.
- `pca(data)`: principal-component analysis.

Distance codes used by cluster functions:

- `e`: Euclidean distance.
- `b`: city-block/Manhattan distance.
- `c`: Pearson distance.
- `a`: absolute Pearson distance.
- `u`: uncentered-correlation distance.
- `x`: absolute uncentered-correlation distance.
- `s`: Spearman rank distance.
- `k`: Kendall tau distance.

## Bio.phenotype workflow

Use `Bio.phenotype` for Phenotype Microarray plates. Format strings must be lowercase.

```python
from io import StringIO
from Bio import phenotype
from Bio.phenotype.phen_micro import PlateRecord, WellRecord

plate = PlateRecord("PM01")
plate["A01"] = WellRecord("A01", signals={0.0: 10.0, 1.0: 11.0, 2.0: 12.0})
plate["A02"] = WellRecord("A02", signals={0.0: 10.0, 1.0: 25.0, 2.0: 40.0})

corrected = plate.subtract_control("A01")
well = corrected["A02"]
print(well.get_raw())
print(well[0:2:0.5])  # interpolated values at half-hour steps
well.fit(None)        # base stats only; no SciPy needed
print(well.min, well.max, well.average_height)

handle = StringIO()
phenotype.write([plate], handle, "pm-json")
```

Use patterns:

- `phenotype.parse(handle_or_path, "pm-json" or "pm-csv")` for multiple records.
- `phenotype.read(handle_or_path, format)` for exactly one record.
- `phenotype.write(records, handle_or_path, "pm-json")` for output; CSV writing is not provided by the high-level writer.
- `PlateRecord` supports well-id lookup (`plate["A05"]`), row/column slicing, iteration, addition/subtraction with compatible plates, and `subtract_control(control="A01")`.
- `WellRecord` supports iteration over raw `(time, signal)` pairs, interpolation via numeric indexing/slicing, arithmetic with another `WellRecord`, `get_raw()`, `get_times()`, `get_signals()`, and `fit()`.
- `fit(None)` or an empty function list calculates `min`, `max`, and `average_height` without SciPy. Sigmoid fitting with `gompertz`, `logistic`, or `richards` needs SciPy and may still fail when the data cannot be fitted.

## GenePop workflow

Use `Bio.PopGen.GenePop` for GenePop text records. Missing alleles represented as zero in the file are normalized to `None` in parsed records.

```python
from io import StringIO
from Bio.PopGen import GenePop

data = """\
Example GenePop file
locus1 locus2
Pop
Ind1, 0102 0303
Ind2, 0200 0000
Pop
Other1, 0101 0403
"""
record = GenePop.read(StringIO(data))
print(record.loci_list)
print(record.populations[0][0])
print(str(record))  # reconstructs GenePop text

record.remove_population(0)
record.remove_locus_by_name("locus2")
```

Operational notes:

- `Record.comment_line`, `loci_list`, `populations`, `pop_list`, and `marker_len` are the main fields.
- `populations` is a list of populations; each population is a list of `(individual_name, allele_list)` pairs.
- GenePop itself does not store reliable population names; use indices or an external name list for `split_in_pops(pop_names)`.
- `remove_population(pos)`, `remove_locus_by_position(pos)`, `remove_locus_by_name(name)`, `split_in_loci()`, and `split_in_pops(pop_names)` mutate or split records in memory.
- For very large files or output-to-file editing, prefer the filename-oriented `Bio.PopGen.GenePop.FileParser`/`LargeFileParser` helpers after checking their API on the installed package.

## Graphics and GenomeDiagram workflow

`Bio.Graphics` depends on ReportLab. Import it only after confirming graphics dependencies are installed, or catch `MissingPythonDependencyError` and provide a non-graphics fallback.

Typical GenomeDiagram flow:

```python
from Bio.Graphics import GenomeDiagram
from Bio.SeqFeature import SeqFeature, SimpleLocation
from reportlab.lib import colors

diagram = GenomeDiagram.Diagram("Example region")
track = diagram.new_track(1, name="Features")
feature_set = track.new_set()
feature = SeqFeature(SimpleLocation(5, 25, strand=1), type="gene", qualifiers={"label": "geneA"})
feature_set.add_feature(feature, color=colors.blue, label=True, name="geneA")

diagram.draw(format="linear", pagesize="A4", fragments=1, start=0, end=40)
diagram.write("example.svg", "SVG")
```

Output guidance:

- Vector outputs: `PS`, `EPS`, `PDF`, `SVG`.
- Bitmap outputs: `JPG`, `BMP`, `GIF`, `PNG`, `TIFF`/`TIF`; these require the optional ReportLab bitmap renderer and usually Pillow.
- `write_to_string(output="SVG")` can be useful when the caller needs bytes instead of a file.
- For a graphics request in an environment without ReportLab, summarize the feature layout or create a tabular intermediate, then tell the user which optional dependency is missing.

## Long-tail module routing

| Module | Use when | Minimum pattern | Route away when |
|---|---|---|---|
| `Bio.CAPS` | Finding cleaved amplified polymorphic sequence markers from an equal-length alignment and restriction enzymes. | Build `CAPSMap(alignment, enzymes=[...])` and inspect `.dcuts`. | The task is general alignment construction; use alignment-search first. |
| `Bio.Compass` | Parsing COMPASS profile/profile comparison output. | `read(handle)` for one record; `parse(handle)` for multiple; inspect query/hit names, score, e-value, alignments, and coverage. | The user asks for BLAST/SearchIO result parsing or running external profile tools. |
| `Bio.NMR.xpktools` / `Bio.NMR.NOEtools` | Reading/manipulating NMRView `.xpk` peak lists or predicting simple NOE crosspeak lines from assignment peak lists. | `Peaklist(filename)`, `XpkEntry(line, headline)`, `residue_dict(nucleus)`, `predictNOE(...)`. | The task is general structural modeling or PDB parsing; use structural-bioinformatics. |
| `Bio.SCOP` | Working with SCOP classification parse files, domains, residues, or ASTRAL-style headers. | `parse_domain(header)`, `Scop(cla_handle=..., des_handle=..., hie_handle=...)`, then query by sid/sunid. | The user needs PDB/mmCIF coordinate parsing, structure superposition, or online downloads. |
| `Bio.Pathway` | Lightweight prototype reaction/network objects for pathway data interchange or algorithm prototyping. | `Reaction`, `System`, `Interaction`, `Network`; treat API as prototype-like. | The user asks for KEGG REST, online pathway retrieval, or BioSQL. |
| `Bio.Data` | Static biological constants such as IUPAC letters, codon tables, and PDB residue mappings. | Import the specific constant/table and keep calculations explicit. | The user needs translation/transcription workflows; use sequence-objects. |

Long-tail cautions:

- These modules are narrower and less commonly used than `SeqIO`, `Bio.Align`, `Bio.PDB`, or `Bio.Entrez`; confirm exact installed APIs for nontrivial scripts.
- Do not promise exhaustive support for old external program formats beyond parsing/manipulating the documented objects.
- For network-backed SCOP/ASTRAL helpers or external tools that produce COMPASS/NMR data, document prerequisites instead of making them part of a base offline workflow.
