# `fio` troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `fio: command not found` | Fiona is not installed in the active environment or its console scripts are not on PATH | Run the package's public install, then invoke the environment's `fio`; verify `fio --version` and `python -m pip check`. |
| `No such command` / missing `filter` or `calc` | Optional calc dependencies are absent | Install the narrow `[calc]` extra, or use `cat`, `dump`, `load`, and Python APIs instead. Do not install all extras merely to hide a route mismatch. |
| `fio load` reports invalid input | Input is not a FeatureCollection or accepted feature sequence, or framing is mixed | Validate one line with a JSON parser, preserve LF versus RS framing, and use `--x-json-seq` when required by the source. |
| Output has wrong geometry/fields | `load` inferred schema from an incompatible first feature | Inspect the first feature and the full stream; use explicit Python schema handling for heterogeneous inputs. |
| `where` fails | SQL field name, quoting, or driver dialect mismatch | Inspect `fio info` schema, simplify the predicate, and confirm the target driver's attribute filter support. |
| CRS output is wrong | `--src-crs`/`--dst-crs` does not describe the actual input | Check CRS metadata and route complex transforms to `crs-transform`; never infer CRS from coordinate magnitude alone. |
| `fio rm` would delete the wrong resource | Destructive operation or wrong layer | Stop. Confirm the path and layer with `fio ls` and use a disposable fixture; never automate `rm` without explicit confirmation and `--yes`. |
