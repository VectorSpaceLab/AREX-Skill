# CLI Reference

This reference maps the MTEB console script to the public Python APIs and describes the command behavior that matters for automation.

## Validate The Installed Command

Start every environment-specific workflow with help checks:

```bash
mteb --help
mteb run --help
mteb available-tasks --help
mteb available-benchmarks --help
mteb create-model-results --help
mteb leaderboard --help
```

Expected signals:

- `mteb --help` lists subcommands including `run`, `available-tasks`, `available-benchmarks`, `create-model-results`, and `leaderboard` for current MTEB releases.
- If documentation or an older prompt says `create-meta`, verify the installed command name. Current command help may expose this workflow as `create-model-results`.
- Help commands should exit with status `0` and should not execute benchmarks.

## `mteb run`

Typical command:

```bash
mteb run \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --tasks Banking77Classification EmotionClassification \
  --output-folder results \
  --overwrite-strategy only-missing \
  --batch-size 32 \
  --no-co2-tracker
```

Important flags:

- `-m`, `--model`: Model registry key or model identifier. The CLI calls `mteb.get_model(model_name, revision=None, device=...)` internally, with `--model-revision` passed as the revision.
- `-t`, `--tasks`: Explicit task names. When specified, task-name selection takes precedence over broad task filters in Python-side task selection.
- `-b`, `--benchmarks`: Benchmark names. When used, `mteb.get_benchmarks(names=...)` supplies the task list and `--tasks`, `--languages`, `--task-types`, `--categories`, and `--eval-splits` are ignored with a warning.
- `--languages`: ISO 639-3 language codes such as `eng`, `deu`, or `fra`.
- `--task-types`: Task type filters such as `Retrieval`, `Classification`, `Clustering`, or other installed task types.
- `--categories`: Category filters such as `s2s` or `p2p` where supported by task metadata.
- `--eval-splits`: Evaluation splits to pass to task selection. Use only when the chosen tasks actually expose those splits.
- `--device`: Device selector passed to model loading. If omitted, MTEB chooses CUDA when available, otherwise CPU.
- `--output-folder`: Base result cache folder. The CLI wraps it as `ResultCache(output_folder)` before calling `mteb.evaluate(...)`.
- `--batch-size`: Passed as `encode_kwargs={"batch_size": value}` to `mteb.evaluate(...)`.
- `--overwrite-strategy`: One of `always`, `never`, `only-missing`, or `only-cache`. Default is `only-missing`.
- `--overwrite`: Deprecated compatibility flag; prefer `--overwrite-strategy always`.
- `--prediction-folder`: Folder for saved predictions. Prefer this over deprecated `--save_predictions`.
- `--co2-tracker` and `--no-co2-tracker`: Mutually exclusive toggles for CO₂ tracking.

Python API mapping:

- Model loading maps to `mteb.get_model(model_name, revision=None, device=None, *, embed_dim=None, **kwargs)`.
- Task selection maps to `mteb.get_tasks(tasks=..., languages=..., task_types=..., categories=..., eval_splits=...)` when `--benchmarks` is not used.
- Evaluation maps to `mteb.evaluate(model, tasks, *, co2_tracker=None, raise_error=True, encode_kwargs=None, cache=ResultCache(...), overwrite_strategy="only-missing", prediction_folder=None, show_progress_bar=True, public_only=None, num_proc=None, timer=None)`.

## Task And Benchmark Listing

List all available tasks:

```bash
mteb available-tasks
```

Filter task inventory:

```bash
mteb available-tasks --task-types Retrieval --languages eng
mteb available-tasks --categories s2s --tasks Banking77Classification
```

List all available benchmarks:

```bash
mteb available-benchmarks
```

Filter benchmark inventory:

```bash
mteb available-benchmarks --benchmarks MTEB\(eng\,\ v1\)
```

Notes:

- `available-tasks` uses task filters similar to `mteb.get_tasks(...)` but the CLI currently exposes a smaller filter set than the full Python API. For private, beta, superseded, aggregate, modality, script, domain, or exclusive-language filtering, use the Python API and the `tasks-and-benchmarks` sub-skill.
- `available-benchmarks` uses benchmark names. If shell quoting is awkward, inspect the output first and pass exact names in quotes.

## Metadata Generation

Current installed command name:

```bash
mteb create-model-results \
  --model-name sentence-transformers/all-MiniLM-L6-v2 \
  --results-folder results/sentence-transformers__all-MiniLM-L6-v2/<revision> \
  --output-path model_card.md \
  --overwrite
```

Optional arguments:

- `--tasks`: Restrict generated metadata to selected task names.
- `--benchmarks`: Restrict generated metadata to selected benchmark names.
- `--from-existing`: Merge results into an existing README/model card path or model-card identifier.
- `--overwrite`: Replace an existing output file. Without it, an existing output file is an error.

Python API mapping:

- The CLI calls a metadata helper equivalent to `generate_model_card(model_name, tasks=..., benchmarks=..., existing_model_card_id_or_path=..., results_cache=ResultCache(results_folder), output_path=...)`.
- `--results-folder` must point at the model/revision result cache folder that contains task JSON files and model metadata, not merely the root output folder unless the cache reader is expected to discover from that root.

## Leaderboard

Launch a local leaderboard over a result cache:

```bash
mteb leaderboard --cache-path results --host 127.0.0.1 --port 7860
```

Useful flags:

- `--cache-path`: Folder containing model result caches. If omitted, MTEB uses its default `ResultCache` location.
- `--rebuild`: Force rebuild from the full results source instead of precomputed JSON cache.
- `--host`: Server bind host. Use `127.0.0.1` for local-only access.
- `--port`: Server port.
- `--share`: Ask Gradio to create a public URL.

Expected signals:

- Missing optional dependencies produce an import error recommending `mteb[leaderboard]`.
- Cache-path mistakes usually show as missing models/results rather than command-line parse failures.
- A successful launch starts a Gradio app and blocks the terminal until interrupted.
