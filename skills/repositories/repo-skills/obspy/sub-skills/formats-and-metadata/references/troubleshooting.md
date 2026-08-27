# Format and metadata troubleshooting

- **`Unknown format` or an unexpected parser:** filename detection is ambiguous or the explicit `format=` value is not a registered plugin name. Inspect the input header, use the exact uppercase plugin name, and keep the failed input unchanged.
- **Read succeeds but fields disappear:** the target format is narrower. Compare only fields the target can represent, preserve StationXML/RESP alongside MiniSEED when response metadata matters, and retain QuakeML when event objects are richer than the legacy target.
- **MiniSEED write fails with encoding or record-length errors:** the encoding is incompatible with the NumPy dtype or `reclen` is invalid/too small. Let ObsPy choose a compatible encoding first, or explicitly choose `STEIM1`/`STEIM2`/`FLOAT32`/`FLOAT64` only after checking dtype and re-reading the result.
- **XML validation fails:** inspect the reported element/namespace and required hierarchy. Fix the object or custom `.extra` mapping, use a declared `nsmap`, write to a fresh path, and retry `validate=True`; do not suppress schema errors.
- **`Response` is missing:** read StationXML/RESP at `level="response"` and verify `channel.response` before calling response-removal methods. Do not infer an instrument response from channel names.
- **`Catalog.write` or `Inventory.write` arguments fail:** both require an explicit `format`; `Catalog` is not a waveform and `Inventory` is not an event catalog. Route to the matching read/write function.
- **A conversion CLI is absent:** the installed distribution may not expose the console script. Run its `--help` check, then use the public Python API or xseed parser; do not call a source-checkout script.
- **Optional KML/shapefile/Cartopy support fails:** the base environment does not guarantee those extras. Install the documented extra only when the workflow needs it, and treat map/geodata downloads as explicit external prerequisites.
