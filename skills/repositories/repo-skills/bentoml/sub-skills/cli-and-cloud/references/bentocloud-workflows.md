# BentoCloud Workflows

Use these workflows to construct safe command plans. Run credentialed commands only after the user confirms the target account, context, cluster, and mutating intent.

## Authentication And Context

1. Confirm whether this is local interactive use, CI, or an already-authenticated shell.
2. For interactive local login, use:

   ```bash
   bentoml cloud login
   ```

3. For CI, use a masked secret and avoid echoing it:

   ```bash
   bentoml cloud login --api-token "$BENTOCLOUD_API_TOKEN"
   ```

4. Confirm context before changing resources:

   ```bash
   bentoml cloud current-context
   bentoml cloud list-context
   ```

5. Switch only after the user names the intended context:

   ```bash
   bentoml cloud update-current-context <context-name>
   ```

`cloud login` can also use `BENTO_CLOUD_API_ENDPOINT` and `BENTO_CLOUD_API_KEY`. Treat context output as potentially identifying because it can include account endpoint and user email.

## First Deployment

For a single-service project in the current directory:

```bash
bentoml deploy . -n <deployment-name> --cluster <cluster-name> --wait --timeout 3600
```

Add common options as needed:

```bash
bentoml deploy . \
  -n <deployment-name> \
  --cluster <cluster-name> \
  --scaling-min 0 \
  --scaling-max 3 \
  --instance-type cpu.2 \
  --access-authorization true \
  --label team=ml-platform \
  --env LOG_LEVEL=info \
  --secret hf-token \
  --wait
```

Deployment creates a Bento when given a project directory and pushes it to BentoCloud as part of creation. If the user only wants to share a Bento without deploying, use `bentoml push <bento_tag>` after build/package planning.

## Configuration File Deployment

Prefer config files when there are multiple services, service-specific resources, config overrides, or repeatable promotion between environments.

Example shape:

```yaml
name: my-deployment
bento: .
access_authorization: true
envs:
  - name: LOG_LEVEL
    value: info
services:
  MyService:
    instance_type: cpu.2
    scaling:
      min_replicas: 1
      max_replicas: 3
    deployment_strategy: Recreate
```

Lint locally before invoking cloud:

```bash
python skills/bentoml/sub-skills/cli-and-cloud/scripts/deployment_config_lint.py deployment.yaml
bentoml deploy -f deployment.yaml
```

## Update, Apply, And Rollout

Use `update` when only explicit fields should change:

```bash
bentoml deployment update <deployment-name> --cluster <cluster-name> --scaling-min 1 --scaling-max 5
bentoml deployment update <deployment-name> --cluster <cluster-name> --bento <bento-name>:<version>
bentoml deployment update <deployment-name> --cluster <cluster-name> --bento ./project-directory
```

Use `apply` when the file should represent the desired full state:

```bash
bentoml deployment apply <deployment-name> --cluster <cluster-name> -f deployment.yaml
```

Explain the difference to users:

- `update` is patch-only; omitted fields remain unchanged.
- `apply` reconciles to the supplied config; omitted fields may reset or disappear.

Rollbacks are available from the BentoCloud console revision UI. The CLI evidence covers list/get/update/apply/start/terminate/delete and instance-type listing; do not invent an unsupported rollback CLI command.

## Inspect Endpoints

Retrieve deployment details and endpoint URLs:

```bash
bentoml deployment get <deployment-name> --cluster <cluster-name> -o json
```

If using `jq`, extract endpoint URLs with:

```bash
bentoml deployment get <deployment-name> -o json | jq '.endpoint_urls'
```

Calling the endpoint with BentoML HTTP clients belongs to `../../serving-and-clients/SKILL.md`.

## Scaling And Hardware

Before choosing an instance type, list account/cluster availability:

```bash
bentoml deployment list-instance-types --cluster <cluster-name>
```

Common scaling flags:

```bash
bentoml deploy . --scaling-min 0 --scaling-max 3
bentoml deployment update <deployment-name> --scaling-min 1 --scaling-max 5
```

If quota or instance availability errors occur, reduce replica bounds, select a smaller instance type, change cluster, or ask the user to check BentoCloud quota.

## Authorization And API Tokens

Enable protected endpoint access at deployment time:

```bash
bentoml deploy . --access-authorization true
```

Create a token for endpoint/API use only in a user-controlled shell:

```bash
bentoml api-token create <token-name> --scope api --expires 30d
```

For organization/cluster automation, add the minimum required scopes such as `read_cluster` or `write_cluster`. Warn that token values are displayed once and should never be pasted back into shared logs.

## Secrets

Create secrets before referencing them from deployments:

```bash
bentoml secret create hf-token HF_TOKEN=@./hf-token.txt --type env --stage runtime --cluster <cluster-name>
bentoml deploy . --secret hf-token
```

For multiple values, prefer dotenv ingestion:

```bash
bentoml secret apply app-secrets --from-file .env.production --stage runtime --cluster <cluster-name>
```

Use `--type file --path <path>` when a secret must be mounted as a file. The CLI maps `--type file` to BentoCloud mount-file secrets.

## Codespaces

Create or attach to a BentoCloud codespace:

```bash
bentoml code . --cluster <cluster-name> --secret hf-token --env LOG_LEVEL=debug
bentoml code --attach <codespace-name>
```

Do not pass `--env` or `--secret` with `--attach`; the CLI rejects this because an existing codespace is reused.

## CI/CD

A typical CI deployment sequence is:

```bash
bentoml cloud login --api-token "$BENTOCLOUD_API_TOKEN"
bentoml deploy . -n "$DEPLOYMENT_NAME" --cluster "$BENTOCLOUD_CLUSTER" --no-wait
```

Safer CI pattern for existing deployments:

```bash
bentoml cloud login --api-token "$BENTOCLOUD_API_TOKEN"
bentoml deployment update "$DEPLOYMENT_NAME" --cluster "$BENTOCLOUD_CLUSTER" --bento .
```

Use masked CI secrets, minimal token scopes, and explicit cluster/deployment variables. Avoid embedding token literals in YAML committed to source control.

## Cleanup

Stop cost-incurring resources without deleting revision history:

```bash
bentoml deployment terminate <deployment-name> --cluster <cluster-name> --wait
```

Delete only after explicit confirmation:

```bash
bentoml deployment delete <deployment-name> --cluster <cluster-name>
```

Secret and API token cleanup are also destructive:

```bash
bentoml secret delete <secret-name> --cluster <cluster-name>
bentoml api-token delete <token-uid>
```
