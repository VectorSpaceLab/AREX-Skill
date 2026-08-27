# LLM and RLHF Workflows

## When to read

Read this for TorchRL LLM post-training tasks: chat environments, LLM inference
wrappers, data formats, tool transforms, `LLMCollector`, GRPO/DAPO/CISPO, SFT,
distillation, policy-version tracking, and vLLM/SGLang weight synchronization.
The installed API facts used here include `ChatEnv(*args, with_tokenizer=False,
**kwargs)` and `LLMCollector(env, *, policy=None, policy_factory=None,
dialog_turns_per_batch=None, ...)`.

## Mental model

TorchRL treats an LLM fine-tuning loop as the same TensorDict-first RL pipeline
used elsewhere, with LLM-specific wrappers and transforms at the edges:

1. **Data/conversation state** lives in `History` and related TensorClass
   containers (`Text`, `Tokens`, `Masks`, `LogProbs`, `ChatHistory`).
2. **Environment state** comes from `ChatEnv` or task-specific LLM envs. The env
   prepares prompts on reset and turns wrapper responses into the next prompt on
   step.
3. **Policy/inference** is a wrapper around a model backend:
   `TransformersWrapper`, `vLLMWrapper`, or `SGLangWrapper`.
4. **Collection** uses `LLMCollector`, which inherits the generic collector
   construction pattern but exposes dialogue-specific batch/termination options.
5. **Objectives** consume token/log-prob keys via LLM-specific losses such as
   `GRPOLoss` and `SFTLoss`, or standard objectives where appropriate.
6. **Remote serving and weight sync** are optional. Treat them as a deployed
   serving system, not as a CPU smoke-test requirement.

## ChatEnv and History

`ChatEnv` is intentionally minimal. It starts from user data under its data key
(default `"query"`) and returns a prompt in one of the input modes:

- `input_mode="history"`: use `History` objects for structured chat state.
- `input_mode="text"`: use text prompt/response fields.
- `input_mode="tokens"`: supported in the API surface, but most robust
  token-first flows use `with_tokenizer=True` to keep token fields synchronized.

Important defaults and keys:

- text prompt key: `("text", "prompt")`
- text response key: `("text", "response")`
- data/reset key: `"query"`
- roles: `system`, `user`, `assistant` by default
- `with_tokenizer=True` requires a tokenizer and wraps the env with the
  incremental tokenizer transform so `tokens.prompt` stays aligned with
  `history.prompt`.

Use `History` when you need multi-turn trajectories, assistant-token masks, tool
calls, or chat-template application. `History.apply_chat_template(...)` can
return strings, token tensors, and assistant masks when the tokenizer/template
supports generation tags. For list-backed histories, initialize TensorDict's
list stacking early in user scripts when needed.

## Wrappers and generation settings

`TransformersWrapper`, `vLLMWrapper`, and `SGLangWrapper` share the
`LLMWrapperBase` contract:

- `input_mode` is `"history"`, `"text"`, or `"tokens"`.
- Input keys default to prompt fields when `generate=True` and full fields when
  `generate=False`, for example `("history", "prompt")` versus
  `("history", "full")`.
- Outputs are TensorClass-style containers under configurable keys:
  `text`, `tokens`, `masks`, `log_probs`, and `history` when applicable.
- Common `generate_kwargs` names include `max_new_tokens`,
  `num_return_sequences`, `temperature`, `top_p`, `top_k`,
  `repetition_penalty`, `do_sample`, `num_beams`, `length_penalty`,
  `early_stopping`, `stop_sequences`, `skip_special_tokens`, and `logprobs`.
- `prefer_tokens=True` tells wrappers to consume existing `tokens.prompt` when
  available. Pair it with `ChatEnv(..., with_tokenizer=True)` for KV-cache and
  log-prob consistency across turns.

Backend notes:

- `TransformersWrapper` is the Hugging Face path. Passing a string model name or
  tokenizer name can trigger downloads; avoid that in offline or unprovisioned
  environments.
- `vLLMWrapper` supports synchronous vLLM models and TorchRL's async vLLM
  backend. The async path is recommended for high-throughput GPU serving but
  requires the `llm-vllm` dependency set and compatible GPU memory.
- `SGLangWrapper` connects to an existing SGLang server URL or an async SGLang
  backend. It requires `llm-sglang` dependencies and server lifecycle planning.

## LLMCollector

Use `LLMCollector` when collection is dialogue-turn based rather than frame
based. Key constructor facts:

- `env` may be an `EnvBase` instance or a factory.
- Pass either `policy` or `policy_factory`; use a factory when the wrapper/model
  is not safely serializable.
- `dialog_turns_per_batch` is required unless completed trajectories are yielded.
- `total_dialog_turns=-1` means unbounded until shutdown.
- `yield_completed_trajectories=True` yields completed dialogues; ensure the env
  or reward/step transforms set `done`, otherwise collection can wait forever.
- `yield_only_last_steps=True` implies completed trajectories and is incompatible
  with `reset_at_each_iter=True` and explicit `flatten_data`.
- If a replay buffer or queue is supplied, the collector writes to it instead of
  yielding raw batches; `flatten_data` defaults to true with a replay buffer.
- `track_policy_version=True` appends a policy-version transform and records the
  version in data. It is not supported with `AsyncEnvPool` unless the transform
  is attached manually.

When a user's question is about generic collector backends, replay buffers, or
storage/sampling, route away from this sub-skill. Stay here only for
LLM-specific batch semantics, response/history keys, policy version tracking,
and LLM weight synchronization.

## Reward shaping and tool transforms

LLM reward transforms should keep reward shapes compatible with sequence losses:

- sparse sequence rewards are usually shaped like `(*batch, 1, 1)`;
- dense token rewards are usually shaped like `(*batch, num_tokens, 1)`;
- the `done` and `terminated` flags must be set when completion criteria are met
  to avoid endless collectors;
- history/text/tokens modes must extract response text from the matching key;
- parsing errors should produce safe low rewards or explicit diagnostics rather
  than crashing a long rollout.

Tool execution is handled through transforms such as `PythonInterpreter` or
MCP-oriented transforms. Treat tool execution as side-effecting: set short
timeouts, limit interpreter pools, isolate untrusted code, and prefer service
mode only when many envs would otherwise each own their own Python process.

## Objectives: GRPO, SFT, distillation

### GRPO family

`GRPOLoss(actor_network=None, *, clip_epsilon=0.2,
kl_mask_threshold=None, aggregation="token_mean", entropy_bonus=True,
entropy_coeff=0.01, kl_to_ref_coeff=None, kl_to_inference_coeff=None,
masking_strategy="sft", ...)` consumes LLM token/log-prob keys. Defaults from
the accepted keys are:

- `advantage`: `"advantage"`
- `action`: `("tokens", "full")`
- `sample_log_prob`: `("log_probs", "full")`
- `ref_log_probs`: `("next", "ref_log_probs", "full")`

Use `set_keys(...)` if your wrapper or replay data uses alternate nested keys.
Keep the actor in eval mode during GRPO updates; train/eval drift changes
importance sampling and shows up as unstable ESS or KL diagnostics. Match
`masking_strategy` to the data pipeline: `"sft"` for response-token masks,
`"rlhf"` for assistant-token masks in multi-turn chat, and `"generic"` for all
valid attention-mask tokens.

DAPO/CISPO variants share the same family and are reference-only for expensive
training unless dependencies and runtime are explicitly provisioned.

### SFT

`SFTLoss(actor_network, tokenizer=None, tokenizer_kwargs=None,
reduction="mean", normalize_by_seq_length=True, kl_to_ref_coeff=None,
loss_function="sft", beta=0.1, device=None)` expects chat history and optional
reference log-probability keys. Defaults include:

- `history`: `("history", "full")`
- `ref_log_prob`: `("next", "ref_log_probs", "full")`
- `log_probs`: `("log_probs", "full")`

The tokenizer must be available, either explicitly or on the actor wrapper.
For KL-regularized SFT, compute or retrieve reference log-probs before the loss.
For `loss_function="minor_sft"`, KL regularization is implicit and explicit
`kl_to_ref_coeff` should not be used.

### Distillation

Distillation utilities use token-level KL estimates and are useful when a
student wrapper should imitate a reference policy. They require the same care
around tokenizer/template compatibility and log-prob key alignment.

## Prompt and reward datasets

`PromptData.from_dataset(...)` and `PairwiseDataset.from_dataset(...)` are
convenience loaders for public LLM datasets. They may require the `datasets`
package, network/cache access, and local storage. For deterministic agents,
prefer predownloaded/local datasets (`from_disk=True`) or small synthetic
TensorDict fixtures until the user authorizes downloads.

`RewardData` and `PairwiseDataset` model chosen/rejected data for reward-model
training. Pairwise preprocessing filters identical chosen/rejected responses and
short summaries.

## Weight synchronization and policy versions

LLM serving often separates the training model from inference replicas. TorchRL
exposes vLLM and SGLang weight synchronization schemes in `torchrl.weight_update.llm`:

- vLLM: `VLLMWeightSyncScheme`, `VLLMDoubleBufferSyncScheme`, associated senders,
  receivers, transports, and `get_model_metadata`.
- SGLang: `SGLangWeightSyncScheme`, `SGLangWeightSender`,
  `SGLangCollectiveTransport`, and `get_sglang_model_metadata`.

Use these only when all of the following are true: model architecture is loaded,
serving workers are live, process groups/ports are assigned, GPU devices are
known, and the collector/policy version tracking plan is explicit. After each
weight update, increment or verify policy versions so collected samples carry
the behavior-policy version used to produce them.

## Reference-only examples and safe adaptation

The source examples for LLM tools, RLHF, GRPO, vLLM, SGLang, and Ray collectors
are not bundled as runnable helpers because they commonly require model
downloads, GPU serving memory, Ray clusters, web/browser services, credentials,
or long training. Use them as design evidence only. For safe local validation,
start with schema/service imports and small TensorDict fixtures from the bundled
scripts instead of running LLM training examples.
