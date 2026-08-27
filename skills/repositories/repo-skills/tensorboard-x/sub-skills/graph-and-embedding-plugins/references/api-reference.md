# Graph And Embedding API Reference

This reference covers the tensorboardX methods owned by the graph and projector plugins. Writer construction and log-directory lifecycle are handled by `logging-core`.

## `SummaryWriter.add_graph`

Signature:

```python
add_graph(model, input_to_model=None, verbose=False, use_strict_trace=True)
```

Purpose: add a PyTorch model graph to the event stream. The implementation imports `torch.utils.tensorboard._pytorch_graph.graph` inside the method and then writes the returned graph/profile through the file writer.

Arguments:

- `model`: a `torch.nn.Module` to trace.
- `input_to_model`: one tensor, a tuple of tensors, or a list/tuple structure that matches `model.forward`. Source examples use both a one-element tuple such as `(torch.zeros(1, 3),)` and multiple inputs such as `(x, y)`.
- `verbose`: forwarded to the PyTorch graph helper to print graph structure.
- `use_strict_trace`: forwarded as `use_strict_trace` to the helper, which passes strictness to `torch.jit.trace`; set it to `False` when a model needs mutable container types such as lists or dicts to be traced.

Dependency boundary: `torch` is required for this method. CPU tensors are sufficient when the model is on CPU. If the model or input is on GPU, all participating tensors and parameters must be on the same device.

## `SummaryWriter.add_onnx_graph`

Signature:

```python
add_onnx_graph(onnx_model_file)
```

Purpose: parse an existing ONNX model file into a TensorBoard `GraphDef` and add it to the event stream.

Arguments:

- `onnx_model_file`: path string for a local ONNX model file.

Dependency boundary: the parser imports `onnx` inside `tensorboardX.onnx_graph.load_onnx_graph`. The method does not download a model. Network-downloading demos are intentionally excluded from the runtime skill; provide a local `.onnx` path instead.

Parser behavior:

- Loads the file with `onnx.load`.
- Adds graph inputs and outputs as `Variable` nodes with dtype and shape attributes.
- Adds each ONNX node using the first output name, `op_type`, input names, and serialized attributes.

## `SummaryWriter.add_openvino_graph`

Signature:

```python
add_openvino_graph(xmlname)
```

Purpose: parse an existing OpenVINO IR XML file into a TensorBoard `GraphDef` and add it to the event stream.

Arguments:

- `xmlname`: path string for a local OpenVINO XML model file.

Dependency boundary: this parser uses Python XML parsing and tensorboardX protobuf classes; it does not require the OpenVINO runtime package for basic XML graph parsing.

Parser behavior:

- Parses the XML with `xml.etree.ElementTree`.
- Reads `layers` and maps each layer `id` to its `name`.
- Reads `edges`; each edge creates a node named by the destination layer with an input from the source layer.
- The parser expects the XML to contain `layers`, `edges`, layer `id`/`name`, and edge `from-layer`/`to-layer` attributes.

## `SummaryWriter.add_embedding`

Signature:

```python
add_embedding(mat, metadata=None, label_img=None, global_step=None, tag='default', metadata_header=None)
```

Purpose: write TensorBoard projector files. The implementation writes TSV, PNG, and `projector_config.pbtxt` files under the writer logdir; it is not an event-file summary workflow.

Arguments:

- `mat`: two-dimensional matrix where each row is one data point and each column is a feature dimension. Accepted values include NumPy arrays and PyTorch tensors through `x2num.make_np`.
- `metadata`: optional labels. Without `metadata_header`, each label is stringified as one TSV column. With a header, each metadata row must have the same number of columns as the header.
- `label_img`: optional image tensor/array in `NCHW` layout. `N` must equal the number of matrix rows. Images must be square (`H == W`).
- `global_step`: optional integer. `None` becomes `0`.
- `tag`: embedding name. Slashes, backslashes, and percent signs are encoded for the directory name, while the projector config tensor name uses the raw tag and zero-padded step.
- `metadata_header`: optional list of TSV column names. Its length must equal the number of columns in each metadata row.

Projector files are detailed in [data-formats.md](data-formats.md). Remote upload behavior for `s3://` or `gs://` logdirs belongs to `remote-and-parallel-integrations`.

## Input Conversion Notes

The projector path uses `tensorboardX.x2num.make_np`:

- `list`, NumPy array, scalar, PyTorch tensor, Chainer tensor, MXNet tensor, JAX array, and Paddle array are converted to NumPy-like arrays when the matching package path is available.
- PyTorch tensors are moved to CPU before conversion with `.cpu().numpy()`.
- The conversion warns if the sum of the converted array is NaN or infinite, then returns the data unchanged.

For graph tracing, `add_graph` delegates to PyTorch; tensorboardX does not coerce devices or repair mismatched input shapes.