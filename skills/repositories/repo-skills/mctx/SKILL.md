---
name: mctx
description: "Use Mctx for JAX-native Monte Carlo tree search, MuZero/Gumbel
  MuZero policies, stochastic MuZero search, and search-tree inspection."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Mctx

Mctx is a compact JAX library for batched Monte Carlo tree search. Use this
skill when the task asks you to plan with a learned model, improve a policy
with search, or inspect the resulting search tree.

## Start here

- Install the library with `pip install mctx`.
- If you want a quick health check, run `python scripts/check_install.py`.
- If you want a safe runnable example, run
  `python scripts/policy_improvement_demo.py --num_runs=1`.
- Read `references/api-reference.md` when you need exact function signatures or
  tensor-shape contracts.
- Read `references/workflows.md` when you need an end-to-end recipe.
- Read `references/troubleshooting.md` when search output, shapes, or optional
  dependencies are failing.

## What this skill covers

### 1. Batched search on a learned model
Use `search(...)` when you already have:

- a batched root state,
- a recurrent model for expansion,
- a root action-selection function,
- an interior action-selection function,
- and a simulation budget.

This is the lowest-level entry point and is best when you need to customize the
search loop.

### 2. Classic MuZero-style planning
Use `muzero_policy(...)` when you want the standard MuZero policy improvement
loop with Dirichlet root noise, PUCT-style action selection, and visit-count
based action weights.

### 3. Gumbel MuZero planning
Use `gumbel_muzero_policy(...)` when you want the Gumbel MuZero variant and
its default Q-value completion strategy. This is the best default when the task
mentions policy improvement by planning with Gumbel.

### 4. Stochastic MuZero planning
Use `stochastic_muzero_policy(...)` when the environment alternates between
decision nodes and chance nodes. Provide separate decision and chance recurrent
functions; the wrapper handles the internal state structure.

## How to choose the right helper

- Use `qtransform_by_parent_and_siblings` for the default MuZero-style value
  normalization.
- Use `qtransform_completed_by_mix_value` for the default Gumbel MuZero path.
- Use `qtransform_by_min_max` when you already know a bounded Q-value range.
- Prefer the policy helper that matches the search style instead of reaching
  into `_src` internals.

## Inspecting results

After search, prefer the public summary APIs over raw tree fields unless you are
troubleshooting.

- `PolicyOutput.action` is the chosen action.
- `PolicyOutput.action_weights` are the training targets for the policy head.
- `PolicyOutput.search_tree` holds the final `Tree`.
- `Tree.summary()` exposes root visit counts, visit probabilities, value, and
  Q-values.
- `Tree.qvalues(node_index)` is the best way to inspect a node.

## Common input contract

- Treat action masks as `1 = invalid`, `0 = valid`.
- Keep root and recurrent outputs batched.
- Make `prior_logits` and `invalid_actions` have the same trailing action
  dimension.
- Keep `recurrent_fn` outputs aligned with the batch size of the root.
- Use `max_depth` only when you intentionally want to cap traversal depth.

## Bundled scripts

- `scripts/check_install.py` verifies the installed package, imports the public
  API, and reports the active JAX backend.
- `scripts/policy_improvement_demo.py` is a tiny bandit-style smoke demo that
  shows how planning can improve a policy.

## Optional dependency note

This skill does not bundle tree visualization. If you need Graphviz-style tree
rendering later, treat it as a separate dependency problem instead of assuming
it is available in a minimal install.

## When to read the deeper references

- Read `references/api-reference.md` before wiring a custom model or action
  mask.
- Read `references/workflows.md` before writing a new MuZero or Gumbel MuZero
  driver.
- Read `references/troubleshooting.md` when output is flat, invalid-action
  handling looks wrong, or JAX is on the wrong backend.
- Read `references/repo-provenance.md` when you need to check whether this
  skill is stale against the source checkout that produced it.
