# Security, Identity, and Payments Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| 401 missing auth | No bearer token or auth disabled/misconfigured. | Send `Authorization: Bearer ...`; check `AUTH__ENABLED` and Hydra URLs. |
| 401 inactive token | Expired/revoked/wrong-Hydra token. | Mint a fresh token from the same Hydra public URL the agent trusts. |
| 403 insufficient scope | Token lacks method scope. | Request `agent:read`/`agent:write` as needed. |
| `did_mismatch` | `X-DID` differs from token client id. | Use a token minted for the same DID that signs the body. |
| `public_key_unavailable` | Hydra/DID metadata has no public key. | Register/update DID document/public key. |
| `crypto_mismatch` | Signed bytes differ from sent bytes or wrong key. | Serialize once, sign exact bytes, match Python sorted JSON payload. |
| Timestamp out of window | Replay guard rejected old/future timestamp. | Use current Unix seconds and account for clock skew. |
| `/agent/private.json` 401 | Auth did not identify caller. | Fix bearer/DID auth first. |
| `/agent/private.json` 403 | DID not allowlisted. | Add the caller DID to `allowed_dids` and restart/reload. |
| `/agent/private.json` 404 | No private surface. | Configure `private_skills` or `allowed_dids`. |
| 402 payment required | No valid `X-PAYMENT`. | Complete paywall/payment and retry with the token/header. |
| Payment verify fails | Bad payload, wrong network/asset, facilitator unsupported, insufficient funds. | Compare 402 requirements with wallet authorization and facilitator `/supported`. |
| Settlement fails before work | Facilitator/chain rejected settle. | No handler cost should occur; inspect payment failure metadata. |
| Payment orphaned | Settle succeeded but handler failed. | Reconcile/refund manually using recorded settlement metadata. |
| mTLS bootstrap failed | step-ca/OIDC unavailable or misconfigured. | Check CA URL, root URL, OIDC token provider, Hydra registration, and network reachability. |
| TLS handshake fails | Missing client cert, wrong CA, SAN/DID mismatch. | Verify peer cert chain and server/client mTLS mode. |
