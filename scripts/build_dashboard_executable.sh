#!/usr/bin/env bash
set -euo pipefail

PYTHON_EXECUTABLE="${PYTHON_EXECUTABLE:-python3}"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DASHBOARD_CONFIG="${DASHBOARD_CONFIG:-config/dashboard_github.toml}"

cd "$PROJECT_ROOT"

"$PYTHON_EXECUTABLE" -m pip install --upgrade pip
"$PYTHON_EXECUTABLE" -m pip install '.[dashboard-build]'

VERSION="$("$PYTHON_EXECUTABLE" -c 'from src.reporting.dashboard_version import DASHBOARD_VERSION; print(DASHBOARD_VERSION)')"

"$PYTHON_EXECUTABLE" -m PyInstaller --noconfirm --clean packaging/dashboard_launcher.spec

BUNDLE_DIR="$PROJECT_ROOT/dist/SalesDashboard"
cp "$DASHBOARD_CONFIG" "$BUNDLE_DIR/dashboard_config.toml"
cp "$PROJECT_ROOT/scripts/update_dashboard_runtime.ps1" "$BUNDLE_DIR/update_dashboard_runtime.ps1"

cat > "$BUNDLE_DIR/dashboard_version.json" <<EOF
{
  "application": "SalesDashboard",
  "version": "$VERSION",
  "channel": "stable",
  "built_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "config_file": "dashboard_config.toml"
}
EOF

ZIP_PATH="$PROJECT_ROOT/dist/SalesDashboard-linux-$VERSION.zip"
rm -f "$ZIP_PATH"
(cd "$BUNDLE_DIR" && zip -r "$ZIP_PATH" .)

echo "BUNDLE_DIR=$BUNDLE_DIR"
echo "ZIP_PATH=$ZIP_PATH"
