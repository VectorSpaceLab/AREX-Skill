# ObsPy format matrix

This matrix is a practical dispatch guide for the public API. The plugin
registrations define the available names and read/write direction; actual
availability can vary with the installed package and optional dependencies.
Use an explicit format name when extension-based detection is uncertain.

## Waveforms (`read` / `Stream.write`)

| Format | Read | Write | Typical use and checks |
|---|---:|---:|---|
| `MSEED` | yes | yes | Compact waveform interchange. Check `tr.id`, UTC bounds, `npts`, dtype, `stats.mseed`, `encoding`, and `reclen`. Native C library support is required by this checkout. |
| `SAC` | yes | yes | Single-trace SAC headers and data. Read/write a trace or one-trace stream; compare SAC header fields and array. |
| `SACXY` | yes | yes | ASCII SAC XY representation. Check timing and numeric precision. |
| `SLIST` | yes | yes | ASCII sample list with `TIMESERIES` header. `custom_fmt` output is intentionally not readable by the normal parser. |
| `TSPAIR` | yes | yes | ASCII timestamp/sample pairs. Check UTC timestamps and sample count. |
| `GSE1` | yes | no | Legacy GSE1 reader. |
| `GSE2` | yes | yes | GSE2 waveform. Check calibration/metadata because conversion can be lossy. |
| `SEGY` / `SU` | yes | yes | SEG-Y/SU seismic traces; inspect format-specific headers. |
| `SEISAN`, `Q`, `SH_ASC`, `WAV`, `AH`, `GCF` | yes | varies | Plugin-backed legacy or audio/instrument formats. Confirm direction and dependencies before committing to a conversion. |
| `CSS`, `WIN`, `KINEMETRICS_EVT`, `PDAS`, `SEG2`, `Y`, `KNET`, `REFTEK130`, `RG16`, `DMX`, `ALSEP_*`, `CYBERSHAKE` | yes | mostly no | Specialized readers. Do not promise write support; use the plugin registry and a representative fixture. |
| `PICKLE` | yes | yes | Python-specific serialization. Avoid as a cross-language interchange format. |

`read()` can autodetect a local waveform when the plugin detector recognizes it.
`format=` bypasses further format checks, so a wrong explicit hint can produce
a parser error or an incorrect interpretation. `Stream.write()` infers from a
suffix only when `format` is omitted; use `format=` when a suffix is ambiguous.

## Events (`read_events` / `Catalog.write`)

| Format | Read | Write | Notes |
|---|---:|---:|---|
| `QUAKEML` | yes | yes | Primary structured event format. `validate=True` invokes the bundled QuakeML Relax NG validation. |
| `SCML` | yes | yes | SeisComP XML conversion through the event plugin; optional schema validation is a writer option. `SC3ML` is deprecated alias behavior in this version. |
| `NDK`, `CMTSOLUTION`, `SCARDEC`, `NORDIC`, `CSV`, `CSZ`, `EVENTTXT` | varies | varies | Use only the direction registered by the installed package; compare origins, magnitudes, IDs, and picks after conversion. |
| `ZMAP`, `MCHEDR`, `NLLOC_HYP`, `GSE2`, `IMS10BULLETIN`, `EVT`, `FOCMEC`, `HYPODDPHA`, `FNETMT` | mostly read | varies | Legacy/event-specialized formats; representation is narrower than QuakeML. |
| `JSON`, `CNV`, `NLLOC_OBS`, `SHAPEFILE`, `KML` | varies | varies | Some are write-only in the plugin table. Shapefile/KML support is optional and was not required by the verified base environment. |

`read_events(path, format=...)` returns a `Catalog`; `Catalog.write(path,
format=...)` requires an explicit format. A successful conversion does not mean
that unsupported QuakeML object types were retained in a narrower format.

## Inventories (`read_inventory` / `Inventory.write`)

| Format | Read | Write | Notes |
|---|---:|---:|---|
| `STATIONXML` | yes | yes | Main FDSN StationXML representation. `level` controls detail and `validate=True` validates the generated document. |
| `SEED` / `XSEED` | yes | no direct `Inventory.write` in this plugin table | Parse with the xseed `Parser` for dataless/XML-SEED conversions. |
| `RESP` | yes | no direct `Inventory.write` in this plugin table | Read response files into an `Inventory`; use xseed conversion tools for writing RESP from dataless SEED. |
| `INVENTORYXML`, `SCML` / `SC3ML` | read | varies | Compatibility readers. |
| `STATIONTXT` | read | yes | FDSN station text representation; check whether response information is representable. |
| `SACPZ`, `CSS`, `SHAPEFILE`, `KML` | usually write | varies | Specialized export; shapefile/KML are optional and not base-environment guarantees. |

StationXML autodetection can fail on real-world files with minor deviations
from the official schema. Prefer `read_inventory(path, format="STATIONXML")`
for a file known to be StationXML, then validate separately. Inventory objects
are hierarchical: `inv[network][station][channel]`; a channel response may be
`None` or a `Response` object.

## MiniSEED write controls

Common public `Stream.write(..., format="MSEED", ...)` options include:

- `encoding`: symbolic or numeric encoding supported by libmseed and compatible
  with the NumPy data type (`STEIM1`, `STEIM2`, `INT16`, `INT32`, `FLOAT32`,
  `FLOAT64`, or ASCII where supported). Do not force an integer encoding for
  floating data without checking the conversion.
- `reclen`: MiniSEED record length, normally a power of two such as 256, 512,
  or 4096. An invalid or too-small value raises an error.
- `byteorder`: where supported, explicitly choose byte order and verify it on
  re-read.

The compact format does not carry a complete Inventory response. Preserve the
StationXML/RESP separately whenever response metadata is needed.

## Format selection recipe

```python
from obspy import read, read_events, read_inventory

st = read("data.with.odd.suffix", format="MSEED", headonly=True)
cat = read_events("events.dat", format="QUAKEML")
inv = read_inventory("stations.xml", format="STATIONXML", level="response")
```

When the format is unknown, first try a small `headonly` read or inspect the
file header; do not guess from a suffix alone. Use the bundled round-trip
helper to exercise a tiny deterministic fixture without modifying an input.
