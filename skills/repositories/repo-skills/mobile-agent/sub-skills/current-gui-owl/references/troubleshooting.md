# Current GUI-Owl Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `adb` not found | Wrong platform-tools path | Set `ADB_PATH` and rebuild with `build_mobile_command.py --adb-path-env ADB_PATH`. |
| `adb devices` shows unauthorized/offline | USB debugging or pairing not accepted | Reconnect, accept authorization prompt, restart adb server, specify `--device` for multi-device hosts. |
| Taps work but text input fails | ADB Keyboard missing/not selected | Install and select ADB Keyboard or equivalent before typing tasks. |
| App open fails | App display name not mapped to installed package | Add clearer `--add_info`, verify installed packages, or provide resolver API/base/model so the launcher can resolve names. |
| `Failed to parse action from model output` | Model returned prose, invalid JSON, or no `<tool_call>` block | Instruct the model/server prompt wrapper to output exactly one `<tool_call>` with nested `arguments`. |
| Clicks land in wrong place | Coordinate convention mismatch or screenshot scaling issue | Use GUI-Owl/Qwen-style normalized `0..1000` coordinates; do not feed absolute pixels when launcher expects normalized coordinates. |
| Desktop route fails on CI/headless shell | No interactive display or OS automation permission | Move to an unlocked desktop session; grant screenshot/accessibility permissions; use browser headless for website tasks when appropriate. |
| Browser says Chromium missing | Playwright browser binary/system deps absent | Install route-specific Playwright dependencies in the runtime env; command builder only validates flags. |
| Browser screenshots missing from model | Wrong image mode or missing OSS config | Use `base64` first; use `file` only with local servers; use `oss` only with private object-store credentials. |
| OmniParser mode fails | OmniParser service URL unavailable | Use CSS SoM or start/verify the OmniParser service and pass `--omni_url`. |
| API returns authentication/model errors | Missing key, wrong base URL, incompatible model name | Export key/base/model env vars and run a separate private endpoint health check before live GUI control. |

Do not retry live GUI actions repeatedly without inspecting logs and screenshots; these agents can mutate device/desktop/browser state.
