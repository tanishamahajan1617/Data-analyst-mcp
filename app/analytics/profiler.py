from typing import Any

import pandas as pd

from app.datasets.loader import DatasetLoader


class DatasetProfiler:
    def __init__(self) -> None:
        self.loader = DatasetLoader()

    def profile(self, dataset_id: str) -> dict[str, Any]:
        df = self.loader.load(dataset_id)

        columns = []

        for column_name in df.columns:
            series = df[column_name]

            column_profile = {
                "name": str(column_name),
                "dtype": str(series.dtype),
                "missing_count": int(series.isna().sum()),
                "missing_percentage": round(
                    float(series.isna().mean() * 100),
                    2,
                ),
                "unique_count": int(series.nunique(dropna=True)),
            }

            columns.append(column_profile)

        numeric_df = df.select_dtypes(include="number")

        numeric_summary = {}

        if not numeric_df.empty:
            description = numeric_df.describe()

            for column_name in numeric_df.columns:
                numeric_summary[str(column_name)] = {
                    "mean": self._safe_number(
                        description.loc["mean", column_name]
                    ),
                    "std": self._safe_number(
                        description.loc["std", column_name]
                    ),
                    "min": self._safe_number(
                        description.loc["min", column_name]
                    ),
                    "max": self._safe_number(
                        description.loc["max", column_name]
                    ),
                }

        return {
            "dataset_id": dataset_id,
            "rows": int(len(df)),
            "columns_count": int(len(df.columns)),
            "duplicate_rows": int(df.duplicated().sum()),
            "columns": columns,
            "numeric_summary": numeric_summary,
        }

    @staticmethod
    def _safe_number(value: Any) -> float | None:
        if pd.isna(value):
            return None

        return round(float(value), 4)