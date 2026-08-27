# Agent Harness Troubleshooting

Use this page for install/layout, `dc-knowledge/`, and agent-harness failures.
For SDK code errors route to `sdk-pipelines`; for query expression errors route
to `query-engine`.

## Quick Checks

```bash
datachain skill list
python skills/disco/datachain/sub-skills/agent-harness/scripts/skill_layout_check.py --target claude
python skills/disco/datachain/sub-skills/agent-harness/scripts/knowledge_base_smoke.py dc-knowledge
```

Adjust script paths to the installed location of this generated skill.

## Symptoms and Actions

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `datachain: command not found` | The CLI is not installed in the active shell environment, or the environment's `bin` directory is not on `PATH`. | Activate the environment that has DataChain, or install it with the project's package manager. Verify with `python -c "import datachain; print(datachain.__version__)"` and `datachain skill list`. |
| `No module named datachain` from helper scripts | The helper is running under a Python interpreter without the DataChain package. | Run the helper with the same Python used by the DataChain CLI, or install DataChain into that interpreter. |
| Unsupported skill name | Only `core`, `knowledge`, and `jobs` are valid bundled skill names. | Re-run with one of those names, comma-separated, or omit the positional skill list to install/uninstall all. |
| Unsupported target name | Only `claude`, `cursor`, `codex`, `pi`, and `copilot` are supported by the DataChain skill CLI. | Use `datachain skill list` or the layout helper to verify target spelling. |
| Local install appears missing | `--local` writes under the current working directory, not necessarily the intended project. | `cd` to the project root and run the layout helper with `--local`; uninstall from the accidental directory if needed. |
| Global install appears missing | The agent is reading project-local directories, or a different user home is active. | Check both global and local layouts. Install with `--local` if the project should carry the skills. |
| Command/rule file points at an old path | `{skill_dir}` placeholder was resolved during an earlier install, then files moved or were copied manually. | Do not hand-edit if avoidable. Uninstall and reinstall in the same target/scope so placeholders resolve to the current destination. |
| `dc-knowledge/index.md` missing | Knowledge base has not been generated in this project, or the agent is in the wrong working directory. | Run the knowledge-base workflow from the project that owns the Dataset DB. Use the smoke helper to confirm the tree. |
| Dataset page missing from `dc-knowledge/` | A script created a dataset but the knowledge base was not refreshed, or JSON enrichment failed. | Re-run the knowledge-base update workflow. Check for temporary JSON files and error output from enrichment. |
| `dc-knowledge/` looks stale | Dataset DB changed after the index was rendered, or a storage listing is expired. | Refresh listings only when needed, then rebuild `dc-knowledge/`. If a bucket page says the listing is stale, update the source listing before trusting counts. |
| Bucket access denied/not found | Missing cloud credentials, wrong profile/project, private bucket, or public bucket not being accessed anonymously. | Run a fast bucket status/access check. Stop and ask for credentials or `anon` intent; do not guess regions, profiles, or endpoints. |
| Job analytics unavailable | Studio token is not configured or Studio API access failed. | Report the jobs workflow error. Configure Studio credentials before fetching job history. |
| Optional dependency import fails in a UDF | The base DataChain install does not include the ML, media, cloud, or model library used by the generated pipeline. | Install the specific missing dependency in the active environment. Do not install broad extras unless the workflow actually requires them. |
| Copilot local files not under `.copilot/` | This is expected: local Copilot uses `.github/instructions/` and `.datachain/skills/`. | Use the layout helper to show the resolved local Copilot layout. |
| Pi local files not under `.pi/agent/` | This is expected: local Pi uses `.pi/skills/` and `.pi/prompts/`. | Use the layout helper to distinguish global Pi from local Pi. |
| JSON files remain under `dc-knowledge/datasets` or `dc-knowledge/buckets` | Rebuild stopped before cleanup, or debugging retained intermediates. | Treat markdown as durable. Re-run cleanup/update when no debugging is needed. |

## Stale Knowledge Recovery

1. Confirm the agent is in the project that owns `.datachain/db` and
   `dc-knowledge/`.
2. Run a read-only smoke check on the knowledge directory.
3. If only markdown is stale, rebuild the knowledge base from the Dataset DB.
4. If bucket counts are stale, refresh the storage listing first when the user
   explicitly wants new/changed files included.
5. If credentials are missing, stop and ask; do not silently switch auth modes.

## Install/Uninstall Recovery

1. Print the intended layout with [skill_layout_check.py](../scripts/skill_layout_check.py).
2. Uninstall using the same `--target` and `--local` mode used for install.
3. Reinstall only the needed skills.
4. Re-run `datachain skill list` and, for target agents with command/rule files,
   verify that the command/rule file and skill directory both exist.
