from src.pipeline import run_pipeline


def main() -> None:
    outputs = run_pipeline()

    print("Pipeline executed successfully.")
    for output_name, output_path in outputs.items():
        print(f"- {output_name}: {output_path}")


if __name__ == "__main__":
    main()
