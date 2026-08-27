# Customization Workflows

This reference distills the repo's "apply to a new dataset" and "customize a
method" guidance into one repeatable recipe.

## 1. Decide the task shape

First determine whether the benchmark is:

- **single-input**: one input tensor produces labels for all tasks;
- **multi-input**: each task owns its own dataloader.

Set `multi_input` accordingly before you wire the trainer.

## 2. Define the task dictionary

Each task entry needs:

- `metrics`
- `metrics_fn`
- `loss_fn`
- `weight`

Example pattern:

```python
task_dict = {
    "task": {
        "metrics": ["Acc"],
        "metrics_fn": AccMetric(),
        "loss_fn": CELoss(),
        "weight": [1],
    }
}
```

For multi-metric tasks, `metrics_fn` can be a custom metric object that returns
multiple scores.

## 3. Build dataloaders with the right structure

- **single-input**: one dataloader that yields `(inputs, {task: labels})`
- **multi-input**: a dictionary of task-name → dataloader

The benchmark examples in this repo follow that exact contract.

## 4. Define the encoder and decoders

The encoder is a class or factory that returns the shared backbone.
The decoders are instantiated modules, usually stored in a `ModuleDict`.

Important patterns from the repo:

- Vision backbones often return feature maps, not final logits.
- MTAN expects a ResNet-based encoder with a `resnet_network` attribute.
- `resnet_dilated('resnet50')` is the standard NYUv2-style feature extractor.

## 5. Wire the trainer

Use the shared trainer with the right names and kwargs:

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

If you do not call `prepare_args`, pass empty `weight_args={}` and
`arch_args={}` explicitly.

## 6. Extend losses and metrics

Subclass the abstract bases and implement the documented hooks:

- `AbsLoss.compute_loss(pred, gt)`
- `AbsMetric.update_fun(pred, gt)`
- `AbsMetric.score_fun()`
- `AbsMetric.reinit()`

The NYUv2 metric and loss pattern in the vision benchmark reference is the
best shape example for a multi-output task.

## 7. Extend architectures or weighting strategies

Start from the abstract base classes:

- `AbsArchitecture` for new model routing logic
- `AbsWeighting` for new gradient weighting logic

Key implementation hooks:

- `AbsArchitecture.forward(...)`
- `AbsArchitecture.get_share_params()`
- `AbsArchitecture.zero_grad_share_params()`
- `AbsWeighting.backward(...)`
- `AbsWeighting.init_param()`

If your method uses representation gradients, preserve the `rep_grad` plumbing
and the detach behavior used in the existing methods.

## 8. Reuse existing benchmark patterns

- **NYUv2 / Cityscapes**: single-input dense prediction with custom heads.
- **Office-31 / Office-Home**: multi-input classification with separate domain
  loaders.
- **QM9**: graph data with PyG loaders and task-specific regression heads.
- **PAWS-X**: multilingual text features with cached tokenized tensors.

## 9. Check the failure modes early

Common extension failures are covered in `troubleshooting.md`. The most common
ones are:

- wrong `multi_input` setting,
- shape mismatch between encoder and decoder,
- unsupported architecture constraints such as `PLE` with multi-input,
- missing CUDA runtime,
- or an outdated scheduler/optimizer choice.
