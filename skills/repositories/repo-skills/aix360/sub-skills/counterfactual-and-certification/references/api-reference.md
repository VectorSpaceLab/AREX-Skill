# API reference

This reference distills the public contracts observed in AIX360 0.3.0. It is
intentionally limited to counterfactual, certification, recourse, and matching
workflows.

## Common contract

| Concern | Contract |
|---|---|
| Verification target | Re-predict every returned counterfactual or applied action and check the requested target/favorable class. |
| Bounds | CEM projects image/array values according to its own normalized domain; GLANCE and Ecertify do not provide a general per-feature bounds or immutability layer. Enforce domain constraints before and after the call. |
| Model outputs | CEM needs a classifier wrapper with batch predictions, class count, input shape, `predict_long`, and differentiable symbolic `predictsym`; GLANCE local methods use `model.predict(DataFrame)` with favorable value `1`; Ecertify accepts a user quality callable; OTMatching does not call a predictive model. |
| Approximation | CEM optimizes a regularized objective, GLANCE samples/optimizes local candidates and merges actions, Ecertify samples or performs bounded zero-order search, and OTMatching searches a candidate tree. None should be described as globally optimal or universally valid without an independent proof. |

## CEM: pertinent positive/negative

Import `CEMExplainer` and `KerasClassifier` from
`aix360.algorithms.contrastive`. Construct `CEMExplainer(model)` and call:

```python
adv_x, delta_x, info = explainer.explain_instance(
    input_x, mode, autoencoder, kappa, binary_search_steps,
    max_iterations, initial_const, beta, gamma,
    alpha=0, threshold=1, offset=0,
)
```

Important semantics:

- `input_x` is a batch, normally batch size one. The implementation expects
  the classifier's training normalization to be known. With `offset=0.5`, the
  caller supplies values in `[-0.5, 0.5]`; the optimization operates in a
  `[0, 1]`-like space and returns the normalized representation.
- `mode` must be `"PP"` or `"PN"`. The implementation has no dependable
  user-facing validation for other strings, so validate it before calling.
- The target one-hot vector is derived from the original predicted class. PP
  seeks a sparse retained version that keeps that class; PN seeks an addition
  that makes the prediction differ from that class. This is not an arbitrary
  requested target-class API.
- `kappa` is the confidence margin in the class-vs-other-class loss;
  `binary_search_steps`/`arg_b` changes the loss constant; `max_iterations`
  controls optimizer work; `initial_const` starts the constant search.
- `beta` controls L1 sparsity, `alpha` the L2 term, and `gamma` the optional
  autoencoder regularizer. `threshold < 1` suppresses small PP/PN changes.
  `autoencoder` may be `None`, but a non-`None` object must be callable in the
  expected TensorFlow graph.
- The tuple contains the candidate `adv_x`, a difference array `delta_x`, and
  a human-readable `info` string. These are not a proof of minimality. Check
  the classifier prediction and the direction of the PP/PN change yourself.

`KerasClassifier(model, input_layer=0, output_layer=0, device=None)` exposes
`predict`, `predict_classes`, `predict_long`, `predictsym`, `nb_classes`, and
`input_shape`. The historical CEM code uses raw symbolic scores/logits in its
loss; a model returning class IDs, a scalar, or a wrongly shaped output is not
compatible. Keep preprocessing, class ordering, and score scale consistent
with the trained model. A probability vector can be numerically accepted but
changes the meaning/scale of `kappa`.

## CEM-MAF: image attributes

Import `CEM_MAFImageExplainer`, `KerasClassifier`, and optionally
`CELEBAModel` from `aix360.algorithms.contrastive`. Construct:

```python
explainer = CEM_MAFImageExplainer(model, attributes, asset_root)
adv_img, attribute_changes, info = explainer.explain_instance(
    session, input_img, input_latent, mode, kappa,
    binary_search_steps, max_iterations, initial_const,
    gamma, beta, attr_reg=1, attr_penalty_reg=1,
    latent_square_loss_reg=1, gan_device=None,
    attr_classifier_device=None,
)
```

- `attributes` names locally available binary attribute classifiers. The
  constructor expects their model JSON/weights in the CEM-MAF asset layout;
  it does not make a safe, automatic substitute when assets are absent.
- `mode="PN"` requires a latent vector and the GAN/attribute assets. It
  returns an image, an attribute-change string, and an info string.
- `mode="PP"` segments the image internally (the historical path uses SLIC)
  and optimizes a mask; `input_latent` is not the PP input. It returns an
  image and currently uses `None` for the two textual fields.
- `gamma` weights attribute/latent/image regularization and `beta` controls PP
  mask sparsity. The PN-specific attribute and latent regularizers are
  `attr_reg`, `attr_penalty_reg`, and `latent_square_loss_reg`.
- The historical implementation is tied to TensorFlow 1.x graph/session APIs,
  old Keras model serialization, and image-specific assets. `gan_device` and
  `attr_classifier_device` can pin vulnerable operations to CPU on affected
  old GPU stacks, but this is a compatibility workaround, not GPU verification.

CEM-MAF explains the original predicted class, not a caller-selected class.
Validate image shape, range, channel order, attribute names, and the returned
class/attributes after optimization. Image training and asset acquisition are
expensive and network-bound; do not use them as a smoke test.

## Ecertify

The direct algorithm is `Ecertify` from
`aix360.algorithms.ecertify.ExpCertifyBB`:

```python
width, confidence_value = Ecertify(
    x, theta, Z, Q, lb=0, ub=float("inf"), sigma_0=0.1,
    s=1, quality=quality, choice="min", eps_mul=0.1,
    eps_fid=0.01,
)
```

`quality(x)` must accept a one-dimensional NumPy point and return one finite
scalar. `theta` is the minimum acceptable quality. The algorithm first checks
`quality(x)`; if it is below `theta`, the implementation returns `-1` rather
than the normal two-tuple, so preflight this condition. `lb` and `ub` are
scalar coordinate half-widths around `x`, not per-feature data bounds. Use a
finite `ub` unless an unbounded search is deliberate, and ensure `ub > lb`.

Strategies are: `s=1` uniform sampling, `s=2` uniform incremental sampling,
`s=3` adaptive incremental sampling, `s=4` zero-order search via ZOOpt, and
`s=5` the IID uniform-incremental variant used by the lower-tail calculation.
`Q` is a per-region query budget and `Z` controls expansion/halving rounds;
large values multiply runtime. `choice` must be `"min"`, `"max"`, or
`"mean"` when a violating point determines the next radius.

`CertifyExplanation(theta, Q, Z=10, lb=0, ub=1, sigma0=0.1, numruns=100)`
wraps repeated calls. Its `certify_instance(instance, quality_criterion,
strategy=3, choice="min", silent=True)` returns the mean width only. Use the
direct function when the per-run confidence/EVT value is needed. The reported
width is an empirical/probabilistic trust region under the chosen sampling and
quality assumptions, not a guarantee outside that region or outside the
feature domain. Ecertify itself does not require a class-probability interface;
a classification quality function usually does, so adapt the model explicitly.

## GLANCE recourse

GLANCE expects a tabular model with `predict(DataFrame)` returning binary
values where favorable is `1`. The affected population should normally be
selected as rows currently predicted `0`; the classes are not inferred or
validated by the library.

### Local methods

- `DiceMethod().fit(model, data, outcome_name, continuous_features,
  feat_to_vary, random_seed=13)` uses `dice_ml` and
  `explain_instances(instances, num_counterfactuals)`. It requests desired
  class `1` and passes `feat_to_vary` to DiCE. The fitted data contains the
  outcome column.
- `NearestNeighborMethod().fit(model, data, outcome_name,
  continuous_features, feat_to_vary, random_seed=13)` retains training rows
  predicted `1`, one-hot encodes categoricals, and returns nearest favorable
  rows from `explain_instances(instances, num_counterfactuals)`. The current
  implementation records `feat_to_vary` but does not use it to constrain the
  neighbor differences; enforce immutability after the call.
- `RandomSampling(model, n_most_important, n_categorical_most_frequent,
  numerical_features, categorical_features, random_state=None)` is fitted by
  `fit(X, y)` and queried with `explain(instance, num_counterfactuals,
  n_samples=1000, random_state=None)` or `explain_instances(...)`. It samples
  numeric values between observed unaffected ranges and categorical values
  among frequent unaffected categories, so it can return fewer candidates or
  `None` for one instance.

### C-GLANCE and T-GLANCE

`C_GLANCE(model, initial_clusters=100, final_clusters=10,
num_local_counterfactuals=5, heuristic_weights=(0.5, 0.5),
alternative_merges=True, random_seed=13, verbose=True)` is fitted with:

```python
method.fit(
    X, y, train_dataset, feat_to_vary="all",
    numeric_features_names=None, categorical_features_names=None,
    clustering_method="KMeans", cf_generator="Dice",
    cluster_action_choice_algo="max-eff",
)
```

Other fit options select nearest-neighbor/random-sampling parameters and
low-cost/effectiveness thresholds. `explain_group(instances)` returns
`(effectiveness_count, total_cost)` and populates `global_actions()`. Actions
are candidate recourse rows, not per-person guarantees. The string local
methods expect `train_dataset` with a column named `target`.

`T_GLANCE(model, split_features=None, partition_counterfactuals=None,
child_count=2, global_method=None, local_method=None,
num_local_counterfactuals=100)` uses `fit(...)`, then
`partition_group(instances) -> Node`; `cumulative_leaf_actions()` returns
`(effectiveness_count, total_cost, action_count)`. If both methods are omitted,
its default global iterative-merges path requires a training dataset.

### Actions and cost

- `extract_actions_pandas(X, cfs, categorical_features, numerical_features,
  categorical_no_action_token="-")` encodes numeric changes as `cf - X` and
  categorical changes as the new value, using the token for no change.
- `apply_action_pandas(X, action, numerical_columns, categorical_columns,
  categorical_no_action_token="-")` adds numeric deltas and assigns changed
  categoricals. `apply_actions_pandas_rows` applies row-specific actions.
- `build_dist_func_dataframe(X, numerical_columns, categorical_columns,
  n_bins=10)` bins numeric differences by each reference range divided by
  `n_bins`, then adds one for each changed categorical value. GLANCE's returned
  cost is this distance summed over effective cases; divide by effectiveness
  yourself if a mean is desired.

These helpers do not enforce bounds, immutability, monotonicity, or feasibility.
A zero numeric range can also make the distance undefined. Prevalidate columns,
avoid constant numeric columns or define a custom cost, and re-check every
applied action.

## OTMatching

Import `OTMatchingExplainer` from `aix360.algorithms.matching`:

```python
explainer = OTMatchingExplainer(deactivate_bounds=False, error_limit=1e-3)
alternatives = explainer.explain_instance(
    matching, costs, (row_marginals, column_marginals),
    num_alternate_matchings=1,
    search_thresholds=(0.5, 0.5), search_node_limit=20,
    search_depth_limit=1, search_match_pos_filter=None,
)
```

`matching` and `costs` are equal-shaped `m x n` arrays. The matching must be
non-negative and satisfy row sums `a` and column sums `b` (with equal total
mass); the example convention normalizes both totals to one. `costs` should be
non-negative. The optional filter is a whitelist of 2-tuples `(i, j)`; invalid
members raise `ValueError`.

The result is a list of `AlternateMatching(matching, salient)`, where
`matching` is the candidate transport plan and `salient` is the sparse list of
positions identified by the search history. Fewer alternatives can be
returned when the search terminates early. `search_thresholds`, node limit,
depth limit, `deactivate_bounds`, `error_limit`, and the filter trade off
search breadth, diversity, and constraint tolerance. The algorithm delegates
to the optional `otoc` dependency and does not compute the base transport plan
or embeddings. Check marginals, cost, and salient positions after every call.
