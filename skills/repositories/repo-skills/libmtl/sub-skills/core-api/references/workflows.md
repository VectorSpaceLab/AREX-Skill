# Core API Workflows

This reference explains the normal way to use the shared LibMTL API.

## 1. Choose the names first

`Trainer` resolves the weighting and architecture from strings. Start by naming
what you want:

- `weighting='EW'`, `'GradNorm'`, `'CAGrad'`, etc.
- `architecture='HPS'`, `'MTAN'`, `'MMoE'`, etc.

If you are unsure of the names, read the root `api-reference.md` first.

## 2. Build the configuration

Preferred path:

```python
kwargs, optim_param, scheduler_param = prepare_args(params)
```

This gives you:

- `kwargs['weight_args']`
- `kwargs['arch_args']`
- `optim_param`
- `scheduler_param`

When you do not use `prepare_args`, provide `weight_args={}` and
`arch_args={}` manually.

## 3. Wire the model pieces

A working LibMTL setup needs:

- a task dictionary with metrics, metric functions, loss functions, and metric
  polarity flags;
- an encoder class that returns shared features;
- a `ModuleDict` of task decoders;
- a CUDA-capable runtime.

The simplest verified pattern is a shared encoder plus task-specific linear
heads.

## 4. Instantiate `Trainer`

```python
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

Important:

- pass strings, not class objects;
- keep `weight_args` and `arch_args` present;
- expect the trainer to move to `cuda:0`.

## 5. Train or test

- `trainer.train(train_dataloaders, test_dataloaders, epochs, ...)`
- `trainer.test(test_dataloaders, ...)`

The trainer can also return loss weights when `return_weight=True`.

## 6. Inspect built-ins

Useful module families:

- `LibMTL.loss`
- `LibMTL.metrics`
- `LibMTL.model`
- `LibMTL.architecture`
- `LibMTL.weighting`

If the user needs the exact class list or signatures, point them back to the
root API reference.

## Suggested smoke path

Use `scripts/check_core_api.py` when you need to verify that a CUDA environment
can construct and run a tiny synthetic `Trainer` instance.
