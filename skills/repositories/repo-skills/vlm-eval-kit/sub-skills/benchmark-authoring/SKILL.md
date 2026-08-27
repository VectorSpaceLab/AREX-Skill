---
name: benchmark-authoring
description: "Author and adapt VLMEvalKit benchmark datasets, TSV/video schemas,
  converters, dataset registration, prompts, and evaluators."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# VLMEvalKit Benchmark Authoring

Use this sub-skill when a task is about adding or adapting a VLMEvalKit benchmark, building a TSV or video metadata artifact, registering a dataset or video preset, implementing `build_prompt` / `evaluate`, or diagnosing dataset-construction failures.

## Route first

- Need to run a completed benchmark evaluation, resume predictions, scan API failures, or summarize outputs? Use [evaluation](../evaluation/SKILL.md).
- Need to add model wrappers, API wrappers, custom model-side prompts, or LiteLLM/OpenAI-compatible model configuration? Use [model-development](../model-development/SKILL.md).
- Need to create benchmark data, a dataset class, a video preset, an evaluator, or a converter? Stay here.

## Operating workflow

1. **Choose the authoring path.**
   - One-off local TSV: put `<DatasetName>.tsv` under `LMUData` or use a `--data-config` JSON data entry.
   - Reusable in-package benchmark: implement or reuse an `ImageBaseDataset`, `TextBaseDataset`, `VideoBaseDataset`, or task-specific subclass such as `ImageMCQDataset`.
   - Video benchmark: add a preset in `supported_video_datasets` with exactly one of `nframe` or `fps`.
   - Conversion task: build a TSV/image tree first; do not start full model inference from this sub-skill.
2. **Author and validate the data artifact.** Use [data formats](references/data-formats.md) for TSV columns, multimodal fields, cache roots, and local validation probes.
3. **Implement the dataset contract.** Use [dataset API reference](references/dataset-api-reference.md) for `load_data`, `prepare_tsv`, `dump_image`, `build_prompt`, `evaluate`, registries, custom fallback behavior, and MCQ evaluation helpers.
4. **Write or adapt converters safely.** Use [converter patterns](references/converter-patterns.md) and the bundled [LongDocURL TSV helper](scripts/build_longdocurl_tsv.py) as the small, runnable pattern. Treat large downloads, archives, and Gradio browsers as optional/reference-only workflows.
5. **Dry-check before handoff.** Prefer import/build/schema checks (`build_dataset`, column probes, tiny converter fixtures). Hand off any full evaluation command to [evaluation](../evaluation/SKILL.md).
6. **Troubleshoot from symptoms.** Use [troubleshooting](references/troubleshooting.md) for missing columns, broken image paths, unsupported-dataset fallback surprises, video frame-configuration errors, cache/download issues, and evaluator output problems.

## Validation boundary

The production evidence for this skill covered source inspection and lightweight runtime checks around package imports, `build_dataset`, dataset registries, CLI help/listing, native LiteLLM/API pipeline tests, and a CUDA smoke probe. It did **not** verify live API calls, dataset downloads, Gradio services, or large model evaluations. Keep those as user-authorized optional steps.
