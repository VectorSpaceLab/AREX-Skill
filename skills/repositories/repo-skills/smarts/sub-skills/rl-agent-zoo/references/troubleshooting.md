# RL and agent-zoo troubleshooting

## Install and import

**`No module named your_policy`** — The locator's module prefix must be
importable by the same Python interpreter that runs SMARTS. Install the policy
package into that environment or expose its package root on `PYTHONPATH`; do
not rely on the current working directory. Confirm with `python -c 'import
module'`, then use the locator checker.

**`No module named ray` while importing RLlibHiWayEnv** — Ray is an optional
integration and is absent from the prepared core environment. Install a
SMARTS-compatible Ray/RLlib extra in an isolated environment only after
choosing compatible versions. This is not a core SMARTS import failure.

**Torch/TensorFlow import fails** — The corresponding optional framework and
model dependencies are not installed or are incompatible with the artifact.
Do not switch frameworks implicitly. Recreate an environment with the exact
policy package pins and validate model loading separately from SMARTS.

**Editable/source import confusion** — A successful import from a source tree
does not prove that an installed wheel contains the module or model files.
Test from an arbitrary directory with the target interpreter.

## Locator and registry

**`ValueError: Cannot register invalid locator`** — Use a versioned key such
as `policy-v0` or `policy-latest`; the registry does not accept an unversioned
key. Keep the module prefix outside the registered key, for example
`package.registration:policy-v0`.

**`NameError: Locator not registered in lookup`** — The module imported but did
not register the exact name/version. Check spelling, hyphens, version suffix,
registration module side effects, and whether the expected `__init__` is the
module actually named by the locator. The checker distinguishes this from
module import failure.

**Bare locator works once then fails** — Bare names use process-local registry
state. Use the fully qualified locator in scenarios, packages, and workers.

**Registration is overwritten** — Registering the same key more than once
warns and replaces the prior factory. Use unique versioned keys and avoid
importing competing policy modules in one process.

## AgentSpec and spaces

**`build_agent` says no builder** — Supply a class/callable as
`agent_builder`; do not pass an already-instantiated policy. Confirm the
`agent_params` shape: dict means keyword parameters, list/tuple means
positional parameters, and another value is passed as one argument.

**Action assertion from the formatter** — The action returned by `act` does
not belong to the space produced for the selected interface. Inspect
`ActionSpaceType`, per-agent action spaces, numeric dtype/bounds, tuple shape,
and discrete values. An adapter must translate the model output before the
SMARTS formatter sees it.

**Observation/model mismatch** — Align dict keys, array shape, dtype, bounds,
and flattening order between the interface formatter, adapter, and RL policy.
Do not fix this by disabling RLlib environment checking; that only hides an
early error.

**Legacy adapters behave unexpectedly** — `AgentSpec` adapter fields remain
for compatibility and are deprecated in core policy design. If an optional
RLlib example uses them, document the exact pre/post shape and test it with the
selected framework release.

## Social agents, bubbles, and data

**Social policy never runs** — Validate the locator first. Then confirm the
scenario contains the actor and bubble, the zone intersects traffic, airlock
and active conditions pass, exclusions do not filter the vehicle, and capture
limits are not exhausted. A traveling bubble also needs exactly one follow id
and a follow offset.

**Bubble constructor rejects the scenario** — Check non-negative margin,
valid closed zone geometry, mutually exclusive follow ids, required offset,
boid-only `keep_alive`, and actor-state restrictions on broadphase active
conditions.

**Policy kwargs are ignored** — Put overrides in
`SocialAgentActor.policy_kwargs`; they are factory kwargs for the registered
AgentSpec, not fields on `AgentSpec.agent_params` unless the entry point passes
them through. Check the entry point signature and the final spec.

**Worker cannot find scenario/model data** — Use paths readable from every Ray
worker, not driver-only relative paths. Package model data or configure a
shared absolute path appropriate to the deployment. Avoid sharing one mutable
output directory among workers.

## RLlib, Ray, and workflow failures

**`worker_index`/`vector_index` missing** — `RLlibHiWayEnv` expects a Ray/RLlib
environment config object with these fields. A plain dict is useful for
inspection only if those fields are supplied; it is not a full worker config.

**`__all__` or active-agent errors** — Submit actions only for active agents.
The adapter filters final observations/rewards/info to submitted ids and tracks
aggregate completion. Preserve the final transition and stop sending actions
for agents already done.

**Ray port/process/resource collision** — Give workers distinct ports where an
external service is used, limit worker/CPU counts, and keep headless mode on
for bounded checks. Do not launch Ray clusters, SUMO, Envision, or training as
part of locator validation.

**Resume checkpoint crashes or changes behavior** — A resumed experiment is
expected to use the recorded configuration. Altering spaces, model
preprocessing, policy map, or environment config requires a new experiment or
an explicit compatible checkpoint migration; verify before loading.

**Benchmark command fails after a clean locator check** — Locator validation
only proves import and registry presence. Route CLI behavior, benchmark
listing/version, package installation, scenario assets, and external
requirements to `cli-integrations`; inspect those separately.
