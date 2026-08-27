---
name: optax
description: "Route Optax tasks across optimizer construction, loss and schedule
  workflows, and advanced utilities or contrib topics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Optax

Use this skill when the user asks about **Optax**, the JAX-based gradient processing and optimization library. This root skill is a router: use it to decide whether the request is about optimizer composition, losses and schedules, or advanced utilities and contrib-style algorithms.

## First checks

- Confirm whether the user is trying to:
  - build or debug an optimizer pipeline,
  - choose a loss, schedule, or microbatching helper, or
  - use a projection, assignment, tree, linear-algebra, second-order, or contrib feature.
- Confirm the active Python environment can import `jax` and `optax` before assuming any runtime behavior.
- For a fast health check, run `scripts/optax_skill_doctor.py --smoke` in an isolated environment.
- Use `references/repo-provenance.md` to check whether this skill matches the current checkout snapshot.
- Use `references/troubleshooting.md` for missing-JAX, shape, backend, and API-misuse triage before diving into a sub-skill.

## Route by user intent

| User asks for | Open |
| --- | --- |
| Choose, build, chain, wrap, or debug optimizers and gradient transformations; apply updates; inject schedules into hyperparameters; use `adam`, `adamw`, `sgd`, `chain`, `named_chain`, `partition`, `lookahead`, or `MultiSteps` | `sub-skills/core-optimization/SKILL.md` |
| Select or combine losses, schedules, microbatching helpers, or perturbation wrappers; compare classification/regression/ranking/self-supervised losses; tune warmup/cosine/piecewise schedules | `sub-skills/losses-and-schedules/SKILL.md` |
| Work with projections, assignment, tree utilities, linear algebra, second-order helpers, or contrib/experimental algorithms such as `sam`, `schedule_free`, `dpsgd`, `muon`, `galore`, or `reduce_on_plateau` | `sub-skills/advanced-topics/SKILL.md` |

## Read these bundled references

- `references/core-workflows.md` for optimizer composition patterns, update flow, and schedule injection.
- `references/losses-and-schedules.md` for loss families, schedule families, microbatching, and perturbation helpers.
- `references/advanced-topics.md` for projections, assignment, tree math, linear algebra, second order, contrib, and experimental features.
- `references/examples-index.md` for notebook and example routes that demonstrate the main workflows.
- `references/troubleshooting.md` whenever the request involves installation, missing JAX, backend confusion, shape mismatches, or unstable contrib features.
- `scripts/optax_skill_doctor.py` when you need a quick import, backend, or tiny smoke check.

## Common workflow reminders

- Optax is backend-agnostic at the library level, but actual execution depends on the installed JAX backend. A CPU-only JAX install can prove importability and many small smoke checks, but not accelerator-specific claims.
- Do not tell future agents to open the original repository notebooks or tests from runtime instructions. Distill any needed recipes into the bundled references or scripts.
- When the user asks for “the best optimizer,” start with `core-optimization` and use `references/core-workflows.md` to compare the common families before narrowing further.
- When the user asks for a loss or schedule, start with `losses-and-schedules`; when they ask for anything projection-like, tree-like, assignment-like, or contrib-like, start with `advanced-topics`.

## Package-level sanity check

If you need a one-line import check rather than the full doctor script, use:

```bash
python -c "import optax; print(optax.__version__)"
```

That only proves the package imports in the current environment. Use the doctor script when you also need selected API signatures, JAX backend facts, or a tiny end-to-end optimizer smoke test.
