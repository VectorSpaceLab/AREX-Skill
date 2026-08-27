# CLI And BentoCloud Troubleshooting

Start with safe local checks, then move to credentialed reads, then mutating fixes only after user confirmation.

## Safe First Checks

```bash
bentoml --help
bentoml cloud --help
bentoml deployment --help
bentoml env
python skills/bentoml/sub-skills/cli-and-cloud/scripts/deployment_config_lint.py deployment.yaml
```

Use `scripts/inspect_bentoml_cli.py` to collect version-specific help text without contacting BentoCloud.

## Not Logged In Or Token Invalid

Symptoms:

- CLI error says BentoCloud API token is required.
- HTTP 401 or bad credentials during `deploy`, `deployment`, `secret`, or `api-token` commands.

Actions:

1. Do not ask the user to paste tokens into chat.
2. Ask the user to run `bentoml cloud login` interactively or use a masked `BENTOCLOUD_API_TOKEN` secret in CI.
3. Confirm `bentoml cloud current-context` after login.
4. If using `--api-token`, verify the endpoint matches the token's organization.

## Wrong Context Or Cluster

Symptoms:

- Deployment, secret, or instance type is missing.
- Command works in one shell but not another.
- Resources appear in an unexpected organization or region.

Actions:

```bash
bentoml cloud current-context
bentoml cloud list-context
bentoml deployment list --cluster <expected-cluster>
bentoml deployment list-instance-types --cluster <expected-cluster>
```

Switch with `bentoml cloud update-current-context <context-name>` only after the user confirms the target. Pass `--cluster` explicitly for deployment and secret operations in multi-cluster accounts.

## Invalid Deployment Config

Symptoms:

- CLI says deployment config is invalid.
- `--label` rejects a value.
- Environment variable is missing when using `--env NAME`.
- Deployment create/update/apply fails before or during verification.

Actions:

1. Lint YAML/JSON locally with `scripts/deployment_config_lint.py`.
2. Ensure labels are `key=value`.
3. For `--env NAME`, ensure `NAME` exists in the current shell; use `--env NAME=value` for explicit values.
4. Use config-file structure with `name`, `bento`, `envs`, and `services` for complex deployments.
5. Use `update` for partial patches and `apply` only when a full desired-state file is intended.

## Missing Secret

Symptoms:

- Deployment references `--secret NAME` but startup fails or deployment validation complains.
- The secret exists in another cluster.

Actions:

```bash
bentoml secret list --search <name> -o table
bentoml secret list --search <name> -o yaml
```

If creating or updating secrets, keep values out of chat and shared logs:

```bash
bentoml secret apply <secret-name> --from-file <dotenv-file> --stage runtime --cluster <cluster-name>
```

Then update or redeploy with `--secret <secret-name>`.

## Wait Timeout Or Deployment Not Ready

Symptoms:

- `bentoml deploy` waits until timeout.
- Deployment remains `deploying`, `failed`, or `scaled_to_zero`.

Actions:

```bash
bentoml deployment get <deployment-name> --cluster <cluster-name> -o yaml
bentoml deployment list --cluster <cluster-name>
```

Then inspect BentoCloud console logs/status. Common fixes include increasing `--timeout`, lowering `--scaling-min`/`--scaling-max`, choosing a smaller available `--instance-type`, checking secrets/env vars, or rolling out a known-good Bento with `deployment update --bento`.

## Cloud Quota Or Instance Unavailable

Symptoms:

- Requested GPU/CPU instance type cannot be scheduled.
- Scaling bounds exceed account or cluster quota.

Actions:

```bash
bentoml deployment list-instance-types --cluster <cluster-name>
```

Reduce replicas, switch instance type, select a different cluster, or ask the user to request BentoCloud quota. Do not retry high-cost deploys repeatedly without user confirmation.

## Push/Pull Auth Failures

Symptoms:

- `bentoml push` or `bentoml pull` fails with authorization or not-found errors.

Actions:

1. Confirm login and context.
2. Confirm Bento tag spelling and version.
3. Confirm the token has required organization/cluster access.
4. Use build/package guidance from `../../packaging-and-containerization/SKILL.md` for local Bento creation issues.

## Destructive Operation Guardrails

Before `delete`, `terminate`, secret deletion, or API token deletion, state:

- Target name/UID and cluster/context.
- Consequence and reversibility.
- Safer alternative, if any.

Examples:

- Prefer `bentoml deployment terminate` over `delete` when the user may need to restart the deployment.
- Prefer `api-token get` or `list` before deleting a token by UID.
- Prefer `secret apply` to rotate values instead of deleting a secret used by active deployments.
