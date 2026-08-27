# Inference workflow

Use this workflow to decide whether and how to run OmegaFold inference safely.

## 1. Validate without downloads

Run the bundled smoke helper before any full inference:

```bash
python scripts/omegafold_cli_smoke.py
```

The helper checks that `omegafold` is on `PATH`, runs `omegafold --help` with a timeout, and reports recognized flags. This does not instantiate the model or download weights.

For a FASTA-specific dry run:

```bash
python scripts/omegafold_cli_smoke.py --fasta INPUT_FILE.fasta --output-dir OUTPUT_DIRECTORY --model 2 --device cuda --weights-file /path/to/model2.pt
```

The helper inspects headers and sequence lengths, predicts output PDB names, and prints the command it would run. It never calls full inference.

## 2. Check inputs and output directory

Before full inference:

- Confirm the FASTA path exists and is a file.
- Confirm each record has a header beginning with `>` or `:` and at least one following sequence line.
- Confirm the output directory path is intentional. The real CLI creates it if missing.
- For details on FASTA substitutions, invalid residues, chain sorting, and PDB naming, route to `../data-and-outputs/SKILL.md`.

## 3. Choose model and weights

Use model 1 by default:

```bash
omegafold input.fasta outputs/ --model 1
```

Use model 2 when requested or when the task wants the later release:

```bash
omegafold input.fasta outputs/ --model 2
```

For no-network or reproducible runs, provide a local checkpoint:

```bash
omegafold input.fasta outputs/ --model 2 --weights_file /path/to/model2.pt
```

Do not start full inference if the checkpoint is missing and downloads are disallowed. The CLI may download into the user cache when a default checkpoint file is absent.

## 4. Choose device

If `--device` is omitted, OmegaFold prefers CUDA, then MPS, then CPU. Use explicit devices when reproducibility or troubleshooting matters:

```bash
omegafold input.fasta outputs/ --device cuda
omegafold input.fasta outputs/ --device cuda:0
omegafold input.fasta outputs/ --device mps
omegafold input.fasta outputs/ --device cpu
```

Explicit unavailable devices fail early with `ValueError`, for example CUDA on a CPU-only host or MPS on non-Apple/non-nightly Torch setups. When a user reports mismatch failures, retry with a supported fallback only after confirming the runtime cost.

## 5. Tune resources

Start with defaults for short sequences. For long sequences or GPU OOM:

- Lower `--subbatch_size` first. Smaller values reduce memory and increase runtime.
- The README reports 4096 residues on an 80 GB A100 with `--subbatch_size 448`, but no general formula exists.
- If OOM persists, halve `--subbatch_size` and retry rather than changing model internals.
- Lower `--num_cycle` only when a speed/quality trade-off is acceptable.
- Reduce `--num_pseudo_msa` only when memory pressure remains severe and the user accepts divergence from defaults.

Example for a long FASTA on A100-class hardware:

```bash
omegafold long.fasta outputs/ --model 2 --device cuda --subbatch_size 448 --num_cycle 10 --weights_file /path/to/model2.pt
```

Example conservative fallback after OOM:

```bash
omegafold long.fasta outputs/ --model 2 --device cuda --subbatch_size 224 --num_cycle 10 --weights_file /path/to/model2.pt
```

## 6. Run and validate outputs

After full inference, expect one `.pdb` per FASTA record in the output directory. The PDB filename is derived from the record header unless the header is too long for the filesystem. Confidence values are stored in the PDB B-factor field.

Minimum post-run checks:

```bash
find outputs -maxdepth 1 -name '*.pdb' -type f -print
```

Then inspect at least one PDB for ATOM records and non-empty content. Route detailed PDB interpretation and confidence checks to `../data-and-outputs/SKILL.md`.

## When not to run full inference

Do not run full inference when:

- The task only asks whether the CLI is installed or how to build a command.
- Network downloads are disallowed and no checkpoint file exists.
- The selected accelerator is unavailable.
- The sequence is long and the user has not accepted high memory/runtime cost.
- The environment uses legacy Torch 1.12 with incompatible NumPy 2.x behavior that has not been resolved.
