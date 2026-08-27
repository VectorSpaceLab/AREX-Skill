# chat-memory-storage Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Chat history does not persist between runs | The storage backend is in-memory or the session id changed. | Use a persistent backend and keep the session id stable. |
| Memory construction fails on import | The backend extra or DB driver is missing. | Install the storage extra that matches the backend you chose. |
| User memory is unexpectedly replaced | `user_memory_mode` is set to `replace` instead of `update`. | Switch the mode or inspect the memory flags before the next run. |
| Chat output ignores previous turns | The session was reset or the history load flag is off. | Check the `load_*` flags and avoid resetting the session between turns. |
| A backend connection error appears | The DB URL or credentials are wrong. | Validate the connection string before rerunning the chat. |

## Smoke check

```bash
python sub-skills/chat-memory-storage/scripts/check_storage_backends.py
```
