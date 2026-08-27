# Event and station metadata workflow

## Purpose

Read this when moving between `Catalog`/QuakeML and `Inventory`/StationXML, when selecting the metadata needed for waveform interpretation, or when validating a conversion.

## Object relationships

- `read_events(path, format="QUAKEML")` returns a `Catalog` of `Event` objects. An event can have origins, magnitudes, picks, arrivals, focal mechanisms, resource IDs, and custom `.extra` data.
- `read_inventory(path, format="STATIONXML", level="response")` returns an `Inventory` containing networks, stations, channels, and optionally `Response` objects. Request `level="response"` before response removal; lower detail levels intentionally omit it.
- FDSN station queries return an `Inventory`; route query construction and live dispatch to `data-access` before serializing or inspecting it here.

## Fresh-output round trip

```python
from obspy import read_events, read_inventory

catalog = read_events("events.xml", format="QUAKEML")
catalog.write("events-copy.xml", format="QUAKEML", validate=True)
reopened_catalog = read_events("events-copy.xml", format="QUAKEML")

inventory = read_inventory("stations.xml", format="STATIONXML", level="response")
inventory.write("stations-copy.xml", format="STATIONXML", validate=True)
reopened_inventory = read_inventory("stations-copy.xml", format="STATIONXML", level="response")
```

Use caller-owned, non-existing paths for outputs. Compare counts and identifiers, then compare task-relevant fields: event origins/magnitudes/picks, or inventory network/station/channel codes, epochs, sample rates, and response presence. Parsing does not prove semantic equivalence; formats can omit fields.

## Custom XML fields

ObsPy models custom namespaced XML content through an object's `.extra` mapping. Entries include at least `value` and `namespace`; `type="attribute"` and `attrib` distinguish an XML attribute from an element. Pass an `nsmap` mapping to an XML writer when stable readable prefixes matter. Values read back from XML are text, so convert them deliberately before scientific use.

## Validation contract

`validate=True` on QuakeML or StationXML writing checks schema-oriented validity; it does not guarantee that a downstream application accepts every optional extension. Preserve the source and validate/reopen the new file before accepting conversion.

## Common losses and boundaries

- A waveform format such as MiniSEED does not replace StationXML response metadata.
- Restricting inventory `level` can intentionally remove response detail.
- Narrower event formats may not retain all QuakeML picks, arrivals, origins, focal mechanisms, or custom extensions.
- RESP and SEED/XSEED are specialized response/station formats; direct `Inventory.write` is not a generic RESP/XSEED exporter. Use the bundled CLI guidance or the relevant parser workflow.
