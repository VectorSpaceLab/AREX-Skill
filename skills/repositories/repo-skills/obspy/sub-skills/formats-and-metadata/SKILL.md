---
name: formats-and-metadata
description: "Choose, validate, convert, and inspect ObsPy waveform, event, and
  station-metadata formats while preserving metadata and reporting
  format-specific limits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ObsPy formats and metadata

Use this skill when a task is about file-format dispatch, waveform serialization,
MiniSEED/SAC/ASCII conversion, QuakeML events, StationXML inventories, RESP or
SEED/XSEED metadata, format validation, or ObsPy format command-line tools.
Keep generic filtering, trimming, merging, and other Stream transforms in
`waveform-processing`; keep FDSN/routing retrieval in `data-access`; keep
response removal and signal algorithms in `signal-analysis`.

## Safe operating rules

- Work on a new output path by default. Do not overwrite an input or existing
  output unless the caller explicitly opts in and the replacement is validated.
- Prefer an explicit `format=` when an extension is ambiguous, absent, or
  misleading. A supplied format disables further waveform format checking.
- After every conversion, read the output with the matching reader and compare
  the intended data, IDs, time range, sample count, and metadata fields. Treat
  format conversion as potentially lossy.
- Use local files or file-like objects for reproducible checks. Do not put
  credentials in format files or logs. This skill does not require network
  access, Cartopy, shapefile support, or live services.

## Choose the object and dispatch path

| Input | Read | Write | Explicit format examples |
|---|---|---|---|
| Waveform | `obspy.read(path, format=...)` | `Stream.write(path, format=...)` or `Trace.write` | `MSEED`, `SAC`, `SLIST`, `TSPAIR`, `GSE2`, `WAV` |
| Events | `obspy.read_events(path, format=...)` | `Catalog.write(path, format=...)` | `QUAKEML`, `SCML`, `NDK`, `CMTSOLUTION`, `CSV` |
| Inventory | `obspy.read_inventory(path, format=..., level=...)` | `Inventory.write(path, format=...)` | `STATIONXML`, `RESP`, `XSEED`, `SEED` |

`read()` accepts a path, `pathlib.Path`, URL, or open file-like object and
supports `headonly`, `starttime`, `endtime`, `dtype`, `apply_calib`, and
`check_compression`. `Stream.write()` can infer a format from the extension,
but explicit format is safer. `Catalog.write()` and `Inventory.write()` require
a format. Use `level="network"`, `"station"`, `"channel"`, or `"response"`
when reading an inventory to control detail and cost.

The plugin registry determines the supported names and read/write directions;
read and write support are not symmetric. See
[format-matrix.md](references/format-matrix.md). Do not infer support merely
from a filename extension.

## Core workflows

1. **Identify:** classify the object (waveform, event, inventory), inspect a
   small header first (`read(..., headonly=True)` for waveforms), and record the
   source format, target format, required metadata, and validation method.
2. **Read explicitly:** use `format="MSEED"`, `format="STATIONXML"`,
   `format="QUAKEML"`, `format="RESP"`, or another registered name when
   dispatch is uncertain. For multiple waveform files, a glob may produce one
   Stream; inspect each trace.
3. **Inspect metadata:** for waveforms check `tr.id`, `tr.stats.starttime`,
   `endtime`, `sampling_rate`, `npts`, `dataquality`, and format-specific
   `stats.mseed`/`stats.sac`/`stats.ascii`. For inventories traverse
   `inv -> network -> station -> channel -> response`; for catalogs inspect
   event IDs, origins, magnitudes, picks, and `extra`.
4. **Write to a fresh destination:** pass format-specific options deliberately.
   For MiniSEED, common controls include `encoding` and `reclen`; ensure the
   data dtype is compatible. For XML, use `validate=True` where supported and
   optionally `nsmap` for declared custom namespaces.
5. **Re-read and verify:** use the corresponding read function, compare the
   fields that the target format can represent, and record expected loss (for
   example, MiniSEED does not carry full StationXML response metadata).
6. **Diagnose before retrying:** preserve the failed output under a diagnostic
   name only if it is useful; never replace a known-good source. See
   [troubleshooting.md](references/troubleshooting.md).

For a deterministic tiny local check, use the bundled
[`format_roundtrip.py`](scripts/format_roundtrip.py). It creates its own
small files in a caller-selected directory, refuses to overwrite by default,
and can test waveform, QuakeML, and StationXML round trips.

## Metadata preservation boundaries

- **Waveform formats:** MiniSEED is the usual interchange format for sampled
  data and selected network/station/location/channel/time and quality fields.
  SAC can carry many header fields but is not a substitute for a complete
  Inventory. SLIST/TSPAIR are readable ASCII forms; their headers carry a
  compact ID/time/rate/unit description. Always compare the actual array and
  timing after a conversion.
- **Station metadata:** StationXML models a hierarchy of networks, stations,
  channels, and responses. `Inventory.select()` can scope an output before
  writing. `level="response"` retains response detail; lower levels intentionally
  omit it. RESP and SEED/XSEED are response/station metadata formats and may
  require the xseed parser and `lxml`.
- **Events:** QuakeML is the primary structured event representation. A
  `Catalog` contains `Event` objects with `Origin`, `Magnitude`, picks, and
  related objects. Formats such as NDK, CMTSOLUTION, CSV, or legacy bulletins
  represent different subsets; validate and compare the fields relevant to the
  task.
- **Custom XML fields:** attach custom namespaced elements/attributes through an
  object's `.extra` mapping. Each entry uses `value` and `namespace`, with
  optional `type="attribute"` and `attrib`; nested mappings are supported.
  Pass `nsmap={prefix: namespace}` to XML writers for stable readable prefixes.
  Values read back from XML are text strings, so normalize types explicitly.
  See [event-inventory.md](references/event-inventory.md).

## Validation and command-line handoff

Use `validate=True` when writing QuakeML or StationXML. For an existing file,
use the public validation helpers where available: StationXML validation
returns `(valid, errors)` and QuakeML validation returns a boolean; inspect the
error log rather than suppressing it. A successful parse is not proof that all
optional metadata survived.

For local inspection, `obspy-print` reports waveform headers and can print
merged gaps; `obspy-mseed-recordanalyzer` reports MiniSEED record headers;
`obspy-dataless2xseed`, `obspy-xseed2dataless`, and `obspy-dataless2resp` are
conversion tools. Their options and safe output behavior are summarized in
[cli-reference.md](references/cli-reference.md). The installed package may
expose these only after its console scripts are installed; if a command is not
on `PATH`, use the equivalent Python API or report the environment limitation.

## Handoff checklist

Before declaring a conversion complete, report:

- source and target format, explicit format arguments, and output path;
- object count, trace/event/station/channel IDs, time/sample summaries;
- fields compared after re-read and any known target-format loss;
- validation result and diagnostic details for malformed input;
- optional dependency or compiled-library requirements, if encountered.
