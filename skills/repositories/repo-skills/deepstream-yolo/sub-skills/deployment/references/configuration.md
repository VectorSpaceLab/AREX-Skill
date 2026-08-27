# Deployment configuration reference

## `deepstream_app_config.txt` groups

| Group | Purpose | Key fields |
| --- | --- | --- |
| `tiled-display` | Output layout and render resolution | `rows`, `columns`, `width`, `height`, `gpu-id`, `nvbuf-memory-type` |
| `sourceN` | Input stream wiring | `type`, `uri`, `num-sources`, `gpu-id`, `cudadec-memtype` |
| `sinkN` | Output sink | `type`, `sync`, `gpu-id`, `nvbuf-memory-type` |
| `streammux` | Batch and mux settings | `batch-size`, `width`, `height`, `live-source`, `batched-push-timeout`, `enable-padding` |
| `primary-gie` | Main inference element | `gie-unique-id`, `config-file`, `nvbuf-memory-type`, `gpu-id` |
| `secondary-gieN` | Additional inference elements | `gie-unique-id`, `operate-on-gie-id`, `operate-on-class-ids`, `config-file` |

## `config_infer_primary*.txt` keys

| Key | Meaning | Common deployment use |
| --- | --- | --- |
| `onnx-file` | ONNX model path | ONNX-based families |
| `custom-network-config` | Darknet config path | `.cfg` + `.weights` families |
| `model-file` | Darknet weights path | `.cfg` + `.weights` families |
| `model-engine-file` | TensorRT engine cache path | Stable cache for repeat runs |
| `num-detected-classes` | Class count | Must match labels and checkpoint |
| `batch-size` | Inference batch | Must match the engine and pipeline setup |
| `network-mode` | Precision mode | `0` FP32, `1` INT8, `2` FP16 |
| `maintain-aspect-ratio` | Resize behavior | Usually `1` for centered / letterboxed families |
| `symmetric-padding` | Padding symmetry | Family-specific; see matrix |
| `model-color-format` | RGB/BGR/gray input order | Must match model family preprocessing |
| `net-scale-factor` | Input normalization | Family-specific scaling/mean choices |
| `cluster-mode` | Post-processing mode | `2` for NMS-style family defaults; `4` for RT-DETR / similar no-NMS flows |
| `force-implicit-batch-dim` | Darknet batching mode | Leave at the family default unless Darknet docs require otherwise |
| `parse-bbox-func-name` | Parser function | Usually `NvDsInferParseYolo` |
| `engine-create-func-name` | TensorRT engine builder | Usually `NvDsInferYoloCudaEngineGet` for ONNX / custom engines |

## Practical rules

- Use the family matrix first, then confirm the template keys here.
- The config file name is part of the workflow contract; pick the template that matches the exporter and model family.
- When the model is already an ONNX file, most edits happen in the infer config, not in the app config.
- If the pipeline runs but detections are wrong, check `labels.txt`, `num-detected-classes`, and the resize / color / normalization knobs.
