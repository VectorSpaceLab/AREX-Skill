# Cross-Cutting Troubleshooting

Use this reference for failures that can occur before a narrower sub-skill owns the workflow. Sub-skill references contain target-specific recovery steps.

## Install and Command Discovery

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `agents-cli: command not found` | Package not installed on `PATH` | Install with `uv tool install google-agents-cli`; then reopen the shell or run the `uv tool dir` path directly. |
| Help output differs from this skill | Package version changed | Run `agents-cli --version`; compare with `references/repo-provenance.md`; refresh this repo skill if the installed major/minor version changed. |
| A command mentioned in old docs is missing | The CLI removed or renamed a capability | Check `references/command-surface.md`; for RAG/data ingestion, use clone-and-study recipes through `sub-skills/adk-code/SKILL.md`. |
| `agents-cli info` cannot find a project | Current directory is not a scaffolded project or manifest is missing | Run from the project root containing `agents-cli-manifest.yaml`, or scaffold/enhance first. |

## Authentication and Cloud Context

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Cloud command reports missing project | `gcloud` project is unset or env vars are missing | Set `gcloud config set project PROJECT_ID` and confirm required flags/env vars for the sub-skill. |
| 403 from Cloud Run, Agent Runtime, Discovery Engine, or Terraform | Missing IAM role or wrong principal | Identify the service account/user used by the command, then follow the deploy/publish/observability sub-skill IAM notes. |
| Agent Runtime or Gemini Enterprise registration fails after deploy | Stale metadata, SDK mismatch, or wrong registration mode | Read `sub-skills/deploy/references/agent-runtime.md` and `sub-skills/publish/SKILL.md`; verify `deployment_metadata.json` and registration type. |

## Project Mutation Safety

- For new projects, do not pre-create the target directory before `agents-cli scaffold create`.
- For existing projects, run `agents-cli info` and inspect `agents-cli-manifest.yaml` before `scaffold enhance` or `scaffold upgrade`.
- Do not hand-edit scaffold-generated serving glue unless the relevant sub-skill says it is safe; generated FastAPI, A2A, service, Docker, Terraform, and CI/CD files carry CLI assumptions.
- Ask before creating repositories, pushing branches, deploying cloud resources, publishing to Gemini Enterprise, or installing skills into other coding-agent directories.

## Skill Refresh Triggers

Refresh this repo skill when any of these are true:

- `agents-cli --version` differs materially from 1.3.1.
- `agents-cli --help` adds/removes command groups or changes major flags.
- Scaffolded templates change serving, session, A2A, Docker, Terraform, eval, or CI/CD layouts.
- Documentation changes product names, supported deployment targets, registration types, or IAM requirements.
