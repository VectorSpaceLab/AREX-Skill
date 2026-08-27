# Workflows

This guide turns the API reference into practical inference and export routes.

## 1) Choose the right prediction path

| Need | Best path | Notes |
| --- | --- | --- |
| Feed numpy arrays through a fresh inference graph | `PredictConfig` + `SmartInit` + `OfflinePredictor` | The common demo path. |
| Reuse an already created session | `OnlinePredictor` | Good for custom code that already owns the graph. |
| Consume an `InputSource` or staged queue | `FeedfreePredictor` | No feed dicts; input comes from the source. |
| Export SavedModel | `ModelExporter.export_serving()` | For TensorFlow Serving or any SavedModel consumer. |
| Export a frozen/pruned graph | `ModelExporter.export_compact()` | For lightweight TensorFlow graph loading. |
| Convert Caffe weights | `tensorpack.utils.loadcaffe` | Produces a dictionary that can be loaded with `SmartInit`. |

## 2) Build a clean inference graph

When you need to write the graph by hand, keep the inference path separate from training logic.

```python
with TowerContext("", is_training=False):
    model.build_graph(input_tensor)
```

Key points:

- `is_training=False` must be explicit when you create the graph yourself.
- Do not import a training metagraph for this step.
- Use a dedicated inference model or tower function if the input layout changes at inference time.
- Expose the tensors you want to fetch with explicit names, usually via `tf.identity(..., name='prediction')`.

`PredictConfig` already builds the inference tower under the correct inference context, so you normally only need manual `TowerContext(...)` when you are bypassing `PredictConfig` or constructing a custom graph for export.

## 3) Simple offline prediction

A standard predictor usually looks like this:

```python
pred_config = PredictConfig(
    model=InferenceModel(),
    session_init=SmartInit("model-100000"),
    input_names=["input_img"],
    output_names=["prediction_img"],
)
predictor = OfflinePredictor(pred_config)
out = predictor(input_batch)
```

Useful reminders:

- `input_names` can refer to declared input signature names or graph tensor names.
- `output_names` must point to tensors that are computable from those inputs.
- `return_input=True` is useful when you want the predictor to echo the fed inputs along with outputs.

## 4) Export choices

### SavedModel / Serving

Use `export_serving()` when you want a TensorFlow Serving-friendly package.
It saves variables plus a SavedModel protobuf.

### Compact graph

Use `export_compact()` when you want a frozen and pruned graph.
This is the better choice when the consumer wants a plain `GraphDef`.

Caveats:

- `export_compact(..., optimize=True)` relies on TensorFlow graph transforms and may fail on some graphs.
- If that happens, rerun with `optimize=False` or choose SavedModel instead.
- `toco_compatible=True` is only meaningful when optimization is on.

## 5) Model-zoo and custom `.npz` workflows

Tensorpack model-zoo files are usually `.npz` dictionaries.
Typical flow:

1. Build the inference graph.
2. Map the loaded variable names to the graph variable names, if needed.
3. Load them with `SmartInit(...)`.
4. Use `OfflinePredictor` or export the graph after the restore step.

If a name mapping is necessary, do it before restore and verify the resulting names with the checkpoint inspector.

## 6) Caffe conversion flow

Caffe-based model zoo workflows usually look like this:

```bash
python -m tensorpack.utils.loadcaffe deploy.prototxt model.caffemodel output.npz
```

Then load the generated `.npz` with `SmartInit(output.npz)`.

Dependency notes:

- Caffe Python bindings are required.
- The converter reads a `.prototxt` plus a `.caffemodel`.
- OpenCV is often used by the example inference scripts for image I/O.

## 7) Distilled source-evidence patterns

Use these patterns as self-contained guidance; do not require the original example checkout unless the user explicitly supplies it.

- **Basic export demo**
  - Trains a toy model on fake data.
  - Uses a separate inference-only graph.
  - Demonstrates both `export_serving()` and `export_compact()`.
  - Demonstrates applying the model through `OfflinePredictor`.
  - Bundled replacement: `../scripts/export_model_demo.py`.

- **Caffe-imported vision models**
  - Convert Caffe weights to `.npz` and run inference with `OfflinePredictor`.
  - Use `PredictConfig`, `SmartInit`, and image preprocessing for imported weights.
  - Treat Caffe bindings and model files as optional external prerequisites.

- **Converted ResNet inference**
  - Load converted weights into a Tensorpack graph.
  - Run ImageNet-style prediction or validation only when the user supplies data and weights.
  - Keep data-layout and preprocessing assumptions explicit.

- **Saliency and CAM**
  - Build predictors around fixed ImageNet-style models.
  - Fetch gradients, activation maps, or postprocessed tensors by exact output names.
  - Expect OpenCV/image I/O and optional DISPLAY constraints.

- **Detection prediction/export**
  - Use detector prediction, evaluation JSON, multiple outputs, and postprocessing patterns.
  - Use `ModelExporter` for compact and Serving outputs in larger models.
  - Treat COCO data, pretrained weights, and pycocotools as required external prerequisites.

## 8) Clean mental model

If you are unsure which route to take, ask three questions:

1. Do I already have a checkpoint or `.npz`? -> `SmartInit`.
2. Do I want a fresh predictor or a portable artifact? -> `OfflinePredictor`, `export_serving()`, or `export_compact()`.
3. Do I need a special input layout or a different inference graph? -> create a separate inference model, do not reuse the training metagraph.
