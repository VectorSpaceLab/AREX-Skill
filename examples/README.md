# DisCo Examples

This directory contains self-contained HTML exports of complete DisCo sessions
and reusable starter files for documented workflows. Clone or download the
repository, open an HTML file in a browser, and expand the tool calls you want
to inspect. No DisCo installation or network connection is required to read an
export.

## Creator

Creator examples are grouped by the workflow that produces the operating
skills.

### Repo-to-Skills

#### huggingface_hub Repository Skill

- [huggingface/huggingface_hub repository](https://github.com/huggingface/huggingface_hub)
- [Open the sanitized session](creator/repo-to-skills/disco-creator-huggingface_hub.html)
- [Browse the resulting skill](creator/repo-to-skills/artifacts/huggingface_hub/huggingface-hub/SKILL.md)
- [Read the artifact bundle](creator/repo-to-skills/artifacts/huggingface_hub/README.md)
- [Read the final skill report](creator/repo-to-skills/artifacts/huggingface_hub/review/final-skill-report.md)
- [Read the verification report](creator/repo-to-skills/artifacts/huggingface_hub/review/verification-report.json)

This session follows Creator as it scopes the `huggingface_hub` 1.29.0
repository, prepares and verifies an isolated inspection environment, uses a
first workflow plus missing-only recovery to draft five sub-skills, integrates
the verified graph, and records final review and native-test boundaries.

The accompanying artifact bundle contains the generated runtime skill,
sanitized routing and review summaries, machine-readable verification results,
and usability test cases. Private environment reports, raw native logs, source
checkouts, and temporary runtime state are intentionally excluded.

### Paper-to-Skills

The Paper2Skills Distiller turns an AI research paper into verified,
module-level skills for paper replication. Start from the
[Distiller TOML configuration](creator/paper-to-skills/distiller-run-config.toml),
which exposes the source-acquisition, recovery, runtime, iteration, and output
settings accepted by DisCo Creator.

From the repository root, copy the starter and edit at least
`workspace_root`, `paper_slug`, and `paper_source`. Set
`original_repo_source` to a local path, Git URL, `none`, or `unknown` as
appropriate:

```bash
cp examples/creator/paper-to-skills/distiller-run-config.toml \
  /absolute/path/to/distiller-run-config.toml

disco --creator -p "/skill:create-paper-skills Use Distiller to generate and verify paper-replication skills for each run in this config. config_path: /absolute/path/to/distiller-run-config.toml"
```

`paper_source` accepts a local PDF or text file, a direct PDF URL, an arXiv URL
or identifier, or a paper title. With the starter's default path settings,
generated skills are written under `<workspace_root>/<paper_slug>/skills/` and
final reports under
`<workspace_root>/<paper_slug>/distillation/reports/final/`. The starter asks
before expensive recovery work and before any final deployment that requires
approval.

See [DisCo Meta Skills](../docs/disco-meta-skills.md#use-meta-skills-in-disco)
for the common Creator entry points and [DisCo Workflows](../docs/disco-workflows.md#construct-paper-replication-skills)
for the complete source-resolution, recovery, validation, and deployment
contract.

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
