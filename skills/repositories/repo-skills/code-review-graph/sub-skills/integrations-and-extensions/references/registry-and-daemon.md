# Registry and Daemon Workflows

## Purpose

Read this when the task is to register multiple repositories, list them, search across them, or keep several repos fresh with the watch daemon.

## Registry workflow

The registry stores repository paths and aliases so CRG can search across multiple repos.

Common commands:

```bash
code-review-graph register /path/to/repo --alias myrepo
code-review-graph repos
code-review-graph unregister myrepo
```

Use the registry when the same user wants CRG available across more than one checkout.

## Daemon workflow

The daemon manages watch processes for registered repositories.

Common commands:

```bash
code-review-graph daemon add /path/to/repo --alias myrepo
code-review-graph daemon start
code-review-graph daemon status
code-review-graph daemon logs --repo myrepo
```

The daemon is a convenience layer for keeping multiple watched repos in sync; it is not required for single-repo CRG usage.

## Repo validation rules

Before registering a repo, CRG expects a path that looks like a repository, usually with `.git` or an existing graph directory. Invalid paths or duplicate aliases are rejected.

## Wiki workflow

The wiki generator turns communities into markdown pages under the graph data directory. Use it after the graph has communities to summarize.

## GitHub Action and eval context

This sub-skill also owns the higher-level integration surfaces that sit next to registry/daemon usage:

- the public PR review GitHub Action,
- the split analysis/comment workflow for forks,
- and the evaluation/benchmark commands.

Those are documented in their dedicated references so registry/daemon users do not have to read the whole package docs.
