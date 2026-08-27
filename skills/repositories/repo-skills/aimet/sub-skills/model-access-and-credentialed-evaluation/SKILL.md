---
name: model-access-and-credentialed-evaluation
description: "Handle AIMET model downloads, Hugging Face tokens, GitHub Actions
  scorecard runs, AWS/S3 checkpoints, caches, and benchmark-result
  comparability."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# AIMET model access and credentialed evaluation

Use this sub-skill when a task involves Hugging Face model or dataset access, gated checkpoints, `HF_TOKEN`, `gh`-dispatched GenAI scorecards, S3 export downloads, AWS/SAML credentials, cached FP/recipe/model outputs, metric scoring versions, or comparing GenAILab results.

## Read/run first

- Read [model access and credentialed evaluation](../../references/model-access-and-credentialed-evaluation.md) for token, cache, online-run, S3, and metric-comparability rules.
- Read [GenAILab workflows](../../references/genai-lab.md) for config and scorecard execution details.
- Run [genai_config_preflight.py](../../scripts/genai_config_preflight.py) before using credentials on a long run.
- Use [download_genai_checkpoint.sh](../../scripts/download_genai_checkpoint.sh) for S3 checkpoint downloads without depending on the original repo script.
- Use [genai_results_summary.py](../../scripts/genai_results_summary.py) to inspect `profiling_data.json` and identify metric `scoring_version` comparability warnings without rerunning benchmarks.

## Core workflow

1. **Identify the credential boundary.** Hugging Face tokens, GitHub CLI auth, AWS credentials, SAML app IDs, and AI Hub/QNN auth are separate concerns.
2. **Validate config without secrets.** Do a dry preflight before calling remote services or launching benchmark downloads.
3. **Use explicit caches.** Set FP cache, recipe cache, model cache, export dir, and results dir when the run will be repeated or compared.
4. **Preserve scoring semantics.** Compare metric results only when metric names and `scoring_version` match.
5. **Download artifacts safely.** Validate S3 URL shape, profile, and destination before copying/exporting checkpoint zips.
6. **Avoid leaking credentials.** Never write tokens into config files, generated artifacts, shell history snippets, or user-visible logs.

## Boundaries

- Route local GenAILab recipe design to [genai-lab](../genai-lab/SKILL.md).
- Route cluster execution to [cluster-pod-workflows](../cluster-pod-workflows/SKILL.md).
- Route Qualcomm AI Hub/QNN compile/profile/inference jobs to [qualcomm-sdk-deployment](../qualcomm-sdk-deployment/SKILL.md).

## Expected answer shape

For credentialed evaluation tasks, include the required credential type, how to verify it without exposing secrets, cache/result paths, whether the run is local or online, how artifacts are downloaded or merged, and the result-comparability constraints.
