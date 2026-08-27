# CLI Reference

## Root Commands

```bash
paddlespeech help
paddlespeech version
paddlespeech stats --task asr
paddlespeech stats --task tts
paddlespeech stats --task cls
paddlespeech stats --task text
paddlespeech stats --task vector
```

Core task commands:

```bash
paddlespeech asr --input input_16k.wav
paddlespeech st --input input_16k.wav
paddlespeech ssl --task asr --lang en --input input_16k.wav
paddlespeech whisper --task transcribe --input input_16k.wav
paddlespeech text --task punc --input 今天的天气真不错啊你下午有空吗
paddlespeech tts --input "你好，欢迎使用百度飞桨深度学习框架！" --output output.wav
paddlespeech cls --input input.wav --topk 10
paddlespeech vector --task spk --input input_16k.wav
paddlespeech vector --task score --input pair.job
paddlespeech kws --input input_16k.wav --threshold 0.8
```

`stats` is a registry display helper. In this checkout, ASR/TTS/CLS/TEXT/VECTOR stats are safe. SSL, Whisper, and KWS stats may report a display failure even when their command parser and modules import; use `--help` and the owning sub-skill references instead of treating that as a model/runtime failure.

## Batch, Stdin, and Job Inputs

Most executors share `BaseExecutor.get_input_source`:

- A direct `--input` value becomes one task item.
- If `--input` points to a `.job`, `.txt`, or `.scp` file, each non-empty line is parsed as an id plus one value.
- If `--input` is omitted and stdin is piped, one-token lines or `id value` lines are consumed.
- `-d` / `--job_dump_result` writes a `.done` file beside a job input for executors that use shared result handling.

Important limitations:

- The shared job parser only accepts two whitespace-separated fields, so TTS English text with spaces is not safe in `.job` form. Use direct `--input "sentence with spaces"` for spaced text.
- The vector executor overrides job parsing and supports `id enroll.wav test.wav` for `--task score`.
- Model execution may download archives even if parser/help commands do not.

## Server and Client Commands

```bash
paddlespeech_server help
paddlespeech_server stats --task tts
paddlespeech_server start --config_file application.yaml

paddlespeech_client help
paddlespeech_client asr --server_ip 127.0.0.1 --port 8090 --input input_16k.wav
paddlespeech_client tts --server_ip 127.0.0.1 --port 8090 --input "您好" --output output.wav
paddlespeech_client tts_online --server_ip 127.0.0.1 --port 8092 --protocol http --input "您好" --output output.wav
paddlespeech_client vector --task spk --server_ip 127.0.0.1 --port 8090 --input input_16k.wav
paddlespeech_client vector --task score --server_ip 127.0.0.1 --port 8090 --enroll enroll.wav --test test.wav
```

Starting a server is not a help check. It initializes engines, warms models, and binds ports. Inspect configs with `sub-skills/deployment-serving/scripts/inspect_server_config.py` before launching.
