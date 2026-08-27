---
name: benchmark-evaluation
description: "Guide Otter config-driven benchmark evaluation, registries,
  GPT-judged requirements, logging, cache/model paths, and public suite
  caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Otter benchmark-evaluation sub-skill

Use this sub-skill when the task is to plan, validate, or run Otter benchmark evaluation with `pipeline.benchmarks.evaluate`, benchmark YAMLs, supported model/dataset registry names, GPT-judged benchmark credentials, output logs, cache directories, or the OpenFlamingo-style public dataset suite.

## Fast route

1. Pick the evaluator path:
   - Config-driven Otter evaluator: [benchmark-configs](references/benchmark-configs.md).
   - Supported `models[].name` and `datasets[].name` keys: [model-and-dataset-registry](references/model-and-dataset-registry.md).
   - Public COCO/VQA/Flickr/TextVQA/VizWiz/Hateful-Memes/ImageNet suite: [public-suite](references/public-suite.md).
2. Validate the benchmark YAML before launching model or dataset downloads:

```bash
python scripts/validate_benchmark_config.py benchmark.yaml
```

3. Launch with the correct flag name after validation:

```bash
python -m pipeline.benchmarks.evaluate --config benchmark.yaml
```

The source docs contain a typo, `--confg`; use `--config` or `-c`.

4. Before expensive or networked runs, check [troubleshooting](references/troubleshooting.md) for GPT API keys, Hugging Face dataset downloads, missing local model repos, cache placement, and expected skip reasons.

## Route elsewhere

- Training and finetuning launch construction: [training](../training/SKILL.md).
- MIMIC-IT, Syphus, Convert-It, and large data conversion: [data-preparation](../data-preparation/SKILL.md).
- Controller/worker/Gradio/API serving: [serving](../serving/SKILL.md).
- Prompt/media tensor details for ad hoc generation outside benchmarks: [model-inference](../model-inference/SKILL.md).

## Safety boundary

Benchmark evaluation can load large models, download benchmark datasets, write result files, and call paid GPT APIs. This skill supports static planning and config validation; only run evaluation when the user has supplied model paths or approved downloads, dataset/cache/output locations, required credentials, and GPU/runtime budget.
