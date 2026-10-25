import argparse
from pathlib import Path

import yaml

from pipelines.digital_data_etl import digital_data_etl

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"


def load_config(filename: str) -> dict:
    config_path = CONFIGS_DIR / filename

    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    return config.get("parameters", {})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the digital data ETL pipeline.")

    parser.add_argument(
        "--config-filename",
        type=str,
        default="digital_data_etl_andrej_karpathy.yaml",
        help="YAML configuration filename in the configs directory.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable pipeline caching.",
    )

    args = parser.parse_args()
    parameters = load_config(args.config_filename)

    digital_data_etl.with_options(
        enable_cache=not args.no_cache,
    )(**parameters)


if __name__ == "__main__":
    main()
