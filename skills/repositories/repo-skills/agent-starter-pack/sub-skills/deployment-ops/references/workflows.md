# Deployment workflows

## CI/CD bootstrap
Use `setup-cicd` when the user wants the generated project to provision a staging/production pipeline and connect it to GitHub.

Typical flow:
1. Run the command from the generated project root.
2. Confirm staging and production project IDs.
3. Choose or detect the CI/CD runner.
4. Decide whether the repository is new or existing.
5. Provision Terraform state and the necessary cloud resources.
6. Link the GitHub repository and configure triggers.

Common `setup-cicd` signals:
- `--staging-project`
- `--prod-project`
- `--cicd-project`
- `--dev-project`
- `--region`
- `--repository-name`
- `--repository-owner`
- `--host-connection-name`
- `--github-pat`
- `--github-app-installation-id`
- `--local-state`
- `--auto-approve`
- `--create-repository`
- `--use-existing-repository`
- `--cicd-runner`

## Generated-project deployment commands
Use the generated `Makefile` after a project exists.

Core commands to remember:
- `make install`
- `make playground`
- `make lint`
- `make test`
- `make deploy`
- `make setup-dev-env`
- `make register-gemini-enterprise`
- `make data-ingestion`
- `make sync-data`
- `make inspector`

Template-specific commands may also exist for live frontends, local backends, or load tests.

## Data ingestion and observability
- `agentic_rag` is the clearest template that needs data ingestion.
- Data ingestion can be Vertex AI Search or Vertex AI Vector Search.
- Cloud Trace telemetry is always present in generated projects.
- BigQuery Agent Analytics is an opt-in ADK feature and is not available everywhere.

## Gemini Enterprise registration
Use the registration guide when the user already deployed an agent and wants to expose it to Gemini Enterprise.

Signal differences to keep in mind:
- ADK on Agent Engine uses an Agent Engine ID.
- A2A on Cloud Run or GKE uses an agent card URL.
- The command can infer metadata from deployment output when available.

## Handoff points
- If the user only wants to understand how a template is generated, hand back to `project-scaffolding`.
- If the user wants to patch a generated project before deploying it, hand back to `project-maintenance`.
