"""Update the tracked dashboard release manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write published_app/dashboard_release.json for a new dashboard release.",
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--channel", default="stable")
    parser.add_argument("--windows-package-url", default="")
    parser.add_argument("--linux-package-url", default="")
    parser.add_argument("--release-notes", default="")
    parser.add_argument(
        "--install-instructions-url",
        default=(
            "https://github.com/JosueAfouda/automate-excel-with-python/blob/"
            "executable/streamlit/apprendre_python.md"
        ),
    )
    parser.add_argument(
        "--source-archive-url",
        default=(
            "https://github.com/JosueAfouda/automate-excel-with-python/archive/"
            "refs/heads/executable/streamlit.zip"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("published_app/dashboard_release.json"),
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    payload = {
        "application": "SalesDashboard",
        "channel": args.channel,
        "version": args.version,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "windows_package_url": args.windows_package_url,
        "linux_package_url": args.linux_package_url,
        "release_notes": args.release_notes,
        "install_instructions_url": args.install_instructions_url,
        "source_archive_url": args.source_archive_url,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
