# Sensors, viewers, and examples

## Sensor API overview

Installed inspection confirmed these public sensor constructors:

- `SensorContact(model, *, sensing_bodies=None, sensing_shapes=None, counterpart_bodies=None, counterpart_shapes=None, measure_total=True, verbose=None, request_contact_attributes=True, **kwargs)` measures contact forces/friction/positions on selected bodies or shapes.
- `SensorFrameTransform(model, shapes, reference_sites, *, verbose=None)` measures transforms of shapes/sites relative to reference sites.
- `SensorIMU(model, sites, *, verbose=None, request_state_attributes=True)` measures acceleration and angular velocity at site frames.
- `SensorTiledCamera(model, *, default_render_config=None, config=<deprecated>, load_textures=True)` raytraces color/depth output arrays across worlds.

Most sensors are created once during setup, request any extended attributes they need, and then update each simulation step. Create sensors before allocating `State` or `Contacts` when they request extra arrays, or recreate those buffers afterwards.

## Label matching

Several sensor APIs accept integer indices, glob strings, lists of glob strings, or compiled regular expressions.

- Ordinary strings use glob syntax such as `foot_*`.
- Regex patterns use full-match semantics.
- Use explicit indices after debugging labels when ambiguity is possible.

## Sensor update order

Typical loop:

1. Build model and sites/shapes.
2. Create sensors so they request needed extended attributes.
3. Allocate `State`, `Control`, `CollisionPipeline`, and `Contacts`.
4. Step the solver and update contacts.
5. Call sensor `update()`.
6. Copy or inspect outputs with `.numpy()` when needed.

`SensorContact` needs contact-force attributes populated by a solver/contact update path. If contact forces are missing, recreate contacts after sensor creation and verify the solver supports requested contact attributes.

## Viewer API overview

Installed inspection confirmed these public viewer constructors:

- `ViewerNull(num_frames=1000, benchmark=False, benchmark_timeout=None, benchmark_start_frame=3)` for tests/headless runs.
- `ViewerFile(output_path, auto_save=True, save_interval=100, max_history_size=None)` for persistent state snapshots.
- `ViewerUSD(output_path, fps=60, up_axis="Z", num_frames=100, scaling=1.0, points_as_spheres=True)` for USD time-sampled scene output.
- `ViewerGL(width=1920, height=1080, vsync=False, headless=False, paused=False, plot_history_size=250)` for OpenGL live/headless rendering.
- `ViewerRTX(width=1280, height=720, vsync=False, headless=False, paused=False, fps=60, up_axis="Z", num_frames=None, scaling=1.0, environment="default", async_rendering=True)` for OVRTX path-traced rendering.
- `ViewerRerun(app_id=None, rec_id=None, address=None, serve_web_viewer=True, web_port=9090, grpc_port=9876, keep_historical_data=False, keep_scalar_history=True, record_to_rrd=None)` for Rerun timelines.
- `ViewerViser(port=8080, label=None, verbose=True, share=False, record_to_viser=None, plot_history_size=250)` for browser/notebook visualization.

Common methods include `set_model()`, `begin_frame()`, `log_state()`, `log_contacts()`, `log_lines()`, `log_points()`, `log_image()`, `end_frame()`, `is_running()`, `is_paused()`, `should_step()`, `close()`, `set_camera()`, `set_visible_worlds()`, and `set_world_offsets()`.

## Viewer loop pattern

```python
viewer = newton.viewer.ViewerNull(num_frames=100)
viewer.set_model(model)

while viewer.is_running():
    if viewer.should_step():
        # step simulation
        pass
    viewer.begin_frame(sim_time)
    viewer.log_state(state)
    viewer.log_contacts(contacts, state)
    viewer.end_frame()
viewer.close()
```

Use `ViewerNull` in tests when visual output is not required.

## Example CLI

Newton exposes examples through the package CLI:

```bash
python -m newton.examples --list
python -m newton.examples basic_pendulum --viewer null --device cpu --test
python -m newton.examples basic_pendulum --help
```

Important common flags:

- `--viewer {gl,usd,rtx,rerun,null,viser}`.
- `--device DEVICE` for Warp device selection.
- `--num-frames N` for fixed run length.
- `--test` to run example assertions.
- `--headless` for GL/RTX headless modes where supported.
- `--output-path PATH` for USD output.
- `--benchmark [SECONDS]` to force null viewer and benchmark timing.
- `--warp-config KEY=VALUE` for validated `warp.config` overrides.

Examples may require optional extras; use root and sub-skill diagnostics before assuming a CLI error is a code bug.

## Persistent artifacts

- Use `ViewerUSD` when a USD scene/timeline is the requested output.
- Use `ViewerFile` for state-snapshot recording/replay workflows.
- Use `ViewerRerun(record_to_rrd=...)` when a Rerun timeline artifact is desired and dependencies are installed.
- Use `ViewerViser(record_to_viser=...)` for Viser recordings where supported.

Keep output paths controlled by the user or a temporary workspace; do not overwrite user files silently.
