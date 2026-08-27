# Integrations and Extensions Troubleshooting

## Custom language not loading

**Symptoms**
- A file extension is ignored even after adding a TOML entry.
- Logs mention a grammar or TOML validation problem.

**Likely causes**
- The extension collides with a built-in language.
- The grammar name is not shipped by `tree_sitter_language_pack`.
- The entry has no node types.
- The TOML is malformed.

**Recovery**
1. Fix the extension or grammar name.
2. Start with one language and one tiny fixture.
3. Rebuild the graph and inspect the resulting nodes.

## Embeddings not available

**Symptoms**
- Semantic search returns only keyword-like results.
- The embedding workflow reports the provider is unavailable.

**Likely causes**
- The optional embeddings dependency is missing.
- The provider environment variables are missing.
- The provider/model combination does not match existing stored embeddings.

**Recovery**
1. Install the correct extra for the chosen provider.
2. Confirm the provider spelling and environment variables.
3. Rebuild or refresh embeddings only when the requested provider/model identity is stable.

## Cloud embedding warnings

**Symptoms**
- The CLI warns about external egress.
- A provider seems valid but is intentionally blocked by policy.

**Likely causes**
- Cloud embeddings are opt-in and require explicit acceptance.
- The endpoint is not local, so CRG warns before sending code snippets out.

**Recovery**
1. Only continue if the user explicitly accepted the external provider.
2. Prefer local embeddings when privacy matters.
3. Use the warning as a stop signal, not a false positive.

## Registry or daemon refuses a repo

**Symptoms**
- Register/unregister operations fail for a path or alias.
- The daemon reports no repository or a duplicate alias.

**Likely causes**
- The path is not a repository or does not exist.
- The alias is already in use.
- The repo was moved after registration.

**Recovery**
1. Verify the path is a real repo checkout.
2. Use a unique alias.
3. Re-register after moving or recreating the repo.

## Wiki generation is sparse

**Symptoms**
- The wiki only contains an index or very little content.

**Likely causes**
- The graph has few or no communities.
- The optional wiki summary backend is unavailable.

**Recovery**
1. Ensure the graph has enough structure.
2. Install or configure the optional summary backend only if needed.
3. Treat structural-only wiki output as valid when summaries are intentionally unavailable.

## GitHub Action workflow safety issues

**Symptoms**
- A fork PR cannot comment directly.
- The trusted workflow checks out untrusted code or misses the artifact gate.

**Likely causes**
- The split analysis/comment workflow was not used.
- The trusted workflow lost its source-event or commit validation.

**Recovery**
1. Keep analysis and comment publishing in separate jobs.
2. Validate the artifact before posting.
3. Avoid direct privileged checkout of PR code.

## Eval reproduction is too heavy for the current session

**Symptoms**
- Benchmark reproduction needs clones, time, or network the session cannot provide.

**Likely causes**
- The user asked for a maintainer-level benchmark run, not a unit check.

**Recovery**
1. Run the unit-level eval tests first.
2. Stop and ask before attempting expensive benchmark clones.
3. Record the missing upstream snapshot or dependency explicitly.