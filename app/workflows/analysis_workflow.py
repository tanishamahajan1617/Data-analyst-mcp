from pathlib import Path
from typing import Any

from app.analytics.cleaning.executor import CleaningExecutor
from app.analytics.cleaning.planner import CleaningPlanner
from app.analytics.profiler import DatasetProfiler
from app.analytics.quality import DataQualityAnalyzer
from app.datasets.loader import DatasetLoader
from app.datasets.parser import DatasetParser
from app.datasets.store import DatasetStore
from app.powerbi.builder import PowerBIProjectBuilder
from app.powerbi.dashboard_planner import DashboardLayoutPlanner
from app.powerbi.planner import DashboardPlanner
from app.powerbi.semantic import SemanticAnalyzer


class AnalysisWorkflowError(Exception):
    """Raised when the end-to-end analysis workflow fails."""


class AnalysisWorkflow:
    """
    Orchestrates the complete:

        dataset
        -> inspection
        -> profiling
        -> quality assessment
        -> cleaning
        -> semantic analysis
        -> dashboard planning
        -> dashboard layout
        -> Power BI project

    The workflow coordinates existing application
    services and does not duplicate their internal logic.
    """

    SAFE_CLEANING_OPERATIONS = {
        "rename_column",
        "remove_duplicates",
        "trim_whitespace",
    }

    def __init__(self) -> None:
        # Dataset services
        self.loader = DatasetLoader()
        self.store = DatasetStore()
        self.parser = DatasetParser()

        # Analytics services
        self.profiler = DatasetProfiler()
        self.quality_analyzer = DataQualityAnalyzer()

        # Cleaning services
        self.cleaning_planner = CleaningPlanner()
        self.cleaning_executor = CleaningExecutor()

        # Semantic/dashboard services
        self.semantic_analyzer = SemanticAnalyzer()
        self.dashboard_planner = DashboardPlanner()
        self.layout_planner = DashboardLayoutPlanner()

        # Power BI
        self.powerbi_builder = PowerBIProjectBuilder()

    # =========================================================
    # FILE -> COMPLETE WORKFLOW
    # =========================================================

    def run_file(
        self,
        file_path: str,
        *,
        clean: bool = True,
        build_dashboard: bool = True,
    ) -> dict[str, Any]:
        """
        Import a local CSV/XLSX file and run the complete
        autonomous analysis workflow.

        This is the highest-level entry point for clients
        that do not already have a dataset_id.
        """

        # -------------------------------------------------
        # 1. Validate path
        # -------------------------------------------------

        if not file_path:
            raise AnalysisWorkflowError(
                "file_path is required."
            )

        source_path = Path(file_path).expanduser()

        if not source_path.exists():
            raise AnalysisWorkflowError(
                f"Dataset file does not exist: {source_path}"
            )

        if not source_path.is_file():
            raise AnalysisWorkflowError(
                f"Dataset path is not a file: {source_path}"
            )

        # -------------------------------------------------
        # 2. Import dataset
        # -------------------------------------------------

        try:
            import_result = self.store.save_path(
                source_path=source_path,
            )
        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Unable to import dataset: {source_path}"
            ) from exc

        dataset_id = import_result.get("dataset_id")

        if not dataset_id:
            raise AnalysisWorkflowError(
                "Dataset import did not return a dataset_id."
            )

        # -------------------------------------------------
        # 3. Structural inspection
        # -------------------------------------------------

        try:
            inspection = self.parser.inspect(
                dataset_id
            )
        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Unable to inspect dataset '{dataset_id}'."
            ) from exc

        # -------------------------------------------------
        # 4. Stop if dataset cannot be parsed
        # -------------------------------------------------

        if not inspection.get("parseable", False):
            return {
                "status": "review_required",
                "dataset_id": dataset_id,
                "import": import_result,
                "inspection": inspection,
                "reason": (
                    "Dataset contains structural problems "
                    "that require repair or user review "
                    "before analysis can continue."
                ),
            }

        # -------------------------------------------------
        # 5. Run analysis workflow
        # -------------------------------------------------

        result = self.run(
            dataset_id=dataset_id,
            clean=clean,
            build_dashboard=build_dashboard,
        )

        # -------------------------------------------------
        # 6. Attach import/inspection information
        # -------------------------------------------------

        return {
            **result,
            "import": import_result,
            "inspection": inspection,
        }

    # =========================================================
    # DATASET_ID -> COMPLETE WORKFLOW
    # =========================================================

    def run(
        self,
        dataset_id: str,
        *,
        clean: bool = True,
        build_dashboard: bool = True,
    ) -> dict[str, Any]:
        """
        Run the complete analysis workflow for an
        already-imported dataset.
        """

        if not dataset_id:
            raise AnalysisWorkflowError(
                "dataset_id is required."
            )

        # -------------------------------------------------
        # 1. Validate dataset
        # -------------------------------------------------

        try:
            metadata = self.loader.get_metadata(
                dataset_id
            )

            source_stage = self.loader.get_active_stage(
                dataset_id
            )

        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Unable to load dataset '{dataset_id}'."
            ) from exc

        # -------------------------------------------------
        # 2. Profile original dataset
        # -------------------------------------------------

        try:
            profile_before = self.profiler.profile(
                dataset_id
            )
        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Unable to profile dataset '{dataset_id}'."
            ) from exc

        # -------------------------------------------------
        # 3. Assess original quality
        # -------------------------------------------------

        try:
            quality_before = (
                self.quality_analyzer.analyze(
                    dataset_id
                )
            )
        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Unable to assess quality for "
                f"dataset '{dataset_id}'."
            ) from exc

        # -------------------------------------------------
        # 4. Create cleaning plan
        # -------------------------------------------------

        cleaning_plan = {
            "dataset_id": dataset_id,
            "source_stage": source_stage,
            "operation_count": 0,
            "operations": [],
        }

        safe_operations: list[dict[str, Any]] = []
        review_operations: list[dict[str, Any]] = []

        if clean:
            try:
                cleaning_plan = (
                    self.cleaning_planner.create_plan(
                        dataset_id
                    )
                )
            except Exception as exc:
                raise AnalysisWorkflowError(
                    f"Unable to create cleaning plan for "
                    f"dataset '{dataset_id}'."
                ) from exc

            all_operations = cleaning_plan.get(
                "operations",
                [],
            )

            for operation in all_operations:
                operation_type = operation.get("type")
                strategy = operation.get("strategy")

                if (
                    operation_type
                    in self.SAFE_CLEANING_OPERATIONS
                    and strategy != "review"
                ):
                    safe_operations.append(operation)
                else:
                    review_operations.append(operation)

        # -------------------------------------------------
        # 5. Execute safe cleaning operations
        # -------------------------------------------------

        cleaning_result = None

        if clean:
            try:
                cleaning_result = (
                    self.cleaning_executor.execute(
                        dataset_id=dataset_id,
                        operations=safe_operations,
                    )
                )
            except Exception as exc:
                raise AnalysisWorkflowError(
                    f"Unable to clean dataset "
                    f"'{dataset_id}'."
                ) from exc

        # -------------------------------------------------
        # 6. Determine active stage
        # -------------------------------------------------

        try:
            active_stage = (
                self.loader.get_active_stage(
                    dataset_id
                )
            )
        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Unable to determine active stage for "
                f"dataset '{dataset_id}'."
            ) from exc

        # -------------------------------------------------
        # 7. Profile final dataset
        # -------------------------------------------------

        try:
            profile_after = self.profiler.profile(
                dataset_id
            )

            quality_after = (
                self.quality_analyzer.analyze(
                    dataset_id
                )
            )
        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Unable to profile final dataset "
                f"'{dataset_id}'."
            ) from exc

        # -------------------------------------------------
        # 8. Semantic analysis
        # -------------------------------------------------

        try:
            semantic_analysis = (
                self.semantic_analyzer.analyze(
                    dataset_id
                )
            )
        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Semantic analysis failed for "
                f"dataset '{dataset_id}'."
            ) from exc

        # -------------------------------------------------
        # 9. Logical dashboard plan
        # -------------------------------------------------

        try:
            dashboard_plan = (
                self.dashboard_planner.create_plan(
                    dataset_id
                )
            )
        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Dashboard planning failed for "
                f"dataset '{dataset_id}'."
            ) from exc

        # -------------------------------------------------
        # 10. Physical dashboard layout
        # -------------------------------------------------

        try:
            dashboard_layout = (
                self.layout_planner.create_layout(
                    dataset_id
                )
            )
        except Exception as exc:
            raise AnalysisWorkflowError(
                f"Dashboard layout planning failed for "
                f"dataset '{dataset_id}'."
            ) from exc

        # -------------------------------------------------
        # 11. Build Power BI project
        # -------------------------------------------------

        powerbi_result = None

        if build_dashboard:
            try:
                powerbi_result = (
                    self.powerbi_builder.build(
                        dataset_id
                    )
                )
            except Exception as exc:
                raise AnalysisWorkflowError(
                    f"Power BI project generation failed "
                    f"for dataset '{dataset_id}'."
                ) from exc

        # -------------------------------------------------
        # 12. Final result
        # -------------------------------------------------

        return {
            "status": "completed",
            "dataset_id": dataset_id,

            "dataset": {
                "filename": metadata.get(
                    "filename"
                ),
                "file_type": metadata.get(
                    "file_type"
                ),
                "source_stage": source_stage,
                "active_stage": active_stage,
            },

            "profile": {
                "before": profile_before,
                "after": profile_after,
            },

            "quality": {
                "before": quality_before,
                "after": quality_after,
                "score_before": (
                    quality_before.get(
                        "quality_score"
                    )
                ),
                "score_after": (
                    quality_after.get(
                        "quality_score"
                    )
                ),
            },

            "cleaning": {
                "requested": clean,
                "plan": cleaning_plan,
                "safe_operations": (
                    safe_operations
                ),
                "review_operations": (
                    review_operations
                ),
                "result": cleaning_result,
            },

            "semantic_analysis": (
                semantic_analysis
            ),

            "dashboard_plan": (
                dashboard_plan
            ),

            "dashboard_layout": (
                dashboard_layout
            ),

            "powerbi": (
                powerbi_result
            ),
        }