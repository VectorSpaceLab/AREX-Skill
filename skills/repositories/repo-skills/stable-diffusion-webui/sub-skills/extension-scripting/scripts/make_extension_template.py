#!/usr/bin/env python3
"""Create a safe Stable Diffusion WebUI extension skeleton.

This helper intentionally imports only Python stdlib modules. The generated
extension files may import WebUI runtime modules because WebUI loads them inside
its own process.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from textwrap import dedent

VALID_KINDS = ("selectable", "alwayson", "postprocessing", "callback")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-_").lower()
    if not slug:
        raise argparse.ArgumentTypeError("name must contain at least one letter or digit")
    return slug


def class_suffix(slug: str) -> str:
    parts = re.split(r"[-_]+", slug)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def py_identifier(slug: str) -> str:
    ident = re.sub(r"\W+", "_", slug).strip("_").lower()
    if not ident:
        ident = "extension"
    if ident[0].isdigit():
        ident = f"ext_{ident}"
    return ident


def display_name(slug: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[-_]+", slug) if part)


def write_new(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def selectable_script(slug: str) -> str:
    cls = f"Script{class_suffix(slug)}"
    title = display_name(slug)
    return dedent(f'''
        import gradio as gr
        from modules import scripts
        from modules.processing import process_images


        class {cls}(scripts.Script):
            def title(self):
                return "{title}"

            def show(self, is_img2img):
                return True

            def ui(self, is_img2img):
                enabled = gr.Checkbox(label="Enable {title}", value=True, elem_id=self.elem_id("enabled"))
                strength = gr.Slider(label="{title} strength", value=0.5, minimum=0.0, maximum=1.0, step=0.05, elem_id=self.elem_id("strength"))
                self.infotext_fields = [(strength, "{title} Strength")]
                self.paste_field_names = ["{title} Strength"]
                return [enabled, strength]

            def run(self, p, enabled, strength):
                if enabled:
                    p.extra_generation_params["{title} Strength"] = strength
                return process_images(p)
        ''').lstrip()


def alwayson_script(slug: str) -> str:
    cls = f"Script{class_suffix(slug)}"
    title = display_name(slug)
    return dedent(f'''
        import gradio as gr
        from modules import scripts


        class {cls}(scripts.Script):
            def title(self):
                return "{title}"

            def show(self, is_img2img):
                return scripts.AlwaysVisible

            def ui(self, is_img2img):
                enabled = gr.Checkbox(label="Enable {title}", value=False, elem_id=self.elem_id("enabled"))
                tag = gr.Textbox(label="{title} infotext tag", value="demo", elem_id=self.elem_id("tag"))
                self.infotext_fields = [(tag, "{title} Tag")]
                self.paste_field_names = ["{title} Tag"]
                return [enabled, tag]

            def before_process(self, p, enabled, tag):
                if not enabled:
                    return
                p.extra_generation_params["{title} Tag"] = tag
        ''').lstrip()


def postprocessing_script(slug: str) -> str:
    cls = f"ScriptPostprocessing{class_suffix(slug)}"
    title = display_name(slug)
    return dedent(f'''
        import gradio as gr
        from modules import scripts_postprocessing


        class {cls}(scripts_postprocessing.ScriptPostprocessing):
            name = "{title}"
            order = 1000

            def ui(self):
                enabled = gr.Checkbox(label="Enable {title}", value=False)
                note = gr.Textbox(label="{title} note", value="")
                return {{
                    "enabled": enabled,
                    "note": note,
                }}

            def process(self, pp: scripts_postprocessing.PostprocessedImage, enabled, note):
                if not enabled:
                    return
                if note:
                    pp.info["{title} Note"] = note
        ''').lstrip()


def callback_script(slug: str) -> str:
    route = py_identifier(slug).replace("_", "-")
    title = display_name(slug)
    return dedent(f'''
        from fastapi import FastAPI
        from modules import script_callbacks


        def add_api_routes(demo, app: FastAPI):
            @app.get("/sdapi/v1/{route}/status")
            async def status():
                return {{"ok": True, "extension": "{title}"}}


        def on_unload():
            # Undo monkey patches, hooks, or global state here if this extension adds any.
            pass


        script_callbacks.on_app_started(add_api_routes, name="api-routes")
        script_callbacks.on_script_unloaded(on_unload, name="cleanup")
        ''').lstrip()


def javascript(slug: str) -> str:
    marker = py_identifier(slug)
    return dedent(f'''
        onUiLoaded(function() {{
            document.body.dataset.{marker}Loaded = "true";
        }});
        ''').lstrip()


def readme(slug: str, kind: str) -> str:
    title = display_name(slug)
    return dedent(f'''
        # {title}

        Generated Stable Diffusion WebUI extension skeleton.

        ## Kind

        `{kind}`

        ## Files

        - `scripts/{slug}.py` contains the Python extension entrypoint.
        - `javascript/{slug}.js` is present only when generated with `--javascript`.
        - `metadata.ini` is intentionally omitted; add it only when extension/script/callback ordering is required.

        ## Next Checks

        1. Start WebUI with extensions enabled.
        2. Confirm the script or callback behavior appears in the UI or API.
        3. Query `/sdapi/v1/script-info` for generation scripts and verify argument order before automating API calls.
        ''').lstrip()


def script_for_kind(kind: str, slug: str) -> str:
    if kind == "selectable":
        return selectable_script(slug)
    if kind == "alwayson":
        return alwayson_script(slug)
    if kind == "postprocessing":
        return postprocessing_script(slug)
    if kind == "callback":
        return callback_script(slug)
    raise ValueError(f"unsupported kind: {kind}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Stable Diffusion WebUI extension skeleton.")
    parser.add_argument("name", type=slugify, help="Extension directory name, e.g. my-alwayson-hook")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd(), help="Parent directory for the extension directory; default: current directory")
    parser.add_argument("--kind", choices=VALID_KINDS, default="alwayson", help="Skeleton type to generate")
    parser.add_argument("--javascript", action="store_true", help="Also create javascript/<name>.js with a minimal onUiLoaded hook")
    parser.add_argument("--force", action="store_true", help="Overwrite generated files if they already exist")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.output_dir / args.name
    script_path = root / "scripts" / f"{args.name}.py"
    readme_path = root / "README.md"

    write_new(script_path, script_for_kind(args.kind, args.name), force=args.force)
    write_new(readme_path, readme(args.name, args.kind), force=args.force)

    if args.javascript:
        write_new(root / "javascript" / f"{args.name}.js", javascript(args.name), force=args.force)

    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
