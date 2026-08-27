# Generated-project commands

This page summarizes the Makefile targets that generated projects commonly expose.

## Universal targets
- `make install` — install dependencies.
- `make playground` — launch the local playground.
- `make lint` — run code-quality checks.
- `make test` — run tests.
- `make deploy` — deploy the project.
- `make setup-dev-env` — provision a dev environment with Terraform.
- `make register-gemini-enterprise` — register a deployed agent.

## Data and observability targets
- `make setup-datastore` — provision datastore resources where supported.
- `make data-ingestion` — run a data-ingestion pipeline where supported.
- `make sync-data` — trigger a data sync for datastore-backed projects.
- `make inspector` — launch the A2A protocol inspector where supported.

## Additional targets that may appear by template
- `make local-backend`
- `make ui`
- `make build-frontend`
- `make playground-dev`
- `make playground-remote`
- `make build`
- `make clean`
- `make load-test`
- custom extra commands defined by the template configuration

## Template sensitivity
Not every target exists in every generated project.
Availability depends on:
- template family
- deployment target
- whether CI/CD scaffolding was included
- whether the project includes live UI, RAG, or A2A support

## How to use this reference
When a user asks about "what can I run in the generated project?", use this page to identify the target family and then hand them to the more specific workflow reference for deployment, observability, data ingestion, or Gemini Enterprise.
