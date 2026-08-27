# Proxy, SPL, Long-Context, Research, Search, and Code Plugins

## Proxy plugin

The proxy plugin load-balances and fails over across multiple LLM providers. It can be used directly (`proxy-model`) or as a wrapper around another approach via request config.

### Config template

Place provider configuration in the user-level OptiLLM config location used by the plugin, typically `~/.optillm/proxy_config.yaml`:

```yaml
providers:
  - name: primary
    base_url: https://api.openai.com/v1
    api_key: ${OPENAI_API_KEY}
    weight: 2
    max_concurrent: 5
    model_map:
      gpt-4: gpt-4-deployment
  - name: backup
    base_url: http://localhost:8080/v1
    api_key: dummy
    fallback_only: true
routing:
  strategy: weighted  # weighted, round_robin, or failover
timeouts:
  request: 30
  connect: 5
queue:
  max_concurrent: 100
  timeout: 60
```

Use `proxy_wrap`, `wrapped_approach`, or `wrap` to run another approach/plugin through proxy-selected providers:

```python
extra_body={"optillm_approach": "proxy", "proxy_wrap": "moa"}
```

## SPL plugin

System Prompt Learning stores and applies learned problem-solving strategies.

- Basic use: `spl-model`.
- Learning mode: `extra_body={"spl_learning": True}`.
- Strategy and metrics data are JSON files managed by the plugin.
- Learning mode can modify strategy storage, so treat it as stateful and review before enabling in shared deployments.

## LongCePO plugin

LongCePO handles very long contexts by planning and divide-and-conquer map/reduce processing.

Input format:

```text
<context text><CONTEXT_END><question>
```

The delimiter is configurable in the plugin's longcepo config. LongCePO is useful when context exceeds the base model's window, but it adds multiple provider calls and expects long-context text to be supplied in the prompt.

## DeepThink and Deep Research

- `deepthink` combines self-discover style reasoning structure with uncertainty-routed chain-of-thought.
- `deep_research` performs iterative research loops with web search/fetch/evaluation and report generation.

Both can be expensive and should be bounded with request config and explicit user approval when web access or long runs are involved.

## Web and URL tools

- `readurls` extracts URLs from the request and fetches webpage content.
- `web_search` uses Selenium/Chrome automation for Google search.

Use them only when external web access is intended. Expect SSL, browser-driver, CAPTCHA, rate-limit, and corporate-network issues.

## Code execution plugins

- `executecode` extracts and executes Python code when the request or model output asks for code execution.
- `coc` implements chain-of-code style extraction, execution, fixing, and simulation.

Treat both as unsafe for untrusted prompts unless the runtime is sandboxed. Do not grant filesystem/network access unless required and approved.

## Router plugin

The router plugin loads a classifier model to predict an OptiLLM approach. It may require model files or HuggingFace access. If a task is only about deterministic routing, prefer explicit model prefixes or `optillm_approach` over classifier routing.

## Compact plugin

The compact plugin estimates tokens, parses tagged conversations, compresses older turns with the LLM, and preserves recent turns. Configure thresholds and recent-turn retention through request config or environment variables, and expect extra provider calls when compression triggers.
