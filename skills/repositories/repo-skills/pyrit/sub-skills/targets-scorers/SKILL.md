---
name: targets-scorers
description: "Configure PyRIT prompt targets, target capabilities, scorers,
  score aggregation, and target/scorer troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Targets and Scorers

Use this sub-skill when you need to:

- choose and configure a prompt target
- reason about target capabilities, modalities, auth, and rate limits
- choose or compose scorers
- aggregate, threshold, or batch score results
- debug credential, endpoint, browser, model, JSON, or modality failures

## Start here

- [Targets and scorers reference](references/targets-scorers-reference.md)
- [API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [Offline smoke script](scripts/target_scorer_smoke.py)

## Fast routing

- Offline dry run, logging, or manual prompt capture: `TextTarget`
- OpenAI / Azure OpenAI / OpenAI-compatible services: `OpenAIChatTarget`, `OpenAIResponseTarget`, `OpenAICompletionTarget`
- Raw HTTP or API-style endpoints: `HTTPTarget`, `HTTPXAPITarget`
- Browser or web UI workflows: `PlaywrightTarget`, `PlaywrightCopilotTarget`, `WebSocketCopilotTarget`
- Provider fan-out or load balancing: `LiteLLMChatTarget`, `RoundRobinTarget`
- Local model / torch / download-heavy workflows: `HuggingFaceChatTarget`
- Exact or regex detectors: `SubStringScorer`, `RegexScorer`
- LLM-guided judgment: `SelfAsk*` scorers, `LlamaGuardScorer`, `ShieldGemmaScorer`
- Aggregation, thresholding, and memory-backed evaluation: `TrueFalseCompositeScorer`, `FloatScaleThresholdScorer`, `BatchScorer`, `pyrit.analytics`

## Boundaries

- For memory and configuration bootstrap, use [setup-memory-core](../setup-memory-core/SKILL.md).
- For attacks and scenarios that consume targets and scorers, use [attacks-scenarios](../attacks-scenarios/SKILL.md).
- For converters and datasets that shape target input, use [converters-datasets](../converters-datasets/SKILL.md).
- For scanner/backend commands, use [cli-backend-scanner](../cli-backend-scanner/SKILL.md).

## Operating rule

1. Pick the smallest target family that fits the endpoint or workflow.
2. Check capabilities before assuming the target can accept a modality or conversation shape.
3. Prefer local scorers when the signal is lexical or rule-based.
4. Use LLM-backed scorers only when the judgment needs model reasoning.
5. Keep live-service checks separate from the offline smoke script.

## Bundled files

- [references/targets-scorers-reference.md](references/targets-scorers-reference.md)
- [references/api-reference.md](references/api-reference.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/target_scorer_smoke.py](scripts/target_scorer_smoke.py)
