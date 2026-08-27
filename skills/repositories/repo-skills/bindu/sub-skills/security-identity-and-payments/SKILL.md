---
name: security-identity-and-payments
description: "Operate Bindu security, identity, private catalog, mTLS, and x402
  payment workflows without re-reading repository sources."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Security, Identity, and Payments

Use this sub-skill when a task involves Hydra OAuth2, DID keys/documents/signatures, request signing, private skill catalogs, mTLS certificates, x402 payment gating, payment sessions, settlement metadata, or auth/payment troubleshooting.

## Route elsewhere

- Python agent authoring, handler/config basics, A2A task bodies → `../agent-authoring-and-a2a/`.
- Gateway or Inbox as a caller using DID-signed peer auth → `../gateway-inbox-and-orchestration/`.
- gRPC SDK registration details → `../grpc-and-language-sdks/`.
- Deployment, storage, process supervision, or cloud rollout → `../deployment-runtime-and-operations/`.

## References and helper

- `references/security-stack.md` — separate mTLS, Hydra, DID signatures, private allowlists, and x402.
- `references/auth-and-did-reference.md` — bearer token, DID headers, canonical payload, DID doc, resolver, and failure reasons.
- `references/x402-payments.md` — `execution_cost`, `X-PAYMENT`, payment sessions, verify/settle, fake facilitator, live-chain cautions.
- `references/private-skills-and-mtls.md` — `/agent/private.json`, allowlist outcomes, step-ca bootstrap and renewal.
- `references/troubleshooting.md` — 401/403/404, token, DID, x402, and mTLS failures.
- `scripts/signing_payload_check.py` — reproduce Bindu's Python-style signing payload without private keys.

## Operating rules

1. Keep layers separate: bearer token authorizes; DID signature proves exact body origin; mTLS authenticates transport; x402 proves payment; private allowlists gate private catalog visibility.
2. Never request or print tokens, client secrets, DID seeds, wallet keys, TLS keys, or payment payload secrets. Use placeholders and non-secret status evidence.
3. For `crypto_mismatch`, first compare signed body bytes with sent body bytes, then check Python-compatible JSON serialization and timestamp freshness.
4. For `/agent/private.json`, distinguish 401 unauthenticated, 403 authenticated but not allowlisted, and 404 no private surface configured.
5. Treat Hydra, step-ca, facilitators, chains, and wallets as live external services. Use local/mock/testnet paths unless the user explicitly requests production effects.
