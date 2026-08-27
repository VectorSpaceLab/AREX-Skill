# Cross-cutting Troubleshooting

Use this when the failure happens before a workflow-specific sub-skill is obvious.

## `otter_ai` import fails

1. Confirm the distribution and import names: install `otter-ai`, import `otter_ai`.
2. Run `python scripts/check_otter_environment.py --json` from this skill's root.
3. If the traceback mentions `split_torch_state_dict_into_shards` or `huggingface_hub.errors`, check for a mismatched Transformers/Accelerate/PEFT/Hub stack. A source-compatible set is:

```bash
python -m pip install "transformers==4.35.1" "tokenizers==0.14.1" \
  "huggingface_hub==0.17.3" "accelerate==0.23.0" "peft==0.4.0"
```

4. If the traceback involves `xformers_model`, read [model-inference troubleshooting](../sub-skills/model-inference/references/troubleshooting.md#xformers-and-xformers_model-risk).

## CUDA exists but model runtime fails

A successful CUDA import or tiny tensor allocation proves only basic framework visibility. It does not prove that a 7B/9B multimodal checkpoint fits memory, that Flash-Attention/fused operators are installed, or that a serving worker can load the model.

- For generation shape/prompt issues: [model-inference troubleshooting](../sub-skills/model-inference/references/troubleshooting.md).
- For training memory and distributed launch issues: [training troubleshooting](../sub-skills/training/references/troubleshooting.md).
- For model-worker CUDA errors: [serving troubleshooting](../sub-skills/serving/references/troubleshooting.md#cuda-or-model-load-failures).

## Data path or schema errors

If a training run fails before loading batches, do not change model code first. Validate the MIMIC-IT YAML and referenced instruction/image files with [data-preparation](../sub-skills/data-preparation/SKILL.md). Common root causes are unexpected group names, missing `data` in instruction JSON, missing image ids in parquet/json, nonexistent paths, and `num_samples` values with the wrong type.

## Benchmark or GPT judging errors

Benchmark evaluation can require large datasets, local model paths, Hugging Face downloads, and API keys for GPT-judged datasets. Validate config structure with [benchmark-evaluation](../sub-skills/benchmark-evaluation/SKILL.md) before running. The source docs contain a typo: use `--config` or `-c`, not `--confg`.

## Serving import errors

If controller, model worker, or Gradio modules fail before showing help, route to [serving troubleshooting](../sub-skills/serving/references/troubleshooting.md). Known defects include missing `pipeline.constants` and a top-level `flamingo` import in the worker.

## Credential and network boundaries

- Syphus and GPT-judged benchmarks can call external APIs or local OpenAI-compatible services.
- Gradio moderation uses OpenAI moderation and requires `OPENAI_API_KEY`.
- Hugging Face model loading may download checkpoints automatically unless offline/cache settings are configured.

Do not run these paths without explicit user approval for credentials, network, cost, and cache locations.

## Where to route next

| Symptom | Next sub-skill |
|---|---|
| `vision_x`, `lang_x`, prompt formatting, batch inference YAML, checkpoint conversion | [model-inference](../sub-skills/model-inference/SKILL.md) |
| Accelerate/DeepSpeed launch, W&B, checkpointing, Fuyu/OtterHD finetuning | [training](../sub-skills/training/SKILL.md) |
| MIMIC-IT YAML, instruction JSON, image parquet/JSON, Syphus/Convert-It | [data-preparation](../sub-skills/data-preparation/SKILL.md) |
| Benchmark config, dataset/model registry, GPT judging | [benchmark-evaluation](../sub-skills/benchmark-evaluation/SKILL.md) |
| Controller/worker/Gradio, endpoints, ports, model-worker load bits | [serving](../sub-skills/serving/SKILL.md) |
