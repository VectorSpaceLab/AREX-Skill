# Advanced workflow troubleshooting

| Surface | Symptom | Recovery |
| --- | --- | --- |
| GP | Covariance shape not `(n, n)` or conditional fails | Ensure `X`/`Xnew` are 2-D with columns equal to `input_dim`; check kernel active dimensions. |
| GP | Noisy observations modeled with `Latent` unexpectedly | Use `Marginal` for Gaussian-noise observations unless the latent function is itself sampled. |
| ODE | `n_theta` or `n_states` error | Match `theta` length to `n_theta`; match `y0` and derivative count to `n_states`. |
| ODE | Observed shape mismatch | Use observed arrays shaped like `(len(times), n_states)`. |
| ODE | Unsupported return type | Return list/array of derivatives, not dicts/sets/nested unsupported structures. |
| VI | NaN loss | Check finite initial logp, lower learning rate, scale data, or simplify model. |
| VI/minibatch | Wrong posterior scale | Set likelihood `total_size` for minibatches and ensure equal leading dimension. |
| Approximation sample lacks expected variables | Approximation built outside intended model context or transformed inclusion mismatch | Build and sample inside the model context; decide whether transformed variables are needed. |
