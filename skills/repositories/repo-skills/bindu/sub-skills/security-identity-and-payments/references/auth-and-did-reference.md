# Authentication and DID Reference

## Bearer token

Enable Hydra auth with:

```bash
AUTH__ENABLED=true
AUTH__PROVIDER=hydra
HYDRA__ADMIN_URL=<hydra-admin-url>
HYDRA__PUBLIC_URL=<hydra-public-url>
```

Callers send:

```http
Authorization: Bearer <access-token>
```

The middleware introspects the opaque token and expects `active: true`, `client_id`/`sub`, scopes such as `agent:read`/`agent:write`, and a non-expired `exp`.

## DID headers

```http
X-DID: <caller-did>
X-DID-Timestamp: <unix-seconds>
X-DID-Signature: <base58-ed25519-signature>
```

For DID clients, the DID must match the OAuth token identity and the signature must verify against the public key in the DID document/client metadata.

## Canonical signing payload

Bindu reconstructs:

```python
{"body": body_string, "did": did, "timestamp": timestamp}
```

Then signs/verifies `json.dumps(payload, sort_keys=True)` using Python's default separators, which include spaces after commas and colons. The body must be the exact bytes/string sent on the wire. Do not sign a parsed dict and then send differently serialized JSON.

Use `scripts/signing_payload_check.py --body-file request.json --did did:... --timestamp 1710000000` to inspect the payload string.

## DID document shape

A Bindu DID document contains `@context`, `id`, `created`, and `authentication` entries with `publicKeyBase58`. The `did:bindu:<author>:<agent_name>:<uuid>` form includes sanitized author/name metadata and a UUID derived from public-key material.

## Failure meanings

| Failure | Meaning |
|---|---|
| `missing_signature_headers` | One or more DID headers absent. |
| `did_mismatch` | Token owner and `X-DID` disagree. |
| `public_key_unavailable` | No public key found for DID. |
| `timestamp_out_of_window` | Replay window exceeded. |
| `malformed_input` | Signature/public key base58 malformed or wrong length. |
| `crypto_mismatch` | Signature does not verify for reconstructed payload. |
