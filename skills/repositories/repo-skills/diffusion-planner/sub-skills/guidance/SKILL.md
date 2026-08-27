---
name: guidance
description: "Use when adding or debugging classifier/collision guidance, a
  custom reward or guidance_fn, GuidanceWrapper behavior, or guided nuPlan
  simulation in Diffusion-Planner."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Diffusion-Planner guidance

Use this sub-skill for the guidance extension point in Diffusion-Planner. It
teaches a Researcher to reason about `GuidanceWrapper`, write a differentiable
custom guidance callable, preserve the planner's tensor/device/normalization
contracts, configure guided sampling, and diagnose failures such as NaNs,
detached rewards, empty collision pairs, or shape mismatches.

## Applicability and boundaries

Natural triggers include **classifier guidance**, **collision avoidance
guidance**, **custom reward**, `guidance_fn`, `GuidanceWrapper`, and **guided
nuPlan simulation**. Do not use this sub-skill for generic training or an
un-guided simulation; use the sibling skills for those tasks:

- [Diffusion-Planner root skill](../../SKILL.md) for shared repository setup and provenance.
- [model-training](../model-training/SKILL.md) for training and checkpoints.
- [closed-loop-planning](../closed-loop-planning/SKILL.md) for ordinary planner and nuPlan simulation setup.

The sibling links are part of the planned graph; the guidance files themselves
remain self-contained and do not assume that sibling instructions are loaded.

## Fast route

1. Read [the API contract](references/api-reference.md) before writing a
   guidance function. In particular, distinguish the flattened sampler input
   from the `[B, P, T, 4]` view seen by guidance functions.
2. Follow [the guided workflow](references/workflows.md): establish the
   interpreter and nuPlan paths as user configuration, run the deterministic
   local smoke helper, then launch only when checkpoint, dataset, maps, and
   simulation permissions are available.
3. If the reward is zero, detached, non-finite, or the wrapper fails before the
   simulation starts, use [the troubleshooting playbook](references/troubleshooting.md).
4. Keep custom code in a project-owned extension/worktree. Treat the original
   checkout as evidence; do not make a future Researcher patch or open it in
   place merely to try a guidance experiment.

## Non-negotiable runtime contract

A custom function has the public shape:

```python
def my_guidance_fn(x, t, cond, inputs) -> torch.Tensor:
    """Return a differentiable per-batch guidance energy."""
```

The live wrapper currently invokes registered functions with `**kwargs`, so a
practical implementation should accept `inputs` by keyword and tolerate
additional keyword arguments when the deployment passes them. It must return a
finite `torch.Tensor` whose computation graph reaches the differentiable parts
of `x`; the DPM classifier adapter differentiates the returned energy with
respect to the sampler input. `cond` is commonly `None` in this repository.

`GuidanceWrapper` receives the flattened sampler tensor, applies the model
correction and inverse normalizers, and then calls each registered function.
The guidance function therefore sees physical-unit state and inverse-normalized
observation fields, not the normalized tensors fed to the model. The wrapper
also passes `model`, `model_condition`, `state_normalizer`, and
`observation_normalizer` in keyword arguments. The built-in collision function
uses `neighbor_current_mask` and `neighbor_agents_past` from `inputs`.

The guided YAML selects `GuidanceWrapper` as `guidance_fn`; the decoder passes
it to DPM-Solver in `classifier` mode with guidance scale `0.5`. The supplied
launch script is a semantic example only: replace its placeholder dataset and
nuPlan locations and its private interpreter/sudo invocation with an
interpreter that the Researcher controls. See the workflow reference for the
safe equivalent.

## Bundled verification

From the repository root, run the helper with the prepared environment (or an
equivalent environment that can import the installed package):

```bash
/path/to/diffusion-planner-inspection/bin/python \
  skills/disco/diffusion-planner/sub-skills/guidance/scripts/synthetic_guidance_smoke.py
```

The helper uses fixed in-memory rectangles and a tiny `[B=1, P=2, T=3, 4]`
tensor. It checks rectangle geometry, the live collision function, wrapper
normalization hooks, finiteness, and autograd connectivity; it does not fetch
nuPlan data, checkpoints, or launch workers. Use `--help` to see its options.

For the exact signatures, tensor layout, guided YAML meaning, and failure
recovery, continue to the bundled references rather than guessing from a
simulation error.
