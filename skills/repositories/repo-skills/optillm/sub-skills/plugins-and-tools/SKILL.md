---
name: plugins-and-tools
description: "Configure and troubleshoot OptiLLM plugins, tool integrations,
  MCP, memory, privacy, JSON structured output, proxy load balancing, SPL,
  LongCePO, web search, and code execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Plugins and Tools

Use this sub-skill when a task involves OptiLLM plugins or tool integrations rather than only core approach algorithms.

## Read first for these tasks

- Enable or diagnose plugin slugs such as `mcp`, `memory`, `privacy`, `json`, `proxy`, `spl`, `longcepo`, `deepthink`, `deep_research`, `web_search`, `executecode`, `compact`, `coc`, `genselect`, `majority_voting`, `readurls`, or `router`.
- Configure MCP servers, memory persistence, privacy anonymization, JSON structured output, proxy provider routing, SPL strategy learning, LongCePO long-context input, or web/browser tools.
- Understand plugin side effects: network fetches, browser automation, code execution, local model loading, file-backed memory, or external tool calls.
- Debug plugin import/version problems.

Route server host/auth/SSL/provider basics to [../proxy-server/SKILL.md](../proxy-server/SKILL.md). Route core approach selection to [../optimization-approaches/SKILL.md](../optimization-approaches/SKILL.md). Route local model backend problems to [../local-inference-decoding/SKILL.md](../local-inference-decoding/SKILL.md).

## Plugin model

A plugin module is loaded when it defines:

```python
SLUG = "plugin_slug"
def run(system_prompt, initial_query, client, model, ...):
    ...
```

Loaded plugins join `plugin_approaches`, so plugin slugs can be used in model prefixes and compositions just like approach slugs when the server is in auto mode.

## High-value plugin groups

- **Context/tools:** `mcp`, `readurls`, `web_search`, `deep_research`, `executecode`, `coc`.
- **State/privacy/format:** `memory`, `privacy`, `json`, `compact`.
- **Selection/reasoning augmentation:** `genselect`, `majority_voting`, `deepthink`, `spl`, `longcepo`, `router`.
- **Provider operations:** `proxy` load balancing/failover plugin.

## References and script

- [references/plugin-catalog.md](references/plugin-catalog.md) lists slugs, signatures, and task fit.
- [references/mcp-memory-privacy-json.md](references/mcp-memory-privacy-json.md) covers MCP, memory, privacy, and JSON structured output.
- [references/proxy-spl-longcontext-tools.md](references/proxy-spl-longcontext-tools.md) covers proxy plugin, SPL, LongCePO, deepthink/deep research, web/search/code tools, and router.
- [references/troubleshooting.md](references/troubleshooting.md) maps plugin import, config, browser, model-loading, MCP, PII, and unsafe-side-effect failures.
- Run `python scripts/plugin_matrix.py --help` to inspect plugin slugs and signatures without making real tool/provider calls.

## Safe enablement checklist

1. Identify whether the plugin performs external I/O, code execution, browser automation, or model downloads.
2. Verify required dependencies with `scripts/plugin_matrix.py --check-imports`.
3. Keep secrets in environment variables or user config files, not prompts or logs.
4. Start with dry-run/config inspection before real tool calls.
5. Combine plugins with approaches only when you understand the order (`&`) or parallel behavior (`|`).
6. Add explicit user approval for plugins that execute code, open browsers, fetch arbitrary URLs, or call MCP tools with side effects.

## Common examples

MCP as a model prefix:

```text
mcp-gpt-4o-mini
```

Memory with opt-in file persistence:

```bash
export OPTILLM_MEMORY_FILE=/secure/path/memory.json
```

Proxy plugin wrapping an approach:

```python
extra_body={"optillm_approach": "proxy", "proxy_wrap": "moa"}
```

LongCePO input format:

```text
<long context text><CONTEXT_END>question about the context
```

## Security notes

- `executecode` and `coc` can run Python code; treat untrusted prompts as untrusted code sources.
- `web_search` uses browser automation and can hit CAPTCHAs or external web services.
- `mcp` can call external tools; only configure trusted servers with least-privilege access.
- `privacy` anonymizes before provider calls and deanonymizes after, but prompts/logs around it still need data-handling care.
