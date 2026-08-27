# Private Skills and mTLS

## Private skill catalog

Public skill discovery uses `/.well-known/agent.json` and `/agent/skills`. Private skills are configured separately:

```python
config = {
    "skills": ["skills/public-status"],
    "private_skills": ["skills/cbam-line-classify"],
    "allowed_dids": ["did:bindu:partner:agent:abc123"],
}
```

The private route `/agent/private.json` is registered only when the manifest declares a private surface. It returns public plus private skills only after auth and allowlist checks.

| Result | Meaning |
|---|---|
| 401 | No authenticated caller DID reached the handler. |
| 403 | Caller DID is authenticated but not in `allowed_dids`. |
| 404 | No private surface is configured or route is absent. |

Private skills are access-controlled catalog entries, not encrypted-at-rest secrets.

## mTLS concepts

`MTLSAgentExtension` bootstraps cert material from step-ca using an OIDC token provider, stores cert/key/CA bundle, and renews before expiry.

Important settings commonly include:

```bash
MTLS__ENABLED=true
MTLS__MODE=hybrid
MTLS__REQUIRE_CLIENT_CERT=true
MTLS__CA_URL=<step-ca-api-url>
MTLS__CA_ROOT_URL=<step-ca-root-bundle-url>
```

Lifecycle:

1. Fetch CA bundle if missing.
2. Reuse a valid cert when not near renewal.
3. Otherwise generate a keypair/CSR and ask step-ca to sign it using Hydra/OIDC identity.
4. Build HTTP/gRPC server/client TLS material from the live store.
5. Renewal loop periodically reissues when the cert approaches expiry.

mTLS depends on step-ca health, correct OIDC token provider wiring, and peer trust in the CA bundle. Treat cert/key paths and OIDC tokens as secrets.
