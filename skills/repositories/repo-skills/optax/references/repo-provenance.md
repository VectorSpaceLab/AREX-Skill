---
schema: disco.repo-provenance.v1
skill: optax
---

# Repository Provenance

- Skill id: `optax`
- Source project: Optax
- Package distribution: `optax`
- Package version observed during inspection: `0.2.9.dev`
- Source commit: `2edbcbe2390da13983b92cbef94ac0460ecde1c5`
- Source branch: `main`
- Exact source tag: none detected
- Remote URL: `https://github.com/google-deepmind/optax.git`
- Working tree state at generation: dirty because the repo contains untracked local generation artifacts under `skills/`

## Evidence paths

- `pyproject.toml`, `README.md`, `test.sh`, `docs/development.md`
- `docs/api/optimizers.rst`, `docs/api/transformations.rst`, `docs/api/losses.rst`, `docs/api/optimizer_schedules.rst`, `docs/api/optimizer_wrappers.rst`, `docs/api/combining_optimizers.rst`, `docs/api/utilities.rst`, `docs/api/projections.rst`, `docs/api/assignment.rst`, `docs/api/perturbations.rst`, `docs/api/microbatching.rst`, `docs/api/contrib.rst`, `docs/api/experimental.rst`
- `optax/__init__.py`, `optax/_src/alias.py`, `optax/_src/base.py`, `optax/_src/combine.py`, `optax/_src/transform.py`, `optax/_src/update.py`, `optax/_src/wrappers.py`, `optax/_src/schedule.py`, `optax/losses/`, `optax/schedules/`, `optax/projections/`, `optax/assignment/`, `optax/microbatching/`, `optax/perturbations/`, `optax/tree_utils/`, `optax/second_order/`, `optax/contrib/`, `optax/experimental/`
- `examples/README.md`, `examples/contrib/README.md`, and representative notebooks under `examples/`

## Inspection snapshot

A private CPU JAX inspection environment verified that `optax` imports, the package metadata resolves to `0.2.9.dev`, and basic APIs such as `adam`, `chain`, `apply_updates`, `cosine_decay_schedule`, `softmax_cross_entropy`, `projection_simplex`, `hungarian_algorithm`, `microbatch`, `make_perturbed_fun`, `tree_add`, and `hvp` are present with the expected high-level signatures.

## Refresh signals

Refresh this skill when any of these change materially:

- public optimizer constructors or transform wrappers in `optax.__init__`
- loss, schedule, or microbatching APIs and their expected label/step conventions
- projection, assignment, tree, second-order, contrib, or experimental module names
- notebook examples that become the canonical workflow references
- package metadata, dependency constraints, or the testing/development story in `test.sh`
