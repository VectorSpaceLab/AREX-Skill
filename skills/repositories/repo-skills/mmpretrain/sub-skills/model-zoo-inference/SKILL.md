---
name: model-zoo-inference
description: "Operate MMPreTrain model zoo discovery, inference APIs, task
  inferencers, and feature extraction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMPreTrain model zoo and inference router

Use this sub-skill when the user needs to discover packaged MMPreTrain model names, construct a model from the model zoo or a config, run an inference API, extract image features, choose checkpoint/device/offload options, or interpret an inferencer result.

## Route by intent

- **Find a model name or task family:** use `references/api-reference.md` for `list_models`, task-filter names, and `ModelHub` behavior. The bundled `scripts/list_models.py` helper is safe for local model-zoo discovery and does not download checkpoints.
- **Construct a model without weights or with a local/URL checkpoint:** use `references/api-reference.md#get_model-and-checkpoint-selection` and prefer `pretrained=False` when the user explicitly wants no download.
- **Run image classification:** use `references/inference-recipes.md#image-classification` or the bundled `scripts/classify_image.py` helper. The helper avoids checkpoint downloads unless the caller passes `--checkpoint` or `--use-default-checkpoint`.
- **Run image retrieval or multimodal retrieval:** use `references/inference-recipes.md#retrieval-prototypes-caches-and-top-k` for `prototype`, `prototype_cache`, `prepare_batch_size`, `fast_match`, and `topk` planning.
- **Run captioning, VQA, visual grounding, or NLVR:** use `references/inference-recipes.md#multimodal-inferencers` and check optional dependency gates in `references/troubleshooting.md`.
- **Extract features or do no-download model surgery:** use `references/inference-recipes.md#no-download-model-surgery-and-feature-extraction`.
- **Debug model-index, checkpoint, device, prototype, visualization, or optional-extra failures:** use `references/troubleshooting.md`.

## Boundary and handoff

- Route training commands, config authoring, evaluation, resume/AMP/TTA, and checkpoint production to `../training-and-evaluation/SKILL.md`.
- Route dataset annotation schemas, custom datasets, custom registries, transforms, and project modules to `../datasets-and-customization/SKILL.md`.
- Route CAM, t-SNE, log/result analysis, FLOPs, checkpoint publishing/conversion, TorchServe, and deployment utilities to `../tools-analysis-and-deployment/SKILL.md`.
- Do not ask users to open repository docs, demos, tests, configs, or scripts. Use the bundled references and helpers here, or route to the neighboring sub-skill.

## Operational defaults

1. Decide whether the request may download weights before constructing an inferencer. MMPreTrain inferencer classes default to `pretrained=True`; `get_model` defaults to `pretrained=False`.
2. For offline or architecture-only work, use `pretrained=False` and `device='cpu'` unless the user chooses a verified accelerator environment.
3. For meaningful predictions, use an explicit local checkpoint path or an allowed URL/default checkpoint. Keep cache/network failures separate from model-name failures.
4. Treat returned dictionaries as convenient summaries. Use `return_datasamples=True` when the user needs full `DataSample` tensors/fields for downstream Python logic.
5. Use `show_dir` instead of `show=True` in headless sessions.
