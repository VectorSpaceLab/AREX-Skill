---
name: skill-authoring
description: "Create, register, test, package, and maintain ClawBio skills and
  their intent descriptors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ClawBio Skill Authoring

Use this sub-skill when a contributor must scaffold or modify a ClawBio skill, its
`SKILL.md`, executable implementation, tests, demo fixtures, CLI registration,
`INTENTS.json`, catalog metadata, or packaging contribution. Keep this sub-skill
focused on the authoring lifecycle; domain algorithms and scientific-result
interpretation belong to the domain skill and `validation-safety`.

## Operating route

1. Read [`references/authoring.md`](references/authoring.md) before changing a skill.
2. Define a one-task scope, explicit trigger and do-not-trigger cases, input/output
   contract, safety boundary, synthetic demo, and registration plan.
3. Scaffold from the repository template; write tests before implementation and
   demonstrate the red/green cycle.
4. Register only a working executable. Keep the CLI alias, skill directory, script
   path, descriptor, and catalog distinctions explicit.
5. Use [`scripts/check_skill_assets.py`](scripts/check_skill_assets.py) with an
   explicit target-checkout root, then run focused tests and the appropriate
   public CLI/demo in that checkout.
6. Regenerate the catalog with the repository generator after frontmatter changes;
   inspect the diff rather than hand-editing generated JSON.
7. Hand off validation and scientific evidence to `validation-safety`.

## Contracts to preserve

- Contributor skill folders are lowercase hyphenated identifiers; Python modules
  and tests use lowercase underscores.
- A contributor `SKILL.md` follows `templates/SKILL-TEMPLATE.md`; its `name`
  matches the folder, metadata is complete, triggers are loud and discriminating,
  and documented output is honest.
- Executable skills accept the stable `--input`, `--output`, and `--demo` contract,
  use synthetic data for demos, warn before overwriting, and include the exact
  ClawBio medical disclaimer in reports.
- `clawbio.py`'s static `SKILLS` entry is the CLI registration and its
  `allowed_extra_flags` is the security boundary. An `INTENTS.json` descriptor is
  deterministic routing metadata, not a shell command or a privilege grant.
- Catalog JSON is generated output. Never repair a stale catalog by blindly editing
  the artifact; fix source metadata/registration, run the generator, and review.

## References

- [`references/authoring.md`](references/authoring.md) — scaffold-to-tested workflow,
  trigger and I/O quality, demos, tests, registration, and contributor expectations.
- [`references/intent-descriptors.md`](references/intent-descriptors.md) — schema,
  route planning, slot extraction, path confinement, and blocked descriptor args.
- [`references/validation-and-packaging.md`](references/validation-and-packaging.md) —
  checker/test commands, catalog generation, hatch package inclusion, and PR gates.
- [`references/troubleshooting.md`](references/troubleshooting.md) — recovery for
  stale catalogs, missing scripts, invalid frontmatter, ignored descriptors, and
  package/test failures.

## Static checker

From the repository root, run:

```bash
python sub-skills/skill-authoring/scripts/check_skill_assets.py \
  --root <ClawBio-checkout> --skill <ClawBio-checkout>/skills/<skill-name> \
  --catalog <ClawBio-checkout>/skills/catalog.json
```

The checker is read-only, reports actionable errors, validates static registry and
catalog distinctions, and exits nonzero on a contract violation. Use `--help` to
inspect options; it never generates or overwrites artifacts.
