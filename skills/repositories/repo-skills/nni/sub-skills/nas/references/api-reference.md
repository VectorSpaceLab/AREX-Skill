# NAS API Reference

This reference names stable NAS concepts and public objects. It intentionally avoids unverified constructor signatures for APIs that require optional stacks such as `torch` or `pytorch_lightning` to import.

## Concept Map

| Concept | Role | Common objects |
| --- | --- | --- |
| Model space | Defines candidate neural architectures | `ModelSpace`, `LayerChoice`, `InputChoice`, `Repeat`, `Cell`, mutable `torch.nn` wrappers, `nni.choice` |
| Evaluator | Trains/evaluates a candidate and reports metrics | `FunctionalEvaluator`, `Evaluator`, `MutableEvaluator`, `nni.report_intermediate_result`, `nni.report_final_result` |
| Strategy | Explores model choices | `Random`, `GridSearch`, `RegularizedEvolution`, `TPE`, `PolicyBasedRL`, `DARTS`, `ENAS`, `GumbelDARTS`, `RandomOneShot`, `Proxyless` |
| Experiment | Coordinates model space, evaluator, and strategy | `NasExperiment`, `NasExperimentConfig`, `export_top_models` |
| Model format | Internal representation for mutation/execution | raw, simplified, graph, `RawFormatModelSpace`, `model_context` |
| Execution engine | Runs candidate models | training-service engine, sequential engine, CGO middleware |
| Hub / benchmarks | Prebuilt spaces and benchmark query tools | `nni.nas.hub.pytorch`, `nni.nas.benchmark.*` |

## Import Boundaries

Core NAS imports:

```python
from nni.nas.experiment import NasExperiment, NasExperimentConfig
from nni.nas.evaluator import FunctionalEvaluator
from nni.nas.space import model_context, RawFormatModelSpace
import nni.nas.strategy as strategy
```

PyTorch NAS model-space imports require `torch`:

```python
import nni.nas.nn.pytorch as nas_nn
from nni.nas.nn.pytorch import ModelSpace, LayerChoice, InputChoice, Repeat, Cell
```

PyTorch Lightning evaluator imports require both `torch` and `pytorch_lightning`:

```python
import nni.nas.evaluator.pytorch as pl
from nni.nas.evaluator.pytorch import Classification, Regression, Lightning, LightningModule, Trainer, DataLoader
```

One-shot strategies are exposed from `nni.nas.strategy`, but practical use generally requires PyTorch model spaces and Lightning-compatible evaluators.

## Model-Space Objects

### `ModelSpace`

`ModelSpace` is the PyTorch base class for NNI NAS model spaces. It behaves like a PyTorch module for authoring convenience, but the unfrozen object is not a normal final model. Use it to declare mutables and candidate structure; use `model_context` or `freeze` to instantiate a fixed architecture.

Key cautions:

- Mutables should have stable manual labels unless the class defines a label prefix.
- Unfrozen `ModelSpace.forward()` is a dry-run path and is not a reliable final model evaluation path.
- Exporting state from an unfrozen model space is not a substitute for training a fixed model or using a one-shot strategy.

### `LayerChoice`

`LayerChoice` selects one candidate module from a list or dictionary. It can be called like a normal module in `forward`.

Use it for operation choices such as convolution type, pooling type, activation blocks, or alternate residual blocks. Dictionary candidates give readable exported values such as `"conv3x3"` instead of numeric indices.

### `InputChoice`

`InputChoice` selects from candidate input tensors. It supports reductions including `sum`, `mean`, `concat`, and `none`.

Use it for cell DAG edges, skip connections, or deciding which earlier node feeds the current node. Ensure chosen tensors have compatible shapes for the selected reduction.

### `Repeat`

`Repeat` repeats a block by fixed or mutable depth. Use it for searching stack depth or repeated cells.

Cautions:

- A repeated module is deep-copied when a module instance is provided.
- Repeated `LayerChoice` labels may be shared if the repeated block is copied; use a factory with index-based labels for independent choices.
- Minimum depth can be zero in some modes, but graph-engine support is limited.

### `Cell` and Hub Modules

`Cell` expresses cell structures common in NAS literature. Hub modules include curated spaces and components such as NAS-Bench cells, DARTS, NASNet-family spaces, ProxylessNAS, MobileNetV3Space, ShuffleNetSpace, and AutoFormer.

Use hub spaces when the user wants a known image-classification search space, a pre-searched model, or a baseline for algorithm comparison. Confirm task fit before applying them to non-image or non-classification problems.

### Mutable Layer Wrappers and `nni.choice`

Use `nni.choice(label, values)` for mutable scalar choices. For PyTorch layer constructor arguments, use NNI's mutable wrappers such as `MutableLinear`, `MutableConv2d`, `MutableDropout`, `MutableBatchNorm2d`, and similar classes from `nni.nas.nn.pytorch`.

## Evaluator Objects

### `FunctionalEvaluator`

`FunctionalEvaluator(function, **kwargs)` wraps a Python function. The function receives the model as its first positional argument, plus keyword arguments supplied at evaluator construction. It should report a scalar or structured metric using NNI trial APIs.

```python
import nni
from nni.nas.evaluator import FunctionalEvaluator

def fit(model, dataloader):
    metric = train_and_validate(model, dataloader)
    nni.report_final_result(metric)

evaluator = FunctionalEvaluator(fit, dataloader=dataloader)
```

Use it when adapting existing training loops or when the task does not need one-shot Lightning integration.

### `Evaluator`, `MutableEvaluator`, and Mock Runtime

`Evaluator` is the base abstraction. Evaluators can be mutable when their arguments contain `nni.choice` or other mutables. For local checks, evaluators support mock runtime patterns so NNI trial APIs such as `get_next_parameter` and `report_final_result` can work without a full experiment.

### PyTorch Lightning Evaluators

`nni.nas.evaluator.pytorch` provides built-in task evaluators and wrappers:

- `Classification`: classification evaluator built on Lightning.
- `Regression`: regression evaluator built on Lightning.
- `Lightning`: wrapper around a custom Lightning module, trainer, and dataloaders.
- `LightningModule`: NAS-aware Lightning module base that can receive the candidate model.
- `Trainer` and `DataLoader`: traced Lightning-compatible helpers.

Use these for one-shot strategies or when a Lightning training loop is desired. If imports fail, run `scripts/check_nas_optional_deps.py` and see `troubleshooting.md`.

## Strategy Objects

### Multi-Trial Strategies

- `Random`: random architecture sampling; good for smoke tests and baselines.
- `GridSearch`: exhaustive traversal; only appropriate for tiny spaces.
- `RegularizedEvolution`: evolution-style NAS over independently evaluated models.
- `TPE`: tree-structured Parzen estimator strategy over architecture choices.
- `PolicyBasedRL`: policy-gradient/RL strategy; may require extra optional dependencies.

These strategies can work with `FunctionalEvaluator` or Lightning evaluators and often use training-service execution.

### One-Shot Strategies

- `DARTS`: differentiable architecture search over a supernet.
- `GumbelDARTS`: Gumbel Softmax variant of differentiable search.
- `ENAS`: controller-based shared-weight NAS.
- `RandomOneShot`: path-sampling shared-weight baseline.
- `Proxyless`: Proxyless-style differentiable search with lower memory design.

One-shot strategies require compatible PyTorch model spaces and Lightning-style evaluators. They may support only a subset of mutation primitives; check strategy compatibility before promising a design will run.

## Experiment Objects

### `NasExperiment`

`NasExperiment(model_space, evaluator, strategy, config=None, id=None)` is the NAS entry point. It differs from generic HPO experiments:

- `search_space` is auto-generated from the model space.
- `trial_command` is auto-set for NAS trial execution.
- There is no tuner/assessor/advisor; exploration is implemented by the NAS strategy.
- One-shot strategies run locally/sequentially by default rather than through the NNI manager.

### `export_top_models`

`experiment.export_top_models(top_k=1, formatter=...)` returns the best models known to the strategy.

- `formatter="dict"`: returns architecture choice dictionaries.
- `formatter="instance"`: returns instantiated callable models.
- `formatter="code"`: returns generated Python code only for graph-format model spaces.
- `formatter=None`: returns internal executable model-space objects.

## Fixed-Architecture Helpers

### `model_context`

`model_context(architecture_dict)` sets the choices used while constructing a model space:

```python
from nni.nas.space import model_context

with model_context(architecture):
    final_model = MyModelSpace()
```

Use this when the final model should be created from an exported architecture dict.

### `freeze`

Many model-space objects and mutable modules implement `freeze(sample)`. It returns a fixed module/model for the provided architecture sample.

Use `freeze` for simple fixed instantiation, but warn that retraining and weight handling depend on the strategy and model-space design.

## Serialization and `nni.trace`

NAS multi-trial execution may serialize model spaces, evaluators, datasets, transforms, dataloaders, and other objects into trial workers. Use `nni.trace` on custom classes/factories and recursively on objects that need clean reconstruction.

Guidelines:

- Trace datasets, transforms, dataloader factories, and custom Lightning modules when they are passed through evaluator construction.
- Prefer traced `nni.nas.evaluator.pytorch.DataLoader` for Lightning evaluators.
- Avoid serializing large untraced objects; binary pickles can be large or rejected.
- Keep downloads and dataset preparation outside minimal scaffolds unless the user explicitly asks to run them.

## Benchmark APIs

Benchmark query modules include:

```python
from nni.nas.benchmark.nasbench101 import query_nb101_trial_stats
from nni.nas.benchmark.nasbench201 import query_nb201_trial_stats
from nni.nas.benchmark.nds import query_nds_trial_stats
```

They require local benchmark databases, normally discovered from a cache directory or `NASBENCHMARK_DIR`, and `peewee` for database access. Do not download benchmark databases or run expensive benchmark preparation without user approval.
