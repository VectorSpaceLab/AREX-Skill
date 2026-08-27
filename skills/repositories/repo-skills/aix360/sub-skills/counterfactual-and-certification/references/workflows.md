# Workflows

The workflows below are deliberately small and do not download models,
embeddings, datasets, or image assets. They describe what to execute after the
caller has supplied local data and compatible optional dependencies.

## 1. Validate a counterfactual request before selecting an algorithm

Create a tiny fixture with two numeric and one categorical feature, a model
whose `predict` returns a one-dimensional binary array, and one affected row.
Write down:

- favorable class (`1` for the GLANCE methods);
- immutable columns and allowed-to-vary columns;
- finite lower/upper bounds and categorical domains;
- numeric and categorical column lists with no overlap;
- the desired number of counterfactuals and what counts as success.

Run the model on the factual row. For each proposed counterfactual, assert
same columns and dtypes, all bounds and actionability rules, and a favorable
prediction. If no valid result exists, report that rather than relaxing a
constraint silently.

## 2. GLANCE local recourse and cost audit

1. Split `train_dataset` into feature columns plus a target column named
   `target` when using the string local-method selector. Keep an explicit
   `X`, `y`, and affected `instances` table.
2. Declare numeric/categorical columns instead of relying on dtype inference
   when a pandas column is ambiguous.
3. Start with `NearestNeighborMethod` or `RandomSampling` for a small CPU
   fixture. Use `DiceMethod` only after the DiCE backend is available.
4. Fit the local method, request a small number of counterfactuals, and check
   the returned shape. Apply the action validator from the API reference;
   nearest-neighbor output may change immutable columns because its current
   implementation does not apply `feat_to_vary`.
5. For a global explanation, fit `C_GLANCE` with small
   `initial_clusters`, `final_clusters`, and `num_local_counterfactuals`.
   Call `explain_group`, then inspect `global_actions()` and re-evaluate each
   action on the whole affected population.
6. Use `build_dist_func_dataframe` only after checking that every numeric
   reference range is nonzero. Report raw effectiveness count and raw cost,
   plus a separately computed mean if required.

`T_GLANCE` is useful when the deliverable is a subgroup policy tree. Fit it,
call `partition_group`, and audit `cumulative_leaf_actions`; tree visualization
is optional and is not part of the numerical acceptance test.

## 3. Ecertify with an explicit quality contract

Define a one-dimensional quality function around a tiny local model and
explanation. A classification quality function should explicitly select the
original class probability, for example:

```python
def quality(point):
    black_box_value = float(model.predict_proba([point])[0, original_class])
    explanation_value = float(explanation([point])[0])
    return 1.0 - abs(black_box_value - explanation_value)
```

Preflight `quality(x) >= theta`, choose finite `lb < ub`, and use a small `Q`
and `Z` for a smoke test. Call `Ecertify` directly if both width and the
confidence/EVT value are needed. Repeat with a fixed random seed only for
reproducible debugging; the algorithm itself samples and its width is an
estimate. Increase `Q`, `Z`, or `numruns` only after the contract and runtime
are understood.

Interpret the width in the coordinates supplied to Ecertify. If the model was
standardized, the width is in standardized units; it is not automatically a
raw-feature radius. Ecertify does not clip sampled points to a data manifold,
legal domain, or actionability set, so a domain-aware quality function or an
external validator is required.

## 4. CEM on a prepared historical model

Only use this workflow when a compatible TensorFlow 1.x/Keras installation,
trained classifier, optional autoencoder, and preprocessing contract are
already available locally.

1. Confirm the classifier exposes batch numeric scores, class count, input
   shape, `predict_long`, and graph-compatible `predictsym`.
2. Confirm class ordering and input normalization. For a `[-0.5, 0.5]` model,
   pass `offset=0.5`; do not mix normalized and `[0, 1]` data.
3. Start with one image/array and very small iteration counts only to verify
   tensor shapes. Then run PN and PP separately with explicit `mode`.
4. Re-predict `adv_x` and, for PP, also inspect `delta_x`; assert the intended
   class relation and range. A successful optimizer return with no valid
   class change is a failed explanation.
5. Record `kappa`, regularizers, binary-search steps, iterations, random seed,
   and whether an autoencoder was used. Do not call this a certified minimum.

CEM-MAF additionally needs attribute classifiers and, for PN, the latent/GAN
assets. Treat model and sample acquisition as a separate approved preparation
step. CPU pinning can avoid known old-GPU numerical failures but does not make
modern environments compatible.

## 5. OTMatching alternative plans

1. Build a nonnegative cost matrix from caller-owned features. If using text,
   tokenization and embeddings are upstream inputs; this route does not
   download or construct them.
2. Compute or receive a normalized transport plan. Check its shape, row/column
   sums, and total mass against `a` and `b` before calling the explainer.
3. Restrict `search_match_pos_filter` to valid `(row, column)` tuples when
   certain positions must be considered. Start with low depth/node limits.
4. Call `explain_instance`, then for each returned alternative check nonnegative
   entries, marginal residuals against `error_limit`, total transport cost,
   and that every salient position is a valid matrix index.
5. Report fewer alternatives as a search result, not as an exception or a
   claim that no other alternatives exist. Increase depth/nodes only with an
   explicit compute budget.

The optional `otoc` implementation is a separate dependency. Keep matching in
its own compatible environment when it conflicts with a historical neural
stack; importing or verifying one must not be used as evidence that the other
is installed.

## Acceptance checklist

- The target/favorable class and model-output contract are stated.
- Bounds, actionability, categorical domains, and immutable columns are
  validated outside methods that do not enforce them.
- Output is re-predicted and its shape/cost/marginals are checked.
- Sampling, optimization, search depth, and query budget are recorded.
- Network-bound assets, legacy TensorFlow, and missing optional packages are
  reported as limits rather than silently bypassed.
