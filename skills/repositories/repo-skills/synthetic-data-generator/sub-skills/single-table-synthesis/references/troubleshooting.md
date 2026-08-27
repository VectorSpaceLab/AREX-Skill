# Single-table synthesis troubleshooting

## CTGAN construction and training

- `AssertionError` at CTGAN initialization usually means `batch_size` is odd. Use an even batch size such as `10`, `100`, or `500`.
- Long or memory-heavy training usually means default `epochs=300` or large categorical expansion. Use `epochs=1` for smoke tests and choose categorical encoders/thresholds deliberately for high-cardinality columns.
- If CUDA fails, set `device="cpu"` for a CPU fallback or repair the torch/CUDA environment before using GPU claims.
- If generated rows are fewer than requested, filters such as `PositiveNegativeFilter` may remove invalid rows. Inspect processor logs and constraints.

## Save/load

- `Synthesizer.load(load_dir, model=...)` needs the same model class/name family used during save. Pass `CTGANSynthesizerModel` or `"CTGAN"` explicitly.
- Keep metadata JSON with the saved model directory; `Synthesizer.save` writes `metadata.json` and a `model/` subdirectory.
- Loading statistic models may prefer CUDA unless `SDG_FORCE_LOAD_CPU` is set; use this variable when CPU-only loading is required.

## CLI

- Use `--json_output true` to capture structured result status.
- If `sdgx --help` fails after installation but `pip check` passes, test `python -c 'from sdgx.cli.main import cli'` to isolate import failures.
- `--data_connector csvconnector` requires `--data_connector_kwargs '{"path":"..."}'`.
- `--dry_run true` initializes only; it does not prove a model can fit/sample.

## Output validation

Always check:

```python
assert len(sampled) == requested_count
assert sampled.columns.tolist() == expected_columns
assert not sampled.empty
```

For quality, add metrics from the evaluation sub-skill. For domain constraints, inspect metadata processors and run task-specific validations.
