# Chai Lab Cross-Cutting Troubleshooting

Use this reference for failures that span multiple Chai workflows. For workflow-specific issues, route to the nearest sub-skill troubleshooting file.

## Install or Import Fails

Symptoms:
- `ModuleNotFoundError: No module named 'chai_lab'`
- `chai-lab: command not found`
- Import errors for compiled packages such as `torch`, `rdkit`, `gemmi`, `tmtools`, or parquet dependencies.

Actions:
1. Confirm the public package is installed in the active environment: `python -m pip show chai_lab`.
2. Run `python scripts/check_chai_lab_environment.py --check-cli` from this skill to verify import and entry-point visibility.
3. Use Python `>=3.10`; avoid very new Python versions unless the Chai dependency stack supports them.
4. Reinstall into an isolated environment if dependency conflicts appear in `python -m pip check`.

## CUDA or Device Failures

Symptoms:
- `torch.cuda.is_available()` is false.
- Chai defaults to `cuda:0` and fails on a CPU-only machine.
- Out-of-memory errors during folding.

Actions:
1. Run `python scripts/check_chai_lab_environment.py --require-cuda` before starting a fold.
2. Pass an explicit `--device cuda:N` or `device="cuda:N"` when the default GPU is not correct.
3. Reduce input size or lower `--num-diffn-samples`, `--num-diffn-timesteps`, or trunk samples for exploratory runs.
4. Do not promise CPU inference; use CPU only for validators and non-model inspection unless the user explicitly accepts unsupported/slow experimentation.

## Model or Asset Download Problems

Symptoms:
- First fold stalls or fails while downloading model components or conformers.
- Default package-local download location is not writable or too small.

Actions:
1. Set `CHAI_DOWNLOADS_DIR` to a writable cache location with enough space before folding.
2. Pre-create the directory and ensure only one process performs first-time downloads when possible.
3. In air-gapped or restricted networks, ask the user to provide a pre-populated asset cache rather than silently retrying downloads.

## Output Directory Is Not Empty

Symptoms:
- Chai raises an assertion that `output_dir` is not empty.

Actions:
1. Use a fresh run directory for every fold.
2. If a script intentionally reuses a directory, clean it only after user confirmation because previous CIF and score outputs may be valuable.
3. The `cli-inference` helper can generate templates that fail fast by default or clean only when explicitly requested.

## Network MSA or Template Server Problems

Symptoms:
- `--use-msa-server` or `--use-templates-server` hangs or fails.
- ColabFold API limits, service availability, or local firewall/proxy issues.

Actions:
1. Use local `.aligned.pqt` files when reproducibility matters or network access is restricted.
2. Validate local MSA files with `sub-skills/msa-templates/scripts/validate_aligned_pqt.py`.
3. Treat server calls as external side effects and record the server URL used for reproducibility.

## FASTA, Restraint, MSA, or Template Data Fails Later

Route to the workflow owner:
- FASTA/entity/name/tokenization failures: `sub-skills/input-data-formats/references/troubleshooting.md`.
- `.aligned.pqt`, A3M, m8, template, or ColabFold staging failures: `sub-skills/msa-templates/references/troubleshooting.md`.
- Contact/pocket/covalent/glycan restraint failures: `sub-skills/restraints-glycans/references/troubleshooting.md`.
- Inference output, ranking, sampling, and runtime failures: `sub-skills/cli-inference/references/troubleshooting.md`.
