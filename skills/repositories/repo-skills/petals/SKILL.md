---
name: petals
description: "Use Petals for distributed large-language-model inference, prompt
  tuning, server swarms, block-level internals, benchmarks, and package
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Petals Repo Skill

Use this skill when a task involves Petals, the Python package for collaborative distributed inference and prompt tuning of large language models whose transformer blocks are hosted by remote peers.

This skill is self-contained. Do not rely on a repository checkout being present unless the user explicitly says they are maintaining one; use the bundled references and scripts below for ordinary package workflows.

## Start here

1. For install, import, dependency, cache, model-access, and backend readiness, read [references/installation-and-environment.md](references/installation-and-environment.md).
2. Run the safe root checker when you need a no-network local sanity check:

   ```bash
   python scripts/check_petals_environment.py --pretty
   ```

   A passing checker means local imports, API discovery, and CLI parser checks worked. It does not prove public swarm health, model access, GPU serving performance, or adapter execution.
3. Route the user request to the nearest sub-skill below.
4. For cross-cutting failures, read [references/troubleshooting.md](references/troubleshooting.md).
5. Before refreshing this skill against a newer Petals release, read [references/repo-provenance.md](references/repo-provenance.md).

## Sub-skill routing

| User intent | Read this |
| --- | --- |
| Write client code for distributed generation, sequence classification, public/private swarm clients, `AutoDistributedModel*`, `.generate()`, `inference_session`, routing or retry options | [sub-skills/client-inference/SKILL.md](sub-skills/client-inference/SKILL.md) |
| Host model blocks, start a server, bootstrap a private DHT, construct `python -m petals.cli.run_server` / `run_dht` commands, reason about ports, identities, cache, device, dtype, quantization, adapters, or reachability | [sub-skills/server-swarms/SKILL.md](sub-skills/server-swarms/SKILL.md) |
| Adapt a distributed model with `tuning_mode="ptune"` or `"deep_ptune"`, train prompt embeddings/classifier heads, plan causal-LM or classification prompt tuning, or troubleshoot PEFT adapter safety | [sub-skills/prompt-tuning/SKILL.md](sub-skills/prompt-tuning/SKILL.md) |
| Work with `RemoteSequential`, block slices, hidden-state tensors, `load_pretrained_block`, `QuantType`, tensor parallel conversion, speculative Llama internals, dtype resolution, or block-level errors | [sub-skills/distributed-blocks/SKILL.md](sub-skills/distributed-blocks/SKILL.md) |
| Build benchmark command templates, plan tiny smoke checks, select focused native maintainer checks, or interpret benchmark/CI health signals | [sub-skills/benchmarks-maintenance/SKILL.md](sub-skills/benchmarks-maintenance/SKILL.md) |

## Core operating model

- Petals model classes are Transformers-compatible wrappers. Embeddings and heads live on the client; transformer blocks are discovered through a Hivemind DHT and executed by remote Petals servers.
- The default public swarm is external: availability, hosted block coverage, peer latency, and gated model access can change independently of local package health.
- Private swarms require consistent `initial_peers`, `dht_prefix`, model identifier, and block ranges across clients and servers.
- Generation needs a remote attention-cache budget. Without an active session, pass exactly one of `max_new_tokens` or `max_length`; for interactive continuation, explicitly create and reuse `inference_session(max_length=...)`.
- Prompt tuning trains local prompt embeddings and, for classification models, local heads. The client does not update remote transformer blocks hosted by servers.
- Server-side quantization and adapters are optional backend features. Verify the actual torch/CUDA/ROCm/MPS/bitsandbytes stack before claiming they work.

## Install and minimal import

```bash
python -m pip install petals
python - <<'PY'
import petals
from petals import AutoDistributedModelForCausalLM
print(petals.__version__)
PY
```

For a checkout maintained by the user, use that checkout's package metadata to choose the Python version and dependencies, then run the same import check from outside the checkout directory. Do not treat import success as proof that a public swarm, gated model, GPU serving, or adapter loading is available.
