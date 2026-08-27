# Mctx troubleshooting

## Shape and batching errors

**Symptom:** `chex.assert_shape` or `chex.assert_equal_shape` fails.

**Likely cause:** The root output, invalid-action mask, or recurrent output is
not batched consistently.

**Fix:**
- Keep `prior_logits` shaped `[B, A]`.
- Keep `value`, `reward`, and `discount` shaped `[B]`.
- Keep `invalid_actions` shaped `[B, A]` when you pass it.
- Make sure your recurrent model returns the same batch size that the root used.

## All actions invalid

**Symptom:** The policy returns action `0`, or the root weights look flat.

**Likely cause:** Every action is masked out at the root, usually because the
mask is wrong or you reached a terminal state but still invoked search.

**Fix:**
- Treat `1` as invalid and `0` as valid.
- Check the mask before search.
- If the state is terminal, handle it outside Mctx instead of asking search to
  choose among impossible actions.

## Search output looks underexplored or overconfident

**Likely cause:** The Q-transform or search budget does not match the task.

**Fix:**
- Use the default MuZero or Gumbel MuZero Q-transform unless you know a better
  normalization.
- Increase `num_simulations` if the root search is too shallow.
- Revisit `max_num_considered_actions` for Gumbel MuZero if the action set is
  large.
- Make sure `temperature` is appropriate for the final sampling step.

## `max_depth` confusion

**Symptom:** A leaf seems to be revisited or search stops earlier than expected.

**Likely cause:** `max_depth` counts edges from the root. When the cutoff is
reached, Mctx can expand the existing leaf again instead of discovering a new
node.

**Fix:**
- Increase `max_depth` if you want deeper traversal.
- Leave it unset when you want the search budget to govern depth.

## JAX backend confusion

**Symptom:** The environment reports CPU even on a GPU machine.

**Likely cause:** The installed `jaxlib` is CPU-only.

**Fix:**
- The library still works on CPU for its core workflows.
- Install a matching accelerator-enabled JAX wheel only if you truly need
  accelerator execution for your own workloads.

## Optional visualization dependencies are missing

**Symptom:** Tree-rendering tooling fails because Graphviz or `pygraphviz` is
missing.

**Likely cause:** The optional visualization stack was not installed.

**Fix:**
- Treat visualization as optional.
- Install the extra dependencies only if you need graph rendering.
- Do not assume a minimal install includes external Graphviz tooling.

## Install/import issues

**Symptom:** `pip install` succeeds but the package still fails to import.

**Likely cause:** The environment was not using the intended Python or the
editable install was done in a different prefix.

**Fix:**
- Run `python scripts/check_install.py` from the environment you expect to use.
- Confirm the environment Python prints the installed `mctx` module path.
- Reinstall into the same prefix if the module path is wrong.
