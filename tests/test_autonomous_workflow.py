import json
from pathlib import Path

from app.workflows.analysis_workflow import AnalysisWorkflow


def main() -> None:
    workflow = AnalysisWorkflow()

    test_file = (
        Path(__file__).parent / "test_sales.csv"
    ).resolve()

    print("\n=== INPUT ===")
    print(test_file)

    result = workflow.run_file(
        file_path=str(test_file),
        clean=True,
        build_dashboard=True,
    )

    print("\n=== RESULT ===")
    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )

    print("\n=== SUMMARY ===")
    print("Status:", result["status"])
    print("Dataset ID:", result["dataset_id"])
    print(
        "Active stage:",
        result["dataset"]["active_stage"],
    )

    powerbi = result.get("powerbi")

    if powerbi:
        print(
            "PBIP:",
            powerbi["pbip_file"],
        )
        print(
            "Visual count:",
            powerbi["pbir_report"]["visual_count"],
        )


if __name__ == "__main__":
    main()