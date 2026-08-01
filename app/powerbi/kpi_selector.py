from typing import Any

from app.powerbi.ranking import DashboardRanking


class KPISelector:
    """
    Select the most valuable KPI cards for a dashboard
    using semantic information and business ranking.
    """

    def __init__(self) -> None:
        self.ranking = DashboardRanking()

    def select(
        self,
        identifiers: list[dict[str, Any]],
        measures: list[dict[str, Any]],
        currencies: list[dict[str, Any]],
        percentages: list[dict[str, Any]],
        max_kpis: int = 6,
    ) -> list[dict[str, Any]]:

        kpis: list[dict[str, Any]] = []

        # ------------------------------------------
        # Dataset size KPI
        # ------------------------------------------

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

        # ------------------------------------------
        # Rank business measures
        # ------------------------------------------

        ranked = self.ranking.rank_measures(
            currencies
            + measures
            + percentages
        )

        for column in ranked:

            aggregation = (
                column.get(
                    "suggested_aggregation"
                )
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

            if len(kpis) >= max_kpis:
                break

        return kpis

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

    @staticmethod
    def _kpi_title(
        field: str,
        aggregation: str,
    ) -> str:

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

        return (
            f"{prefix} "
            f"{KPISelector._display_name(field)}"
        )