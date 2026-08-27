# Data and model API for LTR training settings

Use this reference when editing or creating training settings. It summarizes the interfaces that appear in the included LTR settings without requiring a full training run.

## Entry-point API

The training entry point exposes:

```python
run_training(train_module, train_name, cudnn_benchmark=True)
```

It performs these steps:

1. Sets OpenCV thread count to zero to avoid worker/thread crashes.
2. Sets `torch.backends.cudnn.benchmark` from the argument.
3. Constructs a `Settings` object.
4. Fills `settings.module_name`, `settings.script_name`, and `settings.project_path = 'ltr/<module>/<name>'`.
5. Imports `ltr.train_settings.<module>.<name>` and calls its `run(settings)` function.

`Settings` loads `settings.env` from the local training config and defaults `settings.use_gpu=True`.

## Local environment fields

The generated local config template includes:

```text
workspace_dir
tensorboard_dir
pretrained_networks
pregenerated_masks
lasot_dir
got10k_dir
trackingnet_dir
coco_dir
lvis_dir
sbd_dir
imagenet_dir
imagenetdet_dir
ecssd_dir
hkuis_dir
msra10k_dir
davis_dir
youtubevos_dir
lasot_candidate_matching_dataset_path
```

Additional fields used by some code but not present in the default template include:

```text
imagenet_vid_gmot_dir
tao_burst_dir
davis_testdev_dir
davis16_dir
```

Add these attributes explicitly when a selected dataset constructor or train setting references them.

## Dataset constructors

Common dataset constructors and key arguments:

| Dataset class | Main purpose | Key arguments / fields |
| --- | --- | --- |
| `Lasot` | SOT video training/validation | `root`, `split`, optional `vid_ids`, `data_fraction` |
| `Got10k` | SOT video training/validation | `root`, `split`, optional `seq_ids`, `data_fraction` |
| `TrackingNet` | SOT video training | `root`, `set_ids`, optional `data_fraction` |
| `MSCOCOSeq` | COCO as sequence-like SOT data | `root`, `split`, `version`, optional `data_fraction` |
| `MSCOCOMOTSeq` | COCO in MOT-style sequence form | `root`, `split`, `version` |
| `LasotCandidateMatching` | KeepTrack candidate matching | `root`, `path_to_json`, `split` |
| `ImagenetVIDMOT` | TaMOs MOT-style ImageNet-VID | `root`, `split`, `multiobj` |
| `TAOBURST` | TaMOs TAO/BURST data | `root`, `split`, `multiobj` |
| `YouTubeVOS` | VOS/multi-object data | `root`, `version`, `split`, `multiobj`, `all_frames` |
| `Davis` | DAVIS VOS data | `root`, `version`, `split`, `multiobj` |
| `LVIS`, `SBD`, `ECSSD`, `HKUIS`, `MSRA10k` | Image/object or segmentation datasets | `root`, split/fraction/min-area options |
| `SyntheticVideo`, `SyntheticVideoBlend` | Generate video-like samples from images | Base image datasets plus transform arguments |

Dataset classes usually expose video-dataset methods used by samplers: `is_video_sequence()`, `get_num_sequences()`, `get_sequence_info(seq_id)`, `get_frames(seq_id, frame_ids, seq_info_dict)`, and `get_name()`.

## Processing classes

Processing objects crop, augment, normalize, build labels, and convert sampled frames/annotations into tensors expected by the actor.

| Processing class | Used by | Notes |
| --- | --- | --- |
| `ATOMProcessing` | ATOM | Crops train/test frames and prepares IoU-Net bounding-box regression data. |
| `KLBBregProcessing` / `ATOMwKLProcessing` | Probabilistic ATOM variants | Prepares KL/probabilistic bounding-box regression targets. |
| `DiMPProcessing` | DiMP | Prepares classifier labels plus bounding-box regression data. |
| `KLDiMPProcessing` | PrDiMP / SuperDiMP | Prepares KL regression labels for classifier and/or box outputs. |
| `KYSProcessing` | KYS | Handles longer sampled sequences and prediction inputs for KYS. |
| `LWLProcessing` | LWL | Segmentation/VOS processing with masks. |
| `RTSProcessing` | RTS | Segmentation processing with RTS classifier branch needs. |
| `TargetCandiateMatchingProcessing` | KeepTrack | Candidate-matching data; note the class name typo is present in the API. |
| `LTRBDenseRegressionProcessing` | ToMP | Dense bounding-box regression and transformer-style labels. |
| `TaMOsProcessing` | TaMOs | Multi-object/SOT/MOT processing with dense labels. |

When modifying processing, keep output keys compatible with the selected actor. For example, a segmentation actor needs mask tensors, while a dense regression actor needs dense box/classification targets.

## Samplers and loaders

Samplers are PyTorch datasets that draw sequence/frame samples; loaders batch them.

| Sampler | Used by | Key behavior |
| --- | --- | --- |
| `ATOMSampler` | ATOM | Interval frame sampling; one train frame and one or more test frames. |
| `DiMPSampler` | DiMP, PrDiMP, ToMP | Causal or interval train/test frame sampling for tracking losses. |
| `KYSSampler` | KYS | Samples longer test sequences for response prediction. |
| `LWLSampler` | LWL, RTS | Samples train/test frames with VOS masks and optional sequence reversal. |
| `SequentialTargetCandidateMatchingSampler` | KeepTrack | Reads candidate-matching JSON and sequences candidate states. |
| `TaMOsDatasetSampler` | TaMOs | Extends tracking sampling for SOT/MOT multi-object training. |

`LTRLoader` extends PyTorch `DataLoader` with a `name`, `training` flag, `epoch_interval`, and `stack_dim` option. `MultiEpochLTRLoader` repeats the batch sampler to avoid expensive worker restarts across epochs; it is used by TaMOs-style high-throughput training.

Debugging loader changes:

- Set `num_workers=0` first.
- Keep `stack_dim` aligned with actor expectations.
- Make train and validation loader names unique; TensorBoard uses loader names as subdirectories.
- Keep `epoch_interval` intentional for validation loaders that should not run every epoch.

## Model constructors

LTR models use constructor-decorated functions so checkpoints can store constructor metadata. Constructors used by the included settings include:

| Family | Constructor examples |
| --- | --- |
| ATOM | `atom_resnet18`, `atom_resnet50` |
| DiMP / PrDiMP | `dimpnet18`, `dimpnet50`, `dimpnet50_simple`, `klcedimpnet18`, `klcedimpnet50` |
| KYS | `kysnet_res50` |
| KeepTrack | `target_candidate_matching_net_resnet50` |
| LWL | `steepest_descent_resnet50` in LWL modules |
| RTS | `steepest_descent_resnet50_with_clf_encoder` |
| TaMOs | `tamosnet_resnet50`, `tamosnet_swin_base` |
| ToMP | `tompnet50`, `tompnet101` |

When replacing a model, verify actor compatibility, expected output dictionary keys, pretrained weight names, and whether the setting wraps the network in `MultiGPU(net, dim=1)`.

## Actors, objectives, and trainers

Actors call the network, compute losses, and return `(loss, stats)` to the trainer.

| Actor | Typical setting | Expected output style |
| --- | --- | --- |
| `AtomActor` | ATOM | IoU/bounding-box regression loss. |
| `AtomBBKLActor` | Probabilistic ATOM | KL/probabilistic bounding-box regression. |
| `DiMPActor` | DiMP | Classifier loss plus IoU regression. |
| `KLDiMPActor` | PrDiMP / SuperDiMP | KL regression losses. |
| `DiMPSimpleActor` | SuperDiMP simple | Hinge classifier plus box losses. |
| `KYSActor` | KYS | Prediction/classification sequence losses. |
| `TargetCandiateMatchingActor` | KeepTrack | Candidate association/matching loss. |
| `LWLActor` | LWL | Segmentation losses. |
| `LWLBoxActor` | LWL box init | Segmentation and box-initialization losses. |
| `RTSActor` | RTS | Segmentation plus classifier branch losses. |
| `ToMPActor` | ToMP | Dense GIoU and target classification losses. |
| `TaMOsActor` | TaMOs | Multi-object dense GIoU/classification losses. |

`LTRTrainer` handles device placement, train/validation cycling, optimizer steps, gradient clipping through `settings.grad_clip_max_norm`, stats printing, TensorBoard writes, checkpoint saving, and checkpoint loading. It moves data to GPU unless `settings.move_data_to_gpu=False`.

## Data specs

Text files under `ltr/data_specs` define dataset splits and class maps used by dataset constructors, including GOT-10k train/val/VOT splits, LaSOT train splits, ImageNet-VID MOT splits, TrackingNet class map, and YouTubeVOS JJ train/valid splits. If a constructor fails on a split name, verify both the local dataset root and the corresponding split file expected by that constructor.
