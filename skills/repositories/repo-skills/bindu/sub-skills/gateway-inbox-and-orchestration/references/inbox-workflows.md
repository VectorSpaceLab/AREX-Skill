# Inbox Workflows

Bindu Inbox is an operator console for A2A traffic.

## Processes and ports

| Port | Process |
|---|---|
| `3775` | Vite UI |
| `3787` | Hono API |
| auto | Personal agent |
| `5773`, `5776` | Optional joke/poet demo peers |
| `3774` or auto | Gateway |

## Startup

```bash
cd inbox
npm install
npm run dev
```

A missing `GATEWAY_API_KEY` warning only blocks multi-agent Gateway compose, not basic direct peer messaging.

## Personal agent

Create a persona in the UI, then click Start. The spawner chooses a free port, renders a Python Bindu agent, writes an environment file, starts it, waits for health, captures the DID, and registers it as `me`. OpenRouter/Hydra settings are needed for the full signed demo path.

## Contacts and compose

Add peers by URL. Inbox fetches the agent card, records DID/skills, and uses direct A2A sends for one peer or Gateway planning for multi-peer compose. Webhooks thread replies back into the SQLite event store.
