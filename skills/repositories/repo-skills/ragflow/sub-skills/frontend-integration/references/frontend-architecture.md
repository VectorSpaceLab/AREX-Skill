# RAGFlow Frontend Architecture

## Runtime Shape

RAGFlow's web UI is a Vite React 18 TypeScript application. The app shell provides shared browser-side infrastructure before rendering the router:

- React Router v7 renders lazy-loaded routes with a fallback overlay.
- TanStack React Query owns server-state caches and mutations.
- Theme, tooltip, toast, i18n, responsive breakpoints, and dayjs plugins are initialized at the app boundary.
- Zustand is used for local agent-canvas graph state; React Query should stay responsible for server state.

The frontend integration stack is intentionally layered:

1. Endpoint constants define URLs and dynamic path builders.
2. Request clients attach auth, convert outgoing keys, add tenant parameters, and normalize error handling.
3. Services bind endpoint constants to HTTP methods and small compatibility transforms.
4. Hooks expose typed UI operations through `useQuery` and `useMutation`.
5. Pages/components call hooks and manage route parameters, forms, tables, canvas state, and local UI state.

When adding or debugging a feature, trace this full stack in order instead of patching only the page.

## App and Routing

The route table is built from a `Routes` enum and a lazy route config. Keep enum entries, route config paths, page imports, and navigation helpers in sync. Important route groups include:

- Dataset list and nested dataset pages: datasets, dataset files, retrieval testing, knowledge graph, overview/logs, and configuration.
- Chat pages: chat list, chat detail, share, and widget views.
- Agent pages: agent editor, agent explore, agent share, agent logs, dataflow result, and pipeline/dataflow screens.
- User settings and admin pages: settings, model/team/API/MCP/data-source/chat-channel, and admin sections.

The router uses a `basename` from `VITE_BASE_URL` when present. If a route works in local dev but fails under a sub-path deployment, check Vite `base`, router basename, generated asset URLs, and reverse-proxy routing together.

## React Query Defaults

The app-level `QueryClient` disables refetch-on-window-focus and retries queries twice by default. Hooks often override cache behavior with `gcTime: 0`, `enabled`, `refetchInterval`, or `placeholderData`.

Common conventions:

- Query keys are enum-like strings plus parameter objects, for example chat list keys include search text and pagination.
- Mutations invalidate the list/detail keys they change; use `exact: false` when a list key includes parameter objects and every variant must refresh.
- Detail queries are usually gated by route IDs with `enabled: !!id`.
- Polling is local to specific flows, such as document parsing status, and should not be added globally.

Stale UI after a successful mutation usually means the mutation invalidated the wrong key, omitted a detail key, or used a list key without matching the hook's parameterized key shape.

## Request Client Boundary

Newer code should prefer the Axios request client and `registerNextServer`. It performs these browser-side operations:

- Converts outgoing `data` and `params` keys to snake_case unless the payload is `FormData`.
- Adds tenant parameters to applicable non-FormData requests.
- Attaches the authorization header unless `skipToken` is explicitly set.
- Handles HTTP 401 and RAGFlow response code 401 with a single redirect-to-login flow.
- Returns raw blob responses when `responseType: 'blob'` is set.

Some older services still use the deprecated request helper. Preserve existing behavior when touching those call sites, but avoid expanding deprecated patterns for new endpoint work.

## Dataset UI Flow

Dataset pages cover dataset CRUD, document upload, document parsing/reparse, parser configuration, chunk operations, retrieval testing, metadata, graph view, and overview logs. High-value frontend contracts:

- Dataset and document IDs appear under several historical names (`dataset_id`, `kb_id`, `knowledge_id`, `document_id`, `doc_id`). Service compatibility helpers map these before calling REST endpoints.
- REST dataset endpoints generally use `/api/v1/datasets/...`; a few legacy web endpoints still use `/v1`.
- `parser_config` is normalized before dataset/document updates. Known parser fields remain top-level; unknown parser fields move into `ext`; RAPTOR extras move into `raptor.ext`; child-chunk UI fields become `parent_child`.
- Document list polling is driven by running status and invalidates dataset detail as parsing progress changes.
- Retrieval testing builds dataset IDs from the current route unless the form explicitly supplies IDs.

Cross-check `dataset-ingestion-retrieval` for backend ingestion/retrieval behavior whenever a UI parser or retrieval form change affects API semantics.

## Chat UI Flow

Chat integration uses REST-style chat endpoints for chat assistants, sessions, messages, feedback, file upload, TTS, mind maps, related questions, and shared chatbot info.

Typical path:

1. Route/query parameters identify chat ID and session/conversation ID.
2. Chat hooks fetch chat lists/details and session lists/details.
3. Mutations create/update/patch chats and sessions, then invalidate list/detail keys.
4. File upload uses `FormData` and upload-progress callbacks; do not force snake_case conversion on the file payload.
5. Chat utility tests protect message/LaTeX preprocessing used when rendering model output.

If a chat page displays stale data, check whether the mutation invalidates both the list key and the relevant detail/session key.

## Agent Canvas Flow

Agent UI integration spans route wiring, React Flow canvas state, DSL conversion, service calls, debug/test sheets, logs, sessions, shared inputs, file uploads, and webhook/dataflow flows.

The agent DSL has one canonical wire shape:

- `graph` stores React Flow nodes and edges for layout and UI state.
- `components` stores executable topology and component parameters.
- `globals`, `variables`, `path`, `retrieval`, and `history` carry runtime context.

The frontend rebuilds `components` from `graph` on save. The strict DSL bridge treats `graph.nodes` as the canonical import shape; `_layout`-only or components-only payloads fall back to an empty seed. Preserve this contract when adding canvas features, import/export behavior, or tests.

Cross-check backend/API behavior with `backend-api-services` when changing agent routes, logs, component debug, webhook, or task cancellation endpoints.

## Vite, Proxy, and Commands

Development runs through Vite. The dev server defaults to port `9222` unless `PORT` overrides it. Proxy behavior is selected by `API_PROXY_SCHEME` with Python, hybrid, and Go-oriented routing schemes for `/api`, `/api/v1/admin`, and `/v1`.

Useful commands from `web/`:

- `npm install` installs frontend dependencies.
- `npm run dev` starts the Vite dev server.
- `npm run build` builds production assets.
- `npm run lint` runs ESLint on `src`.
- `npm run type-check` runs `tsc --noEmit`.
- `npm run test` runs Jest with coverage.

Focused test examples:

- `npm run test -- src/hooks/tests/parser-config-utils.test.ts --runInBand`
- `npm run test -- src/pages/agent/utils/tests/dsl-bridge.test.ts --runInBand`
- `npm run test -- src/utils/tests/chat.test.ts --runInBand`
