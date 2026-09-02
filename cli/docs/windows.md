# Windows Setup

DisCo requires a bash shell on Windows. Checked locations (in order):

1. Custom path from `~/.disco/agent/settings.json`
2. Git Bash (`C:\Program Files\Git\bin\bash.exe`)
3. `bash.exe` on PATH (Cygwin, MSYS2, WSL)

For most users, [Git for Windows](https://git-scm.com/download/win) is sufficient.
The DisCo PowerShell managed installer checks for an existing bash first and
can prepare a user-level Git for Windows runtime when no usable bash is found.

## Custom Shell Path

```json
{
  "shellPath": "C:\\cygwin64\\bin\\bash.exe"
}
```
