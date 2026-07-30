from typing import Any

from fastmcp import FastMCP

from app.powerbi.builder import PowerBIProjectBuilder
from app.powerbi.semantic import SemanticAnalyzer
from app.powerbi.planner import DashboardPlanner
from app.powerbi.dashboard_planner import DashboardLayoutPlanner


semantic_analyzer = SemanticAnalyzer()
dashboard_planner = DashboardPlanner()
layout_planner = DashboardLayoutPlanner()
powerbi_builder = PowerBIProjectBuilder()


def register_powerbi_tools(
    mcp: FastMCP,
) -> None:

    @mcp.tool
    def analyze_dataset(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Analyze the semantic meaning of dataset columns.

        Identifies dimensions, measures, currency,
        percentages, identifiers, and datetime fields,
        and suggests appropriate aggregations.
        """

        return semantic_analyzer.analyze(
            dataset_id
        )

    @mcp.tool
    def plan_dashboard(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Generate a logical Power BI dashboard plan.

        Selects KPIs, charts, distributions, and
        slicers based on dataset semantics.
        """

        return dashboard_planner.create_plan(
            dataset_id
        )

    @mcp.tool
    def plan_dashboard_layout(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Generate the physical Power BI dashboard layout.

        Assigns dashboard elements to positions on
        the Power BI report canvas.
        """

        return layout_planner.create_layout(
            dataset_id
        )

    @mcp.tool
    def build_powerbi_dashboard(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Build a Power BI PBIP project from a dataset.

        Uses the active dataset stage and automatically
        generated dashboard plan.
        """

        return powerbi_builder.build(
            dataset_id
        )