# Troubleshooting

These issues are common across the DiG subprojects.

## Missing datasets or checkpoints

Symptoms:
- a command fails because a dataset directory is empty
- a checkpoint path cannot be found
- the workflow talks about a SAS token or external download that was never run

Likely causes:
- the source workflow assumes data and checkpoints were downloaded already
- the files were unpacked into the wrong directory
- the source token or download URL has expired

Recovery:
- confirm the expected directory layout before any real run
- treat data and checkpoint download as an external prerequisite
- use the command renderer or reference notes when the asset is not present

## GPU and DDP issues

Symptoms:
- `nvidia-smi` sees GPUs but the DiG command still fails
- distributed launch hangs or ranks disagree
- a workflow runs too slowly on a CPU-only host

Likely causes:
- the selected workflow assumes CUDA and multiple processes
- the `CUDA_VISIBLE_DEVICES`, rank, or master-port settings do not match the run
- the host does not have the memory budget for the selected batch size

Recovery:
- choose a GPU host with enough memory for the selected workflow
- keep the process count, visible devices, and batch size aligned
- render the command first and inspect the notes before attempting execution

## Protein inference first-run delay

Symptoms:
- the first protein run appears stuck before producing outputs

Likely causes:
- the SO(3) helper array is being built for the first time

Recovery:
- wait for the first run to complete
- reuse the same environment for later runs so the cached work is not repeated

## Docker environment issues

Symptoms:
- the protein-ligand workflow cannot see the GPU inside the container
- the container starts but the workflow cannot find the mounted data

Likely causes:
- the container was started without GPU access
- the working directory was not mounted where the workflow expects it

Recovery:
- confirm GPU passthrough before starting the container
- bind-mount the subproject directory and keep the data layout stable

## Workflow naming and criterion typos

Symptoms:
- a command uses a criterion name or workflow mode that does not exist
- the render looks plausible but the source repository uses a different spelling

Likely causes:
- the DiG research code contains older naming quirks or source-specific mode names

Recovery:
- compare the rendered command against the reference notes
- do not assume every source helper is a stable public API

## When to stop and defer

These workflows are often too expensive for quick repair loops. If the data,
checkpoint, GPU, or Docker prerequisites are not available, stop after rendering
the command and hand the task to a later Researcher session.
