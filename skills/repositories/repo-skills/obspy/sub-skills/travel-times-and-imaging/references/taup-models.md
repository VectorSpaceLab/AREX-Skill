# TauP models, phases, and geometry

## Models and construction

`from obspy.taup import TauPyModel` exposes the high-level interface. Construct
`TauPyModel(model='iasp91', verbose=False, planet_flattening=0.0, cache=None)`.
The shipped model names documented by this package include `1066a`, `1066b`,
`ak135`, `ak135f`, `ak135f_no_mud`, `herrin`, `iasp91`, `jb`, `prem`, `pwdk`,
and `sp6`. A custom model is an absolute path to an ObsPy TauP `.npz` model;
only use one when the caller has supplied and can validate it. Model loading is
not a network operation, but can be expensive, so reuse the instance.

`planet_flattening` affects geographic-coordinate-to-epicentral-distance
conversion only. The travel-time and ray-path calculation remains spherical.
`cache` may be an ordered cache object or `False`; it controls depth-split model
reuse and is an optimization, not a different physical model.

## Arrivals

```python
from obspy.taup import TauPyModel

model = TauPyModel(model="iasp91")
arrivals = model.get_travel_times(
    source_depth_in_km=55.0,
    distance_in_degree=67.0,
    phase_list=["P", "S", "PP"],
    receiver_depth_in_km=0.0,
)
for arrival in arrivals:
    print(arrival.name, arrival.time, arrival.ray_param,
          arrival.takeoff_angle, arrival.incident_angle)
```

The result is an `Arrivals` list of `Arrival` objects sorted by time. `time` is
seconds; `distance` and `purist_distance` are degrees; depth arguments are km;
ray parameter values have the units exposed by the Arrival attributes. An
empty result is a valid result for a phase/distance combination and should be
reported rather than replaced with a guessed phase.

Use an explicit phase list for reproducibility. The convenience names
`ttall` and `ttbasic` are accepted phase-list selectors. TauP parses phase names
rather than relying on a fixed list, so malformed or physically unavailable
phase paths can raise a TauP parsing/model error or produce no arrival. Start
with `P` or `S`, then add the requested phase after validating it.

## Ray paths and pierce points

```python
rays = model.get_ray_paths(500.0, 130.0, phase_list=["P", "S"])
pierce = model.get_pierce_points(
    500.0, 130.0, phase_list=["P"], add_depth=[35.0, 410.0, 660.0]
)
for arrival in rays:
    # A NumPy record array; fields are p, time, dist, depth.
    print(arrival.name, arrival.path.dtype, len(arrival.path))
for arrival in pierce:
    print(arrival.name, arrival.pierce.dtype, len(arrival.pierce))
```

`get_ray_paths` returns sampled ray geometry in the `path` field. `get_pierce_points`
returns intersections at model discontinuities and requested `add_depth` values
in `pierce`. These are distinct from a travel-time-only arrival. `receiver_depth_in_km`
is available on both calls; ensure its sign and units match the API (depth below
surface, in km).

For geographic input, use the corresponding `get_travel_times_geo`,
`get_pierce_points_geo`, or `get_ray_paths_geo` methods. They accept source and
receiver latitude/longitude in degrees and source depth in km. With
geographiclib available, geographic path/pierce records can be augmented with
latitude/longitude fields; without it, the calculation may still return the
arrival but warns that positions cannot be evaluated. The `resample=True`
option adds points for easier geographic interpolation and is useful for
plotting long or diffracted paths.

## Plotting TauP results

```python
import matplotlib.pyplot as plt
from obspy.taup import plot_ray_paths, plot_travel_times

fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
plot_ray_paths(100.0, min_degrees=20, max_degrees=140, npoints=6,
               phase_list=["P", "S"], plot_type="spherical",
               fig=fig, ax=ax, show=False, legend=True)
fig.savefig("ray-paths.png", dpi=120)
plt.close(fig)

fig, ax = plt.subplots()
plot_travel_times(10.0, phase_list=["P", "S", "PP"],
                   min_degrees=0, max_degrees=100, npoints=8,
                   fig=fig, ax=ax, show=False)
fig.savefig("travel-times.png", dpi=120)
plt.close(fig)
```

For a precomputed result, `arrivals.plot_rays(plot_type='spherical'|'cartesian',
show=False, ...)` or `arrivals.plot_times(show=False, ...)` returns a Matplotlib
axes. A spherical ray plot needs a polar axes; a Cartesian plot needs an ordinary
axes. `plot_all=False` removes wrap-around rays that travel the other direction
around the globe. `plot_travel_times` and `plot_ray_paths` calculate over a
range of distances; bound `npoints` for runtime and use `verbose=True` when
missing distances need diagnosis.

## Geographic distance choice

- `locations2degrees(lat1, lon1, lat2, lon2)` gives spherical great-circle
distance in degrees and accepts broadcastable NumPy arrays.
- `gps2dist_azimuth(lat1, lon1, lat2, lon2)` gives WGS84 ellipsoidal distance in
metres, forward azimuth at point 1, and backazimuth at point 2. The results are
not TauP travel times.
- `degrees2kilometers` and `kilometer2degrees` use a spherical radius and are
convenience conversions; state the radius if comparing results.

TauP's `get_*_geo` methods use the model radius and `planet_flattening` to get
an epicentral degree distance. They do not apply ellipticity corrections to the
ray travel itself. Do not mix WGS84 metres, spherical km, and degrees without
an explicit conversion and record.

## Evidence boundary

This reference distills the public `obspy.taup` high-level docs/API and tests,
`obspy.geodetics` public utilities, and the travel-time tutorial examples. It
is self-contained and intentionally does not depend on source-checkout paths or
copy test fixtures into the runtime skill.
