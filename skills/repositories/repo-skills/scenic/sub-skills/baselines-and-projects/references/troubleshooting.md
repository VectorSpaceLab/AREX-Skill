# Troubleshooting baselines, projects, checkpoints, datasets, registries, and tools

Use this reference before retrying a failed project run or approving a project-owned conversion/evaluation tool. The safest default is static inspection plus a prerequisite checklist; only run data/checkpoint tools after inputs, outputs, credentials, and compute are explicit.

## Quick triage

| Failure or request | First action | Likely owner after triage |
|---|---|---|
| User asks which project to start from | Use `project-catalog.md` route tables; identify task output and modality. | This sub-skill, then `running-and-training`. |
| Missing import | Identify project and dependency group in `optional-dependencies.md`; install only that group. | This sub-skill for group choice; environment preparation/runner for install. |
| Unsupported model/trainer/dataset | Check selected project's registry pattern and config key names. | This sub-skill for registry route; `modeling-and-layers` if implementation details are needed. |
| Placeholder checkpoint/data path | Stop and ask for real path, checkpoint type, and data state. | User/data owner; `data-pipelines` for dataset preparation. |
| User wants to run a `tools/` helper | Treat as reference-only until prerequisites and write policy are verified. | This sub-skill for guardrails; `data-pipelines` for conversions when approved. |
| Eval metric fails late | Check annotation files, prediction JSON, caption metrics, Java, LVIS/COCO packages. | This sub-skill for prerequisites; `running-and-training` for rerun. |
| GPU/TPU memory or device failure | Check project memory assumptions and reduce scope; do not assert CPU equivalence. | `running-and-training`. |

## Missing optional dependencies

| Error text or symptom | Typical project(s) | Meaning | Recovery |
|---|---|---|---|
| `ModuleNotFoundError: dmvr` | ViViT, MTV, Vid2Seq, Streaming DVC, MBT, ObjectViViT, PolyViT | Video input/preprocessing extra not installed. | Install the DMVR group only for selected video project; otherwise perform static config inspection. |
| `ModuleNotFoundError: lingvo` | MBT | Audio/video MBT stack missing. | Use a dedicated MBT environment; Lingvo can conflict with other TensorFlow/JAX stacks. |
| `ModuleNotFoundError: t5`, `t5x`, `gin` | Vid2Seq, Streaming DVC Vid2Seq routes, PixelLLM T5 configs | Text decoder stack missing. | Install T5/T5X group and require a T5/T5X checkpoint path. |
| `ModuleNotFoundError: clip` or Torch loader errors | CLIP baseline, OWL-ViT, CLIP conversion routes | Torch/OpenAI CLIP stack missing or checkpoint type mismatch. | Install CLIP/Torch group; verify whether checkpoint is Torch, `.npy`, Scenic, or converted JAX format. |
| `ModuleNotFoundError: big_vision` | OWL-ViT, PlainViT, big_vision checkpoint-format routes | big_vision source package not importable. | Install big_vision or change route only if the checkpoint format is truly Scenic-compatible. |
| `ModuleNotFoundError: tensorflow_addons` | Big Transfer style image preprocessing | Big Transfer preprocessing ops require TensorFlow Addons. | Install tensorflow-addons or choose preprocessing not using those ops. |
| `ModuleNotFoundError: pycocotools`, `lvis`, `pycocoevalcap` | DETR, Deformable DETR, CenterNet, OWL-ViT, PixelLLM, DenseVOC, Streaming DVC | Detection/caption metric packages missing. | Install only the relevant metric group and verify annotation files before rerunning. |
| `ott`/Sinkhorn matcher import or version error | DETR Sinkhorn config, OWL-ViT | OTT version does not match project expectation. | Pin OTT for the selected project in an isolated environment. |
| JAX/JAXLIB/CUDA mismatch | Deformable DETR or old pinned projects | Environment pin conflict, especially CUDA wheels. | Use a dedicated legacy env or narrow to static inspection if host CUDA cannot match. |

## Checkpoint and tokenizer failures

### Common checkpoint fields

| Field | Seen in | Expected value |
|---|---|---|
| `config.init_from.checkpoint_path` | ViT, ViViT, MTV, AV-MAE finetune, UnLoc, SVViT, DETR | Existing Scenic/AugReg/big_vision-compatible checkpoint path, depending on `checkpoint_format`. |
| `config.init_from.checkpoint_format` | ViViT, MTV, PlainViT, AV-MAE, MBT, PolyViT | String such as `scenic`, `big_vision`, or project-specific variant. Must match loader. |
| `config.weights` | CenterNet, DenseVOC, Streaming DVC, PixelLLM-like configs | Existing converted/pretrained weights path for the model/backbone. |
| `dataset_configs.tokenizer_weight_path` | PixelLLM, DenseVOC, Streaming DVC | Existing BERT vocab/tokenizer or project tokenizer asset. |
| T5/T5X pretrained path | Vid2Seq and T5 PixelLLM routes | Existing T5.1.1/T5X checkpoint or configured Scenic T5 path. |

### Recovery rules

- If a config still contains a placeholder path, stop and ask for the concrete checkpoint/tokenizer path. Do not run a job expecting a placeholder to be ignored.
- If the checkpoint is from Torch/CLIP/SAM/MAE/VitDet, require a conversion plan and output path before any conversion. Do not assume Scenic can load Torch directly.
- If the checkpoint format is `big_vision`, require the big_vision package and keep `checkpoint_format` explicit. Do not relabel it as `scenic` to bypass an import error.
- If restoring a classification checkpoint into a different label count, preserve the recipe's classifier-reset or partial-restore behavior. Route parameter-tree details to `modeling-and-layers`.
- If an evaluation-only request lacks `eval_only=True` or equivalent trainer selection, hand the selected fields to `running-and-training` rather than editing blindly.

## Dataset and annotation failures

| Project family | Required data shape | Frequent missing item | Recovery |
|---|---|---|---|
| ViViT / MTV / ObjectViViT | Video datasets preprocessed for DMVR/TFDS/TFRecord-style loaders. | Kinetics/Epic/MiT/SSv2 raw videos not converted; pretrained image checkpoint missing. | Route dataset conversion to `data-pipelines`; do not start training from raw videos unless the data pipeline is ready. |
| AV-MAE / MBT | Audio/video TFRecords with waveform/spectrogram/rgb modalities. | AudioSet/VGGSound paths, modality keys, spectrogram shape assumptions. | Verify modality tuple and input signature before training. |
| Vid2Seq | Dense-caption records with captions, start/end times, ASR strings/times, and CLIP ViT-L/14 features at 1 FPS. | ASR columns, CLIP features, T5 checkpoint, caption metrics. | Stop with required column checklist; do not synthesize missing ASR/features. |
| Streaming DVC | FlexIO/dense-caption TFRecords and generated ground-truth JSON for eval. | BERT vocab for GIT route, pretrained GIT/Vid2Seq weights, ground-truth JSON. | Prepare evaluation JSON only after TFRecords and output path are confirmed. |
| DenseVOC | Visual Genome/Spoken-MiT/VidSTG/VLN TFRecords plus COCO-format eval JSONs. | Chained VidOR->VidSTG conversion, BERT tokenizer, converted CLIP/VitDet weights. | Validate all upstream datasets before running any converter. |
| PixelLLM | Localized Narratives, COCO, Visual Genome, RefCOCO/MDETR/UNINEXT, LLaVA-style sources. | Raw images or preprocessed JSONs absent; BERT vocab/T5 checkpoint missing. | Ask which subtask is needed and list only that subtask's data prerequisites. |
| OWL-ViT | Detection data and annotations for train/eval; image/text queries for inference. | LVIS/COCO annotations and checkpoint. | For no data but with checkpoint, offer inference/static config path; for LVIS eval require annotation path. |
| DETR/CenterNet/Deformable DETR | COCO or COCO-format images/annotations, possibly TFDS data dir. | Backbone weights, pycocotools, COCO annotation/image path. | Require data and weights before train/eval. |
| PointCloud | ModelNet40/S3DIS/ShapeNet point-cloud data. | Dataset not registered or not in expected format. | Route dataset format details to `data-pipelines`. |
| CLAY/layout_denoise | Generated mobile UI layout examples with object types. | CLAY/Rico-derived dataset generation not done. | Stop for generated data; do not use generic image classification data. |
| SVViT | Pileup window/coverage data and labels. | Genomics dataset absent or incompatible split. | Require data schema and label set before training. |

## Project custom registry errors

| Error | Likely cause | Recovery |
|---|---|---|
| `Unsupported trainer: vivit_trainer` outside ViViT route | Using project trainer string with common main or wrong project main. | Use the project-specific ViViT main identity or change to a central trainer supported by the selected baseline. |
| `Unsupported trainer: mtv_trainer` outside MTV route | Wrong main/config pair. | Pair MTV config with MTV main identity. |
| `Unrecognized model: densevoc` or `grit` | Wrong project main or `config.model.model_name` miskeyed. | DenseVOC expects `config.model.model_name` and DenseVOC main identity. |
| `Unrecognized model: streaming_vid2seq` | Wrong project main or model-name typo. | Streaming DVC expects model names such as `git`, `streaming_model`, `streaming_dense_model`, `streaming_vid2seq`, or `vid2seq`. |
| `KeyError` in UnLoc `MODELS` | `config.model_name` is not one of UnLoc's model registry keys. | Use `unloc_temporal_localization`, `unloc_moment_retrieval`, `unloc_action_segmentation`, or `unloc_highlight_detection`. |
| Dataset registry cannot find dataset | `config.dataset_name` belongs to project-specific imports not loaded by the selected main. | Use the project main that imports the dataset ops/builders, or route dataset registration mechanics to `data-pipelines`. |
| Missing preprocessing op in PixelLLM/Streaming DVC | Custom FlexIO op libraries were not imported by the selected main/config path. | Ensure the selected project main identity imports its `io.ops` libraries; route op implementation details to `data-pipelines`. |

## Project-owned tool guardrails

Project tools are not generic examples. They are data/checkpoint/evaluation converters with side effects. Use this decision gate before any tool run:

```text
Tool requested: <project tool identity>
Purpose: <TFRecord conversion | checkpoint conversion | metric recomputation | eval JSON generation>
Inputs present: <raw images/videos/annotations/checkpoint/predictions/tokenizer>
Output target: <directory/file, free space, overwrite policy>
Runtime: <CPU/GPU, expected hours, shard count>
Credentials/network: <not needed | dataset download | cloud bucket | private data>
Safe to run now: yes/no
If no: <exact missing prerequisites>
```

### Reference-only/excluded source tools and reasons

| Tool identity | Do not run by default because |
|---|---|
| `baselines.centernet.tools.build_coco_tfrecord` | Requires local COCO-format JSON/images and writes sharded TFRecords. |
| `densevoc.tools.build_smit_tfrecord` | Requires Spoken-MiT split/caption/video paths, decodes video, writes TFRecords. |
| `densevoc.tools.build_vg_tfrecord` | Requires Visual Genome/GRiT annotations and raw images, writes TFRecords. |
| `densevoc.tools.build_vidor_tfrecord` | Requires VidOR annotations/videos, decodes videos, writes TFRecords. |
| `densevoc.tools.build_vidstg_tfrecord` | Requires VidSTG annotations plus previously built VidOR TFRecords; chained conversion can fail late. |
| `densevoc.tools.build_vln_tfrecord` | Requires UVO/VLN annotations and image frames, writes TFRecords. |
| `densevoc.tools.convert_video_tfrecord_to_image_tfrecord` | Reads existing video TFRecords and writes image TFRecords; schema-specific. |
| `densevoc.tools.create_coco_json_from_tfrecord` | Reads DenseVOC TFRecords and writes COCO-format JSON and optional extracted images. |
| `densevoc.tools.eval_chota` | Requires ground-truth/prediction JSONs and Java runtime path; writes results. |
| `densevoc.tools.eval_densecap` | Requires dense-caption ground-truth and predictions; writes/prints metric outputs. |
| `densevoc` CLIP conversion notebook | Notebook/network/checkpoint conversion side effects; needs official CLIP weights and chosen output. |
| `pixel_llm.tools.build_ln_tfrecord` | Requires Localized Narratives and COCO paths; writes TFRecords. |
| `pixel_llm.tools.build_vg_tfrecord` | Requires Visual Genome annotations/images; writes TFRecords. |
| `pixel_llm.tools.build_mdetr_ref_tfrecord` | Requires MDETR-style RefCOCO annotations and COCO images; writes TFRecords and annotations. |
| `pixel_llm.tools.build_uninext_ref_tfrecord` | Requires UNINEXT annotations plus COCO/VG/Flickr images; writes TFRecords and annotations. |
| `pixel_llm.tools.build_llava_tfrecord` | Requires LLaVA JSON and image root; writes TFRecords and may transcode images. |
| `objectvivit.tools.add_orvit_bbox_to_tfrecord` | Rewrites video TFRecords with external object boxes; requires backups and validated box folders. |
| `objectvivit.tools.convert_videomae_checkpoint` | Converts external PyTorch checkpoint to Flax train state; writes checkpoint directory. |
| `streaming_dvc.tools.create_densecap_json_from_tfrecord` | Reads validation TFRecords and writes dense-caption ground-truth JSON. |

If the user lacks data or checkpoints, answer with the missing prerequisite list instead of attempting a run. For a safe static action, run the bundled config indexer against the checkout to inventory configs/requirements/tools without importing project code.

## Java and caption-metric issues

Vid2Seq, DenseVOC, PixelLLM, and Streaming DVC evaluators may require captioning metric assets and a Java runtime. Some project mains contain a placeholder for the Java binary path. If Java is missing or a placeholder remains:

1. Stop before evaluation.
2. Ask for the Java executable path and metric assets directory, or ask permission to install/provide them.
3. Use `eval_only=True` only after annotation JSONs, predictions/checkpoints, Java, and metric assets are present.

Do not edit source code just to hard-code a local Java path into reusable skill content. Use runtime config/environment handling in `running-and-training`.

## Compute and memory stop rules

Stop and report compute constraints when:

- DenseVOC video evaluation needs high accelerator memory and only CPU/small GPU is available.
- OWL-ViT LVIS evaluation is requested without practical GPU/TPU capacity.
- ViViT/MTV/AV-MAE full training is requested without accelerator access.
- Deformable DETR requires the legacy CUDA/JAX wheel stack that the host cannot support.
- A tool would write hundreds of GB of TFRecords/checkpoints and free space is unverified.

Offer a narrowed alternative: static config inventory, CPU import smoke, tiny synthetic config inspection, or prerequisite checklist. Do not claim a full result will be reproduced on CPU when the project recipe assumes accelerators.

## Verification anchors, not runtime prerequisites

For skill verification only, useful native anchors include baseline ViT/Mixer tests, DETR tests, Deformable DETR tests, and project tests for ViViT, MTV, OWL-ViT, or UnLoc if their optional dependencies are available. They should not be presented to end users as required before using a project.
