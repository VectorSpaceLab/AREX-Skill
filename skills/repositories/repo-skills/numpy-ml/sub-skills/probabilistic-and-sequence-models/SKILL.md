---
name: probabilistic-and-sequence-models
description: "Routes numpy-ml probabilistic, topic-model, hidden-Markov, and
  n-gram tasks with corpus and probability-shape guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Probabilistic and Sequence Models

Use this sub-skill for `numpy-ml` workflows around probability models, hidden
state models, topic models, and sequence language models:

- Gaussian mixture models;
- multinomial hidden Markov models;
- LDA and smoothed LDA;
- maximum-likelihood, additive, and Good-Turing n-gram language models.

## First Checks

1. Read [`references/api-reference.md`](references/api-reference.md) for exact
   constructor signatures and the methods that expect arrays versus corpus file
   paths.
2. Run the smoke script for tiny validation:

   ```bash
   python sub-skills/probabilistic-and-sequence-models/scripts/probabilistic_sequence_smoke.py
   ```

3. Read [`references/workflows.md`](references/workflows.md) for small
   end-to-end examples and when to combine this route with preprocessing.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) when
   probability matrices, stochasticity checks, or corpus/tokenization inputs
   are wrong.

## Route by Task

| User asks for | Use this route |
| --- | --- |
| Gaussian mixture clustering or density fitting | GMM workflow and tiny synthetic arrays. |
| HMM log likelihood or decoding | HMM workflow with integer observation sequences and valid matrices. |
| LDA topic modeling | LDA/SmoothedLDA workflow with document-term style inputs. |
| n-gram scoring or corpus language modeling | n-gram workflow with a text corpus file and tokenization choices. |
| tokenization, stop words, punctuation cleanup | Cross-link to `../preprocessing-and-utilities/SKILL.md` first. |

## Operating Notes

- `fit` and related training calls mutate the model in place in the usual
  `numpy-ml` style.
- HMM/GMM/LDA/n-gram examples in the repo are intentionally small; prefer
  bounded arrays or tiny text corpora when validating behavior.
- Do not require plot scripts or notebook-style demos for routine use.
