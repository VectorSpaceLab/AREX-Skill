# Model Zoo and SuperAnimal workflows

Use these workflows to plan pretrained DeepLabCut work before running any download-capable command.

## 1. No-training SuperAnimal video inference

Decision order:

1. Identify the target animal/view family: quadruped side view, top-view mouse, human body, FMPose3D animals, FMPose3D humans, or an experimental family.
2. Choose `model_name` and engine behavior:
   - PyTorch top-down animal inference: `model_name="hrnet_w32"` plus `detector_name="fasterrcnn_resnet50_fpn_v2"` is the most evidence-backed quadruped/top-view mouse choice.
   - TensorFlow bottom-up inference: `model_name="dlcrnet"`, no detector, and consider `scale_list`.
   - Human body: `model_name="rtmpose_x"`, `superanimal_name="superanimal_humanbody"`, and omit `detector_name` to use the default filtered torchvision person detector unless the user intentionally chooses another supported torchvision detector.
   - FMPose3D: use `model_name="fmpose3d_animals"` or `model_name="fmpose3d_humans"`.
3. Decide output behavior: `dest_folder`, `create_labeled_video`, `plot_bboxes`, and `pcutoff`.
4. Decide scale/crop/memory behavior: `cropping`, `scale_list`, `batch_size`, `detector_batch_size`, `device`, and `max_individuals`.
5. Decide whether the run may download weights. If not, require custom checkpoint paths or a confirmed pre-populated cache.

Example PyTorch animal inference:

```python
import deeplabcut

results = deeplabcut.video_inference_superanimal(
    videos=["trial_mouse_topview.mp4"],
    superanimal_name="superanimal_topviewmouse",
    model_name="hrnet_w32",
    detector_name="fasterrcnn_resnet50_fpn_v2",
    dest_folder="modelzoo_outputs",
    cropping=None,
    video_adapt=False,
    batch_size=4,
    detector_batch_size=2,
    pcutoff=0.1,
    max_individuals=1,
    device="auto",
    plot_bboxes=True,
    create_labeled_video=True,
)
```

Example TensorFlow bottom-up scale-sensitive inference:

```python
import deeplabcut

results = deeplabcut.video_inference_superanimal(
    videos=["quadruped_sideview.mp4"],
    superanimal_name="superanimal_quadruped",
    model_name="dlcrnet",
    detector_name=None,
    scale_list=[200, 300, 400],
    dest_folder="modelzoo_outputs",
    video_adapt=False,
    pcutoff=0.1,
    create_labeled_video=True,
)
```

Example human-body inference:

```python
import deeplabcut

results = deeplabcut.video_inference_superanimal(
    videos=["human_motion.mp4"],
    superanimal_name="superanimal_humanbody",
    model_name="rtmpose_x",
    detector_name=None,
    max_individuals=2,
    batch_size=4,
    detector_batch_size=2,
    device="auto",
    dest_folder="humanbody_outputs",
)
```

## 2. FMPose3D video inference

Use this only when the user wants the pretrained FMPose3D monocular video branch. For camera calibration, triangulation, stereo/multi-camera 3D, or generic 3D post-processing, route to `../postprocessing-3d-video-exports/SKILL.md`.

Animals:

```python
import deeplabcut

result = deeplabcut.video_inference_superanimal(
    videos=["quadruped_sideview.mp4"],
    superanimal_name="superanimal_quadruped",
    model_name="fmpose3d_animals",
    batch_size=8,
    max_individuals=1,
    dest_folder="fmpose_outputs",
    create_labeled_video=True,
    fmpose_return_3d=True,
)

# result["quadruped_sideview.mp4"] contains df_2d and df_3d when fmpose_return_3d=True.
```

Humans:

```python
import deeplabcut

result = deeplabcut.video_inference_superanimal(
    videos=["human_motion.mp4"],
    superanimal_name="superanimal_humanbody",
    model_name="fmpose3d_humans",
    batch_size=8,
    max_individuals=1,
    dest_folder="fmpose_outputs",
    fmpose_return_3d=True,
)
```

FMPose3D notes:

- It requires optional FMPose3D support in the environment; route installation questions to the root compatibility guidance.
- It writes 2D and 3D files. The `fmpose_return_3d` flag only changes the in-memory return payload.
- It is not a replacement for calibrated multi-camera triangulation.

## 3. Video adaptation without manual labels

Use video adaptation when zero-shot predictions are jittery, brightness/domain shift is visible, or the user explicitly wants self-supervised adaptation. It is not the same as training on manually labeled data.

Planning checklist:

1. Run on one representative video first. The implementation uses the first video for adaptation and expects similar videos to benefit.
2. Keep `create_labeled_video=True` for the first attempt unless storage is tight; visual inspection helps decide whether pseudo-label thresholds are reasonable.
3. For PyTorch top-down animal models, plan both detector and pose adaptation. For `superanimal_humanbody`, only pose adaptation is trained.
4. Start with modest epochs (`detector_epochs=4`, `pose_epochs=4`) and reduce batch sizes if memory is limited.
5. If the pseudo-label training set is empty, lower overly strict thresholds or improve crop/scale/model choice before increasing epochs.

Example:

```python
import deeplabcut

results = deeplabcut.video_inference_superanimal(
    videos=["trial_mouse_topview.mp4"],
    superanimal_name="superanimal_topviewmouse",
    model_name="hrnet_w32",
    detector_name="fasterrcnn_resnet50_fpn_v2",
    video_adapt=True,
    pseudo_threshold=0.1,
    bbox_threshold=0.9,
    detector_epochs=4,
    pose_epochs=4,
    video_adapt_batch_size=4,
    dest_folder="adapted_outputs",
    device="auto",
)
```

Expected behavior:

- A first pass creates `_before_adapt` outputs.
- Frames and pseudo annotations are prepared from the first video.
- Adapted pose and, for non-human animal models, detector checkpoints are trained or reused if already present.
- A final pass creates `_after_adapt` outputs.

## 4. Custom checkpoint inference

Use custom checkpoints when the user already has compatible SuperAnimal-style weights or wants offline inference from pre-fetched files.

```python
import deeplabcut

results = deeplabcut.video_inference_superanimal(
    videos=["trial_quadruped.mp4"],
    superanimal_name="superanimal_quadruped",
    model_name="hrnet_w32",
    detector_name="fasterrcnn_resnet50_fpn_v2",
    customized_pose_checkpoint="checkpoints/my_pose.pt",
    customized_detector_checkpoint="checkpoints/my_detector.pt",
    customized_model_config="configs/my_superanimal_pose.yaml",
    dest_folder="custom_checkpoint_outputs",
    create_labeled_video=False,
)
```

Custom checkpoint checks:

- Pose checkpoint architecture must match `model_name` or the supplied `customized_model_config`.
- Detector checkpoint must match `detector_name` and the detector section in the config.
- For human-body inference, expect the filtered torchvision detector path rather than a custom detector snapshot.
- If a custom model config switches to bottom-up behavior, do not rely on detector output.

## 5. Pretrained project creation

Use `create_pretrained_project` when the user wants a reusable DeepLabCut project initialized with pretrained weights.

PyTorch SuperAnimal project:

```python
import deeplabcut

config_path, train_config_path = deeplabcut.create_pretrained_project(
    project="pretrained-quadruped-demo",
    experimenter="researcher",
    videos=["quadruped_sideview.mp4"],
    model="superanimal_quadruped",
    engine=deeplabcut.Engine.PYTORCH,
    net_name="hrnet_w32",
    detector_name="fasterrcnn_resnet50_fpn_v2",
    working_directory="projects",
    copy_videos=False,
    analyzevideo=False,
)
```

Pretrained project notes:

- `copy_videos=False` uses symlinks when supported; use `copy_videos=True` on systems where symlinks are unavailable or undesirable.
- `analyzevideo=True` immediately runs analysis and may create labeled videos. Use `False` for project-only setup.
- PyTorch pretrained project creation downloads weights into the project model train folder and writes PyTorch config files.
- TensorFlow Model Zoo project creation is legacy. If the user asks for a TensorFlow-only Model Zoo model, route installation compatibility questions to the root guidance first.

Legacy full-human helper:

```python
import deeplabcut

deeplabcut.create_pretrained_human_project(
    project="legacy-human-demo",
    experimenter="researcher",
    videos=["human_motion.mp4"],
    working_directory="projects",
    copy_videos=False,
    analyzevideo=False,
)
```

Use the legacy helper only for the legacy TensorFlow full-human model path, not for the current `superanimal_humanbody` video inference path.

## 6. Transfer learning from SuperAnimal weights

This sub-skill owns the SuperAnimal weight-selection facts, but custom labeled dataset training belongs to `../pytorch-training-evaluation-inference/SKILL.md` after the training dataset exists.

Transfer-learning setup pattern:

```python
import deeplabcut
from deeplabcut.modelzoo import build_weight_init

config_path = "my_project/config.yaml"
superanimal_name = "superanimal_topviewmouse"
model_name = "hrnet_w32"
detector_name = "fasterrcnn_resnet50_fpn_v2"

weight_init = build_weight_init(
    cfg=config_path,
    super_animal=superanimal_name,
    model_name=model_name,
    detector_name=detector_name,
    with_decoder=False,
)

deeplabcut.create_training_dataset(
    config_path,
    weight_init=weight_init,
    net_type=model_name,
    detector_type=detector_name,
)

# Hand off actual training/evaluation to the PyTorch training sub-skill.
deeplabcut.train_network(
    config_path,
    epochs=10,
    superanimal_name=superanimal_name,
    superanimal_transfer_learning=True,
)
```

Fine-tuning with decoder weights requires a conversion table between project bodyparts and SuperAnimal bodyparts. Memory replay is available only for the decoder/fine-tuning path. The SuperAnimal human-body family is not supported by the `build_weight_init` helper for transfer learning or fine-tuning.

## 7. No-download planning script

Before running a real inference command, use the bundled script to validate arguments and print a checklist without importing DeepLabCut or downloading weights:

```bash
python scripts/plan_superanimal_inference.py \
  --video trial_mouse_topview.mp4 \
  --superanimal-name superanimal_topviewmouse \
  --model-name hrnet_w32 \
  --detector-name fasterrcnn_resnet50_fpn_v2 \
  --dest-folder modelzoo_outputs \
  --batch-size 4 \
  --detector-batch-size 2
```

The script prints planned `video_inference_superanimal` keyword arguments, warnings, errors, and a preflight checklist. It is safe for offline planning because it does not import DeepLabCut and does not fetch weights.
