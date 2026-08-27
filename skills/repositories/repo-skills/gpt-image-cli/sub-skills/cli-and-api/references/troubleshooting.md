# CLI/API troubleshooting

Use this guide before rerunning any command that could call the OpenAI Images API. Real calls can cost money; do not blindly retry failures.

## `OPENAI_API_KEY` is missing

Signal:

```text
error: OPENAI_API_KEY not set. Add it to env / .env / ~/.env, or use your host agent's native image tool.
```

Meaning: the CLI exits with code `2` before any API call.

Actions:

1. If the user wants to use this CLI, ask them to provide credentials through their normal secret-management flow.
2. Check presence without printing the value:

   ```bash
   test -n "${OPENAI_API_KEY:-}" && echo "OPENAI_API_KEY set" || echo "OPENAI_API_KEY not set"
   ```

3. Remember the CLI also loads `./.env` and `~/.env` without overriding an existing process variable.
4. If the user does **not** want local-key use, ensure the key is unset and that local dotenv files will not be loaded for that run.
5. Never write `.env` or API-key files unless explicitly requested.

## `gpt-image` command is missing

Signals:

```text
gpt-image: command not found
No module named gpt_image_cli
```

Actions:

```bash
command -v gpt-image || true
python -m gpt_image_cli.cli --help
python scripts/gpt_image_cli_helper.py preflight
```

If both command and module are absent, install `gpt-image-cli` through the user's approved Python tool or package source, then rerun help before any API call. Do not reinstall blindly over an existing working skill/CLI.

## Reference image path is invalid

Signal:

```text
error: --image not found: path/to/image.png
```

Meaning: edit-route preflight failed and exited `2` before an API call.

Actions:

- Verify each `-i/--image` path exists and is a file.
- For multi-reference edits, repeat `-i` once per file and reference them by index in the prompt.
- Use common image formats accepted by the API; if the API rejects the file type or content later, convert the file to PNG/JPEG/WebP and retry only with user approval.

## Mask path is invalid or mask lacks an image

Signals:

```text
error: --mask requires --image (edits endpoint only)
error: --mask not found: path/to/mask.png
```

Actions:

- Always provide at least one `-i/--image` when using `-m/--mask`.
- Use a PNG mask with alpha information for inpainting.
- Interpret masks as: opaque pixels are preserved; transparent pixels are regenerated.
- Keep the mask aligned with the target image dimensions when possible.

## `--input-fidelity` is ignored for the default model

Signal on stderr for edit calls with the default model:

```text
note: dropping --input-fidelity because gpt-image-2 rejects that parameter.
```

Meaning: this is intentional. The CLI avoids a known `gpt-image-2` parameter rejection by omitting `input_fidelity` locally.

Actions:

- For `gpt-image-2`, omit `--input-fidelity`; preserve fidelity by writing stronger edit invariants in the prompt.
- If the user explicitly targets a model that supports `input_fidelity`, pass the flag with that model and verify against live API behavior.

## Wrong endpoint was used

Symptoms:

- A user expected an edit, but the command generated a new standalone image.
- A mask was supplied without a reference image.

Actions:

- Any edit must include at least one `-i/--image`.
- Multi-reference edit = repeat `-i` for each reference.
- Inpaint = `-i target.png -m mask.png`.
- `--moderation` applies to the generation route, not the edit route in this CLI.

## Output file or format surprises

Symptoms:

- A `.png` filename contains WebP or JPEG bytes.
- Multiple outputs overwrite expectations.
- Compression appears ignored.

Actions:

- Keep `--format` and `-f/--file` suffix consistent yourself:

  ```bash
  gpt-image -p "catalog chair" --format webp --compression 80 -f chair.webp
  ```

- For `-n > 1`, expect `_0`, `_1`, ... suffixes before the extension.
- `--compression` is intended for `jpeg`/`webp`; do not expect it to affect PNG.
- If `-f` is omitted, the CLI writes to `./fig/` if present, otherwise to the current directory.

## Size was rejected or output quality is variable

Actions:

- Prefer stable shortcuts first: `1k`, `portrait`, `landscape`, or `square`.
- For final large assets, try `2k` before experimental 4K-style sizes.
- Literal sizes must be multiples of 16, within the total pixel range, and within the live API's edge/ratio constraints.
- If live API behavior rejects a documented shortcut, choose the nearest smaller valid literal size.

## API error, refusal, or no image data

Signals: the CLI exits `1` and prints an OpenAI API error/refusal, or reports no image data in the response.

Actions:

1. Read the exact error text; do not hide it unless it contains secrets.
2. Check prompt policy/safety wording, file validity, size constraints, model name, and API account access.
3. Do not automatically retry high-cost commands. Ask the user whether to retry, lower quality, reduce count, simplify the prompt, or switch to a host-native image tool.
4. For refusals, revise the prompt toward a safe, allowed transformation rather than trying to bypass moderation.

## Native image tool confusion

Some agent hosts may provide their own image-generation tool. If the user asks to use the host-managed tool, do that instead of this CLI. If they ask specifically for `gpt-image-cli`, use this sub-skill and preserve the API-key/cost boundary.
