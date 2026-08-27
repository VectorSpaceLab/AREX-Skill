# Routing, Eligibility, Provenance, and Composition

Use this reference when a user asks why a Skill or MetaSkill is visible,
selected, hidden, shadowed, disabled, degraded, or safe to install.

## Catalog Layers and Shadowing

OpenSquilla compiles Skills from multiple layers. The source defines layer
precedence from low to high as:

1. `extra`
2. `bundled`
3. `managed`
4. `personal`
5. `project`
6. `workspace`

If multiple physical Skill trees expose the same runtime `name`, the
highest-precedence eligible candidate is active and lower-precedence candidates
are shadowed. Shadowed candidates can still be visible to Doctor and install
results, but a higher-precedence Skill remains the one used at runtime.

Practical route:

```sh
opensquilla skills list --json
opensquilla skills doctor <skill-name-or-install-id> --json
```

Look for lifecycle/selection states rather than assuming the newest install is
active.

## Lifecycle Vocabulary

Doctor and management results distinguish these concepts:

| Axis | What it answers |
| --- | --- |
| Install state | Is a tracked managed package present, missing, untracked, or drifted? |
| Load state | Did the loader accept, reject, validate offline, serve a previous version, or not discover it? |
| Selection state | Is this candidate active, shadowed by another layer, disabled, hidden, or otherwise unavailable? |
| Compatibility state | Is the content native/trusted or projected to instruction-only/degraded compatibility? |
| Readiness state | Are required binaries, env vars, config, or setup steps ready? |

Do not collapse these states into a single "installed/not installed" answer. A
Skill can be installed but shadowed, disabled, missing setup, degraded, or only
validated offline for the next Gateway start.

## Managed Identity and Provenance

OpenSquilla tracks separate identities for Community packages:

- source type such as `clawhub` or `github`;
- source package id and resolved immutable revision;
- safe managed-directory key;
- runtime frontmatter `name`;
- `install-id` for exact mutations;
- tree digest and artifact digest.

Use `--install-id` for exact update/uninstall when runtime names collide or a
name-only mutation is ambiguous. A package can preserve an ecosystem-native
runtime name without using that value as its filesystem path.

## Community Skill Projection Boundary

Community installs are intentionally instruction-only in this build:

- Instruction text and safe invocation metadata remain usable.
- Declared runtime dependencies are not installed by `skills install`.
- Claude/OpenClaw-style executable/control-flow fields such as hooks, plugin/MCP
  activation, direct `/skill` command semantics, argument substitution, and
  executable sandbox materialization are not activated by Community install.
- `allowed-tools` does not grant tool preapproval. Doctor reports that as a
  compatibility diagnostic.
- Claude-style dynamic context such as ``!`command` `` is retained as text rather
  than executed while loading; Doctor can mark the installation degraded.

If the user wants full execution compatibility with another agent ecosystem,
make the compatibility boundary explicit instead of promising it.

## Eligibility and Operator Gates

A Skill can be gated out even when its files parse:

- `[skills].disabled` disables named Skills from the agent view.
- `[skills].coding_mode` is off by default; `code-task` is unreachable through
  every Skill API while coding mode is off.
- `disable-model-invocation` hides a Skill/MetaSkill from model-visible
  selection. This is intentional for generated repo operating skills, but it is
  a problem if an OpenSquilla MetaSkill is expected to be chosen by the model.
- Readiness checks can mark a Skill `needs_setup` when bins, environment,
  config, or managed toolchain probes are missing.

Use Doctor to prove which gate applies.

## Runtime Selection Guidance

Users should ask for outcomes, not internal Skill names:

```text
Create a PowerPoint deck summarizing this report.
```

is better than:

```text
Load the pptx skill and run its script.
```

OpenSquilla chooses eligible Skills from the current catalog by description,
triggers, and runtime context. Mentioning a Skill name can help, but the task
intent still needs to be clear.

## MetaSkill Visibility and Activation

MetaSkills are `kind: meta` Skills with `composition.steps`. Product default is
manual launch through `/meta` and `/meta <name>` on supported chat surfaces.
Natural-language model triggering is compatibility mode only when
`meta_skill.auto_trigger = true`.

Operators can disable the meta-skill subsystem with:

```toml
[meta_skill]
enabled = false
```

When disabled, MetaSkills can remain installed for inventory and historical run
inspection, but model-visible invocation is rejected or hidden.

## Composition Rules to Remember

A MetaSkill composition is a small DAG, not arbitrary recursion:

- steps must have unique ids;
- `depends_on`, `route.to`, and `on_failure` references must resolve;
- the graph must be acyclic;
- a MetaSkill cannot compose another `kind: meta` Skill;
- sub-agent steps are prevented from invoking `meta_invoke` recursively;
- tool and skill execution steps remain subject to operator gates;
- user input and previous step outputs must be filtered and bounded before
  flowing into templates.

When a compiled plan looks wrong, inspect it before running:

```sh
opensquilla skills inspect <meta-skill-name>
```

## Live vs Offline Catalog Observations

- A running Gateway owns the live catalog; the CLI tries Gateway RPC first for
  list/Doctor/mutations.
- Offline `skills list` and Doctor can validate local files when no Gateway is
  reachable, but output should be described as offline readiness, not active
  live availability.
- A current agent turn can keep a pinned catalog; a newly installed Skill may be
  visible from the next turn or next Gateway start, not necessarily immediately
  in the same turn.
- `skills reload` is a running-Gateway operation. If it fails, the prior
  generation remains active.

## Routing Boundaries

- Provider/model/router/search provider configuration belongs to
  `configuration-and-routing`.
- Sessions, general history exports, diagnostics toggles, cron jobs, and replay
  outside `skills meta runs` belong to `cli-and-automation`.
- `/meta` UI surfacing and terminal/desktop launch behavior belong to
  `tui-and-desktop`.
- Channels and MCP belong to `channels-and-integrations`.
- Generic gateway setup belongs to `setup-and-gateway`.
