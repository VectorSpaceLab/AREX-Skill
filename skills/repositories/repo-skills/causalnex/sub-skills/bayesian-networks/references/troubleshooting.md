# Bayesian Network Troubleshooting

## Graph and state problems

- `The given structure has ... separated graph components`: connect the graph before building `BayesianNetwork`.
- `The given structure is not acyclic`: remove the cycle before fitting a BN.
- `The data does not cover all the features found in the Bayesian Network`: ensure every node appears in the dataframe used for `fit_node_states`.
- `node '...' contains None state`: drop or impute missing node states before fitting state dictionaries.

## CPD and prediction problems

- `Bayesian Network does not contain any CPDs`: fit CPDs before creating `InferenceEngine` or calling prediction methods.
- `unrecognised method`: use `MaximumLikelihoodEstimator` or `BayesianEstimator`.
- `unrecognised bayes_prior`: use `K2` or `BDeu`.
- `No CPDs found. The model has not been fitted`: fit the BN before calling the sklearn classifier's `predict`.

## Inference and intervention problems

- `Variable names must match ^[0-9a-zA-Z_]+$`: rename nodes to use only letters, digits, and underscores.
- `Expecting observations to be a dict, list or None`: pass the supported type to `InferenceEngine.query`.
- `The cpd for the provided observation must sum to 1`: normalize the intervention distribution before `do_intervention`.
- `The cpd for the provided observation must be between 0 and 1`: clamp or renormalize intervention probabilities.
- `Do calculus cannot be applied because it would result in an isolate`: choose a node with at least one neighbor.

## Evaluation and plotting problems

- `roc_auc` or `classification_report` look wrong: inspect `bn.node_states`, the fitted CPDs, and the discrete target values first.
- Plotting errors usually mean `pyvis` is missing or the environment cannot write the HTML output file.
- If `InferenceEngine.query(parallel=True)` fails, retry with `parallel=False` and repair `pathos` only after the serial query works.

## Latent-variable EM problems

- `initial_params must be a dictionary or one of ...`: pass `"random"` or a node->CPD mapping.
- `Invalid priors`: pass a dict of CPD-shaped priors or leave the argument unset.
- `Invalid box constraints`: pass a dict of CPD-shaped min/max tables or leave the argument unset.
- If EM looks unstable, reduce `n_jobs` to `1`, inspect the latent-variable states, and verify the Markov blanket before tuning priors or box constraints.
