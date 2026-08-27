# ST-GCN checkpoint aliases

Return to the [recognition router](../SKILL.md), then use the [CLI reference](cli-reference.md)
for test-config wiring and [troubleshooting](troubleshooting.md) for readiness
gates. The [tiny smoke](../scripts/run_stgcn_smoke.py) never resolves an alias or
downloads a checkpoint.

## Supported aliases

The checkpoint helper recognizes these exact `mmskeleton://` names:

| Alias | Intended benchmark | Matching model contract |
|---|---|---|
| `mmskeleton://st_gcn/kinetics-skeleton` | Kinetics-skeleton | `ST_GCN_18`, `in_channels: 3`, `num_class: 400`, `layout: openpose`, commonly `strategy: spatial` |
| `mmskeleton://st_gcn/ntu-xsub` | NTU RGB+D cross-subject | `ST_GCN_18`, `in_channels: 3`, `num_class: 60`, `layout: ntu-rgb+d`, commonly `strategy: spatial` |
| `mmskeleton://st_gcn/ntu-xview` | NTU RGB+D cross-view | `ST_GCN_18`, `in_channels: 3`, `num_class: 60`, `layout: ntu-rgb+d`, commonly `strategy: spatial` |

A plain filename is treated as a local checkpoint path. Pass a local path when
network access is unavailable or when the checkpoint has already been checked
for compatibility. An unknown alias is not a fallback to a guessed URL.

## Readiness checks

Before an actual test run, check all of the following independently:

1. The selected config's `num_class`, `layout`, `in_channels`, and dataset label
   vocabulary match the checkpoint's model head and input contract.
2. The dataset files and labels exist and are readable. The alias alone does
   not provide data.
3. The checkpoint is available locally, or the runtime has approved network
   access and can resolve the alias. A failed URL request is a network/cache
   issue, not evidence that the model architecture is wrong.
4. CUDA is available for the processor's `MMDataParallel(...).cuda()` path and
   the requested batch fits memory. See [troubleshooting](troubleshooting.md).

The historical model-zoo entries have reported top-1/top-5 figures in the
project documentation, but this generated skill does not claim to reproduce
them. It also does not download, carry, or verify checkpoint binaries.

## Checkpoint mismatch clues

- A classifier-head size error usually means `num_class` differs from the
  checkpoint or the wrong benchmark alias was selected.
- A reshape/adjacency failure usually means the input's `V` does not match the
  configured layout; inspect the [API shape contract](api-reference.md).
- A missing file or URL error means the checkpoint/data readiness gate is
  incomplete; do not “fix” it by changing the graph layout.
