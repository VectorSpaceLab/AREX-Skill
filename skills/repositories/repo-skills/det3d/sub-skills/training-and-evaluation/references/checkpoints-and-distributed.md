# Checkpoints and Distributed Runs

Checkpoint metadata may include Det3D version, serialized config text, and
`CLASSES`. Prefer the checkpoint's classes only when the dataset and task match;
otherwise stop and resolve the mismatch.

For distributed runs, select one launcher (`pytorch`, `slurm`, or the supported
test launcher modes), set rank/world-size/master address/port consistently, and
make sure each process sees the intended GPU. NCCL errors can be caused by
wrong visibility, stale rendezvous variables, driver mismatch, or a second job
using the same port. Start with one GPU and a bounded input before scaling out.

Keep per-run artifacts separate. Do not overwrite a good checkpoint with an
unverified resume; use an explicit work directory and retain the exact config.
