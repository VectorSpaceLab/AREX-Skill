# DoWhy Cross-Cutting Troubleshooting

Use this page for package-wide issues that do not clearly belong to one sub-skill.
It points to the owning workflow when the failure is actually workflow-specific.

## Fast first checks

1. Run `python -m pip check` in the active environment.
2. Run `python scripts/check_dowhy_environment.py`.
3. Confirm `import dowhy` and `import dowhy.gcm` both succeed.
4. If the task uses a graph parser or optional estimator, read
   [optional-integrations.md](optional-integrations.md) before installing more
   packages.

## Import or install failure

### Symptoms

- `ModuleNotFoundError` for `dowhy`, `sklearn`, `numpy`, `pandas`, `scipy`, or
  another core scientific dependency.
- `ImportError` during `import dowhy` or `import dowhy.gcm`.
- `python -m pip check` reports broken requirements.

### Likely causes

- The package was not installed into the active environment.
- A partial or incompatible scientific stack is present.
- The environment is missing a wheel for the current Python version.

### Recovery

- Install the package with `python -m pip install dowhy`.
- Re-run the environment probe script.
- If the user was trying an optional integration, install the optional package
  first or route to the sub-skill that owns that boundary.

## Optional dependency missing

### Symptoms

- `ImportError` for `pydot`, `pygraphviz`, `econml`, `causalml`, `tabpfn`,
  `torch`, `torchvision`, `pymc3`, or `matplotlib`.
- A workflow works in one environment but not another because an extra is absent.

### Likely causes

- The user is on the core install but asked for an optional route.
- The optional package has a Python-version or wheel mismatch.
- A system library such as Graphviz is missing for `pygraphviz`.

### Recovery

- Read [optional-integrations.md](optional-integrations.md) to decide whether the
  optional path is truly required.
- If it is required, install the missing optional package in a compatible
  environment.
- If it is not required, switch to the core route or an alternate backend.

## Graph/data mismatch

### Symptoms

- Treatment or outcome column names do not exist in the DataFrame.
- Graph nodes and DataFrame columns do not match.
- A parser cannot read a DOT string or plot a graph.

### Likely causes

- The task belongs in `data-graph-interfaces`, not in effect estimation.
- DOT parsing is missing `pydot` or `pygraphviz`.
- The graph itself is malformed or uses a format the workflow does not support.

### Recovery

- Route to [sub-skills/data-graph-interfaces/SKILL.md](../sub-skills/data-graph-interfaces/SKILL.md).
- Prefer a `networkx.DiGraph` or GML graph when parser setup is causing trouble.
- If plotting quality matters, install the plotting backend and Graphviz system
  dependency; otherwise use a non-visual validation step.

## Wrong workflow family

### Symptoms

- The user asks for a scalar effect estimate but you are looking at GCM.
- The user asks for generated samples or counterfactual rows but you are in the
  classic `CausalModel` flow.
- The user asks about pandas `.causal.do` but you are handling `CausalModel.do`.

### Likely causes

- The task was routed to the wrong sub-skill.
- The output type was not identified up front.

### Recovery

- Use `effect-estimation` for classic effect estimates, `graphical-causal-models`
  for mechanism-based sampling and attribution, and `data-graph-interfaces` for
  graph/data setup and pandas sampling.
- If the user wants a sampled DataFrame, do not promise `CausalModel.do`.
- If the user wants a counterfactual row from an observed row, route to GCM and
  require an invertible model.

## When to stop and ask for more context

Stop and ask when the fix would require:

- a different optional package or Python version,
- a system dependency such as Graphviz,
- a data file, model weight download, or other external asset,
- or a workflow-specific assumption that is not yet known.

For classic effect-estimation failures, continue in
[effect-estimation](../sub-skills/effect-estimation/SKILL.md). For GCM-specific
failures, continue in
[graphical-causal-models](../sub-skills/graphical-causal-models/SKILL.md).
For graph/data preparation failures, continue in
[data-graph-interfaces](../sub-skills/data-graph-interfaces/SKILL.md).
