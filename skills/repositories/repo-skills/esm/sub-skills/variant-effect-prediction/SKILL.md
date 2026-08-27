---
name: variant-effect-prediction
description: "Score deep mutational scan CSVs with ESM-1v or MSA Transformer
  using wt-marginals, masked-marginals, or pseudo-ppl workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Variant Effect Prediction

Use this sub-skill when a task asks for zero-shot scoring of a deep mutational scan (DMS) CSV with ESM-1v or MSA Transformer models.

## Route Here For

- Building commands equivalent to the ESM variant prediction example with `--model-location`, `--sequence`, `--dms-input`, `--mutation-col`, `--dms-output`, `--offset-idx`, and `--scoring-strategy`.
- Choosing among `wt-marginals`, `masked-marginals`, and `pseudo-ppl` for single-substitution DMS scoring.
- Validating mutation strings such as `A24D` against a supplied wild-type sequence and residue-numbering offset.
- Preparing MSA Transformer masked-marginals runs with `--msa-path`, `--msa-samples`, and A3M insertion stripping expectations.

## Start With

1. Read [workflows](references/workflows.md) to choose the model family and scoring strategy.
2. Check the DMS CSV and mutation numbering with [data formats](references/data-formats.md).
3. Run or adapt [the helper script](scripts/variant_prediction_helper.py) before launching expensive model inference.
4. If inference fails, use [troubleshooting](references/troubleshooting.md) to separate data issues from model download, CUDA, and MSA issues.

## Boundaries

- This sub-skill covers sequence-only ESM-1v and MSA Transformer zero-shot variant effect scoring for DMS CSVs.
- For model loading, alphabets, batch converters, and representation extraction basics, use [model embeddings](../model-embeddings/SKILL.md).
- For structure-conditioned ESM-IF1 scoring, use [inverse folding](../inverse-folding/SKILL.md).
- Supervised classifiers over embeddings are background evidence only; do not use this sub-skill as the primary guide for training downstream supervised predictors.
