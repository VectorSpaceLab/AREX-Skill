---
name: symbolic-tasks
description: "Guides CPU-only BDDL activity discovery, problem parsing, initial
  and goal condition inspection, symbolic scope construction, grounding,
  callback-based evaluation, natural-language rendering, and safe syntax
  validation. Use for BDDL activities, behavior task definitions, .bddl
  problems, predicates, object scope, or activity lists."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Symbolic Tasks

Use this sub-skill for symbolic BDDL work that needs only the `bddl` Python
package and packaged activity/domain data.

## Route

1. Confirm the package before inspecting definitions:

   ```bash
   python -m pip install "bddl==3.7.0"
   python -c "from importlib.metadata import version; import bddl; print(version('bddl'))"
   ```

2. For a read-only packaged activity inspection, run:

   ```bash
   python sub-skills/symbolic-tasks/scripts/inspect_bddl_activity.py --activity <activity> --instance 0 --domain behavior-1k
   ```

   Omit `--activity` to list packaged activities. Add `--natural-language` for
   readable conditions or `--tokens` for the raw nested token tree.

3. Read [API reference](references/api-reference.md) before constructing parsed
   conditions, scopes, compiled expressions, grounded options, evaluation
   callbacks, or BDDL text.
4. Read [troubleshooting](references/troubleshooting.md) when activity lookup,
   packaged files, syntax, predicates, scope, grounding, or evaluation fails.

## Boundaries

- This route covers symbolic parsing, representation, inspection, compilation,
  grounding, and callback-driven Boolean evaluation on CPU.
- It does **not** launch a simulator, populate physical scenes, execute robot
  behavior, provide object-state implementations, or establish that a symbolic
  task is physically feasible.
- Route object taxonomy, synset abilities, generated object metadata, and
  knowledge-base model questions to the sibling
  [knowledge-base sub-skill](../knowledge-base/SKILL.md). Return here after
  obtaining the object categories or metadata needed for a symbolic condition.
- Do not import OmniGibson or Isaac Sim for these workflows.
