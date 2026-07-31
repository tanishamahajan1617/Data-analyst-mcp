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
        Run the complete autonomous data-analysis workflow for a dataset
        that has already been uploaded to the Data Analyst MCP server.

        Use this tool when a valid dataset_id is available.

        Profiles the dataset, assesses data quality, performs safe cleaning
        when requested, runs semantic analysis, identifies KPIs, creates
        the dashboard plan and layout, and optionally generates the
        Power BI PBIP project and downloadable artifact.

        If the user wants to analyze a new dataset but no dataset_id exists,
        use get_dataset_upload_url first so the dataset can be uploaded to
        the Data Analyst MCP server.

        Do not use client-local file paths with this tool.
        """

        return workflow.run(
            dataset_id=dataset_id,
            clean=clean,
            build_dashboard=build_dashboard,
        )


    @mcp.tool
    def analyze_file_and_build_dashboard(
        file_path: str,
        clean: bool = True,
        build_dashboard: bool = True,
    ) -> dict[str, Any]:
        """
        Run the complete analysis workflow for a dataset file that is
        already accessible on the SAME filesystem as the MCP server.

        IMPORTANT:
        Do NOT use this tool for files attached in Claude or another
        remote MCP client when file_path belongs to that client's
        filesystem, for example:

        /mnt/user-data/uploads/...

        Such client-local paths are not accessible to the remote
        Data Analyst MCP server.

        For a new dataset from a remote client such as Claude, use
        get_dataset_upload_url first. After the user uploads the dataset
        to the Data Analyst MCP server, use analyze_and_build_dashboard
        with the returned dataset_id.

        Use this tool only when file_path is genuinely accessible to the
        MCP server process.
        """

        return workflow.run_file(
            file_path=file_path,
            clean=clean,
            build_dashboard=build_dashboard,
        )