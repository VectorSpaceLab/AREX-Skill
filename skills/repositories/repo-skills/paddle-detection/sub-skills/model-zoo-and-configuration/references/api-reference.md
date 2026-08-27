# Configuration and Model-Zoo API Reference

Live inspection on PaddleDetection release/2.9 source with PaddlePaddle 2.6.2 confirmed these signatures:

```python
from ppdet.core.workspace import load_config, merge_config, create, register
from ppdet.engine import Trainer
from ppdet.model_zoo import list_model, get_config_file, get_weights_url, get_model

load_config(file_path)
merge_config(config, another_cfg=None)
create(cls_or_name, **kwargs)
register(cls)
Trainer(cfg, mode='train')
list_model(filters=[])
get_config_file(model_name)
get_weights_url(model_name)
get_model(model_name, pretrained=True)
```

`load_config` returns the global configuration object after recursive `_BASE_` merging and adds a `filename` field. `create` accepts a registered class name or class. `Trainer` accepts only `train`, `eval`, or `test`; `test` is the least expensive construction mode but can still allocate a large model.

A custom component must be registered before config loading or construction if its name is referenced by YAML. Keep registration importable from the target project and avoid side effects at module import time.
