# ObsPy format and inspection CLIs

Use these commands against local files after validating inputs and choosing a fresh output path. Run `--help` first in the active package environment; the exact format choices are version-dependent.

## Waveform inspection and plots

- `obspy-print FILE...` prints stream summaries. Useful flags include `-f FORMAT`, `-n` to suppress sample counts, `--no-sorting`, and `-g` for gap-oriented output.
- `obspy-plot FILE... -o OUTPUT` creates a waveform plot. Set `MPLBACKEND=Agg` for headless runs and use a new output path.
- `obspy-scan PATH...` summarizes data availability. Bound `--start-time`/`--end-time`, use `--id` for a selector, and avoid `--write`/`--load` unless the caller explicitly wants persistent scan state.
- `obspy-mseed-recordanalyzer FILE` inspects MiniSEED record headers. Use `-n N` to limit records and `-a`/`-f` only when their help text confirms the intended detail/output behavior.

## Metadata conversion

- `obspy-dataless2xseed INPUT OUTPUT` converts dataless SEED to XML-SEED when the input and parser support it.
- `obspy-xseed2dataless INPUT OUTPUT` converts XML-SEED back to dataless SEED.
- `obspy-dataless2resp INPUT OUTPUT` exports RESP files. Treat the output as response metadata, not waveform samples.

For all conversion commands: write to a non-existing destination, inspect `--help`, keep the source untouched, and reopen/parse the result with the matching public API. If a command is missing from `PATH`, use `read`, `read_inventory`, `Inventory.write`, or the xseed parser directly.

## Verified help smoke

The base environment's help checks passed for `obspy-print`, `obspy-flinn-engdahl`, `obspy-plot`, `obspy-scan`, and `obspy-mseed-recordanalyzer`. This verifies parser availability only; it does not verify a live service, optional Cartopy map data, or every legacy format.
