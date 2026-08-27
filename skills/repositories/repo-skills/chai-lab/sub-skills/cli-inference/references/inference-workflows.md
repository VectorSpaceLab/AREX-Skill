# Inference Workflows

This reference shows safe ways to construct Chai-1 inference commands and Python scripts. It assumes inputs are already valid Chai FASTA files; for entity syntax and validation, route to `../input-data-formats/SKILL.md`.

## Install And Check The CLI

Use a public install form rather than local editable paths:

```bash
pip install chai_lab==0.6.1
chai-lab --help
chai-lab fold --help
chai-lab citation
```

`chai-lab` is the console script exposed by the `chai_lab` distribution. The commands relevant to this sub-skill are:

| Command | Use |
| --- | --- |
| `chai-lab fold FASTA_FILE OUTPUT_DIR` | Run Chai-1 inference on a complete complex FASTA. |
| `chai-lab citation` | Print the Chai-1 citation text. |
| `chai-lab a3m-to-pqt ...` | MSA utility; route details to `../msa-templates/SKILL.md`. |

## Minimal Fold Command

```bash
mkdir -p outputs
chai-lab fold input.fasta outputs/chai-run --seed 42 --device cuda:0
```

Important output rule: `outputs/chai-run` may be absent or empty, but it must not contain old files. Chai checks this before running and raises `AssertionError: Output directory ... is not empty.`

The default path uses ESM embeddings, no MSA server, no template server, `num_trunk_recycles=3`, `num_diffn_timesteps=200`, `num_diffn_samples=5`, `num_trunk_samples=1`, and `low_memory=True`.

## Inference Controls

Use these flags to trade compute, diversity, and reproducibility:

| CLI option | Python parameter | Purpose |
| --- | --- | --- |
| `--seed INTEGER` | `seed` | Reproducible sampling seed. With multiple trunk samples, each trunk uses an incremented seed. |
| `--num-trunk-recycles INTEGER` | `num_trunk_recycles` | Number of trunk recycle passes; default `3`. |
| `--num-diffn-timesteps INTEGER` | `num_diffn_timesteps` | Diffusion denoising steps; default `200`. Lower values are faster but may reduce quality. |
| `--num-diffn-samples INTEGER` | `num_diffn_samples` | Candidate structures per trunk; default `5`. |
| `--num-trunk-samples INTEGER` | `num_trunk_samples` | Independent trunk samples; output is nested under `trunk_0`, `trunk_1`, ... when greater than one. |
| `--recycle-msa-subsample INTEGER` | `recycle_msa_subsample` | Optional MSA subsampling recycle control. Use only with MSA-aware workflows. |
| `--device TEXT` | `device` | Torch device string such as `cuda:0`. Chai defaults to `cuda:0`. |
| `--low-memory / --no-low-memory` | `low_memory` | Keep intermediate outputs on CPU when enabled; default is enabled. |
| `--fasta-names-as-cif-chains` | `fasta_names_as_cif_chains` | Use FASTA entity names as output CIF chain names. Coordinate with input/restraint naming. |

For quick dry-run scaffolding without an expensive fold, run only `chai-lab fold --help` or use `scripts/write_inference_template.py` to generate a Python script.

## MSA, Template, And Restraint Flags

The fold command accepts these integration flags, but this sub-skill only covers how they attach to inference:

```bash
chai-lab fold \
  --use-msa-server \
  --use-templates-server \
  --msa-server-url https://api.colabfold.com \
  input.fasta outputs/chai-run
```

```bash
chai-lab fold \
  --msa-directory prepared-msas \
  --template-hits-path hits.m8 \
  input.fasta outputs/chai-run
```

Route preparation and validation to sibling skills:

- `--use-msa-server`, `--msa-server-url`, `--msa-directory`, `--use-templates-server`, and `--template-hits-path`: `../msa-templates/SKILL.md`.
- `--constraint-path`: `../restraints-glycans/SKILL.md`.
- `--fasta-names-as-cif-chains` naming implications: `../input-data-formats/SKILL.md` and `../restraints-glycans/SKILL.md`.

Chai rejects conflicting MSA/template inputs in Python: do not specify both server and local MSA directory, or both server and local template path.

## Output Files

For `num_trunk_samples=1`, Chai writes outputs directly under `output_dir`:

| Output | Meaning |
| --- | --- |
| `pred.model_idx_0.cif`, ... | Candidate CIF structures, one per diffusion sample. |
| `scores.model_idx_0.npz`, ... | Ranking/confidence arrays for the corresponding candidate. |
| `msa_depth.pdf` | MSA coverage plot, only when MSA features are present. |

For `num_trunk_samples > 1`, each trunk sample writes under `output_dir/trunk_0`, `output_dir/trunk_1`, and so on. The returned `StructureCandidates.concat(...)` still combines candidates in Python.

The best candidate is available through `candidates.sorted()` or by sorting ranking aggregate scores descending.

## Safe Python Template Workflow

Generate a script template:

```bash
python scripts/write_inference_template.py \
  --fasta input.fasta \
  --output-dir outputs/chai-run \
  --script-out run_chai_inference.py \
  --device cuda:0 \
  --seed 42 \
  --num-diffn-samples 2
```

Then review and run the generated script in the target environment:

```bash
python run_chai_inference.py
```

The generated script creates or cleans the output directory only when explicitly requested via generator flags. By default, it fails fast if the output directory is non-empty, matching Chai's own expectation and avoiding accidental deletion.

## Protein + Ligand Example Command

For a FASTA containing a protein entity and a ligand SMILES entity, keep inference simple and route FASTA syntax details to `input-data-formats`:

```bash
chai-lab fold protein_ligand.fasta outputs/protein-ligand \
  --seed 7 \
  --device cuda:0 \
  --num-diffn-samples 5 \
  --num-trunk-recycles 3
```

Do not add MSA/template server flags unless the task explicitly requests network-backed MSA/template search and the environment permits it.

## Advanced Custom Context Route

Use `run_inference` for ordinary folding. Use the lower-level route only when the task requires a custom `AllAtomFeatureContext`, manually prepared embeddings/MSAs/templates/restraints, or custom context inspection:

1. Build context with `chai_lab.chai1.make_all_atom_feature_context(...)`.
2. Modify or inspect the returned `AllAtomFeatureContext` if required.
3. Fold with `chai_lab.chai1.run_folding_on_context(...)`.

Keep MSA/template construction details in `../msa-templates/SKILL.md` and restraint/glycan details in `../restraints-glycans/SKILL.md`.
