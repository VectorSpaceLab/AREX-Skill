---
name: chai-lab
description: "Use Chai Lab / Chai-1 for molecular structure prediction, input
  preparation, MSA/template setup, restraints, glycans, and repo-specific
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chai Lab Repo Skill

Use this skill when a task mentions Chai Lab, Chai-1, `chai_lab`, `chai-lab fold`, molecular structure prediction, protein/ligand/DNA/RNA/glycan complexes, MSA/template setup, or Chai restraint files.

## Start Here

1. Check package availability with `scripts/check_chai_lab_environment.py --help`, then run the checks that are safe for the target machine.
2. Read `references/troubleshooting.md` if install/import, CUDA, model download, network server, or output-directory failures are likely.
3. Read `references/repo-provenance.md` before refreshing this skill against a newer checkout.
4. Route to one focused sub-skill rather than trying to keep all Chai details in the root context.

## Sub-Skill Routing

- `sub-skills/cli-inference/SKILL.md`: run or template `chai-lab fold`, call `chai_lab.chai1.run_inference`, inspect `StructureCandidates`, tune sample/recycle/device options, and debug inference runtime failures.
- `sub-skills/input-data-formats/SKILL.md`: author and validate Chai FASTA records for proteins, ligands, DNA, RNA, modified residues, glycan headers, entity names, and chain-name mode decisions.
- `sub-skills/msa-templates/SKILL.md`: prepare `.aligned.pqt` files, convert A3M to Chai MSA parquet, use ColabFold server flags, prepare template m8 inputs, and stage existing ColabFold outputs.
- `sub-skills/restraints-glycans/SKILL.md`: write and validate contact, pocket, covalent, and glycan restraint CSVs, including atom notation and chain-name consistency.

## Common Public Setup

Chai Lab publishes the Python distribution `chai_lab` and import package `chai_lab`. Prefer a pinned public release when reproducibility matters:

```bash
pip install chai_lab==0.6.1
python - <<'PY'
import chai_lab
from chai_lab.chai1 import run_inference
print(chai_lab.__version__, run_inference)
PY
```

For unreleased changes, install from the public Git repository instead of mixing source files into a skill workflow:

```bash
pip install git+https://github.com/chaidiscovery/chai-lab.git
```

Chai-1 inference is intended for Linux, Python `>=3.10`, and a CUDA GPU with bfloat16 support. The package can be imported and many input validators can run without launching a fold, but practical folding should be treated as GPU-backed and potentially memory-intensive.

## High-Level Workflows

- Basic CLI fold: validate the FASTA with `sub-skills/input-data-formats/scripts/validate_chai_fasta.py`, choose a fresh output directory, then build `chai-lab fold input.fasta output_dir` with options from `sub-skills/cli-inference/SKILL.md`.
- Python inference: use `sub-skills/cli-inference/scripts/write_inference_template.py` to generate a safe script template, then add MSA/template/restraint options from sibling sub-skills.
- MSA/template-backed fold: validate `.aligned.pqt` files and template m8 inputs through `sub-skills/msa-templates/SKILL.md` before passing `--msa-directory`, `--use-msa-server`, `--use-templates-server`, or `--template-hits-path`.
- Restrained fold: validate contact, pocket, covalent, and glycan CSVs through `sub-skills/restraints-glycans/SKILL.md`, then pass the CSV as `constraint_path` or `--constraint-path`.

## Shared Checks

Run the root helper for lightweight environment and backend visibility checks:

```bash
python scripts/check_chai_lab_environment.py --json
python scripts/check_chai_lab_environment.py --require-cuda --check-cli
```

This helper imports Chai Lab, checks the CLI, reports PyTorch/CUDA visibility when PyTorch is installed, and prints `CHAI_DOWNLOADS_DIR` status. It does not download model weights or run inference.

## Important Boundaries

- Do not run full Chai inference as a cheap smoke test; use CLI `--help`, parser validators, and tiny data-format checks first.
- Do not tell future agents to open original repository examples, tests, or scripts. The useful details are distilled into this skill's references and bundled scripts.
- Keep local machine paths, private environment prefixes, cache paths, and artifact directories out of public instructions.
- Treat network-backed MSA/template generation and first-time model downloads as explicit side effects that may need user approval in restricted environments.
- When a repository checkout has changed, compare it with `references/repo-provenance.md` and refresh this skill instead of relying on stale API details.

## Reference Map

- `references/troubleshooting.md`: cross-cutting install/import, CUDA, download, output-directory, and network-service failure modes.
- `references/repo-provenance.md`: source snapshot and evidence paths used to create this skill.
- `references/repo-routing-metadata.json`: structured import metadata for `repo-skills-router`.
