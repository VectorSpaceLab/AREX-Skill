# Dependency Environment Decorators

## Decorators

- `@pypi(packages={}, python=None, disabled=None)` applies PyPI packages to one step.
- `@pypi_base(packages={}, python=None, disabled=None)` applies PyPI packages to all steps.
- `@conda(packages={}, libraries={}, python=None, disabled=None)` applies Conda/PyPI-style dependencies to one step.
- `@conda_base(packages={}, libraries={}, python=None, disabled=None)` applies dependencies to all steps.

Step-level packages augment or override flow-level base packages. Use explicit version pins for reproducibility.

## Environment modes

- `--environment=local`: run in the current interpreter; dependency decorators that require isolated environments are not satisfied.
- `--environment=conda`: create Conda/micromamba-backed step environments.
- `--environment=pypi`: user-facing alias for PyPI package resolution on the Conda-backed environment implementation in this version.
- `--environment=uv`: use the UV environment implementation where supported.

Do not install all dev requirements merely to run one step. Select only packages required by the flow steps and datastore/backend.

## Datastore-pinned libraries

Metaflow pins runtime libraries for isolated environments based on datastore type:

- local: `requests`.
- S3: `requests` plus `boto3`.
- Azure: Azure identity/storage/key-vault and downloader packages.
- GS: Google Cloud storage/auth/secret-manager, downloader, and packaging.

If a remote step cannot access artifacts, check whether its isolated environment contains the libraries required by the selected datastore.
