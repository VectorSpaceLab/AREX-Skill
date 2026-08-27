# Graph And Projector Workflows

These workflows assume a `SummaryWriter` already exists or will be created for a local log directory. For writer lifecycle choices, use `logging-core`.

## PyTorch CPU Graph Workflow

Use this when the user wants to visualize a `torch.nn.Module` graph.

1. Ensure `torch` is installed and importable.
2. Put the model in a trace-friendly state. For most inference-style graph captures, call `model.eval()` so stochastic layers such as dropout do not vary during tracing.
3. Create representative CPU input tensors with shapes that match `forward`.
4. Wrap multiple inputs in a tuple matching the forward signature.
5. Call `writer.add_graph(model, input_to_model, verbose=False)`.
6. Flush or close the writer through the lifecycle guidance in `logging-core`.

Minimal shape:

```python
class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(3, 2)
    def forward(self, x):
        return self.linear(x)

writer.add_graph(Tiny().eval(), (torch.zeros(1, 3),))
```

CPU is enough for this workflow. Use GPU only when the user's actual model/tensors require it; then move both the model and every input tensor to the same device before calling `add_graph`.

### Multiple Inputs And Outputs

Supported patterns include:

- one input tuple: `(torch.zeros(1, 3),)`;
- multiple inputs: `(torch.zeros(1, 3), torch.zeros(1, 3))` for `forward(self, x, y)`;
- multiple outputs: returning tuples from `forward`;
- shared-module outputs where the same layer appears in more than one returned branch.

If tracing fails for a tuple/list/dict-heavy model, try `use_strict_trace=False` when the model legitimately uses mutable containers during tracing.

## ONNX Graph Workflow

Use this only for a local ONNX file that already exists.

1. Confirm the file path points to a local `.onnx` file.
2. Confirm the `onnx` Python package is installed.
3. Call `writer.add_onnx_graph(path_to_model)`.
4. Flush or close through `logging-core`.

Do not ask future agents to download the ONNX model zoo or run a network-downloading demo. If the user needs ONNX export from PyTorch, perform export as a separate user task, then pass the resulting local file to tensorboardX.

## OpenVINO XML Graph Workflow

Use this for an existing OpenVINO IR XML graph.

1. Confirm the XML file exists and is readable.
2. Confirm it has `layers` and `edges` sections.
3. Call `writer.add_openvino_graph(path_to_xml)`.
4. Flush or close through `logging-core`.

The tensorboardX parser does not require OpenVINO runtime for basic XML parsing, but it does require a structurally valid XML graph with layer ids/names and edges. A standalone `.bin` weights file is not used by this parser.

## Embedding Projector Workflow

Use this when the user wants TensorBoard's projector tab.

1. Prepare a 2D feature matrix `mat` with shape `(N, D)`.
2. Optionally prepare `metadata` with exactly `N` labels or rows.
3. If `metadata_header` is provided, make every metadata row a sequence with the same number of columns as the header.
4. Optionally prepare `label_img` in `NCHW` layout with exactly `N` images and square patches (`H == W`). Single-channel image batches are expanded to RGB by the sprite helper; three-channel image batches are already RGB-like.
5. Choose `global_step` and `tag`. Use distinct combinations for multiple embeddings to avoid duplicate directory warnings.
6. Call `writer.add_embedding(mat, metadata=..., label_img=..., global_step=..., tag=..., metadata_header=...)`.
7. Inspect the generated projector files using [data-formats.md](data-formats.md) if TensorBoard does not show the embedding.

Example pattern:

```python
features = numpy.array([[0.0, 0.1], [1.0, 1.1], [2.0, 2.1]], dtype=numpy.float32)
metadata = [("zero", "train"), ("one", "train"), ("two", "valid")]
labels = numpy.zeros((3, 3, 4, 4), dtype=numpy.float32)
writer.add_embedding(
    features,
    metadata=metadata,
    metadata_header=["name", "split"],
    label_img=labels,
    global_step=7,
    tag="demo",
)
```

## Bundled Smoke Checks

Run the bundled scripts as local sanity checks for tensorboardX plugin behavior:

- `python sub-skills/graph-and-embedding-plugins/scripts/tbx_graph_smoke.py`
- `python sub-skills/graph-and-embedding-plugins/scripts/tbx_projector_smoke.py`
- `python sub-skills/graph-and-embedding-plugins/scripts/tbx_onnx_openvino_smoke.py --onnx-path /path/to/model.onnx`

The ONNX path is optional. Without it, the combined ONNX/OpenVINO smoke still checks a generated minimal OpenVINO XML and reports that ONNX was skipped.