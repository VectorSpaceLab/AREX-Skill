# Cross-cutting troubleshooting

Read this before deciding whether a failure belongs to model setup or search workflow logic.

## Import surface fails before any user code runs

Symptoms:

- `ModuleNotFoundError: No module named 'swarms'`
- `ModuleNotFoundError: No module named 'swarm_models'`
- `ModuleNotFoundError` involving `langchain_community`
- Imports work from the source checkout but fail from another directory

Checks:

```bash
python scripts/check_tree_of_thoughts_env.py --json
python - <<'PY'
from tree_of_thoughts import TotAgent, ToTDFSAgent
from tree_of_thoughts.bfs import BFSWithTotAgent
print("imports OK")
PY
```

Recoveries:

1. Ensure the intended Python environment is active.
2. Install the runtime package: `python -m pip install -U tree-of-thoughts==0.6.5`.
3. If LangChain split-package imports fail, install the compatibility package observed during verification: `python -m pip install -U langchain-community==0.3.31`.
4. Re-run the environment checker.

## Real model calls fail but fake-agent checks pass

Symptoms:

- Authentication, rate-limit, network, provider, or `OPENAI_API_KEY` errors.
- Search helpers with deterministic fake agents succeed.

Interpretation: package orchestration is probably working; provider configuration is not. Route to `sub-skills/agents-and-models/` and check `.env`, `OPENAI_API_KEY`, provider-specific dependencies, and model-output shape.

## Search output is malformed or empty

If imports and model setup pass but DFS/BFS returns unexpected JSON, route to `sub-skills/search-workflows/`. Start with the deterministic smoke helper:

```bash
python sub-skills/search-workflows/scripts/fake_agent_search_smoke.py --mode dfs --max-loops 1 --number-of-agents 2 --no-autosave
python sub-skills/search-workflows/scripts/fake_agent_search_smoke.py --mode bfs --max-loops 1 --number-of-agents 2 --breadth-limit 2 --no-autosave
```

If these pass, inspect the real agent's `thought`/`evaluation` outputs and parameter settings.

## Unsafe model-output parsing

`TotAgent.run` uses a parser that evaluates model output as Python text. Do not feed untrusted arbitrary text into it. Validate samples with:

```bash
python sub-skills/agents-and-models/scripts/check_model_contract.py \
  --sample-output '{"thought":"try a smaller branch","evaluation":0.74}'
```

Use a safer wrapper or post-processing layer if model output can include code, imports, function calls, or user-controlled text.

## No-PyTorch warning from transformers

A warning like `PyTorch was not found. Models won't be available...` can appear during imports through transitive model dependencies. It is not a blocker for the selected package scope unless you intend to use a local Transformers/PyTorch model. For OpenAI-backed or fake-agent workflows, the DFS/BFS orchestration does not require PyTorch.

## Autosave files appear unexpectedly

DFS may write JSON into a `tree_of_thoughts_runs/` directory relative to the current working directory when `autosave_on=True`. For tests and reproducible smoke checks, set `autosave_on=False` or use the fake-agent helper with `--no-autosave`.
