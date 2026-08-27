# Advanced external workflows

These workflows were present as source-side helper surfaces, but they are not part of the required runtime verification scope for this generated skill. Treat them as optional, user-approved, external pipelines. Do not require them for CPU dataset preparation, layout validation, pair combining, Cityscapes conversion, training command construction, or import gates.

## Cityscapes FCN labels-to-photos evaluation

Purpose: evaluate generated Cityscapes label-to-photo predictions on the Cityscapes validation split using an FCN-8s semantic segmentation model and compare FCN outputs with Cityscapes ground-truth labels.

Required external prerequisites:

- licensed original Cityscapes dataset with validation labels and helper metadata,
- Caffe and `pycaffe`, typically with an NVIDIA GPU,
- the FCN-8s Cityscapes Caffe model archive, about 512 MB,
- an evaluator implementation that accepts the interface below,
- predictions named with the original Cityscapes left-image convention, for example `frankfurt_000001_038418_leftImg8bit.png`, under the prediction directory.

External evaluator interface (not a bundled command):

```bash
EXTERNAL_CAFFE_EVALUATOR \
  --cityscapes_dir CITYSCAPES_ORIGINAL_ROOT \
  --result_dir GENERATED_VALIDATION_PREDICTIONS \
  --output_dir METRIC_OUTPUT_DIR \
  --split val \
  --gpu_id 0
```

Use this shape only after an external Caffe evaluator has been installed and validated in its own environment. This generated skill does not bundle or invoke that evaluator.

Expected output: a text report named `evaluation_results.txt` containing mean pixel accuracy, mean class accuracy, mean class IoU, and per-class accuracy/IoU. Some evaluator variants can also save FCN output images.

Important behavior:

- The intended split is Cityscapes validation.
- Generated predictions are expected at 256x256 in the original workflow; the evaluator upsamples internally for comparison with 1024x2048 labels.
- To debug correctness, first evaluate resized real Cityscapes images before trusting synthetic predictions.
- This workflow is excluded from required verification because it combines licensed data, a large network model download, Caffe/pycaffe, GPU assumptions, and older scientific Python dependencies.

## HED edge extraction for edges-to-photo datasets

Purpose: derive simplified edge maps from photos for pix2pix-style edge-to-image datasets such as shoes or handbags.

Required external prerequisites:

- an external HED/Caffe checkout and compatible Caffe Python bindings,
- HED model weights and deploy prototxt placed where that external HED setup expects them,
- GPU access for practical throughput, or a manually modified CPU version,
- MATLAB for post-processing,
- Piotr Dollar's Computer Vision MATLAB Toolbox,
- compiled `edgesNmsMex.cpp` MATLAB mex helper.

External pipeline interface (not bundled):

```bash
EXTERNAL_HED_BATCH \
  --caffe_root CAFFE_ROOT \
  --caffemodel HED_CAFFEMODEL \
  --prototxt HED_DEPLOY_PROTOTXT \
  --images_dir PHOTO_INPUT_DIR \
  --hed_mat_dir HED_MAT_OUTPUT_DIR \
  --gpu_id 0

EXTERNAL_MATLAB_POSTPROCESS HED_MAT_OUTPUT_DIR EDGE_IMAGE_OUTPUT_DIR
```

These placeholders describe the external interface only. This generated skill does not provide an HED/Caffe/MATLAB executable or imply that those dependencies are installed.

Expected output: `.mat` files containing HED edge predictions followed by simplified edge images, commonly JPEGs, ready to be paired with corresponding photos.

Important behavior and hazards:

- Large images can exceed GPU memory; resize photos before running the external HED stage.
- Some Caffe/HED runs can report a driver-shutdown error after computations have completed. Verify output files before deciding whether the run failed.
- Post-processing depends on MATLAB morphology operations and the external mex helper, so it is not portable to the minimum Python-only runtime.
- This workflow is excluded from required verification because it requires external repositories, model downloads, Caffe, GPU-specific setup, MATLAB, and non-Python compiled helpers.

## When to escalate from reference-only

Escalate only when the user explicitly requests one of these external workflows and provides or approves the missing prerequisites. Then record the workflow as an external environment task, keep dataset conversion and validation artifacts separate from the runtime skill tree, and route model training/testing steps to [`translation-workflows`](../../translation-workflows/SKILL.md) after data outputs validate.
