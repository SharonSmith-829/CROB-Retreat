#!/usr/bin/env python3

import argparse
from pathlib import Path

import folium
import pandas as pd
from folium.plugins import HeatMap


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a heat map from outreach event CSV data."
    )
    parser.add_argument("--input", required=True, help="Path to outreach events CSV.")
    parser.add_argument(
        "--output", default="outreach_heatmap.html", help="Output HTML map file."
    )
    parser.add_argument(
        "--radius", type=int, default=25, help="Heat point radius (default: 25)."
    )
    return parser.parse_args()


def build_heat_data(dataframe: pd.DataFrame) -> list[list[float]]:
    if "attendance" in dataframe.columns:
        return dataframe[["latitude", "longitude", "attendance"]].values.tolist()
    return dataframe[["latitude", "longitude"]].values.tolist()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        dataframe = pd.read_csv(input_path)
    except Exception as error:
        raise ValueError(f"Unable to read input CSV: {input_path}") from error
    required = {"latitude", "longitude"}
    missing = required - set(dataframe.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"Missing required column(s): {missing_columns}")

    dataframe["latitude"] = pd.to_numeric(dataframe["latitude"], errors="coerce")
    dataframe["longitude"] = pd.to_numeric(dataframe["longitude"], errors="coerce")
    invalid_coordinates = dataframe[dataframe["latitude"].isna() | dataframe["longitude"].isna()]
    if not invalid_coordinates.empty:
        invalid_rows = ", ".join(str(index + 2) for index in invalid_coordinates.index[:5])
        raise ValueError(
            f"Found invalid latitude/longitude value(s) in CSV row(s): {invalid_rows}"
        )

    if "attendance" in dataframe.columns:
        dataframe["attendance"] = pd.to_numeric(dataframe["attendance"], errors="coerce").fillna(1)

    center_lat = dataframe["latitude"].mean()
    center_lon = dataframe["longitude"].mean()

    outreach_map = folium.Map(location=[center_lat, center_lon], zoom_start=5)
    HeatMap(build_heat_data(dataframe), radius=args.radius).add_to(outreach_map)
    outreach_map.save(output_path)


if __name__ == "__main__":
    main()
