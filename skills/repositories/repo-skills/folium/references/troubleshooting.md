# Folium Troubleshooting

## Purpose

Use this for cross-cutting Folium problems that are not specific to one sub-skill: installation, import errors, optional dependencies, browser/CDN failures, PNG export, or skill staleness.

## Install and import issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ImportError` when importing `folium` | The package is not installed or the environment is broken | Reinstall Folium in the active Python environment and rerun `python -c "import folium"`. |
| `ImportError` mentioning `branca` | A core dependency is missing or mismatched | Reinstall Folium together with its dependencies; do not mix incompatible package versions in the same environment. |
| A workflow fails only when `pandas`, `geopandas`, `pillow`, `flask`, `jenkspy`, or `selenium` is used | The optional support package for that workflow is missing | Install the missing package only for the sub-skill that needs it. |

## Browser, CDN, and client-side behavior

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Python render succeeds but the map is blank or broken in the browser | The browser could not fetch Leaflet assets, plugin assets, or tiles | Open the browser console and network panel, then check CDN/CSP/ad-blocker failures before changing Python code. |
| A plugin appears in Python HTML but not visually in the browser | The browser rejected the plugin's JavaScript or CSS | Verify that the browser loaded the expected script tags and that custom callback code is valid JavaScript. |
| A map works in notebook output but not in a deployed page | The page blocks remote assets or mixed content | Try a local HTML save first, then inspect browser security settings and CSP rules. |

## PNG export and notebook output

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `_repr_png_()` returns `None` | PNG export is disabled on the map | Enable PNG export only when you need it. |
| PNG export raises a Selenium or browser-driver error | The environment lacks the Selenium/browser pieces Folium uses for screenshot capture | Install Selenium plus a working headless browser/driver, then rerun the PNG check. |
| Notebook output shows a trust warning instead of rendering cleanly | The notebook is not trusted or the browser is blocking the inline output | Save the map to HTML or trust the notebook before retrying. |

## Skill staleness

If the repository commit, package version, or working tree state no longer matches `references/repo-provenance.md`, refresh the generated skill before relying on its instructions.

## Fast recovery sequence

1. Re-run the minimal import check.
2. Confirm the workflow's optional support packages are installed.
3. Save the map to a local HTML file and open it in a browser.
4. Inspect the browser console/network panel.
5. If PNG export is the problem, verify Selenium and the browser driver before changing Folium code.
