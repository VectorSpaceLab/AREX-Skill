# Pose troubleshooting

Use [SKILL.md](../SKILL.md) as the entry point and run the no-download
[readiness checker](../scripts/check_pose_readiness.py) before attempting any
optional detector workflow. For API fields and output interpretation, see
[api-reference.md](api-reference.md); for command flow, see
[workflows.md](workflows.md).

## Optional detector gate fails

If `--require-detector` reports missing `mmdet.apis`, missing `mmcv._ext`, or
missing CUDA, stop. The current prepared environment has working torch CUDA
core but excludes full MMCV/MMDetection ops; `mmcv-full==1.7.2` source
compilation failed at missing `thrust/complex.h`. Do not substitute an
ST-GCN success for detector verification. Install a version-matched detector
stack in an isolated environment, or remain on the core/data/recognition
routes. The checker is diagnostic and does not repair the environment.

## Version or config mismatch

These configs belong to an older OpenMMLab stack. Pair Cascade-RCNN with its
Cascade-RCNN checkpoint, or HTC with its HTC checkpoint, and pair either with
the HRNet config/checkpoint expected by the estimator. Current MMDetection may
not accept legacy fields or may require a matching MMCV release. A model
configuration alone is not a checkpoint and an `mmskeleton://` alias is not a
local artifact.

## Checkpoint cannot load

A checkpoint alias may require network access and remote artifact resolution.
Prefer a verified local checkpoint path in a controlled environment. Check
that the checkpoint architecture matches the config and that the file is
readable before investigating model code. Do not place downloaded weights in
this skill tree, and do not claim that a successful alias lookup verifies
compiled detector ops.

## Image API errors

Confirm both config sections are supplied to `init_pose_estimator` and that
`detection_cfg.bbox_thre`, `estimation_cfg.data_cfg.image_size`,
`pixel_std`, `image_mean`, and `image_std` are present. Keep the input image in
the format expected by the detector; the package's pose preprocessing changes
channel order for HRNet. A result with `has_return: false` is a valid no-person
case: `joint_preds`, `joint_scores`, and `meta` are `None`, and
`person_bbox` is empty. It is not evidence of successful pose quality.

The estimator's flip augmentation path uses CUDA tensors. If a CPU-only
attempt fails there, use the documented GPU-compatible path or inspect the
implementation in an environment that matches its assumptions; do not claim
CPU image inference is supported just because initialization accepted
`device=None`.

## No boxes or unexpected output

The detector filter keeps only class-0 person boxes with score at least
`bbox_thre`. Lowering a threshold changes recall and output volume; it does not
repair detector incompatibility. Inspect `person_bbox` scores and
`has_return` before interpreting keypoints. Keypoints are per detected person,
not a persistent track. The dataset builder assigns a frame-local `id` and
leaves `person_id` null.

## Video demo fails

Check that MMFlow/MMCV/OpenCV video decoding can read the input, that output
paths are writable, and that `gpus * worker_per_gpu` does not exceed available
memory. Start with one GPU and one worker. A demo may process frames but fail
while writing a codec; separate input decoding from output encoding when
isolating the issue. Do not run a video workflow as a readiness test.

`pose_demo` uses Cascade-RCNN + HRNet; `pose_demo_HD` uses HTC + HRNet. They
are different detector configurations, not merely a quality flag. Confirm the
matching detector checkpoint for the selected command.

## Dataset builder and tracker

The builder caches checkpoints, launches workers, reads each video up to
`video_max_length`, and writes JSON records. It explicitly raises
`NotImplementedError` when `tracker_cfg` is non-null. Set it to `null`; there
is no supported tracker implementation in this path. Missing detections are
skipped, and a category not present in the annotation mapping receives
`category_id: -1`.

Before recognition, send every JSON file to `data-preparation` for strict
validation. Check `info.num_keypoints`, the `[x, y, score]` channel declaration,
frame indices, annotation keypoint lengths, resolution, and category mapping.
Then route validated data to `recognition` to choose a graph/layout and model.
Do not use this sub-skill to hand-edit malformed JSON or to claim that raw
video is directly consumable by ST-GCN.

## Handoff difficult cases

- **Optional-boundary:** if torch CUDA and ST-GCN are healthy but `mmcv._ext`
  is unavailable, keep the pose route unresolved and explicitly route the user
to dependency preparation; never report detector readiness.
- **Pose-output-handoff:** if output contains sparse frames, frame-local person
  IDs, inconsistent keypoint lengths, or an unsupported joint layout, route it
to `data-preparation` and stop before choosing a recognition graph. Recognition
  begins only after validation establishes the data contract.
