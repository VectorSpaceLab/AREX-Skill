# Install and Environment Reference

## Install Tiers

PaddleSpeech installation has three practical tiers:

1. **Package-user inference tier**: install `paddlespeech` plus a compatible PaddlePaddle runtime. Use this for CLI/API inference, model listing, and server clients.
2. **Server tier**: add FastAPI/Uvicorn/WebSocket dependencies and task-specific model dependencies. This is needed for `paddlespeech_server start` and `paddlespeech_client` workflows.
3. **Recipe/development tier**: add dataset, Kaldi/MFA/KenLM/OpenFST, CTC decoder, test, and toolchain dependencies only when running training recipes or maintainer tests.

For modern CPU inspection, a working environment must import at least:

```bash
python -I -c "import paddle, paddlespeech; print(paddle.__version__)"
python -I -c "import paddlespeech.cli.base_commands, paddlespeech.server.base_commands"
```

Use the root checker for a safer multi-surface check:

```bash
python scripts/check_paddlespeech_environment.py --check cli --check server --check imports
```

## PaddlePaddle Runtime

PaddleSpeech is built on PaddlePaddle. The source metadata allows Python 3.7+ and this checkout was inspected successfully with Python 3.10 and `paddlepaddle` 2.6.x CPU.

Choose the PaddlePaddle wheel by backend:

- CPU: enough for imports, parser checks, static config checks, and many small utility tests.
- CUDA/GPU: optional for faster inference/training or if the user specifically asks to verify GPU execution.
- ONNXRuntime: needed for `paddlespeech tts --use_onnx` and online ONNX streaming TTS configs.
- Paddle Inference / Paddle Lite / FastDeploy / Android / ARM / C++ runtime: deployment-specific; do not install or build by default.

## Runtime Dependencies Worth Checking

The full package imports can require audio, text, server, and model packages including `soundfile`, `librosa`, `paddlenlp`, `yacs`, `prettytable`, `onnxruntime`, `paddlespeech_feat`, `fastapi`, `uvicorn`, `websockets`, `pypinyin`, `opencc`, `inflect`, `resampy`, and `tiktoken`.

A known compatibility pitfall is the AIStudio SDK/PaddleNLP path used by punctuation and SSL modules. If imports fail with an error similar to `cannot import name 'download' from aistudio_sdk.hub`, use an AIStudio SDK version whose `aistudio_sdk.hub.download` API is available, or pin the dependency consistently with the installed PaddleNLP version.

## Cache and Download Roots

PaddleSpeech uses `PPSPEECH_HOME` to choose its cache root. If unset, it uses a user cache directory named `.paddlespeech`. Subdirectories are created for:

- `models`: downloaded model archives and decompressed resources.
- `conf`: cached CLI stats/config information.
- `datasets`: downloaded auxiliary resources such as Whisper resource data.

Set `PPSPEECH_HOME` before running model downloads when you need an isolated or reusable cache. Make sure the value is a directory or a path that can be created.

## Side Effects to Confirm

Ask before running commands that do any of the following:

- Download model archives, language models, sample audio, or datasets.
- Bind service ports or start long-lived Uvicorn/WebSocket processes.
- Run full example `run.sh` recipes, `tests/unit/cli/test_cli.sh`, TIPC scripts, or benchmark scripts.
- Start Docker Compose services for audio search.
- Install or build Kaldi, KenLM, MFA, OpenFST, Paddle Lite, FastDeploy, Android, ARM, or C++ toolchains.
- Run GPU training or multi-hour fine-tuning recipes.
