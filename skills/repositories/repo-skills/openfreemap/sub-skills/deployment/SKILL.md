---
name: deployment
description: "Routes OpenFreeMap clean-server bootstrap and deployment tasks
  driven by init-server.py and ssh_lib."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Deployment

Use this route when a task is about starting from a clean Ubuntu server or VM and turning it into an OpenFreeMap host.

This sub-skill assumes the root repo packages are already installed for inspection and that the task is about deployment orchestration rather than the runtime details of a specific host role.

## Typical triggers

- "set up OpenFreeMap on a new server"
- "bootstrap a host"
- "run init-server.py"
- "prepare the remote venv"
- "install the OpenFreeMap host stack"
- "configure a clean Ubuntu VM"

## What this route covers

- SSH connection setup and optional password handling.
- Remote user creation, sudo configuration, and base package installation.
- Deploying the HTTP host, tile-generation host, or load-balancer host.
- The quick verification path that starts with `SKIP_PLANET=true`.
- The one-time round-robin certificate writer setup.

## What this route does not cover

- Day-to-day HTTP-host sync, mounting, or nginx refresh details.
- Tile generation internals such as Btrfs extraction or upload promotion.
- Ongoing DNS health checks and record fixes.

Route those to the sibling sub-skills:

- `../http-host/SKILL.md`
- `../tile-generation/SKILL.md`
- `../load-balancing/SKILL.md`

## Read next

- `references/workflows.md` — the deployment command families and their intended order.
- `references/api-reference.md` — the helper signatures behind the deployment CLI.
- `references/troubleshooting.md` — SSH, config, sudo, and bootstrap failures.
- `../../references/configuration.md` — shared `.env` and `config.json` facts.

## Good first checks

1. Confirm the target is a clean Ubuntu server or VM with sudo.
2. Confirm the repo has a usable `.env` or `.env.<ENV>` file.
3. Confirm the deployment goal: HTTP host only, tile generation, load balancing, or all three.
4. Read the workflow reference before executing anything that changes a remote machine.

## When to escalate

Stop and hand the task to a different route when the user actually wants one of these runtime details:

- how a host downloads and mounts btrfs images
- how a host generates and publishes tiles
- how a host updates round-robin DNS records
- how the public tile styles are used in an app or website

## Practical reminder

OpenFreeMap is designed for dedicated machines, not for casual local installs. If the request sounds like a bootstrap of a personal dev machine, call out the deployment assumptions before proceeding.
