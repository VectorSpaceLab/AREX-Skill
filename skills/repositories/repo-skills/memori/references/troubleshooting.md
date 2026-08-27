# Memori Troubleshooting

## Cross-cutting failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` or wrong package version | wrong environment or stale editable install | run the bundled install smoke, then reinstall `memori` in the intended environment |
| CLI banner/help looks wrong | a different `python` is being used | run the bundled smoke script from the target environment Python |
| Optional driver import fails | missing extra or provider SDK | install only the extra needed for the selected workflow |
| Cloud call fails without credentials | missing `MEMORI_API_KEY` or quota | set the key, check quota, and retry only if the request payload is valid |
| SQLite/BYODB works in tests but not in a user script | schema build was skipped | call `mem.config.storage.build()` once after creating the instance |
| Memory recall is empty | missing attribution, no wait, or wrong mode | verify `entity_id`, `process_id`, `augmentation.wait()`, and cloud vs BYODB mode |
| Native model/runtime path fails | optional Rust core or model download issue | temporarily disable Rust core and diagnose the base Python path first |
| TypeScript import or peer dependency fails | Node version too old or missing peer packages | install Node 20.19+ and the required driver/provider package |

## Safe recovery rules

- Prefer the smallest fix that matches the selected route.
- Do not suggest running maintainer release scripts or destructive cluster
  commands as a user-facing remedy.
- Do not claim GPU support; Memori's selected default verification path is CPU.
- If a required backend is missing for the chosen workflow, explain the exact
  missing dependency or service instead of papering over it with a generic skip.

## Where to go next

- Cloud / CLI / MCP failures: `sub-skills/cli-and-cloud/references/troubleshooting.md`
- BYODB setup / driver / provisioning failures: `sub-skills/byodb-storage/references/troubleshooting.md`
- Python LLM provider failures: `sub-skills/llm-integration/references/troubleshooting.md`
- Recall/search/native failures: `sub-skills/memory-and-search/references/troubleshooting.md`
- TypeScript / Node failures: `sub-skills/typescript-sdk/references/troubleshooting.md`
