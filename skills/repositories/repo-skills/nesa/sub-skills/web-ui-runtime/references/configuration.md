# Web UI Configuration

The Nesa web UI settings and flags determine whether the demo runs in encrypted
mode, which backend it uses, and whether the service is exposed.

## Important settings

| Setting | Meaning | Expected Nesa value or caution |
|---|---|---|
| `mode` | UI interaction mode. | Use `equivariant-encrypt` for Nesa encrypted workflows. |
| `equivariant-encrypt_command` | Prompt wrapper inserted around the user's prompt in encrypted mode. | Preserve user intent; do not delete this field accidentally. |
| `autoload_model` | Whether the selected model loads automatically. | Keep false when debugging downloads or model paths. |
| `stream` | Whether UI streams output updates. | The remote LLM path is streaming-oriented. |
| `truncation_length` / `max_new_tokens` | Context and generation limits. | Lower them for small CPU tests or memory errors. |
| `default_extensions` | Web UI extensions enabled on startup. | Keep minimal unless a user asks for extensions. |

## Command flags

The checked command flags include `--cpu`. This is safe for small local checks,
but it prevents GPU use even when a GPU is present. Remove or override CPU mode
only after selecting and verifying a compatible accelerator stack.

High-risk flags:

- `--listen` or binding to all interfaces exposes the service beyond localhost.
- `--share` creates an external tunnel; treat it as public exposure.
- `--trust-remote-code` lets model repositories execute custom code; use only
  when the user trusts the model source.
- auth flags are required when exposing beyond localhost.

## Prompt flow in encrypted mode

The web UI's encrypted mode wraps the conversation as follows:

1. Build a standard chat or instruction prompt from history.
2. Remove duplicate BOS tokens where needed.
3. Insert the prompt into `equivariant-encrypt_command`.
4. Create outer messages for the local tokenizer/model handler.
5. Tokenize locally before remote or local model inference.

If generated prompts look malformed, inspect templates and history conversion
before blaming model output.

## Validator usage

Use the bundled validator with explicit files:

```bash
python scripts/validate_runtime_config.py --settings settings.yaml --cmd-flags CMD_FLAGS.txt
```

The validator checks YAML shape, encrypted mode, prompt-command presence, auth
risk signals, and CPU/public-serving flag combinations. It does not launch the
UI or mutate files.
