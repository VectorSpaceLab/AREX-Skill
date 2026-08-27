# ALBERT Collaborative-Training Example

## Purpose

Read this when you need the concrete end-to-end collaborative-training recipe that ships with the repository's ALBERT example.

## What this workflow covers

- preprocessing WikiText-103 into the tokenized local dataset layout
- starting the DHT monitor / first peer
- joining with one or more training peers
- tuning collaborative batch and matchmaking settings
- checkpointing and optional Weights & Biases reporting

## Required optional dependencies

The example workflow uses extra packages beyond the base `hivemind` install:

- `transformers`
- `datasets`
- `torch_optimizer`
- `wandb`
- `sentencepiece`
- `requests`
- `nltk`

Use the bundled preflight first:

```bash
python scripts/check_install.py --check-albert
```

That check will report which optional packages are missing.

## Data preparation

The example assumes a local tokenized dataset and tokenizer directory.
The preprocessing stage downloads WikiText-103, uses an ALBERT tokenizer, and writes:

- a tokenized dataset directory
- a tokenizer directory

The safe way to reason about the prep stage is:

1. make sure the data cache is writable
2. make sure network access is available for the one-time dataset/model download
3. let the preprocessing step create the tokenized dataset and tokenizer artifacts

If the downloads are not allowed in your environment, stop here and hand the task back as a network-limited workflow.

## First peer / monitor

The first peer hosts the DHT and records metrics.

Typical settings:

- choose a stable `--run_id`
- pass one or more `--initial_peers` only when joining an existing collaboration
- set `--wandb_project` only if you actually want online logging
- use `--use_google_dns` or explicit announce addresses when public reachability matters

The monitor output should periodically show a step number, loss, and the number of active peers.

## Trainer peers

Trainer peers join with the first peer's visible multiaddresses.

Important knobs:

- `--client_mode` for peers behind firewalls or NAT
- `--matchmaking_time` for slow or unstable networks
- `--batch_size_lead` to begin averaging slightly before the target batch size
- `--gradient_accumulation_steps` and `--per_device_train_batch_size` to fit the GPU memory budget

The example trainer is GPU-oriented, but the base collaborative-training APIs are not tied to GPUs. Treat the trainer as a higher-cost optional path rather than the minimal smoke path.

## Expected log signals

Healthy peers should periodically report lines similar to:

- `Found N initial peers`
- `Loading state from peers`
- `Step #...`
- `Averaged gradients with N peers`
- `Averaged parameters with N peers`

If you never see averaging lines, the usual problem is peer discovery, not the optimizer math.

## Troubleshooting tips

- If the tokenizer is missing, rerun the preprocessing step before starting trainers.
- If the monitor cannot publish metrics, check the DHT addresses first.
- If trainers stall on startup, verify `--initial_peers`, `--client_mode`, and firewall/relay settings.
- If the run uses the wrong batch size, recompute the local-to-global batch relationship from `per_device_train_batch_size`, `gradient_accumulation_steps`, and the number of visible GPUs.
- If `wandb` is not configured, omit the logging flag instead of letting the trainer hang on an account prompt.

## When to stop

Stop local debugging when the issue requires:

- external dataset downloads that are not allowed
- a logged-in Weights & Biases account
- a GPU that is not present
- a peer address you cannot reach from the current network

At that point, report the exact missing artifact or network condition rather than guessing at the trainer code.
