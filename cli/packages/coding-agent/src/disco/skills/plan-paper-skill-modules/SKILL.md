---
name: plan-paper-skill-modules
description: "Analyze a local AI research paper, optionally using a local repository as supporting evidence, and produce a concise paper profile plus a validated module plan of at most five reusable skill modules."
metadata:
  disco-role: meta
---

# Plan Paper Skill Modules

Use this skill after `paper-skills-distiller` has initialized an attempt directory. The goal is to identify the paper's transferable ideas and split them into no more than five modules that can become independent skills.

Write all artifacts in English.

## Inputs

- Local paper path or extracted paper text.
- Optional local repository path.
- Attempt directory containing `run_manifest.json`.

## Output Artifacts

Write these files into the attempt directory:

- `paper_profile.md`
- `module_plan.json`
- `modules/<module_id>.md` for every module

## Workflow

1. Extract or read the paper text. If the paper is a PDF, use `scripts/extract_paper_text.py` or another reliable parser.
2. Build `paper_profile.md` with:
   - bibliographic identity if available
   - problem statement
   - core insight
   - method components
   - datasets and reported metrics
   - expected fastest recovery experiment
   - repository evidence, if a repo exists
3. Inspect the repository only after understanding the paper. Use it to confirm names, scripts, data formats, and implementation details.
4. Split the method into at most five modules. Prefer modules with separable contracts:
   - data/protocol formatting
   - retrieval/tool adapter
   - core algorithm loop
   - refinement/compression component
   - evaluation/recovery harness
5. For each module, write a markdown document describing:
   - purpose
   - inputs and outputs
   - paper insight
   - algorithm or workflow
   - edge cases
   - test strategy
   - evidence from paper and repo
6. Write `module_plan.json` and validate it with `scripts/validate_module_plan.py`.

## Cross-Module Contract Checks

While modularizing, identify which module outputs are consumed by later modules. State negative constraints explicitly in the module docs. Examples:

- A retrieval adapter returns evidence documents, not final answers.
- A document-refinement module returns concise evidence, not answer directives.
- A rollout controller records raw model generations and extracted final answers separately.
- An evaluation module owns answer extraction/canonicalization, not the retrieval or refinement module.

## Module Plan Schema

Use this structure:

```json
{
  "schema_version": 1,
  "paper_id": "short_slug",
  "title": "Paper title",
  "fast_recovery_target": {
    "dataset": "dataset name",
    "split": "split or subset",
    "metric": "metric name",
    "paper_value": 0.0,
    "proxy": true,
    "rationale": "why this is a faithful fast recovery"
  },
  "modules": [
    {
      "id": "stable_module_id",
      "name": "Human readable module name",
      "skill_name": "operating-skill-directory-name",
      "summary": "One sentence.",
      "inputs": ["input contract"],
      "outputs": ["output contract"],
      "insight": "The paper idea preserved by this module.",
      "test_strategy": "How create-paper-module-skill should test it.",
      "evidence": ["paper section, figure, table, or repo path"]
    }
  ]
}
```

## Acceptance Criteria

- `modules` length is between 1 and 5.
- Every module has a stable snake_case `id` for artifact filenames and a unique
  canonical lowercase-hyphen `skill_name` of at most 64 characters for the
  generated operating skill directory and frontmatter name.
- The plan covers the main paper method and the chosen recovery experiment.
- The split avoids thin modules that only wrap one helper unless the helper is a distinct paper contribution.
- The recovery target is explicit enough for `recover-paper-result` to run without the source repository.

## Scripts

- `scripts/extract_paper_text.py`: extract text from a PDF or copy text from a plain text file.
- `scripts/validate_module_plan.py`: validate `module_plan.json` and optional module docs.
