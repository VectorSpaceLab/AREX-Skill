# Targets and Scorers Reference

This reference distills the PyRIT target, scorer, and analytics surface for offline configuration work.

## 1) Pick a target family

| Need | Use | Notes |
| --- | --- | --- |
| No-secret dry run, manual capture, or local logging | `TextTarget` | Writes the latest prompt to a text stream and returns no assistant response. Good smoke target for offline validation.
| OpenAI chat-style or Azure OpenAI deployments | `OpenAIChatTarget` | Text and image input, text output. Supports Azure-style Entra auth when the endpoint is recognized.
| OpenAI Responses API / tool calls / reasoning | `OpenAIResponseTarget` | Use when function-call and reasoning pieces matter.
| Legacy completion-style prompts | `OpenAICompletionTarget` | Text-only completion endpoint.
| Raw HTTP request capture or Burp-style requests | `HTTPTarget` | Use a raw request template and an optional response callback.
| API-mode file uploads or JSON/form requests | `HTTPXAPITarget` | Easier than raw HTTP when you already know the URL and body shape.
| Many providers through one interface | `LiteLLMChatTarget` | Optional dependency; useful when the provider is not OpenAI-native.
| Multiple same-class deployments with failover / weights | `RoundRobinTarget` | All inner targets must be the same concrete class and share the same configuration.
| Browser or app UI interaction | `PlaywrightTarget`, `PlaywrightCopilotTarget`, `WebSocketCopilotTarget` | Requires browser/runtime state and usually an authenticated page or websocket session.
| Local model downloads / torch inference | `HuggingFaceChatTarget` | Optional heavyweight path; can use CUDA when available.
| Classifier or safety-service endpoints | `PromptShieldTarget`, `AzureMLChatTarget`, `GandalfTarget` | Credential- and service-bound targets.

## 2) Capability rules

PyRIT target capability state lives in `TargetConfiguration`:

- `TargetCapabilities` declares what the target natively supports.
- `CapabilityHandlingPolicy` says what to do when a capability is missing.
- `ConversationNormalizationPipeline` is derived from the capability gap.

Key capability names:

- `supports_multi_turn`
- `supports_multi_message_pieces`
- `supports_editable_history`
- `supports_system_prompt`
- `supports_json_output`
- `supports_json_schema`
- `input_modalities`
- `output_modalities`

Default policy behavior in this PyRIT release:

- `MULTI_TURN` -> `RAISE`
- `SYSTEM_PROMPT` -> `RAISE`
- `JSON_SCHEMA` -> `ADAPT`

Use these helpers before you build an attack or scorer:

```python
from pyrit.prompt_target import CHAT_TARGET_REQUIREMENTS
from pyrit.prompt_target.common.target_capabilities import CapabilityName

CHAT_TARGET_REQUIREMENTS.validate(target=target)
target.configuration.ensure_can_handle(capability=CapabilityName.MULTI_TURN)
```

Use `TargetRequirements` when the consumer also needs input/output modalities.

## 3) Target configuration patterns

### OpenAI / Azure OpenAI

- Pass `model_name`, `endpoint`, and `api_key` explicitly, or use the target-specific env vars.
- Recognized Azure OpenAI / AI Foundry endpoints can fall back to Entra authentication automatically when no key is provided.
- Use `get_azure_openai_auth(endpoint)` when you want to supply a token provider yourself.
- The API-key and endpoint env vars are target-specific; common examples include `OPENAI_CHAT_*`, `OPENAI_RESPONSES_*`, `OPENAI_COMPLETION_*`, `OPENAI_IMAGE_*`, `OPENAI_TTS_*`, `OPENAI_VIDEO_*`, and `OPENAI_REALTIME_*`.

### HTTP targets

- `HTTPTarget` expects a raw request string.
- The placeholder string defaults to `{PROMPT}`.
- A callback function can parse the HTTP response into the final response text.
- `HTTPXAPITarget` is the simpler API-style alternative when you already know the URL and request body.

### Round-robin targets

`RoundRobinTarget` is only valid when:

- every inner target is the same concrete class
- every inner target has the same `TargetConfiguration`
- the inner targets support multi-turn and editable history
- weights, if present, are positive integers with the same length as the target list

Use it for load balancing or rate-limit spreading, not for mixing unrelated target families.

### Playwright targets

`PlaywrightTarget` and `PlaywrightCopilotTarget` need a live page object and a browser session. Treat the browser, account, and page lifecycle as external dependencies.

### Hugging Face targets

`HuggingFaceChatTarget` needs either `model_id` or `model_path`, not both. `model_id` usually needs a Hugging Face token; local `model_path` can avoid network downloads. CUDA is optional and should be treated as best-effort.

## 4) Pick a scorer family

| Need | Use | Notes |
| --- | --- | --- |
| Local exact text check | `SubStringScorer` | Fast, deterministic, no credentials.
| Local regex / keyword detector | `RegexScorer` and regex subclasses | Good for PII, jailbreak markers, and output leakage.
| Boolean LLM judgment | `SelfAskTrueFalseScorer` | Uses a chat target and a JSON response contract.
| Refusal detection | `SelfAskRefusalScorer` | Blocked responses short-circuit to `True`.
| Category classification | `SelfAskCategoryScorer` | Returns category labels when the response matches.
| 1-5 rubric scoring | `SelfAskLikertScorer` | Returns a normalized float-scale score.
| Custom numeric rubric | `SelfAskScaleScorer`, `SelfAskGeneralFloatScaleScorer` | Use when the built-in scale templates do not fit.
| Custom boolean rubric | `SelfAskGeneralTrueFalseScorer` | Use when the built-in templates do not fit.
| Threshold a float score into a boolean | `FloatScaleThresholdScorer` | Preserves the original float in metadata.
| Combine boolean scorers | `TrueFalseCompositeScorer` | `AND`, `OR`, or `MAJORITY`.
| Score many stored responses | `BatchScorer` | Reads from memory and batches scoring work.
| Hosted safety / classifier scorers | `AzureContentFilterScorer`, `PromptShieldScorer`, `LlamaGuardScorer`, `ShieldGemmaScorer` | Credentialed or endpoint-bound.
| Risk / overlap / leak scoring | `InsecureCodeScorer`, `PlagiarismScorer`, `SystemPromptExtractionScorer` | Useful offline or chat-target-backed.

## 5) Score data and aggregation

Scorers emit `Score` objects with:

- `score_type`: `true_false`, `float_scale`, or `unknown`
- `score_value`: string-encoded payload
- `score_category`: optional list of labels
- `score_rationale`: explanation text
- `score_metadata`: optional structured metadata

Aggregation rules to remember:

- `TrueFalseScoreAggregator.AND`, `.OR`, `.MAJORITY` combine boolean scores.
- `FloatScaleScoreAggregator.AVERAGE`, `.MAX`, `.MIN` combine float scores.
- `FloatScaleScorerByCategory` keeps category groups separate.
- `FloatScaleScorerAllCategories` folds categories together.
- `FloatScaleThresholdScorer` stores the original float score in metadata under `original_float_value`.
- Category lists are deduplicated and sorted when score aggregators combine results.

## 6) Evaluation and analytics

Use these when you need to summarize or compare scoring results:

- `pyrit.analytics.analyze_results(attack_results)`
- `pyrit.analytics.ConversationAnalytics(memory_interface=...)`
- `pyrit.analytics.get_cached_results_for_technique(...)`
- `BatchScorer.score_responses_by_filters_async(...)`

These are for post-run analysis, not live target configuration.

## 7) Debug loop

1. Verify the target class and its config first.
2. Confirm whether the failure is auth, endpoint, rate limit, modality, or schema related.
3. If the target is live-service bound, isolate it from offline scorers.
4. If the scorer is LLM-backed, check the response handler before changing the attack.
5. If the category result looks wrong, inspect aggregation rules before changing the scorer.
