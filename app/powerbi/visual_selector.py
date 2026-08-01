from typing import Any

from app.powerbi.ranking import DashboardRanking


class VisualSelector:
    """
    Build business-oriented dashboard visuals from
    semantic metadata.
    """

    def __init__(self) -> None:
        self.ranking = DashboardRanking()

    def select(
        self,
        measures: list[dict[str, Any]],
        currencies: list[dict[str, Any]],
        percentages: list[dict[str, Any]],
        dimensions: list[dict[str, Any]],
        datetimes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        visuals: list[dict[str, Any]] = []

        ranked_measures = self.ranking.rank_measures(
            currencies
            + measures
            + percentages
        )

        ranked_dimensions = self.ranking.rank_dimensions(
            dimensions
        )

        if not ranked_measures:
            return visuals

        primary = ranked_measures[0]

        aggregation = (
            primary.get(
                "suggested_aggregation"
            )
            or "sum"
        )

        # ------------------------------------------
        # Time Trend
        # ------------------------------------------

        if datetimes:

            visuals.append(
                {
                    "type": "line_chart",
                    "title": (
                        f"{self._display_name(primary['name'])} Trend"
                    ),
                    "x": datetimes[0]["name"],
                    "y": primary["name"],
                    "aggregation": aggregation,
                }
            )

        # ------------------------------------------
        # Category Comparisons
        # ------------------------------------------

        for dimension in ranked_dimensions[:2]:

            visuals.append(
                {
                    "type": "bar_chart",
                    "title": (
                        f"{self._display_name(primary['name'])} "
                        f"by {self._display_name(dimension['name'])}"
                    ),
                    "category": dimension["name"],
                    "value": primary["name"],
                    "aggregation": aggregation,
                }
            )

        # ------------------------------------------
        # Scatter Relationships
        # ------------------------------------------

        if len(ranked_measures) >= 2:

            secondary = ranked_measures[1]

            visuals.append(
                {
                    "type": "scatter_chart",
                    "title": (
                        f"{self._display_name(secondary['name'])} "
                        f"vs {self._display_name(primary['name'])}"
                    ),
                    "x": secondary["name"],
                    "y": primary["name"],
                }
            )

        if len(ranked_measures) >= 3:

            tertiary = ranked_measures[2]

            visuals.append(
                {
                    "type": "scatter_chart",
                    "title": (
                        f"{self._display_name(tertiary['name'])} "
                        f"vs {self._display_name(primary['name'])}"
                    ),
                    "x": tertiary["name"],
                    "y": primary["name"],
                }
            )

        # ------------------------------------------
        # Distribution Charts
        # ------------------------------------------

        for measure in ranked_measures[:2]:

            visuals.append(
                {
                    "type": "distribution_chart",
                    "title": (
                        f"{self._display_name(measure['name'])} "
                        "Distribution"
                    ),
                    "field": measure["name"],
                    "bin_count": 10,
                }
            )

        # ------------------------------------------
        # Donut Chart
        # ------------------------------------------

        if ranked_dimensions:

            visuals.append(
                {
                    "type": "donut_chart",
                    "title": (
                        f"{self._display_name(ranked_dimensions[0]['name'])}"
                        " Distribution"
                    ),
                    "category": ranked_dimensions[0]["name"],
                }
            )

        return visuals

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