# Enclave workflows

The enclave flow has DO1, DO2, DS, and a neutral secure enclave. Data owners upload private assets toward the enclave; DS submits analysis; all listed data owners must approve; the enclave runs the approved analysis in a confidential container; only agreed outputs return.

Runner command:

```bash
python -m syft_enclaves
```

Required/high-value environment variables:

| Variable | Purpose |
| --- | --- |
| `SYFT_ENCLAVE_EMAIL` | Enclave datasite email. |
| `SYFT_ENCLAVE_DATA_OWNERS` | Comma-separated owner emails; all must approve each job. |
| `SYFT_ENCLAVE_TOKEN_PATH` | Pre-authorized Drive token path; production default is `/run/syft-enclave/token.json`. |
| `SYFT_ENCLAVE_POLL_INTERVAL` | Poll seconds; minimum 1. |
| `SYFT_ENCLAVE_REQUIRE_TEE` | Refuse startup outside Confidential Spaces when true. |
| `SYFT_ENCLAVE_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, or `ERROR`. |
| `SYFT_ENCLAVE_FRESH_STATE` | Wipe local/Drive state at boot when true. |
| `SYFT_ENCLAVE_USE_ENCRYPTION` | End-to-end encrypted peer communication when true. |

Use the bundled render script to build a `.env` without exposing token contents.
