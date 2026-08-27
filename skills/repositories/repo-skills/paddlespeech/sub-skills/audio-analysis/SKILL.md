---
name: audio-analysis
description: "Use PaddleSpeech audio classification, speaker
  vector/verification, keyword spotting, SSL vector, audio augmentation, and
  audio-search planning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Audio Analysis

Use this sub-skill for PaddleSpeech audio classification (`cls`), speaker embeddings and scoring (`vector`), keyword spotting (`kws`), SSL vector extraction, audio augmentation utility checks, ESC-50/VoxCeleb/HeySnips recipe planning, and audio search orientation.

## Choose the Workflow

| User goal | Use |
| --- | --- |
| Classify environmental/audio events | `paddlespeech cls`; read `references/cli-and-api.md` |
| Extract speaker embedding | `paddlespeech vector --task spk` |
| Score whether two clips match | `paddlespeech vector --task score`; use `scripts/build_vector_job.py` for job files |
| Detect a keyword | `paddlespeech kws --threshold ...` |
| Extract SSL representation | route to `../speech-to-text/SKILL.md` for `paddlespeech ssl --task vector` |
| Build Milvus/MySQL audio retrieval app | read `references/audio-workflows.md`, then route deployment/service parts to `../deployment-serving/SKILL.md` |

## Safe Workflow

1. Validate WAV format/sample rate with `../speech-to-text/scripts/validate_audio_inputs.py` when possible.
2. Use parser/help checks before model execution:

   ```bash
   paddlespeech cls --help
   paddlespeech vector --help
   paddlespeech kws --help
   ```

3. Confirm model downloads before running default inference.
4. For vector score, prepare pairs explicitly:

   ```bash
   python scripts/build_vector_job.py --output pairs.job --pair demo:enroll.wav:test.wav
   paddlespeech vector --task score --input pairs.job
   ```

## References and Helper

- `references/cli-and-api.md` covers CLS/vector/KWS commands and executor behavior.
- `references/audio-workflows.md` covers ESC-50, VoxCeleb, HeySnips, augmentation, and audio-search boundaries.
- `references/troubleshooting.md` covers sample-rate, top-k, vector pair, KWS threshold, cache, and service-app issues.
- `scripts/build_vector_job.py` builds vector embedding or score job files.

## Do Not Do by Default

- Do not run ESC-50, VoxCeleb, HeySnips, or audio-search recipes without approval; they require datasets, services, downloads, or long training.
- Do not start Milvus/MySQL/Docker Compose for audio search unless the user requested that service workflow.
- Do not treat a vector augmentation unit test as proof that pretrained speaker recognition model inference has run.
