---
name: workflow-orchestration
description: "Use FedML workflow DAGs, Job subclasses, WorkflowMLOpsApi, and
  train/deploy/inference job wrappers to orchestrate dependent jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent_skill: "fedml"
license: Apache 2.0
---

# FedML Workflow Orchestration

Use this sub-skill for `fedml.workflow` DAGs, custom `Job` subclasses, `Workflow.add_job`, workflow status/output inspection, and customized job wrappers such as `TrainJob`, `ModelDeployJob`, and `ModelInferenceJob`.

## Do not use this for

- A single `fedml launch job.yaml` without dependencies: use `../launch-and-packaging/SKILL.md`.
- Plain model card deployment without a workflow DAG: use `../model-serving/SKILL.md`.
- Training-loop internals: use `../distributed-training/SKILL.md`.

## Local DAG smoke

For offline structural validation, use custom `Job` subclasses and run the bundled helper from the root skill directory:

```bash
python sub-skills/workflow-orchestration/scripts/local_workflow_smoke.py
```

The helper avoids backend workflow creation and remote launch side effects. It validates job dependencies, inputs/outputs, and status transitions.

## Core local pattern

```python
from fedml.workflow import Job, JobStatus, Workflow

class LocalJob(Job):
    def run(self):
        self.output_data_dict = {"ok": True, "inputs": self.input_data_dict}
    def status(self):
        return JobStatus.FINISHED
    def kill(self):
        pass

workflow = Workflow("demo")
a = LocalJob("prepare")
b = LocalJob("consume")
workflow.add_job(a)
workflow.add_job(b, dependencies=[a])
```

For fully offline tests, avoid `Workflow.run()` unless backend update calls are mocked. The bundled smoke manually computes metadata and executes a dependency-safe local path.

## Remote workflow path

Real workflow runs and customized jobs may call backend APIs, upload/download inputs/outputs, and launch jobs. Before using them, confirm:

- API key and backend version.
- The workflow type and name.
- Job YAML paths for `TrainJob` or deploy/inference wrappers.
- Remote side effects and resource usage are allowed.
- Output storage and cleanup expectations.

Relevant classes:

- `Workflow(name, loop=False, api_key=None, workflow_type=...)`
- `Workflow.add_job(job, dependencies=None)`
- `Workflow.run()`
- `WorkflowMLOpsApi`
- `Job` and `JobStatus`
- `TrainJob`, `ModelDeployJob`, `ModelInferenceJob`

## Evidence anchors

- `python/fedml/workflow/workflow.py` — workflow graph and execution order.
- `python/fedml/workflow/jobs.py` — `Job`/`JobStatus` contracts.
- `python/fedml/workflow/workflow_mlops_api.py` — backend workflow APIs.
- `python/fedml/workflow/customized_jobs/` — train/deploy/inference wrappers.
- `python/fedml/workflow/driver_example/` — remote workflow example.

## Cautions

- `Workflow.add_job` rejects non-`Job` objects and duplicate names.
- Cycles fail when topological order is computed.
- `Workflow.run()` updates backend workflow status, so it is not purely offline.
- Customized jobs encode inputs, launch job YAMLs, and move outputs through FedML storage; they need credentials.

## Exit criteria

A workflow-orchestration task is complete when the DAG shape, job dependencies, local-vs-remote execution path, credentials, and output handoff are explicit, and local smoke or remote workflow status is recorded.
