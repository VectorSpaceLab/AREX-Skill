# Model Repository Troubleshooting

## Symptom-to-fix map

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Invalid git repo url` | URL does not match the supported Git syntax. | Run `scripts/validate_repo_url.py` first. Check for a missing scheme, owner, repo, or branch formatting issue. |
| `Invalid repo name` | Alias contains unsupported characters. | Use a lowercase identifier-style alias. |
| `Repo <name> not found` | The configured repo alias is not present. | Run `openllm repo list` or inspect the generated config path in the `environment-maintenance` sub-skill. |
| `The repo cache is never updated` | No repository refresh has occurred yet. | Run `openllm repo update` when network access is available. |
| `The repo cache is outdated` | Model metadata is older than OpenLLM's update interval. | Refresh the repository cache before relying on the latest model list. |
| `No model found for ...` | The requested tag is missing from the selected repo. | Inspect `openllm model list`, verify the repo alias, and check whether the tag should include a version suffix. |
| Multiple models match a tag | The tag is too broad. | Add a version suffix or inspect the rendered table to choose the exact Bento. |
| Git clone failure during repo update | Network, DNS, auth, or remote repository problem. | Verify the public repo URL and retry after fixing network or proxy issues. |

## Recovery order

1. Validate the repo URL.
2. Confirm the alias exists.
3. Refresh the repository cache.
4. Inspect the model list for exact tags.
5. Only then attempt a serving workflow.

## Helper to use next

- `scripts/validate_repo_url.py` for safe URL parsing.
- `scripts/inspect_model_catalog.py` for local catalog inspection without network.
