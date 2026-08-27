# Discriminator and latent config notes

## Field map

| Field | Used by | What it changes | Practical note |
| --- | --- | --- | --- |
| `num_disc_obs_steps` | AMP, ADD, ASE task envs | Number of temporal discriminator frames; also drives the history buffer length | AMP/ASE use multi-step history; ADD uses `1` for a one-step difference discriminator. |
| `disc_dof_vel_obs` | AMP, ASE via `AMPEnv` | Whether discriminator velocity obs includes DOF velocity | Default is `true`; some task envs in other routes override it to `false`. |
| `disc_buffer_size` | AMP, ADD, ASE | Replay buffer size for discriminator training data | Larger buffers reduce overfitting to the latest rollout but cost memory. |
| `disc_replay_samples` | AMP, ADD, ASE | How many rollout samples are added to replay once the buffer is full | Lower it if the discriminator starts seeing too much stale data. |
| `disc_grad_penalty` | AMP, ADD, ASE | Gradient penalty weight on discriminator logits | AMP/ASE defaults are stronger than ADD in the shipped configs. |
| `disc_logit_reg` | AMP, ADD, ASE | L2 regularization on discriminator logit weights | Useful if logits saturate or overfit. |
| `disc_reward_scale` | AMP, ADD, ASE | Scales the discriminator reward before it is mixed into PPO return | If the agent ignores imitation, check this before changing the task reward. |
| `task_reward_weight` | AMP, ADD, ASE | Multiplies task reward before mixing with adversarial reward | Set to `0` for pure imitation; increase it for task-conditioned control. |
| `disc_reward_weight` | AMP, ADD, ASE | Multiplies the adversarial reward before mixing with task reward | Balance this against `task_reward_weight` rather than changing the env first. |
| `latent_dim` | ASE | Size of the latent skill code and encoder output | Must match the actor/critic latent input shape and the encoder head. |
| `latent_time_min` | ASE | Minimum lifetime of a sampled latent before resampling | Smaller values make the skill code change more often. |
| `latent_time_max` | ASE | Maximum lifetime of a sampled latent before resampling | Larger values let one latent persist longer across the rollout. |
| `enc_reward_weight` | ASE | Reward weight for encoder alignment | If the encoder route is weak, increase it before changing the model shape. |
| `diversity_weight` | ASE | Actor-side diversity regularization weight | Nonzero values encourage different actions for different latents. |
| `diversity_tar` | ASE | Target action-diversity ratio | Tune together with `diversity_weight`; otherwise the diversity term can dominate or vanish. |
| `default_reset_prob` | ASE env | Probability of resetting the character to a default pose on env reset | Helps ASE mix motion-reset and default-pose starts. |

## Discriminator observation construction

### AMP / ASE
- `AMPEnv` builds discriminator history with `num_disc_obs_steps` frames.
- The stored history is pulled from the live character state: `root_pos`, `root_rot`, `root_vel`, `root_ang_vel`, `joint_rot`, `dof_vel`, and `body_pos`.
- `compute_disc_obs(...)` reuses the DeepMimic target-observation helper for the pose part and appends velocity features.
- When `global_obs` is false, heading-normalized observations are used.
- When `root_height_obs` is false, the root-height term is removed from the pose observation path.
- `disc_dof_vel_obs` toggles whether DOF velocity appears in the discriminator velocity observation.
- `key_bodies` decide whether key-body positions are included.
- `fetch_disc_obs_demo(...)` samples motion frames from the motion library, so the demo discriminator observation must align with the current env config and motion asset.

### ADD
- `ADDEnv` uses the same basic discriminator observation family, but the training signal is based on a difference: `disc_obs_demo - disc_obs`.
- The difference is normalized by `DiffNormalizer` before it reaches the discriminator.
- The discriminator is trained on the zero-difference anchor (`pos_diff`) versus replayed difference samples.
- In the shipped ADD config, `num_disc_obs_steps` is `1`, so the discriminator sees a single-step difference observation.

## Reward composition

### AMP and ADD
```text
r = task_reward_weight * task_r + disc_reward_weight * disc_r
```

### ASE
```text
r = task_reward_weight * task_r + disc_reward_weight * disc_r + enc_reward_weight * enc_r
```

### Discriminator reward
- The discriminator reward comes from the discriminator logit after sigmoid conversion.
- A small floor is used inside the log term to avoid `log(0)`.
- `disc_reward_scale` multiplies the final reward before it is mixed with task reward.

### Encoder reward in ASE
- The encoder sees discriminator observations and predicts a normalized latent vector.
- The encoder reward is a clipped alignment score between the target latent and the encoder prediction.
- In practice, treat it as a positive cosine-like shaping term: if the latent prediction and target latent align, the reward rises; if they disagree, it is clipped at zero.

## ASE latent routing

### Latent sampling and reset timing
- The latent buffer stores one latent vector per environment.
- At reset time, ASE samples a normalized latent from Gaussian noise.
- The latent lifetime is randomized between `latent_time_min` and `latent_time_max`.
- When the env time reaches the latent reset time, the agent resamples latents for the affected environments.

### Diversity regularization
- ASE can add a diversity loss to the actor.
- The loss compares the current action mean against the action mean under a fresh latent on the same observation.
- The target ratio is controlled by `diversity_tar`.
- If the diversity term becomes noisy, tune `diversity_weight` first; only then revisit `diversity_tar`.

### Default-pose reset
- `ASEEnv` can reset a subset of environments to the default character pose according to `default_reset_prob`.
- This makes latent sampling and reset behavior less tied to a single motion trajectory.
- If the skill collapses to one reset style, adjust `default_reset_prob` before touching the policy architecture.

## Shape and checkpoint sanity
- Changing `num_disc_obs_steps` changes discriminator input shape.
- Changing `disc_dof_vel_obs` changes discriminator input shape.
- Changing `latent_dim` changes the actor, critic, and encoder interfaces in ASE.
- Do not reuse checkpoints across those shape changes unless the full config family was regenerated.
