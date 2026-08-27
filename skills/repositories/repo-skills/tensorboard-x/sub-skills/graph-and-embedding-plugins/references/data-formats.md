# Graph And Projector Data Formats

## PyTorch Graph Inputs

`add_graph` forwards its inputs to PyTorch's TensorBoard graph helper.

- Pass a `torch.nn.Module` instance as `model`.
- Pass `input_to_model` in the same structure expected by `forward`.
- For one tensor argument, a one-element tuple such as `(x,)` is a safe pattern.
- For `forward(self, x, y)`, pass `(x, y)`.
- Use CPU tensors unless the user deliberately traces a GPU model; tensorboardX does not move graph-tracing tensors between devices.

Shape mismatches are surfaced by PyTorch tracing. For example, passing a `(1, 9)` tensor into a linear layer expecting three features raises a runtime error.

## ONNX Graph Files

`add_onnx_graph` expects a local ONNX model file path. The parser reads:

- graph inputs and outputs with tensor dtype and shape;
- graph nodes with `op_type`, input names, first output name, and attributes.

Known boundaries:

- The method imports `onnx`; missing package errors must be resolved by installing ONNX in the user's runtime.
- The method does not download a model and should not be pointed at a URL.
- The source network-downloading demo is intentionally not bundled.

## OpenVINO XML Graph Files

`add_openvino_graph` expects a local OpenVINO IR XML path. The parser uses:

- root `layers` element;
- child `layer` elements with `id` and `name` attributes;
- root `edges` element;
- child `edge` elements with `from-layer` and `to-layer` attributes.

It maps layer ids to names and creates TensorBoard nodes from edges. Missing `layers`, missing `edges`, missing layer ids/names, or edges that refer to unknown ids can fail parsing. The parser does not inspect a `.bin` weights file.

## Projector Output Layout

`add_embedding` writes a projector-specific file tree under the writer logdir. It does not add a normal event summary.

For `global_step=7` and `tag="demo"`, the directory layout is:

```text
<logdir>/projector_config.pbtxt
<logdir>/00007/demo/tensors.tsv
<logdir>/00007/demo/metadata.tsv        # only when metadata is provided
<logdir>/00007/demo/sprite.png          # only when label_img is provided
```

If `global_step` is omitted, tensorboardX uses `0`, so the step directory is `00000`.

Tag encoding for directories:

- `%` becomes `%25`;
- `/` becomes `%2f`;
- `\` becomes `%5c`.

The `projector_config.pbtxt` entry uses the raw `tag` and zero-padded global step in `tensor_name`, for example `tensor_name: "demo:00007"`. It stores `tensor_path`, optional `metadata_path`, and optional `sprite` fields using paths relative to the logdir.

## Projector Matrix Contract

`mat` must be two-dimensional with shape `(N, D)`:

- `N`: number of data points;
- `D`: feature dimensions.

The generated `tensors.tsv` contains one row per data point and tab-separated feature values. The implementation asserts `mat.ndim == 2` after optional metadata and label-image processing.

## Metadata Contract

Without `metadata_header`:

- `metadata` length must equal `N`;
- each metadata item is converted to a string;
- `metadata.tsv` has one string column per data point.

With `metadata_header`:

- `metadata` length must equal `N`;
- every metadata row must have the same number of columns as the header;
- the first line of `metadata.tsv` is the tab-separated header;
- subsequent lines are tab-separated metadata rows.

Example:

```python
metadata = [("cat", "train"), ("dog", "valid")]
metadata_header = ["class", "split"]
```

A header length mismatch raises an assertion error before writing a valid metadata TSV.

## Label Image Sprite Contract

`label_img` is only the projector label-image path, not the general image-summary API.

Required shape: `(N, C, H, W)`.

Constraints:

- `N` must equal the number of rows in `mat`.
- `H` must equal `W`; non-square patches raise an assertion.
- The generated sprite image must fit TensorBoard's frontend limit. tensorboardX enforces a maximum sprite side length of `8192`.
- Source comments state TensorBoard expects both the full sprite and each image patch to be square. The helper pads on the bottom when making the full square sprite, not on the right, because TensorBoard interprets right padding as extra images.
- One-channel batches are expanded to three channels by the grid helper. Three-channel batches are the normal RGB case.

The generated `projector_config.pbtxt` includes:

```text
sprite {
  image_path: "00007/demo/sprite.png"
  single_image_dim: <W>
  single_image_dim: <H>
}
```

## Duplicate Directory Warning

`add_embedding` creates the destination directory from `global_step` and `tag`. If it already exists, tensorboardX prints:

```text
warning: Embedding dir exists, did you set global_step for add_embedding()?
```

Use unique `global_step`/`tag` pairs for separate projector entries unless overwriting is intentional and understood.