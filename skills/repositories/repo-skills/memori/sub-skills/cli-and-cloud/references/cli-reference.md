# Memori CLI Reference

## Command table

`python -m memori` loads `.env` from the current directory and prints a command
menu when no subcommand is supplied.

| Command | Purpose | Notes |
| --- | --- | --- |
| `python -m memori` | Show the command table | Safe help-style path |
| `python -m memori quota` | Check quota | Requires cloud access |
| `python -m memori sign-up <email>` | Request an API key | Network-bound |
| `python -m memori setup` | Print suggested setup steps | Safe until it reaches networked steps |
| `python -m memori provision` | Provision a BYODB database | Usually routed to BYODB guidance |
| `python -m memori cockroachdb cluster start` | Manage CockroachDB clusters | External service interaction |
| `python -m memori cockroachdb cluster claim` | Claim a CockroachDB cluster | External service interaction |
| `python -m memori cockroachdb cluster delete` | Delete a CockroachDB cluster | Destructive; never suggest as a default action |

## Startup behavior

- The CLI reads `.env` from the current working directory before it checks the
  command name.
- Existing environment variables are not overwritten by `.env` entries.
- The command menu is the safest way to confirm that the installed package is
  being resolved from the intended environment.

## Cloud mode behavior

When `Memori()` is created without a connection factory, the package enters
cloud mode and requires `MEMORI_API_KEY`. A BYODB connection factory switches
Memori into local storage mode instead.

## Practical use

- Use this CLI when the user wants a quick health check, quota lookup, API-key
  setup, or a help table.
- Use the root install smoke if the task is only about whether the package is
  installed correctly.
