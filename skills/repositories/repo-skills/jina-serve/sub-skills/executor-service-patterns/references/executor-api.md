# Executor API

## Class contract

An Executor is a Python class that subclasses `jina.Executor` and serves logic over DocArray documents.

```python
from jina import Executor, requests
from docarray import BaseDoc, DocList

class InputDoc(BaseDoc):
    text: str = ""

class MyExecutor(Executor):
    def __init__(self, model_name: str = "default", **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name

    @requests(on="/process")
    def process(self, docs: DocList[InputDoc], **kwargs) -> DocList[InputDoc]:
        for doc in docs:
            doc.text = doc.text.strip()
        return docs
```

Rules:

- If you define `__init__`, include `**kwargs` and call `super().__init__(**kwargs)`.
- Define Executor classes at module top level for multiprocessing/spawn compatibility.
- Use `@requests` to expose a method. `@requests` without `on=` is the default fallback handler.
- Endpoint names should start with `/`, such as `/index`, `/search`, `/generate`, or `/default`.
- Methods may be synchronous or asynchronous. Generator endpoints are possible for streaming use cases.

## Executor runtime fields

Jina injects these fields through `super().__init__(**kwargs)`:

- `self.workspace`: workspace directory for the Executor instance.
- `self.requests`: endpoint-to-method mapping.
- `self.metas`: metadata such as name/description.
- `self.runtime_args`: dynamic runtime information such as replicas, shards, and runtime name.

Do not hard-code private machine paths in these fields. Pass paths through `workspace`, config, or environment variables.

## Configuration overrides

In Python:

```python
from jina import Deployment

Deployment(
    uses="MyExecutor",
    py_modules=["executor.py"],
    uses_with={"model_name": "tiny"},
    uses_metas={"name": "text-cleaner"},
    uses_requests={"/clean": "process"},
)
```

In YAML:

```yaml
jtype: MyExecutor
py_modules:
  - executor.py
with:
  model_name: tiny
metas:
  name: text-cleaner
requests:
  /clean: process
```

## Dynamic batching and monitoring decorators

- `dynamic_batching` can batch endpoint calls for model inference; configure preferred batch size and timeout at the endpoint level.
- `monitor` instruments method-level metrics when observability support is enabled.
- Use dynamic batching only when the Executor method can safely process batches and return aligned outputs.

## Stateful Executor cautions

Stateful Executors can update internal state. For replicated consistency, state-changing endpoints may need write semantics and deterministic updates. Provide snapshot/restore methods if long-running logs could grow unbounded. Avoid stateful replicas unless the service truly needs them.
