# Contribution and case-study structure

DeepAnalyze accepts contributions to code, model assets, UI/deployment support, and user case studies. This reference focuses on the contribution patterns a future agent should preserve when preparing a change or a case-study folder.

## Code and model contributions

Appropriate contribution categories include:

- bug fixes or improvements to DeepAnalyze code;
- Docker packaging and deployment improvements;
- model conversion or quantization workflows;
- workflows that make DeepAnalyze usable with closed-source LLM providers;
- UI and demo improvements;
- documentation that clarifies reproducible usage.

Before preparing a pull request:

1. Identify the exact subsystem: API/client, frontend, model serving, training/evaluation, or examples.
2. Keep unrelated refactors out of the change.
3. Include a minimal reproduction or smoke command when possible.
4. Avoid committing local checkpoints, API keys, downloaded benchmark data, generated caches, or private paths.
5. State whether the change was CPU-only inspected, GPU-tested, model-tested, or benchmark-tested.

## Case-study contribution layout

A case study should live in a new folder under the repository's `example/` area. Use a descriptive lowercase folder name, for example:

```text
example/my_case_study/
  data/
    input-file-1.csv
    input-file-2.xlsx
  prompt.txt
  README.md
```

Required parts:

- `data/`: the uploaded files or a small reproducible sample. Do not include sensitive raw data.
- `prompt.txt`: the user instruction exactly as DeepAnalyze should receive it.
- `README.md`: a readable case report.

Recommended `README.md` sections:

```text
# Case title

## Input
- Files supplied
- Prompt summary or full prompt

## DeepAnalyze output
- Final answer/report
- Generated charts or files, if safe to include

## Comparison baseline (optional)
- Output from another LLM or tool
- Screenshots are acceptable if text output is unavailable

## Evaluation and comments
- What DeepAnalyze did well
- What it missed or did worse than a stronger closed-source model
- Suggestions for improving DeepAnalyze

## Reproduction notes
- Model or API surface used
- Any important settings such as max rounds or file preprocessing
```

DeepAnalyze is an 8B model; case studies where it performs slightly worse than a closed-source LLM are still useful if the gap is clearly documented.

## Review checklist for case studies

- The prompt and data files are sufficient to reproduce the interaction.
- The case does not reveal private credentials, personal data, or local machine paths.
- Output claims are supported by attached data or a clear screenshot/quote.
- Generated files are small enough for review, or the README explains where they came from.
- The README separates the user's input, DeepAnalyze's output, optional baseline output, and the author's evaluation.
- If the case exposes a failure mode, it is framed as actionable feedback rather than a benchmark claim.

## When to route elsewhere

- If a case study requires API upload/download instructions, route to `api-and-clients`.
- If it requires launching a model endpoint, route to `model-serving`.
- If it requires WebUI, CLI, or Jupyter screenshots, route to `interactive-frontends`.
- If it is meant to become a formal benchmark run, use `benchmark-playgrounds.md` first.
