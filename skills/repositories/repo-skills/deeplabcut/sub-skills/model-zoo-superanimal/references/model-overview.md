# Model Zoo and SuperAnimal overview

This reference summarizes the pretrained-model behavior that a future agent needs without opening any source repository files.

## Main public APIs

### `deeplabcut.video_inference_superanimal`

Use this API for direct video inference from a pretrained SuperAnimal or FMPose3D model without creating a labeled training dataset first.

Signature shape:

```python
deeplabcut.video_inference_superanimal(
    videos,
    superanimal_name,
    model_name,
    detector_name=None,
    scale_list=None,
    video_extensions=None,
    dest_folder=None,
    cropping=None,
    video_adapt=False,
    plot_trajectories=False,
    batch_size=1,
    detector_batch_size=1,
    pcutoff=0.1,
    adapt_iterations=1000,
    pseudo_threshold=0.1,
    bbox_threshold=0.9,
    detector_epochs=4,
    pose_epochs=4,
    max_individuals=10,
    video_adapt_batch_size=8,
    device="auto",
    customized_pose_checkpoint=None,
    customized_detector_checkpoint=None,
    customized_model_config=None,
    plot_bboxes=True,
    create_labeled_video=True,
    fmpose_return_3d=False,
)
```

Important parameter meanings:

| Parameter | Use |
| --- | --- |
| `videos` | One video path or a list of video paths. A directory input can be filtered with `video_extensions`. |
| `superanimal_name` | Dataset/project family, such as `superanimal_quadruped`, `superanimal_topviewmouse`, `superanimal_humanbody`, or the evidenced `superanimal_bird` configuration. |
| `model_name` | Pose architecture or special model branch. `dlcrnet` routes to TensorFlow; `hrnet_w32`, `resnet_50`, `rtmpose_s`, `rtmpose_x`, and `fmpose3d_*` route to PyTorch behavior. |
| `detector_name` | Required for PyTorch top-down animal SuperAnimal inference unless a custom model config changes the method. For human body, an omitted detector uses the default filtered torchvision person detector. |
| `scale_list` | Spatial-pyramid resolutions for bottom-up/TensorFlow-style scale-sensitive inference. It is mainly useful for bottom-up `dlcrnet`; PyTorch top-down inference depends on detector/crop choices instead. |
| `dest_folder` | Folder where HDF5/JSON predictions and labeled videos are written. If omitted, outputs go beside the first video. |
| `cropping` | Shared crop `[x1, x2, y1, y2]` applied to all videos in the call. Use separate calls for videos needing different crops. |
| `video_adapt` | Runs self-supervised adaptation from pseudo-labels. It uses one representative video first, then re-runs inference with adapted checkpoints. |
| `plot_trajectories` | TensorFlow branch option for trajectory plotting after inference. For general trajectory workflows, route to post-processing. |
| `batch_size`, `detector_batch_size`, `video_adapt_batch_size` | Throughput and memory controls for pose inference, detector inference, and adaptation training. Reduce these first on CPU or when GPU memory is low. |
| `pcutoff` | Confidence cutoff for plotted keypoints and dataframe confidence decisions. |
| `adapt_iterations` | Adaptation iteration count used by the TensorFlow branch. |
| `pseudo_threshold`, `bbox_threshold` | Thresholds used to build adaptation pseudo-labels. Higher values are stricter; too-strict thresholds can leave no adaptation data. |
| `detector_epochs`, `pose_epochs` | PyTorch adaptation epoch counts for detector and pose model. Human-body adaptation trains only pose. |
| `max_individuals` | Maximum retained individuals. Top-down inference will not emit more individuals than this. FMPose3D video lifting currently behaves as a single-individual workflow. |
| `device` | PyTorch device string such as `auto`, `cpu`, `cuda:0`, or another supported backend device. |
| `customized_pose_checkpoint` | Optional pose checkpoint path replacing the default downloaded pose weights. |
| `customized_detector_checkpoint` | Optional detector checkpoint path replacing the default detector weights for non-human PyTorch animal models. Human-body inference uses a filtered torchvision person detector. |
| `customized_model_config` | Optional PyTorch model config for custom SuperAnimal-like inference. This determines top-down vs bottom-up behavior. |
| `plot_bboxes` | For top-down labeled videos, controls whether detector boxes are drawn. |
| `create_labeled_video` | If false, keep prediction outputs but skip labeled video rendering. |
| `fmpose_return_3d` | For `model_name` starting with `fmpose3d`, include the in-memory 3D dataframe in the returned payload in addition to written files. |

### `deeplabcut.create_pretrained_project`

Use this API when the user wants a DeepLabCut project initialized with Model Zoo weights.

Signature shape:

```python
deeplabcut.create_pretrained_project(
    project,
    experimenter,
    videos,
    model=None,
    working_directory=None,
    copy_videos=False,
    video_extensions=None,
    analyzevideo=True,
    filtered=True,
    createlabeledvideo=True,
    trainFraction=None,
    engine=deeplabcut.Engine.PYTORCH,
    multi_animal=False,
    individuals=None,
    net_name=None,
    detector_name=None,
)
```

Key behavior:

- With the PyTorch engine, `model` is treated as the SuperAnimal dataset name. If omitted, the default dataset is `superanimal_quadruped`.
- With the PyTorch engine, `net_name` defaults to `hrnet_w32` and `detector_name` defaults to `fasterrcnn_resnet50_fpn_v2`.
- The function creates a project, copies or symlinks videos according to `copy_videos`, writes SuperAnimal bodyparts/skeleton into `config.yaml`, prepares train/test model folders, downloads pretrained pose and detector weights, writes PyTorch train/test config files, and optionally analyzes/videos and creates labeled videos.
- Set `analyzevideo=False` when you only want the project and downloaded weights/config files, not immediate inference.
- For TensorFlow Model Zoo models, use `engine=deeplabcut.Engine.TF` and a TensorFlow Model Zoo model name; this path is legacy and may require TensorFlow-compatible installation choices.

### `deeplabcut.create_pretrained_human_project`

This is a legacy helper for the TensorFlow `full_human` model. It forwards to `create_pretrained_project(..., model="full_human", engine=deeplabcut.Engine.TF, ...)`. Use it only when the user explicitly asks for the legacy full-human project helper. For current SuperAnimal human-body video inference, prefer `video_inference_superanimal(..., superanimal_name="superanimal_humanbody", model_name="rtmpose_x", ...)`.

## Engine and model routing

- `model_name="dlcrnet"` routes to the TensorFlow bottom-up branch. It can use `scale_list`; it does not use a PyTorch detector runner.
- Other standard model names route to PyTorch. Top-down PyTorch animal models need a detector name, typically `fasterrcnn_resnet50_fpn_v2` for quadruped and top-view mouse workflows.
- `superanimal_humanbody` is PyTorch top-down with a filtered torchvision person detector. If `detector_name` is omitted, the default detector is `fasterrcnn_mobilenet_v3_large_fpn`. Other torchvision Faster R-CNN names may be accepted depending on the installed torchvision version and DeepLabCut build.
- `model_name="fmpose3d_animals"` and `model_name="fmpose3d_humans"` route to the FMPose3D video branch. Model selection is driven by `model_name`; use `superanimal_name="superanimal_quadruped"` for animals and `superanimal_name="superanimal_humanbody"` for humans to keep naming consistent.

## SuperAnimal families evidenced in this repo skill

| `superanimal_name` | Main use | Evidenced bodyparts | Notes |
| --- | --- | ---: | --- |
| `superanimal_quadruped` | Side/orthogonal-view quadrupeds such as horses, dogs, sheep, rodents, and elephants. | 39 | Documented for `hrnet_w32` PyTorch top-down with detector and `dlcrnet` TensorFlow bottom-up. FMPose3D animals uses this family name for consistency. |
| `superanimal_topviewmouse` | Top-view lab mouse videos in freely moving assays. | 27 | Documented for `hrnet_w32` PyTorch top-down with detector and `dlcrnet` TensorFlow bottom-up. |
| `superanimal_humanbody` | Human-body pose with COCO-style body parts. | 17 | Documented for `rtmpose_x` PyTorch top-down with a filtered person detector. Weight initialization/transfer learning from this family is not supported by the SuperAnimal `build_weight_init` helper. |
| `superanimal_bird` | Bird anatomy configuration. | 42 | Project configuration and colormap evidence exist, but the no-training video-inference weight/model combination was not verified in the inspected evidence. Treat as experimental: confirm installed Model Zoo availability before promising a run. |

Representative bodypart counts matter for transfer and custom configs. If a user wants to train on a custom labeled dataset with fewer or renamed keypoints, plan a conversion table or transfer-learning setup, then route the training work to the PyTorch training sub-skill.

## Outputs and side effects

- Standard SuperAnimal video inference writes prediction dataframes (`.h5`) and JSON predictions, and it writes a labeled `.mp4` unless `create_labeled_video=False`.
- With PyTorch video adaptation, an initial `_before_adapt` inference is produced, a pseudo-label dataset is created from the first video, adapted checkpoints are written under that pseudo dataset, and a final `_after_adapt` inference is produced.
- FMPose3D video inference writes 2D prediction `.h5`/`.json` outputs and 3D `_3d.h5`/`_3d.json` outputs. With `fmpose_return_3d=True`, the return payload includes both `df_2d` and `df_3d` for each video.
- Model weights are downloaded automatically when needed. Plan for internet access, sufficient cache space, and a writable installed-package cache location unless all custom checkpoints are already supplied.
- SuperAnimal models are provided for research/non-commercial use; remind users to check their use case before deployment.
