# Environment Training

`GRPOTrainer` supports agent training in two ways: stateless `tools=` and stateful `environment_factory=`. Use environments when actions change later observations, reward state is stored across turns, or a sandbox/server controls task progression.

## Core Contract

`environment_factory` must be a zero-argument callable that returns a fresh environment instance. TRL creates one instance per rollout slot, calls `reset(**dataset_row)` at the start of each episode, exposes public methods as model-callable tools, runs the multi-turn loop, and passes the live instances to reward functions as `environments=`.

A minimal environment class has this shape:

```python
class CountingEnv:
    def __init__(self):
        self.count = 0
        self.reward = 0.0

    def reset(self, **kwargs) -> str | None:
        self.count = 0
        self.reward = 0.0
        return "Reach exactly 3 by calling increment."

    def increment(self, step: int) -> str:
        """Increase the counter.

        Args:
            step: Amount to add.
        """
        self.count += step
        self.reward = 1.0 if self.count == 3 else 0.0
        return f"count={self.count}"


def reward_func(environments, **kwargs) -> list[float]:
    return [env.reward for env in environments]
```

Tool methods must be public methods other than `reset`, with typed arguments and docstrings. Avoid generic `step(action)` tools unless the model has no better semantic action surface; named tools such as `guess`, `move`, `bash`, or `submit_answer` are easier for chat templates and models to use.

## Environment Type Selection

| Integration | Use when | Trainer slots | Hidden assumptions |
| --- | --- | --- | --- |
| Custom/OpenEnv wrapper | You control a Python class around an OpenEnv-style client or game server. | Provide `train_dataset`, `environment_factory`, and reward function yourself. | Server must already be reachable; concurrency must support one session per rollout slot. |
| OpenReward | You train against an ORS-speaking environment from the OpenReward catalog, a self-hosted URL, or local ORS server. | `OpenRewardSpec(...).train_dataset`, `.environment_factory`, `.reward_funcs`. | Requires `trl[openreward]`/`openreward`; catalog targets commonly require `OPENREWARD_API_KEY`; self-hosted single-URL servers may need API/session URL overrides. |
| Harbor | You train against sandboxed task suites with instruction, environment image, and verifier. | `HarborSpec(...).train_dataset`, `.environment_factory`, `.reward_funcs`. | Requires `trl[harbor]`, a supported sandbox backend, and documented vLLM-oriented training setup. Docker/E2B/service credentials are outside TRL. |
| `rollout_func` | The normal environment tool loop cannot represent the agent protocol, or an external agent server owns generation. | Return `prompt_ids`, `completion_ids`, `logprobs`, plus optional reward fields. | You own generation, token/logprob alignment, tool masking, and reward forwarding. This API is experimental. |

## OpenEnv Pattern

OpenEnv-style wrappers usually instantiate a client in `__init__` or `reset`, return the first observation from `reset`, expose one method per model action, and store `reward`/`done` state for a reward function. For multi-environment runs, add a dataset routing column such as `env`, select the backing client inside `reset(**kwargs)`, expose all possible tools, and raise `ValueError` when a tool is invalid for the active environment. TRL catches tool exceptions and feeds the error string back as a tool response.

Key settings:

- Increase `max_completion_length` for multi-turn episodes because the limit covers all generated text and tool responses in the episode.
- Set `max_tool_calling_iterations` when an environment can loop indefinitely.
- For OpenEnv servers, ensure `max_concurrent_envs` is at least the generation batch size, commonly `per_device_train_batch_size * steps_per_generation`.
- Store final reward state on the env instance; reward functions can read `environments` and return per-rollout floats or `None` for unrelated environments.

## OpenReward Pattern

`OpenRewardSpec(target, ...)` lazily discovers tasks and tools, then exposes:

- `train_dataset`: chat-format prompts plus `task_index` and optional task metadata.
- `environment_factory`: a zero-arg factory producing per-rollout ORS adapters with dynamically bound typed tool methods.
- `reward_funcs`: default outcome reward using the last non-null reward in the trajectory.

Selection tips:

- Use a catalog name for hosted OpenReward environments and provide `OPENREWARD_API_KEY` when required.
- Use a direct URL for self-hosted ORS servers and set API/session URL overrides when the server is single-host rather than split into API and session subdomains.
- Use `indices` for fixed subsets and `num_tasks` for first-N debugging; they are mutually exclusive.
- For task-specific tools, leave discovery enabled unless probing sessions are too expensive and shared tools are sufficient.

## Harbor Pattern

`HarborSpec(dataset, agent="bash", environment_type="docker")` resolves a Harbor task suite, builds a dataset of task directories, creates a fresh `HarborEnv` per rollout, and computes outcome reward with the task verifier.

Important boundaries:

- TRL uses Harbor as an external-agent harness: the policy model remains in TRL, and tool methods execute into the sandbox. Harbor installed agents that run their own model inside the container are not trainable through this integration because TRL cannot capture policy tokens/logprobs.
- The built-in `bash` harness exposes one `bash(command: str)` tool and expects final answer submission by writing `/workdir/answer.txt`.
- Custom harnesses should subclass `HarborEnv`, add typed public tool methods, keep helpers underscore-prefixed, and use sandbox execution helpers internally.
- `environment_type` is passed through to Harbor; choose `docker` for local daemon-backed runs or a cloud backend such as `e2b` when credentials and cluster policy allow it.

## `rollout_func` Boundary

Use `environment_factory` unless the environment protocol cannot be expressed as typed tools. A `rollout_func(prompts, trainer)` must preserve prompt shape, perform generation itself, and return at least:

```python
{
    "prompt_ids": prompt_ids,
    "completion_ids": completion_ids,
    "logprobs": logprobs,
}
```

Any extra fields are forwarded to reward functions. When using vLLM utilities inside custom rollouts, keep backend setup and scaling concerns in the scaling/backends skill; this sub-skill only covers the contract and routing decision.
