# RL Zoo configuration semantics

RL Zoo training loads one algorithm-specific config source, selects one environment entry, preprocesses special keys, and then passes the remaining values to the Stable-Baselines3 algorithm constructor. Use this reference to reason about that config stage before delegating actual training execution.

## Config source forms

| Source form | Runtime contract | Static-validation note |
| --- | --- | --- |
| YAML file | Root object is a mapping from environment id, `default`, or `atari` to a hyperparameter mapping. YAML anchors and merge keys are fine after YAML loading. | The bundled validator parses YAML with `yaml.safe_load`; it does not run training. |
| Python file | File must define a top-level `hyperparams` dictionary keyed like the YAML root. | The validator statically inspects literal/dict-style assignments by default. Use `--import-python` only for trusted files that build configs dynamically. |
| Python module | Importable module must expose `hyperparams`. | Static inspection can resolve importable module files; `--import-python` executes module top-level code. |

## Entry selection

When a config is loaded for `--env <env_id>`:

1. An exact top-level `<env_id>` entry wins.
2. If no exact entry exists and the environment is Atari, the `atari` entry is used.
3. If no exact entry exists and the environment is not Atari, the `default` entry is used.
4. If the selected entry is absent, training fails before the model is created.

For static checks, pass `--env-id` and, for Atari fallback checks, `--env-kind atari` to `scripts/validate_hyperparams_config.py`.

## Special key semantics

| Key | Accepted shape | Runtime meaning and pitfalls |
| --- | --- | --- |
| `n_timesteps` | Positive int/float; YAML often uses `!!float 1e6` | Required by ordinary config entries. `--n-timesteps` can override it at command time, but an incomplete config is still a portability risk. |
| `policy` | Policy name string (`MlpPolicy`, `CnnPolicy`, `MlpLstmPolicy`) or dotted class path; Python configs may use class objects | Dotted paths are imported dynamically; class implementation details belong to the custom-components sub-skill. |
| `n_envs` | Positive integer | Number of parallel training environments. Save/eval/checkpoint frequencies are divided by this in the training layer. |
| `learning_rate`, `clip_range`, `clip_range_vf`, `delta_std` | Number or `lin_<float>` string | `lin_0.001` becomes a linear schedule from the initial value to zero. Other strings usually fail preprocessing. |
| `normalize` | Boolean, mapping, or Python-expression string returning a mapping/bool | `True` wraps with VecNormalize. Mapping/string forms can choose `norm_obs`/`norm_reward`; when `gamma` is also present, the runtime copies it into normalization kwargs. String forms are evaluated as Python. |
| `policy_kwargs` | Mapping or Python-expression string returning a dict | YAML strings such as `"dict(net_arch=[64, 64], activation_fn=nn.ReLU)"` are evaluated at runtime. YAML mapping form is also valid for literal values. |
| `replay_buffer_class` | Python-expression string or class object | Used by HER/off-policy configs. Strings such as `HerReplayBuffer` are evaluated in the training module context. |
| `replay_buffer_kwargs` | Mapping or Python-expression string returning a dict | Same eval trust boundary as `policy_kwargs`. |
| `env_kwargs` | Mapping | Passed to the environment constructor. In config files this should be a mapping; CLI `--env-kwargs` uses a different key:value parser. |
| `monitor_kwargs` | Mapping or Python-expression string returning a dict | Configures Monitor info keywords; goal-env success metrics often need `info_keywords=('is_success',)`. |
| `env_wrapper` | String, single-key mapping, or list mixing both | Each string or mapping names one Gym wrapper. A mapping must have exactly one wrapper target key; its value is kwargs. |
| `vec_env_wrapper` | Same grammar as `env_wrapper` | Applies to the vectorized env before normalization/frame stacking. Prefer the dedicated `normalize` and `frame_stack` keys for those two built-ins. |
| `callback` | String, single-key mapping, list mixing both; Python configs may use callback objects | Same list/dict indentation rules as wrappers. CLI overrides must evaluate to a string/list, so quoted strings are common. |
| `frame_stack` | Positive integer | Applies VecFrameStack through a dedicated config key after vector-env construction and normalization handling. Avoid also adding a `VecFrameStack` `vec_env_wrapper`. |
| `train_freq` | Integer or two-item list such as `[1, "episode"]` | List form is converted to a tuple for off-policy algorithms. |
| `noise_type`, `noise_std` | String and numeric pair | Off-policy action-noise helper. Use together; unknown noise strings fail at runtime. |

## Wrapper, VecEnv wrapper, and callback grammar

Single target without kwargs:

```yaml
env_wrapper: gymnasium.wrappers.FlattenObservation
```

List with kwargs:

```yaml
env_wrapper:
  - rl_zoo3.wrappers.FrameSkip:
      skip: 2
  - gymnasium.wrappers.transform_observation.GrayscaleObservation:
      keep_dim: true

callback:
  - stable_baselines3.common.callbacks.StopTrainingOnMaxEpisodes:
      max_episodes: 3
```

Common bad indentation creates a mapping with more than one key in a list item; the runtime raises a formatting assertion. The validator catches this shape before training.

## StoreDict-style CLI override grammar

`--hyperparams`, `--env-kwargs`, and `--eval-env-kwargs` all parse tokens of the form `key:value`. The parser splits only at the first colon, then evaluates the value as Python code.

Examples:

```bash
--hyperparams learning_rate:0.001 policy_kwargs:"dict(net_arch=[64, 64])"
--env-kwargs g:8.0 render_mode:"'rgb_array'"
--eval-env-kwargs g:5.0
--hyperparams callback:"'rl_zoo3.callbacks.RawStatisticsCallback'"
```

Important consequences:

- Numbers, booleans, lists, tuples, dicts, and `dict(...)` expressions can be written directly.
- Literal strings must be quoted as Python strings inside the shell token, for example `name:"'value'"`.
- Callback and wrapper class-path overrides usually need an evaluated string, hence the nested quotes.
- Values are evaluated with Python `eval`; never feed untrusted config files or CLI override strings into an RL Zoo process.

## Validator limits

`scripts/validate_hyperparams_config.py` is a static checker. It can catch missing entries, missing required fields, malformed wrapper/callback mappings, bad schedule strings, and unparsable eval strings. It cannot prove that an environment id is registered, a custom class path imports, optional simulator packages are installed, or an algorithm/env pair will learn correctly. Route those runtime checks to the sibling skill that owns execution or custom components.
