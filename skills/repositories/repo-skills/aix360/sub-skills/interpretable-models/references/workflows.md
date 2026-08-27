# Workflows

The following workflows are deliberately small and data-local. They show the
fit/transform/explain order without depending on repository files, remote data,
or notebooks.

## Workflow A: tree-derived binary rules

1. Split a pandas `DataFrame` and target with a fixed random seed.
2. Decide categorical columns and a missing-value policy. For tree-derived
   features, impute or add explicit missing indicators before fit; do not pass
   NaN/None to `fit`.
3. Fit `FeatureBinarizerFromTrees` on the training frame and target.
4. Transform train and test with the same transformer. If `returnOrd=True`,
   carry both frames and use the same `Xstd` pair downstream.
5. Fit `BooleanRuleCG`/`BRCGExplainer` or `LogisticRuleRegression`/
   `GLRMExplainer`.
6. Predict on the test binary frame, check the target shape and class set, then
   inspect rule strings or coefficient rows.
7. Save the MultiIndex feature manifest and a readable rule summary.

A minimal configuration for a smoke run is `treeNum=1`, `treeDepth=2`,
`threshRound=4`, `randomState=0`, BRCG `iterMax`/`timeMax` bounded, and GLRM
`iterMax` bounded. Increase complexity only after this path is stable.

### Direct model variation

- For numerical regression, replace the classifier with
  `LinearRuleRegression`, call `GLRMExplainer.predict`, and evaluate against
  the continuous target.
- For probabilities, use `LogisticRuleRegression.predict_proba`; do not treat
  `BRCG.predict` as a calibrated probability.
- For a compact rule set, increase `lambda0`/`lambda1` or lower search depth;
  record the resulting accuracy/readability trade-off.

## Workflow B: ProtoDash summary or local candidate comparison

1. Represent both `X` and candidate `Y` as finite, same-semantic numeric arrays.
2. Apply the same encoding/scaling to both. Keep a reversible mapping to source
   row ids; do not use row positions as permanent ids without recording them.
3. Choose `m <= len(Y)` and a kernel. Use `kernelType='other'` for a simple
   inner-product similarity or `Gaussian` with a positive `sigma`.
4. Start with `optimizer='osqp'` or `cvxpy` after probing availability.
5. Call `ProtodashExplainer.explain`; validate that `len(indices)` and
   `len(weights)` match, indices are unique/in-range, weights are finite and
   non-negative, and objective history is finite where present.
6. Render selected candidate rows with the stored source ids and weights. A
   prototype is representative under the chosen feature geometry, not proof
   of an individual model's decision.

## Workflow C: RIPPER and typed rules

1. Construct a clean pandas frame with stable columns and no unsupported dtype.
   RIPPER treats non-float columns as nominal; explicitly choose float dtype for
   continuous columns.
2. Fit `RipperExplainer(...).fit(X, y, target_label=positive)` for a binary
   target, or omit `target_label` for ordered multi-class induction.
3. Call `predict` on a frame with the same columns and call `explain()` for a
   binary `DnfRuleSet`; call `explain_multiclass()` for ordered outputs.
4. Evaluate the typed ruleset against an assignment dictionary to verify
   semantic behavior before exporting.
5. If a TRXF classifier is needed, create `RuleSetClassifier`, choose a
   conflict method, and call `update_rules_with_metrics` on held-out data.
6. Construct a data dictionary from the exact input schema before PMML export.
   If the serializer rejects a feature, preserve the typed TRXF/JSON rule and
   state that PMML was excluded.

An empty conjunction is an always-true rule. An empty DNF list is always false
for its target rule set. Treat both as valid degenerate outputs and test their
fallback behavior.

## Workflow D: model differencing with IMD

1. Fit two independent classifiers on the same training split.
2. Produce `y1_train` and `y2_train` from exactly the same row order and retain
   the feature frame used for those predictions.
3. Fit `IMDExplainer` with a bounded `max_depth`, explicit `split_criterion`,
   `alpha`, and `verbose=False` for automation.
4. Inspect `diffrules` and `diffregions`. Each rule's `class_label` indicates
   whether the two surrogate outputs differ in that region, while the region
   itself is bounded by observed training feature ranges.
5. Evaluate test predictions through `metrics`. Before dividing, check for
   zero total differences and zero samples in predicted regions.
6. If visualization is requested, render a graph only in an environment with
   graphviz and pygraphviz. The textual rules and ranges are the canonical
   fallback.

This workflow explains *where the models differ*, not why either model is
correct and not a local attribution of individual features.

## Workflow E: TED Cartesian teaching

1. Define a domain explanation codebook and encode it as dense integer ids
   `0..K-1`. Keep a decoder beside the model artifact.
2. Verify `Y` and `E` have the same length and that `Y` is compatible with the
   integer composition used by the implementation (the common contract is
   binary labels).
3. Instantiate a base estimator that accepts the resulting composite labels
   and fit `TED_CartesianExplainer(base).fit(X, Y, E)`.
4. Call `predict_explain` first and confirm that returned label and explanation
   ids are in the decoder's ranges. Then call `predict`/`explain` as separate
   views.
5. Use `score` with held-out `(X, Y, E)` and report combined, label, and
   explanation accuracy separately.

Do not claim that TED reproduces a previously trained classifier unless that
classifier was explicitly the training target. TED learns a joint decision
and teaching explanation.

## Workflow F: optional neural and profile methods

### CoFrNet

1. Normalize numeric tabular inputs consistently, usually to a bounded range.
2. Generate a supported connection mask with compatible input/output sizes.
3. Construct `CoFrNet_Model`, use a small `DataLoader` and a bounded training
   loop, then evaluate without gradients.
4. Use `CoFrNet_Explainer.explain("importances")` for final-layer feature
   summaries or `explain("print_co_fr", max_layer_num, var_num)` for one ladder.
5. Validate the selected variable and layer bounds; inspect for reciprocal
   overflow or NaN before interpreting.

### DIPVAE

1. Validate the model-args namespace and dataset contract, including shape,
   `next_batch`, latent size, likelihood, output activation, and instance count.
2. Construct the explainer with CPU first; use CUDA only when available and
   explicitly selected.
3. Fit for a tiny epoch/batch smoke test and verify finite ELBO values.
4. Call `explain` with a valid latent dimension and compare reconstruction/edit
   shapes. Store the latent edit, not only an image filename.

### ProfWeight

1. Validate that each probe `.npy` array has the same `(samples, classes)`
   shape and that the inclusive start/end layer indices are in range.
2. Validate one-hot labels and compute `prof_weight_compute` first. Check
   weights are finite and have the expected sample count.
3. Provide a legacy-compatible Keras simple-model factory and all required
   hyperparameters/callbacks before using `ProfweightExplainer.fit` or
   `explain`.
4. Compare weighted and unweighted simple models on the same evaluation split;
   keep probe confidence and model accuracy separate.

## Output review checklist

- Inputs and output arrays have matching row counts.
- Class/target domain and explanation-code domain are explicit.
- Feature names, binary MultiIndex columns, categories, and missing policy are
  preserved.
- Rule count, conjunction degree, coefficient sign, prototype positions, or
  difference-region count are recorded.
- Optional dependencies were probed and any omitted artifact is named.
- The result is not described as a black-box explanation when it is a newly fit
  direct model.
