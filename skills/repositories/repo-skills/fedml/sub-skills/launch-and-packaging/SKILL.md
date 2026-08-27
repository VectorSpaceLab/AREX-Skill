---
name: launch-and-packaging
description: "Build FedML client/server packages, validate job YAML, and launch
  jobs on FedML/TensorOpera with explicit credential and side-effect control."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent_skill: "fedml"
license: Apache 2.0
---

# FedML Launch and Packaging

Use this sub-skill for `fedml build`, `fedml train build`, `fedml federate build`, `fedml launch`, and the Python launch/build APIs.

## Do not use this for

- Basic login/run/cluster/storage CLI tasks: use `../setup-and-cli/SKILL.md`.
- Training-loop implementation details: use `../distributed-training/SKILL.md`.
- Model card lifecycle and predictor code: use `../model-serving/SKILL.md`.
- Multi-job workflow DAGs: use `../workflow-orchestration/SKILL.md`.

## Preflight checklist

1. Read `../../references/cli-reference.md#launch-and-build`.
2. Read `../../references/backend-matrix.md#workflow-backend-requirements`.
3. Locate the job YAML and workspace/entry point it references.
4. Run the bundled YAML preflight helper when a local YAML file is available:

   ```bash
   python sub-skills/launch-and-packaging/scripts/validate_job_yaml.py path/to/job.yaml
   ```

5. Decide whether the requested action is **package-only** or **remote launch**.

## Package-only route

Package-only tasks are safe if they do not upload or launch remote resources.

Use one of:

```bash
fedml build --help
fedml train build --help
fedml federate build --help
```

Python API equivalents:

```python
import fedml.api
fedml.api.fedml_build(platform, type, source_folder, entry_point, config_folder, dest_folder, ignore)
fedml.api.train_build(job_yaml_file, dest_folder)
fedml.api.federate_build(job_yaml_file, dest_folder)
```

## Remote launch route

Remote launch tasks require explicit approval because they can consume platform resources.

Before launching, confirm:

- API key or logged-in context.
- Backend version (`release`, `test`, `dev`, or `local`).
- Cluster or resource target, if any.
- Whether auto-created clusters/resources are allowed.
- How logs/status should be inspected after launch.

CLI and API entry points:

```bash
fedml launch job.yaml
fedml launch job.yaml -k <api-key> -c <cluster-name>
```

```python
import fedml.api
result = fedml.api.launch_job("job.yaml", api_key="...")
result = fedml.api.launch_job_on_cluster("job.yaml", cluster="my-cluster", api_key="...")
```

A successful `LaunchResult` exposes `result_code`, `result_msg`, `run_id`, `project_id`, and sometimes `inner_id` for serving endpoints.

## Repo-specific cautions

- The verified CLI root does not expose `fedml jobs`; older docs may mention `fedml jobs start`.
- Build/package can be local; launch and run inspection are backend-bound.
- Resource matching errors usually reflect YAML resource requests, cluster state, or account/provider availability.
- Original Docker/AWS/PDSH scripts are reference-only unless the user explicitly asks for that infrastructure setup.

## Exit criteria

A launch/packaging task is complete when the YAML/workspace is validated, package-vs-launch intent is clear, any remote side effects are approved, and launch/build outputs or blocking errors are recorded with run ids when available.
