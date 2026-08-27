# Distiller Copy Prompt

Copy this prompt into DisCo, Codex, or Claude Code when starting one or more Paper2Skills Distiller runs that generate and verify skills for paper replication. Fill a config by copying `create-paper-skills/assets/distiller-run-config-template.toml` from the installed Distiller skills directory.

```text
Use Distiller to generate and verify paper-replication skills for each run in this config.

config_path: /path/to/distiller_run_config.toml
```

In the config, set `paper_source` to a local path, URL, arXiv id, or paper title. Set `original_repo_source` to a local path, Git URL, `none`, or `unknown`; when it is `unknown`, use `repo_discovery_mode = "ask"`, `"auto"`, or `"disabled"` to control whether the agent asks, runs bounded GitHub discovery, or proceeds paper-only. By default each paper writes process artifacts to `<workspace_root>/<paper_slug>/distillation/` and generated skills to `<workspace_root>/<paper_slug>/skills/`. Set `recovery_mode = "hard"` when full-standard recovery is required and reduced/proxy/fallback experiments must not be accepted as success; set `recovery_mode = "soft"` only when a validated reduced/proxy recovery may count after full recovery is blocked. `iteration_budget` is the maximum number of refine cycles after the first recovery; keep the default `10` or replace it with another non-negative integer.
