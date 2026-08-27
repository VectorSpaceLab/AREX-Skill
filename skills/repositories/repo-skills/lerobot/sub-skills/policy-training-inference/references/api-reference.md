# API and serialization reference

The following signatures were checked against the installed LeRobot 0.6.2
package. Heavy model classes are intentionally lazy; class import can still
raise an optional-dependency error.

## Policy API

```python
from lerobot.configs import PreTrainedConfig
from lerobot.policies import (
    PreTrainedPolicy,
    get_policy_class,
    make_policy,
    make_policy_config,
    make_pre_post_processors,
)

make_policy_config(policy_type: str, **kwargs) -> PreTrainedConfig
get_policy_class(name: str) -> type[PreTrainedPolicy]
make_policy(
    cfg: PreTrainedConfig,
    ds_meta=None,
    env_cfg=None,
    rename_map: dict[str, str] | None = None,
    defer_weight_load: bool = False,
) -> PreTrainedPolicy
make_pre_post_processors(
    policy_cfg: PreTrainedConfig,
    pretrained_path: str | None = None,
    pretrained_revision: str | None = None,
    **kwargs,
) -> tuple[PolicyProcessorPipeline, PolicyProcessorPipeline]
```

`PreTrainedPolicy(config, *inputs, **kwargs)` requires a concrete
`PreTrainedConfig`. Its subclass contract requires `config_class` and `name`,
plus implementations of `get_optim_params`, `reset`, `forward`,
`predict_action_chunk`, and `select_action`.

```python
PreTrainedPolicy.from_pretrained(
    pretrained_name_or_path,
    *, config=None, force_download=False, resume_download=None,
    proxies=None, token=None, cache_dir=None, local_files_only=False,
    revision=None, strict=False, **kwargs
) -> PreTrainedPolicy
```

The policy loader reads `config.json` and `model.safetensors` from a local
folder or the Hub, moves the model to `config.device`, and calls `eval()`. It
reports missing/unexpected safetensor keys; `strict=True` turns key mismatch
into a load failure. A local checkpoint should contain at least
`config.json` and `model.safetensors` for this loader.

`forward(batch)` returns `(loss, output_dict_or_none)` for training.
`select_action(batch, **kwargs)` returns an action for environment execution;
`predict_action_chunk(batch, **kwargs)` returns a chunk for chunking policies.
`reset()` clears episode state. `drop_queued_actions()` clears action queues
without clearing observation history and is relevant when task conditioning
changes mid-episode. `supports_rtc()` and `supports_text_generation()` expose
optional rollout capabilities.

## Processor API

```python
from lerobot.processor import (
    DataProcessorPipeline, PolicyProcessorPipeline, ProcessorStep,
    ProcessorStepRegistry, DeviceProcessorStep,
    NormalizerProcessorStep, UnnormalizerProcessorStep,
)

DataProcessorPipeline(
    steps=..., name="...", to_transition=..., to_output=...
)
pipeline(data) -> converted output
pipeline.step_through(data) -> iterable[EnvTransition]
pipeline.transform_features(initial_features) -> transformed_features
pipeline.process_observation(observation) -> observation
pipeline.process_action(action) -> action
pipeline.reset() -> None
```

A `ProcessorStep` implements `__call__(transition)` and
`transform_features(features)`. It may provide `get_config`, `state_dict`,
`load_state_dict`, `save_artifacts`, and `reset`. `ProcessorStepRegistry` maps
serialized names to classes. The step order is serialized and is a behavioral
contract; do not reorder steps casually.

```python
DataProcessorPipeline.save_pretrained(
    save_directory=None, *, repo_id=None, push_to_hub=False,
    card_kwargs=None, config_filename=None, **kwargs
)
DataProcessorPipeline.from_pretrained(
    pretrained_model_name_or_path, config_filename, *,
    force_download=False, resume_download=None, proxies=None, token=None,
    cache_dir=None, local_files_only=False, revision=None, overrides=None,
    to_transition=None, to_output=None, **kwargs
)
```

Policy factory checkpoint loading normally requests
`policy_preprocessor.json` and `policy_postprocessor.json`. Stateful processor
steps save their tensors as safetensors alongside those JSON files. Overrides
are keyed by registry name or class name; unused keys are rejected. Relative
and absolute action processor references are reconnected after deserialization.
Groot, MolmoAct2, and EVO1 have additional reconciliation logic.

## Normalization and device path

Canonical policy preprocessing commonly is:

`rename observations -> add batch dimension -> move to policy device -> normalize`

and postprocessing is:

`unnormalize action -> move to CPU`.

Policies may insert tokenizers, image transforms, frame/action adapters, or
relative-action steps. `NormalizerProcessorStep` and
`UnnormalizerProcessorStep` consume feature-specific stats and normalization
modes. Supported mathematical modes are `IDENTITY`, `MEAN_STD`, `MIN_MAX`,
`QUANTILES` (`q01`/`q99`), and `QUANTILE10` (`q10`/`q90`). Missing required stats
raise at processing time; missing stats can also silently leave identity paths,
so inspect the pipeline and stats rather than relying only on construction.

`DeviceProcessorStep(device, float_dtype=None)` recursively moves tensors in
observations, actions, rewards, done/truncated, and complementary data. It
preserves an already-placed CUDA tensor's CUDA device under multi-GPU use,
works around MPS float64, and optionally casts floating tensors. The policy
config's device is not a substitute for checking backend availability.
