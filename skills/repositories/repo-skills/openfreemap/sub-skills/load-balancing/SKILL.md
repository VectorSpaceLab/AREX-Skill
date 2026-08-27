---
name: load-balancing
description: "Routes OpenFreeMap round-robin DNS, certificate publishing, and
  host-health check workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Load balancing

Use this route when the task is about keeping OpenFreeMap's round-robin hosts healthy or updating their DNS records.

This route assumes the host bootstrap and HTTP-host setup are already in place. It focuses on the check/fix loop and the one-time certificate publishing path.

## Typical triggers

- "check the round-robin hosts"
- "fix Cloudflare records"
- "publish the round-robin cert"
- "run the load balancer"
- "set up the DNS writer hook"
- "why are no hosts healthy?"

## What this route covers

- The `check` and `fix` load-balancer commands.
- Cloudflare zone lookup and record replacement.
- Host-health probing through the round-robin domain.
- Telegram alerts for load-balancer events.
- The `rclone_write.sh` deploy hook used by the certificate writer path.

## What this route does not cover

- Host bootstrap and package installation.
- HTTP-host asset sync and nginx refresh.
- Tile generation and upload.

Route those tasks to:

- `../deployment/SKILL.md`
- `../http-host/SKILL.md`
- `../tile-generation/SKILL.md`

## Read next

- `references/api-reference.md` — verified helper signatures and command families.
- `references/workflows.md` — the one-time setup path and the recurring check/fix loop.
- `references/troubleshooting.md` — host list, Cloudflare, Telegram, and deploy-hook failures.
- `scripts/rclone_write.sh` — bundled certificate publish hook.

## Good first checks

1. Confirm the round-robin domain exists in `.env`.
2. Confirm the host list is populated.
3. Confirm the Cloudflare and rclone config files exist.
4. Confirm whether the user wants a one-time setup or the recurring cron check.

## Runtime facts to remember

- `check` only reports health; `fix` can rewrite DNS records.
- `fix` falls back to the full host list if it sees no healthy hosts at all.
- The host checks use `pycurl` with custom host resolution.
- The first few minutes after a deploy use a relaxed mode while the deployed version is still settling.

## When to escalate

If the user actually wants to change the HTTP-host runtime or regenerate tiles, hand the task back to the sibling sub-skill instead of stretching the load-balancing route.
