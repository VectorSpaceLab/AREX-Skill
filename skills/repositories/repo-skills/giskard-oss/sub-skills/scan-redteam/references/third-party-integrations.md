# Third-Party Scan Integrations

## Purpose

Use this reference when choosing between native Giskard scan generation and
external scanner bridges. All integrations return `giskard.checks.SuiteResult`,
so result interpretation stays in [checks-evals](../../checks-evals/SKILL.md).
Provider configuration and default generator credentials stay in
[llm-providers](../../llm-providers/SKILL.md).

## Discovery Commands

```python
from giskard.scan import list_scan_items

list_scan_items("giskard")                         # built-in scenario generator names
list_scan_items("garak")                           # active garak probe plugin names
list_scan_items("garak", include_inactive=True)    # active + inactive garak probes
list_scan_items("deepteam")                        # supported vulnerability + attack names
```

`list_scan_items("garak")` requires the garak optional extra. `list_scan_items("deepteam")`
requires the deepteam optional extra. `list_scan_items("lidar")` is not a public
listing API; lidar is only reachable through `third_party_scan(tool="lidar")` in
environments where the private lidar package is installed.

## Integration Matrix

| Tool | Install / availability prerequisite | Main API options | Provider/network expectations | Skip behavior |
| --- | --- | --- | --- | --- |
| Native Giskard | `giskard-scan` or a root install that includes scan support. | `vulnerability_scan`, `quality_scan`, `generate_suite`, native generator registries. | Many generators and checks need the Giskard default generator/provider; Hugging Face dataset generators need network or cache. | Empty knowledge bases, single-turn filtering, unsupported languages, and HF outages can produce warnings or empty scenario lists. |
| garak | Install `giskard-scan[garak]`; the importable package must include garak plugin discovery. | `third_party_scan(target, tool="garak", description=..., probes=None | "all" | list[str], target_mode=...)`. `description` is required by the API but garak ignores it. | The target is called concurrently from worker threads. Some detectors need external API keys; LLM-judge detectors use Giskard's default generator instead of a separate garak OpenAI key. | Unknown, inactive, or unloadable probes become skip scenarios. Missing detector API keys become skip check results with the missing key in details. Broken probes become error scenarios instead of silently disappearing. |
| deepteam | Install `giskard-scan[deepteam]`. | `third_party_scan(target, tool="deepteam", description=..., vulnerabilities=None | list[str], attacks=None | list[str], attacks_per_vulnerability_type=1, target_mode=...)`. | Requires a working Giskard default generator/provider; there is no keyless deepteam mode. Cost scales with vulnerability subtypes × attacks × `attacks_per_vulnerability_type`. | Unknown vulnerabilities/attacks become skip scenarios. `target_mode="singleturn"` filters multi-turn attacks into skip scenarios. If no valid attack/vulnerability remains, the result contains only skip scenarios or is empty. |
| lidar | Private Giskard package, not a normal PyPI extra. The environment must already have lidar and its runtime dependencies installed. | `third_party_scan(target, tool="lidar", description=..., languages=None | list[str], probes=None | list[str], tags=None | list[str], target_mode=...)`. | Requires the private scanner and a default generator/provider. It may run its own scan executor and target tracking. | `target_mode="singleturn"` filters lidar probes tagged as multi-turn. If filtering removes every requested probe, the adapter returns an empty `SuiteResult`. Missing lidar raises `ImportError`. |

## garak Workflow

Use garak when the user explicitly wants garak probes or detector-specific
coverage. Keep the first run bounded; `probes="all"` can be broad and slow.

```python
import asyncio
from giskard.scan import third_party_scan

async def target(inputs: str) -> str:
    return await call_my_agent(inputs)

async def main() -> None:
    result = await third_party_scan(
        target,
        tool="garak",
        description="Support assistant for account questions.",
        probes=["probes.goodside.ThreatenJSON"],
        target_mode="singleturn",
    )
    print(result.passed_count, result.failed_count, result.skipped_count)

asyncio.run(main())
```

Operational notes:

- `probes=None` uses a curated default set aligned with common red-team themes:
  bias/toxicity, PII leakage, misinformation, prompt leakage, jailbreak or
  injection, and data exfiltration.
- `probes="all"` attempts every active loadable garak probe. Prefer an explicit
  list when debugging one family of failures.
- Garak probes run in a dedicated thread pool with a capped worker count. The
  target must be safe to invoke concurrently, and async targets must not rely on
  thread-local state unless the wrapper manages it.
- Garak judge detectors are wired to Giskard's default generator. Configure the
  Giskard provider once, instead of setting separate garak judge credentials.
- Non-judge detectors may still require their own service keys. For example,
  Perspective-backed detectors need `PERSPECTIVE_API_KEY`; without it they
  produce skip results rather than aborting the whole scan.

## deepteam Workflow

Use deepteam when the user wants DeepTeam vulnerability/attack taxonomies and is
ready to run LLM-generated attacks plus LLM judging.

```python
import asyncio
from giskard.scan import third_party_scan

async def target(inputs: str) -> str:
    return await call_my_agent(inputs)

async def main() -> None:
    result = await third_party_scan(
        target,
        tool="deepteam",
        description="Support assistant for account questions.",
        vulnerabilities=["Bias", "Toxicity"],
        attacks=["PromptInjection", "Roleplay"],
        attacks_per_vulnerability_type=1,
        target_mode="singleturn",
    )
    print(result.failed_count, result.skipped_count)

asyncio.run(main())
```

Supported vulnerability names include `Bias`, `Toxicity`, `PIILeakage`,
`PromptLeakage`, and `Misinformation`. Supported attack names include the
single-turn attacks `PromptInjection`, `Roleplay`, `Leetspeak`, and `ROT13`, and
the multi-turn attacks `LinearJailbreaking`, `CrescendoJailbreaking`,
`TreeJailbreaking`, `SequentialJailbreak`, and `BadLikertJudge`.

Operational notes:

- Omit `vulnerabilities` or `attacks` for curated defaults; pass an empty list
  only when you intentionally want no items from that side.
- `attacks_per_vulnerability_type` must be a positive integer.
- DeepTeam uses the supplied `description` as the target purpose. Write a
  concise but realistic description; vague target purpose weakens attack
  selection and judging.
- Multi-turn attacks are skipped in `target_mode="singleturn"`; inspect skipped
  scenario messages instead of treating the pass rate alone as the verdict.

## lidar Workflow

Use lidar only when the environment already has the private lidar scanner and
the user asks for it. Do not make lidar a base prerequisite for Giskard scan
workflows.

```python
import asyncio
from giskard.scan import third_party_scan

async def target(inputs: str) -> str:
    return await call_my_agent(inputs)

async def main() -> None:
    result = await third_party_scan(
        target,
        tool="lidar",
        description="Support assistant for account questions.",
        languages=["en"],
        probes=["deepset-injection:1.0"],
        target_mode="singleturn",
    )
    print(result)

asyncio.run(main())
```

Operational notes:

- Lidar is private and not listed by `list_scan_items`; discover probe IDs from
  the user's installed lidar package or user-supplied scanner configuration.
- `target_mode="singleturn"` resolves the requested lidar probes and drops those
  tagged as multi-turn. If no probes remain, the adapter returns an empty
  `SuiteResult` without calling the scanner.
- Missing lidar raises `ImportError` explaining that lidar is private and must
  be installed separately.

## Choosing the Right Tool

- Prefer native `vulnerability_scan` when the user wants Giskard's built-in
  vulnerability generators, prompt-injection datasets, and `commercial_use`
  filtering.
- Prefer native `quality_scan` when the user has RAG documents and wants
  hallucination/retrieval/history quality scenarios.
- Prefer `third_party_scan(tool="garak")` when the user names garak probes,
  detector behavior, or garak catalog coverage.
- Prefer `third_party_scan(tool="deepteam")` when the user names DeepTeam
  vulnerabilities/attacks or wants that taxonomy.
- Use `tool="lidar"` only for environments with the private scanner already
  installed and explicitly requested.
