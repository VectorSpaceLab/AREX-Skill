# Source build and contributor checks

This repository uses Poetry for the Python backend and Yarn for the frontend.

## Backend development commands

From `backend/`:

```bash
poetry install
poetry run task wait_for_db
poetry run task migrate
poetry run task test
poetry run task flake8
poetry run task isort
poetry run task black
poetry run task mypy
```

## Frontend development commands

From `frontend/`:

```bash
yarn install
yarn dev
yarn lint
yarn lint:prettier
yarn fix:prettier
yarn build
yarn start
```

## Package build workflow

The repo-maintained build helper builds the frontend, copies the compiled client into the backend package layout, installs backend dependencies, collects static files, and then builds the Python package.

Use the bundled `scripts/build-package.sh` when you need that end-to-end packaging path in one step.

## CI signal

The backend CI workflow runs the Poetry install, database migration, formatting, type-check, and test commands. The frontend CI workflow runs Yarn install and the lint/prettier checks.
