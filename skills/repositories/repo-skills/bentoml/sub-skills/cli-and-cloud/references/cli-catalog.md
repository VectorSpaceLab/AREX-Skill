# BentoML CLI Catalog

This catalog summarizes CLI command families relevant to BentoCloud and safe operational planning. Confirm exact flags with `bentoml <command> --help` or the bundled `scripts/inspect_bentoml_cli.py` helper because installed versions may differ.

## Root Commands

The verified root CLI includes `api-token`, `build`, `cloud`, `code`, `containerize`, `delete`, `deploy`, `deployment`, `env`, `export`, `get`, `import`, `list`, `models`, `pull`, `push`, `secret`, and `serve`.

Use neighboring sub-skills for non-cloud concerns:

- Local service design: `../../service-authoring/SKILL.md`
- Local serve and HTTP clients: `../../serving-and-clients/SKILL.md`
- Build/containerize/push mechanics: `../../packaging-and-containerization/SKILL.md`
- Runtime observability and operations config: `../../observability-and-operations/SKILL.md`

## Safe Local Commands

| Command | Purpose | Cloud contact | Notes |
| --- | --- | --- | --- |
| `bentoml --help` | Show root command list | No | Safe first check. |
| `bentoml <group> --help` | Show subcommands/options | No | Use for version-specific flags. |
| `bentoml env` | Print environment info | No | Useful for diagnostics and support bundles. |
| `bentoml build --help` | Inspect build options | No | Build/container details belong to packaging. |
| `bentoml serve --help` | Inspect serve options | No | Serve execution belongs to serving-and-clients. |

## Cloud Context Commands

| Command | Purpose | Risk |
| --- | --- | --- |
| `bentoml cloud login [--endpoint URL] [--api-token TOKEN]` | Configure BentoCloud credentials and current context | Credentialed; avoid exposing token. |
| `bentoml cloud current-context` | Print active context JSON | Safe but may reveal endpoint/email. |
| `bentoml cloud list-context` | List configured context names | Safe but may reveal context names. |
| `bentoml cloud update-current-context CONTEXT` | Switch active context | Mutates local CLI config; confirm target. |

`cloud login` reads `BENTO_CLOUD_API_ENDPOINT` and `BENTO_CLOUD_API_KEY` when set. Prefer environment-secret injection in CI and avoid placing token literals in shared logs.

## Deployment Creation

`bentoml deploy [BENTO]` creates a BentoCloud deployment. The `BENTO` argument can be omitted, a local project directory such as `.`, or an existing Bento reference such as `name:version`.

Important flags:

- `-n, --name`: deployment name.
- `--cluster`: target BentoCloud cluster.
- `--access-authorization`: enable protected endpoint access.
- `--scaling-min`, `--scaling-max`: autoscaling bounds.
- `--instance-type`: hardware type such as `cpu.2` or GPU families available to the account.
- `--strategy`: deployment strategy such as `Recreate`, `RollingUpdate`, `RampedSlowRollout`, or `BestEffortControlledRollout`.
- `--label key=value`: repeatable labels.
- `--env key=value` or `--env KEY`: repeatable environment variables; `--env KEY` reads from the caller's environment.
- `--secret NAME`: repeatable BentoCloud secret names attached to the deployment.
- `-f, --config-file`: YAML/JSON deployment config.
- `--config-dict`: JSON string config.
- `--wait/--no-wait`, `--timeout`: readiness wait behavior.
- `--arg`, `--arg-file`: build/service argument injection inherited from CLI utilities.

## Deployment Management

| Command | Purpose | Notes |
| --- | --- | --- |
| `bentoml deployment list [--cluster CLUSTER] [--search TEXT] [--label KEY=VALUE] [-o table|json|yaml]` | List deployments | Credentialed read. |
| `bentoml deployment get NAME [--cluster CLUSTER] [-o yaml|json]` | Retrieve details, endpoint URLs, config, and status | Credentialed read. |
| `bentoml deployment update NAME ...` | Patch only specified fields | Safer for incremental changes. |
| `bentoml deployment apply [BENTO] -n NAME -f CONFIG` | Create/update toward full desired config | Can reset unspecified fields. |
| `bentoml deployment start NAME` | Start terminated deployment | Mutating; may resume cost. |
| `bentoml deployment terminate NAME [--wait]` | Stop deployment | Mutating; can be restarted. |
| `bentoml deployment delete NAME` | Delete deployment | Destructive and irreversible. |
| `bentoml deployment list-instance-types [--cluster CLUSTER]` | List available hardware | Credentialed read. |

`deployment update` accepts `--bento`, `--access-authorization`, scaling flags, `--instance-type`, `--strategy`, `--label`, `--env`, `--secret`, `-f/--config-file`, `--config-dict`, and `--arg/--arg-file`.

## Codespaces

`bentoml code [BENTO_DIR]` creates or attaches to a BentoCloud codespace.

Useful flags:

- `--attach NAME`: attach to an existing codespace instead of creating one.
- `--cluster CLUSTER`: select cluster.
- `--env key=value` or `--env KEY`: set environment variables when creating.
- `--secret NAME`: attach BentoCloud secrets when creating.
- `--arg`, `--arg-file`: pass build/service arguments.

Do not combine `--attach` with `--env` or `--secret`; the CLI rejects that combination because attach does not create a new environment.

## Secrets

| Command | Purpose | Risk |
| --- | --- | --- |
| `bentoml secret list [-o table|json|yaml] [--search TEXT]` | List secrets | Does not print secret values, but reveals names/keys. |
| `bentoml secret create NAME KEY=VALUE ...` | Create secret | Sensitive; prefer local shell, redaction, or dotenv file. |
| `bentoml secret apply NAME KEY=VALUE ...` | Create/update secret | Sensitive and mutating. |
| `bentoml secret delete NAME` | Delete secret | Destructive; can break deployments. |

Secret flags include `--cluster`, `-d/--description`, `-t/--type env|file`, `-s/--stage build|runtime|all`, `-p/--path`, and `-f/--from-file DOTENV_FILE`. Values can be loaded from files with `KEY=@path` or from dotenv files with `--from-file`.

## API Tokens

| Command | Purpose | Risk |
| --- | --- | --- |
| `bentoml api-token list [-o table|json|yaml] [--search TEXT]` | List token metadata | Credentialed read; no token values. |
| `bentoml api-token create NAME [--scope SCOPE] [--expires 30d]` | Create token | Prints token once; protect output. |
| `bentoml api-token get UID [-o table|json|yaml]` | Inspect token metadata | Credentialed read. |
| `bentoml api-token delete UID` | Delete token | Destructive; may break automation. |

Known scopes include `api`, `read_organization`, `write_organization`, `read_cluster`, and `write_cluster`. Expiration accepts duration forms such as `30d`, `1w`, `24h`, or date/time strings such as `2024-12-31`.

## Push And Pull

- `bentoml push BENTO_TAG` uploads a local Bento to BentoCloud; it is credentialed and mutating.
- `bentoml pull BENTO_TAG` downloads a Bento from BentoCloud; it is credentialed and can overwrite local store state depending on flags.
- `bentoml build --push` pushes after build, and `bentoml build --containerize` enters packaging/container responsibilities.

For build and container flags, defer to `../../packaging-and-containerization/SKILL.md`.
