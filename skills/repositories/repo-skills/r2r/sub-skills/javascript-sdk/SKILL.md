---
name: javascript-sdk
description: "Use the R2R JavaScript client for Node/browser auth, uploads,
  retrieval, streaming, and response handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# JavaScript SDK

Use this sub-skill when the user wants to use `r2r-js` from Node or a browser, handle camelCase payloads, or work with streamed responses in JavaScript.

## What it owns

- client construction and auth/token refresh helpers
- Node vs browser file upload and download behavior
- retrieval, documents, graphs, collections, and user calls from JS
- streaming response handling and casing differences

## Start here

```javascript
const { r2rClient } = require("r2r-js");
const client = new r2rClient("http://localhost:7272");
```

## Route out when the work becomes another topic

- Server install/config/Docker: `../server-configuration/SKILL.md`
- Python SDK details: `../python-sdk/SKILL.md`
- Document ingestion semantics: `../ingestion-documents/SKILL.md`
- Search/RAG semantics: `../retrieval-rag/SKILL.md`
- Graph semantics: `../graph-workflows/SKILL.md`

## Bundled assets

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/js_sdk_quickstart.mjs`
