# Installation and Environment

Read this when a task involves installing OpenFE, checking an environment, choosing a container/conda route, or diagnosing imports before planning or execution.

## Public Install Routes

OpenFE is distributed primarily through conda-style environments because it depends on scientific Python, chemistry, and OpenMM packages. Prefer one of these public routes:

- Conda or micromamba from conda-forge for a normal user environment.
- The OpenFE single-file installer when the user wants a bundled OpenFEforge environment.
- Docker or Apptainer/Singularity images for containerized execution, especially on HPC systems.
- Developer checkout installation only when the user is editing OpenFE itself: create the documented dependency environment first, then install the checkout editable with dependencies already satisfied.

OpenFE requires POSIX-like systems and Python 3.11 or newer in the generated skill baseline. Avoid translating OpenFE into a plain `pip install` expectation unless the user already has all compiled/conda dependencies available.

## Minimal Import and CLI Checks

Use these checks after installation and before deeper workflow work:

```bash
python - <<'PY'
import openfe, openfecli
print(openfe.__version__)
print(openfecli.__version__)
PY
openfe --help
```

If the CLI fails but imports work, check console-script installation and the `openfecli` package. If imports fail, run the environment diagnostic helper:

```bash
python scripts/check_openfe_environment.py --json
```

## Important Dependencies and Optional Surfaces

OpenFE workflows commonly require these dependency families:

- OpenMM and OpenMMTools for molecular simulation execution.
- OpenFF Toolkit, RDKit, OpenEye or related chemistry backends for molecule handling and charges.
- LOMAP, Kartograf, Konnektor, and Perses-related packages for atom mapping and network planning surfaces.
- PyMBAR/JAX for analysis; OpenFE disables PyMBAR JAX acceleration by default unless the user changes `PYMBAR_DISABLE_JAX`.
- Cinnabar and pandas-like tooling for result analysis and tabular outputs.

Missing optional chemistry backends can block charge generation or specific mapper choices while still allowing read-only planning diagnostics.

## OpenMM and Hardware Notes

OpenFE can run on CPU or GPU depending on OpenMM platform settings and installed drivers/toolkits. On HPC systems, validate the runtime node rather than only the login node.

When diagnosing GPU execution:

- Check `nvidia-smi` or the cluster-provided hardware report on the node where jobs run.
- Check OpenMM platform availability with a small OpenMM test only when the user wants environment validation.
- CUDA/PTX errors usually mean the OpenMM/CUDA toolkit version is incompatible with the host driver or GPU architecture.
- JAX warnings from PyMBAR analysis do not necessarily mean OpenMM simulation fell back to CPU.

## Environment Hygiene

- Use isolated environments; avoid installing into conda `base`.
- Do not run long OpenFE tests, `quickrun`, or tutorial downloads unless the user explicitly asks.
- Keep installation paths, activation commands, and private environment names out of generated reports or reusable guidance.
- Record only public package names, versions, import names, and safe diagnostic outputs when documenting an issue.
