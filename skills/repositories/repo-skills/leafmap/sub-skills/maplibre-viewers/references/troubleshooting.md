# MapLibre Viewer Troubleshooting

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `view-vector` or `view-raster` not found | CLI entry points are not installed or the environment is stale | Re-run the smoke helper with `--mode cli` and check the install. |
| `localtileserver` import failure | The raster viewer dependency is missing | Install the missing package or limit yourself to vector-only smoke. |
| `No module named fiona` during `view-vector` | The vector-file driver stack is incomplete | Install the MapLibre extras or add `fiona` and rerun the vector smoke. |
| `view-raster` appears to hang | The command intentionally keeps the tile server alive | Treat that as expected; use `--help` or a vector smoke unless you explicitly need the server. |
| HTML output is created but nothing opens | `--no-browser` was used or browser opening is disabled | Inspect the HTML path that the command prints, or use the returned HTML from `Map.to_html(...)`. |
| A local file is rejected | The file path is wrong or the data format does not match the viewer | Confirm the file exists and use the viewer that matches the format. |

## Recovery checklist

1. Run `python scripts/check_leafmap_smoke.py --mode maplibre`.
2. If the CLI parser is the issue, run `--mode cli`.
3. If `view-vector` fails on file reading, check for `fiona` or the broader `leafmap[maplibre]` extra.
4. If a raster viewer is involved, confirm that a long-lived server is actually what you want.
5. If the user only needs an example or proof of concept, prefer `view-vector` over `view-raster`.

## When to stop

Stop and redirect when:
- the request is actually about a notebook widget map,
- the input file is remote-service data that belongs in `data-workflows`,
- or the user wants a different backend altogether.
