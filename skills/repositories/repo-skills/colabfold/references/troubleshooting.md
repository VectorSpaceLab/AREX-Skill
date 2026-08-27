# Cross-Cutting Troubleshooting

Read this for failures that affect more than one ColabFold workflow. Use the nearest sub-skill troubleshooting reference for workflow-specific symptoms.

## `alphafold is not installed`

Symptom: `colabfold_batch` raises `RuntimeError: alphafold is not installed. Please run pip install colabfold[alphafold]`.

Likely cause: base ColabFold was installed without prediction extras.

Recovery:

1. If the task only needs MSA search, input parsing, or command planning, route away from prediction and do not install heavy extras.
2. If prediction is required, install `colabfold[alphafold]` and a compatible JAX backend.
3. Re-run a safe `colabfold_batch --help` or the batch planning helper before launching prediction.

## Missing MMseqs2 or Databases

Symptoms: `mmseqs` command not found, `Database ... does not exist`, or local search exits before creating `.a3m` outputs.

Recovery:

1. Use `sub-skills/msa-search/scripts/check_mmseqs_databases.py` to inspect the database directory.
2. Confirm whether the workflow needs public-server MSA, local CPU search, GPU search, or a dedicated MSA server.
3. Do not start database downloads unless the user approves large network/storage work.

## Public MSA Server Limits and Privacy

Symptoms: slow/failed server queries, policy concerns, or user asks for high-throughput/private sequences.

Recovery:

- Prefer serial small public-server jobs only when sequence privacy and rate are acceptable.
- Use local databases or a local MSA server for private, large, or repeated workloads.
- Split `--msa-only` and prediction phases to avoid mixing network and GPU failure modes.

## GPU/JAX/OpenMM Problems

Symptoms: JAX sees no GPU, CUDA memory errors, OpenMM GPU platform unavailable, or `gpuserver` timeout.

Recovery:

1. Verify the requested backend separately from package import success.
2. For prediction, reduce model count/recycles, use `--use-gpu-relax false` or CPU relaxation, or stage MSA generation separately.
3. For local MSA GPU search, align `CUDA_VISIBLE_DEVICES` between server and client and check database index mode.
4. For relaxation, fall back to CPU unless GPU OpenMM is specifically required and verified.

## Input/Output Boundary Confusion

Symptoms: a user asks why AF3 ligands do not receive MSAs, why output plots are missing, or why an A3M directory is treated differently from FASTA/CSV.

Recovery:

- Route input syntax and parser behavior to `inputs-and-formats`.
- Route MSA generation and AF3 JSON MSA export to `msa-search`.
- Route `colabfold_batch --af3-json` and prediction command construction to `batch-prediction`.
- Route score files, plots, citations, and relaxation to `relaxation-and-outputs`.
