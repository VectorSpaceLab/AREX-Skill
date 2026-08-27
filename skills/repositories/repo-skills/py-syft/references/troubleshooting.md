# Cross-cutting troubleshooting

| Symptom | Start with |
| --- | --- |
| Login or token/email mismatch | `auth-sync-transport` |
| Peer request pending/missing | `auth-sync-transport` |
| Dataset not found or permission denied | `datasets-permissions` |
| Job not submitted/run or outputs missing | `jobs-execution` |
| Notifications or auto-approval not working | `background-services` |
| TEE attestation or obfuscation failure | `enclaves-restrict` |

Safe checks:

```bash
python scripts/check_py_syft_install.py
python scripts/mock_rds_pair_smoke.py
```

Stop and ask before refreshing tokens, live Drive checks, deleting SyftBox state, starting services, approving jobs, provisioning cloud resources, or treating failed attestation as acceptable.
