---
name: cluster-pod-workflows
description: "Operate AIMET cluster and Pod workflows for GPU development,
  source builds, GenAILab runs, sync, exec, and cleanup."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# AIMET cluster and Pod workflows

Use this sub-skill when the user asks to launch or reuse AIMET GPU pods, sync an AIMET checkout to a cluster workspace, run GenAILab or source builds on a pod, pass resource requests, reconnect, list/stop workflows, or troubleshoot Argo/Kubernetes credentials.

## Read/run first

- Read [cluster and Pod workflows](../../references/cluster-pod-workflows.md) for self-contained launch, sync, exec, setup, and cleanup instructions.
- Use [cluster_pod_helper.sh](../../scripts/cluster_pod_helper.sh) for preflight, launch, sync-once, exec, list, and stop operations without depending on the original repo scripts.
- Read [GenAILab workflows](../genai-lab/SKILL.md) when the pod is being used for LLM/VLM scorecards.
- Read [install-and-build](../install-and-build/SKILL.md) when the pod is being used for AIMET source builds.

## Core workflow

1. **Preflight local tooling and auth.** Check `argo`, `kubectl`, `rsync` or `tar`, `jq`, and `kubectl auth whoami` in the chosen namespace.
2. **Launch or reuse a pod.** Choose CPU, GPU, memory, namespace, workflow template, and image before submitting a workflow.
3. **Sync the checkout.** Copy the AIMET tree to `/scratch/<repo-name>` or a specified remote directory while excluding `.git`, build outputs, virtualenvs, and GenAILab artifacts.
4. **Prepare the pod environment.** Inside the pod, run the GenAI setup or source-build wrapper appropriate to the task.
5. **Execute the bounded command.** Prefer one explicit command at a time: smoke, build, GenAILab run, pytest target, or export inspection.
6. **Clean up.** Stop workflows when the run is done, especially expensive GPU pods.

## Safety and credential boundaries

Cluster operations can mutate remote state and consume GPU quota. Do not launch, terminate, or delete pods unless the user asked for that operation. Do not paste tokens into generated logs. If the task asks for a pod but credentials are missing, report the exact missing credential/tool and the command that failed.

## Expected answer shape

For pod tasks, include namespace, template/image, resource request, local and remote directory, command to run, expected completion signal, how to reconnect, and cleanup command.
