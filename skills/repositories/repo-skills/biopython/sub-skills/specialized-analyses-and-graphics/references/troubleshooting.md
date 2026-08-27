# Specialized Analyses Troubleshooting

## Purpose

Use this guide when a specialized Biopython workflow fails during motif, restriction, clustering, phenotype, GenePop, graphics, protein-analysis, or long-tail module work. Start with the offline smoke script when checking whether base specialized modules import and run:

```bash
python scripts/specialized_modules_smoke.py
```

## Import and optional dependency failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'Bio'` | Biopython is not installed in the active Python environment. | Install Biopython, restart the interpreter/session, then rerun the smoke script. |
| `MissingPythonDependencyError: Install NumPy if you want to use Bio.motifs` | Motif matrix/scoring code requires NumPy. | Install a Biopython build with NumPy available; rerun the motif section of the smoke script. |
| `MissingPythonDependencyError: Please install NumPy if you want to use Bio.Cluster` | `Bio.Cluster` requires NumPy and its compiled extension. | Install NumPy and a compatible Biopython wheel/build. If importing from a source checkout, install the package rather than relying on unbuilt source files. |
| `MissingPythonDependencyError: Please install NumPy if you want to use Bio.phenotype` | Phenotype parsing/objects use NumPy. | Install NumPy or use an environment where Biopython's numeric dependency is present. |
| Importing `Bio.Graphics` raises a ReportLab error | Graphics support is optional and ReportLab is missing. | Install ReportLab for vector graphics; install ReportLab's bitmap backend and Pillow for bitmap output. If graphics are not essential, produce a non-graphics summary instead. |
| Bitmap output (`PNG`, `JPG`, etc.) fails while `PDF`/`SVG` works | ReportLab vector output is available, but bitmap rendering backend or Pillow is missing. | Prefer `SVG`/`PDF`, or install the missing bitmap dependencies. |
| Phenotype `well.fit()` fails because SciPy is missing | Sigmoid fitting and area extraction require SciPy. | Use `well.fit(None)` for `min`, `max`, and `average_height`, or install SciPy before requesting fitted `area`, `lag`, `slope`, `plateau`, or model. |

## Motif failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError: No motifs found in handle` from `motifs.read()` | The input is empty, the wrong format was chosen, or the handle is already consumed. | Rewind/reopen the handle, verify the format string, and use `motifs.parse()` to inspect record count. |
| `ValueError: More than one motif found in handle` from `motifs.read()` | The file contains multiple motifs. | Use `motifs.parse(handle, fmt)` and select the record you need. |
| `ValueError: Unknown format ...` | Unsupported or misspelled motif format. | Use a supported format such as `pfm`, `jaspar`, `sites`, `transfac`, `meme`, `minimal`, `mast`, `alignace`, `clusterbuster`, `xms`, `pfm-four-columns`, or `pfm-four-rows`. |
| `PSSM has wrong alphabet` | PSSM scanning is being used with a non-DNA alphabet. | Use DNA motifs with alphabet `ACGT` for `pssm.calculate()`/`search()`, or use counts/PWM summaries instead. |
| Scores/hits differ after changing pseudocounts/background | PWM/PSSM and relative entropy are defined by current pseudocounts/background. | Set `m.pseudocounts` and `m.background` explicitly before calculating thresholds or comparing results. |
| WebLogo/JASPAR database examples fail offline | WebLogo and JASPAR SQL/database access are network/database-backed. | Keep offline work to motif objects and flat files. Route database credentials, network policy, and SQL connection work to the web/database sub-skill. |

## Restriction failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `TypeError: Expected Seq or MutableSeq instance` or similar | Restriction search received a raw string. | Wrap sequence text with `Bio.Seq.Seq(...)` or `MutableSeq(...)` before searching. |
| Invalid-character error from `FormattedSeq` | Sequence contains non-alphabetic characters such as gaps or punctuation. | Remove gaps/coordinates/whitespace artifacts before restriction analysis. Plain alphabetic ambiguity codes are allowed by the formatter, but recognition depends on enzyme definitions. |
| Cut positions appear shifted by one | Restriction enzymes report biological one-based cut positions, not Python slice offsets. | Document one-based positions, or convert deliberately when slicing Python strings. |
| A site across the sequence boundary is missed | Linear/circular topology mismatch. | Pass `linear=False` for circular plasmids or circularized fragments. |
| Too many enzymes or noisy output from `AllEnzymes` | Broad batch screens can produce very large maps. | Start with a targeted `RestrictionBatch`, then filter with `with_sites()`, `with_N_sites()`, `blunt()`, `overhang5()`, `overhang3()`, or name/site-size filters. |

## Bio.Cluster failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError` for matrix parsing | Data are ragged, empty, not numeric, wrong rank, or contain invalid cells. | Convert to a rectangular numeric array before calling cluster functions. |
| Mask-related `ValueError` | Mask shape or values do not match data expectations. | Use a mask with the same shape as `data`; `0` means missing, nonzero means present. |
| Results are not reproducible | Partitioning methods used random initialization. | Supply `initialid` for `kcluster()`/`kmedoids()` when deterministic output is required, or use hierarchical clustering. |
| Distances look unexpectedly small/large | The selected `dist` code or `transpose` value does not match the intended problem. | Recheck distance code (`e`, `b`, `c`, `a`, `u`, `x`, `s`, `k`) and whether rows or columns should be clustered. |

## Phenotype Microarray failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError: Format string 'PM-CSV' should be lower case` | Format names are case-sensitive. | Use `pm-csv` or `pm-json`. |
| `ValueError: More than one record found in handle` from `phenotype.read()` | The input contains multiple plates. | Use `phenotype.parse()` and iterate/select the plate. |
| `ValueError: Unknown format` or writer error for CSV | High-level writer supports JSON output, not CSV output. | Parse CSV with `pm-csv`, but write with `pm-json` or perform custom CSV export outside this helper. |
| Control subtraction fails | Control well or requested wells are absent from the plate. | Check `control in plate` and validate all well IDs before `subtract_control()`. |
| Interpolation returns `nan` | Requested time is outside measured time range. | Use `well.get_times()` to choose valid intervals. |
| Sigmoid fitting raises `RuntimeError` | Data cannot be fit by the requested model(s). | Try `fit(None)` for base summaries, inspect raw curves, or pass an ordered tuple of supported models: `("gompertz", "logistic", "richards")`. |

## GenePop failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError: No population data found` | Input is not valid GenePop text or lacks a `Pop` section. | Verify the first line, loci section, and at least one `Pop` separator before parsing. |
| Population names seem unreliable or missing | GenePop format does not preserve reliable population names. | Refer to populations by index or pass an external name list when splitting into populations. |
| Missing allele values appear as `None` | Zero-coded alleles are normalized to `None`. | Preserve `None` during analysis and let Biopython reconstruct zeros when converting the record back to text. |

## Graphics and long-tail failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| GenomeDiagram import fails | ReportLab is absent. | Install ReportLab or route to a non-graphics summary; do not import `Bio.Graphics` at module top level in scripts that should run without graphics support. |
| GenomeDiagram output format error | Unsupported output label or missing bitmap backend. | Use vector `PDF`, `SVG`, `PS`, or `EPS`; use bitmap labels only when renderPM/Pillow are installed. |
| `Bio.CAPS` raises alignment length errors | CAPS maps require equal-length aligned sequences. | Build or validate an alignment first, then pass enzymes to `CAPSMap`. |
| COMPASS parser raises unexpected end/format errors | Input is not COMPASS output or is truncated. | Validate the header lines and use `parse()` for multiple records or `read()` for exactly one. |
| NMR NOE prediction returns an empty line | Required residue/nucleus labels are missing, or the peaklist is not a diagonal assignment list. | Inspect `Peaklist.datalabels` and `residue_dict(...)`; validate the experimental assumptions before predicting. |
| SCOP construction fails with missing CLA/DES/HIE data | A complete SCOP parse-file set is required for full hierarchy construction. | Provide all required parse handles/files, or limit the task to parsing individual ASTRAL-style domain headers with `parse_domain(...)`. |
| `Bio.Pathway` behavior feels incomplete | The module is a lightweight/prototype-style abstraction, not a full pathway database client. | Use it for in-memory reaction/network prototyping; route KEGG or database retrieval to the web/database sub-skill. |
