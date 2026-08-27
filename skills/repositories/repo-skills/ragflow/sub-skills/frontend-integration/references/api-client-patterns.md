# API Client Patterns

## Prefix Selection

RAGFlow web endpoint constants use two browser-visible API prefixes:

- `restAPIv1 = '/api/v1'` for newer RESTful APIs.
- `webAPI = '/v1'` for legacy web/API endpoints that still exist under the older prefix.

Use `/api/v1` for new REST-style frontend integration unless the backend route is explicitly a legacy `/v1` route. Do not guess based on resource name alone; verify the backend route family when wiring a new endpoint. Cross-check `backend-api-services` for route registration and prefix ownership.

Common prefix examples:

- Auth/user/team/model/provider/data source/chat channel/system/admin/skills endpoints use `/api/v1`.
- Dataset/document/chunk/search/chat/agent/memory/MCP REST endpoints mostly use `/api/v1`.
- Legacy endpoints still present in web integration include selected document metadata, canvas input elements/log sessions, and dataflow endpoints under `/v1`.

The Vite dev proxy supports both `/api` and `/v1`, so a wrong prefix may appear as a 404/405, a response-code error, or a call landing in the wrong backend process depending on proxy scheme.

## Endpoint Constants

Keep all route strings and dynamic path builders in the central endpoint constant module instead of constructing URLs inside pages. Preferred endpoint entries are either string constants or typed functions for dynamic paths.

Good endpoint checklist:

- Use the right prefix constant for the backend route family.
- Keep path parameters explicit and ordered like the backend route.
- Include query strings only for stable route-level modifiers, not arbitrary form state.
- Reuse existing endpoint keys where the backend route is unchanged; do not create aliases with different names unless compatibility requires it.
- After adding a key, ensure a service actually uses it and a hook/page consumes the service.

## Request Clients

Prefer the Axios client for new work. It is responsible for auth headers, snake_case conversion, tenant parameter injection, global error notifications, and 401 redirect behavior.

Important request details:

- Plain object `data` and `params` are converted to snake_case before sending.
- `FormData` is passed through without key conversion; append the exact backend field names.
- `skipToken` suppresses auth header injection for endpoints that must run unauthenticated.
- Blob downloads must request `responseType: 'blob'` so interceptors return the raw response.
- Do not add custom global response handling in a page; use hook/service-level handling for feature-specific behavior.

Older code may still use the deprecated request helper. When a service depends on deprecated behavior, make the smallest compatible change and prefer migrating only when the call path is covered by focused tests or manual verification.

## Service Layer

Services should bind endpoint keys to HTTP methods and contain small request/response compatibility transforms. They should not contain page state, React hooks, or display logic.

Patterns:

- `registerNextServer` wraps endpoint records and can pass either simple data or native Axios config with `useAxiosNativeConfig=true`.
- Dynamic endpoint functions can be called by passing route IDs as config when the wrapper expects it, or by supplying a native Axios `url` override.
- Use direct `request.get/post/patch/delete` calls when a method needs custom URL construction, response mapping, upload progress, or compatibility transforms.
- Keep legacy-to-REST shape adapters close to the service boundary, such as dataset/document/chunk ID aliases and response field aliases.

Avoid duplicating backend business rules in services. If a transform becomes complex, verify whether it belongs in a shared frontend utility or a backend compatibility response.

## Hook Layer

Hooks turn service functions into UI-facing operations with React Query. Prefer one hook per user action or data requirement.

Query checklist:

- Build query keys from a stable action enum plus every parameter that changes the result.
- Gate route-ID queries with `enabled` when the ID can be absent.
- Use `initialData` or `placeholderData` to keep components simple, but do not hide error states the page needs.
- Use `gcTime: 0` deliberately for pages that should not reuse stale data across navigation.
- Keep debounced search and pagination values in the query key.

Mutation checklist:

- Return response codes/data consistently for the calling page.
- Show user messages only after successful RAGFlow response codes.
- Invalidate every list/detail/query family affected by the mutation.
- Use `exact: false` when invalidating parameterized list keys across all filters/pages.
- Invalidate both list and detail keys when editing an entity that appears in both places.

## Dataset and Parser Config Patterns

Dataset/document frontend integration has compatibility shims because historical UI names and REST names coexist.

ID aliases commonly handled by services:

- Dataset: `dataset_id`, `kb_id`, `knowledge_id`.
- Document: `document_id`, `doc_id`.
- Chunk: `chunk_id`, `id`.

Parser-config normalization before update:

- Known parser fields stay top-level.
- Unknown parser fields merge into `parser_config.ext`.
- Known RAPTOR fields stay under `parser_config.raptor`.
- Unknown RAPTOR fields and normalized `clustering_method`/`tree_builder` merge into `parser_config.raptor.ext`.
- Child-chunk UI fields map to `parser_config.parent_child` when children are enabled.

When a parser form sends a shape the backend rejects, inspect the hook's normalization utility first, then verify the backend data contract with `dataset-ingestion-retrieval`.

## Chat Patterns

Chat hooks typically derive IDs from route params and search params, then use chat service methods for assistants, sessions, messages, feedback, upload, mind map, related questions, and shared chatbot info.

Key patterns:

- List queries include search/pagination in the query key.
- Chat update/patch mutations invalidate both chat list and chat detail.
- Session create/update/delete mutations invalidate session list.
- Manual session fetch is a mutation when it is triggered imperatively by user selection.
- Upload flows use `FormData`, `AbortController`, and progress callbacks.

## Agent Patterns

Agent hooks and pages cover agent list/detail, tags, templates, setting saves, DSL saves, file uploads, debug, logs, versions, sessions, shared inputs, webhook traces, and dataflow cancellation.

Key patterns:

- Agent list filters build explicit request params for page, page size, keywords, canvas category, owners, and tags.
- Agent detail fetch normalizes message UUIDs and ensures expected system globals exist.
- Saving an existing agent calls the update endpoint; creating without an ID calls create.
- Successful saves invalidate list keys and, for existing agents, the detail key for that agent ID.
- Agent canvas persistence must preserve the canonical DSL shape documented in `frontend-architecture.md`.

## Static API-Key and Prefix Audit

This sub-skill includes `scripts/check_web_api_keys.py`, a standalone read-only checker. It scans frontend endpoint constants and service/hook/page API references to find:

- Duplicate endpoint keys in the endpoint constants object.
- Missing endpoint keys referenced as `api.someKey` outside the constants file.
- Unused endpoint keys that may be stale.
- Prefix summary for `/api/v1` versus `/v1` endpoint definitions.
- Suspicious string literals that contain both prefixes or malformed duplicate prefix fragments.

Example commands from this skill directory:

- `python scripts/check_web_api_keys.py --root <ragflow-checkout>`
- `python scripts/check_web_api_keys.py --web-src <ragflow-checkout>/web/src --json`

The checker is intentionally static and conservative. Treat findings as review prompts, not automatic proof that a route is wrong.
