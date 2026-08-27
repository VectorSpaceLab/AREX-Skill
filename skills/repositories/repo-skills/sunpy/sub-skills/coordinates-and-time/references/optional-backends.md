# Optional and external coordinate backends

The core coordinates/time route is CPU-only and works with SunPy plus Astropy's
normal dependencies. The following capabilities are intentionally not bundled
into the safe smoke helper because they need optional packages, kernels,
network access, or mission-specific provenance.

## SPICE (`sunpy.coordinates.spice`)

The module requires the optional `spiceypy` package and valid SPICE kernels.
Kernel loading is process-global and the wrapper is not thread-safe; use
separate processes for parallel jobs. The public flow is conceptually:

1. install `spiceypy` in the target environment;
2. call `sunpy.coordinates.spice.initialize(kernels)` with local kernel paths;
3. use `install_frame()`, `get_body()`, or `get_fov()` as required;
4. transform a SPICE coordinate or call its
   `.to_helioprojective()` method.

Kernels are not data-free configuration: record their source, version, coverage,
frame names, and loaded paths in the experiment record. Two-dimensional SPICE
coordinates can only transform when the source/destination centers match;
velocity transforms are not supported. Do not invent a kernel path or download
one implicitly. A missing `spiceypy`, frame, kernel coverage, or center is an
optional-backend block, not a reason to weaken a core coordinate claim.

## Horizons and remote ephemerides

`sunpy.coordinates.get_horizons_coord()` sends a request to JPL Horizons and
may accept a time sequence or a range dictionary. It is unsuitable for an
offline smoke test and can fail due to network, service, or body-name issues.
Use `get_body_heliographic_stonyhurst()` for a local baseline, then compare
against Horizons only when the remote result and query parameters are recorded.
Do not place credentials, remote URLs, or downloaded responses in a generated
runtime skill.

Astropy's higher-accuracy JPL solar-system ephemeris providers may also require
an optional package, network download, or cache. Configure them explicitly and
label the provider; SunPy's built-in ephemeris is the deterministic default, not
a guarantee of mission-kernel accuracy.

## WCS/map dependencies

Astropy WCS frame registration is part of the core route. A complete map,
reprojection, or plotting workflow may additionally need SunPy map support,
`reproject`, Matplotlib, or local FITS metadata. Those dependencies do not
change the coordinate-frame contracts here. Use an existing map's
`coordinate_frame` when available and route map construction/visualization
elsewhere.
