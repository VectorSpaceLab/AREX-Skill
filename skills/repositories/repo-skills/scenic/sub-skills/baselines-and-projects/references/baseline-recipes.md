# Baseline recipes and safe config adaptation

Use this reference when the user asks for a Scenic baseline, a starting config, or how to adapt a baseline safely. It is intentionally focused on route selection and config fields; send generic launch/restart/distributed-training mechanics to `running-and-training`.

## Safe baseline adaptation checklist

Before editing or overriding any baseline config, identify these fields:

```text
config.model_name or config.model.model_name
config.trainer_name
config.dataset_name
config.dataset_configs.*
config.batch_size
config.num_training_epochs or config.total_steps
config.init_from.* or config.weights
config.checkpoint / config.checkpoint_steps
config.rng_seed
config.model_dtype_str
```

Then apply these rules:

1. **Change only one axis at a time**: dataset, model size, checkpoint, resolution, or optimizer schedule. Changing all at once makes registry and shape errors difficult to diagnose.
2. **Keep data semantics consistent**: classification configs expect labels; detection configs expect boxes/classes; dense-caption configs expect temporal segments/captions; SAM prompt inference expects images plus prompts, not detection labels.
3. **Match checkpoint format to loader**: Scenic checkpoints, AugReg `.npz`, big_vision checkpoints, Torch/CLIP checkpoints, and converted SAM/MAE/VitDet checkpoints are not interchangeable.
4. **Scale batch and learning rate together only when the trainer recipe says to**. Detection and dense-video projects often have per-device memory assumptions; do not blindly scale up.
5. **Verify registry strings before training**: unsupported model/trainer names fail before useful computation. If a registry error appears, compare the selected recipe's expected `model_name`, `model.model_name`, and `trainer_name`.
6. **Keep tool-generated data immutable** after conversion: if a TFRecord or JSON conversion was produced for an experiment, record the source raw data version and command options outside the runtime skill tree.

## Image classification and representation baselines

| Baseline | Use when | Entrypoint/config identity | Key knobs | Prerequisites |
|---|---|---|---|---|
| ViT | Canonical transformer image classification or transfer baseline. | Common Scenic main with config strings such as `scenic/projects/baselines/configs/imagenet/imagenet_vit_config.py` or `scenic/projects/baselines/configs/imagenet/imagenet_augreg_vit_config.py`. | `config.model_name`, `config.model.patches.size`, `hidden_size`, `num_layers`, `num_heads`, `classifier`, `init_from.checkpoint_path`, `init_from.checkpoint_format`. | ImageNet/TFDS-style data, optional Scenic/AugReg/big_vision checkpoint. |
| MLP-Mixer | All-MLP image baseline. | Common Scenic main with `scenic/projects/baselines/configs/imagenet/imagenet_augreg_mixer_config.py`. | Patch size, mixer hidden dims, dropout/stochastic depth, augmentation and optimizer schedule. | ImageNet/TFDS-style data; no detection/segmentation labels. |
| ResNet / BiT ResNet | Convolutional supervised image baseline and transfer starting point. | Common Scenic main with `imagenet_resnet_config.py`, `imagenet_resnet_randaug_config.py`, or `imagenet_bit_resnet_config.py` config identifiers. | Depth/width variant, data augmentation, `model_name`, optimizer schedule, optional pretrained checkpoint. | ImageNet/TFDS-style data; BiT checkpoints are separate from ordinary ResNet checkpoints. |
| Axial-ResNet | Image classification baseline with axial attention ideas. | Common Scenic main with `imagenet_axial_resnet_config.py`. | Axial attention/resolution settings, batch size, optimizer schedule. | ImageNet/TFDS-style data and compatible JAX/Flax environment. |
| TokenLearner | Add dynamic token reduction to image/video transformer experiments. | `scenic.projects.token_learner.main` with `scenic/projects/token_learner/configs/im1k_token_learner_config.py`. | `config.model.tokenizer.type='dynamic'`, `num_tokens`, `tokenlearner_loc`, `use_tokenfuse`, `use_v11`, `trainer_name`. | ImageNet-style data; choose ViViT trainer only for video-style configs. |
| MatViT | Nested/elastic FFN dimensions for deployment trade-offs. | `scenic.projects.matvit.main` with `scenic/projects/matvit/configs/imagenet_augreg_matvit_config.py`; classification eval identity accepts `matvit_dims`. | Nested FFN dimensions, model size, `matvit_dims` sequence for eval, checkpoint path. | ImageNet/TFDS-style data and MatViT checkpoint for eval. |
| PlainViT | Lightweight transfer/VTAB-style baseline forked from big_vision ideas. | `scenic.projects.baselines.plainvit.main` with PlainViT transfer/VTAB config identifiers. | `init_from.checkpoint_format='big_vision'`, transfer dataset, classifier reset. | big_vision-compatible checkpoint and target dataset. |

Example handoff after choosing ViT:

```text
Selected baseline: ViT image classification
Entrypoint module: scenic.main
Config identifier: scenic/projects/baselines/configs/imagenet/imagenet_augreg_vit_config.py
Required edits/overrides: dataset name/splits, batch size, workdir, optional init_from.checkpoint_path and checkpoint_format
Next skill: running-and-training for launch mechanics; data-pipelines if the dataset is not already available
```

## Detection and segmentation baselines

| Baseline | Use when | Entrypoint/config identity | Key knobs | Prerequisites and caveats |
|---|---|---|---|---|
| DETR | End-to-end object detection with bipartite matching. | `scenic.projects.baselines.detr.main`; `detr_config.py` for Hungarian matching, `detr_sinkhorn_config.py` for Sinkhorn/OTT matching. | `config.dataset_name='coco_detr_detection'`, `config.model_name='detr'`, `trainer_name='detr_trainer'`, `dataset_configs.max_boxes`, `init_from.checkpoint_path`. | COCO data, pycocotools, pretrained ResNet50 backbone. Sinkhorn requires OTT. |
| Deformable DETR | Faster/multiscale transformer detection with deformable attention and iterative box refinement. | `scenic.projects.baselines.deformable_detr.main`; `coco_config.py`, `mini_config.py`, or cloud-oriented config identity. | `config.model_name`, `dataset_configs`, batch size override, eval-only flag, ResNet50 checkpoint. | This project has strict old JAX/JAXLIB/Flax/CUDA pins in its requirements; isolate its environment. It implements iterative refinement but not the two-stage paradigm. |
| CenterNet / CenterNet2 | Anchor-free object detection and VitDet/ConvNeXt detector baselines. | `scenic.projects.baselines.centernet.main`; configs such as `centernet2_CXT_LSJ_4x.py`, `centernet2_ViTDetB_LSJ_4x.py`, or Objects365/VitDet variants. | `config.model.model_name`, `backbone_name`, `weights`, `dataset_configs.max_boxes`, crop size, score/NMS thresholds. | pycocotools, COCO/COCO-format data, converted ConvNeXt/MAE/VitDet checkpoint if required. Multi-device defaults often need downscaling. |
| OWL-ViT | Open-vocabulary, text-conditioned, and one-shot detection. | `scenic.projects.owl_vit.main` for training/fine-tuning; evaluator identity for LVIS/COCO evaluation. Config identities include CLIP B/32, B/16, L/14, mask-head, and OWLv2 variants. | `checkpoint`, `dataset_configs.train/eval.decoder_kwarg_list`, LVIS/COCO annotation paths, prompt/query settings, checkpoint path. | Torch/CLIP, big_vision, COCO/LVIS APIs, large checkpoints; LVIS evaluation is separate and slower than the training loop. |
| SAM | Prompt-based zero-shot segmentation. | Inference-style use through SAM model/demo utilities, not a normal training config route. | `model_size`, `input_size`, point/box prompts, cached image embeddings, converted checkpoint path. | Official PyTorch weights must be converted to JAX first. Treat conversion notebooks as reference-only, not unattended tools. |
| UNet | Semantic segmentation baseline. | Common Scenic model registry and segmentation configs when available. | `dataset_name`, segmentation trainer, crop/resize and class-count settings. | Segmentation masks and preprocessing must match the dataset pipeline. |

DETR-style example handoff:

```text
Selected baseline: DETR for COCO-style object detection
Entrypoint module: scenic.projects.baselines.detr.main
Config identifier: scenic/projects/baselines/detr/configs/detr_config.py
Required edits/overrides: ResNet50 init_from.checkpoint_path, dataset location/TFDS data dir if non-default, workdir
Dependencies: pycocotools; ott-jax only if using Sinkhorn config
```

## Language and vision-language baselines

| Baseline/project | Use when | Entrypoint/config identity | Key knobs | Prerequisites |
|---|---|---|---|---|
| CLIP baseline | Image/text embedding baseline, CLIP checkpoint conversion/loading, or tokenizer behavior. | Import-level recipe via `scenic.projects.baselines.clip`; not a from-scratch training route. | `model_name` such as ResNet or ViT CLIP variants, `IMAGE_RESOLUTION`, `IMAGE_MEAN`, `IMAGE_STD`, max text length 77. | Torch and OpenAI CLIP dependency for official checkpoint loading/conversion; converted `.npy` for JAX use. |
| BERT baseline | BERT pretraining or GLUE finetuning/few-shot evaluation in Scenic. | `scenic.projects.baselines.bert.main` with `bert_pretraining_config.py` or task configs if added. | Vocabulary path, TFRecord input paths, `max_seq_length`, masked-LM parameters, GLUE task metadata. | Official-format BERT TFRecords; external preprocessing scripts are not bundled here. |
| PixelLLM | Pixel-aligned LLM localization and dense object captioning. | `scenic.projects.pixel_llm.main` with BERT or T5 config families. | `dataset_configs.train/eval.sources`, `tokenizer_weight_path`, `model.git_backbone_name`, `model.sam_backbone_name`, box/mask/text decoder keys. | COCO/LN/VG/RefCOCO/LLaVA/MDETR/UNINEXT data, pycocotools/pycocoevalcap, BERT vocab or T5-XL checkpoint. |
| Vid2Seq / Streaming Vid2Seq | Dense video captioning with T5-style decoder. | Vid2Seq or Streaming DVC main modules with dense-caption config identities. | `num_bins`, `tmp_only`, `order`, `max_caption_length`, T5 pretrained config, `weights`. | T5/T5X, DMVR/FlexIO data, ASR/CLIP features, Java/caption metrics for evaluation. |

CLIP inference recipe facts:

```python
# Distilled API shape; route code-level details to modeling-and-layers.
model = clip.MODELS[model_name]()
vars = clip.load_model_vars(model_name)
model_bound = model.bind(vars)
text_tokens = tokenizer("a photo of a cat")
image = clip.normalize_image(image_array)  # native image resolution depends on model_name
encoded_image, encoded_text = model_bound(image, text_tokens)
```

CLIP constraints to preserve:

- Images are normalized with CLIP image mean/std and run at the model's native resolution unless the model code explicitly supports another size.
- Maximum text length is 77 tokens.
- New official checkpoints must be converted from Torch state dicts before JAX loading.
- Current Scenic CLIP baseline is not a from-scratch training recipe.

## Video and audio/video baselines

| Baseline/project | Use when | Entrypoint/config identity | Key knobs | Prerequisites |
|---|---|---|---|---|
| ViViT | Pure-transformer video classification. | `scenic.projects.vivit.main`; Kinetics400/600, Epic Kitchens, and Something-Something config families. | `model_name`, `trainer_name='vivit_trainer'`, `dataset_configs.num_frames`, temporal/spatial view eval, pretrained image ViT checkpoint. | DMVR, video data preprocessing, image ViT checkpoint, accelerator memory. |
| MTV | Multi-view transformer video classification. | `scenic.projects.mtv.main`; Kinetics, Epic, MiT, SSv2 MTV config families. | Per-view encoders, cross-view attention, lateral/global fusion, `init_from` checkpoint formats. | DMVR, pretrained image ViT checkpoints, multiple view settings. |
| AV-MAE | Self-supervised audio/video masked autoencoder and transfer finetuning. | `scenic.projects.av_mae.main`; AudioSet/VGGSound/Imagenet pretrain and finetune config identities. | `model_name` in AV-MAE registry, modalities tuple, spectrogram/rgb input signatures, `init_from.checkpoint_path`, trainer variant. | Audio/video TFRecords, waveform/rgb preprocessing, modality-compatible checkpoint. |
| MBT | Audio/video fusion bottleneck classification. | MBT project main/config identities. | Bottleneck/fusion layer placement, modality configs, `checkpoint_format` including big_vision in some paths. | DMVR and Lingvo; isolate if Lingvo conflicts with modern packages. |
| ObjectViViT | Action recognition with external object detections. | ObjectViViT main/config identities. | Object-box sampling/fusion settings, SSV2 configs, VideoMAE conversion if used. | Video data plus external object detector boxes; conversion tools are side-effectful. |

## Dense captioning and localization recipes

| Project | Use when | Entrypoint/config identity | Key knobs | Prerequisites |
|---|---|---|---|---|
| Vid2Seq | Offline dense event captioning from video plus ASR/features. | `scenic.projects.vid2seq.main`; ActivityNet-Captions, YouCook2, YT-Temporal config identities. | `dataset_configs.num_bins`, `tmp_only`, `order`, T5 decoder settings, `num_training_epochs`, pretrained T5 path. | Flax 0.5 compatibility expectation, T5/T5X, DMVR, ASR columns, CLIP ViT-L/14 features at 1 FPS, caption metrics/Java for eval. |
| Streaming DVC | Long-video dense captioning with streaming input/output. | `scenic.projects.streaming_dvc.main`; GIT and Vid2Seq streaming configs for ActivityNet, YouCook2, ViTT. | `model.streaming_method`, `streaming_buffer_size`, `weights`, tokenizer path, `eval_only`. | DMVR/FlexIO, pycocoevalcap, T5/T5X for Vid2Seq routes, BERT vocab for GIT routes, pretrained GIT/Vid2Seq weights. |
| DenseVOC | Object trajectory detection/tracking/captioning. | `scenic.projects.densevoc.main`; disjoint pretraining, VidSTG, VLN, GRiT/VG config identities. | `dataset_configs.max_frames_train/test`, `train_data_path`, `test_annotation_path`, `model.with_tracking`, `caption_with_track`, `weights`, `eval_only`. | pycocotools/pycocoevalcap, BERT tokenizer, Visual Genome/Spoken-MiT/VidSTG/VLN TFRecords, COCO-format eval JSONs, converted CLIP/VitDet weights. |
| UnLoc | Temporal action localization, moment retrieval, highlight detection, action segmentation. | `scenic.projects.unloc.main`; ActivityNet, ActivityNet-Captions, Charades-STA, COIN, QVHighlights config families. | `dataset_configs.task`, `modality_configs`, feature pyramid settings, `class_name_csv`, `prompt_csv`, `init_from.load_from_unloc_checkpoint`. | Task-specific table inputs and labels, CLIP image/text checkpoints, class/prompt metadata. |

## Less-common project recipes

| Project | Use when | Key facts |
|---|---|---|
| PointCloud/PCT | Point-cloud classification or segmentation. | Classification uses ModelNet40-style data; segmentation uses S3DIS or ShapeNet-style data and separate segmentation entrypoint identities. Configs include `max_seq_len`, `dataset_name`, and `trainer_name`. |
| CLAY/layout_denoise | Mobile UI layout object typing/denoising. | Config builds a dictionary of datasets from `config.dataset_names`; requires CLAY/Rico-style generated data before training. |
| SVViT | Structural variant identification/genotyping. | Configs distinguish pileup coverage vs pileup window data and ViT vs XViT classifiers; transfer configs require `init_from.checkpoint_path`. |
| Universal Transformer / PonderNet | Sequence modeling with adaptive computation. | Use only when the user's task is explicitly sequence/adaptive-computation experimentation rather than image/video modeling. |
| Boundary Attention | Boundary detection in noisy images. | Has extra geometry/media dependencies and Kaleidoshapes data generation; not a generic segmentation baseline. |

## Validation anchors, not user runtime dependencies

For final skill verification or content QA, useful native anchors include baseline ViT and Mixer tests, DETR tests, Deformable DETR tests, and project tests for ViViT, MTV, OWL-ViT, or UnLoc if their optional dependencies are installed. These anchors are not prerequisites for a user's training or inference task.
