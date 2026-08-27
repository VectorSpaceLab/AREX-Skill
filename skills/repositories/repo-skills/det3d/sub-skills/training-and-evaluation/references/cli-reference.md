# Training and Evaluation CLI

The source entry points accept these core forms:

```text
python tools/train.py CONFIG [--work_dir DIR] [--resume_from CKPT]
  [--validate] [--gpus N] [--seed N] [--launcher pytorch|slurm]
  [--autoscale-lr]
python tools/test.py CONFIG CHECKPOINT [--out FILE.pkl] [--json_out PREFIX]
  [--show] [--txt_result] [--launcher none|pytorch|slurm|mpi]
```

The generated skill does not require the original checkout: translate these
into the equivalent entry point in the user's Det3D checkout or package
installation. Always specify an output operation for testing (`--out`,
`--json_out`, or `--show`); the source test script asserts this.

`train.py` sets `LOCAL_RANK` when absent, derives distributed mode from the
available CUDA devices, and records `gpus` in the config. Distributed launch
also needs correct rendezvous environment variables and an appropriate launcher.
Do not run a multi-process job as a first import test.
