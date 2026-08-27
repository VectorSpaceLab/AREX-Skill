# Porcupine troubleshooting

Use this root page for cross-cutting failures before routing to a platform-specific sub-skill.

## Fast triage

1. Identify the SDK family: Python, Node.js, Web/React, managed/mobile, or C/MCU.
2. Run the safest package/import check for that family before attempting detection.
3. Confirm a valid Picovoice AccessKey is available only when engine initialization or training is actually needed.
4. Verify the keyword `.ppn` platform and language `.pv` model pairing.
5. Verify 16-bit mono PCM at the engine sample rate and exact frame length.
6. Stop at credential, microphone, browser, mobile-device, or MCU requirements that are outside the current environment.

## Safe Python root check

When Python is available, this generated skill bundles a no-credential helper:

```bash
python scripts/check_porcupine_install.py
python scripts/check_porcupine_install.py --json
```

The helper imports `pvporcupine`, resolves packaged assets, and lists devices. It does not initialize an engine and does not require an AccessKey.

## AccessKey symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Activation, refused, throttled, or limit errors | Invalid key, quota/account limits, or too many retries | Validate the key/account outside the code path; avoid retry loops; redact keys in logs. |
| Safe import/device checks pass but detection initialization fails | AccessKey is required only at engine initialization | Re-run with a real AccessKey; keep no-credential checks separate from detection checks. |
| Training API fails before producing `.ppn` bytes | Missing key, network failure, invalid phrase/language/platform, or quota | Use `sub-skills/custom-keywords-and-assets/references/training-api-reference.md` and preserve HTTP/error text without logging secrets. |

## Asset pairing failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Built-in keyword not found | Phrase is not exposed as a built-in in that SDK/platform | Print SDK built-ins or use a custom `.ppn` path. |
| Custom keyword file loads on one platform but not another | `.ppn` files are platform-specific | Train or select the `.ppn` for the runtime platform: Linux, macOS, Windows, Raspberry Pi, Android, iOS, WebAssembly, or Cortex-M. |
| Non-English detection misses consistently | Wrong language model `.pv` paired with keyword | Pair non-English `.ppn` with the matching language model asset. |
| Web app fails after updating assets | IndexedDB/public path cache still serves old bytes | Version/cache-bust asset labels and use the web troubleshooting page. |

## Audio contract failures

Porcupine is not a general audio decoder. Convert input before processing:

- PCM, signed 16-bit integer samples,
- mono channel,
- engine sample rate,
- one exact engine frame per process call.

If a demo or user app reads stereo WAV, process only one channel or downmix explicitly. If chunks come from microphone APIs or browsers, buffer until exactly one frame is available.

## Device/backend failures

- Prefer `best` while diagnosing AccessKey or asset failures.
- Use enumeration helpers before hard-coding `gpu:0` or `cpu:<N>`.
- If a task explicitly requires GPU or platform hardware verification, initialize and run that backend with a valid AccessKey; a CPU import check is not enough.
- Mobile/browser/MCU hardware workflows are optional native verification unless the user explicitly asks to run them.

## Package-family routes

| Failure surface | Read next |
| --- | --- |
| Python import, signatures, file WAV processing, `available_devices`, frame errors | `sub-skills/python-and-cli/references/troubleshooting.md` |
| Node native `.node` loading, `Int16Array`, built-in enum, server file/mic flows | `sub-skills/nodejs-server/references/troubleshooting.md` |
| Browser WASM worker, public path/base64 assets, IndexedDB, microphone permission, React hook lifecycle | `sub-skills/web-and-react/references/troubleshooting.md` |
| Java/Android/iOS/.NET/Flutter/React Native package, permission, callback, lifecycle, custom asset placement | `sub-skills/managed-and-mobile-sdks/references/troubleshooting.md` |
| C linker/load errors, header/library mismatch, file frame loop, MCU conversion/toolchain | `sub-skills/c-and-embedded/references/troubleshooting.md` |
| Custom `.ppn`, `.pv`, language/platform, training API | `sub-skills/custom-keywords-and-assets/references/troubleshooting.md` |

## Stop conditions

Do not pretend a workflow is verified when it requires resources that are absent. Stop and ask for the missing input when the next step requires:

- a Picovoice AccessKey,
- outbound access to Picovoice training services,
- a real microphone/audio device,
- a mobile simulator/device or browser UI,
- MCU board/toolchain/debugger,
- private app signing credentials,
- platform-specific native package installation outside the selected environment.
