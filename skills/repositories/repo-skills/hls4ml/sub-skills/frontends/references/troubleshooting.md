# Troubleshooting

## Dependency and environment issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError` for TensorFlow, Keras, PyTorch, ONNX, qonnx, qkeras, snntorch, HGQ, HGQ2, da4ml, or pquant-ml | Missing optional frontend package | Install only the extras needed for the model family |
| Keras v2 and Keras v3 packages fight each other | Conflicting frontend stacks in one environment | Split the work into two environments |
| QKeras does not import under Keras 3 | Wrong Keras family | Move the model to the Keras v2 stack |
| `plot_model` cannot import pydot or Graphviz | Plotting dependency missing | Install pydot and Graphviz |
| `fetch_example_model()` fails or hangs | Network access is required | Run in a network-enabled scratch directory or use local copies |

## Conversion issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Layer ... not found in registry` | Unsupported frontend op or missing optional package | Check the active registry and either simplify the model or enable the right extra |
| Keras `Add` / `Subtract` / `Multiply` / `Divide` nodes fail | Those are operators, not the supported layer path | Replace them with supported Keras layers or a custom extension |
| `Lambda` layers fail | Generic lambda parsing is not supported | Rewrite the model without `Lambda` or move the custom logic to an extension |
| `channels_first` Keras / PyTorch input layout causes wrong shapes | hls4ml uses channels-last internally | Convert the input layout or keep the transposition inside the model config |
| `io_stream` PyTorch conversion fails on transposed inputs | Stream mode does not add the user input transpose | Use `channels_last_conversion='internal'` and transpose the input yourself |
| Brevitas cannot be parsed directly | Direct Brevitas ingestion is not supported | Export to ONNX/QONNX first |
| ONNX `Gemm` or other layout-sensitive nodes fail | The graph was not cleaned enough | Clean the graph, convert to channels-last, rewrite `Gemm`, then clean again |
| QONNX `Quant` conversion fails | The quantizer parameters are not constant or not in an accepted form | Make `scale`, `zeropt`, and `bitwidth` constant and simplify the graph |

## Quantization-specific issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| QKeras input precision looks wrong | No quantizer near the inputs | Put a `QActivation` with a suitable quantizer near the input path |
| HGQ / HGQ2 / PQuantML conversion ignores hand-edited precision | Model-wise precision propagation is taking over | Let the model's own quantizers drive the result, or disable bit-exact mode explicitly if that is intended |
| `Precision: auto` at the model level does not work | Only layer-level auto precision is supported | Use layer-level granularity or edit the layer precisions manually |
| Narrow fixed-point types reduce accuracy in SNN membrane readout | Membrane accumulation spans the whole window | Widen the readout precision or shorten the window |

## SNN issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| SNN output drifts between runs | The model is stateful across top-level calls | Feed the sequence one timestep at a time and respect the window boundary |
| SNN readout seems off by one window | The wrong window size was used | Keep the `window_size` / `stream_length` consistent from conversion to inference |
| `output_mode='membrane'` rejects the decision rule | Invalid membrane-mode pairing | Use `argmax_membrane` or `binary_logit` |
| SNN backend selection fails | Only the Vitis path is supported for this flow | Keep the SNN route on the Vitis backend |

## Backend boundary issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Conversion config fails before parsing the model | The selected backend is missing its own prerequisites | Treat it as a backend issue and hand off to the backend workflow |
| `compile()` works but build/report fails | Vendor toolchain missing | That is outside the frontend scope |

## Supported-layer inspection

If you are unsure whether a layer is supported, run `scripts/inspect_supported_layers.py` and compare the active registry with the model's layer types.
