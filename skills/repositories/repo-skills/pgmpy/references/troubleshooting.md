# Cross-Cutting pgmpy Troubleshooting

Read this before debugging errors that span multiple pgmpy workflows. For task-specific failures, continue to the nearest sub-skill troubleshooting reference.

| Symptom or error signal | Likely cause | Recovery |
|---|---|---|
| `PackageNotFoundError: pgmpy` or `ModuleNotFoundError: No module named 'pgmpy'` | pgmpy is not installed in the active Python environment, or the agent is using a different Python than the user expects. | Run `python -c "import pgmpy; print(pgmpy.__version__)"`. Install with `pip install pgmpy` or use the environment the user selected. Run `scripts/check_pgmpy_environment.py --json` once import works. |
| A workflow imports from `pgmpy.estimators` but examples use `pgmpy.causal_discovery`, `pgmpy.parameter_estimator`, `pgmpy.structure_score`, or `pgmpy.ci_tests`. | The code is using legacy compatibility imports. | For new code, move to canonical packages. Keep legacy imports only when maintaining backwards compatibility with older user code. |
| `BayesianNetwork` or `MarkovNetwork` warnings/deprecation confusion. | Deprecated aliases are being used. | Use `DiscreteBayesianNetwork` and `DiscreteMarkovNetwork` in new code. |
| `check_model()` fails before inference, sampling, serialization, or causal query. | CPDs are missing, assigned to the wrong variables, have wrong parent order/cardinality, or columns do not normalize. | Route to `modeling-and-factors`; inspect each CPD variable, evidence order, `evidence_card`, table shape, and `state_names`. |
| `KeyError`, unknown state, or mismatched labels in evidence/query/data. | Discrete state labels in CPDs do not match evidence strings or DataFrame values. | Print CPD `state_names` and the DataFrame unique values. Use consistent state labels or pass numeric states intentionally. |
| Algorithms are slow or noisy in automation because progress bars appear. | Many pgmpy APIs default to progress output. | Pass `show_progress=False` in scripted examples, tests, and agent-generated snippets unless a human explicitly wants progress. |
| `FunctionalBayesianNetwork` raises that the backend is `numpy`. | Functional CPDs require the torch backend and Pyro distributions. | Install `pgmpy[torch]`, then call `from pgmpy.global_vars import config; config.set_backend("torch")` before constructing the functional model. Reset to NumPy when done if needed. |
| `ModuleNotFoundError: pyro`, `torch`, `litellm`, `pygraphviz`, or plotting backend errors. | Optional extras are not installed, or system Graphviz/provider credentials are missing. | Install only the needed extra (`pgmpy[torch]` or `pgmpy[optional]`) and any system dependency. Do not install broad extras or call provider APIs without user approval. |
| Dataset/model loading tries to access the network or HuggingFace cache. | Requested asset is remote-backed or missing from local cache. | Use `list_datasets()`/`list_models()` to inspect names. Prefer local bundled example models for no-network checks. Ask before downloads or provider/network calls. |
| Reader/writer errors for BIF/XMLBIF/NET/UAI/XDSL. | Format dialect, filetype, extension, or malformed content mismatch. | Route to `data-io-and-evaluation`; try model-level `save/load` with explicit `filetype`, then reader/writer classes for format-specific options. |
| Graph metric values look wrong or metrics raise node/edge alignment errors. | Predicted and reference graphs have different node sets, graph classes, or directed/partially directed semantics. | Align nodes first and choose the metric that matches the graph type: SHD for structural distance, adjacency/orientation confusion matrices for edge-orientation diagnostics, data-based metrics for model-data compatibility. |
| Causal result differs from ordinary conditioning. | The task mixes `P(Y | X=x)` with `P(Y | do(X=x))`. | Use `inference-sampling-and-simulation` for observational conditioning and `causal-identification-and-effects` for interventions, adjustment/frontdoor, ATE, or regressors. |
| User asks for a new algorithm/test/score under `pgmpy.estimators`. | New functionality belongs in canonical packages; `estimators` is legacy. | Route to `extending-pgmpy` and use the relevant canonical package/template path. |

## Safe diagnostic command

Run this against the user's installed package when basic import, registries, and a tiny BN query need verification:

```bash
python scripts/check_pgmpy_environment.py --json
```

Add `--check-optional` only when the task depends on optional torch/Pyro, LLM provider, or plotting imports.
