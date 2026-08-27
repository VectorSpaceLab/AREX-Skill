---
name: retrieval-client
description: "Guides PageIndexClient workspace persistence, document metadata,
  structure retrieval, page content lookup, and agentic RAG tools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Retrieval Client

Use this sub-skill when the user mentions `PageIndexClient`, workspace directories, document ids, `get_document`, `get_document_structure`, `get_page_content`, cached JSON documents, or agentic vectorless RAG.

Do not use it for initial tree construction unless the user specifically wants `PageIndexClient.index()`:

- classic PDF tree extraction -> `../pdf-indexing/`
- Flash PDF tree extraction -> `../flash-indexing/`
- Markdown tree extraction -> `../markdown-indexing/`

## Required context

Read these shared references as needed:

- `../../references/workflows.md#workspace-retrieval-and-agentic-qa` for workflow recipes.
- `../../references/api-reference.md#retrieval-client-and-low-level-tools` for verified signatures.
- `../../references/data-formats.md#workspace-layout` for workspace JSON structure.
- `../../references/configuration.md#credentials` for model key behavior.
- `../../references/troubleshooting.md#workspace-retrieval` for common retrieval failures.

## Operating flow

1. Create or load a workspace:

   ```python
   from pageindex import PageIndexClient

   client = PageIndexClient(workspace="workspace")
   ```

2. Index only when the user wants to build or refresh a document entry:

   ```python
   doc_id = client.index("document.pdf")
   ```

   `index()` calls the PDF or Markdown tree builders and can require model credentials.

3. Retrieve in the standard order for agent workflows:

   ```python
   print(client.get_document(doc_id))
   print(client.get_document_structure(doc_id))
   print(client.get_page_content(doc_id, "5-7"))
   ```

4. For an offline workspace smoke check, run `python scripts/workspace_smoke.py` from this sub-skill directory.

## Agentic RAG pattern

The repo's agentic demo pattern exposes three tools:

- `get_document()` — confirm document metadata and page or line count.
- `get_document_structure()` — inspect the tree without text fields.
- `get_page_content(pages)` — fetch tight ranges such as `"5-7"` or `"12"`.

Keep agent instructions strict:

- Call metadata first.
- Use structure to decide relevant ranges.
- Fetch only tight ranges; never fetch the entire document by default.
- Answer only from tool outputs.

The OpenAI Agents SDK route needs the optional `openai-agents` dependency plus the user's model credentials. Loading an existing workspace and calling retrieval helpers can be fully offline.

## Common decisions

- If a workspace JSON is corrupt, rebuild it by re-indexing or repair `_meta.json` plus the document JSON file.
- If `get_page_content` errors, validate the page selector syntax before rerunning.
- If a Markdown document is queried, explain that ranges refer to heading line numbers rather than PDF pages.
- If the user wants improved extraction quality before retrieval, route back to the relevant indexing sub-skill.
