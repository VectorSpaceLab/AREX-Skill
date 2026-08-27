# Metrics Data Formats

## Detection/tracking Objects

Detection/tracking submissions use object protos with context name, frame timestamp, object type, score, and box fields. 3D boxes use center x/y/z, length, width, height, and heading. 2D boxes use image-plane center x/y, length, and width plus a camera name.

## Metric configs

Detection/tracking configs choose box type, breakdown generators, difficulty levels, IoU thresholds, score cutoffs, and optional fields such as no-label-zone overlap. Motion metric configs choose object types, measurement steps, history/future lengths, and scenario/object identifiers.

## Tensor shapes

- Detection prediction boxes: `[M, D]`, where D matches the config box type.
- Detection frame ids/types/scores/no-label-zone flags: length `[M]`.
- Motion prediction trajectories: `[B, M, K, N, TP, 2]`.
- Motion ground truth trajectories: `[B, A, TG, 7]` with validity `[B, A, TG]`.

Use the wrapper docstrings and this shape map before constructing tensors.
