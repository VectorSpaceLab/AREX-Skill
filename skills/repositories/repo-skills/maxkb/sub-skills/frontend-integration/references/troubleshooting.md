# Troubleshooting

## Common UI issues
- Wrong base path or proxy target: check `ui/vite.config.ts` and the matching env file.
- Build output missing in Django: rebuild the frontend and rerun static collection.
- Admin/chat pages 404: confirm the backend prefixes and the UI route base path agree.
- Workflow canvas mismatch: check that the backend node family and UI node component names still line up.
- Type-check or lint failures: fix the source issue rather than editing generated build output.
- Locale/theme regressions: confirm the shared UI bootstrap and stored locale choice still match the app shell.

## Safe response pattern
- Identify whether the issue is build-time, route-time, or runtime.
- Name the exact prefix or route module involved.
- State whether Node dependencies were actually available.

## Do not do
- Do not claim the SPA is healthy unless the build or route contract was verified.
- Do not hard-code a proxy target if the env file already controls it.
