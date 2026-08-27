# Evaluation workflows

Use these workflows to choose a safe execution path before running VLMEvalKit. For exact flag meanings, see [CLI reference](cli-reference.md). For outputs, see [results and status](results-and-status.md).

## 1. Preflight an installed environment

```bash
python run.py --help
vlmutil dlist l1
vlmutil mlist api
```

Optional, side-effecting checks:

```bash
# May instantiate a model and require weights, GPU memory, or API access.
vlmutil check MODEL_NAME
```

Record before a real run:

- Selected datasets and whether they are image, video, or multi-turn.
- Selected model and whether it is local, registry API, or OpenAI-compatible endpoint.
- Work directory, expected output format, and whether old outputs may be reused.
- Judge model/service availability for tasks that cannot use exact matching.
- Available GPUs/API quotas/dataset cache, if the command depends on them.

## 2. Image benchmark: run inference and evaluation

```bash
python run.py \
  --data MMBench_DEV_EN MME \
  --model GPT4o \
  --mode all \
  --work-dir outputs \
  --api-nproc 16 \
  --retry 6
```

Expected path through source evidence:

1. `run.py` builds a dataset with `build_dataset` or `build_dataset_from_config`.
2. For non-video, non-multi-turn datasets, it dispatches inference through `infer_data_job` from `vlmeval/inference.py`.
3. Prediction rows are written to `MODEL_DATASET.{xlsx|tsv|json}` depending on `PRED_FORMAT`.
4. Rank 0 runs `dataset.evaluate(result_file, **judge_kwargs)` unless `--mode infer` or a dataset-specific skip condition applies.
5. `status.json` and latest symlinks are updated in the model output root.

## 3. Video benchmark

```bash
torchrun --nproc-per-node=2 run.py \
  --data MMBench_Video_8frame_nopack \
  --model idefics2_8 \
  --work-dir outputs
```

Operational notes:

- Video presets come from `vlmeval/dataset/video_dataset_config.py` or a `--data-config`/`--config` dataset entry.
- `run.py` dispatches video datasets to `infer_data_job_video` from `vlmeval/inference_video.py` when `dataset.MODALITY == 'VIDEO'`.
- Video datasets normally require either `nframe` or `fps`, not both.
- API video runs may use `--video-llm` when the endpoint accepts native video or omit it to use multi-image style prompts if the model wrapper supports that path.
- Real video decoding, dataset downloads, and high-throughput GPU behavior were not verified during skill construction; treat them as environment-specific.

## 4. Multi-turn benchmark

`run.py` dispatches datasets with `dataset.TYPE == 'MT'` to `infer_data_job_mt` from `vlmeval/inference_mt.py`.

```bash
python run.py \
  --data MULTI_TURN_DATASET_NAME \
  --model MODEL_NAME \
  --mode all \
  --work-dir outputs
```

Operational notes:

- Multi-turn inference uses `model.chat`/`chat_inner` style behavior and stores a list of predictions per row.
- API multi-turn paths use the same standard API failure text as image/video paths.
- If a model lacks chat capability, route to [model-development](../../model-development/SKILL.md) to inspect or implement the wrapper contract.

## 5. Inference-only now, evaluation-only later

```bash
# Run only prediction generation.
python run.py --data MMBench_DEV_EN --model GPT4o --mode infer --work-dir outputs

# Later reuse the completed prediction and evaluate.
python run.py --data MMBench_DEV_EN --model GPT4o --mode eval --reuse --reuse-aux all --work-dir outputs
```

Recovery behavior:

- `--mode eval` forces `--reuse=True`.
- `prepare_reuse_files` searches previous eval-id directories under the same model output root.
- If a complete prediction file is found, it is copied to the new run. When formats differ and the file can be converted, the prediction is materialized in the requested format.
- `--reuse-aux infer` copies inference checkpoints/temporaries; `--reuse-aux all` can also reuse compatible evaluation auxiliary files when the judge model matches.
- Without `--keep-failed`, rows containing the standard API failure text are treated as retryable and omitted from reuse completeness.

## 6. Resume or retry failed API rows

```bash
# Scan latest model output root for failed prediction/evaluation rows.
python sub-skills/evaluation/scripts/scan_api_failures.py \
  --model-root outputs/GPT4o \
  --datasets MMBench_DEV_EN

# Rerun without --keep-failed so failed rows are retried.
python run.py \
  --data MMBench_DEV_EN \
  --model GPT4o \
  --reuse \
  --reuse-aux infer \
  --work-dir outputs \
  --api-nproc 8 \
  --retry 8
```

If the prior prediction is complete except for failed API rows, this pattern copies usable predictions/checkpoints and retries failed rows. If you intentionally want to keep failed rows and avoid more calls, add `--keep-failed`.

## 7. OpenAI-compatible local/API service

```bash
python run.py \
  --data MMStar \
  --model SERVICE_MODEL_NAME \
  --base-url http://localhost:23333/v1 \
  --key "$INFERENCE_API_KEY" \
  --api-nproc 64 \
  --retry 4 \
  --timeout 1800
```

Notes:

- `--base-url` constructs `LMDeployAPI` arguments and appends `/chat/completions` internally.
- Use `--custom-prompt` if a registered adapter is needed for the model/dataset combination.
- Use `--local-media` only when the service can access local media paths from the same filesystem view.
- Use `--stream` only for an endpoint that correctly implements streaming responses.
- Starting or validating the remote service itself belongs to the runtime environment; no live API calls were verified in skill construction.

## 8. Async API mode for high-concurrency API evaluations

```bash
python run.py \
  --api-mode \
  --data MMBench_DEV_EN MMStar \
  --model GPT4o \
  --work-dir outputs \
  --api-nproc 64 \
  --monitor-interval 30 \
  --mode all
```

Expected path:

1. `run.py` validates that only one model is selected.
2. It builds `DatasetConfig` entries from `vlmeval/inference_api.py`.
3. `APIEvalPipeline` creates a shared inference queue with `--api-nproc` workers.
4. Image, video, and multi-turn samples are produced by the relevant async producer.
5. Evaluation runs in subprocesses unless `--debug` is set.
6. `monitor_interval` controls periodic queue/progress snapshots.

Constraints:

- Do not use multi-process `torchrun`; API mode rejects `WORLD_SIZE > 1`.
- Datasets requiring special official-submission handling may be skipped in the pipeline.
- If evaluation subprocesses crash, inspect `eval_logs/` inside the run directory and `status.json` error messages.

## 9. Format and environment-control workflows

### Long responses or thinking models

```bash
PRED_FORMAT=tsv SPLIT_THINK=True \
python run.py --data MMLongBench --model MODEL_NAME --work-dir outputs
```

- `PRED_FORMAT=tsv` avoids `.xlsx` cell-length truncation for long predictions.
- `SPLIT_THINK=True` splits `<think>...</think>` content into a `thinking` column when possible or uses a model-specific `split_thinking` method when available.

### JSON summaries/evaluation files

```bash
EVAL_FORMAT=json python run.py --data DATASET --model MODEL --work-dir outputs
```

`EVAL_FORMAT` supports `csv` by default and `json` when set. `PRED_FORMAT` supports `xlsx` by default and `tsv`/`json` when set.

### Cache and download roots

```bash
LMUData=/path/to/lmudata VLMEVALKIT_USE_MODELSCOPE=1 \
python run.py --data VIDEO_DATASET --model MODEL --work-dir outputs
```

- `LMUData` selects the cache/data root used by loaders and media localization.
- `VLMEVALKIT_USE_MODELSCOPE=1` opts into ModelScope download routes where supported.
- Dataset downloads were not performed during skill construction; verify availability and licensing before relying on a remote benchmark source.

### Evaluation proxy or local judge

```bash
EVAL_PROXY=http://proxy.example:8080 \
python run.py --data DATASET --model MODEL --judge JUDGE_MODEL --work-dir outputs
```

```bash
LOCAL_LLM=LOCAL_JUDGE_NAME \
python run.py --data DATASET --model MODEL --work-dir outputs
```

- `EVAL_PROXY` is applied around evaluation calls.
- `LOCAL_LLM` participates in local judge selection when the installed judge wrappers read it.
- `FWD_API=1` makes supported API registry entries use the `GPT4V` class path in local mode.

## 10. Summarize and compare runs

```bash
python sub-skills/evaluation/scripts/summarize_runs.py --work-dir outputs/GPT4o
python sub-skills/evaluation/scripts/summarize_runs.py --work-dir outputs/GPT4o/T20260101-120000 --verbose
python sub-skills/evaluation/scripts/summarize_runs.py --work-dir outputs/GPT4o --work-dir outputs/OtherModel --data MMBench_DEV_EN MMStar
```

Use summaries to decide whether a run needs rerun, eval-only reuse, or deeper troubleshooting. See [results and status](results-and-status.md) for expected fields.
