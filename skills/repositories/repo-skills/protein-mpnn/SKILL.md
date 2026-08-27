---
name: protein-mpnn
description: "Use ProteinMPNN to design protein sequences from backbones,
  prepare constraint JSONL inputs, interpret scores/probability outputs, retrain
  models, and use custom checkpoints in a local ProteinMPNN checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ProteinMPNN

Use this skill when a user is working in or around a ProteinMPNN checkout and needs help with sequence design, scoring, constraint preparation, output interpretation, retraining, or custom checkpoints.

## What This Skill Covers

- Running `protein_mpnn_run.py` for single-PDB and parsed-JSONL design workflows.
- Preparing helper JSONL inputs for designed chains, fixed positions, tied positions, bias, omit masks, and PSSM-guided design.
- Choosing vanilla, soluble, CA-only, or custom checkpoint weights.
- Interpreting generated FASTA headers, score/probability NPZ files, and output folders.
- Validating training data layout, adapting training commands, and routing custom checkpoints back into inference.

## Minimum Runtime Assumptions

ProteinMPNN is a script-style repository, not a packaged library. Future agents should assume the user has a ProteinMPNN checkout containing `protein_mpnn_run.py`, `protein_mpnn_utils.py`, `helper_scripts/`, `training/`, and any model weights they intend to use. The Python environment needs at least PyTorch and NumPy for inference; training and CIF preparation may need additional scientific dependencies.

Do not copy model checkpoints into this skill. Point ProteinMPNN commands at the user's own checkout weights or training outputs.

## Route By Task

- **Run design, scoring, or probability output**: use `sub-skills/inference-design/` for `protein_mpnn_run.py` commands, model-family choices, direct-PDB versus JSONL mode, score-only mode, probability flags, output interpretation, and runtime troubleshooting.
- **Prepare constraints or JSONL inputs**: use `sub-skills/constraint-inputs/` for `helper_scripts/` commands, parsed-PDB JSONL, chain assignment, fixed/design-only positions, tied positions, homooligomers, amino-acid bias, omit masks, PSSM dictionaries, and schema validation.
- **Train or use custom checkpoints**: use `sub-skills/training-custom-models/` for training data layout, debug training, SLURM adaptation, checkpoint naming, resume behavior, and using `--path_to_model_weights` with inference.

## Common First Questions

1. Is the user starting from one PDB file or a folder/batch of PDBs?
2. Are constraints needed before inference, such as fixed chains, tied residues, PSSM, or amino-acid bias?
3. Is the desired task sequence generation, score-only evaluation, conditional/unconditional probabilities, or training?
4. Which model family is intended: vanilla full-backbone, soluble full-backbone, CA-only, or custom checkpoint?
5. Is the run expected to be a safe dry run, CPU-compatible smoke check, or a full GPU/HPC job?

## Safe Starter Checks

Use these checks before a full design or training run:

```bash
python - <<'PY'
import numpy, torch
print('numpy', numpy.__version__)
print('torch', torch.__version__, 'cuda', torch.cuda.is_available())
PY
python protein_mpnn_run.py --help
```

For constraint files, use the validator bundled in `sub-skills/constraint-inputs/scripts/validate_constraint_jsonl.py`. For custom training data, use `sub-skills/training-custom-models/scripts/check_training_layout.py`.

## Shared References

- `references/repo-provenance.md` records the repository evidence baseline used to create this skill.
- `references/troubleshooting.md` covers cross-cutting install/import, checkout layout, dependency, and routing issues.

## Boundaries

- This skill is not a substitute for the original model code or model weights.
- Do not run long training jobs, GPU-heavy inference, network downloads, or notebook workflows unless the user explicitly asks and the environment is appropriate.
- Do not depend on source repo examples or docs as runtime skill content; use the bundled references and scripts here, then adapt commands to the user's checkout.
