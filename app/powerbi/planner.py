from typing import Any

from app.powerbi.semantic import SemanticAnalyzer


class DashboardPlanner:
    def __init__(self) -> None:
        self.semantic_analyzer = SemanticAnalyzer()

    def create_plan(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        semantic = self.semantic_analyzer.analyze(
            dataset_id
        )

        columns = semantic["columns"]

        identifiers = self._columns_by_role(
            columns,
            "identifier",
        )

        dimensions = self._columns_by_role(
            columns,
            "dimension",
        )

        datetimes = self._columns_by_role(
            columns,
            "datetime",
        )

        currencies = self._columns_by_role(
            columns,
            "currency",
        )

        measures = self._columns_by_role(
            columns,
            "measure",
        )

        percentages = self._columns_by_role(
            columns,
            "percentage",
        )

        numeric_fields = (
            currencies
            + measures
            + percentages
        )

        kpis = self._build_kpis(
            identifiers=identifiers,
            numeric_fields=numeric_fields,
        )

        visuals = self._build_visuals(
            dimensions=dimensions,
            datetimes=datetimes,
            numeric_fields=numeric_fields,
        )

        slicers = self._build_slicers(
            dimensions=dimensions,
            datetimes=datetimes,
        )

        return {
            "dataset_id": dataset_id,
            "title": "Data Analysis Dashboard",
            "source_stage": semantic["stage"],
            "kpis": kpis,
            "visuals": visuals,
            "slicers": slicers,
        }

    @staticmethod
    def _columns_by_role(
        columns: list[dict[str, Any]],
        role: str,
    ) -> list[dict[str, Any]]:

        return [
            column
            for column in columns
            if column["semantic_role"] == role
        ]

    def _build_kpis(
        self,
        identifiers: list[dict[str, Any]],
        numeric_fields: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        kpis = []

        # One useful distinct-count KPI.
        if identifiers:
            identifier = identifiers[0]

            kpis.append(
                {
                    "type": "card",
                    "title": (
                        f"Distinct "
                        f"{self._display_name(identifier['name'])}"
                    ),
                    "field": identifier["name"],
                    "aggregation": "distinct_count",
                }
            )

        # Up to three numeric KPIs.
        for column in numeric_fields[:3]:
            aggregation = (
                column["suggested_aggregation"]
                or "sum"
            )

            kpis.append(
                {
                    "type": "card",
                    "title": self._kpi_title(
                        column["name"],
                        aggregation,
                    ),
                    "field": column["name"],
                    "aggregation": aggregation,
                }
            )

        return kpis

    def _build_visuals(
        self,
        dimensions: list[dict[str, Any]],
        datetimes: list[dict[str, Any]],
        numeric_fields: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        visuals = []

        if not numeric_fields:
            return visuals

        primary_measure = numeric_fields[0]

        measure_name = primary_measure["name"]

        aggregation = (
            primary_measure["suggested_aggregation"]
            or "sum"
        )

        # Time trend.
        if datetimes:
            date_column = datetimes[0]["name"]

            visuals.append(
                {
                    "type": "line_chart",
                    "title": (
                        f"{self._display_name(measure_name)} "
                        "Trend"
                    ),
                    "x": date_column,
                    "y": measure_name,
                    "aggregation": aggregation,
                }
            )

        # Comparison by dimension.
        if dimensions:
            dimension = dimensions[0]["name"]

            visuals.append(
                {
                    "type": "bar_chart",
                    "title": (
                        f"{self._display_name(measure_name)} "
                        f"by {self._display_name(dimension)}"
                    ),
                    "category": dimension,
                    "value": measure_name,
                    "aggregation": aggregation,
                }
            )

        # Second useful dimension if available.
        if len(dimensions) >= 2:
            dimension = dimensions[1]["name"]

            visuals.append(
                {
                    "type": "column_chart",
                    "title": (
                        f"{self._display_name(measure_name)} "
                        f"by {self._display_name(dimension)}"
                    ),
                    "category": dimension,
                    "value": measure_name,
                    "aggregation": aggregation,
                }
            )

        # Distribution for a numeric field.
        visuals.append(
            {
                "type": "distribution_chart",
                "title": (
                    f"{self._display_name(measure_name)} "
                    "Distribution"
                ),
                "field": measure_name,
                "bin_count": 10,
            }
        )

        return visuals

    @staticmethod
    def _build_slicers(
        dimensions: list[dict[str, Any]],
        datetimes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        slicers = []

        for dimension in dimensions[:2]:
            slicers.append(
                {
                    "type": "slicer",
                    "field": dimension["name"],
                }
            )

        if datetimes:
            slicers.append(
                {
                    "type": "date_slicer",
                    "field": datetimes[0]["name"],
                }
            )

        return slicers

    @staticmethod
    def _kpi_title(
        field: str,
        aggregation: str,
    ) -> str:

        display_name = DashboardPlanner._display_name(
            field
        )

        labels = {
            "sum": "Total",
            "average": "Average",
            "distinct_count": "Distinct",
            "count": "Count",
            "min": "Minimum",
            "max": "Maximum",
        }

        prefix = labels.get(
            aggregation,
            aggregation.title(),
        )

        return f"{prefix} {display_name}"

    @staticmethod
    def _display_name(
        field: str,
    ) -> str:

        return (
            field
            .replace("_", " ")
            .strip()
            .title()
        )