# MinkowskiEngine layer and network API reference

The APIs below are exposed from `import MinkowskiEngine as ME` unless an explicit module import is shown. Signatures reflect the inspected 0.5.x Python API plus live CPU signature probes for key classes. CUDA execution depends on the user's installed build and is not claimed by the bundled CPU smoke.

## Input contracts used by the examples

```python
import torch
import torch.nn as nn
import MinkowskiEngine as ME
import MinkowskiEngine.MinkowskiFunctional as MF

D = 3
coords = ME.utils.batched_coordinates([torch.IntTensor([[0, 0, 0], [1, 0, 0]])])
feats = torch.randn(len(coords), 4)
x = ME.SparseTensor(features=feats, coordinates=coords)
```

- `ME.SparseTensor(features, coordinates=None, tensor_stride=1, coordinate_map_key=None, coordinate_manager=None, quantization_mode=..., allocator_type=None, minkowski_algorithm=None, requires_grad=None, device=None)` is the normal sparse-layer input.
- `ME.TensorField(features, coordinates=None, tensor_stride=1, coordinate_field_map_key=None, coordinate_manager=None, quantization_mode=..., allocator_type=None, minkowski_algorithm=None, requires_grad=None, device=None)` can feed wrappers such as `MinkowskiLinear`, `MinkowskiBatchNorm`, nonlinearities, and field-to-sparse workflows.
- Prefer `ME.utils.batched_coordinates(...)` or `ME.utils.sparse_collate(...)`. In this API, the collation utility prepends the batch index.

## Convolution family

| API | Signature | Use |
| --- | --- | --- |
| `ME.MinkowskiConvolution` | `(in_channels, out_channels, kernel_size=-1, stride=1, dilation=1, bias=False, kernel_generator=None, expand_coordinates=False, convolution_mode=DEFAULT, dimension=None)` | Sparse convolution from input support to generated or supplied output support. |
| `ME.MinkowskiConvolutionTranspose` | `(in_channels, out_channels, kernel_size=-1, stride=1, dilation=1, bias=False, kernel_generator=None, expand_coordinates=False, convolution_mode=DEFAULT, dimension=None)` | Sparse transposed convolution/up-convolution. |
| `ME.MinkowskiGenerativeConvolutionTranspose` | `(in_channels, out_channels, kernel_size=-1, stride=1, dilation=1, bias=False, kernel_generator=None, convolution_mode=DEFAULT, dimension=None)` | Transposed convolution that always expands coordinates for generative decoding. |
| `ME.MinkowskiChannelwiseConvolution` | `(in_channels, kernel_size=-1, stride=1, dilation=1, bias=False, kernel_generator=None, dimension=-1)` | Depthwise/channelwise sparse convolution; output width equals input width. |

Forward calls accept output-coordinate control:

```python
conv = ME.MinkowskiConvolution(4, 16, kernel_size=3, stride=2, dimension=D)
y = conv(x)                            # generated strided coordinates

up = ME.MinkowskiConvolutionTranspose(16, 4, kernel_size=2, stride=2, dimension=D)
y_aligned = up(y, x)                   # output support copied from x
y_key = up(y, x.coordinate_map_key)    # equivalent key form
y_coords = up(y, explicit_coords)      # explicit batched IntTensor coordinates
```

Rules:

- `dimension` must be positive and must match `input.D`.
- If a `kernel_generator` is supplied, the layer ignores layer-level `kernel_size`, `stride`, and `dilation`.
- `kernel_size == 1` with unit stride uses a matrix-multiplication fast path.
- `expand_coordinates=True` creates the outer product of kernel offsets and input coordinates. Use intentionally because it can grow the active support.
- Even-sized kernels use offsets in `[0, K)^D` rather than symmetric centered offsets.

## Kernel generator and custom regions

```python
kg = ME.KernelGenerator(
    kernel_size=3,
    stride=1,
    dilation=1,
    is_transpose=False,
    region_type=ME.RegionType.HYPER_CUBE,
    region_offsets=None,
    expand_coordinates=False,
    axis_types=None,
    dimension=D,
)
```

Common region choices:

- `ME.RegionType.HYPER_CUBE`: default hyper-cubic kernel, volume `prod(kernel_size)`.
- `ME.RegionType.HYPER_CROSS`: cross-shaped kernel; kernel sizes must be odd; useful to reduce high-dimensional kernel volume.
- `ME.RegionType.CUSTOM`: pass `region_offsets=torch.IntTensor([[...], ...])` with shape `N x D`.
- `ME.RegionType.HYBRID`: per-axis region composition through `axis_types`; verify on the target version before relying on it.

Custom-offset example:

```python
offsets = torch.IntTensor([[0, 0, 0], [1, 0, 0], [-1, 0, 0]])
kg = ME.KernelGenerator(
    kernel_size=-1,
    stride=1,
    dilation=1,
    region_type=ME.RegionType.CUSTOM,
    region_offsets=offsets,
    dimension=3,
)
conv = ME.MinkowskiConvolution(8, 16, kernel_generator=kg, dimension=3)
```

## Pooling and global pooling

| API | Signature | Use |
| --- | --- | --- |
| `ME.MinkowskiAvgPooling` | `(kernel_size=-1, stride=1, dilation=1, kernel_generator=None, dimension=None)` | Average over actual sparse contributors; cardinality can vary by output site. |
| `ME.MinkowskiSumPooling` | `(kernel_size, stride=1, dilation=1, kernel_generator=None, dimension=None)` | Sum contributors without sparse-cardinality division. |
| `ME.MinkowskiMaxPooling` | `(kernel_size, stride=1, dilation=1, kernel_generator=None, dimension=None)` | Channel-wise max over sparse neighbors. |
| `ME.MinkowskiPoolingTranspose` | `(kernel_size, stride, dilation=1, kernel_generator=None, expand_coordinates=False, dimension=None)` | Sparse unpooling/up-sampling; can be aligned to target coordinates. |
| `ME.MinkowskiGlobalPooling` | `(mode=ME.PoolingMode.GLOBAL_AVG_POOLING_PYTORCH_INDEX)` | Batch-wise reduction to one origin coordinate per batch. |
| `ME.MinkowskiGlobalSumPooling` | `(mode=ME.PoolingMode.GLOBAL_SUM_POOLING_PYTORCH_INDEX)` | Global sum. |
| `ME.MinkowskiGlobalAvgPooling` | `(mode=ME.PoolingMode.GLOBAL_AVG_POOLING_PYTORCH_INDEX)` | Global average. |
| `ME.MinkowskiGlobalMaxPooling` | `(mode=ME.PoolingMode.GLOBAL_MAX_POOLING_PYTORCH_INDEX)` | Global max. |

```python
pool = ME.MinkowskiMaxPooling(kernel_size=2, stride=2, dimension=D)
z = pool(x)
unpool = ME.MinkowskiPoolingTranspose(kernel_size=2, stride=2, dimension=D)
z_aligned = unpool(z, x)
```

Pooling with `kernel_size == stride` has a trivial map and is often faster for hierarchical downsampling.

## Broadcast operations

```python
g = ME.MinkowskiGlobalAvgPooling()(x)
add = ME.MinkowskiBroadcastAddition()(x, g)
mul = ME.MinkowskiBroadcastMultiplication()(x, g)
copy = ME.MinkowskiBroadcast()(x, g)
cat = ME.MinkowskiBroadcastConcatenation()(x, g)
```

- The second argument should be a reduced/global `SparseTensor` in the same coordinate-manager graph.
- Addition and multiplication keep the input feature width; concatenation appends global feature channels.

## Normalization, nonlinearities, and linear layers

| API | Signature | Notes |
| --- | --- | --- |
| `ME.MinkowskiBatchNorm` | `(num_features, eps=1e-5, momentum=0.1, affine=True, track_running_stats=True)` | Wraps `torch.nn.BatchNorm1d` on `.F`; preserves `SparseTensor`/`TensorField` wrapper. |
| `ME.MinkowskiSyncBatchNorm` | `(num_features, eps=1e-5, momentum=0.1, affine=True, track_running_stats=True, process_group=None)` | Distributed synchronized batch norm; verify target distributed/CUDA runtime first. |
| `ME.MinkowskiInstanceNorm` | `(num_features)` | Instance normalization for `SparseTensor`. |
| `ME.MinkowskiStableInstanceNorm` | `(num_features)` | Alternative instance norm built from global pooling and broadcast primitives. |
| `ME.MinkowskiLinear` | `(in_features, out_features, bias=True)` | Applies `torch.nn.Linear` to `.F` and preserves sparse/field coordinates. |

Nonlinearity/dropout modules wrap the corresponding `torch.nn` module on `.F`: `MinkowskiReLU`, `MinkowskiLeakyReLU`, `MinkowskiELU`, `MinkowskiPReLU`, `MinkowskiGELU`, `MinkowskiSELU`, `MinkowskiCELU`, `MinkowskiSigmoid`, `MinkowskiSiLU`, `MinkowskiTanh`, `MinkowskiSoftmax`, `MinkowskiLogSoftmax`, `MinkowskiDropout`, `MinkowskiAlphaDropout`, threshold and hard/soft shrink variants. Pass normal PyTorch constructor args, for example `ME.MinkowskiReLU(inplace=True)`.

`ME.MinkowskiSinusoidal(in_channel, out_channel)` applies a learned sinusoidal feature transform and preserves coordinates.

## Pruning, interpolation, and union

```python
keep = scores.F.squeeze(-1) > 0
x_kept = ME.MinkowskiPruning()(x, keep)  # True entries are kept
```

- `ME.MinkowskiPruning()` expects a boolean mask with length `len(input)` on the same device.

```python
queries = ME.utils.batched_coordinates([query_points], dtype=torch.float32, device=x.device)
interp = ME.MinkowskiInterpolation(return_kernel_map=True, return_weights=True)
out_feat, (in_map, out_map), weights = interp(x, queries)
```

- `ME.MinkowskiInterpolation(return_kernel_map=False, return_weights=False)` returns a plain feature `torch.Tensor`; optional outputs are kernel maps and interpolation weights.

```python
y = ME.MinkowskiUnion()(x_a, x_b, x_c)
```

- `ME.MinkowskiUnion()` requires at least two `SparseTensor` inputs in the same coordinate manager graph. It returns union coordinates and sums overlapping features; channel widths must be compatible.

## Sparse feature utilities and dense conversion

| API | Signature | Use |
| --- | --- | --- |
| `ME.cat` | `(*sparse_tensors)` | Concatenate features for identical supports. |
| `ME.sum` | `(*sparse_tensors)` | Elementwise feature sum for identical supports. |
| `ME.mean` | `(*sparse_tensors)` | Elementwise feature mean for identical supports. |
| `ME.var` | `(*sparse_tensors)` | Elementwise feature variance for identical supports. |
| `ME.dense_coordinates` | `(shape)` | Build reusable coordinates for a dense `B x C x spatial...` tensor. |
| `ME.to_sparse` | `(x, format=None, coordinates=None, device=None)` | Convert a dense batched tensor to sparse using non-zero spatial positions. |
| `ME.to_sparse_all` | `(dense_tensor, coordinates=None)` | Convert all dense spatial positions to sparse. |
| `ME.MinkowskiToSparseTensor` | `(remove_zeros=True, coordinates=None)` | Module wrapper for dense tensor or `TensorField` to `SparseTensor`. |
| `ME.MinkowskiToDenseTensor` | `(shape=None)` | Module wrapper for sparse-to-dense conversion. |
| `ME.MinkowskiToFeature` | `()` | Extract `.F` as a regular tensor. |
| `ME.MinkowskiStackCat/Sum/Mean/Var` | `(*modules)` | Run branches on the same input and aggregate sparse outputs. |

`ME.cat`, `ME.mean`, `ME.var`, and `ME.sum` are strict: same device, same coordinate manager, and same coordinate map key/field key.

## Functional wrappers

`MinkowskiEngine.MinkowskiFunctional` applies `torch.nn.functional` to `.F` and rewraps feature transforms:

```python
x = MF.relu(x, inplace=False)
x = MF.dropout(x, p=0.2, training=self.training)
x = MF.linear(x, weight, bias)
loss = MF.cross_entropy(logits, labels)  # loss wrappers return regular tensors
```

Feature-preserving wrappers include activations, softmax/log-softmax, normalization, linear, and dropout. Loss wrappers include `cross_entropy`, `mse_loss`, `l1_loss`, `nll_loss`, `binary_cross_entropy`, and related PyTorch functional losses.

## Sparse matrix multiplication

```python
rows = torch.IntTensor([0, 0, 1, 1])
cols = torch.IntTensor([0, 1, 2, 3])
vals = torch.ones(4, dtype=torch.float32)
mat = torch.randn(4, 3)
out = ME.spmm(rows, cols, vals, torch.Size([2, 4]), mat, is_sorted=False)
```

- `ME.spmm(rows, cols, vals, size, mat, is_sorted=False, cuda_spmm_alg=1)` returns shape `(size[0], mat.shape[1])`.
- `from MinkowskiEngine.sparse_matrix_functions import spmm_average` exposes averaging SPMM when needed; it returns `(result, COO, vals)`.
- `MinkowskiSPMMFunction` and `MinkowskiSPMMAverageFunction` expose autograd `Function` wrappers. Use float32 or float64 and keep all operands on compatible devices.

## Network and residual modules

```python
class Net(ME.MinkowskiNetwork):
    def __init__(self, in_channels, out_channels, D):
        super().__init__(D)
        self.net = nn.Sequential(
            ME.MinkowskiConvolution(in_channels, 32, kernel_size=3, dimension=D),
            ME.MinkowskiBatchNorm(32),
            ME.MinkowskiReLU(inplace=True),
            ME.MinkowskiGlobalAvgPooling(),
            ME.MinkowskiLinear(32, out_channels),
        )
    def forward(self, x):
        return self.net(x)
```

- `ME.MinkowskiNetwork(D)` stores the spatial dimension and requires `forward`.
- `MinkowskiEngine.modules.resnet_block.BasicBlock(inplanes, planes, stride=1, dilation=1, downsample=None, bn_momentum=0.1, dimension=-1)` composes two sparse convolutions with batch norm and residual addition.
- `MinkowskiEngine.modules.resnet_block.Bottleneck(inplanes, planes, stride=1, dilation=1, downsample=None, bn_momentum=0.1, dimension=-1)` uses 1x1, 3x3, 1x1 sparse convolutions and expansion `4`.
- `MinkowskiEngine.modules.senet_block.SELayer(channel, reduction=16, D=-1)` uses global pooling, `MinkowskiLinear`, sigmoid, and broadcast multiplication for squeeze-and-excitation.
- SE block wrappers exist, but prefer verifying their constructor names on the target install or composing `SELayer` into a known-good residual block.
