from src.cli import main as cli_main


def main() -> None:
    raise SystemExit(main_cli())


def main_cli() -> int:
    return cli_main(["run"])


if __name__ == "__main__":
    main()
