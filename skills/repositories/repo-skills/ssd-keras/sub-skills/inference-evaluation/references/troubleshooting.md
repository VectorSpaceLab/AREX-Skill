# Inference and Evaluation Troubleshooting

## Common failures

- **`load_model` cannot deserialize an SSD model**
  - Cause: the custom layers and custom loss were not passed in `custom_objects`.
  - Fix: include the same custom objects that the notebook uses for the selected model mode.

- **Predictions come back empty**
  - Cause: the confidence threshold is too high, the weights do not match the architecture, or the model is being decoded with the wrong mode.
  - Fix: lower `confidence_thresh`, confirm the weights file matches the builder, and check `model_mode`.

- **Boxes are shifted or scaled incorrectly**
  - Cause: `normalize_coords`, `img_height`, `img_width`, or the anchor settings do not match the model configuration.
  - Fix: keep the decoder settings aligned with the training settings.

- **VOC evaluation fails or reports nonsense AP values**
  - Cause: the ground-truth generator and the model predictions use different coordinate conventions.
  - Fix: inspect `pred_format`, `gt_format`, and the image-size assumptions before trusting the metric.

- **COCO export or evaluation fails**
  - Cause: the category map is not built correctly, or `pycocotools` is missing.
  - Fix: build the category maps with `get_coco_category_maps()` and install `pycocotools` only when you need the full COCO evaluation path.

- **`scipy.misc.imread` is missing in the notebook-era code**
  - Cause: modern SciPy removed that helper.
  - Fix: use `imageio` or Pillow in new helper scripts.

- **`Evaluator` returns warnings about the data generator**
  - Cause: the generator does not expose the labels or evaluation-neutral flags the evaluator expects.
  - Fix: load the evaluation dataset through the data-preparation route and keep the label metadata intact.

## Fast recovery path

1. Run `scripts/check_env.py`.
2. Run `sub-skills/inference-evaluation/scripts/smoke.py`.
3. Confirm the model mode, decoder settings, and image dimensions all agree.
4. Only then move to the full notebook-scale inference or evaluation workflow.
