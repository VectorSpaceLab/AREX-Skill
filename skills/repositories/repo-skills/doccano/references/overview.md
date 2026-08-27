# Repository overview

doccano is a web-based annotation platform for building labeled datasets. The repository is split into a Python backend, a Nuxt frontend, deployment helpers, and documentation.

## Main surfaces

| Surface | What it owns | Typical questions |
| --- | --- | --- |
| `backend/` | Django apps, models, serializers, Celery tasks, CLI commands, and REST APIs | Install, run, manage projects, import/export data, auto-labeling, and repository tests |
| `frontend/` | Nuxt pages, components, routes, and client-side workflow UI | Which page to use for labels, members, datasets, metrics, or task-specific annotation screens |
| `docs/` | Installation, tutorial, FAQ, developer guide, and advanced deployment notes | How to install, deploy, troubleshoot, or use a doccano workflow |
| `tools/` | Repo-maintained shell helpers for packaging and container/runtime entry points | Build package, Docker runtime, Heroku bootstrap, and production startup behavior |
| `docker/` | Dockerfiles, compose files, and nginx config | Local image builds, container startup, and compose deployment |
| `cloud/aws/` | CloudFormation deployment template | One-click AWS EC2 deployment |

## User workflow families

- Setup and deploy: install doccano, initialize the database, create an admin, start the webserver, run the Celery worker, and deploy with Docker or cloud helpers.
- Project annotation: create projects, define labels, add members, assign work, annotate documents or files, and inspect progress metrics.
- Data transfer: import source files into a project and export annotations back out in task-appropriate formats.
- Auto-labeling: configure external model/API requests, map responses into doccano labels, and enable automated labeling inside a project.
- Repository maintenance: build the package, run tests and checks, and update source or documentation safely.

## Key package facts

- Backend package name: `doccano`.
- Primary import root: `backend`.
- CLI entry point: `doccano`.
- Default port: `8000`.
- Default database: SQLite unless `DATABASE_URL` overrides it.
- Default task runner: Celery worker started with `doccano task` or the Docker helper scripts.

## Read next

- `task-types.md` for supported project types and annotation shapes.
- `cli-reference.md` for the full CLI and environment variables.
- `troubleshooting.md` for installation, runtime, and data-validation failures.
