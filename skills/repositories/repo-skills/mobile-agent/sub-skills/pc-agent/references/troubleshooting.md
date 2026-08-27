# PC-Agent Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Screenshot fails on CI/SSH | No interactive GUI session | Move to a real Mac/Windows desktop session; do not verify PC-Agent live in headless CI. |
| Mac cannot control apps | Accessibility/screen-recording permission missing | Grant Terminal/Python permissions and rerun a tiny private task. |
| Windows clicks offset | Wrong `--ratio` or font/scaling mismatch | Start with `--ratio 1.0`, verify screenshot scaling, and set an existing Windows font path. |
| Mac clicks offset | Retina scaling mismatch | Try `--ratio 2.0`; compare screenshot pixels to screen coordinates. |
| Config validator warns about OCR keys | OCR API mode missing credentials | Add private OCR keys or use local/fallback OCR if installed. |
| API returns auth/model error | `config.json` token/url/model invalid | Validate config shape, then test endpoint privately outside live desktop control. |
| SoM boxes obscure or mislabel UI | Font path/OCR/A11y/perception settings | Adjust `--draw_text_box`, `--use_a11y`, `--use_perception_info`, and font path. |
| v1 flags ignored in current run | Mixed `run.py` vs `run_v1.py` | Use the command builder `--version` that matches the script. |

PC-Agent logs/screenshots may contain private desktop content. Store them under private paths and redact before sharing.
