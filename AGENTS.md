# Repository Guidelines

## Project Structure & Module Organization
This repository is a packaged Python sales-data pipeline used as both a working application and a teaching project.

- `src/` contains the application code: `ingestion/`, `transformation/`, `analytic/`, `reporting/`, plus `pipeline.py`, `cli.py`, `runtime.py`, and `settings.py`.
- `run_pipeline.py` is a simple wrapper around the packaged CLI.
- `config/` contains environment-specific TOML runtime settings (`dev`, `recette`, `prod`).
- `scripts/` contains PowerShell install/run/check/build helpers for Windows-style operations.
- `docs/` contains Ops-facing documentation (`runbook_ops.md`, `test_installation_venv.md`).
- `raw_sales_data/` holds monthly Excel inputs; `outputs/` stores generated CSVs, logs, and `outputs/reports/rapport_ventes_latest.xlsx`.

Keep business logic in `src/` and treat `scripts/` and `docs/` as operational wrappers.

## Build, Test, and Development Commands
Run commands from the repository root.

- `python3 -m pip install .`: install the packaged application locally.
- `sales-pipeline check --config config/prod.toml --runtime-root .`: validate runtime layout and input availability.
- `sales-pipeline run --config config/prod.toml --runtime-root .`: execute the full pipeline and refresh outputs.
- `python3 -m py_compile run_pipeline.py src/__main__.py src/cli.py src/runtime.py src/settings.py src/pipeline.py src/reporting/excel_report.py`: quick syntax and import smoke check.
- `python3 -m pip wheel . --no-deps -w /tmp/wheels`: build a distributable wheel.

## Coding Style & Naming Conventions
Use 4-space indentation, type hints, short docstrings, and `pathlib.Path` for filesystem work. Follow the existing Python naming style:

- functions and modules: `snake_case`
- classes and dataclasses: `PascalCase`
- constants: `UPPER_SNAKE_CASE`

Prefer small helper functions and explicit adapters over large scripts with mixed responsibilities.

## Testing Guidelines
There is no committed `tests/` directory yet. Add focused tests under `tests/` mirroring `src/` paths, for example `tests/analytic/test_kpis.py`.

Before opening a PR, verify:

- `sales-pipeline check --config config/prod.toml --runtime-root .`
- `sales-pipeline run --config config/prod.toml --runtime-root .`
- `python3 -m pip wheel . --no-deps -w /tmp/wheels`

## Commit & Pull Request Guidelines
Recent commits use short, descriptive subjects in either French or English, such as `industrialisation`, `redaction du readme`, and `Implemented the new reporting model`. Keep commits narrow in scope and written as concise summaries of the change.

Pull requests should include a short description, affected layers (`src/`, `config/`, `scripts/`, `docs/`), validation commands run, and screenshots when `src/reporting/streamlit_app.py` changes. Do not commit private raw sales data unless it has been explicitly sanitized for sharing.
