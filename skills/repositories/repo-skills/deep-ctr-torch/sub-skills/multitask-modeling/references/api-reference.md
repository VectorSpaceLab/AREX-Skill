# Multi-task API reference

## Constructors

```python
MMOE(
    dnn_feature_columns,
    num_experts=3,
    expert_dnn_hidden_units=(256, 128),
    gate_dnn_hidden_units=(64,),
    tower_dnn_hidden_units=(64,),
    l2_reg_linear=1e-05,
    l2_reg_embedding=1e-05,
    l2_reg_dnn=0,
    init_std=0.0001,
    seed=1024,
    dnn_dropout=0,
    dnn_activation='relu',
    dnn_use_bn=False,
    task_types=('binary', 'binary'),
    task_names=('ctr', 'ctcvr'),
    device='cpu',
    gpus=None,
)

PLE(
    dnn_feature_columns,
    shared_expert_num=1,
    specific_expert_num=1,
    num_levels=2,
    expert_dnn_hidden_units=(256, 128),
    gate_dnn_hidden_units=(64,),
    tower_dnn_hidden_units=(64,),
    l2_reg_linear=1e-05,
    l2_reg_embedding=1e-05,
    l2_reg_dnn=0,
    init_std=0.0001,
    seed=1024,
    dnn_dropout=0,
    dnn_activation='relu',
    dnn_use_bn=False,
    task_types=('binary', 'binary'),
    task_names=('ctr', 'ctcvr'),
    device='cpu',
    gpus=None,
)

SharedBottom(
    dnn_feature_columns,
    bottom_dnn_hidden_units=(256, 128),
    tower_dnn_hidden_units=(64,),
    l2_reg_linear=1e-05,
    l2_reg_embedding=1e-05,
    l2_reg_dnn=0,
    init_std=0.0001,
    seed=1024,
    dnn_dropout=0,
    dnn_activation='relu',
    dnn_use_bn=False,
    task_types=('binary', 'binary'),
    task_names=('ctr', 'ctcvr'),
    device='cpu',
    gpus=None,
)

ESMM(
    dnn_feature_columns,
    tower_dnn_hidden_units=(256, 128),
    l2_reg_linear=1e-05,
    l2_reg_embedding=1e-05,
    l2_reg_dnn=0,
    init_std=0.0001,
    seed=1024,
    dnn_dropout=0,
    dnn_activation='relu',
    dnn_use_bn=False,
    task_types=('binary', 'binary'),
    task_names=('ctr', 'ctcvr'),
    device='cpu',
    gpus=None,
)
```

Import them from either location:

```python
from deepctr_torch.models import SharedBottom, ESMM, MMOE, PLE
# or
from deepctr_torch.models.multitask import SharedBottom, ESMM, MMOE, PLE
```

## Common MTL contract

| Item | Contract |
| --- | --- |
| Input features | `dnn_feature_columns` only; these are shared by all tasks. Use the feature-column input sub-skill for constructing and ordering them. |
| Task count | `len(task_names)` defines `num_tasks`; all four models require more than one output, and `ESMM` requires exactly two. |
| Target shape | `y.shape == (n_samples, num_tasks)`. Column `i` is the label for `task_names[i]`. |
| Prediction shape | `model.predict(x, batch_size).shape == (n_samples, num_tasks)`. Column `i` is the prediction for `task_names[i]`. |
| Loss list | If `loss` is a list, its length must equal `num_tasks`; loss `i` trains prediction column `i` against target column `i`. |
| Supported loss strings | `binary_crossentropy`, `mse`, `mae`. |
| Device | `device='cpu'` or a CUDA device string. If `gpus` is set, `gpus[0]` must match `device`. |

## Supported task types

| Model | `task_types` values | Notes |
| --- | --- | --- |
| `SharedBottom` | `binary`, `regression` | Any list/tuple length equal to `len(task_names)` and greater than one. |
| `MMOE` | `binary`, `regression` | Any list/tuple length equal to `len(task_names)` and greater than one. |
| `PLE` | `binary`, `regression` | Any list/tuple length equal to `len(task_names)` and greater than one. |
| `ESMM` | `binary` only | Exactly two tasks; both task types must be `binary`. |

`PredictionLayer('binary')` applies sigmoid-like binary output behavior. `PredictionLayer('regression')` leaves regression outputs for regression losses.

## Validation and predictable constructor errors

| Model | Validation enforced by the implementation |
| --- | --- |
| `SharedBottom` | `num_tasks > 1`; non-empty `dnn_feature_columns`; `len(task_types) == num_tasks`; every task type is `binary` or `regression`. |
| `MMOE` | `num_tasks > 1`; `num_experts > 1`; non-empty `dnn_feature_columns`; `len(task_types) == num_tasks`; every task type is `binary` or `regression`. |
| `PLE` | `num_tasks > 1`; non-empty `dnn_feature_columns`; `len(task_types) == num_tasks`; every task type is `binary` or `regression`. |
| `ESMM` | `num_tasks == 2`; non-empty `dnn_feature_columns`; `len(task_types) == 2`; both task types are `binary`. |

## Architecture-specific parameters

### SharedBottom

| Parameter | Meaning |
| --- | --- |
| `bottom_dnn_hidden_units` | Hidden units for the shared bottom network. |
| `tower_dnn_hidden_units` | Hidden units for each task-specific tower. Empty towers are covered by native tests. |

### ESMM

| Parameter | Meaning |
| --- | --- |
| `tower_dnn_hidden_units` | Hidden units for CTR and CVR towers. Keep this non-empty. |
| `task_names` | Names the two output columns. Defaults to `('ctr', 'ctcvr')`, matching the actual output semantics. |

`ESMM` internally computes:

```text
ctr_pred = CTR tower output
cvr_pred = CVR tower output
ctcvr_pred = ctr_pred * cvr_pred
return concatenate([ctr_pred, ctcvr_pred])
```

The second output is therefore CTCVR, not raw CVR.

### MMOE

| Parameter | Meaning |
| --- | --- |
| `num_experts` | Number of shared experts; must be greater than 1. |
| `expert_dnn_hidden_units` | Hidden units for each expert DNN. |
| `gate_dnn_hidden_units` | Hidden units for each task gate DNN. Empty gates are covered by native tests. |
| `tower_dnn_hidden_units` | Hidden units for each task tower. Empty towers are covered by native tests. |

Forward shape summary:

```text
expert_outs: (batch_size, num_experts, expert_dim)
gate per task: softmax over num_experts
task_outs: concatenate task outputs along the last dimension -> (batch_size, num_tasks)
```

### PLE

| Parameter | Meaning |
| --- | --- |
| `shared_expert_num` | Number of task-shared experts. Native coverage uses values equal to `specific_expert_num`. |
| `specific_expert_num` | Number of task-specific experts per task. |
| `num_levels` | Number of CGC levels. |
| `expert_dnn_hidden_units` | Hidden units for experts. |
| `gate_dnn_hidden_units` | Hidden units for gates. Empty gates are covered by native tests. |
| `tower_dnn_hidden_units` | Hidden units for final task towers. Empty towers are covered by native tests. |

Forward shape summary:

```text
input is replicated as [task_1_input, ..., task_n_input, shared_input]
each CGC level mixes task-specific and shared experts through gates
task towers produce one output per task
concatenate task outputs -> (batch_size, num_tasks)
```

## Training API quick reference

```python
model.compile(optimizer, loss=None, metrics=None)
model.fit(x, y, batch_size=None, epochs=1, validation_split=0.0, validation_data=None, callbacks=None)
model.predict(x, batch_size=256)
model.evaluate(x, y, batch_size=256)
```

MTL-specific fit behavior:

```python
# for each batch and each task i
loss = sum(loss_func[i](y_pred[:, i], y[:, i]) for i in range(num_tasks))
```

MTL-specific predict behavior:

```python
pred = model.predict(model_input, batch_size=256)
assert pred.ndim == 2
assert pred.shape[1] == len(task_names)
```

Metrics are not task-aware in the shared API; they flatten 2D arrays before calling the metric implementation. For task-level metrics, compute them after prediction using one column at a time.
