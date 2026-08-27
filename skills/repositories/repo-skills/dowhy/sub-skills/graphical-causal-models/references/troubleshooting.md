# GCM Troubleshooting

Use this reference when a GCM workflow fails, produces implausible scores, or is
too slow.

## Fast diagnostic checklist

1. Is the graph a directed acyclic graph?
2. Does every graph node have a matching data column?
3. Does every node have a causal mechanism before fitting?
4. Was the model fitted after the latest graph or mechanism change?
5. Does the selected task require an invertible structural model?
6. Are intervention or counterfactual inputs mutually exclusive as required?
7. Are categorical, discrete, and continuous variables encoded intentionally?
8. Are NaNs present?
9. Are Shapley, sample, bootstrap, and parallelism settings bounded?

## Graph is not a DAG

Symptom:

- Validation or sampling fails while checking the causal graph.
- Topological sorting fails.

Fix:

- Remove directed cycles before using GCM APIs.
- If feedback loops are real in the domain, this GCM workflow is not a direct
  fit; ask the user to define a time-lagged or acyclic abstraction and route
  temporal graph construction to the data/graph interface sub-skill.

## Data columns do not match graph nodes

Symptom:

- Fit raises a message that data for a node cannot be found.
- Queries fail when selecting parent columns.
- Output columns are unexpected because graph node labels differ from DataFrame
  labels.

Fix:

```python
missing = set(causal_model.graph.nodes) - set(data.columns)
extra = set(data.columns) - set(causal_model.graph.nodes)
print("missing graph columns", missing)
print("extra data columns", extra)
```

Rename columns or graph nodes before fitting. Do not silently drop required
parents. Extra data columns are fine if every graph node is present and the
workflow selects graph columns explicitly.

## Missing causal mechanisms

Symptom:

- Error says a node has no assigned causal mechanism.
- `draw_samples`, validation, or fitting fails before model training.

Fix:

- Run `gcm.auto.assign_causal_mechanisms(causal_model, data)` before fitting;
  or
- manually assign root stochastic models and non-root conditional mechanisms;
  then
- run `gcm.fit(causal_model, data)`.

If mechanisms were already assigned but should be replaced, call automatic
assignment with `override_models=True`.

## Mechanism type does not match node role

Symptom:

- Root node expected a stochastic model.
- Non-root node expected a conditional stochastic model.
- Structural or invertible workflow fails because the mechanism is not a
  compatible functional causal model.

Fix:

- Root nodes: assign `EmpiricalDistribution`, `ScipyDistribution`, or another
  stochastic model.
- Non-root probabilistic nodes: assign conditional stochastic mechanisms.
- Structural non-root nodes: assign functional causal mechanisms such as
  additive noise models.
- Invertible structural non-root nodes: use mechanisms invertible with respect
  to noise when point counterfactuals or anomaly attribution are needed.

## Fit-before-task and changed graph structure

Symptom:

- Error says the mechanism is not fitted to the graphical structure.
- Results are implausible after adding/removing edges.

Fix:

- Re-run `gcm.fit` after any graph edge, parent set, mechanism, or column
  schema change.
- Avoid mutating the graph after fitting unless the next step is a refit.
- If using cloned models for bootstrap or distribution change, ensure the clone
  has assigned mechanisms before the query.

## Interventional input exclusivity

Symptom:

- Error says either observed samples/data or number of samples to draw must be
  set, not both or neither.

Fix:

- For `gcm.interventional_samples` and `gcm.average_causal_effect`, pass exactly
  one of:
  - `observed_data=...`, or
  - `num_samples_to_draw=...`.

Use `observed_data` to propagate interventions through specific rows. Use
`num_samples_to_draw` to sample from the fitted generative model first.

## Counterfactual observed/noise exclusivity

Symptom:

- Error says either `observed_data` or `noise_data` must be given.
- Error says `observed_data` and `noise_data` cannot both be given.

Fix:

- Pass exactly one of `observed_data` or `noise_data`.
- If starting from factual observations, pass only `observed_data`.
- If using precomputed compatible noise values, pass only `noise_data`.

This is a common difficult case: do not try to merge both inputs. Decide whether
noise should be reconstructed from observations or supplied directly.

## Counterfactual invertibility requirement

Symptom:

- Error says observed data requires an `InvertibleStructuralCausalModel`.
- Categorical mechanisms fail for point counterfactual reconstruction.

Fix:

- Recreate the model as `gcm.InvertibleStructuralCausalModel` before assigning
  and fitting mechanisms.
- Prefer invertible continuous mechanisms such as additive noise models for
  non-root nodes.
- If variables are categorical and point counterfactuals are required, explain
  that the available mechanism may not support sample-specific noise inversion;
  consider interventions or a task-specific model redesign instead.

## Categorical, ordered discrete, and continuous variables

Symptom:

- Automatic assignment chooses an unexpected model.
- A numeric category is treated as ordered discrete or continuous.
- Multi-class target fails in `average_causal_effect`.

Fix:

- Encode unordered categories as category/string values when automatic
  assignment should treat them as categorical.
- Keep genuinely ordered discrete variables numeric only when ordering is
  meaningful.
- For GCM ACE, use continuous or binary categorical targets. Multi-class
  categorical targets are not supported by that scalar helper.
- For custom categorical models, verify downstream tasks do not require
  invertibility.

## NaNs and missing values

Symptom:

- Automatic assignment raises that data contains NaN.
- Later GCM tasks fail despite experimental NaN assignment.

Fix:

- Prefer imputation, filtering, or a task-specific missingness model before GCM
  fitting.
- If the user accepts limitations, use
  `experimental_allow_nans=True` in automatic assignment for numerical
  variables only.
- Do not assume every GCM query supports missing data just because assignment
  accepted it.

## Expensive Shapley, sampling, and bootstrap settings

Symptom:

- Attribution, influence, or confidence interval jobs are very slow.
- CPU usage is high because nested parallelism is active.
- Memory grows during feature relevance or intrinsic influence.

Fix:

- Reduce `num_samples`, `num_distribution_samples`,
  `num_samples_randomization`, `num_samples_baseline`, or bootstrap resamples.
- Use a bounded Shapley config:

```python
cfg = gcm.shapley.ShapleyConfig(
    approximation_method=gcm.shapley.ShapleyApproximationMethods.PERMUTATION,
    num_permutations=20,
    n_jobs=1,
)
```

- Lower `max_batch_size` for memory-sensitive relevance/influence calls.
- Set one layer of parallelism to 1 when using confidence intervals around
  Shapley-based queries.
- Use `max_num_samples` and a small evaluation config for validation.

## Implausible attribution or influence scores

Potential causes:

- The graph omits an important parent or includes a wrong direction.
- Mechanisms fit poorly or categorical/continuous encoding is wrong.
- Sample sizes are too small for the selected Shapley or distribution measure.
- The selected difference or attribution function has units that do not match
  the user's interpretation.
- Distribution-change data do not represent comparable old/new regimes.

Fix:

- Run `evaluate_causal_model` with bounded settings.
- Run graph or invertible-model refutation if relevant.
- Repeat with larger samples or confidence intervals.
- State score units explicitly.
- For changed-population questions, verify old and new datasets have the same
  schema and comparable measurement process.

## Clean output for scripts

Progress bars can clutter logs. Disable them in scripts:

```python
gcm.config.disable_progress_bars()
```

Set random seeds for NumPy and any user-supplied model libraries when examples
need reproducible output. Do not present exact numeric smoke-script values as
scientific conclusions.
