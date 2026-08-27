# AIMET cluster and Pod workflows

Use these instructions for AIMET GPU development pods, GenAILab scorecards, source builds, and cleanup. These operations require external Argo/Kubernetes credentials and may consume GPU quota.

## Preflight

```bash
scripts/cluster_pod_helper.sh preflight --namespace aihub
```

The preflight checks for `argo`, `kubectl`, `jq`, `tar`, and Kubernetes auth. If auth fails, obtain a valid kubeconfig or bearer token before launching a workflow.

## Launch a GPU pod

```bash
scripts/cluster_pod_helper.sh launch --namespace aihub -c 8 -g 1 -m 32Gi
```

Optional arguments:

- `--template <workflow-template>`: defaults to `aihub-interactive`.
- `--name <workflow-name>`: explicit Argo workflow name.
- `--docker-image <image>`: override pod image when the workflow template supports it.
- `--output pod|workflow`: print the pod name or workflow name.

Record both workflow and pod names. Use the workflow for stop/delete and the pod for exec/sync.

## Sync an AIMET checkout once

```bash
scripts/cluster_pod_helper.sh sync-once --namespace aihub --pod <pod-name> \
  --local-dir /path/to/aimet --remote-dir /scratch/aimet
```

The bundled sync excludes `.git`, `build`, `__pycache__`, `*.pyc`, `.venv`, and `GenAILab/artifacts`. It uses a tar stream rather than depending on the source repo's rsync wrapper.

## Execute a command on the pod

```bash
scripts/cluster_pod_helper.sh exec --namespace aihub --pod <pod-name> -- \
  bash -lc 'cd /scratch/aimet && python -m GenAILab --framework torch --config cfg.yaml -v'
```

For source builds on an A100 pod, use the AIMET build wrapper or the bundled build adapter with explicit CUDA architecture when `nvcc` is available:

```bash
bash scripts/environment/setup_genai.sh --skip-aimet --repo-dir /scratch/aimet
bash scripts/environment/build_aimet.sh --torch-only --cuda-arch 80 --clean --repo-dir /scratch/aimet
```

## List and stop workflows

```bash
scripts/cluster_pod_helper.sh list --namespace aihub
scripts/cluster_pod_helper.sh stop --namespace aihub <workflow-name>
```

Use `--delete` only when the user asks to delete workflow records rather than terminate running jobs.

## Troubleshooting

- Missing `argo`/`kubectl`: install those tools using your organization's normal bootstrap path; do not curl-install tools in a hidden step.
- `kubectl auth whoami` fails: kubeconfig is missing, expired, or points to the wrong cluster/namespace.
- Pod launches but sync fails: verify the pod is running, remote `/scratch` is writable, and tar is present on both sides.
- GenAILab fails on pod: verify `HF_TOKEN`, CUDA visibility, Python environment, and model memory requirements before rerunning.
