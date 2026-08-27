---
name: behavior-1k
description: "CPU-only operating guidance for the BEHAVIOR-1K BDDL 3.7.0
  package: symbolic activity definitions, condition parsing/evaluation, object
  taxonomy, and generated-data-backed knowledge-base inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# BEHAVIOR-1K BDDL

Use this skill when a Researcher needs the **BDDL** portion of BEHAVIOR-1K:
activity-definition lookup, parsing, symbolic condition reasoning, object
synset/category taxonomy, or read-only knowledge-base inspection.

## Route by task

- **Activities, `.bddl` files, predicates, initial/goal conditions, scope,
  grounding, or symbolic evaluation:** read
  [symbolic-tasks](sub-skills/symbolic-tasks/SKILL.md).
- **Synsets, categories, substances, abilities, generated metadata, or
  `KnowledgeBase` models:** read
  [knowledge-base](sub-skills/knowledge-base/SKILL.md).
- **Package compatibility, shared installation failures, or scope limits:**
  read [API overview](references/api-overview.md) and
  [troubleshooting](references/troubleshooting.md).

## Supported contract

This generated skill intentionally covers only CPU-verifiable BDDL package
workflows from the pinned repository snapshot. Install the public distribution
in a compatible Python environment:

```bash
python -m pip install "bddl==3.7.0"
python -c "from importlib.metadata import version; import bddl; print(version('bddl'))"
```

The package includes activity/domain definitions and generated taxonomy data as
package-relative runtime data. Use the bundled read-only inspectors for quick
checks, then consult the sub-skill API references for programmatic workflows:

```bash
python sub-skills/symbolic-tasks/scripts/inspect_bddl_activity.py --help
python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py --help
python scripts/smoke_bddl_install.py --help
```

## Hard boundary

This skill does **not** cover OmniGibson, Isaac Sim, simulator/environment
execution, object-state runtime behavior, robots, controllers, sensors,
action primitives, cuRobo, GPU backends, physical hardware, asset production,
benchmark orchestration, or the excluded BEHAVIOR-1K monorepo packages. A
symbolic BDDL condition is not evidence that a simulator can instantiate or
satisfy that condition. The source snapshot's OmniGibson/Isaac Sim workflows
were not generated or verified because the required runtime was unavailable;
do not route such requests here as if CPU guidance were a substitute.

The generated-data files are runtime inputs. Do not run maintainer-only
`data_generation` pipelines as a routine repair or query method. Use the
troubleshooting references when package data is missing or inconsistent.

## Verification entry point

For a quick, read-only package/data smoke check, run
`scripts/smoke_bddl_install.py`. For activity-level and taxonomy-level
validation, use the inspectors linked above. Keep all simulator-dependent
claims outside this skill.

See [provenance](references/repo-provenance.md) for the source revision and
[evidence overview](references/api-overview.md) for the retained package
surface.
