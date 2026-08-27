# 1D Sequence Troubleshooting

Use this reference when `Unet1D`, `GaussianDiffusion1D`, `Dataset1D`, or `Trainer1D` fails due to tensor layout, invalid hyperparameters, sampling settings, or training-loop assumptions.

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `seq length must be ...` | Tensor length axis does not match `seq_length`, or `channel_first` was set incorrectly. | Default shape is `(batch, channels, seq_length)`. For channel-last data, transpose or use a wrapper and `channel_first=False`. |
| `Conv1d` expected channels mismatch | Bare public `Unet1D` received `(batch, seq_length, channels)`. | Transpose to channel-first, or wrap `Unet1D` as shown in workflows. |
| `objective must be either ...` | Unsupported objective string. | Use exactly `'pred_noise'`, `'pred_x0'`, or `'pred_v'`. |
| `unknown beta schedule` | Unsupported beta schedule. | Use exactly `'cosine'` or `'linear'`. |
| Assertion during construction with `sampling_timesteps` | `sampling_timesteps > timesteps`. | Use `None`, equal to `timesteps`, or smaller. |
| `unexpected keyword argument 'self_cond'` | 2.3.1 self-conditioning keyword mismatch. | Prefer `self_condition=False` or wrap the model to accept `self_cond` and forward as `x_self_cond`. |
| Non-finite loss | Data scaling, unstable custom model, AMP, or schedule issue. | Start with normalized `[0, 1]` data, `timesteps=8`, `sampling_timesteps=4`, `beta_schedule='cosine'`, and `amp=False`. |
| `number of samples must have an integer square root` | `Trainer1D(num_samples=...)` is not square. | Use `1`, `4`, `9`, `16`, `25`, etc. |
| User expects FID or built-in generated-sequence metrics | `Trainer1D` intentionally has no sample metric. | Add task-specific metrics outside the package trainer loop. |
| Mixed precision or multi-GPU differs from plain run | `Trainer1D` uses Accelerate. | Verify CPU/single GPU with `amp=False`, then use `accelerate config` and `accelerate launch`. |

Fast isolation: run the bundled sequence smoke on CPU, print the user's tensor shape, match `seq_length` and `channels`, verify valid objective/schedule, then construct `Dataset1D` and `Trainer1D` only after direct loss/sample passes.
