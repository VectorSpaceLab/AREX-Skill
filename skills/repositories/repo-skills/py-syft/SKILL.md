---
name: py-syft
description: "Route PySyft privacy-preserving remote data science, SyftBox sync,
  datasets, jobs, background services, enclaves, and syft-restrict workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PySyft repo skill

Use this skill for PySyft v2 / `syft-client` workflows: data-owner and data-scientist login, SyftBox/Google Drive peer sync, mock/private datasets, remote jobs, `syft-bg` background services, `syft-enclave` TEE workflows, and `syft-restrict` private-code verification.

## Safe local checks

From this skill directory:

```bash
python scripts/check_py_syft_install.py
python scripts/mock_rds_pair_smoke.py
```

These checks do not contact Google Drive, Gmail, Pub/Sub, GCP, Docker, or a TEE. Passing them proves local package usability only.

## Route by intent

- Auth, OAuth token files, peer approval, sync, Drive transport, checkpoints, versions, and cleanup: [sub-skills/auth-sync-transport/SKILL.md](sub-skills/auth-sync-transport/SKILL.md).
- Dataset create/read/share/delete, mock/private split, `resolve_dataset_file_path`, `syft://`, `syft.pub.yaml`, and permissions: [sub-skills/datasets-permissions/SKILL.md](sub-skills/datasets-permissions/SKILL.md).
- Job submission/review/run, outputs/logs, entrypoints/dependencies, generated `run.sh`, and `syft-job`: [sub-skills/jobs-execution/SKILL.md](sub-skills/jobs-execution/SKILL.md).
- `syft-bg` notify/approve services, auto-approval, logs, TUI, systemd, Gmail/PubSub: [sub-skills/background-services/SKILL.md](sub-skills/background-services/SKILL.md).
- Enclaves, Confidential Spaces, TEE attestation, `SYFT_ENCLAVE_*`, `syft-restrict`, and obfuscation policy: [sub-skills/enclaves-restrict/SKILL.md](sub-skills/enclaves-restrict/SKILL.md).

## Cross-cutting references

- [references/package-map.md](references/package-map.md) maps distributions, imports, and CLIs.
- [references/remote-data-science-overview.md](references/remote-data-science-overview.md) summarizes the DO/DS lifecycle.
- [references/troubleshooting.md](references/troubleshooting.md) routes common failures.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot and staleness signals.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) provides managed repo-router metadata.

## Safety

Do not tell users to open original repository files at runtime; use bundled references and scripts. Ask before refreshing OAuth tokens, deleting SyftBox state, starting daemons, approving jobs, provisioning cloud resources, running notebooks, or accepting failed/unpinned production attestation.
