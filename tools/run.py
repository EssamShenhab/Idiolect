import argparse
from pathlib import Path

import yaml

from pipelines.zenml_demo import zenml_demo

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"


def load_config(filename: str) -> dict:
    config_path = CONFIGS_DIR / filename

    with config_path.open("r") as file:
        config = yaml.safe_load(file)

    return config.get("parameters", {})


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--run-zenml-demo",
        action="store_true",
        help="Run the ZenML demo pipeline.",
    )

    parser.add_argument(
        "--config-filename",
        type=str,
        help="YAML configuration file from the configs directory.",
    )

    args = parser.parse_args()

    if args.run_zenml_demo:
        if not args.config_filename:
            raise ValueError(
                "--config-filename is required when running the ZenML demo."
            )

        parameters = load_config(args.config_filename)

        zenml_demo(**parameters)


if __name__ == "__main__":
    main()
