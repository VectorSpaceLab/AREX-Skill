---
name: fedml
description: "Use FedML for setup, CLI operations, MLOps launch, distributed and
  federated training, model serving, and workflow orchestration."
disable-model-invocation: true
metadata:
  disco-role: operating
  generated_by: "create-repo-skill"
  repo: "FedML"
  package: "fedml"
  version: "0.8.30"
  source_commit: "03e11dfee69a458a9820ec4e05b531a5f935eb2b"
license: Apache 2.0
---

# FedML Repo Skill

Use this skill when the task involves the `fedml` Python package, the `fedml` CLI, FedML/TensorOpera MLOps jobs, FedML training examples, federated-learning simulation/cross-silo workflows, model serving, or FedML workflow DAGs.

## First checks

1. Read `references/repo-provenance.md` if the task depends on the current source checkout.
2. Read `references/installation.md` before installing or repairing the package.
3. Run a minimal check in the target environment when needed:

   ```bash
   python scripts/check_install.py
   ```

4. If a command/API may contact the platform, ask before creating, stopping, killing, deploying, uploading, or launching remote resources.

## Scope

Covered:

- Python package install/import and CLI command routing.
- Account, device, cluster, run, storage, network, and environment diagnostics.
- Build/package and launch-job workflows.
- Centralized, cross-cloud, and LLM training recipes.
- Federated learning: single-process simulation, cross-silo/cross-cloud patterns, security/privacy/analytics references.
- Model cards, local serving, remote deployment, streaming inference, and inference requests.
- `fedml.workflow` DAGs and customized job wrappers.

Excluded from verified runtime coverage:

- Android, IoT, MNN/mobile client stacks.
- Maintainer release scripts and CI plumbing.
- Host-mutating MPI install scripts.
- Docker/AWS/PDSH cluster scripts unless the user explicitly asks for infrastructure setup.

## Route by task

| Task shape | Read next | Why |
| --- | --- | --- |
| Install, import, CLI help, login/logout, device binding, run/cluster/storage/env/network diagnostics | `sub-skills/setup-and-cli/SKILL.md` | Owns package setup and platform CLI basics |
| Build local packages or launch YAML-defined jobs on FedML/TensorOpera | `sub-skills/launch-and-packaging/SKILL.md` | Owns `fedml build`, `fedml launch`, and launch APIs |
| Centralized training, cross-cloud training, LLM train scripts, `FedMLRunner`, data/model loading | `sub-skills/distributed-training/SKILL.md` | Owns non-FL training pipelines |
| Simulation, cross-silo/cross-device/cross-cloud FL, algorithm flow, privacy/security/analytics examples | `sub-skills/federated-learning/SKILL.md` | Owns FL training modes and optional MPI/NCCL routing |
| Model card lifecycle, local/on-prem/cloud serving, `FedMLPredictor`, `FedMLInferenceRunner`, streaming inference | `sub-skills/model-serving/SKILL.md` | Owns deployment and inference surfaces |
| Multi-job DAGs, `Workflow`, `Job`, `TrainJob`, `ModelDeployJob`, `ModelInferenceJob` | `sub-skills/workflow-orchestration/SKILL.md` | Owns workflow dependency graphs and job wrappers |

## Shared references

- `references/cli-reference.md` — verified CLI command names and groups.
- `references/api-reference.md` — public Python APIs and network-bound calls.
- `references/workflows.md` — workflow routing map and source-script policy.
- `references/backend-matrix.md` — CPU/CUDA/MPI/remote-backend requirements.
- `references/troubleshooting.md` — import, CLI, backend, launch, training, serving, and workflow failures.
- `references/repo-routing-metadata.json` — structured router import metadata.

## Repo-specific cautions

- The current CLI command for connectivity diagnostics is `fedml network`, not `fedml diagnosis`.
- The current CLI root does not expose `fedml jobs`; use `fedml launch`, `fedml run`, or `fedml.api.launch_job`.
- MPI and NCCL examples are optional backend variants. Do not claim they are verified unless the target runtime has the needed host tools.
- `fedml model deploy`, `fedml launch`, remote `fedml.api.*` calls, storage operations, and workflow job wrappers can create or inspect remote state; require user approval and credentials.
