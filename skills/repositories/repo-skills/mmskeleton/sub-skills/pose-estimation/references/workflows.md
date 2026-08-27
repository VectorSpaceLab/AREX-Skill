# Pose workflows

Start at [SKILL.md](../SKILL.md), run the optional gate described in
[compatibility.md](compatibility.md), and use [api-reference.md](api-reference.md)
for result fields. These workflows are documented recipes only; do not treat
them as runtime-verified in the current environment.

## Image or frame inference

For a Python caller with an image/frame, load the API configuration, initialize
with `init_pose_estimator`, and call `inference_pose_estimator` once per image.
The returned dictionary contains detector boxes and HRNet keypoints; callers
choose how to render or serialize it. This is distinct from a video demo: the
image API gives one result at a time and does not read, sort, or write a video.
Its configuration still requires both a detector and a pose estimator.

Before use, confirm that the detector config, HRNet config, local checkpoint
files or supported aliases, `mmdet.apis`, MMCV custom ops, CUDA, and the native
pose NMS path are available. The bundled checker is a no-download import and
capability report, not a substitute for inference.

## Video demo

The standard demo is the config-driven command:

```text
mmskl pose_demo --video VIDEO --gpus N
mmskl pose_demo_HD --video VIDEO --gpus N
```

The commands consume caller-provided pose-demo configurations. Keep config
and media paths project-relative to the caller's own application or replace
them with explicit paths valid in that environment; this runtime skill does
not bundle or depend on any checkout. The regular demo
uses Cascade-RCNN plus HRNet; the HD variant uses HTC plus HRNet. Both read a
video frame-by-frame, detect persons, estimate each person's keypoints, collect
frame indices, optionally render boxes/joints, and can write a rendered video.
The documented speed claim was measured on eight TITAN X GPUs and is not a
promise for another machine.

The processor supports one process (`gpus=1`, `worker_per_gpu=1`) or a
multi-process queue. For multiple workers it caches checkpoints before starting
workers and uses `gpus * worker_per_gpu` processes. Start with one worker per
GPU while diagnosing memory, codec, or ordering problems. Do not run this
workflow as part of a lightweight readiness check.

## Video-to-skeleton dataset

Use `processor.skeleton_dataset.build` through a caller-provided dataset
builder configuration:

```text
mmskl path/to/build-dataset-config.yaml \
  --video_dir VIDEO_DIR --category_annotation CATEGORIES.json --out_dir OUT_DIR
```

The builder reads each video, limits frames to `video_max_length` (default
10000), submits frames to detector/HRNet workers, and writes one
`VIDEO_NAME.json` per input video. The optional category annotation has a
`categories` list and an `annotations` mapping from video filename to
`category_id`; absent mappings become `-1`.

Set `tracker_cfg: null`. The current builder explicitly raises
`NotImplementedError` if `tracker_cfg` is non-null, so do not describe that
field as a supported tracking implementation. The resulting records are skeleton data, not a recognition prediction.
Route them to [data-preparation](../../data-preparation/SKILL.md) for JSON
validation and then to [recognition](../../recognition/SKILL.md) for ST-GCN
configuration and inference.

## Checkpoint and network behavior

The `mmskeleton://...` aliases are symbolic names resolved by the package's
checkpoint helper to remote URLs. Relevant aliases include the Cascade-RCNN,
HTC, and HRNet models used by these recipes. A symbolic alias is not a bundled
weight. Prefer a local checkpoint path when the environment is network-restricted;
otherwise download/check the expected artifact outside this runtime tree.
Never represent successful checkpoint alias resolution as proof that detector
ops are importable.

## Safe sequence

1. Run `scripts/check_pose_readiness.py --device ...`.
2. If `--require-detector` fails, stop the detector route and follow
   [troubleshooting.md](troubleshooting.md); do not run pose/video commands.
3. If the gate passes in a separately validated environment, check config and
   checkpoint paths, then choose image API, demo, or dataset builder.
4. Validate emitted JSON through `data-preparation`.
5. Hand validated skeleton data to `recognition`; do not infer recognition
   compatibility from the pose model alone.
