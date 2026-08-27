# Targets and Scorers API Reference

Use this reference when constructing or debugging PyRIT prompt targets and scorers. Signatures were verified from the installed package baseline.

## Target families

| Family | Representative classes | Use when | Notes |
|---|---|---|---|
| Offline/manual | `TextTarget` | Capture prompts to a stream or dry-run prompt normalization. | Safe for no-secret tests; does not represent live model behavior. |
| OpenAI/Azure OpenAI | `OpenAIChatTarget`, `OpenAIResponseTarget`, `OpenAICompletionTarget`, media targets | The target speaks an OpenAI-compatible API. | Requires endpoint/model/deployment/API key or identity. Check multimodal capabilities before sending media. |
| HTTP | `HTTPTarget`, `HTTPXAPITarget` | The system under test is an HTTP endpoint or form/API endpoint. | `HTTPTarget` lives in `pyrit.prompt_target.http_target.http_target`; validate request templates and response callbacks. |
| Browser/UI | `PlaywrightTarget`, `PlaywrightCopilotTarget`, `WebSocketCopilotTarget` | The surface is a web UI or Copilot-like browser session. | Requires browser/session/account setup and optional extras. |
| Provider abstraction | `LiteLLMChatTarget`, `RoundRobinTarget` | Route through multiple providers or load-balance compatible targets. | Keep capabilities and auth consistent across inner targets. |
| Local/model-download | `HuggingFaceChatTarget` | Run against a HuggingFace model interface. | Optional torch/model downloads; GPU may improve speed but is not a base requirement. |

Verified examples:

- `TextTarget(*, text_stream=stdout, custom_configuration=None)`.
- `OpenAIChatTarget(*, max_completion_tokens=None, temperature=None, top_p=None, frequency_penalty=None, presence_penalty=None, seed=None, n=None, audio_response_config=None, extra_body_parameters=None, custom_configuration=None, **kwargs)`.

## Capability and configuration objects

`TargetConfiguration`, `TargetCapabilities`, and target requirement helpers describe supported input/output modalities, multi-turn behavior, JSON/tool/audio support, and configuration policy. Before composing converters or scorers, verify that the target accepts the produced modality and conversation shape.

## Scorer families

| Family | Representative classes | Use when |
|---|---|---|
| Rule/regex | `SubStringScorer`, `RegexScorer` and security regex scorers | Exact, lexical, or known-pattern detection. |
| True/false self-ask | `SelfAskTrueFalseScorer`, refusal/question-answer scorers | Model judgment over a yes/no rubric. |
| Float/scale | `SelfAskScaleScorer`, Likert/numeric scorers, aggregators | Severity, quality, or risk scores. |
| Policy/model scorers | LlamaGuard, ShieldGemma, Azure content filter, Prompt Shield | Specialized safety/policy classifiers. |
| Batch/evaluation | `BatchScorer`, scorer evaluator/metrics classes | Apply scorers across memory results or compare scorer quality. |

Verified examples:

- `SubStringScorer(*, substring, text_matcher=None, categories=None, aggregator=..., validator=None)`.
- `SelfAskTrueFalseScorer(*, chat_target=None, system_prompt=None, question=None, response_handler=None, validator=None, score_aggregator=...)`.

## Composition rules

1. Choose a target for the surface under test; choose an adversarial/scorer target separately if needed.
2. Match `MessagePiece` data types and target capabilities before sending.
3. Use offline/rule scorers when the answer can be determined from text alone.
4. Use LLM-backed scorers only when the judgment requires model reasoning and a scorer target is configured.
5. Aggregators combine multiple score rows; they do not execute attack branching directly. Attack/executor logic consumes scorer results.

Run `scripts/target_scorer_smoke.py --json` for import/signature checks only. It does not verify live service credentials or model quality.
