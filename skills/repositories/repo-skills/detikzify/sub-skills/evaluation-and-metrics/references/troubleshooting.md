# Troubleshooting

## Missing optional dependencies

- `CrystalBLEU` can fail if `crystalbleu` or `sacremoses` is missing.
- `DreamSim` can fail if the `dreamsim` package or its cached assets are unavailable.
- `ClipScore` and `ImageSim` require the transformer vision stack and image processor support.
- `KernelInceptionDistance` needs the `torchmetrics` image metric stack.

## Compile / rasterize problems

- Evaluation often depends on compileable TikZ, not just string equality.
- Missing TeX packages, Ghostscript, or Poppler will make the compile-backed metrics unusable.
- If the document compiles but renders blank, inspect the rasterized image instead of the raw compile status.

## Workflow-specific failures

- A wrong `model_inputs` choice can make the evaluation look broken even when generation itself is fine.
- `examples/eval.py` initializes `torch.distributed` at startup; when you run it directly for `--help` or a single-process debug invocation, set `RANK=0`, `WORLD_SIZE=1`, `MASTER_ADDR=127.0.0.1`, and a free `MASTER_PORT`.
- If cached predictions are stale, delete or bypass the cache before trusting the score summary.
- If redacted metrics behave strangely, verify the redact step on one document before running the full batch.
