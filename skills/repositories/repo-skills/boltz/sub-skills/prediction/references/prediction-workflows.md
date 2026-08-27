# Prediction Workflows

## Minimal Decision Flow

1. **Choose input style.** Use YAML for new work. Use FASTA only for legacy polymer/ligand inputs that do not need affinity, templates, modifications, covalent bonds, or pocket/contact constraints.
2. **Choose MSA source.** Use `--use_msa_server` when protein MSAs are omitted. Use custom `msa` paths when the user already has `.a3m` files or paired CSV MSAs. Use `msa: empty` only when deliberately accepting lower single-sequence accuracy.
3. **Choose model/runtime.** Boltz defaults to Boltz-2. Use `--model boltz1` only for Boltz-1 compatibility. Use GPU by default; CPU runs are possible but slow.
4. **Choose output policy.** Use a dedicated `--out_dir`. Add `--override` when rerunning changed inputs into an existing output directory.
5. **Preflight validate.** Run the bundled validator before any command that may download model/cache assets or start GPU work.

## Local Preflight Without Downloads

```bash
python sub-skills/prediction/scripts/boltz_input_validator.py input.yaml --use-msa-server --check-auth
```

Useful variants:

```bash
python sub-skills/prediction/scripts/boltz_input_validator.py inputs/ --use-msa-server
python sub-skills/prediction/scripts/boltz_input_validator.py input.yaml --no-use-msa-server --out-dir predictions
python sub-skills/prediction/scripts/boltz_input_validator.py input.yaml --basic-auth --api-key --check-auth
```

The validator checks file suffixes, directory contents, YAML/FASTA shape, obvious MSA conflicts, MSA auth conflicts, `BOLTZ_CACHE` absoluteness, and expected output locations. It does not import Boltz, RDKit, PyTorch, or model weights.

## Standard Commands

### YAML with MSA Server

```bash
boltz predict input.yaml \
  --out_dir predictions \
  --use_msa_server \
  --model boltz2
```

Use this when YAML proteins omit `msa` or set `msa: null`/empty. Boltz will contact the MMSeqs2-compatible server and may need network access.

### YAML with Custom MSA

```bash
boltz predict input.yaml \
  --out_dir predictions \
  --model boltz2 \
  --max_msa_seqs 8192
```

Each protein should use one of:

```yaml
msa: ./msa/chain_a.a3m
msa: ./msa/paired_chains.csv
msa: empty
```

Do not add `--use_msa_server` for a target that intentionally uses custom MSA files. If one protein omits MSA and another provides a custom MSA, Boltz rejects the mixed auto/custom MSA target; either provide all MSAs, set all proteins to `empty`, or use the server for all omitted MSAs.

### Directory Batch

```bash
boltz predict inputs/ --out_dir predictions --use_msa_server
```

Boltz accepts a directory only when every direct child is a YAML/FASTA input. It errors on nested directories or unrelated files. Use separate directories for source inputs, MSA files, templates, and previous outputs.

### Higher Sampling / AF3-Like Settings

```bash
boltz predict input.yaml \
  --out_dir predictions \
  --use_msa_server \
  --recycling_steps 10 \
  --diffusion_samples 25 \
  --sampling_steps 200 \
  --max_parallel_samples 5
```

This is much slower and more memory intensive than defaults. Increase `--diffusion_samples` for more candidate structures; tune `--max_parallel_samples` down if GPU memory is limited.

### CPU or Kernel-Compatible Run

```bash
boltz predict input.yaml --out_dir predictions --use_msa_server --accelerator cpu
```

```bash
boltz predict input.yaml --out_dir predictions --use_msa_server --no_kernels
```

Use `--accelerator cpu` for CPU-only machines, accepting slow runtime. Use `--no_kernels` for old NVIDIA GPU or `cuequivariance`/kernel failures while keeping GPU execution.

## MSA Server Authentication

Use one auth method only.

### Basic Auth

Prefer environment variables for secrets:

```bash
export BOLTZ_MSA_USERNAME='user'
export BOLTZ_MSA_PASSWORD='secret'
boltz predict input.yaml --use_msa_server
```

CLI flags also work but may expose secrets in shell history:

```bash
boltz predict input.yaml --use_msa_server \
  --msa_server_username user \
  --msa_server_password secret
```

### API Key Auth

Prefer environment variables for values:

```bash
export MSA_API_KEY_VALUE='secret-token'
boltz predict input.yaml --use_msa_server --api_key_header X-API-Key
```

CLI flags:

```bash
boltz predict input.yaml --use_msa_server \
  --api_key_header X-Gravitee-Api-Key \
  --api_key_value secret-token
```

If both basic auth and API-key auth are provided, Boltz raises an error. If both `MSA_API_KEY_VALUE` and `--api_key_value` are set, the CLI value takes precedence.

## Affinity Prediction

Affinity is requested inside YAML, not by a standalone CLI flag:

```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: MSEQUENCE...
      msa: ./msa/target.a3m
  - ligand:
      id: L
      smiles: 'CCO'
properties:
  - affinity:
      binder: L
```

Run with Boltz-2:

```bash
boltz predict affinity.yaml --out_dir predictions --model boltz2
```

Optional affinity controls:

```bash
boltz predict affinity.yaml \
  --out_dir predictions \
  --sampling_steps_affinity 200 \
  --diffusion_samples_affinity 5 \
  --affinity_mw_correction
```

Constraints to remember:

- Affinity requires Boltz-2 input parsing.
- Only one affinity ligand is supported.
- The affinity binder must be a ligand chain, not a protein/DNA/RNA chain.
- A ligand with multiple identical copies cannot be the affinity binder.
- Very large ligands are unsupported or unreliable; Boltz raises for ligands above its hard atom limit and warns above the training-regime size.
- The output is most reliable for small-molecule/protein targets; RNA/DNA/co-factor targets may run but are not reliable.

## Cache, Checkpoints, and Downloads

Boltz downloads CCD/molecule data and model weights into `--cache`, defaulting to `~/.boltz` or `BOLTZ_CACHE` when set. `BOLTZ_CACHE` must resolve to an absolute path. For reproducible automation, pass an explicit absolute cache path:

```bash
boltz predict input.yaml --out_dir predictions --cache /absolute/cache/path --use_msa_server
```

Use `--checkpoint` to override the structure model checkpoint and `--affinity_checkpoint` to override the affinity checkpoint. Do not use custom checkpoints unless the user knows which Boltz model family they match.

## Output Refresh Policy

Without `--override`, Boltz reuses cached processed files and skips existing prediction folders. Add `--override` when input content, MSA files, template files, constraints, model settings, or output format changed but the output directory and input stem stayed the same.
