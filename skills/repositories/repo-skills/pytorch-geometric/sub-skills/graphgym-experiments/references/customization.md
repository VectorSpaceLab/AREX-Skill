# GraphGym Customization

GraphGym customization is registry-driven. Register custom modules before the experiment config is loaded and before model/data/training builders look up keys. A project entrypoint usually imports a customization package for side effects, then calls GraphGym config loading and training code.

## Registries

PyG GraphGym exposes registration helpers under `torch_geometric.graphgym.register`, including:

- `register_act(key, module=None)` for activations.
- `register_layer(key, module=None)` for GraphGym-format GNN layers.
- `register_pooling(key, module=None)` for graph pooling/readout.
- `register_head(key, module=None)` for prediction heads.
- `register_network(key, module=None)` for model architectures.
- `register_dataset(key, module=None)` and `register_loader(key, module=None)` for data sources/loaders.
- `register_optimizer(key, module=None)` and `register_scheduler(key, module=None)` for optimization.
- `register_loss(key, module=None)`, `register_train(key, module=None)`, and `register_metric(key, module=None)` for training behavior and reporting.
- `register_config(key, module=None)` for adding custom config defaults.

Each helper inserts into an in-memory dictionary and raises `KeyError` when the key already exists. Use unique, stable lowercase keys and import custom modules exactly once in tests to avoid accidental collisions.

## Decorator Pattern

```python
from torch_geometric.graphgym.register import register_act

@register_act('identity')
def identity_act(x):
    return x
```

This registers a callable under `identity`. The config can then reference the key where the corresponding registry is used.

## Direct Registration Pattern

```python
import torch
from torch_geometric.graphgym.register import register_act

register_act('lrelu_03', torch.nn.LeakyReLU(0.3))
```

Use direct registration for simple module instances or factories. Check that the target key is not already present before registering in reusable libraries.

## Custom Layer Skeleton

GraphGym layers are batch-in/batch-out modules. A layer should read `batch.x` and `batch.edge_index`, update `batch.x`, and return the same batch object.

```python
import torch.nn as nn
from torch_geometric.graphgym.config import cfg
from torch_geometric.graphgym.register import register_layer
from torch_geometric.nn import MessagePassing

@register_layer('myconv')
class MyConv(nn.Module):
    def __init__(self, dim_in, dim_out, **kwargs):
        super().__init__()
        self.conv = MessagePassing(aggr=cfg.gnn.agg)
        self.lin = nn.Linear(dim_in, dim_out)

    def forward(self, batch):
        batch.x = self.lin(batch.x)
        return batch
```

For production use, subclass `MessagePassing` or wrap a PyG convolution such as `GCNConv`, `SAGEConv`, or `GATConv`, then assert the output node feature shape before training.

## Custom Config Defaults

Custom config functions receive the global config node and add defaults before a YAML file merges overrides:

```python
from yacs.config import CfgNode as CN
from torch_geometric.graphgym.register import register_config

@register_config('my_project')
def set_cfg_my_project(cfg):
    cfg.my_project = CN()
    cfg.my_project.dropout_schedule = 'none'
```

This requires the optional `yacs` dependency. Keep custom keys shallow and document their expected types in the project config template.

## Review Checklist

- The customization package is imported before config loading and training.
- Registry keys are unique and stable; collisions are handled as errors, not silently overwritten.
- Config YAML values match registry keys exactly, including case.
- Custom layers use GraphGym's batch-in/batch-out contract rather than raw `(x, edge_index)` signatures unless wrapped.
- Custom config defaults are registered before the YAML is merged.
- Unit tests import the custom package and assert the registry dictionary contains the expected key.
