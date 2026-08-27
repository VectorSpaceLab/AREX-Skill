# WeNet Package CLI Reference

Read this when the user wants the installed `wenet` command rather than Python
code or a full experiment recipe.

## Command shape

```bash
wenet [options] audio_file
```

The positional `audio_file` is required. Use `wenet --help` in the target
environment to confirm the installed version before running a real transcription.

## Verified options

| Option | Meaning |
|---|---|
| `-m`, `--model MODEL` | Built-in model key or local model directory. Default is `wenetspeech`. Public examples also use `paraformer`, `firered`, `whisper-large-v3`, and `whisper-large-v3-turbo`. |
| `--device {cpu,npu,cuda}` | Backend device requested for model execution. This is a request, not a backend proof. |
| `-t`, `--show_tokens_info` | Request token/word-level timing or confidence information when supported. |
| `--align` | Force-align an input audio file and transcript. Requires `--label`. |
| `--label LABEL` | Transcript label used with forced alignment. |
| `--beam BEAM` | Beam size for decoding. Default is `5` in the package CLI. |
| `--context_path CONTEXT_PATH` | Path to a context/hotword list for context biasing. |
| `--context_score CONTEXT_SCORE` | Score added for context biasing. Default is `6.0`. |
| `--punc` | Request punctuation processing. |
| `-pm`, `--punc_model_dir PUNC_MODEL_DIR` | Custom punctuation model directory. |

## Examples

CPU transcription with a built-in model key:

```bash
wenet -m paraformer --device cpu audio.wav
```

Local model directory:

```bash
python sub-skills/package-transcription/scripts/check_wenet_package.py \
  --model-dir /models/my-wenet-model --device cpu
wenet -m /models/my-wenet-model --device cpu audio.wav
```

Forced alignment:

```bash
wenet -m /models/my-wenet-model --device cpu --align \
  --label "expected transcript" audio.wav
```

Context biasing:

```bash
wenet -m /models/my-wenet-model --device cpu \
  --context_path hotwords.txt --context_score 6.0 audio.wav
```

## When not to use this CLI

- Use [../../training-and-decoding/SKILL.md](../../training-and-decoding/SKILL.md)
  for batch decoding a `data.list`, comparing recognition modes, averaging
  checkpoints, or computing WER/CER.
- Use [../../model-export/SKILL.md](../../model-export/SKILL.md) when the user
  needs TorchScript, ONNX, IPEX, or BPU export artifacts.
- Use [../../runtime-deployment/SKILL.md](../../runtime-deployment/SKILL.md)
  for C++/mobile/web/server deployment.
