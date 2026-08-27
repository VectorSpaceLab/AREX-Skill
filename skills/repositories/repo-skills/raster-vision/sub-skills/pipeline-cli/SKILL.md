---
name: pipeline-cli
description: "Guides Raster Vision agents through rastervision CLI pipeline
  runs, pipeline configs, runners, model bundles, and config or URI
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# pipeline-cli

Use this sub-skill when a Raster Vision request is about:
- `rastervision run`, `run_command`, `predict`, or `predict_scene`
- `PipelineConfig` / `RVPipelineConfig` loading, output URIs, or `get_config(s)` modules
- `--arg`, `--splits`, runner selection, or config summary checks
- model bundles, prediction inputs, or CLI failures caused by config or URI mismatches

## Read first
1. [CLI reference](references/cli-reference.md)
2. [Pipeline configuration](references/pipeline-configuration.md)
3. [Model bundles](references/model-bundles.md)
4. [Troubleshooting](references/troubleshooting.md)

## Runtime helper
Use [scripts/summarize_pipeline_config.py](scripts/summarize_pipeline_config.py) to inspect a Raster Vision config module or JSON file without executing any pipeline commands.

## Boundaries
- Keep this sub-skill to Raster Vision CLI and generic pipeline execution.
- Route core data, source, and label APIs to the data-and-models sub-skill.
- Route PyTorch task recipes to the pytorch-workflows sub-skill.
- Route AWS, Docker, and CloudFormation details to the cloud-and-filesystems sub-skill.
- Do not include runner internals beyond CLI-level routing.
