# Troubleshooting Chai-1 Inference

Use safe checks first. `chai-lab --help`, `chai-lab fold --help`, `chai-lab citation`, import checks, and template generation do not run expensive folding. Actual `fold` or `run_inference` calls may download assets, use the network when server flags are enabled, and require a CUDA GPU.

## Output Directory Is Not Empty

Symptom:

```text
AssertionError: Output directory ... is not empty.
```

Cause: `run_inference` refuses to write into a directory that already contains files.

Fix:

```bash
run_id=$(date +%Y%m%d-%H%M%S)
chai-lab fold input.fasta "outputs/chai-${run_id}" --device cuda:0 --seed 42
```

Or in Python:

```python
if output_dir.exists() and any(output_dir.iterdir()):
    raise SystemExit(f"Refusing to overwrite non-empty output directory: {output_dir}")
```

Only remove an old output directory when the user explicitly approves deletion.

## CUDA Or Device Failures

Symptoms can include missing CUDA, invalid device strings, out-of-memory errors, or failures while loading TorchScript model components.

Checklist:

```bash
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
print("cuda devices", torch.cuda.device_count())
if torch.cuda.is_available():
    print("device 0", torch.cuda.get_device_name(0))
PY
```

Guidance:

- Prefer `--device cuda:0` or `device="cuda:0"` when a CUDA GPU is available.
- Do not claim CPU inference is a supported practical path. The code can construct `torch.device(...)`, but Chai-1 inference is documented for CUDA/bfloat16-capable GPUs.
- Keep `low_memory=True` unless the task specifically asks to optimize speed and the GPU has enough memory.
- For memory pressure, reduce `--num-diffn-samples`, `--num-diffn-timesteps`, or input size before changing model internals.

## Model Or Helper Downloads

Chai downloads model components and helper data automatically when first used. The download destination defaults to a package-local `downloads` area unless `CHAI_DOWNLOADS_DIR` is set.

Use a stable cache path when package-local writes are unsuitable:

```bash
export CHAI_DOWNLOADS_DIR="$HOME/.cache/chai-lab-downloads"
chai-lab fold input.fasta outputs/chai-run --device cuda:0
```

If downloads fail:

- Check outbound HTTPS access to Chai asset URLs.
- Check free disk space in `CHAI_DOWNLOADS_DIR`.
- Check file permissions on the cache directory.
- Re-run after a partial download failure; Chai uses lock files and temporary files around downloads.

Do not embed local cache paths in shared scripts or public instructions; use an environment variable placeholder.

## Missing Or Broken Install

Symptoms:

```text
chai-lab: command not found
ModuleNotFoundError: No module named 'chai_lab'
```

Check:

```bash
python - <<'PY'
import chai_lab
print(chai_lab.__version__)
PY
python -m pip show chai_lab
```

Fix with a public install in the active environment:

```bash
python -m pip install chai_lab==0.6.1
```

The console script is named `chai-lab`; the import package is `chai_lab`.

## MSA Or Template Option Conflicts

Symptoms:

```text
AssertionError: Cannot specify both MSA server and directory
AssertionError: Cannot specify both templates server and path
```

Cause: Chai accepts either generated server data or local prepared data for each route, not both.

Fix:

- Server route: use `--use-msa-server` and optionally `--use-templates-server`.
- Local route: use `--msa-directory prepared-msas` and/or `--template-hits-path hits.m8`.
- Route preparation details to `../msa-templates/SKILL.md`.

## Duplicate FASTA Entity Names

Symptom:

```text
UnsupportedInputError: name=... used more than once in inputs. Each entity must have a unique name
```

Cause: Chai requires unique entity names during context construction.

Fix: route the FASTA file to `../input-data-formats/SKILL.md` and make every entity name unique. If `--fasta-names-as-cif-chains` is enabled, also ensure names are valid for the downstream chain-naming use case and consistent with restraint chain names.

## Long Or Expensive Jobs

Chai inference can run for a long time and may use large GPU memory, especially for large complexes or default-quality diffusion settings.

Safe reductions for exploratory runs:

```bash
chai-lab fold input.fasta outputs/quick-check \
  --device cuda:0 \
  --seed 42 \
  --num-diffn-samples 1 \
  --num-diffn-timesteps 50 \
  --num-trunk-recycles 1
```

Be clear that these settings are for fast smoke checks or template validation, not best-quality production predictions.

## ESM, MSA, And Network Side Effects

Default inference uses ESM embeddings and no MSA/template server. Network side effects occur when:

- Model/helper assets are missing and must be downloaded.
- `--use-msa-server` or `use_msa_server=True` is enabled.
- `--use-templates-server` or `use_templates_server=True` is enabled with server-backed MSA/template search.

For offline or restricted environments:

- Pre-populate `CHAI_DOWNLOADS_DIR` with required assets if allowed.
- Use local `--msa-directory` and `--template-hits-path` only when prepared and validated.
- Avoid server flags unless the user explicitly permits network access.

## Output Files Missing Or Nested Unexpectedly

Expected direct outputs for one trunk sample:

```text
pred.model_idx_0.cif
scores.model_idx_0.npz
pred.model_idx_1.cif
scores.model_idx_1.npz
...
```

With `--num-trunk-samples` greater than one, look under:

```text
trunk_0/pred.model_idx_0.cif
trunk_1/pred.model_idx_0.cif
...
```

`msa_depth.pdf` appears only when MSA data exists.

## Citation Command

Use the no-GPU citation command when the task asks how to cite Chai-1:

```bash
chai-lab citation
```

If a user used ColabFold MMseqs2 MSA generation, include the relevant ColabFold/MMseqs2 citation in addition to Chai's citation.
