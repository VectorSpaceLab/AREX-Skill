# SK²Decompile Troubleshooting

## `clang-format` missing or too old

- **Symptom**: normalization helpers fail immediately.
- **Likely cause**: `clang-format` is not installed in the target environment.
- **Recovery**: install `clang-format` before running pseudo-code normalization.

## Psychec / header inference fails

- **Symptom**: `inf_type.py` exits because the generator or solver binary cannot be found.
- **Likely cause**: the external Psychec toolchain is not installed or `stack` is missing.
- **Recovery**: either install the toolchain or treat the header-inference stage as intentionally unverified.

## Embedding server unreachable

- **Symptom**: the identifier-naming reward helpers fail or return empty outputs.
- **Likely cause**: the OpenAI-compatible embedding endpoint is not running or the base URL is wrong.
- **Recovery**: start the embedding server, verify the API base, and confirm the model path env var matches the server.

## `func_map.jsonl` contains no overlaps

- **Symptom**: the function-map builder prints warnings or produces empty JSONL output.
- **Likely cause**: the source path, pseudo-code dump, or assembly dump is missing, or the function names do not align.
- **Recovery**: verify the binary naming convention and make sure the source, pseudo, and asm files use the same function names.

## Two-stage inference strips the wrong function name

- **Symptom**: the final result still contains the model's placeholder name rather than the original symbol.
- **Likely cause**: the stripping logic does not match the generated signature.
- **Recovery**: inspect the `gen_result_model2` log and confirm the function-name post-processing step is aligned with the model output.

## BringUpBench evaluation cannot locate the benchmark checkout

- **Symptom**: the evaluator exits before any build or test runs.
- **Likely cause**: `BENCH_REPO_ROOT` is unset or points to the wrong checkout.
- **Recovery**: set `BENCH_REPO_ROOT` in `config.env` or the environment before launching the evaluator.
