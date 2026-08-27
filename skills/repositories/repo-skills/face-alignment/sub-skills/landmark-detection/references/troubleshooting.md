# Landmark Detection Troubleshooting

## Purpose

Use this file when the main landmark workflow misbehaves after the package installs successfully.

## Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No faces were detected.` | The image is hard to detect, the chosen backend is a poor fit, or the detector thresholds are too strict | Try a clearer face image, switch detectors, or pass precomputed bounding boxes through `detected_faces` |
| Slow first call or `torch.compile` warning | The compile path is warming up or unavailable | Re-run with `compile=False` when you want instant startup or simpler debugging |
| Memory pressure on images with many faces | The model is processing too many crops in one chunk | Lower `max_batch_size` |
| Batch inference returns empty per-image lists | A given batch element had no detected faces | Check the input image, detector choice, and thresholds for that batch element |
| Directory scan finds no images | The extensions list does not match the files, or the path is wrong | Confirm `extensions` and `recursive`, then verify the directory path |
| Shape errors on batch input | The tensor is not in `B, C, H, W` order | Reorder the array before converting to a torch tensor |
| Tuple output when you expected bare landmarks | `return_bboxes` or `return_landmark_score` was enabled | Handle the `(landmarks, scores, boxes)` return shape explicitly |

## Input assumptions

- `get_landmarks_from_image` accepts a path, NumPy array, or tensor.
- `get_landmarks_from_batch` expects a torch tensor batch.
- `get_landmarks_from_directory` expects a directory containing image files with matching extensions.

## Recovery patterns

1. Start with `device='cpu'` and `compile=False` to isolate model issues from acceleration or compilation issues.
2. Confirm that the detector backend itself is healthy using the detector sub-skill if detections are missing.
3. If the image already has known boxes, skip detector work and pass them in as `detected_faces`.
4. Once the image pipeline works, turn `compile=True` back on if you want the first-run compile cache.
