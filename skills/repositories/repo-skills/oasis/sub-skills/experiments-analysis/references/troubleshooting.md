# Troubleshooting

Use this page to decide whether a legacy experiment or analysis request is runnable, blocked, or just misconfigured.

## Fast triage

- If the request only needs interpretation, inspect the existing DB, JSON, CSV, or PNG artifact first.
- If the request starts from a SQLite database, route the first inspection to the safe DB summary helper in `platform-actions` before writing custom analysis code.
- If the request wants a simulation run, verify the model backend, data paths, and output paths before assuming it is safe.

## Common blockers

### Missing API keys or provider settings
- **Symptom:** OpenAI-backed generation or analysis fails immediately.
- **Likely cause:** The required API key or base URL is absent or wrong.
- **Safe next step:** Treat the run as blocked until credentials are supplied, or switch to a reference-only analysis plan.

### Hugging Face download or local model issues
- **Symptom:** A local-model example cannot start because the model path is missing or the weights are unavailable.
- **Likely cause:** The open-source model was never downloaded, or the path in the YAML is stale.
- **Safe next step:** Confirm the model exists and the path is current; otherwise mark the open-source run blocked.

### VLLM server, GPU, or port mismatch
- **Symptom:** The example has a `server_url` section but the client cannot connect.
- **Likely cause:** The host is unreachable, the ports do not match the deployed server, or the model server was never started.
- **Safe next step:** Compare the YAML host and ports against the actual deployment before touching the analysis code.
- **Special case:** The 1M-agent simulation is blocked if the GPU/server pool is not already confirmed, even if the config file looks complete.

### Slurm or cluster allocation problems
- **Symptom:** A large open-source recipe needs a cluster allocation that is not available.
- **Likely cause:** Insufficient GPU memory, missing node access, or a host that is not reachable from the current network.
- **Safe next step:** Mark the run blocked until the required cluster resources are confirmed.

### Missing result DB or JSON files
- **Symptom:** A visualization or analysis script cannot find its input files.
- **Likely cause:** The simulation did not complete, the output base name changed, or the paths still point to example-only locations.
- **Safe next step:** Check whether the simulation wrote both the database and its companion metadata file, then inspect those outputs rather than inventing new file names.

### Neo4j credentials or service problems
- **Symptom:** Dynamic follow-network export fails to connect.
- **Likely cause:** Missing Neo4j environment variables or an unreachable Neo4j service.
- **Safe next step:** Treat the graph export as blocked until the credentials and service are verified.

### Plotting or async-analysis dependencies
- **Symptom:** Score plots or counterfactual analysis fail on import.
- **Likely cause:** Missing `matplotlib`, `numpy`, `scipy`, `aiohttp`, or `neo4j`.
- **Safe next step:** Install the missing analysis dependency in the analysis environment before blaming the data.

### Large-scale cost or runtime
- **Symptom:** A request sounds like a full legacy run rather than a quick analysis.
- **Likely cause:** The scenario is one of the higher-cost legacy recipes.
- **Safe next step:** Lower `num_timesteps`, `round_post_num`, and `activate_prob` first, or limit the task to a structural review if the user only needs planning.

### Stale source experiment paths
- **Symptom:** A legacy YAML or script points at directories that do not exist in the current environment.
- **Likely cause:** The original example used author-specific output locations or old data paths.
- **Safe next step:** Rewrite the paths to current writable locations and preserve the scenario semantics instead of copying the stale path literally.

## Tiny-budget adaptation rules

### Reddit counterfactual smoke
- Keep the same treatment structure, but shrink the sample size and timestep count first.
- If the goal is only to verify config shape, do not run the provider-scored analysis pipeline.
- If the goal is a meaningful plot, say explicitly when the budget is too small for stable statistics.

### 1M-agent VLLM run
- If the config is missing a usable GPU/server allocation, the run is blocked, not merely inconvenient.
- If the config has a host and ports but the server is down, that is still a blocker.
- If the model is present and the server is reachable, only then is it worth checking the remaining experiment knobs.

## Final decision rule

When in doubt, prefer a safe analysis plan over an unsafe execution promise. If the task needs credentials, downloads, GPUs, or a live graph service that is not already confirmed, call it blocked and explain why.
