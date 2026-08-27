# Model-zoo boundaries

Towhee has two related but different model surfaces:

1. The main `towhee` package, which provides pipelines, operators, runtime, service helpers, and the optional trainer bridge.
2. The optional `towhee.models` package/model zoo, which exposes deep-learning model implementations directly through Python modules.

Do not assume that installing the main `towhee` package installs every model implementation or all model-specific dependencies.

## `towhee.models` install split

The repository packages `towhee.models` separately from the main `towhee` distribution. The main install excludes deep `towhee.models` implementations, while the model package is intended for users who directly instantiate model-zoo Python modules.

Use this boundary in task planning:

| User intent | Better surface |
|---|---|
| Build a Towhee pipeline with task-oriented operators and reusable pre/post-processing. | Hub operators through the operator/pipeline workflow. |
| Create a raw model object in Python for custom training, inspection, or integration. | `towhee.models` if the needed model exists and dependencies are acceptable. |
| Avoid network/model downloads in a portability check. | Do not install or import model-zoo modules; use a config/template or tiny local `torch.nn.Module`. |
| Need exhaustive per-model signatures, weights, or benchmarks. | Treat as a new model-specific task, not this general Towhee repo skill. |

## Direct model pattern

The model README documents a consistent direct-creation pattern. Individual model modules may have additional parameters, but the high-level shape is:

```python
from towhee.models import vit

model = vit.create_model(**kwargs)
pretrained_model = vit.create_model(model_name='vit_base_16x224', pretrained=True)
```

For safe local experiments, prefer `pretrained=False` or omit pretrained flags until the user approves any weight downloads and dependency installation.

## Hub operators versus `towhee.models`

Prefer Hub operators when the user is working in a Towhee pipeline or wants task-level behavior. Operators often bundle expected preprocessing, postprocessing, schema conventions, cache behavior, and version/revision selection.

Prefer `towhee.models` when the user asks for direct access to the underlying Python model implementation, wants to fine-tune a `torch.nn.Module` with `Trainer`, or needs to compose model internals outside a Towhee pipeline.

A useful decision rule:

- If the next code line should look like `pipe.input(...).map(..., ops.namespace.operator(...)).output(...)`, route to operator and pipeline guidance.
- If the next code line should look like `from towhee.models import some_model` and `some_model.create_model(...)`, stay here and plan optional model-zoo dependencies.

## Dependency and download expectations

Model-zoo modules are PyTorch-heavy and may require packages that are not needed by the Towhee core runtime. Some model names also imply large pretrained weights, remote checkpoints, video/audio/image dependencies, or CUDA-sensitive packages. Do not use broad model-zoo tests as routine validation for this repo skill.

For controlled work:

1. Install only the package/model family the user needs.
2. Start with `pretrained=False` when a shape/API smoke is enough.
3. Record whether downloads, caches, GPU, or special media libraries are required before running model code.
4. For training, pass a real `torch.nn.Module` into `Trainer` or set it on an `NNOperator` as `self.model`/`self._model` before calling `setup_trainer(...)`.

## What this sub-skill intentionally does not cover

- Complete model list maintenance.
- Full constructor tables for every model-zoo module.
- Large pretrained-weight integration tests.
- Benchmark reproduction for individual papers/models.
- Hub operator authoring or CLI scaffolding.

Use this sub-skill to decide the correct model surface and produce safe trainer/model-zoo setup guidance; use a model-specific task for deep per-model API work.
