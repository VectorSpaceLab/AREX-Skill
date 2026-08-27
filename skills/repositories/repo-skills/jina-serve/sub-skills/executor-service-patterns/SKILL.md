---
name: executor-service-patterns
description: "Build Jina Executor services, endpoints, DocArray schemas,
  Deployments, dynamic batching, templates, and Executor troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Executor Service Patterns

Use this sub-skill when a task involves writing a Jina `Executor`, exposing `@requests` endpoints, serving a single service with `Deployment`, configuring `uses_with` or endpoint aliases, creating an Executor project, or debugging service startup/runtime errors.

## Read first

- [Executor API](references/executor-api.md) for class structure, DocArray schemas, endpoint mapping, constructor rules, and decorators.
- [Deployment recipes](references/deployment-recipes.md) for Python, YAML, and CLI ways to serve one Executor.
- [Troubleshooting](references/troubleshooting.md) for constructor, import, spawn, workspace, dynamic batching, GPU, and stateful Executor issues.
- Use [create_minimal_deployment_project.py](scripts/create_minimal_deployment_project.py) to create a self-contained starter project.
- Use [validate_executor_service.py](scripts/validate_executor_service.py) for static checks on an Executor module/YAML before running a long service.

## Minimal service

```python
from jina import Executor, Deployment, requests
from docarray import BaseDoc, DocList

class TextDoc(BaseDoc):
    text: str = ""

class UppercaseExecutor(Executor):
    @requests(on="/uppercase")
    def uppercase(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        for doc in docs:
            doc.text = doc.text.upper()
        return docs

with Deployment(uses=UppercaseExecutor, port=12345) as dep:
    out = dep.post(on="/uppercase", inputs=DocList[TextDoc]([TextDoc(text="hello")]), return_type=DocList[TextDoc])
    print(out[0].text)
```

For production, move the Executor into a module, define YAML, and start with `jina deployment --uses deployment.yml`.

## Boundary rules

- Use this sub-skill for one Executor or one Deployment. Use [orchestration-and-deployment](../orchestration-and-deployment/SKILL.md) when several Executors form a `Flow`.
- Use [client-and-protocols](../client-and-protocols/SKILL.md) for remote callers, retries, callbacks, and protocol/TLS behavior.
- Use [observability-and-production](../observability-and-production/SKILL.md) for Docker, Kubernetes, JCloud, Hub push/pull, health checks, and monitoring stack setup.
