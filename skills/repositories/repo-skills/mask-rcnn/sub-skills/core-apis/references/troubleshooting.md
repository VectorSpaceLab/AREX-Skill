# Core API Troubleshooting

## `detect()` or `train()` assertion fails on mode

`MaskRCNN` models are mode-specific. Build a training model for `train()` and an inference model for `detect()`:

```python
train_model = modellib.MaskRCNN(mode="training", config=config, model_dir="logs")
infer_model = modellib.MaskRCNN(mode="inference", config=infer_config, model_dir="logs")
```

## `len(images) must be equal to BATCH_SIZE`

`detect()` expects a list of images with length exactly equal to `config.BATCH_SIZE`. For single-image inference, set `GPU_COUNT = 1` and `IMAGES_PER_GPU = 1` in the inference config, then call `model.detect([image])`.

## Image dimensions are not divisible by 64

The FPN upsamples/downsamples across six stride levels. Use square dimensions such as 512 or 1024, or set `IMAGE_RESIZE_MODE = "pad64"` for inference-style configs that should pad images to valid sizes.

## Layer or weight names are confusing

Use `model.keras_model.summary()` to inspect Keras layers and `model.get_trainable_layers()` to list layers with weights. Training owns the layer-selection regex guidance in `../../training/references/training-workflows.md`.

## Missing optional package

- `pycocotools`: only required for COCO loading/evaluation and mask encoding.
- `cv2`/OpenCV: required for Shapes drawing and video helpers.
- `imgaug`: required for augmentation paths.

If the current task is only API inspection or dataset JSON validation, do not install optional training/evaluation packages unnecessarily.

## Import succeeds but graph build fails

Run the inspector with the graph flag:

```bash
python sub-skills/core-apis/scripts/inspect_mask_rcnn_api.py --build-tiny-graph
```

If graph build fails under modern Keras, switch to a TF1/Keras2 stack or treat the task as source modernization. Do not proceed to training/inference until graph build passes.
