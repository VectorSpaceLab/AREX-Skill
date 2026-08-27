# Task Contract

TorchDrug tasks adapt representation models to trainable objectives. `core.Engine` treats the task as the model it trains, evaluates, checkpoints, and serializes.

## Base Interface

The base `tasks.Task` defines these hooks:

```python
class Task(torch.nn.Module):
    def preprocess(self, train_set, valid_set, test_set): ...
    def predict_and_target(self, batch, all_loss=None, metric=None): ...
    def predict(self, batch, all_loss=None, metric=None): ...
    def target(self, batch): ...
    def evaluate(self, pred, target): ...
```

The default `predict_and_target()` calls `predict(batch, all_loss, metric)` and `target(batch)`. Many tasks override it when prediction and target must be sampled together.

## Engine Lifecycle

1. User constructs a representation model.
2. User wraps the model in a task.
3. User creates `optimizer = torch.optim.Adam(task.parameters(), ...)`.
4. User constructs `core.Engine(task, train_set, valid_set, test_set, optimizer, ...)`.
5. Engine calls `task.preprocess(train_set, valid_set, test_set)` if the method exists.
6. Engine moves the task to the selected CUDA device when `gpus` is not `None` and the device is CUDA.
7. `train()` calls `task(batch)` and expects `(loss, metric)`.
8. `evaluate(split)` calls `task.predict_and_target(batch)` and then `task.evaluate(pred, target)`.

`preprocess()` can return replacement `(train_set, valid_set, test_set)` tuples. If it adds trainable parameters, Engine adds only the newly observed parameters to the existing optimizer.

## Forward Contract

A task `forward(batch)` should:

- Create `all_loss = torch.tensor(0, dtype=torch.float32, device=self.device)`.
- Create a mutable `metric = {}`.
- Call `predict(batch, all_loss, metric)` or a task-specific joint prediction routine.
- Build targets and compute one or more differentiable losses.
- Add criterion losses to `all_loss`.
- Add scalar tensors to `metric` with readable names.
- Return `(all_loss, metric)`.

Engine raises `RuntimeError("Loss doesn't require grad...")` if the returned loss has no gradient, which usually means no differentiable criterion was added or model parameters were bypassed.

## Predict / Target / Evaluate

- `predict(batch, all_loss=None, metric=None)` produces predictions. During training, `all_loss` and `metric` are mutable accumulators that submodules can update.
- `target(batch)` extracts target tensors from the batch.
- `predict_and_target(batch, all_loss=None, metric=None)` returns `(pred, target)` and is used by Engine evaluation. Override it for tasks that sample masks, distances, angles, negatives, or reactants together with targets.
- `evaluate(pred, target)` returns a dictionary of metric tensors. Engine logs the returned metrics under `train/epoch`, `valid/epoch`, or `test/epoch` categories.

During evaluation, Engine concatenates per-batch predictions and targets with TorchDrug utilities before calling `evaluate()`. Design `predict_and_target()` outputs so they can be concatenated across batches.

## Model Integration Pattern

Representation models typically accept graph-like inputs plus optional loss/metric accumulators and return a dictionary of representations:

```python
output = model(graph, graph.node_feature.float(), all_loss=all_loss, metric=metric)
graph_feature = output["graph_feature"]
node_feature = output["node_feature"]
```

Task wrappers then attach heads and losses. For example, property prediction uses a representation model, creates an MLP head in `preprocess()`, predicts from `output["graph_feature"]`, and reads task labels from the batch by name.

If writing a custom model, route implementation details to `layers-and-extensions`, but make sure the model exposes the attributes the task expects, such as `output_dim`, `node_output_dim`, or the representation keys used by the task.

## Configurable And Registry Requirements

To serialize a custom task or model through TorchDrug configs:

```python
from torchdrug import core, tasks
from torchdrug.core import Registry as R

@R.register("tasks.MyTask")
class MyTask(tasks.Task, core.Configurable):
    def __init__(self, model, loss_weight=1.0):
        super().__init__()
        self.model = model
        self.loss_weight = loss_weight
```

Rules:

- Inherit `core.Configurable` in the exact class whose constructor arguments should be captured.
- Register the class with a stable key such as `tasks.MyTask` or `models.MyModel`.
- Store constructor arguments as normal attributes; `Configurable` records the arguments passed to `__init__`.
- Keep non-serializable runtime state out of constructor arguments when JSON config export is required.
- Import the Python module that defines a custom registered class before loading a config that references it.

## Device Expectations

TorchDrug modules commonly use `self.device` inside task methods. Engine moves the task to CUDA when appropriate; CPU mode leaves tensors on CPU. When creating tensors inside task code, use `device=self.device` or derive the device from input tensors.

For direct prediction outside `solver.evaluate()`, the caller must move the batch to `solver.device` when using CUDA. Engine handles this movement inside `train()` and `evaluate()`.

## Choosing Task Families

Use task-specific sub-skills for detailed recipes, but keep these Engine-facing signatures in mind:

- `tasks.PropertyPrediction(model, task=(), criterion="mse", metric=("mae", "rmse"), num_mlp_layer=1, normalization=True, num_class=None, mlp_batch_norm=False, mlp_dropout=0, graph_construction_model=None, verbose=0)`.
- Knowledge graph completion tasks train on triplets and have negative-sampling/evaluation options; route details to `knowledge-graphs`.
- Molecular pretraining, generation, retrosynthesis, and protein tasks have specialized batch layouts; route details to their domain sub-skills.

## Custom Task Checklist

- Define `preprocess()` if the task needs dataset statistics, graph buffers, prediction heads, masks, or split-dependent preprocessing.
- Return updated splits from `preprocess()` only if the Engine should replace its datasets.
- Build optimizers from `task.parameters()` before Engine construction so Engine can append parameters created during preprocessing.
- Ensure `forward()` returns a gradient-carrying loss during training.
- Ensure evaluation outputs from all batches can be concatenated.
- Register and inherit `core.Configurable` if config round-trip is required.
- Save weights with `solver.save()` and save hyperparameters with `solver.config_dict()`; neither one fully replaces the other.
