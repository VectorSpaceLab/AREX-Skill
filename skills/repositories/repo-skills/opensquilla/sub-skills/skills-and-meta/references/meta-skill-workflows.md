# MetaSkill Workflows and Authoring

MetaSkills package repeatable multi-step work as reusable, inspectable workflows.
They compose existing Skills, tool calls, LLM calls, user-input pauses, and
validation steps; they do not add unrestricted execution atoms.

## Running MetaSkills

Default launch is explicit:

```text
/meta
/meta <meta-skill-name>
```

- Web chat and the CLI gateway TUI support listing and running MetaSkills.
- Channel surfaces can list MetaSkills with `/meta`, but they do not run
  MetaSkills from ordinary channel text.
- Standalone CLI chat requires gateway mode for `/meta`.
- Natural-language auto-triggering is disabled by default and should be enabled
  only deliberately with `meta_skill.auto_trigger = true`.

For UI launch context and where `/meta` is surfaced, route to
`tui-and-desktop`.

## Request Shape

A strong MetaSkill request states:

- outcome;
- context and materials;
- decision standard;
- expected output;
- constraints;
- actions that must not happen without confirmation.

Template:

```text
/meta <name>

Outcome:
Context:
Decision standard:
Expected output:
Constraints:
Do not:
```

Warn users to mark pasted transcripts, old skill lists, prompt examples, and Web
UI dumps as quoted context when they do not want a workflow to run.

## Built-In Workflow Family

The installed catalog is the source of truth:

```sh
opensquilla skills list
opensquilla skills search meta
opensquilla skills inspect <meta-skill-name>
```

Docs and bundled evidence describe retained workflows such as:

| MetaSkill | Use it for | Key boundary |
| --- | --- | --- |
| `meta-paper-write` | Academic drafts, manuscript structure, citation planning, experiment placeholders, and LaTeX/PDF paths. | PDF compilation requires a TeX readiness probe or managed setup approval. |
| `meta-short-drama` | Short-drama scripts, visual prompts, subtitles, and local video artifacts. | Rendering/media dependencies and paid provider submits have explicit approval boundaries. |
| `AwesomeWebpageMetaSkill` | Packaged local multimedia webpage workflows where present in the installed catalog. | Real media generation depends on configured media provider readiness and explicit cost/send approval. |
| `meta-skill-creator` | Creating a new MetaSkill proposal from a repeated multi-skill collaboration pattern. | Produces a proposal/gates for review, not an unreviewed production rollout. |

Availability can differ by build and operator configuration, so always confirm
with `skills list` or `/meta` before promising a workflow exists.

## `meta-skill-creator` Route

Use `meta-skill-creator` only when the user explicitly asks to create, compose,
synthesize, or propose a new MetaSkill that orchestrates multiple existing
Skills. Good fits include:

- turning repeated multi-skill collaboration into a reusable workflow;
- defining trigger surfaces and false-positive boundaries;
- composing existing Skills into a DAG;
- adding validation and risk checks;
- producing a proposal for review.

Poor fits:

- normal standalone Skill creation;
- asking what MetaSkill is;
- analyzing existing Skill lists without creating anything;
- diagnosing pasted old pages or transcripts;
- broad requests that do not need a stable multi-step output.

High-quality creator request:

```text
/meta meta-skill-creator

Create a new meta-skill for product launch briefs. It should search current
sources, collect product context, draft a launch memo, generate a DOCX handoff,
check evidence gaps, and avoid publishing anything automatically.

Please propose:
- name
- description
- triggers
- steps
- validation gates
- collision checks
```

Expected result: a proposal plus validation notes. Persistence or acceptance is
a separate reviewed step unless the user explicitly requested and authorized it.

## Creator Flow Internals

The bundled creator workflow includes these surfaces:

1. Intent clarification: distinguish MetaSkill composition from normal Skill
   creation and collect missing workflow fields when needed.
2. Creation mode classification: preview-only, persisted proposal, or full gated
   validation.
3. Optional history/decision-log harvesting for unattended auto-propose runs.
4. Pattern selection and slot filling against bounded schemas.
5. Assembly into a `SKILL.md` candidate.
6. Trigger-collision checks, lint, smoke/runtime gates, and preview/final
   response.
7. Optional proposal persistence under the managed proposal area.
8. Optional auto-enable only when configured and deterministic low-risk gates
   allow it.

Creator helper tools are registered for orchestrator use but hidden from normal
owner tool catalogs. Do not direct users to invoke those internal tools directly.

## Authoring Frontmatter Essentials

A normal OpenSquilla MetaSkill uses frontmatter like:

```yaml
---
name: short-stable-name
kind: meta
description: One sentence explaining when this workflow applies.
triggers:
  - natural trigger phrase
meta_priority: 50
always: false
final_text_mode: auto
metadata:
  opensquilla:
    risk: low
    capabilities: []
composition:
  steps: []
---
```

Important fields:

- `kind: meta` marks the Skill as a MetaSkill.
- `triggers` and `description` drive compatibility auto-trigger behavior.
- `meta_priority` breaks ties between trigger matches.
- `final_text_mode` controls whether final output is auto-summarized, raw, or
  taken from `step:<step_id>`.
- `metadata.opensquilla.risk` and `metadata.opensquilla.capabilities` document
  side effects and gate unattended auto-enable.
- `composition.steps` is the DAG.

## Step Kinds

| Kind | Use for |
| --- | --- |
| `agent` | A skill-backed sub-agent turn for reasoning/synthesis. |
| `llm_chat` | One bounded LLM generation step with no tool loop. |
| `llm_classify` | One closed-set classification. Requires `output_choices`. |
| `user_input` | Pause and collect structured fields through `clarify`. |
| `tool_call` | Deterministic direct tool execution. Keep arguments narrow and declare allowlists. |
| `skill_exec` | Run a Skill with an `entrypoint` as a subprocess. |

Steps without dependencies may run in parallel. A dependent step waits for all
`depends_on` ids. `on_failure` can name one substitute step; the substitute must
exist in the same plan and not define its own dependency/failure chain.

## Template Safety

Treat user input and previous step output as untrusted:

- For user text, start with `xml_escape` or `slugify`, then bound with
  `truncate`.
- For `outputs.<step_id>`, bound or encode with `truncate`, `xml_escape`,
  `slugify`, or `tojson`.
- Do not pass raw `{{ inputs.user_message }}` downstream.
- Do not pass raw `{{ outputs.some_step }}` downstream.
- Keep prompt-shaped strings concise and task-specific.

Safe examples:

```yaml
query: "{{ inputs.user_message | xml_escape | truncate(512) }}"
text: "{{ outputs.search | truncate(2000) }}"
slug: "{{ inputs.user_message | slugify | truncate(80) }}"
payload: "{{ outputs.plan | tojson }}"
```

## Validation Checklist

Before sharing, accepting, or enabling a MetaSkill:

1. YAML frontmatter parses.
2. `kind: meta` and `composition.steps` are present.
3. Step ids are unique.
4. `depends_on`, `route.to`, and `on_failure` references resolve.
5. The graph is acyclic.
6. No step composes another `kind: meta` Skill.
7. User input and step outputs are filtered and bounded.
8. Risk/capability metadata matches side effects.
9. Trigger phrases do not collide with explanation questions or neighboring
   workflows.
10. Lint/smoke/runtime gates and proposal detail are reviewed before acceptance.

## Configuration Switches

```toml
[meta_skill]
enabled = true
auto_trigger = false
```

- `enabled = false` keeps inventory/history useful but disables model-visible
  runtime invocation.
- `auto_trigger = false` is the default manual-only product mode. Set true only
  for compatibility with older natural-language triggering.

Unattended creator proposal settings are nested under `meta_skill.auto_propose`:

| Key | Meaning |
| --- | --- |
| `enabled` | Schedule recurring auto-propose. Default off. |
| `cron` | Five-field local-time cron expression. |
| `window_days` | Decision-log aggregation window. |
| `min_freq` | Minimum observed co-occurrence frequency. |
| `top_k` | Maximum patterns considered per run. |
| `on_dream_complete` | Also run after memory-consolidation dreams. |
| `auto_enable` | Promote eligible proposals automatically. Default off. |
| `auto_enable_max_risk` | Highest deterministic risk class accepted for unattended promotion. |
| `agent_ids` | Optional restriction to selected durable agents. |

Keep unattended auto-enable conservative. A failed or degraded gate should leave
the proposal pending for review.

## Maintainer Script Boundary

Source maintainer scripts such as meta validation matrices, live creator E2E
harnesses, live soft-activation harnesses, benchmark integrity checks, and
OpenClaw comparison harnesses are evidence for product behavior, not ordinary
runtime tools. They are live-provider, benchmark, credentialed, or internal
comparison workflows and are not copied into this operating sub-skill. Use the
CLI surfaces above for user-facing operation.
