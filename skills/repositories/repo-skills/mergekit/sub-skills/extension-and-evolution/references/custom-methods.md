# Custom merge methods and task graphs

## When to read this

Read this reference for a contributor change that adds a merge method or needs
fine-grained task scheduling. It is pinned to the public MergeKit 0.1.4
contracts. It covers implementation and registration; ordinary YAML method
selection and parameter precedence remain in the sibling `merge-configs`
route.

## Choose the API

| Need | API | Contract |
|---|---|---|
| One tensor transformation with scalar and per-model parameters | `@merge_method` from `mergekit.merge_methods.easy_define` | The adapter validates the supported parameter annotations, resolves configuration values, and creates a task. |
| Multiple stages, named dependencies, metadata, or custom scheduling | `MergeMethod` plus `Task` subclasses | The method creates a graph node; each task declares dependencies and executes after them. |
| A public method name in a YAML merge | Import/registry path | The defining module must be imported, and the method name must be present in `REGISTERED_MERGE_METHODS`. |

Start with the decorator. Use the class API when an operation cannot be
expressed as one function or when it needs explicit graph dependencies. Neither
API replaces the normal merge configuration contract.

## Decorator / easy-define API

The public factory is:

```python
merge_method(
    name: str,
    reference_url: str | None = None,
    pretty_name: str | None = None,
) -> Callable
```

A decorated function must have a parameter named `tensors` annotated exactly as
`List[torch.Tensor]` (the implementation inspects the runtime annotation), and
it should return one `torch.Tensor`. In this release, avoid
`from __future__ import annotations` in a decorator module: postponed
annotations become strings and do not satisfy the adapter's exact annotation
check. Use ordinary `typing.List` annotations in the function signature.

Supported user parameters are deliberately small:

- `bool`, `float`, and `int` are scalar/global parameters. A parameter without
a default is required; a default makes it optional.
- `List[float]` and `List[int]` are per-model/tensor parameters. An optional
default must be one scalar number, not a list; MergeKit broadcasts that default.
- `base_tensor` is special. Annotate it `torch.Tensor` to require a configured
base model, or `Optional[torch.Tensor]` to allow no base model.
- `output_weight` and `base_model` are special auto-populated context values
when present. Keep the documented type annotations (`WeightInfo` and
`ModelReference`/`Optional[ModelReference]`) even though the adapter's
registration check primarily dispatches by parameter name.
- Do not add arbitrary unannotated or unsupported parameter types. They are not
added to the generated configuration schema and will generally fail later when
the wrapper calls the function.

Example of a small, CPU-testable method:

```python
from typing import List

import torch
from mergekit.merge_methods.easy_define import merge_method


@merge_method(
    name="weighted_average",
    pretty_name="Weighted Average",
    reference_url="https://example.invalid/weighted-average",
)
def weighted_average(
    tensors: List[torch.Tensor],
    weight: List[float],
    normalize: bool = True,
) -> torch.Tensor:
    if not tensors:
        raise ValueError("weighted_average needs at least one tensor")
    if len(tensors) != len(weight):
        raise ValueError("one weight is required per input tensor")
    if normalize:
        total = sum(weight)
        if total == 0:
            raise ValueError("weights cannot sum to zero when normalize is true")
        weight = [value / total for value in weight]
    return sum(tensor * value for tensor, value in zip(tensors, weight))
```

The adapter passes scalar values from global configuration and collects vector
values for the input models. The callable receives tensors, not model-reference
keys. Test a two-model fixture to prove that each per-model value is paired with
the intended tensor; do not recover model identity from the callable's list.
When a `base_tensor` argument is present, model tensors exclude the base tensor
and the base tensor is passed separately. Without `base_tensor`, a configured
base tensor is included at the front of `tensors`.

The generated decorator task has these verified behaviors:

- `arguments()` returns the gathered tensor task.
- `group_label()` follows the gathered input's group label.
- `uses_accelerator()` returns `True`, so dependency tensors are moved to the
executor's math device before the function and the result is moved to storage.
- `output_weight`, `base_model`, global `parameters`, and
`tensor_parameters` are populated only when the function signature requests
them.

The decorator does not prove the returned value's shape, dtype, or semantic
meaning. A focused test must assert those properties and should reject wrong
lengths, a zero normalization denominator, and incompatible tensor shapes.

## Class-based API

Implement `MergeMethod` for complex methods. The current base contract is:

```python
class MergeMethod(ABC):
    def tensor_parameters(self) -> List[ConfigParameterDef]: ...  # default []
    def parameters(self) -> List[ConfigParameterDef]: ...         # default []
    def name(self) -> str: ...                                    # required
    def pretty_name(self) -> str | None: ...
    def reference_url(self) -> str | None: ...
    def make_task(
        self,
        *,
        output_weight: WeightInfo,
        tensors: MergeTensorInput,
        parameters: ImmutableMap[str, Any],
        tensor_parameters: ImmutableMap[
            ModelReference, ImmutableMap[str, Any]
        ],
        base_model: ModelReference | None,
    ) -> Task: ...                                               # required
```

`MergeTensorInput` is the package union of gathered tensors, permuted
embeddings, and a model-reference-to-task wrapper. Preserve it in
`make_task`; do not eagerly load model weights there.

`ConfigParameterDef` in the 0.1.4 implementation has only these fields:

```python
ConfigParameterDef(
    name: str,
    required: bool = False,
    default_value: Any = None,
)
```

Do not copy a type argument into the second positional slot from older or
informal examples: that slot is `required`, not a type declaration. Describe
parameter types in the task/config validation code that actually consumes them.

A task is a frozen Pydantic `Task[ValueT]` model. Declare its data as fields and
implement:

```python
class CustomTask(Task[torch.Tensor]):
    tensors: MergeTensorInput
    parameters: ImmutableMap[str, Any]
    tensor_parameters: ImmutableMap[
        ModelReference, ImmutableMap[str, Any]
    ]
    weight_info: WeightInfo

    def arguments(self) -> dict[str, Task]:
        return {"tensors": self.tensors}

    def priority(self) -> int:
        return 0

    def group_label(self) -> str | None:
        return self.weight_info.name

    def uses_accelerator(self) -> bool:
        return True

    def execute(
        self,
        tensors: dict[ModelReference, torch.Tensor],
    ) -> torch.Tensor:
        # Read resolved values from self.parameters and self.tensor_parameters.
        return ...
```

Every key returned by `arguments()` becomes a keyword passed to `execute()`;
keys and parameter names must match exactly. Dependencies can be custom task
objects, not just tensor gathers. `priority()` defaults to `0`; larger values
win the scheduler's within-group ordering. `group_label()` groups compatible
work when dependencies permit it. `uses_accelerator()` should be true for
matrix-heavy work and false for CPU-only bookkeeping.

The graph base also exposes `main_thread_only()` and `duplicate_per_gpu()`
policy hooks. The basic `Executor` is a dependency scheduler, not a promise of
parallel execution; do not claim that those hooks alone provide multi-GPU
placement. Route cross-device and multi-GPU execution design to the sibling
architecture route.

A class method's `make_task()` should retain the resolved `parameters`,
per-model `tensor_parameters`, `output_weight`, and optional `base_model` in
the task fields. Use an explicit dependency task for anything that must be
computed before the final tensor. Avoid hidden global state and mutable task
fields: task equality and hashing are used for graph deduplication.

## TaskUniverse and Executor

`TaskUniverse(tasks: Optional[Iterable[Task]] = None)` accepts optional initial
tasks. `add_task(task, recursive=True)` returns a `TaskHandle` and recursively
adds dependencies. Existing equal tasks are deduplicated. Handles belong to one
universe and must not be mixed across universes.

`Executor` accepts either a list of `Task` or a list of `TaskHandle` targets:

```python
Executor(
    targets,
    math_device=torch.device("cpu"),
    storage_device=torch.device("cpu"),
    cached_values=None,
)
```

The schedule is a topological order of the target closure. Shared dependencies
execute once. A task result is retained until its last scheduled use, then
released; values in `cached_values` are treated as already available and are
not scheduled again. `run()` yields only target task/value pairs, while
`execute()` runs and discards target values.

For a task whose `uses_accelerator()` is true, dependency values are recursively
moved through tensors nested in dicts, lists, and tuples to `math_device`; each
result is then moved to `storage_device`. Non-tensor values are unchanged. This
means a task's explicit dependency values are handled, but arbitrary tensor
state stored outside the graph is not. Make device assumptions explicit in
custom code and test CPU first.

A dependency cycle is invalid. The schedule builder uses a NetworkX
lexicographical topological sort and raises `networkx.NetworkXUnfeasible` for a
cycle, including a self-dependency. Missing dependency keys or a mismatched
`execute()` signature fail before a valid result is produced. Do not suppress
these errors or fall back to an unsafe partial result.

## Registration and method discovery

Decorator registration occurs when the defining module is imported:

```python
# package initialization or another guaranteed import path
from .my_method import weighted_average  # noqa: F401
```

The decorator inserts the generated method under its declared name in
`REGISTERED_MERGE_METHODS`. Import order matters. A name collision overwrites
the mapping, so use a unique name and inspect the final registry before using a
YAML configuration.

Class-based registration is explicit. Import the class and add an instance to
`STATIC_MERGE_METHODS` in the registry module. The registry then builds
`REGISTERED_MERGE_METHODS` from each method's `name()`. Keep a class method's
`name()` aligned with the YAML `merge_method` value; ordinary selection and
parameter precedence belong to `merge-configs`.

Run the bundled checker without importing model code:

```sh
python scripts/check_extension_registration.py \
  --api decorator \
  --module path/to/my_method.py \
  --import-anchor path/to/guaranteed_import.py

python scripts/check_extension_registration.py \
  --api class \
  --module path/to/my_method.py \
  --registry path/to/registry.py
```

The checker is an AST-only preflight. It catches missing decorator/task method
shapes and missing static registration/import anchors; it cannot prove tensor
outputs or execute a merge. Follow it with a small focused test using synthetic
CPU tensors and no downloaded models.

## Contributor-safe validation

- Run formatting and AST/YAML checks according to the project's contributor
  hooks; keep the change limited to the new method, its import/registry entry,
  tests, and documentation.
- Test the decorator's registration name, scalar defaults, per-model alignment,
  base-model behavior, output tensor contract, and failure paths.
- Test a class task's dependency order, shared-dependency deduplication,
  `priority()`/`group_label()` behavior where used, cached values, and CPU
  execution. Include a cyclic fixture that expects
  `networkx.NetworkXUnfeasible`.
- Do not use full checkpoints, network downloads, credentialed evaluators, or
  GPU search as registration smoke tests. A CUDA test is an additional backend
  check, not evidence that the CPU graph contract is correct.
