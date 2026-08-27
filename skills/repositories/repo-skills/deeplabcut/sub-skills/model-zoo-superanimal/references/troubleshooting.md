# Model Zoo and SuperAnimal troubleshooting

Use this guide when a pretrained DeepLabCut workflow fails before, during, or after `video_inference_superanimal` or `create_pretrained_project`.

## Start with a no-download preflight

Run the bundled planner first when the task is not explicitly asking to execute inference:

```bash
python scripts/plan_superanimal_inference.py \
  --video my_video.mp4 \
  --superanimal-name superanimal_quadruped \
  --model-name hrnet_w32 \
  --detector-name fasterrcnn_resnet50_fpn_v2
```

The planner catches common name, detector, crop, threshold, and batch-size mistakes without importing DeepLabCut or downloading weights.

## Import, extras, and optional dependency failures

Symptoms:

- `ModuleNotFoundError` for `dlclibrary`, TensorFlow, torchvision, or FMPose3D support.
- A TensorFlow Model Zoo model is requested in a PyTorch-only environment.
- FMPose3D model names are requested but optional FMPose3D dependencies are not installed.

Actions:

1. Route install and backend selection to the root DeepLabCut compatibility guidance. Do not install broad extras from this sub-skill without the user's environment decision.
2. Keep the workflow narrow: if the user only needs planning, use the no-download script and do not import DeepLabCut.
3. For FMPose3D, distinguish optional dependency installation from runtime inference; the video API can plan the branch, but execution needs the optional package.

## Wrong model, dataset, or detector name

Common causes:

- Confusing `superanimal_name` with `model_name`.
- Passing a combined/deprecated name where the current API expects a family name plus a separate `model_name`.
- Using PyTorch top-down animal inference without `detector_name`.
- Choosing a model/config family that exists locally but has no verified pretrained weights in the current installation.

Recovery:

- Use `superanimal_name` for the dataset family: `superanimal_quadruped`, `superanimal_topviewmouse`, or `superanimal_humanbody` for documented mainstream workflows.
- Use `model_name` for the architecture or FMPose3D branch: `hrnet_w32`, `dlcrnet`, `rtmpose_x`, `fmpose3d_animals`, or `fmpose3d_humans` as appropriate.
- For quadruped/top-view mouse PyTorch top-down inference, supply `detector_name="fasterrcnn_resnet50_fpn_v2"` unless a custom model config clearly avoids detector use.
- For `superanimal_humanbody`, try `detector_name=None` first so the default filtered person detector is used.
- Treat `superanimal_bird` as configuration-evidenced but not fully verified for no-training video inference. Confirm installed Model Zoo availability before promising a run.

## Download and cache failures

Symptoms:

- Network timeout or authentication/proxy errors while fetching model weights.
- Cache directory is unwritable or full.
- Downloaded checkpoint filename is missing after the download helper returns.
- The workflow starts downloading even though the user expected an offline run.

Recovery:

1. Ask whether downloads are allowed and whether the environment has internet access and enough storage.
2. If downloads are not allowed, require `customized_pose_checkpoint` and, for non-human top-down animal models, `customized_detector_checkpoint` or a confirmed pre-populated cache.
3. For `create_pretrained_project`, remember that PyTorch project creation downloads pose and detector weights into the new project model train folder.
4. For `video_inference_superanimal`, default pretrained weights are downloaded to the installed DeepLabCut model-zoo checkpoint cache when missing.
5. Do not delete partial user data. Retry only after the network/cache cause is fixed.

## Detector and pose checkpoint mismatch

Symptoms:

- Shape mismatch or missing keys while loading a checkpoint.
- Detector runner cannot be created.
- Top-down inference emits no detections or too few individuals.
- `customized_detector_checkpoint` appears unused for human-body inference.

Recovery:

- Ensure the pose checkpoint matches `model_name` and the supplied or default model config.
- Ensure the detector checkpoint matches `detector_name` and the detector section in the model config.
- Keep `max_individuals` high enough for the expected number of animals/humans, but not so high that memory use becomes excessive.
- For human-body inference, expect a filtered torchvision person detector; custom detector snapshots are not the normal path.
- If a custom model config declares bottom-up behavior, a detector may be absent even if a detector name was provided.

## Spatial scale, crop, and object-size failures

Symptoms:

- The animal is consistently missed in large frames.
- Predictions cluster around background or a small image region.
- Bottom-up `dlcrnet` predictions are worse than expected.
- The same crop works for one video but not for another.

Recovery:

- For bottom-up/TensorFlow-style inference, pass a practical `scale_list` such as `[200, 300, 400]`, then widen based on the approximate animal size in pixels.
- For very large quadruped videos, try scale values below the full frame size and focus near the animal's apparent size rather than the full image resolution.
- For PyTorch top-down inference, prefer a detector plus `cropping` around the relevant arena/object when the video contains clutter.
- Remember that `cropping=[x1, x2, y1, y2]` applies to every video in the same call. Use separate calls for different crops.
- If the video resolution is excessive and not needed for keypoints, route video resizing/cropping utility questions to the post-processing/video sub-skill.

## Pixel statistics and domain shift

Symptoms:

- Jittery keypoints despite detections.
- Unusual brightness, contrast, illumination, or animal color compared with the pretrained family.
- Top-view mouse or quadruped videos fail zero-shot in a visually shifted setup.

Recovery:

1. Try a crop or scale adjustment first if the animal size is wrong.
2. Use `video_adapt=True` on one representative video when size/framing is reasonable but appearance differs.
3. Keep thresholds moderate for the first adaptation attempt. A too-high `bbox_threshold` or `pseudo_threshold` can leave too few pseudo-labels.
4. Inspect `_before_adapt` and `_after_adapt` outputs before applying adapted settings broadly.

## Video adaptation failures

Symptoms:

- Adaptation returns early with no valid predictions.
- It takes much longer than expected.
- Adapted output is worse than zero-shot output.
- Multiple videos are supplied but only the first seems to drive adaptation.

Recovery:

- The adaptation workflow uses the first video as the pseudo-label source. Choose the most representative video first.
- If no valid annotations are built, lower overly strict thresholds, use a better crop, change `model_name`, or run non-adapted inference first to inspect quality.
- Reduce `video_adapt_batch_size`, `batch_size`, or `detector_batch_size` if memory is tight.
- Keep `detector_epochs` and `pose_epochs` modest unless visual inspection shows clear gains from longer adaptation.
- If adapted checkpoints already exist, the workflow may reuse them. Change epoch counts or clear only the disposable adaptation output if the user explicitly wants a rerun.

## CPU/GPU speed and memory issues

Symptoms:

- CPU inference is too slow.
- CUDA out-of-memory during detector, pose, labeled-video, or adaptation stages.
- Device string is ignored or unsupported.

Recovery:

- Use `device="auto"` for normal PyTorch behavior; use `device="cpu"` for deterministic CPU-only planning or when GPU is unavailable.
- Reduce `batch_size` first for pose OOM, then `detector_batch_size`, then `video_adapt_batch_size` for adaptation OOM.
- Disable `create_labeled_video` if the user only needs HDF5/JSON predictions.
- Use a crop to reduce frame size when the animal occupies a small arena region.
- Do not claim that a CPU import check proves GPU performance or GPU memory sufficiency.

## Output naming and missing files

Symptoms:

- Predictions are written but no labeled video appears.
- Outputs are not in the expected folder.
- Adapted outputs have unexpected suffixes.
- FMPose3D results return only 2D data.

Recovery:

- Check `dest_folder`; if omitted, outputs are written beside the first video.
- Check `create_labeled_video`; when false, only prediction files are expected.
- For adaptation, expect `_before_adapt` and `_after_adapt` suffixes.
- For FMPose3D, expect both 2D and `_3d` files. Set `fmpose_return_3d=True` only if the caller needs `df_3d` in memory.
- If the user needs filtering, trajectory plots, refined labeled videos, codec decisions, or generic video inventory, route to the post-processing/video sub-skill.

## Pretrained project creation failures

Symptoms:

- `create_pretrained_project` rejects a dataset/model/detector.
- Symlink creation fails.
- The project is created but analysis/labeled videos fail.
- The user expected a blank project but got SuperAnimal bodyparts.

Recovery:

- For PyTorch, `model` is the SuperAnimal dataset name; `net_name` and `detector_name` choose the pretrained pose and detector architectures.
- Use `copy_videos=True` when symlinks are unavailable or the project must remain portable without original video locations.
- Use `analyzevideo=False` to create only the project and pretrained config/weights.
- If the user wants a blank project or different bodyparts, route to project setup and data-labeling sub-skills instead of using pretrained project creation.

## Transfer-learning and fine-tuning mistakes

Symptoms:

- `build_weight_init` raises for human body.
- Decoder fine-tuning fails because bodyparts do not match.
- Training is requested directly from a Model Zoo planning task.

Recovery:

- `build_weight_init` does not support `superanimal_humanbody` transfer/fine-tuning.
- `with_decoder=False` is the simpler transfer-learning path when project bodyparts differ.
- `with_decoder=True` requires a conversion table from project bodyparts to SuperAnimal bodyparts; memory replay also belongs to that decoder/fine-tuning path.
- After weight initialization and training-dataset creation are planned, route actual custom training/evaluation to `../pytorch-training-evaluation-inference/SKILL.md`.
