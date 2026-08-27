# Training API reference

Porcupine training is a networked service that turns a phrase into a wake-word model. The bindings in this repo all submit the phrase to Picovoice’s training endpoint and then save the returned bytes as a keyword asset.

## Where the API exists

| SDK | Training entry point | Return value | Platform field |
| --- | --- | --- | --- |
| Python | `train_wake_word_from_phrase(access_key, output_path, language, phrase, platform=None)` | `None` | Optional; defaults to the current runtime platform |
| Android | `Porcupine.trainWakeWordFromPhrase(accessKey, outputPath, language, phrase)` | `void` | Hard-coded to `android` |
| iOS | `Porcupine.trainWakeWordFromPhrase(accessKey:outputPath:language:phrase:)` | `throws` only on failure | Hard-coded to `ios` |
| Web | `Porcupine.trainWakeWordFromPhrase(accessKey, writePath, language, phrase)` | `Promise<PorcupineKeyword>` | Hard-coded to `wasm` |
| React | No separate trainer in the React wrapper | Use the Web SDK trainer | Same as Web |
| Node.js / .NET / Java / Flutter / React Native | No trainer in this checkout | Consume prebuilt assets only | N/A |

## Python signature and validation

The Python public wrapper performs the following validation before sending the network request.

```python
train_wake_word_from_phrase(
    access_key: str,
    output_path: str,
    language: str,
    phrase: str,
    platform: Optional[str] = None,
) -> None
```

Validation rules:
- `language` must be one of `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, `pt`.
- `platform` must be one of `linux`, `mac`, `windows`, `raspberry-pi`, `wasm`, `android`, `ios` when provided.
- `phrase` must not be empty.
- `phrase` must not exceed 64 characters.

If `platform` is omitted, Python resolves the current runtime platform and sends that value.

## Request contract

The bindings send a JSON POST to:

`https://rest.picovoice.ai/{language}/api/ppn`

Payload shape:

```json
{
  "platform": "android|ios|wasm|linux|mac|windows|raspberry-pi",
  "phrase": "custom wake phrase"
}
```

Headers:
- `x-api-key: <AccessKey>`
- `Content-Type: application/json` is set by the web binding and by the JSON request flow used in the other bindings.

The response body is the trained wake-word asset bytes.

## Output-path behavior

The path you supply is the storage target, not a parser gate.

- Python, Android, and iOS write the response bytes to the file path you provided.
- Web writes the bytes to IndexedDB under the requested write path and returns a `PorcupineKeyword` object.
- The filename suffix is a convention; the returned bytes still need the correct platform/language pairing regardless of the suffix you choose.

Use the correct platform/language pairing for the returned bytes; the extension alone does not make a file loadable.

## AccessKey and network requirements

Training requires:
- a valid Picovoice `AccessKey`,
- outbound HTTPS access to `rest.picovoice.ai`, and
- whatever quota or account allowance your Console plan provides.

The training helpers do not perform offline synthesis.

## Error mapping

- Invalid language or platform inputs fail before the network call.
- Empty or overlong phrases fail before the network call.
- HTTP failures are converted into runtime errors that include the response body when available.
- Network, TLS, or proxy failures surface as request/runtime errors from the binding.
- Save failures are reported when the output path cannot be written.

## Asset lifecycle after training

1. Train the model for the target platform.
2. Pair the returned asset with the matching `.pv` language model.
3. Load it through the SDK-specific keyword-path mechanism for that platform.
4. Keep keyword order aligned with sensitivity order.

If you need to package the resulting bytes into MCU firmware as a C array, hand off to the sibling `../c-and-embedded/` skill instead of trying to invent a local conversion flow here.
