# Evaluation troubleshooting

Start with `status.json`, the latest run log, and the prediction file. Then use [results and status](results-and-status.md) to decide whether the failure is in command construction, dataset building, inference, judging, result reuse, or reporting.

## Fast triage checklist

```bash
python run.py --help
vlmutil dlist l1
vlmutil mlist api
python sub-skills/evaluation/scripts/summarize_runs.py --work-dir outputs/MODEL --verbose
python sub-skills/evaluation/scripts/scan_api_failures.py --model-root outputs/MODEL --show-missing --datasets DATASET
```

Ask these questions:

1. Did `run.py` parse the intended flags and write a new eval-id directory?
2. Does `status.json` show `pending`, `infer`, `eval`, `done`, `skip_reason`, or `error_message` for the dataset?
3. Is the prediction file present, loadable, and complete for all dataset indices?
4. Did evaluation require a judge model/API, an official server, or ground truth that is unavailable?
5. Are latest symlinks pointing at the intended eval id, or should you inspect a specific run directory?

## Symptoms and recoveries

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `--data and --model should not be set when using --config` | Mixed config and direct launch styles. | Use either `--config config.json` or `--data ... --model ...`; do not combine with `--data-config`. |
| `--data-config must be a valid JSON dict string` | Shell quoting or malformed JSON. | Quote the JSON with single quotes in POSIX shells and validate with `python -m json.tool`. |
| `Unsupported parameter(s) for dataset class ...` | `--data-config` includes kwargs not accepted by the selected dataset class. | Check the dataset constructor or move benchmark implementation changes to [benchmark-authoring](../../benchmark-authoring/SKILL.md). |
| `fps and nframe should not be set at the same time` | Video dataset config conflict. | Set exactly one of `fps` or `nframe`, or use a supported video preset. |
| Dataset is skipped as `invalid_dataset` | Unknown dataset name, missing optional dataset dependency, or failed download/cache setup. | Run `vlmutil dlist all`; check `LMUData`; inspect dataset logs; avoid assuming network downloads were successful. |
| `Model "..." not found in supported_VLM` in API mode | API mode needs a registry model or `--base-url`. | Use a registered model name or pass `--base-url` for an OpenAI-compatible endpoint. |
| `Unknown adapter: ...` | `--custom-prompt` is not registered. | List/inspect prompt adapters and route adapter implementation to [model-development](../../model-development/SKILL.md). |
| API mode says `WORLD_SIZE > 1` unsupported | Launched with `torchrun` or inherited distributed env. | Run API mode with plain `python` and unset distributed env vars. |
| `No reusable completed prediction found` in eval mode | No previous complete prediction under the same model output root. | Check `--work-dir`, model name, eval id, `PRED_FORMAT`, and whether failed rows were treated as incomplete. |
| `Incomplete infer result` | Prediction file exists but missing indices or retryable failure rows remain. | Rerun with `--reuse --reuse-aux infer` and omit `--keep-failed`; scan failures first. |
| Repeated `Failed to obtain answer via API.` rows | Provider errors, rate limits, payload/media incompatibility, or timeout. | Lower `--api-nproc`, increase `--retry`/`--timeout`, check `--base-url`, `--key`, `--video-llm`, `--local-media`, and provider logs. |
| Evaluation file has `All retries failed` or failed judge rows | Judge API/service failure. | Lower `--judge-api-nproc`, set `--judge-retry`, verify `--judge-base-url` and judge credentials, or use exact matching only when appropriate. |
| Very long predictions are truncated in spreadsheet output | `.xlsx` cell-length limit. | Set `PRED_FORMAT=tsv` before inference; rerun prediction generation if truncation already occurred. |
| Thinking text pollutes evaluated answers | Model returns `<think>...</think>` but predictions were not split. | Set `SPLIT_THINK=True`; for custom parsing, route model wrapper changes to [model-development](../../model-development/SKILL.md). |
| CUDA out-of-memory or process hangs at model load | Too many model instances or model weights too large. | Use `python run.py` for one model instance, reduce `--nproc-per-node`, narrow `CUDA_VISIBLE_DEVICES`, or choose a smaller/remote backend. |
| `torchrun` launches with zero or unexpected GPUs | No visible GPUs or incorrect `CUDA_VISIBLE_DEVICES`. | Run `nvidia-smi --list-gpus`; use [../scripts/run_torchrun.sh](../scripts/run_torchrun.sh) in `--dry-run` mode; fall back to `python run.py` for CPU/API tasks. |
| VLLM run conflicts with model splitting | `--use-vllm` backend may not support torchrun splitting. | Prefer `python run.py` with visible GPUs for VLLM unless the model path explicitly supports distributed operation. |
| `MMBench` evaluation requires official server | Local data lacks official answer fields. | Treat output as inference/submission artifact unless an official authorized evaluation source is available. |
| Test split without ground truth | Dataset supports inference but not local metric computation. | Use generated prediction/submission file; do not expect local metrics. |
| Latest files look stale | Model-root symlinks point to a different eval id than expected. | Inspect a specific `<work-dir>/<model>/<eval-id>/` directory and its `status.json`. |
| Summary script prints nothing | No dataset rows, missing `status.json`, or filtered data not present. | Run with `--verbose` on a specific eval-id directory and remove `--data` filters. |

## Environment variables

| Variable | Effect | Troubleshooting note |
| --- | --- | --- |
| `PRED_FORMAT` | Prediction format: default `xlsx`, optional `tsv` or `json`. | Use `tsv` for long responses; keep the same value when reusing predictions unless conversion is intended. |
| `EVAL_FORMAT` | Evaluation metric format: default `csv`, optional `json`. | Some evaluator auxiliaries may still be `.xlsx`; scan all matching files. |
| `SPLIT_THINK` | Splits thinking text from predictions when enabled. | Use for thinking models before evaluation metrics are produced. |
| `SKIP_ERR` | Local model inference catches runtime errors and writes failure text instead of aborting. | Useful for partial progress, but failures still need scan/retry decisions. |
| `MMEVAL_ROOT` | Overrides `--work-dir`. | If outputs are missing from the requested `--work-dir`, check this variable. |
| `EVAL_PROXY` | Temporarily sets proxy during evaluation. | Only affects evaluation-stage calls; provider inference may use other proxy settings. |
| `LOCAL_LLM` | Names a local judge model for wrappers that read it. | Ensure the local judge service and model name are reachable. |
| `FWD_API` | In local mode, routes supported API models through the `GPT4V` class path. | Use only when that compatibility path is intended. |
| `LMUData` | Data/cache root for datasets, localized media, and downloaded files. | Missing or unwritable cache roots cause dataset construction/download failures. |
| `VLMEVALKIT_USE_MODELSCOPE` | Enables ModelScope download routes where supported. | Does not guarantee every dataset is available; downloads were not verified during skill construction. |

## API and judge failures

For inference-provider failures:

```bash
python sub-skills/evaluation/scripts/scan_api_failures.py \
  --model-root outputs/MODEL \
  --datasets DATASET \
  --fail-on-detected
```

Then choose one:

- Retry failed rows: rerun with `--reuse --reuse-aux infer`, lower `--api-nproc`, increase `--retry`/`--timeout`, and omit `--keep-failed`.
- Preserve failures for auditing: rerun or summarize with `--keep-failed` only when no more provider calls are allowed.
- Change endpoint: use `--base-url`, `--key`, `--custom-prompt`, `--video-llm`, or `--local-media` only after confirming the service contract.

For judge failures:

- Confirm whether the dataset can use exact matching; many free-form tasks cannot.
- Set `--judge`, `--judge-base-url`, `--judge-key`, `--judge-api-nproc`, `--judge-retry`, and `--judge-timeout` explicitly.
- Inspect evaluation auxiliary files and `eval_logs/` for subprocess exceptions.

## Reuse and checkpoint failures

- `--reuse` only searches previous eval-id directories under the same `<work-dir>/<model>/` root.
- `PRED_FORMAT` changes can make prediction reuse require conversion; unsupported conversion is skipped.
- `--reuse-aux all` copies compatible evaluation auxiliary files only when judge model context matches.
- `--keep-failed` changes completeness checks: failed rows count as present, so eval may run on failed predictions.
- If rank pickle files remain after an interrupted distributed run, copy the run directory before using `vlmutil merge_pkl` or manual cleanup.

## What cannot be verified from the skill alone

| Need | Why it remains environment-specific |
| --- | --- |
| Live proprietary/API model success | Requires credentials, quotas, network, and provider-specific behavior. |
| Large local VLM evaluation | Requires model weights, compatible optional dependencies, GPU memory, and backend-specific versions. |
| Dataset downloads | Requires network access, license acceptance, cache storage, and stable upstream mirrors. |
| Video decoding and high-throughput video benchmarks | Requires video files, optional decoding packages, and media-compatible model/service behavior. |
| Gradio or official evaluation services | Starts external services and may move/upload files; not part of the safe default runtime. |

Do not treat documentation examples as verified runtime success unless the target environment has run the corresponding smoke or benchmark command.
