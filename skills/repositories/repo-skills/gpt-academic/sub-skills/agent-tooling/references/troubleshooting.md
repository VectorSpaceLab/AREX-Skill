# Agent Tooling Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Void Terminal picks wrong plugin | natural-language intent too vague or overlaps domains | choose domain sub-skill and exact plugin manually |
| config mutation did not persist | edited runtime state, wrong config precedence, or app not restarted | use `config_private.py`, restart app, verify with root config reference |
| Code Interpreter cannot find file | path is browser-local or upload expired | re-upload or provide server-local path |
| generated code fails import | dependency missing from app environment | ask before installing; prefer a small self-contained script or simpler analysis |
| command assistant output is unsafe | command mutates/deletes/installs/network-downloads | require confirmation, dry-run, backup, or refuse unsafe action |
| plugin execution loops or times out | model/API stall, too broad task, or long-running generated code | narrow scope, lower concurrency, set timeout expectations, split task |
| user pasted API key into prompt | secret exposure risk | tell user to rotate if needed and move secrets to `config_private.py` or environment variables |
