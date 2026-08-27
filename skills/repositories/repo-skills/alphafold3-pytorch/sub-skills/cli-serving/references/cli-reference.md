# CLI and app reference

This reference is the self-contained operating contract for the package version
covered by this skill. The command names below are installed entry points; they
are not Python module invocation requirements.

## Entry points

| Console command | Role | Required at runtime |
|---|---|---|
| `alphafold3_pytorch` | One non-interactive multimolecule inference and mmCIF write | An existing checkpoint and at least one protein, RNA, or DNA entity |
| `alphafold3_pytorch_app` | Local Gradio entity editor, inference button, and molecule viewer | An existing checkpoint; the command then launches the UI |

`--help` is safe to use for either command. The package may import optional
chemistry/data components while displaying help, so import-time informational
messages or chemistry warnings are not evidence that inference started.

## `alphafold3_pytorch` options

The short and long forms are both supported. Options with `multiple=True` are
repeatable, and each occurrence contributes one sequence to the corresponding
input list.

| Short | Long | Click type | Default | Operational meaning |
|---|---|---|---|---|
| `-ckpt` | `--checkpoint TEXT` | string | none | Checkpoint path. The Click option is not marked required, but the function immediately asserts that the path exists; treat it as required and use a regular file. |
| `-prot` | `--protein TEXT` | string, repeatable | `()` | One protein sequence per occurrence. |
| `-rna` | `--rna TEXT` | string, repeatable | `()` | One single-stranded RNA sequence per occurrence. |
| `-dna` | `--dna TEXT` | string, repeatable | `()` | One single-stranded DNA sequence per occurrence. |
| `-steps` | `--num-sample-steps INTEGER` | integer | `None` | Number of diffusion sampling steps. Omit it to let model defaults apply; a positive bounded value is safer for a planned run. |
| `-cuda` | `--use-cuda BOOLEAN` | Click boolean value | `None` | Request CUDA when available. This is a value-taking option, not a flag: use `--use-cuda true` or `--use-cuda false`. |
| `-o` | `--output TEXT` | string | `output.cif` | Destination mmCIF path. |

A repeated entity is not comma-separated. For example, the following keeps two
proteins, one RNA, and two DNA entities as five separate entries:

```bash
alphafold3_pytorch \
  --checkpoint /models/af3.pt \
  --protein MKTW \
  --protein AGTC \
  --rna ACGU \
  --dna ACGT \
  --dna TTAA \
  --num-sample-steps 8 \
  --use-cuda true \
  --output results/complex.cif
```

The CLI builds `Alphafold3Input(proteins=..., ss_rna=..., ss_dna=...)`, loads
through the model's checkpoint helper, optionally moves the model to CUDA, and
requests a Bio.PDB structure from the model. It then creates missing output
parent directories recursively and writes the returned structure with an
mmCIF writer. The output path is not a cache/session path and the CLI does not
provide ligand or metal-ion flags. Route richer input construction to
[input-representation](../../input-representation/SKILL.md), and checkpoint
compatibility/loading internals to
[model-inference](../../model-inference/SKILL.md).

The CLI does not itself impose the Gradio UI's four-character or alphabet
checks. Do not use that difference to bypass input validation: sequence and
molecule semantics belong to the input sub-skill, and a malformed input can
still fail while constructing or executing the model.

## `alphafold3_pytorch_app` options

| Short | Long | Click type | Default | Operational meaning |
|---|---|---|---|---|
| `-ckpt` | `--checkpoint TEXT` | string, required by Click | none | Existing checkpoint path; the function asserts it exists before loading. |
| `-cache` | `--cache-dir TEXT` | string | `cache` | Disposable root for per-session PDB output. If it already exists, startup recursively deletes it before recreating it. |
| `-prec` | `--precision TEXT` | string | `float32` | Accepted text only. The live conversion code is commented out, so this currently does not change model dtype or device. |

The app has no `--use-cuda`, `--host`, `--port`, authentication, or dry-run
option. After loading the checkpoint it builds a Gradio interface and calls
`launch()`. Use `--help` for parser inspection, but do not use a normal app
command as a harmless preflight: it launches the server and deletes the cache
root first.

## App entities and output

The UI offers `Protein`, `DNA`, `RNA`, `Ligand`, and `Ion` entity types plus a
copy count. On add, it rejects an empty selection, strips leading/trailing
whitespace, and uppercases the value. Polymer checks are:

- protein alphabet `ARDCQEGHILKMNFPSTWYV`;
- DNA alphabet `ACGT`;
- RNA alphabet `ACGU`;
- at least four submitted characters for each polymer type.

Provide at least four meaningful residues/bases after trimming even though the
implemented length check is applied to the submitted string. A sequence that
passes the UI still becomes an `Alphafold3Input`; detailed atom and molecule
semantics are owned by [input-representation](../../input-representation/SKILL.md).

Ligand choices are labels such as `ADP - Adenosine disphosphate`, `ATP -
Adenosine triphosphate`, `FAD - Flavin adenine dinucleotide`, `HEM - Heme`, and
other entries shown by the UI. The stored value is the text before the first
`" - "`, e.g. `ADP`; the descriptive label is not sent to the model. Ion
choices include `Mg²⁺`, `Zn²⁺`, `Cl⁻`, `Ca²⁺`, `Na⁺`, `Mn²⁺`, `K⁺`, `Fe³⁺`,
`Cu²⁺`, and `Co²⁺`. The stored ion value keeps only alphabetic characters, so
`Mg²⁺` becomes `Mg` and `Cl⁻` becomes `Cl`. Use the offered dropdown values and
route chemical validity questions to [input-representation](../../input-representation/SKILL.md).

Each entity is expanded by `num_copies` during `fold`. The UI uses a general
number widget rather than a strict integer validator; enter a positive integer
copy count to avoid list-multiplication/type errors.

For a prediction, the app writes a random URL-safe filename under
`<cache-dir>/<session-hash>/` with a `.pdb` suffix and returns that path to the
molecule viewer. The CLI's `.cif` output and the app's `.pdb` cache output are
different paths and formats.

## Cache and session lifecycle

The app has two cleanup layers:

1. At command startup, an existing `cache-dir` is removed recursively and a
   fresh directory is created. Never point it at a directory containing files
   that are not disposable prediction artifacts.
2. A request's `session_hash` selects its own directory. On unload, the app
   removes only that session directory when a hash is present; a request with
   no hash is ignored. Gradio's block-level cache deletion policy is also
   configured for periodic cleanup.

This is local application behavior, not a durable artifact store. Copy a PDB
out of the cache only after a prediction if it must survive a later app start.
