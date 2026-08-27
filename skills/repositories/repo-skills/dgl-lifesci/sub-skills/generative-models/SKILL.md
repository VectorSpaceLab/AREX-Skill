---
name: generative-models
description: "Plan and troubleshoot DGL-LifeSci molecular generative workflows
  with DGMG, JTVAE/JTNNVAE, vocabulary handling, reconstruction, pretraining,
  generation, and safe input validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Generative Models

Use this sub-skill when an agent needs to plan, adapt, or debug DGL-LifeSci molecular generation workflows built around `dgllife.model.DGMG`, `dgllife.model.JTNNVAE`, `dgllife.utils.JTVAEVocab`, JTVAE MolTree utilities, or JTVAE datasets/collators.

## Use This For

- Choosing between DGMG autoregressive graph generation and JTVAE/JTNNVAE junction-tree variational autoencoding.
- Preparing SMILES text inputs, DGMG atom/bond vocabularies, JTVAE vocabulary files, reconstruction inputs, and checkpoint expectations.
- Planning DGMG train/eval/generate or JTVAE pretrain/vae-train/reconstruct workflows without launching long training jobs.
- Diagnosing RDKit parseability, vocabulary mismatch, invalid generated molecules, checkpoint shape errors, and CPU/GPU/runtime issues.

## Route Elsewhere

- For generic SMILES cleaning, CSV schemas, graph featurizers, and molecule dataset basics, use `../molecule-data-prep/SKILL.md`.
- For generic model-zoo constructor inspection or pretrained model loading outside DGMG/JTVAE, use `../model-zoo-pretraining/SKILL.md`.
- For property-prediction metrics, split strategy, training loops, and supervised evaluation, use `../property-prediction/SKILL.md`.

## References

- Read [references/workflows.md](references/workflows.md) for DGMG/JTVAE planning, API entry points, CLI-style arguments, outputs, and safe/unsafe execution classes.
- Read [references/data-formats.md](references/data-formats.md) for SMILES files, DGMG atom/bond types, JTVAE vocabulary/MolTree expectations, and checkpoint contracts.
- Read [references/troubleshooting.md](references/troubleshooting.md) for import/install, optional dependencies, RDKit sensitivity, vocabulary mismatch, invalid molecules, checkpoint shape, and long-runtime failures.
- Run [scripts/validate_generative_inputs.py](scripts/validate_generative_inputs.py) to validate small SMILES fixtures and optional JTVAE vocabulary tokens without training or downloading data.

## Fast Workflow

1. Classify the task: DGMG for direct graph-generation decisions; JTVAE/JTNNVAE for junction-tree encoding, reconstruction, and latent sampling.
2. Validate user SMILES or vocabulary files with `python scripts/validate_generative_inputs.py --smiles-file molecules.txt --max-rows 100` before planning model code.
3. For JTVAE, add `--vocab-file vocab.txt` or `--derive-jtvae-vocab` to detect malformed vocabulary tokens, duplicates, and missing MolTree vocabulary tokens.
4. Check `references/workflows.md` for constructor signatures, expected checkpoint naming, and whether a requested action is safe as a smoke check or requires explicit user approval.
5. Use `references/troubleshooting.md` when RDKit, DGL, Torch, vocabulary, checkpoint, generation validity, or runtime symptoms appear.

## Version Notes

The verified installed package was `dgllife` 0.3.1 with DGL 1.1.3, CPU Torch, RDKit, scikit-learn, NumPy/SciPy, and pandas importable. Verified generative signatures included `DGMG(atom_types, bond_types, node_hidden_size=128, num_prop_rounds=2, dropout=0.2)` and `JTNNVAE(vocab, hidden_size, latent_size, depth, stereo=True)`.
