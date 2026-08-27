# Darknet API reference

This reference covers the model/configuration API in this script-oriented PyTorch YOLOv3 repo. Use the bundled inspection script for read-only checks before constructing a model or loading weights.

## Public functions and methods

### `parse_cfg(cfgfile)`

- Input: path to a Darknet-style `.cfg` file.
- Output: list of dictionaries, one dictionary per block.
- Parsing behavior:
  - Blank lines and lines whose first character is `#` are skipped.
  - Section headers such as `[net]`, `[convolutional]`, `[route]`, and `[yolo]` become `block["type"]` values.
  - `key=value` lines are stripped around the key and left-stripped around the value; values remain strings until later construction code casts them.
- Validation behavior: minimal. A cfg can parse successfully even when later model construction fails.

### `create_modules(blocks)`

- Input: the parsed block list from `parse_cfg`.
- Output: `(net_info, module_list)`.
  - `net_info` is `blocks[0]`, normally the `[net]` block.
  - `module_list` is an `nn.ModuleList` whose indices correspond to `blocks[1:]`.
- Supported block types in this implementation:
  - `net`: used as metadata; no module is appended for this block.
  - `convolutional`: creates `nn.Conv2d`, optional `nn.BatchNorm2d`, and optional `nn.LeakyReLU(0.1, inplace=True)` for `activation=leaky`.
  - `upsample`: creates nearest-neighbor `nn.Upsample(scale_factor=2, mode="nearest")`.
  - `route`: creates an `EmptyLayer`; routing is computed during `Darknet.forward`.
  - `shortcut`: creates an `EmptyLayer`; residual addition is computed during `Darknet.forward`.
  - `maxpool`: creates `nn.MaxPool2d` or a custom stride-1 maxpool wrapper.
  - `yolo`: creates a `DetectionLayer` storing the selected anchors from the `mask`.
- Unsupported block types: `region` and `reorg` appear in some bundled cfg variants but have no branch in `create_modules`. They trigger the fallback branch, which prints `Something I dunno` and raises `AssertionError`.
- Important side effect: route block `layers` strings are split and stored back into the block dictionaries during construction.

### `Darknet(cfgfile)`

- Constructor signature: `Darknet.__init__(cfgfile)`.
- Construction steps:
  1. Calls `parse_cfg(cfgfile)`.
  2. Calls `create_modules(self.blocks)`.
  3. Initializes `self.header` to a tensor and `self.seen` to `0` for Darknet weight I/O.
- Useful inspection methods:
  - `get_blocks()` returns parsed block dictionaries.
  - `get_module_list()` returns the constructed `nn.ModuleList`.
- Verified constructible default: `cfg/yolov3.cfg` parses to 108 blocks and constructs 107 modules with 3 YOLO detection blocks.

### `Darknet.forward(self, x, CUDA)`

- Signature: `forward(self, x, CUDA)` where `CUDA` is a boolean-like flag passed into prediction transformation.
- Expected input tensor: a batched image tensor shaped like `N x 3 x H x W` after preprocessing by the image-detection flow.
- Execution behavior:
  - Applies convolutional, upsample, and maxpool modules directly.
  - Resolves `route` and `shortcut` blocks from cached intermediate outputs.
  - For each `yolo` block, reads anchors from the `DetectionLayer`, uses `self.net_info["height"]` as the input dimension, reads `classes` from the block, and calls `predict_transform`.
  - Concatenates detections from all YOLO blocks when available; returns `0` if no detections are produced.
- Do not use this sub-skill for image preprocessing, non-max suppression, drawing, or CLI inference; route those tasks to the image-detection sub-skill.

### `load_weights(self, weightfile)`

- Signature: `load_weights(self, weightfile)`.
- Input: local Darknet binary weights file matching the cfg architecture.
- Header behavior:
  - Reads 5 little-endian `int32` values with `np.fromfile(fp, dtype=np.int32, count=5)`.
  - Stores the tensor in `self.header`.
  - Sets `self.seen = self.header[3]`.
- Payload behavior:
  - Reads the remaining bytes as `float32` weights.
  - Iterates through `self.module_list` and only loads `convolutional` blocks.
  - For convolutional blocks with batch normalization, load order is:
    1. batch-norm bias
    2. batch-norm weight
    3. batch-norm running mean
    4. batch-norm running variance
    5. convolution weights
  - For convolutional blocks without batch normalization, load order is:
    1. convolution bias
    2. convolution weights
- Safety notes:
  - The implementation does not perform an early file-size compatibility check.
  - Short or mismatched files typically fail later during tensor reshape/copy.
  - Extra payload values are not explicitly reported.
  - After class-count or filter changes, original pretrained detection-head weights usually no longer match.

### `save_weights(self, savedfile, cutoff=0)`

- Signature: `save_weights(self, savedfile, cutoff=0)`.
- Behavior:
  - Writes `self.header` after updating `header[3]` from `self.seen`.
  - Writes convolutional layers in the same batch-norm/non-batch-norm order described for loading.
- Caution: the `cutoff` argument is accepted, but the provided implementation iterates through the whole `module_list`; do not rely on it for partial weight export unless the code has been patched and verified.

## Safe inspection commands

Use the bundled script for cfg and names checks without downloading weights or running inference:

```bash
python scripts/inspect_darknet_config.py --repo-root <repo-root> --cfg cfg/yolov3.cfg --names data/coco.names
```

To additionally prove that `Darknet(cfgfile)` instantiates in the current runtime:

```bash
python scripts/inspect_darknet_config.py --repo-root <repo-root> --cfg cfg/yolov3.cfg --names data/coco.names --build-model
```

For cfg variants that contain unsupported block types, the script reports the incompatible block types and explains the `Something I dunno`/`AssertionError` construction failure without downloading or loading weights.
