# Sparse layer and network workflows

Use these patterns after checking signatures in [api-reference.md](api-reference.md). The runnable synthetic smoke is [../scripts/layer_smoke.py](../scripts/layer_smoke.py).

## CPU-safe smoke

From this sub-skill directory:

```bash
python scripts/layer_smoke.py --help
python scripts/layer_smoke.py --device cpu
```

The script creates a tiny two-batch 2D `SparseTensor`, runs convolution, max-pooling, transposed convolution on specified coordinates, global pooling, `MinkowskiLinear`, broadcast, pruning, union, and SPMM. It uses no downloads.

## Quick-start sparse classifier

```python
import torch
import torch.nn as nn
import MinkowskiEngine as ME

class SparseClassifier(ME.MinkowskiNetwork):
    def __init__(self, in_channels=3, num_classes=5, D=3):
        super().__init__(D)
        self.net = nn.Sequential(
            ME.MinkowskiConvolution(in_channels, 32, kernel_size=3, stride=1, dimension=D),
            ME.MinkowskiBatchNorm(32),
            ME.MinkowskiReLU(inplace=True),
            ME.MinkowskiConvolution(32, 64, kernel_size=3, stride=2, dimension=D),
            ME.MinkowskiBatchNorm(64),
            ME.MinkowskiReLU(inplace=True),
            ME.MinkowskiGlobalAvgPooling(),
            ME.MinkowskiLinear(64, num_classes, bias=True),
        )
    def forward(self, x):
        return self.net(x)

points = [torch.IntTensor([[0, 0, 0], [1, 0, 0], [0, 1, 1]])]
coords = ME.utils.batched_coordinates(points)
feats = torch.randn(len(coords), 3)
x = ME.SparseTensor(features=feats, coordinates=coords)
logits = SparseClassifier(D=3)(x).F
```

Checklist: `len(coords) == len(feats)`, batched coordinates have `D + 1` columns, every spatial layer has the same `dimension=D`, and losses consume `output.F`.

## Generated versus specified output coordinates

```python
D = 2
stem = ME.MinkowskiConvolution(2, 8, kernel_size=3, stride=1, dimension=D)
down = ME.MinkowskiConvolution(8, 16, kernel_size=2, stride=2, dimension=D)
up = ME.MinkowskiConvolutionTranspose(16, 8, kernel_size=2, stride=2, dimension=D)

skip = stem(x)
z = down(skip)          # generated strided output support
aligned = up(z, skip)   # output support copied from skip
merged = ME.cat(aligned, skip)
```

Accepted target forms are `SparseTensor`, `CoordinateMapKey`, or explicit batched coordinates:

```python
aligned = up(z, skip)
aligned = up(z, skip.coordinate_map_key)
aligned = up(z, explicit_coords)
```

If you insert your own support, keep it in the same coordinate manager graph when possible:

```python
coords_key, _ = x.coordinate_manager.insert_and_map(explicit_coords, tensor_stride=1)
y = stem(x, coords_key)
```

Use coordinate expansion only when you want new candidate sites:

```python
gen = ME.MinkowskiGenerativeConvolutionTranspose(16, 8, kernel_size=2, stride=2, dimension=D)
y_gen = gen(z)
```

## Custom kernels

Cross-shaped kernels reduce high-dimensional volume:

```python
kg = ME.KernelGenerator(
    kernel_size=3,
    stride=1,
    dilation=1,
    region_type=ME.RegionType.HYPER_CROSS,
    dimension=D,
)
conv = ME.MinkowskiConvolution(32, 64, kernel_generator=kg, dimension=D)
```

Custom offsets define exactly which neighbors participate:

```python
offsets = torch.IntTensor([[0, 0, 0], [1, 0, 0], [-1, 0, 0], [0, 1, 0]])
kg = ME.KernelGenerator(
    kernel_size=-1,
    stride=1,
    dilation=1,
    region_type=ME.RegionType.CUSTOM,
    region_offsets=offsets,
    dimension=3,
)
conv = ME.MinkowskiConvolution(16, 16, kernel_generator=kg, dimension=3)
```

Rules: `region_offsets` must be `N x D`; `HYPER_CROSS` needs odd kernel sizes; a supplied `kernel_generator` owns kernel size, stride, and dilation.

## Pooling and up/downsampling

```python
pool = ME.MinkowskiMaxPooling(kernel_size=2, stride=2, dimension=D)
unpool = ME.MinkowskiPoolingTranspose(kernel_size=2, stride=2, dimension=D)

skip = ME.MinkowskiConvolution(4, 8, kernel_size=3, dimension=D)(x)
z = pool(skip)
z_up = unpool(z, skip)
out = ME.cat(z_up, skip)
```

Choose `MinkowskiMaxPooling` for maxima, `MinkowskiAvgPooling` for average over actual sparse contributors, `MinkowskiSumPooling` when you want no sparse-cardinality division, and `MinkowskiPoolingTranspose` for unpooling aligned to target coordinates.

## Global pooling classification head

```python
class GlobalMaxAvgHead(nn.Module):
    def __init__(self, in_channels, num_classes):
        super().__init__()
        self.gmax = ME.MinkowskiGlobalMaxPooling()
        self.gavg = ME.MinkowskiGlobalAvgPooling()
        self.head = nn.Sequential(
            ME.MinkowskiLinear(in_channels * 2, 128, bias=False),
            ME.MinkowskiBatchNorm(128),
            ME.MinkowskiReLU(inplace=True),
            ME.MinkowskiDropout(p=0.2),
            ME.MinkowskiLinear(128, num_classes, bias=True),
        )
    def forward(self, x):
        return self.head(ME.cat(self.gmax(x), self.gavg(x)))
```

For a dense PyTorch tail, use `ME.MinkowskiToFeature()` after global pooling.

## Generative upsampling with pruning

```python
class PrunedUpsample(nn.Module):
    def __init__(self, in_channels, hidden_channels, D):
        super().__init__()
        self.up = ME.MinkowskiGenerativeConvolutionTranspose(
            in_channels, hidden_channels, kernel_size=2, stride=2, dimension=D
        )
        self.refine = nn.Sequential(
            ME.MinkowskiConvolution(hidden_channels, hidden_channels, kernel_size=3, dimension=D),
            ME.MinkowskiBatchNorm(hidden_channels),
            ME.MinkowskiELU(inplace=True),
        )
        self.classifier = ME.MinkowskiConvolution(hidden_channels, 1, kernel_size=1, bias=True, dimension=D)
        self.prune = ME.MinkowskiPruning()
    def forward(self, x, threshold=0.0):
        candidates = self.refine(self.up(x))
        keep = self.classifier(candidates).F.squeeze(1) > threshold
        return self.prune(candidates, keep)
```

The pruning mask must be boolean, length `len(candidates)`, and on the same device as `candidates.F`.

## Broadcast and squeeze-excitation

```python
class SparseSE(nn.Module):
    def __init__(self, channels, reduction=16):
        super().__init__()
        hidden = max(1, channels // reduction)
        self.pool = ME.MinkowskiGlobalAvgPooling()
        self.fc = nn.Sequential(
            ME.MinkowskiLinear(channels, hidden),
            ME.MinkowskiReLU(inplace=True),
            ME.MinkowskiLinear(hidden, channels),
            ME.MinkowskiSigmoid(),
        )
        self.gate = ME.MinkowskiBroadcastMultiplication()
    def forward(self, x):
        return self.gate(x, self.fc(self.pool(x)))
```

Other broadcast variants:

```python
g = ME.MinkowskiGlobalAvgPooling()(x)
x_plus_global = ME.MinkowskiBroadcastAddition()(x, g)
x_times_global = ME.MinkowskiBroadcastMultiplication()(x, g)
x_with_global_channels = ME.MinkowskiBroadcastConcatenation()(x, g)
```

## Union, cat, mean, and var

Use strict feature utilities only for identical supports:

```python
same_support = ME.cat(branch_a, branch_b)
avg_support = ME.mean(branch_a, branch_b)
var_support = ME.var(branch_a, branch_b)
```

Use union for different supports in the same coordinate-manager graph:

```python
b = ME.SparseTensor(features=features_b, coordinates=coords_b, coordinate_manager=a.coordinate_manager)
merged_support = ME.MinkowskiUnion()(a, b)  # overlapping features are summed
```

If you need concatenation after different-support branches, align one branch to the other's coordinates first with a transposed layer call like `up(z, skip)`.

## Interpolation pattern

```python
query_points = torch.tensor([[0.1, 0.2, 0.0], [1.4, 0.5, 0.0]], dtype=torch.float32, device=x.F.device)
queries = ME.utils.batched_coordinates([query_points], dtype=torch.float32, device=x.F.device)
interp = ME.MinkowskiInterpolation(return_kernel_map=True, return_weights=True)
features, (in_map, out_map), weights = interp(x, queries)
```

`features` is a regular `torch.Tensor`. Wrap it back into a `TensorField` or pair it with query coordinates if later code needs coordinate-aware objects.

## Functional wrappers and dense conversion

```python
x = MF.relu(x)
x = MF.dropout(x, p=0.1, training=self.training)
loss = MF.cross_entropy(logits, labels)

dense = torch.randn(2, 4, 16, 16)
sparse_nonzero = ME.to_sparse(dense, format="BCXX")
coords = ME.dense_coordinates(dense.shape)
sparse_all = ME.to_sparse_all(dense, coordinates=coords)
back_to_dense = ME.MinkowskiToDenseTensor(shape=dense.shape)(sparse_all)
```

## SPMM

```python
rows = torch.IntTensor([0, 0, 1, 1])
cols = torch.IntTensor([0, 1, 2, 3])
vals = torch.ones(4, dtype=torch.float32)
mat = torch.randn(4, 8)
out = ME.spmm(rows, cols, vals, torch.Size([2, 4]), mat)
```

Use matching lengths, matching dtype between `vals` and `mat`, and compatible devices. CUDA SPMM requires a CUDA-enabled build and should be verified in the target environment.

## Residual and U-Net blocks

```python
from MinkowskiEngine.modules.resnet_block import BasicBlock

block = BasicBlock(32, 32, stride=1, dilation=1, dimension=D)
y = block(x)

downsample = nn.Sequential(
    ME.MinkowskiConvolution(32, 64, kernel_size=1, stride=2, dimension=D),
    ME.MinkowskiBatchNorm(64),
)
block = BasicBlock(32, 64, stride=2, downsample=downsample, dimension=D)
```

U-Net skip pattern:

```python
enc1 = ME.MinkowskiConvolution(3, 16, kernel_size=3, dimension=D)(x)
enc2 = ME.MinkowskiConvolution(16, 32, kernel_size=2, stride=2, dimension=D)(enc1)
dec1 = ME.MinkowskiConvolutionTranspose(32, 16, kernel_size=2, stride=2, dimension=D)(enc2, enc1)
y = ME.cat(dec1, enc1)
y = ME.MinkowskiConvolution(32, out_channels, kernel_size=1, dimension=D)(y)
```

For squeeze-and-excitation, the explicit `SparseSE` pattern above is safer than relying on a version-specific SE block constructor.

## Performance guidance

- Reuse repeated layer structures. The coordinate manager caches coordinates and kernel maps; repeated convolutions with the same tensor stride, stride, and kernel offsets amortize kernel-map cost.
- Mirror encoder/decoder strides. A transposed layer can reuse a previous kernel map by swapping input and output roles when strides and offsets match.
- In high dimensions, avoid large hyper-cubic kernels. Use `HYPER_CROSS`, custom offsets, or pooling with `kernel_size == stride` when possible.
- Use `kernel_size=1` for pure channel mixing; convolution falls back to matrix multiplication when stride is one.
- Keep sparse tensor construction in the main process when using multiprocessing data loaders; coordinate managers cannot be shared safely across worker processes after construction.
- For variable-size batches, watch peak memory because larger sparse supports trigger new allocations. On CUDA-enabled runs, periodic `torch.cuda.empty_cache()` can reduce allocator fragmentation if validated in the target loop.
- Tune `OMP_NUM_THREADS` on CPU when kernel-map construction oversubscribes cores.
- Avoid unnecessary `expand_coordinates=True`; expanded coordinates can dominate memory before pruning.
