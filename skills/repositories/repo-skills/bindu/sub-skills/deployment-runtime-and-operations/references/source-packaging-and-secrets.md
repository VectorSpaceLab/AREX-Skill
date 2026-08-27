# Source Packaging and Secrets

`bindu deploy` detects a project root by walking up from the script for `pyproject.toml`, `setup.py`, `requirements.txt`, or `.git`. It builds a gzipped tarball with `.gitignore` and `.binduignore` rules plus hard-coded safety exclusions.

Default excluded directories include `.git`, `.venv`, `venv`, `node_modules`, caches, and bytecode. Sensitive files are never shipped: `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, SSH keys, credential JSON/YAML, kubeconfigs, and secret directories such as `.aws`, `.ssh`, `.gnupg`, `.bindu`.

Compressed tarball cap: 50 MB. Add large data/model/build paths to `.binduignore`.

Use `bindu deploy SCRIPT --runtime=boxd --dry-run` to see agent name, source root, entry script, resource config, env-var keys, tarball size, and dropped sensitive files before any cloud action.
