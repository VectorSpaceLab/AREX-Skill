# NAS Workflows

## Core NAS Pattern

NNI NAS is organized around three objects:

1. A model space that describes candidate architectures.
2. An evaluator that trains/evaluates a sampled architecture and reports metrics.
3. A strategy that explores the model space.

Typical scaffold:

```python
from nni.nas.experiment import NasExperiment

model_space = MyModelSpace()
evaluator = make_evaluator()
strategy = make_strategy()
experiment = NasExperiment(model_space, evaluator, strategy)
experiment.config.max_trial_number = 3
experiment.config.trial_concurrency = 1
experiment.config.trial_gpu_number = 0
experiment.run(port=8081)
```

Use this as a shape, not as a promise that execution is cheap. Real NAS can launch trials, train models, download datasets if user code does so, or require GPUs.

## Build a Model Space

For PyTorch NAS, define a class that inherits `nni.nas.nn.pytorch.ModelSpace` rather than plain `torch.nn.Module`. Put candidate operations and mutable hyperparameters in `__init__`, then use them in `forward` like ordinary modules.

```python
import nni
import torch.nn as torch_nn
import torch.nn.functional as F
import nni.nas.nn.pytorch as nas_nn

class MyModelSpace(nas_nn.ModelSpace):
    def __init__(self):
        super().__init__()
        self.conv = nas_nn.LayerChoice({
            "conv3x3": torch_nn.Conv2d(16, 32, 3, padding=1),
            "conv5x5": torch_nn.Conv2d(16, 32, 5, padding=2),
        }, label="conv")
        hidden = nni.choice("hidden", [64, 128, 256])
        self.head = nas_nn.MutableLinear(hidden, 10)

    def forward(self, x):
        x = F.relu(self.conv(x))
        x = x.mean(dim=(2, 3))
        return self.head(x)
```

Model-space rules:

- Use stable manual labels such as `"conv"`, `"dropout"`, or `"cell/op_0"`; exported architecture dicts are keyed by labels.
- Use `LayerChoice` to choose one module from candidate operations.
- Use `InputChoice` to choose and reduce tensor inputs with `sum`, `mean`, `concat`, or `none`.
- Use `Repeat` to search over repeated depth; a factory function with labels like `f"block_{index}"` avoids accidental label sharing.
- Use mutable `torch.nn` wrappers such as `MutableLinear`, `MutableConv2d`, `MutableDropout`, `MutableBatchNorm2d`, and related modules when layer constructor arguments depend on `nni.choice`.
- Avoid mixing legacy mutators with inline mutation primitives in the same design.

## Choose Evaluator Type

Use `FunctionalEvaluator` when the user already has normal training code and wants full control:

```python
import nni
from nni.nas.evaluator import FunctionalEvaluator

def fit(model, train_loader, val_loader):
    train(model, train_loader)
    metric = validate(model, val_loader)
    nni.report_final_result(metric)

evaluator = FunctionalEvaluator(fit, train_loader=train_loader, val_loader=val_loader)
```

Use PyTorch Lightning evaluators when the user wants built-in classification/regression loops or one-shot strategy compatibility:

```python
import nni.nas.evaluator.pytorch as pl

evaluator = pl.Classification(
    train_dataloaders=pl.DataLoader(train_dataset, batch_size=64),
    val_dataloaders=pl.DataLoader(val_dataset, batch_size=64),
    max_epochs=10,
)
```

Evaluator selection checklist:

- `FunctionalEvaluator`: best for existing custom training loops and multi-trial strategies; expose final score with `nni.report_final_result`.
- `pl.Classification` / `pl.Regression`: convenient PyTorch Lightning wrappers; require `torch` and `pytorch_lightning`.
- `pl.Lightning`: wrap a custom `LightningModule`, `Trainer`, and dataloaders for advanced Lightning flows.
- For multi-trial execution, objects such as datasets, transforms, dataloaders, and factories may need `nni.trace` so they can be serialized into trial workers.
- When using Lightning dataloaders in NAS, prefer `nni.nas.evaluator.pytorch.DataLoader` or recursively trace custom dataloader construction.

## Choose Strategy

Multi-trial strategies train each sampled architecture independently. They are easier to reason about, can use `FunctionalEvaluator`, and can run through training services, but can be much more expensive.

- `Random`: start here for smoke tests or baselines.
- `GridSearch`: only for tiny finite spaces.
- `RegularizedEvolution`: population/evolution search for larger spaces.
- `TPE`: HPO-style search over architecture choices.
- `PolicyBasedRL`: reinforcement-learning strategy; can require extra optional packages such as `tianshou`.

One-shot strategies train a supernet or shared-weight model. They reduce search cost but impose evaluator and mutable support constraints.

- `DARTS`: differentiable architecture search.
- `GumbelDARTS`: differentiable search with Gumbel Softmax sampling.
- `ENAS`: controller-based shared-weight NAS.
- `RandomOneShot`: uniform path-sampling supernet.
- `Proxyless`: lower-memory differentiable search for Proxyless-style spaces.

Decision guide:

- Choose multi-trial when correctness, simple evaluator reuse, or distributed trial isolation matters more than raw search cost.
- Choose one-shot when the search space supports the strategy, PyTorch + Lightning are available, and the user accepts weight-sharing approximation caveats.
- Choose `Random` with low `max_trial_number` for a first end-to-end NAS smoke test.
- Choose DARTS-style one-shot only when the model space and evaluator satisfy one-shot constraints; do not pair it blindly with arbitrary mutable modules.

## Launch and Configure Experiments

`NasExperiment` auto-generates NAS-specific config. It does not use user-provided `search_space`, generic HPO `tuner`, `assessor`, or `trial_command`; the strategy and model space own architecture exploration.

Common safe knobs:

```python
experiment.config.max_trial_number = 3
experiment.config.trial_concurrency = 1
experiment.config.trial_gpu_number = 0
```

Use the HPO/experiment sub-skill for training-service YAML, platform setup, remote machine lists, or `nnictl` operations. NAS-specific execution concepts are:

- Multi-trial defaults to a training-service execution engine and simplified model format.
- One-shot defaults to sequential local execution and raw model format.
- Graph model format uses TorchScript graph IR and is required for code export or cross-graph optimization.
- Cross-graph optimization is experimental, requires graph format, remote training service, and PyTorch Lightning-compatible multi-model components.

## Export and Use Fixed Architectures

After a search, export top architectures as dictionaries:

```python
architecture = experiment.export_top_models(formatter="dict")[0]
```

Instantiate the selected architecture with `model_context`:

```python
from nni.nas.space import model_context

with model_context(architecture):
    final_model = MyModelSpace()
```

Or freeze an existing model space when appropriate:

```python
final_model = MyModelSpace().freeze(architecture)
```

Important fixed-architecture cautions:

- An exported dict records architecture choices, not fully trained final weights.
- Retrain or fully evaluate the fixed model with the desired final train/validation/test split.
- For one-shot strategies, `freeze` may preserve weights only at best effort depending on how the model space was mutated.
- `formatter="code"` is only for graph-format model spaces; otherwise use `formatter="dict"` or `formatter="instance"`.

## Adapt a DARTS-Style Search Space

DARTS-style spaces are cell-based. Typical architecture dicts include labels for normal and reduction cells, operation choices, and input choices. When adapting one:

1. Decide whether the task uses a prebuilt hub space or a custom `ModelSpace`.
2. Keep operation candidates compatible in tensor shape.
3. Label normal and reduction cell choices consistently.
4. Use `InputChoice` for selecting previous nodes and `LayerChoice` for selecting operators.
5. Search on a smaller proxy network when appropriate, then instantiate and train a fixed architecture at the target scale.

Do not imply `nni.nas.hub.pytorch.DARTS` model space and `nni.nas.strategy.DARTS` strategy must always be used together. They can be paired, but either can be replaced when compatibility is preserved.

## Benchmark and Hub Cautions

The model space hub offers prebuilt image-classification spaces such as `NasBench101`, `NasBench201`, `NASNet`, `ENAS`, `AmoebaNet`, `PNAS`, `DARTS`, `ProxylessNAS`, `MobileNetV3Space`, `ShuffleNetSpace`, and `AutoFormer`. Use them as starting points or searched-model loaders when the user accepts their task/domain assumptions.

Benchmark query APIs such as `query_nb101_trial_stats`, `query_nb201_trial_stats`, and `query_nds_trial_stats` require local benchmark databases and `peewee`. Download commands and benchmark databases can be large; ask before downloading data or running benchmark preparation.
