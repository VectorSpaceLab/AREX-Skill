# Motion-imitation config tuning

Use this checklist when modifying a DeepMimic, AWR, LCP, or vault/static-object recipe.

## Good edit order

1. Pick the right character family and motion clip.
2. Update `motion_file` and any matching `char_file`, `key_bodies`, `contact_bodies`, `ref_char_offset`, or `init_pose` values.
3. Tune reward and termination settings.
4. Tune the agent hyperparameters.
5. Train a fresh model and only then test it with a checkpoint.

## Environment knobs

| Knob | What it controls | Tuning notes |
| --- | --- | --- |
| `motion_file` | The reference clip or dataset the env tracks | Must point to an existing motion pickle or dataset YAML. Single-clip recipes and multi-motion dataset recipes both use this field. |
| `reward_pose_w`, `reward_vel_w`, `reward_root_pose_w`, `reward_root_vel_w`, `reward_key_pos_w` | Relative weight of each reward term | The reward is a weighted sum of exponential tracking terms. Increase one weight to emphasize that term relative to the others. |
| `reward_pose_scale`, `reward_vel_scale`, `reward_root_pose_scale`, `reward_root_vel_scale`, `reward_key_pos_scale` | Sharpness of each reward term | Larger scales make the reward harsher around tracking error; smaller scales tolerate more deviation. |
| `pose_termination` | Whether pose divergence can fail the episode early | Turn it off only while debugging. If it is on, a too-small distance threshold can end episodes almost immediately. |
| `pose_termination_dist` | Max tolerated pose error before fail | Typical values in this repo are `0.5`, `0.7`, or `1.0` meters depending on the character and task. |
| `enable_tar_obs` | Adds future target observations to the policy input | When enabled, the agent/model must be trained with the larger observation space. |
| `tar_obs_steps` | Future horizons, in simulator steps, for target obs | Keep the list non-empty. The shipped recipes commonly use `[1, 2, 3]`. |
| `joint_err_w` | Per-joint pose error weights | The vector length must equal the number of joints minus one. Use this to emphasize feet, hands, spine, or weapon-bearing links. |
| `global_obs` / `root_height_obs` / `enable_phase_obs` / `num_phase_encoding` | Observation layout controls | Copy the existing recipe defaults unless you know the model input layout you want. Changing these values changes the observation shape. |
| `key_bodies` / `contact_bodies` | Which bodies matter for tracking and fall detection | Keep them consistent with the character asset and the task. Incorrect lists can break reward shaping or termination. |
| `objects` | Static-object placement for vault recipes | Only used by `StaticObjectsEnv`. Each entry defines a rigid object asset and its placement. |
| `zero_center_action` | Action centering used by some recipes | Preserve it when copying G1, PI+, or vault recipes unless you know the target action convention. |

## How the reward is assembled

The DeepMimic-style env reward is built from exponential terms over pose, velocity, root pose, root velocity, and key positions. That means:

- the `*_w` fields choose which terms matter most,
- the `*_scale` fields choose how quickly each term decays with error,
- and `joint_err_w` changes the per-joint contribution to pose error before the reward is computed.

A practical rule: change one weight or one scale at a time, then rerun a short test.

## Agent knobs

| Knob | Scope | Tuning notes |
| --- | --- | --- |
| `steps_per_iter` | PPO/AWR/LCP base agent | Number of rollout steps before one optimization pass. Larger values collect more data per update. |
| `iters_per_output` | PPO/AWR/LCP base agent | Controls how often training logs and checkpoints are written. |
| `test_episodes` | PPO/AWR/LCP base agent | Number of evaluation episodes used during training-time output. `run.py --mode test` can still override this from the command line. |
| `actor_epochs` / `critic_epochs` | PPO/AWR/LCP base agent | Number of optimization sweeps over each buffer. More epochs increase compute per iteration. |
| `actor_batch_size` / `critic_batch_size` | PPO/AWR/LCP base agent | These are multiplied by `num_envs` inside the agent code before minibatching. |
| `td_lambda` | PPO/AWR/LCP base agent | Return estimator tradeoff. The shipped recipes use `0.95`. |
| `ppo_clip_ratio` | PPO and LCP actor loss | PPO clipping threshold. Wider clipping allows larger policy updates. |
| `norm_adv_clip` | PPO and LCP actor loss | Advantage clipping after normalization. |
| `action_bound_weight` | PPO/AWR/LCP | Adds a penalty when the actor moves outside the action bounds. |
| `action_entropy_weight` | PPO/AWR/LCP | Encourages exploration by rewarding entropy. |
| `action_reg_weight` | PPO/AWR/LCP | Regularizes policy parameters. |
| `critic_eval_batch_size` | PPO/AWR/LCP optional | Chunk size for critic evaluation during target/value computation. Use it when memory is tight. |
| `awr_temp` | AWR only | Converts normalized advantage to an action weight. Smaller values sharpen the weighting. |
| `a_weight_clip` | AWR only | Caps the AWR action weights. Lower values reduce the influence of high-advantage samples. |
| `lcp_weight` | LCP only | Multiplies the Lipschitz smoothness penalty. Larger values make the policy smoother but can hurt task performance. |

## Practical starting points

- If the policy never reaches the target motion, first check `motion_file`, `key_bodies`, `contact_bodies`, and `pose_termination_dist`.
- If the policy learns but looks too jerky, tune `reward_*_scale`, then `lcp_weight` for LCP or `awr_temp` / `a_weight_clip` for AWR.
- If the observation or checkpoint no longer loads, assume the env shape changed and retrain.
- If the recipe uses the wrong character family, do not try to patch it with a checkpoint swap; fix the env/agent pair instead.
