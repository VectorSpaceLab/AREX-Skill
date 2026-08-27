# Media Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| image generation says wrong model | selected model is not GPT/OpenAI-compatible image-capable path | switch model/provider and verify key/proxy |
| uploaded image ignored | selected model lacks vision support | choose a vision model; keep image path server-visible |
| browser microphone unavailable | no HTTPS/localhost permission or browser blocked mic | use localhost/HTTPS, grant mic permission, reload UI |
| voice assistant fails recognition | missing Aliyun/speech credentials or audio dependencies | verify `ENABLE_AUDIO`, credentials, and package imports |
| Edge TTS produces no audio | network failure, `edge-tts` missing, `ffmpeg` missing for pydub conversion | run backend checker; install ffmpeg; check network |
| SoVITS returns connection error | external SoVITS API not running or URL wrong | start service, verify `GPT_SOVITS_URL`, check firewall/GPU service logs |
| audio/video summary times out | media too long or conversion slow | split media, reduce length, use faster model, confirm ffmpeg |
| Manim animation fails | Manim not installed or scene too complex | install Manim dependencies, simplify prompt, render a tiny scene first |
| video resource search is irrelevant | query too vague or external site blocked | refine prompt, provide lyrics/artist/site, or use conversation search first |
