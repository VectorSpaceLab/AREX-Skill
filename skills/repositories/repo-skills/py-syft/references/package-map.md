# PySyft package map

| Distribution | Import | Role |
| --- | --- | --- |
| `syft-client` | `syft_client` | Login, Drive/SyftBox transport, peers, token utilities, dataset path utilities. |
| `syft-rds` | `syft_rds` | Remote data science client combining sync, datasets, and jobs. |
| `syft-dataset` | `syft_datasets` | Mock/private dataset storage and protocol layouts. |
| `syft-job` | `syft_job` | Job submission, state, runner, generated `run.sh`, protocol codecs. |
| `syft-bg` | `syft_bg` | Background notify/approve services and CLI. |
| `syft-enclave` | `syft_enclaves` | Enclave clients, runner, environment, and attestation. |
| `syft-restrict` | `syft_restrict` | Static private-region verifier/obfuscator. |
| `syft-permissions` | `syft_permissions` | Low-level `syft.pub.yaml` ACL engine. |
| `syft-perms` | `syft_perms` | User-facing file/folder permission API. |
| `syft-migration` | `syft_migration` | Protocol/version migrations used by jobs/datasets. |
| `syft-notebook-ui` | `syft_notebook_ui` | Rich notebook displays. |

Use `scripts/check_py_syft_install.py` for import and metadata checks.

## CLI caveats

- `syft-bg --help` is the primary background-services CLI.
- In the inspected package version, `syft-job` maps to `syft_job:main`, but `syft_job.__init__` does not export `main`. Prefer `python -m syft_job.runner_main --help` or package APIs until that entry point is fixed.
