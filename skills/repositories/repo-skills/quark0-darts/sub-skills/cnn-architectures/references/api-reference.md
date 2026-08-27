# CNN architecture and API reference

This reference captures the convolutional DARTS model/search API facts future agents need without reopening the source tree. It is source-backed by the CNN search model, fixed-genotype model, operations, architect update code, utilities, genotypes, and runner scripts.

## High-level object map

| Concern | Object/function | Used by | Key fact |
| --- | --- | --- | --- |
| Search network | `Network` in the search model | CIFAR search | Learns `alphas_normal` and `alphas_reduce`, applies softmax over candidate operations, and derives a CNN genotype. |
| Search mixed edge | `MixedOp` | Search cells | Weighted sum over all search primitives for one edge. |
| Search cell | `Cell` in the search model | Search network | For each intermediate node, mixes all previous states and concatenates the last `multiplier` states. |
| Architecture optimizer | `Architect` | `train_search.py` | Updates architecture parameters on validation minibatches with first-order or one-step unrolled second-order approximation. |
| Fixed genotype cell | `Cell` in the evaluation model | CIFAR/ImageNet train/test | Compiles exactly two selected input edges per intermediate node from a genotype. |
| CIFAR fixed network | `NetworkCIFAR` | `train.py`, `test.py` | 32x32 stem, reduction cells at one-third/two-thirds depth, optional CIFAR auxiliary head, adaptive global pooling. |
| ImageNet fixed network | `NetworkImageNet` | `train_imagenet.py`, `test_imagenet.py` | Multi-stage strided stem for 224x224 crops, optional ImageNet auxiliary head, fixed 7x7 average pool. |
| Ops registry | `OPS` | Search and fixed cells | Maps operation names to PyTorch modules; includes operations beyond the search primitive list for imported genotypes. |
| Utilities | CIFAR transforms, accuracy, save/load, drop-path | All CNN runners | Provide normalization, Cutout, top-k accuracy, state-dict checkpointing, and CUDA-only drop-path. |

## Search-space primitives and operation registry

The CNN search primitive list contains eight candidates, in this order:

1. `none`
2. `max_pool_3x3`
3. `avg_pool_3x3`
4. `skip_connect`
5. `sep_conv_3x3`
6. `sep_conv_5x5`
7. `dil_conv_3x3`
8. `dil_conv_5x5`

The operation registry supports those plus additional names used by some predefined non-DARTS genotypes:

- `sep_conv_7x7`
- `conv_7x1_1x7`

Important operation behavior:

- `none` returns a `Zero` op; with stride 1 it multiplies the tensor by zero, and with stride greater than 1 it strides spatial dimensions before zeroing.
- `skip_connect` is identity at stride 1 and `FactorizedReduce` at stride 2.
- Pooling ops are average or max pooling with kernel 3, padding 1, and the stride passed by the cell.
- `sep_conv_*` applies two depthwise-separable convolution blocks with BatchNorm.
- `dil_conv_*` applies depthwise dilated convolution, pointwise convolution, and BatchNorm.
- `FactorizedReduce` asserts the output channel count is even, applies ReLU, takes two stride-2 1x1 convolutions with one branch shifted by one pixel, concatenates them, then BatchNorms the result.
- In search `MixedOp`, pooling ops receive an additional BatchNorm with `affine=False` after the pooling op.

## Search `MixedOp`

`MixedOp(C, stride)` constructs one candidate module per primitive in the search primitive list. Its forward signature is conceptually:

```python
output = sum(weight * op(input) for weight, op in zip(edge_weights, candidate_ops))
```

The weights passed to `MixedOp.forward` are rows from `softmax(alphas_normal)` or `softmax(alphas_reduce)`. Each edge therefore remains differentiable during search.

## Search `Cell`

The search cell is parameterized by `steps`, `multiplier`, previous channel counts, current channel count, whether this cell is a reduction cell, and whether the previous cell reduced spatial size.

Source-backed behavior:

- The first two states are the outputs of the previous two cells after preprocessing.
- If the previous cell was reduction, `s0` is preprocessed by `FactorizedReduce`; otherwise `s0` uses `ReLUConvBN` with kernel 1, stride 1.
- `s1` always uses `ReLUConvBN` with kernel 1, stride 1.
- For intermediate node `i`, the cell creates one `MixedOp` from every previous state (`2 + i` edges).
- In a reduction cell, edges from the two input states use stride 2; all other edges use stride 1.
- Forward pass sums all mixed incoming edges for each intermediate node.
- Output is `torch.cat(states[-multiplier:], dim=1)`. With default `steps=4` and `multiplier=4`, this concatenates the four intermediate node states.

## Search `Network`

The CNN search network is used by CIFAR-10 architecture search.

Constructor semantics:

- Inputs: initial channels `C`, `num_classes`, `layers`, loss `criterion`, and optional defaults `steps=4`, `multiplier=4`, `stem_multiplier=3`.
- Stem: `Conv2d(3, stem_multiplier*C, kernel_size=3, padding=1, bias=False)` followed by BatchNorm.
- Cells: `layers` cells; at layer indices `layers//3` and `2*layers//3`, the current channel count doubles and the cell is a reduction cell.
- Classifier: adaptive average pool to `1x1`, flatten, and linear classifier.
- Architecture parameters: two CUDA `Variable`s, `alphas_normal` and `alphas_reduce`, each shaped `[k, num_ops]` where `k = sum(2+i for i in range(steps))`. With default 4 steps, `k=14`; with 8 primitives, each alpha tensor is `14 x 8`.

Forward semantics:

1. Stem the input to initialize `s0 = s1`.
2. For each cell, choose softmaxed normal or reduction alpha weights based on `cell.reduction`.
3. Update `s0, s1 = s1, cell(s0, s1, weights)`.
4. Adaptive-pool the final state and classify.

Genotype derivation:

- `genotype()` parses `softmax(alphas_normal)` and `softmax(alphas_reduce)` independently.
- For each intermediate node, it selects the two previous input edges with the largest best non-`none` operation weight.
- For each selected edge, it chooses the highest-weight operation excluding `none`.
- The default concat is `range(2 + steps - multiplier, steps + 2)`, which is equivalent to nodes `[2, 3, 4, 5]` for the default 4-step, 4-multiplier cell.
- Returned genotype fields are `normal`, `normal_concat`, `reduce`, and `reduce_concat`.

## `Architect` search updates

`Architect(model, args)` owns an Adam optimizer over `model.arch_parameters()` with:

- learning rate `args.arch_learning_rate` (default `3e-4`),
- betas `(0.5, 0.999)`,
- weight decay `args.arch_weight_decay` (default `1e-3`).

`step(input_train, target_train, input_valid, target_valid, eta, network_optimizer, unrolled)` does one architecture update:

- First-order mode (`unrolled=False`): backpropagates validation loss through the current model and steps the architecture optimizer.
- Unrolled mode (`unrolled=True`):
  1. Builds an unrolled model by applying one virtual SGD update to the network weights using train loss, SGD momentum, and network weight decay.
  2. Backpropagates validation loss through the unrolled model.
  3. Computes an implicit gradient correction with a finite-difference Hessian-vector product using `r=1e-2` scaled by vector norm.
  4. Copies corrected architecture gradients back to the original model's alpha parameters before stepping Adam.

Operational consequences:

- `--unrolled` is more faithful to the README's second-order approximation but uses more memory.
- Search requires alternating weight minibatches and validation minibatches from the CIFAR training set split by `--train_portion`.
- Architecture parameters are CUDA variables; a CPU-only path is not implemented.

## Fixed-genotype `Cell`

The evaluation cell consumes a concrete CNN genotype instead of softmaxed architecture weights.

Compile behavior:

- For a reduction cell, it reads `genotype.reduce` and `genotype.reduce_concat`; otherwise it reads `genotype.normal` and `genotype.normal_concat`.
- The genotype edge list must contain operation-name/index pairs. The code asserts that operation names and indices have equal length and sets `_steps = len(op_names) // 2`.
- Each intermediate node uses exactly two operations: positions `2*i` and `2*i+1` in the compiled edge list.
- An operation runs with stride 2 only when the cell is a reduction cell and the selected input index is one of the two cell inputs (`index < 2`). Otherwise stride is 1.
- The output is the concatenation of states listed by the genotype concat field.

Forward behavior:

- Preprocesses the two input states as in search cells.
- For each intermediate node, applies the two selected operations, optionally applies drop-path to non-identity ops during training, sums them, and appends the result as a new state.
- Returns concatenated states according to the genotype's concat list.

Manual-construction caveat: both fixed networks read `self.drop_path_prob` inside cell forwarding. The runner scripts assign `model.drop_path_prob` before use. If constructing a network manually, set `model.drop_path_prob = 0.0` or a chosen value before calling it.

## `NetworkCIFAR`

`NetworkCIFAR(C, num_classes, layers, auxiliary, genotype)` is used by CIFAR train/test.

Architecture:

- Stem: 3x3 convolution from RGB to `3*C` channels plus BatchNorm, preserving 32x32 resolution.
- Cells: same reduction schedule as search: reductions at `layers//3` and `2*layers//3`, with channel doubling at each reduction.
- Auxiliary head: if `auxiliary=True`, creates `AuxiliaryHeadCIFAR` at the two-thirds-depth channel count.
- Pool/classifier: adaptive average pool to `1x1`, then linear classifier.

Forward result:

```python
logits, logits_aux = model(input)
```

- `logits_aux` is `None` unless `auxiliary=True` and the model is in training mode at the two-thirds-depth cell.
- In CIFAR training, the runner adds `auxiliary_weight * auxiliary_loss` when `--auxiliary` is set.
- In CIFAR testing, the runner ignores the auxiliary output but the module must still exist if the checkpoint includes auxiliary-head keys.

`AuxiliaryHeadCIFAR` assumes an 8x8 feature map. It applies ReLU, average pooling with kernel 5 and stride 3, 1x1 and 2x2 convolutions, BatchNorms, ReLUs, then a 768-to-class linear classifier.

## `NetworkImageNet`

`NetworkImageNet(C, num_classes, layers, auxiliary, genotype)` is used by ImageNet train/test.

Architecture:

- `stem0`: strided 3x3 conv from 3 to `C//2`, BatchNorm, ReLU, then strided 3x3 conv to `C`, BatchNorm.
- `stem1`: ReLU, strided 3x3 conv from `C` to `C`, BatchNorm.
- The initial `reduction_prev` flag is `True`, so the first cell preprocesses the earlier stem state through a reduction path.
- Cells use reductions at `layers//3` and `2*layers//3` with channel doubling.
- Auxiliary head: if `auxiliary=True`, creates `AuxiliaryHeadImageNet` at two-thirds depth.
- Pool/classifier: fixed `AvgPool2d(7)` followed by linear classifier. This assumes the standard 224x224 validation crop and native downsampling schedule.

Forward result:

```python
logits, logits_aux = model(input)
```

`AuxiliaryHeadImageNet` assumes a 14x14 feature map. It intentionally omits a BatchNorm after the 768-channel convolution for consistency with the paper experiments, according to the source comment.

## Data transforms

### CIFAR-10

Training transform:

1. Random crop 32x32 with padding 4.
2. Random horizontal flip.
3. Convert to tensor.
4. Normalize with mean `[0.49139968, 0.48215827, 0.44653124]` and std `[0.24703233, 0.24348505, 0.26158768]`.
5. If `--cutout` is enabled, append Cutout with length `--cutout_length` (default 16).

Validation/test transform:

1. Convert to tensor.
2. Normalize with the same CIFAR mean/std.

Cutout chooses a random center pixel, masks a square clipped to the image bounds, expands the mask across channels, and multiplies the tensor in place.

### ImageNet

Training transform:

1. Random resized crop to 224.
2. Random horizontal flip.
3. Color jitter with brightness/contrast/saturation 0.4 and hue 0.2.
4. Convert to tensor.
5. Normalize with ImageNet mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.

Validation transform:

1. Resize to 256.
2. Center crop to 224.
3. Convert to tensor.
4. Normalize with the same ImageNet mean/std.

## Optimizers and schedulers

| Runner | Weight optimizer | Scheduler | Loss |
| --- | --- | --- | --- |
| `train_search.py` | SGD with `learning_rate=0.025`, `momentum=0.9`, `weight_decay=3e-4` by default | Cosine annealing over search epochs with min lr `0.001` | Cross entropy |
| `train.py` | SGD with `learning_rate=0.025`, `momentum=0.9`, `weight_decay=3e-4` by default | Cosine annealing over full CIFAR epochs | Cross entropy plus optional auxiliary loss |
| `train_imagenet.py` | SGD with `learning_rate=0.1`, `momentum=0.9`, `weight_decay=3e-5` by default | StepLR every `decay_period=1` epoch with `gamma=0.97` | Label-smoothed cross entropy for training, plain cross entropy for validation; optional auxiliary loss |

All training runners clip gradients with `--grad_clip` (default 5 or 5.0).

## Accuracy and logging

- `accuracy(output, target, topk=(1, 5))` uses `output.topk`, compares predictions to targets, and returns percentages.
- `AvgrageMeter` (source spelling) tracks current average from sum and count.
- CIFAR search/train/test log top-1 and top-5 in step logs, but epoch summary emphasizes `train_acc`, `valid_acc`, or `test_acc` top-1.
- ImageNet train/test log both top-1 and top-5 validation accuracy.

## Checkpoint save/load contracts

### CIFAR search and training

- `utils.save(model, path)` writes `model.state_dict()` directly with `torch.save`.
- `train_search.py` writes `weights.pt` under its `search-*` directory each epoch.
- `train.py` writes `weights.pt` under its `eval-*` directory each epoch.

### CIFAR pretrained/test load

- `utils.load(model, model_path)` calls `model.load_state_dict(torch.load(model_path))`.
- Therefore `test.py` expects the file at `--model_path` to be a raw state dict compatible with the instantiated `NetworkCIFAR`.
- `--arch`, `--init_channels`, `--layers`, and `--auxiliary` must match the checkpoint.

### ImageNet training save

`train_imagenet.py` writes a checkpoint dictionary each epoch:

```text
epoch: epoch + 1
state_dict: model.state_dict()
best_acc_top1: best validation top-1 so far
optimizer: optimizer.state_dict()
```

It writes `checkpoint.pth.tar` and copies to `model_best.pth.tar` when validation top-1 improves.

### ImageNet pretrained/test load

`test_imagenet.py` loads:

```python
model.load_state_dict(torch.load(args.model_path)['state_dict'])
```

So the file must be a dictionary with a `state_dict` key, not a raw CIFAR-style state dict.

DataParallel caveat: ImageNet training with `--parallel` wraps the model in `nn.DataParallel` before saving. That can add `module.` prefixes to state-dict keys. The ImageNet test runner instantiates a non-parallel model, so a parallel-trained checkpoint may require key-prefix handling before native test loading.

## Genotype consumption

- Native CNN runners resolve `--arch` with `eval("genotypes.%s" % args.arch)`. A missing or misspelled name raises a runtime error.
- Built-in `DARTS` is an alias of `DARTS_V2`.
- Fixed CNN genotypes must have fields `normal`, `normal_concat`, `reduce`, and `reduce_concat`.
- Operation names in a fixed genotype must exist in the operation registry, not only in the search primitive list.
- Search-derived genotypes choose operations only from the eight search primitives and exclude `none` during parsing.
- CNN and RNN genotypes have different schemas; do not use an RNN genotype in these CNN networks.

For genotype catalogs, validation helpers, and DOT rendering, route to `../genotypes-and-visualization/`.
