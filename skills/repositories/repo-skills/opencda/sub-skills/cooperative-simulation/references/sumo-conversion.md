# SUMO files and OpenDRIVE conversion

## The map triplet

A co-simulation scenario is organized around a basename. For a directory named
`MapName`, keep these files together:

- `MapName.sumocfg`: SUMO configuration; its `<input>` section points to the
  network and route files.
- `MapName.net.xml`: SUMO road graph, usually produced from the matching
  OpenDRIVE map.
- `MapName.rou.xml`: vehicle types, routes, flows, or explicit vehicles.

`CoScenarioManager` derives the config path from the directory basename and
requires that exact `.sumocfg` file. A missing file, directory/config basename
mismatch, or config references to files in another directory should be treated
as a preflight error. The XML config may use relative paths; resolve them from
the config file's directory, not the caller's current directory.

The route file must reference edge/lane IDs that exist in the selected network.
This checker can confirm files and config references but cannot validate route
connectivity without a SUMO network parser/server. Do not assume that an
existing XML file is semantically compatible with a CARLA map.

## Converting OpenDRIVE

The repository's `netconvert_carla.py` adapts an OpenDRIVE file for SUMO. It
invokes the external `netconvert`, imports the generated network, builds
OpenDRIVE-to-SUMO topology, and inserts traffic-light landmarks/programs. It
requests original names because the bridge uses mapped road/lane identity.
`--guess-tls` changes how junction traffic-light connections are inferred.

The conversion command is intentionally not wrapped by the bundled preflight
script. Only run it after confirming SUMO_HOME/tools, `netconvert`, `sumolib`,
CARLA Python bindings, the input `.xodr`, and a writable output location. Use a
new output path; do not overwrite the source OpenDRIVE or a known-good network
without an explicit backup/reproducibility decision. Conversion can fail on
missing original lane IDs, unsupported OpenDRIVE features, no edges, or
traffic-light connectivity that cannot be mapped.

## Configuration review

Before a live run, check:

1. Directory and three filenames share the intended basename.
2. `<net-file value="...">` resolves to the intended `.net.xml`.
3. `<route-files value="...">` resolves to one or more intended `.rou.xml`
   files, with semicolon-separated values handled explicitly.
4. Route vehicle types and edge IDs exist in the network; use SUMO tooling for
   this semantic check when available.
5. `step_length`, host/port, client order, and GUI settings are present in
   OpenCDA YAML.
6. The CARLA map is the same OpenDRIVE source or a deliberately documented
   coordinate-compatible map, including landmark IDs and network offset.

The safe checker reports environment and XML/file facts only. It never invokes
`netconvert`, `sumo`, `sumo-gui`, TraCI, or CARLA.
