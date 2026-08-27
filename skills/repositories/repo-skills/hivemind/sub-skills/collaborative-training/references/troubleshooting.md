# Collaborative Training Troubleshooting

## Purpose

Read this when optimizer wrapping, averaging rounds, state sharing, or the ALBERT example fails.

## 1) Import or install failures

**Symptoms**

- `ModuleNotFoundError` for `numpy`, `torch`, `grpcio-tools`, `pydantic`, or `uvloop`
- `hivemind` imports fail before you can create a DHT or optimizer

**Likely causes**

- the package was installed into a different Python environment
- the editable install was attempted without the required build tools
- the optional ALBERT extras were never installed

**Recovery**

1. Run `python scripts/check_install.py`.
2. If you are using a local checkout, reinstall with `pip install -e . --no-build-isolation` after making sure `grpcio-tools` is installed.
3. Use the same environment for every peer.
4. For the ALBERT recipe, run `python scripts/check_install.py --check-albert` and install the missing extras listed there.

## 2) `Optimizer` never averages or never advances the epoch

**Symptoms**

- the model keeps training locally but no averaging log appears
- `local_epoch` never changes
- peers seem to run but never synchronize

**Likely causes**

- `run_id` does not match across peers
- `target_batch_size` is too large for the current swarm
- `matchmaking_time` is too short for the network latency
- the peer is stuck in the wrong `client_mode`

**Recovery**

- confirm that every peer uses the same `run_id`
- reduce `target_batch_size` for small test runs
- increase `matchmaking_time` on slow or wide-area networks
- make sure peers behind firewalls use `client_mode=True`

## 3) `load_state_from_peers` times out or returns stale state

**Symptoms**

- a late-joining peer cannot catch up
- the first local step is wasted or the optimizer state looks inconsistent

**Likely causes**

- no peer is advertising loadable state
- the state-sharing window expired
- the peer joined before the swarm had formed

**Recovery**

- call `load_state_from_peers()` before the first minibatch when joining a running swarm
- keep `allow_state_sharing` enabled on at least one healthy peer
- increase the load-state timeout only after verifying that the swarm is reachable

## 4) `reuse_grad_buffers=True` misuse

**Symptoms**

- gradients disappear unexpectedly
- `zero_grad()` appears to break accumulation
- training diverges after enabling the memory-saving path

**Likely cause**

- `reuse_grad_buffers=True` changes the expected gradient lifecycle

**Recovery**

- only use this mode when you understand that the optimizer expects a different `zero_grad` pattern
- if you want the simplest behavior, turn it off first and get the basic training loop working

## 5) Compression confusion

**Symptoms**

- numerical error is larger than expected
- an 8-bit path behaves differently from the float16 path
- `BlockwiseQuantization` errors mention `bitsandbytes`

**Likely causes**

- the selected compression is too aggressive for the tensor type
- the optional `bitsandbytes` package is missing for blockwise compression

**Recovery**

- start with `NoCompression` or `Float16Compression`
- switch to `Uniform8BitQuantization` or `Quantile8BitQuantization` only after checking the error budget
- treat `BlockwiseQuantization` as optional and install `bitsandbytes` only if you really need that path

## 6) ALBERT example problems

**Symptoms**

- the preprocessing step cannot find the tokenizer or dataset
- `wandb` prompts for login or fails to report
- trainers never begin averaging with peers

**Likely causes**

- the optional example dependencies are missing
- the tokenized dataset was never generated
- peer addresses are wrong or unreachable

**Recovery**

- run `python scripts/check_install.py --check-albert`
- make sure the tokenized dataset and tokenizer directories exist before starting trainers
- verify the peer addresses copied from the first peer's output
- use `--client_mode` when the trainer is behind a firewall or NAT

## 7) When to stop

Stop local debugging and escalate when the issue depends on:

- network connectivity to another peer you cannot reach
- a missing GPU for the example trainer
- a missing optional package that you are not allowed to install
- a version mismatch across peers that you cannot normalize
