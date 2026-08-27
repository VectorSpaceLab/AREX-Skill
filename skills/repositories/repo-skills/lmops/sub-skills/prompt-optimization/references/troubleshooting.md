# Prompt Optimization Troubleshooting

For shared LMOps install, credential, hardware, and checkout boundaries, also consult `../../../references/troubleshooting.md`. This file covers ProTeGi and Promptist-specific failure modes.

## ProTeGi dependency issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: liquid` | Prompt rendering uses Liquid templates. | Install a compatible Python Liquid package in the run environment, then rerun only after confirming credentials and data. |
| `ModuleNotFoundError: requests` | Provider calls use HTTP requests. | Install `requests`; check outbound network policy before a real provider call. |
| `ModuleNotFoundError: pandas` | Built-in task loaders use dataframes for some datasets. | Install `pandas`; for JSONL-only custom tasks, confirm whether the selected loader really needs it. |
| `ModuleNotFoundError: tqdm` | Optimizer/evaluators show progress bars. | Install `tqdm` or adjust the environment; do not remove progress imports in a shared checkout without review. |
| `ModuleNotFoundError: sklearn` | Classification metrics use scikit-learn. | Install scikit-learn if running built-in evaluation. |
| Multiprocessing pool repeatedly breaks | Provider timeouts, SSL/network failures, worker count too high, or serialization issues. | Lower `--max-threads`, reduce sampled data/prompts, and inspect provider/network errors before increasing concurrency. |

## Provider and credential errors

- ProTeGi needs a chat/completion provider for textual gradients, prediction, and log-likelihood scoring.
- Keep provider credentials outside prompts, logs, scripts, and skill files.
- `--engine` is stored in the config, but the actual provider implementation may still be fixed by the run environment. Do not assume changing `--engine` changes endpoints.
- `401`, `403`, or authentication errors: verify API key scope, model access, and environment/config loading.
- `429`, timeout, SSL, or retry loops: reduce `--max-threads`, reduce `--samples-per-eval`, reduce `--eval-prompts-per-round`, or wait for quota recovery.
- Log-likelihood scoring (`--scorer ll`) uses a completion/logprobs style endpoint; it may fail even when chat-style prediction works.

## Missing or malformed ProTeGi data

Run the bundled builder before a real optimization:

```bash
python scripts/protegi_command_builder.py --help
```

Common layout fixes:

- `ethos`: provide `ethos_ishate_binary_shuf.csv` with semicolon-separated text and numeric score columns.
- `jailbreak`: provide `train.tsv` and `test.tsv`, each line as a JSON conversation, tab, and integer label.
- `liar` and `ar_sarcasm`: provide `train.jsonl` and `test.jsonl`, each record with `text` and integer `label`.
- If files are not ready yet, use `--path-policy warn` for planning and treat builder warnings as a staging checklist.
- If the user wants to convert raw corpus material into this layout, route to `../adaptation-and-training/SKILL.md` first.

## Malformed ProTeGi prompts

- Prompt files must contain a `# Task` section; ProTeGi rewrites that section during optimization.
- Use a `{{ text }}` placeholder so the predictor can render each example.
- Keep labels aligned with the binary `No`/`Yes` task mapping.
- For multiple seed prompts, use comma-separated files and verify they all share task semantics.
- If the builder reports missing headers or placeholders, repair the prompt before spending provider budget.

## Wrong evaluator or scorer names

Supported evaluator names:

- `bf`: brute force
- `ucb`: upper-confidence-bound bandit
- `ucb-e`: UCB-E variant
- `sr`: successive rejects
- `s-sr`: sampled successive rejects
- `sh`: successive halving

Supported scorer names:

- `01`: cached binary correctness
- `ll`: cached log likelihood of the correct label

Unsupported values cause the native program to raise before optimization.

## Promptist rewrite planning problems

Use the offline skeleton first:

```bash
python scripts/promptist_rewrite_skeleton.py --help
```

- The skeleton imports only Python standard-library modules.
- It does not import PyTorch, Transformers, Diffusers, CLIP, TRLX, or Gradio.
- It does not download `microsoft/Promptist`, `gpt2`, Stable Diffusion weights, CLIP weights, or aesthetic scorer weights.
- If the user wants a real local rewrite, confirm model cache/network access, accepted model licenses, PyTorch/Transformers installation, and CPU/GPU expectations.
- Generation constraints from the demo imply `num_return_sequences <= num_beams` when deterministic beam generation is used.

## Promptist RL training problems

Treat RL training as optional/unverified unless the user provides a suitable GPU environment and asks for execution.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Stable Diffusion model fails to load | Missing model cache, denied model access, token/license issue, or wrong model id. | Confirm access out of band; stage model/cache before training. |
| `LOCAL_RANK` missing | Trainer expects distributed CUDA rank variables. | Launch through a distributed runner that sets rank variables; do not run the trainer as a trivial single-process smoke test without adapting it. |
| CUDA out-of-memory | Image generation and CLIP/aesthetic scoring are part of the reward path. | Lower batch/rollout settings, use fewer beams/images, or move to larger GPUs. |
| W&B or model-registry errors | Logging/model access credentials are absent or scoped incorrectly. | Set credentials securely and avoid printing them in logs. |
| Multi-node launch hangs | Wrong main process IP/port, machine rank, process count, or firewall policy. | Validate cluster networking with a small distributed diagnostic before Promptist training. |
| Training runs for too long | PPO config can target large step counts and repeated image generation. | Make a bounded user-approved pilot config; do not treat full training as required repo-skill verification. |

If the request is really about retrieval-based example selection, route to `../example-retrieval/SKILL.md` instead of forcing Promptist or ProTeGi.
