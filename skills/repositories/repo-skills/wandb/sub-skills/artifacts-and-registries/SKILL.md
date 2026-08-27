---
name: artifacts-and-registries
description: "Create, log, consume, download, link, and troubleshoot W&B
  Artifacts and registry/model-registry flows through Python and CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# W&B Artifacts and Registries

Use this sub-skill when a task involves versioned datasets, models, files, directories, external object-store references, artifact aliases/tags/types, downloads, artifact CLI commands, or linking artifacts into registries/model registries.

## Route by task

- **Create or log artifacts:** Use `references/workflows.md#create-and-log-versioned-artifacts` and `references/api-reference.md#artifact-construction` for `wandb.Artifact`, `add_file`, `add_dir`, `add_reference`, and `Run.log_artifact` patterns.
- **Consume or download artifacts:** Use `references/workflows.md#consume-and-download-artifacts` and `references/api-reference.md#artifact-consumption` for `Run.use_artifact`, `wandb.Api().artifact`, `Artifact.download`, `Artifact.file`, and path forms.
- **Use artifact CLI:** Use `references/cli-reference.md` for `wandb artifact put`, `get`, `ls`, and `cache cleanup` syntax and path expectations.
- **Link to registries:** Use `references/workflows.md#link-artifacts-to-registries` and `references/api-reference.md#registries-and-linking` for `Run.link_artifact`, `Artifact.link`, registry paths, aliases, and public API registry helpers.
- **Debug failures:** Use `references/troubleshooting.md` for invalid names/types, missing files, credentials, optional storage dependencies, alias/version confusion, finalized mutation errors, and registry path/link errors.
- **Offline validation helper:** Run `python sub-skills/artifacts-and-registries/scripts/artifact_manifest_smoke.py --help` from the root skill directory to validate names/types and preview a local manifest without upload.

## Boundaries

This sub-skill covers artifact creation, artifact references, artifact lifecycle operations, artifact CLI usage, registry linking, registry lookup, and storage integration gotchas. For general scalar/media metric logging, use the experiment-tracking sub-skill. For large Public API reporting and automation beyond artifacts/registries, use public-api-and-automation. For launch jobs or sweeps that consume artifacts, use sweeps-and-launch after preparing artifacts here.
