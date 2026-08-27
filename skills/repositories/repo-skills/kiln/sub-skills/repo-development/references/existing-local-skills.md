# Existing local skills

Use this reference when a maintenance request resembles one of Kiln's local `.agents/skills` procedures. These are checkout-local maintenance workflows, not product runtime APIs. Do not run costed, credentialed, or outward-facing parts without explicit user approval.

## Summary table

| Local skill | Purpose | Safe default boundary | Human/credential gates |
| --- | --- | --- | --- |
| `claude-maintain-models` | Add, integrate, or register new LLM models in Kiln's model list, including provider IDs, capability flags, tests, and announcement draft. | Research and code-review model-list changes from authoritative provider/catalog evidence. | Paid provider tests, suggested-model flag swaps, Discord/public announcement copy, and any uncertain provider capability decisions need confirmation. |
| `kiln-check-deprecation` | Audit chat/model provider entries for deprecated, missing, or sunset models using provider model-listing endpoints. | Listing checks are intended to be non-inference/free where supported. Report findings clearly. | Network credentials may be needed. Marking `deprecated=True`, checking Vertex/Bedrock credentials, or removing models requires confirmation. |
| `kiln-check-finetune-deprecation` | Audit static and dynamic fine-tune base-model support across providers. | Report stale fine-tune IDs, dynamic Fireworks support differences, and recommended remediations. | Provider credentials may be needed. Any remediation code change needs confirmation. |
| `kiln-prerelease-check` | Run standard checks plus curated prerelease paid smoke tests, diagnose failures and stale prerelease pins, and write a readable report. | Read-only report generation. Standard checks are local; prerelease smoke is explicitly gated. | Paid provider credentials, live network access, and user approval are required. Do not edit code or whitelists during the prerelease check itself. |
| `release-digest` | Build a release recap from changes merged since the latest release tag and post it to the release Slack channel after confirmation. | Gather and classify unreleased changes; compose a message for review. | Ask for the new release name, show the composed Slack message, and get confirmation before posting. |

## Model-list maintenance boundaries

Model-list tasks often blend code changes, provider research, paid tests, and public communication.

Before adding or updating a model entry:

- Verify every provider `model_id` from an authoritative provider or catalog source.
- Compare with the predecessor model in the same family for naming, capabilities, parser/formatter behavior, and provider-specific quirks.
- Treat catalog capability flags as the primary capability signal, then cross-check against Kiln's predecessor configuration.
- Do not set `suggested_for_evals` or `suggested_for_data_gen` casually. If swapping suggestions, ask the user to confirm the zero-sum change.
- Use exact parametrized pytest node IDs or bracketed filters for model/provider tests when possible.
- Paid tests cost money and require credentials; confirm before running.
- Public announcement drafts require user approval before posting.

Route runtime model execution semantics to `task-execution-providers-tools`; this reference only covers repository maintenance workflow boundaries.

## Deprecation check boundaries

General model deprecation checks should be conservative:

- Listing endpoints can indicate missing, expiring, legacy, or skipped providers.
- Already-deprecated entries should not be repeatedly rechecked unless the user asks.
- OpenRouter virtual routing suffixes, Vertex aliases, dynamic Fireworks entries, and provider-specific API quirks require careful interpretation.
- Mark a provider entry deprecated only after a confirmed provider-specific signal and user approval.
- Do not remove model entries automatically; Kiln convention is to preserve entries and mark deprecated where appropriate.

Fine-tune deprecation checks are separate from inference deprecation. A base model can still work for inference but no longer be supported for fine-tuning. Treat stale fine-tune support as a recommendation until the user confirms remediation.

## Prerelease check boundaries

Prerelease checks are release-candidate smoke tests, not ordinary local unit tests.

- They run standard repo checks and a curated subset of paid tests marked `prerelease`.
- Missing credentials should be reported as skipped coverage, not code failure.
- Live provider failures should be diagnosed into cause classes such as missing credentials, provider rejection, rate limit/transient, behavioral regression, or Kiln code regression.
- Retry likely transient live failures once, disclose the retry, and distinguish flakes from reproducible failures.
- The model-pin staleness sweep is mandatory for a prerelease report even if tests are green.
- The workflow is read-only. Do not edit production source, prerelease whitelists, or tests as part of the prerelease check unless the user starts a separate fix task.

## Release digest boundaries

Release digests are outward-facing team communication.

- Gather changes from the commit range since the latest release tag, not by merge date.
- Group changes by author and classify each as feature, bug fix, or task.
- Routine model-catalog changes are tasks unless they add a genuinely new product capability.
- Ask the user for the new release name.
- Show the final message and wait for confirmation before posting to Slack.
- Linear ticket targeting is out of scope for the digest unless the user gives new instructions.

## When to route elsewhere

- Product API route behavior, OpenAPI details, webhost/Git sync/jobs/chat, and MCP server behavior: `server-desktop-web-api`.
- Core datamodel and project/task/run object workflows: `project-datamodel`.
- Provider adapters, run configs, tools, skills, and model execution semantics: `task-execution-providers-tools`.
- RAG, documents, vector stores, LanceDB, indexing, and search: `rag-documents-data`.
- Evals, synthetic data, prompt optimization, fine-tuning, and repair behavior: `evals-optimization-finetuning`.

## Evidence notes

This summary is based on the frontmatter and workflow bodies in `.agents/skills/claude-maintain-models/SKILL.md`, `.agents/skills/kiln-check-deprecation/SKILL.md`, `.agents/skills/kiln-check-finetune-deprecation/SKILL.md`, `.agents/skills/kiln-prerelease-check/SKILL.md`, and `.agents/skills/release-digest/SKILL.md`.
