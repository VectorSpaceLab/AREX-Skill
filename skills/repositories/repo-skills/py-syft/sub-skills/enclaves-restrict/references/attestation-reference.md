# Attestation reference

Enclave peers can publish a Google Confidential Spaces attestation JWT. `verify_attestation_token(token, policy=None, verbose=True)` verifies signature, secure boot, debug status, syft-client version nonce, and optional container image digest.

Policy shape:

```python
from syft_enclaves.attestation import AppraisalPolicy, verify_attestation_token
policy = AppraisalPolicy(expected_image_digest="sha256:...", expected_syft_version="0.1.117")
verify_attestation_token(token, policy=policy)
```

Production appraisal should pin an independently confirmed image digest. Leaving `expected_image_digest=None` skips digest pinning and should be treated as development or incomplete production evidence. Debug status must be `disabled-since-boot`; secure boot must be true. GPU confidential-computing evidence is relevant only on GPU deployments.
