# Scenic project catalog and route selection

Scenic hosts both shared baselines and research projects. A project typically owns its own model files, trainer, configs, binary `main` module, local registries, dataset/input helpers, and sometimes conversion or evaluation tools. Scenic intentionally favors forked or copied research code for project-specific experiments, so similar-looking projects may have different registry names, config keys, dependency pins, and data prerequisites.

Use this reference to choose the smallest project family that matches the user's task, then hand generic command execution to `running-and-training`, dataset registry details to `data-pipelines`, and model/layer APIs to `modeling-and-layers`.

## Route selection by task family

| User task | Start here | Why | Common prerequisites and blockers |
|---|---|---|---|
| Image classification baseline | Baseline ViT, MLP-Mixer, ResNet/BiT, Axial-ResNet, PlainViT, MatViT, TokenLearner | Canonical supervised image backbones and transfer experiments. | ImageNet/TFDS or equivalent data, optional pretrained ViT/big_vision/Scenic checkpoints, batch-size/device tuning. |
| Video classification | ViViT, MTV, TokenLearner, ObjectViViT | ViViT is the canonical video transformer; MTV adds multi-view encoders and lateral/global fusion; TokenLearner reduces token count; ObjectViViT adds external object detections. | DMVR/video data preprocessing, Kinetics/Epic/Moments/SSv2-style TFRecords or TFDS, pretrained image ViT checkpoint, accelerator memory. |
| Audio/video representation learning | AV-MAE, MBT | AV-MAE pretrains masked audio/video encoders and finetunes unimodal or multimodal heads; MBT uses fusion bottlenecks for multimodal classification. | AudioSet/VGGSound or audio/video TFRecords, spectrogram/waveform/rgb modalities, optional Lingvo for MBT, pretrained/finetuned checkpoint paths. |
| Open-vocabulary image detection | OWL-ViT | Text-conditioned and image-conditioned object detection with CLIP-like backbones; OWLv2 checkpoints are drop-in replacements for v1 at the model level. | CLIP/Torch/big_vision dependencies, COCO/LVIS APIs for evaluation, large JAX or SavedModel checkpoints, LVIS/COCO annotations for evaluation. |
| Dense video captioning | Vid2Seq, Streaming DVC | Vid2Seq is the offline single-stage dense captioning route; Streaming DVC handles long videos with streaming inputs/outputs and bounded memory. | DMVR/FlexIO TFRecords, T5/T5X or GIT/ViT weights, BERT vocab for GIT routes, Java and captioning-metrics files for metric computation, ASR and CLIP features for Vid2Seq data. |
| Object-centric dense video captioning | DenseVOC | Detects, tracks, and captions object trajectories in videos. | Visual Genome/Spoken-MiT/VidSTG/VLN TFRecords, COCO-format eval JSONs, BERT tokenizer, CLIP/VitDet-style converted weights, high accelerator memory. |
| Pixel-aligned visual language | PixelLLM | Localization-capable language model for location-conditioned captioning, referring localization/segmentation, dense object captioning, and trace-like supervision. | Localized Narratives, COCO, Visual Genome, RefCOCO/MDETR/UNINEXT/LLaVA-style data, pycocotools/pycocoevalcap, T5-XL or BERT vocab/checkpoints. |
| Temporal video localization | UnLoc | Unified framework for temporal action localization, moment retrieval, highlight detection, and action segmentation. | TFRecords or table inputs, class/prompt CSVs, CLIP-like image/text checkpoints, task-specific `dataset_configs.task`. |
| Point-cloud classification/segmentation | PointCloud/PCT | Transformer-based point cloud classification, S3DIS segmentation, and ShapeNet part segmentation. | ModelNet40/S3DIS/ShapeNet data in the expected dataset builders, trainer and entrypoint matching classification vs segmentation. |
| Prompt-based segmentation | SAM baseline | Zero-shot segmentation from image prompts; supports point prompts and cached image embeddings. | Converted SAM checkpoint; official PyTorch weights must be converted outside normal training flow. |
| COCO-style object detection | DETR, Deformable DETR, CenterNet/CenterNet2 | DETR/Deformable DETR for transformer detection; CenterNet/CenterNet2 for anchor-free/object-detection baselines and VitDet/ConvNeXt variants. | COCO or COCO-format data, pycocotools, pretrained ResNet/VitDet/ConvNeXt/MAE checkpoints, potentially strict JAX/CUDA pins for Deformable DETR. |
| UI layout denoising | CLAY / layout_denoise | Transformer object typing for denoising mobile UI layouts. | CLAY/Rico-derived training data, project-specific dataset config dictionary, object typing labels. |
| Structural-variant genomics | SVViT | ViT/XViT-style models for structural variant identification/genotyping from pileup data. | Pileup window/coverage datasets, transfer checkpoints, genomics-specific labels. |

## Answers for common ambiguous requests

### "Which project should I start from for video classification?"

Choose according to the experimental goal:

1. **ViViT** for a stable pure-transformer video classification baseline with Kinetics/Epic/SSv2-style configs and pretrained image ViT initialization.
2. **MTV** when the user wants multi-view video recognition or stronger multi-view fusion with separate encoders and lateral/global connections.
3. **TokenLearner** when the project goal is speed/compute reduction through dynamic token selection in image/video transformers.
4. **AV-MAE** if the user asks for audio/video self-supervised pretraining or unimodal/multimodal finetuning from masked-autoencoder checkpoints.
5. **ObjectViViT** only when external object detector boxes are already available or are part of the method.

If the user has no video data preprocessing yet, do not promise a training run; hand the route plus DMVR/TFRecord prerequisites to `data-pipelines`.

### "Which project should I start from for open-vocabulary detection?"

Use **OWL-ViT**. It is the Scenic project for open-vocabulary object detection from text queries and one-shot/image-conditioned detection. CLIP provides image/text encoders and embedding recipes but is not, by itself, a detector. DETR, Deformable DETR, and CenterNet are supervised object detection baselines rather than open-vocabulary query detectors.

If the user has no checkpoint, pick an OWL-ViT v1/v2 config identifier and stop with checkpoint/download/storage prerequisites. If the user wants LVIS evaluation, also require LVIS annotations and COCO/LVIS evaluation packages.

### "Which project should I start from for dense video captioning?"

- Use **Vid2Seq** for offline dense video captioning from frames/features plus ASR/transcribed speech, producing a token sequence with event captions and temporal localization.
- Use **Streaming DVC** when the user cares about online/long-video latency: it streams frames one at a time and can stream outputs before seeing the full video.
- Use **DenseVOC** when captions must be tied to object trajectories with detection/tracking/captioning.

If the user lacks data/checkpoints, do not run project tools. List prerequisites: dense-caption TFRecords, captioning-metrics files, Java runtime path, tokenizer/checkpoint paths, and sufficient accelerator memory.

## Project structure pattern

Most project packages follow this pattern:

| Component | Purpose | Typical names and keys |
|---|---|---|
| Configs | Experiment parameters for model, trainer, dataset, optimizer, checkpointing, eval. | `configs/*.py` with `get_config()`, `config.model_name` or `config.model.model_name`, `config.trainer_name`, `config.dataset_name`, `config.dataset_configs`, `config.init_from`, `config.weights`, `config.eval_only`. |
| Main module | Binds config to model class, trainer, and dataset/input pipeline. | `python -m scenic.projects.<project>.main` for project-specific binaries; baselines without project-specific binaries use Scenic's common main. |
| Model registry | Maps config string to model class. | `get_model_cls(config.model_name)`, project `MODELS` dictionaries, or direct model class selection. |
| Trainer registry | Maps config trainer string to train/eval function. | Project-specific `get_trainer()`, central Scenic trainer registry, or explicit `trainer.train_and_evaluate`. |
| Dataset route | Builds a dataset object or dataset dict. | `train_utils.get_dataset`, project `input_pipeline.get_dataset`, FlexIO sources, or explicit point-cloud/layout dataset builders. |
| Tools | One-off dataset/checkpoint/evaluation converters. | Treat as reference-only until data, output, credentials, runtime, and overwrite policy are verified. |

Baseline models are the main exception: many baseline architectures are registered in Scenic's shared model registry and run through Scenic's common main, while DETR/Deformable DETR/CenterNet/BERT/PlainViT/PonderNet/Universal Transformer have their own project-like binary modules.

## Main/config/registry patterns by representative project

| Project | Entrypoint identity | Model selection | Trainer selection | Dataset/input selection | Notable config fields |
|---|---|---|---|---|---|
| ViViT | `scenic.projects.vivit.main` | `model.get_model_cls(config.model_name)` | `config.trainer_name == 'vivit_trainer'` | Common `train_utils.get_dataset` | `dataset_configs.num_frames`, `model.attention_config`, `init_from.checkpoint_path`, `init_from.checkpoint_format`. |
| MTV | `scenic.projects.mtv.main` | `model.get_model_cls(config.model_name)` | `config.trainer_name == 'mtv_trainer'` | Common `train_utils.get_dataset` | Per-view configs, multi-view checkpoint paths/formats, Kinetics/Epic/MiT/SSv2 config families. |
| OWL-ViT | `scenic.projects.owl_vit.main`; evaluator has separate module identity | Direct `TextZeroShotDetectionModel` for training | Project trainer | Common `train_utils.get_dataset` | `checkpoint`, `dataset_configs.train/eval.decoder_kwarg_list`, LVIS/COCO eval paths, OWLv1/OWLv2 config identifiers. |
| UnLoc | `scenic.projects.unloc.main` | `model.MODELS[config.model_name]` with `unloc_temporal_localization`, `unloc_moment_retrieval`, `unloc_action_segmentation`, `unloc_highlight_detection` | `single_task_trainer` | Common `train_utils.get_dataset` | `dataset_configs.task`, `base_dir`, `tables`, `class_name_csv`, `prompt_csv`, `init_from.load_from_unloc_checkpoint`. |
| Vid2Seq | `scenic.projects.vid2seq.main` | `DenseVideoCaptioningModel` | Train/eval if `num_training_epochs`; eval-only path otherwise | Project dense-video-captioning TFRecord dataset builder | `dataset_configs.num_bins`, `tmp_only`, `order`, ASR/feature columns, T5 checkpoint path. |
| AV-MAE | `scenic.projects.av_mae.main` | Project registry includes ViT/ViViT/MBT masked autoencoder and finetuning classes | `avmae_trainer`, `avmae_transfer_trainer`, multimodal variants | Common `train_utils.get_dataset` | `dataset_configs.modalities`, spectrogram/rgb settings, `init_from.checkpoint_path`, modality-specific finetuning. |
| PixelLLM | `scenic.projects.pixel_llm.main` | Direct `PixelLlmModel` | `trainer.train_and_evaluate` or evaluator when `eval_only`/`trainer == 'evaluator'` | Common `train_utils.get_dataset` with custom FlexIO ops | `dataset_configs.train/eval.sources`, tokenizer path, refer/densecap/caption configs, `model.git_backbone_name`, `model.sam_backbone_name`. |
| DenseVOC | `scenic.projects.densevoc.main` | `config.model.model_name` in `{grit, densevoc}` | Train/evaluate or eval-only | Project `input_pipeline.get_dataset` | `dataset_configs.train_data_path`, `test_data_path`, `test_annotation_path`, `tokenizer_weight_path`, `model.with_tracking`, `config.weights`. |
| Streaming DVC | `scenic.projects.streaming_dvc.main` | `config.model.model_name` in `{git, streaming_model, streaming_dense_model, streaming_vid2seq, vid2seq}` | Train/evaluate or evaluator when `eval_only`/`trainer == 'evaluator'` | Common `train_utils.get_dataset` with FlexIO/densecap ops | `dataset_configs.train/eval.sources`, `test_annotation_path`, tokenizer path, `model.streaming_method`, `model.streaming_buffer_size`, `weights`. |
| PointCloud/PCT | `scenic.projects.pointcloud.main` for classification; segmentation has separate S3DIS/ShapeNet entrypoint identities | PCT classification or segmentation model class | Central classification trainer or project segmentation trainer | Project point-cloud dataset builders | `dataset_name` in `{modelnet40, s3dis, shapenet}`, `max_seq_len`, `trainer_name`. |
| TokenLearner | `scenic.projects.token_learner.main` | `model.get_model_cls(config.model_name)` | ViViT trainer or central trainer registry | Common `train_utils.get_dataset` | `model.tokenizer.type='dynamic'`, `num_tokens`, `tokenlearner_loc`, `use_tokenfuse`, `use_v11`. |
| SVViT | `scenic.projects.svvit.main` | `vit_classification`, `xvit_classification`, `vit_xvit_classification` style names | `classification_trainer`, `transfer_trainer`, `inference`, or central trainer | Common `train_utils.get_dataset` with pileup datasets imported by main | `dataset_name` in pileup families, `init_from.checkpoint_path`, XViT attention config. |
| MatViT | `scenic.projects.matvit.main`; separate classification eval identity | Direct MatViT multi-label classification model | Project trainer | Common `train_utils.get_dataset` | Matryoshka FFN dims, `matvit_dims` for mix-and-match eval, pretrained MatViT checkpoints. |
| CLAY/layout_denoise | `scenic.projects.layout_denoise.main` | Direct `LayoutModel` | Project trainer | Project layout dataset dict built from `config.datasets` | `dataset_names`, per-dataset configs, `model_type`, object typing settings. |

## Project-owned tools inventory and safety classification

The following tool names are part of Scenic's project tree, but they are not normal runtime dependencies. Treat them as **reference-only** unless prerequisites are explicitly supplied and the user authorizes side effects.

| Tool family | Purpose | Required prerequisites | Why reference-only by default |
|---|---|---|---|
| CenterNet COCO TFRecord builder | Convert COCO-format annotations and image folders into sharded TFRecords. | Local COCO-style JSON, image directory, output path, shard count/storage budget. | Reads large image sets and writes TFRecords; wrong paths can create partial/incorrect data. |
| DenseVOC TFRecord builders | Build Spoken-MiT, Visual Genome, VidOR, VidSTG, and Video Localized Narratives TFRecords; convert video TFRecords to image TFRecords. | Raw videos/images, downloaded annotations, derived VidOR TFRecords for VidSTG, UVO/VLN assets, output shard paths. | Large data IO, video decoding, chained prerequisites, and many output files. |
| DenseVOC COCO JSON and metric tools | Create COCO-format eval JSONs and recompute CHOTA/dense-caption metrics. | Existing DenseVOC TFRecords or prediction JSON, ground-truth JSON, caption metric files, Java runtime path for some metrics. | Writes evaluation JSON/results and may fail late without Java or metric assets. |
| DenseVOC CLIP conversion notebook | Convert/download CLIP B/16 weights to JAX-compatible checkpoint. | Official CLIP checkpoint, notebook/runtime environment, target checkpoint path. | Notebook/network/checkpoint mutation workflow; not a safe unattended script. |
| PixelLLM TFRecord builders | Build Localized Narratives, Visual Genome, MDETR RefCOCO, UNINEXT RefCOCO, and LLaVA TFRecords/annotations. | Raw datasets, external preprocessed annotations, image roots, output dirs. | Reads external datasets and writes task-specific records/annotation sidecars. |
| ObjectViViT tools | Add ORViT boxes into TFRecords or convert VideoMAE PyTorch checkpoints. | Existing video TFRecords, external object-box NPZ folders, PyTorch checkpoint, output dir. | Mutates/rewrites data or checkpoints; must not run without validated inputs and backups. |
| Streaming DVC densecap JSON helper | Convert validation TFRecords into dense-caption JSON for evaluation. | Existing TFRecords, output JSON path. | Writes evaluation files and assumes the TFRecord schema used by Streaming DVC. |

When a user asks to run one of these tools but lacks the required data/checkpoint, answer with a prerequisite checklist and a safe static alternative such as `scripts/project_config_index.py`.

## Static inventory helper

Use the bundled helper when the user supplies a checkout path and you need an import-free inventory:

```bash
python sub-skills/baselines-and-projects/scripts/project_config_index.py <SCENIC_CHECKOUT> --include-tools
```

The helper only scans files under `scenic/projects`, reads config and requirement filenames, and optionally lists tool-script names. It does not import Scenic or execute project code.
