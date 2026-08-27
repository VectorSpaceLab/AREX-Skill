---
name: baselines-and-projects
description: "Choose and safely operate Scenic baselines and project-specific
  research stacks, configs, registries, optional dependencies, checkpoints,
  datasets, and repo-owned tools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Baselines and Projects

Use this sub-skill when a task is about **which Scenic project or baseline to start from**, how project-specific binaries/configs/registries fit together, which optional dependency stack is needed, or whether a repo-owned conversion/evaluation tool is safe to run.

Do **not** use this sub-skill for generic launch mechanics, low-level dataset registry implementation, or model/layer APIs:

- Route `python -m ... --config=... --workdir=...`, config override syntax, workdir/checkpoint hygiene, device flags, and restart/eval-only mechanics to `running-and-training` after this sub-skill identifies the project and required config fields.
- Route TFDS/DMVR/FlexIO dataset registration and preprocessing operator internals to `data-pipelines`.
- Route Flax module signatures, model/layer implementation details, parameter trees, and checkpoint surgery to `modeling-and-layers`.

## Fast decision procedure

1. Identify the user's task family and modality.
   - Video classification: start with ViViT for the canonical pure-transformer baseline, MTV for multi-view video recognition, TokenLearner for token-reduction experiments, AV-MAE for audio/video self-supervised pretraining or finetuning, and ObjectViViT when external object boxes are part of the method.
   - Open-vocabulary or text-conditioned object detection: start with OWL-ViT. Use CLIP only for image/text embedding baselines, not detection by itself.
   - Dense video captioning: use Vid2Seq for offline single-stage dense captioning, Streaming DVC for long/low-latency streaming captions, and DenseVOC when the output must track and caption object trajectories.
   - Generic image classification: use the baseline ViT, MLP-Mixer, ResNet/BiT, Axial-ResNet, TokenLearner, MatViT, or PlainViT families depending on the architecture being compared.
   - Detection/segmentation baselines: use DETR, Deformable DETR, CenterNet/CenterNet2, OWL-ViT, or SAM according to the supervision and prompt/query style.
2. Read [references/project-catalog.md](references/project-catalog.md) for the project family catalog, route selection table, project structure pattern, and project-specific main/config/registry conventions.
3. Read [references/baseline-recipes.md](references/baseline-recipes.md) when the user asks for a baseline recipe, a safe baseline config adaptation, or the difference between ViT/ResNet/DETR/CLIP/BERT/MLP-Mixer/UNet/CenterNet/SAM families.
4. Read [references/optional-dependencies.md](references/optional-dependencies.md) before installing project extras or interpreting missing imports. Install only the group required by the selected project.
5. Read [references/troubleshooting.md](references/troubleshooting.md) before running project-owned conversion/evaluation tools, when data/checkpoints/tokenizers/Java are missing, or when a custom registry reports an unsupported model/trainer/dataset.
6. Optionally run [scripts/project_config_index.py](scripts/project_config_index.py) against a user-supplied Scenic checkout to get a non-importing inventory of project config files, requirements files, and tool-script names before choosing a route.

## Required context to collect before acting

Ask or infer the following before recommending a project, installing extras, or approving a project tool:

- Task output: classification labels, boxes, masks, temporal segments, dense captions, object trajectories, layout labels, point-cloud classes/parts, genomic variant classes, etc.
- Modality: image, video, audio, audio+video, text+image, text+video, point cloud, UI layout, genomic pileup image.
- Desired baseline type: stable baseline, newest project, reproduction target, transfer/fine-tune, inference only, or data conversion only.
- Dataset status: already in TFDS/DMVR/FlexIO/TFRecord form, raw files only, remote/private storage, or not yet acquired.
- Checkpoint/tokenizer status: Scenic checkpoint, big_vision/ViT checkpoint, CLIP/Torch checkpoint, T5/T5X checkpoint, BERT vocab, SAM/MAE/VitDet conversion, or absent.
- Compute and dependency budget: CPU smoke only, single GPU, multi-GPU/TPU, strict pinned JAX/Flax environment, or no network installs.

## Safety rules

- Treat project-owned `tools/` scripts and conversion notebooks as **reference-only until prerequisites are proven**. Many tools read large external datasets, download or convert checkpoints, require Java or dataset credentials, and write TFRecords/JSON/checkpoints. See [references/troubleshooting.md](references/troubleshooting.md#project-owned-tool-guardrails).
- Do not run a conversion/evaluation tool merely because the user names it. First confirm all required input files, output location, expected runtime/storage, credentials, and overwrite behavior.
- If a requested project requires unavailable data, checkpoints, tokenizer files, Java, or accelerator memory, stop with a prerequisites list instead of silently switching projects.
- If two projects require conflicting pins, create isolated environments; do not mix Deformable DETR's old JAX/CUDA pins, Vid2Seq's Flax 0.5 expectation, Lingvo, and modern JAX extras in one environment.
- Record any narrowed recommendation explicitly: e.g. "OWL-ViT is the open-vocabulary detector, but with no LVIS/COCO annotations available I can only prepare an inference or config-inspection path."

## Quick handoff templates

Project selection handoff to `running-and-training`:

```text
Selected Scenic project: <project family>
Reason: <task/modality/desired output>
Entrypoint module: <python -m module name>
Config identifier: <package-relative config path string or config module>
Required config fields to set: <dataset paths, weights/checkpoint, tokenizer, eval_only, batch size>
Optional dependency group: <group from optional-dependencies.md>
Blocked prerequisites: <none or explicit data/checkpoint/compute/credential list>
```

Unsafe tool response template:

```text
Do not run the project tool yet. It is a conversion/evaluation helper with external data/write side effects.
Prerequisites to verify first: <input dataset/annotation/checkpoint/tokenizer>, <output path>, <storage/runtime>, <credentials>, <overwrite policy>.
Safe alternative now: use scripts/project_config_index.py for static inventory, or prepare a dry prerequisite checklist.
```
