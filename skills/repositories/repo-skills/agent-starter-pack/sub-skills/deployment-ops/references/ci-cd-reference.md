# CI/CD reference

## What `setup-cicd` does
`setup-cicd` provisions the infrastructure and repository wiring needed for a generated project to deploy through staging into production.

It coordinates:
- GitHub repository setup
- Cloud Build or GitHub Actions configuration
- Terraform state and environment resources
- repository connection or authentication material
- generated deployment triggers

## Prerequisites
- GitHub CLI (`gh`)
- Google Cloud CLI (`gcloud`)
- Terraform
- Access to the required Google Cloud projects
- A usable GitHub repository owner/name

## Runner split
### Cloud Build
- Uses GitHub connection material and Cloud Build resources.
- Can run in interactive or programmatic auth modes.
- May require a GitHub PAT secret or a GitHub App installation ID.

### GitHub Actions
- Uses Workload Identity Federation and repository secrets/variables.
- Requires GitHub repository auth that can create the workflow wiring.

## Important options
- `--staging-project` and `--prod-project` define the deployment targets.
- `--cicd-project` selects the project that hosts CI/CD resources.
- `--region` controls Terraform and cloud resource placement.
- `--local-state` replaces the default remote GCS state backend.
- `--create-repository` and `--use-existing-repository` are mutually exclusive.
- `--cicd-runner` can be set explicitly or inferred from the generated project.

## What can go wrong
- GitHub CLI is not installed or not authenticated.
- GitHub token scopes are insufficient.
- `gcloud` is missing or ADC is not configured.
- The project layout does not contain the expected Terraform structure.
- The user supplies contradictory repository or runner flags.

## What this is not
This reference is about provisioning the generated project’s delivery pipeline, not about starting a brand-new template or upgrading an existing project.
