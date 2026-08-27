---
name: pipelines-and-job-templates
description: "Route CubeStudio pipeline, job-template, Argo, and NNI/HPO workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Pipelines and job templates

Use this sub-skill for CubeStudio tasks that design, register, inspect, or debug pipeline DAGs, task templates, Argo workflow generation, NNI/HPO templates, or workflow/run-history behavior.

## Use when

- you need to author or explain a pipeline DAG, task graph, or upstream dependency chain
- you need to register or debug a job template, its Docker image, or its launch arguments
- you need to understand how a task template becomes an Argo workflow and then a run history entry
- you need to inspect NNI / hyperparameter-search templates or the built-in template catalog
- you need to reason about pipeline metrics, visualization outputs, retries, skips, or parallelism

## Start here

1. Read [references/pipeline-workflows.md](references/pipeline-workflows.md) for the end-to-end task → pipeline → workflow flow.
2. Read [references/job-template-catalog.md](references/job-template-catalog.md) for the built-in template families, directory layout, and safe build guidance.
3. Read [references/argo-and-resource-contract.md](references/argo-and-resource-contract.md) for the resource, env-var, image-pull, and workflow-field contract.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for common failures and recovery paths.
5. Before trusting a task-argument payload, run the bundled validator:

   ```bash
   python scripts/validate_job_template_args.py --help
   python scripts/validate_job_template_args.py --sample
   python scripts/validate_job_template_args.py /path/to/args.json
   ```

## Safety contract

This sub-skill is for guidance and validation. Do not run template launchers, Docker builds, image pushes, registry pulls, or live Argo submissions unless the operator has explicitly approved the side effects and environment. Treat the source job-template `build.sh` and `launcher.py` files as evidence and examples, not as generic runnable helpers.

Never run blindly: template `build.sh` scripts, job launchers, Docker image builds, registry pushes, notebook or serving deployment commands, or live pipeline submission endpoints.

## Route elsewhere

- Dataset ingestion, metadata tables, dimension tables, SQLLab engines, ETL data templates: `data-metadata-and-sqllab`
- Cluster bring-up, private registry, PVC/CRD order, offline deployment: `deploy-and-operate`
- Notebook resource selectors, GPU strings, image catalog, and monitoring: `compute-notebooks-and-images`
- Model registry, inference services, AIHub, chat, and LLM gateway settings: `serving-aihub-and-llm`
- Shared backend plumbing, auth, permissions, app startup, and frontend build/proxy changes: `backend-and-configuration`

## Expected operating output

Return a plan or explanation that makes the following clear:

- which template family or pipeline object is being discussed;
- the input schema, especially `args`, `env`, `working_dir`, `volume_mount`, `resource_*`, `timeout`, `retry`, `skip`, `parallelism`, and metrics fields;
- how the workflow is generated or interpreted;
- which bundled reference or helper to consult next;
- what failure mode is most likely when the workflow does not behave as expected.

Keep the detailed class/method tables in the bundled references, not here.
