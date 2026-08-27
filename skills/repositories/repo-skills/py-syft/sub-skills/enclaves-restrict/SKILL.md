---
name: enclaves-restrict
description: "Operate PySyft enclave, Confidential Spaces, attestation, and
  syft-restrict private-code verification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# enclaves-restrict

Use this sub-skill for `syft-enclave`, multi-owner private-private jobs, Confidential Spaces, `python -m syft_enclaves`, `SYFT_ENCLAVE_*` environment variables, TEE attestation verification, image digest pinning, and `syft-restrict` private-code obfuscation/verification.

## Workflow

1. Determine whether the user needs a local/mock enclave explanation, a production TEE deployment plan, attestation appraisal, or static model-code verification.
2. For enclave runner configuration, render/check environment variables with [scripts/render_enclave_env.py](scripts/render_enclave_env.py).
3. For private model-code sharing, mark private regions with `# syft-restrict: obfuscate-start` / `obfuscate-end` or `hide` markers, then run [scripts/verify_obfuscate_file.py](scripts/verify_obfuscate_file.py).
4. For production, require `SYFT_ENCLAVE_REQUIRE_TEE=true`, data-owner list, token handling, and independently verified image digest policy.
5. For attestation, do not treat unsigned, expired, debug-enabled, unpinned, or version-mismatched tokens as production-ready.

Read [references/enclave-workflows.md](references/enclave-workflows.md), [references/attestation-reference.md](references/attestation-reference.md), [references/syft-restrict-policy.md](references/syft-restrict-policy.md), and [references/troubleshooting.md](references/troubleshooting.md).
