# VLMEvalKit troubleshooting

Start with the symptom and route to a sub-skill once the failure surface is clear.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import logs `Did not detect the .env file` | No repository-local `.env` file for API keys. | Non-fatal for imports. Set provider keys in the environment or create `.env` only when API/judge calls need it. |
| `ModuleNotFoundError: rouge_score` | MMLongBench metrics import `rouge_score`, but broad requirements may not install it. | Install `rouge-score` in the active environment. |
| `pip check` reports `decord ... not supported on this platform` | Pip decord wheel metadata/platform mismatch. | If video decoding is needed, try a conda-forge `decord` package or verify `import decord` plus a tiny local video fixture. |
| NumPy/Pandas/OpenCV binary errors | Compiled wheel ABI/version mismatch. | Pin a compatible trio for the task; verify `import numpy, pandas, cv2` and rerun native tests. |
| `torch` imports but CUDA is false | CPU torch wheel, missing GPU passthrough, incompatible driver/runtime, or container limitation. | Check `nvidia-smi`, `torch.version.cuda`, `torch.cuda.is_available()`, and use a wheel compatible with the driver/GPU. |
| `run.py --help` imports many modules slowly | The runner imports model/dataset registries at startup. | Treat slow help as normal after a cold import; if it fails, inspect the first missing dependency in the traceback. |

## API and judge failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Many predictions contain `Failed to obtain answer via API` | Missing key/base URL, provider outage, rate limits, timeout, or wrong model name. | Scan outputs with `evaluation/scripts/scan_api_failures.py`, fix credentials/service, then rerun with reuse enabled and `--keep-failed` only when you intentionally want to preserve failures. |
| Judge evaluation fails but inference succeeded | Judge model/key/base URL or exact-matching fallback is unsuitable for the dataset. | Use `--judge`, `--judge-base-url`, `--judge-key`, `--judge-api-nproc`, and `--judge-retry`; for local judges, set `LOCAL_LLM` as documented. |
| LiteLLM provider raises missing package or provider-specific error | `litellm` not installed, provider model string wrong, or provider env vars missing. | Install `litellm>=1.55,<1.85`, set `LITELLM_API_KEY`/provider keys, and test a tiny provider call outside full evaluation. |
| OpenAI-compatible `--base-url` gives 404 or malformed URL | VLMEvalKit appends `/chat/completions` to the base URL. | Pass the service root ending in `/v1`, not a full `/chat/completions` URL unless the specific wrapper expects it. |

## Data/cache failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Dataset build returns `None` for a custom dataset | TSV not found under `LMUData` or lacks a `question` column. | Put `<DatasetName>.tsv` under `LMUData`, add required columns, or provide `--data-config` with the proper class. |
| Image paths fail during prompt building | `image_path` is relative to the wrong image root, missing, or malformed JSON list. | Read `benchmark-authoring/references/data-formats.md`; validate TSV rows and `LMUData/images/<dataset>` layout. |
| Large TSV localization repeats or is stale | `*_local.tsv` is missing/stale or `FORCE_LOCAL` is set. | Unset `FORCE_LOCAL` for reuse, or regenerate localization intentionally. |
| Video dataset errors on `fps`/`nframe` | Both or neither are set where the dataset requires exactly one frame policy. | Use a preset from `supported_video_datasets` or define a `--data-config` item with only `nframe` or only `fps`. |
| Download fails from Hugging Face/OpenCompass/ModelScope | Network, mirror, token, or region issue. | Use existing local TSV/images where possible; set `VLMEVALKIT_USE_MODELSCOPE` for supported paths; pass HF tokens only through environment variables. |

## Output/result failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Long model answers truncated in spreadsheets | `.xlsx` cell size limit. | Set `PRED_FORMAT=tsv` before inference for long-response/thinking models. |
| Thinking text pollutes evaluated answer | `<think>...</think>` content not split or model uses a nonstandard format. | Set `SPLIT_THINK=True`; if custom splitting is needed, route to `model-development` to implement `split_thinking`. |
| Eval-only mode skips combinations | No completed reusable prediction file exists. | Rerun inference or enable the correct `--reuse`/`--reuse-aux` path from `evaluation/references/workflows.md`. |
| `status.json` says done with skip reason | Dataset is official-submission-only, test split lacks answers, invalid dataset, or evaluation returned `None`. | Read `evaluation/references/results-and-status.md`; decide whether this is expected or a dataset/evaluator bug. |

## When to route deeper

- Command construction, `run.py` flags, reuse, output scans, and summaries: [evaluation](../sub-skills/evaluation/SKILL.md).
- Model/API wrapper, `supported_VLM`, provider, prompt adapter, or media-format issues: [model-development](../sub-skills/model-development/SKILL.md).
- Dataset class, TSV/video schema, converter, `build_prompt`, or `evaluate` issues: [benchmark-authoring](../sub-skills/benchmark-authoring/SKILL.md).
