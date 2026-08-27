#!/usr/bin/env python3
"""Print safe SkyPilot infrastructure/resource/storage preflight checklists.

This helper is intentionally read-only: it does not import SkyPilot, read local
credentials, inspect kubeconfig, contact cloud APIs, or mutate infrastructure.
"""

import argparse
import textwrap
from typing import Iterable, List, Optional


CLOUD_ALIASES = {
    'k8s': 'kubernetes',
    'kubernetes': 'kubernetes',
    'slurm': 'slurm',
    'ssh': 'ssh',
}

OBJECT_STORAGE_MODES = {'mount', 'copy', 'mount_cached', 'object', 'bucket'}
VOLUME_MODES = {'volume', 'volumes', 'pvc', 'k8s-pvc', 'runpod-volume'}


def _emit_section(title: str, items: Iterable[str]) -> List[str]:
    lines = [f'\n## {title}']
    lines.extend(f'- {item}' for item in items)
    return lines


def _normalize_cloud(cloud: Optional[str]) -> Optional[str]:
    if cloud is None:
        return None
    base = cloud.split('/', 1)[0].lower()
    normalized_base = CLOUD_ALIASES.get(base, base)
    if '/' not in cloud:
        return normalized_base
    return normalized_base + '/' + cloud.split('/', 1)[1]


def _base_checklist(cloud: Optional[str], workspace: Optional[str]) -> List[str]:
    items = [
        'State the workload requirements first: accelerator, CPU, memory, disk, network ports, data size, and whether spot/preemptible is acceptable.',
        'Prefer requirements over manual provider, region, zone, context, partition, or instance-type pins unless placement is required.',
        'Use `sky launch --dryrun <task.yaml>` before a new expensive launch; route exact task YAML syntax to the task-yaml sub-skill.',
        'Do not paste secrets, kubeconfigs, SSH private keys, or cloud credential files into prompts or logs.',
    ]
    if cloud:
        check_target = cloud.split('/', 1)[0]
        items.append(f'Run `sky check {check_target}` locally and share only redacted enabled/disabled status plus error categories.')
    else:
        items.append('Run `sky check` locally to see enabled and disabled infrastructures before pinning a provider.')
    if workspace:
        items.append(f'Run `sky check --workspace {workspace}` if workspace policy may affect provider/context availability.')
    return items


def _kubernetes_checklist(cloud: str) -> List[str]:
    context_hint = ''
    if '/' in cloud:
        context_hint = f' The selected context appears to be `{cloud.split("/", 1)[1]}`.'
    return [
        f'Use `infra: k8s`/`infra: kubernetes` for the current context, or `infra: k8s/<context>` for explicit placement.{context_hint}',
        'Ask the user to run `kubectl config current-context` and `sky check kubernetes`; collect context names and redacted error categories only.',
        'For GPU workloads, run `sky gpus list --infra k8s` to verify requestable quantities and real-time utilization.',
        'If GPU labels are missing on NVIDIA nodes, use `sky gpus label`; use `sky gpus label --cleanup` after failed labeler jobs.',
        'Check namespace, service account/RBAC, quotas, node selectors, taints/tolerations, image pull access, pod priority, and PVC binding when pods stay pending.',
    ]


def _slurm_checklist(cloud: str) -> List[str]:
    parts = cloud.split('/')
    placement = []
    if len(parts) >= 2:
        placement.append(f'cluster `{parts[1]}`')
    if len(parts) >= 3:
        placement.append(f'partition `{parts[2]}`')
    placement_text = f' Pinned placement: {", ".join(placement)}.' if placement else ''
    return [
        f'Interpret `slurm/<cluster>` as a cluster pin and `slurm/<cluster>/<partition>` as a partition pin.{placement_text}',
        'Run `sky check slurm` to validate Slurm configuration, scheduler access, and SSH/controller connectivity.',
        'Run `sky gpus list --cloud slurm -v` for per-partition GPU availability and supported quantities.',
        'If container images are involved, confirm Pyxis or the configured container backend is available on the selected cluster.',
        'If object-store `MOUNT` or `MOUNT_CACHED` is involved, confirm FUSE support; otherwise consider `COPY` or explicit staging.',
    ]


def _ssh_checklist(cloud: str) -> List[str]:
    pool = cloud.split('/', 1)[1] if '/' in cloud else None
    pool_text = f' for pool `{pool}`' if pool else ''
    return [
        f'Use `infra: ssh` for any configured SSH node pool or `infra: ssh/<pool>` for a specific pool{pool_text}.',
        'Run `sky check ssh` and verify the pool was created with SkyPilot SSH node-pool setup.',
        'Do not specify a zone for SSH node pools; zones are unsupported.',
        'Verify API server/client SSH connectivity to hosts, resource capacity on hosts, and consistent host paths for host-volume mounts.',
        'For GPU hosts, confirm driver visibility and resource detection before assuming a SkyPilot catalog issue.',
    ]


def _generic_provider_checklist(cloud: str) -> List[str]:
    check_target = cloud.split('/', 1)[0]
    return [
        f'Run `sky check {check_target}` and resolve disabled-provider output before changing resource requests.',
        f'Use `sky gpus list --infra {cloud}` or `sky gpus list <GPU> --infra {cloud}` for provider-specific accelerator offerings.',
        'If quota/capacity fails after credentials pass, broaden region/zone/instance choices or use explicit fallback resources.',
        'Keep provider CLI/SDK credentials local; ask for redacted categories such as permission denied, project missing, quota exceeded, or not found.',
    ]


def _gpu_checklist(gpu: str, cloud: Optional[str]) -> List[str]:
    target = f' --infra {cloud}' if cloud and not cloud.startswith('slurm') else ''
    if cloud and cloud.startswith('slurm'):
        return [
            f'Check spelling/count for `{gpu}` with `sky gpus list --cloud slurm -v`.',
            'Compare requested quantity with per-partition requestable quantities and free utilization.',
            'If launch fails despite listing support, treat it as scheduler capacity, GRES mapping, or partition policy first.',
        ]
    if cloud and cloud.startswith('kubernetes'):
        return [
            f'Check spelling/count for `{gpu}` with `sky gpus list --infra k8s` or the selected context-specific infra.',
            'Compare requested quantity with requestable quantity per node, not just total cluster GPUs.',
            'If labels exist but resources are zero, inspect device plugin/operator health and node readiness.',
        ]
    return [
        f'Check supported accelerator spelling/count with `sky gpus list {gpu}{target}`.',
        f'Use `sky gpus list {gpu} --all-regions` only when a specific accelerator needs region-level offering details.',
        'Treat catalog support as offering evidence, not a guarantee of live quota or stock.',
    ]


def _storage_checklist(storage: str, cloud: Optional[str]) -> List[str]:
    storage_key = storage.lower().replace('-', '_')
    if storage_key in VOLUME_MODES:
        items = [
            'Confirm the user means SkyPilot volumes, not object-store `Storage` or `file_mounts`.',
            'Persistent volumes use `sky volumes apply`, `sky volumes ls`, `sky volumes delete`, then task `volumes: /mount: volume-name`.',
            'Ephemeral volumes are inline task YAML `volumes` entries and are deleted with the cluster lifecycle.',
            'For Kubernetes PVC volumes, verify `type: k8s-pvc`, `infra: k8s` or `k8s/<context>`, size, namespace, storage class, and access mode.',
            'For multi-node mounts, require a storage class and access mode that support all nodes, typically `ReadWriteMany`.',
        ]
        if cloud and not (cloud.startswith('kubernetes') or cloud.startswith('runpod')):
            items.append('Volume support is infrastructure-specific; Kubernetes PVC and RunPod are the expected volume backends.')
        return items
    if storage_key in OBJECT_STORAGE_MODES:
        return [
            'Confirm the user means object-store storage or `file_mounts`, not SkyPilot volumes.',
            '`MOUNT` is the default and usually needs FUSE/mount support on the target infrastructure.',
            '`COPY` requires a source path or cloud URI and syncs data into the cluster as regular file mounts.',
            '`MOUNT_CACHED` uses cached object-store access; check cache/writeback config and provider credentials.',
            'Use `sky storage ls` for managed storage objects and delete only named objects after confirming workspace/ownership.',
        ]
    return [
        'Classify storage as object-store `Storage`, `file_mounts`, persistent volume, ephemeral volume, or advanced Kubernetes pod volume.',
        'Check provider credentials, mount mode, destination path, source existence, FUSE support, and lifecycle ownership in that order.',
    ]


def build_checklist(args: argparse.Namespace) -> str:
    cloud = _normalize_cloud(args.cloud)
    lines = [
        '# SkyPilot Infrastructure/Storage Preflight',
        '',
        'This checklist is safe to print and share. It does not read credentials or contact cloud APIs.',
    ]
    lines.extend(_emit_section('General', _base_checklist(cloud, args.workspace)))

    if cloud:
        base = cloud.split('/', 1)[0]
        if base == 'kubernetes':
            lines.extend(_emit_section('Kubernetes', _kubernetes_checklist(cloud)))
        elif base == 'slurm':
            lines.extend(_emit_section('Slurm', _slurm_checklist(cloud)))
        elif base == 'ssh':
            lines.extend(_emit_section('SSH Node Pools', _ssh_checklist(cloud)))
        else:
            lines.extend(_emit_section('Provider', _generic_provider_checklist(cloud)))

    if args.gpu:
        lines.extend(_emit_section('GPU/Accelerator', _gpu_checklist(args.gpu, cloud)))

    if args.storage:
        lines.extend(_emit_section('Storage/Volumes', _storage_checklist(args.storage, cloud)))

    if args.include_triage:
        lines.extend(_emit_section('Failure Triage', [
            'If `sky check` disables a provider, fix credentials/tooling/workspace policy before changing resources.',
            'If `sky check` passes but launch fails, treat quota, capacity, unsupported resource, or stockout as resource-selection problems.',
            'If both disabled-cloud output and mount errors appear, fix provider/store credentials first, then mount mode and FUSE/PVC details.',
            'Route YAML field edits to task-yaml and cluster/job/service lifecycle cleanup to the relevant sibling sub-skill.',
        ]))

    return '\n'.join(lines) + '\n'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Print a safe SkyPilot infrastructure/resource/storage preflight checklist.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
            Examples:
              %(prog)s --cloud aws --gpu H100:1
              %(prog)s --cloud k8s/my-context --gpu L4:1 --storage volume --include-triage
              %(prog)s --cloud slurm/cluster-a/gpu --gpu A100:4 --storage mount
              %(prog)s --cloud ssh/my-pool --storage host-volume
        '''),
    )
    parser.add_argument(
        '--cloud',
        help='Infrastructure target, e.g. aws, gcp/us-central1, k8s/context, slurm/cluster/partition, ssh/pool.',
    )
    parser.add_argument(
        '--gpu',
        help='Accelerator request to reason about, e.g. H100:1, A100:4, L4.',
    )
    parser.add_argument(
        '--storage',
        help='Storage surface, e.g. mount, copy, mount_cached, object, volume, pvc, k8s-pvc.',
    )
    parser.add_argument(
        '--workspace',
        help='Optional SkyPilot workspace name to include in check commands.',
    )
    parser.add_argument(
        '--include-triage',
        action='store_true',
        help='Include a short disabled-cloud/capacity/storage failure triage section.',
    )
    return parser.parse_args()


def main() -> None:
    print(build_checklist(parse_args()), end='')


if __name__ == '__main__':
    main()
