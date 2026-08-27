# `tts-server` Workflows

`tts-server` is the installed local demo server entry point. It provides a browser/API interface over a single loaded model and is useful for local demos, manual audio checks, and speaker/language UI exploration. It is not a production deployment recipe.

## Safe checks before launch

| Task | Command | Why it is safe |
| --- | --- | --- |
| Show server parser | `tts-server --help` | Exits after parser output; does not bind a port. |
| List released models | `tts-server --list_models` | Reads the bundled registry; does not start Flask. |
| Scripted check | From the skill root, `python sub-skills/server-and-cli/scripts/check_tts_server_cli.py` | Runs help/list only and validates expected flags. |

If `tts-server` is not on `PATH`, resolve package installation or entry-point activation before trying to run a server. Do not switch to source-tree server scripts.

## Server flags

| Flag | Use | Caution |
| --- | --- | --- |
| `--list_models` | Print released model registry and exit. | Low side effect; does not bind a server. |
| `--model_name NAME` | Load released TTS model; default is `tts_models/en/ljspeech/tacotron2-DDC`. | Can download model files and default vocoder. Use names from `tts-server --list_models`. |
| `--vocoder_name NAME` | Load an explicit released vocoder. | Can download a vocoder; verify compatibility with selected TTS model. |
| `--model_path PATH` + `--config_path PATH` | Load custom TTS checkpoint/config. | Supply both; check config/checkpoint compatibility before launch. |
| `--vocoder_path PATH` + `--vocoder_config_path PATH` | Load custom vocoder checkpoint/config. | Supply both and verify audio/mel compatibility. |
| `--speakers_file_path PATH` | Custom speaker JSON for custom multi-speaker model. | No custom language-id file flag is exposed by `tts-server` in this version. |
| `--port PORT` | TCP port; default `5002`. | Check that the port is free before launch. |
| `--use_cuda True|False` | Use CUDA when loading the server-side model. | Server CLI has `--use_cuda` but not `--device`; choose visible GPUs outside the command if needed. |
| `--debug True|False` | Enable Flask debug mode. | Debug mode can expose traceback details and reloader behavior; use only for local debugging. |
| `--show_details True|False` | Enable a model details page. | May expose model/config details in the UI; avoid when sharing a server. |

The installed server runs Flask with host `::` and the selected `--port`, so it may listen on more than just a single local IPv4 interface depending on host networking. Treat any launch as a network-binding action.

## Local launch patterns

### Released model, default vocoder

```bash
tts-server --model_name tts_models/en/ljspeech/tacotron2-DDC \
  --port 5002 \
  --debug False \
  --show_details False
```

Before running it, confirm:

- the model name came from `tts-server --list_models`;
- network/cache/disk side effects are approved if the checkpoint is not already cached;
- port `5002` is free or a different port is selected;
- the process will be stopped after the local demo.

### Released model with explicit vocoder

```bash
tts-server --model_name tts_models/en/ljspeech/glow-tts \
  --vocoder_name vocoder_models/en/ljspeech/hifigan_v2 \
  --port 5002 \
  --debug False
```

Use this only when the vocoder is compatible with the TTS model. If audio quality is poor or shapes mismatch, switch back to the model's default vocoder or use [../../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md) for compatibility checks.

### Custom checkpoint

```bash
tts-server --model_path model.pth \
  --config_path config.json \
  --vocoder_path vocoder.pth \
  --vocoder_config_path vocoder_config.json \
  --speakers_file_path speakers.json \
  --port 5002 \
  --debug False
```

Only include custom vocoder and speakers-file flags when those artifacts exist and are required. This version's server custom flags are `--model_path`, `--config_path`, `--vocoder_path`, and `--vocoder_config_path`; do not use older checkpoint/config alias names.

## Interacting with the demo server

Once launched, use the web page for manual local synthesis. The server also exposes a TTS endpoint that accepts text plus optional speaker/language fields, and it includes MaryTTS-compatible compatibility endpoints. Keep this sub-skill focused on safe startup and troubleshooting; route API-level synthesis semantics to [../../inference-and-model-zoo/SKILL.md](../../inference-and-model-zoo/SKILL.md).

## Pre-launch checklist

1. Run `tts-server --help` and confirm the expected flags are present.
2. If using a released model, run `tts-server --list_models` and copy the exact full model name.
3. Decide whether model downloads are allowed; if not, use only already-cached released models or explicit local custom paths.
4. Check the chosen port. If it is busy, pick a different `--port` or stop the old process.
5. Keep `--debug False` unless you need local traceback diagnostics.
6. Plan how to stop the process; do not leave a persistent listener running after the demo.

## Bundling and exclusion decisions

- The installed `tts-server` entry point is wrapped by [../scripts/check_tts_server_cli.py](../scripts/check_tts_server_cli.py) for help/list validation.
- The Flask app, HTML templates, and persistent server implementation are not bundled. Copying them would turn a local demo reference into a deployment surface and would drift from the installed package. Future agents should run the installed `tts-server` only after explicit local-network and model-download validation.
- Container or persistent-service deployment remains reference/troubleshooting-only here. If a user asks for production deployment, first clarify the runtime/security/deployment target and route outside this CLI/demo-server sub-skill.
