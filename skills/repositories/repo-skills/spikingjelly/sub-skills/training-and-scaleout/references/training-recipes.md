# Training recipes

This reference distills the practical image-classification workflows owned by the `training-and-scaleout` sub-skill.

## 1) Quick routing map

| Need | Start here | Why |
| --- | --- | --- |
| Legacy single-node / DDP-style ImageNet training | `spikingjelly.activation_based.model.train_classify.Trainer` | Extensible torchvision-reference-style trainer with sample preprocessing, output reduction, optimizer, scheduler, compile, and EMA hooks |
| Spiking ResNet baseline training | `spikingjelly.activation_based.model.spiking_resnet` | Stable model-zoo family used by the legacy ImageNet example |
| SEW-ResNet image-classification training | `spikingjelly.activation_based.model.sew_resnet` | Official SEW-style residual family and the built-in distributed vision builder |
| Spikformer image-classification training | `spikingjelly.activation_based.model.spikformer` | Native multi-step Transformer-style SNN family and the built-in distributed vision builder |
| DDP / FSDP2 / TP / PP vision topology | `spikingjelly.activation_based.distributed.vision` | Declarative config + builder contract + topology checks |
| Safe smoke of the above | `scripts/vision_training_config_smoke.py` | No-download contract check that does not launch distributed training |

## 2) Verified live signatures

These are the public entry points the sub-skill should target.

### `train_classify`

- `Trainer()`
- `set_deterministic(_seed_: int = 2020, disable_uda=False)`
- `seed_worker(worker_id)`

Trainer override points inspected in the prepared environment:

- `get_data_to_device_kwargs(self, args)`
- `cal_acc1_acc5(self, output, target)`
- `preprocess_train_sample(self, args, x)`
- `preprocess_test_sample(self, args, x)`
- `process_model_output(self, args, y)`
- `compile_model(self, args, model, *, enabled=None)`
- `get_eval_model(self, args, train_model, model_without_ddp)`
- `train_one_epoch(...)`
- `evaluate(...)`
- `load_data(self, args)`
- `load_CIFAR10(self, args)`
- `load_ImageNet(self, args)`
- `load_model(self, args, num_classes)`
- `get_tb_logdir_name(self, args)`
- `set_optimizer(self, args, parameters)`
- `set_lr_scheduler(self, args, optimizer)`
- `main(self, args)`
- `before_test_one_epoch(self, args, model, epoch)`
- `before_train_one_epoch(self, args, model, epoch)`
- `get_args_parser(self, add_help=True)`

### `spiking_resnet`

- `spiking_resnet18(pretrained=False, progress=True, spiking_neuron=None, **kwargs)`
- `spiking_resnet34(...)`
- `spiking_resnet50(...)`
- `spiking_resnet101(...)`
- `spiking_resnet152(...)`
- `spiking_resnext50_32x4d(...)`
- `spiking_resnext101_32x8d(...)`
- `spiking_wide_resnet50_2(...)`
- `spiking_wide_resnet101_2(...)`

### `sew_resnet`

- `sew_resnet18(pretrained=False, progress=True, cnf=None, spiking_neuron=None, **kwargs)`
- `sew_resnet34(...)`
- `sew_resnet50(...)`
- `sew_resnet101(...)`
- `sew_resnet152(...)`
- `sew_resnext50_32x4d(...)`
- `sew_resnext101_32x8d(...)`
- `sew_wide_resnet50_2(...)`
- `sew_wide_resnet101_2(...)`

### `spikformer`

- `Spikformer(T=4, in_channels=3, img_size_h=224, img_size_w=224, patch_size=16, num_classes=1000, embed_dims=256, num_heads=8, mlp_ratio=4.0, depths=4, backend='torch', tau=2.0, detach_reset=True)`
- `SpikformerBlock(dim, num_heads, mlp_ratio=4.0, backend='torch', tau=2.0, detach_reset=True)`
- `SpikformerConv2dBN(...)`
- `SpikformerConv2dBNLIF(...)`
- `SpikformerMLP(...)`
- `SpikformerPatchStem(...)`
- `spikformer_cifar10(T=4, num_classes=10, backend='torch')`
- `spikformer_s(T=4, in_channels=3, img_size_h=224, img_size_w=224, num_classes=1000, backend='torch')`
- `spikformer_ti(T=4, in_channels=3, img_size_h=224, img_size_w=224, num_classes=1000, backend='torch')`

## 3) Legacy `Trainer` recipe

`Trainer` is the right surface when you want a torchvision-style classifier trainer with a small number of spiking-specific overrides.

### Typical overrides

| Hook | What to override | Common SpikingJelly use |
| --- | --- | --- |
| `load_model` | Build the model-zoo network | Load a `spiking_resnet` family member, then call `functional.set_step_mode(model, 'm')` if the loop consumes time-major sequences |
| `preprocess_train_sample` | Convert the DataLoader sample before the forward pass | Expand a static `[N, C, H, W]` batch to `[T, N, C, H, W]` |
| `preprocess_test_sample` | Same as training, but for validation | Keep evaluation readout aligned with the training layout |
| `process_model_output` | Reduce the model output to classifier logits | Usually `y.mean(0)` for `[T, N, C]` outputs |
| `set_optimizer` | Replace or extend the optimizer choice | Add Adamax, AdamW variants, or custom weight decay policies |
| `set_lr_scheduler` | Replace or extend the scheduler choice | Keep a familiar step/cosine/warmup layout |
| `get_args_parser` | Add CLI switches | `--T`, `--cupy`, `--backend`, or model-zoo-specific flags |
| `before_train_one_epoch` / `before_test_one_epoch` | Pre-epoch hooks | Sync state, print diagnostics, or freeze buffers |

### Reference pattern

```python
import torch
from spikingjelly.activation_based import functional, neuron, surrogate
from spikingjelly.activation_based.model import spiking_resnet, train_classify


class SResNetTrainer(train_classify.Trainer):
    def preprocess_train_sample(self, args, x: torch.Tensor):
        return x.unsqueeze(0).expand(args.T, -1, -1, -1, -1)

    def preprocess_test_sample(self, args, x: torch.Tensor):
        return x.unsqueeze(0).expand(args.T, -1, -1, -1, -1)

    def process_model_output(self, args, y: torch.Tensor):
        return y.mean(0)

    def load_model(self, args, num_classes):
        model = spiking_resnet.spiking_resnet18(
            pretrained=args.pretrained,
            spiking_neuron=neuron.IFNode,
            surrogate_function=surrogate.ATan(),
            detach_reset=True,
            num_classes=num_classes,
        )
        functional.set_step_mode(model, 'm')
        return model
```

### Key `Trainer` rules

- `train_one_epoch` and `evaluate` already call `functional.reset_net(model)` internally after each batch.
- `Trainer` expects the model output to be reduced before loss/accuracy calculation.
- `Trainer` is the legacy route; it is not the right place to encode TP, PP, or FSDP2 topology logic.

## 4) Spiking ResNet recipe

Use `spiking_resnet` when you want the classic ImageNet-style baseline and the simplest training loop.

### Practical setup

```python
from spikingjelly.activation_based import functional, neuron, surrogate
from spikingjelly.activation_based.model import spiking_resnet

model = spiking_resnet.spiking_resnet34(
    pretrained=False,
    spiking_neuron=neuron.IFNode,
    surrogate_function=surrogate.ATan(),
    detach_reset=True,
    num_classes=1000,
)
functional.set_step_mode(model, 'm')
```

### Readout contract

- Multi-step training usually feeds `[T, N, C, H, W]`.
- The model returns `[T, N, num_classes]` or a compatible batched time layout.
- For classification loss, reduce over time with `y.mean(0)` unless the task defines a different readout.

### When to prefer this family

- You want a direct ImageNet-style baseline.
- You need a model that is close to the torchvision ResNet structure.
- You are adapting the legacy `train_classify` workflow rather than the distributed vision API.

## 5) SEW-ResNet recipe

Use `sew_resnet` for the built-in SEW image-classification family and for the distributed vision builder that owns channel TP and PP.

### Practical setup

```python
from spikingjelly.activation_based import functional, neuron, surrogate
from spikingjelly.activation_based.model import sew_resnet

model = sew_resnet.sew_resnet34(
    pretrained=False,
    cnf='ADD',
    spiking_neuron=neuron.LIFNode,
    tau=2.0,
    detach_reset=True,
    num_classes=1000,
    backend='torch',
)
functional.set_step_mode(model, 'm')
```

### Connection choices

`cnf` selects the residual combine rule:

- `"ADD"` — additive residual connection
- `"AND"` — multiplicative gating
- `"IAND"` — inhibitory multiplicative form

### Readout contract

- The built-in model works with single-step or multi-step conventions depending on the surrounding trainer.
- For distributed vision, prefer `step_mode='m'` and a time-major input.
- For legacy classifier loops, reduce the time dimension before the loss.

### When to prefer this family

- You want the official SEW classifier family.
- You expect to use the distributed vision builders.
- You want a valid topology that can be split into PP stages or channel-sharded blocks.

## 6) Spikformer recipe

Use `spikformer` for the Transformer-style image-classification workflow.

### Practical setup

```python
from spikingjelly.activation_based.model import spikformer

model = spikformer.spikformer_cifar10(T=4, num_classes=10, backend='torch')
```

### Input and output shape notes

- The module accepts either a static image batch `[N, C, H, W]` or a prebuilt sequence `[T, N, C, H, W]`.
- A static image batch is internally repeated across time.
- The model returns a sequence-shaped classifier output.
- The common classifier reduction is `logits = y.mean(0)`.

### Architecture notes that matter for training

- `SpikformerPatchStem` uses patch splitting; the image size must be compatible with the chosen patch size when PP is enabled.
- `SpikformerBlock` is naturally multi-step.
- `spikformer_cifar10` is the official 32×32 / 4×4-patch / 384-channel / 12-head / 4-block variant.

### When to prefer this family

- You are training a Spikformer image classifier.
- You need the CIFAR-10 or ImageNet-style built-in variants.
- You want a distributed vision topology that can shard heads and channels.

## 7) Distributed-vision starter patterns

Use `spikingjelly.activation_based.distributed.vision` when you need a declarative multi-GPU vision topology.

### High-level patterns

- `SEWResNet34Config` — built-in ImageNet-style SEW model.
- `SpikformerConfig` — built-in 224×224 Spikformer-S.
- `SpikformerCIFAR10Config` — official 32×32 CIFAR-10 Spikformer.
- `TrainingConfig` — controls data, optimizer, loss, precision, DP/FSDP2, TP, PP, and checkpoints.
- `train_classification(config)` — executes the full run.

### Topology semantics to remember

- `batch_size` is per data-parallel rank.
- Global batch is `batch_size * data_parallel_size`.
- TP and PP do not multiply the global batch.
- `input_layout` is explicit; it does not get inferred from tensor rank.
- `step_mode='m'` is required for PP and memopt in the built-in vision configs.

## 8) Safe smoke cases

The bundled smoke script should prove:

1. `Trainer` can still parse and expose the extension points.
2. `TrainingConfig` round-trips through `as_dict()` / `from_dict()`.
3. Built-in model builders produce the expected CPU shapes on synthetic inputs.
4. PP shape metadata is returned for the built-in configs.
5. Invalid combinations are rejected early.

## 9) Practical advice

- For quick experiments, start with `spiking_resnet` or `sew_resnet` before moving to `Spikformer`.
- For custom loops, decide on the time axis first and keep the readout explicit.
- For distributed training, treat `distributed.vision` as the canonical entry point and keep `Trainer` for the legacy single-node/DDP surface.
- If you need dataset details, route to the datasets sub-skill instead of expanding this reference.
