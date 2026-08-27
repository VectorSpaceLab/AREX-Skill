---
name: setup-and-deploy
description: "Install, initialize, run, package, and deploy doccano."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# setup-and-deploy

Use this sub-skill when you need doccano running for the first time, when you need to move between pip, Docker, Compose, or cloud deployment, or when you need the package build and source-install workflow that supports repository maintenance.

## Covers

- pip installation and optional PostgreSQL support
- database initialization, admin bootstrap, server startup, Celery worker startup, and Flower
- Docker image usage, Docker Compose deployment, AWS template deployment, and Heroku bootstrap helpers
- source build and packaging workflows used by maintainers
- basic install/runtime troubleshooting

## Excludes

- project creation, labels, members, annotation, comments, and metrics: use `project-annotation`
- import/export format details: use `data-transfer`
- auto-labeling setup and request mapping: use `auto-labeling`

## Typical path

1. Decide whether the task is pip, Docker, Compose, or cloud based.
2. Install doccano and verify the CLI is present.
3. Initialize the database and create the admin user.
4. Start the webserver and the task queue.
5. If the task is about packaging or contributor maintenance, read the build/test reference and use the bundled build helper.

## Read next

- `references/install-and-runtime.md` for installation and runtime commands.
- `references/build-and-test.md` for source builds, package builds, backend checks, and frontend developer commands.
- `references/deployment.md` for Docker, Compose, AWS, and Heroku deployment notes.
- `references/troubleshooting.md` for startup, packaging, and deployment failures.
- `scripts/build-package.sh` for the source packaging helper adapted from the repo-maintained packaging script.
- `../../scripts/cli-smoke.sh` for a quick install and CLI sanity check.
