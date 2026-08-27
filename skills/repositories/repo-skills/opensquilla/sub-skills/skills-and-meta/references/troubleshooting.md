# Skills and Meta-Skills Troubleshooting

Use this when Skill catalog or MetaSkill behavior disagrees with user
expectations. Prefer read-only commands first, then decide whether mutation is
needed.

## Quick Triage

```sh
opensquilla skills list --json
opensquilla skills view <skill-name> --json
opensquilla skills doctor <skill-name-or-install-id> --json
opensquilla skills inspect <meta-skill-name>
opensquilla skills meta runs failures --since 24h --json
opensquilla skills meta proposals list --json
```

If the problem is about sessions, global diagnostics, replay outside MetaSkill
run history, memory, cron jobs, provider/model config, channels/MCP, or UI
startup, route to the sibling sub-skill named for that surface.

## Skill Is Installed but Not Selected

Likely causes:

- a higher-precedence layer shadows it;
- the operator disabled the Skill;
- optional dependency readiness is `needs_setup`;
- Community compatibility is degraded/instruction-only;
- the current turn has a pinned catalog and will not see the install until the
  next turn or Gateway restart;
- the task wording does not match the Skill description/triggers.

Actions:

1. Run `skills doctor <name-or-install-id> --json`.
2. Check selection/readiness/compatibility lifecycle fields.
3. If shadowed, identify the active candidate and use exact `--install-id` for
   mutation.
4. If disabled, explain that operator config gates it out; do not bypass config.
5. If `needs_setup`, install or configure the missing dependency separately;
   `skills install` does not do this automatically.
6. Ask for the desired outcome in normal language rather than only naming the
   Skill.

## Install or Update Conflict

Symptoms:

- ambiguous name-only update/uninstall;
- same runtime name from another source;
- `replaceSource` required;
- installed tree drift;
- new install appears as shadowed or disabled.

Actions:

- Use `skills doctor --json` to collect install ids and lifecycle rows.
- Use `skills update --install-id <id>` or `skills uninstall --install-id <id>`
  when names collide.
- Use `skills install ... --replace-source` only after the user confirms they
  intend to replace a same-name install from a different package/source.
- Use `--allow-drift` only after reviewing local file changes and accepting that
  uninstall should remove the drifted tracked tree.
- If the result is shadowed, explain that a higher-precedence Skill remains
  active until that layer changes.

## Scanner Confirmation Required

Symptoms include `SCAN_CONFIRMATION_REQUIRED` or a CLI hint to retry with
`--force --risk-confirmation <token>`.

Do:

1. Review the scanner findings and source identity.
2. Confirm the artifact/revision did not change.
3. Retry only the exact reviewed artifact with both flags:

   ```sh
   opensquilla skills install <identifier> --source <source> \
     --force --risk-confirmation <token>
   ```

Do not:

- reuse a token for a changed revision or different fetched content;
- treat `--force` as bypassing path, digest, archive, transaction, or postflight
  validation;
- hide scanner findings from the user.

## Transaction or Recovery Issues

Symptoms:

- `SKILL_RECOVERY_REQUIRED`;
- `RECOVERY_REQUIRED`;
- pending managed Skill transaction journal;
- profile lock busy;
- reload/list refuses an offline catalog scan.

Actions:

- Avoid manual edits in the managed Skill directory while recovery is pending.
- Run Doctor when safe; it is the read-only surface for store/readiness state.
- If a profile lock is busy, stop the concurrent OpenSquilla process or retry
  later rather than racing it.
- If recovery remains blocking, escalate to an operator with the diagnostic code
  and journal phase. The transaction logic is fail-closed to prevent publishing
  a half-installed Skill.

## Reload or Live/Offline Catalog Mismatch

Symptoms:

- `skills list` says "validated offline";
- `skills reload` reports Gateway unavailable;
- `GATEWAY_UPGRADE_REQUIRED` appears for Doctor;
- a newly installed Skill is not selected in the current turn;
- `skills meta runs list` reports no history yet.

Actions:

- `skills list` can fall back to offline validation; do not call those rows live
  or active unless the payload says the catalog is live.
- `skills reload` needs a running compatible Gateway and never falls back.
- If Doctor returns `GATEWAY_UPGRADE_REQUIRED`, restart the Gateway from the
  same upgraded installation; do not race an older reachable Gateway with an
  offline scan.
- After accepting a proposal or offline install, restart or reload the Gateway as
  appropriate.
- A missing MetaSkill run database can simply mean no Gateway MetaSkill run has
  occurred yet.

## MetaSkill Does Not Appear or Run

Check:

```sh
opensquilla skills list
opensquilla skills view <meta-skill-name>
opensquilla skills inspect <meta-skill-name>
```

Likely causes:

- not under a loaded Skill directory;
- missing `kind: meta`;
- no non-empty `composition.steps` list;
- `disable-model-invocation` set for a workflow expected to be model-visible;
- `meta_skill.enabled = false`;
- user expected natural-language triggering while `meta_skill.auto_trigger` is
  false;
- the surface does not support running `/meta`.

Remember: default product behavior is manual `/meta` launch. If the user wants
natural-language triggering, make the compatibility setting explicit.

## MetaSkill Compile or Inspect Failure

Common manifest/plan problems:

- duplicate step ids;
- unknown `kind` values;
- missing `skill` for `agent` or `skill_exec`;
- missing `output_choices` for `llm_classify`;
- missing `clarify.fields` for `user_input`;
- missing `tool`, invalid `tool_args`, or mismatched `tool_allowlist` for
  `tool_call`;
- cycles or undefined `depends_on` references;
- `route.to` or `on_failure` points to a missing step/Skill;
- step composes another `kind: meta` Skill;
- raw `inputs.user_message` or raw unbounded `outputs.<step>` in templates.

Actions:

1. Run `opensquilla skills inspect <meta-skill-name>`.
2. Validate frontmatter YAML and the `composition.steps` DAG.
3. Bound and escape every user-input and step-output template.
4. For generated proposals, inspect creator gates and linter diagnostics before
   acceptance.

## Trigger Collision or Accidental Activation

Symptoms:

- a MetaSkill runs when the user asked how it works;
- creator starts on generic "create skill" wording;
- pasted history or old catalog text triggers a workflow;
- two triggers match the same neighboring domain.

Actions:

- Prefer short natural trigger phrases, but include negative boundaries in the
  description/body.
- Do not let `meta-skill-creator` handle normal standalone Skill creation.
- Ask users to mark old transcripts, examples, and Skill lists as quoted context
  when they only want analysis.
- Use `skills meta runs draft <run-id>` to inspect a seed and reported trigger
  conflicts.
- Maintainer-level deterministic and live trigger harnesses are reference-only;
  ordinary users should rely on `/meta <name>` for explicit launch.

## Recursion Guards and Execution Gating

Relevant safeguards:

- A MetaSkill cannot compose another MetaSkill; linter/runtime reject nested
  `kind: meta` references.
- Sub-agent tool lists filter out `meta_invoke`, so child agents cannot recurse
  into MetaSkill invocation.
- Meta invocation has depth and per-turn caps that return structured failure
  rather than unbounded recursion.
- Auto-propose synthesizes messages that avoid creator trigger phrases to
  prevent self-triggering loops.
- `code-task` remains gated unless coding mode is explicitly enabled.

If a run fails with a gating error, treat it as a safety boundary, not as a
missing package bug.

## Proposal Acceptance Mistakes

Before acceptance:

```sh
opensquilla skills meta proposals show <proposal-id>
```

Check:

- proposal id is eight lowercase hex characters;
- `SKILL.md` parses and has the intended `name`;
- gates and auto-enable audit are acceptable;
- risk metadata matches side effects;
- trigger surface avoids false positives;
- no existing managed Skill already uses the target name.

`accept` refuses ineligible gates unless `--force` is supplied and refuses to
overwrite an existing managed Skill. Use `--force` only with explicit operator
review.

## Tap or Source Repository Issues

Symptoms:

- search source diagnostics or partial results;
- rate limits;
- invalid source responses;
- GitHub reference resolution failure;
- immutable revision returns different content;
- custom tap not listed.

Actions:

```sh
opensquilla skills search <query> --json --include-diagnostics
opensquilla skills tap list
opensquilla skills tap add <owner/repo>
opensquilla skills tap remove <owner/repo>
```

- Use source diagnostics to distinguish no matches from source failures.
- Retry rate-limited searches later or narrow the source.
- Treat immutable-revision digest changes as a source integrity problem.
- Confirm custom tap owner/repo spelling and network access.

## Optional Dependencies and Backend Boundaries

The evidence baseline for this generated repo skill was CPU-only. There is no
GPU/ROCm/MPS/accelerator requirement for this Skill/MetaSkill management
sub-skill. Some bundled MetaSkills still have workflow-specific local toolchain
or provider prerequisites:

- document/PDF workflows may require TeX or document tooling;
- media workflows may require FFmpeg/FFprobe/font setup and a ready media
  provider profile;
- Community Skills may declare bins/env/config but installation does not install
  them;
- live provider/media calls require explicit cost/send approval where the
  workflow defines that boundary.

Route provider/model setup to `configuration-and-routing`; route generic
installation/gateway readiness to `setup-and-gateway`.
