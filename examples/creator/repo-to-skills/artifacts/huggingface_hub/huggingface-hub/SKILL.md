---
name: huggingface-hub
description: "Use the Hugging Face Hub Python client and hf CLI for repository and artifact management, downloads and caching, hosted inference, cloud compute, model integration, and safe automation."
license: Apache-2.0
disable-model-invocation: true
metadata:
  disco-role: operating
---

# Hugging Face Hub

Use this repo skill for `huggingface_hub` 1.29.0 workflows: the official Python
client and `hf` CLI for interacting with model, dataset, Space, and storage
resources on the Hugging Face Hub. This is a router, not an exhaustive API
manual. Resolve the user's dominant operation and load only the smallest
focused route.

## Install and establish the version

For an application, install the base package:

```bash
python -m pip install huggingface_hub
python -c "import huggingface_hub; print(huggingface_hub.__version__)"
```

Add only the optional surface required by the task:

- `huggingface_hub[torch]` for torch/safetensors model serialization and mixins.
- `huggingface_hub[oauth]` for OAuth server helpers.
- `huggingface_hub[mcp]` for MCP client/agent connections.
- `huggingface_hub[gradio]` for Gradio-based webhook server integrations.
- `huggingface_hub[hf_xet]` when explicitly controlling the Xet transfer extra.

The base package includes the `hf` entry point. Before relying on a detailed
flag, run `hf --help`, `hf version`, and the relevant command's `--help`; CLI
surfaces are version-sensitive. Keep `HF_TOKEN` or an existing login in a
secret store and never put a token in source, output, URLs, or reports.

## Route the request

| User intent | Load this route |
|---|---|
| Create/search/manage repos, upload or commit files, branches/tags, cards, collections, discussions, PRs, or Hub webhook resources | [hub-operations](sub-skills/hub-operations/SKILL.md) |
| Download files/snapshots, use cache/offline mode, Xet, `HfFileSystem`, `hf://`, buckets, copy, or sync | [downloads-and-storage](sub-skills/downloads-and-storage/SKILL.md) |
| Call hosted models, select providers, stream/async chat, use tools or JSON schema, MCP, or manage Inference Endpoints | [inference-and-endpoints](sub-skills/inference-and-endpoints/SKILL.md) |
| Choose `hf` commands, parse output, automate shell flows, use extensions, or generate/update CLI skills | [cli-and-automation](sub-skills/cli-and-automation/SKILL.md) |
| Run Jobs/Sandboxes, configure Spaces, build OAuth/webhook servers, integrate models/cards, serialize DDUF or torch checkpoints, or use TensorBoard | [hosted-compute-and-integrations](sub-skills/hosted-compute-and-integrations/SKILL.md) |

When a workflow crosses routes, keep one owner per operation: use the CLI route
for command syntax and output, the Hub route for remote repository mutations,
the storage route for read/cache behavior, and the hosted-compute route for
paid or stateful cloud resources.

## Safety contract

1. Identify the endpoint, namespace/repo ID, singular Python `repo_type`
   (`model`, `dataset`, or `space`), revision, and credential source.
2. Classify each step as local/read-only, remote mutation, credentialed, or
   destructive. Use placeholders only for examples, never as authorization.
3. Inspect resources and current revisions before changing them. Pin a commit
   or branch when reproducibility or optimistic concurrency matters.
4. Preview downloads, copies, sync plans, uploads, visibility changes, and
   deletes. Confirm exact targets immediately before destructive actions.
5. Keep remote, paid, networked, credentialed, and long-running operations out
   of local smoke checks. Use mocked transports and temporary fixtures first.
6. Verify the result by reading the resulting resource, revision, cache path,
   output shape, or terminal cloud status; do not infer success from a request
   being accepted.

Read [cross-cutting troubleshooting](references/troubleshooting.md) when
access, version, network, optional dependencies, cache state, or ambiguous
mutation outcomes are involved. Read [repository provenance](references/repo-provenance.md)
before deciding whether this skill matches a checkout or needs refreshing.

## Minimal local check

```bash
python -c "import huggingface_hub; from huggingface_hub import HfApi, InferenceClient; print(huggingface_hub.__version__)"
hf --help
```

Do not run a command that creates, deletes, uploads, launches compute, changes
secrets, or incurs inference cost until the target and authorization are
explicit. The generated references contain safe mocked and local-only checks;
they are not a substitute for permission to contact or mutate the Hub.
