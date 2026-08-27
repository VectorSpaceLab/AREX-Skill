# API Reference

## Purpose

Read this when you need the verified signatures for the training-side model, optimizer, scheduler, loss, and metric helpers.

## Verified signatures

### `model.model.parsingNet`

```python
parsingNet(size=(288, 800), pretrained=True, backbone='50', cls_dim=(37, 10, 4), use_aux=False)
```

### `utils.factory.get_optimizer`

```python
get_optimizer(net, cfg)
```

Supports:

- `cfg.optimizer == 'Adam'`
- `cfg.optimizer == 'SGD'`

### `utils.factory.get_scheduler`

```python
get_scheduler(optimizer, cfg, iters_per_epoch)
```

Supports:

- `cfg.scheduler == 'multi'`
- `cfg.scheduler == 'cos'`

### `utils.factory.get_loss_dict`

```python
get_loss_dict(cfg)
```

### `utils.factory.get_metric_dict`

```python
get_metric_dict(cfg)
```

### `utils.common.get_work_dir`

Builds a dated subdirectory under `cfg.log_path` using the learning rate, batch size, and optional note.

### `utils.common.save_model`

```python
save_model(net, optimizer, epoch, save_path, distributed)
```

Writes a checkpoint named `ep%03d.pth` into the work directory.

### `utils.common.cp_projects`

```python
cp_projects(auto_backup, to_path)
```

Copies the working tree into the log directory when `auto_backup` is enabled.

## Important model facts

- `parsingNet` returns a classification head and, when `use_aux=True`, an auxiliary segmentation head.
- The code expects the selected backbone to be one of the allowed ResNet/ResNeXt/Wide-ResNet variants.
- The training and test code assume CUDA tensors.

## Practical reminder

The model and loader dimensions are dataset-dependent, so keep the `data-and-config` row-anchor and `griding_num` guidance in sync with the training command.
