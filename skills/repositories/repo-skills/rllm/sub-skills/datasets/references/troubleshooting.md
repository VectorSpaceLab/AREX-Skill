# Dataset Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Dataset file not found` | Registry split path is stale or local file was moved | Run `rllm dataset info <name>` and re-register or repair the split path. |
| `Unsupported file format` | File extension not in JSON/JSONL/CSV/Parquet/Arrow | Convert to a supported format or add a custom loader before using rLLM CLI. |
| Eval sees empty instructions | Rows use a nonstandard prompt field | Map/rename to `instruction` or `question`, or add a loader/metadata transform that produces `Task.instruction`. |
| Verifier not found | Missing `[verifier]`, catalog `reward_fn`, or CLI `--evaluator` | Add metadata or pass evaluator explicitly; see the evaluation sub-skill for scoring semantics. |
| Task claims environment but eval does not provision one | Flow/evaluator cannot consume the sandbox | Use a sandbox-aware flow/evaluator or remove the unused environment declaration. |
| Harbor/HF pull fails | Network, auth, gated dataset, or missing optional integration | Do not retry blindly; confirm credentials and whether the user approved network/data download. |
| `from-eval` yields no useful SFT rows | Episodes lack messages/trajectories or filtering removed all examples | Inspect saved episode JSON and validate message rows before `rllm sft`. |
