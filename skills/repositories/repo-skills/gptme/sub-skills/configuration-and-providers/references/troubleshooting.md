# Configuration and provider troubleshooting

Use this reference to diagnose configuration, credentials, provider prefixes, model defaults, local/OpenAI-compatible endpoints, and auth helpers. Prefer static checks and help commands before running browsers, provider connectivity tests, or LLM calls.

## Triage sequence

1. Parse the involved TOML files with [the config validator](../scripts/validate_gptme_config.py). Invalid TOML or duplicate keys must be fixed first.
2. Explain the model-selection priority with [the model-selection explainer](../scripts/explain_model_selection.py). Do not assume `MODEL` wins if `[models].default` exists.
3. Identify the selected provider prefix and required credential or local base URL.
4. Confirm whether the key comes from process env, local config, project/chat env, credential store, or OAuth token files. Report only the source, never the raw value.
5. If the error involves live auth, local servers, browser OAuth, or provider connectivity, ask before running any command that contacts a service or opens a browser.

## Common symptoms

| Symptom | Likely cause | Safe diagnosis | Fix |
| --- | --- | --- | --- |
| `No API key found, couldn't auto-detect provider` | No `--model`, no chat/default `MODEL`, and no configured provider credentials. | Check `[models].default`, `MODEL`, known API-key env vars, credential store provider names, and OAuth token presence. | Set `[models].default`, export a provider key, run `/account setup`, or run `gptme-auth login` for the managed provider. |
| `Environment variable ... not set in env/config or credentials.toml` | Selected provider has no key source. | Determine selected model prefix; map it to the expected key source in [providers-and-models.md](providers-and-models.md). | Add the key to shell env, `config.local.toml`, `gptme.local.toml`, or credential store. |
| A different model is used than expected | Higher-priority `--model`, chat config, or `[models].default` overrides `MODEL`. | Run the model-selection explainer with all known sources. | Remove or update the higher-priority setting; prefer one permanent `[models].default`. |
| `Unknown provider` or `Model name must be fully qualified` | Missing/typoed provider prefix, unconfigured custom provider, or stale plugin package. | Check model string prefix and configured `[[providers]]` names. | Use `provider/model`, add/fix `[[providers]]`, install/enable the provider plugin, or use `gptme-util models list` in a live environment. |
| TOML parse error or duplicate key | Same key appears twice in one table, or invalid TOML syntax. | Static TOML parser reports the file and line. | Remove the duplicate. Use `[models].default` or `[env].MODEL`, not multiple `MODEL` keys in one `[env]` table. |
| Keys appear in shared config | Secrets were placed in `config.toml` or `gptme.toml`. | Search only for secret-like key names; do not display values. | Move secrets to `config.local.toml`, `gptme.local.toml`, credential store, or process env. |
| `/account` shows no configured accounts | No API keys in env/config/credential store/OAuth locations visible to that process. | `/account list` is safe inside gptme; the static validator can inspect a credential file path. | Run `/account setup <provider>` or configure env/local config. |
| `gptme-auth status` says not logged in | No managed-service token for the selected URL. | `gptme-auth status --help` is safe; `status` reads local token metadata. | Run `gptme-auth login` for the intended service URL; use `--no-browser` on headless hosts. |

## `[models].default` versus `MODEL`

`[models].default` is the recommended permanent default and has higher priority than `MODEL`. Conflicts are common after `/account setup`, because the setup helpers may write an `env.MODEL` value while a user already has `[models].default`.

Example conflict:

```toml
[models]
default = "anthropic/claude-sonnet-4-6"

[env]
MODEL = "openai/gpt-5"
```

Resolution:

- If the user wants Anthropic globally, keep `[models].default` and remove `MODEL` to reduce confusion.
- If the user wants OpenAI globally, set `[models].default = "openai/gpt-5"` and remove `MODEL`.
- If a project temporarily needs a model, prefer an explicit `--model` for that run or document a project `[env].MODEL` while noting it is still below global `[models].default`.

## Local/Ollama and OpenAI-compatible endpoint failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Missing environment variable OPENAI_BASE_URL` | Selected model starts with `local/` but no local base URL is configured. | Add `OPENAI_BASE_URL = "http://127.0.0.1:11434/v1"` or pass it in env. |
| Connection refused on `:11434` | Ollama is not running or listening elsewhere. | Ask the user to start `ollama serve` or provide the actual base URL. |
| Model not found | The tag after `local/` does not exactly match the local server's model name. | Compare against `ollama list` or the server's `/models` output; include the `:tag`. |
| Text works but tools loop/fail | Local model is too small or poor at the selected tool format. | Use a larger instruction model; try `gptme --tool-format xml`; reduce tool complexity. |
| Local calls time out | Slow local inference or large context. | Set `LLM_API_TIMEOUT` to a numeric value; use a smaller context/model. |
| Summary generation fails with local model | gptme uses the same local model for summary tasks because there is no separate local summary model. | Troubleshoot the same endpoint/model and consider a more capable local model. |

Static Ollama preparation without live calls:

```toml
[env]
MODEL = "local/llama3.2:3b"
OPENAI_BASE_URL = "http://127.0.0.1:11434/v1"
```

Then explain to the user that a live check, if authorized, should start with a simple `gptme "hello" -m local/llama3.2:3b` before testing tool calls.

## OpenRouter failures

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| 401/403 | Missing, invalid, or expired `OPENROUTER_API_KEY`. | Re-run `/account setup openrouter` or `gptme-auth openrouter` with user approval. |
| 400 mentioning provider routing, reasoning, or no providers | Over-constrained routing: reasoning plus strict `require_parameters`/privacy/provider pinning. | Remove provider suffix or quantization; only set `OPENROUTER_DATA_COLLECTION=allow` if the user accepts it. |
| Tool calls fail silently through routed providers | Backend selected by OpenRouter may not support required parameters. | For non-reasoning models, gptme sets `require_parameters=true`; choose a model/provider known to support tools or pin a compatible backend. |
| User expects training/data collection to be denied | `OPENROUTER_DATA_COLLECTION` may override default. | Check whether it is set to `allow`; unset it or set `deny` for non-reasoning requests. |
| Quantization behavior surprises user | `OPENROUTER_QUANTIZATION` restricts eligible backends. | Show the configured list; remove invalid/overly restrictive values. |

Never print OpenRouter API keys. A masked preview is acceptable only if produced by gptme's own account listing or by a validator that redacts values.

## OAuth/browser auth issues

| Flow | Common problem | Fix |
| --- | --- | --- |
| `gptme-auth login` | Browser cannot open on SSH/headless host. | Use `gptme-auth login --no-browser` and manually open the URL/code. |
| `gptme-auth login` | Device code expires or polling times out. | Re-run login; ensure the service URL/auth URL are correct. |
| `gptme-auth openrouter` or `/account setup openrouter` | Browser callback/sign-in fails. | Retry with a normal browser session; if still failing, use manual `OPENROUTER_API_KEY` in local config. |
| `gptme-auth openai-subscription` | Browser OAuth fails or account is not Plus/Pro. | Retry auth; for production/multi-user work use direct `openai/...` with `OPENAI_API_KEY`. |
| `gptme-auth grok-subscription` | Local callback port unavailable or grok CLI token invalid. | Close the conflicting process, retry, or use valid grok CLI auth before running the command. |

Auth helpers store local tokens/keys. They are user actions, not maintainer tests; do not run them just to verify a generated skill.

## Custom provider pitfalls

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Bare custom provider name raises `no default_model` | `[[providers]]` lacks `default_model`. | Add `default_model` or use `provider/model` explicitly. |
| Custom provider key error | `api_key_env` is unset and no direct key/default env var is available. | Set the env var or use a local override. For no-auth local endpoints, omit `api_key_env` and let the default placeholder be used. |
| Provider list has duplicates | Repeated setup appended instead of upserting, or local/main entries differ by name. | Merge by exact `name`; keep one entry per provider. |
| Plugin provider fails at startup | Provider plugin exports wrong type or custom `init` did not register an OpenAI-compatible client. | Verify the entry point exports a `ProviderPlugin` or unified plugin with a provider; fix `init`. |
| Streaming endpoint rejects `stream=True` | Metadata alone does not disable streaming transport. | Add a proxy that supports streaming or use a provider/endpoint compatible with gptme's OpenAI client path. |
| Vision claims do not work | Provider does not accept standard OpenAI `image_url` content parts. | Set `supports_vision` accurately in plugin metadata or avoid image inputs. |

## Help-only native candidates

These commands are safe to use as native verification candidates because they should not authenticate, open a browser, or call a model when invoked with `--help`:

```sh
gptme-auth --help
gptme-doctor --help
```

`gptme-doctor` without `--help` inspects the host environment; ask before using it in a user's environment. `gptme-util providers test` and model test commands make network calls and require explicit approval.

## When the task is maintainer-only

Say the task is maintainer-only for a gptme checkout before recommending any of these:

- editing `gptme/config/`, `gptme/llm/`, `gptme/oauth/`, or tests.
- running `pytest tests/test_config*.py tests/test_credentials*.py tests/test_llm*.py tests/test_custom_providers.py`.
- adding a built-in provider PR, changing provider metadata, or altering OAuth implementation.
- running `make test`, `make lint`, `make typecheck`, or release/package checks.

For end-user configuration tasks, use static validation, help output, and narrowly scoped config edits instead.
