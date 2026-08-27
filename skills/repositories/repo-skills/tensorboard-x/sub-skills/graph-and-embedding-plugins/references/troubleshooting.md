# Graph And Projector Troubleshooting

## `add_graph` Fails To Import Torch

Symptom: `ModuleNotFoundError` or import failure from `torch` or `torch.utils.tensorboard._pytorch_graph`.

Cause: `add_graph` depends on PyTorch and imports the graph helper inside the method.

Fix:

- Install a PyTorch build suitable for the user's runtime.
- CPU PyTorch is sufficient unless the user deliberately needs GPU tensors.
- Do not install GPU packages just to use the graph plugin on a CPU model.

## PyTorch Tracing Or Forward Pass Fails

Symptoms: runtime errors during `writer.add_graph`, wrong input-size errors, missing positional arguments, or exceptions from `forward`.

Likely causes and fixes:

- Input shape does not match the module. Create a representative tensor with the exact batch/channel/feature dimensions expected by `forward`.
- Multiple inputs are not wrapped correctly. For `forward(self, x, y)`, pass `(x, y)`, not only `x`.
- A one-tensor model receives an ambiguous input. Use a one-element tuple `(x,)` when in doubt.
- The model has data-dependent Python control flow that tracing cannot represent reliably. Consider simplifying the trace path or use a representative branch; tensorboardX delegates this behavior to PyTorch tracing.
- The model uses mutable containers. Try `use_strict_trace=False` when list/dict mutation is expected and safe for the visualization goal.
- Training-mode stochastic layers create unstable traces. Use `model.eval()` for graph capture unless the user explicitly wants training behavior.

## CPU/GPU Tensor Mismatch

Symptom: PyTorch reports tensors or parameters are on different devices.

Fix:

- For a normal tensorboardX graph visualization, keep both model and inputs on CPU.
- If the user intentionally uses GPU, move the model and all inputs to the same device before `add_graph`.
- tensorboardX does not perform device reconciliation for graph tracing.

## ONNX Package Missing

Symptom: `ModuleNotFoundError: No module named 'onnx'` from `add_onnx_graph`.

Fix:

- Install the `onnx` Python package in the current runtime.
- Re-run with a local model path.
- Do not rely on network download demos or ONNX model zoo fetches in this skill.

## ONNX File Or Parse Problems

Symptoms: file-not-found errors, invalid protobuf/model errors, or parser failures.

Fix:

- Pass a local `.onnx` path, not a URL.
- Confirm the file was exported successfully and can be loaded by `onnx.load`.
- If the source model is PyTorch, debug PyTorch-to-ONNX export separately before calling `add_onnx_graph`.
- Avoid using source demos that download archives; they are intentionally excluded from runtime guidance.

## OpenVINO XML Parse Failures

Symptoms: XML parse errors, `NoneType` iteration errors, missing-key errors for `id`, `name`, `from-layer`, or `to-layer`, or key errors resolving edge ids.

Likely causes:

- The XML file is missing a `layers` section.
- The XML file is missing an `edges` section.
- A `layer` lacks an `id` or `name` attribute.
- An `edge` lacks `from-layer` or `to-layer`.
- An edge references a layer id not present in the layers map.

Fix:

- Use a complete local OpenVINO IR XML graph.
- Validate the XML structure before passing it to `add_openvino_graph`.
- The parser does not need or read a `.bin` weights file for graph visualization.

## Embedding Matrix Problems

Symptoms: `mat should be 2D` assertion, malformed `tensors.tsv`, or TensorBoard projector cannot find the tensor.

Fix:

- Ensure `mat` has shape `(N, D)`, not `(N,)` or `(N, C, H, W)`.
- Convert high-dimensional activations to feature vectors before logging, for example by pooling or flattening outside tensorboardX.
- Watch for NaN/Inf warnings from `x2num.make_np`; clean the input features if TensorBoard behaves unexpectedly.

## Metadata Row Count Or Header Mismatch

Symptoms: `#labels should equal with #data points` or `len of header must be equal to the number of columns in metadata` assertions.

Fix:

- Make `len(metadata) == mat.shape[0]`.
- Without a header, pass a simple list of labels if one metadata column is enough.
- With a header, pass row-like metadata such as tuples/lists and ensure every row has exactly `len(metadata_header)` columns.
- Keep the header as a list of column names, not a string.

## Label Image Mismatch Or Sprite Failure

Symptoms: `#images should equal with #data points`, `Image should be square`, or `Sprite too large` assertions.

Fix:

- Make `label_img.shape[0] == mat.shape[0]`.
- Use `NCHW` layout: batch, channels, height, width.
- Make every image patch square: `H == W`.
- Reduce `N` or image size if the generated sprite side would exceed `8192` pixels.
- Route general image-summary formatting issues to `rich-media-summaries`; this guidance only covers projector label images.

## Duplicate Embedding Directory Warning

Symptom: tensorboardX prints `warning: Embedding dir exists, did you set global_step for add_embedding()?`.

Cause: the destination directory for the same zero-padded `global_step` and encoded `tag` already exists.

Fix:

- Use a new `global_step` or `tag` for each projector snapshot.
- If repeating the same step is intentional, remove or archive the old projector subdirectory before writing, according to the user's logdir lifecycle policy from `logging-core`.

## Projector Files Exist But TensorBoard Does Not Show The Entry

Check:

- `projector_config.pbtxt` exists in the writer logdir.
- The config has an `embeddings` block for the expected `tag:step`.
- `tensor_path` points to the generated `tensors.tsv` relative to the logdir.
- `metadata_path` exists when metadata is configured.
- `sprite.image_path` exists when label images are configured.
- The tag did not encode path separators unexpectedly in the directory name; see [data-formats.md](data-formats.md).

For remote S3/GCS paths, route credential, upload, and bucket behavior to `remote-and-parallel-integrations`.