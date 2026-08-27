# Prompt Modes and Conditioning

This reference distills the repo-owned prompt guidance into a local decision map for HunyuanImage-3.0.

## 1) Choose the prompt path

### Manual prompt writing
Use this when you want deterministic local behavior, do not have Tencent Cloud credentials, need to avoid network calls, or already have a detailed prompt.

The repo's prompt handbook guidance boils down to:

- state the main subject and scene first,
- then image quality and style,
- then composition and viewpoint,
- then lighting and atmosphere,
- then technical details.

For text rendering, keep visible text explicit and quoted, and keep the language of the quoted text unchanged.

### Local model self-rewrite
Use this when the model should expand or restructure the prompt before image generation.

Recommended local instruct path:

- `use_system_prompt="en_unified"`
- `bot_task="think_recaption"`
- `image_size="auto"` for ratio inference unless a fixed size is required
- `infer_align_image_size=True` for image editing or fusion when you want the output aligned to the reference ratio or dimensions

This is the safest path for Instruct and Instruct-Distil when you want reasoning plus rewrite inside the model workflow.

### External DeepSeek PE rewrite
Use this only when you intentionally want the repository's prompt-enhancement service.

It requires:

- `DEEPSEEK_KEY_ID`
- `DEEPSEEK_KEY_SECRET`
- network access to Tencent Cloud LKEAP

The PE flow is reference-only in this sub-skill because it is credentialed and network bound. Do not silently fallback to a different prompt mode when credentials are missing.

## 2) Mode matrix

| Intent | Recommended `use_system_prompt` | Recommended `bot_task` | Notes |
|---|---|---|---|
| Direct T2I | `en_vanilla` or `None` | `image` | Best when the prompt is already specific. With `image_size="auto"`, the model may still infer a ratio before image generation. |
| Manual rewrite through local model | `en_unified` | `think_recaption` | Best default for Instruct / Instruct-Distil. Supports rich prompt expansion and editing. |
| Rewrite only, no think stage | `en_recaption` or `en_unified` | `recaption` | Good when you want a clean rewrite without the think stage. |
| Explicit think + rewrite | `en_think_recaption` | `think_recaption` | The prompt is tuned for reasoning-plus-rewrite behavior. |
| Dynamic preset routing | `dynamic` | `image` or `recaption` | The source resolver maps `dynamic` for `image`, `recaption`, and internal `think`, but not for CLI `think_recaption`. |
| Custom system prompt | `custom` | any supported task | You must provide `--system-prompt`. An empty custom prompt is usually a mistake. |
| External PE rewrite | `universal` or `text_rendering` inside PE | `image` after rewrite | Only use when Tencent credentials and network are available. |

## 3) System-prompt resolution

The source resolver behaves like this:

- `None` → no system prompt
- `en_unified` → unified multimodal prompt
- `en_vanilla` / `en_recaption` / `en_think_recaption` → the matching English prompt block
- `dynamic` → selects by `bot_task`
  - `think` → think+recaption prompt
  - `recaption` → recaption prompt
  - `image` → vanilla prompt
  - anything else → returns the custom prompt string
- `custom` → returns the user-provided system prompt string
- anything else → unsupported

Important mismatch:

- the local CLI accepts `bot_task="think_recaption"`,
- but the dynamic resolver only special-cases `think`, not `think_recaption`.

So `dynamic + think_recaption` does not resolve to the think prompt in this snapshot.

## 4) Think, recaption, and image stages

In the model path, `think`, `recaption`, and `think_recaption` first run a text stage and then continue into image generation.

Practical meaning:

- `think`: analyze first, then continue toward image generation
- `recaption`: rewrite the prompt into a stronger caption, then continue toward image generation
- `think_recaption`: think first, then recaption, then continue toward image generation

The returned `cot_text` is the generated text-stage output, and `samples` is the generated image list.

## 5) Multi-image conditioning

Repository guidance and examples support up to three reference images for fusion/editing tasks.

Behavior to keep in mind:

- the CLI accepts comma-separated paths,
- whitespace is stripped from each path,
- empty items are ignored,
- order matters and should match the prompt's `图1 / 图2 / 图3` references,
- if a path contains a comma, the CLI split logic will misread it.

For editing or fusion, prefer an explicit ordered list of references and a prompt that names each source role.

### Recommended prompt pattern

- `图1` supplies identity or composition,
- `图2` supplies material, style, or texture,
- `图3` supplies background or supporting content.

## 6) Image-size and ratio choices

Supported user-facing forms:

- `auto`
- `HxW`
- `W:H`

Implementation detail worth remembering:

- the parser in `image_processor` treats `HxW` as height × width,
- the ratio form is interpreted as width:height,
- the size is then snapped to the nearest supported resolution in the model's resolution group.

Practical guidance:

- use `auto` when composition should be inferred,
- use square or explicit aspect ratios when the scene layout matters,
- use `infer_align_image_size=True` when a reference image's ratio should be preserved in editing or fusion.

## 7) Text rendering rules

For UI, poster, logo, or signage prompts:

- every visible text string must be explicit,
- every visible text string must be enclosed in double quotes,
- preserve the user's language and spelling exactly,
- do not convert descriptive text into quoted text unless it is actual visible copy,
- quantify layout elements instead of using vague count words.

For UI-style prompts, the distilled structure is:

1. overall background and main container
2. macro layout
3. section-by-section element description
4. exact text content and typography
5. composition and visual effects

For poster/logo style prompts, the distilled structure is:

1. overall description
2. main subject or core elements
3. background and environment
4. text and logos
5. composition and visual effects

## 8) DeepSeek PE rewrite path

The repo's PE rewrite path is designed to enhance sparse prompts, especially for the base pretrain checkpoint.

Facts to remember:

- `PE/deepseek.py` uses Tencent Cloud LKEAP,
- it hard-requires credentials and network access,
- it is not a local fallback,
- it is safe to reference only as behavior guidance here.

The current CLI snapshot has a known mismatch:

- the rewrite branch references `args.sys_deepseek_prompt`,
- but the parser does not register that argument in `run_image_gen.py`.

So a rewrite request may fail even after credentials are set, unless the CLI is patched or the mode is avoided.

## 9) When to prefer manual prompts over rewrite

Prefer manual writing when:

- credentials are unavailable,
- the run must be offline,
- the prompt already contains precise scene, style, and text requirements,
- you are debugging a mode combination instead of generating final art.

Prefer rewrite when:

- the prompt is sparse,
- you want richer composition and lighting detail,
- you are using the instruct path with reasoning,
- the external PE credentials and network are intentionally available and tested.
