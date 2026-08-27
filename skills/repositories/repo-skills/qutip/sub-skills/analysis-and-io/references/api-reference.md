# Analysis and I/O API reference

Use this file for plotting, phase-space, tomography, serialization, and reporting helpers.

## Plotting helpers

Representative plotting entry points include:

- `Bloch(fig=None, axes=None, view=None, figsize=None, background=False)` for Bloch-sphere rendering.
- `hinton(...)` for Hinton diagrams of operators and qubit superoperators.
- `matrix_histogram(...)` for matrix bar plots.
- `plot_wigner(...)`, `plot_qfunc(...)`, `plot_wigner_sphere(...)`, `plot_spin_distribution(...)` for quasi-probability views.
- `plot_expectation_values(...)` for solver-result expectation values.
- `anim_*` helpers for animations when Matplotlib animation support is available.

## Phase-space and distribution functions

- `wigner(psi, xvec, yvec=None, method='clenshaw', g=sqrt(2), sparse=False, parfor=False, offset=0)` computes Wigner values.
- `qfunc(...)`, `spin_wigner(...)`, and `spin_q_function(...)` compute related quasi-probability functions.
- `HarmonicOscillatorWaveFunction` and `HarmonicOscillatorProbabilityFunction` wrap harmonic-oscillator probability distribution calculations.

## Tomography and visualization utilities

- `qpt`, `qpt_plot`, and `qpt_plot_combined` support quantum process tomography workflows.
- `wigner_cmap` and `complex_phase_cmap` provide QuTiP color maps.
- `qutip.settings.colorblind_safe` adjusts default plotting color choices.

## File I/O and reporting

- `qsave(data, filename='qutip_data')` serializes QuTiP objects and appends `.qu`.
- `qload(filename)` loads saved QuTiP objects.
- `file_data_store(...)` and `file_data_read(...)` handle raw numeric matrix data.
- `about()` prints package/dependency/runtime information.
- `cite()` prints citation guidance.
- `ipynbtools.version_table` helps with notebook environment reports when IPython-style tools are installed.
