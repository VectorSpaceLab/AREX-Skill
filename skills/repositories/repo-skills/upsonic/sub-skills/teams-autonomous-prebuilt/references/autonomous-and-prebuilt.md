# Autonomous and Prebuilt Workflows

## Verified surfaces

| Surface | Use |
| --- | --- |
| `AutonomousAgent` | Sandboxed agent with filesystem and shell toolkits restricted to a workspace. |
| `PrebuiltAutonomousAgentBase` | Base class for packaged agent bundles that ship prompts and template assets. |
| `AppliedScientist` | Prebuilt autonomous agent with `new_experiment(...)` and `Experiment` handles. |
| `Experiment` | Runtime object with `run`, `run_async`, `run_stream`, and `run_in_background`. |
| `RalphLoop` | Requirements → todo → incremental development loop with build/test/lint backpressure. |
| `Simulation` | Time-series simulation runner driven by an LLM and a domain object. |

## What to remember

- `AutonomousAgent` is for workspace-bound file/shell automation.
- `AppliedScientist` bundles reusable templates and experiment bookkeeping.
- `RalphLoop` is for autonomous software development, not ordinary agent chat.
- `Simulation` is for model-driven time-series forecasts, not generic chat or tools.
