from typing import Any

from fastmcp import FastMCP

from app.workflows.analysis_workflow import (
    AnalysisWorkflow,
)


workflow = AnalysisWorkflow()


def register_workflow_tools(
    mcp: FastMCP,
) -> None:

    @mcp.tool
    def analyze_and_build_dashboard(
        dataset_id: str,
        clean: bool = True,
        build_dashboard: bool = True,
    ) -> dict[str, Any]:
        """
        Run the complete autonomous data-analysis workflow.

        Profiles and assesses the dataset, plans cleaning,
        safely applies automatic cleaning operations,
        performs semantic analysis, generates a dashboard
        plan and layout, and optionally builds a Power BI
        PBIP project.

        Operations requiring human review are not applied
        automatically and are returned in the result.
        """

        return workflow.run(
            dataset_id=dataset_id,
            clean=clean,
            build_dashboard=build_dashboard,
        )