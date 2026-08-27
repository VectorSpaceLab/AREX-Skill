# Config and hyperparameter troubleshooting

Use this matrix before launching training. The bundled validator can catch static shape issues, but runtime class imports and environment registration still need the sibling execution/component skills.

| Symptom or validator signal | Likely cause | Fix |
| --- | --- | --- |
| `missing-entry`: no exact env entry and no usable fallback | The config has no top-level key for `--env`, and the required `default` or `atari` fallback is absent. | Add an exact env-id entry, add a complete `default` fallback for non-Atari envs, or add a complete `atari` fallback and validate with `--env-kind atari`. |
| `missing-field` for `n_timesteps` or `policy` | The selected entry or fallback is incomplete. | Add `n_timesteps` and `policy` to every entry that may be selected. `--n-timesteps` can override the value later, but a portable config should still declare it. |
| Runtime assertion says to check YAML indentation near a wrapper/callback dict; validator reports `bad-wrapper-item` | A list item under `env_wrapper`, `vec_env_wrapper`, or `callback` became a mapping with more than one key because kwargs were not indented under the class name. | Make every kwargs-bearing list item a single-key mapping, e.g. `- rl_zoo3.wrappers.FrameSkip:` then indent `skip: 2` under that key. |
| `bad-expr` or runtime `SyntaxError`/`NameError` in `policy_kwargs`, `monitor_kwargs`, `normalize`, or replay-buffer fields | A Python-expression string is malformed or references names not available in the training module context. | Prefer YAML mappings for literal values. If you need Python names such as `nn.ReLU`, keep the whole expression as one quoted string, e.g. `policy_kwargs: "dict(activation_fn=nn.ReLU)"`. |
| CLI override seems ignored or parses as the wrong type | `--hyperparams`, `--env-kwargs`, and `--eval-env-kwargs` split `key:value` tokens and evaluate the value. Strings need nested quotes. | Use `learning_rate:0.001` for numbers, `policy_kwargs:"dict(net_arch=[64, 64])"` for dict expressions, and `name:"'literal-string'"` for a literal string. |
| Security concern around eval-based values | RL Zoo uses Python `eval` for StoreDict CLI values and for several config string fields. | Treat YAML/Python configs and override strings as trusted local inputs only. Do not pass unreviewed user text, downloaded snippets, or secrets through these fields. |
| `env id not found` or training suggests a closest match | Gymnasium environment id versions changed, or the optional environment package did not register the id. | Update both the config key and `--env` to the installed env id. For external/custom envs, install/import the package and pass the appropriate gym-package route in the training layer. |
| Optional env package import error | The config names wrappers/envs from Atari, Box2D, MuJoCo, PyBullet, MiniGrid, highway-env, a project package, or another optional dependency that is not installed. | Keep the config syntax here, but route dependency/import verification to the environment/custom-components owner. Do not solve it by weakening the hyperparameter entry unless the env family is intentionally out of scope. |
| Normalization works in training but fails or behaves differently in evaluation | `normalize`, `frame_stack`, custom `vec_env_wrapper`, and saved VecNormalize stats interact with a fixed wrapper order. | Prefer `normalize` for VecNormalize and `frame_stack` for VecFrameStack. Avoid also listing `VecFrameStack` as a `vec_env_wrapper`. Ensure evaluation loads the same saved config/stats and uses matching `env_kwargs`. |
| `monitor_kwargs` errors about missing info keys | A Monitor `info_keywords` entry is configured, but the environment does not put that key in the final episode `info` dict. | Remove the keyword, choose a key emitted by the env, or add a wrapper/custom env change in the custom-components workflow. Goal-style success metrics often use `info_keywords=('is_success',)`. |
| `train_freq` or action-noise preprocessing fails | Off-policy fields use the wrong shape or incomplete pair. | Use `train_freq: [1, "episode"]` or an integer. If `noise_type` is set, also set numeric `noise_std`; use known strings such as `normal` or `ornstein-uhlenbeck`. |

## What the validator cannot prove

- It does not create an environment or import wrapper/callback targets by default.
- It does not know whether a Gymnasium id is registered unless a separate runtime check is run.
- It cannot prove algorithm-specific learning quality, device support, Optuna search-space validity, or log/model artifact correctness.
- It statically inspects Python config files unless `--import-python` is set. Importing a Python config executes top-level code and should be used only for trusted local files.
