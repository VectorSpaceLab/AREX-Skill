# Migration Tools

MemMachine includes repo-maintained tooling for migrating conversation exports,
including ChatGPT/OpenAI-style exports and LoCoMo-style data. Treat migration as
a two-phase workflow: local parsing/probing first, then live upload only after
approval.

## Two-phase Migration Plan

### Phase 1: Local-only probe

```bash
python scripts/chatgpt_export_probe.py path/to/export.json
```

The probe summarizes JSON shape, likely conversations/messages, and schema
issues without contacting a server or printing full private conversation text.

### Phase 2: Live upload

Only after the user confirms endpoint, API key, org/project, metadata mapping,
and write permission:

```bash
# Example shape; use the installed migration command/module for the user's version.
python -m tools.chatgpt2memmachine.parsers.cli \
  --input path/to/export.json \
  --base-url "$MEMORY_BACKEND_URL" \
  --api-key "$MEMMACHINE_API_KEY" \
  --org-id "my-org" --project-id "my-project"
```

If the installed package does not expose the migration module, use the migration
source/tooling from the user's checkout or translate the local parse result into
SDK `memory.add(...)` calls.

## Metadata Mapping

Recommended metadata for imported conversations:

| Field | Purpose |
| --- | --- |
| `source` | e.g. `chatgpt_export`, `openai_export`, `locomo`. |
| `conversation_id` | Stable source conversation/thread identifier. |
| `message_index` | Original order within conversation. |
| `role` or `source_role` | User/assistant/system role. |
| `import_batch` | Identifier for retry/dedup bookkeeping. |
| `timestamp` | Source timestamp when available. |
| `user_id` | Target MemMachine user/profile isolation. |

Do not store API keys, raw account identifiers, or secrets as memory metadata.

## Deduplication And Batching

- Probe counts before upload.
- Upload in small batches so failures can resume.
- Keep a batch log with source IDs and returned MemMachine IDs.
- If the same export is imported twice, use source conversation/message IDs to
  detect duplicates before adding again.
- Rate-limit provider-backed semantic extraction by using server configuration
  and retry behavior, not by blindly re-sending large batches.

## Validation After Upload

1. Run a count/list query for the import batch metadata.
2. Search for two or three known non-sensitive facts.
3. Verify user/session isolation by searching from the target metadata context.
4. Inspect failures/skips without exposing full conversation content.
5. If semantic memory is enabled, allow ingestion latency before judging
   profile/semantic results.

## Unsafe Or Expensive Migration Sources

- Huge exports may require streaming or chunking.
- Exports can contain private data; never paste full contents into prompts.
- Provider-backed semantic ingestion can incur model cost.
- Delete/rollback operations are destructive; prefer tagging an import batch so
  the user can review before deletion.
