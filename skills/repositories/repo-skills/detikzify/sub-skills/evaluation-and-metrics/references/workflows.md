# Workflows

## Evaluation pipeline

1. Load the chosen model(s) and prepare the train and test sets.
2. Run the generation step for each model and optionally cache predictions.
3. Convert the final generated TikZ into `TikzDocument` objects for compiled scoring.
4. Compute the selected metrics and write the score summary to JSON.
5. If you run `examples/eval.py` directly rather than through a launcher, set the distributed environment variables (`RANK`, `WORLD_SIZE`, `MASTER_ADDR`, and a free `MASTER_PORT`) before calling `--help` or any single-process debug command.

## Important choices

- `model_inputs` controls whether the model sees images, sketches, captions, or combinations of them.
- A timeout changes the meaning of the scoring summary in the repo's evaluation script.
- Cached predictions are reused when available.
- Redacted metrics compare outputs after text redaction when that branch is enabled.

## When to debug instead of score

- If generation never produces compileable TikZ, debug inference first.
- If a metric import fails, install the optional metric dependency rather than forcing a CPU-only fallback.
- If the evaluation path is unexpectedly slow, check whether the compile / rasterize step or the model generation step is dominating.
