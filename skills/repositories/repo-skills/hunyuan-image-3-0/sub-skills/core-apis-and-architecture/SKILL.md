---
name: core-apis-and-architecture
description: "Explain the HunyuanImage-3.0 package layout, public APIs,
  generation helpers, cache utilities, and lazy import behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core APIs and Architecture

Use this sub-skill when you need to understand how HunyuanImage-3.0 is wired,
which public objects are stable, and how config, tokenizer, image processing,
scheduler, cache, and model objects relate to one another.

## Read first

1. [API reference](references/api-reference.md)
2. [Architecture](references/architecture.md)
3. [Troubleshooting](references/troubleshooting.md)
4. [Core API surface checker](scripts/check_core_api_surface.py) for safe import and signature smoke checks.

## Route elsewhere

- End-user generation commands, checkpoint selection, and CLI examples:
  `../local-inference-cli/SKILL.md`
- System-prompt modes, recaption/think flows, and image-conditioning policy:
  `../prompt-and-image-conditioning/SKILL.md`
- Repo-wide install/import guidance and staleness checks:
  `../../SKILL.md` once the root skill is present

## Owned surface

- `HunyuanImage3Config`
- `HunyuanImage3ForCausalMM`
- `HunyuanImage3Model`
- `HunyuanImage3TokenizerFast`
- `HunyuanImage3ImageProcessor`
- `HunyuanImage3Text2ImagePipeline`
- `FlowMatchDiscreteScheduler`
- `HunyuanStaticCache`
- `cache_utils` helpers (`cache_init`, `TaylorCacheContainer`, `CacheWithFreqsContainer`)
- `get_system_prompt`
- import / lazy-loading behavior
- signature-level notes and object relationships

## What to explain here

- Which module owns which responsibility
- How `generate_image` turns prompt/image/message input into model inputs
- How the tokenizer and image processor cooperate on mixed text/image sections
- How the pipeline, scheduler, VAE, and caches interact during generation
- Why `skip_load_module` exists and what it does not guarantee

## What not to explain here

- CLI walkthroughs and shell launch recipes
- Gradio UI launch
- vLLM deployment or client request execution
- prompt rewrite service operation details
