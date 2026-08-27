# Troubleshooting

## Purpose

Use this page when a Nexent frontend change breaks build, locale routing, API calls, chat streaming, or runtime proxy behavior.

## Fast triage

1. If the issue is a broken request/response contract, inspect `references/api-contracts.md` first.
2. If the issue is streaming chat, inspect `references/streaming-and-chat.md` first.
3. If the issue is a route, locale, or base-path failure, inspect `references/frontend-architecture.md` first.
4. If the issue looks server-side, route the work to `../backend-services-api/SKILL.md` instead of patching the frontend blindly.

## Common failure modes

| Symptom | Likely cause | What to check next | Recovery step |
| --- | --- | --- | --- |
| `npm run check-all` fails during type-check | A backend payload changed but the frontend type or mapper did not. | `frontend/types/*.ts`, `frontend/services/*.ts`, and `scripts/extract_frontend_api_calls.py --repo-root <repo-root>`. | Update the shared type, then update the service mapper and the consuming UI. |
| `npm run build` succeeds locally but `npm run start` fails in production mode | `server.js` and `next.config.mjs` are out of sync, or the standalone build artifacts are missing. | `frontend/server.js`, `frontend/next.config.mjs`, `frontend/base-path.mjs`. | Rebuild the frontend, keep `output: "standalone"`, and ensure the production start path uses the generated `.next` artifacts. |
| `/zh` or `/en` redirects incorrectly, loops, or 404s | Locale middleware or base-path logic changed without matching the route shell. | `frontend/middleware.ts`, `frontend/app/[locale]/i18n.tsx`, `frontend/base-path.mjs`, `frontend/lib/basePath.ts`. | Keep locale redirect logic and base-path normalization aligned, then clear the browser locale cookie if needed. |
| UI shows the wrong language or missing strings | `common.json` / `custom.json` files are missing keys, or the locale loader cannot fetch them. | `frontend/public/locales/zh/common.json`, `frontend/public/locales/en/common.json`, `frontend/app/[locale]/i18n.tsx`. | Add the missing key to both locales and verify the key is loaded through the locale loader. |
| Chat stream stops updating or shows raw chunk JSON | A new backend chunk type is not mapped in both chat adapters. | `frontend/const/chatConfig.ts`, `frontend/types/chat.ts`, `app/[locale]/chat/streaming/*`, `app/[locale]/newchat/adapter/*`. | Add the new chunk family to the frontend map, then re-run the helper script and the frontend checks. |
| Chat resume duplicates steps, metrics, or sources | `streaming_message`, `unit_index`, or resume skipping logic is not aligned with the persisted backend shape. | `conversationService.getDetail()`, `chatStreamHandler.tsx`, `conversation-thread-list-adapter.tsx`. | Restore the skipped-unit logic and keep the persisted stream snapshot format unchanged. |
| Sub-agent cards collapse into one card or appear in the wrong order | `invocation_id` or `runId` is missing from the SSE metadata. | `remote-chat-model-adapter.ts`, `thread.tsx`. | Propagate `invocation_id` through the stream chunks and keep the grouping metadata stable. |
| Voice input does nothing | STT config is missing or the websocket path is blocked. | `conversationService.stt.*`, `frontend/server.js`, browser microphone permission. | Configure the STT model, allow microphone access, and confirm the websocket proxy is reachable. |
| File upload or preview fails with `413` or a missing attachment | Upload limits, MinIO metadata, or proxy handling are mismatched. | `frontend/services/api.ts`, `conversationService.ts`, `adapter/attachment-adapter.ts`, `services/storageService.ts`, `server.js`. | Check the file limit and the returned `object_name` / `presigned_url` metadata, then retry the upload. |
| Session suddenly expires or the app keeps redirecting to login | Cookie/session handling is inconsistent. | `frontend/lib/auth.ts`, `frontend/services/api.ts`, `frontend/lib/session.ts`. | Let the shared auth helper handle the error, then refresh the session or log in again. |
| A page renders but a repository import or listing action fails | The frontend mapper still expects the older repository payload. | `types/agentRepository.ts`, `types/skillRepository.ts`, `services/agentRepositoryService.ts`, `services/skillRepositoryService.ts`. | Update the mapper and the detail/list types together before touching the UI. |

## Build and runtime checks

- Use `npm run type-check` to isolate pure TypeScript drift.
- Use `npm run lint` to catch hook, import, and React misuse.
- Use `npm run build` to catch production-only config issues.
- Use `npm run check-all` when you want the full frontend gate.

## When to stop and route elsewhere

Stop patching the frontend and hand the task to `../backend-services-api/SKILL.md` when:

- the backend route itself changed,
- the server response shape is still being decided,
- the stream event contract is incompatible with the frontend UI,
- or the failure only exists because the backend service is returning malformed data.

The frontend should adapt to a stable contract, not compensate for an unstable server interface.
