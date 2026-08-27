# Bindu Security Stack

| Layer | Proves | Primary material | Typical failure |
|---|---|---|---|
| mTLS | The socket is mutually authenticated and encrypted. | step-ca X.509 cert/key and CA bundle. | TLS handshake failure or bootstrap/renewal error. |
| Hydra OAuth2 | The caller is authorized now. | `Authorization: Bearer <token>` introspected by Hydra admin. | 401 invalid/missing/inactive token or insufficient scope. |
| DID signature | The DID signed the exact HTTP body. | `X-DID`, `X-DID-Timestamp`, `X-DID-Signature`, public key in DID metadata/doc. | Missing headers, did mismatch, public key unavailable, invalid signature. |
| Private allowlist | The authenticated DID may see private skills. | `private_skills` and `allowed_dids`. | `/agent/private.json` 401/403/404. |
| x402 | The paid request has valid payment authorization and settlement can occur. | `execution_cost`, `X-PAYMENT`, facilitator verify/settle. | 402, replay, payment-failed, payment-orphaned. |

Production posture normally enables Hydra and, when available, mTLS. Paid agents add x402 configuration. Private catalogs require both auth and allowlists.
