# Troubleshooting

Use this guide when Porcupine asset selection or training fails.

## Fast diagnosis table

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `Invalid language ('xx')` | Unsupported training language | Use one of the validated training codes in the training reference. |
| `Invalid platform ('xx')` | Unsupported Python training platform | Omit the platform to use the runtime default, or choose a value from the validated platform list. |
| `Phrase must not be empty` | Blank wake phrase | Provide a non-empty phrase. |
| `Phrase must not exceed 64 characters` | Phrase too long | Shorten the phrase to 64 characters or fewer. |
| `Failed to train model: ...` | Picovoice rejected the request | Check AccessKey validity, quota, and the response body. |
| `Request failed: ...` | Network, DNS, TLS, or proxy problem | Verify outbound HTTPS to `rest.picovoice.ai`. |
| Custom keyword loads in one SDK but not another | Wrong platform-family asset | Regenerate or choose the matching platform-specific `.ppn`. |
| Non-English inference fails | Wrong `.pv` model | Use the language-specific model that matches the wake-word asset. |
| Web asset disappears after reload | IndexedDB cache mismatch | Use the right `customWritePath` and bump `version` when the asset changes. |
| False positives are too frequent | Sensitivity too high | Lower the sensitivity for the affected keyword only. |

## Invalid language

The training helpers validate language before they hit the network.

- Python/Android/iOS/Web training currently accept `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, and `pt`.
- Runtime inference assets also include `zh`, but the training validation list in this checkout does not currently accept it.
- If you need a `zh` inference asset, load the packaged model/keyword files rather than expecting the trainer to accept `zh`.

## Invalid platform

Python is the only helper here that accepts an explicit platform argument.

- Valid values: `linux`, `mac`, `windows`, `raspberry-pi`, `wasm`, `android`, `ios`.
- `cortexm` assets exist in the repository, but they are part of the embedded delivery flow and are not accepted by the training validator.
- If you are not sure, omit the platform and let Python choose the current runtime.

## HTTP and AccessKey failures

If the server response is non-2xx, the bindings preserve the body in the exception text when possible.

Likely explanations:
- invalid or expired AccessKey,
- account quota reached,
- temporary service-side failure,
- blocked or intercepted outbound HTTPS.

Do not debug these as local file errors until the response body is inspected.

## Wrong platform file

A keyword trained for one platform is not the same as a keyword trained for another platform.

Examples:
- Web wants `wasm` assets.
- Android wants `android` assets.
- iOS wants `ios` assets.
- Native desktop bindings usually expect their own platform family or absolute path overrides.

If a file loads in the wrong SDK family, re-check the platform suffix first.

## Wrong language model

If the wake-word asset is correct but the model file is wrong, detection usually fails at init or produces nonsense detection behavior.

Use the language-specific `porcupine_params_<lang>.pv` that matches the keyword asset’s language.

## Web-specific asset issues

For Web and React:
- `publicPath` requires the file to be served from a web server.
- `base64` avoids the server requirement.
- If both are set, the base64 asset wins.
- Custom keyword objects need a `label` so detections can be reported meaningfully.

## Sensitivity-related false positives

Sensitivity is a tradeoff:
- higher sensitivity = fewer misses, more false alarms
- lower sensitivity = fewer false alarms, more misses

If a custom wake word is firing too often, lower the sensitivity before changing the model.
If it is missing obvious detections, raise the sensitivity gradually and re-test.

## Mixed asset selection mistakes

When deciding between assets, compare three things together:
1. keyword phrase,
2. platform family, and
3. language model.

A correct phrase with the wrong platform or wrong language still fails.

## When to hand off to the embedded skill

If the task becomes “turn this `.ppn` or `.pv` into a C array for firmware,” stop here and use the sibling `../c-and-embedded/` skill. This sub-skill only owns the asset-selection side of that problem.
