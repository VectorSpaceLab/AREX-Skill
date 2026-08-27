# Provider, Model, and Router Workflows

## Provider catalog facts

In the verified OpenSquilla 0.5.3 inspection build, `providers list --json` exposed 49 provider entries. Catalog entries include runtime support, verification state, default base URL, API-key requirements, base-URL requirements, router support, default model, fields, and setup recipes.

Provider entries can be runtime-supported without being equally verified. Treat `verification = verified` as stronger evidence than `experimental`, and use `providers status` or `models probe` before relying on an experimental or custom endpoint.

Verified provider ids observed in the catalog were:

- `tokenrhythm`
- `openrouter`
- `dashscope`
- `anthropic`
- `qianfan`
- `byteplus`
- `deepseek`
- `gemini`
- `moonshot`
- `ollama`
- `openai`
- `openai_responses`
- `qwen_token_plan`
- `qwen_token_plan_anthropic`
- `volcengine`
- `zhipu`

Always prefer the user's installed catalog over hard-coded lists:

```sh
opensquilla providers list --json
opensquilla onboard catalog providers --json
```

## Provider selection patterns

Use direct single-provider setup when the user wants one exact model, provider-specific behavior, or billing audit:

```sh
opensquilla configure router --router disabled
opensquilla configure provider --provider openai --model gpt-5.4-mini --api-key-env OPENAI_API_KEY
```

Use router setup when the user wants normal cost/quality balancing:

```sh
opensquilla configure provider --provider openrouter --model deepseek/deepseek-v4-pro --api-key-env OPENROUTER_API_KEY
opensquilla configure router --router recommended
```

Use local or compatible endpoints only with explicit base URL and a truthful model id:

```toml
[llm]
provider = "custom_anthropic"
model = "vendor-model"
base_url = "https://llm.example.com/anthropic"
api_key_env = "CUSTOM_ANTHROPIC_API_KEY"
```

Custom provider boundaries:

- `custom` is OpenAI Chat Completions compatible.
- `custom_anthropic` is Anthropic Messages compatible and appends the Messages path.
- Unknown custom models keep conservative defaults unless the operator adds model metadata under `[models.<provider>."<model>"]`.
- Arbitrary user-named provider ids, arbitrary request headers, and inferred reasoning dialects are not part of the persisted provider contract.

## OpenAI provider ids

OpenAI is exposed through two provider ids:

- `openai` — chat/completions request shape for standard chat-style turns and broad tool compatibility.
- `openai_responses` — native Responses API shape with `chat` and `responses` capabilities.

Both use `OPENAI_API_KEY` and the same default OpenAI base URL. Switching between them is a provider-id change, not a credential change.

## Model inspection workflow

1. Check provider metadata locally:

   ```sh
   opensquilla providers list --json
   ```

2. If the gateway is running, list runtime models:

   ```sh
   opensquilla models list --provider openrouter --json
   ```

3. For credential validity or reachability, run a deliberate live probe:

   ```sh
   opensquilla models probe --provider openai --model gpt-5.4-mini --json
   ```

4. If context-window or pricing data is wrong, prefer a config override rather than assuming the catalog will refresh immediately.

## Router modes

| Mode | Use when | Command |
| --- | --- | --- |
| `recommended` | Ordinary personal-agent use; let the active provider's default routing profile choose tiers. | `opensquilla configure router --router recommended` |
| `openrouter-mix` | You intentionally want OpenRouter's mixed-model defaults. | `opensquilla configure router --router openrouter-mix` |
| `disabled` | You need one configured provider/model for every turn, exact provider debugging, benchmark reproducibility, or billing audit. | `opensquilla configure router --router disabled` |
| `custom` | Advanced tier ownership or provider mix. Catalog and setup-engine aware, but routine CLI help emphasizes the three modes above. | Prefer guided setup or explicit TOML after inspecting `onboard catalog router --json`. |

The router can affect selected model tier, direct model fallback, reasoning level, prompt policy, image-capable model selection, and cache-continuity safeguards. It does not replace provider credentials or make unsupported providers work.

## Router tiers and profile concepts

OpenSquilla text tiers are `c0`, `c1`, `c2`, and `c3`; the default text tier is normally `c1`. Some presets also define `image_model` for vision-capable input routing.

Inspect active tier values:

```sh
opensquilla config get squilla_router.tiers
opensquilla config get squilla_router.default_tier
```

Inspect catalog profiles:

```sh
opensquilla onboard catalog router --json
```

The observed catalog exposed legacy/persistable profile ids such as `openrouter`, `openai`, `deepseek`, `gemini`, `dashscope`, `moonshot`, `volcengine`, `byteplus`, and `zhipu`. Provider-specific inline presets can also be applied without persisting a legacy `tier_profile`.

## Cross-provider tier boundary

By default, `squilla_router.cross_provider_tiers = false`. If a router tier names a different provider than the active `llm.provider`, OpenSquilla preserves historical behavior by routing the tier's model id on the active provider and recording/flagging the mismatch.

When `cross_provider_tiers = true`, a routed tier can execute on its own provider. Credentials then resolve from `[llm_profiles.<provider>]`, provider-profile pools/env, or the registry env key if safe. Provider-native continuity state from one provider is not replayed to another provider.

Advanced mismatch behavior:

```toml
[squilla_router]
cross_provider_tiers = false
tier_provider_mismatch = "veto"  # advanced: rebind to an active-provider tier when possible
```

Use `veto` only when the operator understands that foreign tier choices may be discarded to keep execution on the active provider.

## Router runtime and optional dependencies

The verified inspection environment had the recommended CPU-only router/search/model-tokenization extras importable, including LightGBM and ONNX Runtime. A user's installation can still differ. If SquillaRouter optional dependencies are missing, OpenSquilla can still run with direct single-model routing, and `configure router --router disabled` is the deterministic fallback.

When diagnosing router behavior:

```sh
opensquilla config get squilla_router.enabled
opensquilla config get squilla_router.strategy
opensquilla providers status
opensquilla diagnostics on
```

On macOS source/terminal installs, LightGBM can require `libomp`. On Windows, ONNX Runtime can require the Visual C++ Redistributable. Route install/runtime remediation to setup-and-gateway unless the user is only asking which mode to select.
