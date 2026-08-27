---
name: cli-inference
description: "Run, script, and troubleshoot Chai-1 folding with the chai-lab
  fold CLI and chai_lab.chai1.run_inference API."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Chai-1 CLI and Inference

Use this sub-skill when the task is to run, template, script, or debug Chai-1 molecular structure prediction through `chai-lab fold` or `chai_lab.chai1.run_inference`.

## Use This For

- Constructing `chai-lab fold` commands, including device, seed, recycle, sample, and output settings.
- Writing Python inference scripts around `chai_lab.chai1.run_inference` and reading `StructureCandidates` outputs.
- Diagnosing inference setup failures: non-empty output directories, CUDA/device problems, model downloads, and long-running jobs.
- Routing advanced custom-context work to `make_all_atom_feature_context` plus `run_folding_on_context`.

## Route Elsewhere

- FASTA entity syntax, duplicate entity names, ligands, DNA/RNA, and chain-name choices: [`../input-data-formats/SKILL.md`](../input-data-formats/SKILL.md).
- MSA `.aligned.pqt`, ColabFold server, `a3m-to-pqt`, and template hit files: [`../msa-templates/SKILL.md`](../msa-templates/SKILL.md).
- Contact, pocket, covalent, and glycan restraints: [`../restraints-glycans/SKILL.md`](../restraints-glycans/SKILL.md).

## Quick Start

Install a pinned public package build or a Git build in a Linux Python 3.10+ environment:

```bash
pip install chai_lab==0.6.1
# or: pip install git+https://github.com/chaidiscovery/chai-lab.git
```

Run a minimal ESM-only fold, writing to a new or empty directory:

```bash
chai-lab fold input.fasta outputs/chai-run --seed 42 --device cuda:0
```

Print citation metadata without running inference:

```bash
chai-lab citation
```

Generate a configurable Python script template without starting a GPU job:

```bash
python scripts/write_inference_template.py \
  --fasta input.fasta \
  --output-dir outputs/chai-run \
  --script-out run_chai_inference.py \
  --device cuda:0 \
  --seed 42
```

## Runtime Expectations

- Chai-1 inference is intended for Linux, Python `>=3.10`, and a CUDA GPU with bfloat16 support; do not promise practical CPU inference.
- The default device is effectively `cuda:0` if `device` is not provided.
- Model and helper assets download automatically on first use. Set `CHAI_DOWNLOADS_DIR=/path/to/cache` when the default package-local download location is unsuitable.
- Folding can be slow and memory-intensive. Reduce `--num-diffn-samples`, `--num-diffn-timesteps`, or input size for faster/cheaper exploratory runs.
- `output_dir` must not contain existing files; create a fresh run directory or deliberately clean it before invoking inference.

## Reference Map

- [`references/inference-workflows.md`](references/inference-workflows.md): command recipes, output handling, and script templates.
- [`references/api-reference.md`](references/api-reference.md): exact Python APIs, parameters, outputs, and advanced context route.
- [`references/troubleshooting.md`](references/troubleshooting.md): common failures and safe diagnosis steps.
- [`scripts/write_inference_template.py`](scripts/write_inference_template.py): bundled helper that writes a configurable Python inference template.
