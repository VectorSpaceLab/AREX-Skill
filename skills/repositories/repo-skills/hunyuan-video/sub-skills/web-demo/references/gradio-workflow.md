# Gradio Workflow Reference

Read this when launching or explaining HunyuanVideo's browser UI.

## Safe command construction

Build a localhost-only command:

```bash
python sub-skills/web-demo/scripts/build_gradio_command.py \
  --model-base ckpts \
  --server-name 127.0.0.1 \
  --server-port 7860 \
  --flow-reverse
```

The printed command uses the bundled service runner, for example:

```bash
GRADIO_ANALYTICS_ENABLED=False SERVER_NAME=127.0.0.1 SERVER_PORT=7860 python sub-skills/web-demo/scripts/run_gradio_server.py --model-base ckpts --save-path ./results --flow-reverse
```

Only run that command after dependency, checkpoint, CUDA, and port-exposure checks pass.

## UI defaults and fields

The HunyuanVideo Gradio workflow exposes:

| UI field | Default | Notes |
| --- | --- | --- |
| Prompt | `A cat walks on the grass, realistic style.` | Passed directly to `model.predict`. |
| Resolution | `1280x720` | Choices: `1280x720`, `720x1280`, `1104x832`, `832x1104`, `960x960`, `960x544`, `544x960`, `832x624`, `624x832`, `720x720`. |
| Video Length | `129` | Choices: 65 frames (about 2s) and 129 frames (about 5s). |
| Inference Steps | `50` | Slider from 1 to 100. |
| Seed | `-1` | `-1` is converted to `None`, producing random seed behavior. |
| Guidance Scale | `1.0` | Advanced option. |
| Flow Shift | `7.0` | Advanced option. |
| Embedded Guidance Scale | `6.0` | Advanced option. |

The UI does not expose a negative prompt. The bundled runner follows the repo behavior and sends an empty negative-prompt string from the UI callback.

## Output behavior

Generated videos are written under a `gradio_outputs/` directory in the current working directory of the launched server process. The output filename includes a timestamp, seed, and sanitized prompt prefix.

`--save-path` is still accepted because it is part of the shared HunyuanVideo argument set and model initialization path, but the Gradio generation callback saves to `gradio_outputs/`.

## Binding guidance

- `127.0.0.1` is safer for local-only use.
- `0.0.0.0` listens on reachable interfaces and may expose the UI to other machines on the network.
- `SERVER_PORT` must be an integer and the port must be free.
