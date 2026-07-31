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
        Run the complete autonomous data-analysis and dashboard workflow
        for a dataset already uploaded to the Data Analyst MCP server.

        A valid dataset_id is required.

        If the user has a new dataset, including a file attached in Claude,
        and no dataset_id exists yet, do NOT attempt to use the attachment's
        local file path.

        Client-local paths such as /mnt/user-data/uploads/... are not
        accessible to this remote MCP server.

        For a new dataset, use get_dataset_upload_url first. After the user
        uploads the dataset and receives a dataset_id, call this tool.

        This workflow performs profiling, quality assessment, safe cleaning,
        semantic analysis, KPI discovery, dashboard planning, layout
        generation, Power BI PBIP generation, and artifact packaging.
        """

        return workflow.run(
            dataset_id=dataset_id,
            clean=clean,
            build_dashboard=build_dashboard,
        )