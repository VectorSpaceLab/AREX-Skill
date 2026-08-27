# Deployment troubleshooting

## Docs selection problems
- **No docs found:** run exploration first, or choose no-doc mode if you accept a lower success rate.
- **Both docs bases exist:** select either `auto_docs/` or `demo_docs/` explicitly.
- **Docs are out of date:** regenerate exploration docs for the current app version.

## Device and adb problems
- **No device found:** `adb devices` returned nothing.
- **Invalid device size:** the controller could not read the screen geometry.
- **Input command failed:** adb may have lost the connection or the app may have changed state unexpectedly.

## Parser and model problems
- **Action parser error:** the multimodal backend did not return the expected four-field format.
- **Unsupported model type:** `MODEL` must be `OpenAI` or `Qwen`.
- **Backend request errors:** check the selected API key, endpoint, and model name in `config.yaml`.

## Grid and motion issues
- **Grid mode selected the wrong spot:** this is usually a model or labeling issue, but the precise grid-swipe helper is also known to be buggy in the source repo.
- **Swipe seems offset:** prefer ordinary element swipes when they are available.

## Layout and output problems
- **Task logs are missing:** confirm the chosen `root_dir` is writable.
- **Generated output clutters the checkout:** use a separate working directory for `root_dir`.
- **The task ends immediately:** the model may have returned `FINISH`, or the max-round limit may have been reached too early.
