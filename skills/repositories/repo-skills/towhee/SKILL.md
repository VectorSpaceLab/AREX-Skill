---
name: towhee
description: "Route Towhee pipeline, operator, data utility, service, Triton,
  training, and model-zoo tasks to self-contained workflow guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Towhee Repo Skill

Use this skill when the user asks about Towhee, x2vec, Towhee Hub operators, `towhee.pipe`, `towhee.ops`, `AutoPipes`, `AutoConfig`, `DataCollection`, `towhee server`, `APIService`, Triton packaging for Towhee pipelines, or optional Towhee training/model-zoo workflows.

Towhee 1.1.x is a Python framework for orchestrating unstructured-data pipelines over text, image, audio, video, embeddings, retrieval, service wrapping, and optional Triton deployment. This generated skill is self-contained; do not reopen the original repository checkout for normal operation.

## First checks

1. Read [installation and compatibility](references/installation-and-compatibility.md) when the task starts with install/import failures, package versions, optional dependency choices, or environment setup.
2. Run the safe root diagnostic when the user wants proof that a Towhee environment is usable:

   ```bash
   python scripts/check_towhee_environment.py --verbose
   ```

   The helper verifies imports, a local lambda pipeline, batch execution, `Entity.combine`, `APIService`, and CLI help. It does not download Hub operators, start web servers, run Docker/Triton, use GPUs, or train models.
3. Read [root troubleshooting](references/troubleshooting.md) for cross-cutting import, `pkg_resources`, Pydantic, Hub/cache, optional dependency, service, Docker, or Triton issues.
4. Read [repo provenance](references/repo-provenance.md) before deciding whether this skill is stale for a different Towhee checkout.

## Route by task

| User task | Read next |
|---|---|
| Build or debug a custom method-chained pipeline with `pipe.input(...).map(...).output(...)`, `flat_map`, `filter`, `window`, `concat`, `batch`, `debug`, `flush`, `AutoConfig`, or `AutoPipes` | [pipeline-programming](sub-skills/pipeline-programming/SKILL.md) |
| Use `ops`, register local operators, choose Hub operator revisions, validate `towhee` CLI help, or reason about `towhee init` side effects | [operator-hub-and-cli](sub-skills/operator-hub-and-cli/SKILL.md) |
| Wrap a pipeline/function as an API service, plan `towhee server`, HTTP/GRPC routes, Triton model repositories, Docker images, `build_pipeline_model`, or `build_docker_image` | [serving-and-triton](sub-skills/serving-and-triton/SKILL.md) |
| Convert pipeline results with `DataCollection`, use `Entity`, `DataLoader`, media array wrappers, display tables, serialization, visualizer, tracer, or profiler outputs | [data-utilities](sub-skills/data-utilities/SKILL.md) |
| Configure optional PyTorch training, `TrainingConfig`, `Trainer`, `NNOperator.train`, checkpoints/model cards, or decide whether to install `towhee.models` | [training-and-models](sub-skills/training-and-models/SKILL.md) |

## Common safe patterns

### Minimal local pipeline

```python
from towhee import AutoConfig, pipe

p = (
    pipe.input('x')
        .map('x', 'y', lambda x: x + 1, config=AutoConfig.LocalCPUConfig())
        .output('y')
)
print(p(2).get())  # [3]
```

Start with local lambdas/callables to validate schema and graph shape before introducing Hub operators, model downloads, Triton, or training.

### Hub/model operators

Hub operators are accessed through `ops`, for example `ops.image_embedding.timm(...)` or `ops.namespace.operator(...)`. Treat Hub resolution as potentially networked and dependency-installing. Pin revisions when reproducibility matters and use the operator/CLI sub-skill for local registration or `towhee init` guidance.

### Service and deployment

Construct `APIService` objects or `api_service.build_service(...)` before starting live HTTP/GRPC servers. Use object-level smoke checks first; only run `towhee server`, Docker, Triton, or GPU/CUDA commands after confirming ports, dependencies, artifacts, cleanup, and user approval.

### Optional training and model zoo

Towhee's training/model surfaces are optional and PyTorch-centered. Use CPU-safe config templates first. Do not import trainer/model modules in a constrained environment unless optional package installation is acceptable; Towhee dependency helpers can auto-install missing packages.

## Known compatibility flags

- Towhee 1.1.x imports `pkg_resources`; if import fails with `No module named 'pkg_resources'`, install a compatible setuptools such as `setuptools<81`.
- The repo's own test requirements use `pydantic<2`; prefer Pydantic v1 for old Towhee service workflows unless the exact Pydantic v2 path has been tested.
- GPU, Docker/Triton, live HTTP/GRPC service, Hub downloads, and real model training are optional workflow checks, not proof from a base Towhee import.
