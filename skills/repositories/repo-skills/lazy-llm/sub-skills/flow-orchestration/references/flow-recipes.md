# Flow Recipes

## Sequential pipeline

Use `pipeline` for left-to-right composition.

```python
import lazyllm

def add_one(x):
    return x + 1

result = lazyllm.pipeline(add_one, add_one)(1)
assert result == 3
```

Use a context manager when you need named stages or nested flows:

```python
from lazyllm import pipeline, bind

def length(text):
    return len(text)

def format_result(n, original):
    return {"length": n, "original": original}

with pipeline() as p:
    p.length = length
    p.format = format_result | bind(original=p.input)
```

## Parallel fan-out

`parallel` sends the same input to multiple functions and returns a tuple by default.

```python
from lazyllm import parallel

p = parallel(lambda x: x + 1, lambda x: x * 2)
assert p(3) == (4, 6)
```

Named stages can be selected with `_skip_items` or `_kept_items`:

```python
with parallel() as p:
    p.inc = lambda x: x + 1
    p.double = lambda x: x * 2
    p.square = lambda x: x * x

assert p(3, _kept_items=["inc", "square"]) == (4, 9)
```

Do not provide `_skip_items` and `_kept_items` together.

## Diverter

Use `diverter` when each callable consumes a separate input value.

```python
from lazyllm import diverter

d = diverter(lambda x: x + 1, lambda x: x * 2, lambda x: -x)
assert d(1, 2, 3) == (2, 4, -3)
```

Named diverters can return dictionaries with `.asdict` and can map dict inputs by key.

## Conditional routes

Use `switch` when multiple predicates choose actions:

```python
from lazyllm import switch

is_one = lambda x: x == 1
is_two = lambda x: x == 2
sw = switch({is_one: lambda x: x * 2, is_two: lambda x: x * 3, "default": lambda x: x}, judge_on_full_input=True)
assert sw(2) == 6
```

Use `ifs(condition, true_action, false_action)` for simple branches. Callable condition failures propagate as real errors, so use them for validation when needed.

## Loops

Use `loop(action, count=N)` for fixed iterations or `loop(stop_condition=...)` for dynamic termination. Keep actions deterministic during debugging and set a bounded count or stop condition before swapping in model calls.

## Binding inputs and prior outputs

`bind` is the primary way to use the original pipeline input or earlier stage outputs as parameters to later callables. When debugging `bind`, print or assert each stage's shape with ordinary callables first.

## Flow nodes that call other LazyLLM systems

- Model modules: configure and smoke-check in model-deployment first.
- RAG retrievers/rerankers: build local document/index smoke in rag-document-processing first.
- Agents/tools: register deterministic tools in agents-tools first.
- Writer artifacts: validate local artifact round-trip in writer-review first.

This separation prevents provider/GPU/service failures from hiding pure flow shape bugs.
