---
name: reaction-prediction
description: "Plan and troubleshoot DGL-LifeSci WLN reaction center prediction
  and candidate ranking workflows with USPTO datasets, reaction SMILES,
  candidate bond files, and rexgen-direct style commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Reaction Prediction

Use this sub-skill when a task involves DGL-LifeSci reaction prediction with Weisfeiler-Lehman Networks (WLN):

- Prepare mapped reaction SMILES inputs for reaction center prediction.
- Choose between `WLNCenterDataset`, `USPTOCenter`, `WLNRankDataset`, and `USPTORank`.
- Instantiate or reason about `WLNReactionCenter` and `WLNReactionRanking` tensors and constructor dimensions.
- Plan the rexgen-direct two-stage flow: center prediction first, candidate bond generation second, candidate product ranking last.
- Diagnose invalid reaction files, candidate-bond mismatches, reaction-size filtering, and long training/download boundaries.

## Start Here

1. Read `references/workflows.md` to decide whether the task is center prediction, candidate ranking, or the full two-stage pipeline.
2. Read `references/data-formats.md` before creating or validating reaction files, processed graph-edit files, or candidate-bond files.
3. Run `scripts/validate_reaction_inputs.py --help`, then validate tiny custom reaction fixtures before constructing WLN datasets.
4. Use `references/troubleshooting.md` when parsing, dataset construction, pretrained downloads, multiprocessing, or config compatibility fails.

## Quick Validation

Validate a custom reaction text file without training, downloads, DGL, or RDKit:

```bash
python scripts/validate_reaction_inputs.py --reactions train.txt --max-rows 100 --max-length 5000 --require-atom-maps
```

Validate candidate ranking alignment after candidate bonds have been produced:

```bash
python scripts/validate_reaction_inputs.py \
  --reactions train_valid_reactions.proc \
  --candidate-bonds train_candidate_bonds.txt \
  --processed --max-rows 200
```

## Routing Boundaries

Stay in this sub-skill for WLN reaction center prediction, WLN candidate ranking, USPTO reaction datasets, reaction SMILES with atom mapping, candidate-bond files, and rexgen-direct command planning.

Route elsewhere when the task asks for:

- Generic SMILES parsing, molecule featurizers, graph construction, or CSV datasets: use `../molecule-data-prep/SKILL.md`.
- General model constructor catalog, pretrained model naming patterns, or non-reaction model selection: use `../model-zoo-pretraining/SKILL.md`.
- Molecular property prediction train/eval workflows: use `../property-prediction/SKILL.md`.

## Bundled Resources

- `references/workflows.md`: two-stage WLN workflow, dataset/model APIs, config fields, command classes, and safety notes.
- `references/data-formats.md`: reaction SMILES, processed graph edits, candidate-bond rows, cutoffs, and validation expectations.
- `references/troubleshooting.md`: import/install, optional dependency, reaction parsing, candidate generation, config, multiprocessing, and long-run failure modes.
- `scripts/validate_reaction_inputs.py`: safe offline validator for reaction text files and candidate-bond row alignment.
