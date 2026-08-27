# Mctx workflows

This note turns the API into concrete usage patterns. Use it when you need to
wire a model into planning or to debug the outputs of a finished search.

## 1. Standard MuZero-style planning

Use this pattern when you already have a representation model and a dynamics
model.

1. Build a batched `RootFnOutput` from your policy / value network.
2. Write a batched `recurrent_fn(params, rng_key, action, embedding)` that
   returns `RecurrentFnOutput` and the next embedding.
3. Call `mctx.muzero_policy(...)` with a simulation budget.
4. Feed `policy_output.action` to the environment.
5. Train the policy head on `policy_output.action_weights`.

```python
root = mctx.RootFnOutput(
    prior_logits=policy_logits,
    value=root_value,
    embedding=root_embedding,
)
policy_output = mctx.muzero_policy(
    params=params,
    rng_key=rng_key,
    root=root,
    recurrent_fn=recurrent_fn,
    num_simulations=32,
)
```

## 2. Gumbel MuZero policy improvement

Use this pattern when the task mentions policy improvement, Gumbel MuZero, or
better action ranking at the root.

1. Keep the same batched root / recurrent contract.
2. Use `mctx.gumbel_muzero_policy(...)`.
3. Prefer `qtransform_completed_by_mix_value` unless you have a reason to
   rescale Q-values differently.
4. Inspect `policy_output.search_tree.extra_data.root_gumbel` if you need to
   compare the chosen action against the original logits.

The bundled `scripts/policy_improvement_demo.py` runs a tiny random bandit and
prints the improvement over the prior policy.

## 3. Stochastic MuZero

Use this pattern when a game or environment alternates between decision nodes
and chance nodes.

1. Define `decision_recurrent_fn` to emit `chance_logits` and an afterstate
   value.
2. Define `chance_recurrent_fn` to emit action logits, reward, discount, and
   value.
3. Call `mctx.stochastic_muzero_policy(...)`.
4. Treat the public result exactly like the other policy helpers: choose
   `action`, inspect `action_weights`, and debug the tree summary when needed.

## 4. Search-tree debugging

When a search result looks wrong, inspect the tree instead of only looking at
`action`.

- `policy_output.search_tree.summary()` shows root visit counts and Q-values.
- `policy_output.search_tree.qvalues(0)` is useful for the root.
- `policy_output.search_tree.children_prior_logits` shows the logits that were
  actually expanded.
- `policy_output.search_tree.children_visits` helps explain why an action was
  or was not selected.

Typical debugging questions:

- Did the mask mark too many actions as invalid?
- Is the recurrent function returning the right batch size?
- Is the Q-transform appropriate for the action-value scale?
- Is `max_depth` truncating the search too early?

## 5. Smoke-check workflow

Use the bundled install checker when you only need to confirm that the package
imports and JAX is usable.

```bash
python scripts/check_install.py
```

This is the fastest way to confirm the environment before running anything
heavier.
