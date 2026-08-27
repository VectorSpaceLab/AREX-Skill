# Auto-approval policy

Auto-approval checks submitted job files against policy:

1. Every submitted file must match an approved entry.
2. Content-matched files must have a matching SHA256 hash.
3. If peers are listed, submitter email must match.
4. Files listed by name only should be limited to non-secret parameter files when that risk is accepted.

Prefer strict mode and content hashes for executable files. Recompute hashes after every code edit. Do not auto-approve jobs from unknown peers or wildcard domains without explicit user acceptance.
