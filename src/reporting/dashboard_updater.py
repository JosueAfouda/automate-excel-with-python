"""Update metadata helpers for the distributed dashboard."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen, urlretrieve

from .dashboard_settings import DashboardSettings, load_dashboard_settings
from .dashboard_version import DASHBOARD_VERSION


@dataclass(frozen=True)
class DashboardReleaseManifest:
    """Latest published dashboard release metadata."""

    version: str
    channel: str
    published_at: str
    windows_package_url: str | None
    linux_package_url: str | None
    release_notes: str
    install_instructions_url: str | None
    source_archive_url: str | None


@dataclass(frozen=True)
class DashboardUpdateStatus:
    """Resolved update status for the local dashboard installation."""

    current_version: str
    latest_version: str | None
    update_available: bool
    download_url: str | None
    message: str | None = None


def _parse_version(value: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", value)
    if not numbers:
        return (0,)
    return tuple(int(number) for number in numbers)


def fetch_release_manifest(manifest_url: str) -> DashboardReleaseManifest:
    """Download and parse the dashboard release manifest."""
    with urlopen(manifest_url, timeout=10) as response:
        payload = json.load(response)

    return DashboardReleaseManifest(
        version=str(payload.get("version", "")).strip(),
        channel=str(payload.get("channel", "stable")).strip(),
        published_at=str(payload.get("published_at", "")).strip(),
        windows_package_url=str(payload.get("windows_package_url", "")).strip() or None,
        linux_package_url=str(payload.get("linux_package_url", "")).strip() or None,
        release_notes=str(payload.get("release_notes", "")).strip(),
        install_instructions_url=str(
            payload.get("install_instructions_url", "")
        ).strip()
        or None,
        source_archive_url=str(payload.get("source_archive_url", "")).strip() or None,
    )


def resolve_package_url(
    manifest: DashboardReleaseManifest,
    platform_name: str,
) -> str | None:
    """Return the platform-specific package URL."""
    platform_name = platform_name.lower()
    if platform_name.startswith("win"):
        return manifest.windows_package_url
    if platform_name.startswith("linux"):
        return manifest.linux_package_url
    return None


def get_dashboard_update_status(
    settings: DashboardSettings,
    *,
    platform_name: str | None = None,
) -> DashboardUpdateStatus:
    """Resolve whether a newer dashboard build is available."""
    if not settings.check_for_updates or not settings.release_manifest_url:
        return DashboardUpdateStatus(
            current_version=DASHBOARD_VERSION,
            latest_version=None,
            update_available=False,
            download_url=None,
            message="Verification de mise a jour desactivee.",
        )

    try:
        manifest = fetch_release_manifest(settings.release_manifest_url)
    except Exception as error:  # pragma: no cover - network-dependent
        return DashboardUpdateStatus(
            current_version=DASHBOARD_VERSION,
            latest_version=None,
            update_available=False,
            download_url=None,
            message=f"Impossible de verifier la version distante: {error}",
        )

    if not manifest.version:
        return DashboardUpdateStatus(
            current_version=DASHBOARD_VERSION,
            latest_version=None,
            update_available=False,
            download_url=None,
            message="Le manifeste de release ne contient pas de version exploitable.",
        )

    package_url = resolve_package_url(
        manifest,
        platform_name=platform_name or sys.platform,
    )
    update_available = _parse_version(manifest.version) > _parse_version(DASHBOARD_VERSION)

    if update_available and not package_url:
        message = (
            "Une version plus recente est signalee, mais aucun package n'est encore "
            "publie pour cette plateforme."
        )
    elif update_available:
        message = f"Nouvelle version disponible: {manifest.version}"
    else:
        message = "Le dashboard local est deja sur la derniere version connue."

    return DashboardUpdateStatus(
        current_version=DASHBOARD_VERSION,
        latest_version=manifest.version,
        update_available=update_available,
        download_url=package_url,
        message=message,
    )


def download_dashboard_package(download_url: str, destination_dir: Path) -> Path:
    """Download the published dashboard package for manual installation."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    package_name = download_url.rstrip("/").split("/")[-1]
    destination_path = destination_dir / package_name
    urlretrieve(download_url, destination_path)
    return destination_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales-dashboard-check-update",
        description="Check whether a newer distributed dashboard build exists.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional TOML config file describing dashboard sources and manifest URLs.",
    )
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=None,
        help="Optional runtime root used to resolve default config paths.",
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=None,
        help="If provided and a package URL exists, download the new build to this directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        settings = load_dashboard_settings(
            config_path=args.config,
            runtime_root=args.runtime_root,
        )
        status = get_dashboard_update_status(settings)
        print(f"CURRENT_VERSION={status.current_version}")
        print(f"LATEST_VERSION={status.latest_version or 'n/a'}")
        print(f"UPDATE_AVAILABLE={status.update_available}")
        print(f"DOWNLOAD_URL={status.download_url or 'n/a'}")
        print(f"MESSAGE={status.message or 'n/a'}")

        if args.download_dir and status.update_available and status.download_url:
            package_path = download_dashboard_package(status.download_url, args.download_dir)
            print(f"DOWNLOADED_PACKAGE={package_path}")
        return 0
    except Exception as error:  # pragma: no cover - defensive CLI guard
        print(f"ERROR_MESSAGE={error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
