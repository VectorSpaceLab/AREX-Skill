# Troubleshooting

## 1) Missing Tencent credentials for rewrite

**Symptom**

- The rewrite path raises a credentials error before any prompt enhancement happens.

**Cause**

- `PE/deepseek.py` requires both Tencent Cloud key variables.

**Recovery**

- Set `DEEPSEEK_KEY_ID` and `DEEPSEEK_KEY_SECRET`.
- Verify network access to Tencent Cloud LKEAP.
- If you do not intend to use the external rewrite path, disable `--rewrite` and stay on the local prompt modes.

**Important**

- Do not silently fall back to a different prompt mode. A missing-credential rewrite request should be treated as a hard failure, not a quiet downgrade.

## 2) Rewrite requested but the CLI still fails

**Symptom**

- The command reaches the rewrite branch and then fails with an attribute error.

**Cause**

- The current `run_image_gen.py` rewrite branch reads `args.sys_deepseek_prompt`, but the parser does not define that argument in this snapshot.

**Recovery**

- Do not assume the documented rewrite flag works as-is.
- Either patch the CLI to define the missing argument, or avoid `--rewrite` and use manual prompt writing or local model self-rewrite instead.
- If you need a quick safe workaround, prefer `use_system_prompt="en_unified"` with `bot_task="think_recaption"` for Instruct models.

## 3) Invalid `use_system_prompt` / `bot_task` combination

**Symptom**

- The resolver returns an unsupported prompt selection or the downstream model path raises a mode error.

**Typical mistakes**

- `use_system_prompt="dynamic"` with CLI `bot_task="think_recaption"`
- `use_system_prompt="custom"` with an empty `--system-prompt`
- unsupported `use_system_prompt` strings
- vLLM client assumptions copied into the local CLI

**Recovery message to use**

- "Use `en_unified` with `think_recaption` for instruct editing, or change the task to `image` / `recaption` if you want dynamic routing."

**Notes**

- In the source resolver, `dynamic` only has explicit branches for `think`, `recaption`, and `image`.
- The local CLI accepts `think_recaption`, but `dynamic` does not special-case that string.

## 4) Multi-image conditioning list is malformed

**Symptom**

- References are misread, only one image is used, or the wrong image order is encoded.

**Cause**

- The CLI splits `--image` on commas and strips whitespace.
- Empty items are ignored.
- Commas inside a path are not safe.

**Recovery**

- Pass comma-separated paths in the same order you want the model to read them.
- Use the ordinal labels in the prompt: `图1`, `图2`, `图3`.
- Keep the reference order aligned with the prompt order.
- If you need more complex file names or batch handling, switch to the programmatic API instead of the comma-split CLI form.

## 5) Text rendering is broken or unstable

**Symptom**

- The image generator omits the intended words or invents layout text.

**Recovery**

- Put every visible string in double quotes.
- Preserve the original language and spelling inside the quotes.
- Specify position, size, weight, color, and arrangement for each piece of text.
- For UI-style prompts, describe the layout hierarchically from background to container to regions to elements.

**Common mistake**

- Describing a text-bearing region vaguely, such as "some contact details" or "a title area".

## 6) `dynamic` mode does not pick the expected rewrite preset

**Symptom**

- You expected a think/recaption prompt, but the model behaves like a plain or empty system-prompt path.

**Cause**

- The source dynamic resolver only understands `think`, `recaption`, and `image` as explicit branches.
- `think_recaption` is a separate local task string, not a dynamic routing key.

**Recovery**

- Use `en_think_recaption` explicitly for think-plus-recaption behavior.
- Use `en_unified` for instruct editing and multi-image workflows.

## 7) Image-size format confusion

**Symptom**

- The requested shape is not the shape you get.

**Cause**

- `HxW` and `W:H` are both accepted, but they are interpreted differently in the implementation.
- The selected size is then snapped to the nearest supported resolution.

**Recovery**

- Use `auto` when you want the model to infer ratio.
- Use an explicit square or ratio when composition is important.
- For editing, pair the size choice with `infer_align_image_size=True` if you want the output to preserve the source geometry more closely.

## 8) Base checkpoint vs Instruct checkpoint confusion

**Symptom**

- You expect automatic prompt rewriting from the base checkpoint, but the result is too literal.

**Cause**

- The base checkpoint does not self-rewrite in the same way the instruct path does.

**Recovery**

- Manually expand the prompt using the prompt handbook structure, or use the instruct path with `use_system_prompt="en_unified"` and `bot_task="think_recaption"`.

## 9) Synthetic recovery case: unsupported prompt mode plus dynamic routing

**Recommended recovery message**

- "Dynamic mode cannot infer this task string. Switch to `en_unified` for instruct editing, or route to `image` / `recaption` explicitly."

## 10) Synthetic recovery case: rewrite requested without credentials

**Recommended recovery message**

- "Disable `--rewrite` or provide Tencent credentials and network access. Do not rely on a silent fallback."
