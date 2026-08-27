---
name: nesa
description: "Use the Nesa repository for Equivariant Encryption demos,
  encrypted AI web UI setup, backend protocol inspection, and Hack EE contest
  context."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# Nesa Repository Skill

Use this skill when a task mentions **Nesa**, **Equivariant Encryption (EE)**,
encrypted token IDs, the encrypted DistilBERT sentiment demo, the Nesa encrypted
AI web UI, the Nesa backend streaming protocol, or the Hack EE contest.

Nesa's public repo is a demo/application repository, not a normal installable
Python package. Treat its code as four user-facing surfaces:

1. a minimal encrypted DistilBERT sentiment demo,
2. a modified text-generation web UI for encrypted AI demos,
3. Nesa-specific backend protocol/model-registry helpers, and
4. contest/security material about recovering encrypted token mappings.

## First decision

Before giving commands, ask what the user is trying to do:

- **Run a small local encrypted sentiment example:** read
  [encrypted-distilbert](sub-skills/encrypted-distilbert/SKILL.md).
- **Install, launch, or debug the local encrypted AI web UI:** read
  [web-ui-runtime](sub-skills/web-ui-runtime/SKILL.md).
- **Inspect request/response structs, model registry, prompt construction, or
  remote encrypted LLM streaming:** read
  [backend-protocol](sub-skills/backend-protocol/SKILL.md).
- **Understand Hack EE contest rules, mapping submissions, or attack baselines:**
  read [security-contest](sub-skills/security-contest/SKILL.md).

If the user asks a broad Nesa question, read
[references/runtime-overview.md](references/runtime-overview.md) first, then route
to the closest sub-skill.

## Safety and runtime boundaries

- Do **not** promise that future agents can decrypt Nesa's encryption. The repo
  contains demos, public contest rules, and baseline attack ideas; it does not
  include a guaranteed break of EE.
- Treat model downloads, web UI launches, and remote Nesa stream calls as
  network/service operations. Get user approval before doing them in an
  interactive session.
- Treat one-click installer scripts as environment-mutating. Prefer explaining
  their choices and running small read-only checks first.
- CPU is enough for the required small DistilBERT and protocol workflows. GPU,
  ROCm, MPS, Intel accelerator, and Nesa remote stream checks are optional and
  should be reported separately.
- Never expose the web UI on a public interface without authentication and an
  explicit user decision.

## Quick environment expectations

For local experiments, a Python 3.9+ or 3.11 environment usually needs:

```bash
python -m pip install torch transformers msgspec pydantic-settings python-dotenv \
  nats-py httpx requests tqdm safetensors pyyaml
```

For web UI work, add the UI/runtime dependencies described in
[web-ui-runtime/references/installation-and-runtime.md](sub-skills/web-ui-runtime/references/installation-and-runtime.md).
Use [scripts/check_nesa_runtime.py](scripts/check_nesa_runtime.py) to print a
read-only dependency and backend summary for the current environment.

## Core facts to preserve

- Equivariant Encryption is demonstrated as tokenization/model transformation:
  client-side text becomes encrypted token IDs, the server sees encrypted tokens,
  and plaintext remains client-side.
- The minimal local demo uses an encrypted DistilBERT sentiment model and
  tokenizer; the web UI supports both encrypted DistilBERT and a remote encrypted
  Llama flow.
- The backend protocol uses `msgspec` structs for messages, sampling params,
  session IDs, and streaming responses.
- The remote LLM flow posts server-sent-event requests to a configured stream
  URL and decodes encrypted output tokens with the local tokenizer.
- Hack EE contest submissions are JSON token mappings shaped like
  `{"tokens":{"12":"an","345":"swer"}}` and are scored per correct or
  incorrect mapping.

## Reference map

- [references/runtime-overview.md](references/runtime-overview.md): high-level
  repo architecture, evidence-derived workflow map, and capability boundaries.
- [references/troubleshooting.md](references/troubleshooting.md): cross-cutting
  install/import, model asset, network, and backend failure triage.
- [references/repo-provenance.md](references/repo-provenance.md): source commit,
  dirty-state summary, and evidence baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json):
  structured router metadata for managed repo-skill import.

## Output discipline for future work

When you create commands, scripts, or analysis from this skill, keep them
self-contained. Do not point users back to this skill's original construction
checkout. If a user has a separate Nesa checkout, ask for its path and treat it
as the current working copy, not as a hidden dependency of this skill.
