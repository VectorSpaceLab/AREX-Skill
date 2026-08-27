# Custom and Marketplace Tools

## When to Read

Read this when a tool is not built in and must be loaded from `tools.json`, a
GitHub repository, or the marketplace flow.

## Static Dynamic-Tool Behavior

- `superagi/tool_manager.py` downloads repo zipballs from GitHub and extracts
  tool directories into `superagi/tools/external_tools` or
  `superagi/tools/marketplace_tools`.
- `superagi.helper.tool_helper.process_files` scans built-in, external, and
  marketplace tool trees to register toolkits and tool records in the database.
- `tool_manager.py` also updates `tools.json` entries that point to tool
  repositories.

## Why This Is Sensitive

- The dynamic download path performs network access.
- It writes files into the checkout or container filesystem.
- The installer script can trigger apt and pip package installation.
- Marketplace tools may carry their own requirements or filesystem assumptions.

## Safe Interpretation for Future Agents

- Treat the dynamic downloader as evidence, not as a default helper to run.
- Prefer static inspection of `tools.json`, built-in tool classes, and toolkit
  config keys before downloading anything.
- If a user wants a specific custom tool, confirm the target repository and the
  safety of the download/install process before proceeding.
- Keep tool-specific troubleshooting near the owning tool or toolkit family when
  a failure is obviously local to one integration.
