#!/usr/bin/env python3
"""Download the approved workflow font assets into a target directory.

This is a self-contained, stdlib-only helper for provisioning the approved font
set used by workflow visualisations. It downloads only immutable, pinned URLs
and verifies each file against the recorded SHA-256 checksum before the file is
made visible at the destination path.

Example:
    python scripts/provision_workflow_fonts.py
    python scripts/provision_workflow_fonts.py --target-dir ./workflow-font-assets
    python scripts/provision_workflow_fonts.py --only geist_mono --only inter
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import time
import urllib.request
from pathlib import Path

MAX_FONT_FILE_BYTES = 20 * 1024 * 1024
DOWNLOAD_CHUNK_BYTES = 64 * 1024
DOWNLOAD_MAX_ATTEMPTS = 3
DOWNLOAD_BACKOFF_SECONDS = 1.0
DEFAULT_TARGET_DIR = Path("workflow-font-assets")

FONT_ENTRIES = (
    {
        "identifier": "geist_mono",
        "display_name": "Geist Mono",
        "file_name": "GeistMono-Regular.ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "1.7.2",
        "source_url": "https://raw.githubusercontent.com/vercel/geist-font/v1.7.2/fonts/GeistMono/ttf/GeistMono-Regular.ttf",
        "sha256": "5a0de4b3d54ab272f76a1d8c84b7fb24c67bbec6591d5300e61c7bc10094b6c8",
        "license_url": "https://raw.githubusercontent.com/vercel/geist-font/v1.7.2/OFL.txt",
        "license_sha256": "c683bfbcc7e087f5d37a54ef628f10387c451a83ddc459b151403a164ac46c90",
    },
    {
        "identifier": "geist",
        "display_name": "Geist",
        "file_name": "Geist-Regular.ttf",
        "monospaced": False,
        "license_name": "OFL-1.1",
        "version": "1.7.2",
        "source_url": "https://raw.githubusercontent.com/vercel/geist-font/v1.7.2/fonts/Geist/ttf/Geist-Regular.ttf",
        "sha256": "85a1c6b18a6b0a06dfe9fd4f6d6a5d4979f74ec861eaef4bc7868b5492b8a117",
        "license_url": "https://raw.githubusercontent.com/vercel/geist-font/v1.7.2/OFL.txt",
        "license_sha256": "c683bfbcc7e087f5d37a54ef628f10387c451a83ddc459b151403a164ac46c90",
    },
    {
        "identifier": "jetbrains_mono",
        "display_name": "JetBrains Mono",
        "file_name": "JetBrainsMono[wght].ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
        "sha256": "48715a42ec242c21e9f02692891e147d022299a52e48d5e413e1a942193ffeda",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/jetbrainsmono/OFL.txt",
        "license_sha256": "b2fe5e8987594e9ffd1d2ca52a2f5d73eb8335243893c5d6254b5ad69269591d",
    },
    {
        "identifier": "ibm_plex_mono",
        "display_name": "IBM Plex Mono",
        "file_name": "IBMPlexMono-Regular.ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/ibmplexmono/IBMPlexMono-Regular.ttf",
        "sha256": "6a3412f058c7d8dfd9170c41e85ade48e5156ecb89356110ca57a0a27734af46",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/ibmplexmono/OFL.txt",
        "license_sha256": "7e6b2818edbd8f6a01ae80641cc8f16a51080d08fb4e532be3a0b6f74adb07da",
    },
    {
        "identifier": "source_code_pro",
        "display_name": "Source Code Pro",
        "file_name": "SourceCodePro[wght].ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/sourcecodepro/SourceCodePro%5Bwght%5D.ttf",
        "sha256": "b400fc584e10aff25d0e775ce181b4fc1c5ea1b5dc37b81aeb2084375b945790",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/sourcecodepro/OFL.txt",
        "license_sha256": "cb30d3086a8b3ce0b9e3690bf48d6620402b61160bc658076f95180ccd9e9dae",
    },
    {
        "identifier": "space_mono",
        "display_name": "Space Mono",
        "file_name": "SpaceMono-Regular.ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/spacemono/SpaceMono-Regular.ttf",
        "sha256": "95837e182baeeada83368f7748db28357f0a1b75c6b84ff7065b5edf933c8e18",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/spacemono/OFL.txt",
        "license_sha256": "8e4ee42b2553e1e01504e61cb0d46d148cd8c9e5eacaa3622a7df2d4f2955b9f",
    },
    {
        "identifier": "roboto_mono",
        "display_name": "Roboto Mono",
        "file_name": "RobotoMono[wght].ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/robotomono/RobotoMono%5Bwght%5D.ttf",
        "sha256": "66a80e79d17e4c7cabd162e2916578a4cc08fd19eef6e2a643305eae9c567b2b",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/robotomono/OFL.txt",
        "license_sha256": "50ab8dd54680d3473f649c9db86fece88434d097c7834475c1c72d2f8c429215",
    },
    {
        "identifier": "inter",
        "display_name": "Inter",
        "file_name": "Inter[opsz,wght].ttf",
        "monospaced": False,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
        "sha256": "29160a80ff49ddcab2c97711247e08b1fab27a484a329ce8b813d820dc559031",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/inter/OFL.txt",
        "license_sha256": "5b9321a4298cfeb6b34354164a1c3afc3db114569984c502b9b35d988fd58c57",
    },
    {
        "identifier": "open_sans",
        "display_name": "Open Sans",
        "file_name": "OpenSans[wdth,wght].ttf",
        "monospaced": False,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/opensans/OpenSans%5Bwdth%2Cwght%5D.ttf",
        "sha256": "36643644f318a812aab2d2ed3bb98f8cf0872527f835fe9398d95fe6b9adb878",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/opensans/OFL.txt",
        "license_sha256": "fbbbcfef55318de350562559b671360de6d597112ecc5c73881b05092db89602",
    },
    {
        "identifier": "noto_sans",
        "display_name": "Noto Sans",
        "file_name": "NotoSans-Regular.ttf",
        "monospaced": False,
        "license_name": "OFL-1.1",
        "version": "notofonts.github.io@eaa1a5cf",
        "source_url": "https://raw.githubusercontent.com/notofonts/notofonts.github.io/eaa1a5cf8cb83ea73941197e492d659e51bb11dd/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
        "sha256": "478c558ea716033cd60c03438f628dfa75694dcf6b5f6d505a2f05fd2b4f3823",
        "license_url": "https://raw.githubusercontent.com/notofonts/notofonts.github.io/eaa1a5cf8cb83ea73941197e492d659e51bb11dd/fonts/LICENSE",
        "license_sha256": "f2095b08bed08b23a6fe26112fcd679a2bee3f002eef077eb05d215ed1051bd8",
    },
    {
        "identifier": "fira_code",
        "display_name": "Fira Code",
        "file_name": "FiraCode[wght].ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/firacode/FiraCode%5Bwght%5D.ttf",
        "sha256": "9335b082b3c7850d98a64b584f3417f65355f3471278bb5eeb8c6c0e8657aeeb",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/firacode/OFL.txt",
        "license_sha256": "926041dac670e6922505e35ac1661a4e8d20f1ffeabbbcb5edb5544370702369",
    },
    {
        "identifier": "inconsolata",
        "display_name": "Inconsolata",
        "file_name": "Inconsolata[wdth,wght].ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/inconsolata/Inconsolata%5Bwdth,wght%5D.ttf",
        "sha256": "23ded25b447074d00659392bf9b1123d89df55cb07b0ad9bfef3366d199b5fcb",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/inconsolata/OFL.txt",
        "license_sha256": "29bd0cfd0fb2a45f9b057c834a057724bae1f63b525a8ac83d3e7525706d9f80",
    },
    {
        "identifier": "anonymous_pro",
        "display_name": "Anonymous Pro",
        "file_name": "AnonymousPro-Regular.ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/anonymouspro/AnonymousPro-Regular.ttf",
        "sha256": "46d8b9a5f4b38fc9d30f3cdd676d4c6f78a9bef949bb1a8304216cc731eb87f8",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/anonymouspro/OFL.txt",
        "license_sha256": "8594350034ab1cb85a1946ef8852e69290255816c311450a66fed6eeda9d6292",
    },
    {
        "identifier": "pt_mono",
        "display_name": "PT Mono",
        "file_name": "PTM55FT.ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/ptmono/PTM55FT.ttf",
        "sha256": "cbe732b3b8fd211fd986ebdfc9b870ddeca4faab0bb5425fc509b37f9b4ac804",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/ptmono/OFL.txt",
        "license_sha256": "511125dc85198375795fdbc109d088654d3b7f9dbd3ccb7bf93d844aef0b153c",
    },
    {
        "identifier": "courier_prime",
        "display_name": "Courier Prime",
        "file_name": "CourierPrime-Regular.ttf",
        "monospaced": True,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/courierprime/CourierPrime-Regular.ttf",
        "sha256": "72f793376f8e2841656bf21d77a5de010f2929bd6956a22ee848ad0c7eb978af",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/courierprime/OFL.txt",
        "license_sha256": "9a755af092b494944c99f471be6fddd19b006a448fefdc4717e4ee0aa09a97b0",
    },
    {
        "identifier": "roboto",
        "display_name": "Roboto",
        "file_name": "Roboto[wdth,wght].ttf",
        "monospaced": False,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf",
        "sha256": "d7598e12c5dbef095ff8272cfc55da0250bd07fbdecbac8a530b9b277872a134",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/roboto/OFL.txt",
        "license_sha256": "061402327a96aadb0bfb694a960ed289ecd38d383e396243831ab81feb109c41",
    },
    {
        "identifier": "lato",
        "display_name": "Lato",
        "file_name": "Lato-Regular.ttf",
        "monospaced": False,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/lato/Lato-Regular.ttf",
        "sha256": "d636e4683231f931eda222d588e944d082bfd3bdba02f928bee461c0f185b251",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/lato/OFL.txt",
        "license_sha256": "74ba064d03f1f1c4a952da936c3eb71866c34404916734de3cae73b34357e59e",
    },
    {
        "identifier": "montserrat",
        "display_name": "Montserrat",
        "file_name": "Montserrat[wght].ttf",
        "monospaced": False,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
        "sha256": "0f7b311b2f3279e4eef9b2f968bcdbab6e28f4daeb1f049f4f278a902bcd82f7",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/montserrat/OFL.txt",
        "license_sha256": "8b7141c03fa4f8d44e6345d5d4931709290f0f67875e452e95ac1fd3a027802e",
    },
    {
        "identifier": "work_sans",
        "display_name": "Work Sans",
        "file_name": "WorkSans[wght].ttf",
        "monospaced": False,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/worksans/WorkSans%5Bwght%5D.ttf",
        "sha256": "f50f61f2ba738e239442d40bf1069adb195c224b6a5a73a581fc2f3ed62a9f63",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/worksans/OFL.txt",
        "license_sha256": "749aca05078664ce682dce1b1b10096ac397cb088c1a6df4e1bb56f0092a9272",
    },
    {
        "identifier": "nunito_sans",
        "display_name": "Nunito Sans",
        "file_name": "NunitoSans[YTLC,opsz,wdth,wght].ttf",
        "monospaced": False,
        "license_name": "OFL-1.1",
        "version": "google/fonts@7ff85c87",
        "source_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/nunitosans/NunitoSans%5BYTLC%2Copsz%2Cwdth%2Cwght%5D.ttf",
        "sha256": "f934d7142fb4784bf828da485b7dcbd90c0c80d514e9d49a5da0ed3a1ae2491d",
        "license_url": "https://raw.githubusercontent.com/google/fonts/7ff85c87f93ea6cca5f41c69f2e4edcb90240f26/ofl/nunitosans/OFL.txt",
        "license_sha256": "efbb0c9e864cef973982d9a17567e6be5c3d1759695574586f3f18c7ecca064b",
    },
)

FONTS_REGISTRY = {entry["identifier"]: entry for entry in FONT_ENTRIES}


class FontDownloadError(RuntimeError):
    """Raised when an approved font asset cannot be downloaded and verified."""


def compute_file_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(DOWNLOAD_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file_with_checksum(
    url: str,
    *,
    destination: Path,
    expected_sha256: str,
    timeout_seconds: int = 60,
    max_bytes: int = MAX_FONT_FILE_BYTES,
    max_attempts: int = DOWNLOAD_MAX_ATTEMPTS,
    backoff_seconds: float = DOWNLOAD_BACKOFF_SECONDS,
) -> Path:
    if not url.lower().startswith("https://"):
        raise FontDownloadError(f"Refusing to download font asset over non-HTTPS URL: {url}")

    for attempt in range(1, max_attempts + 1):
        try:
            return _download_once(
                url=url,
                destination=destination,
                expected_sha256=expected_sha256,
                timeout_seconds=timeout_seconds,
                max_bytes=max_bytes,
            )
        except FontDownloadError:
            raise
        except Exception as error:
            if attempt == max_attempts:
                raise FontDownloadError(
                    f"Could not download font asset from {url} after {max_attempts} attempts: {error}"
                ) from error
            time.sleep(backoff_seconds * 2 ** (attempt - 1))


def _download_once(
    url: str,
    *,
    destination: Path,
    expected_sha256: str,
    timeout_seconds: int,
    max_bytes: int,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial_path = destination.with_name(f"{destination.name}.part")
    digest = hashlib.sha256()
    downloaded_bytes = 0

    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            with partial_path.open("wb") as partial_file:
                while True:
                    chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                    if not chunk:
                        break
                    downloaded_bytes += len(chunk)
                    if downloaded_bytes > max_bytes:
                        raise FontDownloadError(
                            f"Font asset from {url} exceeds the maximum allowed size of {max_bytes} bytes."
                        )
                    digest.update(chunk)
                    partial_file.write(chunk)
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise

    actual_sha256 = digest.hexdigest()
    if actual_sha256 != expected_sha256:
        partial_path.unlink(missing_ok=True)
        raise FontDownloadError(
            f"Checksum mismatch for font asset downloaded from {url}: expected sha256={expected_sha256}, got sha256={actual_sha256}."
        )

    shutil.move(str(partial_path), str(destination))
    return destination


def download_fonts(target_dir: Path, *, only: list[str]) -> int:
    selected_identifiers = only or sorted(FONTS_REGISTRY)
    unknown_identifiers = [identifier for identifier in selected_identifiers if identifier not in FONTS_REGISTRY]
    if unknown_identifiers:
        print(f"ERROR: unknown font identifiers: {', '.join(unknown_identifiers)}")
        return 1

    failures: list[str] = []
    for identifier in selected_identifiers:
        metadata = FONTS_REGISTRY[identifier]
        files_to_provision = [
            (
                metadata["source_url"],
                target_dir / identifier / metadata["file_name"],
                metadata["sha256"],
            ),
            (
                metadata["license_url"],
                target_dir / identifier / "OFL.txt",
                metadata["license_sha256"],
            ),
        ]

        for source_url, destination, expected_sha256 in files_to_provision:
            if destination.is_file() and compute_file_sha256(destination) == expected_sha256:
                print(f"[skip] {identifier}: {destination.name} already present and verified")
                continue
            try:
                download_file_with_checksum(
                    source_url,
                    destination=destination,
                    expected_sha256=expected_sha256,
                )
                print(f"[ok]   {identifier}: downloaded and verified ({destination})")
            except Exception as error:
                failures.append(identifier)
                print(f"[FAIL] {identifier}: {error}")

    if failures:
        print(f"ERROR: failed to provision fonts: {', '.join(sorted(set(failures)))}")
        return 1

    print(f"All requested fonts available in {target_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download approved workflow font assets (checksum-verified).",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=DEFAULT_TARGET_DIR,
        help=f"Directory to place font assets in (default: {DEFAULT_TARGET_DIR})",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="FONT_IDENTIFIER",
        help="Limit download to the given font identifier (repeatable).",
    )
    arguments = parser.parse_args()
    return download_fonts(arguments.target_dir, only=arguments.only)


if __name__ == "__main__":
    raise SystemExit(main())
