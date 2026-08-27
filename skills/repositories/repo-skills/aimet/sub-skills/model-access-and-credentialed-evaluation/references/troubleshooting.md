# Model access and credentialed evaluation troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Hugging Face model download fails with 401/403 | Missing token, gated model terms not accepted, or wrong account | Verify `HF_TOKEN` is present without printing it, run `hf auth whoami`, and accept model terms in the account UI. |
| GenAILab online run ignores local changes | `--online` dispatches GitHub Actions on a branch/ref and uses pushed code | Commit/push the change or run locally/pod-side instead. |
| `gh` workflow dispatch fails | GitHub CLI not installed/authenticated or workflow unavailable on branch | Run `gh auth status`, verify the branch contains the workflow, and use `--branch` explicitly. |
| S3 checkpoint download fails | Missing AWS profile/credentials, expired SAML session, wrong bucket URL, or no permissions | Run `aws sts get-caller-identity --profile <profile>`, refresh SAML login, and validate URL shape with the bundled downloader's `--dry-run`. |
| GenAILab summary warns about mixed metric versions | Results were produced under different scoring semantics | Compare only matching `scoring_version`; rerun the baseline under the current version when comparing. |
