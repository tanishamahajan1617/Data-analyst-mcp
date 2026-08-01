from typing import Any

from app.powerbi.ranking import DashboardRanking


class RelationshipDetector:
    """
    Detect meaningful measure-to-measure and
    dimension-to-measure relationships for
    dashboard visualizations.
    """

    def __init__(self) -> None:
        self.ranking = DashboardRanking()

    def detect(
        self,
        measures: list[dict[str, Any]],
        currencies: list[dict[str, Any]],
        percentages: list[dict[str, Any]],
        dimensions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        relationships: list[dict[str, Any]] = []

        ranked_measures = self.ranking.rank_measures(
            currencies
            + measures
            + percentages
        )

        ranked_dimensions = self.ranking.rank_dimensions(
            dimensions
        )

        # -------------------------------------------------
        # Measure ↔ Measure
        # -------------------------------------------------

        primary = ranked_measures[0] if ranked_measures else None

        if primary:

            for measure in ranked_measures[1:4]:

                relationships.append(
                    {
                        "type": "scatter_chart",
                        "title": (
                            f"{self._display(primary['name'])} vs "
                            f"{self._display(measure['name'])}"
                        ),
                        "x": measure["name"],
                        "y": primary["name"],
                        "relationship": "measure_measure",
                    }
                )

        # -------------------------------------------------
        # Dimension ↔ Measure
        # -------------------------------------------------

        if primary:

            for dimension in ranked_dimensions[:3]:

                relationships.append(
                    {
                        "type": "bar_chart",
                        "title": (
                            f"{self._display(primary['name'])} by "
                            f"{self._display(dimension['name'])}"
                        ),
                        "category": dimension["name"],
                        "value": primary["name"],
                        "aggregation": (
                            primary.get(
                                "suggested_aggregation"
                            )
                            or "sum"
                        ),
                        "relationship": "dimension_measure",
                    }
                )

        return relationships

    @staticmethod
    def _display(
        field: str,
    ) -> str:

        return (
            field
            .replace("_", " ")
            .strip()
            .title()
        )