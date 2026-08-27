# ESPnet CI Command Map

Use focused commands unless the user explicitly requests broad CI.

| Change area | Candidate command | Notes |
| --- | --- | --- |
| ESPnet2 bin CLI | `pytest -q test/espnet2/bin/test_<module>.py` | Add a `python -m espnet2.bin.<module> --help` parser smoke when useful. |
| ESPnet2 task/model component | `pytest -q test/espnet2/tasks test/espnet2/<area>` | Optional dependency-heavy tests may skip or need focused extras. |
| Recipe/config changes | `bash ci/test_configuration_espnet2.sh <task>` | This can iterate many configs; run only after approval or with a narrowed task. |
| ESPnet3 utilities/systems | `pytest -q test/espnet3/utils test/espnet3/systems/<area>` | Prefer a targeted file such as `test/espnet3/utils/test_stages.py`. |
| Shell scripts | `bash ci/test_shell_espnet2.sh` | Requires shellcheck/bats and may traverse many recipes. |
| Docs | `bash ci/doc.sh` | Requires doc extras. |
| Import surface | `python ci/test_import_all.py` | Can be broad; skip optional k2/mir_eval paths like CI does. |

Use the bundled selector to generate a starting point without executing anything:

```bash
python sub-skills/development-and-testing/scripts/select_espnet_tests.py --changed-file espnet2/bin/asr_train.py
```
