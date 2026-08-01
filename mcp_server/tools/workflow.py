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
        Run the complete autonomous data-analysis workflow
        for a dataset that already exists on the Data
        Analyst platform.

        Parameters
        ----------
        dataset_id:
            Identifier of an existing uploaded dataset.

        clean:
            Automatically execute safe cleaning operations
            before analysis.

        build_dashboard:
            Generate a Power BI PBIP project and package
            all generated dashboard artifacts.

        ------------------------------------------------------------------
        IMPORTANT
        ------------------------------------------------------------------

        A valid dataset_id is REQUIRED.

        This tool ONLY works with datasets that have already
        been uploaded to the Data Analyst platform.

        If the user wants to analyze a new CSV or XLSX dataset
        and no dataset_id is available:

        1. Call get_dataset_upload_url().
        2. Direct the user to the upload page.
        3. Wait until the upload completes.
        4. Obtain the returned dataset_id.
        5. Call analyze_and_build_dashboard().

        ------------------------------------------------------------------
        DO NOT
        ------------------------------------------------------------------

        Never attempt to analyze:

        • attached files
        • local filesystem paths
        • client-local paths
          (for example /mnt/user-data/uploads/...)
        • copied CSV content
        • copied Excel content
        • partial datasets
        • truncated dataset contents

        Remote MCP servers cannot reliably access
        client-local attachments or local filesystem
        paths.

        The upload page is the ONLY supported ingestion
        workflow for new datasets.

        ------------------------------------------------------------------
        WORKFLOW
        ------------------------------------------------------------------

        This workflow automatically performs:

        • Dataset profiling
        • Data quality assessment
        • Cleaning plan generation
        • Safe automatic cleaning
        • Exploratory data analysis
        • Semantic role detection
        • KPI discovery
        • Dashboard planning
        • Dashboard layout generation
        • Power BI PBIP generation
        • Dashboard artifact packaging

        Returns
        -------
        Complete workflow results including all generated
        analysis outputs and Power BI artifacts.
        """

        return workflow.run(
            dataset_id=dataset_id,
            clean=clean,
            build_dashboard=build_dashboard,
        )