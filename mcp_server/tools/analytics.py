from typing import Any

from fastmcp import FastMCP

from app.analytics.profiler import DatasetProfiler
from app.analytics.quality import DataQualityAnalyzer
from app.analytics.explorer import DatasetExplorer
from app.analytics.cleaning.planner import CleaningPlanner
from app.analytics.cleaning.executor import CleaningExecutor
from app.workflows.analysis_workflow import AnalysisWorkflow


profiler = DatasetProfiler()
quality_analyzer = DataQualityAnalyzer()
explorer = DatasetExplorer()
cleaning_planner = CleaningPlanner()
cleaning_executor = CleaningExecutor()
workflow = AnalysisWorkflow()


def register_analytics_tools(
    mcp: FastMCP,
) -> None:

    @mcp.tool
    def profile_dataset(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Profile a dataset.

        Returns dataset dimensions, column data types,
        missing values, unique values, duplicates,
        and numeric summaries.
        """

        return profiler.profile(
            dataset_id
        )

    @mcp.tool
    def assess_data_quality(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Assess dataset quality.

        Detects missing values, duplicate rows,
        constant columns, high-cardinality columns,
        and potential numeric outliers.
        """

        return quality_analyzer.analyze(
            dataset_id
        )

    @mcp.tool
    def explore_dataset(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Return a structural exploration summary.

        Identifies rows, columns, active dataset stage,
        numeric columns, and categorical columns.
        """

        return explorer.summary(
            dataset_id
        )

    @mcp.tool
    def get_numeric_statistics(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Calculate descriptive statistics for
        numeric columns.

        Includes count, mean, median, standard
        deviation, min, max, Q1, and Q3.
        """

        return explorer.numeric_statistics(
            dataset_id
        )

    @mcp.tool
    def get_value_counts(
        dataset_id: str,
        column: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Return the most frequent values in a column.

        Limit must be between 1 and 100.
        """

        return explorer.value_counts(
            dataset_id=dataset_id,
            column=column,
            limit=limit,
        )

    @mcp.tool
    def get_correlations(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Calculate pairwise correlations between
        numeric columns.

        Results are ordered by absolute correlation
        strength.
        """

        return explorer.correlations(
            dataset_id
        )

    @mcp.tool
    def group_dataset(
        dataset_id: str,
        group_column: str,
        value_column: str,
        aggregation: str,
    ) -> dict[str, Any]:
        """
        Group a dataset column and aggregate another.

        Supported aggregations:
        sum, mean, median, min, max, count.
        """

        return explorer.group_by(
            dataset_id=dataset_id,
            group_column=group_column,
            value_column=value_column,
            aggregation=aggregation,
        )

    @mcp.tool
    def plan_cleaning(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Generate an automatic cleaning plan for
        a dataset without modifying the dataset.
        """

        return cleaning_planner.create_plan(
            dataset_id
        )

    @mcp.tool
    def clean_dataset(
        dataset_id: str,
    ) -> dict[str, Any]:
        """
        Automatically plan and execute dataset
        cleaning.

        The cleaning planner determines the
        operations and the cleaning executor
        creates the cleaned dataset stage.
        """

        plan = cleaning_planner.create_plan(
            dataset_id
        )

        operations = plan.get(
            "operations",
            [],
        )

        result = cleaning_executor.execute(
            dataset_id=dataset_id,
            operations=operations,
        )

        return {
            **result,
            "cleaning_plan": plan,
        }

    @mcp.tool
    def analyze_file_and_build_dashboard(
        file_path: str,
        clean: bool = True,
        build_dashboard: bool = True,
    ) -> dict[str, Any]:
        """
        Import a local CSV or XLSX file and run the
        complete autonomous data-analysis workflow.

        The workflow:

        1. Imports the dataset
        2. Inspects its structure
        3. Profiles the dataset
        4. Assesses data quality
        5. Plans safe cleaning
        6. Executes safe cleaning
        7. Performs semantic analysis
        8. Plans dashboard visuals
        9. Plans dashboard layout
        10. Optionally generates a Power BI PBIP project

        Returns the dataset_id, inspection results,
        analysis results, cleaning information,
        dashboard plan, dashboard layout, and
        Power BI project information.
        """

        return workflow.run_file(
            file_path=file_path,
            clean=clean,
            build_dashboard=build_dashboard,
        )