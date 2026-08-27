---
name: inference-sampling-and-simulation
description: "Guide pgmpy exact and approximate inference, sampling, simulation,
  and DBN inference workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference, Sampling, and Simulation

Use this sub-skill when a task asks for posterior probabilities, MAP assignments,
exact or approximate inference, samples from an already-parameterized model,
Dynamic Bayesian Network inference, or model-level simulation.

Do **not** use this sub-skill to build or fit the model first. Route graph/CPD
construction and `check_model()` failures to `modeling-and-factors`, structure or
parameter learning to `learning-structure-and-parameters`, causal identification,
ATE, and effect regressors to `causal-identification-and-effects`, and model/data
loading or metric evaluation to `data-io-and-evaluation`.

## First decisions

1. Confirm the model is parameterized and valid before inference or simulation:
   call `model.check_model()` on Bayesian-network-style models after CPDs are
   attached.
2. Decide whether the user wants an observational query or an intervention:
   - `query(..., evidence={...})` and `simulate(..., evidence={...})` condition on
     observed variables.
   - `simulate(..., do={...})` generates data under an intervention. If the task
     asks to identify or estimate a causal effect, route to
     `causal-identification-and-effects` instead of treating conditioning as a
     substitute for `do`.
3. Use state names exactly as stored in CPDs. If the model was created with named
   states, evidence such as `{"Test": "positive"}` is valid but `{"Test": 1}`
   may not be.
4. Set `show_progress=False` or globally disable progress bars with
   `pgmpy.global_vars.config.set_show_progress(False)` for automated scripts.
5. Use `seed=` for repeatable simulation and approximate inference.

## Routing table

| Need | Primary pgmpy entry point | Notes |
|---|---|---|
| Exact posterior on a discrete BN, Markov model, factor graph, or junction tree | `pgmpy.inference.VariableElimination` or `BeliefPropagation` | Prefer `VariableElimination` for one-off exact queries; consider `BeliefPropagation` when repeatedly querying a calibrated junction-tree workflow. |
| MAP assignment | `infer.map_query(...)` | Query variables must not overlap evidence variables. |
| Large discrete model where exact inference is too expensive | `pgmpy.inference.ApproxInference` | Sampling-based; increase `n_samples` and use `seed` for reproducibility. |
| Forward, rejection, or likelihood-weighted samples from a BN | `pgmpy.sampling.BayesianModelSampling` | Direct sampler API; `model.simulate(...)` wraps it for common workflows. |
| Gibbs samples from a BN or Markov network | `pgmpy.sampling.GibbsSampling` | Uses integer state encodings in generated Markov-chain states; provide a valid start state when needed. |
| Model-level synthetic data with evidence, interventions, soft evidence, or missingness | `DiscreteBayesianNetwork.simulate(...)` or `DynamicBayesianNetwork.simulate(...)` | Returns a pandas object or array depending on DBN `return_format`. |
| Dynamic Bayesian Network exact inference | `pgmpy.inference.DBNInference` | Variables and evidence use tuple nodes like `("X", 2)`. |

## Bundled references and script

- [Inference and sampling API map](references/inference-api.md) lists public
  imports, signatures, return shapes, and automation notes.
- [Workflows](references/workflows.md) gives copyable recipes for exact/MAP
  inference, approximate inference, direct sampling, simulation, soft evidence,
  missingness, and DBN queries.
- [Troubleshooting](references/troubleshooting.md) covers invalid evidence,
  missing CPDs, query/evidence overlap, exact-inference tractability, progress
  bars, seeds, virtual evidence, and DBN time-slice conventions.
- [inference_smoke.py](scripts/inference_smoke.py) builds a tiny BN from scratch,
  validates it, runs exact query/MAP checks, compares belief propagation, and
  simulates a few rows without reading repository files.

## Minimal copyable pattern

```python
from pgmpy.global_vars import config
from pgmpy.inference import VariableElimination

config.set_show_progress(False)
model.check_model()
infer = VariableElimination(model)
posterior = infer.query(
    variables=["Disease"],
    evidence={"Test": "positive"},
    show_progress=False,
)
map_state = infer.map_query(
    variables=["Disease"],
    evidence={"Test": "positive"},
    show_progress=False,
)
```

If that code fails, inspect the model's CPDs and state names before changing the
algorithm. Most inference errors come from an invalid model, evidence variable
not in the graph, evidence state not in a CPD, or asking for the same variable in
both `variables` and `evidence`.
