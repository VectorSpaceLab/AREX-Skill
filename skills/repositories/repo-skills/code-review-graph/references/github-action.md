# Repo-Level GitHub Action Summary

For detailed instructions, use `sub-skills/integrations-and-extensions/references/github-action.md` and the review sub-skill.

The action runs CRG on a CI runner, analyzes PR changes, renders a sticky markdown comment, and can fail a job on high/critical risk. For fork PRs, keep analysis unprivileged and publish comments from a separate trusted `workflow_run` workflow after artifact validation.