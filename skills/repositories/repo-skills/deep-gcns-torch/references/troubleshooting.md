# Cross-Cutting Troubleshooting

## Install and import

**Symptoms:** `ModuleNotFoundError: torch_scatter` or `torch_cluster`, an
undefined symbol, or an import crash immediately after installing PyG.

**Recovery:** install PyTorch first, then install PyG extension wheels whose
Torch and CPU/CUDA tags match that exact build. Run `python scripts/check_env.py`
and `pip check`. Do not mix a CPU extension with a CUDA Torch build. The
repository has no package metadata, so its source modules are historically used
from a prepared checkout; the generated skill itself must not depend on that
checkout.

**Symptoms:** a task entry point cannot import `__init__`, `config`, `model`, or
`utils` as a dotted package.

**Recovery:** recognize this as a source-era directory-local import convention,
not a missing public package. Use a caller-owned prepared source/release copy
and its task-local execution context, or adapt the code into a normal package
before running it. Do not add a hidden checkout path to this skill.

## PyG/API drift

**Symptoms:** `GraphConv(..., conv='sage')` or `RSAGEConv` raises an inspector
inconsistent-type error or `AttributeError` for `weight`.

**Cause:** the wrapper was written for an older PyG `SAGEConv` internal contract;
modern PyG uses different linear members and message signatures.

**Recovery:** use a coherent historical PyTorch/PyG pair for exact legacy
experiments, or select the verified `edge`, `mr`, `gcn`, `gin`, or `GENConv`
paths and adapt SAGE explicitly. Do not report the SAGE route as current-backend
verified. See [graph-layer troubleshooting](../sub-skills/graph-layers/references/troubleshooting.md).

**Symptoms:** a documented flag is rejected or a parser default disagrees with
a README.

**Recovery:** use the owning workflow's parser table and `--help` output as the
authority. Historical task folders contain different generations of defaults;
do not copy flags between OGB, PPI, and point-cloud tasks.

## Data and checkpoints

**Symptoms:** a dataset starts downloading, a checkpoint path is missing, or a
state dict has unexpected keys/shapes.

**Recovery:** stop the automatic download, stage data/checkpoints through an
approved offline process, and validate dataset split, feature width, label
count, block type, convolution, depth, width, pooling, and edge encoding before
loading. Use `scripts/checkpoint_roundtrip.py` only for serialization sanity;
it cannot validate a task-specific checkpoint.

## Backend and memory

**Symptoms:** CUDA out-of-memory, KNN allocation failure, or a native extension
fails only on GPU.

**Recovery:** first run the relevant synthetic helper. For dense point clouds,
reduce batch size, point count, KNN width, or depth because matrix KNN is
quadratic in points. For sparse/OGB graphs, use the task's documented
partitioning or smaller batch while retaining feature and label contracts. If
the extension ABI is wrong, reinstall matching wheels rather than changing
model dimensions. A tiny CUDA allocation is not proof of training-scale
capacity.

## Optional surfaces

- The DGL RevGAT path is optional and needs its own DGL-CUDA/PyTorch/OGB stack;
  do not substitute PyG results or install it merely to use the core skill.
- PartNet visualization uses optional VTK/display behavior and is reference-only
  unless a caller explicitly stages OBJ output and a non-interactive renderer.
- OGB, ModelNet40, S3DIS, PartNet, and PPI may require network downloads or
  access-controlled checkpoints. Keep those side effects outside bundled
  helpers and record the exact missing prerequisite.
