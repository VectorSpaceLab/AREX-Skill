# CLI reference for evaluation

This reference focuses on operating VLMEvalKit. It assumes `vlmeval` is installed and that `run.py` is available from the working tree or through an explicit path chosen by the user.

## Preflight commands

```bash
python run.py --help
vlmutil dlist l1
vlmutil mlist api
```

Use `vlmutil check MODEL_NAME` only after accepting its side effects: it instantiates the model and calls `generate` on a sample image, so it can require GPU memory, model weights, or API access.

## `run.py` launch forms

### Direct dataset/model lists

```bash
python run.py \
  --data MMBench_DEV_EN MME \
  --model GPT4o \
  --work-dir outputs \
  --mode all \
  --api-nproc 16 \
  --retry 6
```

Rules:

- `--data` and `--model` are lists of registered names.
- Use `vlmutil dlist all` and `vlmutil mlist all` to inspect the installed registry.
- `--mode all` runs inference and evaluation; `--mode infer` writes predictions only; `--mode eval` forces `--reuse` and evaluates existing completed predictions.
- `MMEVAL_ROOT` overrides `--work-dir` when set.

### JSON config file

```bash
python run.py --config config.json --work-dir outputs
```

Rules:

- `--config` is mutually exclusive with `--data`, `--model`, and `--data-config`.
- The config JSON has top-level `model` and `data` objects.
- Model entries either reference a `supported_VLM` shortcut with `{}` or specify a `class` in `vlmeval.vlm`/`vlmeval.api` plus class kwargs.
- Data entries specify a class in `vlmeval.dataset`, usually a `dataset` value, and video settings such as `nframe` or `fps` when needed.

Minimal shape:

```json
{
  "model": {
    "GPT4o_alias": {"class": "GPT4V", "model": "gpt-4o", "temperature": 0}
  },
  "data": {
    "MMBench_DEV_EN_V11": {"class": "ImageMCQDataset", "dataset": "MMBench_DEV_EN_V11"},
    "Video-MME_16frame": {"class": "VideoMME", "dataset": "Video-MME", "nframe": 16}
  }
}
```

### Inline dataset config

Use `--data-config` when one command needs custom dataset names or video options but a full config file is unnecessary.

```bash
python run.py \
  --data Video-MME_16frame_subs \
  --model GPT4o \
  --data-config '{"Video-MME_16frame_subs":{"class":"VideoMME","dataset":"Video-MME","nframe":16,"use_subtitle":true}}'
```

Rules:

- The value must be a JSON object string.
- Keys must match names passed to `--data`.
- Dataset config values must be JSON objects; `class` and `dataset` must be strings when present.
- For video datasets, do not set both `fps` and `nframe`; set at least one valid value unless using a supported preset shortcut.

## Modes, reuse, and failure retry flags

| Flag | Use |
| --- | --- |
| `--mode all` | Run inference then evaluation. Default. |
| `--mode infer` | Stop after prediction file generation. Status marks datasets done with `mode_infer`. |
| `--mode eval` | Reuse completed prediction files and run only evaluation. If no complete reusable prediction exists, the dataset is skipped. |
| `--reuse` | Search previous eval-id run directories under the same model output root and copy prediction/auxiliary files into the new run. |
| `--reuse-aux all` | Reuse inference auxiliary files and compatible evaluation auxiliary files. Default. |
| `--reuse-aux infer` | Reuse inference checkpoints/temporaries only. |
| `--reuse-aux none` | Reuse prediction files only. |
| `--keep-failed` | Treat rows containing the standard API failure text as completed; otherwise failed rows are dropped from checkpoints and retried. |
| `--retry N` | Set retry count for API VLMs and, by default, judge calls. |

Typical resume/evaluate sequence:

```bash
# First create predictions only.
python run.py --data MMBench_DEV_EN --model GPT4o --mode infer --work-dir outputs

# Later evaluate the latest reusable prediction, preserving compatible aux files.
python run.py --data MMBench_DEV_EN --model GPT4o --mode eval --reuse --reuse-aux all --work-dir outputs
```

## Distributed and backend flags

```bash
torchrun --nproc-per-node=2 run.py --data MME --model qwen_chat --work-dir outputs
```

- With `torchrun`, `run.py` derives GPU visibility from `CUDA_VISIBLE_DEVICES` or `nvidia-smi` and assigns a slice of visible GPUs to each local rank.
- Prefer `python run.py` for very large models that internally shard across all visible GPUs.
- `--use-vllm` is passed through only for supported model paths; do not combine it with assumptions about torchrun model splitting unless the model documentation confirms support.
- `--use-verifier` passes verifier intent into judge kwargs.
- Use [../scripts/run_torchrun.sh](../scripts/run_torchrun.sh) for a safer torchrun wrapper that checks visible GPU count and supports dry-run command review.

## API and OpenAI-compatible endpoint flags

```bash
python run.py \
  --data MMStar \
  --model InternVL2-8B \
  --base-url http://localhost:23333/v1 \
  --key "$INFERENCE_API_KEY" \
  --api-nproc 64 \
  --retry 4 \
  --timeout 1800
```

- `--base-url` creates an LMDeploy/OpenAI-compatible model without editing `vlmeval/config.py`; pass the base API root such as `http://host:port/v1`, because `run.py` appends `/chat/completions`.
- `--key` sets the inference API key argument. Prefer environment variables or a local `.env` file instead of embedding secrets in shell history or committed scripts.
- `--custom-prompt ADAPTER` selects a registered prompt adapter by name.
- `--video-llm` declares that the API model can accept native video inputs.
- `--local-media` sends local media file paths to the API model rather than uploading/encoding media.
- `--stream` enables streaming for OpenAI-compatible API models.
- `--extra-body '{...}'` merges extra JSON parameters into inference model args.
- `--max-tokens`, `--temperature`, `--top-k`, `--top-p`, `--repetition-penalty`, and `--timeout` tune requests when the selected wrapper accepts them.

## Judge flags

```bash
python run.py \
  --data MathVista_MINI \
  --model GPT4o \
  --judge gpt-4o-mini \
  --judge-api-nproc 8 \
  --judge-retry 4 \
  --judge-timeout 600
```

| Flag | Use |
| --- | --- |
| `--judge MODEL` | Override dataset-specific default judge selection. |
| `--judge-args '{...}'` | Merge additional judge kwargs from JSON. |
| `--judge-base-url URL` | Use an OpenAI-compatible judge endpoint; pass the base API root, not the final chat-completions URL. |
| `--judge-key VALUE` | Set judge API key argument; prefer environment or local dotenv handling for real credentials. |
| `--judge-api-nproc N` | Set judge concurrency; defaults to `--api-nproc` when unset. |
| `--judge-retry N` | Set judge retry count; defaults to `--retry` when unset. |
| `--judge-timeout SEC` | Set per-judgement timeout. |

If no judge key/service is available, some yes/no and multiple-choice tasks can fall back to exact matching. Free-form tasks normally need a judge model.

## Async API pipeline (`--api-mode`)

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

Rules:

- API mode supports a single model per command.
- Do not launch API mode with multi-process `torchrun`; the pipeline rejects `WORLD_SIZE > 1`.
- API mode builds all valid dataset configs first, then uses `APIEvalPipeline` for a unified async inference queue and subprocess evaluation.
- `--debug` runs evaluation in the main process and is useful only for debugging evaluator exceptions.

## `vlmutil` operating modes

| Mode | Command | Notes |
| --- | --- | --- |
| Dataset list | `vlmutil dlist l1` or `vlmutil dlist all` | Lists predefined benchmark groups or all supported datasets. |
| Model list | `vlmutil mlist api`, `vlmutil mlist all`, `vlmutil mlist 4.37.0 small` | Lists model registry groups; exact availability depends on installed optional dependencies. |
| Model check | `vlmutil check MODEL_NAME` | Instantiates a model and calls generation on a sample image; may need GPUs, weights, or API access. |
| Single-file eval | `vlmutil eval DATASET_NAME PREDICTION_FILE --judge JUDGE_NAME` | Re-evaluates a prediction file with optional judge override. |
| Result scan | `vlmutil scan --model MODEL --data DATASET --root outputs` | Scans existing result files for API failures; see also the bundled scan script. |
| Merge pkl | `vlmutil merge_pkl PKL_DIR WORLD_SIZE` | Re-merges rank-sharded pickle outputs for world sizes 1, 2, 4, or 8. Use only on a copied or well-understood output directory. |
| Missing report | `vlmutil missing l1` | Maintainer-scale report based on default `outputs/` conventions; can write a missing list file. |
| Auto run | `vlmutil run l2 hf` | Maintainer-scale launcher that may start many GPU jobs. Prefer explicit `run.py` commands for normal operation. |

## Source-script decisions

- `scripts/run.sh` was adapted into [../scripts/run_torchrun.sh](../scripts/run_torchrun.sh) with usage text, dry-run support, and GPU checks.
- `scripts/apires_scan.py` was adapted into [../scripts/scan_api_failures.py](../scripts/scan_api_failures.py) with explicit arguments and no source-checkout dependency.
- `scripts/summarize.py` was adapted into [../scripts/summarize_runs.py](../scripts/summarize_runs.py) with direct `status.json` parsing.
- `scripts/srun.sh`, `scripts/auto_run.py`, and `scripts/mmb_eval_gradio.py` are reference-only because they are cluster-, maintainer-, or service-launcher workflows rather than safe default runtime helpers.
