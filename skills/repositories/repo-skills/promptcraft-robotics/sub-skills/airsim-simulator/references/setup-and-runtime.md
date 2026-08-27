# Setup and runtime

This reference describes the ChatGPT-AirSim sample at a conceptual level so future agents can reason about it without reopening the source checkout.

## Environment shape

The inspected sample stack used:

- Python 3.9
- `openai 0.27.2`
- `numpy 1.24.2`
- `airsim 1.8.1`
- `requests 2.28.2`
- `msgpack-rpc-python 0.4.1`
- `msgpack-python 0.5.6`

The published repository environment file also pins `opencv-contrib-python` and `tornado` even though the core sample logic is centered on OpenAI + AirSim + NumPy.

## Runtime inputs

The sample expects:

- an OpenAI API key in the config file;
- a simulator-ready AirSim environment;
- a settings file for the simulator;
- a prompt file and a system prompt file that define the drone's allowed actions and response style.

## Runtime shape

The sample does the following in order:

1. Loads the configuration file and reads the OpenAI API key.
2. Loads the system prompt and primes the chat history.
3. Initializes the AirSim wrapper.
4. Reads the user prompt template.
5. Sends user text to the OpenAI ChatCompletion API.
6. Appends the assistant response to the chat history.
7. Extracts fenced code blocks from the assistant response.
8. Executes the extracted code directly.

## Consequences of that shape

- The sample is not a passive text generator; it is an execution loop.
- Because generated code is executed directly, the sample should be treated as unsafe unless it is sandboxed.
- The AirSim wrapper is small and opinionated, so the prompt must respect the exact helper function names.
- The sample assumes local prompt/config files are present and readable from the working context.

## Human-facing launch checklist

This skill deliberately focuses on preflight and explanation rather than a bundled launcher.
Use the checklist below when you want to reason about the runtime:

- confirm the Python environment can import the required packages;
- confirm the config contains a non-placeholder API key;
- confirm the simulator settings file matches the intended AirSim mode;
- confirm the prompt and system prompt describe only the allowed helper functions;
- confirm the simulator itself is running before attempting a live drone session.

## Common runtime assumptions from the source material

- The sample was documented as Windows-only in the repository README.
- The prompt should only refer to the helper functions the sample exposes.
- The prompt should ask clarification questions when an object is ambiguous or duplicated.
- The human-readable prompt uses positive X as forward, positive Y as right, and positive Z as up.

## When to read this file

Read this file when the user wants to understand the sample runtime contract, not when they want the full API reference or troubleshooting steps. For those, use the adjacent references.
