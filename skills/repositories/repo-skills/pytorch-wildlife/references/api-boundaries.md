# API boundaries and shared contracts

Read this when a request crosses more than one sub-skill. These are distilled
from the source wrappers and live package inspection for version 1.3.0.

## Detection to classification

A detector result normally contains `img_id` (or an in-memory image), a
`supervision.Detections` object, and `labels`. The detections object carries
pixel-space `xyxy`, `confidence`, and integer `class_id` arrays. The standard
MegaDetector map is `0=animal`, `1=person`, `2=vehicle`. `DetectionCrops`
selects only the configured animal class (default `0`), crops source images by
`xyxy`, and returns `(crop, path)` items. It does not return the original
detection index, so retain an explicit `(image id, detection index, box)` map if
labels must be joined back to individual animals.

Classifiers return a single dictionary for one image and a list for batches.
The common fields are `img_id`, `prediction`, `class_id`, `confidence`, and
`all_confidences`; the Opossum model has a narrower result contract. Validate
class names and checkpoint output dimensions before joining results.

## Image data

`ClassificationImageFolder` recursively finds common raster extensions and
returns `(RGB image tensor, image path)`. `DetectionImageFolder` returns
`(RGB image tensor, image path, original (height, width))`. The source traversal
is recursive and should not be assumed sorted. The v5 detector transform uses
letterbox padding and CHW float tensors; the classifier transform resizes to a
square and applies ImageNet normalization.

## Bioacoustics

`load_config(path)` returns a nested `DomainConfig` and expands `${VAR}` values
in strings. `build_windows` uses sample indices at the target rate and returns
window metadata (`window_id`, `dataset`, `sample_rate`, `sound_id`, `start`,
`end`, `label`); multiclass adds `ann_overlap`. Inference windows instead use
`window_id`, `sound_path`, `start`, and `end`. Spectrogram helpers save `.npy`
arrays and opportunistically select CUDA; audio is decoded on CPU.

Binary audio inference output uses `audio`, `start(s)`, `end(s)`, `prediction`,
`probability`, and `confidence`. Multiclass output uses `file_path`, audio and
timing fields, `prediction`, and one `<class>_prob` column per class. Do not
apply binary per-second aggregation logic to multiclass output.

## Post-processing

Output serializers are side-effecting and write images or JSON. Detection JSON
uses integer `bbox`, parallel `category`, and `confidence` lists. Dot JSON uses
`dot`; TimeLapse output uses normalized `xywh` boxes. Classification association
requires aligned detector/crop result ordering and should be checked before
serialization. `detection_folder_separation` copies files into `Animal` or
`No_animal`; category `0` must be strictly above the threshold.

## Video

`process_video(source_path, target_path, callback, target_fps=1, codec="mp4v")`
passes RGB frames and an index to the callback. The callback must return an RGB
array. Codec support is platform-dependent; `avc1` can help browser playback
when the local OpenCV/FFmpeg build supports it.
