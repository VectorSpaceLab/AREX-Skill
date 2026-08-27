---
name: data-preparation
description: "Prepare and validate Otter MIMIC-IT data YAMLs, instruction JSON,
  image parquet/JSON assets, Convert-It outputs, and Syphus preflight."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-preparation

Use this sub-skill when the task is to prepare Otter training data before handing it to training: MIMIC-IT YAML validation, instruction JSON checks, image parquet or legacy base64 JSON handling, Convert-It adapter planning, Syphus instruction-generation preflight, and large dataset conversion safety.

## Route here for

- Data YAMLs containing `IMAGE_TEXT`, `TEXT_ONLY`, `VIDEO_TEXT`, and `IMAGE_TEXT_IN_CONTEXT` groups.
- Dataset entries with `mimicit_path`, optional `images_path`, optional `train_config_path`, `num_samples`, and optional `task_description`.
- Instruction JSON files with a top-level `data` object of instruction ids.
- Image parquet files with a `base64` column indexed by image id, or legacy image JSON files that should be converted to parquet.
- Convert-It adapter names and expected image JSON output filenames.
- Syphus environment and dependency preflight without making model/API calls.
- Safe conversion of large base64 JSON files into partitioned parquet outputs.

## Route away

- Actual training launch, Accelerate, DeepSpeed, W&B, checkpoint cadence, or GPU training resources: [training](../training/SKILL.md).
- Model inference, generation, prompt/media tensors, or checkpoint conversion for inference: [model-inference](../model-inference/SKILL.md).
- Benchmark dataset/model registries and evaluation YAMLs: [benchmark-evaluation](../benchmark-evaluation/SKILL.md).
- Controller/worker/Gradio/API serving: [serving](../serving/SKILL.md).

## Operating workflow

1. Normalize the data task: YAML validation, JSON/parquet conversion, Convert-It source conversion planning, Syphus preflight, or large WebDataset conversion planning.
2. For training data YAMLs, read [data formats](references/data-formats.md), start from [mimicit_data.yaml](scripts/templates/mimicit_data.yaml), and validate with:

```bash
python scripts/validate_mimicit_yaml.py DATA.yaml --check-paths --check-records
```

3. For legacy image JSON, convert to parquet before training:

```bash
python scripts/convert_base64_json_to_parquet.py images.json images.parquet --validate-sample 8
```

4. For Convert-It tasks, use [Convert-It](references/convert-it.md) to choose the adapter id and expected output file, then convert the resulting image JSON to parquet if it will be used for training.
5. For Syphus tasks, use [Syphus](references/syphus.md) and run the no-network preflight:

```bash
python scripts/check_syphus_env.py --dataset-name video.DenseCaptions
```

6. For very large conversions, read [large dataset conversion](references/large-dataset-conversion.md) before creating shards or parquet directories.
7. If validation or loading fails, use [troubleshooting](references/troubleshooting.md) before changing dataset contents.

## Quick reference map

| Need | Start with |
|---|---|
| MIMIC-IT YAML schema and loader behavior | [data-formats](references/data-formats.md) |
| Validate YAML, JSON, parquet, and id links | [validate_mimicit_yaml.py](scripts/validate_mimicit_yaml.py) |
| Convert legacy image JSON to parquet | [convert_base64_json_to_parquet.py](scripts/convert_base64_json_to_parquet.py) |
| Convert-It adapter names and outputs | [convert-it](references/convert-it.md) |
| Syphus env vars, output files, dependency preflight | [syphus](references/syphus.md), [check_syphus_env.py](scripts/check_syphus_env.py) |
| MMC4/LAION-style large conversion safety | [large-dataset-conversion](references/large-dataset-conversion.md) |
| Common validation and loader failures | [troubleshooting](references/troubleshooting.md) |

## Safety boundary

Data preparation can touch large local datasets and credentialed services. Do not launch training from this skill. Do not start Syphus API calls, Convert-It media conversion, or multi-shard WebDataset conversion unless the user supplies paths, budget, licensing/credential confirmation, and permission to run the job. The bundled scripts are local validation/preflight/conversion helpers only.
