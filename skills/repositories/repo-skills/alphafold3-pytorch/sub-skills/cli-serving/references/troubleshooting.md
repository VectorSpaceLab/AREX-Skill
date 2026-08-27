# CLI and serving troubleshooting

## Command construction and Click

### `--use-cuda` is rejected or behaves unexpectedly

This option is declared with `type=bool`, so it consumes a value. Use an
explicit value such as `--use-cuda true` or `--use-cuda false`; do not use the
flag-only form `--use-cuda` and do not use a Click flag idiom such as
`--no-use-cuda` unless a future version changes the declaration. The helper
rejects missing/invalid boolean values before printing a command.

### A repeated entity is missing

`--protein`, `--rna`, and `--dna` are `multiple=True`. Repeat the option for
each sequence:

```bash
--protein MKTW --protein AGTC --rna ACGU --dna ACGT
```

Do not combine entities into a comma-separated value or assume one option can
represent copies. The CLI does not expose a ligand or ion option. If the
intended complex includes those, use the input-representation workflow or the
app's entity editor instead.

### The helper refuses an input

The safe builder intentionally requires an existing regular checkpoint, a
non-empty entity list, non-empty strings, a valid CLI DNA/RNA/protein alphabet,
a positive sample-step count when supplied, and a non-empty output path. It
also rejects an output path that is an existing directory. These are planning
gates; it does not prove checkpoint compatibility or run the model. Use
`--help` for the helper's complete options.

## Checkpoint and model failures

### Missing checkpoint

The plain CLI does not mark `--checkpoint` as Click-required, but the callback
immediately asserts that the path exists and reports `AlphaFold 3 checkpoint
must exist at ...`. The app marks it required in Click and then asserts
`checkpoint does not exist at path`. Supply a readable file and check that the
path points to the intended artifact, not merely a directory.

### Checkpoint incompatibility

A present path is not enough. `Alphafold3.init_and_load` must be able to rebuild
the model and load the saved state. Constructor dimensions, optional modules,
checkpoint format, and package version can differ. Typical symptoms include
missing/unexpected state keys, tensor-size mismatch, or failure during model
construction. Do not “fix” this by changing CLI flags: route checkpoint
inspection and model reconstruction to
[model-inference](../../model-inference/SKILL.md), and preserve the original
error for diagnosis.

### Inference fails after the command was valid

The helper validates syntax and cheap local facts only. The actual CLI still
performs full model loading and diffusion sampling. Check, in order:

1. compatible checkpoint/model contract;
2. at least one supported entity and valid input semantics;
3. CPU/GPU memory and device placement;
4. a bounded sampling-step setting;
5. output write permission and a writable parent.

For tensor, molecule, atom, or sampling internals, route to the relevant sibling
rather than duplicating their API here.

## CUDA behavior

The plain CLI moves the loaded model to CUDA only for the conjunction
`use_cuda` truthy and `torch.cuda.is_available()` true. If CUDA was requested
but unavailable, it does not raise a CUDA-specific error and leaves the model
on its original device. This can make an ostensibly GPU-requested run execute
on CPU and become slow or memory constrained. Verify hardware with the shared
environment diagnostic before execution; do not infer device placement from the
presence of `--use-cuda true` alone.

The app's commented conversion block means its `--precision` option currently
has no dtype/device effect. An invalid precision string is not rejected by the
current app because the code that would call `getattr(torch, precision)` and
fallback to `float32` is commented out. Treat this as a verified limitation,
not as a supported precision fallback.

## Output path behavior

The plain CLI uses `Path(output).parents[0].mkdir(exist_ok=True, parents=True)`
before the mmCIF write. A nested output such as
`results/2026/complex.cif` therefore creates missing parents during actual
execution. It does not create them during `--help` or with the safe command
builder. Ensure the output string names a file, not a directory, and expect an
existing file to be subject to the writer's normal overwrite behavior; do not
assume an explicit CLI overwrite guard exists.

The app does not use `--output`. It writes a generated `.pdb` below the cache
root and returns the path to the viewer. To keep a result, copy it elsewhere
before restarting the app or allowing session cleanup.

## App cache, sessions, and entity normalization

### Valuable files disappeared at app startup

This is expected when the configured cache directory already existed: the app
calls recursive removal before `mkdir`. Stop using that directory for anything
else. Choose a newly dedicated disposable directory and recover files from
backup if necessary; this sub-skill does not attempt restoration.

### Session output is not visible after another user's request

Output paths include `cache_dir / session_hash / random_filename.pdb`. Session
isolation is intentional. Unload removes the session directory only when a
session hash exists. Do not treat a session path as stable or share it as a
persistent output URL.

### Ligand or ion value is rejected/misinterpreted

Use an exact dropdown choice. Ligand normalization stores the component code
before the first `" - "` (for example, `ATP - ...` becomes `ATP`). Ion
normalization keeps alphabetic characters from labels containing Unicode charge
marks (for example, `Mg²⁺` becomes `Mg`). The app's display label is not itself
the model input. Chemical component availability and metal semantics belong to
[input-representation](../../input-representation/SKILL.md).

### Polymer cannot be added

The UI uppercases after stripping outer whitespace and allows only:

- protein: `A R D C Q E G H I L K M N F P S T W Y V`;
- DNA: `A C G T`;
- RNA: `A C G U`.

It requires at least four characters. Remove FASTA headers, whitespace inside a
sequence, unsupported symbols, and ambiguous letters before retrying. The CLI
has no identical UI gate, but malformed sequences can fail later in input
construction; use the same conservative validation when planning commands.

### Copy count causes a fold error

The app multiplies a list by `num_copies`. The UI uses `gr.Number`, not a
strict integer/positive validator. Use a positive integer such as `1`, `2`, or
`3`; do not rely on fractional, negative, or non-finite values.

## Server scope and safe checks

`alphafold3_pytorch_app --help` is the safest app inspection. A normal app
invocation loads a checkpoint, deletes/recreates the cache, constructs the UI,
and calls Gradio `launch()`. There is no built-in dry-run, host, port,
authentication, or access-control option in this entry point. Do not launch it
just to check syntax, and do not present it as a hardened remote service.

The bundled command builder is intentionally narrower than the real CLI: it
prints a shell-safe command only, catches common argument/path errors, supports
repeated polymer options and explicit Click booleans, and avoids package
imports, downloads, inference, server launch, and destructive changes.
