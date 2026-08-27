# Guardrail Catalog

Use this reference to choose the right built-in rail family, flow name, and supporting config for a guardrails application.

## Quick map

| Family | Typical flows | When to use | Common caveats |
| --- | --- | --- | --- |
| Content safety | `content safety check input`, `content safety check output`, `llama guard check input`, `llama guard check output` | Block or mask harmful, unsafe, or policy-violating content. | Prompt tasks and model types must line up; reasoning models need enough `max_tokens`. |
| Jailbreak protection | `jailbreak detection heuristics`, `jailbreak detection model` | Detect adversarial prompt attacks before the main model runs. | Heuristics can run in-process for testing, but production should use a configured server or model endpoint. |
| Topic control | `topic safety check input $model=topic_control` | Keep the conversation inside a defined domain. | The `topic_control` model type and matching prompt task are required. |
| PII / sensitive data | `mask sensitive data on input`, `mask sensitive data on output`, `mask sensitive data on retrieval`, `detect sensitive data on ...`, `gliner detect pii on ...`, `gliner mask pii on ...` | Protect personal or regulated data in user text, responses, or retrieved chunks. | Presidio needs extra packages and a spaCy model; GLiNER uses `rails.config.gliner` and may require an API key or local endpoint. |
| Self-check | `self check input`, `self check output`, `self check facts`, `self check hallucination` | Use the LLM itself to judge input/output safety or factuality. | Missing prompts fail at load time; output parsers matter; reasoning models need enough tokens. |
| Fact-checking / hallucination | `self check facts`, `alignscore check facts`, `patronus lynx check output hallucination` | Ground answers in evidence or judge hallucinations. | Requires relevant chunks, prompt tasks, or a hosted model depending on the chosen rail. |
| Agentic security | `injection detection` | Protect tool-using or agentic flows from code, SQL, template, or XSS injection. | YARA rules and reject/omit behavior need careful tuning. |
| Tool calling | `tool call validation`, `tool result validation` | Validate OpenAI-style tool calls and tool results. | IORails only; the rails do not execute tools. |
| Third-party rails | `activefence moderation on input/output`, `autoalign check input/output`, `clavata ...`, `guardrailsai check ...`, `fiddler ...`, `cleanlab trustworthiness`, `pangea ai guard ...`, `trend ai guard ...`, `ai defense inspect ...`, `hf classifier check ...`, `protect prompt`, `protect response` | Use a managed moderation or detector service. | Usually requires a service key, endpoint, or provider-specific package. |

## Content safety

Use content safety rails when you want a dedicated safety model to block or mask policy violations.

### Common config pattern

```yaml
models:
  - type: main
    engine: openai
    model: gpt-4o-mini
  - type: content_safety
    engine: nim
    model: nvidia/llama-3.1-nemoguard-8b-content-safety

rails:
  input:
    flows:
      - content safety check input $model=content_safety
  output:
    flows:
      - content safety check output $model=content_safety

prompts:
  - task: content_safety_check_input $model=content_safety
    content: |
      ...
  - task: content_safety_check_output $model=content_safety
    content: |
      ...
```

### Notes

- The `$model=...` reference in the flow must match a `models.type` entry.
- The matching prompt task must include the same `$model=...` suffix.
- If you use a reasoning safety model, give the prompt task enough `max_tokens` for both internal reasoning and the final verdict.
- Multilingual refusal messages are an optional feature and need the `multilingual` extra.

## Jailbreak protection

Use jailbreak detection to catch obvious prompt attacks before they reach the main model.

### Heuristics-based rail

```yaml
rails:
  input:
    flows:
      - jailbreak detection heuristics

  config:
    jailbreak_detection:
      server_endpoint: http://localhost:1337/heuristics
      length_per_perplexity_threshold: 89.79
      prefix_suffix_perplexity_threshold: 1845.65
```

### Model-based rail

```yaml
rails:
  input:
    flows:
      - jailbreak detection model

  config:
    jailbreak_detection:
      nim_base_url: http://localhost:8000/v1
      nim_server_endpoint: classify
      api_key_env_var: NVIDIA_API_KEY
```

### Notes

- In-process heuristics are intended for testing, not production.
- The jailbreak detector fails open when the detector cannot be reached.
- The YARA-based injection path is part of the same security family and typically needs the jailbreak extra or a direct YARA install.

## Topic control

Topic control rails keep conversations in a bounded subject area.

### Common config pattern

```yaml
models:
  - type: topic_control
    engine: nim
    model: nvidia/llama-3.1-nemoguard-8b-topic-control

rails:
  input:
    flows:
      - topic safety check input $model=topic_control

prompts:
  - task: topic_safety_check_input $model=topic_control
    content: |
      ...
```

### Notes

- Topic control is usually an input rail.
- The flow name, model type, and prompt task must all match exactly.
- If the prompt is missing, config loading fails immediately.

## PII and sensitive data

Choose between a prompt-free detector/masker or a model-backed GLiNER rail.

### Presidio-based rails

```yaml
rails:
  config:
    sensitive_data_detection:
      input:
        entities:
          - PERSON
          - EMAIL_ADDRESS
      output:
        entities:
          - PERSON
          - EMAIL_ADDRESS
      retrieval:
        entities:
          - PERSON
          - EMAIL_ADDRESS

  input:
    flows:
      - mask sensitive data on input
  output:
    flows:
      - mask sensitive data on output
  retrieval:
    flows:
      - mask sensitive data on retrieval
```

### GLiNER-based rails

```yaml
rails:
  config:
    gliner:
      server_endpoint: https://integrate.api.nvidia.com/v1/chat/completions
      api_key_env_var: NVIDIA_API_KEY
      threshold: 0.5
      input:
        entities:
          - first_name
          - last_name
          - email
          - phone_number
      output:
        entities:
          - first_name
          - last_name
          - email
          - phone_number

  input:
    flows:
      - gliner detect pii on input
  output:
    flows:
      - gliner mask pii on output
```

### Notes

- Presidio-based rails usually need `nemoguardrails[sdd]` plus the spaCy language model used by the detector.
- GLiNER rails can run against a hosted NVIDIA endpoint or a local deployment.
- `detect` rails block; `mask` rails rewrite the text in place.
- Retrieval flows protect KB chunks before they are added to the prompt.

## Self-check and hallucination/fact-checking

Use self-check rails when you want the model itself to judge user input, bot output, or factual grounding.

### Self-check input/output

```yaml
rails:
  input:
    flows:
      - self check input
  output:
    flows:
      - self check output

prompts:
  - task: self_check_input
    content: |
      ...
  - task: self_check_output
    content: |
      ...
```

### Fact-checking and hallucination

```yaml
rails:
  output:
    flows:
      - self check facts
      - self check hallucination

prompts:
  - task: self_check_facts
    content: |
      ...
  - task: self_check_hallucination
    content: |
      ...
```

### Notes

- Missing self-check prompts fail at config load.
- `self check facts` uses `$relevant_chunks` when available.
- `self check hallucination` can be used with or without KB evidence.
- Reasoning models need enough `max_tokens` to reach the final yes/no verdict.
- For stronger hallucination detection, consider AlignScore or Patronus Lynx-style rails.

## Tool calling

Use tool-calling rails when you want the engine to validate model-emitted tool calls and app-returned tool results.

```yaml
rails:
  tool_output:
    flows:
      - tool call validation
  tool_input:
    flows:
      - tool result validation
```

### Notes

- These rails run only on the IORails engine.
- They validate structure and linkage; they do not execute tools.
- The flow names are fixed. A typo disables the tool rail.
- Tool rails are intended for OpenAI chat-completions style function calls.

## Third-party rails

Third-party rails usually combine a provider-specific `rails.config.<provider>` block with one or more named flows.

Common families include:

- ActiveFence moderation
- AutoAlign
- Clavata
- Cleanlab trustworthiness
- CrowdStrike AIDR
- Fiddler safety / faithfulness
- GuardrailsAI validators
- Google Cloud text moderation
- HuggingFace classifier rails
- Pangea AI Guard
- Prompt Security
- Trend Micro AI Guard
- Cisco AI Defense
- Patronus API / Lynx

### General rules

- Treat every third-party rail as provider-specific until you have confirmed its config block and required env vars.
- If the rail needs an API key or endpoint, keep it in the config or environment, not in the prompt.
- Many third-party rails are input or output rails; a few also cover retrieval.
- Some hosted detectors are better suited to production than in-process fallback paths.

## Choosing a rail family

A good default sequence is:

1. Start with the smallest built-in rail that matches the problem.
2. Add a prompt-backed self-check only when a dedicated model is not enough.
3. Use a third-party rail when you need a managed service or a specialized detector.
4. Add tool-calling rails only when you need function-call structure validation.

If a config mixes several rail families, make sure each family has its own model, prompt, or provider settings before you test runtime behavior.
