# Specialty Troubleshooting and Safe Stops

Use the first matching row, collect the exact error and command, then route to
the owning sibling when the problem is not specialty-specific. Do not retry a
full merge blindly.

| Symptom | Likely cause | Safe action |
|---|---|---|
| `No module named peft`, bitsandbytes/quantization import error, or missing Transformers model class | Optional PEFT, 4/8-bit, or newer architecture extra is absent | Stop. Install/verify the approved isolated environment or remove the optional flag. Do not silently substitute an incompatible version. |
| Base, donor, expert, tokenizer, raw file, or YAML not found | Wrong local path, unapproved Hub/network resolution, missing revision, or output mistaken for input | Resolve and read-test each input. Pin revisions and credentials/network policy. Never turn on remote code just to hide a missing path. |
| Raw merge says tensor missing | Default strict presence contract or incomplete tensor union | Choose exactly `--tensor-intersection` or `--tensor-union`, then confirm the selected method accepts missing inputs. Union does not repair shapes. |
| Raw merge reports incompatible shapes or an operation error | Tensor-name collision with different dimensions/layouts | Inspect names and shapes using an isolated local fixture. Stop and choose compatible checkpoints or use the architecture route; do not use `--allow-crimes`. |
| Multi-stage says duplicate name, unnamed-document error, unresolved model, or circular dependency | Bad document names/references, more than one final document, missing intermediate, self-edge, or cycle | Run the bundled `--check-multistage` preflight, fix the graph, and use a fresh intermediate directory. A name that is not declared can become a remote model lookup. |
| `--lazy` appears to use stale output | Existing intermediate has `config.json` and a checkpoint marker | After changing recipe/source, use `--no-lazy` and a new output or approved overwrite. Preserve provenance. |
| MoE rejects architecture or reports no compatible output | Mixed model types, unsupported installed family, shared-expert/gate constraint, or missing optional Qwen class | Run with `-v`, compare every config's model type and dimensions, and inspect installed candidates. Do not add `--allow-crimes` as a fix. |
| MoE says too few experts, duplicate prompts, or all experts are identical | `experts_per_token` exceeds count, prompts cannot distinguish experts, or sparse-upcycling inputs are intentionally identical | Correct the config. If the result will be trained, use the explicit training-caveat flag and record that it is not useful before training. |
| MoE warns degenerate gates | Prompt embeddings/hidden states produce indistinguishable router vectors | Stop inference use; revise positive/negative prompts, gate mode, or expert diversity and rerun only with approved local resources. |
| MoE OOM or hidden-state loading fails | `hidden` gate mode needs base-model evaluation; GPU/RAM or quantization extra is insufficient | Try `cheap_embed`, a bounded CPU/device plan, or approved 4/8-bit loading. Route backend and memory diagnosis to model IO. |
| LoRA output is missing or adapter loader rejects it | Failed SVD, wrong base, vocabulary mismatch, unsupported module naming, or unsafe overwrite | Check `adapter_config.json`, target modules, rank patterns, base revision, and vocab sizes. Use include/exclude or `--skip-undecomposable` only when the omitted modules are acceptable. |
| LoRA has unexpected full-rank modules | `--save-module` was supplied or decomposition was intentionally skipped | Inspect generated config and document the trade-off; do not call it a low-rank-only adapter without checking. |
| TokenSurgeon has no shared tokens, missing embedding/head, or donor IDs exceed rows | Tokenizer normalization mismatch, unsupported architecture, absent tied/untied tensor, or malformed checkpoint | Stop. Compare vocabularies and row counts. Choose `subword`/simple fallback only with explicit quality acceptance; out-of-range tokens are not silently valid. |
| TokenSurgeon approximation is unstable or too large | `k`, batching, OMP/PCA/STB memory, bad conditioning, or random/noise settings | Use a positive bounded batch, lower `k` after accepting quality impact, or choose a more suitable documented method. Validate special-token IDs and encode/decode afterward. |
| `--prefix-match`/`--byte-match` changes only one matrix unexpectedly | `embed` or `lm_head` mode was selected | Confirm the intended scope; use `yes` only when both matrices should reuse the shortcut. |
| LayerShuffle writes an unexpected config or errors on model/weight counts | No model, weights do not align with models, model configs differ, or a random selection exposed an unsupported layer | Run `--dry-run --write-yaml NEW_CONFIG`, inspect slices and layer ranges, and validate with the core config/architecture routes before merging. |
| LayerShuffle output collides with a source or existing model | Destructive output selection | Stop and choose a new output directory. Do not rely on dry-run to protect a later command. |
| Legacy/bakllama help or import fails | Compatibility wrapper is stale or installed against a changed internal API | Do not patch or invoke the checkout script from this route. Prefer modern YAML. Treat `bakllama` as blocked until its entry point imports and its help probe passes. |
| `--trust-remote-code` or a Hub request prompts/fails | Network, credentials, revision, or code-execution boundary | Stop and ask for explicit permission and pinned source. Offline-only work must use complete local files and tokenizer/config artifacts. |
| Output has partial shards or a writer failure | Disk full, output collision, async-write memory pressure, or interrupted process | Preserve the partial directory for diagnosis, do not treat it as valid, check disk and write settings, then rerun into a fresh approved path. |

## Dangerous flags

`--allow-crimes` only bypasses an architecture-mixing guard. It does not prove
keys, shapes, tokenizer IDs, or runtime semantics. `--trust-remote-code` can
execute code from a model repository. `--read-to-gpu`, `--low-cpu-memory`,
`--multi-gpu`, `--gpu-rich`, async writing, and 4/8-bit options change resource
behavior and require a verified backend plan. Never add them as generic fixes.

## External boundaries

A model identifier may cause Hub access even when the specialty operation is
otherwise offline. No command in this route supplies credentials, and no
bundled script downloads models, runs a full merge, or mutates a source. Ask for
network, credential, remote-code, and overwrite approval separately. For
architecture conversion, checkpoint key diagnosis, shard/memory planning, or
backend failures, hand off to
[model-io-and-architecture](../../model-io-and-architecture/SKILL.md). For
ordinary YAML method/tokenizer semantics, hand off to
[merge-configs](../../merge-configs/SKILL.md).
