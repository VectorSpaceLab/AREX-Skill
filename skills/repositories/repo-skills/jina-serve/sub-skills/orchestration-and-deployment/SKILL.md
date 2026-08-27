---
name: orchestration-and-deployment
description: "Build and route Jina Flow and Gateway topologies, multi-Executor
  deployments, readiness checks, and export commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Orchestration and Deployment

Use this sub-skill when a task involves `Flow`, multiple `Deployment`s, Gateway configuration, replicas/shards, YAML topologies, readiness/profiling, or static exports to Docker Compose/Kubernetes/schema artifacts.

## Read first

- [Flow and Gateway reference](references/flow-and-gateway.md) for topology, protocol, and Gateway routing behavior.
- [YAML and export reference](references/yaml-and-export.md) for `load_config`, `save_config`, variables, schema/export commands, and deployment materialization.
- [Troubleshooting](references/troubleshooting.md) for startup, readiness, multiprocess, protocol, export, and local-vs-production topology issues.
- Use [create_minimal_flow_project.py](scripts/create_minimal_flow_project.py) to create a tiny local Flow project from scratch.
- Use [validate_flow_yaml.py](scripts/validate_flow_yaml.py) to statically inspect a Flow/Deployment YAML file.

## Quick example

```python
from jina import Flow, Executor, requests
from docarray import BaseDoc, DocList

class InputDoc(BaseDoc):
    text: str = ""

class EchoExecutor(Executor):
    @requests(on="/echo")
    def echo(self, docs: DocList[InputDoc], **kwargs) -> DocList[InputDoc]:
        for doc in docs:
            doc.text = f"echo:{doc.text}"
        return docs

flow = Flow(protocol="grpc", port=12345).add(uses=EchoExecutor)
with flow:
    flow.block()
```

## Boundaries

- Use this sub-skill for topology and deployment graphs. Use [executor-service-patterns](../executor-service-patterns/SKILL.md) for service logic inside a single Executor.
- Use [client-and-protocols](../client-and-protocols/SKILL.md) for caller-side request semantics.
- Use [observability-and-production](../observability-and-production/SKILL.md) for Docker Compose, Kubernetes, JCloud, Hub, and production observability operations that go beyond static export.
