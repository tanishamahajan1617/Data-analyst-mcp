import asyncio
import json
from pathlib import Path

from fastmcp import Client

from mcp_server.server import mcp


async def main() -> None:
    async with Client(mcp) as client:

        # ------------------------------------------
        # 1. List MCP tools
        # ------------------------------------------

        tools = await client.list_tools()

        print("\n=== MCP TOOLS ===")

        for tool in tools:
            print(f"- {tool.name}")

        # ------------------------------------------
        # 2. Health check
        # ------------------------------------------

        print("\n=== HEALTH CHECK ===")

        health = await client.call_tool(
            "health_check",
            {},
        )

        print(
            json.dumps(
                health.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 3. Create a NEW test dataset
        # ------------------------------------------

        test_file = Path(
            "tests/test_sales.csv"
        ).resolve()

        test_file.write_text(
            "Customer,Region,Sales,Quantity\n"
            "Alice,North,12000,2\n"
            "Bob,South,18000,3\n"
            "Charlie,North,15000,1\n"
            "David,West,22000,4\n"
            "Eva,South,19500,2\n",
            encoding="utf-8",
        )

        print("\n=== IMPORT DATASET ===")
        print(f"Source: {test_file}")

        imported = await client.call_tool(
            "import_dataset",
            {
                "file_path": str(
                    test_file
                ),
            },
        )

        import_data = (
            imported.structured_content
        )

        print(
            json.dumps(
                import_data,
                indent=2,
            )
        )

        dataset_id = import_data[
            "dataset_id"
        ]

        # ------------------------------------------
        # 4. Metadata through MCP
        # ------------------------------------------

        print("\n=== DATASET METADATA ===")

        metadata = await client.call_tool(
            "get_dataset_metadata",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                metadata.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 5. Structural inspection through MCP
        # ------------------------------------------

        print("\n=== INSPECT DATASET ===")

        inspection = await client.call_tool(
            "inspect_dataset",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                inspection.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 6. Load dataset information
        # ------------------------------------------

        print("\n=== DATASET INFO ===")

        info = await client.call_tool(
            "get_dataset_info",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                info.structured_content,
                indent=2,
            )
        )


                # ------------------------------------------
        # 7. Profile dataset
        # ------------------------------------------

        print("\n=== PROFILE DATASET ===")

        profile = await client.call_tool(
            "profile_dataset",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                profile.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 8. Assess data quality
        # ------------------------------------------

        print("\n=== DATA QUALITY ===")

        quality = await client.call_tool(
            "assess_data_quality",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                quality.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 9. Explore dataset
        # ------------------------------------------

        print("\n=== EXPLORATION ===")

        exploration = await client.call_tool(
            "explore_dataset",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                exploration.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 10. Numeric statistics
        # ------------------------------------------

        print("\n=== NUMERIC STATISTICS ===")

        statistics = await client.call_tool(
            "get_numeric_statistics",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                statistics.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 11. Value counts
        # ------------------------------------------

        print("\n=== REGION VALUE COUNTS ===")

        counts = await client.call_tool(
            "get_value_counts",
            {
                "dataset_id": dataset_id,
                "column": "Region",
                "limit": 10,
            },
        )

        print(
            json.dumps(
                counts.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 12. Correlations
        # ------------------------------------------

        print("\n=== CORRELATIONS ===")

        correlations = await client.call_tool(
            "get_correlations",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                correlations.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 13. Group analysis
        # ------------------------------------------

        print("\n=== SALES BY REGION ===")

        grouped = await client.call_tool(
            "group_dataset",
            {
                "dataset_id": dataset_id,
                "group_column": "Region",
                "value_column": "Sales",
                "aggregation": "sum",
            },
        )

        print(
            json.dumps(
                grouped.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 14. Generate cleaning plan
        # ------------------------------------------

        print("\n=== CLEANING PLAN ===")

        cleaning_plan = await client.call_tool(
            "plan_cleaning",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                cleaning_plan.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 15. Execute cleaning
        # ------------------------------------------

        print("\n=== CLEAN DATASET ===")

        cleaned = await client.call_tool(
            "clean_dataset",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                cleaned.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 16. Verify active stage
        # ------------------------------------------

        print("\n=== INFO AFTER CLEANING ===")

        cleaned_info = await client.call_tool(
            "get_dataset_info",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                cleaned_info.structured_content,
                indent=2,
            )
        )

                # ------------------------------------------
        # 17. Semantic analysis
        # ------------------------------------------

        print("\n=== SEMANTIC ANALYSIS ===")

        semantic = await client.call_tool(
            "analyze_dataset",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                semantic.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 18. Dashboard plan
        # ------------------------------------------

        print("\n=== DASHBOARD PLAN ===")

        dashboard_plan = await client.call_tool(
            "plan_dashboard",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                dashboard_plan.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 19. Dashboard layout
        # ------------------------------------------

        print("\n=== DASHBOARD LAYOUT ===")

        dashboard_layout = await client.call_tool(
            "plan_dashboard_layout",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                dashboard_layout.structured_content,
                indent=2,
            )
        )


                # ------------------------------------------
        # 20. Build Power BI dashboard
        # ------------------------------------------

        print("\n=== BUILD POWER BI DASHBOARD ===")

        powerbi = await client.call_tool(
            "build_powerbi_dashboard",
            {
                "dataset_id": dataset_id,
            },
        )

        print(
            json.dumps(
                powerbi.structured_content,
                indent=2,
            )
        )

        # ------------------------------------------
        # 21. Autonomous end-to-end workflow
        # ------------------------------------------

        print("\n=== AUTONOMOUS WORKFLOW ===")

        workflow_result = await client.call_tool(
            "analyze_and_build_dashboard",
            {
                "dataset_id": dataset_id,
                "clean": True,
                "build_dashboard": True,
            },
        )

        print(
            json.dumps(
                workflow_result.structured_content,
                indent=2,
                default=str,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())

           