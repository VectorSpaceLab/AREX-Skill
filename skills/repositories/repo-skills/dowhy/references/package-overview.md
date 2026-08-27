# DoWhy Package Overview

Use this map when the user names a DoWhy module or feature family but has not
yet chosen a precise workflow. It helps route to the smallest useful sub-skill.

## Public module families

| Module family | What it covers | Best sub-skill |
|---|---|---|
| `dowhy` / `CausalModel` | classic four-step causal effect workflow, identification, estimation, refutation, and `do` | `effect-estimation` |
| `dowhy.causal_identifier` | backdoor/frontdoor/IV/general-adjustment/ID identification helpers | `effect-estimation` |
| `dowhy.causal_estimators` | built-in estimators and optional wrappers such as EconML, CausalML, and TabPFN | `effect-estimation` |
| `dowhy.causal_refuters` | bootstrap, placebo, random common cause, dummy outcome, overlap, and sensitivity refuters | `effect-estimation` |
| `dowhy.gcm` | probabilistic/structural/invertible causal models, mechanisms, sampling, attribution, validation | `graphical-causal-models` |
| `dowhy.api` / `df.causal.do` | pandas causal accessor and sampling-based interventional DataFrame workflows | `data-graph-interfaces` |
| `dowhy.graph`, `dowhy.causal_graph` | graph construction, graph-string parsing, and graph/data alignment | `data-graph-interfaces` |
| `dowhy.do_samplers` | do-sampler lookup and interventional sampling backends | `data-graph-interfaces` |
| `dowhy.datasets`, `dowhy.data_transformers`, `dowhy.timeseries` | synthetic datasets, bundled transformers, and temporal graph helpers | `data-graph-interfaces` |
| `dowhy.utils.plotting`, `dowhy.utils.graphviz_plotting`, `dowhy.utils.networkx_plotting` | plotting backends and graph rendering helpers | `data-graph-interfaces` |
| `dowhy.causal_prediction` | optional prediction extension built around deep-learning dependencies | see `optional-integrations` |
| `dowhy.graph_learners` | deprecated wrappers around external graph-discovery packages | see `optional-integrations` |

## How to use the map

1. If the user wants a treatment-effect estimate, route to `effect-estimation`.
2. If the user wants generated samples, interventions, counterfactuals, or
   GCM-based attribution, route to `graphical-causal-models`.
3. If the user needs graph syntax, graph/DataFrame alignment, or sampler setup,
   route to `data-graph-interfaces` first.
4. If the user asks about optional integrations, route to
   [optional-integrations.md](optional-integrations.md) and make the dependency
   boundary explicit.

## Typical task families

- "Estimate the causal effect of X on Y"
- "Why did this anomaly happen?"
- "How do I parse a DOT/GML graph into DoWhy?"
- "How do I use `df.causal.do`?"
- "Which DoWhy workflow should I use for counterfactuals?"
- "Is `tabpfn` or `econml` required here?"

The answer depends on the output type: a scalar effect estimate, a sampled
DataFrame, a mechanism-based attribution result, or a graph/data setup step.
