# Example and app troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CLI exits with `KeyError: GOOGLE_API_KEY` | example reads the key at import/startup | export `GOOGLE_API_KEY` before running real model examples |
| STT/TTS example exits with missing `GOOGLE_PROJECT_ID` | Google Cloud project ID is required | export `GOOGLE_PROJECT_ID` and verify credentials/API enablement |
| audio app hears itself | speaker output loops into mic | use headphones or AI Studio/browser echo cancellation |
| applet cannot connect to backend | WebSocket server not running, wrong port, CORS/browser restriction, or localhost mismatch | start backend on expected port, verify `ws://localhost:8765`, check browser console |
| server says port already in use | old backend still running | stop the old process or choose another port flag |
| widget output blocks or never appears | tool result not routed to UI/status substream or function response ID not associated | preserve reserved substreams and function-response metadata |
| trip request returns only an error substream | first schema model found missing required fields | prompt the user for destination/start/end dates or inspect `TripRequest.error` |
| Ollama example cannot respond | Ollama server/model missing | run `ollama serve` and `ollama pull <model>` before starting the CLI |
| ADK web cannot find agent | wrong working directory or package import path | run from the examples parent expected by ADK and verify the agent module name |
| trace files are too large | audio/video app traced without limits | use `--trace_dir` only for short sessions and set size limits when available |

## Before running any example

1. Identify credentials, devices, local services, and browser permissions.
2. Run `scripts/check_example_env.py` from this sub-skill.
3. Prefer a text-only or import-only path before opening audio/video devices.
4. Decide whether network/model calls are acceptable for the task budget.
5. Keep secrets in environment variables or secure config, never in generated
   code or logs.

## Adapting examples safely

- Replace prompts, model names, tools, and UI rendering in small increments.
- Preserve the processor chain shape until the adapted version works.
- Keep the example-specific `models.py` helper inside demos; for production,
  construct the desired model wrapper directly.
- Separate application configuration from processor construction so tests can
  instantiate processors with fake configs.
