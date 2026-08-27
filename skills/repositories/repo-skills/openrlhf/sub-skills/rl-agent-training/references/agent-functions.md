# Reward and Agent Functions

OpenRLHF uses agent executors to turn prompts into token-level rollout samples. Single-turn reward files, multi-turn agents, VLM agents, and OpenAI-compatible executors all plug into this path.

## Single-turn reward function contract

A local reward function is loaded when `--reward.remote_url` points to a `.py` file. It must define:

```python
def reward_func(queries, prompts, labels, **kwargs):
    ...
    return {"rewards": rewards, "scores": scores, "extra_logs": {...}}
```

Expected behavior:

- `queries`: full prompt plus generated response texts.
- `prompts`: original prompt texts before generation.
- `labels`: values from `--data.label_key`; use data-preparation to choose the correct key.
- `rewards`: tensor-like values used for advantage calculation.
- `scores`: tensor-like values in a filterable range, usually `[0, 1]`, used by dynamic filtering.
- `extra_logs`: optional scalar/tensor diagnostics for experiment logging.

Keep reward functions deterministic where possible. If a reward invokes external services or executes code, add timeouts, sandboxing, and failure-to-zero behavior deliberately.

## HTTP reward URL contract

When `--reward.remote_url` is an HTTP endpoint, OpenRLHF posts JSON shaped like:

```json
{"query": ["prompt+response"], "prompts": ["prompt"], "labels": ["label"]}
```

The response should match the Python reward dict shape for the posted batch. Multiple comma-separated remote URLs are sharded across requests. Keep remote services close to Ray workers to avoid rollout stalls.

## Math reward pattern

A math reward commonly extracts the response from `query[len(prompt):]`, parses a final answer such as `\\boxed{...}`, compares it with the label, and returns binary rewards plus accuracy logging.

Checklist:

- Make answer extraction explicit and robust to missing boxes.
- Treat unparsable responses as reward `0.0`, not as exceptions.
- Return both `rewards` and `scores` if using DAPO/dynamic filtering.
- Log aggregate accuracy, parse failure rate, or format compliance in `extra_logs`.

## Multi-turn agent contract

A multi-turn agent script imports `AgentInstanceBase` and `MultiTurnAgentExecutor`, defines an `AgentInstance`, then exports `AgentExecutor`:

```python
from openrlhf.utils.agent import AgentInstanceBase, MultiTurnAgentExecutor

class AgentInstance(AgentInstanceBase):
    async def reset(self, states: dict, **kwargs):
        return {"observation": states["observation"]}

    async def step(self, states: dict, **kwargs):
        return {
            "rewards": reward_tensor,
            "scores": score_tensor,
            "environment_feedback": feedback_text,
            "done": done,
            "sampling_params": states.get("sampling_params"),
            "extra_logs": {"metric": reward_tensor},
        }

class AgentExecutor(MultiTurnAgentExecutor):
    def __init__(self):
        super().__init__(AgentInstance)
```

`reset()` receives `states["observation"]` and `states["label"]`. `step()` receives:

- `observation_text`: conversation text so far.
- `action_text`: the latest model generation.
- `label`: ground-truth label for the prompt.
- `sampling_params`: current vLLM sampling parameters.

Return `done=True` when the episode is complete. Intermediate turns usually return zero reward and environment feedback that prompts the next model action. Final turns usually return the task reward.

## Agent feedback formatting

The agent executor concatenates `observation_text + action_text + environment_feedback`. Make feedback match the model chat template. For chat-tuned models, include the user turn terminator and assistant generation prefix that the tokenizer/model expects. Bad separators often look like reward collapse or repeated role tokens rather than a Python error.

## VLM multi-turn contract

A VLM agent uses the same `MultiTurnAgentExecutor` contract, plus image handling:

- Dataset prompts can provide initial images through the dataset image key.
- `step()` may return `environment_images`, usually a list of PIL images.
- `environment_feedback` must contain the matching model-specific image placeholder token for each returned image.
- Avoid returning images when the tokenizer/processor lacks multimodal support.

For Qwen-style VLM templates, image feedback may include a placeholder such as `<|vision_start|><|image_pad|><|vision_end|>`, but adjust this to the actual actor model.

## OpenAI-compatible agent server executor

Use an `AgentExecutorBase` subclass when a custom agent library expects OpenAI chat-completions. The OpenRLHF example pattern:

- Starts a local FastAPI server in the vLLM Ray actor.
- Exposes `/v1/chat/completions`, `/v1/models`, and `/tokenize`.
- Uses vLLM to generate completions.
- Stores token traces by `session_id`.
- Stitches prompt/completion token IDs into `observation_tokens` and `action_ranges`.

Override `run_agent(prompt, label, session_id)` to call the local `self.client`. Pass the same `session_id` in each request so all turns are collected for one rollout sample.

## Template generation

Create starter files with:

```bash
python skills/openrlhf/sub-skills/rl-agent-training/scripts/create_reward_or_agent_template.py \
  --kind multiturn \
  --output agent_func.py
```

Then edit the reward logic, environment feedback, model-specific chat formatting, imports, and any external service calls before launching training.

## Safety and reproducibility notes

- Keep file paths passed to `--reward.remote_url` and `--train.agent_func_path` visible to every Ray worker.
- Do not assume local imports from a notebook or parent checkout will exist inside Ray runtime environments.
- Avoid unbounded external API calls inside reward or agent steps; rollout generation waits on them.
- If an agent uses subprocesses, browsers, games, simulators, or code execution, classify the run as unsafe/expensive unless the user confirms sandboxing and resources.
