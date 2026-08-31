# DisCo Examples

These self-contained HTML exports show complete DisCo sessions. Clone or
download the repository, open an HTML file in a browser, and expand the tool
calls you want to inspect. No DisCo installation or network connection is
required to read an export.

## Creator

### huggingface_hub Repository Skill

- [huggingface/huggingface_hub repository](https://github.com/huggingface/huggingface_hub)
- [Open the sanitized session](creator/disco-creator-huggingface_hub.html)
- [Browse the resulting skill](creator/artifacts/huggingface_hub/huggingface-hub/SKILL.md)
- [Read the artifact bundle](creator/artifacts/huggingface_hub/README.md)
- [Read the final skill report](creator/artifacts/huggingface_hub/review/final-skill-report.md)
- [Read the verification report](creator/artifacts/huggingface_hub/review/verification-report.json)

This session follows Creator as it scopes the `huggingface_hub` 1.29.0
repository, prepares and verifies an isolated inspection environment, uses a
first workflow plus missing-only recovery to draft five sub-skills, integrates
the verified graph, and records final review and native-test boundaries.

The accompanying artifact bundle contains the generated runtime skill,
sanitized routing and review summaries, machine-readable verification results,
and usability test cases. Private environment reports, raw native logs, source
checkouts, and temporary runtime state are intentionally excluded.

## Researcher

### vLLM vs SGLang: Qwen3.5-4B Serving Benchmark

- [vLLM repository](https://github.com/vllm-project/vllm)
- [SGLang repository](https://github.com/sgl-project/sglang)
- [Qwen3.5-4B model](https://huggingface.co/Qwen/Qwen3.5-4B)
- [Open the sanitized session](researcher/disco-researcher-vllm_sglang.html)
- [Read the curated benchmark report](researcher/artifacts/vllm_sglang/REPORT.md)
- [Browse the vLLM skill](../skills/repositories/repo-skills/vllm/SKILL.md)
- [Browse the SGLang skill](../skills/repositories/repo-skills/sglang/SKILL.md)

This session shows how Researcher uses repository skills to run an auditable
serving benchmark. `repo-skills-router` narrows the task to model deployment
and inference serving, then selects only the relevant vLLM and SGLang skills.

The vLLM skill guides server configuration, metrics, and bounded runtime tuning;
the SGLang skill guides startup, cache and scheduler settings, workload control,
GPU measurement, and framework-specific troubleshooting. Together, they keep
the model, workload, client, and hardware limits consistent across both
frameworks, while separating correctness checks from performance measurement.

The report records the resulting commands, versions, and evidence. Its runtime
comparison is an observation of this environment—not a performance claim about
the skills themselves.

## Sanitization

Some sensitive and environment-specific information has been sanitized from
the public exports while preserving the task, skill usage, execution flow, and
results needed to understand the examples.
