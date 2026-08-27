# Scan Troubleshooting

## Purpose

Use this reference when `giskard.scan` setup, suite generation, target execution,
knowledge-base workflows, dataset loading, or optional scanner integrations fail
or return mostly skipped/empty results.

## Start With Safe Inspection

Run the bundled helper from the sub-skill directory or by path from any current
working directory:

```bash
python scripts/inspect_scan_api.py
```

If this fails to import `giskard.scan`, fix installation before debugging live
scans. If it succeeds but reports optional scanners as unavailable, native
Giskard scans can still work; only garak/deepteam/lidar workflows are affected.

## Missing Default Generator or Provider Credentials

Symptoms:

- Scan generation or execution fails when an `LLMGenerator`, `LLMJudge`,
  `Conformity`, embeddings, or quality recommendation runs.
- Errors mention a missing provider SDK, missing API key, unsupported model,
  authentication failure, rate limit, or default generator/provider setup.
- DeepTeam fails immediately because it has no keyless mode.

Likely cause:

- Many scan scenarios are LLM-backed. Native prompt-injection and Hugging Face
  dataset generators may load scenarios without a provider, but running those
  scenarios still invokes LLM-backed interactions or checks. Quality generators
  may also need embeddings during knowledge-base retrieval.

Recovery:

1. Decide which provider/model should back Giskard's default generator and any
   embedding model.
2. Install the needed provider extra or SDK.
3. Set provider credentials in environment variables such as `OPENAI_API_KEY`,
   `GOOGLE_API_KEY` or `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, or the Azure
   OpenAI endpoint/key variables required by the provider.
4. Verify provider routing using [llm-providers](../../llm-providers/SKILL.md)
   before rerunning an expensive scan.
5. For exploratory scans, use `return_exception=True`, small `max_scenarios`,
   and `parallel=False` so configuration errors are easier to isolate.

Stop if the user cannot provide credentials and the selected workflow requires
live generation/judging. Offer a no-live-call plan, `list_scan_items`, or the
bundled inspection script instead.

## Empty or Missing Knowledge Base

Symptoms:

- `quality_scan received no knowledge base; knowledge-base quality scenarios will be skipped.`
- `quality_scan received an empty knowledge base; knowledge-base quality scenarios will be skipped.`
- `KnowledgeBase must contain at least one non-empty document`.
- A quality scan returns an empty result or only a recommendation/report with no
  generated scenarios.

Likely cause:

- `knowledge_base=None`, an empty list, or only whitespace documents were passed.
- A bare string was passed where a `list[str]` was expected.
- `target_mode="singleturn"` skipped multi-turn quality generators, or there
  were too few documents for multi-topic scenarios.

Recovery:

1. Pass `KnowledgeBase.from_texts([...])` or a `list[str]` with at least one
   non-empty chunk. Do not pass a single raw string.
2. Prefer multiple focused chunks for RAG quality scans. `MultiTopicScenarioGenerator`
   needs at least two documents.
3. Keep `target_mode="multiturn"` unless the target is genuinely single-turn.
4. If embeddings fail, configure a provider-capable embedding model or supply
   `Document(content=..., embeddings=[...])` with valid finite, non-zero vectors
   of consistent dimensionality.
5. If the goal is only to inspect APIs, run `scripts/inspect_scan_api.py`; it
   builds a tiny `KnowledgeBase` without computing embeddings.

## Target Concurrency or State Failures

Symptoms:

- Flaky failures appear only with `parallel=True`.
- Scenarios contaminate one another's conversation history.
- A local service, database, file, cache, or provider rate limit fails under
  concurrent calls.
- Garak scans appear to call the target from unexpected threads.

Likely cause:

- Scan helpers default to `parallel=True` for suite execution. `max_concurrency=None`
  means there is no explicit Giskard cap. Garak also runs probes through worker
  threads, and third-party scanners may own their own execution model.

Recovery:

1. Rerun with `parallel=False` for native `quality_scan`/`vulnerability_scan`.
2. If parallel execution is required, set `max_concurrency` to a conservative
   value and increase only after target traces remain isolated.
3. Ensure every scenario gets fresh conversation/session state. Do not store
   current conversation state in a shared global without a scenario/session key.
4. Protect local files, caches, or mutable clients with locks or per-scenario
   instances.
5. For agent workflow target wrappers, review state handling in
   [agents-workflows](../../agents-workflows/SKILL.md).

## Hugging Face Dataset and Network Issues

Symptoms:

- `HuggingFaceDatasetScenarioGenerator` returns no scenarios.
- Warnings mention Hub outage, unavailable language subsets, local-entry-not-found,
  offline mode, proxy errors, or HTTP 502/503/504.
- A scan unexpectedly skips Hugging Face-backed generators in offline CI.

Likely cause:

- Remote dataset metadata or files are unavailable, the requested language subset
  is absent, network/proxy settings block Hugging Face Hub, or the environment is
  in offline mode.

Recovery:

1. Confirm whether network access is allowed for this task. If not, use bundled
   local generators such as `PromptInjectionScenarioGenerator` or prebuilt suites.
2. Check that requested language codes match dataset subsets, usually BCP-47
   style values such as `"en"`.
3. Use a small `max_scenarios` and explicit generator list while debugging.
4. Treat a zero-scenario result from a dataset generator as an operational skip,
   not as proof that the target is safe.

## Commercial-Use Flags and Dataset Licensing

Symptoms:

- Vulnerability scan produces fewer scenarios than expected when
  `commercial_use=True`.
- Expected dataset-backed generators are absent from the generated suite.

Likely cause:

- `commercial_use=True` filters the vulnerability registry to generators whose
  `allow_commercial_use` property is true. Generators backed by datasets marked
  non-commercial are excluded.

Recovery:

1. Ask whether the scan output will be used commercially before selecting the
   flag.
2. Use `commercial_use=True` for commercial contexts and document that some
   datasets will be skipped.
3. Use `commercial_use=False` only when non-commercial dataset use is acceptable
   for the user's context.
4. For explicit Hugging Face generators, set `repo_allow_commercial_use` based
   on the dataset's terms and the user's policy; do not assume the flag is legal
   approval.

## garak Missing Extra, Probes, and Detectors

Symptoms:

- `ImportError: garak is not installed. Run: pip install giskard-scan[garak]`.
- `list_scan_items("garak")` fails.
- Requested garak probes return skipped scenarios.
- Check details mention missing detector keys such as `PERSPECTIVE_API_KEY`.

Likely cause:

- The garak extra is missing, the probe name is unknown/inactive/unloadable, a
  detector plugin failed to load, or a detector needs an API key. Garak judge
  detectors use Giskard's default generator; other detectors can have their own
  service-key requirements.

Recovery:

1. Install the optional extra for a garak workflow: `pip install giskard-scan[garak]`.
2. Use `list_scan_items("garak")` to choose active probe names. Use
   `include_inactive=True` only when diagnosing catalog availability.
3. Prefer a small explicit `probes=[...]` list before `probes="all"`.
4. Inspect skipped scenario/check details. Unknown, inactive, load-failed, and
   missing-key cases are intentionally surfaced as skips rather than dropped.
5. Configure Giskard's default generator for judge detectors and set detector-
   specific service keys only for detectors that require them.
6. If target calls are flaky under garak, make the target thread-safe or narrow
   the probe set; garak probes are run concurrently through a capped worker pool.

## deepteam Missing Extra, Names, or Credentials

Symptoms:

- `ImportError: deepteam is not installed. Run: pip install giskard-scan[deepteam]`.
- DeepTeam scan fails due to missing default generator/provider credentials.
- Unknown vulnerabilities or attacks become skipped scenarios.
- `target_mode="singleturn"` yields skips for multi-turn attacks.
- `attacks_per_vulnerability_type` validation fails.

Likely cause:

- The optional extra is missing, Giskard's default generator is not configured,
  item names do not match the integration maps, single-turn filtering removed
  multi-turn attacks, or `attacks_per_vulnerability_type` is not a positive int.

Recovery:

1. Install `giskard-scan[deepteam]` only when the user selects deepteam.
2. Configure provider credentials before running; deepteam has no keyless mode.
3. Use `list_scan_items("deepteam")` to get supported names.
4. Keep `attacks_per_vulnerability_type=1` for initial runs; cost scales quickly.
5. Read skipped scenario messages. Skips are part of the result and should be
   reported alongside pass/fail counts.

## lidar Missing Private Scanner or Filtered Probes

Symptoms:

- `ImportError` says lidar is not installed and is a private Giskard package.
- `list_scan_items("lidar")` raises `ValueError` because lidar is not a public
  listing tool.
- `third_party_scan(tool="lidar", target_mode="singleturn", ...)` returns an
  empty result without calling the scanner.

Likely cause:

- The private lidar dependency is absent, the environment lacks access to it, or
  all requested probes were multi-turn and filtered out for a single-turn target.

Recovery:

1. Use lidar only if the user already has the private scanner installed and asks
   for it explicitly.
2. Get probe IDs or tags from the user's installed lidar environment or
   configuration; do not rely on `list_scan_items`.
3. If single-turn filtering removes every probe, either select single-turn lidar
   probes or rerun with `target_mode="multiturn"` only if the target truly
   supports multi-turn conversations.
4. If lidar is unavailable, choose native Giskard, garak, or deepteam according
   to [third-party integrations](third-party-integrations.md).

## Empty, Skipped, or Misleading Results

Symptoms:

- `SuiteResult` has no scenarios.
- `skipped_count` is high.
- Pass rate looks high even though many requested probes/checks skipped.

Likely cause:

- Empty knowledge base, unsupported language subsets, single-turn filtering,
  missing optional extras, unknown scanner items, missing detector keys, or a
  deliberately empty custom registry.

Recovery:

1. Always report counts for passed, failed, errored, and skipped results.
2. Inspect skip messages and details before summarizing risk.
3. Group by a meaningful key: `"threat-type"` for vulnerability scans,
   `"component"` for quality scans, or another annotation/tag key if the suite
   was custom-generated.
4. Treat a run with all skips or no scenarios as inconclusive. Fix prerequisites
   or narrow the scan plan instead of claiming the target passed.
