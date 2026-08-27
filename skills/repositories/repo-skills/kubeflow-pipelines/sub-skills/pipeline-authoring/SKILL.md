---
name: pipeline-authoring
description: "Author Kubeflow Pipelines DSL components, pipelines, artifacts,
  task modifiers, control flow, and local execution smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipeline Authoring

Use this sub-skill when the task is to write, repair, or locally smoke-check Kubeflow Pipelines (KFP) v2 Python DSL code: `@dsl.component`, `@dsl.container_component`, `@dsl.pipeline`, artifact/parameter typing, task dependencies/modifiers, control flow, and KFP local execution.

## Route first

Handle here:

- Creating or fixing Python-function components with `@dsl.component`.
- Creating or fixing command/image components with `@dsl.container_component` and `dsl.ContainerSpec`.
- Composing tasks with `@dsl.pipeline`, task outputs, `.after()`, retries, caching, display names, env vars, and basic CPU/memory/accelerator modifiers.
- Using KFP artifact classes and annotations: `dsl.Input`, `dsl.Output`, `dsl.InputPath`, `dsl.OutputPath`, `dsl.Artifact`, `dsl.Dataset`, `dsl.Model`, `dsl.Metrics`, and `dsl.ClassificationMetrics`.
- Using authoring-level control flow such as `dsl.If`/`dsl.Elif`/`dsl.Else`, legacy `dsl.Condition`, `dsl.ParallelFor`, `dsl.ExitHandler`, and `dsl.OneOf`.
- Choosing and debugging `kfp.local` runners for compile-adjacent local execution smoke tests.

Route away:

- Compile flags, CLI compilation behavior, compiler output shape, PipelineSpec YAML inspection, and Kubernetes manifest output: use `compiler-and-cli`.
- Live `kfp.Client` runs, uploads, experiments, schedules, wait/list/get/delete workflows, or Registry operations: use `client-and-registry`.
- Kubernetes-specific helper APIs such as secrets, ConfigMaps, PVCs, pod labels/annotations, tolerations, affinity, image pull secrets, and security context: use `kubernetes-platform`.
- Editing this repository, generated code, frontend/backend, maintainer tests, CI, release, or source-checkout policy: use `repo-development`.

## Operating procedure

1. Identify whether the user is authoring a Python component, a container component, or the pipeline graph. If the request is mostly about compile/run/upload tooling, route before drafting code.
2. Load the smallest needed reference:
   - `references/api-reference.md` for signatures, accepted types, and task modifier behavior.
   - `references/workflows.md` for concise authoring recipes and examples.
   - `references/local-execution.md` for `kfp.local` runner setup and local-only caveats.
   - `references/troubleshooting.md` for symptom-to-fix guidance.
3. Prefer explicit type annotations. Treat missing annotations, ambiguous artifact/parameter wiring, and multiple-output access as first-class bugs.
4. Keep component body imports self-contained. Imports needed only to define the pipeline stay outside component bodies; imports needed at task runtime go inside the component function or into the runtime image/package list.
5. For artifact IO, wire producer task outputs to consumers by output key. Use `task.output` only when the task has exactly one output.
6. For local smoke checks, initialize `kfp.local` before calling components or pipelines as Python functions. Use the bundled `scripts/compile_minimal_pipeline.py` only as an authoring sanity check; route custom compile options to `compiler-and-cli`.

## Safety and verification

- Do not assume a Kubernetes cluster or KFP deployment is available for this sub-skill.
- Do not require the original source checkout, samples, or tests at runtime. Use only the installed `kfp` package and bundled files in this skill tree.
- When giving code, include the imports and component annotations needed to run or compile it from a standalone Python file.
- When suggesting local execution, state runner prerequisites and whether the flow uses lightweight Python components or container components.
- If the user asks to inspect generated YAML fields or compile with specific flags, stop authoring and route to `compiler-and-cli`.

## Quick smoke helper

From this sub-skill directory, a safe package-level compile smoke check is available:

```bash
python scripts/compile_minimal_pipeline.py --output /tmp/kfp-authoring-smoke.yaml
```

It compiles a tiny self-contained pipeline that exercises parameters, artifacts, task modifiers, control flow, and a container component. It does not contact a cluster and does not read any original repository files.
