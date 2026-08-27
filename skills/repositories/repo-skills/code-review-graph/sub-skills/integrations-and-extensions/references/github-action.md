# GitHub Action Integration

## Purpose

Read this when the task is to use CRG as a pull-request review bot or to understand the split analysis/comment workflow.

## What the action does

The composite GitHub Action:

1. installs `code-review-graph`,
2. restores or builds the graph on the CI runner,
3. runs `detect-changes`,
4. renders a sticky PR comment,
5. and can enforce a simple risk gate.

## Safe workflow pattern

For fork-safe CI, keep the analysis job unprivileged and publish the comment from a separate trusted workflow. That pattern avoids running untrusted PR code with a write token.

Key ideas:
- use the analysis workflow to generate the report artifact;
- use a separate `workflow_run` comment workflow to validate the artifact and post the sticky comment;
- keep the source-event and SHA checks in the trusted workflow;
- never replace the renderer with raw JSON pasted into a comment body.

## Renderer behavior

The bundled PR renderer:

- takes `detect-changes` JSON,
- escapes markdown control characters,
- relativizes CI-runner absolute paths,
- and keeps the hidden marker as the first line so the comment can be updated in place.

## Inputs worth knowing

- `github-token`
- `comment`
- `fail-on-risk`
- `python-version`

## When to use

Use this reference whenever a user asks to:
- publish CRG review comments in GitHub Actions,
- understand why direct `pull_request_target` is unsafe for untrusted code,
- or adapt CRG’s PR review workflow to another repository.
