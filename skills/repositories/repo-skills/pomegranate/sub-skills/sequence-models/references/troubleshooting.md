# Sequence Models Troubleshooting

## Data shape errors

- HMM and Markov-chain scoring generally expects `(n, length, d)`.
- A list of 2D tensors can be used for variable-length HMM fitting; pomegranate groups equal-length sequences internally.
- `MarkovChain` data should be integer categorical observations.
- Emission distributions determine HMM observation constraints: an `Exponential` emission still requires nonnegative observations, a `Categorical` emission requires valid category ids, and so on.

## Dense vs sparse HMM setup

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `SparseHMM` initialization fails with no usable edges | Sparse HMM cannot be uniformly initialized as a dense graph. | Provide explicit nonzero edge triples or use `DenseHMM`. |
| Edge tuple is rejected | Sparse edge entry is not `[distribution_a, distribution_b, probability]`. | Use the distribution objects themselves and a float probability in `[0, 1]`. |
| Dense transition matrix shape error | Matrix is not `(n_states, n_states)`. | Match matrix rows/columns to the number and order of emission distributions. |
| Start probability validation fails | Starts are wrong length or do not sum to 1. | Provide one start probability per state and normalize. |
| Sampling raises about length/end probabilities | HMM has neither fixed `sample_length` nor usable end probabilities. | Set `sample_length=...` or provide end probabilities. |

## Fitting and EM behavior

- `fit` runs iterative Baum-Welch/EM until `tol` or `max_iter` stops it.
- Use `verbose=True` only when debugging convergence.
- If emissions are uninitialized, pomegranate initializes them from sequence observations using KMeans-like initialization.
- If an emission distribution is frozen, it will not update even if the HMM updates transitions.
- For large or variable-length datasets, prefer `summarize` and `from_summaries` in deliberate batches.

## Priors and semi-supervised sequence labels

- HMM priors must have the same sequence batch/length leading dimensions and a final state dimension.
- Each prior row should be nonnegative and sum to 1.
- One-hot rows are hard state labels; soft rows bias posterior estimates but do not impose supervised loss targets.
- If priors are supplied for variable-length lists, keep each prior tensor aligned with its corresponding sequence tensor.

## Device and dtype issues

- Move both the HMM and all emission distributions to the same device as the data.
- Do not mix CPU transition tensors with CUDA observations.
- Use floating tensors for continuous emissions and integer tensors for categorical emissions.
- Validate in full precision before trying mixed precision.

## Viterbi vs posterior prediction

`predict` uses posterior marginals, while `viterbi` returns a best path under dynamic programming. If the paths differ, it does not necessarily mean either method is broken; they answer different decoding questions.
