---
name: core-runner
description: "Operate the ClawBio installation, CLI, public Python runner,
  patient profiles, output contracts, and reproducibility bundles safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core Runner

Use this sub-skill when a request concerns installing ClawBio, listing or
running a registered skill, using the stable Python API, creating or reusing a
patient profile, composing the full profile run, or interpreting run outputs
and replay metadata. This is the execution and provenance layer, not the
scientific method used by an individual domain skill.

## Route by task

- Installation, wheel-versus-checkout behavior, or public imports: read
  [api-reference.md](references/api-reference.md).
- `clawbio list`, `clawbio run`, `clawbio upload`, flags, path resolution, or
  structured failures: read [cli-reference.md](references/cli-reference.md).
- `report.md`, `result.json`, profile persistence, checksums, audit records, or
  `reproducibility/`: read
  [output-and-reproducibility.md](references/output-and-reproducibility.md).
- A failed install, missing input, stale profile, output collision, or replay:
  read [troubleshooting.md](references/troubleshooting.md).
- To inspect an already-created output without changing it, run
  [scripts/check_output_contract.py](scripts/check_output_contract.py) with
  `--help` first.

## Operating procedure

1. Confirm whether the caller has an installed package or a source checkout;
   do not assume the checkout-only skill tree is available in a wheel.
2. For a direct single-skill run, select exactly one input mode: `--demo`,
   `--input`, or a patient `--profile`. Choose a fresh, writable output
   directory for durable artifacts.
3. For personal genotype data, prefer `clawbio upload --input ...` once, then
   reuse the generated profile. Verify the profile path and checksum before a
   chain of analyses.
4. Treat `run_skill(...)` as a structured boundary: inspect `success`,
   `exit_code`, `stderr`, `output_dir`, and `files`; then inspect the promoted
   `result.json`/`report.md` fields when present. Never infer scientific
   findings from an exit code alone.
5. Require the output contract appropriate to the selected skill. The common
   contract is a report plus structured result; reproducibility files are
   skill-dependent rather than guaranteed for every run.
6. On failure, preserve the returned error and fix the stated input, profile,
   output, dependency, or timeout issue. Do not bypass the runner's per-skill
   extra-flag allowlist or pass raw patient data to network services.

## Stable contracts

The public package exports `run_skill`, `list_skills`, `upload_profile`, and
`__version__`. `list_skills()` prints a human-readable registry and returns the
registry mapping. `upload_profile(...)` creates a JSON `PatientProfile` with
parsed genotypes, source metadata, and a SHA-256 checksum. `run_skill(...)`
launches the selected registered skill and returns a structured result; the
virtual `full-profile` skill runs the configured genotype-consuming chain and
writes `pipeline_summary.json`.

Input paths are made absolute before subprocess execution. A profile can supply
the original input path when it is still present; a missing stored input does
not recreate the source data. Relative output paths resolve from the caller's
current working directory. Existing directories are reusable, but an existing
file at the output path or an uncreatable directory is a preflight failure.
Use a fresh directory when comparing replayed artifacts.

Keep these boundaries clear:

- Domain-routing skills own scientific interpretation and method choice.
- Pipeline/integration skills own network services and Nextflow behavior.
- Skill-authoring rules own how new domain skills are written.
- This sub-skill owns invocation, state transfer, output/provenance inspection,
  and safe failure handling.
