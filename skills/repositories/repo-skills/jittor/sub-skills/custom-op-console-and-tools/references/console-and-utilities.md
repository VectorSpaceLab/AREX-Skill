# C++ console, utility flags, and interoperability boundaries

This reference covers public utility surfaces related to C++ embedding and conversion. It does not cover backend installation or host-level compiler setup.

## `jittor_utils.config` flag generator

`jittor_utils.config` is the public module CLI for C++ console build flags and example code:

```bash
python -m jittor_utils.config --help
python -m jittor_utils.config --include-flags --libs-flags --cxx-flags
python -m jittor_utils.config --cxx-example > example.cc
```

Flag meanings:

| Flag | Emits | Watch for |
| --- | --- | --- |
| `--include-flags` | Python and Jittor include flags for C++ compilation. | Output is machine-local by design; use it in the compile command, not in reusable docs. |
| `--libs-flags` | Link flags for the Python dynamic library. | Fails if the active Python install does not expose a shared library. |
| `--cxx-flags` | C++ compilation options, including C++17 and position-independent-code flags. | Compiler must support C++17. |
| `--cxx-example` | A complete C++ console example. | Example executes Python/Jittor code and may JIT-compile when run. |
| `--help` | Usage text. | Some help text may mention `--link-flags`; the documented and tested link flag is `--libs-flags`. |

Prefer the bundled wrapper so future agents do not need to remember the exact command form:

```bash
python scripts/jittor_console_flags.py --help
python scripts/jittor_console_flags.py --mode command --source example.cc --output example
python scripts/jittor_console_flags.py --mode example > example.cc
python scripts/jittor_console_flags.py --mode flags
```

The wrapper prints or delegates to `python -m jittor_utils.config`; it does not compile, run, start services, or require a source checkout.

## C++ console embedding workflow

The console API lets a C++ application create a Python/Jittor console, run Python snippets, and exchange scalar, vector, map, and array values.

Basic flow:

1. Generate example source: `python scripts/jittor_console_flags.py --mode example > example.cc`.
2. Inspect the generated source and remove heavyweight model calls if a tiny embedding smoke is enough.
3. Generate a compile command template: `python scripts/jittor_console_flags.py --mode command --source example.cc --output example`.
4. Compile with a C++17-capable compiler and the flags produced for the same Python environment.
5. Run the binary only after confirming that executing embedded Python/Jittor code is acceptable for the task.

Core API concepts used by the example:

```cpp
#include <pyjt/pyjt_console.h>

jittor::Console console;
console.run("print('hello jt console', flush=True)");

console.set<int>("a", 1);
int a = console.get<int>("a");

std::vector<int> x{1, 2, 3, 4};
console.set("x", x);
auto x2 = console.get<std::vector<int>>("x");

jittor::array<float, 2> arr({2, 3});
console.set_array("arr", arr);
console.run("arr2 = arr + 1");
auto arr2 = console.get_array<float, 2>("arr2");
```

Rules:

- Match the C++ template type and dimension in `get_array<T, NDIM>` to the Python-side value. Mismatches are runtime errors.
- Keep the Python used for `jittor_utils.config` identical to the Python embedded by the compiled binary.
- If `--libs-flags` cannot find the Python dynamic library, use a Python build/environment that provides a shared `libpython` instead of guessing link flags.
- The generated example may import built-in models and run a Jittor forward pass. For a minimal smoke, remove model sections and test only scalar or tiny array exchange.

## Utility wrappers in this sub-skill

| Script | Default safety behavior | Use it when |
| --- | --- | --- |
| `scripts/custom_op_smoke.py` | `--help` is import-free; default run is a tiny CPU `jt.code` sanity check; `--skip-compile` checks imports/callables only. | You need a bounded signal that `jt.code` and custom-op public names are available. |
| `scripts/jittor_console_flags.py` | Default mode prints a compile-command template; other modes print flags or example source; it never compiles or runs the example. | You need C++ console flags or a sample source file without depending on repo-local scripts. |

## PyTorch conversion and interoperability boundaries

The conversion utility is a source-to-source aid, not a correctness guarantee.

Minimal Python use:

```python
from jittor.utils.pytorch_converter import convert

jittor_source = convert(pytorch_source_text)
```

Operational boundaries:

- Conversion maps common PyTorch module/function names to Jittor equivalents where known. Unsupported constructs may intentionally emit runtime errors requiring manual implementation.
- Always review converted source and run small numerical parity tests before using it in production workflows.
- PyTorch is optional for conversion-time comparisons; if it is absent, perform manual review or install a compatible comparison environment only when needed.
- Avoid pretrained-weight downloads in converter checks unless network use is explicitly part of the task. Use non-pretrained constructors or tiny local fixtures for parity.
- Checkpoint load/save interop belongs with model/data/checkpoint workflows; keep this sub-skill focused on converter boundaries and service safety.

## Converter server and unsafe service caveats

A converter server entry point exists, but it imports Flask, listens on all interfaces, and exposes a JSON API that runs the converter. Treat it as a service deployment, not a local smoke test.

Do not start converter servers, Docker service scripts, network listeners, or background loops by default. Only proceed when the user explicitly asks for service deployment and accepts dependency, network, and security boundaries. For ordinary conversion, call the Python `convert(...)` function directly and test the generated code in a bounded local process.

## Difficult case: console flags without source checkout

When a user asks for C++ console compile flags:

1. Run the bundled wrapper in `--mode command` to show the exact command shape.
2. Run `--mode flags` only when the active Python environment is ready to emit machine-local flags.
3. Warn that C++17 support and a Python shared library are required.
4. Do not assume generated include or library paths are stable across machines; regenerate them in the target environment.
