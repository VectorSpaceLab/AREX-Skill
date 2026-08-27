---
name: data-and-alignment
description: "Prepare Facenet class-folder datasets, validate LFW pair inputs,
  and build safe MTCNN alignment workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Facenet Data and Alignment

Use this sub-skill when the user needs to prepare or check face image data before embedding, evaluation, or training. This includes class-folder dataset layout, LFW pair files, image preprocessing assumptions, and MTCNN alignment commands.

## When to read

- The user asks how to structure a Facenet dataset or why labels/classes are wrong.
- A workflow needs aligned face thumbnails before `compare`, classifier training, LFW validation, or training.
- The task mentions `align_dataset_mtcnn`, MTCNN thresholds, margin, image size, multiple faces, or bounding-box output.
- The user has an LFW-style `pairs.txt` file and missing-image or skipped-pair issues.

## Core conventions

- Facenet datasets use `data_dir/class_name/image_file` directories. `facenet.get_dataset()` sorts class directories and assigns integer labels by sorted class order.
- `facenet.load_data()` reads images, converts grayscale to RGB, optionally prewhitens, then crops/flips to the requested image size.
- MTCNN alignment writes class subdirectories under an output directory and records bounding boxes in `bounding_boxes_<random>.txt`.
- For pretrained 2018 models, later inference/evaluation often needs fixed image standardization; route to [`../evaluation/SKILL.md`](../evaluation/SKILL.md) before LFW evaluation.

## Practical workflow

1. Validate source layout with [`scripts/validate_facenet_dataset.py`](scripts/validate_facenet_dataset.py). It checks class directories, image extensions, minimum images per class, and optional LFW pair references without importing TensorFlow.
2. Read [`references/data-formats.md`](references/data-formats.md) for class-folder, LFW pair, learning-rate schedule, and large dataset conversion formats.
3. If images are unaligned, read [`references/alignment-workflows.md`](references/alignment-workflows.md), then build a command with [`scripts/build_alignment_command.py`](scripts/build_alignment_command.py).
4. Choose `--image_size` and `--margin` based on the downstream workflow. README-era examples commonly use `182` aligned output for training and `160` for model input.
5. Decide whether multiple detected faces should be saved. The default behavior picks one centered/large face; `--detect_multiple_faces` changes output naming and class counts.
6. After alignment, validate the output dataset again before training or classifier workflows.

## Decision points

- **Unaligned vs aligned input**: `compare` and contributed clustering can align internally, but training and LFW evaluation expect prepared aligned face patches.
- **Random order**: use `--random_order` only to help multiple alignment jobs split work; it makes logs harder to compare.
- **Multiple faces**: enable only when each input image may legitimately contain more than one identity; otherwise it can pollute class folders.
- **Skipped images**: alignment records output filenames without boxes when no face is found. Treat a high skip rate as detector/quality/data issue, not a training issue.

## Output contract

A successful preparation pass should leave:

- a validated source or aligned class-folder directory;
- a recorded image size and margin;
- a bounding-box/no-face log from alignment when alignment was run;
- a second validation report showing class counts after alignment.

Keep raw photos and aligned outputs in separate directories so a failed detector run can be discarded without data loss.

## Route onward

- For embedding comparison, classifier training, export, or clustering, continue with [`../embeddings-and-classification/SKILL.md`](../embeddings-and-classification/SKILL.md).
- For LFW pair metrics, continue with [`../evaluation/SKILL.md`](../evaluation/SKILL.md).
- For softmax/triplet model training, continue with [`../training/SKILL.md`](../training/SKILL.md).
- For model path and tensor-name issues, continue with [`../model-export-and-checkpoints/SKILL.md`](../model-export-and-checkpoints/SKILL.md).

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for invalid class-folder layouts, missing pairs, MTCNN import errors, deprecated SciPy image I/O, and unexpected face counts.
