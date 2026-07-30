from typing import Any

import pandas as pd

from app.datasets.loader import DatasetLoader


class DataQualityAnalyzer:
    def __init__(self) -> None:
        self.loader = DatasetLoader()

    def analyze(self, dataset_id: str) -> dict[str, Any]:
        df = self.loader.load(dataset_id)

        issues: list[dict[str, Any]] = []

        self._detect_missing_values(df, issues)
        self._detect_duplicates(df, issues)
        self._detect_constant_columns(df, issues)
        self._detect_high_cardinality(df, issues)
        self._detect_outliers(df, issues)

        return {
            "dataset_id": dataset_id,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "quality_score": self._calculate_quality_score(df, issues),
            "issue_count": len(issues),
            "issues": issues,
        }

    def _detect_missing_values(
        self,
        df: pd.DataFrame,
        issues: list[dict[str, Any]],
    ) -> None:
        for column in df.columns:
            missing_count = int(df[column].isna().sum())

            if missing_count == 0:
                continue

            percentage = (
                missing_count / len(df) * 100
                if len(df) > 0
                else 0
            )

            severity = "low"

            if percentage >= 50:
                severity = "high"
            elif percentage >= 20:
                severity = "medium"

            issues.append(
                {
                    "type": "missing_values",
                    "column": str(column),
                    "severity": severity,
                    "count": missing_count,
                    "percentage": round(percentage, 2),
                    "message": (
                        f"Column '{column}' contains "
                        f"{missing_count} missing values."
                    ),
                }
            )

    def _detect_duplicates(
        self,
        df: pd.DataFrame,
        issues: list[dict[str, Any]],
    ) -> None:
        duplicate_count = int(df.duplicated().sum())

        if duplicate_count == 0:
            return

        percentage = (
            duplicate_count / len(df) * 100
            if len(df) > 0
            else 0
        )

        issues.append(
            {
                "type": "duplicate_rows",
                "column": None,
                "severity": "medium",
                "count": duplicate_count,
                "percentage": round(percentage, 2),
                "message": (
                    f"Dataset contains {duplicate_count} duplicate rows."
                ),
            }
        )

    def _detect_constant_columns(
        self,
        df: pd.DataFrame,
        issues: list[dict[str, Any]],
    ) -> None:
        for column in df.columns:
            unique_count = int(df[column].nunique(dropna=False))

            if unique_count <= 1:
                issues.append(
                    {
                        "type": "constant_column",
                        "column": str(column),
                        "severity": "low",
                        "count": None,
                        "percentage": None,
                        "message": (
                            f"Column '{column}' contains only one "
                            "unique value."
                        ),
                    }
                )

    def _detect_high_cardinality(
        self,
        df: pd.DataFrame,
        issues: list[dict[str, Any]],
    ) -> None:
        if len(df) == 0:
            return

        for column in df.select_dtypes(
            include=["object", "string", "category"]
        ).columns:
            unique_count = int(df[column].nunique(dropna=True))
            ratio = unique_count / len(df)

            if len(df) >= 20 and ratio >= 0.90:
                issues.append(
                    {
                        "type": "high_cardinality",
                        "column": str(column),
                        "severity": "low",
                        "count": unique_count,
                        "percentage": round(ratio * 100, 2),
                        "message": (
                            f"Column '{column}' has a high number "
                            "of unique values."
                        ),
                    }
                )

    def _detect_outliers(
        self,
        df: pd.DataFrame,
        issues: list[dict[str, Any]],
    ) -> None:
        numeric_df = df.select_dtypes(include="number")

        for column in numeric_df.columns:
            series = numeric_df[column].dropna()

            if len(series) < 4:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            if iqr == 0:
                continue

            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)

            outlier_mask = (
                (series < lower_bound)
                | (series > upper_bound)
            )

            outlier_count = int(outlier_mask.sum())

            if outlier_count == 0:
                continue

            percentage = outlier_count / len(series) * 100

            issues.append(
                {
                    "type": "outlier_candidates",
                    "column": str(column),
                    "severity": "low",
                    "count": outlier_count,
                    "percentage": round(percentage, 2),
                    "message": (
                        f"Column '{column}' contains "
                        f"{outlier_count} potential outliers."
                    ),
                }
            )

    def _calculate_quality_score(
        self,
        df: pd.DataFrame,
        issues: list[dict[str, Any]],
    ) -> float:
        if df.empty:
            return 0.0

        penalties = {
            "high": 15,
            "medium": 8,
            "low": 3,
        }

        total_penalty = sum(
            penalties.get(issue["severity"], 0)
            for issue in issues
        )

        return round(max(0.0, 100.0 - total_penalty), 2)