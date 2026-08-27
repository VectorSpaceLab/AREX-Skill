---
name: protein-sequence-function
description: "Use for PaddleHelix protein sequence pretraining, prediction,
  protein function workflows, tokenizer/model guidance, and safe protein input
  validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Protein Sequence Function

Use this sub-skill when the task asks about PaddleHelix TAPE-style protein sequence models, protein property prediction, protein function prediction apps, protein sequence tokenization, FASTA/plain sequence validation, PPI routing, or HelixProtX high-level protein modality routing.

## Route First

- Use this sub-skill for TAPE train/eval/predict command construction, model config checks, `ProteinTokenizer` behavior, and protein sequence model-family orientation.
- Use this sub-skill for DeepFRI, ProteinSIGN, and PTHL protein function prediction command anatomy, data roles, checkpoints, and missing-argument diagnosis.
- Route biomolecular 3D structure prediction, HelixFold, and HelixFold3 input/output planning to `../structure-prediction/SKILL.md`.
- Route LinearRNA folding/partition tasks to `../linear-rna/SKILL.md`; route compound/drug workflows to `../compound-drug-discovery/SKILL.md`.
- Treat PPI S2F requests as not-yet-released in the scoped PaddleHelix evidence; explain the gap and ask whether the user wants adjacent sequence/function guidance instead.

## Safe First Steps

1. Classify the request as TAPE sequence modeling, graph-based function prediction, PPI, or HelixProtX multimodal protein routing.
2. Validate sequences and model config before constructing a training/eval/predict command.
3. Check that all user-provided data, checkpoint, graph, and label paths are explicit; do not assume app defaults are valid.
4. Confirm before starting downloads, training, GPU/distributed jobs, graph preprocessing over PDB, or HelixProtX demos.

## Bundled Helper

Use the safe validator before heavyweight commands. It performs local parsing only and never downloads data, trains, mutates checkpoints, or imports Paddle/PGL.

```bash
python sub-skills/protein-sequence-function/scripts/validate_protein_inputs.py \
  --sequence ACDJX \
  --show-token-ids
```

For TAPE prediction preflight, add `--workflow tape-predict`, `--config`, `--predict-model`, and either `--predict-data`, `--fasta`, or `--sequence`. For function-prediction checks, use `--workflow function-test` with `--model-name`, `--label-data-path`, `--test-file`, and `--protein-chain-graphs`; missing `--model-name` or `--label-data-path` is a real evaluation blocker.

## Reference Map

- `references/workflows.md`: TAPE and function-prediction command anatomy, data/checkpoint/model roles, PPI and HelixProtX routing.
- `references/data-formats.md`: sequence, tokenizer, TAPE NPZ/config, function-prediction graph and label formats.
- `references/api-reference.md`: `ProteinTokenizer`, protein sequence model class family, task heads, criteria, metrics, and dataloader orientation.
- `references/troubleshooting.md`: unknown residues, missing data/checkpoints, Paddle/PGL versions, GPU/distributed flags, and PDB graph requirements.
- `scripts/validate_protein_inputs.py`: safe local validator for FASTA/plain sequences, token IDs, TAPE configs, optional JSON/config parsing, and function workflow path checks.

## Evidence Labels

Distilled from these repo-relative evidence labels: `apps/pretrained_protein/tape/`, `apps/protein_function_prediction/`, `apps/protein_protein_interaction/`, `apps/helixprotx/`, `pahelix/utils/protein_tools.py`, `pahelix/model_zoo/protein_sequence_model.py`, and `tutorials/protein_pretrain_and_property_prediction_tutorial.ipynb`.
