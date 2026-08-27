# PandasAI Sandbox Workflows

## Purpose

Use this reference when deciding how to execute PandasAI-generated code safely.
It covers the abstract `Sandbox` contract, the optional Docker extension, and a
small custom sandbox pattern.

## Abstract contract

The base `Sandbox` class defines the interface:

- `start()`
- `stop()`
- `execute(code, environment)`
- `_exec_code(code, environment)`
- `transfer_file(csv_data, filename)`
- `_extract_sql_queries_from_code(code)`
- `_compile_code(code)`

The first five are abstract on the base class except `execute`, which starts the
sandbox automatically if it has not yet started.

### Minimal subclass pattern

```python
from pandasai.sandbox import Sandbox

class LocalSandbox(Sandbox):
    def start(self):
        self._started = True

    def stop(self):
        self._started = False

    def _exec_code(self, code: str, environment: dict) -> dict:
        exec_globals = environment.copy()
        exec(code, exec_globals)
        return exec_globals

    def transfer_file(self, csv_data, filename="file.csv"):
        return filename
```

## Using a sandbox with chat

```python
import pandasai as pai

sandbox = LocalSandbox()
sandbox.start()
response = pai.chat("Analyze the dataframe", df, sandbox=sandbox)
sandbox.stop()
```

Pass the sandbox explicitly. PandasAI does not sandbox generated code unless a
`Sandbox` instance is supplied.

## Docker sandbox extension

When the user wants container isolation, install the optional package:

```bash
pip install pandasai-docker
```

Then use the extension's `DockerSandbox` class, start it before chat, and stop it
afterwards. Docker must be installed and running on the host.

## Recommended scenarios

| Scenario | Recommend sandbox? | Notes |
| --- | --- | --- |
| Public-facing prompt inputs | Yes | Prevent generated code from touching the host directly. |
| Sensitive data | Yes | Minimize access to host filesystem and network. |
| Local experimentation with trusted code | Optional | Base execution may be sufficient. |
| Offline deterministic unit tests | Not needed | Use a tiny fake sandbox or `FakeLLM` smoke. |
| Custom restricted execution environment | Yes, if code is still generated | Provide a subclass with only the allowed environment. |

## SQL extraction helper

The sandbox can heuristically extract SQL strings from Python code. This helps
inspect generated code before execution, but it does not guarantee full safety for
all dynamic string-building patterns.

Use the helper script to validate the contract:

```bash
python sub-skills/sandbox-and-security/scripts/sandbox_contract_smoke.py
```
