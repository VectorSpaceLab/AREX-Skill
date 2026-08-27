# Pipeline workflows

CubeStudio pipelines connect job templates, task records, DAG JSON, and Argo workflow YAML.

## Core object flow

1. `Job_Template` defines the reusable container command, arguments, environment, volume mount, and default resources.
2. `Task` binds a template to one pipeline node and stores node-specific arguments, resources, working directory, and skip/retry behavior.
3. `Pipeline` stores the DAG, scheduling policy, namespace, global environment, and parallelism.
4. `Workflow` is the generated runtime CRD object created from the pipeline and submitted to the cluster.
5. `RunHistory` records the execution instance and its status.

## Important behavior from the source

- `make_workflow_yaml(...)` creates a workflow object from a pipeline, a workflow label set, hubsecret list, and generated DAG/container templates.
- `dag_to_pipeline(...)` loads and normalizes DAG JSON, resolves task objects, renders Jinja-style variables, merges global env values, and builds container templates.
- Pipeline-level env values are rendered before task-level templates so shared variables can be referenced consistently.
- Skip behavior is encoded into the Argo DAG as a false `when` clause for skipped tasks.
- Parallelism is controlled by the pipeline field, not by the template itself.

## What future agents should look for

- `Task.args` JSON structure and how each field becomes CLI flags or container settings.
- `task.job_template.env`, `task.job_template.workdir`, `task.volume_mount`, and `task.get_node_selector()` as the source of runtime container settings.
- Argo labels and annotations for pipeline name, description, workflow name, and namespace.
- `KFJ_*` environment variables that are injected for task execution and downstream UI integration.
- How metrics and output artifacts are written back to the workspace or visualization paths.

## Common workflow shapes

- single-task debug pipeline
- feature processing or data-prep chain
- model training pipeline with a later deployment step
- example / demo job-template pipelines shipped with the repository
- NNI or hyperparameter-search templates

## Best paired reference files

- `job-template-catalog.md` for the built-in template families and args schema
- `argo-and-resource-contract.md` for resource, environment, and workflow field semantics
- `troubleshooting.md` for DAG, Argo, image-pull, and metrics failures

## Native evidence to keep in mind

- `job-template/README.md` describes the template directory layout and args schema.
- The repository's model and view classes expose many pipeline and job-template route methods, so the UI route layer is part of the workflow contract.
- Seed JSON under `myapp/init/` contains sample pipeline definitions such as vision, ML, deepseek, and task-specific examples.
