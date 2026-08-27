# Model inference troubleshooting

## Import fails with a missing COCO label map

Symptom:

```text
FileNotFoundError: ... data/coco/coco_labels.txt
```

Why it happens:

- `ssd.py` imports `from data import voc, coco`.
- `data/__init__.py` imports the COCO dataset module.
- The COCO dataset class has a default `target_transform=COCOAnnotationTransform()` argument.
- Constructing that default opens the COCO label-map file at import time.

This can break VOC-only model construction even when you do not plan to use COCO.

Safe remedies:

1. Put the expected `coco_labels.txt` file in the configured COCO data directory for the runtime user.
2. Patch the COCO dataset constructor to use `target_transform=None` as the default and instantiate `COCOAnnotationTransform()` inside `__init__` only when needed.
3. For narrow inspection scripts, load the specific file you need without importing the package-level `data` module, or run in a controlled environment where the label map exists.

Do not hide this failure by claiming `ssd` always imports cleanly.

## `build_ssd` returns `None`

Likely causes:

- `phase` was not exactly `'train'` or `'test'`.
- `size` was not exactly `300`.

The repository prints an error and returns `None`; it does not raise an exception. Always check the result before calling methods on it:

```python
net = build_ssd(phase, size, num_classes)
if net is None:
    raise ValueError('unsupported phase or size')
```

## State-dict loading mismatch

Common symptoms:

```text
Missing key(s) in state_dict
Unexpected key(s) in state_dict
size mismatch for conf.*.weight
size mismatch for conf.*.bias
```

Checks:

- Confirm `num_classes` matches the weight file. VOC weights require `num_classes=21`.
- Confirm the checkpoint was saved for the same SSD300 architecture.
- Strip `module.` prefixes if the checkpoint came from `DataParallel`.
- Use `map_location='cpu'` when loading GPU-trained weights on CPU.
- Do not use `strict=False` as a first response for confidence-head mismatches; that may leave randomly initialized heads while making the load look successful.

Minimal prefix-strip pattern:

```python
state = torch.load(weight_path, map_location='cpu')
if any(k.startswith('module.') for k in state):
    state = {k.removeprefix('module.'): v for k, v in state.items()}
net.load_state_dict(state)
```

## Test-phase forward fails on modern PyTorch

Symptom:

```text
Legacy autograd function with non-static forward method is deprecated
```

Cause:

- `Detect` subclasses `torch.autograd.Function` but defines an instance `forward` method. Modern PyTorch expects new-style autograd functions with static methods and `.apply(...)`, or ordinary modules/callables for non-gradient inference code.

Resolution options:

1. Port `Detect` to a regular non-gradient callable/module and keep the existing decode/NMS tensor logic.
2. Port it to a new-style autograd function if you specifically need autograd-function semantics.
3. Use a legacy-compatible PyTorch runtime.
4. Avoid `phase='test'` and inspect `phase='train'` raw outputs plus custom decode/NMS.

Do not promise evaluation, demo, or live inference works on a modern runtime until this is resolved.

## `center_size` raises a `torch.cat` TypeError

Symptom:

```text
TypeError: cat() takes from 1 to 2 positional arguments but 3 were given
```

Cause:

- The source `center_size` helper is intended to concatenate `(cxcy, wh)` but passes the tensors as separate positional arguments to `torch.cat` under modern PyTorch.

Resolution:

- Patch the helper in a local working copy to compute `cxcy = (boxes[:, 2:] + boxes[:, :2]) / 2`, `wh = boxes[:, 2:] - boxes[:, :2]`, then return `torch.cat((cxcy, wh), 1)`.
- If you only need encode/decode/NMS checks, use the bundled `check_box_utils.py`; it reports this known issue as a warning and continues validating the other utility paths.

## Tensor device and default-type issues

Legacy scripts sometimes use:

```python
torch.set_default_tensor_type('torch.cuda.FloatTensor')
```

This can make newly created tensors CUDA tensors by default and cause confusing CPU/GPU mismatches in helper code or postprocessing.

Prefer explicit devices:

```python
device = torch.device('cuda' if use_cuda and torch.cuda.is_available() else 'cpu')
net.to(device)
x = x.to(device)
scale = torch.tensor([width, height, width, height], device=device, dtype=x.dtype)
```

If using `Detect`, also ensure the output tensor and input tensors are created on compatible devices after any patch. The original `Detect.forward` creates `torch.zeros(...)` without explicitly using `loc_data.device`, so a modern patch should allocate with the input device and dtype.

## Prior or output shape is not `8732`

Expected SSD300 prior count is `8732` for both VOC and COCO configs. If you see a different count:

- Verify `size=300` and the repository's SSD300 config was not edited.
- Verify feature-map sizes are `[38, 19, 10, 5, 3, 1]`.
- Verify `mbox['300']` is `[4, 6, 6, 6, 4, 4]`.
- Verify preprocessing resizes to exactly 300 x 300.

If `conf` shape is `(batch, 8732, N)` where `N` is not what you expected, inspect the `num_classes` argument used to construct the model.

## `Variable(..., volatile=True)` warning

Modern PyTorch ignores the old `volatile` argument and may warn during construction. This warning was observed during train-phase construction/forward and is not the same as the `Detect` forward failure. Use `with torch.no_grad():` for inference-style code in modern PyTorch.
