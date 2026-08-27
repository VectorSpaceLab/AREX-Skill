# Tooling and Forge Troubleshooting

## `atomic` CLI not found

**Symptom:** `atomic: command not found`

**Cause:** the package is not installed into the active environment, or the shell is not using that environment.

**Fix:** install the package, rerun `atomic --help`, and verify the active environment before continuing.

## Tool selection is ambiguous

**Symptom:** the agent is unsure which tool to use.

**Cause:** the tool names or descriptions are too similar.

**Fix:** override the tool title and description through `BaseToolConfig`, or use a routing agent only when the user input genuinely determines the tool choice.

## Downloaded tool dependencies are missing

**Symptom:** a Forge tool imported into a user project fails on import or runtime.

**Cause:** the tool package was copied without its declared runtime dependencies.

**Fix:** install the tool package's own requirements and follow its README after download; do not assume Atomic Agents itself provides the tool's dependencies.

## API-key or network failures

**Symptom:** a Forge tool such as search, weather, scrape, or YouTube transcript fails during a live call.

**Cause:** network access, a remote service, or an API key is missing.

**Fix:** verify the tool's README for the exact environment variables or endpoint requirements before treating the tool as broken.

## Tool authoring mistakes

**Symptom:** a custom tool is difficult to route or produces vague schema descriptions.

**Cause:** the input schema docstring, field descriptions, or tool config title/description are too thin.

**Fix:** keep the schema docstring and field descriptions precise, and override tool title/description when the default schema-derived wording is not clear enough.
