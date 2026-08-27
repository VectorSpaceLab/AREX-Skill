# PaddleViT model catalog

Read this reference when a request says “PaddleViT model” without naming the
standalone project. Select a family from the task and constraints, then inspect
that family's own config and model builder before changing a command.

| Task | Families and representative directories | Prefer when |
|---|---|---|
| Image classification | `ViT`, `DeiT`, `SwinTransformer`, `VOLO`, `CSwin`, `PVTv2`, `BEiT`, `Focal_Transformer`, `MobileViT`, `ViP`, `XCiT`, `PiT`, `HaloNet`, `PoolFormer`, `BoTNet`, `CvT`, `HVT`, `TopFormer`, `ConvNeXt`, `CoaT`, `ResT`, `MLP-Mixer`, `ResMLP`, `gMLP`, `FF_Only`, `RepMLP`, `CycleMLP`, `ConvMixer`, `ConvMLP`, `RepLKNet`, `MobileOne` | `classification` route; choose the named config's directory and keep its source root isolated |
| Object detection | `object_detection/DETR`, `object_detection/Swin`, `object_detection/PVTv2` | DETR query-based end-to-end boxes, or hierarchical backbone + FPN/RPN/RoI workflows |
| Semantic segmentation | `semantic_segmentation` models: SETR, UperNet, DPT, Segmenter, Trans2Seg, SegFormer, TopFormer | Pixel masks, mIoU, dataset conversion, directory demo, or dense prediction |
| Self-supervision | `self_supervised_learning/dino` | DINO teacher/student multi-crop pretraining or DINO checkpoint reasoning |
| GAN | `gan/transGAN`, `gan/Styleformer` | Image generation, generator/discriminator experiments, FID/PSNR/SSIM |
| Specialized classification | `facial_expression` Swin | ABAW/facial-expression labels and the repository's coarse/negative variants |

## Selection cautions

- A model name in a paper or checkpoint is not enough to choose a source
  directory. Confirm the matching YAML and builder; similarly named modules are
  not interchangeable.
- Classification and detection both contain Swin/PVTv2 names but use different
  configs, heads, data contracts, and entry points.
- Segmentation backbones are not classification predictors: the decoder/head,
  crop size, class count, and checkpoint type must match.
- MAE includes pretraining and fine-tuning surfaces; route ordinary supervised
  fine-tuning to classification and route masked pretraining only when the
  selected source documents support it.
- Cross-framework weight-porting scripts are optional conversion evidence, not
  a general way to load a PyTorch checkpoint into every PaddleViT family.

## Shared architecture convention

Most classification folders expose a model module, `config.py`, `datasets.py`,
loss/augmentation helpers, a single- or multi-GPU main script, YAML configs, and
shell launch examples. Detection and segmentation add task-specific dataset,
loss, matching/post-processing, and metric layers. Use the owning sub-skill for
those details instead of treating the repository as a unified library API.
