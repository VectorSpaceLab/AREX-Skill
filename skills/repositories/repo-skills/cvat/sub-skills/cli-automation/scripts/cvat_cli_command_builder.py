#!/usr/bin/env python3
"""Build credential-safe cvat-cli command lines.

The script prints a shell-quoted cvat-cli command and never contacts a CVAT server.
It intentionally refuses raw token/password values; use CVAT_ACCESS_TOKEN, PASS, or
saved cvat-cli profiles outside the generated command.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from collections.abc import Iterable


def q(parts: Iterable[object]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if part is not None)


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", help="saved cvat-cli profile name; mutually exclusive with server/auth flags")
    parser.add_argument("--server-host", help="explicit CVAT server URL/host")
    parser.add_argument("--server-port", type=int, help="server port to append when the server URL has no port")
    parser.add_argument("--auth-user", help="username for password auth; emits '--auth USER' only, never a password")
    parser.add_argument("--require-token-env", action="store_true", help="document that CVAT_ACCESS_TOKEN must be set out of band")
    parser.add_argument("--org", "--organization", dest="organization", help="organization slug; pass an empty string only for personal workspace")
    parser.add_argument("--insecure", action="store_true", help="include --insecure for explicitly trusted test/self-hosted servers")
    parser.add_argument("--debug", action="store_true", help="include --debug; redact logs before sharing")
    parser.add_argument("--prefix", default="cvat-cli", help="command executable prefix, default: cvat-cli")


def global_parts(args: argparse.Namespace) -> list[str]:
    conflicting = [
        name
        for name in ("server_host", "server_port", "auth_user")
        if getattr(args, name, None) not in (None, "")
    ]
    if args.profile and conflicting:
        raise SystemExit("error: --profile is mutually exclusive with --server-host, --server-port, and --auth-user")
    if args.profile and args.require_token_env:
        raise SystemExit("error: --profile already supplies credentials; do not combine it with --require-token-env")

    parts: list[str] = [args.prefix]
    if args.insecure:
        parts.append("--insecure")
    if args.profile:
        parts += ["--profile", args.profile]
    if args.server_host:
        parts += ["--server-host", args.server_host]
    if args.server_port is not None:
        parts += ["--server-port", str(args.server_port)]
    if args.auth_user:
        if ":" in args.auth_user:
            raise SystemExit("error: --auth-user must be a username only; put the password in PASS or use a profile/PAT")
        parts += ["--auth", args.auth_user]
    if args.organization is not None:
        parts += ["--org", args.organization]
    if args.debug:
        parts.append("--debug")
    return parts


def append_option(parts: list[str], flag: str, value: object | None) -> None:
    if value is not None and value != "":
        if flag:
            parts.extend([flag, str(value)])
        else:
            parts.append(str(value))


def append_bool(parts: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        parts.append(flag)


def append_repeated(parts: list[str], flag: str, values: list[str] | None) -> None:
    for value in values or []:
        parts.extend([flag, value])


def maybe_note(args: argparse.Namespace, command: str) -> str:
    notes = []
    if getattr(args, "require_token_env", False):
        notes.append("# Requires CVAT_ACCESS_TOKEN to be set securely outside this command.")
    if getattr(args, "auth_user", None):
        notes.append("# If non-interactive password auth is needed, set PASS securely outside this command.")
    if notes:
        return "\n".join(notes + [command])
    return command


def cmd_task_create(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["task", "create", args.name]
    append_option(parts, "--annotation_path", args.annotation_path)
    append_option(parts, "--annotation_format", args.annotation_format)
    append_option(parts, "--bug_tracker", args.bug_tracker)
    append_option(parts, "--chunk_size", args.chunk_size)
    append_option(parts, "--completion_verification_period", args.completion_verification_period)
    append_bool(parts, "--copy_data", args.copy_data)
    append_option(parts, "--frame_step", args.frame_step)
    append_option(parts, "--image_quality", args.image_quality)
    append_option(parts, "--labels", args.labels)
    append_option(parts, "--project_id", args.project_id)
    append_option(parts, "--overlap", args.overlap)
    append_option(parts, "--segment_size", args.segment_size)
    append_option(parts, "--sorting-method", args.sorting_method)
    append_option(parts, "--start_frame", args.start_frame)
    append_option(parts, "--stop_frame", args.stop_frame)
    append_bool(parts, "--use_cache", args.use_cache)
    append_bool(parts, "--use_zip_chunks", args.use_zip_chunks)
    append_option(parts, "--cloud_storage_id", args.cloud_storage_id)
    append_option(parts, "--filename_pattern", args.filename_pattern)
    parts += [args.resource_type, *args.resources]
    return parts


def cmd_task_ls(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["task", "ls"]
    append_bool(parts, "--json", args.json)
    return parts


def cmd_delete(args: argparse.Namespace, resource: str) -> list[str]:
    return global_parts(args) + [resource, "delete", *map(str, args.ids)]


def cmd_frames(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["task", "frames"]
    append_option(parts, "--outdir", args.outdir)
    append_option(parts, "--quality", args.quality)
    parts += [str(args.task_id), *map(str, args.frame_ids)]
    return parts


def cmd_export(args: argparse.Namespace, resource: str) -> list[str]:
    parts = global_parts(args) + [resource, "export-dataset"]
    append_option(parts, "--format", args.format)
    append_option(parts, "--completion_verification_period", args.completion_verification_period)
    append_option(parts, "--with-images", args.with_images)
    parts.append(str(args.resource_id))
    append_option(parts, "", args.filename)
    return parts


def cmd_import(args: argparse.Namespace, resource: str) -> list[str]:
    parts = global_parts(args) + [resource, "import-dataset"]
    append_option(parts, "--format", args.format)
    parts += [str(args.resource_id), args.filename]
    return parts


def cmd_backup(args: argparse.Namespace, resource: str) -> list[str]:
    parts = global_parts(args) + [resource, "backup"]
    append_option(parts, "--completion_verification_period", args.completion_verification_period)
    parts.append(str(args.resource_id))
    append_option(parts, "", args.filename)
    return parts


def cmd_from_backup(args: argparse.Namespace, resource: str) -> list[str]:
    parts = global_parts(args) + [resource, "create-from-backup"]
    append_option(parts, "--completion_verification_period", args.completion_verification_period)
    parts.append(args.filename)
    return parts


def add_function_flags(parts: list[str], args: argparse.Namespace) -> None:
    if args.function_module and args.function_file:
        raise SystemExit("error: choose only one of --function-module or --function-file")
    if not args.function_module and not args.function_file:
        raise SystemExit("error: one of --function-module or --function-file is required")
    append_option(parts, "--function-module", args.function_module)
    append_option(parts, "--function-file", args.function_file)
    append_repeated(parts, "-p", args.function_parameter)


def cmd_auto_annotate(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["task", "auto-annotate", str(args.task_id)]
    add_function_flags(parts, args)
    append_bool(parts, "--clear-existing", args.clear_existing)
    append_bool(parts, "--allow-unmatched-labels", args.allow_unmatched_labels)
    append_option(parts, "--conf-threshold", args.conf_threshold)
    append_bool(parts, "--conv-mask-to-poly", args.conv_mask_to_poly)
    return parts


def cmd_project_create(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["project", "create", args.name]
    append_option(parts, "--bug_tracker", args.bug_tracker)
    append_option(parts, "--labels", args.labels)
    append_option(parts, "--dataset_path", args.dataset_path)
    append_option(parts, "--dataset_format", args.dataset_format)
    append_option(parts, "--completion_verification_period", args.completion_verification_period)
    return parts


def cmd_project_ls(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["project", "ls"]
    append_bool(parts, "--json", args.json)
    return parts


def cmd_profile_create(args: argparse.Namespace) -> list[str]:
    # Profile creation may use --server-host/--server-port but never raw passwords.
    parts = global_parts(args) + ["profile", "create"]
    append_option(parts, "--name", args.name)
    append_bool(parts, "--set-default", args.set_default)
    append_bool(parts, "--force", args.force)
    append_option(parts, "--file", args.file)
    if args.prompt_token:
        pass
    return parts


def cmd_profile_list(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["profile", "list"]
    append_bool(parts, "--names-only", args.names_only)
    return parts


def cmd_profile_default(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["profile", "default"]
    append_bool(parts, "--unset", args.unset)
    append_option(parts, "", args.name)
    return parts


def cmd_config_default_server(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["config", "default-server"]
    append_bool(parts, "--unset", args.unset)
    append_option(parts, "", args.server)
    return parts


def cmd_function_create_native(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["function", "create-native", args.name]
    append_option(parts, "--visibility", args.visibility)
    add_function_flags(parts, args)
    return parts


def cmd_function_run_agent(args: argparse.Namespace) -> list[str]:
    parts = global_parts(args) + ["function", "run-agent", str(args.function_id)]
    add_function_flags(parts, args)
    append_bool(parts, "--burst", args.burst)
    return parts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a quoted cvat-cli command without executing it. No raw passwords or token values are accepted.",
    )
    add_common(parser)
    sub = parser.add_subparsers(dest="builder_action", required=True)

    p = sub.add_parser("task-create", help="build cvat-cli task create")
    p.add_argument("name")
    p.add_argument("resource_type", choices=("local", "share", "remote"))
    p.add_argument("resources", nargs="+")
    p.add_argument("--annotation-path", dest="annotation_path")
    p.add_argument("--annotation-format", dest="annotation_format")
    p.add_argument("--bug-tracker", dest="bug_tracker")
    p.add_argument("--chunk-size", dest="chunk_size", type=int)
    p.add_argument("--completion-verification-period", dest="completion_verification_period", type=float)
    p.add_argument("--copy-data", dest="copy_data", action="store_true")
    p.add_argument("--frame-step", dest="frame_step", type=int)
    p.add_argument("--image-quality", dest="image_quality", type=int)
    p.add_argument("--labels")
    p.add_argument("--project-id", dest="project_id", type=int)
    p.add_argument("--overlap", type=int)
    p.add_argument("--segment-size", dest="segment_size", type=int)
    p.add_argument("--sorting-method", choices=("lexicographical", "natural", "predefined", "random"))
    p.add_argument("--start-frame", dest="start_frame", type=int)
    p.add_argument("--stop-frame", dest="stop_frame", type=int)
    p.add_argument("--use-cache", dest="use_cache", action="store_true")
    p.add_argument("--use-zip-chunks", dest="use_zip_chunks", action="store_true")
    p.add_argument("--cloud-storage-id", dest="cloud_storage_id", type=int)
    p.add_argument("--filename-pattern", dest="filename_pattern")
    p.set_defaults(func=cmd_task_create)

    p = sub.add_parser("task-ls", help="build cvat-cli task ls")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_task_ls)

    p = sub.add_parser("task-delete", help="build cvat-cli task delete")
    p.add_argument("ids", type=int, nargs="+")
    p.set_defaults(func=lambda a: cmd_delete(a, "task"))

    p = sub.add_parser("task-frames", help="build cvat-cli task frames")
    p.add_argument("task_id", type=int)
    p.add_argument("frame_ids", type=int, nargs="+")
    p.add_argument("--outdir")
    p.add_argument("--quality", choices=("original", "compressed"))
    p.set_defaults(func=cmd_frames)

    for action, resource in [
        ("task-export-dataset", "task"),
        ("project-export-dataset", "project"),
    ]:
        p = sub.add_parser(action, help=f"build cvat-cli {resource} export-dataset")
        p.add_argument("resource_id", type=int)
        p.add_argument("filename", nargs="?")
        p.add_argument("--format")
        p.add_argument("--completion-verification-period", dest="completion_verification_period", type=float)
        p.add_argument("--with-images", dest="with_images", choices=("yes", "no", "true", "false", "1", "0"))
        p.set_defaults(func=lambda a, resource=resource: cmd_export(a, resource))

    for action, resource in [
        ("task-import-dataset", "task"),
        ("project-import-dataset", "project"),
    ]:
        p = sub.add_parser(action, help=f"build cvat-cli {resource} import-dataset")
        p.add_argument("resource_id", type=int)
        p.add_argument("filename")
        p.add_argument("--format")
        p.set_defaults(func=lambda a, resource=resource: cmd_import(a, resource))

    for action, resource in [("task-backup", "task"), ("project-backup", "project")]:
        p = sub.add_parser(action, help=f"build cvat-cli {resource} backup")
        p.add_argument("resource_id", type=int)
        p.add_argument("filename", nargs="?")
        p.add_argument("--completion-verification-period", dest="completion_verification_period", type=float)
        p.set_defaults(func=lambda a, resource=resource: cmd_backup(a, resource))

    for action, resource in [
        ("task-create-from-backup", "task"),
        ("project-create-from-backup", "project"),
    ]:
        p = sub.add_parser(action, help=f"build cvat-cli {resource} create-from-backup")
        p.add_argument("filename")
        p.add_argument("--completion-verification-period", dest="completion_verification_period", type=float)
        p.set_defaults(func=lambda a, resource=resource: cmd_from_backup(a, resource))

    p = sub.add_parser("task-auto-annotate", help="build cvat-cli task auto-annotate")
    p.add_argument("task_id", type=int)
    add_function_args(p)
    p.add_argument("--clear-existing", action="store_true")
    p.add_argument("--allow-unmatched-labels", action="store_true")
    p.add_argument("--conf-threshold", type=float)
    p.add_argument("--conv-mask-to-poly", action="store_true")
    p.set_defaults(func=cmd_auto_annotate)

    p = sub.add_parser("project-create", help="build cvat-cli project create")
    p.add_argument("name")
    p.add_argument("--bug-tracker", dest="bug_tracker")
    p.add_argument("--labels")
    p.add_argument("--dataset-path", dest="dataset_path")
    p.add_argument("--dataset-format", dest="dataset_format")
    p.add_argument("--completion-verification-period", dest="completion_verification_period", type=float)
    p.set_defaults(func=cmd_project_create)

    p = sub.add_parser("project-ls", help="build cvat-cli project ls")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_project_ls)

    p = sub.add_parser("project-delete", help="build cvat-cli project delete")
    p.add_argument("ids", type=int, nargs="+")
    p.set_defaults(func=lambda a: cmd_delete(a, "project"))

    p = sub.add_parser("profile-create", help="build cvat-cli profile create; token is prompted or read from --file")
    p.add_argument("--name")
    p.add_argument("--set-default", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--file")
    p.add_argument("--prompt-token", action="store_true", help="document prompt-mode; no token value is accepted")
    p.set_defaults(func=cmd_profile_create)

    p = sub.add_parser("profile-list", help="build cvat-cli profile list")
    p.add_argument("--names-only", action="store_true")
    p.set_defaults(func=cmd_profile_list)

    p = sub.add_parser("profile-default", help="build cvat-cli profile default")
    p.add_argument("name", nargs="?")
    p.add_argument("--unset", action="store_true")
    p.set_defaults(func=cmd_profile_default)

    p = sub.add_parser("config-default-server", help="build cvat-cli config default-server")
    p.add_argument("server", nargs="?")
    p.add_argument("--unset", action="store_true")
    p.set_defaults(func=cmd_config_default_server)

    p = sub.add_parser("function-create-native", help="build cvat-cli function create-native")
    p.add_argument("name")
    p.add_argument("--visibility", choices=("private", "public"))
    add_function_args(p)
    p.set_defaults(func=cmd_function_create_native)

    p = sub.add_parser("function-run-agent", help="build cvat-cli function run-agent")
    p.add_argument("function_id", type=int)
    add_function_args(p)
    p.add_argument("--burst", action="store_true")
    p.set_defaults(func=cmd_function_run_agent)

    p = sub.add_parser("function-delete", help="build cvat-cli function delete")
    p.add_argument("ids", type=int, nargs="+")
    p.set_defaults(func=lambda a: cmd_delete(a, "function"))

    return parser


def add_function_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--function-module", help="qualified module name for an auto-annotation/native function")
    parser.add_argument("--function-file", help="Python file implementing an auto-annotation/native function")
    parser.add_argument(
        "--function-parameter",
        "-p",
        action="append",
        help="parameter as NAME=TYPE:VALUE; repeat for multiple parameters",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = q(args.func(args))
    print(maybe_note(args, command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
