# Mctx API reference

This reference captures the public surface that matters when you are wiring a
learned model into search or when you are debugging search outputs.

## Core data structures

| Type | Purpose | Important fields |
| --- | --- | --- |
| `RootFnOutput` | Input from the representation / policy head at the search root | `prior_logits [B, A]`, `value [B]`, `embedding` |
| `RecurrentFnOutput` | Output from the generic recurrent dynamics function | `reward [B]`, `discount [B]`, `prior_logits [B, A]`, `value [B]` |
| `DecisionRecurrentFnOutput` | Output for a decision node in stochastic MuZero | `chance_logits [B, C]`, `afterstate_value [B]` |
| `ChanceRecurrentFnOutput` | Output for a chance node in stochastic MuZero | `action_logits [B, A]`, `value [B]`, `reward [B]`, `discount [B]` |
| `PolicyOutput[T]` | Final policy result | `action [B]`, `action_weights [B, A]`, `search_tree` |
| `Tree[T]` | Batched search tree | node values, visit counts, children arrays, embeddings, and `extra_data` |

`B` is the batch dimension. `A` is the number of actions. `C` is the number of
chance outcomes.

## Public functions

### `search(...)`

Use when you want the raw batched MCTS loop.

```python
search(
    params,
    rng_key,
    *,
    root,
    recurrent_fn,
    root_action_selection_fn,
    interior_action_selection_fn,
    num_simulations,
    max_depth=None,
    invalid_actions=None,
    extra_data=None,
    loop_fn=jax.lax.fori_loop,
) -> Tree
```

Notes:
- `root_action_selection_fn` runs at depth 0.
- `interior_action_selection_fn` runs below the root.
- `invalid_actions` is a root-only mask with `1 = invalid`.
- `extra_data` is stored on the tree and is available to action-selection
  helpers.

### `muzero_policy(...)`

Use for standard MuZero-style planning.

Key defaults:
- `qtransform=qtransform_by_parent_and_siblings`
- `dirichlet_fraction=0.25`
- `dirichlet_alpha=0.3`
- `pb_c_init=1.25`
- `pb_c_base=19652`
- `temperature=1.0`

It returns a `PolicyOutput[None]` whose `action_weights` are the root visit
probabilities.

### `gumbel_muzero_policy(...)`

Use for the Gumbel MuZero variant and policy-improvement workflows.

Key defaults:
- `qtransform=qtransform_completed_by_mix_value`
- `max_num_considered_actions=16`
- `gumbel_scale=1.0`

The returned `PolicyOutput` stores `GumbelMuZeroExtraData` in the search tree,
including `root_gumbel`.

### `stochastic_muzero_policy(...)`

Use when the environment alternates between decision and chance nodes.

Provide:
- `decision_recurrent_fn`
- `chance_recurrent_fn`

The helper handles the internal wrapper state and action masking across decision
and chance nodes.

## Tree inspection helpers

### `Tree.summary()`

Returns a `SearchSummary` with:

- `visit_counts`
- `visit_probs`
- `value`
- `qvalues`

This is the first place to look when a policy is behaving unexpectedly.

### `Tree.qvalues(indices)`

Returns Q-values for one node or a batch of nodes. Use this when you need to
compare raw search values against policy logits or to debug selection behavior.

### Useful `Tree` properties

- `num_actions`
- `num_simulations`

## Q-transform helpers

| Helper | Best for | Main behavior |
| --- | --- | --- |
| `qtransform_by_parent_and_siblings` | Default MuZero scoring | Normalizes sibling Q-values relative to the parent value |
| `qtransform_completed_by_mix_value` | Gumbel MuZero | Fills missing Q-values with a mixed value and rescales them |
| `qtransform_by_min_max` | Known bounded ranges | Maps Q-values into a fixed `[0, 1]` interval |

## Contract reminders

- Root and recurrent outputs must be batched.
- `prior_logits` and `invalid_actions` must agree on the action dimension.
- `action_weights` are intended as training targets for the policy head.
- `max_depth` counts edges from the root.
- The search helpers are JIT-friendly and designed for vectorized use.
