# Prompt sampling

The following representative prompts were selected from the external usability
case suite for final review:

1. **Novice/root:** install `huggingface_hub`, verify Python/CLI versions, and
   choose routes for dataset download, hosted inference, and repo creation
   without a remote operation.
2. **Hub troubleshooting:** create/reuse a private dataset, inspect a revision,
   upload a PR with `parent_commit`, recover once from a stale-parent 409, and
   prevent token leakage or duplicate PRs.
3. **Storage troubleshooting:** plan a bucket copy involving `logs/`,
   `logs-old/`, and `../secrets.txt`, preserving trailing-slash semantics and
   rejecting traversal before apply.
4. **Inference expert:** mock a chat tool call with JSON schema, handle stream
   cancellation and provider fallback, and explain the optional MCP extra.
5. **CLI automation:** parse dry-run JSON from stdout while preserving stderr,
   then prove a delete without confirmation is refused.
6. **Integration:** validate a local model card/checkpoint/DDUF artifact and
   produce, but do not apply, an API/CLI PR upload plan with stale-parent
   recovery.

These samples cover root routing, novice and expert roles, primary/support/
troubleshooting flows, bundled scripts, safety gates, and multi-sub-skill
composition. Full prompts and assertions remain in `test-cases/`.
