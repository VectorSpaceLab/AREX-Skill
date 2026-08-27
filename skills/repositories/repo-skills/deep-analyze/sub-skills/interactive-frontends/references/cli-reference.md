# DeepAnalyze CLI reference

Use the terminal client when the goal is quick interaction, file upload/download, or command-history driven analysis.

## Start conditions

- The API server should be reachable at `http://localhost:8200/v1`.
- The client prechecks `http://localhost:8200/health` and falls back to model listing.
- The English and Chinese entry points behave the same, with localized command labels.
- Command history is stored under `~/.deeppanalyze_history_en` or `~/.deeppanalyze_history_zh`.

## Command map

| Command | Effect | Notes |
|---|---|---|
| `help` / `h` | Show command help | Lists file, system, and history commands |
| `quit` / `exit` | Leave the loop | Ctrl+C and EOF also exit |
| `files` / `ls` | Show uploaded and generated files | Generated files are workspace outputs with URLs |
| `upload <file_path>` | Upload a local file | File is pushed to the server and tracked locally |
| `delete <file_id>` | Delete one uploaded file | Removes it from the server and from the local list |
| `download <file_id> [save_path]` | Download by file id | If `save_path` is a directory, the original file name is used |
| `status` | Show server, model, thread, and counts | Useful for connectivity checks |
| `history` | Show recent conversation records | Shows last 6 messages and counters |
| `fid` | Show full uploaded file IDs | Helpful when the truncated list is not enough |
| `clear` | Clear conversation history only | Resets generated-file records and thread id too |
| `clear-all` | Clear everything | Also deletes uploaded files on the server |

Chinese aliases accepted by the Chinese CLI include `帮助`, `退出`, `清除`, `全部清除`, `文件`, `状态`, and `历史`.

## File behavior

- `upload` records the remote file id, original name, size, and purpose.
- `files` shows two groups:
  - user uploaded files
  - AI generated workspace files, which may include reports, tables, or images
- `fid` shows the complete file ids; `files` truncates them.
- `clear` keeps uploaded files on the server; `clear-all` removes them.
- `download` uses the uploaded-file name when it knows it, or a fallback `downloaded_file_<prefix>` name otherwise.

## Conversation state

- The CLI stores the current thread id and sends it with the latest user message.
- Uploaded file ids are attached from the local uploaded-file list.
- Generated files are collected from streamed response chunks and remembered separately.
- `history` shows recent user/assistant turns, the current thread id, and the generated-file count.

## Examples

```text
upload sales.csv
files
fid
download file-abc123 ./downloads
status
clear
clear-all
```

## Troubleshooting notes

- If the client says the API server is offline, check the backend endpoint first.
- If `download` returns an error, confirm that the id belongs to an uploaded file.
- If history does not persist, check write permission for the shell history file.
