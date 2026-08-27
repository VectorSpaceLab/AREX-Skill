# Troubleshooting sparse layers and networks

## Missing or invalid dimension

Symptoms:

- `Invalid dimension. Please provide a valid dimension argument.`
- A convolution, pooling, or residual block initializes but fails when called.

Fix:

```python
D = 3
layer = ME.MinkowskiConvolution(16, 32, kernel_size=3, dimension=D)
assert x.D == D
```

Every spatial layer in a network should receive the same positive `dimension=D`. Updating a model from 2D to 3D requires changing all spatial layer constructors.

## Channel mismatch

Symptoms:

- `Channel size mismatch ...`
- Dense linear error such as `mat1 and mat2 shapes cannot be multiplied`.
- Residual addition or `ME.cat` fails after a width-changing branch.

Fixes:

- Match `in_channels` to `input.F.shape[1]`.
- Match `MinkowskiLinear(in_features=...)` to the incoming `.F` width.
- Add a projection on residual branches when width or stride changes:

```python
downsample = nn.Sequential(
    ME.MinkowskiConvolution(in_ch, out_ch, kernel_size=1, stride=stride, dimension=D),
    ME.MinkowskiBatchNorm(out_ch),
)
```

## Coordinate manager or coordinate key mismatch

Symptoms:

- `Invalid coordinate manager`
- `Coordinate key different`
- `All inputs must have the same coordinate manager`
- `ME.cat`, `ME.mean`, `ME.var`, broadcast, or union fails even though feature shapes look right.

Rules:

- `ME.cat`, `ME.mean`, `ME.var`, `ME.sum`, and in-place sparse arithmetic require the same device, same coordinate manager, and same coordinate map key.
- `ME.MinkowskiUnion` requires the same coordinate manager but accepts different supports.
- Broadcast expects the global tensor to come from the same coordinate-manager graph, usually via global pooling of the input.

Fix patterns:

```python
# Different support but same graph.
b = ME.SparseTensor(features=fb, coordinates=cb, coordinate_manager=a.coordinate_manager)
merged = ME.MinkowskiUnion()(a, b)

# Skip-aligned transpose so ME.cat is legal.
up = ME.MinkowskiConvolutionTranspose(ch2, ch1, kernel_size=2, stride=2, dimension=D)
y = ME.cat(up(z, skip), skip)
```

## Device mismatch

Symptoms:

- `Device must be the same`
- CPU coordinates/masks are mixed with CUDA features.

Fix:

- Move every participating sparse tensor, mask, and dense SPMM operand to the same device before the call.
- Keep the bundled smoke on CPU unless the target install reports CUDA support and the user explicitly requests GPU execution.

## CPU_ONLY build or unavailable CUDA path

Symptoms:

- Import prints a CPU-only warning.
- `.cuda()` calls or CUDA examples fail while CPU operators work.
- `torch.cuda.is_available()` is true but `ME.is_cuda_available()` is false.

Fix:

- Run CPU workflows and CPU smoke by default.
- Rebuild or install a CUDA-enabled MinkowskiEngine only when GPU execution is required.
- Treat CUDA examples as unverified until they are run on the target CUDA-enabled build.

## Kernel-map cache, expansion, and memory pressure

Symptoms:

- Slow repeated sparse layers.
- Out-of-memory after generative transpose or `expand_coordinates=True`.
- Variable-size batches cause memory spikes.

Fix:

- Reuse repeated convolution blocks with the same tensor stride, stride, and kernel offsets so cached kernel maps can be reused.
- Mirror encoder/decoder strides to let transposed layers reuse maps by swapping input/output roles.
- Prefer pooling with `kernel_size == stride` for efficient hierarchical downsampling when architecture allows.
- In high dimensions, replace large hyper-cubic kernels with `ME.RegionType.HYPER_CROSS` or `CUSTOM` offsets.
- Prune speculative decoder sites soon after generative expansion.
- On CUDA training loops, use `torch.cuda.empty_cache()` only after validating that it helps the target workload.
- Tune `OMP_NUM_THREADS` locally if CPU kernel-map construction oversubscribes cores.

## Custom kernel or interpolation shape problems

Symptoms:

- `region_offset must have the same dimension as the network`.
- `kernel_size must be odd for region_type HYPER_CROSS`.
- Interpolation returns unexpected feature shapes or empty-looking output.

Fix:

- Use `region_offsets` with shape `N x D` and integer dtype for `RegionType.CUSTOM`.
- Use odd `kernel_size` values for `HYPER_CROSS`.
- Use `ME.utils.batched_coordinates(..., dtype=torch.float32)` for interpolation queries and keep them in the same batching convention as the sparse tensor.

## Pruning, union, and SPMM pitfalls

- Pruning masks must be boolean, length `len(input)`, and on the same device as `input.F`.
- `MinkowskiUnion` requires at least two sparse tensors, same coordinate manager, and compatible feature widths; overlapping features are summed.
- `ME.spmm` requires `len(rows) == len(cols) == len(vals)`, `vals.dtype == mat.dtype`, and compatible devices. CPU paths support float32/float64 values.

## Residual or SE block mismatch

Symptoms:

- Residual branch cannot be added back into the main branch.
- SE gate has the wrong feature width.
- Version-specific SE block wrapper constructor names do not match a residual block constructor.

Fix:

- Add a residual projection when width or stride changes.
- For SE-style gating, make the gate output width equal to the input feature width before `MinkowskiBroadcastMultiplication`.
- Prefer an explicit `SELayer`/broadcast pattern when a packaged `SEBasicBlock` constructor has version-specific keyword names.
