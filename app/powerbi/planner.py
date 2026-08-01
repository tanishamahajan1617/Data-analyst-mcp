from typing import Any

from app.powerbi.semantic import SemanticAnalyzer
from app.powerbi.ranking import DashboardRanking
from app.powerbi.kpi_selector import KPISelector
from app.powerbi.visual_selector import VisualSelector
from app.powerbi.relationship_detector import (
    RelationshipDetector,
)


class DashboardPlanner:
    """
    Dashboard Planner V2

    Orchestrates the dashboard planning pipeline.

    Semantic Analysis
            ↓
    Measure / Dimension Ranking
            ↓
    KPI Selection
            ↓
    Relationship Detection
            ↓
    Visual Selection
            ↓
    Slicer Selection
            ↓
    Dashboard Plan
    """

    def __init__(self) -> None:

        self.semantic = SemanticAnalyzer()

        self.ranking = DashboardRanking()

        self.kpi_selector = KPISelector()

        self.visual_selector = VisualSelector()

        self.relationship_detector = (
            RelationshipDetector()
        )

    def create_plan(
        self,
        dataset_id: str,
    ) -> dict[str, Any]:

        semantic = self.semantic.analyze(
            dataset_id
        )

        columns = semantic["columns"]

        identifiers = self._role(
            columns,
            "identifier",
        )

        dimensions = self._role(
            columns,
            "dimension",
        )

        datetimes = self._role(
            columns,
            "datetime",
        )

        measures = self._role(
            columns,
            "measure",
        )

        currencies = self._role(
            columns,
            "currency",
        )

        percentages = self._role(
            columns,
            "percentage",
        )

        ranked_measures = (
            self.ranking.rank_measures(
                currencies
                + measures
                + percentages
            )
        )

        ranked_dimensions = (
            self.ranking.rank_dimensions(
                dimensions
            )
        )

        kpis = self.kpi_selector.select(
            identifiers=identifiers,
            measures=measures,
            currencies=currencies,
            percentages=percentages,
        )

        visuals = self.visual_selector.select(
            measures=measures,
            currencies=currencies,
            percentages=percentages,
            dimensions=ranked_dimensions,
            datetimes=datetimes,
        )

        relationships = (
            self.relationship_detector.detect(
                measures=measures,
                currencies=currencies,
                percentages=percentages,
                dimensions=ranked_dimensions,
            )
        )

        visuals.extend(
            relationships
        )

        slicers = self._build_slicers(
            ranked_dimensions,
            datetimes,
        )

        return {
            "dataset_id": dataset_id,
            "title": "Data Analysis Dashboard",
            "planner_version": "v2",
            "source_stage": semantic["stage"],
            "kpis": kpis,
            "visuals": visuals,
            "slicers": slicers,
            "summary": {
                "measure_count": len(
                    ranked_measures
                ),
                "dimension_count": len(
                    ranked_dimensions
                ),
                "visual_count": len(
                    visuals
                ),
                "kpi_count": len(
                    kpis
                ),
            },
        }

    @staticmethod
    def _role(
        columns: list[dict[str, Any]],
        role: str,
    ) -> list[dict[str, Any]]:

        return [
            column
            for column in columns
            if column["semantic_role"] == role
        ]

    @staticmethod
    def _build_slicers(
        dimensions: list[dict[str, Any]],
        datetimes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        slicers = []

        for dimension in dimensions[:3]:

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