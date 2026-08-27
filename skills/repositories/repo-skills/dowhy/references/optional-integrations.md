# DoWhy Optional Integrations

Use this reference when the user asks about DoWhy features that are optional,
external, version-sensitive, or heavier than the core `dowhy` install.

## Why this file exists

The core package covers classic effect estimation, graph/data setup, and GCM
workflows. Some features depend on extras or third-party packages that may not
be present in every environment. Treat missing optional packages as a boundary
question, not as a failure of the core package.

## Optional feature matrix

| Feature | What it enables | Typical dependency boundary | Notes |
|---|---|---|---|
| EconML wrappers | `backdoor.econml...` and `iv.econml...` estimators for conditional treatment effects | `econml` plus a compatible scientific-Python stack | Compatibility can be version-sensitive; if installation fails on the current Python version, use a core estimator or a separate compatible environment. |
| CausalML wrappers | `backdoor.causalml...` estimators | external `causalml` package | Not part of the core runtime checks; route to `effect-estimation` only after the package is installed and importable. |
| TabPFN estimator | `backdoor.tabpfn` | `tabpfn` and `torch` | May require model downloads or access checks outside the core workflow. |
| Causal prediction extension | `dowhy.causal_prediction` modules and demo workflows | `torch`, `torchvision`, `pytorch-lightning` and related deep-learning dependencies | Heavy optional surface; do not assume it is present in a minimal install. |
| DOT parsing and Graphviz plotting | DOT graph parsing and high-quality rendering | `pydot` or `pygraphviz`, and for plotting a Graphviz system install | Use GML or NetworkX graph objects if the parser/plotting backend is unavailable. |
| MCMC do-sampler | `method="mcmc"` in the pandas causal accessor | `pymc3` | Heavier than weighting or kernel-density samplers and often unnecessary for smoke checks. |
| External graph discovery wrappers | Deprecated wrappers around learned DAG tooling | packages such as `causal-learn`, `cdt`, or `lingam` | DoWhy expects an external DAG as input; treat graph discovery as upstream tooling, not a core DoWhy workflow. |
| Plotting extras | Notebook-friendly and utility plots | `matplotlib` and related plotting stack | If plotting is unavailable, use non-visual validation and keep the workflow moving. |

## Practical guidance

- For a core workflow, do not install optional packages unless the user needs a
  route that actually depends on them.
- If a user asks about an optional package that is missing, say whether the task
  can be solved with a core DoWhy workflow instead.
- If the user explicitly wants the optional route, verify the package boundary
  first, then return to the owning sub-skill.
- If the optional route fails because of a version or wheel mismatch, describe
  the compatible environment instead of pretending the core package is broken.

## Common optional-integration questions

- "Do I need EconML for all DoWhy effect estimates?" No; only for the optional
  wrapper routes and some CATE-style workflows.
- "Do I need pygraphviz for every graph workflow?" No; GML and NetworkX-based
  flows work without it, and pydot can sometimes provide a lighter fallback.
- "Can I use causal prediction without extra deep-learning packages?" No; that
  extension is outside the core minimal install.
- "Does DoWhy discover graphs internally?" Not as a core workflow; use external
  discovery tooling and pass the resulting DAG into DoWhy.

## Where to go next

- `effect-estimation` for optional estimator wrappers.
- `data-graph-interfaces` for graph parsing, plotting backends, and temporal
  setup.
- `graphical-causal-models` for GCM workflows that do not need optional deep
  learning packages.
- `troubleshooting.md` for symptoms and recovery steps when an optional package
  is missing or mismatched.
