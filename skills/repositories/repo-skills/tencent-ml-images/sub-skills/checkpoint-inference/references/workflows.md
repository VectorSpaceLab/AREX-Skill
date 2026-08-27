# Checkpoint Inference Workflows

These workflows validate inputs and print safe command templates for Tencent
ML-Images checkpoint-backed inference.

## 1. Classify a small set of images

Validate first:

```bash
python scripts/inspect_inference_inputs.py \
  --images data/im_list_for_classification.txt \
  --dictionary data/imagenet2012_dictionary.txt \
  --checkpoint checkpoints/resnet.ckpt \
  --top-k 5 \
  --class-num 1000
```

If the inspector reports no errors, run the printed command in a TensorFlow
1.x/OpenCV runtime prepared for the checkout you are actually using.

Expected behavior:

- The graph restores a checkpoint with `tf.train.Saver`.
- OpenCV reads each image and the helper performs the same center-crop resize
  shown in the source.
- The result file defaults to `label_pred.txt` unless the caller overrides it.

## 2. Extract features

Validate first:

```bash
python scripts/inspect_feature_inputs.py \
  --images data/im_list_for_classification.txt \
  --checkpoint checkpoints/ckpt-resnet101-mlimages-imagenet \
  --result features.txt
```

If the inspector reports no errors, run the printed command in a compatible
runtime.

Expected behavior:

- `net.feat` is extracted after global average pooling.
- The output file records the image path and the feature vector values.
- The script can run on a single image or on a list of images.

## 3. How to read the public shell examples

The source shell examples are short wrappers, not the actual safety boundary.
They show the expected flags and file names:

- `--images` points at a newline-separated image list.
- `--dictionary` points at the ImageNet dictionary.
- `--model_dir` or `--pretrain_ckpt` points at a TensorFlow checkpoint prefix.
- `--result` sets the output file.
- `--top_k_pred` controls the number of class predictions.

Use the bundled inspectors to validate those paths before any restore step.

## 4. When to stop instead of running

Stop and fix the inputs if:

- the checkpoint prefix has no `.index`/`.data-*` files;
- the dictionary row count does not match `class_num`;
- image paths are missing or unreadable;
- a CPU-only environment cannot import OpenCV or the TensorFlow 1.x APIs;
- the source checkout still has the `from __future__` placement issue in the
  original scripts and you have not patched it.
