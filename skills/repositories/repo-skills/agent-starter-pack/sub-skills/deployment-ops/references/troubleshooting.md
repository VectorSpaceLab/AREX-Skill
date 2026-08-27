# Deployment troubleshooting

## Authentication and tooling
### GitHub CLI problems
- `gh` is missing.
- The token is not authenticated.
- The token scopes are missing what the CI/CD runner needs.

### Google Cloud CLI problems
- `gcloud` is missing.
- Application-default credentials are not available.
- The selected project does not match the intended deployment target.

### Terraform problems
- The generated project does not contain the expected Terraform structure.
- The backend state bucket or state backend is misconfigured.
- The user requested a setup mode that conflicts with the generated project layout.

## CI/CD setup problems
- The repository name or owner is wrong.
- The user asked for both create-repository and use-existing-repository.
- The runner choice does not match the generated project’s workflow files.
- GitHub repository access is insufficient for the requested action.

## Data ingestion and observability problems
- The selected datastore does not match the template’s supported ingestion path.
- Bucket, dataset, or connection permissions are missing.
- A user expects telemetry features that the template does not actually ship.

## Gemini Enterprise registration problems
- The Agent Engine ID is malformed.
- The agent card URL cannot be fetched.
- The user has not deployed the agent yet.
- The project number or app ID is missing from the registration context.

## What to do next
- If the problem is really about changing the project itself, move back to `project-maintenance`.
- If the problem is about choosing a template or generation-time option, move back to `project-scaffolding`.
- If the problem needs a live cloud action, explain the prerequisite clearly before attempting any repair.
