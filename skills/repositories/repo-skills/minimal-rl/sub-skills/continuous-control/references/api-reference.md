# Continuous-Control API Reference

## Purpose

Read this when adapting minimalRL's continuous-action Pendulum algorithms. These contracts are distilled from the DDPG, PPO-Continuous, and SAC scripts.

## Shared assumptions

| Item | Contract |
|---|---|
| Environment family | Pendulum-style continuous control. |
| Observation shape | Length 3 vector. |
| Action shape | One scalar action. |
| Action range | Source scripts assume `[-2, 2]`; DDPG and SAC explicitly scale actions by `2`. |
| Backend | CPU PyTorch is sufficient for the selected skill scope. |
| Training length | Full scripts use many episodes; start with bundled shape smoke checks. |

## DDPG contracts

| Surface | Contract |
|---|---|
| `ReplayBuffer` | deque of `(s, a, r, s_prime, done)` with `buffer_limit=50000` |
| `ReplayBuffer.sample(n)` | returns tensors `s`, `a`, `r`, `s_prime`, `done_mask`; actions are shaped `(batch,1)` float |
| `MuNet.forward(x)` | `Linear(3,128) -> Linear(128,64) -> tanh(fc_mu) * 2`; returns one action |
| `QNet.forward(x, a)` | encodes state and action separately to 64 dims each, concatenates to 128, returns scalar Q |
| `OrnsteinUhlenbeckNoise(mu)` | stateful exploration noise with `theta=0.1`, `dt=0.01`, `sigma=0.1` |
| `train(mu, mu_target, q, q_target, memory, q_optimizer, mu_optimizer)` | samples replay, trains critic to target Q, then trains actor by maximizing critic value |
| `soft_update(net, net_target)` | target update: `target = target * (1 - tau) + source * tau`, `tau=0.005` |
| Hyperparameters | `lr_mu=0.0005`, `lr_q=0.001`, `gamma=0.99`, `batch_size=32` |

## Continuous PPO contracts

| Surface | Contract |
|---|---|
| Class | `PPO` in the continuous script |
| `pi(x, softmax_dim=0)` | returns `(mu, std)` where `mu = 2*tanh(fc_mu)` and `std = softplus(fc_std)` |
| `v(x)` | returns scalar value |
| Data transition | `(s, a, r, s_prime, prob_a, done)` where `prob_a` is the old log-probability scalar in the source loop |
| `make_batch()` | pops `minibatch_size * buffer_size` rollouts and returns a list of minibatches |
| `calc_advantage(data)` | computes TD target and GAE for each minibatch |
| `train_net()` | optimizes clipped PPO objective for `K_epoch=10` over prepared minibatches |
| Hyperparameters | `learning_rate=0.0003`, `gamma=0.9`, `lmbda=0.9`, `eps_clip=0.2`, `rollout_len=3`, `buffer_size=10`, `minibatch_size=32` |

## SAC contracts

| Surface | Contract |
|---|---|
| `ReplayBuffer` | deque of `(s, a, r, s_prime, done)` with `buffer_limit=50000` |
| `PolicyNet.forward(x)` | returns tanh-squashed action and corrected log probability using `log_prob - log(1 - tanh(action)^2 + 1e-7)` |
| `PolicyNet.train_net(q1, q2, mini_batch)` | optimizes `-min(q1,q2) - entropy` and updates `log_alpha` |
| `QNet.forward(x,a)` | state/action encoders concatenate and output scalar Q |
| `QNet.train_net(target, mini_batch)` | smooth-L1 critic update |
| `QNet.soft_update(net_target)` | target update with `tau=0.01` |
| `calc_target(pi, q1, q2, mini_batch)` | computes SAC target with min twin Q and entropy term |
| Hyperparameters | `lr_pi=0.0005`, `lr_q=0.001`, `init_alpha=0.01`, `gamma=0.98`, `batch_size=32`, `target_entropy=-1.0`, `lr_alpha=0.001` |

## Shape rules

- Actor inputs: `(3,)` for one observation or `(batch,3)` for a batch.
- Critic inputs: state `(batch,3)` and action `(batch,1)`.
- Continuous PPO and SAC stochastic policies should preserve action/log-prob shape `(batch,1)` for replay and Q input compatibility.
- If you change action dimension, update every `Linear(..., 1)` action head and every action encoder/input shape together.
