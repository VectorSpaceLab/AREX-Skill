# Astropy CLI Reference

Run every command with `--help` before using it on user data.

| Command | Main owner | Purpose | Safety note |
| --- | --- | --- | --- |
| `fitsinfo` | `tables-io` | Print FITS HDU summary | Read-only |
| `fitsheader` | `tables-io` | Print FITS headers/keywords | Read-only |
| `fitsdiff` | `tables-io` | Compare FITS files | Read-only unless output path overwrites |
| `fitscheck` | `tables-io` | Verify/update FITS checksum and compliance | Can mutate with update/checksum flags; use copies |
| `fits2bitmap` | `visualization-convolution` | Convert FITS image to bitmap | Use explicit output temp path first |
| `showtable-astropy` | `tables-io` | Display Astropy-readable tables | Read-only |
| `volint` | `tables-io` | Validate VOTable files | Read-only validation |
| `wcslint` | `wcs-nddata` | Diagnose FITS WCS headers | Diagnostic; follow with numeric WCS checks |
| `samp_hub` | `cli-config-data` | Start/control SAMP hub | Starts service; use only when requested |

## Safe Smoke

```bash
python path/to/astropy/scripts/astropy_cli_smoke.py
python path/to/astropy/scripts/astropy_cli_smoke.py --with-fixtures
```

The fixture mode writes only temporary files and checks a bounded read-only
subset.

## Command Formation Rules

1. Prefer explicit input and output paths.
2. Avoid overwriting unless the user asked for it.
3. Use temporary files for parser and format experiments.
4. For commands that can modify FITS metadata, make a backup/copy first.
5. Route command-specific interpretation to the owning sub-skill.
