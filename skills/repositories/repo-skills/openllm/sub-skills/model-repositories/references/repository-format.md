# OpenLLM Repository Format

## When to read

Read this when creating or debugging a custom public repository for OpenLLM model Bentos.

## Expected layout

OpenLLM expects a repository tree that contains a `bentos/` directory with model/version subdirectories.

```text
<repo-root>/
  bentos/
    <model-name>/
      <version>/
        bento.yaml
      <alias> -> version file or alias pointer
```

In practice, the lookup logic scans paths shaped like `bentoml/bentos/<model>/<version>` inside a cloned repository cache. If a file exists instead of a directory, OpenLLM treats it as an alias pointer to the real version directory.

## Required metadata

Each Bento directory should contain a `bento.yaml` file with:

- `name`
- `version`
- `labels`
- `envs`
- `services`
- `schema`

The `labels` section can include a `platforms` value such as `linux` and may include `aliases` for alternate tag names.

## Public repository constraint

OpenLLM's documented custom repository workflow is for public Git repositories. If the repository is private, the model-repository workflow should stop and ask for an alternate access plan.

## User-facing patterns

- Default repository alias: `default`
- Additional packaged alias: `nightly`
- Custom repository registration: `openllm repo add <alias> <git-url>`
- Model lookup by repository alias: `openllm model list --repo <alias>` or `openllm model get <tag> --repo <alias>`
