# Deployment Recipes

## Serve a class directly in Python

```python
from jina import Deployment
from executor import MyExecutor

with Deployment(uses=MyExecutor, port=12345) as dep:
    dep.block()
```

Use this for local development and debugging.

## Serve from Deployment YAML

`deployment.yml`:

```yaml
jtype: Deployment
with:
  uses: MyExecutor
  py_modules:
    - executor.py
  port: 12345
  timeout_ready: -1
```

Run:

```bash
jina deployment --uses deployment.yml
```

## Send a local debug request

Inside the same Python process, `Deployment.post()` is convenient:

```python
from docarray import DocList, BaseDoc

with Deployment(uses=MyExecutor) as dep:
    response = dep.post(on="/", inputs=DocList[BaseDoc]([BaseDoc()]), return_type=DocList[BaseDoc])
```

For production clients, use `jina.Client` against the network endpoint.

## Executor project structure

A simple project:

```text
my_service/
  executor.py
  config.yml
  deployment.yml
  client.py
  requirements.txt
```

Use the bundled `scripts/create_minimal_deployment_project.py` to create a starter. Put model-specific dependencies in `requirements.txt` for the service project, not in global Jina documentation.

## GPU Executor pattern

Jina does not impose a GPU framework. Put device selection in the Executor:

```python
class MyGPUExec(Executor):
    def __init__(self, device: str = "cpu", **kwargs):
        super().__init__(**kwargs)
        self.device = device
```

Then pass `uses_with={"device": "cuda"}` or YAML `with.device: cuda` only when the environment includes a compatible GPU framework. For round-robin CUDA assignment across replicas, Jina can pass `CUDA_VISIBLE_DEVICES=RR`; verify the actual model framework separately.
