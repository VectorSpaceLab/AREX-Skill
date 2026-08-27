# Dataset Operations

## CLI commands

```bash
rllm dataset list
rllm dataset info <name>
rllm dataset inspect <name> --split <split> --limit 5
rllm dataset pull <source-or-name>
rllm dataset register <name> <file-or-directory> --split train
rllm dataset remove <name>
rllm dataset from-eval <eval-results-or-episodes-dir> --output <file>
```

Use `rllm dataset --help` and `rllm dataset <subcommand> --help` for exact options in the installed version.

## Registered dataset behavior

`DatasetRegistry` stores a versioned registry under rLLM home and resolves splits to file paths. Supported direct file loads include JSON, JSONL, CSV, Parquet, and Arrow IPC. Registered datasets may also carry metadata used by evaluation/training catalog lookup.

## Pulling and registration

- Pulling Hugging Face or Harbor datasets can contact network services and may require credentials. Do not run pulls unless the user expects network/data side effects.
- Register local data when the user already has a file/directory and wants stable CLI names.
- Use `inspect` on small limits before full eval/training to verify columns and examples.

## Eval-to-SFT curation

`rllm dataset from-eval` converts saved evaluation trajectories/episodes into supervised fine-tuning data. It is most useful after `rllm eval` saved per-episode JSON files. Validate the resulting rows with the SFT guidance in `../../training/references/sft-data-and-config.md` before launching `rllm sft`.
