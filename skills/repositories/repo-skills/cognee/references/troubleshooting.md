# Cross-cutting Cognee Troubleshooting

Read this before drilling into a sub-skill when the failure surface is unclear.

| Symptom | Likely owner | Next step |
| --- | --- | --- |
| `import cognee` fails | Install/package environment | Reinstall the base package, then run `python scripts/check_install.py --json`. |
| CLI is missing | CLI/service surface | Install Cognee in the active environment and route to [api-cli-services](../sub-skills/api-cli-services/SKILL.md). |
| LLM or embedding call fails with missing key | Configuration/provider setup | Route to [configuration-backends](../sub-skills/configuration-backends/SKILL.md); confirm `LLM_API_KEY`/`EMBEDDING_API_KEY` or local provider config. |
| Vector shape mismatch | Embedding configuration | Set `EMBEDDING_DIMENSIONS` to the selected embedding model’s actual dimension and isolate/rebuild incompatible stores. |
| Empty recall/search results | Search or graph build | Confirm data was ingested and cognified, then route to [search-retrieval](../sub-skills/search-retrieval/SKILL.md). |
| Session memory missing | Cache/session setup | Route to [agent-session-memory](../sub-skills/agent-session-memory/SKILL.md) and configuration cache settings. |
| Custom graph output shape is wrong | Custom model/prompt | Route to [advanced-graphs-pipelines](../sub-skills/advanced-graphs-pipelines/SKILL.md). |
| API, MCP, UI, Docker, or port failures | Service operation | Route to [api-cli-services](../sub-skills/api-cli-services/SKILL.md). |
| Optional backend import missing | Extra not installed | Install the specific extra for the selected backend; do not install all extras unless the user explicitly asks. |

## Debug order

1. Package import and version: `python scripts/check_install.py --json`.
2. Provider credentials and model/dimension settings.
3. Database/storage/cache backend selection and path isolation.
4. Dataset/session scope: dataset names, dataset ids, `session_id`, and user/agent identity.
5. Workflow-specific parameters: `SearchType`, custom graph model, task list, or service flags.

## Safety stop points

Stop and ask before:

- Starting long-running services if the user did not request it.
- Installing broad optional extras or mutating an existing user environment.
- Using real API keys or cloud credentials.
- Deleting all datasets or running destructive `forget`/`delete` commands.
