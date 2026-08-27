# MMAction2 data and config reference

This reference is self-contained operating knowledge for preparing MMAction2 inputs. It covers the dataset classes, annotation schemas, dataloader/pipeline structure, config families, inheritance, and override syntax that future agents need for data/config work.

## 1. Dataset selection map

| User data | Dataset type | Annotation file | Main `data_prefix` key | Typical loading transforms |
| --- | --- | --- | --- | --- |
| Encoded videos for RGB/flow recognition | `VideoDataset` | text list | `video` | `DecordInit`/`OpenCVInit`/`PyAVInit` + `SampleFrames` + matching decode |
| Extracted RGB/flow frame folders | `RawframeDataset` | text list | `img` | `SampleFrames` + `RawFrameDecode` |
| Skeleton/keypoint action recognition | `PoseDataset` | `.pkl` | optional `video`, optional `skeleton` | pose transforms such as `PoseDecode`, `PreNormalize*`, `GenSkeFeat`, `GeneratePoseTarget` |
| Offline audio features | `AudioDataset` | text list | `audio` | `LoadAudioFeature` + `SampleFrames` + `AudioFeatureSelector` |
| Spatio-temporal action detection | `AVADataset` | CSV plus optional exclude/label/proposal files | `img` | `SampleAVAFrames` + decode + spatial transforms |
| Temporal action localization from features | `ActivityNetDataset` | JSON | `video` | `LoadLocalizationFeature` + `GenerateLocalizationLabels` + `PackLocalizationInputs` |
| Video-text retrieval pairs | `VideoTextDataset` | JSON mapping video to text list | `video` | video decode + `CLIPTokenize` + pack/format steps from the config |

Use `test_mode=True` in validation/test dataset configs. Keep `shuffle=True` only for the training sampler and `shuffle=False` for validation/test samplers.

## 2. Annotation schemas

### `VideoDataset`

Text file, one sample per line:

```text
relative/or/absolute/video_000.mp4 0
relative/or/absolute/video_001.mp4 3
```

Behavior and checks:

- With `multi_class=False`, each line is `filename label`; `label` must parse as one integer.
- With `multi_class=True`, each line is `filename label_1 label_2 ...`; set `num_classes` and keep every label in `[0, num_classes - 1]`.
- A line with only `filename` is treated as an unlabeled/inference-like sample with label `-1`; do not use such lines for supervised training.
- `data_prefix=dict(video=ROOT)` is joined to relative filenames. Use `dict(video=None)` only when filenames are already complete and should not be joined.
- Default `start_index` is `0` for videos because decoded video frames are zero-based.
- If a non-space separator is used, set `delimiter` consistently.

Minimal dataloader dataset block:

```python
dataset=dict(
    type='VideoDataset',
    ann_file='train_list.txt',
    data_prefix=dict(video='videos_train'),
    pipeline=train_pipeline)
```

### `RawframeDataset`

Text file, one video/clip directory per line:

```text
class_a/video_000 163 0
class_b/video_001 122 3
```

Multi-label:

```text
class_a/video_000 163 0 4 9
```

Clip-with-offset form, enabled by `with_offset=True`:

```text
class_a/video_000 12 163 0
# fields: frame_dir offset total_frames label...
```

Behavior and checks:

- Required fields without offset: `frame_dir total_frames label...`.
- Required fields with offset: `frame_dir offset total_frames label...`.
- `total_frames` is an integer count of available frames for that sample or clip.
- `data_prefix=dict(img=ROOT)` is joined to relative `frame_dir` values.
- Default `filename_tmpl` is `img_{:05}.jpg`; change it for different frame names such as `{:06d}.jpg` or `frame_{:04d}.png`.
- Default `start_index` is `1` for raw frames because standard extracted frame names are one-based.
- `multi_class=True` requires `num_classes` and one or more labels per line.
- `RawFrameDecode` expects `frame_dir`, `filename_tmpl`, `frame_inds`, `modality`, and optionally `offset`.

Minimal dataset block:

```python
dataset=dict(
    type='RawframeDataset',
    ann_file='train_rawframes.txt',
    data_prefix=dict(img='rawframes_train'),
    filename_tmpl='img_{:05}.jpg',
    pipeline=train_pipeline)
```

### `PoseDataset`

Pickle file ending in `.pkl`. Two common layouts are accepted.

List layout:

```python
[
    dict(
        frame_dir='video_000',
        total_frames=103,
        label=0,
        img_shape=(1080, 1920),
        original_shape=(1080, 1920),
        keypoint=<array shape [M, T, V, C]>,
        keypoint_score=<array shape [M, T, V]>),
    ...
]
```

Split layout:

```python
dict(
    split=dict(train=['video_000'], val=['video_001']),
    annotations=[dict(frame_dir='video_000', ...), dict(frame_dir='video_001', ...)])
```

Required and optional fields:

- `frame_dir` or `filename`: video identifier used for splits and optional prefix joining.
- `total_frames`: integer number of pose frames.
- `label`: integer class id.
- `keypoint`: array with shape `[M, T, V, C]`, where `M` persons, `T` frames, `V` keypoints, `C` coordinate dimensions.
- `keypoint_score`: array with shape `[M, T, V]`; required for common 2D pose pipelines.
- `img_shape` and `original_shape`: `(height, width)`; needed by 2D pose heatmap/compact transforms.
- Kinetics-pose-style filtering can use `valid`, `box_score`, `valid_ratio`, and `box_thr`. `box_thr` accepts only `0.5`, `0.6`, `0.7`, `0.8`, or `0.9`.

Keypoint format guidance:

- Built-in graph/pipeline layouts include `coco`, `nturgb+d`, and `openpose`.
- For GCN-style configs, keep the graph layout in the backbone and the skeleton feature transform consistent, for example `graph_cfg=dict(layout='coco', ...)` with `GenSkeFeat(dataset='coco')`.
- For PoseC3D heatmaps, keep `Flip`, `GeneratePoseTarget`, and any left/right keypoint or limb definitions aligned to the keypoint order.

### `AudioDataset`

Text file, one audio feature sample per line:

```text
sample_000.npy 300 153
sample_001.npy 240 321
```

Behavior and checks:

- Fields are `audio_feature_filename total_frames label...`.
- `audio_feature_filename` points to an offline feature file, commonly a NumPy feature array.
- `total_frames` is the frame count of the original video timeline used to align audio clips to sampled frames.
- With `multi_class=False`, exactly one label is required; missing labels raise an assertion.
- With `multi_class=True`, set `num_classes` and provide one or more labels.
- Use `data_prefix=dict(audio=ROOT)` for relative feature filenames.
- Common pipeline: `LoadAudioFeature`, `SampleFrames`, `AudioFeatureSelector`, `FormatAudioShape`, `PackActionInputs`.

### `AVADataset`

Ground-truth CSV, one action label for one person box at one timestamp per line:

```text
video_id,0902,0.063,0.049,0.524,0.996,12,0
video_id,0902,0.063,0.049,0.524,0.996,74,0
```

Fields:

1. `video_id`
2. `timestamp` as an integer; formatted as four digits for proposal keys
3. `x1` normalized left coordinate
4. `y1` normalized top coordinate
5. `x2` normalized right coordinate
6. `y2` normalized bottom coordinate
7. `label` integer action id
8. `entity_id` integer linking the same person across frames

Behavior and checks:

- Box coordinates and proposal coordinates must be relative values in `[0.0, 1.0]`.
- Multiple rows with the same `video_id,timestamp` and same box/entity are merged into a multi-label target when `multilabel=True`.
- Default `num_classes=81`; AVA-style models reserve an extra background/unused index. If using `custom_classes`, do not include class `0`, and set `num_classes=len(custom_classes)+1`.
- `exclude_file` is a CSV-like list of `video_id,timestamp` rows to drop.
- `label_file` is used when class names or custom class validation are needed.
- `proposal_file` is a pickle dictionary keyed by `video_id,timestamp` with timestamp zero-padded, for example `video_id,0902`.
- Each proposal value is an `N x 4` or `N x 5` array. `N x 5` means `[x1, y1, x2, y2, score]`; scores are filtered by `person_det_score_thr`, but at least the highest-scoring proposal is kept.
- `data_prefix=dict(img=ROOT)` is joined to frame directories. When `use_frames=False`, the dataset emits `filename` instead of `frame_dir` after initial parsing.
- Defaults: `start_index=1`, `filename_tmpl='img_{:05}.jpg'`, `timestamp_start=900`, `timestamp_end=1800`, `fps=30`.
- For frame-counted datasets such as MultiSports-like inputs, set `fps=1` and verify `start_index`/timestamp logic with a tiny sample before a full run.

### `ActivityNetDataset`

JSON object keyed by video name:

```json
{
  "video1": {
    "duration_second": 211.53,
    "duration_frame": 6337,
    "annotations": [
      {"segment": [30.0259, 205.2319], "label": "Rock climbing"}
    ],
    "feature_frame": 6336,
    "fps": 30.0,
    "rfps": 29.9579
  }
}
```

Behavior and checks:

- `data_prefix=dict(video=FEATURE_ROOT)` is used to construct `feature_path = FEATURE_ROOT / (video_name + '.csv')`.
- `segment` values are temporal start/end seconds, not frame indices.
- `duration_second`, `duration_frame`, `feature_frame`, `fps`, and `rfps` should be present for localization label generation and metric post-processing.
- Typical pipeline: `LoadLocalizationFeature`, `GenerateLocalizationLabels`, `PackLocalizationInputs`.

### `VideoTextDataset`

JSON object mapping each video filename to one or more text strings:

```json
{
  "videos/clip_000.mp4": ["a person opens a door", "someone enters a room"],
  "videos/clip_001.mp4": ["a dog runs outside"]
}
```

Behavior and checks:

- The dataset expands each text into a separate `(filename, text)` pair.
- Use `data_prefix=dict(video=ROOT)`; keep JSON filenames relative to that root unless they are intentionally complete paths.
- There is no class label. Retrieval configs normally pair video decode transforms with `CLIPTokenize` or a model-specific tokenizer.

## 3. Dataloader structure

Modern MMAction2 configs use MMEngine-style dataloaders:

```python
train_dataloader = dict(
    batch_size=32,
    num_workers=8,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=True),
    dataset=dict(
        type='VideoDataset',
        ann_file='train.txt',
        data_prefix=dict(video='videos_train'),
        pipeline=train_pipeline))

val_dataloader = dict(
    batch_size=1,
    num_workers=8,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type='VideoDataset',
        ann_file='val.txt',
        data_prefix=dict(video='videos_val'),
        pipeline=val_pipeline,
        test_mode=True))

test_dataloader = dict(..., dataset=dict(..., pipeline=test_pipeline, test_mode=True))
```

Checklist:

- `train_dataloader.dataset.pipeline` should point to `train_pipeline`; validation/test should point to deterministic pipelines.
- Validation/test datasets should set `test_mode=True` unless a specialized config intentionally handles this elsewhere.
- Use `batch_size=1` for validation/test when multi-crop, AVA, or variable-shape samples would otherwise exceed memory.
- `persistent_workers=True` is useful for real training but can be disabled for small debugging runs.
- If `data_root` is used, relative `ann_file` and `data_prefix` values are resolved under it by MMEngine dataset handling; keep this consistent and avoid mixing absolute and unintended relative paths.

## 4. Pipeline patterns

A pipeline is a list of transforms. Each transform consumes and returns a Python dictionary; the dataset supplies initial keys such as `filename`, `frame_dir`, `total_frames`, `label`, `modality`, and `start_index`.

### Encoded video recognition

```python
train_pipeline = [
    dict(type='DecordInit'),
    dict(type='SampleFrames', clip_len=32, frame_interval=2, num_clips=1),
    dict(type='DecordDecode'),
    dict(type='Resize', scale=(-1, 256)),
    dict(type='RandomResizedCrop'),
    dict(type='Resize', scale=(224, 224), keep_ratio=False),
    dict(type='Flip', flip_ratio=0.5),
    dict(type='FormatShape', input_format='NCTHW'),
    dict(type='PackActionInputs')]
```

Test-time changes usually include `test_mode=True` in `SampleFrames`, a larger `num_clips`, deterministic crop such as `CenterCrop`, `ThreeCrop`, or `TenCrop`, and `flip_ratio=0` unless flip testing is intentional.

### Rawframe recognition

Use `SampleFrames` before `RawFrameDecode` and set the dataset type to `RawframeDataset`. Verify `filename_tmpl` and `start_index` before blaming the decoder.

### AVA detection

Use `SampleAVAFrames`, `RawFrameDecode` or a matching video decoder, spatial transforms that keep boxes synchronized, `FormatShape(input_format='NCTHW', collapse=True)`, and `PackActionInputs`. Never use recognition-only transforms that drop box fields before packing.

### Skeleton recognition

Common transform families:

- Decode/sample: `UniformSampleFrames`, `PoseDecode`, `MMUniformSampleFrames`, `MMDecode`.
- Normalize/compact: `PreNormalize2D`, `PreNormalize3D`, `PoseCompact`, `MMCompact`.
- Feature generation: `JointToBone`, `ToMotion`, `MergeSkeFeat`, `GenSkeFeat`, `GeneratePoseTarget`.
- Format: `FormatGCNInput` for GCN-style tensors or `FormatShape`/`PackActionInputs` for heatmap-style pipelines.

Keep the number/order of keypoints consistent across the annotation file, graph layout, and pipeline transforms.

### Audio recognition

Use offline features and a timeline-aligned sampler: `LoadAudioFeature`, `SampleFrames`, `AudioFeatureSelector`, `FormatAudioShape`, and pack. Most audio errors are caused by a mismatch between feature length, `total_frames`, and sampled frame indices.

### Localization

`ActivityNetDataset` supplies `feature_path` and metadata; `LoadLocalizationFeature` reads feature CSVs and `GenerateLocalizationLabels` uses segment annotations. Do not use video frame decoders for feature-based localization configs.

### Transform family catalog

- Temporal sampling: `SampleFrames`, `DenseSampleFrames`, `UniformSample`, `UntrimmedSampleFrames`, `SampleAVAFrames`, pose-specific uniform samplers.
- Video/raw loading: `DecordInit`/`DecordDecode`, `OpenCVInit`/`OpenCVDecode`, `PyAVInit`/`PyAVDecode`, `PIMSInit`/`PIMSDecode`, `RawFrameDecode`, `ImageDecode`, `ArrayDecode`.
- Audio/localization loading: `LoadAudioFeature`, `AudioFeatureSelector`, `LoadLocalizationFeature`, `GenerateLocalizationLabels`, `LoadProposals`.
- Spatial/appearance: `Resize`, `RandomResizedCrop`, `RandomCrop`, `RandomRescale`, `MultiScaleCrop`, `CenterCrop`, `ThreeCrop`, `TenCrop`, `Flip`, `ColorJitter`, `RandomErasing`, `Fuse`.
- Pose: `DecompressPose`, `GeneratePoseTarget`, `PoseCompact`, `PreNormalize2D`, `PreNormalize3D`, `JointToBone`, `ToMotion`, `MergeSkeFeat`, `GenSkeFeat`, `PoseDecode`, `PadTo`.
- Formatting/packing: `FormatShape`, `FormatAudioShape`, `FormatGCNInput`, `PackActionInputs`, `PackLocalizationInputs`, `Transpose`.
- Text/wrappers: `CLIPTokenize`, `TorchVisionWrapper`, `PytorchVideoWrapper`, `ImgAug`.

## 5. Config families and naming

Top-level config families are organized by task:

- `recognition`: RGB/flow video or rawframe classification.
- `recognition_audio`: audio-feature classification.
- `skeleton`: keypoint/skeleton action recognition.
- `detection`: AVA-style spatio-temporal action detection.
- `localization`: temporal action localization from features.
- `retrieval` and selected `multimodal`: video-text retrieval or VQA-like multimodal tasks.
- `_base_`: reusable model, schedule, and runtime fragments.

Config file names follow this logical pattern:

```text
{algorithm-info}_{module-info}_{training-info}_{data-info}.py
```

Interpretation examples:

- Algorithm info: `tsn`, `i3d`, `slowfast`, `videomae`, `stgcn`, `bmn`.
- Module info: backbone and pretraining, for example `imagenet-pretrained-r50`, `vit-base-p16`, `k400-pre`.
- Training info: batch/GPU and sampling/schedule, for example `8xb32`, `32x2x1`, `100e`, `cosine-10e`, `amp`.
- Data info: dataset and modality, for example `kinetics400-rgb`, `ava21-rgb`, `activitynet-feature`, `ntu60-xsub-keypoint`, `msrvtt-9k-rgb`.

Underscores separate logical groups; hyphens separate settings inside a group. `8xb32` means eight devices with batch size 32 per device in the original recipe; adapt batch sizes to the user's hardware before training.

## 6. `_base_` inheritance and config editing

MMAction2 config files are Python files loaded by MMEngine. A config can inherit one string or a list of strings through `_base_`:

```python
_base_ = [
    'path/to/base_model.py',
    'path/to/base_schedule.py',
    'path/to/default_runtime.py']
```

Rules for safe editing:

- Resolve inheritance with a config parser or the bundled inspector before editing deeply nested fields.
- Prefer overriding only the fields that change: dataset type, annotation files, data roots, class counts, pipelines, sampler/batch settings, evaluator, and model head classes.
- If replacing an inherited dictionary wholesale, use MMEngine's `_delete_=True` convention in the replacement dict.
- Keep top-level `default_scope='mmaction'` unless the task intentionally uses external registries.
- When adapting to a custom classification dataset, update both `model.cls_head.num_classes` and dataset/evaluator class assumptions.
- When adapting AVA detection, update `num_classes`, `label_file`, `custom_classes`, evaluator label/exclude files, and proposal compatibility together.

## 7. `--cfg-options` override syntax

`--cfg-options` merges key-value pairs into the parsed config. Dotted keys traverse dictionaries; numeric path components index lists.

Examples:

```shell
--cfg-options model.backbone.norm_eval=False
--cfg-options model.cls_head.num_classes=5
--cfg-options train_pipeline.0.type=DenseSampleFrames
--cfg-options train_pipeline.0.num_clips=8
--cfg-options train_dataloader.dataset.ann_file=train_custom.txt
--cfg-options train_dataloader.dataset.data_prefix.video=videos_train
--cfg-options model.data_preprocessor.mean="[127.5,127.5,127.5]"
--cfg-options train_dataloader.batch_size=4 val_dataloader.num_workers=2
```

Quoting rules:

- Quote lists, tuples, and nested structures so the shell passes them as one argument: `key="[1,2,3]"`, `key="[(1,2),(3,4)]"`.
- Avoid spaces inside list/tuple override strings unless the shell quoting is known to preserve them.
- For string values containing spaces or commas, use config-file edits rather than command-line overrides.
- After applying overrides, inspect the resolved config summary before launching expensive work.

## 8. Pre-run validation checklist

1. Dataset class matches the annotation schema and the pipeline's loader.
2. `data_prefix` uses the correct key: `video`, `img`, or `audio` as required by the dataset.
3. Validation/test datasets set `test_mode=True` and deterministic sampling/cropping.
4. Labels are integers for classification/detection, within range, and consistent with `num_classes`.
5. Rawframe `total_frames`, `filename_tmpl`, and `start_index` match actual frame files.
6. AVA boxes/proposals are normalized in `[0, 1]` and proposal keys use zero-padded timestamps.
7. Localization JSON has duration and feature metadata; feature CSV names are `video_name + '.csv'`.
8. Pose keypoint arrays match `[M, T, V, C]`; graph/pipeline layout matches `V` and keypoint order.
9. Audio feature length and `total_frames` are compatible with the sampling window.
10. `--cfg-options` were quoted correctly and verified with the config inspector.
