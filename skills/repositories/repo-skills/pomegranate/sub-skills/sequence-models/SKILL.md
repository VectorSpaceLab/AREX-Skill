---
name: sequence-models
description: "Guides pomegranate sequence workflows with MarkovChain, DenseHMM,
  and SparseHMM, including sequence shapes, variable-length batches, transition
  setup, Baum-Welch fitting, priors, posterior decoding, and Viterbi."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# sequence-models

## Use this sub-skill when

Use this sub-skill for pomegranate sequence models: k-th order categorical `MarkovChain`, dense-transition `DenseHMM`, sparse-transition `SparseHMM`, sequence likelihood scoring, sequence sampling, hidden-state posterior decoding, Viterbi paths, variable-length sequence training, and prior-weighted/semi-supervised HMM learning.

## Start here

Typical imports:

```python
from pomegranate.distributions import Categorical, ConditionalCategorical, Exponential, Normal
from pomegranate.markov_chain import MarkovChain
from pomegranate.hmm import DenseHMM, SparseHMM
```

Read [references/api-reference.md](references/api-reference.md) for constructors, sequence data shapes, dense/sparse edge formats, and examples. Run [scripts/smoke_sequence_models.py](scripts/smoke_sequence_models.py) to verify tiny MarkovChain, DenseHMM, and SparseHMM workflows.

## Core workflow

1. **Choose the model.** Use `MarkovChain` for observed categorical sequences. Use `DenseHMM` when hidden state transitions are dense. Use `SparseHMM` when only a few state transitions are possible.
2. **Shape input as sequences.** Most HMM/Markov-chain scoring uses `(n, length, d)`. HMM fitting can also accept lists of sequences or grouped tensors for variable lengths.
3. **Create emissions.** HMM states are pomegranate distributions such as `Normal`, `Exponential`, or richer distributions.
4. **Define starts, ends, and transitions.** Dense HMMs use a transition matrix; sparse HMMs use `[start_distribution, end_distribution, probability]` edge triples plus optional starts/ends.
5. **Train or score.** Use `fit` for Baum-Welch/EM, `summarize`/`from_summaries` for chunked updates, and `log_probability` for sequence likelihoods.
6. **Decode states.** Use `predict`, `predict_proba`, `predict_log_proba`, or `viterbi` depending on whether you need posterior marginals or a best path.

## Route elsewhere when

- You need base emissions or categorical distributions: read [../distributions/SKILL.md](../distributions/SKILL.md).
- You need non-sequential mixtures or classifiers: read [../mixtures-and-classifiers/SKILL.md](../mixtures-and-classifiers/SKILL.md).
- You need Bayesian networks or factor graphs over discrete variables: read [../graph-models/SKILL.md](../graph-models/SKILL.md).

## Guardrails

- HMMs are over sequences; do not pass ordinary `(n, d)` arrays to HMM scoring/fitting unless the method specifically documents that format.
- `SparseHMM` needs explicit nonzero edges; if every state connects to every state, use `DenseHMM`.
- Sampling from HMMs requires either fixed `sample_length` or usable end probabilities.
- Prior tensors for HMMs must align with sequence shape and state count.
- Read [references/troubleshooting.md](references/troubleshooting.md) when variable-length data, edge formats, start/end probabilities, priors, or sampling fail.
