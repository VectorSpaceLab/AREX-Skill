# Troubleshooting LLM, VLA, Services, and Rendering

## First safe checks

- Run `python scripts/check_vla_schema.py` from the sub-skill directory, or pass
  `--repo-root` if testing an editable checkout, to validate the VLA schema,
  chunking, tokenization, and action scaling with tiny CPU tensors.
- Run `python scripts/smoke_services.py` to inspect service signatures and test
  direct owner/client lifecycle without starting Ray, downloading models, or
  rendering videos.
- For render configuration, use `rlrender --help`, then `rlrender ... --dry-run
  --print-config` or `--validate-only` before writing outputs.

## Optional extras and missing imports

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: transformers`, tokenizer/model classes missing | LLM base extra not installed | Install the `llm` dependency set or avoid LLM wrappers and use schema/service smoke tests only. |
| vLLM import, engine, or CUDA-extension failures | `llm-vllm` dependencies absent or incompatible with platform/GPU stack | Treat vLLM as unverified; install the vLLM extra in a dedicated environment and re-run only import/server checks before collection. |
| SGLang wrapper cannot connect or import | `llm-sglang` dependencies absent, server URL wrong, or server not started | Start/verify the SGLang server separately, then connect with `SGLangWrapper`; do not let collection create an implicit long-lived service without a shutdown plan. |
| GRPO example imports fail for `peft`, `wandb`, `ray`, `flash-attn`, `bitsandbytes`, or `xformers` | `grpo` stack is optional and GPU-oriented | Keep GRPO reference-only until the user approves the full training/serving dependency set. |
| LeRobot/OpenX dataset classes or image preprocessing deps missing | `vla` or `offline-data` extras absent | Use canonical TensorDict fixtures and `check_vla_schema.py`; install dataset extras only for real robot dataset loading/conversion. |
| `rlrender` YAML/video/codecs fail | `rendering` or `video` extras absent | Use JSON configs and `--format jsonl/npz/frames` when possible; install codec/rendering extras before MP4/GIF/PNG. |

## Model downloads, cache, and offline mode

Passing model names such as a Hugging Face repository ID to wrappers or
tokenizers can trigger network downloads. In offline runs, use local model paths
that already contain weights and tokenizer files, or build wrappers around
already-loaded model/tokenizer objects. Do not start a training or collection
job until cache access, license requirements, and disk budget are explicit.

If a wrapper fails while loading from a string, retry with separately loaded
objects so tokenizer and model errors are isolated.

## GPU serving and memory

vLLM, SGLang, GRPO, flash-attention, bitsandbytes, and large Transformers models
are GPU-sensitive. Typical symptoms include CUDA OOM, failed CUDA extension
imports, worker startup timeouts, NCCL rendezvous errors, and slow generation
from CPU fallback. Recovery steps:

1. Verify the selected backend is actually installed and compatible with the
   PyTorch/CUDA build.
2. Start with a smaller local model or fewer replicas before enabling collection.
3. Set explicit device placement, tensor-parallel size, replica count, and max
   sequence/generation lengths.
4. For weight sync, reserve ports/process groups and confirm all serving workers
   are alive before calling update methods.
5. If GPU is unavailable or the environment uses a CPU PyTorch build, mark
   serving and GPU-specific claims unverified rather than treating CPU imports
   as proof.

## Tokenizer and chat-template mismatch

Symptoms include wrong assistant masks, shape mismatches in SFT/GRPO, empty
responses, inconsistent log-probs, or tokenizer errors around padding/EOS.
Check:

- model and tokenizer come from the same checkpoint family;
- `tokenizer.pad_token` is set when padding is requested;
- `chat_template`, `chat_template_name`, and `add_generation_prompt` match
  training and inference;
- `return_assistant_tokens_mask=True` is supported by the template when RLHF
  masking needs assistant-only tokens;
- `ChatEnv(..., with_tokenizer=True)` is paired with wrapper
  `prefer_tokens=True` when token-first KV-cache consistency matters.

## LLMCollector hangs or yields wrong shapes

- If using `yield_completed_trajectories` or `yield_only_last_steps`, verify that
  the env or reward/step transform sets `done` and `terminated`.
- Do not set `yield_only_last_steps=True` with `reset_at_each_iter=True` or an
  explicit `flatten_data` value.
- If using a replay buffer or queue, remember the collector may write instead of
  yielding, and `flatten_data` defaults differently.
- If policy version tracking is enabled, ensure the collector increments policy
  versions after weight updates and that async env pools add tracking manually.

## GRPO/SFT key and mask failures

- Use `loss.set_keys(...)` whenever tokens, log-probs, advantages, or reference
  log-probs are not under the defaults.
- Match GRPO `masking_strategy` to the masks produced by data collection:
  response-only (`sft`), assistant-only (`rlhf`), or all valid attention tokens
  (`generic`).
- Keep behavior-policy log-probs separate from recomputed current log-probs.
- Monitor `ESS`, `clip_fraction`, and KL outputs; sudden changes often indicate
  model mode drift, bad masks, or too-large updates.

## VLA schema diagnostics

Common validator issues and fixes:

- `missing language instruction`: set `"language_instruction"` or pass the
  custom `instruction_key`; disable `require_instruction` only for workflows
  that truly do not use language.
- `no perception found`: provide `("observation", "image")` or
  `("observation", "state")`, or pass custom image/state keys.
- `missing action`: set raw per-step `"action"` or pass a custom `action_key`.
- `empty language instruction`: strip/validate converted dataset text.
- `non-finite values in action`: clean NaN/Inf before scaling, tokenizing, or
  loss computation.
- descending into a tensor leaf with a longer nested key is reported as missing,
  not as a crash; check whether a single image tensor or camera-keyed image
  TensorDict is expected.

## Action chunking and action scaling errors

- `ActionChunkTransform` needs time-structured actions. Reshape flat sampler
  outputs to `[num_slices, slice_len, action_dim]` before chunking.
- If `("next", done_key)` shape does not align with actions, either fix done
  shape to match the time dimension or pass `done_key=None` to ignore internal
  boundaries.
- Use `action_is_pad` in the loss; otherwise repeated tail actions contaminate
  chunked behavior cloning.
- `ActionScaling` without explicit stats must be attached to an env with a
  fully bounded continuous action spec.
- Forward-only replay-buffer normalization (`in_keys_inv=[]`) requires explicit
  `loc` and `scale` or metadata/stat constructors.
- One `ActionScaling` instance handles one action key; compose several for
  multiple action streams.

## Action tokenizer mismatch

- `UniformActionTokenizer` requires `num_bins >= 1`, matching `low`/`high`
  shapes, and `high > low` for every dimension.
- `VocabTailActionTokenizer` requires `num_bins >= 2`; `full_vocab_size`, when
  used, must be at least `num_bins`.
- Decide whether downstream code stores window IDs or full LM-vocabulary IDs.
- If using OpenVLA norm stats, provide matching low/high arrays and masks;
  gripper binarization/inversion must match the robot benchmark convention.

## Ray and service lifecycle

- `get_services` currently supports `backend="ray"` for the registry. Passing
  `direct` or `process` to `get_services` is a configuration error, not a local
  registry mode.
- Use direct/process service owners through their constructors, not through the
  Ray registry.
- Always call `reset()` or `shutdown()` for registry-owned Ray services and
  `shutdown()` for externally owned services.
- Use unique namespaces per run to avoid reusing stale service names.
- Registering an existing service owner requires it to be started first and does
  not transfer ownership; you still shut it down in the driver.
- If a remote actor dies, prefer explicit cleanup and re-registration over
  retrying calls against a stale handle.

## Python tool execution

- `PythonInterpreter(services="ray")` fails unless the named
  `PythonExecutorService` is already registered in the same namespace.
- Local persistent mode can leak resources if transforms are not closed; call
  `close()`/environment cleanup.
- Keep timeouts low and do not execute untrusted code without sandboxing.
- Service mode helps when many envs share an interpreter pool; for one or two
  envs, local persistent or temporary mode is simpler.

## Rendering, video, and display

- `rlrender` requires `--ckpt`, `--policy`, and `--env` after config merging.
- Factory specs must be importable as `module_or_file:callable`. Use
  `--print-config` to see normalized keys.
- `--format mp4` or GIF/PNG paths need optional encoding dependencies; if
  codecs fail, try `--format frames`, `npz`, or `jsonl` to separate rollout from
  encoding.
- Pixel backend needs the configured pixel key in TensorDict rollouts;
  environment render backend needs an env with compatible `render()` output.
- Headless servers may lack display libraries; prefer RGB-array/pixels backends
  or null backend validation before interactive display.
- MuJoCo WASM notebooks require Node.js and a JS package manager; sidecar viewer
  setup may require network on first install.
