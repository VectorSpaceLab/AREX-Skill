# PEFT Repo Development Troubleshooting

## Missing Maintainer Approval

Symptom: The user wants to implement a new feature, claim an issue, or add a new method but cannot point to approval or assignment.

Action:

- Stop PR-oriented coding until the user coordinates with maintainers.
- Ask for an issue link, approval comment, or assignment confirmation.
- For new features or new PEFT methods, recommend a proposal issue first.
- Do not prepare a duplicate PR if an existing PR or assignee already covers the work.

## Duplicate PR or Issue Ownership

Symptom: Search shows an open PR or assigned issue for the same fix.

Action:

- Do not open another PR for the same scope.
- Suggest reviewing or testing the existing PR, or ask maintainers whether a separate approach is wanted.
- If the new work is broader, clearly separate scope and reference the overlap in the proposal.

## AI-Assisted PR Disclosure Missing

Symptom: The PR plan omits AI assistance disclosure or shifts responsibility to the agent.

Action:

- Warn that breaching PEFT's agent contribution guidelines can result in automatic banning.
- Add a PR note that AI assistance was used.
- Ensure the human contributor reviews every line and can explain the implementation.
- Include the issue/approval link and test results.

## Wrong Ruff Version

Symptom: `make quality` or `make style` disagrees with CI, or formatting changes unrelated files.

Action:

- Check that ruff satisfies `~=0.15.12`.
- Reinstall development dependencies with the PEFT test or quality extras.
- Undo unrelated formatter churn before committing.
- Prefer `make quality` before `make style` when diagnosing whether tools are misconfigured.

## Broad Formatter Churn

Symptom: Running style modifies files unrelated to the patch.

Action:

- Treat unrelated churn as a tooling/environment problem or stale checkout symptom.
- Revert unrelated changes.
- Re-run focused style after confirming tool versions.
- Do not include drive-by formatting in PEFT PRs.

## Unsupported Python or Transformers Compatibility

Symptom: A change uses newer Python syntax, assumes a newer Transformers API, or fails on older supported versions.

Action:

- Keep Python `>=3.10` compatibility.
- Add compatibility guards for Transformers behavior that changed across supported versions.
- Prefer existing PEFT compatibility utilities and patterns.
- Add tests covering the fallback path when practical.

## Missing Tests for a Bug Fix

Symptom: A bug fix changes behavior without a regression test.

Action:

- Add a test that fails on the old behavior and passes with the fix when practical.
- Place the test in the existing test file that owns that behavior.
- For GPU-only failures, use PEFT's GPU test files and markers.
- If no automated test is feasible, document the reason and provide a manual reproduction in the PR.

## Missing Docs for a New Method or Public API

Symptom: A method/config field is public but absent from package reference docs or examples.

Action:

- Add package reference documentation.
- Register the docs page in the toctree.
- Include a short usage snippet and autodoc blocks.
- Compare with nearby methods when users could confuse the capabilities.

## New Method Registration Fails

Symptom: Importing PEFT raises errors about unknown PEFT type, duplicate method, duplicate prefix, or lowercase method names.

Action:

- Add the uppercase enum value to `PeftType`.
- Pass a lowercase unique `name` to `register_peft_method`.
- Use a unique adapter prefix.
- Export public classes from both tuner-level and top-level `__init__.py` files.
- Run mapping/import tests and a focused custom-model test.

## Focused Test Selector Runs Nothing

Symptom: Pytest reports all tests deselected.

Action:

- Broaden the selector or target a concrete test file.
- Use `tests/test_custom_models.py -k <method>` for tuner method coverage.
- For LoRA, include exclusions for similarly named methods but verify the expression still matches plain LoRA tests.
- Add missing tests if no test covers the changed behavior.
