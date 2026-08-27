---
name: background-services
description: "Operate syft-bg background notification, approval, auto-approval,
  logs, service lifecycle, and Gmail/PubSub setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# background-services

Use this sub-skill for `syft-bg` CLI/API setup, notify and approve services, auto-approval objects, peer auto-approval, service lifecycle, logs/status/TUI, Gmail token scope, Pub/Sub readiness, and systemd user services.

## Workflow

1. Confirm user is a data owner and already has SyftBox/auth working; otherwise route to [../auth-sync-transport/SKILL.md](../auth-sync-transport/SKILL.md).
2. Initialize config with explicit email, SyftBox root, and token path.
3. Check environment with `syft-bg setup-status` before starting services.
4. For job auto-approval, prefer hash-pinned script policies for named peers.
5. Start only requested services; ask before installing systemd auto-start.

Read [references/cli-reference.md](references/cli-reference.md), [references/configuration.md](references/configuration.md), [references/auto-approval.md](references/auto-approval.md), and [references/troubleshooting.md](references/troubleshooting.md).

Use [scripts/hash_auto_approval_files.py](scripts/hash_auto_approval_files.py) to compute approval hashes and [scripts/render_syft_bg_config.py](scripts/render_syft_bg_config.py) to render a minimal config.
