# x402 Payments

Bindu can require payment before running an agent task by adding `execution_cost` to the agent config.

## Single option

```python
"execution_cost": {
    "amount": "0.01",
    "token": "USDC",
    "network": "base-sepolia",
    "pay_to_address": "0xYourWallet"
}
```

## Multiple options

```python
"execution_cost": [
    {"amount": "0.1", "token": "USDC", "network": "base", "pay_to_address": "0x..."},
    {"amount": "0.0001", "token": "ETH", "network": "ethereum", "pay_to_address": "0x..."}
]
```

Bindu normalizes a single dict to a list internally. The first option is used for backward-compatible primary fields; all options can be advertised.

## Flow

1. Caller sends a protected request without payment.
2. Middleware returns 402 with payment requirements.
3. Caller signs payment authorization with wallet and resends with `X-PAYMENT`.
4. Middleware asks facilitator `/verify` whether payment is valid.
5. The A2A endpoint attaches payment context to message metadata.
6. `ManifestWorker` settles first through facilitator `/settle` before invoking the handler.
7. If settlement fails, no handler work runs. If handler fails after settlement, task metadata records orphan-payment risk for operator reconciliation.

## Payment sessions

Payment-session endpoints support browser capture flows:

| Endpoint | Purpose |
|---|---|
| `POST /api/start-payment-session` | Create a session and browser URL. |
| `GET /payment-capture?session_id=...` | Render/capture paywall payment. |
| `GET /api/payment-status/{session_id}` | Poll status and retrieve payment token after completion. |

## Network and facilitator caution

Base/Base Sepolia are the safest defaults. Non-default EVM networks require both a facilitator that supports the network and asset metadata in Bindu settings. Live-chain workflows are production-impacting; prefer fake facilitators and testnets while debugging.

## Development fake facilitator

A local fake facilitator can implement `/supported`, `/verify`, and `/settle` and always return valid/settled responses. This is useful for seeing 402 → paid retry → completed task behavior without wallet or chain side effects. Never use a fake facilitator in production.
