---
name: hivemind
description: "Routes Hivemind workflows for decentralized DHTs, collaborative
  training, and remote experts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Hivemind

Use this skill for the public `hivemind` package and its three main user-facing workflows:

- DHT peer setup and record storage
- collaborative averaging and peer training
- hosted experts and remote mixture-of-experts routing

## Install first

Preferred community install:

```bash
python -m pip install hivemind
```

If you are already inside a local checkout and want an editable install instead:

```bash
python -m pip install -e . --no-build-isolation
```

Minimum runtime prerequisites:

- Python 3.9 or newer
- PyTorch 1.9 or newer
- the package dependencies resolved by the installer

Optional extras are only needed for specific workflows:

- `bitsandbytes` for the optional blockwise compression path
- the ALBERT example extras for the collaborative-training tutorial

## Quick preflight

Run the bundled helper after installation:

```bash
python scripts/check_install.py
```

Add `--check-cuda` if you want to verify the host's CUDA path, and `--check-albert` only when you intend to use the optional ALBERT tutorial stack.

## Route map

| If the task is about... | Read this route |
| --- | --- |
| starting or joining a DHT, storing or fetching records, bootstrap peers, relay settings, or `hivemind-dht` | [`sub-skills/dht/SKILL.md`](sub-skills/dht/SKILL.md) |
| averaging tensors, wrapping a PyTorch optimizer, progress tracking, compression choices, or the ALBERT collaborative-training recipe | [`sub-skills/collaborative-training/SKILL.md`](sub-skills/collaborative-training/SKILL.md) |
| hosting experts, remote expert clients, custom expert registration, MoE routing, or `hivemind-server` | [`sub-skills/moe/SKILL.md`](sub-skills/moe/SKILL.md) |

## What this skill does not cover

- Benchmarks and throughput experiments are intentionally excluded from the runtime routes.
- Repo-maintenance workflows live elsewhere and are not part of this operating graph.

## Read these shared references when needed

- [`references/repo-provenance.md`](references/repo-provenance.md) when you need to check whether this skill matches the current checkout.
- [`references/troubleshooting.md`](references/troubleshooting.md) when package-wide install, import, or CLI issues appear.
- [`scripts/check_install.py`](scripts/check_install.py) when you want a fast import and CLI smoke check before deeper work.

## Core package facts

- `hivemind.DHT` coordinates peers through a background DHT process.
- `hivemind.Optimizer` and `hivemind.DecentralizedAverager` are the main collaborative-training entry points.
- `hivemind.moe.Server`, `RemoteExpert`, and `RemoteMixtureOfExperts` are the main MoE serving and client APIs.
- `hivemind-dht` and `hivemind-server` are the installable console commands for the two networking-heavy workflows.
- On CUDA-capable hosts, some server and training paths may prefer GPU defaults unless you override them.

## Freshness check

Read `references/repo-provenance.md` before reusing this skill on a different checkout.
If the commit, dirty state, or installed package version has changed, prefer a refreshed skill over this one.
