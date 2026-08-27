# Contribution Policy for Model Extension

Transformers has mandatory agent contribution rules. Treat them as gating requirements, not optional etiquette.

## Agent Warning

Before coding or drafting PR-ready instructions, warn the human submitter:

> Breaching the Transformers agent contribution guidelines can result in automatic banning. A human submitter must understand, review, and be able to defend every changed line.

## Coordination Before Coding

If the work maps to an issue:

1. Read the issue and comments.
2. Confirm the issue author or a maintainer approved the submitter's work if the issue is not theirs.
3. Check for duplicate PRs.
4. Stop if approval is missing, ambiguous, or another PR already covers the same fix.

Required GitHub checks before PR-ready output:

```bash
gh issue view <issue_number> --repo huggingface/transformers --comments
gh pr list --repo huggingface/transformers --state open --search "<issue_number> in:body"
gh pr list --repo huggingface/transformers --state open --search "<short area keywords>"
```

Use area keywords such as model name, `model_type`, tokenizer class, processor class, pipeline task, or failing utility name.

## Fail-Closed Rules

Do not proceed to PR-ready output when:

- coordination evidence cannot be found
- the issue belongs to someone else and no maintainer or issue-author approval exists
- another open PR implements the same model, tokenizer, processor, pipeline, or auto mapping fix
- the requested edit is low-value busywork, such as a single typo or isolated cleanup
- the human cannot validate and explain an AI-assisted patch

If blocked, return a concise explanation naming the missing approval link, duplicate PR, or scope issue.

## AI-Assisted PR Accountability

A human submitter is responsible for reviewing every changed line and running relevant tests. PR descriptions for AI-assisted work must include:

- link to issue discussion and coordination or approval comment
- explanation of why the PR does not duplicate existing work
- test commands run and results
- clear statement that AI assistance was used

Do not open PRs, create branches, or commit changes unless the human explicitly asks for those local actions and coordination is already satisfied.

## Model-Extension Specific Ownership Signals

For model additions, look for:

- a `New model` issue or maintainer request
- comments assigning or approving the contributor
- no competing PR with the same model name, architecture, or model doc
- no competing PR touching the same auto mappings for the same model type

For pipeline additions, look for:

- task-level agreement that the task belongs in Transformers rather than as Hub custom code
- tests under the pipeline test suite
- a default model or documented reason no default is appropriate

For tokenizer or processor additions, look for:

- explicit model integration need
- clear fast/slow tokenizer plan
- auto mapping changes aligned with config `model_type`

## Local Checklist Script

Run the bundled local-only checklist to surface missing evidence without network calls:

```bash
python ../scripts/model_extension_checklist.py --repo . --model <model>
```

Use its `policy` section as a prompt for what must be verified manually or through the required `gh` commands before PR-ready output.
