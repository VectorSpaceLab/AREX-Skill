# Data layouts and presets

Reference scripts expect prepared datasets. They do not create full datasets for you, and most official training recipes assume local high-throughput storage and GPUs.

## Classification and quantization

- Dataset: ImageNet-style classification root.
- Common layout: `<root>/train/<class_name>/*` and `<root>/val/<class_name>/*`, compatible with folder-per-class image loading.
- Quantization: post-training quantization still needs representative calibration batches; QAT needs training data.
- Presets: classification presets include crop size, resize size, interpolation, auto-augment, random erase, mixup/cutmix, repeated augmentation, and optional v2 transforms.
- Weight-specific preprocessing: when evaluating a weight enum, use the enum's transforms and metadata rather than hard-coding crop/resize unless reproducing a documented reference command.

## Detection

- Dataset: COCO-style detection or keypoint data.
- Expected pieces: image directories plus annotation JSON files for instances or keypoints.
- Common placeholders: `<coco-root>/train2017`, `<coco-root>/val2017`, and `<coco-root>/annotations/instances_train2017.json` / `instances_val2017.json`; keypoint tasks use person keypoint annotations.
- Dependencies: COCO evaluation typically requires `pycocotools`; plotting/debug paths may need `matplotlib`.
- Presets: detection presets cover horizontal flip, large-scale jittering, multiscale behavior, SSD/SSDLite augmentation, copy-paste augmentation, and optional v2 transforms.

## Segmentation

- Dataset: COCO-style segmentation data with masks/annotations.
- Expected pieces: image roots and segmentation-capable annotations; the exact labels and mask conversion must match the script's dataset adapter.
- Presets: segmentation training commonly uses random resize/crop, horizontal flip, normalization, optional v2 transforms, and `--aux-loss` for models with auxiliary heads.

## Video classification

- Dataset: Kinetics-style action classification data.
- Common layout: train and validation video folders under one root, usually grouped by class label.
- Storage warning: Kinetics-scale datasets are hundreds of GB and require video decode throughput.
- Presets: reference video transforms include dtype conversion, resize, random horizontal flip, normalization, crop, and layout conversion from batched video frames to channel-first clip tensors.
- Key shape knobs: `--clip-len`, `--frame-rate`, `--clips-per-video`, train/validation resize sizes, and crop sizes.

## Optical flow

- Datasets: FlyingChairs, FlyingThings3D, Sintel, and KITTI are common reference names.
- Root expectation: `--dataset-root` points to a directory containing the selected dataset families in the layout expected by TorchVision dataset adapters.
- Training stages: RAFT large is commonly trained on Chairs first and resumed/fine-tuned on Things.
- Presets: optical-flow transforms handle paired images and flow fields; crop/resize and batch size interact with GPU memory.

## Similarity learning

- Default style: FashionMNIST-like supervised labels are used to form triplets.
- Batch layout: `--labels-per-batch` times `--samples-per-label` defines the effective training batch and must provide multiple samples per class.
- Checkpoint flow: use `--resume` for evaluation or continuation and `--save-dir` for outputs.

## Stereo depth

- Datasets: CREStereo, ETH3D, Middlebury2014, InStereo2k, FallingThings, Carla, Sintel, and SceneFlow variants appear in reference recipes.
- Multi-dataset training: `--train-datasets` and `--dataset-steps` must align in length and sampling intent.
- Shape sensitivity: crop size, resize size, scale range, maximum disparity, aspect ratio, and disparity scale strongly affect results.
- Fragility warning: some stereo reference material depends on prototype-era components that are not guaranteed in current stable packages.

## Distributed and environment notes

- `torchrun --nproc_per_node=<gpus>` launches one process per GPU; set it to available local GPUs, not the value copied from a paper recipe.
- Multi-node launches require rendezvous configuration, network connectivity, and consistent data paths on all nodes.
- `--world-size` and `--dist-url` flags are script-level distributed knobs; do not invent values without knowing the cluster setup.
- `--sync-bn` and `--amp` assume compatible GPU training; CPU-only environments should avoid them.
- `--cache-dataset` can increase disk or memory pressure; verify capacity before enabling.
