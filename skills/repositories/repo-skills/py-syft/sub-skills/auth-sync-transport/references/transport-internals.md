# Transport internals

SyftBox is a local folder synchronized through Google Drive or a mock Drive backend. Peer requests create per-peer inbox/outbox state; DO approval is required before datasets, jobs, or results flow.

Useful facts:

- Use `client.syftbox_folder` instead of guessing paths.
- `client.peers` may auto-sync when `PRE_SYNC` is enabled; set `PRE_SYNC=false` for deterministic debugging and call `sync()`/`load_peers()` explicitly.
- RDS wraps the same sync engine and reacts to `peer_approved`/`peers_loaded` to create job folders and share `users="any"` datasets with approved peers.
- Checkpoints and rolling state prevent unbounded event replay; corrupt caches should be handled with careful resync before destructive cleanup.

Cleanup APIs can delete local and remote state. Ask before using `delete_syftbox` or cleanup commands.
