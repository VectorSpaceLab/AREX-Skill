# Zoo and benchmark packaging

## Inference package contract

A benchmark-ready policy package separates policy implementation from the
small module that registers it. The common layout is:

```text
inference/
  package_name/
    __init__.py
    policy.py          # class Policy(Agent)
    model files        # only when distribution is permitted and bounded
  __init__.py          # defines entry_point and calls register
  MANIFEST.in          # package data, if needed
  setup.cfg            # metadata and pinned policy dependencies
  setup.py             # invokes setuptools
```

The registration module should import the policy, define an entry point that
creates an `AgentInterface` and `AgentSpec`, and register a stable versioned
name. A typical entry point is:

```python
def entry_point(**kwargs):
    interface = AgentInterface(...)
    return AgentSpec(
        interface=interface,
        agent_builder=Policy,
        agent_params={"model_path": "..."},
    )

register("contrib-agent-v0", entry_point=entry_point)
```

The package's own dependencies belong in `install_requires`, preferably with
exact versions when following the benchmark contribution template. Do not
silently include SMARTS as an install requirement; the benchmark host supplies
it. Keep model artifacts out of source control when they are large or
restricted, and fail clearly if an expected model path is missing.

Package metadata must match the actual supported Python/framework versions.
The repository's benchmark examples use older Python and model dependency
pins than the prepared SMARTS core environment; treat those as historical
examples, not a current compatibility claim. Reconcile framework, model,
SMARTS, and benchmark versions before installing.

## Compatibility gate

A benchmark runner consumes a locator, resolves its `AgentSpec`, and uses the
spec's interface to build the ego agent. Before handing off a package:

1. Build a clean target environment with SMARTS plus only the policy's
   declared dependencies.
2. Import the registration module.
3. Run `check_agent_locator.py` with the fully qualified locator.
4. Construct the spec and inspect its interface.
5. Instantiate the policy only if model files and optional frameworks are
   available; run an action-space/observation-space check without training.
6. Verify the benchmark's expected action type, observation requirements,
   scenario support, and versioned locator.

Benchmark and zoo commands are intentionally not bundled here. Route
`scl zoo install`, `scl zoo build`, `scl benchmark list`, and
`scl benchmark run` to `cli-integrations`. A benchmark's `--auto-install` may
install requirements from its listing; do not use it with an untrusted custom
listing, because a listing selects executable entry points and dependencies.

## Versioning

Use `agent-name-v0` for the first stable contract, then increment the version
when changing model preprocessing, interface sensors, action semantics,
required model files, or dependency assumptions. Keep the benchmark version
separate from the agent locator version. A benchmark may accept a range of
agent versions, but the package must document the exact tested combination.

Do not depend on a bare locator in a package or scenario. A bare name resolves
only after another module has registered it in the same process. Always publish
the importable module prefix in benchmark/scenario configuration.

## Full training and evaluation boundary

The repository includes PPO/Stable-Baselines and RLlib examples, training
configs, checkpoint directories, benchmark evaluation, and packaged model
patterns. They are reference workflows only in this skill. Full training,
checkpoint downloads, Envision sessions, benchmark-scale runs, and regression
suites are not a safe locator smoke. The prepared environment has no Ray,
RLlib, Torch, or TensorFlow, so no success claim may be inferred from the
presence of an example file or package metadata.
