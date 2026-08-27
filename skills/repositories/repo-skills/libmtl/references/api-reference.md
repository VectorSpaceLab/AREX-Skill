# LibMTL API Reference

This file captures the public API surface that was verified from source and the
installed inspection environment.

## Package exports

`LibMTL.__init__` exposes these top-level namespaces:

- `Trainer`
- `config`
- `loss`
- `metrics`
- `model`
- `architecture`
- `weighting`
- `utils`

## Verified signatures

### `LibMTL.Trainer`

```python
Trainer(
    task_dict,
    weighting,
    architecture,
    encoder_class,
    decoders,
    rep_grad,
    multi_input,
    optim_param,
    scheduler_param,
    save_path=None,
    load_path=None,
    **kwargs,
)
```

Notes:

- `weighting` and `architecture` are passed as string names such as `"EW"`
  and `"HPS"`, not class objects.
- `kwargs` should contain `weight_args` and `arch_args`. If you are not using
  `prepare_args`, pass `weight_args={}` and `arch_args={}` yourself.
- `Trainer` sets `self.device = torch.device('cuda:0')`; it is a CUDA-first
  training engine.
- `Trainer.train(...)` dispatches to `train_bilevel(...)` for
  `MOML`, `FORUM`, and `AutoLambda`.

### `LibMTL.config`

```python
LibMTL_args  # argparse.ArgumentParser
prepare_args(params)
```

`prepare_args` returns:

1. `kwargs` with `weight_args` and `arch_args`
2. `optim_param`
3. `scheduler_param`

Verified caveats:

- `optim='adam'` and `optim='sgd'` are wired in the current implementation.
  `adagrad` and `rmsprop` appear in the parser/help text but are not fully
  populated by `prepare_args`.
- `scheduler='step'` is wired. `cos` and `exp` appear in help text but are not
  fully populated by `prepare_args`.

### `LibMTL.utils`

```python
get_root_dir()
set_random_seed(seed)
set_device(gpu_id)
count_parameters(model)
count_improvement(base_result, new_result, weight)
```

### `LibMTL.loss`

```python
AbsLoss
CELoss
KLDivLoss
L1Loss
MSELoss
```

### `LibMTL.metrics`

```python
AbsMetric
AccMetric
L1Metric
```

### `LibMTL.model`

```python
resnet18(resnet34, resnet50, resnet101, resnet152)
resnext50_32x4d
resnext101_32x8d
wide_resnet50_2
wide_resnet101_2
resnet_dilated
```

The ResNet builders return feature extractors, not classifiers. Use task
specific decoders or heads on top of the returned feature maps.

### `LibMTL.architecture`

```python
AbsArchitecture
HPS
Cross_stitch
MMoE
MTAN
CGC
PLE
DSelect_k
LTB
```

### `LibMTL.weighting`

```python
AbsWeighting
EW
GradNorm
MGDA
UW
DWA
GLS
GradDrop
PCGrad
GradVac
IMTL
CAGrad
Nash_MTL
RLW
MoCo
Aligned_MTL
DB_MTL
STCH
ExcessMTL
FairGrad
FAMO
MoDo
SDMGrad
UPGrad
```

## Extension points

### `AbsArchitecture`

Important methods to override when defining a new architecture:

- `forward(inputs, task_name=None)`
- `get_share_params()`
- `zero_grad_share_params()`
- `_prepare_rep(rep, task, same_rep=None)`

### `AbsWeighting`

Important methods to override when defining a new weighting strategy:

- `init_param()`
- `backward(losses, **kwargs)`
- `_get_grads(...)` when you need custom gradient plumbing
- `_backward_new_grads(...)` when you need custom gradient injection

### `AbsLoss` and `AbsMetric`

- Override `compute_loss(pred, gt)` for losses.
- Override `update_fun`, `score_fun`, and `reinit` for metrics.

## Verified runtime facts

- `resnet18(pretrained=False)` returns a feature tensor of shape
  `(N, 512, 7, 7)` for `224x224` inputs.
- `resnet_dilated('resnet50', pretrained=False)` returns a feature tensor of
  shape `(N, 2048, 36, 48)` for `288x384` inputs.
- A minimal synthetic `Trainer` run with `weighting='EW'`, `architecture='HPS'`,
  and empty `weight_args` / `arch_args` completed successfully in the verified
  CUDA inspection environment.

## Example usage pattern

```python
kwargs, optim_param, scheduler_param = prepare_args(params)
trainer = Trainer(
    task_dict=task_dict,
    weighting=params.weighting,
    architecture=params.arch,
    encoder_class=Encoder,
    decoders=decoders,
    rep_grad=params.rep_grad,
    multi_input=params.multi_input,
    optim_param=optim_param,
    scheduler_param=scheduler_param,
    **kwargs,
)
```

For direct construction without `prepare_args`, make sure you provide empty
`weight_args` and `arch_args` dictionaries.
