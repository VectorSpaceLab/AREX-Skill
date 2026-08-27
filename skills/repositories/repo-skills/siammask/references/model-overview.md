# Model and Experiment Overview

## Purpose

Use this reference when choosing a SiamMask experiment family, checkpoint/config pair, or tracking/training flags.

## Experiment Families

| Family | Typical use | Model behavior | Key config signals | Backend notes |
| --- | --- | --- | --- | --- |
| SiamMask base | Train or evaluate the base mask tracker before refine training | ResNet50 feature extractor, RPN classification/regression heads, coarse mask head | `network.arch: Custom`, `hp.instance_size: 255`, anchors stride 8 with ratios `[0.33, 0.5, 1, 2, 3]` | Training is CUDA-only; inference can use CPU or CUDA. |
| SiamMask sharp/refine | Default demo and benchmark segmentation tracker; DAVIS/VOT/YouTube-VOS workflows | Base tracker plus refine module producing sharper `127x127` masks | `config_davis.json`, `config_vot.json`, and `config_vot18.json` tune `seg_thr`, `penalty_k`, `window_influence`, and `lr` for datasets | Tracking can run on CPU; VOS tuning script requires CUDA. |
| SiamRPN ResNet | Unofficial box-only SiamRPN++/ResNet baseline | ResNet50 feature extractor with RPN classification/regression, no mask/refine output | `loss.weight` has two values, not three; training dataset mix mirrors base | Training is CUDA-only; use tracking without `--mask`/`--refine`. |

## Core Runtime Objects

- `TrackerConfig` owns inference hyperparameters such as `penalty_k`, `window_influence`, `lr`, `seg_thr`, `instance_size`, `exemplar_size`, `base_size`, and anchor metadata.
- `load_config(args)` reads a JSON config, populates loss defaults, LR defaults, clip settings, and sets `args.arch` from `network.arch`.
- `load_pretrain(model, checkpoint)` strips a `module.` prefix if needed and tolerates feature-only pretraining by retrying with a `features.` prefix.
- `siamese_init(image, target_pos, target_sz, model, hp, device)` initializes template features, anchors, windowing, and state.
- `siamese_track(state, image, mask_enable, refine_enable, device)` advances tracking and optionally converts predicted masks back to image-space polygons.
- `DataSets` in the training dataset modules consumes config-provided dataset roots/JSONs, constructs positive/negative pairs, applies SiamFC-style crops/augmentation, and yields tensors for the training scripts.

## Choosing Configs and Flags

- Use a refine/sharp checkpoint with a refine-aware config and both `--mask --refine` when the task is segmentation quality on VOT/DAVIS/YouTube-VOS.
- Use `--mask` without `--refine` for the base SiamMask mask branch.
- Omit `--mask` and `--refine` for SiamRPN box-only workflows.
- VOT configs adjust tracking penalties and segmentation thresholds for reset-based VOT evaluation.
- DAVIS/YouTube-VOS configs favor segmentation masks and multi-object VOS handling.
- Training configs reference checkout-local `data/*/crop511` and JSON files; validate the data layout before launching training.

## Expected Artifacts

- Pretrained/checkpoint files end in `.pth` for SiamMask/SiamRPN and `resnet.model` for backbone initialization.
- Tracking outputs are checkout-local runtime results under a `test/<dataset>/...` or `result/<dataset>/...` tree, depending on test versus tuning.
- Training outputs are checkpoints such as `snapshot/checkpoint_e<epoch>.pth`, logs, and TensorBoard summaries in experiment-local directories.

Read the tracking, training, and data-preparation sub-skills for workflow-specific commands and validation steps.
