# API Reference: Datagen, Evaluation, and Benchmarks

This reference summarizes the CAMEL-AI surfaces most relevant to synthetic data generation and evaluation. Verify exact signatures in the installed package for the target runtime because optional extras can affect importability.

## Synthetic Data Generation

| Area | Entry Points | Notes |
| --- | --- | --- |
| Chain-of-thought generation | `camel.datagen.CoTDataGenerator` | Uses generator/verifier agents, golden answers, search limits, MCTS-style exploration, import/export helpers; model-backed in normal use. |
| Self-instruct pipeline | `camel.datagen.self_instruct.SelfInstructPipeline` | Loads JSONL seed tasks, mixes human/machine instructions, filters instructions, classifies tasks, generates instances, writes JSON output. |
| Evol-instruct | `camel.datagen.evol_instruct.EvolInstructPipeline` | Evolves prompts using template methods or strategies, supports iterative generations, scorer selection, and threaded generation. Tests mock `ChatAgent` for deterministic validation. |
| Source2Synth | `camel.datagen.source2synth.UserDataProcessor`, `ProcessorConfig`, `ExampleConstructor`, `DataCurator`, `MultiHopQA`, `ContextPrompt` | Converts raw text into multi-hop QA examples. Set `ProcessorConfig(use_ai_model=False)` for rule/template-only local checks; `use_ai_model=True` invokes a multi-hop generation agent. |
| Self-improving CoT | `camel.datagen.SelfImprovingCoTPipeline` | Iterative reasoning improvement and reward-trace evaluation; plan for model costs and checkpointing. |

Important Source2Synth schema objects:

- `ProcessorConfig`: `seed`, `min_length`, `max_length`, `complexity_threshold`, `dataset_size`, `use_ai_model`, `hop_generating_agent`.
- `MultiHopQA`: `question`, `reasoning_steps`, `answer`, `supporting_facts`, `type`.
- `ContextPrompt`: `main_context`, optional `related_contexts`.

## Data Collectors and Dataset Wrappers

| Area | Entry Points | Input/Output Contract |
| --- | --- | --- |
| Collector base | `camel.data_collectors.CollectorData`, `BaseDataCollector` | Collector records normalize external conversation/instruction formats before downstream training. |
| Alpaca collector | `AlpacaDataCollector` | Converts Alpaca-style `instruction`, `input`, `output` records. Validate missing columns before collection. |
| ShareGPT collector | `ShareGPTDataCollector`, `ConversationItem`, `ShareGPTData` | Converts role/content conversation records. Validate role vocabulary and turn ordering. |
| Static datasets | `camel.datasets.DataPoint`, `StaticDataset` | `DataPoint` requires string `question` and `final_answer`; optional `rationale` and `metadata`. `StaticDataset` accepts HF datasets, PyTorch datasets, JSON/JSONL paths, or lists of dictionaries, with `strict` controlling invalid sample handling. |
| Generators | `BaseGenerator`, `FewShotGenerator`, `SelfInstructGenerator` | Iterable data sources for environments and training examples. `SelfInstructGenerator` normally uses two `ChatAgent` instances plus a `BaseVerifier`. |

Use `StaticDataset(strict=True)` when failing fast on schema errors is preferred. Use `strict=False` only when skipping invalid rows is acceptable and logged.

## Verifiers and Extractors

| Entry Point | Contract | Deterministic Use |
| --- | --- | --- |
| `BaseVerifier` | Async lifecycle: `setup()`, `verify(solution, reference_answer)`, `cleanup()`. Returns `VerificationResult`. | Always call `cleanup()` in `finally` when a verifier creates resources. |
| `VerificationResult` | `status`, `result`, `duration`, `timestamp`, `metadata`, optional `error_message`. | `VerificationOutcome.SUCCESS` is truthy; failure/error/timeout are falsy. |
| `MathVerifier` | Compares math expressions with optional extractor, timeout, `float_rounding`, `numeric_precision`, `enable_wrapping`. | Requires the optional `math-verify` dependency; good for no-model answer checking after import succeeds. |
| `PythonVerifier` | Executes generated Python in an isolated virtual environment; optional `required_packages` and `float_tolerance`. | Potentially creates venvs and installs packages. Treat untrusted generated code as unsafe unless sandboxed by the caller. |
| `BaseExtractor` | Pipeline of extraction strategy stages; each stage tries strategies in order and feeds output into the next stage. | Useful for normalizing LLM outputs before verification. |
| Python extractor strategies | `BoxedStrategy`, `PythonListStrategy`, `PythonDictStrategy`, `PythonSetStrategy`, `PythonTupleStrategy` | Native tests cover boxed LaTeX extraction and Python literal normalization. |

## Environments

| Entry Point | Contract | Notes |
| --- | --- | --- |
| `Action` | Pydantic model with `llm_response`, `index`, `metadata`, `timestamp`. | Wrap model responses in the expected action format for the environment. |
| `Observation` | Pydantic model with `question`, `context`, optional `metadata`. | The prompt for the next action. |
| `StepResult` | `observation`, `reward`, `rewards_dict`, `done`, `info`; `as_tuple()` returns `(observation, reward, done, info)`. | Some multi-step environments return this tuple form. |
| `SingleStepEnv` | Dataset + verifier, async `setup()`, `reset(batch_size=1, seed=None)`, `step(action)`, `close()`. | Good for deterministic verifier-backed benchmark harnesses around `StaticDataset`. |
| `MultiStepEnv` | Extractor + max steps, async `setup()`, `reset()`, `step(action)`, `close()`. | Requires subclasses to implement state update, observation, reward, and terminal behavior. |
| `TicTacToeEnv` | Multi-step game environment that accepts `<Action>n</Action>` moves. | Native tests cover reset, invalid moves, win/loss/draw, render helpers, and opponent behavior. |
| `RLCardsEnv` and subclasses | RLCard-backed games such as blackjack, Leduc hold'em, and Dou Dizhu. | Heavy optional dependencies; verify availability before routing agents there. |
