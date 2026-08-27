# Remote data science overview

1. Data Owner and Data Scientist authenticate with `login_do` / `login_ds`.
2. DS calls `add_peer(do_email)`; DO approves; both sides sync.
3. DO publishes a dataset with mock and private files. Mock is shared; private stays owner-side.
4. DS develops against mock files.
5. DS submits a Python or bash job.
6. DO reviews, approves or rejects, and runs approved jobs on private data.
7. DO shares outputs and optionally logs; both sides sync.
8. `syft-bg` can automate notification and approval with explicit file/hash/peer policy.
9. `syft-enclave` adds a TEE peer and multi-owner approval when private assets from several owners must meet only inside a confidential environment.

Diagnose failures in order: auth/token, peer/sync/version, dataset/permissions, job execution, background service, enclave/attestation.
