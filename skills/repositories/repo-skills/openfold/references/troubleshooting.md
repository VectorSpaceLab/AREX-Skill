# OpenFold Cross-Cutting Troubleshooting

Read this before drilling into a specific workflow when the symptom involves installation, imports, optional dependencies, assets, external binaries, or broad runtime readiness.

## Fast Triage

1. Run `scripts/check_openfold_imports.py --json` in the target environment.
2. If core config/parser imports fail, repair the package installation before using any sub-skill workflow.
3. If model imports or CLI help fail with `attn_core_inplace_cuda`, repair the compiled/stub extension before claiming inference/training/model readiness.
4. If parameters, sequence databases, template mmCIFs, HMMER/HHSuite/Kalign binaries, CUDA, OpenMM, TensorRT, DeepSpeed, or cuEquivariance are missing, route to `sub-skills/installation-assets/`.
5. If the input problem is FASTA, MSA, mmCIF, precomputed alignments, alignment DB indexes, caches, duplicate chains, or cluster files, route to `sub-skills/data-preparation/`.

## Common Symptoms

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` while installing | Build isolation ran `setup.py` without torch, but OpenFold imports torch at build time. | Reinstall in an environment with torch available and disable build isolation for the editable/local build. |
| `ModuleNotFoundError: attn_core_inplace_cuda` | OpenFold compiled/stub attention extension is missing from import path. | Rebuild/reinstall OpenFold; use `sub-skills/installation-assets/references/troubleshooting.md` before retrying CLI/model checks. |
| CLI `--help` for inference/training crashes before argument output | Top-level imports require model modules and the extension even for help. | Fix extension/import readiness first, or use bundled dry-run command builders to plan while the environment is repaired. |
| `openmm`, `pdbfixer`, or relaxation imports fail | Relaxation dependencies are absent or incompatible. | Use `--skip_relaxation` to isolate prediction, then repair relaxation dependencies if relaxed structures are required. |
| HMMER/HHSuite/Kalign binary not found | External sequence/template-search binaries are absent or not on `PATH`. | Route install and binary-path planning to `installation-assets`; provide explicit binary paths in inference commands. |
| Parameters or databases missing | Required model weights or sequence/template databases were not downloaded or pointed to. | Use the asset planner in `installation-assets` and avoid downloads until the user approves disk/network use. |
| Precomputed alignments are ignored or reported missing | Directory root, per-query subdirectory names, or expected filenames do not match FASTA tags/mode. | Validate with `sub-skills/data-preparation/scripts/validate_alignment_layout.py` or `sub-skills/inference/scripts/validate_inference_inputs.py`. |
| Training fails before launch due to seed/distributed settings | OpenFold requires `--seed` for multi-GPU or multi-node training. | Rebuild the command with `sub-skills/training/scripts/build_training_command.py` and include a deterministic seed. |
| DeepSpeed plus precision errors | OpenFold rejects DeepSpeed with Lightning precision `16`; BF16 is usually preferred on A100-class GPUs. | Use `sub-skills/training/references/distributed-and-deepspeed.md` and choose BF16 or remove DeepSpeed. |
| TensorRT/cuEquivariance/FlashAttention import or runtime errors | Optional acceleration backend is missing or incompatible with CUDA/PyTorch/device. | Disable the optional flag or route backend installation to `installation-assets` and API-level configuration to `model-apis`. |
| CPU-only environment requested for production training | OpenFold training is documented as GPU/CUDA-dependent for practical use. | Use CPU only for import/config/data validation; do not promise full training without GPU resources. |

## Safe Checks Versus Unsafe Work

Safe by default:

- Import/config/parser checks from bundled scripts.
- Dry-run command builders.
- FASTA/alignment/cache/layout validation over tiny user-provided fixtures.
- Asset planning that prints required downloads without starting them.

Require explicit user approval:

- Downloading model parameters or sequence databases.
- Running alignment searches, MMseqs clustering, full cache generation, inference, relaxation, training, or benchmarks.
- Rebuilding CUDA extensions in a user-provided environment when it may mutate or break that environment.
- Launching cluster, Slurm, MPI, or multi-node jobs.

## Routing Examples

- “OpenFold import fails with `attn_core_inplace_cuda`” → `sub-skills/installation-assets/`.
- “Build a monomer command using precomputed alignments” → validate layout in `sub-skills/data-preparation/`, then command-build in `sub-skills/inference/`.
- “Prepare OpenProteinSet training data” → `sub-skills/data-preparation/`, then `sub-skills/training/` for command construction.
- “Convert old OpenFold weights or inspect `model_config`” → `sub-skills/model-apis/`.
