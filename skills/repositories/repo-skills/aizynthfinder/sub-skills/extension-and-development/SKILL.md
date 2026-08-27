---
name: extension-and-development
description: "Extend AiZynthFinder with custom hooks, stocks, scorers, policies,
  plugins, search algorithms, and focused development tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# AiZynthFinder Extension and Development

Use this sub-skill when the task is to add, validate, or debug AiZynthFinder extension points rather than only run an existing planning job.

## Route Here

- Custom Python import paths for stocks, scorers, expansion/filter policies, search trees, Retro* costs, or CLI hooks.
- CLI pre-processing modules exposing `pre_processing(finder, index)` and post-processing modules exposing `post_processing(finder)`.
- Custom stock query objects, `smiles2stock --source module` SMILES extractors, custom scorer classes, and custom expansion strategies.
- Optional plugin-like expansion strategies such as Chemformer REST and ModelZoo-backed policies.
- Search algorithm selection or implementation involving MCTS, breadth-first, DFPN, Retro*, or a custom `SearchTree`-compatible class.
- Focused source-edit validation, test selection, and maintainer task orientation.

## Route Elsewhere

- For ordinary YAML structure, stocks/model file placement, optional dependency installation choices, and environment variable use, use `configuration-and-data`.
- For running `aizynthcli`, checkpoints, multi-target execution, and CLI hook invocation, use `planning-workflows`.
- For interpreting route scores, ranking routes, route statistics, clustering, or custom scorer outputs after a run, use `route-analysis`.

## Core References

- `references/customization.md` covers extension interfaces, dynamic class paths, hooks, stocks, scorers, policies, and optional plugins.
- `references/search-algorithms.md` covers MCTS, breadth-first, DFPN, Retro*, and custom search-tree config guidance.
- `references/development-tests.md` gives focused pytest selection and maintainer-command safety guidance for source edits.
- `references/troubleshooting.md` maps dynamic-loading, hook, plugin/service, optional dependency, and test failures to fixes.
- `scripts/check_custom_aizynth_module.py` imports a user-specified module/class/function and reports interface checks without starting services or touching networks.

## Fast Triage

1. Identify the extension mode: hook, SMILES extractor, stock object, scorer class, expansion class, search tree, or optional plugin.
2. Confirm the object is importable in the same Python environment and from the same working context that will run AiZynthFinder.
3. Validate the object with `scripts/check_custom_aizynth_module.py` before asking AiZynthFinder to load it.
4. Put fully qualified class paths in YAML when dynamic loading is used; bare names work only for built-in defaults that provide a default module.
5. Keep plugin/service configuration explicit: installed extra/package, importable module path, reachable service URL or local model path, and conservative time limits.
