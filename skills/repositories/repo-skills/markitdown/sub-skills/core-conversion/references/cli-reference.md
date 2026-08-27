# MarkItDown CLI Reference

## Command Shape

```bash
markitdown [OPTIONS] [FILENAME]
```

If `FILENAME` is omitted, the CLI reads bytes from stdin. By default Markdown is written to stdout; use `--output` to write a file.

Common examples:

```bash
markitdown report.pdf > report.md
markitdown report.pdf --output report.md
cat report.html | markitdown --extension html --mime-type text/html --charset utf-8
```

The console script entry point is `markitdown = markitdown.__main__:main`; `python -m markitdown` exercises the same module.

## Core Flags

| Flag | Meaning |
| --- | --- |
| `-v`, `--version` | Print MarkItDown version and exit. |
| `-o`, `--output PATH` | Write Markdown to `PATH` instead of stdout. |
| `-x`, `--extension EXT` | Hint file extension, especially for stdin. The CLI normalizes `html` to `.html`. |
| `-m`, `--mime-type TYPE/SUBTYPE` | Hint MIME type. Values without exactly one slash are rejected. |
| `-c`, `--charset NAME` | Hint charset. The CLI validates names with Python codecs and normalizes aliases. |
| `-p`, `--use-plugins` | Enable installed third-party plugin converters. Route plugin authoring to `../plugin-development/SKILL.md`. |
| `--list-plugins` | List installed MarkItDown plugin entry points and exit. |
| `--keep-data-uris` | Preserve embedded data URIs instead of truncating them. Use only when large base64 output is acceptable. |

Cloud flags exist in CLI help but are outside this sub-skill: `--use-docintel`, `--use-cu`, `--endpoint`, `--cu-endpoint`, `--cu-analyzer`, and `--cu-file-types` route to `../cloud-integrations/SKILL.md`.

## Stdin and Stream Hints

When reading from stdin, MarkItDown may not know the filename, extension, MIME type, or charset. Provide hints when the bytes are not self-describing:

```bash
cat payload.bin | markitdown --extension pdf --mime-type application/pdf > payload.md
printf '<h1>Hello</h1>' | markitdown --extension html --mime-type text/html --charset utf-8
```

Hints are optional for formats that Magika and built-in sniffing can identify reliably, but explicit hints make automation more robust and improve error messages.

## Output Handling

- `--output path.md` writes Markdown with UTF-8 encoding.
- Without `--output`, redirect stdout with shell redirection when needed.
- CLI errors print a message to stderr and exit non-zero. Invalid MIME types and invalid charsets are rejected before conversion.
- `--list-plugins` exits after listing plugins and does not convert input.

## Data URI Preservation

The default behavior truncates data URIs embedded in generated Markdown. Use `--keep-data-uris` only when downstream consumers need full embedded base64 payloads and output size is acceptable:

```bash
markitdown page.html --keep-data-uris --output page.md
```

The API equivalent is `keep_data_uris=True` on `convert`, `convert_local`, `convert_stream`, `convert_uri`, or `convert_response`.

## Safe CLI Boundaries

- Treat input paths and URI-like strings as I/O performed with current process privileges.
- For untrusted stdin, prefer explicit `--extension`, `--mime-type`, and `--charset` hints and write output to a controlled path.
- Do not use cloud flags unless the user explicitly asks for Azure conversion and provides the required endpoint configuration.
- Do not enable `--use-plugins` unless installed plugin behavior is trusted for the input.
