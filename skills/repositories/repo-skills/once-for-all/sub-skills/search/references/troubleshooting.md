# Search Troubleshooting

## Purpose

Read this when search helpers fail to import, download, or finish.

## Common issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `pyyaml`, `thop`, or `matplotlib` | Optional search extras are not installed. | Install the search extras from `references/dependencies.md`. |
| `AccuracyPredictor(pretrained=True)` tries to download files | The pretrained predictor resolves public weights. | Use `pretrained=False` for smoke checks or cache the weight file. |
| `LatencyTable` fails to build | The latency tables are downloaded from a public URL. | Provide network access or use a cached lookup table path. |
| `EvolutionFinder` prompts for input | The constraint type or constraint value is invalid. | Use a valid constraint type and a constraint inside the documented range. |
| `FLOPsTable` is slow | LUT construction is expensive by design. | Use the bundled dummy smoke or a cached efficiency table instead of rebuilding the table every time. |

## Practical recovery

- For offline verification, run the bundled dummy smoke instead of the full
  notebook-style search.
- If you only need to prove the API shape, `AccuracyPredictor(pretrained=False)`
  and a short evolution loop are enough.
- For real FLOPs or latency curves, expect public downloads or a cached LUT.
